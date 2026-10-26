"""Backdrop beyond the horizon: mountain ranges, rolling hills, distant towns with night lights
and the forest edge. Every strip tiles horizontally. Colours are the daylight look; the game
mixes in the haze of the hour and darkens them at night."""
import os

import numpy as np
from PIL import Image, ImageFilter


def _noise1(w, cells, seed, octaves=5, gain=0.5):
    """Periodic fractal value noise along x, values in [0,1]."""
    rng = np.random.default_rng(seed)
    x = np.arange(w)
    out = np.zeros(w)
    a, total = 1.0, 0.0
    for o in range(octaves):
        c = cells * 2 ** o
        g = rng.random(c)
        t = x * c / w
        i0 = np.floor(t).astype(int)
        f = t - i0
        f = f * f * (3 - 2 * f)
        out += (g[i0 % c] * (1 - f) + g[(i0 + 1) % c] * f) * a
        total += a
        a *= gain
    return out / total


def _sample1(table, u):
    """Linear lookup into a periodic 1-D table at fractional positions u."""
    w = table.shape[0]
    i0 = np.floor(u).astype(int)
    f = u - i0
    return table[i0 % w] * (1 - f) + table[(i0 + 1) % w] * f


def _noise2(w, h, cx, cy, seed, octaves=4):
    """Fractal noise periodic in x with separate cell counts across and down."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    a, total = 1.0, 0.0
    for o in range(octaves):
        nx = cx * 2 ** o
        ny = max(2, cy * 2 ** o)
        g = rng.random((ny + 2, nx))
        tx = np.arange(w) * nx / w
        ty = np.arange(h) * ny / h
        x0 = np.floor(tx).astype(int)
        y0 = np.floor(ty).astype(int)
        fx = tx - x0
        fy = ty - y0
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        a00 = g[y0][:, x0 % nx]
        a01 = g[y0][:, (x0 + 1) % nx]
        a10 = g[y0 + 1][:, x0 % nx]
        a11 = g[y0 + 1][:, (x0 + 1) % nx]
        top = a00 * (1 - fx)[None, :] + a01 * fx[None, :]
        bot = a10 * (1 - fx)[None, :] + a11 * fx[None, :]
        out += (top * (1 - fy)[:, None] + bot * fy[:, None]) * a
        total += a
        a *= 0.5
    return out / total


def _smooth(v, r):
    k = np.ones(2 * r + 1) / (2 * r + 1)
    return np.convolve(np.concatenate([v[-r:], v, v[:r]]), k, mode="same")[r:-r]


def _ridge_profile(w, cells, seed, sharp=1.5):
    """Mountain crest line in [0,1]: ridged noise with pointed peaks."""
    n = _noise1(w, cells, seed, 6, 0.5)
    r = 1 - np.abs(n - 0.5) * 2
    big = _noise1(w, max(1, cells // 2), seed + 1, 3)
    return np.clip(r ** sharp * (0.55 + 0.6 * big), 0, 1)


def perlin2(w, z, cx, cz, seed):
    """Gradient noise on a (z, w) grid, periodic in x, values about [-0.7, 0.7]."""
    rng = np.random.default_rng(seed)
    ang = rng.random((cz + 2, cx)) * 2 * np.pi
    gx, gy = np.cos(ang), np.sin(ang)
    u = np.arange(w) * cx / w
    v = np.arange(z) * cz / z
    x0 = np.floor(u).astype(int)
    y0 = np.floor(v).astype(int)
    fx = (u - x0)[None, :]
    fy = (v - y0)[:, None]
    X0, X1 = x0 % cx, (x0 + 1) % cx

    def dot(yi, xi, dx, dy):
        return gx[yi][:, xi] * dx + gy[yi][:, xi] * dy

    n00 = dot(y0, X0, fx, fy)
    n10 = dot(y0, X1, fx - 1, fy)
    n01 = dot(y0 + 1, X0, fx, fy - 1)
    n11 = dot(y0 + 1, X1, fx - 1, fy - 1)
    sx = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    sy = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    a = n00 * (1 - sx) + n10 * sx
    b = n01 * (1 - sx) + n11 * sx
    return a * (1 - sy) + b * sy


def ridged(w, z, cx, cz, seed, octaves=7):
    out = np.zeros((z, w))
    weight = np.ones((z, w))
    amp, total = 1.0, 0.0
    for o in range(octaves):
        n = perlin2(w, z, cx * 2 ** o, cz * 2 ** o, seed + o * 13)
        r = (1 - np.abs(n) * 1.6) ** 2
        r = np.clip(r, 0, 1) * weight
        weight = np.clip(r * 1.8, 0, 1)
        out += r * amp
        total += amp
        amp *= 0.52
    return out / total


def fbm(w, z, cx, cz, seed, octaves=5):
    out = np.zeros((z, w))
    amp, total = 1.0, 0.0
    for o in range(octaves):
        out += perlin2(w, z, cx * 2 ** o, cz * 2 ** o, seed + o * 7) * amp
        total += amp
        amp *= 0.5
    return out / total + 0.5


def landscape(H, h, colour, depth_fog, fog_col, rise=0.55, persp=0.5):
    """Render a height field H (rows far..near, columns) as a side view, voxel style.
    colour(Hn, nx, nz, shade) -> (Z, W, 3). Returns an RGBA image (h, W)."""
    Z, W = H.shape
    zr = np.arange(Z)[:, None] / (Z - 1)                  # 0 far .. 1 near
    scale = persp + (1 - persp) * zr
    y = h - (1 - zr) * Z * rise - H * scale               # screen y of each sample
    dHx = np.gradient(H, axis=1)
    dHz = np.gradient(H, axis=0) / max(rise, 0.05)
    n = np.stack([-dHx, -dHz * 0.6, np.ones_like(H)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.62, 0.35, 0.7])
    L /= np.linalg.norm(L)
    shade = np.clip((n * L).sum(-1), 0, 1)
    col = colour(H, n, shade)
    fog = (1 - zr) ** 1.3 * depth_fog
    col = col * (1 - fog[..., None]) + fog_col[None, None, :] * fog[..., None]
    # front-to-back running minimum of y decides which row shows at each pixel
    yf = y[::-1]
    ymin = np.minimum.accumulate(yf, axis=0)
    img = np.zeros((h, W, 4))
    ys = np.arange(h) + 0.5
    for x in range(W):
        k = np.searchsorted(-ymin[:, x], -ys, side="left")
        vis = k < Z
        zi = Z - 1 - np.minimum(k, Z - 1)
        img[vis, x, :3] = col[zi[vis], x]
        img[vis, x, 3] = 255
    return img


def mountains_far(w, h):
    Z = 300
    zr = np.linspace(0, 1, Z)[:, None]
    R = ridged(w, Z, 4, 3, 11, 6)
    env = 0.3 + 0.7 * np.exp(-((zr - 0.3) / 0.4) ** 2)
    H = R * env * 330

    def colour(H, n, shade):
        rock = np.array([96, 106, 128.0])
        snow = np.array([250, 252, 255.0])
        flat = n[..., 2]
        sn = np.clip((H - 112 + (flat - 0.7) * 230) / 20, 0, 1)
        base = rock[None, None, :] * (1 - sn[..., None]) + snow[None, None, :] * sn[..., None]
        lit = 0.42 + 0.72 * shade
        return base * lit[..., None]
    return _out(landscape(H, h, colour, 0.55, np.array([196, 212, 232.0]), rise=0.35, persp=0.55))


def mountains_mid(w, h):
    Z = 240
    zr = np.linspace(0, 1, Z)[:, None]
    R = ridged(w, Z, 6, 3, 23, 6)
    env = 0.25 + 0.75 * np.exp(-((zr - 0.3) / 0.38) ** 2)
    H = R * env * 230
    grain = fbm(w, Z, 300, 40, 29, 3)

    def colour(H, n, shade):
        flat = n[..., 2]
        rock = np.array([108, 112, 118.0])
        forest = np.array([58, 84, 64.0]) * (0.85 + 0.3 * grain[..., None])
        snow = np.array([240, 244, 252.0])
        trees = np.clip((157 - H + (flat - 0.8) * 160) / 30, 0, 1)
        base = rock[None, None, :] * (1 - trees[..., None]) + forest * trees[..., None]
        sn = np.clip((H - 180 + (flat - 0.75) * 200) / 20, 0, 1)
        base = base * (1 - sn[..., None]) + snow[None, None, :] * sn[..., None]
        lit = 0.42 + 0.72 * shade
        return base * lit[..., None]
    return _out(landscape(H, h, colour, 0.45, np.array([178, 198, 218.0]), rise=0.3, persp=0.55))


def hills(w, h):
    Z = 160
    zr = np.linspace(0, 1, Z)[:, None]
    F = fbm(w, Z, 9, 3, 37, 5)
    H = np.clip(F - 0.3, 0, None) * 190 * (0.6 + 0.4 * (1 - zr))
    q = fbm(w, Z, 50, 12, 43, 3)
    grain = fbm(w, Z, 500, 60, 47, 2)

    def colour(H, n, shade):
        fw = np.clip((q - 0.5) * 12 + 0.5, 0, 1)[..., None]
        base = np.array([60, 92, 62.0])[None, None, :] * fw + np.array([122, 150, 90.0])[None, None, :] * (1 - fw)
        base = base * (0.85 + 0.3 * grain[..., None])
        lit = 0.5 + 0.62 * shade
        return base * lit[..., None]
    return _out(landscape(H, h, colour, 0.35, np.array([170, 192, 205.0]), rise=0.3, persp=0.6))


def treeline(w, h, seed=61):
    """The edge of the forest where the valley floor meets the hills: rows of crowns."""
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 4))
    n = _noise2(w, h, 700, 40, 63, 2)
    for row, (count, base, dark) in enumerate([(w // 9, h - 22, 1.08), (w // 7, h - 10, 0.96), (w // 8, h, 0.84)]):
        for i in range(count):
            cx = rng.uniform(0, w)
            conifer = rng.random() < 0.45
            tone = rng.uniform(0.9, 1.1) * dark
            leaf = np.array([66, 98, 64.0]) if not conifer else np.array([48, 78, 58.0])
            if conifer:
                r = rng.uniform(5, 9)
                hh = rng.uniform(32, 62)
            else:
                r = rng.uniform(9, 16)
                hh = rng.uniform(26, 50)
            x0, x1 = int(cx - r - 1), int(cx + r + 2)
            y0, y1 = max(0, int(base - hh - r)), int(min(h, base))
            if y1 <= y0:
                continue
            ys = np.arange(y0, y1)[:, None] + 0.5
            xs = np.arange(x0, x1)[None, :] + 0.5
            dx = (xs - cx) / r
            if conifer:
                t = (ys - (base - hh)) / hh                    # 0 tip .. 1 foot
                inside = (np.abs(dx) < t * 1.05) & (t >= 0)
                light = 1.0 - dx * 0.25 - t * 0.15
            else:
                cy = base - hh + r
                dy = (ys - cy) / r
                d2 = dx * dx + dy * dy
                inside = (d2 < 1) | ((ys > cy) & (np.abs(dx) < 0.95))
                light = 1.05 - dx * 0.22 - dy * 0.22
            cols = np.arange(x0, x1) % w
            sub = img[y0:y1][:, cols]
            nn = n[y0:y1][:, cols]
            c = leaf[None, None, :] * (light * tone)[..., None] * (0.86 + 0.28 * nn[..., None])
            sub[..., :3] = np.where(inside[..., None], c, sub[..., :3])
            sub[..., 3] = np.where(inside, 255, sub[..., 3])
            img[y0:y1, cols] = sub
    return _out(img)


def skyline(w, h, seed=51):
    """Distant towns: silhouettes in the day, windows and street glow at night."""
    rng = np.random.default_rng(seed)
    body = np.zeros((h, w, 4))
    glow = np.zeros((h, w, 4))
    x = int(rng.integers(80, 300))
    while x < w - 200:
        big = rng.random() < 0.3
        cw = int(rng.integers(300, 600)) if big else int(rng.integers(110, 300))
        bx = x
        centre = x + cw / 2
        while bx < x + cw:
            bw = int(rng.integers(10, 26))
            k = 1 - abs(bx + bw / 2 - centre) / (cw / 2)          # taller in the middle
            tall = rng.random()
            bh = int(rng.uniform(10, 26) + k * rng.uniform(4, 30 if not big else 60))
            if big and tall > 0.88 and k > 0.4:
                bh = int(rng.uniform(60, 100))
            base = np.array([128, 138, 156.0]) * rng.uniform(0.86, 1.04)
            for xx in range(bx, bx + bw):
                side = 1.06 if xx - bx < bw * 0.45 else 0.9           # sunny and shaded walls
                body[h - bh:h, xx % w, :3] = base * side
                body[h - bh:h, xx % w, 3] = 255
            if bh < 30 and rng.random() < 0.5:                       # pitched roofs on low houses
                for j in range(bw // 2):
                    for xx in (bx + j, bx + bw - 1 - j):
                        body[h - bh - j:h - bh, xx % w, :3] = (128, 104, 100)
                        body[h - bh - j:h - bh, xx % w, 3] = 255
            for yy in range(h - bh + 3, h - 2, 4):
                for xx in range(bx + 2, bx + bw - 2, 3):
                    if rng.random() < 0.42:
                        warm = rng.random() < 0.8
                        glow[yy:yy + 2, xx % w:(xx % w) + 2] = (255, 210, 140, 255) if warm else (200, 220, 255, 255)
                        body[yy:yy + 2, xx % w:(xx % w) + 2, :3] *= 0.85
            if bh > 70:
                glow[h - bh - 3:h - bh - 1, (bx + bw // 2) % w] = (255, 70, 60, 255)
            bx += bw + int(rng.integers(0, 4))
        # the orange glow of street lights over the town
        gx = np.arange(w)
        dx = np.minimum(np.abs(gx - centre), w - np.abs(gx - centre))
        ys = np.arange(h)[:, None]
        fall = np.exp(-(dx[None, :] / (cw * 0.55)) ** 2) * np.exp(-(h - ys) / 22.0)
        glow[..., 0] = np.maximum(glow[..., 0], 255 * fall * 0.55)
        glow[..., 1] = np.maximum(glow[..., 1], 170 * fall * 0.55)
        glow[..., 2] = np.maximum(glow[..., 2], 90 * fall * 0.55)
        glow[..., 3] = np.maximum(glow[..., 3], 255 * fall * 0.55)
        x += cw + int(rng.integers(260, 700))
    return _out(body), _out(glow)


def _out(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def gen(out):
    os.makedirs(out, exist_ok=True)
    W = 4096
    mountains_far(W, 420).save(os.path.join(out, "mtn_far.png"))
    mountains_mid(W, 300).save(os.path.join(out, "mtn_mid.png"))
    hills(W, 150).save(os.path.join(out, "hills.png"))
    b, g = skyline(W, 160)
    b.save(os.path.join(out, "skyline.png"))
    g.save(os.path.join(out, "skyline_glow.png"))
    treeline(W, 90).save(os.path.join(out, "treeline.png"))


if __name__ == "__main__":
    import sys
    gen(sys.argv[1])
