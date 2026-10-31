"""Multi-storey car parks, each with its own look: an open concrete deck garage, a slim automated
tower with car racks, a green garage with a planted facade and a solar roof, and a round spiral garage."""
import math
import random

import numpy as np

from raster import C, Canvas, flat, glow_res, hash2
from arch import Orient, facade, flat_top, Win
import kit
from bkit import ground, tree, bush, lamp, bench, box, slab, post, sign_board, pole_sign, entry, door

CAR_COLS = ["c8342a", "2a5aa8", "e8e8ea", "a8acb0", "2a2c30", "3a7a4a", "e8c040", "1e3060", "7a4a2a", "d8d0c0", "8a2a4a"]


def _glow(col, k=200):
    return lambda u, v, L, H: glow_res(col, u.shape, k)


def _car(T, s, f, z, along="f", col="c84a3a"):
    """A parked car standing on a deck at height z."""
    x, y = T.pt(s, f)
    ax = T.axis(along)
    l, w = 44, 18
    body = flat(col, 4)
    glass = flat("3a4a5a", 3)
    if ax == "x":
        T.cv.box(x - l / 2, y - w / 2, z + 1, x + l / 2, y + w / 2, z + 7, body, body, body)
        T.cv.box(x - l / 4, y - w / 2 + 1, z + 7, x + l / 5, y + w / 2 - 1, z + 12, glass, glass, flat(col, 3))
    else:
        T.cv.box(x - w / 2, y - l / 2, z + 1, x + w / 2, y + l / 2, z + 7, body, body, body)
        T.cv.box(x - w / 2 + 1, y - l / 4, z + 7, x + w / 2 - 1, y + l / 5, z + 12, glass, glass, flat(col, 3))


def _row(T, rng, s0, s1, f, z, along="f", step=28, fill=0.7):
    """A row of parked cars side by side (some bays stay empty)."""
    n = int((s1 - s0) // step)
    for k in range(n):
        if rng.random() < fill:
            s = s0 + step / 2 + k * step
            if along == "f":
                _car(T, s, f, z, "f", rng.choice(CAR_COLS))
            else:
                _car(T, f, s, z, "s", rng.choice(CAR_COLS))


def _cyl(T, s, f, r, z0, z1, col, noise=3, cap=None):
    x, y = T.pt(s, f)
    side = flat(col, noise)
    T.cv.cylinder(x, y, r, z0, z1, lambda a, v, nx, ny: side(a * 20, v), cap or (lambda a, b: flat(col, noise)(a, b)))


def _leafy(col="4a8a3a", seed=0):
    """A planted wall: noisy leaves with a few flowers."""
    base = C(col)

    def fn(u, v, *_):
        h = hash2(np.floor(u / 2), np.floor(v / 2), seed)
        rgb = base + ((h - 0.5) * 46)[..., None]
        dark = hash2(np.floor(u / 5), np.floor(v / 4), seed + 1) < 0.25
        rgb[dark] *= 0.72
        fl = hash2(np.floor(u / 2), np.floor(v / 2), seed + 2) > 0.975
        rgb[fl] = C("f0d050")
        return rgb, np.zeros(u.shape, bool), None
    return fn


def _stripes(c1="f0c020", c2="2a2a30", w=6):
    a, b = C(c1), C(c2)

    def fn(u, v, *_):
        m = (np.floor((u + v) / w) % 2) == 0
        rgb = np.where(m[..., None], a, b).astype(float)
        return rgb, np.zeros(u.shape, bool), None
    return fn


def _barrier(T, s, f, col="e83a2a"):
    """A ticket post with a striped barrier arm across the driveway."""
    T.box(s - 4, f - 4, s + 4, f + 4, 0, 16, all=flat("e8eaee", 2), top=flat(col, 2))
    T.box(s - 3, f - 4.5, s + 3, f - 4, 8, 12, all=_glow("f0d060", 170), top=flat("e8eaee"))
    T.box(s + 4, f - 1, s + 48, f + 1, 12, 14, all=_stripes(col, "f6f6f6", 6), top=_stripes(col, "f6f6f6", 6))


def _deck(T, s0, f0, s1, f1, z, slab_col, wall, gap=None, wall_h=8):
    """One open deck: a floor slab, a lit strip under it and a low parapet round the edge.
    gap = (s_a, s_b) leaves an opening in the front parapet (the driveway)."""
    if z > 0:
        slab(T, s0, f0, s1, f1, z - 3, z, slab_col)
        T.box(s0 + 2, f0 - 0.5, s1 - 2, f0, z - 5, z - 3, all=_glow("f4ecd0", 140), top=flat(slab_col))
    t = 3
    fronts = [(s0, s1)] if gap is None else [(s0, gap[0]), (gap[1], s1)]
    for a, b in fronts:
        if b - a > 1:
            T.box(a, f0, b, f0 + t, z, z + wall_h, all=wall, top=flat(slab_col, 2))
    T.box(s0, f1 - t, s1, f1, z, z + wall_h, all=wall, top=flat(slab_col, 2))
    T.box(s0, f0, s0 + t, f1, z, z + wall_h, all=wall, top=flat(slab_col, 2))
    T.box(s1 - t, f0, s1, f1, z, z + wall_h, all=wall, top=flat(slab_col, 2))


# --------------------------------------------------------------------------- open deck garage
def parking_deck(L, o):
    """A concrete multi-storey car park: open decks with blue-striped parapets and cars on every level,
    a glazed stair tower with a big P, a driveway with a barrier and lights under each deck."""
    floors = 2 + L
    fh = 28
    H = floors * fh
    cv = Canvas(2, H + 120)
    T = Orient(cv, o)
    rng = random.Random(1700 + L * 10 + o)
    ground(T, 0, 0, 320, 320, kit.asphalt_lot("55585e", 1701))
    ground(T, 0, 0, 320, 10, kit.paving("c8c2b4", 8.0, 1702), 0.4)
    blue = "2a5aa8"
    wall = facade("concrete", "c8c4bc", plinth=None, bands=[(5, 8, blue)], seed=1703)
    s0, f0, s1, f1 = 18, 34, 252, 302
    for k in range(floors + 1):
        z = k * fh
        _deck(T, s0, f0, s1, f1, z, "bdb8ae", wall, gap=(150, 210) if k == 0 else None)
        if k < floors:
            for ss in (s0 + 4, 135, s1 - 4):
                for ff in (f0 + 4, 168, f1 - 4):
                    post(T, ss, ff, z, z + fh - 3, "d4d0c8", 5)
        # cars along the front and the sides, a row at the back (fewer on the open roof)
        fill = 0.2 + 0.15 * L if k == floors else 0.7
        _row(T, rng, s0 + 6, s0 + 140 if k == 0 else s1 - 6, f0 + 28, z, "f", 28, fill)
        _row(T, rng, f0 + 56, f1 - 56, s0 + 26, z, "s", 28, fill * 0.85)
        _row(T, rng, f0 + 56, f1 - 56, s1 - 26, z, "s", 28, fill * 0.85)
        _row(T, rng, s0 + 40, s1 - 40, f1 - 28, z, "f", 28, fill * 0.85)
    # roof: light masts and a painted P
    rz = floors * fh
    T.box(110, 150, 160, 154, rz + 0.1, rz + 0.6, all=flat("f4f2ea", 1), top=flat("f4f2ea", 1))
    for ss, ff in ((s0 + 10, f0 + 10), (s1 - 10, f1 - 10)):
        lamp(T, ss, ff, "modern", 0)
        post(T, ss, ff, rz, rz + 40, "6a6e74", 2)
        T.box(ss - 5, ff - 2, ss + 5, ff + 2, rz + 38, rz + 42, all=_glow("f4f0d8", 200), top=flat("4a4e54"))
        cv.mark("light%d" % (0 if ss == s0 + 10 else 1), *T.pt(ss, ff), rz + 38)
    # glazed stair tower on the right with the P sign
    tz = H + 22
    stair = facade("glass", "cfe0ea", win=Win(w=36, h=fh - 8, sill=4, sp=40, margin=6, fh=fh, frame="3a4048", style="plain", group="work"),
                   doors=[(14, 14, 22, "glass")], plinth=("3a4048", 4), seed=1704, lit=0.8)
    side = facade("concrete", "d8d4cc", plinth=None, seed=1705)
    box(T, 256, 34, 306, 92, 0, tz, front=stair, back=side, left=side, right=stair, top=flat_top("6a6e74", blue, 2))
    T.box(262, 32, 300, 34, tz - 34, tz - 4, front=facade("plaster", blue, plinth=None, signs=[(19, 4, "P", 22, None, "ffffff", True)]),
          back=flat(blue), left=flat(blue), right=flat(blue), top=flat(blue))
    door(T, 270, 14, 34, 22)
    # driveway: IN sign over the opening, barrier and a booth
    sign_board(T, 180, f0, fh - 14, "IN", 8, blue, "ffffff")
    _barrier(T, 152, 22)
    box(T, 214, 12, 238, 30, 0, 22, all=facade("plaster", "f2f2f0", win=Win(w=12, h=10, sill=10, sp=18, margin=4, fh=22, frame="3a3a40", group="work"), plinth=None, seed=1706),
        top=flat(blue, 2))
    if L >= 2:
        for k, ss in enumerate((30, 110)):
            tree(T, ss, 16, "lime", 0.55, 1707 + k)
    if L >= 3:
        bench(T, 60, 18, "s")
        lamp(T, 246, 8, "modern", 46, "light2")
    entry(T, 180)
    return cv


# --------------------------------------------------------------------------- automated tower
def parking_tower(L, o):
    """A slim automated parking tower: a steel frame with cars stacked on racks, an orange lift cabin
    in the middle, perforated side panels, a turntable bay at the bottom and a glowing AUTO P crown."""
    levels = 4 + 2 * L
    lh = 22
    H = 30 + levels * lh
    cv = Canvas(1, H + 110)
    T = Orient(cv, o)
    rng = random.Random(1800 + L * 10 + o)
    ground(T, 0, 0, 160, 160, kit.paving("d0d2d4", 8.0, 1801))
    ground(T, 22, 0, 138, 30, kit.asphalt_lot("4e5258", 1802), 0.4)
    steel, orange = "3a4048", "f08a20"
    s0, f0, s1, f1 = 22, 30, 138, 146
    # entry bay: dark portal, turntable, lit edge
    panel = facade("metal", "8a929a", plinth=None, bands=[(v, v + 1.5, "6a727a") for v in range(6, int(H), 10)], seed=1803)
    box(T, s0, f0, s1, f1, 0, 30, front=facade("plaster", "e8eaec", plinth=("3a4048", 3), decals=[(34, 82, 0, 24, "2a2c30")], seed=1804),
        back=panel, left=panel, right=panel, top=flat("5a6066", 2))
    _cyl(T, 80, 14, 16, 0.4, 1.4, "3a3c42", 2, lambda a, b: flat("3a3c42", 2)(a, b))
    T.box(58, 0, 102, 2, 0.4, 1.6, all=_stripes(), top=_stripes())
    T.box(56, f0 - 0.5, 104, f0, 24, 26, all=_glow("f0a040", 200), top=flat(steel))
    # racks with cars, a lift shaft in the middle
    for k in range(levels):
        z = 30 + k * lh
        T.box(s0, f0, s1, f1, z, z + 2, all=flat("7a8088", 2), top=flat("8a9098", 3))
        T.box(s0, f0 - 1, s1, f0, z, z + 2, all=flat(orange, 2), top=flat(orange, 2))
        for ss in (48, 112):
            if rng.random() < 0.85:
                _car(T, ss, f0 + 13, z + 1, "s", rng.choice(CAR_COLS))
    T.box(72, f0 + 8, 88, f1, 30, H, all=flat("5a6066", 3), top=flat(steel))
    cab = 30 + (levels // 2) * lh
    T.box(70, f0 + 4, 90, f0 + 40, cab + 2, cab + lh - 2, all=flat(orange, 3), top=flat(orange, 2))
    T.box(70, f0 + 3.5, 90, f0 + 4, cab + 8, cab + 11, all=_glow("f8f0c0", 200), top=flat(orange))
    # back panels and frame
    box(T, s0, f1 - 10, s1, f1, 30, H, all=panel, top=flat(steel))
    for ss in (s0 + 2, s1 - 2):
        for ff in (f0 + 2, f1 - 2):
            post(T, ss, ff, 0, H + 4, steel, 5)
    for k in range(0, levels + 1, 2):
        z = 30 + k * lh
        T.box(s0, f0, s0 + 2, f1, z + 2, z + 4, all=flat(steel, 2), top=flat(steel, 2))
        T.box(s1 - 2, f0, s1, f1, z + 2, z + 4, all=flat(steel, 2), top=flat(steel, 2))
    # crown with the sign
    T.box(s0 - 2, f0 - 2, s1 + 2, f1 + 2, H, H + 14, front=facade("plaster", "1e2228", plinth=None, signs=[(58, 2, "AUTO P", 10, None, "7ad0f8", True)]),
          back=flat("1e2228"), left=flat("1e2228"), right=flat("1e2228"), top=flat_top("4a5058", orange, 2))
    cv.mark("light", *T.pt(80, 20), 24)
    # pedestrian door and ticket machine
    door(T, 112, 12, f0, 20)
    T.box(124, 18, 132, 24, 0, 16, all=flat("e8eaee", 2), top=flat(orange, 2))
    T.box(124, 17.5, 132, 18, 8, 13, all=_glow("7ad0f8", 180), top=flat("e8eaee"))
    if L >= 2:
        bush(T, 10, 20, 0.5, 1805, None)
        bush(T, 150, 20, 0.5, 1806, None)
    if L >= 3:
        lamp(T, 8, 6, "modern", 44, "light1")
    entry(T, 80)
    return cv


# --------------------------------------------------------------------------- green garage
def parking_green(L, o):
    """An eco garage: decks behind planted parapets with hanging greenery, timber slats, EV bays at the
    bottom, solar panels and a roof garden with trees."""
    floors = 1 + L
    fh = 28
    H = floors * fh
    cv = Canvas(2, H + 130)
    T = Orient(cv, o)
    rng = random.Random(1900 + L * 10 + o)
    ground(T, 0, 0, 320, 320, kit.paving("cfd2c6", 8.0, 1901))
    ground(T, 120, 0, 200, 30, kit.asphalt_lot("4e545a", 1902), 0.4)
    green, wood = "4a8a3a", "a8804c"
    s0, f0, s1, f1 = 16, 30, 304, 296
    planter = facade("wood", wood, plinth=None, bands=[(0, 2, "6a5030")], seed=1903)
    for k in range(floors + 1):
        z = k * fh
        _deck(T, s0, f0, s1, f1, z, "c8c4b8", planter, gap=(130, 190) if k == 0 else None, wall_h=7)
        if k > 0:
            # hedges on the parapet and greenery hanging down the slab edge
            for a, b in ((s0, s1),):
                T.box(a, f0, b, f0 + 4, z + 7, z + 11, all=_leafy(green, 1904 + k), top=_leafy(green, 1905 + k))
            T.box(s0, f0, s0 + 4, f1, z + 7, z + 11, all=_leafy(green, 1906 + k), top=_leafy(green, 1907 + k))
            T.box(s1 - 4, f0, s1, f1, z + 7, z + 11, all=_leafy(green, 1908 + k), top=_leafy(green, 1909 + k))
            for j in range(10):
                ss = s0 + 12 + j * 29 + rng.uniform(-4, 4)
                drop = rng.uniform(6, 14)
                T.box(ss, f0 - 1, ss + rng.uniform(6, 12), f0, z - 3 - drop, z, all=_leafy("3a7a32", 1910 + j), top=_leafy(green))
        if k < floors:
            for ss in range(s0 + 4, s1, 48):
                T.box(ss - 1.5, f0 + 2, ss + 1.5, f0 + 5, z, z + fh - 3, all=flat(wood, 3), top=flat(wood, 3))
            for ss in (s0 + 4, 160, s1 - 4):
                for ff in (f0 + 4, 163, f1 - 4):
                    post(T, ss, ff, z, z + fh - 3, "e0dcd0", 5)
            _row(T, rng, s0 + 6, 126 if k == 0 else s1 - 6, f0 + 28, z, "f", 28, 0.7)
            _row(T, rng, f0 + 56, f1 - 56, s0 + 26, z, "s", 28, 0.6)
            _row(T, rng, f0 + 56, f1 - 56, s1 - 26, z, "s", 28, 0.6)
            _row(T, rng, s0 + 40, s1 - 40, f1 - 28, z, "f", 28, 0.6)
    # green EV bays at the bottom, by the front
    for k in range(3):
        ground(T, 200 + k * 30, 40, 226 + k * 30, 84, flat("3a8a5a", 3), 0.6)
        T.box(206 + k * 30, 86, 214 + k * 30, 90, 0, 16, all=flat("f4f6f4", 2), top=flat("2ab86a", 2))
        T.box(206 + k * 30, 85.5, 214 + k * 30, 86, 8, 13, all=_glow("7af0a8", 180), top=flat("f4f6f4"))
    # roof: solar canopy on one half, a garden with trees on the other
    rz = H
    for ss in (s0 + 10, 150):
        for ff in (f0 + 10, f1 - 10):
            post(T, ss, ff, rz, rz + 22, "8a6a44", 2.6)
    slab(T, s0 + 6, f0 + 6, 156, f1 - 6, rz + 22, rz + 24, wood, flat("8a6a44", 3))
    x0, y0, x1, y1 = T.rect(s0 + 10, f0 + 10, 152, f1 - 10)
    kit.solar(cv, x0, y0, x1, y1, rz + 24, 4)
    ground(T, 170, f0 + 8, s1 - 8, f1 - 8, flat("5a9a42", 10), rz + 0.6)
    for j, (ss, ff) in enumerate(((200, 80), (270, 120), (220, 200), (280, 250))[: 2 + L - 1]):
        x, y = T.pt(ss, ff)
        kit.tree(cv, x, y, "lime", 0.6, 1920 + j, None, rz + 0.6)
    for j, (ss, ff) in enumerate(((180, 140), (250, 170), (190, 260))):
        x, y = T.pt(ss, ff)
        kit.crown(cv, x, y, rz + 0.6, 8, 10, "hedge", 1930 + j, 4, None)
    # stair kiosk with the sign
    kio = facade("glass", "dfeee6", doors=[(10, 14, 22, "glass")], plinth=("4a4e4a", 3), seed=1911, lit=1.0)
    kside = facade("wood", wood, seed=1912)
    box(T, 40, 4, 90, 30, 0, 30, front=kio, back=kside, left=kside, right=kside, top=flat_top("6a6e6a", "2ab86a", 2))
    door(T, 50, 14, 4, 22)
    pole_sign(T, 112, 8, 64, "P", 14, "2ab86a", "ffffff")
    sign_board(T, 160, f0, fh - 14, "ECO PARK", 7, "2ab86a", "ffffff")
    _barrier(T, 134, 20, "2ab86a")
    if L >= 2:
        bush(T, 10, 12, 0.6, 1913, "f0d050")
        bush(T, 300, 12, 0.6, 1914, "e86a8a")
    if L >= 3:
        tree(T, 230, 14, "birch", 0.55, 1915)
        bench(T, 280, 16, "s")
    entry(T, 160)
    return cv


# --------------------------------------------------------------------------- spiral garage
def parking_spiral(L, o):
    """A round garage: stacked circular decks with cars round the edge, a white core with glass bands,
    a red-and-white spiral ramp winding up the outside and a big round P sign on the roof."""
    decks = 2 + L
    dh = 26
    H = decks * dh
    cv = Canvas(2, H + 150)
    T = Orient(cv, o)
    rng = random.Random(2000 + L * 10 + o)
    ground(T, 0, 0, 320, 320, kit.asphalt_lot("55585e", 2001))
    ground(T, 0, 0, 320, 10, kit.paving("c8c2b4", 8.0, 2002), 0.4)
    cx, cf = 160, 176
    R = 112
    red = "d83a2a"
    for k in range(decks + 1):
        z = k * dh
        if k > 0:
            _cyl(T, cx, cf, R, z - 3, z, "c8c4bc", 3)
            _cyl(T, cx, cf, R + 0.5, z - 5, z - 3, "f4ecd0", 0, lambda a, b: flat("c8c4bc")(a, b))
        # parapet ring: low enough that the cars show above it
        _cyl(T, cx, cf, R - 0.5, z, z + 6, red if k % 2 else "f2f0ec", 2, lambda a, b: flat("bdb8ae", 3)(a, b))
        if k == decks and L < 3:
            break
        for j in range(12):
            if rng.random() > 0.75:
                continue
            a = j * math.pi / 6 + 0.26
            r = R - 22
            ss, ff = cx + r * math.cos(a), cf + r * math.sin(a)
            if k == 0 and ff < cf - 60 and abs(ss - cx) < 40:
                continue
            along = "f" if abs(math.cos(a)) > abs(math.sin(a)) else "s"
            _car(T, ss, ff, z + 6, along, rng.choice(CAR_COLS))
        if k < decks:
            for j in range(6):
                a = j * math.pi / 3
                post(T, cx + (R - 8) * math.cos(a), cf + (R - 8) * math.sin(a), z, z + dh - 3, "d4d0c8", 5)
    # core: white with glass bands
    core = flat("f2f0ec", 2)
    glass = flat("8ab8d0", 3)

    def core_side(a, v, nx, ny):
        band = (np.floor(v / 13) % 2) == 1
        rgb_w, m, _ = core(a * 30, v)
        rgb_g, _, _ = glass(a * 30, v)
        return np.where(band[..., None], rgb_g, rgb_w), m, None
    x, y = T.pt(cx, cf)
    T.cv.cylinder(x, y, 34, 0, H + 20, core_side, lambda a, b: flat("6a6e74", 2)(a, b))
    # spiral ramp outside the decks
    n = 72
    for i in range(n * decks):
        a = -math.pi / 2 + i * 2 * math.pi / n
        z = i * dh / n
        ss, ff = cx + (R + 9) * math.cos(a), cf + (R + 9) * math.sin(a)
        col = red if (i // 6) % 2 == 0 else "f2f0ec"
        T.box(ss - 8, ff - 8, ss + 8, ff + 8, z, z + 2.5, all=flat(col, 2), top=flat("6a6c72", 3))
        if i % 4 == 0:
            ss, ff = cx + (R + 17) * math.cos(a), cf + (R + 17) * math.sin(a)
            T.box(ss - 1.5, ff - 1.5, ss + 1.5, ff + 1.5, z + 2.5, z + 8, all=flat("e8e6e2", 2), top=flat(red, 2))
    # the round P sign on a mast
    post(T, cx, cf, H + 20, H + 62, "4a4e54", 3)
    pfn = facade("plaster", "2a5aa8", plinth=None, signs=[(16, 4, "P", 22, None, "ffffff", True)])
    T.box(cx - 16, cf - 2, cx + 16, cf + 2, H + 34, H + 64, front=pfn, back=pfn, left=flat("2a5aa8"), right=flat("2a5aa8"), top=flat("2a5aa8"))
    cv.mark("light", *T.pt(cx, cf), H + 34)
    # driveway with a barrier, a pay kiosk and a door
    ground(T, 130, 0, 190, 70, kit.asphalt_lot("4a4c52", 2003), 0.5)
    _barrier(T, 132, 30)
    kio = facade("glass", "dfe6ee", doors=[(8, 14, 22, "glass")], plinth=("3a4048", 3), seed=2004, lit=1.0)
    box(T, 214, 12, 256, 40, 0, 26, front=kio, back=flat("e8eaee"), left=flat("e8eaee"), right=flat("e8eaee"), top=flat_top("6a6e74", red, 2))
    door(T, 222, 14, 12, 22)
    sign_board(T, 235, 12, 26, "PARK", 6, red, "ffffff")
    if L >= 2:
        tree(T, 24, 24, "lime", 0.55, 2005)
        tree(T, 296, 24, "lime", 0.55, 2006)
    if L >= 3:
        lamp(T, 100, 8, "modern", 46, "light1")
        lamp(T, 280, 60, "modern", 46, "light2")
    entry(T, 160)
    return cv


BUILDERS = {"parking_deck": parking_deck, "parking_tower": parking_tower, "parking_green": parking_green, "parking_spiral": parking_spiral}
