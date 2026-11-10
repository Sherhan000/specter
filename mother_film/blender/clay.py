"""Clay materials (Cycles). Built on CC0 Poly Haven scans (hand-smoothed clay plaster, cracked mud),
box-projected from the `rest_position` attribute so the surface detail sticks to deforming figures.
One node tree, many tints: terracotta skin, buff robe, pale slip, dark stone."""
import bpy, os

TEX = os.environ.get('TEX_DIR', '/home/user/assets/tex')

TINTS = {
    'terracotta': ((0.42, 0.185, 0.105), (0.27, 0.105, 0.06)),
    'umber':      ((0.17, 0.09, 0.055), (0.09, 0.045, 0.03)),
    'buff':       ((0.47, 0.33, 0.21), (0.31, 0.20, 0.12)),
    'slip':       ((0.62, 0.53, 0.42), (0.44, 0.36, 0.27)),
    'white':      ((0.72, 0.69, 0.62), (0.54, 0.50, 0.43)),
    'grey':       ((0.25, 0.215, 0.185), (0.15, 0.13, 0.11)),
    'dark':       ((0.07, 0.058, 0.05), (0.035, 0.03, 0.026)),
    'earth':      ((0.28, 0.175, 0.11), (0.17, 0.10, 0.065)),
    'rock':       ((0.20, 0.15, 0.12), (0.10, 0.075, 0.06)),
    'olive':      ((0.22, 0.25, 0.10), (0.12, 0.15, 0.06)),
    'ochre':      ((0.55, 0.30, 0.08), (0.38, 0.17, 0.05)),
    'blossom':    ((0.70, 0.50, 0.45), (0.55, 0.36, 0.33)),
    'snow':       ((0.80, 0.82, 0.85), (0.62, 0.65, 0.70)),
}


def image(name, colorspace='Non-Color'):
    for ext in ('jpg', 'png'):
        p = f'{TEX}/{name}.{ext}'
        if os.path.exists(p):
            im = bpy.data.images.load(p, check_existing=True)
            im.colorspace_settings.name = colorspace
            return im
    raise FileNotFoundError(name)


def clay(name, tint='terracotta', wet=0.25, cracks=0.0, bump=1.0, scale=2.2, coords='rest', tex='clay_plaster',
         crackable=None, crack_scale=None, sss=0.0, variation=1.0):
    """wet: 0 dry matte .. 1 dripping. cracks: 0..1 dried-mud crackle (animatable when crackable).
    scale: texture tiles per metre."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes; L = nt.links
    bsdf = N['Principled BSDF']
    c1, c2 = TINTS[tint] if isinstance(tint, str) else tint
    if crackable is None:
        crackable = cracks > 0

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

    def mix(kind, fac, a, b):
        n = N.new('ShaderNodeMixRGB'); n.blend_type = kind
        for i, x in enumerate((fac, a, b)):
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            elif isinstance(x, tuple):
                n.inputs[i].default_value = (*x, 1)
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    v_wet = val(wet, 'wet'); v_cr = val(cracks, 'cracks'); v_bump = val(bump, 'bump')

    if coords == 'rest':
        co = node('ShaderNodeAttribute', attribute_name='rest_position').outputs['Vector']
    elif coords == 'object':
        co = node('ShaderNodeTexCoord').outputs['Object']
    else:
        co = node('ShaderNodeNewGeometry').outputs['Position']

    def tex_lookup(img, sc, rot=(0, 0, 0), off=(0, 0, 0)):
        mp = node('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (sc, sc, sc)
        mp.inputs['Rotation'].default_value = rot; mp.inputs['Location'].default_value = off
        L.new(co, mp.inputs['Vector'])
        t = node('ShaderNodeTexImage'); t.image = image(img); t.projection = 'BOX'; t.projection_blend = 0.3
        L.new(mp.outputs['Vector'], t.inputs['Vector'])
        return t.outputs['Color']

    fine = tex_lookup(tex + '_disp', scale)                                   # hand strokes
    big = tex_lookup(tex + '_disp', scale * 0.21, rot=(0.6, 0.4, 1.1), off=(0.37, 0.11, 0.73))   # tonal blotches

    # ---- colour
    ramp = node('ShaderNodeMapRange'); ramp.inputs[1].default_value = 0.5 - 0.22 / max(variation, 1e-3)
    ramp.inputs[2].default_value = 0.5 + 0.22 / max(variation, 1e-3)
    L.new(big, ramp.inputs[0])
    col = mix('MIX', ramp.outputs[0], c2, c1)
    col.node.name = 'tint'
    cav = node('ShaderNodeMapRange'); cav.inputs[1].default_value = 0.25; cav.inputs[2].default_value = 0.7
    cav.inputs[3].default_value = 0.62; cav.inputs[4].default_value = 1.06
    L.new(fine, cav.inputs[0])
    col = mix('MULTIPLY', 1.0, col, cav.outputs[0])
    col = mix('MULTIPLY', math('MULTIPLY', v_wet.outputs[0], 0.6), col, (0.5, 0.42, 0.4))
    height = fine
    if crackable:
        cs = crack_scale or scale * 0.75
        cr = tex_lookup('mud_cracked_dry_03_disp', cs, rot=(0.3, 0.9, 0.2))
        cm = node('ShaderNodeMapRange'); cm.inputs[1].default_value = 0.30; cm.inputs[2].default_value = 0.52
        cm.inputs[3].default_value = 1.0; cm.inputs[4].default_value = 0.0
        L.new(cr, cm.inputs[0])
        crack_m = math('MULTIPLY', cm.outputs[0], v_cr.outputs[0])            # 0..cracks inside crack lines
        col = mix('MULTIPLY', crack_m, col, (0.22, 0.17, 0.15))
        # dry flakes are paler
        col = mix('SCREEN', math('MULTIPLY', math('MULTIPLY', cr, v_cr.outputs[0]), 0.07), col, (0.8, 0.7, 0.6))
        height = math('ADD', height, math('MULTIPLY', math('MULTIPLY', cr, v_cr.outputs[0]), 2.5))
        height = math('SUBTRACT', height, math('MULTIPLY', crack_m, 3.0))
    L.new(col, bsdf.inputs['Base Color'])

    # ---- roughness / coat
    rn = node('ShaderNodeMapRange'); rn.inputs[3].default_value = 0.10; rn.inputs[4].default_value = -0.10
    L.new(fine, rn.inputs[0])
    rbase = math('SUBTRACT', 0.84, math('MULTIPLY', v_wet.outputs[0], 0.5))
    L.new(math('ADD', rbase, rn.outputs[0], clamp=True), bsdf.inputs['Roughness'])
    for nm in ('Coat Weight', 'Coat'):
        if nm in bsdf.inputs:
            L.new(math('MULTIPLY', math('POWER', v_wet.outputs[0], 2.5), 0.7), bsdf.inputs[nm]); break
    if 'Coat Roughness' in bsdf.inputs:
        bsdf.inputs['Coat Roughness'].default_value = 0.16
    for nm in ('Specular IOR Level', 'Specular'):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = 0.3; break
    if sss and 'Subsurface Weight' in bsdf.inputs:
        bsdf.inputs['Subsurface Weight'].default_value = sss
        bsdf.inputs['Subsurface Radius'].default_value = (0.012, 0.005, 0.003)

    # ---- bump
    bp = node('ShaderNodeBump'); bp.inputs['Distance'].default_value = 0.006 * 2.2 / scale
    L.new(height, bp.inputs['Height'])
    L.new(math('MULTIPLY', v_bump.outputs[0], 0.85), bp.inputs['Strength'])
    L.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def add_fade(mat, attr='fade'):
    """Make a clay material vanish where the point attribute `attr` approaches 1 (cut-out transparency)."""
    nt = mat.node_tree; N = nt.nodes; L = nt.links
    out = N['Material Output']; src = out.inputs['Surface'].links[0].from_socket
    a = N.new('ShaderNodeAttribute'); a.attribute_name = attr
    tr = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader')
    L.new(a.outputs['Fac'], mx.inputs[0]); L.new(src, mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])


def set_tint(mat, a, b, t):
    """Blend the clay tint between two named tints (t = 0..1)."""
    n = mat.node_tree.nodes['tint']
    (a1, a2), (b1, b2) = TINTS[a], TINTS[b]
    n.inputs[2].default_value = (*[x + (y - x) * t for x, y in zip(a1, b1)], 1)
    n.inputs[1].default_value = (*[x + (y - x) * t for x, y in zip(a2, b2)], 1)


def param(mat, name):
    """Value node socket ('wet' | 'cracks' | 'bump')."""
    return mat.node_tree.nodes[name].outputs[0]


def setp(mat, name, value):
    mat.node_tree.nodes[name].outputs[0].default_value = value


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
