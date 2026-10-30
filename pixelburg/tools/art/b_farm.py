"""New farm buildings, each with its own look: an apiary, a poultry farm, a melon field (bakhcha), a vineyard,
a windmill, a fish farm and a dairy."""
import math

import numpy as np

from raster import C, Canvas, flat, solid_res, nores, hash2
from arch import Orient, facade, Win, roof_mat, flat_top
import kit
from bkit import ground, tree, bush, fence, lamp, box, post, door, entry, sign_board, car_static
from b_work import silo, hay, crates, cow, tractor


def meadow(seed=0, base="6aa244", flowers=("f0d040", "e84a6a", "f4f0f0", "a070d0"), dens=0.05):
    """Grass dotted with flowers."""
    def fn(u, v, *_):
        rgb = np.broadcast_to(C(base), u.shape + (3,)).copy()
        rgb *= (0.88 + 0.2 * hash2(np.floor(u / 3), np.floor(v / 3), seed))[..., None]
        cell = hash2(np.floor(u / 2), np.floor(v / 2), seed + 1)
        for k, col in enumerate(flowers):
            m = (cell > 1 - dens * (k + 1) / len(flowers)) & (cell <= 1 - dens * k / len(flowers))
            rgb[m] = C(col)
        return rgb, nores(u.shape), None
    return fn


def _cyl(T, s, f, r, z0, z1, col, cap=None, noise=3):
    x, y = T.pt(s, f)
    side = flat(col, noise)
    top = flat(cap or col, noise)
    T.cv.cylinder(x, y, r, z0, z1, lambda a, v, nx, ny: side(a * 20, v), lambda a, b: top(a, b))


def _ball(T, s, f, z, rx, ry, rz, fn):
    x, y = T.pt(s, f)
    T.cv.ellipsoid(x, y, z, rx, ry, rz, fn)


def _solid3(col):
    return lambda wx, *_: solid_res(C(col), wx.shape)


# --------------------------------------------------------------------------- apiary
def _hive(T, s, f, col):
    """A painted beehive on a stand: two boxes and an overhanging lid."""
    for ds in (1, 11):
        post(T, s + ds, f + 6, 0, 4, "6a4a2a", 1.2)
    T.box(s, f, s + 12, f + 12, 4, 11, all=flat(col, 3), top=flat(col, 3))
    T.box(s, f, s + 12, f + 12, 11, 17, all=flat(col, 3, 2), top=flat(col, 3))
    T.box(s, f - 0.4, s + 12, f + 0.4, 5, 6, all=flat("3a2a1a", 1), top=flat("3a2a1a", 1))
    T.box(s - 1.5, f - 1.5, s + 13.5, f + 13.5, 17, 19.5, all=flat("f2eee6", 2), top=flat("c8c4bc", 3))


def apiary(L, o):
    """A beekeeper's meadow: rows of colourful hives among flowers, a little honey hut and a sign."""
    cv = Canvas(1, 70)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, meadow(3))
    ground(T, 66, 0, 94, 60, kit.gravel("b8a888", 5), 0.4)
    cols = ["e8b830", "4a8ad0", "e86a3a", "6ab85a", "f2eee6", "c85aa8"]
    spots = [(14, 30), (38, 30), (14, 66), (38, 66), (110, 30), (134, 30)] + ([(110, 66), (134, 66)] if L >= 2 else [])
    for k, (s, f) in enumerate(spots):
        _hive(T, s, f, cols[k % len(cols)])
    # honey hut: wooden shed with a jar sign
    hut = facade("wood", "b8864a", doors=[(14, 14, 20, "wood", "6a4428")], plinth=None, seed=901)
    box(T, 56, 96, 104, 140, 0, 26, all=hut)
    T.gable(56, 96, 104, 140, 26, 14, roof_mat("8a3a2a", "tiles"), dict(all=hut), ridge="s", o=3)
    door(T, 70, 14, 96, 20)
    entry(T, 80)
    sign_board(T, 80, 96, 22, "HONEY", 6, "e8a820", "3a2a1a", glow=False)
    # honey jars on a little table
    T.box(64, 80, 96, 90, 8, 10, all=flat("8a6a44", 2), top=flat("a8865a", 3))
    for k in range(4):
        _cyl(T, 68 + k * 8, 85, 2.6, 10, 16, "e8a020", "f2eee6")
    for s, f, fl in ((20, 120, "f0d040"), (140, 120, "e84a6a"), (140, 96, "a070d0")):
        bush(T, s, f, 0.6, s + f, fl)
    if L >= 3:
        tree(T, 20, 145, "fruit", 0.55, 9, "f4c8d8")
        fence(T, 4, 156, 156, "s", "c8a070", "picket", 8)
    return cv


# --------------------------------------------------------------------------- poultry farm
def chicken(T, s, f, col="f6f2ea", seed=0):
    rng = np.random.default_rng(seed)
    d = rng.choice([-1, 1])
    _ball(T, s, f, 4, 3.4, 2.6, 2.8, _solid3(col))
    _ball(T, s + 3 * d, f, 7, 1.6, 1.6, 1.8, _solid3(col))
    x, y = T.pt(s + 3 * d, f)
    T.cv.box(x - 0.5, y - 0.5, 8.4, x + 0.5, y + 0.5, 9.6, flat("d8302a", 1), flat("d8302a", 1), flat("d8302a", 1))
    for ds in (-1, 1):
        post(T, s + ds, f, 0, 2, "e8a020", 0.5)


def chicken_farm(L, o):
    """A long white coop with a red metal roof, a fenced run full of chickens, a feed silo and egg crates."""
    cv = Canvas(2, 110)
    T = Orient(cv, o)
    ground(T, 0, 0, 320, 320, kit.lawn_stripes(41))
    ground(T, 10, 150, 310, 310, kit.gravel("b8a07a", 42), 0.4)
    win = Win(w=12, h=7, sill=14, sp=24, margin=12, fh=30, frame="f2eee6", group="work")
    long_side = facade("plaster", "f2eee6", win=win, plinth=("8a6a4a", 4), seed=911)
    end = facade("plaster", "f2eee6", doors=[(22, 26, 22, "double", "a8342a")], plinth=("8a6a4a", 4), seed=912)
    box(T, 20, 70, 300, 130, 0, 26, front=long_side, back=long_side, left=end, right=end)
    T.gable(20, 70, 300, 130, 26, 18, roof_mat("b8382a", "metal"), dict(front=long_side, back=long_side, left=end, right=end), ridge="s", o=4)
    for k in range(4):
        _cyl(T, 60 + k * 70, 100, 3, 44, 50, "c8ccd0", "8a8e94")
    # little office in front with the door to the street
    off = facade("plaster", "f6e8c8", doors=[(14, 14, 22, "wood", "6a4428")], win=Win(w=10, h=10, sill=10, sp=24, margin=34, fh=30), seed=913)
    box(T, 120, 30, 180, 70, 0, 26, all=off, top=flat_top("7a7a80", "f6e8c8", 2))
    door(T, 134, 14, 30, 22)
    entry(T, 141)
    ground(T, 130, 0, 156, 30, kit.paving("c8bca8", 6.0, 43))
    silo(T, 260, 40, 14, 70, "e8e4dc")
    crates(T, 40, 20, 4 + L, 44)
    crates(T, 70, 30, 3, 45)
    # the run: mesh fence and chickens
    for a0, a1, b, al in ((10, 310, 310, "s"), (150, 310, 10, "f"), (150, 310, 310, "f")):
        fence(T, a0, a1, b, al, "c8ccd0", "metal", 9)
    rng = np.random.default_rng(46)
    for k in range(8 + L * 5):
        s, f = rng.uniform(20, 300), rng.uniform(150, 300)
        chicken(T, s, f, ["f6f2ea", "c8763a", "8a4a2a", "f6f2ea"][k % 4], k)
    # feeders
    for s in (80, 160, 240):
        T.box(s, 220, s + 30, 228, 0, 4, all=flat("8a8e94", 2), top=flat("c8a050", 6))
    if L >= 2:
        tractor(T, 210, 20, "s")
    return cv


# --------------------------------------------------------------------------- melon field (bakhcha)
def _vines(seed):
    def fn(u, v, *_):
        rgb = np.broadcast_to(C("8a6a44"), u.shape + (3,)).copy()
        rgb += ((hash2(np.floor(u), np.floor(v), seed) - 0.5) * 18)[..., None]
        n = hash2(np.floor(u / 5), np.floor(v / 5), seed + 1) + 0.5 * hash2(np.floor(u / 2), np.floor(v / 2), seed + 2)
        leaf = (n > 0.75) & ((np.floor(v / 30) % 2) == 0) | (n > 1.05)
        rgb[leaf] = (C("4a8a2a") * (0.8 + 0.4 * hash2(np.floor(u), np.floor(v), seed + 3))[..., None])[leaf]
        return rgb, nores(u.shape), None
    return fn


def melon(T, s, f, kind="water", sc=1.0):
    if kind == "water":
        def fn(wx, wy, wz, *_):
            st = np.sin((wx - wy) * 1.3 / sc) > 0.2
            return np.where(st[..., None], C("2a5a1a"), C("5a9a3a")) * np.ones(wx.shape + (3,)), nores(wx.shape), None
        _ball(T, s, f, 4 * sc, 6 * sc, 6 * sc, 4.5 * sc, fn)
    else:
        def fn(wx, wy, wz, *_):
            n = hash2(np.floor(wx), np.floor(wy + wz), 7)
            return C("e8c850") * (0.85 + 0.25 * n)[..., None], nores(wx.shape), None
        _ball(T, s, f, 3.4 * sc, 6 * sc, 4 * sc, 3.6 * sc, fn)


def _reed_roof(along, across, maxacross):
    rgb = C("c8a868") * (0.82 + 0.3 * hash2(np.floor(along / 1.5), np.floor(across / 6), 5))[..., None]
    return rgb, nores(along.shape), None


def melon_field(L, o):
    """A bakhcha: melon and watermelon vines, a raised wooden shelter on stilts with a reed roof,
    a pile of melons for sale, scales and a cart."""
    cv = Canvas(2, 90)
    T = Orient(cv, o)
    ground(T, 0, 0, 320, 320, _vines(51))
    ground(T, 120, 0, 200, 110, kit.gravel("b89a70", 52), 0.4)
    rng = np.random.default_rng(53)
    for k in range(22 + L * 8):
        s, f = rng.uniform(14, 306), rng.uniform(130, 306)
        melon(T, s, f, "water" if k % 3 else "melon", rng.uniform(0.8, 1.15))
    for k in range(6):
        s, f = rng.uniform(14, 110), rng.uniform(20, 120)
        melon(T, s, f, "water" if k % 2 else "melon", rng.uniform(0.8, 1.1))
    # raised shelter (supa) on stilts: platform, carpet, reed roof
    s0, f0, s1, f1 = 210, 30, 300, 100
    for s, f in ((s0 + 4, f0 + 4), (s1 - 4, f0 + 4), (s0 + 4, f1 - 4), (s1 - 4, f1 - 4)):
        post(T, s, f, 0, 52, "6a4a2a", 2.4)
    T.box(s0, f0, s1, f1, 18, 22, all=flat("8a6a44", 3), top=flat("a8825a", 4))
    T.box(s0 + 10, f0 + 10, s1 - 10, f1 - 10, 22, 23, all=flat("a8202a", 2), top=lambda u, v, LL, D: (
        np.where(((u < 4) | (v < 4) | (u > LL - 4) | (v > D - 4))[..., None], C("e8b84a"), C("a8202a")) * np.ones(u.shape + (3,)), nores(u.shape), None))
    T.box(s0 + 30, f0 + 30, s1 - 30, f1 - 30, 23, 27, all=flat("6a4428", 2), top=flat("8a5a34", 3))
    _cyl(T, (s0 + s1) / 2, (f0 + f1) / 2, 3, 27, 32, "e8e4dc", "c8c0b0")
    T.gable(s0 - 6, f0 - 6, s1 + 6, f1 + 6, 52, 16, _reed_roof, dict(all=flat("8a6a44", 3)), ridge="s", o=2)
    # ladder
    for k in range(4):
        T.box(s0 - 10, f0 + 20, s0 - 2, f0 + 22, k * 5 + 2, k * 5 + 3, all=flat("6a4a2a", 2), top=flat("6a4a2a", 2))
    # stall: a heap of melons on straw, scales
    T.box(130, 20, 190, 60, 0, 3, all=flat("c8a858", 3), top=flat("d8b860", 6))
    for i, (s, f) in enumerate(((140, 30), (152, 30), (164, 30), (176, 30), (146, 42), (160, 42), (172, 42), (154, 36), (168, 36))):
        melon(T, s, f, "water" if i % 3 else "melon", 0.85)
    T.box(196, 10, 206, 20, 0, 12, all=flat("4a5a6a", 2), top=flat("c8ccd0", 2))
    door(T, 150, 20, 20, 1)
    entry(T, 160)
    # cart
    T.box(60, 20, 104, 44, 8, 18, all=flat("8a5a34", 3), top=flat("6a4428", 3))
    for f in (18, 46):
        T.box(76, f - 1, 88, f + 1, 0, 12, all=flat("3a2a1a", 2), top=flat("3a2a1a", 2))
    for k in range(3 + L):
        melon(T, 68 + k * 9, 32, "water", 0.8)
    if L >= 2:
        tree(T, 20, 20, "poplar", 0.8, 54)
    if L >= 3:
        tree(T, 40, 14, "poplar", 0.75, 55)
    return cv


# --------------------------------------------------------------------------- vineyard
def _grape_leaves(seed):
    def fn(u, v, *_):
        n = hash2(np.floor(u / 2), np.floor(v / 2), seed)
        rgb = C("4a8a2a") * (0.75 + 0.45 * n)[..., None]
        return rgb, nores(u.shape), None
    return fn


def vineyard(L, o):
    """Rows of vines on wire trellises with hanging grapes, a stone press house with an arched door and barrels."""
    cv = Canvas(2, 110)
    T = Orient(cv, o)
    ground(T, 0, 0, 320, 320, kit.soil_rows("u", "8a6a44", "6a9a3a", 40.0, 61, 0.2))
    ground(T, 0, 0, 320, 120, kit.lawn_stripes(62), 0.4)
    grape = "5a2a6a" if L != 2 else "8aa83a"
    leaves = _grape_leaves(63)
    rows = 6 if L < 3 else 7
    for i in range(rows):
        s = 20 + i * 44
        if s > 300:
            break
        for f in (140, 220, 300):
            post(T, s, f, 0, 26, "7a5a3a", 1.4)
        T.box(s - 5, 140, s + 5, 300, 12, 26, all=leaves, top=leaves)
        rng = np.random.default_rng(i)
        for f in rng.uniform(146, 296, 9):
            side = rng.choice([-1, 1])
            _ball(T, s + side * 6, f, 12, 2.2, 2.2, 3.4, _solid3(grape))
    # press house: stone walls, tiled roof, arched wooden door
    st = facade("stone", "d8c8a8", doors=[(36, 28, 30, "double", "6a3a1a")],
                win=Win(w=10, h=12, sill=12, sp=40, margin=14, fh=40, frame="6a3a1a", shutters="6a3a1a"), plinth=("8a7a6a", 5), seed=921)
    sd = facade("stone", "d8c8a8", win=Win(w=10, h=12, sill=12, sp=34, margin=14, fh=40, frame="6a3a1a", shutters="6a3a1a"), seed=922)
    box(T, 40, 20, 140, 96, 0, 36, front=st, back=sd, left=sd, right=sd)
    T.gable(40, 20, 140, 96, 36, 22, roof_mat("b8583a", "tiles"), dict(all=sd), ridge="s", o=4)
    door(T, 76, 28, 20, 30)
    entry(T, 90)
    # arch over the door
    for k in range(7):
        a = math.pi * k / 6
        T.box(90 - 17 * math.cos(a) - 2, 18, 90 - 17 * math.cos(a) + 2, 20, 30 + 6 * math.sin(a), 33 + 6 * math.sin(a),
              all=flat("b8a888", 2), top=flat("b8a888", 2))
    # barrels
    for k in range(3 + L):
        _cyl(T, 160 + (k % 3) * 18, 30 + (k // 3) * 18, 7, 0, 16, "8a5a34", "6a4428")
        _cyl(T, 160 + (k % 3) * 18, 30 + (k // 3) * 18, 7.4, 3, 5, "3a3a40")
        _cyl(T, 160 + (k % 3) * 18, 30 + (k // 3) * 18, 7.4, 11, 13, "3a3a40")
    crates(T, 230, 40, 4, 64)
    # pergola with vines over a table
    for s, f in ((240, 70), (300, 70), (240, 110), (300, 110)):
        post(T, s, f, 0, 34, "7a5a3a", 1.6)
    T.box(236, 66, 304, 114, 34, 37, all=leaves, top=leaves)
    T.box(255, 82, 285, 98, 9, 11, all=flat("8a6a44", 2), top=flat("a8825a", 3))
    if L >= 2:
        tree(T, 20, 40, "poplar", 0.8, 65)
    if L >= 3:
        tractor(T, 200, 90, "s")
    return cv


# --------------------------------------------------------------------------- windmill
def windmill(L, o):
    """A white stone windmill with a dark cap and four lattice sails, flour sacks, a cart and a wheat field."""
    cv = Canvas(2, 200)
    T = Orient(cv, o)
    ground(T, 0, 0, 320, 320, kit.soil_rows("v", "8a6a3a", "d8b850", 9.0, 71, 0.7))
    ground(T, 60, 0, 260, 240, kit.gravel("b8a888", 72), 0.4)
    cs, cf = 160, 160
    # tapering tower
    n = 12
    for k in range(n):
        r = 46 - k * 1.6
        _cyl(T, cs, cf, r, k * 10, k * 10 + 10.5, "efeae0", noise=5)
    _cyl(T, cs, cf, 48, 0, 8, "8a7a6a")
    _cyl(T, cs, cf, 30, 118, 122, "4a3a2a")
    _ball(T, cs, cf, 120, 30, 30, 24, lambda wx, wy, wz, *_: (
        C("4a4e56") * (0.85 + 0.2 * ((np.floor(wz / 4) % 2) == 0))[..., None], nores(wx.shape), None))
    # door and windows (dark slits) on the front of the tower
    T.box(cs - 10, cf - 48, cs + 10, cf - 44, 0, 24, all=flat("6a4428", 2), top=flat("6a4428", 2))
    door(T, cs - 10, 20, cf - 48, 24)
    entry(T, cs)
    for z in (50, 84):
        T.box(cs - 4, cf - 46 + z * 0.16, cs + 4, cf - 42 + z * 0.16, z, z + 10, all=flat("2a2a2e", 1), top=flat("2a2a2e", 1))
    # sails on the front: an X of lattice blades on one side of each spar
    hub_z, R, f_s = 112, 92, cf - 36
    _ball(T, cs, f_s - 2, hub_z, 6, 6, 6, _solid3("3a2a1a"))

    def sail_mask(u, v):
        dx, dy = u - R, v - R
        p, q = (dx + dy) / 1.4142, (dx - dy) / 1.4142
        rr = np.hypot(dx, dy)
        spar = ((np.abs(q) < 1.6) | (np.abs(p) < 1.6)) & (rr < R)
        b1 = (p > 14) & (np.sign(p) * q > 0) & (np.abs(q) < 15) & (rr < R - 2)
        b3 = (p < -14) & (q < 0) & (np.abs(q) < 15) & (rr < R - 2)
        b4 = (q < -14) & (p > 0) & (np.abs(p) < 15) & (rr < R - 2)
        b2 = (q > 14) & (p < 0) & (np.abs(p) < 15) & (rr < R - 2)
        return spar | b1 | b2 | b3 | b4

    def sail(u, v, LL, H):
        dx, dy = u - R, v - R
        p, q = (dx + dy) / 1.4142, (dx - dy) / 1.4142
        lat = ((np.abs(p) % 7) < 1.0) | ((np.abs(q) % 7) < 1.0) | (np.abs(q) < 1.6) | (np.abs(p) < 1.6)
        rgb = np.where(lat[..., None], C("5a3a24"), C("f2ead8")) * np.ones(u.shape + (3,))
        return rgb, nores(u.shape), None
    T.panel(cs - R, cs + R, f_s, hub_z - R, hub_z + R, sail, "s", extra=sail_mask)
    # flour sacks and a cart
    for k in range(4 + L):
        _ball(T, 90 + (k % 4) * 12, 60 + (k // 4) * 12, 5, 5.5, 4.5, 5, _solid3("efe8d8"))
    T.box(200, 40, 250, 66, 8, 18, all=flat("8a5a34", 3), top=flat("6a4428", 3))
    T.box(218, 38, 232, 68, 0, 12, all=flat("3a2a1a", 2), top=flat("3a2a1a", 2))
    for k in range(3):
        hay(T, 270 + (k % 2) * 16, 260 + k * 14)
    if L >= 2:
        tree(T, 30, 40, "oak", 0.8, 73)
    if L >= 3:
        fence(T, 6, 314, 6, "f", "8a6a48", "rail", 9)
        lamp(T, 120, 20, "lantern", 40)
    return cv


# --------------------------------------------------------------------------- fish farm
def fish_farm(L, o):
    """Two fish ponds with floating net cages, a wooden walkway, a feeder, a hut and a rowing boat."""
    cv = Canvas(2, 90)
    T = Orient(cv, o)
    ground(T, 0, 0, 320, 320, kit.lawn_stripes(81))
    ponds = [(14, 110, 152, 306), (168, 110, 306, 306)]
    for s0, f0, s1, f1 in ponds:
        x0, y0, x1, y1 = T.rect(s0, f0, s1, f1)
        kit.pool(cv, x0, y0, x1, y1)
    # walkway between the ponds and along the front
    T.box(150, 110, 170, 308, 0, 3, all=flat("8a6a44", 2), top=lambda u, v, LL, D: (
        C("a8825a") * (0.85 + 0.2 * ((np.floor((u + v) / 4) % 2) == 0))[..., None], nores(u.shape), None))
    T.box(14, 100, 306, 112, 0, 3, all=flat("8a6a44", 2), top=flat("a8825a", 4))
    # net cages: dark rings with nets
    net = lambda a, b: (np.where((((a % 3) < 0.5) | ((b % 3) < 0.5))[..., None], C("c8ccd0"), C("2a4a5a")) *
                        np.ones(a.shape + (3,)), nores(a.shape), None)
    cages = [(50, 160), (110, 160), (50, 250), (110, 250), (210, 200), (270, 200)]
    for k, (s, f) in enumerate(cages[: 4 + L]):
        x, y = T.pt(s, f)
        cv.cylinder(x, y, 18, 0.5, 3, lambda a, v, nx, ny: solid_res(C("e8a020"), a.shape), net)
        for d in (-18, 18):
            post(T, s + d, f, 0, 7, "e8e4dc", 0.8)
    # feeder on a stand by the walkway
    post(T, 160, 200, 0, 20, "8a8e94", 1.4)
    _cyl(T, 160, 200, 7, 20, 32, "e8e4dc", "6a9a3a")
    # hut
    hut = facade("wood", "6a8aa8", doors=[(12, 14, 20, "wood", "4a3a2a")], win=Win(w=10, h=10, sill=10, sp=30, margin=34, fh=30), plinth=None, seed=931)
    box(T, 20, 20, 90, 80, 0, 26, all=hut)
    T.gable(20, 20, 90, 80, 26, 16, roof_mat("4a4e56", "metal"), dict(all=hut), ridge="s", o=3)
    door(T, 32, 14, 20, 20)
    entry(T, 39)
    # boat at the jetty
    _ball(T, 240, 280, 1.5, 14, 6, 3, _solid3("c8582a"))
    crates(T, 110, 30, 3 + L, 82)
    for k in range(2):
        _cyl(T, 200 + k * 18, 40, 7, 0, 14, "4a8ad0", "3a6ab0")
    if L >= 2:
        tree(T, 300, 40, "oak", 0.8, 83)
    if L >= 3:
        lamp(T, 160, 104, "lantern", 36)
    return cv


# --------------------------------------------------------------------------- dairy
def dairy(L, o):
    """A big modern dairy: an open-sided cow barn with a green roof, a milking parlour, steel milk tanks,
    feed silos, a milk tanker and cows in the paddock."""
    cv = Canvas(3, 150)
    T = Orient(cv, o)
    ground(T, 0, 0, 480, 480, kit.lawn_stripes(91))
    ground(T, 0, 0, 480, 120, kit.asphalt_lot("6a6c70", 92), 0.4)
    ground(T, 20, 300, 460, 470, kit.paving("8a9a50", 30.0, 93, 0.0), 0.4)
    # open cow barn: low white wall, dark open band, posts, big gable roof
    s0, f0, s1, f1 = 30, 150, 330, 290
    T.box(s0, f0, s1, f1, 0, 12, all=flat("f2eee6", 3), top=flat("e8e4dc", 2))
    T.box(s0 + 2, f0 + 2, s1 - 2, f1 - 2, 12, 34, all=lambda u, v, LL, H: (
        np.where(((u % 30) < 2)[..., None], C("e8e4dc"), C("3a3430")) * np.ones(u.shape + (3,)), nores(u.shape), None), top=flat("3a3430"))
    for k in range(5):
        _ball(T, s0 + 40 + k * 55, f0 - 1, 22, 6, 1, 4, _solid3(["2a2a2a", "f4f0ea", "8a5a34", "2a2a2a", "f4f0ea"][k]))
    T.gable(s0 - 6, f0 - 6, s1 + 6, f1 + 6, 34, 36, roof_mat("3a7a4a", "metal"), dict(all=flat("f2eee6", 3)), ridge="s", o=1)
    T.box(s0 + 20, (f0 + f1) / 2 - 10, s1 - 20, (f0 + f1) / 2 + 10, 70, 74, all=flat("e8ecf0", 2), top=flat("c8ccd0", 2))
    # milking parlour with the main door and a sign
    par = facade("concrete", "f2eee6", doors=[(34, 30, 28, "glass")], win=Win(w=16, h=12, sill=12, sp=36, margin=12, fh=40, frame="3a7a4a"),
                 plinth=("3a7a4a", 5), seed=941, bands=[(34, 40, "3a7a4a")])
    box(T, 340, 140, 450, 230, 0, 40, all=par, top=flat_top("7a7a80", "3a7a4a", 3))
    door(T, 374, 30, 140, 28)
    entry(T, 389)
    sign_board(T, 395, 140, 40, "MILK", 9, "3a7a4a", "f6f2ea")
    # milk tanks
    for k in range(2 + (L >= 2)):
        _cyl(T, 360 + k * 36, 100, 13, 0, 46, "d8dce0", "b8bcc0", noise=2)
        _ball(T, 360 + k * 36, 100, 46, 13, 13, 6, _solid3("c8ccd0"))
    silo(T, 40, 100, 16, 90, "6a9a7a")
    silo(T, 80, 90, 14, 80, "6a9a7a")
    # milk tanker: white cab and a steel tank
    T.box(150, 40, 260, 66, 6, 30, all=flat("e0e4e8", 2), top=flat("c8ccd0", 2))
    T.box(262, 40, 296, 66, 6, 30, all=flat("f2eee6", 2), top=flat("e8e4dc", 2))
    T.box(286, 41, 297, 65, 18, 28, all=flat("3a4a5a", 2), top=flat("e8e4dc", 2))
    for s in (170, 230, 280):
        T.box(s - 8, 38, s + 8, 68, 0, 12, all=flat("2a2a2e", 2), top=flat("2a2a2e", 2))
    sign_board(T, 205, 40, 12, "MILK", 8, "e0e4e8", "3a7a4a", glow=False)
    # paddock with cows
    for a0, a1, b, al in ((20, 460, 300, "s"), (20, 460, 470, "s"), (300, 470, 20, "f"), (300, 470, 460, "f")):
        fence(T, a0, a1, b, al, "e8e4dc", "rail", 10)
    for k in range(4 + L * 2):
        cow(T, 60 + (k % 5) * 80, 340 + (k // 5) * 70 + (k % 2) * 20, "s" if k % 2 else "f", seed=k + 9)
    for k in range(2 + L):
        hay(T, 420 + (k % 2) * 16, 250 + (k // 2) * 16)
    if L >= 2:
        tractor(T, 440, 60, "f")
    if L >= 3:
        lamp(T, 320, 20, "modern", 46)
        tree(T, 460, 280, "oak", 0.9, 94)
    return cv


BUILDERS = {"apiary": apiary, "chicken_farm": chicken_farm, "melon_field": melon_field, "vineyard": vineyard,
            "windmill": windmill, "fish_farm": fish_farm, "dairy": dairy}
