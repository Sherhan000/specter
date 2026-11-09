"""S03 (0:13-0:20) 3:07 AM. The young mother rocks her crying child and whispers a prayer."""
import bpy, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
import common as C, clay as K, fx, cast, mhlib as M, garments as G

FRAMES = 168
START = 312


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    m = cast.mother()
    b = cast.swaddled()
    cast.sit_cradle(m)
    bpy.context.view_layer.update()
    hip = m.pb('upperleg01.L').matrix.translation
    m.arm.location = (0, 0, 0.47 - hip.z)
    bpy.context.view_layer.update()
    ch = m.arm.matrix_world @ m.pb('spine02').matrix.translation
    zd = Vector((0.80, -0.05, 0.45)).normalized()
    C0 = Vector((0.02, ch.y - 0.235, ch.z - 0.06))
    W = cast.frame_matrix(C0 - zd * 0.33, zd, (0.0, -0.55, 0.8))
    loc = cast.attach_local(W, m, 'spine02')
    cast.attach(b, m, 'spine02', loc)
    tl, pl = m.ik_arm('L', C0 + zd * 0.15 + Vector((0.0, -0.07, -0.085)), (0.9, 0.1, 0.3), math.radians(90))
    tr, pr = m.ik_arm('R', C0 - zd * 0.10 + Vector((0.0, -0.09, 0.075)), (-0.9, 0.1, 0.5), math.radians(-125))
    for e in (tl, tr):                                  # hands travel with the child
        mw = e.matrix_world.copy(); e.parent = b.arm; e.matrix_world = mw
    m.curl_fingers('L', 32, 10); m.curl_fingers('R', 32, 10)
    whisper = m.add_shape('whisper', {'mouth-open': 0.5, 'mouth-pursing': 0.4}, 0.0)
    base = {pb.name: pb.rotation_quaternion.copy() for pb in m.arm.pose.bones}

    # ---- the room
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
    P[:, 2] = 0.485 + 0.035 * fx.fbm2(P[:, 0] * 3 + 1, P[:, 1] * 3 + 2, seed=6, octaves=4) + 0.03 * np.sin(P[:, 0] * 9 + P[:, 1] * 4)
    fx.set_co(bl, P); K.assign(bl, K.clay('blanket', 'earth', wet=0.05, coords='object', scale=3))
    s = bl.modifiers.new('s', 'SOLIDIFY'); s.thickness = 0.03
    # bedside table + lamp (behind her, camera right)
    fx.box('table', (0.46, 0.42, 0.62), (1.18, 1.45, 0.31), wood, bevel=0.025)
    fx.lathe('lampbase', [(0.0, 0), (0.075, 0), (0.07, 0.02), (0.022, 0.04), (0.016, 0.26), (0.0, 0.27)], (1.16, 1.42, 0.62), wood)
    shade_m = K.clay('shade', 'slip', wet=0.0, coords='object', scale=6)
    bs = shade_m.node_tree.nodes['Principled BSDF']
    bs.inputs['Emission Color'].default_value = (1.0, 0.55, 0.22, 1); bs.inputs['Emission Strength'].default_value = 3.2
    fx.lathe('shade', [(0.085, 0.0), (0.135, -0.19)], (1.16, 1.42, 1.05), shade_m)
    lamp = C.light(sc, 'POINT', (1.16, 1.42, 0.92), 230, color=(1.0, 0.62, 0.32), size=0.05, name='lamp')
    # the clock, close to the lens
    fx.box('stool', (0.34, 0.34, 0.87), (-0.60, -1.18, 0.435), wood, bevel=0.03)
    fx.box('clock', (0.19, 0.075, 0.085), (-0.60, -1.20, 0.915), K.clay('clockbody', 'dark', wet=0.5, coords='object', scale=8), bevel=0.012)
    digits = fx.text('digits', '3:07', 0.062, (-0.60, -1.2395, 0.917), (math.radians(90), 0, 0), K.emission('digits', (1.0, 0.16, 0.04), 9.0))
    glow = C.light(sc, 'POINT', (-0.60, -1.30, 0.92), 0.12, color=(1.0, 0.2, 0.06), size=0.03, name='clockglow')
    face_fill = C.light(sc, 'AREA', (-0.25, -1.0, 0.42), 9, color=(1.0, 0.66, 0.42), target=(0, -0.1, 1.15), size=0.7, name='facefill')
    bounce = C.light(sc, 'AREA', (1.4, -1.2, 0.5), 14, color=(1.0, 0.6, 0.35), target=(0, 0, 0.9), size=1.5, name='bounce')
    moon = C.light(sc, 'AREA', (-2.6, -1.6, 2.6), 48, color=(0.42, 0.56, 1.0), target=(0, 0, 0.9), size=1.6, name='moon')

    face = m.arm.matrix_world @ m.pb('head').matrix.translation + Vector((0, -0.08, 0.08))
    cam = C.camera(sc, (-0.62, -2.05, 1.0), (0.05, -0.1, 0.98), lens=40, fstop=1.8, name='cam')
    cam0 = cam.location.copy()
    aim0 = Vector((0.05, -0.1, 0.97)); aim1 = Vector((0.08, -0.16, 0.90))
    clock_p = Vector((-0.60, -1.24, 0.92))
    sm = fx.smooth

    def update(f):
        t = f / 24.0
        loud = fx.env(START + f, 'all', 2)
        # rocking: sway of the whole torso, a small nod, and a slow bow towards the child at the end
        for bn in ('spine05', 'spine03', 'neck01', 'head'):
            m.pb(bn).rotation_quaternion = base[bn]
        bpy.context.view_layer.update()
        sway = math.sin(t * 2 * math.pi / 2.5)
        kiss = sm(f, 112, 156)
        m.rot('spine05', 'Y', 4.2 * sway); m.rot('spine05', 'X', 1.2 * math.sin(t * 2 * math.pi / 1.25 + 0.6))
        m.rot('spine03', 'X', 4 * kiss)
        m.rot('neck01', 'X', 4 * kiss); m.rot('head', 'X', 4 * kiss + 1.0 * math.sin(t * 2.1)); m.rot('head', 'Y', -2.0 * sway)
        lift = Matrix.Translation(Vector((0.03, 0.0, 0.11)) * kiss)
        cast.attach(b, m, 'spine02', loc)
        b.arm.matrix_world = lift @ b.arm.matrix_world
        whisper.value = (0.25 + 0.25 * math.sin(t * 9.0) * math.sin(t * 5.3)) * (1 - kiss)
        b.cry.value = max(0.12, (0.45 + 0.6 * loud) * (1 - 0.8 * sm(f, 80, 150)))
        # camera: starts on the clock, racks to her, drifts in
        p = sm(f, 0, FRAMES - 1)
        cam.location = cam0 + Vector((0.16, 0.56, -0.20)) * p
        C.look_at(cam, aim0.lerp(aim1, p))
        fx.shake(cam, f, 0.0012, seed=3)
        r = sm(f, 30, 58)
        d0 = (cam.location - clock_p).length; d1 = (cam.location - face).length
        cam.data.dof.focus_distance = d0 + (d1 - d0) * r
        lamp.data.energy = 230 * (1 + 0.03 * math.sin(t * 13) * math.sin(t * 7.1))

    return dict(frames=FRAMES, update=update)
