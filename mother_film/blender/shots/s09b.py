"""S09B Sunrise. In profile: the son, still on his knees, lifts his head and looks up at his mother; her hand
strokes his hair. (Follows the close-up of her smile; the film fades out on this.)"""
import bpy, math
import numpy as np
from mathutils import Vector, Matrix
import common as C, clay as K, fx, cast
from shots import tableau

FRAMES = 120


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.66, 0.44, 0.30, 1); bg.inputs[1].default_value = 0.22
    st = tableau.make(sc, wet=0.8, eyes=True, eye_tint='white')
    m, s = st['m'], st['s']
    cast.add_eyes(s, tint='white')
    K.setp(m.mat, 'cracks', 0.07)
    smile = m.add_shape('smile', {'mouth-corner-puller': 1.0, 'mouth-elevation': 0.15, 'eye-left-slit': 0.25, 'eye-right-slit': 0.25}, 0.9)
    for mat in (m.mat, m.scarf_mat, s.mat, s.hair_mat):
        K.add_droplets(mat, scale=210.0, amount=0.16)
    sky, e = fx.emit_plane('sky', (120, 40), (0, 30, 16), (90, 0, 0), color=(0.95, 0.62, 0.35), strength=0.5)
    top = C.light(sc, 'AREA', (-2, -2, 6), 600, color=(0.55, 0.66, 1.0), target=(0.4, 0, 0.5), size=6.0, name='top')
    sun_dir = Vector((-0.80, 0.50, -0.10)).normalized()
    sun = C.light(sc, 'SUN', (0, 0, 10), 5.0, color=(1.0, 0.64, 0.36), size=0.012, name='sun')
    sun.rotation_mode = 'QUATERNION'; sun.rotation_quaternion = sun_dir.to_track_quat('-Z', 'Y')
    fill = C.light(sc, 'AREA', (0.6, -3.0, 1.2), 90, color=(1.0, 0.72, 0.50), target=(0.4, 0, 1.0), size=2.5, name='fill')
    drops = fx.Motes(sc, 300, (0.4, -0.5, 0.0), 2.6, 2.6, size=0.0035, seed=6, color=(1.0, 0.85, 0.6), emit=0.25,
                     drift=(0.0, 0.0, -0.05))
    cam = C.camera(sc, CAM, AIM, lens=40, fstop=2.8, name='cam')
    sm = fx.smooth
    hl, hr, th = st['hl'], st['hr'], st['hand']
    st['pole'].location = POLE                          # her elbow hangs down instead of sticking up

    def update(f):
        rise = sm(f, 10, 78)                                # he straightens up
        up = sm(f, 30, 96)                                  # and lifts his face to her
        st['pose_son'](1.0 - 0.82 * rise)
        s.rot('neck01', 'X', -30 * up); s.rot('head', 'X', -46 * up)
        s.shut.value = 1.0 - 0.9 * sm(f, 50, 84)
        s.grief.value = 0.7 - 0.55 * up
        bpy.context.view_layer.update()
        head = s.arm.matrix_world @ s.pb('head').matrix @ Vector((0, 0.13, 0))
        thigh = s.arm.matrix_world @ s.pb('upperleg02.L').matrix.translation
        for e_, sy in ((hl, -1), (hr, 1)):
            a0 = Vector((0.20, sy * 0.15, 0.04)); a1 = Vector((thigh.x - 0.10, sy * 0.15, thigh.z + 0.09))
            e_.location = a0.lerp(a1, rise) + Vector((0, 0, 0.10 * math.sin(rise * math.pi)))
        breath = math.sin(f / 24.0 * 2 * math.pi / 3.6)
        st['pose_mother'](bend=0.6 + 0.035 * breath - 0.15 * up, head=14 + 4 * up)
        m.rot('eye.L', 'X', 10); m.rot('eye.R', 'X', 10)
        m.shut.value = max(0.08, math.exp(-((f - 66) / 2.6) ** 2))
        stroke = math.sin(f / 24.0 * 2 * math.pi / 2.8)
        # her hand: on his hair while he is bowed, then it slides down to cup his cheek as he looks up
        skull = s.arm.matrix_world @ s.pb('head').matrix.translation
        on_hair = Vector((head.x - 0.01, head.y - 0.03, max(head.z + 0.012, 0.5)))
        on_cheek = skull + Vector((-0.085, -0.085, 0.045))
        th.location = on_hair.lerp(on_cheek, sm(f, 40, 92)) + Vector((0.012 * stroke, 0, 0.006 * stroke))
        p = sm(f, 0, FRAMES - 1)
        cam.location = Vector(CAM) + Vector((-0.05, 0.35, 0.03)) * p
        C.look_at(cam, Vector(AIM) + Vector((0, 0, 0.22)) * sm(f, 0, 90))
        fx.shake(cam, f, 0.0007, seed=21)
        cam.data.dof.focus_distance = abs(cam.location.y) - 0.05
        drops.update(f * 0.3)

    return dict(frames=FRAMES, update=update)


CAM = (0.62, -3.1, 0.95)
AIM = (0.42, 0.0, 0.80)
POLE = (0.30, -0.45, 0.0)
