"""S05B Thirty years later, 3:07 AM again. The same room; the son has left. The old mother sits alone on the bed
and waits for the telephone to ring."""
import bpy, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
import common as C, clay as K, fx, cast

FRAMES = 288


def telephone(loc, mat, dial_mat):
    """Old rotary telephone, about 22 cm wide, facing -Y."""
    x, y, z = loc
    obs = [fx.box('ph_base', (0.215, 0.165, 0.062), (x, y, z + 0.031), mat, bevel=0.018),
           fx.box('ph_top', (0.15, 0.115, 0.05), (x, y + 0.012, z + 0.080), mat, bevel=0.016),
           fx.box('ph_fork_l', (0.022, 0.05, 0.035), (x - 0.062, y + 0.02, z + 0.118), mat, bevel=0.006),
           fx.box('ph_fork_r', (0.022, 0.05, 0.035), (x + 0.062, y + 0.02, z + 0.118), mat, bevel=0.006)]
    d = fx.lathe('ph_dial', [(0.0, 0.0), (0.046, 0.0), (0.046, 0.008), (0.018, 0.010), (0.0, 0.010)], (x, y - 0.052, z + 0.064), dial_mat, 32)
    d.rotation_euler = (math.radians(62), 0, 0); obs.append(d)
    # handset: a bar with two round ends, resting across the fork
    obs.append(fx.box('ph_bar', (0.205, 0.030, 0.026), (x, y + 0.02, z + 0.148), mat, bevel=0.011))
    for sx in (-1, 1):
        e = fx.lathe('ph_end', [(0.0, -0.022), (0.030, -0.022), (0.034, 0.0), (0.028, 0.014), (0.0, 0.016)],
                     (x + sx * 0.098, y + 0.02, z + 0.133), mat, 24)
        obs.append(e)
    return obs


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    m = cast.mother(age=1.0, scarf_tint='white', robe_tint='grey', shut=0.0, wet=0.10)
    K.setp(m.mat, 'cracks', 0.45); K.setp(m.robe_mat, 'cracks', 0.10); K.setp(m.scarf_mat, 'cracks', 0.06)
    K.set_tint(m.mat, 'terracotta', 'buff', 0.25)
    cast.add_eyes(m, tint='white')
    sad = m.add_shape('sad', {'eyebrows-left-inner-up': 0.8, 'eyebrows-right-inner-up': 0.8, 'mouth-depression': 0.5,
                              'mouth-compression': 0.3}, 0.7)

    def pose(f):
        for pb in m.arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
        t = f / 24.0
        breath = math.sin(t * 2 * math.pi / 4.2)
        droop = fx.smooth(f, 175, 262)                  # at the end she gives up watching the phone
        m.flex2('upperleg01', 82); m.flex2('lowerleg01', -84)
        m.rot('spine05', 'X', 9 + 0.5 * breath + 3 * droop); m.rot('spine03', 'X', 11 + 0.4 * breath + 3 * droop)
        m.rot('spine01', 'X', 7)
        m.rot('neck01', 'X', 8 + 3 * droop); m.rot('head', 'X', 6 + 8 * droop)
        m.rot('head', 'Z', LOOK * (1 - 0.75 * droop)); m.rot('neck01', 'Z', LOOK * 0.5 * (1 - 0.75 * droop))
        # hands folded in her lap
        m.flex2('upperarm01', 26); m.both('upperarm01', 'Y', ARM_Y); m.flex2('lowerarm01', 62)
        m.twist('lowerarm01.L', FORE_TW); m.twist('lowerarm01.R', -FORE_TW)
        m.curl_fingers('L', 30, 12); m.curl_fingers('R', 30, 12)
        m.rot('eye.L', 'X', 6 + 8 * droop); m.rot('eye.R', 'X', 6 + 8 * droop)
        blink = max(math.exp(-((f - c) / 2.6) ** 2) for c in (64, 150, 221))
        m.shut.value = max(0.22 + 0.5 * droop, blink)
        sad.value = 0.7 + 0.3 * droop

    pose(0)
    bpy.context.view_layer.update()
    hip = m.pb('upperleg01.L').matrix.translation
    m.arm.location = (0, 0, 0.47 - hip.z)
    bpy.context.view_layer.update()

    # ---- the same room as thirty years ago (S03), only emptier
    wall = K.clay('wall', 'grey', wet=0.05, coords='object', scale=0.9)
    dark = K.clay('floor', 'dark', wet=0.15, coords='object', scale=1.2)
    wood = K.clay('wood', 'umber', wet=0.2, coords='object', scale=2.5)
    linen = K.clay('linen', 'slip', wet=0.05, coords='object', scale=2.5)
    fl = fx.grid('floor', 12, 4); K.assign(fl, dark)
    bw = fx.grid('backwall', 12, 4); bw.rotation_euler = (math.radians(90), 0, 0); bw.location = (0, 1.75, 2.0); K.assign(bw, wall)
    fx.box('bedframe', (2.25, 1.12, 0.26), (-0.30, 0.62, 0.13), wood, bevel=0.03)
    fx.box('headboard', (0.08, 1.16, 0.60), (0.85, 0.62, 0.30), wood, bevel=0.03)
    fx.box('mattress', (2.15, 1.05, 0.22), (-0.30, 0.60, 0.36), linen, bevel=0.07, subdiv=10, noise=0.012, seed=3)
    fx.box('pillow', (0.42, 0.72, 0.15), (0.53, 0.62, 0.53), K.clay('pillow', 'white', wet=0.05, coords='object', scale=3),
           bevel=0.07, subdiv=8, noise=0.02, seed=5)
    bl = fx.grid('blanket', 1.0, 90); P = fx.co(bl)
    P[:, 0] = P[:, 0] * 1.25 - 0.75; P[:, 1] = P[:, 1] * 1.12 + 0.62
    P[:, 2] = 0.485 + 0.012 * fx.fbm2(P[:, 0] * 3 + 1, P[:, 1] * 3 + 2, seed=6, octaves=4)      # neatly made: nobody sleeps here
    fx.set_co(bl, P); K.assign(bl, K.clay('blanket', 'earth', wet=0.05, coords='object', scale=3))
    s = bl.modifiers.new('s', 'SOLIDIFY'); s.thickness = 0.03
    fx.box('table', (0.46, 0.42, 0.62), (1.18, 1.45, 0.31), wood, bevel=0.025)
    fx.lathe('lampbase', [(0.0, 0), (0.075, 0), (0.07, 0.02), (0.022, 0.04), (0.016, 0.26), (0.0, 0.27)], (1.16, 1.42, 0.62), wood)
    shade_m = K.clay('shade', 'slip', wet=0.0, coords='object', scale=6)
    bs = shade_m.node_tree.nodes['Principled BSDF']
    bs.inputs['Emission Color'].default_value = (1.0, 0.55, 0.22, 1); bs.inputs['Emission Strength'].default_value = 2.4
    fx.lathe('shade', [(0.085, 0.0), (0.135, -0.19)], (1.16, 1.42, 1.05), shade_m)
    lamp = C.light(sc, 'POINT', (1.16, 1.42, 0.92), 150, color=(1.0, 0.62, 0.32), size=0.05, name='lamp')
    # foreground: the clock and the telephone that does not ring
    fx.box('stand', (0.74, 0.36, 0.87), (-0.36, -1.18, 0.435), wood, bevel=0.03)
    fx.box('clock', (0.19, 0.075, 0.085), (-0.17, -1.20, 0.915), K.clay('clockbody', 'dark', wet=0.5, coords='object', scale=8), bevel=0.012)
    dm = K.emission('digits', (1.0, 0.16, 0.04), 9.0)
    digits = fx.text('digits', '3:07', 0.062, (-0.17, -1.2395, 0.917), (math.radians(90), 0, 0), dm)
    glow = C.light(sc, 'POINT', (-0.17, -1.30, 0.92), 0.12, color=(1.0, 0.2, 0.06), size=0.03, name='clockglow')
    telephone((-0.50, -1.16, 0.872), K.clay('phone', 'terracotta', wet=0.55, coords='object', scale=6),
              K.clay('phonedial', 'slip', wet=0.3, coords='object', scale=8))
    key = C.light(sc, 'AREA', (-0.25, -1.9, 1.5), 5, color=(1.0, 0.7, 0.5), target=(-0.5, -1.16, 0.95), size=0.5, name='phonekey')
    face_fill = C.light(sc, 'AREA', (-0.25, -1.0, 0.42), 6, color=(1.0, 0.66, 0.42), target=(0, -0.1, 1.15), size=0.7, name='facefill')
    bounce = C.light(sc, 'AREA', (1.4, -1.2, 0.5), 9, color=(1.0, 0.6, 0.35), target=(0, 0, 0.9), size=1.5, name='bounce')
    moon = C.light(sc, 'AREA', (-2.6, -1.6, 2.6), 70, color=(0.42, 0.56, 1.0), target=(0, 0, 0.9), size=1.6, name='moon')

    face = m.arm.matrix_world @ m.pb('head').matrix.translation + Vector((0, -0.08, 0.08))
    cam = C.camera(sc, CAM0, (0.0, -0.1, 0.98), lens=40, fstop=1.8, name='cam')
    cam0 = Vector(CAM0)
    aim0 = Vector(AIM0); aim1 = Vector((0.0, -0.25, 0.99))
    fg = Vector((-0.36, -1.22, 0.95))
    sm = fx.smooth

    def update(f):
        t = f / 24.0
        pose(f)
        digits.data.body = '3:08' if f >= 168 else '3:07'     # a minute passes
        p = sm(f, 0, FRAMES - 1)
        cam.location = cam0 + Vector(CAM_MOVE) * p
        C.look_at(cam, aim0.lerp(aim1, sm(f, 40, FRAMES - 1)))
        fx.shake(cam, f, 0.0010, seed=13)
        r = sm(f, 58, 96)                                # rack focus from the telephone to her
        d0 = (cam.location - fg).length; d1 = (cam.location - face).length
        cam.data.dof.focus_distance = d0 + (d1 - d0) * r
        lamp.data.energy = 150 * (1 + 0.03 * math.sin(t * 13) * math.sin(t * 7.1))

    return dict(frames=FRAMES, update=update)


LOOK = -14           # head turned towards the telephone (degrees)
ARM_Y, FORE_TW = 8, 20
CAM0 = (-0.10, -2.12, 1.10)
AIM0 = (-0.22, -0.9, 0.98)
CAM_MOVE = (0.12, 0.50, -0.12)
