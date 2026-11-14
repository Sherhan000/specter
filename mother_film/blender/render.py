"""Shot renderer. Resumable: frames go to $RENDER_DIR/<shot>/f_####.png and existing frames are skipped.

  python3 render.py S01                 full-quality frames + clips/S01.mp4
  python3 render.py S01 --sheet 8       small contact sheet of 8 frames (for checking)
  python3 render.py S01 --still 120     one full-res frame
  python3 render.py S01 --preview       quarter-res animatic -> clips_preview/S01.mp4
  python3 render.py S01 --part 0/2      render only even frames (run several processes side by side)
"""
import sys, os, time, json, importlib, subprocess, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import common as C

ROOT = os.path.dirname(HERE)
RENDER_DIR = os.environ.get('RENDER_DIR', '/home/user/render')

ap = argparse.ArgumentParser()
ap.add_argument('shot')
ap.add_argument('--sheet', type=int, default=0)
ap.add_argument('--still', type=int, default=None)
ap.add_argument('--preview', action='store_true')
ap.add_argument('--frames', default=None)
ap.add_argument('--part', default=None)
ap.add_argument('--samples', type=int, default=None)
ap.add_argument('--scale', type=int, default=None)
ap.add_argument('--out', default=None)
a = ap.parse_args()

mod = importlib.import_module('shots.' + a.shot.lower())
sc = C.reset()
quality = 'sheet' if a.sheet else ('preview' if a.preview else 'final')
C.setup_cycles(sc, samples=getattr(mod, 'SAMPLES', 32))
shot = mod.build(sc, quality)
n = shot['frames']
update = shot.get('update')
if a.samples:
    sc.cycles.samples = a.samples


def render(f, path):
    sc.frame_set(f)
    if update:
        update(f)
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - t


if a.sheet:
    from PIL import Image
    sc.render.resolution_percentage = a.scale or 33
    sc.cycles.samples = a.samples or 16
    fr = [int(round(i * (n - 1) / max(1, a.sheet - 1))) for i in range(a.sheet)] if not a.frames else \
        [int(x) for x in a.frames.split(',')]
    ims = []
    for f in fr:
        p = f'/tmp/_sheet_{a.shot}_{f}.png'
        dt = render(f, p); ims.append(Image.open(p).convert('RGB')); print(f'frame {f}: {dt:.1f}s', flush=True)
    w, h = ims[0].size
    cols = 2 if len(ims) <= 8 else 3
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (w * cols, h * rows))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    out = a.out or f'/home/user/work/prev/{a.shot}_sheet.jpg'
    sheet.save(out, quality=90); print('sheet', out)
    sys.exit(0)

if a.still is not None:
    sc.render.resolution_percentage = a.scale or getattr(mod, 'SCALE', C.FINAL_SCALE)
    out = a.out or f'/home/user/work/prev/{a.shot}_{a.still:04d}.png'
    print(f'still {a.still}: {render(a.still, out):.1f}s -> {out}')
    sys.exit(0)

if a.preview:
    sc.render.resolution_percentage = a.scale or 33
    sc.cycles.samples = a.samples or 12
    d = f'{RENDER_DIR}/preview/{a.shot}'
else:
    sc.render.resolution_percentage = a.scale or getattr(mod, 'SCALE', C.FINAL_SCALE)
    d = f'{RENDER_DIR}/{a.shot}'
os.makedirs(d, exist_ok=True)
frames = list(range(n))
if a.frames:
    lo, hi = a.frames.split('-'); frames = list(range(int(lo), int(hi) + 1))
if a.part:
    k, m = a.part.split('/'); frames = [f for f in frames if f % int(m) == int(k)]
t0 = time.time(); done = 0
for f in frames:
    p = f'{d}/f_{f:04d}.png'
    if os.path.exists(p):
        continue
    open(p + '.lock', 'w').close() if False else None
    dt = render(f, p + '.tmp.png')
    os.replace(p + '.tmp.png', p)
    done += 1
    print(f'[{a.shot}] frame {f}/{n - 1} {dt:.1f}s  (avg {(time.time() - t0) / done:.1f}s)', flush=True)

missing = [f for f in range(n) if not os.path.exists(f'{d}/f_{f:04d}.png')]
if missing:
    print(f'[{a.shot}] {len(missing)} frames still missing (other part running?)')
    sys.exit(0)
cd = f'{ROOT}/clips_preview' if a.preview else f'{ROOT}/clips'
os.makedirs(cd, exist_ok=True)
out = f'{cd}/{a.shot}.mp4'
crf = '20' if a.preview else '15'
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', '24', '-i', f'{d}/f_%04d.png', '-vf', 'crop=trunc(iw/2)*2:trunc(ih/2)*2',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', crf, '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], check=True)
print(f'[{a.shot}] encoded {out}')
