"""Clay garments sculpted procedurally around a MakeHuman figure: robe, headscarf, hair, swaddle.
Every garment is a fused solid (voxel remesh), skinned to the figure's rig by nearest-weight transfer."""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, kdtree
import mhlib as M
import common as C


def _W():
    """Dense weight matrix (n_verts x n_bones) and bone list for the base mesh."""
    if 'W' not in M._cache:
        b = M._base()
        bones = list(b['skel']['bones'].keys())
        bi = {n: k for k, n in enumerate(bones)}
        W = np.zeros((len(b['V']), len(bones)), dtype=np.float32)
        for bn, wl in b['weights'].items():
            if wl:
                a = np.array(wl)
                W[a[:, 0].astype(int), bi[bn]] = a[:, 1]
        s = W.sum(1, keepdims=True); s[s == 0] = 1
        M._cache['W'] = (W / s, bones, bi)
    return M._cache['W']


def descendants(root):
    sk = M._base()['skel']['bones']
    out, grew = {root}, True
    while grew:
        grew = False
        for n, d in sk.items():
            if d['parent'] in out and n not in out:
                out.add(n); grew = True
    return out


def bone_mask(names):
    """Per base-vertex summed weight of a set of bones (prefix match allowed with '*')."""
    W, bones, bi = _W()
    sel = []
    for n in names:
        if n.endswith('*'):
            sel += [k for k, b in enumerate(bones) if b.startswith(n[:-1])]
        else:
            sel.append(bi[n])
    return W[:, sorted(set(sel))].sum(1)


HEAD_BONES = None


def head_mask():
    global HEAD_BONES
    if HEAD_BONES is None:
        HEAD_BONES = sorted(descendants('head'))
    return bone_mask(HEAD_BONES)


def strip_body(h, keep=('head', 'hands', 'feet'), neck=True, forearm=0.5, shin=0.5):
    """Delete body faces hidden under garments. Keeps head(+neck), hands, feet."""
    m = np.zeros(len(M._base()['V']))
    if 'head' in keep:
        m += head_mask()
        if neck:
            m += bone_mask(['neck*', 'spine01', 'clavicle*']) * 1.0
    if 'hands' in keep:
        m += bone_mask(['wrist*', 'finger*', 'metacarpal*']) + bone_mask(['lowerarm02*']) * (1.2 if forearm else 0)
        if forearm > 0.6:
            m += bone_mask(['lowerarm01*'])
    if 'feet' in keep:
        m += bone_mask(['foot*', 'toe*']) + bone_mask(['lowerleg02*']) * (1.2 if shin else 0)
        if shin > 0.6:
            m += bone_mask(['lowerleg01*'])
    if 'all' in keep:
        m += 1
    ob = h.body
    idx = np.zeros(len(ob.data.vertices), dtype=int)
    ob.data.attributes['mh_index'].data.foreach_get('value', idx)
    keepv = m[idx] > 0.5
    bm = bmesh.new(); bm.from_mesh(ob.data)
    dele = [f for f in bm.faces if not any(keepv[v.index] for v in f.verts)]
    bmesh.ops.delete(bm, geom=dele, context='FACES')
    bm.to_mesh(ob.data); bm.free()


# --------------------------------------------------------------------------------------
def _new_obj(name, verts, faces, col=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    ob = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(ob)
    return ob


def _closed_part(Vb, faces):
    """Sub-mesh of base faces with holes capped. Returns (verts, faces, base_index)."""
    used = sorted({i for f in faces for i in f})
    remap = {v: k for k, v in enumerate(used)}
    bm = bmesh.new()
    vs = [bm.verts.new(Vb[i]) for i in used]
    for f in faces:
        try:
            bm.faces.new([vs[remap[i]] for i in f])
        except ValueError:
            pass
    bm.normal_update()
    be = [e for e in bm.edges if e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=be, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.verts.index_update()
    V = np.array([v.co[:] for v in bm.verts]); F = [[v.index for v in f.verts] for f in bm.faces]
    N = np.array([v.normal[:] for v in bm.verts])
    bm.free()
    return V, F, np.array(used), N


def _hull(points, inflate=0.0, col=None, name='hull'):
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    r = bmesh.ops.convex_hull(bm, input=bm.verts)
    junk = list({g for g in r.get('geom_interior', []) + r.get('geom_unused', []) if isinstance(g, bmesh.types.BMVert)})
    bmesh.ops.delete(bm, geom=junk, context='VERTS')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    if inflate:
        for v in bm.verts:
            v.co += v.normal * inflate
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(ob)
    return ob


def _join(obs):
    with bpy.context.temp_override(active_object=obs[0], object=obs[0], selected_objects=obs, selected_editable_objects=obs):
        bpy.ops.object.join()
    return obs[0]


def _voxel(ob, size, smooth=6, factor=0.6):
    m = ob.modifiers.new('rm', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = size; m.adaptivity = 0.0
    m.use_smooth_shade = True
    C.apply_modifier(ob, 'rm')
    if smooth:
        m = ob.modifiers.new('sm', 'SMOOTH'); m.factor = factor; m.iterations = smooth
        C.apply_modifier(ob, 'sm')
    for p in ob.data.polygons:
        p.use_smooth = True


def _co(ob):
    a = np.zeros(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get('co', a)
    return a.reshape(-1, 3)


def _set_co(ob, a):
    ob.data.vertices.foreach_set('co', np.asarray(a).ravel()); ob.data.update()


def _normals(ob):
    a = np.zeros(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get('normal', a)
    return a.reshape(-1, 3)


def skin(h, ob, src_pos, src_idx, k=4, limit=4, blur=0):
    """Skin `ob` to h.arm: weights interpolated from nearest source points (base vertex indices src_idx)."""
    W, bones, bi = _W()
    kd = kdtree.KDTree(len(src_pos))
    for i, p in enumerate(src_pos):
        kd.insert(p, i)
    kd.balance()
    co = _co(ob)
    n = len(co)
    acc = np.zeros((n, len(bones)), dtype=np.float32)
    for vi in range(n):
        res = kd.find_n(co[vi], k)
        for _, j, d in res:
            acc[vi] += W[src_idx[j]] / (d * d + 1e-6)
    if blur:
        # Laplacian blur of weights over mesh edges (softens seams of nearest transfer)
        e = np.zeros(len(ob.data.edges) * 2, dtype=int); ob.data.edges.foreach_get('vertices', e); e = e.reshape(-1, 2)
        for _ in range(blur):
            s = np.zeros_like(acc); c = np.zeros(n)
            np.add.at(s, e[:, 0], acc[e[:, 1]]); np.add.at(s, e[:, 1], acc[e[:, 0]])
            np.add.at(c, e[:, 0], 1); np.add.at(c, e[:, 1], 1)
            acc = 0.5 * acc + 0.5 * s / np.maximum(c, 1)[:, None]
    # keep the strongest `limit` bones
    order = np.argsort(-acc, 1)[:, :limit]
    rows = np.arange(n)[:, None]
    top = acc[rows, order]
    top /= np.maximum(top.sum(1, keepdims=True), 1e-9)
    for b in np.unique(order):
        sel = (order == b)
        vv = np.nonzero(sel.any(1))[0]
        ww = (top * sel).sum(1)[vv]
        vg = ob.vertex_groups.new(name=bones[b])
        for q in np.unique(np.round(ww, 2)):
            if q <= 0.005:
                continue
            vg.add([int(x) for x in vv[np.round(ww, 2) == q]], float(q), 'REPLACE')
    m = ob.modifiers.new('Armature', 'ARMATURE'); m.object = h.arm
    ob.parent = h.arm
    return ob


def _noise3(p, scale, seed=0):
    """Cheap smooth value noise via sum of sines (deterministic, vectorised)."""
    rs = np.random.RandomState(seed)
    out = np.zeros(len(p))
    for _ in range(6):
        d = rs.normal(size=3); d /= np.linalg.norm(d)
        f = scale * rs.uniform(0.6, 1.8)
        out += np.sin(p @ d * f + rs.uniform(0, 6.28))
    return out / 6


# --------------------------------------------------------------------------------------
def make_robe(h, hem=0.035, flare=0.38, inflate=0.016, sleeve=0.022, voxel=0.0065, folds=0.012, nfolds=11,
              loose=0.5, skirt=True, name=None, seed=1):
    """Long loose dress / thobe: fused solid of torso+sleeves (tights helper) and a flared skirt helper."""
    b = M._base(); Vb = h.Vb
    legw = bone_mask(['upperleg*', 'lowerleg*', 'foot*', 'toe*'])
    tf = [f for f, _ in b['groups']['helper-tights'] if not all(legw[i] > (0.5 if skirt else 2) for i in f)]
    V1, F1, I1, N1 = _closed_part(Vb, tf)
    armw = bone_mask(['upperarm*', 'lowerarm*', 'shoulder*'])
    pad = np.full(len(V1), inflate)
    known = I1 >= 0
    aw = armw[I1]
    pad = inflate + (sleeve - inflate) * np.clip(aw * 1.5, 0, 1)
    # loosen the waist/bust: push torso towards its vertical-axis-distance average
    V1 = V1 + N1 * pad[:, None]
    parts = [_new_obj('robe_top', V1, F1, h.col)]
    src_pos = [V1]; src_idx = [I1]
    zc = 0
    if skirt:
        sf = [f for f, _ in b['groups']['helper-skirt']]
        V2, F2, I2, N2 = _closed_part(Vb, sf)
        zmin, zmax = V2[:, 2].min(), V2[:, 2].max()
        top = V2[V2[:, 2] > zmax - 0.03]
        cx, cy = top[:, 0].mean(), top[:, 1].mean()
        t = (V2[:, 2] - zmin) / (zmax - zmin)
        s = 1 + flare * (1 - t) ** 1.4 + 0.10 * t
        V2[:, 0] = cx + (V2[:, 0] - cx) * s
        V2[:, 1] = cy + (V2[:, 1] - cy) * (s + 0.06 * (1 - t))
        V2[:, 2] = hem + (V2[:, 2] - zmin) * (zmax + 0.03 - hem) / (zmax - zmin)
        parts.append(_new_obj('robe_skirt', V2, F2, h.col))
        src_pos.append(V2); src_idx.append(I2)
        zc = zmax
    ob = _join(parts)
    ob.name = name or h.name + '_robe'
    _voxel(ob, voxel, smooth=10)
    co = _co(ob); nr = _normals(ob)
    if skirt and folds:
        t = np.clip((zc - co[:, 2]) / (zc - hem), 0, 1)
        th = np.arctan2(co[:, 1] - cy, co[:, 0] - cx)
        warp = _noise3(co * [1, 1, 0.5], 9, seed) * 1.6
        f = np.sin(nfolds * th + warp) * 0.65 + np.sin((nfolds * 2 + 3) * th - 2 * warp + 1.3) * 0.35
        f = np.sign(f) * np.abs(f) ** 0.8
        amp = folds * t ** 1.3
        rad = np.stack([np.cos(th), np.sin(th), np.zeros_like(th)], 1)
        co = co + rad * (f * amp)[:, None]
    # soft lumps of hand-shaped clay
    co = co + nr * (_noise3(co, 22, seed + 5) * 0.0025)[:, None]
    _set_co(ob, co)
    skin(h, ob, np.vstack(src_pos), np.concatenate(src_idx), blur=3)
    h.objs.append(ob)
    return ob


def face_frame(h):
    """Landmarks of the head in rest pose (Blender space)."""
    sk = M._base()['skel']
    J = lambda j: h.Vb[sk['joints'][j]].mean(0)
    eye = 0.5 * (J(sk['bones']['eye.L']['head']) + J(sk['bones']['eye.R']['head']))
    hm = head_mask()[:M.N_BODY] > 0.6
    P = h.Vb[:M.N_BODY][hm]
    return dict(eye=eye, top=P[:, 2].max(), front=P[:, 1].min(), back=P[:, 1].max(),
                half=np.abs(P[:, 0]).max(), P=P,
                shoulder=J(sk['bones']['upperarm01.L']['head']))


def make_scarf(h, inflate=0.014, voxel=0.005, drop=0.13, face_w=0.070, face_up=0.060, face_down=0.118, cut_depth=0.085,
               name=None, seed=3, folds=0.004):
    """Loose headscarf (hijab): fused solid of a head wrap and a drape over the shoulders, with a face opening."""
    fr = face_frame(h); eye = fr['eye']; P = fr['P']; sh = fr['shoulder']
    Vb = h.Vb[:M.N_BODY]
    zc = eye[2] + 0.5 * (face_up - face_down)          # face oval centre
    hz = 0.5 * (face_up + face_down)
    in_oval = ((P[:, 0] / face_w) ** 2 + ((P[:, 2] - zc) / hz) ** 2 < 1.0) & (P[:, 1] < eye[1] + 0.035)
    crani = P[~in_oval]
    wrap = _hull(crani, inflate=inflate, col=h.col, name='scarf_wrap')
    # drape: neck + shoulders + upper chest/back
    chin_z = eye[2] - face_down
    zlim = sh[2] - drop
    tilt = zlim + 0.35 * (Vb[:, 1] - sh[1]) * 0 - 0.04 * (Vb[:, 1] < sh[1])
    sel = (Vb[:, 2] < chin_z + 0.02) & (Vb[:, 2] > tilt) & (np.abs(Vb[:, 0]) < abs(sh[0]) * 0.93) \
        & (head_mask()[:M.N_BODY] < 0.5)
    jaw = P[(P[:, 2] < chin_z + 0.035)]
    drape = _hull(np.vstack([Vb[sel], jaw]), inflate=inflate + 0.012, col=h.col, name='scarf_drape')
    ob = _join([wrap, drape])
    ob.name = name or h.name + '_scarf'
    _voxel(ob, voxel, smooth=12, factor=0.7)
    # face opening: cut, then re-voxelise so the rim becomes a soft rolled clay edge
    cut = bpy.data.meshes.new('cut'); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=1, radius2=1, depth=1)
    for v in bm.verts:
        x, y, z = v.co
        k = 1.0 + 0.10 * (z + 0.5)                       # opening widens slightly towards the front
        v.co = Vector((x * face_w * k, eye[1] + cut_depth - (z + 0.5) * 0.5, zc + y * hz * k))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(cut); bm.free()
    cob = bpy.data.objects.new('cut', cut); bpy.context.scene.collection.objects.link(cob)
    m = ob.modifiers.new('bool', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cob; m.solver = 'EXACT'
    C.apply_modifier(ob, 'bool')
    bpy.data.objects.remove(cob)
    _voxel(ob, voxel, smooth=8, factor=0.6)
    co = _co(ob); nr = _normals(ob)
    # gentle drape folds running down from the crown
    th = np.arctan2(co[:, 1] - eye[1] - 0.06, co[:, 0])
    dz = np.clip((fr['top'] - co[:, 2]) / (fr['top'] - zlim), 0, 1)
    f = np.sin(9 * th + 2.5 * _noise3(co, 14, seed)) * dz ** 1.5
    co = co + nr * (f * folds + _noise3(co, 30, seed + 1) * 0.0018)[:, None]
    _set_co(ob, co)
    for p in ob.data.polygons:
        p.use_smooth = True
    skin(h, ob, Vb, np.arange(M.N_BODY), blur=4)
    h.objs.append(ob)
    return ob


def make_hair(h, thick=0.012, voxel=0.004, name=None, seed=7, hairline=0.058, rough=0.004):
    """Short sculpted hair cap."""
    fr = face_frame(h); eye = fr['eye']; P = fr['P']
    ymid = 0.5 * (fr['front'] + fr['back'])
    z0 = eye[2] + hairline
    # hairline: above the forehead in front, sweeping down behind the ears to the nape
    lim = z0 - np.clip((P[:, 1] - (ymid - 0.02)) / 0.05, 0, 1) * (hairline + 0.075)
    sel = P[P[:, 2] > lim]
    ob = _hull(sel, inflate=thick, col=h.col, name=name or h.name + '_hair')
    # hull is convex: fine for a cropped sculpted cap; cut away what dips below the hairline in front
    _voxel(ob, voxel, smooth=4)
    co = _co(ob); nr = _normals(ob)
    n = _noise3(co, 90, seed) * 0.6 + _noise3(co, 45, seed + 1) * 0.4
    co = co + nr * (n * rough)[:, None]
    _set_co(ob, co)
    skin(h, ob, h.Vb[:M.N_BODY], np.arange(M.N_BODY), blur=2)
    h.objs.append(ob)
    return ob


def finish(h, subsurf=1):
    """Rest-position attribute (texture sticks under deformation) + subdivision on the body."""
    for ob in h.objs:
        try:
            ob.add_rest_position_attribute = True
        except Exception:
            pass
    if subsurf:
        m = h.body.modifiers.new('sub', 'SUBSURF'); m.levels = subsurf; m.render_levels = subsurf
