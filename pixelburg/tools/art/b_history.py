"""Historic sights, each with its own look: a stone castle with a moat, a brick minaret, a domed mausoleum
with turquoise tiles, the ruins of an ancient temple, a five-tier pagoda and a triumphal arch."""
import math

import numpy as np

from raster import C, Canvas, flat, glow_res, nores, hash2
from arch import Orient, facade, Win, roof_mat
import kit
from bkit import ground, tree, bush, lamp, bench, box, slab, post, entry, door, flowerbed


# --------------------------------------------------------------------------- shared shapes
def _wall_fn(fn):
    """A facade texture used on a cylinder side (u runs around the tower)."""
    def side(a, v, nx, ny):
        return fn((a + math.pi) * 30, v, 190, 200)
    return side


def _cyl(T, s, f, r, z0, z1, side, cap=None):
    """An upright cylinder: side is a colour or a facade fn, cap a colour (defaults to the side colour)."""
    x, y = T.pt(s, f)
    sfn = _wall_fn(side) if callable(side) else (lambda a, v, nx, ny, c=flat(side, 3): c(a * 20, v))
    cfn = flat(cap or (side if not callable(side) else "8a8478"), 3)
    T.cv.cylinder(x, y, r, z0, z1, sfn, lambda a, b: cfn(a, b))


def _hf(T, s, f, w, hfun, colfn, zmin, thick=4.0):
    """A heightfield centred on a front-relative point. hfun(dx, dy) -> height (-inf = empty),
    colfn(wx, wy, wz, dx, dy) -> rgb. Round and square shapes look the same from every side."""
    x, y = T.pt(s, f)
    n = int(math.ceil(w))
    ys, xs = np.mgrid[0:n, 0:n] + 0.5
    H = hfun(xs - n / 2, ys - n / 2)
    x0, y0 = x - n / 2, y - n / 2

    def fn(wx, wy, wz, nx, ny, nz):
        return colfn(wx, wy, wz, wx - x, wy - y), nores(wx.shape), None
    T.cv.heightfield(x0, y0, H, fn, zmin=zmin, thick=thick)


def _cone(T, s, f, r, z, h, col, stripe=None):
    """A pointed round roof of tiles (a castle tower cap)."""
    base = C(col)

    def colfn(wx, wy, wz, dx, dy):
        rgb = np.broadcast_to(base, wx.shape + (3,)).copy()
        row = np.floor((wz - z) / 3.0)
        rgb *= (0.88 + 0.18 * hash2(np.floor(np.arctan2(dy, dx) * 6 + row * 0.5), row, 7))[..., None]
        rgb[((wz - z) % 3.0) < 0.6] *= 0.75
        if stripe:
            rgb[(wz - z) < 2.0] = C(stripe)
        return rgb
    _hf(T, s, f, 2 * r + 2, lambda dx, dy: np.where(np.hypot(dx, dy) < r, z + h * (1 - np.hypot(dx, dy) / r), -np.inf),
        colfn, z - 2, 3.0)


def _dome(T, s, f, r, z, h, col, ribs=0, rib_col=None, pattern=None):
    """Top half of an ellipsoid; ribs: vertical ribs, pattern: a tile diaper colour."""
    x, y = T.pt(s, f)
    base, rc = C(col), C(rib_col or col)

    def fn(wx, wy, wz, nx, ny, nz):
        rgb = np.broadcast_to(base, wx.shape + (3,)).copy()
        rgb *= (0.94 + 0.08 * hash2(np.floor(wx / 2), np.floor(wy / 2), 3))[..., None]
        a = np.arctan2(wy - y, wx - x)
        if ribs:
            rgb[((a / (2 * math.pi) * ribs) % 1.0) < 0.14] = rc
        if pattern:
            d = ((np.floor(a * 9) + np.floor((wz - z) / 5)) % 4) == 0
            rgb[d & ((wz - z) < h * 0.6)] = C(pattern)
        return rgb, nores(wx.shape), None
    T.cv.ellipsoid(x, y, z, r, r, h, fn, cut_z=z)


def _merlons(T, a0, a1, b, z, along="s", col="b8ae9c", th=8, w=6, gap=6, h=7):
    """Battlements along the top of a wall."""
    k = a0
    while k + w <= a1 + 0.01:
        if along == "s":
            T.box(k, b - th / 2, k + w, b + th / 2, z, z + h, all=flat(col, 4), top=flat(col, 3))
        else:
            T.box(b - th / 2, k, b + th / 2, k + w, z, z + h, all=flat(col, 4), top=flat(col, 3))
        k += w + gap


def _ring_merlons(T, s, f, r, z, col, n=10, h=7):
    for i in range(n):
        a = i / n * 2 * math.pi
        ss, ff = s + (r - 3) * math.cos(a), f + (r - 3) * math.sin(a)
        T.box(ss - 3, ff - 3, ss + 3, ff + 3, z, z + h, all=flat(col, 4), top=flat(col, 3))


def _flag(T, s, f, z, col, col2=None, h=26):
    post(T, s, f, z, z + h, "4a4440", 1.2)
    T.box(s + 0.6, f - 0.6, s + 14, f + 0.6, z + h - 10, z + h, all=flat(col, 2), top=flat(col, 2))
    if col2:
        T.box(s + 0.6, f - 0.7, s + 14, f + 0.7, z + h - 6, z + h - 4, all=flat(col2, 1), top=flat(col2, 1))


def _water(u, v, L, D):
    w = np.sin(u * 0.21 + np.sin(v * 0.17) * 2.0) + np.sin(v * 0.19 - np.sin(u * 0.13) * 2.0)
    t = np.clip((w + 2) / 4, 0, 1)
    rgb = C("2e6a8a") * (1 - t[..., None]) + C("4a8aa8") * t[..., None]
    rgb[np.abs(w - 1.2) < 0.07] = C("a8d0e0")
    return rgb, nores(u.shape), None


def _lantern(T, s, f, col="9a948a"):
    """A stone garden lantern with a warm light inside."""
    post(T, s, f, 0, 10, col, 2.4)
    T.box(s - 3.5, f - 3.5, s + 3.5, f + 3.5, 10, 16, all=lambda u, v, L, H: glow_res("ffd890", u.shape, 200), top=flat(col))
    T.box(s - 5, f - 5, s + 5, f + 5, 16, 18.5, all=flat(col, 3), top=flat(col, 3))
    post(T, s, f, 18.5, 21, col, 2.0)


def _cypress(T, s, f, sc=1.0, seed=0):
    tree(T, s, f, "poplar", sc, seed)


# --------------------------------------------------------------------------- castle
def castle(L, o):
    """A grey stone castle: curtain walls with battlements and arrow slits, four round corner towers with
    blue conical roofs, a gatehouse with a portcullis over a moat bridge and a tall keep with banners."""
    cv = Canvas(3, 220)
    T = Orient(cv, o)
    stone, dark, roof, red = "b8ae9c", "8a8274", "3a5a8a", "c8342e"
    ground(T, 0, 0, 480, 480, kit.paving("a8a088", 9.0, 2101))
    ground(T, 0, 0, 480, 480, flat("6a9a48", 6), 0.25)
    # the moat all round, crossed by a wooden bridge at the gate
    ground(T, 20, 20, 460, 460, _water, 0.4)
    ground(T, 52, 52, 428, 428, flat("7aa258", 6, 2102), 0.5)
    ground(T, 212, 0, 268, 60, flat("8a6a44", 3), 0.7)
    for k in range(9):
        ground(T, 212, 4 + k * 6, 268, 5 + k * 6, flat("5a4430", 2), 0.8)
    # courtyard
    ground(T, 70, 70, 410, 410, kit.gravel("b0a48a", 2103), 0.6)
    wall = facade("stone", stone, win=Win(w=3, h=12, sill=24, sp=34, fh=60, frame="4a443c", style="plain", lintel=False),
                  plinth=(dark, 6), seed=2104)
    plain = facade("stone", stone, plinth=(dark, 6), seed=2105)
    # curtain walls (front has a gap for the gatehouse)
    wh = 54
    box(T, 60, 60, 210, 76, 0, wh, front=wall, back=plain, left=plain, right=plain, top=flat("a89e8c", 3))
    box(T, 270, 60, 420, 76, 0, wh, front=wall, back=plain, left=plain, right=plain, top=flat("a89e8c", 3))
    box(T, 60, 404, 420, 420, 0, wh, all=wall, top=flat("a89e8c", 3))
    box(T, 60, 60, 76, 420, 0, wh, all=wall, top=flat("a89e8c", 3))
    box(T, 404, 60, 420, 420, 0, wh, all=wall, top=flat("a89e8c", 3))
    _merlons(T, 60, 210, 63, wh, "s", stone)
    _merlons(T, 270, 420, 63, wh, "s", stone)
    _merlons(T, 60, 420, 417, wh, "s", stone)
    _merlons(T, 60, 420, 63, wh, "f", stone)
    _merlons(T, 60, 420, 417, wh, "f", stone)
    # keep at the back of the courtyard
    kw = facade("stone", "c4baa8", win=Win(w=8, h=16, sill=20, sp=30, fh=36, frame="5a5248", style="vertical", arch=True),
                plinth=(dark, 8), seed=2106, lit=0.7)
    kh = 112
    box(T, 170, 260, 310, 380, 0, kh, all=kw, top=flat("9a907e", 3))
    _merlons(T, 170, 310, 263, kh, "s", "c4baa8")
    _merlons(T, 170, 310, 377, kh, "s", "c4baa8")
    _merlons(T, 260, 380, 173, kh, "f", "c4baa8")
    _merlons(T, 260, 380, 307, kh, "f", "c4baa8")
    tw = facade("stone", "c4baa8", win=Win(w=6, h=12, sill=14, sp=40, fh=30, frame="5a5248", style="plain", arch=True), plinth=None, seed=2107)
    _cyl(T, 290, 280, 18, kh, kh + 36, tw, "9a907e")
    _cone(T, 290, 280, 22, kh + 36, 44, roof)
    _flag(T, 290, 280, kh + 79, red, "f0c020", 30)
    cv.mark("light", *T.pt(240, 260), 60)
    # four corner towers
    for (s, f) in ((68, 68), (412, 68), (68, 412), (412, 412)):
        _cyl(T, s, f, 30, 0, wh + 34, facade("stone", stone, win=Win(w=3, h=12, sill=22, sp=26, fh=44, frame="4a443c", style="plain", lintel=False),
                                             plinth=(dark, 6), seed=2108), "a89e8c")
        _ring_merlons(T, s, f, 30, wh + 34, stone, 12)
        _cone(T, s, f, 34, wh + 41, 52, roof)
    _flag(T, 68, 68, wh + 92, red, None, 20)
    _flag(T, 412, 68, wh + 92, red, None, 20)
    # gatehouse: two square towers and an arch with a portcullis
    gate = facade("stone", stone, doors=[(18, 24, 36, "double", "4a3424")], plinth=(dark, 6), seed=2109,
                  decals=[(16, 44, 34, 36, "3a3430")])
    box(T, 196, 52, 284, 84, 0, wh + 18, front=gate, back=gate, left=plain, right=plain, top=flat("a89e8c", 3))
    for s0 in (186, 262):
        box(T, s0, 46, s0 + 32, 88, 0, wh + 32, front=wall, back=plain, left=plain, right=plain, top=flat("a89e8c", 3))
        _merlons(T, s0, s0 + 32, 49, wh + 32, "s", stone, 6, 5, 4)
        _merlons(T, s0, s0 + 32, 85, wh + 32, "s", stone, 6, 5, 4)
    _merlons(T, 218, 262, 55, wh + 18, "s", stone, 6, 5, 5)
    # portcullis bars inside the arch
    for k in range(5):
        T.box(222 + k * 9, 52, 223.5 + k * 9, 54, 26, 50, all=flat("3a3a3a", 2), top=flat("3a3a3a"))
    T.box(220, 52, 260, 54, 44, 46, all=flat("3a3a3a", 2), top=flat("3a3a3a"))
    door(T, 222, 36, 52, 32)
    lamp(T, 200, 30, "lantern", 40, "light1")
    lamp(T, 280, 30, "lantern", 40, "light2")
    # courtyard: a well and some barrels
    _cyl(T, 130, 200, 10, 0, 10, facade("stone", "a89e8c", plinth=None, seed=2110), "3a5a6a")
    post(T, 122, 200, 10, 24, "5a4430", 1.4)
    post(T, 138, 200, 10, 24, "5a4430", 1.4)
    slab(T, 118, 196, 142, 204, 24, 27, "7a3a2a")
    if L >= 2:
        # banners down the keep and a stable
        for s in (190, 290):
            T.box(s, 258, s + 12, 260, 60, 96, all=flat(red, 2), top=flat(red))
            T.box(s + 4, 257.5, s + 8, 258, 70, 88, all=flat("f0c020", 1), top=flat("f0c020"))
        box(T, 330, 300, 396, 396, 0, 26, all=facade("wood", "8a6a44", doors=[(10, 14, 20, "wood")], plinth=None, seed=2111),
            top=flat("6a4a30"))
        T.gable(330, 300, 396, 396, 26, 14, roof_mat("8a5a3a", "shingle"), facade("wood", "8a6a44", plinth=None, seed=2112), "f")
        tree(T, 30, 440, "oak", 0.8, 2113)
        tree(T, 450, 30, "oak", 0.7, 2114)
    if L >= 3:
        # market tents in the courtyard and knights' flags on every tower
        for k, col in enumerate(("c8342e", "2a5aa8", "e8b830")):
            s = 100 + k * 50
            box(T, s, 110, s + 34, 140, 0, 14, all=flat("e8e0cc", 3), top=flat("e8e0cc"))
            T.gable(s - 2, 108, s + 36, 142, 14, 10, roof_mat(col, "metal"), flat("e8e0cc", 3), "s")
        _flag(T, 68, 412, wh + 92, "2a5aa8", None, 20)
        _flag(T, 412, 412, wh + 92, "2a5aa8", None, 20)
        bench(T, 200, 180, "s")
        lamp(T, 140, 260, "lantern", 36, "light3")
    entry(T, 240)
    return cv


# --------------------------------------------------------------------------- minaret
def minaret(L, o):
    """A tall tapering brick minaret with ornamental bands, a ring of muqarnas under an arched lantern
    and a little dome on top, on a tiled square."""
    cv = Canvas(1, 300)
    T = Orient(cv, o)
    brick, light, tile = "c89a64", "e0c08c", "2a9aa8"
    ground(T, 0, 0, 160, 160, kit.paving("d8ccb0", 8.0, 2201))
    ground(T, 22, 22, 138, 138, kit.paving("c8b898", 6.0, 2202), 0.4)
    # octagonal-looking plinth
    slab(T, 40, 40, 120, 120, 0, 8, "b8a888")
    cs, cf = 80, 80

    def band(seed, accent):
        def fn(u, v, L_, H):
            rgb = np.broadcast_to(C(brick), u.shape + (3,)).copy()
            row = np.floor(v / 2.5)
            off = (row % 2) * 2.5
            rgb *= (0.9 + 0.14 * hash2(np.floor((u + off) / 5), row, seed))[..., None]
            rgb[(v % 2.5) < 0.5] *= 0.8
            pat = ((np.floor(u / 4) + np.floor(v / 4)) % 2 == 0) & (np.abs((v % 24) - 12) < 4)
            rgb[pat] = C(light)
            rgb[np.abs((v % 24) - 12) < 0.8] = C(accent)
            return rgb, nores(u.shape), None
        return fn
    n = 8
    zt = 196
    for k in range(n):
        z0, z1 = 8 + k * (zt - 8) / n, 8 + (k + 1) * (zt - 8) / n
        r = 25 - k * 1.3
        _cyl(T, cs, cf, r, z0, z1, band(2203 + k, tile if k % 2 else "8a5a3a"), brick)
    # muqarnas balcony ring and the arched lantern
    _cyl(T, cs, cf, 19, zt, zt + 6, "e0c08c")
    _cyl(T, cs, cf, 22, zt + 6, zt + 10, tile)
    lan = facade("brick", brick, win=Win(w=6, h=14, sill=3, sp=10, fh=26, frame="6a4a2a", style="plain", arch=True),
                 plinth=None, seed=2211, lit=1.0)
    _cyl(T, cs, cf, 16, zt + 10, zt + 32, lan, brick)
    _cyl(T, cs, cf, 18, zt + 32, zt + 36, light)
    _dome(T, cs, cf, 15, zt + 36, 16, tile, 8, "1e7a88")
    post(T, cs, cf, zt + 50, zt + 62, "d8b040", 1.4)
    cv.mark("light", *T.pt(cs, cf), zt + 20)
    door(T, 72, 16, 55, 22)
    box(T, 70, 52, 90, 58, 8, 32, front=facade("brick", brick, doors=[(3, 14, 22, "wood", "5a3a24")], plinth=None, seed=2212),
        top=flat(light))
    if L >= 2:
        for (s, f) in ((20, 20), (140, 20)):
            _cypress(T, s, f, 0.7, 2213 + s)
        flowerbed(T, 24, 120, 56, 140, 2215)
    if L >= 3:
        lamp(T, 30, 60, "lantern", 36, "light1")
        lamp(T, 130, 60, "lantern", 36, "light2")
        bench(T, 116, 132, "s")
    entry(T, 80)
    return cv


# --------------------------------------------------------------------------- mausoleum
def mausoleum(L, o):
    """A domed mausoleum: a cubic hall faced with glazed tiles, a tall portal (pishtaq) with a blue
    mosaic arch, two slim corner minarets, a ribbed turquoise dome on a drum and a garden with a pool."""
    cv = Canvas(2, 220)
    T = Orient(cv, o)
    sand, tile, deep, gold = "dcc49a", "2aa0b0", "1e4a8a", "d8b040"
    ground(T, 0, 0, 320, 320, flat("6a9a48", 6, 2301))
    ground(T, 40, 40, 280, 300, kit.paving("e0d4b8", 8.0, 2302), 0.4)
    # garden paths and a long pool in front
    kit.pool(cv, *T.rect(146, 0, 174, 64))
    for (s, f) in ((20, 20), (300, 20), (20, 150), (300, 150)):
        _cypress(T, s, f, 0.75, 2303 + s + f)

    def hall_fn(seed):
        base = facade("brick", sand, bands=[(48, 56, tile), (60, 62, deep)], plinth=("a89070", 6), seed=seed,
                      win=Win(w=10, h=20, sill=16, sp=36, fh=70, frame=deep, style="grid", arch=True, top_skip=16))
        return base
    hall = hall_fn(2304)
    box(T, 70, 100, 250, 270, 0, 66, all=hall, top=flat("c8b088", 3))
    # drum with a band of tiles and windows, then the dome
    drum = facade("tile", tile, win=Win(w=6, h=10, sill=5, sp=22, fh=22, frame="f4ecd8", style="plain", arch=True),
                  bands=[(0, 3, sand), (19, 22, sand)], plinth=None, seed=2305)
    _cyl(T, 160, 185, 54, 66, 90, drum, sand)
    _dome(T, 160, 185, 56, 90, 66, tile, 24, "1a7a8a", deep)
    _cyl(T, 160, 185, 3, 154, 160, gold)
    post(T, 160, 185, 160, 176, gold, 1.4)
    # the portal with a deep blue mosaic arch
    def portal(u, v, L_, H):
        rgb, ns, em, rooms = facade("brick", sand, plinth=("a89070", 6), seed=2306)(u, v, L_, H)
        cx = u - L_ / 2
        frame = (np.abs(cx) < 36) & (v < H - 10)
        rgb[frame] = C(tile) * (0.9 + 0.12 * hash2(np.floor(u / 3), np.floor(v / 3), 9))[frame][..., None]
        niche = (np.abs(cx) < 24) & ((v < 62) | ((v < 86) & (cx * cx + (v - 62) ** 2 < 24 ** 2)))
        rgb[niche] = C(deep) * (0.85 + 0.25 * (((np.floor(u / 4) + np.floor(v / 4)) % 2) == 0))[niche][..., None]
        star = niche & (((np.abs(cx) + np.abs((v % 16) - 8)) % 8) < 1.2)
        rgb[star] = C("f4ecd8")
        dr = (np.abs(cx) < 10) & (v < 30)
        rgb[dr] = C("5a3a24")
        rgb[dr & (np.abs(cx) < 0.7)] = C("3a2414")
        rgb[(v > H - 8)] = C(gold)
        return rgb, ns, em, rooms
    box(T, 104, 86, 216, 104, 0, 104, front=portal, back=flat(sand, 3), left=flat(sand, 3), right=flat(sand, 3), top=flat("c8b088", 3))
    door(T, 150, 20, 86, 30)
    for s in (98, 222):
        _cyl(T, s, 92, 7, 0, 116, facade("brick", sand, bands=[(40, 46, tile), (80, 86, tile)], plinth=None, seed=2307), sand)
        _dome(T, s, 92, 8, 116, 9, tile)
    cv.mark("light", *T.pt(160, 80), 40)
    if L >= 2:
        for (s, f) in ((60, 70), (260, 70)):
            flowerbed(T, s - 16, f - 14, s + 16, f + 14, 2310 + s)
        bench(T, 120, 40, "f")
        bench(T, 200, 40, "f")
    if L >= 3:
        for (s, f) in ((40, 290), (280, 290)):
            tree(T, s, f, "oak", 0.7, 2320 + s)
        lamp(T, 130, 10, "lantern", 38, "light1")
        lamp(T, 190, 10, "lantern", 38, "light2")
    entry(T, 160)
    return cv


# --------------------------------------------------------------------------- ancient temple
def _column(T, s, f, z0, z1, col="ece4d4"):
    """A fluted marble column with a square capital."""
    x, y = T.pt(s, f)
    c = C(col)

    def side(a, v, nx, ny):
        rgb = np.broadcast_to(c, a.shape + (3,)).copy()
        rgb *= (0.86 + 0.16 * ((a * 6 / math.pi) % 1.0 > 0.35))[..., None]
        rgb *= (0.94 + 0.08 * hash2(np.floor(a * 8), np.floor(v / 4), 5))[..., None]
        return rgb, nores(a.shape), None
    T.cv.cylinder(x, y, 6, z0, z1, side, lambda a, b: flat(col, 3)(a, b))
    if z1 - z0 > 40:
        T.box(s - 8, f - 8, s + 8, f + 8, z1, z1 + 4, all=flat(col, 3), top=flat(col, 3))


def ancient_temple(L, o):
    """Ruins of an ancient temple on a stepped marble podium: rows of fluted columns, some broken,
    fallen drums in the grass and a surviving corner of the entablature and pediment.
    Higher levels restore more of it."""
    cv = Canvas(2, 160)
    T = Orient(cv, o)
    marble, old = "ece4d4", "c8bca4"
    ground(T, 0, 0, 320, 320, flat("8aa858", 6, 2401))
    ground(T, 0, 0, 320, 320, kit.gravel("c8b898", 2402), 0.3)
    # podium in three steps
    for k in range(3):
        slab(T, 40 + k * 8, 50 + k * 8, 280 - k * 8, 290 - k * 8, k * 4, k * 4 + 4, "e0d8c4" if k % 2 else "d8d0bc")
    zb = 12
    # peristyle: 6 columns across, 8 along
    cols = []
    for i in range(6):
        cols.append((76 + i * 33.6, 82))
        cols.append((76 + i * 33.6, 258))
    for j in range(1, 7):
        cols.append((76, 82 + j * 25.1))
        cols.append((244, 82 + j * 25.1))
    full = 76
    rng = np.random.default_rng(2403)
    broken = {2: 30, 5: 18, 9: 44, 13: 24, 16: 36, 19: 14, 22: 40}
    if L >= 2:
        broken = {5: 18, 13: 24, 19: 14}
    if L >= 3:
        broken = {}
    for k, (s, f) in enumerate(cols):
        h = broken.get(k, full)
        _column(T, s, f, zb, zb + h, marble if h == full else old)
    # the surviving entablature: along the back and up the left side (all round at level 3)
    ent = facade("stone", "e4dccb", bands=[(0, 4, "d0c8b4"), (12, 16, "d0c8b4")], plinth=None, seed=2404)
    zt = zb + full + 4
    box(T, 66, 248, 254, 268, zt, zt + 18, all=ent, top=flat("d8d0bc", 3))
    box(T, 66, 72, 86, 268, zt, zt + 18, all=ent, top=flat("d8d0bc", 3))
    if L >= 2:
        box(T, 234, 72, 254, 268, zt, zt + 18, all=ent, top=flat("d8d0bc", 3))
    if L >= 3:
        box(T, 66, 72, 254, 92, zt, zt + 18, all=ent, top=flat("d8d0bc", 3))

        def ped(u, v, L_, H):
            rgb, ns, em = flat("e4dccb", 3)(u, v)
            fig = (np.abs(u - L_ / 2) < 40) & (v > 3) & (v < 14) & ((np.floor(u / 6) % 2) == 0)
            rgb[fig] = C("c8bca4")
            return rgb, ns, em
        T.gable(66, 72, 254, 268, zt + 18, 20, roof_mat("c8a888", "tiles"), ped, "f")
    else:
        # a broken corner of the pediment at the back
        T.gable(66, 248, 160, 268, zt + 18, 14, roof_mat("b89a7a", "tiles"), flat("e4dccb", 3), "s")
    # the cella walls inside (low ruins)
    cella = facade("stone", "d8ceb8", plinth=None, seed=2405)
    box(T, 120, 130, 200, 228, zb, zb + (22 if L == 1 else 40), all=cella, top=flat("c8bca4", 3))
    door(T, 150, 20, 130, 22)
    # fallen drums and blocks in the grass
    if L < 3:
        for k in range(4 if L == 1 else 2):
            s, f = 24 + rng.uniform(0, 30) + k * 70, 26 + rng.uniform(0, 14)
            T.box(s, f, s + 18, f + 11, 0, 9, all=flat(old, 4), top=flat(old, 3))
    # an info board and a statue
    slab(T, 20, 120, 34, 150, 0, 12, "b8ac94")
    post(T, 27, 135, 12, 30, "8a8274", 3)
    T.box(22, 127, 32, 143, 30, 40, all=flat("8a6a2a", 2), top=flat("8a6a2a"))
    cv.mark("light", *T.pt(160, 180), 50)
    if L >= 2:
        for s in (20, 300):
            _cypress(T, s, 300, 0.8, 2410 + s)
        bench(T, 160, 30, "s")
    if L >= 3:
        lamp(T, 40, 20, "classic", 40, "light1")
        lamp(T, 280, 20, "classic", 40, "light2")
    entry(T, 160)
    return cv


# --------------------------------------------------------------------------- pagoda
def _pagoda_roof(T, s, f, half, z, rh, col, eave="2a2a2a"):
    """A square roof with concave slopes and turned-up corners."""
    base, ec = C(col), C(eave)

    def hfun(dx, dy):
        m = np.maximum(np.abs(dx), np.abs(dy)) / half
        corner = (np.abs(dx) / half) * (np.abs(dy) / half)
        return np.where(m < 1, z + rh * (1 - m) ** 1.7 + 6 * corner ** 4, -np.inf)

    def colfn(wx, wy, wz, dx, dy):
        rgb = np.broadcast_to(base, wx.shape + (3,)).copy()
        m = np.maximum(np.abs(dx), np.abs(dy))
        rib = np.where(np.abs(dx) > np.abs(dy), dy, dx)
        rgb *= (0.84 + 0.2 * ((rib % 4.0) > 1.2))[..., None]
        rgb[m > half - 2.5] = ec
        return rgb
    _hf(T, s, f, 2 * half + 2, hfun, colfn, z - 2, 3.0)


def pagoda(L, o):
    """A five-tier pagoda: red columns and white walls on a stone base, dark green tiled roofs with
    upturned corners, a golden spire with rings, a red gate, stone lanterns and blossoming trees."""
    cv = Canvas(2, 280)
    T = Orient(cv, o)
    red, white, roof, gold = "b8322a", "f0e8d8", "3a5a4a", "d8b040"
    ground(T, 0, 0, 320, 320, flat("7aa258", 6, 2501))
    ground(T, 138, 0, 182, 110, kit.paving("c8c0b0", 7.0, 2502), 0.4)
    slab(T, 88, 100, 232, 244, 0, 10, "9a948a")
    cs, cf = 160, 172
    z = 10
    for k in range(5):
        hw = 46 - k * 6
        wh = 30 if k == 0 else 24

        def wall(u, v, L_, H, hw=hw):
            rgb = np.broadcast_to(C(white), u.shape + (3,)).copy()
            colm = ((u % (2 * hw / 3)) < 4) | (u < 4) | (u > L_ - 4)
            rgb[colm] = C(red)
            rgb[v > H - 4] = C(red)
            win = (~colm) & (v > 6) & (v < H - 7) & (np.abs((u % (2 * hw / 3)) - hw / 3 - 2) < 5)
            rgb[win] = C("6a2a20")
            lat = win & ((((u % 3) < 0.7)) | ((v % 3) < 0.7))
            rgb[lat] = C(gold)
            em = np.zeros(u.shape + (4,))
            em[win & ~lat] = [255, 200, 120, 150]
            return rgb, nores(u.shape), em
        T.box(cs - hw, cf - hw, cs + hw, cf + hw, z, z + wh, all=wall, top=flat(red, 3))
        # balcony rail on the upper tiers
        if k > 0:
            for (a0, a1, b, al) in ((cs - hw - 4, cs + hw + 4, cf - hw - 4, "s"), (cf - hw - 4, cf + hw + 4, cs - hw - 4, "f"),
                                    (cf - hw - 4, cf + hw + 4, cs + hw + 4, "f")):
                T.panel(a0, a1, b, z, z + 5, flat(red, 2), al)
        z += wh
        _pagoda_roof(T, cs, cf, hw + 13, z, 10, roof)
        z += 6
    # spire
    post(T, cs, cf, z, z + 34, gold, 2.4)
    for k in range(6):
        _cyl(T, cs, cf, 4.5 - k * 0.4, z + 6 + k * 4.5, z + 7.5 + k * 4.5, gold)
    _dome(T, cs, cf, 4, z + 34, 6, gold)
    door(T, 152, 16, cf - 48, 22)
    cv.mark("light", *T.pt(cs, cf - 50), 30)
    # the red gate over the path
    for s in (142, 178):
        post(T, s, 40, 0, 46, red, 4)
    T.box(132, 37, 188, 43, 46, 50, all=flat("2a2a2a", 2), top=flat("2a2a2a", 2))
    T.box(138, 38, 182, 42, 38, 42, all=flat(red, 2), top=flat(red, 2))
    for (s, f) in ((126, 90), (194, 90)):
        _lantern(T, s, f)
    x, y = T.pt(50, 70)
    kit.sakura(cv, x, y, 0.8, 2503)
    x, y = T.pt(270, 260)
    kit.sakura(cv, x, y, 0.7, 2504)
    if L >= 2:
        # a koi pond with a little arched bridge
        ground(T, 220, 40, 300, 110, _water, 0.5)
        for k in range(8):
            T.box(244, 60 + k * 4, 276, 64 + k * 4, 0, 2 + 6 * math.sin(math.pi * (k + 0.5) / 8), all=flat(red, 2), top=flat("8a6a44", 3))
        bush(T, 30, 160, 0.6, 2505, "f4a8c0")
    if L >= 3:
        for (s, f) in ((60, 140), (260, 140)):
            _lantern(T, s, f)
        x, y = T.pt(40, 280)
        kit.sakura(cv, x, y, 0.7, 2506)
        bench(T, 110, 120, "f")
    entry(T, 160)
    return cv


# --------------------------------------------------------------------------- triumphal arch
def triumph_arch(L, o):
    """A triumphal arch of pale stone: a great vault over the road, columns and reliefs on the piers,
    an attic with an inscription and a bronze chariot group on top, on a paved square."""
    cv = Canvas(1, 200)
    T = Orient(cv, o)
    stone, bronze = "e4dcc8", "4a7a6a"
    ground(T, 0, 0, 160, 160, kit.paving("d4ccb8", 8.0, 2601))
    ground(T, 56, 0, 104, 160, kit.paving("b8b0a0", 6.0, 2602), 0.4)

    def pier(u, v, L_, H):
        rgb, ns, em, rooms = facade("stone", stone, plinth=("c8bca4", 10), seed=2603)(u, v, L_, H)
        rel = (u > 8) & (u < L_ - 8) & (v > 40) & (v < 64)
        rgb[rel] = C("cfc4ac")
        fig = rel & ((np.floor(u / 5) + np.floor(v / 8)) % 3 == 0)
        rgb[fig] = C("b0a48c")
        return rgb, ns, em, rooms
    fa, fb = 66, 94
    zs, R, zt = 60, 24, 96
    box(T, 22, fa, 56, fb, 0, zt, all=pier, top=flat(stone, 3))
    box(T, 104, fa, 138, fb, 0, zt, all=pier, top=flat(stone, 3))
    # the vault: thin strips fill in above the semicircle
    for k in range(24):
        s0 = 56 + k * 2
        sc = s0 + 1 - 80
        zc = zs + math.sqrt(max(0.0, R * R - sc * sc))
        T.box(s0, fa, s0 + 2, fb, zc, zt, all=flat(stone, 3), top=flat(stone, 3))
    T.box(56, fa + 4, 104, fb - 4, zs - 0.5, zs + 0.5, all=flat("c8bca4", 2), top=flat("c8bca4", 2))
    # columns on the piers
    for s in (26, 52, 108, 134):
        x, y = T.pt(s, fa - 4)
        T.cv.cylinder(x, y, 3, 10, 86, lambda a, v, nx, ny: flat("f0e8d8", 3)(a * 10, v), lambda a, b: flat("f0e8d8")(a, b))
    T.box(18, fa - 8, 142, fb + 4, zt - 6, zt, all=flat("d8d0bc", 3), top=flat(stone, 3))
    # attic with an inscription
    att = facade("stone", stone, plinth=None, seed=2604, signs=[(60, 7, "GLORIA", 9, None, "8a6a2a", False)])
    box(T, 22, fa + 2, 138, fb - 2, zt, zt + 26, all=att, top=flat(stone, 3))
    # bronze chariot group
    slab(T, 54, 74, 106, 86, zt + 26, zt + 32, "c8bca4")
    for k in range(4):
        T.box(58 + k * 8, 76, 63 + k * 8, 84, zt + 32, zt + 46 + (k % 2) * 2, all=flat(bronze, 5), top=flat(bronze, 4))
    T.box(90, 75, 102, 85, zt + 32, zt + 42, all=flat(bronze, 5), top=flat(bronze, 4))
    T.box(94, 78, 99, 82, zt + 42, zt + 56, all=flat(bronze, 5), top=flat(bronze, 4))
    door(T, 60, 40, fa, 56)
    cv.mark("light", *T.pt(80, fa - 6), 40)
    if L >= 2:
        for s in (12, 148):
            bush(T, s, 30, 0.5, 2605 + s, "e84a5a")
            bush(T, s, 130, 0.5, 2607 + s, "f0c040")
    if L >= 3:
        lamp(T, 14, 60, "classic", 40, "light1")
        lamp(T, 146, 60, "classic", 40, "light2")
    entry(T, 80)
    return cv


BUILDERS = {"castle": castle, "minaret": minaret, "mausoleum": mausoleum, "ancient_temple": ancient_temple,
            "pagoda": pagoda, "triumph_arch": triumph_arch}
