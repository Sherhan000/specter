"""S04 He is three. In three cuts, at real speed: the boy runs across the courtyard, trips and falls (wide);
his mother's face - the fear hits her before he has even cried (close-up); she is on her knees, holding him
tight, rocking him (medium)."""
import bpy, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix, Euler
import common as C, clay as K, fx, cast

FRAMES = 144
CUT_B, CUT_C = 50, 86        # first frames of the close-up and of the embrace
TRIP, LAND = 34, 45          # the boy trips / hits the ground


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.42, 0.32, 1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.10
    k = cast.child(tint='teal')
    m = cast.mother(shut=0.0)
    cast.add_eyes(m, tint='white')
    fear = m.add_shape('fear', {'mouth-open': 0.7, 'eyebrows-left-up': 1.0, 'eyebrows-right-up': 1.0, 'eyebrows-left-inner-up': 0.8,
                                'eyebrows-right-inner-up': 0.8, 'eye-left-opened-up': 1.0, 'eye-right-opened-up': 1.0}, 0.0)
    tender = m.add_shape('tender', {'eyebrows-left-inner-up': 0.9, 'eyebrows-right-inner-up': 0.9, 'mouth-compression': 0.3}, 0.0)
    Rk = Matrix.Rotation(math.radians(90), 4, 'Z')          # facing +X
    Rm = Matrix.Rotation(math.radians(90), 4, 'Z')
    Rk_in = Matrix.Rotation(math.radians(-90), 4, 'Z')      # facing -X (towards her, in the embrace)
    tl, pl = m.ik_arm('L', (0.3, 0.2, 1.0), (0.7, 0.3, 0.7), math.radians(90))
    tr, pr = m.ik_arm('R', (0.3, -0.2, 1.0), (-0.7, 0.3, 0.7), math.radians(-90))
    for e in (pl, pr):
        e.parent = m.arm
    ankle0 = m.arm.data.bones['foot.L'].head_local.z

    # ---- courtyard
    earth = K.clay('earth', 'earth', wet=0.05, coords='object', scale=0.7, tex='brown_mud_02', cracks=0.5, crack_scale=0.9)
    g = fx.grid('ground', 40, 160); P = fx.co(g)
    P[:, 2] = fx.fbm2(P[:, 0] * 0.6, P[:, 1] * 0.6, seed=3, octaves=4) * 0.03
    fx.set_co(g, P); K.assign(g, earth)
    wallm = K.clay('wall', 'buff', wet=0.03, coords='object', scale=0.5)
    fx.box('wall', (26, 0.5, 8.0), (0, 3.9, 4.0), wallm, bevel=0.06, subdiv=6, noise=0.03)
    fx.box('wall2', (0.5, 26, 8.0), (9.0, 0, 4.0), wallm, bevel=0.06, subdiv=6, noise=0.03)
    fx.box('door', (1.15, 0.2, 2.2), (-2.3, 3.62, 1.1), K.clay('door', 'dark', wet=0.1, coords='object'), bevel=0.05)
    fx.box('step', (1.7, 0.7, 0.16), (-2.3, 3.4, 0.08), wallm, bevel=0.04)
    potm = K.clay('pot', 'terracotta', wet=0.2, coords='object', scale=3)
    for (x, y, s_) in ((1.5, 3.1, 1.0), (2.15, 2.9, 0.7), (-0.6, 3.2, 1.25), (6.0, 2.4, 1.1)):
        fx.lathe('pot', [(0, 0), (0.16 * s_, 0), (0.30 * s_, 0.25 * s_), (0.26 * s_, 0.5 * s_), (0.13 * s_, 0.62 * s_),
                         (0.17 * s_, 0.7 * s_), (0.14 * s_, 0.7 * s_)], (x, y, 0), potm)
    sun = C.light(sc, 'SUN', (0, 0, 10), 6.0, color=(1.0, 0.72, 0.45), rot=(-47, 0, -52), size=0.03, name='sun')
    bounce = C.light(sc, 'AREA', (-1.5, -5.0, 1.6), 300, color=(1.0, 0.82, 0.66), target=(0, 0.0, 0.7), size=4.0, name='bounce')
    motes = fx.Motes(sc, 520, (0.2, 0.2, 0.0), 3.0, 2.0, size=0.0022, seed=4, color=(1.0, 0.72, 0.42), emit=0.12,
                     drift=(0.012, -0.006, 0.004))
    dust = fx.Motes(sc, 160, (1.05, 0.0, 0.0), 0.45, 0.35, size=0.006, seed=9, color=(0.75, 0.6, 0.45), emit=0.0,
                    drift=(0.05, -0.02, 0.22))

    camA = C.camera(sc, (-0.4, -5.2, 0.62), (0.0, 0.0, 0.70), lens=45, fstop=2.8, name='camA')
    camB = C.camera(sc, (0, -1, 1.5), (0, 0, 1.5), lens=60, fstop=2.8, name='camB')
    camC = C.camera(sc, (0, -2, 0.8), (0, 0, 0.8), lens=75, fstop=2.8, name='camC')
    faceB = C.light(sc, 'AREA', (0, -1, 1.5), 0, color=(1.0, 0.80, 0.62), size=0.9, name='faceB')
    faceC = C.light(sc, 'AREA', (0, -2.2, 1.0), 0, color=(1.0, 0.80, 0.62), target=(0, 0, 0.9), size=1.2, name='faceC')
    sm = fx.smooth

    # the boy's run: position and stride phase per frame
    kx = np.zeros(FRAMES); kph = np.zeros(FRAMES)
    x = KX0
    for f in range(FRAMES):
        v = 1.45 if f < TRIP else 1.45 * max(0.0, 1 - (f - TRIP) / (LAND - TRIP + 4.0))
        x += v / 24.0; kx[f] = x
        kph[f] = kph[f - 1] + 2 * math.pi * (v / 24.0) / 0.58 if f else 0.0
    X_FALL = kx[-1]                                           # where he lies
    MX = X_FALL - 0.36                                        # where she kneels in the last cut

    def pose_kid_run(f):
        k.reset_pose()
        fall = sm(f, TRIP, LAND) ** 1.8 if f >= TRIP else 0.0
        run = 1.0 - sm(f, TRIP, TRIP + 6)
        for sd, o in (('L', 0.0), ('R', math.pi)):
            sw = math.sin(kph[f] + o)
            k.flex(f'upperleg01.{sd}', (34 * sw + 12) * run + (10 if sd == 'L' else -28) * fall)
            k.flex(f'lowerleg01.{sd}', -(18 + 58 * max(0.0, math.sin(kph[f] + o + 1.1)) ** 1.5) * run - (20 if sd == 'L' else 75) * fall)
            k.flex(f'upperarm01.{sd}', -30 * sw * run + 105 * fall); k.rot(f'upperarm01.{sd}', 'Y', (30 if sd == 'L' else -30) * (1 - 0.8 * fall))
            k.flex(f'lowerarm01.{sd}', 75 * run + 18 * fall)
        k.rot('spine03', 'X', 8 * run - 6 * fall); k.rot('neck01', 'X', -6 - 6 * fall); k.rot('head', 'X', -6 - 20 * fall)
        after = max(0, f - LAND)
        pitch = 10 * run + 80 * fall + 3.0 * math.exp(-after / 4.0) * math.sin(after * 1.1) * (1 if f > LAND else 0)
        bob = 0.022 * abs(math.sin(kph[f])) * run
        k.arm.matrix_world = Matrix.Translation((kx[f], 0, bob)) @ Rk @ Matrix.Rotation(math.radians(pitch), 4, 'X')
        k.cry.value = 0.15 + 0.75 * sm(f, LAND - 2, LAND + 8)
        k.shut.value = 0.85

    def stand_mom(f, x, y, lean=0.0, turn=0.0):
        for pb in m.arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
        m.rot('spine05', 'X', 3 + lean * 0.5); m.rot('spine03', 'X', 3 + lean * 0.3); m.rot('spine01', 'X', lean * 0.2)
        m.curl_fingers('L', 14, 6); m.curl_fingers('R', 14, 6)
        m.arm.matrix_world = Matrix.Translation((x, y, 0)) @ Rm @ Matrix.Rotation(math.radians(turn), 4, 'Z')

    def arms(pl_, pr_):
        """Hand targets given in her own frame (x forward, y to her left, z up from the ground at her feet)."""
        Mw = m.arm.matrix_world
        o = Mw.translation; fw = (Mw.to_3x3() @ Vector((0, -1, 0))).normalized(); lf = Vector((-fw.y, fw.x, 0))
        tl.location = Vector((o.x, o.y, 0)) + fw * pl_[0] + lf * pl_[1] + Vector((0, 0, pl_[2]))
        tr.location = Vector((o.x, o.y, 0)) + fw * pr_[0] + lf * pr_[1] + Vector((0, 0, pr_[2]))

    def update(f):
        motes.update(f * 0.9)
        dust.update(max(0, f - LAND) * 1.0)
        dust.ob.location.z = 0.0 if f >= LAND else -5.0
        if f < CUT_B:
            # ---- A: wide. He runs and falls; she is by the door, watching him play
            sc.camera = camA
            faceB.data.energy = 0; faceC.data.energy = 0
            pose_kid_run(f)
            pl.location = Vector((0.7, 0.3, 0.7)); pr.location = Vector((-0.7, 0.3, 0.7))
            see = sm(f, TRIP, TRIP + 8)
            stand_mom(f, MOM_A[0], MOM_A[1], lean=10 * see, turn=-12)
            m.rot('head', 'X', 4); m.rot('head', 'Z', 0)
            arms((0.16 + 0.22 * see, 0.24, 0.82 + 0.28 * see), (0.16 + 0.22 * see, -0.24, 0.82 + 0.24 * see))
            fear.value = 0.9 * see; tender.value = 0
            m.shut.value = 0.12
            p = sm(f, 0, CUT_B)
            camA.location = Vector((-0.55 + 0.45 * p, -5.2, 0.62)); C.look_at(camA, Vector((-0.25 + 0.55 * p, 0.0, 0.70)))
            fx.shake(camA, f, 0.0012 + 0.006 * math.exp(-max(0, f - LAND) / 3.0) * (f >= LAND), seed=5)
            camA.data.dof.focus_distance = 5.15
        elif f < CUT_C:
            # ---- B: her face. Fear, a gasp - and she is already moving
            sc.camera = camB
            pose_kid_run(CUT_B - 1)
            pl.location = Vector((0.7, 0.3, 0.7)); pr.location = Vector((-0.7, 0.3, 0.7))
            g_ = f - CUT_B
            go = sm(g_, 9, CUT_C - CUT_B + 6) ** 1.5              # she surges forward
            stand_mom(f, MOM_A[0] + 1.25 * go, MOM_A[1] - 0.25 * go, lean=6 + 30 * go, turn=-12)
            m.arm.location.z = -0.10 * go
            m.rot('neck01', 'X', -6 * go); m.rot('head', 'X', 2 - 10 * go)
            arms((0.38 + 0.30 * go, 0.22, 1.10), (0.38 + 0.30 * go, -0.22, 1.02))
            fear.value = min(1.0, 0.75 + 0.25 * sm(g_, 0, 5)); tender.value = 0
            m.shut.value = 0.0
            bpy.context.view_layer.update()
            hd = m.arm.matrix_world @ m.pb('head').matrix.translation + Vector((0.06, 0, 0.055))
            # the camera backs away in front of her as she runs, losing a little ground
            camB.location = hd + Vector((1.45 - 0.35 * go, -0.78, -0.04))
            C.look_at(camB, hd)
            fx.shake(camB, f, 0.0022, seed=8)
            camB.data.dof.focus_distance = (camB.location - hd).length
            faceB.location = hd + Vector((1.1, -1.1, 0.25)); C.look_at(faceB, hd); faceB.data.energy = 34
        else:
            # ---- C: on her knees, holding him
            sc.camera = camC
            faceB.data.energy = 0
            faceC.location = Vector((MX + 0.9, -2.0, 1.25)); C.look_at(faceC, Vector((MX + 0.25, 0, 0.9)))
            h = f - CUT_C
            pull = sm(h, 0, 16)
            rock = math.sin(h / 24.0 * 2 * math.pi / 2.3) * sm(h, 10, 30)
            sob = math.sin(h * 1.25) * (0.5 + 0.5 * math.sin(h * 0.21))
            for pb in m.arm.pose.bones:
                pb.rotation_quaternion = (1, 0, 0, 0)
            m.flex2('upperleg01', 52); m.flex2('lowerleg01', -142); m.flex2('foot', -45)      # sitting back on her heels
            lean = 10 + 2 * pull
            m.rot('spine05', 'X', lean * 0.45 + 1.5 * rock); m.rot('spine03', 'X', lean * 0.35 + 1.0 * rock); m.rot('spine01', 'X', lean * 0.2)
            m.rot('spine03', 'Z', 2.0 * rock)
            m.rot('neck01', 'X', 8 + 2 * pull); m.rot('head', 'X', 6 + 4 * pull); m.rot('head', 'Z', MOM_HEAD_TURN * pull)
            m.curl_fingers('L', 36, 14); m.curl_fingers('R', 36, 14)
            m.arm.matrix_world = Matrix.Translation((MX, 0, 0)) @ Rm
            bpy.context.view_layer.update()
            Mw = m.arm.matrix_world
            knee = min((Mw @ m.pb(f'lowerleg01.{sd}').matrix.translation).z for sd in 'LR')
            m.arm.matrix_world = Matrix.Translation((MX, 0, 0.07 - knee)) @ Rm
            fear.value = 0.35 * (1 - pull); tender.value = pull
            m.shut.value = 0.15 + 0.8 * sm(h, 8, 26)
            # the boy, on his feet again, pressed against her
            k.reset_pose()
            k.flex2('upperarm01', 78); k.both('upperarm01', 'Y', 14); k.flex2('lowerarm01', 38)
            k.rot('spine03', 'X', 6 + 1.2 * sob); k.rot('neck01', 'X', 8); k.rot('head', 'X', 14); k.rot('head', 'Z', KID_HEAD_TURN)
            k.curl_fingers('L', 30, 10); k.curl_fingers('R', 30, 10)
            kd = KID_D[0] + (KID_D[1] - KID_D[0]) * pull
            k.arm.matrix_world = Matrix.Translation((MX + kd, -0.045, 0.004 * sob)) @ Rk_in @ Matrix.Rotation(math.radians(6 * pull + 0.8 * rock), 4, 'X')
            k.cry.value = 0.75 - 0.3 * sm(h, 20, 56) + 0.12 * sob
            k.shut.value = 1.0
            bpy.context.view_layer.update()
            kb = k.arm.matrix_world @ k.pb('spine02').matrix.translation
            kh = k.arm.matrix_world @ k.pb('head').matrix.translation
            st = 0.012 * math.sin(h / 24.0 * 2 * math.pi / 1.9)
            # her arms come round him from the sides: one hand across his back, the other on the back of his head
            tl.location = Vector((kb.x + 0.070, 0.085, kb.z - 0.11 + st))
            tr.location = Vector((kb.x + 0.075, -0.080, kb.z - 0.05 - st))
            pl.location = Vector((0.95, -0.45, 0.55)); pr.location = Vector((-0.95, -0.45, 0.75))
            p = sm(h, 0, FRAMES - CUT_C)
            mh = m.arm.matrix_world @ m.pb('head').matrix.translation
            mid = (mh + kh) / 2 + Vector((0, 0, 0.045))
            camC.location = Vector((mid.x + 0.25, -2.25 + 0.35 * p, mid.z + 0.05))
            C.look_at(camC, Vector((mid.x, 0.0, mid.z)))
            faceC.data.energy = 26
            fx.shake(camC, f, 0.0010, seed=11)
            camC.data.dof.focus_distance = abs(camC.location.y) - 0.04
            motes.update(f * 0.9, clear=(tuple(camC.location), camC.data.dof.focus_distance - 0.3))

    return dict(frames=FRAMES, update=update)


KX0 = -1.15                 # where the boy starts his run
MOM_A = (-2.25, 1.9)        # where she stands in the wide shot
KID_D = (0.535, 0.515)       # the boy's distance in front of her before / after she pulls him in
MOM_HEAD_TURN = 0
KID_HEAD_TURN = 30
