"""S06A One day he comes back. Seen over the old mother's shoulder: the grown son walks up to her across the
courtyard at dusk, stops, and sinks to his knees; her hand comes to rest on his head. (S06 follows.)"""
import bpy, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
import common as C, clay as K, fx, cast

FRAMES = 180
SX = 0.78                    # where his knees end up, in front of her (same as S06)
X0 = 3.25                    # where he is when the shot starts
STOP = 62                    # frame at which he stands still in front of her
KNEEL = (70, 118)            # frames over which he goes down on his knees


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.20, 0.24, 0.34, 1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.06
    m = cast.mother(age=1.0, scarf_tint='white', robe_tint='grey', hem=0.115, flare=0.14)
    K.setp(m.mat, 'cracks', 0.6); K.setp(m.robe_mat, 'cracks', 0.07); K.setp(m.scarf_mat, 'cracks', 0.14)
    K.set_tint(m.mat, 'terracotta', 'buff', 0.35)
    s = cast.son()
    cast.add_eyes(s, tint='white')
    Rm = Matrix.Rotation(math.radians(90), 4, 'Z'); Rs = Matrix.Rotation(math.radians(-90), 4, 'Z')
    th, phd = m.ik_arm('R', (0.2, -0.24, 0.80), (0.3, -0.7, 2.2), math.radians(-90))
    ankle0 = s.arm.data.bones['foot.L'].head_local.z

    # ---- courtyard at dusk before the storm (as in S06)
    earth = K.clay('earth', 'earth', wet=0.12, coords='object', scale=0.7, tex='brown_mud_02', cracks=0.9, crack_scale=1.7)
    g = fx.grid('ground', 30, 200); P = fx.co(g)
    P[:, 2] = fx.fbm2(P[:, 0] * 0.6, P[:, 1] * 0.6, seed=3, octaves=4) * 0.012
    fx.set_co(g, P); K.assign(g, earth)
    wallm = K.clay('wall', 'buff', wet=0.03, coords='object', scale=0.5)
    fx.box('wall', (26, 0.5, 8.0), (0, 3.9, 4.0), wallm, bevel=0.06, subdiv=6, noise=0.03)
    fx.box('door', (1.15, 0.2, 2.2), (-2.3, 3.62, 1.1), K.clay('door', 'dark', wet=0.1, coords='object'), bevel=0.05)
    fx.box('farwall', (0.5, 26, 8.0), (9.5, 0, 4.0), wallm, bevel=0.06, subdiv=6, noise=0.03)
    potm = K.clay('pot', 'terracotta', wet=0.2, coords='object', scale=3)
    for (x, y, s_) in ((4.6, 3.1, 1.0), (5.3, 2.9, 0.7), (7.5, 1.6, 1.25), (6.9, -2.2, 0.9)):
        fx.lathe('pot', [(0, 0), (0.16 * s_, 0), (0.30 * s_, 0.25 * s_), (0.26 * s_, 0.5 * s_), (0.13 * s_, 0.62 * s_),
                         (0.17 * s_, 0.7 * s_), (0.14 * s_, 0.7 * s_)], (x, y, 0), potm)
    sky, sky_e = fx.emit_plane('sky', (120, 40), (30, 0, 16), (90, 0, 90), color=(0.30, 0.34, 0.52), strength=0.55)
    dusk = C.light(sc, 'AREA', (-3.0, -3.5, 3.5), 520, color=(0.50, 0.60, 0.95), target=(0.4, 0, 0.8), size=3.0, name='dusk')
    rim = C.light(sc, 'AREA', (3.5, 3.0, 2.2), 420, color=(1.0, 0.62, 0.38), target=(0.4, 0, 0.9), size=1.2, name='rim')
    facel = C.light(sc, 'AREA', (-0.6, -1.6, 1.9), 60, color=(1.0, 0.74, 0.55), target=(1.2, 0, 1.3), size=1.2, name='facel')
    motes = fx.Motes(sc, 420, (1.2, 0.0, 0.0), 2.6, 2.2, size=0.0022, seed=4, color=(1.0, 0.75, 0.45), emit=0.05,
                     drift=(0.01, 0.0, 0.02))
    cam = C.camera(sc, CAM, (1.6, 0.0, 1.45), lens=40, fstop=2.4, name='cam')
    sm = fx.smooth

    # his path: decelerating walk up to her
    xs = np.zeros(FRAMES); ph = np.zeros(FRAMES); sp = np.zeros(FRAMES)
    for f in range(FRAMES):
        u = min(1.0, f / STOP); e = 1 - (1 - u) ** 2.2
        xs[f] = X0 + (SX - X0) * e
    for f in range(1, FRAMES):
        sp[f] = (xs[f - 1] - xs[f]) * 24.0
        ph[f] = ph[f - 1] + 2 * math.pi * (xs[f - 1] - xs[f]) / 1.25

    def update(f):
        kn = sm(f, *KNEEL)
        walk = min(1.0, sp[f] / 0.9)                         # 1 while striding, 0 when he stands
        # ---- son
        s.reset_pose()
        amp = 25 * walk
        for sd, o in (('L', 0.0), ('R', math.pi)):
            s.flex(f'upperleg01.{sd}', amp * math.sin(ph[f] + o) + (12 + 44 * math.sin(math.pi * kn)) * kn ** 0.5)
            s.flex(f'lowerleg01.{sd}', -(4 + 32 * max(0.0, math.sin(ph[f] + o + 0.9)) ** 2) * walk - 112 * kn)
            s.flex(f'foot.{sd}', -50 * kn)
            s.flex(f'upperarm01.{sd}', -amp * 0.55 * math.sin(ph[f] + o) + 12 * kn)
            s.rot(f'upperarm01.{sd}', 'Y', 34 if sd == 'L' else -34)
            s.flex(f'lowerarm01.{sd}', 14 + 8 * walk + 30 * kn)
        lean = 3 * walk + 6 * kn + 16 * math.sin(math.pi * kn)
        s.rot('spine05', 'X', lean * 0.42); s.rot('spine03', 'X', lean * 0.33); s.rot('spine01', 'X', lean * 0.25)
        s.rot('spine03', 'Z', 3.0 * walk * math.sin(ph[f]))
        bowed = sm(f, 40, 100)                               # his head goes down as he nears her
        s.rot('neck01', 'X', 2 + 8 * bowed); s.rot('head', 'X', 2 + 14 * bowed)
        s.curl_fingers('L', 14, 6); s.curl_fingers('R', 14, 6)
        s.grief.value = 0.45 + 0.4 * bowed
        s.shut.value = 0.12 + 0.88 * sm(f, 66, 112)         # he looks at her, then cannot
        s.arm.matrix_world = Matrix.Translation((xs[f], 0, 0)) @ Rs
        bpy.context.view_layer.update()
        Mw = s.arm.matrix_world
        knee = min((Mw @ s.pb(f'lowerleg01.{sd}').matrix.translation).z for sd in 'LR')
        ank = min((Mw @ s.pb(f'foot.{sd}').matrix.translation).z for sd in 'LR')
        dz = max(ankle0 - ank, 0.065 - knee) - 0.012 * walk * (0.5 + 0.5 * math.cos(2 * ph[f]))
        s.arm.matrix_world = Matrix.Translation((xs[f], 0, dz)) @ Rs
        bpy.context.view_layer.update()
        head = s.arm.matrix_world @ s.pb('head').matrix @ Vector((0, 0.13, 0))
        # ---- mother: she has been waiting; her head follows him down and her hand finds his head
        for pb in m.arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
        breath = math.sin(f / 24.0 * 2 * math.pi / 3.8)
        m.rot('spine05', 'X', 8 + 0.4 * breath); m.rot('spine03', 'X', 9); m.rot('spine01', 'X', 8)
        m.rot('neck01', 'X', 6 + 4 * kn); m.rot('head', 'X', 2 + 12 * kn)
        m.flex('upperarm01.L', 4); m.rot('upperarm01.L', 'Y', 26); m.flex('lowerarm01.L', 18)
        m.curl_fingers('L', 30, 12); m.curl_fingers('R', 22, 8)
        m.arm.matrix_world = Rm
        reach = sm(f, 84, 136)
        rest = Vector((0.20, -0.24, 0.80)); onhead = Vector((head.x - 0.02, head.y - 0.03, max(head.z + 0.01, 0.80)))
        trem = Vector((math.sin(f * 2.1) * 0.004, math.sin(f * 2.7 + 1) * 0.004, math.sin(f * 3.3) * 0.003))
        th.location = rest.lerp(onhead, reach) + Vector((0, 0, 0.10 * math.sin(reach * math.pi))) + trem
        # ---- camera: over her shoulder, sinking with him
        p = sm(f, 0, FRAMES - 1)
        cam.location = Vector(CAM) + Vector(CAM_MOVE) * sm(f, 50, 150)
        aim = Vector((head.x * 0.6 + 0.55, 0.0, head.z - 0.10))
        C.look_at(cam, aim)
        fx.shake(cam, f, 0.0010, seed=16)
        cam.data.dof.focus_distance = (cam.location - head).length
        motes.update(f * 0.4)

    return dict(frames=FRAMES, update=update)


CAM = (-0.95, -0.62, 1.52)
CAM_MOVE = (0.38, -0.80, -0.46)
