"""Procedural clay materials (Cycles). One node tree, many tints: terracotta skin, buff robe, pale slip, dark stone.
Texture coordinates come from the `rest_position` attribute so surface detail sticks to deforming figures."""
import bpy

TINTS = {
    'terracotta': ((0.42, 0.185, 0.105), (0.30, 0.12, 0.07)),
    'umber':      ((0.20, 0.105, 0.065), (0.12, 0.06, 0.04)),
    'buff':       ((0.50, 0.36, 0.24), (0.36, 0.24, 0.15)),
    'slip':       ((0.66, 0.58, 0.47), (0.50, 0.42, 0.32)),
    'white':      ((0.74, 0.71, 0.64), (0.58, 0.54, 0.47)),
    'grey':       ((0.27, 0.235, 0.20), (0.17, 0.145, 0.125)),
    'dark':       ((0.075, 0.062, 0.055), (0.04, 0.034, 0.03)),
    'earth':      ((0.30, 0.19, 0.12), (0.20, 0.12, 0.075)),
}


def clay(name, tint='terracotta', wet=0.25, cracks=0.0, bump=1.0, scale=1.0, coords='rest', stroke=1.0,
         grain=1.0, sss=0.0):
    """wet: 0 dry matte .. 1 dripping. cracks: 0..1 dried-mud crackle. scale: texture scale multiplier."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes; L = nt.links
    bsdf = N['Principled BSDF']
    c1, c2 = TINTS[tint] if isinstance(tint, str) else tint

    def node(t, **kw):
        n = N.new(t)
        for k, v in kw.items():
            if k in n.inputs:
                n.inputs[k].default_value = v
            else:
                setattr(n, k, v)
        return n

    def val(v, label):
        n = node('ShaderNodeValue'); n.outputs[0].default_value = v; n.label = label; n.name = label
        return n

    def math(op, a, b=None, clamp=False):
        n = N.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    v_wet = val(wet, 'wet'); v_cr = val(cracks, 'cracks'); v_bump = val(bump, 'bump')

    if coords == 'rest':
        a = node('ShaderNodeAttribute', attribute_name='rest_position')
        co = a.outputs['Vector']
    elif coords == 'object':
        co = node('ShaderNodeTexCoord').outputs['Object']
    else:
        co = node('ShaderNodeNewGeometry').outputs['Position']
    mp = node('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale)
    L.new(co, mp.inputs['Vector']); co = mp.outputs['Vector']

    def noise(sc, detail=3.0, rough=0.55, vec=None, dist=0.0):
        n = node('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = sc
        n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
        n.inputs['Distortion'].default_value = dist
        L.new(vec or co, n.inputs['Vector'])
        return n

    big = noise(3.5, 4.0, 0.6)             # tonal blotches
    mid = noise(28, 3.0, 0.5)              # lumps
    fine = noise(420, 2.0, 0.6)            # grain
    # finger strokes: stretched noise
    st = node('ShaderNodeMapping'); st.inputs['Scale'].default_value = (55, 55, 7)
    st.inputs['Rotation'].default_value = (0.5, 0.3, 0.7)
    L.new(co, st.inputs['Vector'])
    strokes = noise(1.0, 2.0, 0.5, vec=st.outputs['Vector'], dist=0.6)
    # fingerprints-ish ridges
    wv = node('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 18; wv.inputs['Distortion'].default_value = 6
    wv.inputs['Detail'].default_value = 2; wv.inputs['Detail Scale'].default_value = 1.2
    L.new(co, wv.inputs['Vector'])
    # cracks (dry mud): voronoi distance to edge
    vo = node('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 26
    wn = noise(9, 2.0, 0.5)
    wm = N.new('ShaderNodeMixRGB'); wm.blend_type = 'LINEAR_LIGHT'; wm.inputs[0].default_value = 0.06
    L.new(co, wm.inputs[1]); L.new(wn.outputs['Color'], wm.inputs[2]); L.new(wm.outputs[0], vo.inputs['Vector'])
    vo2 = node('ShaderNodeTexVoronoi'); vo2.feature = 'DISTANCE_TO_EDGE'; vo2.inputs['Scale'].default_value = 85
    L.new(wm.outputs[0], vo2.inputs['Vector'])
    cr1 = node('ShaderNodeMapRange'); cr1.inputs[1].default_value = 0.0; cr1.inputs[2].default_value = 0.035
    L.new(vo.outputs['Distance'], cr1.inputs[0])
    cr2 = node('ShaderNodeMapRange'); cr2.inputs[1].default_value = 0.0; cr2.inputs[2].default_value = 0.05
    L.new(vo2.outputs['Distance'], cr2.inputs[0])
    crack = math('MINIMUM', cr1.outputs[0], math('ADD', cr2.outputs[0], 0.35, clamp=True))   # 0 in crack, 1 elsewhere
    crack_m = math('MULTIPLY', math('SUBTRACT', 1.0, crack), v_cr.outputs[0])                 # 0..cracks

    # ---- colour
    ramp = node('ShaderNodeMapRange'); ramp.inputs[1].default_value = 0.3; ramp.inputs[2].default_value = 0.7
    L.new(big.outputs['Fac'], ramp.inputs[0])
    col = N.new('ShaderNodeMixRGB'); col.inputs[1].default_value = (*c2, 1); col.inputs[2].default_value = (*c1, 1)
    L.new(ramp.outputs[0], col.inputs[0])
    geo = node('ShaderNodeNewGeometry')
    pt = node('ShaderNodeMapRange'); pt.inputs[1].default_value = 0.42; pt.inputs[2].default_value = 0.52
    pt.inputs[3].default_value = 0.55; pt.inputs[4].default_value = 1.0
    L.new(geo.outputs['Pointiness'], pt.inputs[0])
    col2 = N.new('ShaderNodeMixRGB'); col2.blend_type = 'MULTIPLY'; col2.inputs[0].default_value = 1.0
    L.new(col.outputs[0], col2.inputs[1]); L.new(pt.outputs[0], col2.inputs[2])
    # dry dusty highlights on strokes when dry; darker when wet
    dry = math('SUBTRACT', 1.0, v_wet.outputs[0], clamp=True)
    dust = N.new('ShaderNodeMixRGB'); dust.blend_type = 'SCREEN'
    L.new(math('MULTIPLY', math('MULTIPLY', strokes.outputs['Fac'], dry), 0.22), dust.inputs[0])
    L.new(col2.outputs[0], dust.inputs[1]); dust.inputs[2].default_value = (0.75, 0.62, 0.5, 1)
    wetdark = N.new('ShaderNodeMixRGB'); wetdark.blend_type = 'MULTIPLY'
    L.new(math('MULTIPLY', v_wet.outputs[0], 0.55), wetdark.inputs[0])
    L.new(dust.outputs[0], wetdark.inputs[1]); wetdark.inputs[2].default_value = (0.5, 0.42, 0.4, 1)
    crk = N.new('ShaderNodeMixRGB'); crk.blend_type = 'MULTIPLY'
    L.new(crack_m, crk.inputs[0]); L.new(wetdark.outputs[0], crk.inputs[1]); crk.inputs[2].default_value = (0.25, 0.2, 0.18, 1)
    L.new(crk.outputs[0], bsdf.inputs['Base Color'])

    # ---- roughness / coat
    rn = node('ShaderNodeMapRange'); rn.inputs[3].default_value = -0.12; rn.inputs[4].default_value = 0.12
    L.new(mid.outputs['Fac'], rn.inputs[0])
    rbase = math('SUBTRACT', 0.86, math('MULTIPLY', v_wet.outputs[0], 0.5))
    rough = math('ADD', rbase, rn.outputs[0], clamp=True)
    L.new(rough, bsdf.inputs['Roughness'])
    for nm in ('Coat Weight', 'Coat'):
        if nm in bsdf.inputs:
            L.new(math('MULTIPLY', math('POWER', v_wet.outputs[0], 2.5), 0.8), bsdf.inputs[nm]); break
    if 'Coat Roughness' in bsdf.inputs:
        bsdf.inputs['Coat Roughness'].default_value = 0.12
    for nm in ('Specular IOR Level', 'Specular'):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = 0.25; break
    if sss and 'Subsurface Weight' in bsdf.inputs:
        bsdf.inputs['Subsurface Weight'].default_value = sss
        bsdf.inputs['Subsurface Radius'].default_value = (0.012, 0.005, 0.003)
        bsdf.inputs['Subsurface Scale'].default_value = 1.0

    # ---- bump
    h = math('MULTIPLY', mid.outputs['Fac'], 0.9)
    h = math('ADD', h, math('MULTIPLY', strokes.outputs['Fac'], 0.55 * stroke))
    h = math('ADD', h, math('MULTIPLY', wv.outputs['Fac'], 0.10 * stroke))
    h = math('ADD', h, math('MULTIPLY', fine.outputs['Fac'], 0.16 * grain))
    h = math('SUBTRACT', h, math('MULTIPLY', crack_m, 2.2))
    bp = node('ShaderNodeBump'); bp.inputs['Distance'].default_value = 0.012
    L.new(h, bp.inputs['Height'])
    L.new(math('MULTIPLY', v_bump.outputs[0], 0.5), bp.inputs['Strength'])
    L.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    for nm in ('Coat Normal',):
        if nm in bsdf.inputs:
            b2 = node('ShaderNodeBump'); b2.inputs['Distance'].default_value = 0.004
            L.new(h, b2.inputs['Height']); b2.inputs['Strength'].default_value = 0.15
            L.new(b2.outputs['Normal'], bsdf.inputs[nm])
    return m


def param(mat, name):
    """Value node socket ('wet' | 'cracks' | 'bump') for keyframing."""
    return mat.node_tree.nodes[name].outputs[0]


def key(mat, name, value, frame):
    s = param(mat, name)
    s.default_value = value
    s.keyframe_insert('default_value', frame=frame)


def emission(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*color, 1); e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    return m


def assign(ob, mat):
    ob.data.materials.clear(); ob.data.materials.append(mat)
