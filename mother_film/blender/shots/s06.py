"""S06 (0:31-0:36) The grown son kneels before his old mother. His eyes fall to her worn bare feet -
and light pours from the earth beneath them. The first drops of rain."""
import bpy, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
import common as C, clay as K, fx, cast, mhlib as M, garments as G

FRAMES = 120
START = 744


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.20, 0.24, 0.34, 1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.06
    m = cast.mother(age=1.0, scarf_tint='white', robe_tint='grey', hem=0.115, flare=0.14)
    K.setp(m.mat, 'cracks', 0.6); K.setp(m.robe_mat, 'cracks', 0.07); K.setp(m.scarf_mat, 'cracks', 0.14)
    K.set_tint(m.mat, 'terracotta', 'buff', 0.35)
    s = cast.son()
    Rm = Matrix.Rotation(math.radians(90), 4, 'Z'); Rs = Matrix.Rotation(math.radians(-90), 4, 'Z')
    SX = 0.78                                           # son's knees are this far in front of her
    # her hand on his head
    th, phd = m.ik_arm('R', (0.5, -0.2, 1.0), (0.3, -0.7, 2.2), math.radians(-90))
    # his hands will come down to her feet
    hl, _ = s.ik_arm('L', (0.4, -0.15, 0.5), None)
    hr, _ = s.ik_arm('R', (0.4, 0.15, 0.5), None)

    # ---- courtyard at dusk before the storm
    earth = K.clay('earth', 'earth', wet=0.12, coords='object', scale=0.7, tex='brown_mud_02', cracks=0.9, crack_scale=1.7)
    K.add_crack_glow(earth, (0.06, 0.0, 0.0), 1.5)
    g = fx.grid('ground', 30, 200); P = fx.co(g)
    P[:, 2] = fx.fbm2(P[:, 0] * 0.6, P[:, 1] * 0.6, seed=3, octaves=4) * 0.012
    fx.set_co(g, P); K.assign(g, earth)
    wallm = K.clay('wall', 'buff', wet=0.03, coords='object', scale=0.5)
    fx.box('wall', (26, 0.5, 3.4), (0, 3.9, 1.7), wallm, bevel=0.06, subdiv=6, noise=0.03)
    fx.box('door', (1.15, 0.2, 2.2), (-2.3, 3.62, 1.1), K.clay('door', 'dark', wet=0.1, coords='object'), bevel=0.05)
    dusk = C.light(sc, 'AREA', (-3.0, -3.5, 3.5), 520, color=(0.50, 0.60, 0.95), target=(0.4, 0, 0.8), size=3.0, name='dusk')
    rim = C.light(sc, 'AREA', (3.5, 3.0, 2.2), 420, color=(1.0, 0.62, 0.38), target=(0.4, 0, 0.9), size=1.2, name='rim')
    gold = C.light(sc, 'AREA', (0.10, 0.0, 0.02), 0, color=(1.0, 0.62, 0.20), size=0.5, name='gold')
    gold.rotation_mode = 'XYZ'; gold.rotation_euler = (math.radians(180), 0, 0)
    rays_ob, rays_set = fx.rays(sc, (0.08, 0.0, 0.0), 16, 2.4, 0.16, seed=4)
    motes = fx.Motes(sc, 420, (0.3, 0.0, 0.0), 1.6, 1.9, size=0.0022, seed=4, color=(1.0, 0.75, 0.45), emit=0.05,
                     drift=(0.01, 0.0, 0.02))
    rain = fx.Rain(sc, 900, (-2.5, -2.2, 0.0), (3.5, 2.5, 4.0), width=0.004, seed=2, strength=0.7)
    cam = C.camera(sc, (0.5, -1.7, 1.0), (0.7, 0, 1.0), lens=50, fstop=2.0, name='cam')
    sm = fx.smooth

    def update(f):
        low = fx.env(START + f, 'low', 2)
        bow = sm(f, 26, 98)
        # ---- mother: old, a little stooped, her hand trembling on his head
        for pb in m.arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
        m.rot('spine05', 'X', 8); m.rot('spine03', 'X', 9); m.rot('spine01', 'X', 8)
        m.rot('neck01', 'X', 10); m.rot('head', 'X', 14 + 6 * bow)
        m.flex('upperarm01.L', 4); m.rot('upperarm01.L', 'Y', 26); m.flex('lowerarm01.L', 18)
        m.curl_fingers('L', 30, 12); m.curl_fingers('R', 22, 8)
        m.arm.matrix_world = Rm
        # ---- son: kneeling, bowing down to her feet
        s.reset_pose()
        s.flex2('upperleg01', 12 + 78 * bow); s.flex2('lowerleg01', -112 - 26 * bow)
        s.flex2('foot', -50)
        lean = 6 + 62 * bow
        s.rot('spine05', 'X', lean * 0.42); s.rot('spine03', 'X', lean * 0.33); s.rot('spine01', 'X', lean * 0.25)
        s.rot('neck01', 'X', 10 + 6 * bow); s.rot('head', 'X', 16 + 10 * bow)
        s.curl_fingers('L', 14, 6); s.curl_fingers('R', 14, 6)
        s.arm.matrix_world = Matrix.Translation((SX, 0, 0)) @ Rs
        bpy.context.view_layer.update()
        knee = (s.arm.matrix_world @ s.pb('lowerleg01.L').matrix.translation)
        s.arm.matrix_world = Matrix.Translation((SX + (SX - knee.x) * 0 + 0.0, 0, 0.065 - knee.z)) @ Rs
        bpy.context.view_layer.update()
        head = s.arm.matrix_world @ s.pb('head').matrix @ Vector((0, 0.13, 0))
        thigh = s.arm.matrix_world @ s.pb('upperleg02.L').matrix.translation
        reach = sm(f, 34, 92)
        for e, sy in ((hl, -1), (hr, 1)):
            a0 = Vector((thigh.x - 0.10, sy * 0.15, thigh.z + 0.09))
            a1 = Vector((0.20, sy * 0.15, 0.04))
            e.location = a0.lerp(a1, reach) + Vector((0, 0, 0.12 * math.sin(reach * math.pi)))
        trem = Vector((math.sin(f * 2.1) * 0.004, math.sin(f * 2.7 + 1) * 0.004, math.sin(f * 3.3) * 0.003))
        th.location = Vector((head.x - 0.02, head.y - 0.03, max(head.z + 0.01, 0.80))) + trem
        s.grief.value = 0.6 + 0.4 * bow
        # ---- light from beneath her feet
        gl = sm(f, 46, 100) ** 1.5; burst = sm(f, 98, 116)
        pulse = 1 + 0.08 * math.sin(f * 0.9)
        K.setp(earth, 'glow', (5 * gl + 16 * burst) * pulse)
        gold.data.energy = (110 * gl + 330 * burst) * pulse
        rays_set((0.28 * gl + 0.9 * burst) * pulse, 0.35 + 0.25 * gl + 0.55 * burst)
        dusk.data.energy = 520 * (1 - 0.3 * burst)
        motes.update(f * 0.4)
        rain.update(f, intensity=0.04 + 0.5 * sm(f, 20, 119) ** 2, speed=2.6, t=f / 24.0)
        # ---- camera: from his face down to her feet
        tilt = sm(f, 22, 86)
        cam.location = Vector((0.52, -1.75, 1.06)).lerp(Vector((0.36, -1.95, 0.13)), tilt) + Vector((0, 0.15, 0)) * sm(f, 86, 119)
        aim = Vector((0.50, 0.0, 1.12)).lerp(Vector((0.30, 0.0, 0.17)), tilt)
        C.look_at(cam, aim)
        fx.shake(cam, f, 0.0008 + 0.0022 * low * sm(f, 20, 60), seed=6)
        cam.data.dof.focus_distance = (cam.location - aim).length

    return dict(frames=FRAMES, update=update)
