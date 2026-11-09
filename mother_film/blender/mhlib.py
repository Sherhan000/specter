"""MakeHuman (CC0) base mesh -> Blender: morph targets, skeleton, weights, posing helpers.

Blender space: X = character's left, -Y = front, Z = up, metres.
"""
import bpy, json, os, math
import numpy as np
from mathutils import Vector, Matrix

MH = os.environ.get('MH_DATA', '/home/user/assets/mhrepo/makehuman/data')
N_BODY = 13380            # body vertices come first in base.obj
_cache = {}


def _base():
    if 'base' in _cache:
        return _cache['base']
    V, VT, groups, g = [], [], {}, None
    for l in open(f'{MH}/3dobjs/base.obj'):
        if l.startswith('v '):
            V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('vt '):
            VT.append([float(x) for x in l.split()[1:3]])
        elif l.startswith('g '):
            g = l.split()[1]
        elif l.startswith('f '):
            f = [p.split('/') for p in l.split()[1:]]
            groups.setdefault(g, []).append(([int(p[0]) - 1 for p in f], [int(p[1]) - 1 for p in f]))
    b = dict(V=np.array(V), VT=np.array(VT), groups=groups)
    b['skel'] = json.load(open(f'{MH}/rigs/default.mhskel'))
    b['weights'] = json.load(open(f'{MH}/rigs/default_weights.mhw'))['weights']
    idx = {}
    for root, _, files in os.walk(f'{MH}/targets'):
        for fn in files:
            if fn.endswith('.target'):
                p = os.path.join(root, fn)
                idx[fn[:-7]] = p
                idx[os.path.relpath(p, f'{MH}/targets')[:-7]] = p
    b['tidx'] = idx
    _cache['base'] = b
    return b


def target(name):
    k = 't:' + name
    if k not in _cache:
        ii, dd = [], []
        for l in open(_base()['tidx'][name]):
            if l[0] in '#\n':
                continue
            p = l.split()
            ii.append(int(p[0])); dd.append([float(p[1]), float(p[2]), float(p[3])])
        _cache[k] = (np.array(ii, dtype=int), np.array(dd).reshape(-1, 3))
    return _cache[k]


def morph(targets):
    """targets: {name: weight} -> MH-space vertex array (decimetres, Y up)."""
    V = _base()['V'].copy()
    for n, w in targets.items():
        if abs(w) < 1e-6:
            continue
        i, d = target(n)
        V[i] += w * d
    return V


def to_bl(V):
    """MH space -> Blender space (metres, Z up, ground at z=0)."""
    V = np.asarray(V)
    out = np.stack([V[:, 0], -V[:, 2], V[:, 1]], 1) * 0.1
    return out


def ground_z(Vb):
    return Vb[19150:19158, 2].mean()


def group_faces(names):
    g = _base()['groups']
    out = []
    for n in names:
        out += g[n]
    return out


def make_mesh(name, Vb, faces, arm=None, with_uv=True, collection=None):
    """faces: list of (vertex idx list, uv idx list) in base numbering. Returns object; custom prop-free.
    Keeps a per-vertex int attribute 'mh_index' holding the base vertex index."""
    b = _base()
    used = sorted({i for f, _ in faces for i in f})
    remap = {v: k for k, v in enumerate(used)}
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(Vb[i]) for i in used], [], [[remap[i] for i in f] for f, _ in faces])
    if with_uv:
        uv = me.uv_layers.new(name='UVMap')
        k = 0
        for f, t in faces:
            for ti in t:
                uv.data[k].uv = b['VT'][ti]
                k += 1
    a = me.attributes.new('mh_index', 'INT', 'POINT')
    a.data.foreach_set('value', used)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    if arm is not None:
        bind(ob, arm, used)
    return ob


def bind(ob, arm, used=None):
    """Create vertex groups from MH weights and add an Armature modifier."""
    b = _base()
    if used is None:
        used = [0] * len(ob.data.vertices)
        ob.data.attributes['mh_index'].data.foreach_get('value', used)
    remap = {v: k for k, v in enumerate(used)}
    for bone, wl in b['weights'].items():
        vg = None
        for vi, w in wl:
            k = remap.get(vi)
            if k is None:
                continue
            if vg is None:
                vg = ob.vertex_groups.new(name=bone)
            vg.add([k], w, 'REPLACE')
    m = ob.modifiers.new('Armature', 'ARMATURE')
    m.object = arm
    ob.parent = arm
    return m


def make_armature(name, V_mh, collection=None):
    """Build the MakeHuman default skeleton fitted to morphed vertices (MH space array)."""
    b = _base(); sk = b['skel']
    Vb = to_bl(V_mh)
    J = {j: Vector(Vb[idx].mean(0)) for j, idx in sk['joints'].items()}
    ad = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, ad)
    (collection or bpy.context.scene.collection).objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    done = {}
    pending = dict(sk['bones'])
    while pending:
        for bn in list(pending):
            bd = pending[bn]
            if bd['parent'] and bd['parent'] not in done:
                continue
            eb = ad.edit_bones.new(bn)
            eb.head = J[bd['head']]; eb.tail = J[bd['tail']]
            if (eb.tail - eb.head).length < 1e-4:
                eb.tail = eb.head + Vector((0, 0, 0.01))
            if bd['parent']:
                eb.parent = done[bd['parent']]
            pl = sk['planes'].get(bd.get('rotation_plane') or '')
            if pl:
                p1, p2, p3 = (J[x] for x in pl)
                n = (p2 - p1).cross(p3 - p2)
                if n.length > 1e-8:
                    eb.align_roll(n.normalized())
            done[bn] = eb
            del pending[bn]
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in ob.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    ob.show_in_front = True
    return ob


class Human:
    """A morphed, rigged MakeHuman figure. `parts` are extra helper groups kept as separate objects."""

    def __init__(self, name, targets, collection=None):
        self.name = name
        self.targets = dict(targets)
        self.V_mh = morph(targets)
        self.Vb = to_bl(self.V_mh)
        gz = ground_z(self.Vb)
        self.Vb[:, 2] -= gz
        self.V_mh = self.V_mh.copy(); self.V_mh[:, 1] -= gz * 10
        self.col = collection
        self.arm = make_armature(name + '_rig', self.V_mh, collection)
        self.body = make_mesh(name + '_body', self.Vb, group_faces(['body']), self.arm, collection=collection)
        self.objs = [self.body]
        self.height = self.Vb[:N_BODY, 2].max()

    def helper(self, group, suffix=None):
        ob = make_mesh(f'{self.name}_{suffix or group}', self.Vb, group_faces([group]), self.arm,
                       with_uv=False, collection=self.col)
        self.objs.append(ob)
        return ob

    def add_shape(self, name, targets, value=0.0):
        """Shape key on the body from extra targets (relative to this human's base)."""
        ob = self.body
        if not ob.data.shape_keys:
            ob.shape_key_add(name='Basis')
        used = [0] * len(ob.data.vertices)
        ob.data.attributes['mh_index'].data.foreach_get('value', used)
        d = to_bl(morph(targets) - _base()['V'])
        sk = ob.shape_key_add(name=name)
        for k, vi in enumerate(used):
            if d[vi].any():
                sk.data[k].co = ob.data.vertices[k].co + Vector(d[vi])
        sk.value = value
        return sk

    # ---- posing ---------------------------------------------------------
    def pb(self, bone):
        return self.arm.pose.bones[bone]

    def rot(self, bone, axis, deg):
        """Rotate pose bone about an armature-space axis through the bone head (accumulates)."""
        pb = self.arm.pose.bones[bone]
        bpy.context.view_layer.update()
        M = pb.matrix.copy()
        h = M.translation.copy()
        ax = {'X': Vector((1, 0, 0)), 'Y': Vector((0, 1, 0)), 'Z': Vector((0, 0, 1))}.get(axis, axis)
        R = Matrix.Rotation(math.radians(deg), 4, Vector(ax))
        pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M
        bpy.context.view_layer.update()

    def pose(self, spec):
        """spec: list of (bone, axis, deg). Bones ending with '.' are applied to both sides, mirrored."""
        for bone, axis, deg in spec:
            self.rot(bone, axis, deg)

    def mirror(self, bone_l, axis, deg):
        """Apply to .L and mirrored to .R (mirror across YZ plane)."""
        self.rot(bone_l + '.L', axis, deg)
        ax = {'X': Vector((1, 0, 0)), 'Y': Vector((0, 1, 0)), 'Z': Vector((0, 0, 1))}.get(axis, axis)
        ax = Vector(ax)
        s = 1 if abs(ax.x) > 0.5 else -1     # rotation about X keeps sign; about Y/Z flips
        self.rot(bone_l + '.R', Vector((ax.x, ax.y, ax.z)), deg * s)

    def reset_pose(self):
        for pb in self.arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
        bpy.context.view_layer.update()

    def key(self, frame, bones=None):
        for pb in self.arm.pose.bones:
            if bones and pb.name not in bones:
                continue
            pb.keyframe_insert('rotation_quaternion', frame=frame)
            if pb.name == 'root':
                pb.keyframe_insert('location', frame=frame)

    def curl_fingers(self, side, deg, thumb=None):
        """Curl fingers 2..5 (and optionally the thumb) of one hand by rotating about each bone's local X."""
        for f in (2, 3, 4, 5):
            for s in (1, 2, 3):
                pb = self.pb(f'finger{f}-{s}.{side}')
                self._local(pb, deg * (0.9 if s == 1 else 1.0))
        if thumb is not None:
            for s in (2, 3):
                self._local(self.pb(f'finger1-{s}.{side}'), thumb)

    def _local(self, pb, deg, axis='X'):
        from mathutils import Quaternion
        ax = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}[axis]
        pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(ax, math.radians(deg))
