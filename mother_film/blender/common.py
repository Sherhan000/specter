"""Scene / render helpers shared by all shots."""
import bpy, os, sys, math
from mathutils import Vector

FPS = 24
RES = (1920, 804)        # 2.39:1 - the final cut is letterboxed anyway, so the bars are not rendered
FINAL_SCALE = 75         # rendered at 1440x603 and upscaled in the edit (4 CPU cores, no GPU)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.world = bpy.data.worlds.new('World')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0, 0, 0, 1)
    return sc


def setup_cycles(sc, samples=96, scale=100, threads=0, denoise=True, noise=0.03):
    r = sc.render
    r.engine = 'CYCLES'
    r.resolution_x, r.resolution_y = RES
    r.resolution_percentage = scale
    c = sc.cycles
    c.device = 'CPU'
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = noise
    c.adaptive_min_samples = max(8, samples // 6)
    c.use_denoising = denoise
    try:
        c.denoiser = 'OPENIMAGEDENOISE'
        c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        c.denoising_prefilter = 'FAST'
    except Exception as e:
        print('denoiser:', e)
    c.max_bounces = 5
    c.diffuse_bounces = 3
    c.glossy_bounces = 3
    c.transmission_bounces = 4
    c.volume_bounces = 0
    c.transparent_max_bounces = 6
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 6.0
    c.sample_clamp_direct = 0.0
    c.use_auto_tile = False
    r.threads_mode = 'FIXED' if threads else 'AUTO'
    if threads:
        r.threads = threads
    r.use_persistent_data = False
    r.film_transparent = False
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_mode = 'RGB'
    r.image_settings.color_depth = '8'
    r.image_settings.compression = 15
    sc.view_settings.view_transform = 'Filmic' if 'Filmic' in _views(sc) else 'AgX'
    sc.view_settings.look = 'None'
    return sc


def _views(sc):
    return [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items]


def set_look(sc, transform='AgX', look=None, exposure=0.0, gamma=1.0):
    sc.view_settings.view_transform = transform
    if look:
        try:
            sc.view_settings.look = look
        except Exception:
            try:
                sc.view_settings.look = transform + ' - ' + look
            except Exception as e:
                print('look fallback failed', e)
    sc.view_settings.exposure = exposure
    sc.view_settings.gamma = gamma


def camera(sc, loc, target, lens=50, fstop=None, focus=None, sensor=36, name='Cam'):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens; cd.sensor_width = sensor
    cd.clip_start = 0.01; cd.clip_end = 5000
    ob = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = focus if focus else (Vector(target) - Vector(loc)).length
    sc.camera = ob
    return ob


def look_at(ob, target, roll=0.0):
    d = Vector(target) - Vector(ob.location)
    q = d.to_track_quat('-Z', 'Y')
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = q
    if roll:
        from mathutils import Quaternion
        ob.rotation_quaternion = q @ Quaternion((0, 0, 1), roll)


def light(sc, kind, loc, energy, color=(1, 1, 1), target=None, size=0.5, spot=None, blend=0.3, name=None, rot=None):
    ld = bpy.data.lights.new(name or kind, kind)
    ld.energy = energy; ld.color = color
    if kind == 'AREA':
        ld.size = size
    elif kind in ('POINT', 'SPOT'):
        ld.shadow_soft_size = size
    elif kind == 'SUN':
        ld.angle = size
    if kind == 'SPOT' and spot:
        ld.spot_size = math.radians(spot); ld.spot_blend = blend
    ob = bpy.data.objects.new(name or kind, ld)
    sc.collection.objects.link(ob)
    ob.location = loc
    if target is not None:
        look_at(ob, target)
    if rot is not None:
        ob.rotation_mode = 'XYZ'; ob.rotation_euler = [math.radians(a) for a in rot]
    return ob


def render_still(sc, path, frame=None):
    if frame is not None:
        sc.frame_set(frame)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def apply_modifier(ob, name):
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=name)


def args():
    a = sys.argv
    return a[a.index('--') + 1:] if '--' in a else []


def preview(sc, path, target=(0, 0, 0.8), dist=4.0, views=('front', 'side', 'top', 'q'), res=(420, 420), samples=12):
    """Quick neutral-lit contact sheet of the scene from several directions (for checking poses)."""
    import numpy as np
    saved = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.render.resolution_percentage)
    w = sc.world.node_tree.nodes['Background']
    old = (tuple(w.inputs[0].default_value), w.inputs[1].default_value)
    w.inputs[0].default_value = (0.5, 0.5, 0.5, 1); w.inputs[1].default_value = 1.0
    sun = light(sc, 'SUN', (0, 0, 10), 2.5, rot=(40, 0, 30), name='_pv')
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100; sc.cycles.samples = samples
    dirs = {'front': (0, -1, 0.1), 'back': (0, 1, 0.1), 'side': (1, 0, 0.1), 'left': (-1, 0, 0.1), 'top': (0, -0.05, 1),
            'q': (0.7, -0.7, 0.45), 'q2': (-0.7, -0.7, 0.45)}
    t = Vector(target); files = []
    for v in views:
        d = Vector(dirs[v]).normalized()
        cam = camera(sc, t + d * dist, t, lens=50, name='_pvcam')
        f = f'{path}_{v}.png'
        render_still(sc, f); files.append(f)
        bpy.data.objects.remove(cam)
    bpy.data.objects.remove(sun)
    w.inputs[0].default_value = old[0]; w.inputs[1].default_value = old[1]
    sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.render.resolution_percentage = saved
    try:
        from PIL import Image
        ims = [Image.open(f) for f in files]
        sheet = Image.new('RGB', (res[0] * len(ims), res[1]))
        for i, im in enumerate(ims):
            sheet.paste(im, (i * res[0], 0))
        sheet.save(path + '.jpg', quality=88)
        for f in files:
            os.remove(f)
    except Exception as e:
        print('sheet:', e)
    return path + '.jpg'
