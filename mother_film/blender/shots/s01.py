"""S01 (0:00-0:09) Darkness. A beam of light finds a lump of clay that shapes itself into a curled infant."""
import bpy, math
import numpy as np
from mathutils import Vector
import common as C, clay as K, fx, cast

FRAMES = 216
START = 0          # absolute film frame of the shot start
SAMPLES = 32


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    h = cast.baby(wet=0.2)
    cast.fetal(h, twist=10, head=0.55)
    h.arm.rotation_euler = (0, math.radians(-88), math.radians(-55))       # lie on its left side
    bpy.context.view_layer.update()
    ob = fx.bake(h.body)
    for o in h.objs + [h.arm]:
        bpy.data.objects.remove(o)
    P = fx.co(ob)
    P[:, 2] -= P[:, 2].min() + 0.022
    cen = P.mean(0); P[:, 0] -= cen[0]; P[:, 1] -= cen[1]
    fx.set_co(ob, P)
    N = fx.vnormals(ob).copy()
    fx.set_attr(ob, 'rest_position', P)
    mat = K.clay('baby', 'terracotta', wet=0.3, bump=1.0, scale=7.0)
    K.assign(ob, mat)

    # the mound of clay that moulds itself into the child: a closed skin that sinks onto the body and vanishes
    from mathutils.bvhtree import BVHTree
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=1.0)
    mound = bpy.context.object; mound.name = 'mound'
    for p_ in mound.data.polygons:
        p_.use_smooth = True
    U = fx.co(mound)                                           # unit directions
    cb = np.array([(P[:, 0].min() + P[:, 0].max()) / 2, (P[:, 1].min() + P[:, 1].max()) / 2, 0.0])
    rad = np.array([(P[:, 0].max() - P[:, 0].min()) * 0.56, (P[:, 1].max() - P[:, 1].min()) * 0.60, P[:, 2].max() * 1.15])
    rr0 = 1.0 / np.linalg.norm(U / rad, axis=1)
    rr0 *= 1 + 0.10 * fx.vnoise(U, 3.0, 4, 5) + 0.035 * fx.vnoise(U, 9.0, 8, 5)
    # bulge the mound wherever the body inside would poke through (hints at the form within)
    from mathutils import kdtree
    Dp = P - cb; dl = np.linalg.norm(Dp, axis=1); Du = Dp / dl[:, None]
    kd = kdtree.KDTree(len(Du))
    for i_, d_ in enumerate(Du):
        kd.insert(d_, i_)
    kd.balance()
    need = np.array([max(dl[j] for _, j, _ in kd.find_n(tuple(u), 12)) for u in U]) + 0.018
    Em0 = fx.edges(mound)
    rr = np.maximum(rr0, need)
    for _ in range(4):
        rr = np.maximum(fx.laplace(rr[:, None], Em0, it=3, lam=0.5)[:, 0], need)
    M0 = cb + U * rr[:, None]
    M0[:, 2] = np.maximum(M0[:, 2], -0.03)
    bvh = BVHTree.FromPolygons([tuple(v) for v in P], [tuple(p_.vertices) for p_ in ob.data.polygons])
    Em = fx.edges(mound)
    T = M0.copy()
    for it in range(36):                                       # shrink-wrap with relaxation: skin slides into the creases
        for i in range(len(T)):
            loc, nrm, _, _ = bvh.find_nearest(tuple(T[i]))
            T[i] = np.array(loc) - np.array(nrm) * (0.012 if it == 35 else 0.0)
        if it < 35:
            T = fx.laplace(T, Em, it=2, lam=0.5)
    fx.set_co(mound, M0)
    Nm = fx.vnormals(mound).copy()
    fx.set_attr(mound, 'rest_position', M0)
    mmat = K.clay('mound', 'terracotta', wet=0.12, cracks=1.0, bump=1.2, scale=5.0, crack_scale=2.6)
    K.assign(mound, mmat)
    K.add_fade(mmat)
    # skin that ends up stretched across creases (between limbs) melts away instead of tenting
    LT = np.linalg.norm(T[Em[:, 0]] - T[Em[:, 1]], axis=1)
    es = np.clip((LT / np.percentile(LT, 60) - 1.8) / 1.6, 0, 1)
    stretch = np.zeros(len(T)); np.maximum.at(stretch, Em[:, 0], es); np.maximum.at(stretch, Em[:, 1], es)
    stretch = np.clip(fx.laplace(stretch[:, None], Em, it=2, lam=0.5)[:, 0] * 1.6, 0, 1)
    fattr = mound.data.attributes.new('fade', 'FLOAT', 'POINT')
    sub = mound.modifiers.new('sub', 'SUBSURF'); sub.levels = 1; sub.render_levels = 1
    # moulding order: starts where the mound is far from the body (it has the most to give), broken up by noise
    gap = np.linalg.norm(M0 - T, axis=1); gap = (gap - gap.min()) / (gap.max() - gap.min())
    delay = np.clip(0.5 * (1 - gap) + 0.5 * (fx.vnoise(M0, 11, 11) * 0.5 + 0.5), 0, 1)
    rs = np.random.RandomState(5)
    dents = [(rs.randint(0, len(M0)), rs.uniform(14, 120), rs.uniform(16, 32), rs.uniform(0.04, 0.08)) for _ in range(30)]

    # ground: a slab of dark wet clay
    g = fx.grid('ground', 6.0, 300)
    G = fx.co(g)
    rr = np.linalg.norm(G[:, :2], axis=1)
    G[:, 2] = fx.fbm2(G[:, 0] * 1.3 + 7, G[:, 1] * 1.3 + 3, seed=2, octaves=5) * 0.02 \
        + 0.016 * np.exp(-((rr - 0.27) / 0.09) ** 2) - 0.004
    fx.set_co(g, G)
    gm = K.clay('ground', 'umber', wet=0.32, coords='object', bump=1.2, cracks=0.8, scale=1.6, tex='brown_mud_02', crack_scale=2.4)
    K.assign(g, gm)

    # light: one warm beam from above/behind, a breath of cool rim, fog to make the beam visible
    key = C.light(sc, 'SPOT', (-0.35, 0.9, 2.3), 0, color=(1.0, 0.74, 0.48), target=(0, 0, 0.08), size=0.035,
                  spot=24, blend=0.9, name='beam')
    rim = C.light(sc, 'AREA', (1.3, 1.0, 0.5), 0, color=(0.45, 0.6, 1.0), target=(0, 0, 0.1), size=0.6, name='rim')
    fill = C.light(sc, 'AREA', (-0.6, -1.4, 0.7), 0, color=(1.0, 0.6, 0.4), target=(0, 0, 0.1), size=1.2, name='fill')
    _, beam_s = fx.beam(sc, (-0.35, 0.9, 2.3), (0.03, -0.08, -0.12), 0.5, strength=0.0)
    motes = fx.Motes(sc, 500, (-0.05, 0.0, 0.0), 0.45, 1.0, size=0.0013, seed=4, emit=0.04)

    cam = C.camera(sc, (0.0, -1.0, 1.1), (0, 0, 0.1), lens=85, fstop=2.8)
    sm = fx.smooth

    def update(f):
        t = f / (FRAMES - 1)
        # --- the mound breathes, is pressed by invisible fingers, then moulds itself onto the child
        g2 = (f - 40) / 112.0
        s2 = np.clip((g2 - delay * 0.6) / 0.4, 0, 1); s2 = s2 * s2 * (3 - 2 * s2)
        X = M0 + Nm * (0.006 * sm(f, 8, 40) * np.sin(f * 0.21 + delay * 9))[:, None]
        for vi, f0, dur, rad_ in dents:
            k = (f - f0) / dur
            if 0 < k < 1:
                w = np.exp(-np.sum((M0 - M0[vi]) ** 2, 1) / rad_ ** 2) * math.sin(k * math.pi) ** 2
                X -= Nm * (w * 0.022)[:, None]
        X = X + (T - X) * s2[:, None]
        fx.set_co(mound, X)
        k_ = np.clip((s2 - 0.35) / 0.4, 0, 1)
        fattr.data.foreach_set('value', (stretch * k_ + np.clip((s2 - 0.9) / 0.1, 0, 1) * sm(f, 140, 152)).clip(0, 1).astype(np.float32))
        fx.hide(mound, f > 153)
        fx.hide(ob, f < 46)
        K.setp(mmat, 'cracks', 1.0 - sm(f, 24, 110))
        K.setp(mmat, 'wet', 0.12 + 0.3 * sm(f, 40, 150))
        br = sm(f, 160, 185) * 0.0018 * math.sin((f - 160) / 24 * 2 * math.pi / 1.7)      # first breaths
        fx.set_co(ob, P + N * br)
        K.setp(mat, 'wet', 0.3 + 0.15 * sm(f, 120, 200))
        # --- light pulses with the heartbeat in the soundtrack
        beat = fx.env(START + f, 'low', 1)
        fade = sm(f, 4, 42)
        key.data.energy = 1150 * fade * (0.62 + 0.9 * beat)
        beam_s.default_value = 0.18 * fade * (0.62 + 0.9 * beat)
        rim.data.energy = 14 * sm(f, 60, 170) * (0.7 + 0.6 * beat)
        fill.data.energy = 3 * sm(f, 10, 50) + 6 * sm(f, 70, 190)
        motes.update(f)
        # --- camera: very slow push-in with a slight rise
        p = sm(f, 0, FRAMES - 1)
        cam.location = Vector((0.20 - 0.20 * p, -1.75 + 0.80 * p, 1.05 - 0.40 * p))
        C.look_at(cam, (0.0, 0.0, 0.07))
        cam.data.dof.focus_distance = (cam.location - Vector((0, 0, 0.12))).length

    return dict(frames=FRAMES, update=update)
