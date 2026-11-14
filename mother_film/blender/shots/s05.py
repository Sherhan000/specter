"""S05 (0:25-0:31) She carries him along the road. Seasons flash by; with every step she ages and he grows -
and she keeps carrying him."""
import bpy, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
import common as C, clay as K, fx, cast, mhlib as M, garments as G

FRAMES = 144
START = 600
SEASON = [((1.0, 0.86, 0.72), 4.5, (1.0, 0.80, 0.70)),      # spring: sun colour, sun strength, sky colour
          ((1.0, 0.76, 0.45), 5.5, (1.0, 0.70, 0.40)),      # summer
          ((1.0, 0.52, 0.26), 4.5, (1.0, 0.42, 0.20)),      # autumn
          ((0.62, 0.74, 1.0), 2.6, (0.42, 0.52, 0.72))]     # winter


def season(x):
    """Blend season parameters along the road (x in metres)."""
    u = np.clip((x - 0.4) / 1.75, 0, 2.999); i = int(u); t = fx.smooth(u - i, 0.25, 0.75)
    a, b = SEASON[i], SEASON[i + 1]
    mix = lambda p, q: tuple(p[k] + (q[k] - p[k]) * t for k in range(3))
    return mix(a[0], b[0]), a[1] + (b[1] - a[1]) * t, mix(a[2], b[2])


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    m = cast.mother()
    old = m.add_morph('old', {'macrodetails/caucasian-female-old': 1.0},
                      follow=('upperarm', 'lowerarm', 'wrist', 'metacarpal', 'finger'))
    k = cast.child()
    grow = k.add_morph('older', {'macrodetails/caucasian-male-child': 1.0}, scale_to_height=True)
    k.shut.value = 1.0
    bpy.context.view_layer.update()
    kid_hip = k.pb('upperleg01.L').bone.head_local.z

    # walk: distance and phase per frame (she slows and her steps shorten as she ages)
    age = [fx.smooth(f, 8, 132) for f in range(FRAMES)]
    dist = np.zeros(FRAMES); phase = np.zeros(FRAMES)
    for f in range(1, FRAMES):
        v = 1.25 - 0.70 * age[f]; Lc = 1.2 - 0.5 * age[f]
        dist[f] = dist[f - 1] + v / 24.0
        phase[f] = phase[f - 1] + 2 * math.pi * (v / 24.0) / Lc
    rs = np.random.RandomState(3)

    # ---- the road
    earth = K.clay('earth', 'earth', wet=0.05, coords='object', scale=0.6, tex='brown_mud_02', cracks=0.4, crack_scale=0.8)
    g = fx.terrain('ground', (-8, 16), (-8, 22), 240, 300,
                   lambda X, Y: fx.fbm2(X * 0.5, Y * 0.5, seed=3, octaves=4) * 0.05 * np.clip(np.abs(Y) - 0.6, 0, 1)
                   + np.clip(Y - 6, 0, None) ** 1.5 * 0.03 * (1 + 0.6 * fx.fbm2(X * 0.15, Y * 0.15, seed=5, octaves=4)))
    K.assign(g, earth)
    for i, (x, kind) in enumerate(((0.6, 'blossom'), (2.9, 'olive'), (5.0, 'ochre'), (7.0, 'bare'), (-2.0, 'blossom'), (9.3, 'bare'))):
        fx.tree(f'tree{i}', (x, 4.3 + 0.7 * math.sin(i * 2.3), 0), kind, seed=i + 1, height=3.2 + 0.4 * math.cos(i))
    sky, sky_e = fx.emit_plane('sky', (120, 40), (4, 30, 14), (90, 0, 0), strength=0.65)
    sun = C.light(sc, 'SUN', (0, 0, 10), 5, color=(1, 0.8, 0.5), rot=(-66, 0, -38), size=0.04, name='sun')
    fill = C.light(sc, 'AREA', (2, -6, 2.2), 500, color=(1.0, 0.85, 0.7), target=(3, 0, 1.0), size=5.0, name='fill')
    petals = fx.Motes(sc, 220, (0.3, 0.8, 0.0), 1.6, 2.6, size=0.006, seed=1, color=(0.95, 0.6, 0.55), drift=(0.02, -0.03, -0.35))
    leaves = fx.Motes(sc, 170, (3.9, 0.8, 0.0), 1.3, 2.6, size=0.009, seed=2, color=(0.9, 0.35, 0.06), drift=(0.03, -0.04, -0.6))
    snow = fx.Motes(sc, 600, (5.9, 0.6, 0.0), 2.2, 2.8, size=0.005, seed=3, color=(0.95, 0.97, 1.0), drift=(0.02, -0.02, -0.45),
                    emit=0.15)
    cam = C.camera(sc, (0, -5.0, 1.0), (0, 0, 1.0), lens=50, fstop=2.8, name='cam')
    Rz = Matrix.Rotation(math.radians(90), 4, 'Z')
    sm = fx.smooth

    def update(f):
        a = age[f]; ph = phase[f]; x = dist[f] + 0.2
        for sk in old.values():
            sk.value = a
        for sk in grow.values():
            sk.value = a
        # ---- mother: stooping walk under a growing weight
        for pb in m.arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
        lean = 9 + 22 * a
        m.rot('spine05', 'X', lean * 0.45); m.rot('spine03', 'X', lean * 0.35); m.rot('spine01', 'X', lean * 0.2)
        m.rot('neck01', 'X', -4 + 6 * a); m.rot('head', 'X', 2 + 6 * a)
        amp = 24 - 10 * a
        for s_, o in (('L', 0.0), ('R', math.pi)):
            m.flex(f'upperleg01.{s_}', amp * math.sin(ph + o) + 6 * a)
            m.flex(f'lowerleg01.{s_}', -(6 + 12 * a + 30 * max(0.0, math.sin(ph + o + 0.9)) ** 2))
            trem = a * 2.2 * math.sin(f * 2.3 + o)
            m.flex(f'upperarm01.{s_}', -26 + trem); m.rot(f'upperarm01.{s_}', 'Y', 8 if s_ == 'L' else -8)
            m.flex(f'lowerarm01.{s_}', 78 + trem * 1.5)
        m.curl_fingers('L', 40, 20); m.curl_fingers('R', 40, 20)
        bob = -0.02 - 0.014 * math.cos(2 * ph) - 0.07 * a
        m.arm.matrix_world = Matrix.Translation((x, 0, bob)) @ Rz
        bpy.context.view_layer.update()
        # ---- the son on her back
        sc_k = 1.0 + 0.32 * a
        k.reset_pose()
        k.flex2('upperarm01', 58); k.both('upperarm01', 'Y', 10); k.flex2('lowerarm01', 28)
        k.flex2('upperleg01', 72); k.both('upperleg01', 'Y', -24); k.flex2('lowerleg01', -62 - 10 * a)
        k.rot('neck01', 'X', 8); k.rot('head', 'X', 6); k.rot('head', 'Z', 28); k.rot('head', 'Y', 14)
        k.curl_fingers('L', 30, 10); k.curl_fingers('R', 30, 10)
        Bm = m.arm.matrix_world @ m.pb('spine02').matrix
        up = (Bm.to_3x3() @ Vector((0, 1, 0))).normalized()
        back = -(m.arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
        zdir = (up + Vector((0.16, 0, 0))).normalized()
        anchor = Bm.translation + back * (0.115 + 0.03 * a) - up * (0.11 + 0.05 * a)
        Wk = cast.frame_matrix(anchor - zdir * (kid_hip * sc_k), zdir, Vector((1, 0, 0.1)))
        k.arm.matrix_world = Wk @ Matrix.Scale(sc_k, 4)
        # ---- clay dries and pales with the years
        K.setp(m.mat, 'cracks', 0.5 * a); K.setp(m.robe_mat, 'cracks', 0.16 * a); K.setp(m.scarf_mat, 'cracks', 0.14 * a)
        K.set_tint(m.scarf_mat, 'slip', 'white', a); K.set_tint(m.robe_mat, 'buff', 'grey', 0.55 * a)
        K.set_tint(m.mat, 'terracotta', 'buff', 0.35 * a)
        # ---- seasons
        col, st, skyc = season(x)
        sun.data.color = col; sun.data.energy = st
        sky_e.inputs[0].default_value = (*skyc, 1)
        fill.data.color = tuple(0.5 * (c + 1) for c in col); fill.data.energy = 420 * (0.6 + 0.08 * st)
        fill.location.x = x + 0.5
        petals.update(f); leaves.update(f); snow.update(f)
        # ---- camera travels with her, creeping closer
        p = sm(f, 0, FRAMES - 1)
        cam.location = Vector((x + 0.55 - 0.35 * p, -5.0 + 1.9 * p, 1.02 + 0.06 * p))
        C.look_at(cam, Vector((x + 0.30 - 0.22 * p, 0, 0.98 + 0.12 * p)))
        fx.shake(cam, f, 0.0009, seed=7)
        cam.data.dof.focus_distance = abs(cam.location.y)

    return dict(frames=FRAMES, update=update)
