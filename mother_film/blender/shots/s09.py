"""S09 (0:44-0:56) Sunrise after the storm. The first warm light crosses her wet face; she opens her eyes,
looks down at her son and smiles."""
import bpy, math
import numpy as np
from mathutils import Vector, Matrix
import common as C, clay as K, fx
from shots import tableau

FRAMES = 288
START = 1056


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.16, 0.24, 0.42, 1); bg.inputs[1].default_value = 0.22
    st = tableau.make(sc, wet=0.8, eyes=True)
    m = st['m']
    K.setp(m.mat, 'cracks', 0.07)
    smile = m.add_shape('smile', {'mouth-corner-puller': 1.0, 'mouth-elevation': 0.15, 'eye-left-slit': 0.25, 'eye-right-slit': 0.25}, 0.0)
    for mat in (m.mat, m.scarf_mat):
        K.add_droplets(mat, scale=210.0, amount=0.20)
    sky, e = fx.emit_plane('sky', (120, 40), (0, 30, 16), (90, 0, 0), color=(0.20, 0.30, 0.55), strength=0.5)
    top = C.light(sc, 'AREA', (-2, -2, 6), 1100, color=(0.45, 0.6, 1.0), target=(0.4, 0, 0.5), size=6.0, name='top')
    # the sun rises in front of her (camera right); a far wall's shadow slides down her face
    st['pose_mother'](bend=0.6, head=20)
    bpy.context.view_layer.update()
    def face_pt():
        bpy.context.view_layer.update()
        return m.arm.matrix_world @ ((m.pb('eye.L').matrix.translation + m.pb('eye.R').matrix.translation) / 2) + Vector((0.02, 0, -0.035))
    face = face_pt()
    sun_dir = Vector((-0.80, 0.50, -0.06)).normalized()           # direction the light travels
    sun = C.light(sc, 'SUN', (0, 0, 10), 0.0, color=(1.0, 0.60, 0.30), size=0.012, name='sun')
    sun.rotation_mode = 'QUATERNION'; sun.rotation_quaternion = sun_dir.to_track_quat('-Z', 'Y')
    bpos = face - sun_dir * 7.0
    blocker = fx.box('blocker', (0.2, 30, 12), (bpos.x, bpos.y, bpos.z - 6), K.clay('blk', 'dark', coords='object'), bevel=0)
    blocker.rotation_euler = (0, 0, math.atan2(sun_dir.y, sun_dir.x))
    blocker.visible_camera = False
    fillb = C.light(sc, 'AREA', face + Vector((0.45, -0.25, -0.75)), 0, color=(1.0, 0.66, 0.40), target=face, size=0.9, name='fillb')
    drops = fx.Motes(sc, 500, (0.4, -0.5, 0.0), 3.0, 3.0, size=0.0035, seed=5, color=(0.9, 0.95, 1.0), emit=0.2,
                     drift=(0.0, 0.0, -0.12))
    drops.ob.children[0].data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.05
    cam = C.camera(sc, face + Vector((0.74, -0.66, -0.36)), face, lens=85, fstop=4.0, name='cam')
    cam0 = cam.location.copy()
    sm = fx.smooth

    def update(f):
        rise = sm(f, 20, 150)
        look = sm(f, 110, 200)
        st['pose_mother'](bend=0.6, head=20 - 9 * look + 0.6 * math.sin(f * 0.05))
        m.rot('eye.L', 'X', 14 - 4 * look); m.rot('eye.R', 'X', 14 - 4 * look)
        m.shut.value = 1.0 - 0.08 * sm(f, 118, 190)
        smile.value = 0.95 * sm(f, 165, 262)
        bpy.context.view_layer.update()
        fc = face_pt()
        # sunrise: shadow line travels from the top of her head down past her chin
        blocker.location.z = bpos.z - 6 + 0.34 - 0.62 * rise
        sun.data.energy = 5.2 * sm(f, 10, 120)
        sun.data.color = (1.0, 0.52 + 0.14 * rise, 0.24 + 0.16 * rise)
        top.data.energy = 1100 * (1 - 0.45 * rise)
        fillb.data.energy = 13 * rise
        warm = sm(f, 60, 260)
        e.inputs[0].default_value = (0.20 + 0.75 * warm, 0.30 + 0.32 * warm, 0.55 - 0.2 * warm, 1)
        bg.inputs[0].default_value = (0.16 + 0.5 * warm, 0.24 + 0.2 * warm, 0.42 - 0.12 * warm, 1)
        drops.update(f * 0.3)
        p = sm(f, 0, FRAMES - 1)
        cam.location = cam0.lerp(fc + (cam0 - face) * 0.78, p)
        C.look_at(cam, fc + Vector((0, 0, -0.012)))
        fx.shake(cam, f, 0.0005, seed=9)
        cam.data.dof.focus_distance = (cam.location - fc).length - 0.02

    return dict(frames=FRAMES, update=update)
