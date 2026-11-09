"""S02 (0:09-0:13) Lightning splits the sky behind the mountains; the newborn's first cry shakes them."""
import bpy, math
import numpy as np
from mathutils import Vector, Quaternion
import common as C, clay as K, fx, cast, mhlib as M, garments as G

FRAMES = 96
START = 216
CUT = 36           # frame where we cut from the mountains to the child


def flash(f):
    """Lightning intensity per frame (two strikes, afterglow, a distant flicker)."""
    tab = {0: 1.0, 1: 0.8, 2: 0.4, 3: 0.1, 4: 0.95, 5: 0.6, 6: 0.28, 13: 0.3, 14: 0.18, 22: 0.22, 23: 0.1}
    return max(tab.get(f, 0.0), 0.22 * math.exp(-(f - 6) / 5.0) if f >= 6 else 0)


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    rs = np.random.RandomState(7)

    # ---------------- A: mountains ----------------
    def hf(X, Y):
        band = np.exp(-((Y - 14) / 11.0) ** 2)
        r = fx.fbm2(X * 0.04 + 3, Y * 0.04 + 9, seed=1, octaves=7, ridged=True)
        big = fx.fbm2(X * 0.02 + 1, Y * 0.02 + 5, seed=4, octaves=3)
        peaks = np.clip(r * 0.55 + 0.45 + big * 0.7, 0, None) ** 2.2
        return band * peaks * 22.0 + fx.fbm2(X * 0.2, Y * 0.2, seed=8, octaves=4) * 0.25 * (1 - band)
    ter = fx.terrain('mountains', (-70, 70), (-34, 40), 620, 330, hf)
    tm = K.clay('mountain', 'rock', wet=0.25, coords='object', scale=0.085, tex='cliff_side', bump=1.6)
    K.assign(ter, tm)
    # storm sky: emissive backdrop, clouds lit from within by the flash
    H, W = 384, 1024
    yy, xx = np.mgrid[0:H, 0:W]
    cl = fx.fbm2(xx / 150.0, yy / 70.0, seed=3, octaves=6) * 0.5 + 0.5
    cl = np.clip((cl - 0.25) * 1.6, 0, 1) ** 1.5
    bx, by = 0.44 * W, 0.55 * H
    glow = np.exp(-(((xx - bx) / (0.22 * W)) ** 2 + ((yy - by) / (0.6 * H)) ** 2)) + 0.12
    img = fx.float_image('sky', np.stack([cl, glow * (0.12 + 0.88 * cl ** 1.5), cl * 0 + 1], 2))
    bpy.ops.mesh.primitive_plane_add(size=1)
    sky = bpy.context.object; sky.name = 'sky'
    sky.scale = (260, 100, 1); sky.rotation_euler = (math.radians(90), 0, 0); sky.location = (0, 60, 30)
    sm_ = bpy.data.materials.new('sky'); sm_.use_nodes = True
    nt = sm_.node_tree; N = nt.nodes
    for n in list(N):
        if n.type != 'OUTPUT_MATERIAL':
            N.remove(n)
    tex = N.new('ShaderNodeTexImage'); tex.image = img; tex.extension = 'EXTEND'
    sep = N.new('ShaderNodeSeparateColor'); nt.links.new(tex.outputs['Color'], sep.inputs[0])
    fl = N.new('ShaderNodeValue'); fl.name = 'flash'
    m1 = N.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; nt.links.new(sep.outputs[1], m1.inputs[0]); nt.links.new(fl.outputs[0], m1.inputs[1])
    m2 = N.new('ShaderNodeMath'); m2.operation = 'MULTIPLY_ADD'; nt.links.new(sep.outputs[0], m2.inputs[0])
    m2.inputs[1].default_value = 0.05; nt.links.new(m1.outputs[0], m2.inputs[2])
    em = N.new('ShaderNodeEmission'); em.inputs[0].default_value = (0.55, 0.68, 1.0, 1)
    nt.links.new(m2.outputs[0], em.inputs['Strength']); nt.links.new(em.outputs[0], N['Material Output'].inputs['Surface'])
    sky.data.materials.append(sm_)
    bolt_obs, bolt_set, main = fx.lightning(sc, rs, (-6, 44, 72), (-9, 44, 3), width=0.32, branches=7)
    strike = C.light(sc, 'POINT', (-8, 46, 34), 0, color=(0.7, 0.8, 1.0), size=3.0, name='strike')
    moon = C.light(sc, 'SUN', (0, 0, 50), 0.35, color=(0.45, 0.6, 1.0), rot=(55, 0, 160), size=0.3, name='moon')
    camA = C.camera(sc, (4, -26, 2.6), (0, 14, 9.5), lens=28, name='camA')
    A = [ter, sky, strike, moon] + bolt_obs

    # ---------------- B: the child ----------------
    OFF = Vector((0, 0, -200))                 # the second set lives far below the first
    h = M.Human('baby', {'macrodetails/caucasian-male-baby': 1.0})
    G.finish(h, 1)
    h.add_shape('shut', {'eye-left-closure': 0.9, 'eye-right-closure': 0.9}, 1.0)
    cry = h.add_shape('cry', {'mouth-open': 1.0, 'mouth-retraction': 0.5, 'eyebrows-left-down': 0.9, 'eyebrows-right-down': 0.9,
                              'eyebrows-left-inner-up': 0.35, 'eyebrows-right-inner-up': 0.35, 'nose-left-elevation': 0.8,
                              'nose-right-elevation': 0.8, 'mouth-elevation': 0.15}, 1.0)
    bm = K.clay('baby2', 'terracotta', wet=0.55, scale=7.0)
    K.assign(h.body, bm)
    h.both('upperarm01', 'Y', -18); h.flex2('upperarm01', 20); h.flex2('lowerarm01', 118)
    h.curl_fingers('L', 85, 50); h.curl_fingers('R', 85, 50)
    h.flex2('upperleg01', 55); h.both('upperleg01', 'Y', -18); h.flex2('lowerleg01', -80)
    h.rot('head', 'X', -10)
    h.arm.rotation_euler = (math.radians(-90), 0, 0)
    h.arm.location = OFF + Vector((0, 0, 0.085))
    bpy.context.view_layer.update()
    base = {pb.name: pb.rotation_quaternion.copy() for pb in h.arm.pose.bones}
    head_w = h.arm.matrix_world @ h.pb('head').matrix.translation
    g = fx.grid('ground2', 5.0, 220, center=tuple(OFF))
    Gc = fx.co(g)
    Gc[:, 2] += fx.fbm2(Gc[:, 0] * 1.3 + 7, Gc[:, 1] * 1.3 + 3, seed=2, octaves=5) * 0.02
    fx.set_co(g, Gc)
    K.assign(g, K.clay('ground2', 'dark', wet=0.3, coords='object', bump=1.2, cracks=0.6, scale=1.6,
                       tex='brown_mud_02', crack_scale=2.4))
    face = head_w + Vector((0, 0.03, 0.03))
    camB = C.camera(sc, face + Vector((0.16, -0.26, 0.66)), face, lens=85, fstop=2.8, name='camB')
    camB_loc = camB.location.copy()
    kB = C.light(sc, 'AREA', face + Vector((-0.9, 0.5, 1.0)), 0, color=(0.72, 0.82, 1.0), target=face, size=0.5, name='kB')
    fB = C.light(sc, 'AREA', face + Vector((0.8, -0.6, 0.35)), 0, color=(1.0, 0.62, 0.38), target=face, size=0.8, name='fB')
    motes = fx.Motes(sc, 300, tuple(face + Vector((0, 0, -0.1))), 0.6, 0.8, size=0.0013, seed=9, drift=(0.01, 0.0, -0.25))
    B = [h.body, g, kB, fB, motes.ob] + list(motes.ob.children)
    trem = ['upperarm01.L', 'upperarm01.R', 'lowerarm01.L', 'lowerarm01.R', 'head', 'neck01', 'upperleg01.L', 'upperleg01.R']
    ph = rs.uniform(0, 6.28, (len(trem), 3))

    def update(f):
        a = f < CUT
        for o in A:
            o.hide_render = not a
        for o in B:
            o.hide_render = a
        low = fx.env(START + f, 'low', 1); loud = fx.env(START + f, 'all', 1)
        if a:
            I = flash(f)
            bolt_set(I if I > 0.35 else 0.0)
            N['flash'].outputs[0].default_value = 0.03 + 2.4 * I
            strike.data.energy = 2.2e5 * I
            p = f / CUT
            camA.location = Vector((4 - 0.6 * p, -26 + 2.0 * p, 2.6 + 0.2 * p))
            C.look_at(camA, (0, 14, 9.5))
            fx.shake(camA, f, 0.0035 * (0.4 + 1.5 * low) * min(1, f / 3), seed=1)
            sc.camera = camA
        else:
            k = f - CUT
            v = min(1.0, 0.55 + 0.75 * loud)
            cry.value = v
            for i, bn in enumerate(trem):
                pb = h.pb(bn)
                amp = (0.05 if 'arm' in bn else 0.025) * (0.5 + loud)
                q = Quaternion((1, 0, 0), amp * math.sin(k * 1.9 + ph[i, 0])) @ Quaternion((0, 0, 1), amp * math.sin(k * 2.6 + ph[i, 1]))
                pb.rotation_quaternion = base[bn] @ q
            I = max(flash(k + 4) * 0.8, 0.5 * math.exp(-((k - 30) / 2.0) ** 2), 0.8 * math.exp(-((k - 33) / 1.2) ** 2))
            kB.data.energy = 11 + 260 * I
            fB.data.energy = 9
            p = k / (FRAMES - CUT)
            camB.location = camB_loc + (face - camB_loc) * (0.10 * p)
            C.look_at(camB, face)
            camB.data.dof.focus_distance = (camB.location - (face + Vector((0, -0.03, 0.05)))).length
            fx.shake(camB, f, 0.004 * (0.5 + 1.2 * low), seed=2)
            motes.update(k)
            sc.camera = camB

    return dict(frames=FRAMES, update=update)
