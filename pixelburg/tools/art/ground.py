"""Tileable ground textures for the terrain shader, plus the world terrain map.

Every texture wraps seamlessly, so the shader can repeat it over the whole valley.
"""
import json
import math
import os

import numpy as np
from PIL import Image
from scipy import ndimage


def periodic_noise(n, cells, seed, octaves=4, persistence=0.5):
    """Fractal value noise in [0,1] that wraps on an n x n square."""
    rng = np.random.default_rng(seed)
    out = np.zeros((n, n))
    amp, total = 1.0, 0.0
    for o in range(octaves):
        c = cells * (2 ** o)
        if c > n:
            break
        g = rng.random((c, c))
        t = np.arange(n) * c / n
        i0 = np.floor(t).astype(int)
        f = t - i0
        f = f * f * (3 - 2 * f)
        i1 = (i0 + 1) % c
        a = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i1] * f[None, :]
        b = g[i1][:, i0] * (1 - f)[None, :] + g[i1][:, i1] * f[None, :]
        out += (a * (1 - f)[:, None] + b * f[:, None]) * amp
        total += amp
        amp *= persistence
    return out / total


def cells_noise(n, k, seed, pts=None):
    """Wrapping Worley noise: distance to the nearest of k random points, normalised."""
    rng = np.random.default_rng(seed)
    if pts is None:
        pts = rng.random((k, 2)) * n
    ys, xs = np.mgrid[0:n, 0:n] + 0.5
    best = np.full((n, n), 1e9)
    second = np.full((n, n), 1e9)
    ident = np.zeros((n, n), int)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(xs - px)
        dy = np.abs(ys - py)
        dx = np.minimum(dx, n - dx)
        dy = np.minimum(dy, n - dy)
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < best
        second = np.where(closer, best, np.minimum(second, d))
        ident = np.where(closer, i, ident)
        best = np.where(closer, d, best)
    return best, second, ident


def mix(a, b, t):
    return a * (1 - t[..., None]) + b * t[..., None]


def col(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def save(arr, path):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(path)


def specks(n, count, seed, size=1):
    rng = np.random.default_rng(seed)
    m = np.zeros((n, n))
    ys = rng.integers(0, n, count)
    xs = rng.integers(0, n, count)
    vals = rng.random(count)
    for dy in range(size):
        for dx in range(size):
            m[(ys + dy) % n, (xs + dx) % n] = vals
    return m


def blades(n, count, seed, length=6):
    """Short slanted strokes, like blades of grass seen from above at an angle."""
    rng = np.random.default_rng(seed)
    m = np.zeros((n, n))
    ys = rng.integers(0, n, count)
    xs = rng.integers(0, n, count)
    vals = rng.uniform(-1, 1, count)
    lens = rng.integers(2, length + 1, count)
    for i in range(count):
        for k in range(lens[i]):
            m[(ys[i] - k) % n, (xs[i] + (k // 3)) % n] = vals[i] * (1 - k / (lens[i] + 1))
    return m


# ---------------------------------------------------------------------------- textures
def grass(n=512):
    lo = periodic_noise(n, 4, 1, 4)
    mid = periodic_noise(n, 16, 2, 3)
    hi = periodic_noise(n, 64, 3, 2)
    base = mix(col("4f8f34"), col("6fae47"), np.clip(lo * 1.6 - 0.3, 0, 1))
    base = mix(base, col("3f7a2a"), np.clip((mid - 0.55) * 3, 0, 1) * 0.7)
    base = mix(base, col("86b856"), np.clip((hi - 0.6) * 3, 0, 1) * 0.35)
    b = blades(n, 9000, 4)
    base += np.where(b > 0, b * 34, b * 26)[..., None] * np.array([0.8, 1.0, 0.55])
    flowers = specks(n, 260, 5, 2) > 0.985
    base[flowers] = col("f2e7a0")
    return base


def forest_floor(n=512):
    lo = periodic_noise(n, 6, 11, 4)
    mid = periodic_noise(n, 24, 12, 3)
    base = mix(col("2f4a22"), col("4a5a2a"), np.clip(lo * 1.5 - 0.2, 0, 1))
    base = mix(base, col("5a4a2e"), np.clip((mid - 0.5) * 2.5, 0, 1) * 0.6)
    leaves = specks(n, 7000, 13, 2)
    base += ((leaves > 0.5) * (leaves - 0.5) * 50)[..., None] * np.array([1.0, 0.7, 0.3])
    base -= ((leaves > 0) & (leaves < 0.3))[..., None] * 18
    b = blades(n, 3000, 14, 4)
    base += (b * 20)[..., None] * np.array([0.6, 1.0, 0.5])
    return base


def soil(n=512):
    lo = periodic_noise(n, 8, 21, 4)
    hi = periodic_noise(n, 96, 22, 2)
    base = mix(col("6e5236"), col("8a6a46"), np.clip(lo * 1.4 - 0.2, 0, 1))
    base += ((hi - 0.5) * 26)[..., None]
    clods = specks(n, 5000, 23, 2)
    base -= ((clods > 0.7) * 22)[..., None]
    base += ((clods > 0) & (clods < 0.15))[..., None] * 18
    return base


def dirt(n=512):
    lo = periodic_noise(n, 6, 31, 4)
    hi = periodic_noise(n, 80, 32, 2)
    base = mix(col("8a6c48"), col("a88a5e"), np.clip(lo * 1.4 - 0.2, 0, 1))
    base += ((hi - 0.5) * 22)[..., None]
    peb = specks(n, 2600, 33, 2)
    base[peb > 0.8] = col("c2ad8a")
    base[(peb > 0) & (peb < 0.12)] = col("5e4a34")
    return base


def asphalt(n=512):
    lo = periodic_noise(n, 5, 41, 4)
    hi = periodic_noise(n, 128, 42, 2)
    base = mix(col("45474d"), col("53555b"), np.clip(lo * 1.5 - 0.25, 0, 1))
    base += ((hi - 0.5) * 16)[..., None]
    agg = specks(n, 16000, 43, 1)
    base += ((agg > 0.75) * 22)[..., None]
    base -= ((agg > 0) & (agg < 0.25))[..., None] * 10
    return base


def paving(n=512):
    lo = periodic_noise(n, 6, 51, 3)
    hi = periodic_noise(n, 128, 52, 2)
    base = mix(col("b4ada2"), col("c6c0b4"), np.clip(lo * 1.4 - 0.2, 0, 1))
    base += ((hi - 0.5) * 14)[..., None]
    sp = specks(n, 6000, 53, 1)
    base -= ((sp > 0.8) * 16)[..., None]
    return base


def cobble(n=256):
    rng = np.random.default_rng(62)
    k = 16
    gy, gx = np.mgrid[0:k, 0:k].astype(float)
    gx += (gy % 2) * 0.5
    pts = np.stack([(gx + 0.5 + rng.uniform(-0.18, 0.18, gx.shape)) * n / k,
                    (gy + 0.5 + rng.uniform(-0.18, 0.18, gy.shape)) * n / k], -1).reshape(-1, 2) % n
    best, second, ident = cells_noise(n, len(pts), 61, pts)
    tones = rng.uniform(-16, 16, len(pts))
    gap = second - best
    edge = np.clip((gap - 1.0) / 2.5, 0, 1)
    round_ = np.clip(gap / 9.0, 0, 1) ** 0.6
    base = col("8a8680") + tones[ident][..., None] + (round_ * 26 - 10)[..., None]
    base += ((periodic_noise(n, 64, 63, 2) - 0.5) * 12)[..., None]
    base = mix(col("4a4640"), base, edge)
    return base


def noise_rgba(n=256):
    r = periodic_noise(n, 4, 71, 4) * 255
    g = periodic_noise(n, 16, 72, 3) * 255
    b = periodic_noise(n, 48, 73, 2) * 255
    best, second, _ = cells_noise(n, 40, 74)
    a = np.clip((second - best) / 14.0, 0, 1) * 255
    return np.dstack([r, g, b, a])


def gen_textures(out):
    os.makedirs(out, exist_ok=True)
    for name, fn in (("grass", grass), ("forest", forest_floor), ("soil", soil), ("dirt", dirt),
                     ("asphalt", asphalt), ("paving", paving), ("cobble", cobble)):
        save(fn(), os.path.join(out, name + ".png"))
    save(noise_rgba(), os.path.join(out, "noise.png"))


# ---------------------------------------------------------------------------- world map
def gen_terrain(out, W):
    """Terrain weights per tile: R forest, G farmland, B water, A dry meadow.

    W carries the world layout (same numbers as scripts/data.gd)."""
    n = W["MAP"]
    l0, l1 = W["LAND0"], W["LAND1"]
    ys, xs = np.mgrid[0:n, 0:n].astype(float)
    # distance (in tiles) outside the land square, 0 on the land
    dx = np.maximum(np.maximum(l0 - xs, xs - (l1 - 1)), 0)
    dy = np.maximum(np.maximum(l0 - ys, ys - (l1 - 1)), 0)
    dist = np.maximum(dx, dy)
    lo = ndimage.zoom(periodic_noise(64, 4, 81, 4), n / 64, order=1)[:n, :n]
    mid = ndimage.zoom(periodic_noise(64, 10, 82, 3), n / 64, order=1)[:n, :n]
    forest = np.zeros((n, n))
    field = np.zeros((n, n))
    water = np.zeros((n, n))
    outside = dist > 0
    band = W["FOREST"]
    # thick forest right around the land, thinning into countryside further out
    n12 = ndimage.zoom(periodic_noise(64, 12, 86, 3), n / 64, order=1)[:n, :n]
    near = np.clip((band + 3 + (n12 - 0.5) * 22 + (lo - 0.5) * 10 - dist) / 4.0, 0, 1)
    patches = np.clip((lo - np.quantile(lo, 0.55)) * 7 + (mid - 0.5) * 1.2, 0, 1)
    forest = np.where(outside, np.clip(np.maximum(near * 1.3, patches), 0, 1), 0)
    # the forest does not start at a line: it thins out over a ragged fringe several tiles wide
    hi_n = ndimage.zoom(periodic_noise(64, 24, 85, 2), n / 64, order=1)[:n, :n]
    fringe = np.maximum(0.8, 3.5 + (hi_n - 0.5) * 9.0 + (mid - 0.5) * 6.0)
    forest = forest * np.clip((dist - fringe) / 3.0, 0, 1)
    # woods along the far end of the valley lead the eye into the treeline of the backdrop
    if "HORIZON" in W:
        far = W["HORIZON"] + 8 + (n12 - 0.5) * 12 + (lo - 0.5) * 22 + (hi_n - 0.5) * 6 - (xs + ys)
        forest = np.maximum(forest, np.where(outside & (dist > 4), np.clip(far / 3.0, 0, 1), 0))
    # farmland in the open countryside
    open_land = outside & (dist > band + 2) & (forest < 0.35)
    fq = np.quantile(mid, 0.5)
    field = np.where(open_land & (mid > fq), np.clip((mid - fq) * 8, 0, 1), 0)
    # two quiet lakes
    for (lx, ly, r) in W["LAKES"]:
        d = np.hypot(xs - lx, (ys - ly) * 1.15)
        wob = (mid - 0.5) * 3.0
        water = np.maximum(water, np.clip((r + wob - d) / 2.0, 0, 1))
    forest = np.where(water > 0.05, 0, forest)
    field = np.where(water > 0.05, 0, field)
    # keep roads and their verges clear
    for (x, y) in W["CLEAR"]:
        x0, x1 = max(0, x - 1), min(n, x + 2)
        y0, y1 = max(0, y - 1), min(n, y + 2)
        forest[y0:y1, x0:x1] = np.minimum(forest[y0:y1, x0:x1], 0.0)
        field[y0:y1, x0:x1] = 0
        water[y, x] = 0
    dry = np.clip((lo - 0.45) * 2.5, 0, 1) * np.where(outside, 1.0, 0.45)
    img = np.dstack([forest, field, water, dry]) * 255
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(out, "terrain.png"))
    return forest, field, water


if __name__ == "__main__":
    import sys
    gen_textures(sys.argv[1])
