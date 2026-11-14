"""Shared scene effects: audio envelope, fog volume, dust motes, rain, clay ground, mesh utilities."""
import bpy, bmesh, json, os, math
import numpy as np
from mathutils import Vector, Matrix
import clay as K
import common as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env = None


def env(frame_abs, band='low', smooth=1):
    """Audio envelope (0..~1) of the master mix at an absolute film frame (24 fps)."""
    global _env
    if _env is None:
        _env = json.load(open(f'{ROOT}/audio/envelope.json'))
        for k in list(_env):
            a = np.array(_env[k]); _env[k] = a / a.max()
    a = _env[band]
    i = int(np.clip(frame_abs, 0, len(a) - 1))
    lo, hi = max(0, i - smooth), min(len(a), i + smooth + 1)
    return float(a[lo:hi].mean())


def smooth(x, a=0.0, b=1.0):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def fog(sc, lo, hi, density=0.03, aniso=0.4, color=(1, 1, 1), name='Fog'):
    """Homogeneous scattering volume in a box (visible light beams)."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.object; ob.name = name
    lo, hi = Vector(lo), Vector(hi)
    ob.location = (lo + hi) / 2; ob.scale = hi - lo
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    v = nt.nodes.new('ShaderNodeVolumeScatter')
    v.inputs['Color'].default_value = (*color, 1); v.inputs['Density'].default_value = density
    v.inputs['Anisotropy'].default_value = aniso
    nt.links.new(v.outputs[0], nt.nodes['Material Output'].inputs['Volume'])
    ob.data.materials.append(m)
    ob.visible_shadow = False
    return ob


class Motes:
    """Dust motes: tiny spheres instanced on the vertices of a point mesh, drifting slowly."""

    def __init__(self, sc, n, center, radius, height, size=0.0012, seed=0, color=(1.0, 0.9, 0.75), emit=0.0,
                 drift=(0.004, 0.0, 0.006)):
        rs = np.random.RandomState(seed)
        r = radius * np.sqrt(rs.uniform(0, 1, n)); th = rs.uniform(0, 6.283, n)
        self.p0 = np.stack([center[0] + r * np.cos(th), center[1] + r * np.sin(th),
                            center[2] + rs.uniform(0, height, n)], 1)
        self.ph = rs.uniform(0, 6.283, (n, 3)); self.fr = rs.uniform(0.15, 0.6, (n, 3))
        self.amp = rs.uniform(0.004, 0.02, (n, 1)); self.drift = np.array(drift)
        self.sp = rs.uniform(0.5, 1.5, (n, 1))
        me = bpy.data.meshes.new('motes'); me.from_pydata([tuple(p) for p in self.p0], [], [])
        self.ob = bpy.data.objects.new('motes', me); sc.collection.objects.link(self.ob)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=size)
        s = bpy.context.object; s.name = 'mote'
        m = bpy.data.materials.new('mote'); m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Roughness'].default_value = 0.6
        if emit:
            b.inputs['Emission Color'].default_value = (*color, 1); b.inputs['Emission Strength'].default_value = emit
        s.data.materials.append(m)
        s.parent = self.ob
        self.ob.instance_type = 'VERTS'
        self.height = height; self.z0 = center[2]

    def update(self, frame):
        t = frame / 24.0
        p = self.p0 + self.drift * t * self.sp + self.amp * np.sin(self.ph + self.fr * t * 6.283)
        p[:, 2] = self.z0 + np.mod(p[:, 2] - self.z0, self.height)
        self.ob.data.vertices.foreach_set('co', p.ravel()); self.ob.data.update()


def grid(name, size, n, center=(0, 0, 0)):
    """Flat square grid mesh object with n x n quads."""
    xs = np.linspace(-size / 2, size / 2, n + 1)
    X, Y = np.meshgrid(xs, xs)
    V = np.stack([X.ravel() + center[0], Y.ravel() + center[1], np.full(X.size, center[2])], 1)
    i = np.arange(n * (n + 1)).reshape(n, n + 1)[:, :-1].ravel()
    F = np.stack([i, i + 1, i + n + 2, i + n + 1], 1)
    me = bpy.data.meshes.new(name); me.from_pydata(V.tolist(), [], F.tolist())
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def co(ob):
    a = np.zeros(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get('co', a)
    return a.reshape(-1, 3)


def set_co(ob, a):
    ob.data.vertices.foreach_set('co', np.ascontiguousarray(a, dtype=np.float64).ravel()); ob.data.update()


def vnormals(ob):
    a = np.zeros(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get('normal', a)
    return a.reshape(-1, 3)


def edges(ob):
    e = np.zeros(len(ob.data.edges) * 2, dtype=np.int64); ob.data.edges.foreach_get('vertices', e)
    return e.reshape(-1, 2)


def laplace(P, E, it=50, lam=0.5):
    """Umbrella smoothing of points P over edge list E."""
    P = P.copy(); n = len(P)
    cnt = np.zeros(n); np.add.at(cnt, E[:, 0], 1); np.add.at(cnt, E[:, 1], 1); cnt = np.maximum(cnt, 1)[:, None]
    for _ in range(it):
        s = np.zeros_like(P)
        np.add.at(s, E[:, 0], P[E[:, 1]]); np.add.at(s, E[:, 1], P[E[:, 0]])
        P += lam * (s / cnt - P)
    return P


def vnoise(p, scale, seed=0, octaves=6):
    rs = np.random.RandomState(seed); out = np.zeros(len(p))
    for _ in range(octaves):
        d = rs.normal(size=3); d /= np.linalg.norm(d)
        out += np.sin(p @ d * scale * rs.uniform(0.6, 1.8) + rs.uniform(0, 6.28))
    return out / octaves


def fbm2(x, y, seed=0, octaves=6, lac=2.0, gain=0.5, ridged=False):
    """Value-noise fBm on a 2D grid of coordinates (numpy arrays), in ~[-1, 1]."""
    rs = np.random.RandomState(seed)
    tot = np.zeros_like(x, dtype=float); amp = 1.0; f = 1.0; norm = 0
    for o in range(octaves):
        tab = rs.uniform(-1, 1, (256, 256))
        xi = np.floor(x * f).astype(int); yi = np.floor(y * f).astype(int)
        fx = x * f - xi; fy = y * f - yi
        fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
        a = tab[xi % 256, yi % 256]; b = tab[(xi + 1) % 256, yi % 256]
        c = tab[xi % 256, (yi + 1) % 256]; d = tab[(xi + 1) % 256, (yi + 1) % 256]
        v = a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy
        if ridged:
            v = 1 - 2 * np.abs(v)
        tot += v * amp; norm += amp; amp *= gain; f *= lac
    return tot / norm


def bake(ob, sc=None):
    """Return a new static mesh object from the evaluated (posed, modified) state of `ob`."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    me.transform(ob.matrix_world)
    nb = bpy.data.objects.new(ob.name + '_baked', me)
    (sc or bpy.context.scene).collection.objects.link(nb)
    for p in me.polygons:
        p.use_smooth = True
    return nb


def set_attr(ob, name, P):
    me = ob.data
    a = me.attributes.get(name) or me.attributes.new(name, 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', np.ascontiguousarray(P, dtype=np.float32).ravel())


def hide(ob, v=True):
    ob.hide_render = v; ob.hide_viewport = v


def blob(P, sigma=0.05, cell=0.012):
    """Heavily blurred copy of a point cloud (each point -> gaussian-weighted mean of its surroundings):
    turns a figure into a soft lump with the same vertex order."""
    lo = P.min(0) - 4 * sigma
    n = np.ceil((P.max(0) + 4 * sigma - lo) / cell).astype(int) + 1
    idx = np.floor((P - lo) / cell).astype(int)
    S = np.zeros((*n, 4))
    np.add.at(S, (idx[:, 0], idx[:, 1], idx[:, 2]), np.concatenate([P, np.ones((len(P), 1))], 1))
    r = int(3 * sigma / cell)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) * cell / sigma) ** 2); k /= k.sum()
    for ax in range(3):
        S = np.apply_along_axis(lambda v: np.convolve(v, k, 'same'), ax, S)
    # trilinear sampling of the blurred grid
    g = (P - lo) / cell - 0.5
    i0 = np.floor(g).astype(int); f = g - i0
    out = np.zeros((len(P), 4))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out += S[np.clip(i0[:, 0] + dx, 0, n[0] - 1), np.clip(i0[:, 1] + dy, 0, n[1] - 1),
                         np.clip(i0[:, 2] + dz, 0, n[2] - 1)] * w[:, None]
    return out[:, :3] / np.maximum(out[:, 3:4], 1e-9)


def beam(sc, apex, target, radius, color=(1.0, 0.8, 0.55), strength=1.0, name='beam_fx'):
    """Cheap god-ray: an emissive, transparent cone that fades at its silhouette and along its length."""
    apex = Vector(apex); target = Vector(target)
    L = (target - apex).length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=64, radius1=radius, radius2=radius * 0.06, depth=L)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    ob.location = (apex + target) / 2
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = (apex - target).to_track_quat('Z', 'Y')
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes
    for n in list(N):
        if n.type != 'OUTPUT_MATERIAL':
            N.remove(n)
    lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    p = N.new('ShaderNodeMath'); p.operation = 'POWER'; p.inputs[1].default_value = 2.2
    nt.links.new(lw.outputs['Facing'], p.inputs[0])
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs['Facing'], inv.inputs[1])
    p2 = N.new('ShaderNodeMath'); p2.operation = 'POWER'; p2.inputs[1].default_value = 2.5
    nt.links.new(inv.outputs[0], p2.inputs[0])
    tc = N.new('ShaderNodeTexCoord'); sep = N.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    g = N.new('ShaderNodeMapRange'); g.inputs[1].default_value = 0.0; g.inputs[2].default_value = 1.0
    g.inputs[3].default_value = 0.25; g.inputs[4].default_value = 1.0
    nt.links.new(sep.outputs['Z'], g.inputs[0])
    mu = N.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'
    nt.links.new(p2.outputs[0], mu.inputs[0]); nt.links.new(g.outputs[0], mu.inputs[1])
    st = N.new('ShaderNodeValue'); st.name = 'strength'; st.outputs[0].default_value = strength
    mu2 = N.new('ShaderNodeMath'); mu2.operation = 'MULTIPLY'
    nt.links.new(mu.outputs[0], mu2.inputs[0]); nt.links.new(st.outputs[0], mu2.inputs[1])
    e = N.new('ShaderNodeEmission'); e.inputs[0].default_value = (*color, 1)
    nt.links.new(mu2.outputs[0], e.inputs['Strength'])
    tr = N.new('ShaderNodeBsdfTransparent')
    add = N.new('ShaderNodeAddShader')
    nt.links.new(e.outputs[0], add.inputs[0]); nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], N['Material Output'].inputs['Surface'])
    ob.data.materials.append(m)
    ob.visible_shadow = False; ob.visible_diffuse = False; ob.visible_glossy = False
    return ob, st.outputs[0]


def lump(P, radii_scale=(1.5, 1.5, 1.5), seed=0, rough=0.08):
    """Map a figure's vertices onto a lumpy ellipsoid around its centroid (same vertex order).
    Vertices that were deep inside stay inside, so the lump has one clean outer skin."""
    c = P.mean(0); D = P - c
    rad = D.std(0) * np.array(radii_scale)
    q = np.linalg.norm(D / rad, axis=1)
    dirn = D / np.maximum(np.linalg.norm(D, axis=1, keepdims=True), 1e-9)
    rell = 1.0 / np.linalg.norm(dirn / rad, axis=1)
    k = 0.62 + 0.38 * np.clip(q / np.percentile(q, 97), 0, 1)
    k *= 1 + rough * vnoise(dirn, 3.0, seed, 5)
    return c + dirn * (rell * k)[:, None]


def terrain(name, xr, yr, nx, ny, height_fn):
    """Heightfield mesh. height_fn(X, Y) -> Z (numpy grids)."""
    xs = np.linspace(xr[0], xr[1], nx + 1); ys = np.linspace(yr[0], yr[1], ny + 1)
    X, Y = np.meshgrid(xs, ys)
    Z = height_fn(X, Y)
    V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    i = (np.arange(ny)[:, None] * (nx + 1) + np.arange(nx)[None, :]).ravel()
    F = np.stack([i, i + 1, i + nx + 2, i + nx + 1], 1)
    me = bpy.data.meshes.new(name); me.from_pydata(V.tolist(), [], F.tolist())
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def float_image(name, arr):
    """numpy (H, W, 3|4) float array -> Blender image (linear, non-colour)."""
    h, w = arr.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=False, float_buffer=True)
    px = np.ones((h, w, 4), dtype=np.float32); px[..., :arr.shape[2]] = arr
    im.pixels.foreach_set(px.ravel())
    path = f'/tmp/_fximg_{name}_{os.getpid()}.exr'
    im.filepath_raw = path; im.file_format = 'OPEN_EXR'; im.save()
    bpy.data.images.remove(im)
    im = bpy.data.images.load(path); im.colorspace_settings.name = 'Non-Color'
    return im


def bolt_path(rs, p0, p1, levels=7, jag=0.18):
    """Jagged lightning polyline from p0 to p1 (midpoint displacement in the XZ plane)."""
    pts = [np.array(p0, float), np.array(p1, float)]
    amp = np.linalg.norm(pts[1] - pts[0]) * jag
    for _ in range(levels):
        new = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            m = (a + b) / 2 + np.array([rs.normal() * amp, rs.normal() * amp * 0.15, rs.normal() * amp * 0.25])
            new += [m, b]
        pts = new; amp *= 0.55
    return np.array(pts)


def ribbon(name, paths, mat, facing=(0, -1, 0)):
    """Camera-facing ribbons along polylines. paths: list of (points Nx3, width_start, width_end).
    Three vertices across; point attribute 'a' is 1 on the centre line and 0 at the edges (soft falloff)."""
    V, F, A = [], [], []
    fdir = np.array(facing, float)
    for pts, w0, w1 in paths:
        n = len(pts); base = len(V)
        tan = np.gradient(pts, axis=0); side = np.cross(tan, fdir)
        side /= np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-9)
        w = np.linspace(w0, w1, n)[:, None] * 0.5
        for a_, c_, b_ in zip(pts - side * w, pts, pts + side * w):
            V += [tuple(a_), tuple(c_), tuple(b_)]; A += [0.0, 1.0, 0.0]
        for i in range(n - 1):
            k = base + 3 * i
            F += [(k, k + 1, k + 4, k + 3), (k + 1, k + 2, k + 5, k + 4)]
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F)
    at = me.attributes.new('a', 'FLOAT', 'POINT'); at.data.foreach_set('value', A)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    ob.visible_shadow = False
    return ob


def glow_mat(name, color, strength=1.0, falloff=0.0):
    """Additive emissive material (emission + transparent) with a 'strength' value node.
    falloff > 0: strength is multiplied by attribute 'a' ** falloff (soft ribbon edges)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes
    for n in list(N):
        if n.type != 'OUTPUT_MATERIAL':
            N.remove(n)
    st = N.new('ShaderNodeValue'); st.name = 'strength'; st.outputs[0].default_value = strength
    e = N.new('ShaderNodeEmission'); e.inputs[0].default_value = (*color, 1)
    if falloff:
        at = N.new('ShaderNodeAttribute'); at.attribute_name = 'a'
        pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = falloff
        nt.links.new(at.outputs['Fac'], pw.inputs[0])
        mu = N.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'
        nt.links.new(pw.outputs[0], mu.inputs[0]); nt.links.new(st.outputs[0], mu.inputs[1])
        nt.links.new(mu.outputs[0], e.inputs['Strength'])
    else:
        nt.links.new(st.outputs[0], e.inputs['Strength'])
    tr = N.new('ShaderNodeBsdfTransparent'); add = N.new('ShaderNodeAddShader')
    nt.links.new(e.outputs[0], add.inputs[0]); nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], N['Material Output'].inputs['Surface'])
    return m


def _smooth_path(p, k=9):
    ker = np.ones(k) / k
    q = np.stack([np.convolve(np.pad(p[:, i], k // 2, mode='edge'), ker, 'valid') for i in range(3)], 1)
    return q


def lightning(sc, rs, top, bottom, width=0.25, branches=6, color=(0.6, 0.75, 1.0), name='bolt'):
    """Branching lightning bolt with soft halo ribbons. Returns (objects, set_intensity(0..1), main path)."""
    main = bolt_path(rs, top, bottom)
    sm = _smooth_path(main, 9); sm2 = _smooth_path(main, 25)
    core, halo, halo2 = [(main, width, width * 0.6)], [(sm, width * 9, width * 5)], [(sm2, width * 45, width * 28)]
    L = np.linalg.norm(np.array(bottom) - np.array(top))
    for _ in range(branches):
        i = rs.randint(len(main) // 8, len(main) * 3 // 4)
        d = np.array([rs.choice([-1, 1]) * rs.uniform(0.25, 0.7), 0, -rs.uniform(0.25, 0.6)]) * L * rs.uniform(0.25, 0.5)
        br = bolt_path(rs, main[i], main[i] + d, levels=5, jag=0.22)
        core.append((br, width * 0.45, width * 0.08)); halo.append((_smooth_path(br, 5), width * 3.5, width * 0.6))
    mats = [glow_mat(name + '_core', (1, 1, 1), 0, 0.6), glow_mat(name + '_halo', color, 0, 2.0), glow_mat(name + '_halo2', color, 0, 2.5)]
    obs = [ribbon(name + '_core', core, mats[0]), ribbon(name + '_halo', halo, mats[1]), ribbon(name + '_halo2', halo2, mats[2])]
    obs[1].location.y += 0.05; obs[2].location.y += 0.1

    def set_i(v):
        for m, k in zip(mats, (120.0, 2.2, 0.35)):
            m.node_tree.nodes['strength'].outputs[0].default_value = v * k
        for o in obs:
            o.hide_render = v <= 0.001
    return obs, set_i, main


def shake(cam, f, amp, seed=0):
    """Add handheld/earthquake shake to a camera that has already been placed this frame."""
    rs = np.random.RandomState(seed)
    ph = rs.uniform(0, 6.28, (3, 4)); fr = rs.uniform(0.6, 2.4, (3, 4))
    t = f / 24.0
    d = [float(np.sum(np.sin(ph[i] + fr[i] * t * 6.283 * np.array([1, 2.3, 4.1, 7.7])) * [1, 0.5, 0.3, 0.2])) for i in range(3)]
    from mathutils import Quaternion
    cam.rotation_quaternion = cam.rotation_quaternion @ Quaternion((1, 0, 0), d[0] * amp) @ Quaternion((0, 1, 0), d[1] * amp) \
        @ Quaternion((0, 0, 1), d[2] * amp * 0.6)


def box(name, size, loc, mat=None, bevel=0.02, subdiv=0, noise=0.0, seed=0):
    """Soft-edged clay block (bevelled box, optionally lumpy)."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=3, profile=0.5, affect='EDGES')
    if subdiv:
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=subdiv, use_grid_fill=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    if noise:
        P = co(ob); N_ = vnormals(ob)
        set_co(ob, P + N_ * (vnoise(P, 9.0 / max(size), seed) * noise)[:, None])
    for p in me.polygons:
        p.use_smooth = True
    ob.location = loc
    if mat:
        ob.data.materials.append(mat)
    return ob


def lathe(name, profile, loc, mat=None, segments=48):
    """Surface of revolution from a list of (radius, z) pairs."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segments), r * math.sin(2 * math.pi * i / segments), z))
                      for i in range(segments)])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(segments):
            bm.faces.new((a[i], a[(i + 1) % segments], b[(i + 1) % segments], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    if mat:
        ob.data.materials.append(mat)
    return ob


def text(name, body, size, loc, rot, mat, extrude=0.002):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    ob = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot
    ob.data.materials.append(mat)
    return ob


def tree(name, loc, kind, seed=0, height=3.2):
    """Hand-modelled clay tree. kind: 'blossom' | 'olive' | 'ochre' | 'bare'."""
    rs = np.random.RandomState(seed)
    trunk_m = K.clay(name + '_trunk', 'umber', wet=0.1, coords='object', scale=1.5, bump=1.6)
    h0 = height * 0.5
    prof = [(0.0, 0.0), (0.22, 0.0), (0.15, 0.25), (0.11, h0 * 0.6), (0.09, h0), (0.0, h0 + 0.02)]
    obs = [lathe(name + '_trunk', prof, loc, trunk_m, segments=16)]
    P = co(obs[0]); P[:, 0] += 0.06 * np.sin(P[:, 2] * 2.1 + seed); P[:, 1] += 0.05 * np.cos(P[:, 2] * 1.7 + seed)
    set_co(obs[0], P)
    bm = bmesh.new()
    top = Vector((0.06 * math.sin(h0 * 2.1 + seed), 0.05 * math.cos(h0 * 1.7 + seed), h0))
    # boughs
    tips = []
    for i in range(7):
        a = rs.uniform(0, 6.28); el = rs.uniform(0.5, 1.2)
        d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el) * 0.8, math.sin(el)))
        L = height * rs.uniform(0.25, 0.42)
        tip = top + d * L; tips.append(tip)
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.055, radius2=0.018, depth=L)
        M_ = Matrix.Translation((top + tip) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=M_, verts=r['verts'])
    me = bpy.data.meshes.new(name + '_boughs'); bm.to_mesh(me); bm.free()
    b = bpy.data.objects.new(name + '_boughs', me); bpy.context.scene.collection.objects.link(b)
    b.location = loc; b.data.materials.append(trunk_m); obs.append(b)
    if kind != 'bare':
        bm = bmesh.new()
        n = {'blossom': 16, 'olive': 22, 'ochre': 11}[kind]
        for i in range(n):
            c = tips[i % len(tips)] + Vector(rs.normal(size=3)) * 0.28
            r = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rs.uniform(0.28, 0.5) * (0.8 if kind == 'ochre' else 1))
            bmesh.ops.transform(bm, matrix=Matrix.Translation(c), verts=r['verts'])
        me = bpy.data.meshes.new(name + '_crown'); bm.to_mesh(me); bm.free()
        c_ = bpy.data.objects.new(name + '_crown', me); bpy.context.scene.collection.objects.link(c_)
        m = c_.modifiers.new('rm', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = 0.05; m.use_smooth_shade = True
        C.apply_modifier(c_, 'rm')
        Pc = co(c_); Nc = vnormals(c_)
        set_co(c_, Pc + Nc * (vnoise(Pc, 7.0, seed, 5) * 0.06)[:, None])
        for p in c_.data.polygons:
            p.use_smooth = True
        c_.location = loc
        c_.data.materials.append(K.clay(name + '_crown', kind, wet=0.05, coords='object', scale=1.2, bump=1.8))
        obs.append(c_)
    return obs


def emit_plane(name, size, loc, rot, color=(1, 1, 1), strength=1.0, gradient=True):
    """Emissive backdrop with a vertical gradient (brighter at the horizon). Returns (object, emission node)."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.object; ob.name = name
    ob.scale = (size[0], size[1], 1); ob.rotation_euler = [math.radians(a) for a in rot]; ob.location = loc
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes
    for n in list(N):
        if n.type != 'OUTPUT_MATERIAL':
            N.remove(n)
    e = N.new('ShaderNodeEmission'); e.inputs[0].default_value = (*color, 1); e.inputs[1].default_value = strength
    if gradient:
        tc = N.new('ShaderNodeTexCoord'); sp = N.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['UV'], sp.inputs[0])
        mr = N.new('ShaderNodeMapRange'); mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 1.0
        mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.12
        nt.links.new(sp.outputs['Y'], mr.inputs[0])
        st = N.new('ShaderNodeValue'); st.name = 'strength'; st.outputs[0].default_value = strength
        mu = N.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'
        nt.links.new(mr.outputs[0], mu.inputs[0]); nt.links.new(st.outputs[0], mu.inputs[1])
        nt.links.new(mu.outputs[0], e.inputs[1])
    nt.links.new(e.outputs[0], N['Material Output'].inputs['Surface'])
    ob.data.materials.append(m)
    ob.visible_shadow = False
    return ob, e


class Rain:
    """Rain as additive streaks: N thin quads falling through a box, wrapped vertically.
    update(frame, intensity 0..1, speed m/s). Streak length follows speed (motion blur at 1/48 s)."""

    def __init__(self, sc, n, lo, hi, width=0.004, seed=0, color=(0.75, 0.82, 1.0), strength=2.0, slant=(0.06, 0.0),
                 facing=(0, -1, 0)):
        rs = np.random.RandomState(seed)
        self.lo = np.array(lo, float); self.hi = np.array(hi, float); self.n = n
        self.p0 = self.lo + rs.uniform(0, 1, (n, 3)) * (self.hi - self.lo)
        self.sp = rs.uniform(0.8, 1.2, n); self.w = width * rs.uniform(0.6, 1.4, n)
        self.slant = np.array([slant[0], slant[1], 0.0])
        f = np.array(facing, float); self.side = np.cross([0, 0, 1.0], f); self.side /= np.linalg.norm(self.side)
        me = bpy.data.meshes.new('rain')
        me.from_pydata([(0, 0, 0)] * (4 * n), [], [(4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3) for i in range(n)])
        self.ob = bpy.data.objects.new('rain', me); sc.collection.objects.link(self.ob)
        self.mat = glow_mat('rain', color, strength)
        self.ob.data.materials.append(self.mat)
        self.ob.visible_shadow = False; self.ob.visible_diffuse = False; self.ob.visible_glossy = False

    def update(self, frame, intensity=1.0, speed=8.0, t=None):
        t = frame / 24.0 if t is None else t
        H = self.hi[2] - self.lo[2]
        p = self.p0.copy()
        p[:, 2] = self.lo[2] + np.mod(self.p0[:, 2] - self.lo[2] - speed * self.sp * t, H)
        p[:, :2] += (self.slant[:2] * (self.hi[2] - p[:, 2])[:, None])
        L = np.maximum(0.012, speed * self.sp / 48.0)
        d = np.array([-self.slant[0], -self.slant[1], 1.0]); d /= np.linalg.norm(d)
        top = p + d * L[:, None]
        s = self.side * self.w[:, None] * 0.5
        V = np.stack([p - s, p + s, top + s, top - s], 1)
        k = int(self.n * (1 - min(1.0, max(0.0, intensity))))
        if k:
            V[:k] = 0
        self.ob.data.vertices.foreach_set('co', V.reshape(-1)); self.ob.data.update()


def rays(sc, center, n, length, width, seed=0, color=(1.0, 0.7, 0.25), spread=1.25, name='rays'):
    """Fan of soft light rays rising from a point (additive ribbons). Returns (object, strength socket, setter)."""
    rs = np.random.RandomState(seed); c = np.array(center, float)
    dirs = []
    for i in range(n):
        a = (i + rs.uniform(-0.3, 0.3)) / n * 2 * math.pi
        el = rs.uniform(math.pi / 2 - spread, math.pi / 2 - 0.15)
        dirs.append(np.array([math.cos(a) * math.cos(el), math.sin(a) * math.cos(el) * 0.5, math.sin(el)]))
    Ls = length * rs.uniform(0.5, 1.0, n); Ws = width * rs.uniform(0.5, 1.5, n)
    mat = glow_mat(name, color, 0.0, falloff=1.6)

    def paths(k):
        return [(np.array([c, c + d * (L * k * 0.5), c + d * (L * k)]), w * 0.3, w * (0.4 + k)) for d, L, w in zip(dirs, Ls, Ws)]
    ob = ribbon(name, paths(1.0), mat)
    base = co(ob).copy()

    def set_(strength, grow=1.0):
        mat.node_tree.nodes['strength'].outputs[0].default_value = strength
        set_co(ob, c + (base - c) * grow)
        ob.hide_render = strength <= 1e-4
    return ob, set_


def storm_sky(name, size, loc, bolt_uv=(0.44, 0.55), color=(0.55, 0.68, 1.0), ambient=0.05, seed=3):
    """Emissive storm-cloud backdrop lit from within by lightning. Returns (object, flash socket)."""
    H, W = 384, 1024
    yy, xx = np.mgrid[0:H, 0:W]
    cl = fbm2(xx / 150.0, yy / 70.0, seed=seed, octaves=6) * 0.5 + 0.5
    cl = np.clip((cl - 0.25) * 1.6, 0, 1) ** 1.5
    bx, by = bolt_uv[0] * W, bolt_uv[1] * H
    glow = np.exp(-(((xx - bx) / (0.22 * W)) ** 2 + ((yy - by) / (0.6 * H)) ** 2)) + 0.12
    img = float_image(name, np.stack([cl, glow * (0.12 + 0.88 * cl ** 1.5), cl * 0 + 1], 2))
    bpy.ops.mesh.primitive_plane_add(size=1)
    sky = bpy.context.object; sky.name = name
    sky.scale = (size[0], size[1], 1); sky.rotation_euler = (math.radians(90), 0, 0); sky.location = loc
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes
    for n in list(N):
        if n.type != 'OUTPUT_MATERIAL':
            N.remove(n)
    tex = N.new('ShaderNodeTexImage'); tex.image = img; tex.extension = 'EXTEND'
    sep = N.new('ShaderNodeSeparateColor'); nt.links.new(tex.outputs['Color'], sep.inputs[0])
    fl = N.new('ShaderNodeValue'); fl.name = 'flash'
    m1 = N.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; nt.links.new(sep.outputs[1], m1.inputs[0]); nt.links.new(fl.outputs[0], m1.inputs[1])
    m2 = N.new('ShaderNodeMath'); m2.operation = 'MULTIPLY_ADD'; nt.links.new(sep.outputs[0], m2.inputs[0])
    m2.inputs[1].default_value = ambient; nt.links.new(m1.outputs[0], m2.inputs[2])
    em = N.new('ShaderNodeEmission'); em.inputs[0].default_value = (*color, 1)
    nt.links.new(m2.outputs[0], em.inputs['Strength']); nt.links.new(em.outputs[0], N['Material Output'].inputs['Surface'])
    sky.data.materials.append(m)
    sky.visible_shadow = False
    return sky, fl.outputs[0]


def rain_curtain(name, size, loc, seed=0, strength=0.25, color=(0.7, 0.8, 1.0), tiles=(6, 2)):
    """Distant rain: a big additive sheet of vertical streaks that scrolls downward. Returns (object, set(t, k))."""
    rs = np.random.RandomState(seed)
    H, W = 512, 512
    img = np.zeros((H, W))
    for _ in range(900):
        x = rs.randint(0, W); y = rs.randint(0, H); L = rs.randint(20, 90); v = rs.uniform(0.2, 1.0)
        ys = (y + np.arange(L)) % H
        img[ys, x] = np.maximum(img[ys, x], v * np.sin(np.linspace(0, math.pi, L)))
    im = float_image(name, np.stack([img, img, img], 2))
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.object; ob.name = name
    ob.scale = (size[0], size[1], 1); ob.rotation_euler = (math.radians(90), 0, 0); ob.location = loc
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes
    for n in list(N):
        if n.type != 'OUTPUT_MATERIAL':
            N.remove(n)
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.name = 'map'
    mp.inputs['Scale'].default_value = (tiles[0], tiles[1], 1); mp.inputs['Rotation'].default_value = (0, 0, 0.08)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    tex = N.new('ShaderNodeTexImage'); tex.image = im; nt.links.new(mp.outputs[0], tex.inputs['Vector'])
    st = N.new('ShaderNodeValue'); st.name = 'strength'; st.outputs[0].default_value = strength
    mu = N.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Color'], mu.inputs[0]); nt.links.new(st.outputs[0], mu.inputs[1])
    e = N.new('ShaderNodeEmission'); e.inputs[0].default_value = (*color, 1); nt.links.new(mu.outputs[0], e.inputs['Strength'])
    tr = N.new('ShaderNodeBsdfTransparent'); add = N.new('ShaderNodeAddShader')
    nt.links.new(e.outputs[0], add.inputs[0]); nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], N['Material Output'].inputs['Surface'])
    ob.data.materials.append(m)
    ob.visible_shadow = False; ob.visible_diffuse = False; ob.visible_glossy = False

    def set_(t, k=1.0, speed=1.6):
        mp.inputs['Location'].default_value = (seed * 0.37, t * speed, 0)
        st.outputs[0].default_value = strength * k
    return ob, set_


def village(name, n, xr, yr, height_fn, seed=0, lit=0.45):
    """Scatter of small flat-roofed clay houses, some with glowing windows. One mesh for walls, one for windows."""
    rs = np.random.RandomState(seed)
    bm = bmesh.new(); wm = bmesh.new()
    for i in range(n):
        x = rs.uniform(*xr); y = rs.uniform(*yr)
        w, d, h = rs.uniform(1.0, 2.2), rs.uniform(1.0, 2.0), rs.uniform(0.9, 2.2)
        z = float(height_fn(np.array([[x]]), np.array([[y]]))[0, 0])
        r = bmesh.ops.create_cube(bm, size=1.0)
        rot = Matrix.Rotation(rs.uniform(-0.3, 0.3), 4, 'Z')
        Mx = Matrix.Translation((x, y, z + h / 2 - 0.15)) @ rot @ Matrix.Diagonal((w, d, h, 1))
        bmesh.ops.transform(bm, matrix=Mx, verts=r['verts'])
        if rs.uniform() < 0.3:
            r2 = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=min(w, d) * 0.42)
            bmesh.ops.transform(bm, matrix=Matrix.Translation((x, y, z + h - 0.15)) @ Matrix.Diagonal((1, 1, 0.75, 1)), verts=r2['verts'])
        if rs.uniform() < lit:
            for k in range(rs.randint(1, 3)):
                q = bmesh.ops.create_grid(wm, x_segments=1, y_segments=1, size=0.11)
                off = Vector((rs.uniform(-0.3, 0.3) * w, -d / 2 - 0.012, rs.uniform(-0.15, 0.25) * h))
                Mw = Matrix.Translation((x, y, z + h / 2 - 0.15)) @ rot @ Matrix.Translation(off) @ Matrix.Rotation(math.radians(90), 4, 'X') \
                    @ Matrix.Diagonal((1.0, 1.5, 1, 1))
                bmesh.ops.transform(wm, matrix=Mw, verts=q['verts'])
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.05, segments=2, affect='EDGES')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    me2 = bpy.data.meshes.new(name + '_win'); wm.to_mesh(me2); wm.free()
    win = bpy.data.objects.new(name + '_win', me2); bpy.context.scene.collection.objects.link(win)
    win.data.materials.append(K.emission(name + '_win', (1.0, 0.55, 0.2), 14.0))
    return ob, win
