"""Props at real scale (10 units = 1 m): trees, hedges, fences, lamps, garden things, rooftop kit,
and ground surfaces for lots. Lawns are left transparent so the valley grass shows through."""
import math

import numpy as np

from raster import C, U, M, flat, flat3, hash2, nores, solid_res, glow_res, value_noise, noise3

LEAF = {
    "oak": ["2c5a24", "3a6e2e", "4b8236", "659846"],
    "maple": ["38662a", "477a30", "588e3a", "73a24c"],
    "birch": ["46782e", "578c36", "6ca044", "86b458"],
    "lime": ["2a5626", "386a2e", "497e36", "62944a"],
    "pine": ["24503a", "2e6044", "3a704c", "4c8458"],
    "spruce": ["1f4a34", "275a3e", "336a48", "447c54"],
    "fruit": ["3e7230", "4e8638", "609a42", "7aae56"],
    "hedge": ["325e28", "3e7030", "4c8238", "609446"],
}


def leaf_fn(kind="oak", seed=0, blossom=None, density=0.12, zr=None):
    """Foliage: lit by its own normal in a few soft tones, broken into leaf clumps."""
    pal = np.array([C(c) for c in LEAF[kind]])
    from raster import LIGHT

    def fn(wx, wy, wz, nx, ny, nz):
        shape = wx.shape
        lit = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], -0.3, 1)
        big = noise3(wx / 7.0, wy / 7.0, wz / 7.0, seed)
        small = noise3(wx / 2.2, wy / 2.2, wz / 2.2, seed + 1)
        speck = hash2(np.floor(wx), np.floor(wy * 3 + wz), seed + 2)
        lum = 0.2 + 0.62 * lit + (big - 0.5) * 0.55 + (small - 0.5) * 0.3 + (speck - 0.5) * 0.08
        if zr is not None:
            t = np.clip((wz - zr[0]) / max(1.0, zr[1] - zr[0]), 0, 1)
            lum = lum - (1 - t) ** 2 * 0.35
        lum = np.clip(lum, 0, 0.999)
        idx = (lum * len(pal)).astype(int)
        frac = lum * len(pal) - idx
        nxt = np.minimum(idx + 1, len(pal) - 1)
        rgb = pal[idx] * (1 - frac[..., None] * 0.5) + pal[nxt] * (frac[..., None] * 0.5)
        gap = (small < 0.28) & (big < 0.5)
        rgb[gap] = rgb[gap] * 0.72
        if blossom is not None:
            b = (hash2(np.floor(wx / 1.5), np.floor((wy + wz) / 1.5), seed + 9) < density) & (lum > 0.3)
            rgb[b] = C(blossom) * (0.85 + 0.2 * lum[b])[..., None]
        return rgb, np.ones(shape, bool), None
    return fn


def trunk_fn(col="6a4a30", birch=False):
    c = C(col)

    def side(ang, v, nx, ny):
        shape = ang.shape
        rgb = np.broadcast_to(c, shape + (3,)).copy()
        bark = hash2(np.floor(ang * 6), np.floor(v / 2.5), 3)
        rgb *= (0.82 + 0.3 * bark)[..., None]
        if birch:
            rgb = np.broadcast_to(C("e8e4dc"), shape + (3,)).copy()
            spots = hash2(np.floor(ang * 5), np.floor(v / 1.6), 4) < 0.25
            rgb[spots] = C("3a3430")
        return rgb, nores(shape), None
    return side


def crown(cv, x, y, z0, R, H, kind="oak", seed=0, clumps=8, blossom=None, flat_top=1.0):
    """A leafy crown: overlapping lumps with a ragged edge, as one solid volume."""
    rng = np.random.default_rng(seed)
    w = int(2 * R * 1.5) + 6
    ys, xs = np.mgrid[0:w, 0:w].astype(float) + 0.5
    xs -= w / 2
    ys -= w / 2
    T = np.full(xs.shape, -np.inf)
    B = np.full(xs.shape, np.inf)
    cz = z0 + H * 0.5
    lumps = [(0.0, 0.0, cz, R * 0.8, H * 0.5)]
    for i in range(clumps):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.3, 0.62) * R
        zz = cz + rng.uniform(-0.3, 0.3) * H
        rr = rng.uniform(0.36, 0.5) * R
        lumps.append((math.cos(a) * r, math.sin(a) * r, zz, rr, rr * H / R * rng.uniform(0.85, 1.15)))
    for (lx, ly, lz, rr, hz) in lumps:
        d2 = ((xs - lx) ** 2 + (ys - ly) ** 2) / (rr * rr)
        inside = d2 < 1
        k = np.sqrt(np.clip(1 - d2, 0, 1))
        T = np.where(inside, np.maximum(T, lz + hz * k * flat_top), T)
        B = np.where(inside, np.minimum(B, lz - hz * 0.75 * k), B)
    # leafy roughness
    nz = value_noise(w, w, 5, seed, 3)
    nf = value_noise(w, w, 2, seed + 1, 2)
    ok = np.isfinite(T)
    T = np.where(ok, T + (nz - 0.5) * 6 + (nf - 0.5) * 3, T)
    # ragged silhouette: drop a few edge cells
    edge = ok & (np.hypot(xs, ys) > R * 0.55) & (nf < 0.3) & (T - B < H * 0.35)
    T = np.where(edge, -np.inf, T)
    zr = (float(np.min(B[ok])), float(np.max(T[np.isfinite(T)])))
    cv.heightfield(x - w / 2, y - w / 2, T, leaf_fn(kind, seed, blossom, zr=zr), zmin=float(np.min(B[ok])) - 2,
                   step=0.5, bottom=np.where(np.isfinite(B), B, np.inf))


def tree(cv, x, y, kind="oak", s=1.0, seed=0, blossom=None, z=0.0):
    """Deciduous tree: trunk with a couple of branches and a leafy crown. 8-12 m tall at s=1."""
    birch = kind == "birch"
    th = (32 if not birch else 38) * s
    tr = (2.6 if not birch else 1.8) * s
    cv.cylinder(x, y, tr, z, z + th + 8 * s, trunk_fn("6a4a30" if not birch else "e8e4dc", birch))
    R = {"oak": 32, "lime": 30, "maple": 28, "birch": 20, "fruit": 22}.get(kind, 26) * s
    H = {"birch": 50, "fruit": 30}.get(kind, 42) * s
    crown(cv, x, y, z + th - 6 * s, R, H, kind, seed, 8 if not birch else 6, blossom)


def poplar(cv, x, y, s=1.0, seed=0, z=0.0):
    cv.cylinder(x, y, 2.0 * s, z, z + 24 * s, trunk_fn())
    crown(cv, x, y, z + 18 * s, 13 * s, 100 * s, "lime", seed, 5)


def conifer(cv, x, y, kind="spruce", s=1.0, seed=0, z=0.0):
    """Spruce: a narrow jagged cone of drooping branch tiers."""
    rng = np.random.default_rng(seed)
    h = rng.uniform(95, 120) * s
    r = rng.uniform(19, 24) * s
    cv.cylinder(x, y, 2.2 * s, z, z + 14 * s, trunk_fn("5a3e28"))
    w = int(2 * r + 8)
    ys, xs = np.mgrid[0:w, 0:w] + 0.5
    d = np.hypot(xs - w / 2, ys - w / 2)
    ang = np.arctan2(ys - w / 2, xs - w / 2)
    base = z + 8 * s
    tiers = 8
    H = np.full(d.shape, -np.inf)
    for t in range(tiers):
        f = t / tiers
        ph = rng.uniform(0, 6.28)
        jag = 1.0 + 0.22 * np.sin(ang * 7 + ph) + 0.12 * np.sin(ang * 13 + ph * 2)
        rt = (r * (1 - f) ** 0.9 + 2.5) * jag
        top = base + h * (f + 1.1 / tiers)
        inside = d < rt
        hh = top - (d / np.maximum(rt, 1)) ** 0.8 * h / tiers * 1.9
        H = np.where(inside, np.maximum(H, hh), H)
    H = np.minimum(H, base + h)
    nz = value_noise(w, w, 2, seed, 2)
    H = np.where(np.isfinite(H), H + (nz - 0.5) * 3, H)
    cv.heightfield(x - w / 2, y - w / 2, H, leaf_fn(kind, seed), zmin=base - 4, thick=14.0)


def pine(cv, x, y, s=1.0, seed=0, z=0.0):
    """Scots pine: tall bare trunk with a flat, airy crown."""
    cv.cylinder(x, y, 2.4 * s, z, z + 76 * s, trunk_fn("9a5a38"))
    crown(cv, x, y, z + 66 * s, 22 * s, 26 * s, "pine", seed, 6, flat_top=0.7)


def bush(cv, x, y, s=1.0, seed=0, flowers=None, kind="hedge"):
    crown(cv, x, y, 0, 10 * s, 13 * s, kind, seed, 4, flowers)


def hedge(cv, x0, y0, x1, y1, h=12, seed=0):
    pal = np.array([C(c) for c in LEAF["hedge"]])

    def leaf(u, v, *_):
        hh = hash2(np.floor(u / 2), np.floor(v / 2), seed)
        rgb = pal[(np.clip(0.3 + hh * 0.6 + v / 60, 0, 0.99) * 4).astype(int)]
        return rgb, nores(u.shape), None

    def top(u, v, *_):
        hh = hash2(np.floor(u / 2), np.floor(v / 2), seed + 1)
        return pal[(np.clip(0.55 + hh * 0.45, 0, 0.99) * 4).astype(int)], nores(u.shape), None
    cv.box(x0, y0, 0, x1, y1, h, leaf, leaf, top)


def flowerbed(cv, x0, y0, x1, y1, seed=0, border="b8a890", h=2.5):
    cols = np.array([C("e04a5a"), C("f2c440"), C("f6f0f0"), C("b45ad8"), C("f08a3a"), C("ea7aa8")])

    def fn(u, v, L, D):
        shape = u.shape
        rgb = np.broadcast_to(C("6a4a30"), shape + (3,)).copy()
        leafm = hash2(np.floor(u / 1.6), np.floor(v / 1.6), seed) < 0.85
        rgb[leafm] = C("4f8f36") * (0.75 + 0.3 * hash2(np.floor(u), np.floor(v), seed + 1))[leafm][..., None]
        # each bed is planted with two kinds of flowers, in drifts
        fl = hash2(np.floor(u / 2.2), np.floor(v / 2.2), seed + 2) < 0.3
        two = cols[[seed % len(cols), (seed * 7 + 3) % len(cols)]]
        pick = (hash2(np.floor(u / 14), np.floor(v / 14), seed + 3) < 0.5).astype(int)
        shade = (0.85 + 0.2 * hash2(np.floor(u / 2.2), np.floor(v / 2.2), seed + 4))[..., None]
        rgb[fl] = (two[pick] * shade)[fl]
        edge = (u < 1.5) | (v < 1.5) | (u > L - 1.5) | (v > D - 1.5)
        rgb[edge] = C(border)
        return rgb, nores(shape), None
    side = flat(border, 6)
    cv.box(x0, y0, 0, x1, y1, h, side, side, fn)


def fence(cv, x0, y0, x1, y1, col="f4f0e8", h=10, kind="picket"):
    """Garden fence along a straight line (x0==x1 or y0==y1)."""
    c = C(col)

    def fn(u, v, L, H):
        shape = u.shape
        rgb = np.broadcast_to(c, shape + (3,)).copy()
        rgb *= (0.9 + 0.12 * hash2(np.floor(u / 3), 0, 1))[..., None]
        return rgb, nores(shape), None
    if kind == "picket":
        ext = lambda a, z: ((a % 3.0) < 1.8) | ((z > 3) & (z < 4.5)) | ((z > h - 3.5) & (z < h - 2))
    elif kind == "metal":
        ext = lambda a, z: ((a % 2.5) < 0.6) | (z > h - 1.2) | (z < 1.0) | ((a % 25) < 1.2)
    else:  # wooden boards
        ext = lambda a, z: (a % 4.0) < 3.6
    if y0 == y1:
        cv.face_y(y0, x0, x1, 0, h, fn, extra=lambda wx, wz: ext(wx, wz))
    else:
        cv.face_x(x0, y0, y1, 0, h, fn, extra=lambda wy, wz: ext(wy, wz))


def lamp_post(cv, x, y, h=45, style="classic", name="light"):
    pole = C("2e3036") if style != "classic" else C("2a2c34")
    cv.cylinder(x, y, 1.2, 0, h, lambda a, v, nx, ny: solid_res(pole, a.shape))
    cv.cylinder(x, y, 2.2, 0, 4, lambda a, v, nx, ny: solid_res(pole * 0.9, a.shape))
    if style == "classic":
        cv.box(x - 3, y - 3, h - 2, x + 3, y + 3, h + 6,
               lambda u, v, L, H: glow_res("ffe8b0", u.shape), lambda u, v, L, H: glow_res("f8dca0", u.shape),
               lambda u, v, L, D: solid_res(pole, u.shape))
        cv.box(x - 3.6, y - 3.6, h + 6, x + 3.6, y + 3.6, h + 7.5, flat(pole), flat(pole), flat(pole))
        cv.mark(name, x, y, h + 2)
    elif style == "lantern":
        # wrought-iron post with a scrolled cross-arm, two hanging lanterns and a ball on top
        cv.cylinder(x, y, 1.8, 4, 10, lambda a, v, nx, ny: solid_res(pole * 1.1, a.shape))
        cv.box(x - 9, y - 0.8, h - 1, x + 9, y + 0.8, h + 0.8, flat(pole), flat(pole), flat(pole))
        for lx in (x - 8, x + 8):
            cv.box(lx - 0.4, y - 0.4, h - 4, lx + 0.4, y + 0.4, h - 1, flat(pole), flat(pole), flat(pole))
            cv.box(lx - 2.6, y - 2.6, h - 11, lx + 2.6, y + 2.6, h - 4,
                   lambda u, v, L, H: glow_res("ffd890", u.shape), lambda u, v, L, H: glow_res("f8c878", u.shape),
                   lambda u, v, L, D: solid_res(pole, u.shape))
            cv.box(lx - 3.2, y - 3.2, h - 4, lx + 3.2, y + 3.2, h - 2.8, flat(pole), flat(pole), flat(pole))
            cv.box(lx - 1.4, y - 1.4, h - 12.5, lx + 1.4, y + 1.4, h - 11, flat(pole), flat(pole), flat(pole))
        cv.ellipsoid(x, y, h + 3, 2, 2, 2, lambda wx, wy, wz, nx, ny, nz: solid_res(C("c8a040"), wx.shape))
        cv.mark(name, x, y, h - 7)
    else:
        cv.box(x - 1, y - 1, h - 1, x + 12, y + 1, h + 1, flat(pole), flat(pole), flat(pole))
        cv.box(x + 6, y - 2, h - 2.5, x + 13, y + 2, h - 1, lambda u, v, L, H: glow_res("f4f0e0", u.shape),
               lambda u, v, L, H: glow_res("f4f0e0", u.shape), flat(pole))
        cv.mark(name, x + 9, y, h - 2)


def bench(cv, x, y, axis="x", col="9a6a40"):
    w, d = 16, 5
    leg = flat("3a3a40")
    seat = flat(col, 8)
    if axis == "x":
        for lx in (x + 1, x + w - 2):
            cv.box(lx, y, 0, lx + 1, y + d, 4.5, leg, leg, leg)
        cv.box(x, y, 4.5, x + w, y + d, 5.5, seat, seat, seat)
        cv.box(x, y, 5.5, x + w, y + 1, 9.5, seat, seat, seat)
    else:
        for ly in (y + 1, y + w - 2):
            cv.box(x, ly, 0, x + d, ly + 1, 4.5, leg, leg, leg)
        cv.box(x, y, 4.5, x + d, y + w, 5.5, seat, seat, seat)
        cv.box(x, y, 5.5, x + 1, y + w, 9.5, seat, seat, seat)


def bin_(cv, x, y, col="4a6a4a"):
    cv.cylinder(x, y, 2.4, 0, 9, lambda a, v, nx, ny: solid_res(C(col), a.shape),
                lambda a, b: solid_res(C(col) * 0.8, a.shape))


def wheelie_bins(cv, x, y, cols=("3a5a8a", "4a7a3a")):
    for i, c in enumerate(cols):
        f = flat(c, 4)
        cv.box(x + i * 7, y, 0, x + i * 7 + 6, y + 7, 11, f, f, flat(C(c) * 0.8))


def mailbox(cv, x, y, col="3a6ad0"):
    p = flat("3a3a40")
    cv.box(x, y, 0, x + 1, y + 1, 10, p, p, p)
    cv.box(x - 2, y - 3, 10, x + 3, y + 4, 14, flat(col), flat(col), flat(C(col) * 1.1))


def umbrella_table(cv, x, y, col="e85a4a"):
    wood = flat("8a6a48", 6)
    cv.cylinder(x, y, 5, 6.5, 7.5, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape), lambda a, b: solid_res(C("f0ece4"), a.shape))
    cv.cylinder(x, y, 0.7, 0, 22, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape))
    w = 34
    ys, xs = np.mgrid[0:w, 0:w] + 0.5
    d = np.hypot(xs - w / 2, ys - w / 2)
    H = np.where(d < 15, 25 - d * 0.32, -np.inf)
    ang = np.arctan2(ys - w / 2, xs - w / 2)
    stripes = (np.floor((ang + math.pi) / (math.pi / 4)) % 2) == 0
    cv.heightfield(x - w / 2, y - w / 2, H, lambda wx, wy, wz, nx, ny, nz: (
        np.where(stripes[np.clip((wy - (y - w / 2)).astype(int), 0, w - 1), np.clip((wx - (x - w / 2)).astype(int), 0, w - 1)][..., None],
                 C(col), C("f6f2ea")), nores(wx.shape), None), zmin=19, thick=2.0)
    for (dx, dy) in ((-8, 0), (8, 0), (0, 8)):
        cv.box(x + dx - 2, y + dy - 2, 0, x + dx + 2, y + dy + 2, 4.5, wood, wood, wood)


def ac_unit(cv, x, y, z, w=8, d=6, h=6):
    side = lambda u, v, L, H: (np.broadcast_to(C("c8ccd0"), u.shape + (3,)) * (1 - 0.18 * ((np.floor(u) % 2) == 0))[..., None],
                               nores(u.shape), None)
    cv.box(x, y, z, x + w, y + d, z + h, side, side, flat("d8dce0"))


def solar(cv, x0, y0, x1, y1, z, tilt=6):
    def fn(u, v, L, D):
        shape = u.shape
        rgb = np.broadcast_to(C("2a3a6a"), shape + (3,)).copy()
        grid = ((u % 9) < 0.8) | ((v % 6) < 0.8)
        rgb[grid] = C("a8b0c0")
        rgb[(((u + v) % 15) < 2)] *= 1.5
        return rgb, nores(shape), None
    k = tilt / max(1, (y1 - y0))
    cv.plane(z + tilt + k * y0, 0, -k, (x0, y0, z, x1, y1, z + tilt),
             lambda wx, wy: (wx >= x0) & (wx < x1) & (wy >= y0) & (wy < y1),
             lambda wx, wy, wz: fn(wx - x0, wy - y0, x1 - x0, y1 - y0))


def water_tank(cv, x, y, z, r=7, h=14):
    m = lambda a, v, nx, ny: (C("a8acb0") * (0.92 + 0.08 * ((np.floor(v) % 4) == 0))[..., None], nores(a.shape), None)
    for (dx, dy) in ((-r * 0.6, -r * 0.6), (r * 0.6, -r * 0.6), (-r * 0.6, r * 0.6), (r * 0.6, r * 0.6)):
        cv.box(x + dx - 0.6, y + dy - 0.6, z, x + dx + 0.6, y + dy + 0.6, z + 6, flat("4a4a50"), flat("4a4a50"), flat("4a4a50"))
    cv.cylinder(x, y, r, z + 6, z + 6 + h, m, lambda a, b: solid_res(C("989ca0"), a.shape))


def chimney(cv, x, y, z, h=16, col="9a5a44", name=None):
    from arch import facade
    w = facade("brick", col, plinth=None)
    cv.box(x, y, z, x + 7, y + 7, z + h, w, w, flat("2a2424"))
    cv.box(x - 1, y - 1, z + h - 2, x + 8, y + 8, z + h, flat(col), flat(col), flat("3a3030"))
    if name:
        cv.mark(name, x + 3.5, y + 3.5, z + h)


def antenna(cv, x, y, z):
    p = flat("5a5a60")
    cv.box(x, y, z, x + 0.8, y + 0.8, z + 16, p, p, p)
    cv.box(x - 5, y, z + 12, x + 6, y + 0.8, z + 12.8, p, p, p)
    cv.box(x - 3, y, z + 15, x + 4, y + 0.8, z + 15.8, p, p, p)


def dish(cv, x, y, z):
    cv.ellipsoid(x, y, z + 3, 3.5, 1.2, 3.5, lambda wx, wy, wz, nx, ny, nz: solid_res(C("e4e4e8"), wx.shape))


def swing(cv, x, y):
    p = flat("c84a3a")
    for dx in (0, 22):
        cv.box(x + dx, y, 0, x + dx + 1.2, y + 1.2, 20, p, p, p)
    cv.box(x, y, 20, x + 23, y + 1.2, 21.2, p, p, p)
    for sx in (6, 15):
        cv.box(x + sx, y, 7, x + sx + 0.4, y + 0.4, 20, flat("3a3a40"), flat("3a3a40"), flat("3a3a40"))
        cv.box(x + sx - 2, y - 1.5, 6, x + sx + 2.4, y + 1.9, 7, flat("3a5aa0"), flat("3a5aa0"), flat("3a5aa0"))


def laundry(cv, x, y, length=26):
    p = flat("8a8a90")
    cv.box(x, y, 0, x + 0.8, y + 0.8, 17, p, p, p)
    cv.box(x + length, y, 0, x + length + 0.8, y + 0.8, 17, p, p, p)
    cols = ["e8e4dc", "6a8ad8", "e86a6a", "f0d070", "f4f4f4"]
    for i in range(5):
        cx = x + 3 + i * (length - 4) / 5
        c = cols[i % len(cols)]
        cv.face_y(y + 0.5, cx, cx + 4, 9, 16, lambda u, v, L, H, c=c: solid_res(C(c), u.shape))


def pool(cv, x0, y0, x1, y1):
    rim = flat("e8e4dc", 3)

    def water(u, v, L, D):
        w = np.sin(u * 0.31 + np.sin(v * 0.23) * 2.0) + np.sin(v * 0.27 - np.sin(u * 0.19) * 2.0)
        t = np.clip((w + 2) / 4, 0, 1)
        rgb = C("3aa8d8") * (1 - t[..., None]) + C("6ac4e8") * t[..., None]
        rgb[np.abs(w - 1.3) < 0.08] = C("c8ecf8")
        rgb[(u < 3) | (v < 3)] = C("2e8ab8")
        return rgb, nores(u.shape), None
    with cv.ground:
        cv.box(x0, y0, 0, x1, y1, 1.0, rim, rim, rim)
        cv.top(1.1, x0 + 3, y0 + 3, x1 - 3, y1 - 3, water)


def parked_bike(cv, x, y):
    f = flat("2a5aa0")
    cv.box(x, y, 3, x + 14, y + 0.6, 5, f, f, f)
    for wx in (x + 2, x + 12):
        cv.face_y(y + 0.6, wx - 3, wx + 3, 0, 6, lambda u, v, L, H: solid_res(C("202024"), u.shape),
                  extra=lambda a, z, wx=wx: np.abs(np.hypot(a - wx, z - 3) - 2.6) < 0.7)


# ====================================================================== ground surfaces (drawn with cv.ground)
def paving(col="c4bcae", tile=8.0, seed=2, joint=0.8):
    base = C(col)

    def fn(u, v, *_):
        shape = u.shape
        rgb = np.broadcast_to(base, shape + (3,)).copy()
        rgb *= (0.93 + 0.1 * hash2(np.floor(u / tile), np.floor(v / tile), seed))[..., None]
        rgb += ((hash2(np.floor(u), np.floor(v), seed + 1) - 0.5) * 6)[..., None]
        j = ((u % tile) < joint) | ((v % tile) < joint)
        rgb[j] *= 0.82
        return rgb, nores(shape), None
    return fn


def bricks_pave(col="b07a5a", seed=3):
    base = C(col)

    def fn(u, v, *_):
        shape = u.shape
        rgb = np.broadcast_to(base, shape + (3,)).copy()
        row = np.floor(v / 3)
        off = (row % 2) * 3
        rgb *= (0.88 + 0.18 * hash2(np.floor((u + off) / 6), row, seed))[..., None]
        j = ((v % 3) < 0.5) | (((u + off) % 6) < 0.5)
        rgb[j] *= 0.75
        return rgb, nores(shape), None
    return fn


def asphalt_lot(col="54565c", seed=4, lines=None):
    base = C(col)

    def fn(u, v, L, D):
        shape = u.shape
        rgb = np.broadcast_to(base, shape + (3,)).copy()
        rgb += ((hash2(np.floor(u), np.floor(v), seed) - 0.5) * 10)[..., None]
        if lines is not None:
            axis, start, step, l0, l1 = lines
            a = u if axis == "u" else v
            b = v if axis == "u" else u
            m = (((a - start) % step) < 1.0) & (b > l0) & (b < l1) & (a > start - 1)
            rgb[m] = C("e8e8e0")
        return rgb, nores(shape), None
    return fn


def gravel(col="a89a84", seed=5):
    base = C(col)

    def fn(u, v, *_):
        shape = u.shape
        rgb = np.broadcast_to(base, shape + (3,)).copy()
        rgb += ((hash2(np.floor(u), np.floor(v), seed) - 0.5) * 30)[..., None]
        return rgb, nores(shape), None
    return fn


def lawn_stripes(seed=6):
    """Mown lawn: subtle stripes, mostly transparent-looking because it is close to the valley grass."""
    def fn(u, v, *_):
        shape = u.shape
        g = C("5f9a40")
        rgb = np.broadcast_to(g, shape + (3,)).copy()
        rgb *= (0.94 + 0.1 * ((np.floor(u / 12) % 2) == 0))[..., None]
        rgb += ((hash2(np.floor(u), np.floor(v), seed) - 0.5) * 14)[..., None]
        return rgb, nores(shape), None
    return fn


def soil_rows(axis="u", col="6e5236", crop="5a9a3a", step=10.0, seed=7, crop_w=0.5):
    def fn(u, v, *_):
        shape = u.shape
        a = u if axis == "u" else v
        rgb = np.broadcast_to(C(col), shape + (3,)).copy()
        rgb += ((hash2(np.floor(u), np.floor(v), seed) - 0.5) * 18)[..., None]
        row = ((a % step) / step)
        cm = np.abs(row - 0.5) < crop_w / 2
        cc = C(crop) * (0.85 + 0.3 * hash2(np.floor(u / 2), np.floor(v / 2), seed + 1))[..., None]
        rgb[cm] = cc[cm]
        return rgb, nores(shape), None
    return fn
