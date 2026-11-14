"""The courtyard after the storm: the son bowed at his old mother's feet. Shared by S08 and S09."""
import bpy, math
import numpy as np
from mathutils import Vector, Matrix
import common as C, clay as K, fx, cast

SX = 0.78


def make(sc, wet=0.85, eyes=False):
    m = cast.mother(age=1.0, scarf_tint='white', robe_tint='grey', hem=0.115, flare=0.14, shut=1.0, wet=wet)
    K.setp(m.mat, 'cracks', 0.45); K.setp(m.robe_mat, 'cracks', 0.07); K.setp(m.scarf_mat, 'cracks', 0.04)
    K.set_tint(m.mat, 'terracotta', 'buff', 0.25)
    if eyes:
        cast.add_eyes(m)
    s = cast.son(wet=wet)
    Rm = Matrix.Rotation(math.radians(90), 4, 'Z'); Rs = Matrix.Rotation(math.radians(-90), 4, 'Z')
    th, _ = m.ik_arm('R', (0.5, -0.2, 0.6), (0.3, -0.7, 2.2), math.radians(-90))
    hl, _ = s.ik_arm('L', (0.4, -0.15, 0.5), None)
    hr, _ = s.ik_arm('R', (0.4, 0.15, 0.5), None)
    st = dict(m=m, s=s, hand=th)

    def pose_mother(bend=1.0, head=20.0):
        for pb in m.arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
        m.rot('spine05', 'X', 8 + 6 * bend); m.rot('spine03', 'X', 9 + 6 * bend); m.rot('spine01', 'X', 8 + 4 * bend)
        m.rot('neck01', 'X', 10); m.rot('head', 'X', head)
        m.flex('upperarm01.L', 4); m.rot('upperarm01.L', 'Y', 26); m.flex('lowerarm01.L', 18)
        m.curl_fingers('L', 30, 12); m.curl_fingers('R', 22, 8)
        m.arm.matrix_world = Rm

    def pose_son(bow=1.0):
        s.reset_pose()
        s.flex2('upperleg01', 12 + 78 * bow); s.flex2('lowerleg01', -112 - 26 * bow); s.flex2('foot', -50)
        lean = 6 + 62 * bow
        s.rot('spine05', 'X', lean * 0.42); s.rot('spine03', 'X', lean * 0.33); s.rot('spine01', 'X', lean * 0.25)
        s.rot('neck01', 'X', 10 + 6 * bow); s.rot('head', 'X', 16 + 10 * bow)
        s.curl_fingers('L', 14, 6); s.curl_fingers('R', 14, 6)
        s.arm.matrix_world = Matrix.Translation((SX, 0, 0)) @ Rs
        bpy.context.view_layer.update()
        knee = s.arm.matrix_world @ s.pb('lowerleg01.L').matrix.translation
        s.arm.matrix_world = Matrix.Translation((SX, 0, 0.065 - knee.z)) @ Rs
        bpy.context.view_layer.update()
        hl.location = (0.20, -0.15, 0.04); hr.location = (0.20, 0.15, 0.04)
        head = s.arm.matrix_world @ s.pb('head').matrix @ Vector((0, 0.13, 0))
        return head

    pose_mother(); head = pose_son()
    th.location = Vector((head.x + 0.10, head.y - 0.02, max(head.z + 0.06, 0.50)))
    st.update(pose_mother=pose_mother, pose_son=pose_son, son_head=head)

    earth = K.clay('earth', 'earth', wet=wet, coords='object', scale=0.7, tex='brown_mud_02', cracks=0.5, crack_scale=1.7)
    g = fx.grid('ground', 30, 200); P = fx.co(g)
    P[:, 2] = fx.fbm2(P[:, 0] * 0.6, P[:, 1] * 0.6, seed=3, octaves=4) * 0.012
    fx.set_co(g, P); K.assign(g, earth)
    wallm = K.clay('wall', 'buff', wet=wet * 0.7, coords='object', scale=0.5)
    fx.box('wall', (26, 0.5, 3.4), (0, 3.9, 1.7), wallm, bevel=0.06, subdiv=6, noise=0.03)
    fx.box('door', (1.15, 0.2, 2.2), (-2.3, 3.62, 1.1), K.clay('door', 'dark', wet=0.1, coords='object'), bevel=0.05)
    fx.box('step', (1.7, 0.7, 0.16), (-2.3, 3.4, 0.08), wallm, bevel=0.04)
    potm = K.clay('pot', 'terracotta', wet=wet, coords='object', scale=3)
    for (x, y, s_) in ((2.4, 3.1, 1.0), (3.05, 2.9, 0.7), (-0.9, 3.2, 1.25)):
        fx.lathe('pot', [(0, 0), (0.16 * s_, 0), (0.30 * s_, 0.25 * s_), (0.26 * s_, 0.5 * s_), (0.13 * s_, 0.62 * s_),
                         (0.17 * s_, 0.7 * s_), (0.14 * s_, 0.7 * s_)], (x, y, 0), potm)
    st['earth'] = earth
    return st
