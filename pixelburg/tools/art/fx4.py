"""Sky effects at the real-scale look: soft cumulus clouds and their shadows, storm clouds, birds."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _fbm(w, h, cells, seed, octaves=5):
    from sky import perlin2
    out = np.zeros((h, w))
    amp, total = 1.0, 0.0
    for o in range(octaves):
        out += perlin2(w, h, cells * 2 ** o, max(2, int(cells * h / w)) * 2 ** o, seed + o * 31) * amp
        total += amp
        amp *= 0.5
    return out / total + 0.5


def _cloud(seed, w, h, storm=False):
    """A soft cumulus: blobs of noisy density, lit from the upper left with self-shadowing."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    env = np.zeros((h, w))
    n = 9 if not storm else 16
    for i in range(n):
        t = rng.uniform(0.18, 0.82)
        bump = math.sin(t * math.pi)
        cx = w * t
        rx = w * rng.uniform(0.13, 0.22) * (0.6 + 0.5 * bump)
        ry = h * rng.uniform(0.25, 0.38) * (0.6 + 0.5 * bump)
        cy = h * 0.62 - ry * rng.uniform(0.2, 0.9) * bump
        env = np.maximum(env, np.exp(-(((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2) * 1.3))
    # a flatter base, as cumulus have
    env *= np.clip((h * 0.8 - ys) / (h * 0.08), 0, 1)
    nz = _fbm(w, h, 6, seed + 5, 6)
    D = env * (0.6 + 0.8 * nz) - 0.32
    alpha = np.clip(D / 0.22, 0, 1)
    # treat the smoothed density as a surface lit from the upper left; undersides grey
    from scipy import ndimage
    Ds = ndimage.gaussian_filter(np.clip(D, 0, None), 3.0)
    gy, gx = np.gradient(Ds)
    nrm = np.dstack([-gx * 40, -gy * 40, np.ones_like(D)])
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    L = np.array([-0.5, -0.7, 0.5])
    L /= np.linalg.norm(L)
    lam = np.clip((nrm * L).sum(-1), 0, 1)
    vert = np.clip(1.15 - ys / (h * 0.8), 0, 1)
    lit = np.clip(0.35 + 0.55 * lam + 0.35 * vert - 0.25 * np.clip(Ds * 2 - 0.4, 0, 1) * (1 - vert), 0, 1)
    if storm:
        lo, hi = np.array([54, 58, 74.0]), np.array([170, 174, 190.0])
        lit = lit * 0.8
    else:
        lo, hi = np.array([150, 164, 196.0]), np.array([255, 255, 255.0])
    rgb = lo[None, None, :] * (1 - lit[..., None]) + hi[None, None, :] * lit[..., None]
    a = alpha * (240 if not storm else 250)
    img = Image.fromarray(np.dstack([rgb, a]).clip(0, 255).astype(np.uint8), "RGBA")
    bb = img.getbbox()
    return img.crop(bb) if bb else img


def _shadow(img, strength):
    pad = 40
    a = np.asarray(img)[..., 3].astype(float) / 255
    a = np.pad(a, pad)
    sh = Image.fromarray((a * strength).astype(np.uint8), "L")
    sh = sh.resize((sh.width, max(1, sh.height // 2)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(14))
    out = Image.new("RGBA", sh.size, (8, 12, 24, 0))
    out.putalpha(sh)
    return out


def gen_clouds(out):
    for i, (w, h) in enumerate([(640, 300), (760, 340), (560, 260), (840, 380)]):
        img = _cloud(600 + i, w, h)
        img.save(os.path.join(out, "cloud_%d.png" % i))
        _shadow(img, 60).save(os.path.join(out, "cloud_shadow_%d.png" % i))
    for i, (w, h) in enumerate([(900, 420), (1000, 460)]):
        img = _cloud(700 + i, w, h, storm=True)
        img.save(os.path.join(out, "storm_%d.png" % i))
        _shadow(img, 90).save(os.path.join(out, "storm_shadow_%d.png" % i))


def gen_bird(out):
    """Two frames of a gull-like silhouette, wings up and down."""
    S = 4
    fw, fh = 32, 16
    sheet = Image.new("RGBA", (fw * 2 * S, fh * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(sheet)
    col = (44, 46, 58, 255)
    for f, lift in enumerate([-5, 3]):
        ox = f * fw * S
        cx, cy = ox + fw * S / 2, fh * S / 2 + 1 * S
        for side in (-1, 1):
            pts = [(cx, cy), (cx + side * 6 * S, cy + lift * S * 0.6 - 2 * S), (cx + side * 14 * S, cy + lift * S),
                   (cx + side * 6 * S, cy + lift * S * 0.6 - 0.6 * S), (cx, cy + 1.6 * S)]
            d.polygon(pts, fill=col)
        d.ellipse((cx - 2.2 * S, cy - 1.2 * S, cx + 2.2 * S, cy + 1.8 * S), fill=col)
    sheet = sheet.resize((fw * 2, fh), Image.LANCZOS)
    sheet.save(os.path.join(out, "bird.png"))


def gen(root):
    gen_clouds(os.path.join(root, "nature"))
    gen_bird(os.path.join(root, "fx"))


if __name__ == "__main__":
    import sys
    gen(sys.argv[1])
