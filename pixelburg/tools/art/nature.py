"""Trees, forest clumps, mountains, rocks, clouds and ground / road tiles."""
import math
import os

import numpy as np
from PIL import Image

from raster import C, Canvas, flat, hash2, value_noise, shade_n, U
from props import tree, bush, nores, solid_res, GRASS, grass_fn

TW, TH = 128, 64


def crop_save(cv, path, anchor_world=None):
    img = cv.image()
    bbox = img.getbbox()
    ax, ay = cv.screen(*(anchor_world or (cv.size / 2, cv.size / 2, 0)))
    img.crop(bbox).save(path)
    return [round(ax - bbox[0]), round(ay - bbox[1])]


# ====================================================================== trees
def gen_trees(out):
    meta = {}
    kinds = [("oak", 1.1), ("oak", 0.9), ("pine", 1.2), ("pine", 1.0), ("birch", 1.0), ("sakura", 1.0),
             ("autumn", 1.0), ("autumn", 0.85)]
    for i, (k, s) in enumerate(kinds):
        cv = Canvas(1, 110)
        tree(cv, 32, 32, s, k, 300 + i)
        meta["tree_%d" % i] = crop_save(cv, os.path.join(out, "tree_%d.png" % i), (32, 32, 0))
    cv = Canvas(1, 30)
    bush(cv, 32, 32, 1.3, 320, "e86a8a")
    meta["bush"] = crop_save(cv, os.path.join(out, "bush.png"), (32, 32, 0))
    for i in range(2):
        cv = Canvas(1, 30)
        w = 30
        ys, xs = np.mgrid[0:w, 0:w] + 0.5
        n = value_noise(w, w, 6, 330 + i, 3)
        d = np.hypot(xs - 15, (ys - 15) * 1.2)
        H = np.where(d < 12, np.sqrt(np.clip(144 - d * d, 0, None)) * 0.55 + n * 3, -np.inf)
        rock = lambda wx, wy, wz, nx, ny, nz: (np.broadcast_to(C("8a8a90"), wx.shape + (3,)) *
                                               (0.9 + 0.2 * hash2(np.floor(wx / 3), np.floor(wy / 3), 3))[..., None] +
                                               np.where((nz > 0.85)[..., None], np.array([10, 30, 0]), 0), nores(wx.shape), None)
        cv.heightfield(17, 17, H, rock)
        meta["rock_%d" % i] = crop_save(cv, os.path.join(out, "rock_%d.png" % i), (32, 32, 0))
    # forest clumps (several trees per tile): conifer-heavy, mixed and leafy groves
    rng = np.random.default_rng(7)
    for i in range(16):
        cv = Canvas(1, 130)
        spots = [(14, 16), (44, 18), (20, 46), (48, 46), (32, 32), (30, 10), (10, 34)]
        rng.shuffle(spots)
        mix = i % 4
        chosen = sorted(spots[:3 + i % 3], key=lambda p: p[0] + p[1])
        for j, (x, y) in enumerate(chosen):
            r = rng.random()
            if mix == 0:
                k = "pine" if r < 0.85 else "birch"
            elif mix == 1:
                k = "pine" if r < 0.5 else ("oak" if r < 0.85 else "birch")
            elif mix == 2:
                k = "oak" if r < 0.6 else ("birch" if r < 0.85 else "pine")
            else:
                k = "pine" if r < 0.6 else "autumn" if r < 0.7 else "oak"
            tree(cv, x + rng.uniform(-3, 3), y + rng.uniform(-3, 3), rng.uniform(0.7, 1.2), k, 400 + i * 10 + j)
        for j in range(2):
            bush(cv, rng.uniform(6, 58), rng.uniform(6, 58), rng.uniform(0.5, 0.8), 470 + i * 3 + j,
                 "e86a8a" if rng.random() < 0.2 else None)
        meta["forest_%d" % i] = crop_save(cv, os.path.join(out, "forest_%d.png" % i), (32, 32, 0))
    meta.update(gen_undergrowth(out))
    return meta


def gen_undergrowth(out):
    """Small forest-floor props: ferns, mushrooms, stumps, logs, berry bushes, mossy boulders."""
    meta = {}
    rng = np.random.default_rng(77)

    def save(name, cv):
        meta[name] = crop_save(cv, os.path.join(out, name + ".png"), (32, 32, 0))

    fern = ["1e4a24", "2a6a30", "3a8a3a", "5aa848"]
    for i in range(3):
        cv = Canvas(1, 20)
        for j in range(5 + i):
            a = j * math.tau / (5 + i) + rng.uniform(-0.3, 0.3)
            cv.ellipsoid(32 + math.cos(a) * 5, 32 + math.sin(a) * 5, 3, 6, 2.2, 1.6,
                         lambda wx, wy, wz, nx, ny, nz, s=j: (np.stack([C(c) for c in fern])[
                             np.clip(((nz + (hash2(np.floor(wx), np.floor(wy), s) - 0.5)) * 2).astype(int) + 1, 0, 3)],
                             np.ones(wx.shape, bool), None))
        save("fern_%d" % i, cv)
    # mushrooms
    cv = Canvas(1, 16)
    for (x, y, r, col) in ((30, 32, 3.2, "d83a2a"), (35, 30, 2.4, "d83a2a"), (33, 36, 2.0, "e8c080")):
        cv.cylinder(x, y, r * 0.35, 0, r * 1.3, lambda a, v, nx, ny: solid_res(C("f4ece0"), a.shape))
        cv.ellipsoid(x, y, r * 1.3, r, r, r * 0.6, lambda wx, wy, wz, nx, ny, nz, col=col: (
            np.where((hash2(np.floor(wx), np.floor(wy), 3) > 0.75)[..., None], C("f8f4ec"), C(col)) * np.ones(wx.shape + (3,)),
            nores(wx.shape), None), cut_z=r * 1.3)
    save("mushrooms", cv)
    # stump
    cv = Canvas(1, 20)
    cv.cylinder(32, 32, 6, 0, 7, lambda a, v, nx, ny: (np.broadcast_to(C("6a4426"), a.shape + (3,)) *
                (0.85 + 0.2 * (np.floor(a * 4) % 2))[..., None], nores(a.shape), None),
                lambda a, b: (np.where(((np.hypot(a, b) % 2) < 1)[..., None], C("c8a070"), C("b08a58")) * np.ones(a.shape + (3,)),
                              nores(a.shape), None))
    save("stump", cv)
    # fallen log with moss
    cv = Canvas(1, 16)
    cv.box(18, 28, 0, 48, 35, 7, lambda u, v, L, H: (np.where((v > H - 2)[..., None], C("5a8a3a"), C("6a4426")) * np.ones(u.shape + (3,)), nores(u.shape), None),
           lambda u, v, L, H: (np.where(((np.hypot(u - L / 2, v - H / 2) % 2) < 1)[..., None], C("c8a070"), C("a8804a")) * np.ones(u.shape + (3,)), nores(u.shape), None),
           lambda u, v, L, D: (np.where((hash2(np.floor(u), np.floor(v), 4) > 0.5)[..., None], C("5a8a3a"), C("4a7a2a")) * np.ones(u.shape + (3,)), nores(u.shape), None))
    save("log", cv)
    # berry bush
    cv = Canvas(1, 24)
    bush(cv, 32, 32, 1.0, 81, "3a4ac8")
    save("berries", cv)
    # mossy boulders (wide and low)
    for i in range(2):
        cv = Canvas(1, 24)
        w = 40
        ys, xs = np.mgrid[0:w, 0:w] + 0.5
        n = value_noise(w, w, 8, 90 + i, 3)
        d = np.hypot((xs - 20) / 1.0, (ys - 20) * 1.4)
        H = np.where(d < 15, (np.clip(225 - d * d, 0, None) ** 0.5) * 0.42 + n * 3, -np.inf)
        rock = lambda wx, wy, wz, nx, ny, nz: (np.where((nz > 0.82)[..., None], np.array([92, 128, 70.0]),
                                                        np.array([128, 124, 118.0]) * (0.85 + 0.25 * hash2(np.floor(wx / 3), np.floor(wy / 3), 3))[..., None]),
                                               nores(wx.shape), None)
        cv.heightfield(12, 12, H, rock)
        save("boulder_%d" % i, cv)
    return meta


# ====================================================================== mountains
def mountain(seed, n=4, peak=230, snow=True):
    size = n * U
    cv = Canvas(n, peak + 10)
    w = size
    ys, xs = np.mgrid[0:w, 0:w] + 0.5
    rng = np.random.default_rng(seed)
    base = np.zeros((w, w))
    for k in range(3):
        cx = w * 0.5 + rng.uniform(-0.22, 0.22) * w
        cy = w * 0.5 + rng.uniform(-0.22, 0.22) * w
        r = w * (0.5 if k == 0 else rng.uniform(0.28, 0.38))
        hk = 1.0 if k == 0 else rng.uniform(0.55, 0.8)
        d = np.hypot(xs - cx, ys - cy) / r
        base = np.maximum(base, hk * np.clip(1 - d, 0, 1) ** 1.25)
    edge = np.clip((0.5 * w - np.hypot(xs - w / 2, ys - w / 2)) / (0.08 * w), 0, 1)
    base *= edge
    n1 = value_noise(w, w, 40, seed, 5)
    ridge = 1 - np.abs(value_noise(w, w, 22, seed + 1, 4) * 2 - 1)
    H = base * (0.7 + 0.3 * n1) * (0.72 + 0.28 * ridge) * peak
    H = np.where(base > 0.002, H, -np.inf)
    hn = H / peak
    tex = value_noise(w, w, 6, seed + 2, 2)

    def col(wx, wy, wz, nx, ny, nz):
        rel = wz / peak
        jitter = (hash2(np.floor(wx / 2), np.floor(wy / 2), seed) - 0.5) * 0.08
        r = rel + jitter
        grass = np.array([84, 140, 64.0])
        forest = np.array([40, 84, 48.0])
        rock = np.array([120, 112, 104.0])
        rock2 = np.array([92, 86, 84.0])
        snowc = np.array([238, 242, 248.0])
        rgb = np.where((r < 0.12)[..., None], grass, forest)
        rgb = np.where((r >= 0.3)[..., None], np.where((hash2(np.floor(wx / 4), np.floor(wy / 4), seed + 3) > 0.5)[..., None], rock, rock2), rgb)
        steep = nz < 0.6
        rgb = np.where((steep & (r > 0.12))[..., None], rock2, rgb)
        if snow:
            sn = (r > 0.62) & (nz > 0.45) | (r > 0.8)
            rgb = np.where(sn[..., None], snowc, rgb)
        # little pines on the forest belt
        pines = (r > 0.1) & (r < 0.3) & (hash2(np.floor(wx / 3), np.floor(wy / 3), seed + 4) > 0.7)
        rgb = np.where(pines[..., None], np.array([26, 60, 34.0]), rgb)
        return rgb, nores(wx.shape), None
    cv.heightfield(0, 0, H, col, zmin=-2, step=1.0, floor=-0.5)
    return cv


def gen_mountains(out):
    meta = {}
    for i in range(5):
        cv = mountain(500 + i, 4 if i < 3 else 3, [240, 210, 260, 170, 150][i], True)
        meta["mountain_%d" % i] = {"anchor": crop_save(cv, os.path.join(out, "mountain_%d.png" % i), (cv.size / 2, cv.size / 2, 0)),
                                   "size": cv.n}
    return meta


# ====================================================================== clouds
def _blur(a, r):
    k = np.ones(2 * r + 1) / (2 * r + 1)
    a = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, a)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 1, a)


def cloud_image(seed, w, h, storm=False):
    """Cauliflower cumulus: many sphere puffs lit from the top-left, flat shaded base, 5 tones."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    lum = np.full((h, w), -1.0)
    zbuf = np.full((h, w), -1e9)
    base_y = h * 0.8
    L = np.array([-0.45, -0.6, 0.66])
    L /= np.linalg.norm(L)
    puffs = []
    n = 26 if not storm else 90
    for i in range(n):
        t = rng.uniform(0.04, 0.96)
        bump = math.sin(t * math.pi) ** (0.8 if not storm else 0.35)
        if storm:
            r = h * (0.07 + 0.11 * bump * rng.uniform(0.5, 1.0))
        else:
            r = h * (0.1 + 0.2 * bump * rng.uniform(0.6, 1.0))
        cx = w * t
        top = base_y - h * ((0.12 + 0.62 * bump) if not storm else (0.1 + 0.55 * bump)) * rng.uniform(0.7, 1.0)
        cy = rng.uniform(top + r * 0.4, base_y - r * 0.2)
        puffs.append((cy + r * 0.3, cx, cy, r))
    for _, cx, cy, r in sorted(puffs):            # higher puffs first, lower puffs drawn in front
        dx, dy = (xs - cx) / r, (ys - cy) / r
        d2 = dx * dx + dy * dy
        m = d2 < 1
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        shade = dx * L[0] + dy * L[1] + nz * L[2]
        z = cy + nz * r                           # nearer = lower on screen
        upd = m & (z > zbuf - r * 0.6)
        k = 1.0 if not storm else 0.45
        glob = 1.2 - ys / base_y * 1.3
        lum[upd] = (shade[upd] * k + glob[upd] * (1 - k)) - (cy / base_y) * (0.35 if not storm else 0.15)
        zbuf[upd] = np.maximum(zbuf[upd], z[upd])
    lum[ys > base_y] = -1
    flat_base = (ys > base_y - 5) & (lum > -1)
    lum[flat_base] -= 0.35
    mask = lum > -1
    if storm:
        pal = np.array([[58, 62, 80], [78, 82, 102], [100, 104, 126], [128, 132, 152], [160, 164, 184]], float)
    else:
        pal = np.array([[164, 178, 208], [192, 204, 228], [218, 226, 242], [240, 244, 252], [255, 255, 255]], float)
    q = np.clip(((lum + 0.35) / 1.25) * 5 + (hash2(xs.astype(int) // 2, ys.astype(int) // 2, seed) - 0.5) * 0.28, 0, 4.99)
    rgb = pal[q.astype(int)]
    alpha = np.where(mask, 238 if not storm else 248, 0)
    out = np.dstack([rgb, alpha]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")
    # soft one-pixel rim so the edge is not jagged against the sky
    a_ = np.array(img)
    m = a_[..., 3] > 0
    pad = np.pad(m, 1)
    edge = ~m & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
    a_[edge] = np.append(pal[2], 110).astype(np.uint8)
    return Image.fromarray(a_)


def gen_clouds(out):
    sizes = [(300, 150), (380, 180), (260, 130), (420, 200)]
    for i, (w, h) in enumerate(sizes):
        img = cloud_image(600 + i, w, h)
        img = img.crop(img.getbbox())
        img.save(os.path.join(out, "cloud_%d.png" % i))
        a = np.array(img)
        sh = np.zeros_like(a)
        sh[..., 3] = (a[..., 3] > 0) * 46
        Image.fromarray(sh).resize((img.width, max(1, img.height // 2))).save(os.path.join(out, "cloud_shadow_%d.png" % i))
    for i, (w, h) in enumerate([(460, 220), (520, 240)]):
        img = cloud_image(700 + i, w, h, storm=True)
        img = img.crop(img.getbbox())
        img.save(os.path.join(out, "storm_%d.png" % i))
        a = np.array(img)
        sh = np.zeros_like(a)
        sh[..., 3] = (a[..., 3] > 0) * 70
        Image.fromarray(sh).resize((img.width, max(1, img.height // 2))).save(os.path.join(out, "storm_shadow_%d.png" % i))


# ====================================================================== tiles
def tile_uv():
    ys, xs = np.mgrid[0:TH, 0:TW]
    px, py = xs + 0.5, ys + 0.5
    u = ((px - TW / 2) / (TW / 2) + py / (TH / 2)) / 2
    v = (py / (TH / 2) - (px - TW / 2) / (TW / 2)) / 2
    inside = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
    return u, v, inside


def to_img(rgb, inside):
    out = np.dstack([np.clip(rgb, 0, 255), inside * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA").copy()


def grass_tile(seed, flowers=0.0, locked=False):
    u, v, inside = tile_uv()
    rgb, _, _ = grass_fn(seed, flowers)(u * U, v * U)
    if locked:
        grey = rgb.mean(axis=2, keepdims=True)
        rgb = rgb * 0.7 + grey * 0.22
    return to_img(rgb, inside)


def zone_tile(zone, seed, locked=False, flowers=0.0):
    u, v, inside = tile_uv()
    if zone == "farm":
        h = hash2(np.floor(u * 32), np.floor(v * 32), seed)
        h2 = value_noise(TW, TH, 12, seed, 2)
        pal = np.stack([C("8aa84a"), C("98b452"), C("a8bc5c"), C("b8c068")])
        rgb = pal[np.clip((h * 0.6 + h2 * 0.7) * 3, 0, 3).astype(int)].copy()
        tuft = hash2(np.floor(u * 64), np.floor(v * 64), seed + 3) > 0.95
        rgb[tuft] = C("d8c878")
    elif zone == "industry":
        h = hash2(np.floor(u * 40), np.floor(v * 40), seed)
        n = value_noise(TW, TH, 10, seed, 3)
        rgb = np.broadcast_to(C("9a9488"), u.shape + (3,)) * (0.88 + 0.2 * n[..., None]) + ((h - 0.5) * 16)[..., None]
        gr = n < 0.3
        rgb[gr] = (np.stack(GRASS)[np.clip((h * 3).astype(int), 0, 2)] * 0.85)[gr]
        peb = hash2(np.floor(u * 64), np.floor(v * 64), seed + 2) > 0.95
        rgb[peb] = C("c8c0b4")
    elif zone == "leisure":
        rgb, _, _ = grass_fn(seed, 0.02 + flowers)(u * U, v * U)
        rgb = rgb * np.array([0.9, 1.06, 0.92])
        clover = hash2(np.floor(u * 21), np.floor(v * 21), seed + 5) > 0.9
        rgb[clover] = C("4a9a44")
    else:
        rgb, _, _ = grass_fn(seed, flowers)(u * U, v * U)
    if locked:
        grey = rgb.mean(axis=2, keepdims=True)
        rgb = rgb * 0.7 + grey * 0.24
    return to_img(rgb, inside)


def forest_floor(seed):
    u, v, inside = tile_uv()
    h = hash2(np.floor(u * 32), np.floor(v * 32), seed)
    h2 = value_noise(TW, TH, 10, seed, 2)
    pal = np.stack([C("2c4a24"), C("365a2a"), C("426a30"), C("5a5a2a")])
    idx = np.clip((h * 0.6 + h2 * 0.6) * 3.2, 0, 3).astype(int)
    rgb = pal[idx].copy()
    leaves = hash2(np.floor(u * 64), np.floor(v * 64), seed + 1) > 0.94
    rgb[leaves] = C("8a6a2a")
    return to_img(rgb, inside)


def rock_ground(seed):
    u, v, inside = tile_uv()
    n = value_noise(TW, TH, 12, seed, 3)
    h = hash2(np.floor(u * 32), np.floor(v * 32), seed)
    rgb = np.broadcast_to(C("7a7266"), u.shape + (3,)) * (0.85 + 0.25 * n[..., None]) + ((h - 0.5) * 12)[..., None]
    gr = n < 0.38
    rgb[gr] = (np.stack(GRASS)[np.clip((h * 3).astype(int), 0, 2)] * 0.8)[gr]
    pebble = hash2(np.floor(u * 64), np.floor(v * 64), seed + 2) > 0.97
    rgb[pebble] = C("b8b0a8")
    return to_img(rgb, inside)


def bits(mask):
    return {"ny": bool(mask & 1), "px": bool(mask & 2), "py": bool(mask & 4), "nx": bool(mask & 8)}


def road_tile(mask, kind):
    u, v, inside = tile_uv()
    b = bits(mask)
    ui, vi = np.floor(u * U), np.floor(v * U)
    conns = sum(b.values())
    if kind == "dirt":
        rgb = np.broadcast_to(C("9a7448"), u.shape + (3,)).copy()
        rgb += ((hash2(np.floor(u * 32), np.floor(v * 32), 4) - 0.5) * 18)[..., None]
        # tyre ruts
        if b["nx"] or b["px"]:
            rut = (np.abs(v - 0.35) < 0.025) | (np.abs(v - 0.65) < 0.025)
            rgb[rut] *= 0.82
        if b["ny"] or b["py"]:
            rut = (np.abs(u - 0.35) < 0.025) | (np.abs(u - 0.65) < 0.025)
            rgb[rut] *= 0.82
        edge = np.full(u.shape, 9.0)
        for k, val in (("nx", u), ("px", 1 - u), ("ny", v), ("py", 1 - v)):
            if not b[k]:
                edge = np.minimum(edge, val)
        corner = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v))
        jag = 0.16 + 0.05 * np.sin(u * 40 + v * 23) + 0.03 * np.sin(u * 91 - v * 57)
        g, _, _ = grass_fn(9)(u * U, v * U)
        gm = (edge < jag) | (corner < 0.06)
        rgb[gm] = g[gm]
        rgb[(edge >= jag) & (edge < jag + 0.02)] *= 0.85
        return to_img(rgb, inside)

    w = 0.17
    side = np.zeros(u.shape, bool)
    for k, cond in (("nx", u < w), ("px", u > 1 - w), ("ny", v < w), ("py", v > 1 - w)):
        if not b[k]:
            side |= cond
    side |= ((u < w) | (u > 1 - w)) & ((v < w) | (v > 1 - w))
    if kind == "highway":
        rgb = np.broadcast_to(C("4a4a54"), u.shape + (3,)).copy()
        rgb += ((hash2(np.floor(u * 64), np.floor(v * 64), 4) - 0.5) * 8)[..., None]
        for k, val in (("nx", u), ("px", 1 - u), ("ny", v), ("py", 1 - v)):
            if not b[k]:
                rgb[val < 0.05] = np.array([120, 112, 98.0])
                rgb[(val >= 0.05) & (val < 0.075)] = C("8a8a94")
                rgb[(val >= 0.1) & (val < 0.12)] = C("f0f0f0")
        if b["nx"] or b["px"]:
            dash = (np.abs(v - 0.5) < 0.014) & ((np.floor(u * U) % 16) < 9)
            if not (b["ny"] or b["py"]):
                dash = (np.abs(v - 0.485) < 0.009) | (np.abs(v - 0.515) < 0.009)
            rgb[dash] = C("f0c840")
        if b["ny"] or b["py"]:
            dash = (np.abs(u - 0.5) < 0.014) & ((np.floor(v * U) % 16) < 9)
            if not (b["nx"] or b["px"]):
                dash = (np.abs(u - 0.485) < 0.009) | (np.abs(u - 0.515) < 0.009)
            rgb[dash] = C("f0c840")
        return to_img(rgb, inside)
    if kind == "asphalt":
        rgb = np.broadcast_to(C("56565e"), u.shape + (3,)).copy()
        rgb += ((hash2(np.floor(u * 64), np.floor(v * 64), 4) - 0.5) * 9)[..., None]
        slab = np.broadcast_to(C("c4bcae"), u.shape + (3,)).copy()
        slab[((ui % 8) == 0) | ((vi % 8) == 0)] *= 0.88
    else:
        rgb = np.broadcast_to(C("8a7e70"), u.shape + (3,)).copy()
        bu = np.floor((u * U + (np.floor(v * U / 5) % 2) * 3) / 6)
        bv = np.floor(v * U / 5)
        rgb *= (0.85 + 0.25 * hash2(bu, bv, 5))[..., None]
        mortar = ((np.floor(v * U) % 5) == 0) | (((np.floor(u * U) + (np.floor(v * U / 5) % 2) * 3) % 6) == 0)
        rgb[mortar] = C("5a5048")
        slab = np.broadcast_to(C("c4bcae"), u.shape + (3,)).copy()
        slab[((ui % 8) == 0) | ((vi % 8) == 0)] *= 0.88
    rgb[side] = slab[side]
    pad = np.pad(side, 1)
    near = (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]) & ~side
    rgb[near & inside] = C("9a948a")
    road = ~side
    if kind == "asphalt":
        if conns >= 3:
            for key, along in (("nx", v), ("px", v), ("ny", u), ("py", u)):
                if not b[key]:
                    continue
                pos = u if key in ("nx", "px") else v
                near_edge = (pos > 0.03) & (pos < 0.15) if key in ("nx", "ny") else (pos > 0.85) & (pos < 0.97)
                z = road & near_edge & ((np.floor(along * U) % 6) < 3) & (along > w) & (along < 1 - w)
                rgb[z] = C("ece8dc")
        else:
            if b["nx"] or b["px"]:
                d = road & (np.abs(v - 0.5) < 0.012) & ((np.floor(u * U) % 12) < 7)
                rgb[d] = C("ece8dc")
            if b["ny"] or b["py"]:
                d = road & (np.abs(u - 0.5) < 0.012) & ((np.floor(v * U) % 12) < 7)
                rgb[d] = C("ece8dc")
        mh = np.hypot(u - 0.36, v - 0.62) < 0.035
        if conns == 2 and hash2(np.array(mask), np.array(1), 3) > 0.4:
            rgb[mh & road] = C("3a3a40")
    return to_img(rgb, inside)


def gen_tiles(out):
    """Atlas (16 x 6 tiles of 128x64):
    row 0: zones  0-3 city, 4-5 city locked, 6-7 farm, 8 farm locked, 9-10 industry, 11 industry locked,
                  12-13 leisure, 14 leisure locked, 15 meadow
    row 1: 0-4 forest floor, 5-7 rocky ground, 8-9 clearing grass
    rows 2-5: roads by connection mask: dirt, asphalt, stone, highway
    """
    atlas = Image.new("RGBA", (TW * 16, TH * 6), (0, 0, 0, 0))
    row0 = [zone_tile("city", 1), zone_tile("city", 2), zone_tile("city", 3, flowers=0.004), zone_tile("city", 5, flowers=0.012),
            zone_tile("city", 7, True), zone_tile("city", 8, True, 0.004),
            zone_tile("farm", 30), zone_tile("farm", 31), zone_tile("farm", 32, True),
            zone_tile("industry", 40), zone_tile("industry", 41), zone_tile("industry", 42, True),
            zone_tile("leisure", 50, flowers=0.01), zone_tile("leisure", 51, flowers=0.02), zone_tile("leisure", 52, True),
            zone_tile("city", 60, flowers=0.03)]
    for i, t in enumerate(row0):
        atlas.paste(t, (i * TW, 0))
    row1 = [forest_floor(10), forest_floor(11), forest_floor(12), forest_floor(13), forest_floor(14),
            rock_ground(20), rock_ground(21), rock_ground(22), zone_tile("city", 70, flowers=0.01), zone_tile("leisure", 71, flowers=0.03)]
    for i, t in enumerate(row1):
        atlas.paste(t, (i * TW, TH))
    for m in range(16):
        for r, kind in enumerate(("dirt", "asphalt", "stone", "highway")):
            atlas.paste(road_tile(m, kind), (m * TW, TH * (2 + r)))
    atlas.save(os.path.join(out, "tiles.png"))
    # tile cursors
    u, v, inside = tile_uv()
    pad = np.pad(inside, 1)
    edge = inside & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    edge2 = inside & ~edge & ~(np.pad(inside & ~edge, 1)[:-2, 1:-1] & np.pad(inside & ~edge, 1)[2:, 1:-1])
    for name, col, fill in (("cursor_ok", (90, 230, 90), 26), ("cursor_bad", (240, 70, 60), 50), ("cursor_sel", (255, 220, 90), 40),
                            ("cursor_road", (90, 200, 255), 70)):
        arr = np.zeros((TH, TW, 4), np.uint8)
        arr[inside] = (*col, fill)
        arr[edge | edge2] = (*col, 255)
        Image.fromarray(arr).save(os.path.join(out, name + ".png"))
