"""S08 (0:43-0:44) Silence. The rain has stopped; the last drops hang in the blue air before dawn."""
import bpy, math
import numpy as np
from mathutils import Vector, Matrix
import common as C, clay as K, fx
from shots import tableau

FRAMES = 24
START = 1032


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.16, 0.24, 0.42, 1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.22
    st = tableau.make(sc, wet=0.9)
    sky, e = fx.emit_plane('sky', (120, 40), (0, 30, 16), (90, 0, 0), color=(0.20, 0.30, 0.55), strength=0.5)
    dawn = C.light(sc, 'AREA', (9, -3, 2.0), 260, color=(1.0, 0.62, 0.42), target=(0.4, 0, 0.9), size=4.0, name='dawn')
    top = C.light(sc, 'AREA', (-2, -2, 6), 1300, color=(0.45, 0.6, 1.0), target=(0.4, 0, 0.5), size=6.0, name='top')
    drops = fx.Motes(sc, 650, (0.4, -0.5, 0.0), 3.2, 3.0, size=0.0045, seed=5, color=(0.85, 0.92, 1.0), emit=0.25,
                     drift=(0.0, 0.0, -0.03))
    m = drops.ob.children[0].data.materials[0].node_tree.nodes['Principled BSDF']
    m.inputs['Roughness'].default_value = 0.05
    cam = C.camera(sc, (0.9, -4.3, 0.85), (0.38, 0, 0.95), lens=40, fstop=2.8, name='cam')

    def update(f):
        drops.update(f * 0.25)
        cam.location = Vector((0.9 - 0.02 * f / 24, -4.3 + 0.05 * f / 24, 0.85))
        C.look_at(cam, (0.38, 0, 0.95))
        cam.data.dof.focus_distance = 4.3

    return dict(frames=FRAMES, update=update)
