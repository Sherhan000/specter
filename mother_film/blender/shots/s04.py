"""S04 (0:20-0:25) The child trips and falls - in slow motion; her whole body is already flying towards him."""
import bpy, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix, Euler
import common as C, clay as K, fx, cast, mhlib as M, garments as G

FRAMES = 120
START = 480


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.42, 0.32, 1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.10
    k = cast.child()
    k.shut.value = 0.85
    m = cast.mother(shut=0.0)
    cast.add_eyes(m)
    fear = m.add_shape('fear', {'mouth-open': 0.7, 'eyebrows-left-up': 1.0, 'eyebrows-right-up': 1.0, 'eyebrows-left-inner-up': 0.8,
                                'eyebrows-right-inner-up': 0.8, 'eye-left-opened-up': 1.0, 'eye-right-opened-up': 1.0}, 0.6)

    kid_p = Vector((0.40, 0.0, 0)); kid_dir = Vector((1.0, -0.12, 0)).normalized()
    mom_p0 = Vector((-1.75, 0.38, 0)); mom_dir = Vector((1.0, -0.10, 0)).normalized()
    hk = math.atan2(kid_dir.x, -kid_dir.y); hm = math.atan2(mom_dir.x, -mom_dir.y)

    # arms of the mother reach with IK; targets ride with her body
    tl, pl = m.ik_arm('L', (0.18, -0.5, 1.05), (0.7, 0.3, 0.7), math.radians(90))
    tr, pr = m.ik_arm('R', (-0.18, -0.5, 1.05), (-0.7, 0.3, 0.7), math.radians(-90))
    for e in (tl, pl, tr, pr):
        e.parent = m.arm

    # ---- courtyard
    earth = K.clay('earth', 'earth', wet=0.05, coords='object', scale=0.7, tex='brown_mud_02', cracks=0.5, crack_scale=0.9)
    g = fx.grid('ground', 40, 160); P = fx.co(g)
    P[:, 2] = fx.fbm2(P[:, 0] * 0.6, P[:, 1] * 0.6, seed=3, octaves=4) * 0.03
    fx.set_co(g, P); K.assign(g, earth)
    wallm = K.clay('wall', 'buff', wet=0.03, coords='object', scale=0.5)
    fx.box('wall', (26, 0.5, 3.4), (0, 3.9, 1.7), wallm, bevel=0.06, subdiv=6, noise=0.03)
    fx.box('door', (1.15, 0.2, 2.2), (-2.3, 3.62, 1.1), K.clay('door', 'dark', wet=0.1, coords='object'), bevel=0.05)
    fx.box('step', (1.7, 0.7, 0.16), (-2.3, 3.4, 0.08), wallm, bevel=0.04)
    potm = K.clay('pot', 'terracotta', wet=0.2, coords='object', scale=3)
    for (x, y, s_) in ((1.5, 3.1, 1.0), (2.15, 2.9, 0.7), (-0.6, 3.2, 1.25)):
        fx.lathe('pot', [(0, 0), (0.16 * s_, 0), (0.30 * s_, 0.25 * s_), (0.26 * s_, 0.5 * s_), (0.13 * s_, 0.62 * s_),
                         (0.17 * s_, 0.7 * s_), (0.14 * s_, 0.7 * s_)], (x, y, 0), potm)
    sun = C.light(sc, 'SUN', (0, 0, 10), 6.0, color=(1.0, 0.72, 0.45), rot=(-47, 0, -52), size=0.03, name='sun')
    bounce = C.light(sc, 'AREA', (-1.5, -5.0, 1.6), 300, color=(1.0, 0.82, 0.66), target=(0, 0.0, 0.7), size=4.0, name='bounce')
    motes = fx.Motes(sc, 520, (0.2, 0.2, 0.0), 3.0, 2.0, size=0.0022, seed=4, color=(1.0, 0.72, 0.42), emit=0.12,
                     drift=(0.012, -0.006, 0.004))

    cam = C.camera(sc, (0.0, -4.7, 0.62), (0.0, 0.0, 0.74), lens=45, fstop=2.4, name='cam')
    sm = fx.smooth

    def pose_kid(f):
        k.reset_pose()
        p = min(1.0, f / 100.0)
        a = p ** 1.7
        k.rot('spine03', 'X', -6); k.rot('neck01', 'X', -10); k.rot('head', 'X', -18 - 8 * a)
        k.flex2('upperarm01', 55 + 50 * a); k.both('upperarm01', 'Y', -6)
        k.flex2('lowerarm01', 30 - 12 * a)
        k.flex('upperleg01.L', 14 - 8 * a); k.flex('lowerleg01.L', -18)
        k.flex('upperleg01.R', -8 - 22 * a); k.flex('lowerleg01.R', -45 - 40 * a)
        k.flex('foot.R', -25)
        pitch = 26 + 52 * a + 2.0 * math.exp(-max(0, f - 100) / 5.0) * math.sin(max(0, f - 100) * 0.9)
        k.arm.matrix_world = Matrix.Translation(kid_p + kid_dir * (0.22 * p)) @ Matrix.Rotation(hk, 4, 'Z') \
            @ Matrix.Rotation(math.radians(pitch), 4, 'X')
        k.cry.value = 0.25 + 0.5 * a

    def pose_mom(f):
        for pb in m.arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
        p = sm(f, -30, FRAMES + 10)
        a = f / FRAMES
        lean = 16 + 20 * a
        m.rot('spine05', 'X', lean * 0.5); m.rot('spine03', 'X', lean * 0.3); m.rot('spine01', 'X', lean * 0.2)
        m.rot('neck01', 'X', -8); m.rot('head', 'X', -10 - 6 * a)
        m.flex('upperleg01.L', 50 + 12 * a); m.flex('lowerleg01.L', -62 - 14 * a)
        m.flex('upperleg01.R', -22 - 6 * a); m.flex('lowerleg01.R', -22)
        m.curl_fingers('L', 8, 4); m.curl_fingers('R', 8, 4)
        m.arm.matrix_world = Matrix.Translation(mom_p0 + mom_dir * (0.10 + 0.80 * a) + Vector((0, 0, -0.10 - 0.12 * a))) \
            @ Matrix.Rotation(hm, 4, 'Z')
        tl.location = Vector((0.20, -0.55, 1.18)).lerp(Vector((0.14, -0.86, 0.92)), a)
        tr.location = Vector((-0.16, -0.62, 1.08)).lerp(Vector((-0.15, -0.90, 0.80)), a)
        fear.value = 0.6 + 0.4 * a

    def update(f):
        pose_kid(f); pose_mom(f)
        bpy.context.view_layer.update()
        kh = k.arm.matrix_world @ k.pb('head').matrix.translation
        mh = m.arm.matrix_world @ m.pb('head').matrix.translation
        p = sm(f, 0, FRAMES - 1)
        cam.location = Vector((-0.30 + 0.36 * p, -4.7 + 0.35 * p, 0.62))
        C.look_at(cam, Vector((-0.22 + 0.28 * p, 0.0, 0.72)))
        fx.shake(cam, f, 0.0008, seed=5)
        cam.data.dof.focus_distance = abs(cam.location.y) - 0.05
        motes.update(f * 0.3)

    return dict(frames=FRAMES, update=update)
