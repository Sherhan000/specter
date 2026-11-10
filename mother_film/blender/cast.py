"""The cast: clay figures built from MakeHuman."""
import bpy
import mhlib as M, garments as G, clay as K

EYES_SHUT = {'eye-left-closure': 1.0, 'eye-right-closure': 1.0}


def baby(name='baby', shut=True, wet=0.3):
    t = {'macrodetails/caucasian-male-baby': 1.0}
    if shut:
        t.update(EYES_SHUT)
    h = M.Human(name, t)
    G.finish(h, subsurf=1)
    h.mat = K.clay(name + '_skin', 'terracotta', wet=wet)
    K.assign(h.body, h.mat)
    return h


def fetal(h, k=1.0, twist=42, head=1.0):
    for b in ('spine05', 'spine04', 'spine03', 'spine02', 'spine01'):
        h.rot(b, 'X', 10 * k)
    for b in ('neck01', 'neck02', 'neck03'):
        h.rot(b, 'X', 6 * k * head)
    h.rot('head', 'X', 10 * k * head)
    h.flex2('upperleg01', 112 * k); h.both('upperleg01', 'Y', -6 * k)
    h.flex2('lowerleg01', -128 * k)
    h.flex2('foot', 15 * k)
    h.both('upperarm01', 'Y', 30 * k)
    h.flex2('upperarm01', 30 * k)
    h.twist('upperarm01.L', twist * k); h.twist('upperarm01.R', -twist * k)
    h.flex2('lowerarm01', 100 * k)
    h.curl_fingers('L', 60 * k, 30 * k); h.curl_fingers('R', 60 * k, 30 * k)


def mother(name='mom', age=0.0, robe_tint='buff', scarf_tint='slip', wet=0.12, shut=1.0, voxel=0.0065):
    """The mother. age 0 = young, 1 = old. Clay figure in a long dress and headscarf."""
    t = {'macrodetails/caucasian-female-young': 1.0 - age, 'macrodetails/caucasian-female-old': age,
         'macrodetails/universal-female-old-averagemuscle-minweight': 0.0}
    h = M.Human(name, t)
    h.robe = G.make_robe(h, voxel=voxel)
    h.scarf = G.make_scarf(h)
    G.strip_body(h)
    G.finish(h, subsurf=1)
    h.shut = h.add_shape('shut', EYES_SHUT, shut)
    h.mat = K.clay(name + '_skin', 'terracotta', wet=wet + 0.1, scale=3.0, crackable=True, crack_scale=7.0)
    h.robe_mat = K.clay(name + '_robe', robe_tint, wet=wet, scale=2.2, crackable=True, crack_scale=4.5)
    h.scarf_mat = K.clay(name + '_scarf', scarf_tint, wet=wet, scale=2.6, crackable=True, crack_scale=5.0)
    K.assign(h.body, h.mat); K.assign(h.robe, h.robe_mat); K.assign(h.scarf, h.scarf_mat)
    return h


def swaddled(name='bundle', tint='white', wet=0.15, cry=0.0):
    """A swaddled infant: clay cocoon with the head showing."""
    import numpy as np
    h = M.Human(name, {'macrodetails/caucasian-male-baby': 1.0})
    hm = G.head_mask()[:M.N_BODY]
    V = h.Vb[:M.N_BODY]
    fr = G.face_frame(h)
    chin = fr['eye'][2] - 0.045
    pts = V[(hm < 0.5) & (V[:, 2] < chin + 0.015) & (np.abs(V[:, 0]) < 0.11)]
    pts = pts.copy(); pts[:, 2] = np.maximum(pts[:, 2], 0.10)      # tuck the legs up
    back = fr['P'][(fr['P'][:, 1] > fr['eye'][1] + 0.05)]         # cloth also wraps the back of the head
    ob = G._hull(np.vstack([pts, back]), inflate=0.012, col=h.col, name=name + '_cloth')
    G._voxel(ob, 0.004, smooth=10)
    co = G._co(ob); nr = G._normals(ob)
    co = co + nr * (G._noise3(co * [1, 1, 3.0], 40, 3) * 0.0035)[:, None]
    G._set_co(ob, co)
    G.skin(h, ob, V, np.arange(M.N_BODY), blur=2)
    h.objs.append(ob); h.cloth = ob
    G.strip_body(h, keep=('head',), neck=False)
    G.finish(h, 1)
    h.shut = h.add_shape('shut', {'eye-left-closure': 0.9, 'eye-right-closure': 0.9}, 1.0)
    h.cry = h.add_shape('cry', {'mouth-open': 1.0, 'mouth-retraction': 0.5, 'eyebrows-left-down': 0.9, 'eyebrows-right-down': 0.9,
                                'eyebrows-left-inner-up': 0.35, 'eyebrows-right-inner-up': 0.35, 'nose-left-elevation': 0.8,
                                'nose-right-elevation': 0.8}, cry)
    h.mat = K.clay(name + '_skin', 'terracotta', wet=0.3, scale=7.0)
    h.cloth_mat = K.clay(name + '_cloth', tint, wet=wet, scale=5.0)
    K.assign(h.body, h.mat); K.assign(ob, h.cloth_mat)
    return h


def attach_local(child_world, parent, bone):
    """Local matrix of a desired world matrix relative to a pose bone (in the current pose)."""
    import bpy
    bpy.context.view_layer.update()
    return (parent.arm.matrix_world @ parent.pb(bone).matrix).inverted() @ child_world


def attach(child, parent, bone, local):
    """Place child's armature object relative to a pose bone of parent (call every frame after posing)."""
    import bpy
    bpy.context.view_layer.update()
    child.arm.matrix_world = parent.arm.matrix_world @ parent.pb(bone).matrix @ local


def frame_matrix(origin, z_dir, front_dir):
    """World matrix for a figure whose head (+Z) points along z_dir and whose front (-Y) faces front_dir."""
    from mathutils import Vector, Matrix
    z = Vector(z_dir).normalized()
    f = Vector(front_dir); f = (f - z * f.dot(z)).normalized()
    y = -f; x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


def sit_cradle(m):
    """Mother seated, head bowed to the child in her arms (arms are placed with IK by the shot)."""
    m.flex2('upperleg01', 82); m.flex2('lowerleg01', -84)
    m.rot('spine05', 'X', 6); m.rot('spine03', 'X', 8); m.rot('spine01', 'X', 6)
    m.rot('neck01', 'X', 10); m.rot('head', 'X', 14); m.rot('head', 'Y', -8); m.rot('head', 'Z', -14)
    m.curl_fingers('L', 22, 8); m.curl_fingers('R', 22, 8)


def add_eyes(h, tint='terracotta'):
    """Clay eyeballs with a carved dark pupil (needed when the lids open)."""
    import numpy as np
    obs = []
    for g in ('helper-l-eye', 'helper-r-eye'):
        o = h.helper(g); obs.append(o)
        mat = K.clay(h.name + '_eye_' + g[7], tint, wet=0.55, scale=20.0)
        ys = np.array([v.co.y for v in o.data.vertices]); y0 = ys.min()
        nt = mat.node_tree; N = nt.nodes; L = nt.links
        at = N.new('ShaderNodeAttribute'); at.attribute_name = 'rest_position'
        sp = N.new('ShaderNodeSeparateXYZ'); L.new(at.outputs['Vector'], sp.inputs[0])
        mr = N.new('ShaderNodeMapRange'); mr.inputs[1].default_value = y0 + 0.0016; mr.inputs[2].default_value = y0 + 0.0024
        mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.0
        L.new(sp.outputs['Y'], mr.inputs[0])
        bs = N['Principled BSDF']; src = bs.inputs['Base Color'].links[0].from_socket
        mx = N.new('ShaderNodeMixRGB'); mx.inputs[2].default_value = (0.012, 0.008, 0.006, 1)
        L.new(mr.outputs[0], mx.inputs[0]); L.new(src, mx.inputs[1]); L.new(mx.outputs[0], bs.inputs['Base Color'])
        K.assign(o, mat)
        try:
            o.add_rest_position_attribute = True
        except Exception:
            pass
    h.eyes = obs
    return obs


def child(name='kid', age=0.5, tint='slip', wet=0.12):
    """Small boy (age 0 = baby proportions, 1 = MakeHuman 'child'). Tunic to the knees, cropped hair."""
    t = {'macrodetails/caucasian-male-baby': 1.0 - age, 'macrodetails/caucasian-male-child': age}
    h = M.Human(name, t)
    h.robe = G.make_robe(h, hem=h.height * 0.30, flare=0.22, inflate=0.010, sleeve=0.012, voxel=0.005, folds=0.006, nfolds=9)
    h.hair = G.make_hair(h, thick=0.008, hairline=0.058 * M.face_scale(h.V_mh), rough=0.003)
    G.strip_body(h, forearm=1.0, shin=1.0)
    G.finish(h, subsurf=1)
    h.shut = h.add_shape('shut', EYES_SHUT, 1.0)
    h.cry = h.add_shape('cry', {'mouth-open': 1.0, 'mouth-retraction': 0.4, 'eyebrows-left-inner-up': 0.6,
                                'eyebrows-right-inner-up': 0.6}, 0.0)
    h.mat = K.clay(name + '_skin', 'terracotta', wet=wet + 0.1, scale=5.0)
    h.robe_mat = K.clay(name + '_robe', tint, wet=wet, scale=4.0)
    h.hair_mat = K.clay(name + '_hair', 'umber', wet=wet, scale=9.0, bump=1.8)
    K.assign(h.body, h.mat); K.assign(h.robe, h.robe_mat); K.assign(h.hair, h.hair_mat)
    return h
