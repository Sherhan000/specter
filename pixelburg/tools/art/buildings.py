"""All 35 Pixelburg buildings, each in three upgrade levels (plus scaffolds)."""
import math

import numpy as np

from raster import C, Canvas, flat, hash2, U
from props import (wall, roof_tiles, flat_roof, lot, tree, bush, lamp_post, fence, ac_unit, solar,
                   water_tank, umbrella_table, bench, flower_patch, nores, solid_res, leaf_fn, trunk_fn,
                   LEAF_GREEN, grass_fn, paving, hedge, mailbox, dormer)
import units

T = U  # one tile in world units


# ====================================================================== helpers
def building(cv, x0, y0, x1, y1, h, left, right=None, roof=("flat", "8a8a8a", "c8c0b0"), end=None, z0=0):
    right = right or left
    kind = roof[0]
    # remember the main door (on the visible +y face) so residents can walk in and out
    for d in getattr(left, "doors", []) or []:
        if z0 == 0 and "door_a" not in cv.points:
            u0, w, dh = d[0], d[1], d[2]
            cv.mark("door_a", x0 + u0, y1, 0)
            cv.mark("door_b", x0 + u0 + w, y1, 0)
            cv.mark("door_t", x0 + u0, y1, dh)
    if kind == "flat":
        cv.box(x0, y0, z0, x1, y1, z0 + h, left, right, flat_roof(roof[1], roof[2]))
    else:
        cv.box(x0, y0, z0, x1, y1, z0 + h, left, right, flat("6a6a6a"))
        if kind == "gable":
            _, col, axis, rh = roof[:4]
            style = roof[4] if len(roof) > 4 else "tiles"
            endw = end or (right if axis == "x" else left)
            cv.gable(x0, y0, x1, y1, z0 + h, rh, roof_tiles(col, kind=style), endw, axis, 3)
        elif kind == "hip":
            cv.hip(x0, y0, x1, y1, z0 + h, roof[2], roof_tiles(roof[1], kind=roof[3] if len(roof) > 3 else "tiles"))


def chimney(cv, x, y, z, h=12, name=None, col="9a5a44"):
    c = wall(col, style=dict(brick=0.82, plinth=None), windows=False)
    cv.box(x, y, z, x + 6, y + 6, z + h, c, c, flat("2a2222"))
    cv.box(x - 1, y - 1, z + h - 2, x + 7, y + 7, z + h, flat(col), flat(col), flat("2a2222"))
    if name:
        cv.mark(name, x + 3, y + 3, z + h)


def steps(cv, x0, x1, y, n=2):
    st = flat("c8c0b0", 4)
    for i in range(n):
        cv.box(x0, y + i * 2, 0, x1, y + i * 2 + 2, (n - i) * 1.6, st, st, st)


def awning(cv, x0, x1, y, z, depth, drop, c1, c2="f8f4ec", w=4):
    k = drop / depth
    a, b = C(c1), C(c2)

    def fn(wx, wy, wz):
        rgb = np.where(((np.floor((wx - x0) / w) % 2) == 0)[..., None], a, b) * np.ones(wx.shape + (3,))
        edge = wy > y + depth - 1.5
        rgb[edge] *= 0.85
        return rgb, nores(wx.shape), None
    cv.plane(z + k * y, 0, -k, (x0, y, z - drop, x1, y + depth, z),
             lambda wx, wy: (wx >= x0) & (wx < x1) & (wy >= y) & (wy < y + depth), fn)
    # scalloped valance
    def val(u, v, L, H):
        rgb = np.where(((np.floor(u / w) % 2) == 0)[..., None], a, b) * np.ones(u.shape + (3,))
        return rgb, nores(u.shape), None
    cv.face_y(y + depth, x0, x1, z - drop - 3, z - drop, val,
              extra=lambda wx, wz: (wz > z - drop - 3 + 1.5 * (np.abs(((wx - x0) % w) - w / 2) / (w / 2))))


def awning_x(cv, y0, y1, x, z, depth, drop, c1, c2="f8f4ec", w=4):
    k = drop / depth
    a, b = C(c1), C(c2)

    def fn(wx, wy, wz):
        rgb = np.where(((np.floor((wy - y0) / w) % 2) == 0)[..., None], a, b) * np.ones(wx.shape + (3,))
        return rgb, nores(wx.shape), None
    cv.plane(z + k * x, -k, 0, (x, y0, z - drop, x + depth, y1, z),
             lambda wx, wy: (wy >= y0) & (wy < y1) & (wx >= x) & (wx < x + depth), fn)


def balcony(cv, x0, x1, y, z, depth=5, rail="f4f0e8"):
    slab = flat("c8c0b0")
    cv.box(x0, y, z, x1, y + depth, z + 1.5, slab, slab, slab)

    def railfn(u, v, L, H):
        rgb = np.broadcast_to(C(rail), u.shape + (3,)).copy()
        return rgb, nores(u.shape), None
    cv.face_y(y + depth, x0, x1, z + 1.5, z + 7, railfn,
              extra=lambda wx, wz: ((np.floor(wx) % 3) == 0) | (wz > z + 5.5))
    cv.face_x(x1, y, y + depth, z + 1.5, z + 7, railfn,
              extra=lambda wy, wz: ((np.floor(wy) % 3) == 0) | (wz > z + 5.5))


def pool(cv, x0, y0, x1, y1):
    rim = flat("e8e4dc", 3)

    def water(u, v, L, D):
        w = np.sin(u * 0.7 + v * 0.4) + np.sin(u * 0.3 - v * 0.9)
        rgb = np.where((w > 1.1)[..., None], C("bfeaf8"), C("4ab4e0")) * np.ones(u.shape + (3,))
        rgb[(u < 2) | (v < 2)] = C("3a94c0")
        return rgb, nores(u.shape), None
    cv.box(x0, y0, 0, x1, y1, 1.2, rim, rim, rim)
    cv.top(1.3, x0 + 2, y0 + 2, x1 - 2, y1 - 2, water)


def metal(col):
    c = C(col)

    def fn(wx, wy, wz, nx, ny, nz):
        spec = np.clip(nx * -0.3 + ny * 0.5 + nz * 0.8, 0, 1) ** 6
        rgb = c * (0.8 + 0.25 * nz[..., None]) + spec[..., None] * 90
        return rgb, nores(wx.shape), None
    return fn


def glass_wall(base_frame, seed=0, fh=12, lit=0.5, panel=6):
    """Curtain-wall glass facade for modern towers."""
    fr = C(base_frame)

    def fn(u, v, L, H):
        ui, vi = np.floor(u), np.floor(v)
        t = (v % fh) / fh
        rgb = C("3e6e98") * (1 - t[..., None]) + C("7ab0d8") * t[..., None]
        sky = ((ui - vi * 0.5) % 23) < 4
        rgb[sky] = rgb[sky] * 0.6 + C("d8ecf8") * 0.4
        frame = ((ui % panel) == 0) | ((vi % fh) == 0)
        rgb[frame] = fr
        ns = ~frame
        em = np.zeros(u.shape + (4,))
        lit_m = ~frame & (hash2(np.floor(u / panel), np.floor(v / fh), seed) < lit) & (vi < H - 3)
        em[lit_m] = (255, 226, 150, 235)
        cool = lit_m & (hash2(np.floor(u / panel) + 7, np.floor(v / fh), seed) < 0.2)
        em[cool] = (215, 230, 255, 235)
        rgb[vi < 2] = fr * 0.7
        return rgb, ns, em
    return fn


def car(cv, x, y, d="px", col="d84a3a", kind="sedan"):
    units.car_body(cv, x, y, d, col, kind)


def path_y(x0, x1, y0=0):
    return lambda u, v: (u > x0) & (u < x1) & (v > y0)


def fruit_tree(cv, x, y, fruit="e84a3a", seed=0):
    cv.cylinder(x, y, 1.6, 0, 9, trunk_fn())
    cv.ellipsoid(x, y, 15, 7, 7, 7, leaf_fn(LEAF_GREEN, seed, fruit))


def log_pile(cv, x0, y0, n=3):
    end = lambda u, v, L, H: (np.where((((u % 4) - 2) ** 2 + ((v % 4) - 2) ** 2 < 3)[..., None], C("d8b080"), C("8a5a30"))
                              * np.ones(u.shape + (3,)), nores(u.shape), None)
    side = flat("8a5a30", 10)
    for i in range(n):
        cv.box(x0, y0, i * 4, x0 + 20 - i * 3, y0 + 12 - i * 2, i * 4 + 4, end, side, flat("7a4a22"))


def crates(cv, x, y, n=3, seed=0):
    rng = np.random.default_rng(seed)
    for i in range(n):
        dx, dy = rng.uniform(0, 8), rng.uniform(0, 8)
        z = 0 if i < 2 else 6
        c = flat("c89a5a", 10)
        cv.box(x + dx, y + dy, z, x + dx + 6, y + dy + 6, z + 6, c, flat("b08848", 10), flat("d8aa6a", 10))


def tank(cv, x, y, r, h, col="d8dce0"):
    cv.cylinder(x, y, r, 0, h, lambda a, v, nx, ny: (np.broadcast_to(C(col), a.shape + (3,)) *
                                                    (1 - 0.15 * ((np.floor(v) % 8) == 0))[..., None], nores(a.shape), None),
                lambda a, b: solid_res(C(col) * 1.05, a.shape))


def tower_cone(cv, x, y, r, z, h, col="5a4a8a"):
    w = int(2 * r + 3)
    ys, xs = np.mgrid[0:w, 0:w] + 0.5
    d = np.hypot(xs - w / 2, ys - w / 2)
    H = np.where(d < r, z + h * (1 - d / r), -np.inf)
    cv.heightfield(x - w / 2, y - w / 2, H, lambda wx, wy, wz, nx, ny, nz: solid_res(C(col), wx.shape), zmin=z - 1, thick=3.0)


def dome(cv, x, y, z, r, col="e8c050", glass=False):
    if glass:
        def fn(wx, wy, wz, nx, ny, nz):
            rgb = np.broadcast_to(C("6aa0c8"), wx.shape + (3,)).copy()
            grid = ((np.floor(np.arctan2(wy - y, wx - x) * 6) % 2) == 0) & (np.abs(np.sin((wz - z) * 0.6)) < 0.2)
            rgb[grid] = C("e8eef4")
            spec = np.clip(nx * -0.3 + ny * 0.5 + nz * 0.8, 0, 1) ** 8
            return rgb + spec[..., None] * 100, nores(wx.shape), None
        cv.ellipsoid(x, y, z, r, r, r * 0.8, fn, cut_z=z)
    else:
        cv.ellipsoid(x, y, z, r, r, r * 0.9, metal(col), cut_z=z)


def flag(cv, x, y, z, col="d84a3a"):
    cv.cylinder(x, y, 0.7, z, z + 22, lambda a, v, nx, ny: solid_res(C("d0d0d8"), a.shape))
    cv.face_y(y + 0.5, x, x + 10, z + 15, z + 22, lambda u, v, L, H: solid_res(C(col), u.shape))


def playground(cv, x, y):
    red, yel, blu = flat("e84a3a"), flat("f0c040"), flat("3a8ad8")
    for (dx, dy) in ((0, 0), (14, 0), (0, 8), (14, 8)):
        cv.box(x + dx, y + dy, 0, x + dx + 1.5, y + dy + 1.5, 14, blu, blu, blu)
    cv.box(x, y, 14, x + 15.5, y + 9.5, 15.5, red, red, red)
    cv.plane(8 + 0.5 * (y + 10), 0, -0.5, (x + 2, y + 10, 0, x + 8, y + 26, 8),
             lambda wx, wy: (wx >= x + 2) & (wx < x + 8) & (wy >= y + 10) & (wy < y + 26),
             lambda wx, wy, wz: solid_res(C("f0c040"), wx.shape))


def sandbox(cv, x, y, s=16):
    cv.box(x, y, 0, x + s, y + s, 2.5, flat("b07a48"), flat("9a6a3a"),
           lambda u, v, L, D: (np.broadcast_to(C("ead7a0"), u.shape + (3,)) + ((hash2(np.floor(u), np.floor(v), 4) - 0.5) * 16)[..., None],
                               nores(u.shape), None))


def statue_figure(cv, x, y, z, s=1.0, col="b08040"):
    m = metal(col)
    # legs + body
    cv.box(x - 3 * s, y - 2 * s, z, x - 0.5 * s, y + 2 * s, z + 10 * s, _flatm(col), _flatm(col, 0.8), _flatm(col))
    cv.box(x + 0.5 * s, y - 2 * s, z, x + 3 * s, y + 2 * s, z + 10 * s, _flatm(col), _flatm(col, 0.8), _flatm(col))
    cv.ellipsoid(x, y, z + 15 * s, 4.2 * s, 3.2 * s, 6 * s, m)
    cv.ellipsoid(x, y, z + 24 * s, 2.8 * s, 2.8 * s, 3 * s, m)
    # raised arm with torch
    cv.box(x + 3.5 * s, y - 1 * s, z + 17 * s, x + 5.5 * s, y + 1 * s, z + 31 * s, _flatm(col), _flatm(col, 0.8), _flatm(col))
    fire = lambda wx, wy, wz, nx, ny, nz: (np.broadcast_to(C("ffb030"), wx.shape + (3,)).copy(), np.ones(wx.shape, bool),
                                           np.broadcast_to(np.array([255, 190, 80, 255.0]), wx.shape + (4,)).copy())
    cv.ellipsoid(x + 4.5 * s, y, z + 34 * s, 2 * s, 2 * s, 3 * s, fire)
    cv.mark("light", x + 4.5 * s, y, z + 34 * s)


def _flatm(col, f=1.0):
    return flat(C(col) * f, 6)


# ====================================================================== HOMES
def b_house_small(L):
    cv = Canvas(1, 100)
    lot(cv, "grass", 1, path_y(26, 36, 44))
    h = 22 if L < 3 else 42
    left = wall("ece0c4", style=dict(shutter="4a7a9a" if L >= 2 else "8a5a3a", box=True), door=(18, 9, 16, "8a4a2a"), seed=1, cols=2)
    right = wall("dcd0b4", style=dict(shutter="4a7a9a" if L >= 2 else "8a5a3a", box=L >= 2), seed=2, cols=2)
    building(cv, 12, 12, 46, 44, h, left, right, ("gable", "c0503a", "x", 16), end=wall("dcd0b4", seed=3, cols=1, style=dict(wy=2)))
    chimney(cv, 36, 18, h + 6, 14, "chimney")
    steps(cv, 18, 30, 44)
    mailbox(cv, 38, 56, "d84a3a")
    if L >= 2:
        g = wall("e4d8bc", style=dict(plinth="8a8478"), windows=False,
                 decals=[(2, 16, 0, 13, "9aa0a8")] + [(2, 16, y, y + 1, "7a8088") for y in range(2, 13, 3)])
        building(cv, 46, 26, 60, 50, 16, wall("e4d8bc", windows=False), g, ("flat", "8a7a6a", "a89880"))
        fence(cv, 2, 58, 24, 58)
    else:
        bush(cv, 52, 30, 1.2, 5, "e86a8a")
        hedge(cv, 50, 4, 60, 22, 6, 3)
    if L >= 3:
        solar(cv, 16, 30, 30, 40, h + 10)
        tree(cv, 8, 54, 0.8, "oak", 7)
        flower_patch(cv, 4, 36, 12, 50, 9)
    bush(cv, 6, 30, 1.0, 4, "f0d050")
    return cv


def b_cottage(L):
    cv = Canvas(1, 110)
    lot(cv, "grass", 2, path_y(12, 22, 46))
    h = 24 if L == 1 else 44
    sid = dict(siding=True, frame="ffffff", shutter="ffffff" if L >= 3 else None)
    left = wall("8ab4d0", style=sid, door=(12, 9, 16, "f4f4f4"), seed=4, cols=2)
    right = wall("7aa4c0", style=sid, seed=5, cols=2)
    building(cv, 8, 10, 48, 46, h, left, right, ("gable", "3a4a7a", "y", 18, "slate"),
             end=wall("8ab4d0", style=dict(siding=True, wy=3), seed=6, cols=1))
    if L >= 2:
        awning(cv, 6, 30, 46, 15, 7, 4, "ffffff", "e8eef4")
        fence(cv, 2, 60, 44, 60, "ffffff")
        bench(cv, 34, 50)
    if L >= 3:
        balcony(cv, 26, 46, 46, 26, 5)
        chimney(cv, 22, 14, h + 8, 12, "chimney")
        tree(cv, 56, 12, 0.85, "birch", 8)
    bush(cv, 54, 50, 1.0, 9, "e86a8a")
    mailbox(cv, 26, 58, "3a6ad0")
    if L == 1:
        hedge(cv, 52, 4, 62, 30, 6, 11)
    return cv


def b_bungalow(L):
    cv = Canvas(1, 100)
    lot(cv, "grass", 3, path_y(30, 40, 48))
    wood = wall("c89a6a", style=dict(siding=True, frame="3a3a40", ww=14, wh=14, sp=20, plinth="5a5a62"),
                door=(32, 9, 16, "3a3a40", "glass"), seed=7, cols=2)
    white = wall("f0eee8", style=dict(frame="3a3a40", ww=14, wh=14, sp=20, plinth="5a5a62"), seed=8, cols=2)
    building(cv, 10, 10, 54, 48, 20, wood, white, ("flat", "6a6a70", "3a3a40"))
    if L >= 2:
        pool(cv, 4, 50, 28, 62)
        umbrella_table(cv, 50, 56, "3a8ad8")
    if L >= 3:
        glass = glass_wall("3a3a40", seed=9, fh=14, lit=0.7)
        building(cv, 26, 14, 52, 40, 18, glass, glass, ("flat", "5a7a4a", "3a3a40"), z0=20)
        bush(cv, 30, 18, 0.7, 3)
    bush(cv, 6, 14, 1.0, 10)
    tree(cv, 58, 10, 0.7, "oak", 11)
    mailbox(cv, 44, 58, "2a2a30")
    if L == 1:
        hedge(cv, 4, 52, 26, 60, 5, 12)
    return cv


def b_townhouse(L):
    cv = Canvas(2, 140)
    lot(cv, "grass", 4, lambda u, v: v > 104)
    cols = [("c87858", "5a4a4a", True), ("e8d8a8", "2a7a6a", False), ("a8c0d8", "8a3a2a", False), ("d8a0a0", "4a4a5a", True)]
    n = [2, 3, 4][L - 1]
    h = [32, 44, 56][L - 1]
    w = 116 / n
    for i in range(n):
        x0 = 6 + i * w
        base, roofc, brick = cols[i % 4]
        st = dict(brick=0.84 if brick else None, frame="f4f0e8", box=L >= 2, sp=14, mg=5)
        left = wall(base, style=st, door=(4, 9, 16, ["5a3a2a", "2a5a7a", "7a2a3a", "3a5a3a"][i % 4]), seed=10 + i, cols=2)
        right = wall(base, style=st, seed=20 + i, cols=3)
        building(cv, x0, 40, x0 + w - 1, 96, h, left, right, ("gable", roofc, "y", 16 + i % 2 * 3), end=left)
        steps(cv, x0 + 3, x0 + 14, 96)
        chimney(cv, x0 + w - 12, 46, h + 10, 10, "chimney%d" % i if i == 0 else None)
    for i in range(n):
        bush(cv, 10 + i * w + 18, 110, 0.9, 30 + i, "e86a8a" if i % 2 else None)
        mailbox(cv, 6 + i * w + w - 6, 112, ["d84a3a", "3a6ad0", "4a8a3a", "e8b830"][i % 4])
        if i > 0:
            hedge(cv, 6 + i * w - 1.5, 98, 6 + i * w + 1.5, 120, 5, 40 + i)
    if L >= 3:
        lamp_post(cv, 120, 112, 30)
        tree(cv, 120, 20, 1.0, "oak", 12)
    return cv


def b_villa(L):
    cv = Canvas(2, 150)
    lot(cv, "grass", 5, lambda u, v: (np.abs(u - 50) < 6) & (v > 92), flowers=0.02)
    st = dict(frame="ffffff", shutter="6a8a5a", fh=28, ww=11, wh=16, sp=19)
    left = wall("f0e2c8", style=st, door=(42, 14, 20, "6a4a2a"), seed=13)
    right = wall("e4d4b8", style=st, seed=14)
    building(cv, 24, 30, 92, 90, 50, left, right, ("hip", "a84a32", 26))
    steps(cv, 42, 58, 90, 3)
    if L >= 2:
        building(cv, 92, 46, 118, 84, 30, wall("f0e2c8", style=st, seed=15, cols=1), wall("e4d4b8", style=st, seed=16),
                 ("hip", "a84a32", 14))
        pool(cv, 70, 96, 120, 122)
        umbrella_table(cv, 60, 112, "f0c040")
    if L >= 3:
        cv.cylinder(26, 88, 9, 0, 76, lambda a, v, nx, ny: (np.broadcast_to(C("f0e2c8"), a.shape + (3,)) * (1 - 0.2 * ((np.floor(v) % 28 > 8) & (np.floor(v) % 28 < 22) & (np.abs(np.sin(a * 2)) < 0.3)))[..., None],
                     nores(a.shape), None))
        tower_cone(cv, 26, 88, 11, 76, 24, "a84a32")
        flower_patch(cv, 4, 100, 30, 124, 18)
        lamp_post(cv, 64, 124, 30)
    tree(cv, 12, 14, 1.1, "oak", 19)
    tree(cv, 112, 14, 1.0, "birch", 20)
    bush(cv, 14, 60, 1.2, 21, "e86a8a")
    hedge(cv, 2, 124, 38, 127, 6, 22)
    hedge(cv, 62, 124, 126, 127, 6, 23)
    mailbox(cv, 41, 122, "2a2a30")
    return cv


def b_apartments(L):
    floors = [4, 6, 8][L - 1]
    h = floors * 26
    cv = Canvas(2, h + 60)
    lot(cv, "paved", 6)
    st = dict(frame="9a9aa4", band="c8b898", box=L >= 2, ww=10, wh=13, sp=15, mg=6)
    left = wall("e0d0b4", style=st, door=(52, 14, 18, "4a5a6a", "glass"), seed=22, signs=[], lit=0.55)
    right = wall("d4c4a8", style=st, seed=23, lit=0.55)
    building(cv, 14, 14, 112, 104, h, left, right, ("flat", "8a8a8a", "c8c0b0"))
    awning(cv, 48, 72, 104, 20, 6, 2, "3a6a8a", "3a6a8a")
    ac_unit(cv, 24, 24, h)
    ac_unit(cv, 34, 24, h)
    water_tank(cv, 90, 30, h, 7, 14)
    if L >= 2:
        for fl in range(1, floors):
            balcony(cv, 84, 104, 104, fl * 26 + 2, 4)
    if L >= 3:
        cv.box(40, 50, h, 76, 86, h + 2, flat("6aa84a"), flat("5a984a"), grass_fn(3, 0.05))
        for (x, y) in ((46, 56), (68, 78)):
            tree(cv, x, y, 0.5, "oak", x)
    car(cv, 10, 114, "py", "3a7ad8")
    tree(cv, 120, 112, 0.9, "oak", 24)
    return cv


def b_condo(L):
    fl_a, fl_b = [(5, 7), (7, 9), (9, 11)][L - 1]
    cv = Canvas(2, fl_b * 24 + 70)
    lot(cv, "paved", 7)
    st = dict(frame="f4f4f4", band="f4f4f4", ww=12, wh=13, sp=16, mg=5, fh=24)
    a_l = wall("b8d0d8", style=st, door=(16, 12, 16, "2a3a4a", "glass"), seed=25)
    a_r = wall("a8c0c8", style=st, seed=26)
    b_l = wall("e8d0b8", style=st, seed=27)
    b_r = wall("d8c0a8", style=st, seed=28)
    building(cv, 10, 10, 58, 58, fl_b * 24, a_l, a_r, ("flat", "7a8a8a", "f4f4f4"))
    building(cv, 66, 66, 118, 118, fl_a * 24, b_l, b_r, ("flat", "7a8a8a", "f4f4f4"))
    for fl in range(1, fl_a):
        balcony(cv, 70, 92, 118, fl * 24 + 2, 4, "d0e8f0")
    if L >= 3:
        cv.box(54, 34, fl_a * 24 - 16, 70, 46, fl_a * 24 - 6, glass_wall("f4f4f4", 4), glass_wall("f4f4f4", 5), flat("f4f4f4"))
        solar(cv, 74, 74, 110, 110, fl_a * 24)
    else:
        ac_unit(cv, 80, 80, fl_a * 24)
    pool(cv, 10, 70, 50, 110)
    tree(cv, 120, 30, 0.9, "birch", 29)
    return cv


def b_tower(L):
    floors = [12, 16, 20][L - 1]
    h = floors * 12
    cv = Canvas(2, h + 90)
    lot(cv, "paved", 8)
    gw = glass_wall("aac0d0", seed=30, fh=12, lit=0.5)
    gw2 = glass_wall("aac0d0", seed=31, fh=12, lit=0.5)
    cv.box(18, 18, 0, 110, 110, 14, wall("4a5a6a", style=dict(frame="aac0d0", plinth=None), windows=False,
                                         doors=[(40, 14, 12, "x", "glass")]), wall("4a5a6a", windows=False), flat("5a6a7a"))
    building(cv, 22, 22, 106, 106, h, gw, gw2, ("flat", "6a7a8a", "aac0d0"), z0=14)
    top = 14 + h
    if L >= 2:
        building(cv, 36, 36, 92, 92, 36, gw, gw2, ("flat", "5a6a7a", "aac0d0"), z0=top)
        top += 36
    if L >= 3:
        building(cv, 50, 50, 78, 78, 24, gw, gw2, ("flat", "5a6a7a", "aac0d0"), z0=top)
        top += 24
        cv.cylinder(64, 64, 1.5, top, top + 30, lambda a, v, nx, ny: solid_res(C("d8d8e0"), a.shape))
        top += 30
    else:
        cv.cylinder(64, 64, 1.2, top, top + 14, lambda a, v, nx, ny: solid_res(C("d8d8e0"), a.shape))
        top += 14
    blink = lambda wx, wy, wz, nx, ny, nz: (np.broadcast_to(C("ff4040"), wx.shape + (3,)).copy(), np.ones(wx.shape, bool),
                                            np.broadcast_to(np.array([255, 60, 60, 255.0]), wx.shape + (4,)).copy())
    cv.ellipsoid(64, 64, top + 1, 2, 2, 2, blink)
    tree(cv, 10, 116, 0.8, "oak", 32)
    tree(cv, 116, 10, 0.8, "oak", 33)
    return cv


# ====================================================================== SHOPS 1x1
def shop1(L, seed, base, base_r, awn, sign, sign_bg, sign_fg, extra=None, roofc=None):
    h = [22, 46, 70][L - 1]
    cv = Canvas(1, h + 40)
    lot(cv, "paved", seed)
    signs = [(14, 17, sign, sign_bg, sign_fg, L >= 2)]
    st = dict(frame="f8f4ec", box=L >= 2, sp=16)
    left = wall(base, style=st, shop=(4, 26, 2, 13), door=(30, 9, 15, "x", "glass"), signs=signs, seed=seed)
    right = wall(base_r, style=st, seed=seed + 1, cols=2)
    building(cv, 10, 12, 52, 46, h, left, right, ("flat", roofc or "8a7a6a", "c8b8a0"))
    awning(cv, 9, 40, 46, 15, 6, 3, awn)
    if extra:
        extra(cv, L, h)
    if L >= 3:
        ac_unit(cv, 20, 20, h)
    return cv


def b_bakery(L):
    def ex(cv, L, h):
        chimney(cv, 40, 16, h, 10, "chimney")
        if L >= 2:
            umbrella_table(cv, 56, 52, "e86a8a")
    return shop1(L, 40, "f0d8b8", "e0c8a8", "e86a8a", "BAKERY", "8a4a2a", "f8e0a0", ex, "b06a4a")


def b_cafe(L):
    def ex(cv, L, h):
        for (x, y) in ((8, 56), (26, 56))[: 1 + (L >= 2)]:
            umbrella_table(cv, x, y, "3a8a5a")
        if L >= 3:
            fence(cv, 12, 14, 50, 14, "3a3a40", 4)
    return shop1(L, 42, "7ab48a", "6aa47a", "3a8a5a", "CAFE", "f8f0e0", "3a2a1a", ex)


def b_flowershop(L):
    def ex(cv, L, h):
        flower_patch(cv, 2, 52, 18, 62, 44)
        flower_patch(cv, 22, 52, 38, 62, 45)
        if L >= 2:
            g = glass_wall("f4f4f4", 46, fh=10, lit=0.3, panel=5)
            cv.box(52, 14, 0, 62, 44, 16, g, g, glass_wall("f4f4f4", 47, fh=8, panel=5))
        if L >= 3:
            cv.box(14, 16, h, 48, 42, h + 2, flat("6aa84a"), flat("5a984a"), grass_fn(5, 0.12))
    return shop1(L, 48, "f4e8f0", "e4d8e0", "c86a9a", "FLOWERS", "4a8a3a", "fff4f8", ex, "8a6a7a")


def b_pizzeria(L):
    def ex(cv, L, h):
        chimney(cv, 14, 16, h, 12, "chimney", "8a6a5a")
        if L >= 2:
            car(cv, 56, 30, "py", "e84a3a", "hatch")
    return shop1(L, 50, "e8d0b0", "d8c0a0", "d84a3a", "PIZZA", "2a6a3a", "fff0d0", ex, "7a5a4a")


def b_boutique(L):
    def ex(cv, L, h):
        if L >= 2:
            balcony(cv, 12, 40, 46, 26, 4, "e8d0f0")
        if L >= 3:
            balcony(cv, 12, 40, 46, 50, 4, "e8d0f0")
        lamp_post(cv, 56, 54, 26, "modern")
    return shop1(L, 52, "b890c8", "a880b8", "6a3a8a", "SHOP", "2a1a3a", "f8d8ff", ex, "5a4a6a")


# ====================================================================== SHOPS 2x2
def b_supermarket(L):
    h = [30, 30, 54][L - 1]
    cv = Canvas(2, h + 50)
    lot(cv, "asphalt", 9)
    left = wall("ecece4", shop=(10, 66, 2, 16), door=(36, 14, 16, "x", "glass"), windows=L >= 3,
                signs=[(26, 22, "MARKET", "d84a3a", "fff4e0", L >= 2)], seed=53, style=dict(sp=14))
    right = wall("dcdcd4", seed=54, windows=L >= 3, decals=[(6, 60, 20, 26, "d84a3a")])
    building(cv, 8, 8, 84, 70, h, left, right, ("flat", "9a9aa0", "d0d0d0"))
    awning(cv, 8, 84, 70, 18, 6, 2, "d84a3a", "f8f4ec", 8)
    ac_unit(cv, 20, 20, h)
    if L >= 2:
        ac_unit(cv, 34, 20, h)
        ac_unit(cv, 48, 20, h)
        for (x, y, c, k) in ((22, 96, "3a7ad8", "sedan"), (48, 96, "f0f0f0", "hatch")):
            car(cv, x, y, "py", c, k)
    if L >= 3:
        car(cv, 74, 96, "py", "d84a3a", "pickup")
        lamp_post(cv, 100, 100, 34, "modern")

    def lines(u, v, L_, D):
        rgb = np.broadcast_to(C("6a6a74"), u.shape + (3,)).copy()
        rgb[((np.floor(u) % 26) == 0) & (v > 84)] = C("f0f0f0")
        return rgb, nores(u.shape), None
    cv.top(0.2, 0, 80, 128, 128, lines, shade=1.0)
    tree(cv, 112, 30, 0.9, "oak", 55)
    return cv


def b_restaurant(L):
    h = [30, 30, 56][L - 1]
    cv = Canvas(2, h + 50)
    lot(cv, "grass", 10, lambda u, v: (v > 76) & (u < 80))
    st = dict(frame="2a2a30", ww=12, wh=15, sp=18, cornice="5a3a2a")
    left = wall("8a3a2a", style=dict(st, brick=0.85), shop=(8, 40, 3, 16), door=(46, 12, 17, "x", "glass"),
                signs=[(14, 21, "GRILL", "2a2a30", "f8d070", True)], seed=56)
    right = wall("7a2a1a", style=dict(st, brick=0.85), seed=57)
    building(cv, 10, 14, 80, 74, h, left, right, ("flat", "5a4a44", "8a6a5a"))
    awning(cv, 8, 80, 74, 18, 6, 2, "2a2a30", "2a2a30")
    for x in (14, 34, 54)[: 2 + (L >= 2)]:
        umbrella_table(cv, x, 90, "f4ead2")
    if L >= 2:
        fence(cv, 6, 106, 76, 106, "3a3a40", 5)
        flower_patch(cv, 86, 82, 120, 100, 58)
    if L >= 3:
        for x in range(16, 78, 12):
            cv.ellipsoid(x, 76, h + 2, 1.2, 1.2, 1.2, lambda wx, wy, wz, nx, ny, nz: (
                np.broadcast_to(C("fff0b0"), wx.shape + (3,)).copy(), np.ones(wx.shape, bool),
                np.broadcast_to(np.array([255, 230, 150, 255.0]), wx.shape + (4,)).copy()))
    tree(cv, 104, 24, 1.0, "oak", 59)
    tree(cv, 112, 116, 0.8, "sakura", 60)
    return cv


def b_cinema(L):
    h = [50, 50, 74][L - 1]
    cv = Canvas(2, h + 50)
    lot(cv, "paved", 11)
    bulbs = [(x, x + 1, 37, 38, "emit:fff0a0") for x in range(6, 72, 3)] + \
            [(x, x + 1, 27, 28, "emit:fff0a0") for x in range(6, 72, 3)]
    left = wall("7a3a5a", door=(30, 18, 16, "x", "glass"), windows=False, seed=61,
                signs=[(22, 30, "CINEMA", "2a1a2a", "fff070", True)],
                decals=bulbs + [(6, 18, 2, 22, "e8c860"), (7, 17, 3, 21, "3a6aa8"), (56, 68, 2, 22, "e8c860"), (57, 67, 3, 21, "a83a2a")])
    right = wall("6a2a4a", style=dict(fh=24, wy=8, frame="e8c860"), seed=62, lit=0.8)
    building(cv, 10, 8, 86, 76, h, left, right, ("flat", "4a2a3a", "e8c860"))
    if L >= 2:
        building(cv, 10, 8, 86, 30, 14, right, right, ("flat", "4a2a3a", "e8c860"), z0=h)
        lamp_post(cv, 98, 90, 32)
    if L >= 3:
        cv.cylinder(86, 76, 10, 0, h + 12, lambda a, v, nx, ny: (np.broadcast_to(C("e8c860"), a.shape + (3,)) *
                    (0.85 + 0.15 * ((np.floor(v) % 6) < 3))[..., None], nores(a.shape), None),
                    lambda a, b: solid_res(C("6a2a4a"), a.shape))
    tree(cv, 110, 30, 1.0, "oak", 63)
    bush(cv, 104, 110, 1.2, 64, "f0d050")
    return cv


def b_mall(L):
    h = [40, 52, 52][L - 1]
    cv = Canvas(2, h + 110)
    lot(cv, "paved", 12)
    st = dict(frame="8a9aa8", ww=14, wh=14, sp=20)
    left = wall("e8e4dc", style=st, shop=(8, 80, 2, 18), door=(38, 18, 18, "x", "glass"),
                signs=[(36, 30 if L == 1 else 40, "MALL", "3a8ad8", "ffffff", True)], seed=65)
    right = wall("d8d4cc", style=st, shop=(8, 90, 2, 18), seed=66)
    building(cv, 6, 6, 104, 98, h, left, right, ("flat", "a8a8b0", "e8e4dc"))
    if L >= 2:
        dome(cv, 55, 52, h, 22, glass=True)
    if L >= 3:
        gw = glass_wall("8a9aa8", 67)
        building(cv, 74, 10, 102, 38, 60, gw, gw, ("flat", "8a9aa8", "e8e4dc"), z0=h)
        flag(cv, 88, 24, h + 60, "3a8ad8")
    for (x, d, c) in ((112, "py", "d84a3a"), (122, "py", "f0f0f0")):
        car(cv, x, 60, d, c)
    tree(cv, 116, 112, 0.9, "oak", 68)
    return cv


# ====================================================================== INDUSTRY
def field(cv, x0, y0, x1, y1, crop="6aa84a", dots="e8a030", seed=0):
    def fn(u, v, L, D):
        rgb = np.broadcast_to(C("7a5232"), u.shape + (3,)).copy()
        rgb += ((hash2(np.floor(u), np.floor(v), seed) - 0.5) * 12)[..., None]
        row = (np.floor(v) % 7) < 4
        h = hash2(np.floor(u / 2), np.floor(v), seed + 1)
        rgb[row] = np.where((h[row] > 0.5)[..., None], C(crop), C(crop) * 1.2)
        d = row & (h > 0.85)
        rgb[d] = C(dots)
        return rgb, nores(u.shape), None
    cv.top(0.4, x0, y0, x1, y1, fn, shade=1.0)


def barn(cv, x0, y0, x1, y1, h, col="b8402a"):
    red = wall(col, style=dict(siding=True, frame="f0e8d8", plinth="6a5a4a"), windows=False,
               door=(int((x1 - x0) / 2) - 8, 16, 20, "7a2a1a"),
               decals=[(int((x1 - x0) / 2) - 8, int((x1 - x0) / 2) + 8, 19, 21, "f0e8d8")])
    red2 = wall(col, style=dict(siding=True, frame="f0e8d8"), cols=2, seed=70)
    building(cv, x0, y0, x1, y1, h, red, red2, ("gable", "7a6a5a", "x", 16, "metal"),
             end=wall(col, style=dict(siding=True, wy=3), cols=1, seed=71))


def b_farm(L):
    cv = Canvas(2, 110)
    lot(cv, "grass", 13)
    field(cv, 6, 64, 122, 124, seed=1)
    barn(cv, 8, 8, 58, 50, 26)
    if L >= 2:
        tank(cv, 72, 20, 9, 52, "c8c8c0")
        dome(cv, 72, 20, 52, 9, "9a9aa0")
    if L >= 3:
        barn(cv, 86, 10, 120, 44, 20, "c8a040")
        units.car_body(cv, 70, 52, "px", "4ab04a", "pickup")
    fence(cv, 4, 62, 124, 62, "c8a070", 5)
    tree(cv, 120, 56, 0.8, "oak", 72)
    return cv


def b_orchard(L):
    cv = Canvas(2, 90)
    lot(cv, "grass", 14)
    n = [2, 3, 4][L - 1]
    fruit = ["e84a3a", "f0c040", "f08a3a"]
    for r in range(n):
        for c in range(5):
            fruit_tree(cv, 14 + c * 22, 46 + r * 20, fruit[r % 3], r * 10 + c)
    shed = wall("a87a4a", style=dict(siding=True), windows=False, door=(6, 10, 14, "6a4a2a"))
    building(cv, 8, 6, 40, 30, 18, shed, shed, ("gable", "6a5a4a", "x", 10, "metal"))
    crates(cv, 46, 16, 3, 74)
    if L >= 3:
        g = glass_wall("f4f4f4", 75, fh=8, lit=0.2, panel=6)
        building(cv, 70, 6, 120, 30, 16, g, g, ("gable", "c8e0e8", "x", 8, "metal"))
    return cv


def b_sawmill(L):
    cv = Canvas(2, 110)
    lot(cv, "grass", 15)

    def dirt(u, v, L_, D):
        return (np.broadcast_to(C("9a7a50"), u.shape + (3,)) + ((hash2(np.floor(u), np.floor(v), 6) - 0.5) * 16)[..., None],
                nores(u.shape), None)
    cv.top(0.3, 4, 4, 124, 124, dirt, shade=1.0)
    wood = wall("8a5a32", style=dict(siding=True, frame="d8c8a8", plinth="5a4a3a"), seed=76,
                door=(30, 18, 20, "4a3a2a"), cols=2)
    h = [24, 24, 34][L - 1]
    building(cv, 10, 10, 70, 56, h, wood, wood, ("gable", "5a6a6a", "x", 14, "metal"))
    log_pile(cv, 76, 18, 3)
    log_pile(cv, 20, 76, 2 + (L >= 2))
    if L >= 2:
        log_pile(cv, 60, 90, 3)
        cv.box(96, 70, 0, 99, 73, 50, flat("e8b830"), flat("c89820"), flat("e8b830"))
        cv.box(60, 70, 48, 99, 73, 51, flat("e8b830"), flat("c89820"), flat("f8c840"))
    if L >= 3:
        chimney(cv, 56, 20, h + 10, 20, "smoke1", "6a6a74")
    tree(cv, 118, 10, 1.0, "pine", 77)
    tree(cv, 6, 118, 0.9, "pine", 78)
    return cv


def b_workshop(L):
    cv = Canvas(2, 120)
    lot(cv, "paved", 16)
    h = [28, 28, 50][L - 1]
    st = dict(brick=0.84, frame="d8d0c0", fh=24, plinth="5a5a5a")
    gate = [(6, 22, 0, 18, "9aa0a8")] + [(6, 22, y, y + 1, "7a8088") for y in range(2, 18, 3)]
    left = wall("8a6a5a", style=st, decals=gate + [(30, 46, 0, 18, "9aa0a8")] + [(30, 46, y, y + 1, "7a8088") for y in range(2, 18, 3)],
                seed=79, windows=L >= 3)
    right = wall("7a5a4a", style=st, seed=80)
    building(cv, 10, 10, 76, 64, h, left, right, ("gable", "4a5a6a", "x", 12, "metal"))
    crates(cv, 82, 14, 4, 81)
    if L >= 2:
        building(cv, 82, 40, 118, 76, 20, wall("8a6a5a", style=st, seed=82, cols=1), wall("7a5a4a", style=st, seed=83),
                 ("flat", "6a6a70", "9a9aa0"))
        car(cv, 40, 96, "px", "3a6ad0", "van")
    if L >= 3:
        chimney(cv, 20, 20, h + 10, 14, "smoke1", "6a6a74")
    return cv


def b_factory(L):
    cv = Canvas(2, 170)
    lot(cv, "asphalt", 17)
    h = [32, 32, 44][L - 1]
    st = dict(frame="5a6068", fh=30, wy=14, wh=10, sp=14)
    gate = [(12, 34, 0, 22, "e8c040")] + [(12, 34, y, y + 1, "3a3a3a") for y in range(2, 22, 3)]
    left = wall("9aa0a8", style=st, decals=gate, seed=84)
    right = wall("8a9098", style=st, seed=85)
    cv.box(6, 8, 0, 80, 70, h, left, right, flat("6a7078"))
    for y0 in (8, 26, 44):
        cv.gable(6, y0, 80, y0 + 18, h, 10, roof_tiles("5a6a7a", kind="metal"), right, "x", 0.5)
    stacks = [(60, 12, 90)] + ([(68, 30, 80)] if L >= 2 else []) + ([(52, 30, 100)] if L >= 3 else [])
    for i, (x, y, top) in enumerate(stacks):
        st_ = lambda a, v, nx, ny, top=top: (np.where((np.floor(v / 8) % 2 == 0)[..., None] & (v > top - h - 20)[..., None],
                                                      C("f0f0f0"), C("b84a3a")) * np.ones(a.shape + (3,)), nores(a.shape), None)
        cv.cylinder(x, y, 5, h, top, st_, lambda a, b: solid_res(C("2a2a2a"), a.shape))
        cv.mark("smoke%d" % (i + 1), x, y, top)
    if L >= 2:
        tank(cv, 100, 24, 12, 40)
        dome(cv, 100, 24, 40, 12, "c8ccd0")
    if L >= 3:
        tank(cv, 104, 60, 10, 34)
        cv.box(82, 22, 30, 92, 26, 33, flat("8a8a8a"), flat("7a7a7a"), flat("9a9a9a"))
    cv.top(0.3, 0, 84, 128, 128, lambda u, v, L_, D: (np.where(((np.floor(u) % 12) < 6)[..., None] & (v > 36)[..., None],
                                                                C("e8c040"), C("6a6a74")) * np.ones(u.shape + (3,)), nores(u.shape), None), shade=1.0)
    car(cv, 40, 104, "px", "3a6ad0", "truck")
    return cv


def b_logistics(L):
    cv = Canvas(2, 150)
    lot(cv, "asphalt", 18)
    n_docks = [3, 4, 5][L - 1]
    docks = []
    for i in range(n_docks):
        u0 = 6 + i * 16
        docks += [(u0, u0 + 12, 0, 16, "8a9098")] + [(u0, u0 + 12, y, y + 1, "6a7078") for y in range(2, 16, 3)]
    left = wall("d8dce0", windows=False, decals=docks + [(4, 96, 20, 24, "3a8ad8")], seed=86)
    right = wall("c8ccd0", windows=False, decals=[(4, 60, 20, 24, "3a8ad8")], seed=87)
    building(cv, 8, 8, 104, 70, 30, left, right, ("flat", "b8bcc0", "d8dce0"))
    for i in range(min(n_docks, 3)):
        car(cv, 16 + i * 30, 94, "py", "3a6ad0", "truck")
    if L >= 3:
        gw = glass_wall("aab8c8", 88)
        building(cv, 104, 8, 124, 40, 60, gw, gw, ("flat", "8a9aa8", "d8dce0"))
    return cv


# ====================================================================== SERVICES
def b_school(L):
    cv = Canvas(2, 150)
    lot(cv, "grass", 19)
    h = [30, 30, 44][L - 1]
    st = dict(brick=0.84, frame="f4f0e8", ww=12, wh=14, sp=16)
    left = wall("d8a050", style=st, door=(40, 16, 18, "3a5a8a", "glass"), signs=[(34, 22, "SCHOOL", "3a5a8a", "ffffff", L >= 2)], seed=89)
    right = wall("c89040", style=st, seed=90)
    building(cv, 10, 8, 90, 60, h, left, right, ("hip", "8a3a2a", 14))
    steps(cv, 38, 60, 60)
    playground(cv, 92, 76)
    sandbox(cv, 70, 96)
    flag(cv, 100, 40, 0, "3a8ad8")
    if L >= 2:
        building(cv, 90, 8, 120, 40, 24, wall("d8a050", style=st, seed=91, cols=1), wall("c89040", style=st, seed=92),
                 ("hip", "8a3a2a", 10))
    if L >= 3:
        cv.box(44, 26, h + 6, 60, 42, h + 30, wall("d8a050", style=dict(brick=0.84), windows=False,
                                                   decals=[(4, 12, 12, 20, "f4f0e8")]), wall("c89040", windows=False), flat("6a6a6a"))
        tower_cone(cv, 52, 34, 11, h + 30, 14, "8a3a2a")
    tree(cv, 10, 112, 1.0, "oak", 93)
    return cv


def b_fire_station(L):
    cv = Canvas(2, 150)
    lot(cv, "paved", 20)
    h = [32, 44, 44][L - 1]
    gates = []
    for i in range(2 + (L >= 3)):
        u0 = 6 + i * 22
        gates += [(u0, u0 + 18, 0, 22, "c83a2a")] + [(u0, u0 + 18, y, y + 1, "a82a1a") for y in range(3, 22, 4)]
    st = dict(brick=0.82, frame="f4f0e8", fh=26, wy=26, plinth="6a5a5a")
    left = wall("a8483a", style=st, decals=gates, signs=[(20, 30 if L == 1 else 36, "FIRE", "f4f0e8", "c83a2a", L >= 2)], seed=94,
                windows=L >= 2)
    right = wall("98382a", style=dict(st, wy=8), seed=95)
    building(cv, 8, 10, 82, 72, h, left, right, ("flat", "6a5a5a", "c8b8a8"))
    tw = wall("a8483a", style=dict(brick=0.82), windows=False, decals=[(3, 11, 50, 58, "f4f0e8")])
    cv.box(84, 14, 0, 100, 30, 70, tw, tw, flat("5a4a4a"))
    cv.box(82, 12, 70, 102, 32, 74, flat("5a4a4a"), flat("4a3a3a"), flat("6a5a5a"))
    if L >= 2:
        units.car_body(cv, 30, 98, "py", "d83a2a", "truck")
    lamp_post(cv, 112, 110, 30)
    return cv


def b_police(L):
    cv = Canvas(2, 170)
    lot(cv, "paved", 21)
    h = [32, 54, 54][L - 1]
    st = dict(frame="f4f4f4", band="f4f4f4", ww=12, sp=16)
    left = wall("4a6a9a", style=st, door=(36, 16, 18, "x", "glass"), signs=[(30, 22, "POLICE", "f4f4f4", "2a3a6a", L >= 2)], seed=96)
    right = wall("3a5a8a", style=st, seed=97)
    building(cv, 10, 10, 90, 70, h, left, right, ("flat", "5a6a7a", "c8d0d8"))
    steps(cv, 34, 54, 70)
    flag(cv, 100, 20, 0, "3a6ad0")
    car(cv, 100, 60, "py", "f4f4f4")
    car(cv, 112, 96, "py", "2a2a40")
    if L >= 3:
        cv.cylinder(30, 30, 1.6, h, h + 50, lambda a, v, nx, ny: solid_res(C("c8c8d0"), a.shape))
        cv.box(26, 26, h, 34, 34, h + 4, flat("8a8a90"), flat("7a7a80"), flat("9a9aa0"))
    return cv


def b_hospital(L):
    floors = [3, 5, 7][L - 1]
    h = floors * 24
    cv = Canvas(2, h + 50)
    lot(cv, "paved", 22)
    st = dict(frame="c8d8e0", band="d8e4e8", ww=12, wh=12, sp=16, fh=24)
    cross = [(70, 78, h - 20, h - 8, "e83a3a"), (66, 82, h - 16, h - 12, "e83a3a")]
    left = wall("f4f6f8", style=st, door=(14, 16, 18, "x", "glass"), signs=[(36, 8, "HOSPITAL", "e83a3a", "ffffff", True)],
                decals=cross, seed=98)
    right = wall("e4e8ec", style=st, seed=99)
    building(cv, 8, 10, 98, 88, h, left, right, ("flat", "c8ccd0", "f4f6f8"))
    awning(cv, 10, 34, 88, 18, 8, 2, "e83a3a", "e83a3a")
    if L >= 3:
        def pad(u, v, L_, D):
            rgb = np.broadcast_to(C("5a5a64"), u.shape + (3,)).copy()
            d = np.hypot(u - L_ / 2, v - D / 2)
            rgb[(d > 14) & (d < 16)] = C("f4f4f4")
            hm = ((np.abs(u - L_ / 2 + 5) < 1.5) | (np.abs(u - L_ / 2 - 5) < 1.5)) & (np.abs(v - D / 2) < 7)
            hm |= (np.abs(v - D / 2) < 1.2) & (np.abs(u - L_ / 2) < 5)
            rgb[hm] = C("f4f4f4")
            return rgb, nores(u.shape), None
        cv.box(30, 26, h, 74, 70, h + 2, flat("8a8a90"), flat("7a7a80"), pad)
    else:
        ac_unit(cv, 30, 30, h)
        ac_unit(cv, 44, 30, h)
    units.car_body(cv, 110, 60, "py", "f4f4f4", "van")
    tree(cv, 112, 112, 0.9, "oak", 100)
    return cv


def b_town_hall(L):
    cv = Canvas(2, 190)
    lot(cv, "paved", 23)
    h = 44
    st = dict(frame="f4f0e8", fh=22, ww=10, wh=14, sp=14, cornice="e8e0d0", plinth="a89a88")
    left = wall("e8dcc8", style=st, door=(48, 16, 22, "6a4a2a"), seed=101)
    right = wall("dcd0bc", style=st, seed=102)
    building(cv, 14, 20, 110, 84, h, left, right, ("flat", "a8a090", "e8e0d0"))
    # columns portico
    col = lambda a, v, nx, ny: (np.broadcast_to(C("f4f0e8"), a.shape + (3,)) * (0.92 + 0.08 * (np.floor(a * 6) % 2))[..., None],
                                nores(a.shape), None)
    for x in range(40, 88, 10):
        cv.cylinder(x, 92, 2.6, 0, 36, col)
    cv.box(34, 84, 36, 92, 96, 42, flat("f4f0e8"), flat("e8e0d0"), flat("e8e0d0"))
    cv.gable(34, 84, 92, 96, 42, 12, roof_tiles("e8e0d0", kind="slate"), flat("f4f0e8"), "y", 1)
    steps(cv, 34, 92, 96, 3)
    if L >= 2:
        for (xa, xb) in ((2, 14), (110, 124)):
            building(cv, xa, 30, xb, 76, 32, wall("e8dcc8", style=st, seed=103, cols=0), wall("dcd0bc", style=st, seed=104),
                     ("flat", "a8a090", "e8e0d0"))
    cv.cylinder(62, 52, 16, h, h + 18, lambda a, v, nx, ny: (np.broadcast_to(C("e8dcc8"), a.shape + (3,)).copy(), nores(a.shape), None))
    dome(cv, 62, 52, h + 18, 16, "e8c050" if L >= 3 else "6a9a8a")
    top = h + 18 + 15
    if L >= 3:
        cv.cylinder(62, 52, 1.5, top, top + 16, lambda a, v, nx, ny: solid_res(C("e8c050"), a.shape))
        flag(cv, 62, 52, top + 2, "d84a3a")
    flower_patch(cv, 4, 100, 30, 124, 105)
    flower_patch(cv, 98, 100, 124, 124, 106)
    return cv


# ====================================================================== DECOR
def b_tree(L):
    cv = Canvas(1, 110)
    lot(cv, "grass", 24, flowers=0.03 if L >= 3 else 0.005)
    if L == 1:
        tree(cv, 32, 32, 0.8, "oak", 107)
    elif L == 2:
        tree(cv, 32, 32, 1.3, "oak", 108)
    else:
        tree(cv, 22, 22, 1.1, "oak", 109)
        tree(cv, 46, 30, 0.9, "sakura", 110)
        tree(cv, 28, 48, 0.8, "birch", 111)
    return cv


def b_flowerbed(L):
    cv = Canvas(1, 40)
    lot(cv, "grass", 25)
    if L == 1:
        flower_patch(cv, 14, 14, 50, 50, 112)
    elif L == 2:
        flower_patch(cv, 6, 6, 58, 58, 113)
        bush(cv, 32, 32, 0.8, 114, "f6f0f0")
    else:
        flower_patch(cv, 4, 4, 60, 60, 115, "e8e0d0")
        cv.box(18, 18, 3, 46, 46, 7, flat("e8e0d0"), flat("d8d0c0"),
               lambda u, v, L_, D: (np.where((hash2(np.floor(u / 2), np.floor(v / 2), 9) > 0.4)[..., None], C("e84a8a"), C("4f923e"))
                                    * np.ones(u.shape + (3,)), nores(u.shape), None))
        bush(cv, 32, 32, 0.7, 116, "f0c040")
    return cv


def b_lamp(L):
    cv = Canvas(1, 70)
    lot(cv, "grass", 26, lambda u, v: (u > 20) & (u < 44) & (v > 20) & (v < 44))
    if L == 1:
        lamp_post(cv, 32, 32, 34)
        cv.mark("light", 32, 32, 37)
    elif L == 2:
        lamp_post(cv, 32, 32, 38, "modern")
        cv.mark("light", 38, 32, 37)
        bench(cv, 14, 44)
    else:
        lamp_post(cv, 24, 24, 40)
        lamp_post(cv, 42, 42, 40)
        cv.mark("light", 32, 32, 43)
        flower_patch(cv, 40, 10, 56, 26, 117)
        flower_patch(cv, 8, 40, 24, 56, 118)
    bush(cv, 52, 50, 0.7, 119, "e86a8a")
    return cv


def b_bench(L):
    cv = Canvas(1, 80)
    lot(cv, "grass", 27, lambda u, v: (u > 10) & (u < 54) & (v > 34) & (v < 52))
    if L < 3:
        bench(cv, 24, 36)
        if L == 2:
            tree(cv, 20, 18, 0.9, "oak", 120)
            flower_patch(cv, 44, 44, 58, 58, 121)
    else:
        # gazebo
        wood = lambda a, v, nx, ny: solid_res(C("f4f0e8"), a.shape)
        for ang in range(0, 360, 60):
            x = 32 + math.cos(math.radians(ang)) * 18
            y = 32 + math.sin(math.radians(ang)) * 18
            cv.cylinder(x, y, 1.6, 0, 24, wood)
        cv.cylinder(32, 32, 22, 0, 2, lambda a, v, nx, ny: solid_res(C("c8b898"), a.shape),
                    lambda a, b: (np.broadcast_to(C("d8c8a8"), a.shape + (3,)) * (1 - 0.1 * ((np.floor(a / 4) + np.floor(b / 4)) % 2))[..., None],
                                  nores(a.shape), None))
        tower_cone(cv, 32, 32, 26, 24, 18, "3a6a5a")
        bench(cv, 24, 30)
    return cv


def b_fountain(L, frame=0):
    cv = Canvas(1, 70)

    def stone(u, v, L_, D):
        rgb = np.broadcast_to(C("d0c8b8"), u.shape + (3,)).copy()
        rgb[((np.floor(u / 8) + np.floor(v / 8)) % 2) == 0] *= 0.93
        return rgb, nores(u.shape), None
    cv.ground(stone)

    def water(u, v, L_, D):
        w = np.sin(np.hypot(u - L_ / 2, v - D / 2) * 1.1 - frame * math.pi)
        rgb = np.where((w > 0.45)[..., None], C("a8e0f8"), C("4a9ad0")) * np.ones(u.shape + (3,))
        return rgb, nores(u.shape), None
    rim = flat("b8b0a0", 4)
    r_out = [20, 24, 28][L - 1]
    cv.cylinder(32, 32, r_out, 0, 7, lambda a, v, nx, ny: rim(a * 10, v), lambda a, b: solid_res(C("d8d0c0"), a.shape))
    cv.cylinder(32, 32, r_out - 3, 0, 7.4, lambda a, v, nx, ny: solid_res(C("4a9ad0"), a.shape),
                lambda a, b: water(a + 32, b + 32, 64, 64))
    top = 7
    if L >= 2:
        cv.cylinder(32, 32, 3, 7, 22, lambda a, v, nx, ny: rim(a * 10, v))
        cv.cylinder(32, 32, 10, 22, 26, lambda a, v, nx, ny: rim(a * 10, v), lambda a, b: water(a + 32, b + 32, 64, 64))
        top = 26
    if L >= 3:
        statue_figure(cv, 32, 32, 26, 0.55, "c8a050")
        top = 46
    # water jets
    jet = lambda wx, wy, wz, nx, ny, nz: (np.where((((np.floor(wz) + frame) % 3) == 0)[..., None], C("e8f8ff"), C("9ad4f4"))
                                          * np.ones(wx.shape + (3,)), np.ones(wx.shape, bool), None)
    jh = 10 + frame * 2
    cv.ellipsoid(32, 32, top + jh / 2, 1.6, 1.6, jh / 2, jet)
    for ang in range(0, 360, 90 if L < 3 else 45):
        x = 32 + math.cos(math.radians(ang + frame * 20)) * (r_out - 7)
        y = 32 + math.sin(math.radians(ang + frame * 20)) * (r_out - 7)
        cv.ellipsoid(x, y, 9 + frame, 1.0, 1.0, 2.5, jet)
    return cv


def b_park(L):
    cv = Canvas(2, 80)
    lot(cv, "grass", 28, lambda u, v: (np.abs(u - v) < 5) | (np.abs(u + v - 128) < 5), flowers=0.02)
    pool_ = L >= 2
    if pool_:
        def pond(u, v, L_, D):
            w = np.sin(u * 0.5 + v * 0.3)
            rgb = np.where((w > 0.85)[..., None], C("a8d8f0"), C("4a8ac0")) * np.ones(u.shape + (3,))
            return rgb, nores(u.shape), None
        cv.top(0.5, 80, 10, 118, 40, pond, extra=lambda u, v: ((u - 19) / 19) ** 2 + ((v - 15) / 15) ** 2 < 1)
        bench(cv, 20, 90)
        bench(cv, 60, 56, "y")
    for (x, y, k, s) in ((18, 16, "oak", 1.0), (110, 64, "sakura", 0.9), (14, 112, "sakura", 0.9), (64, 18, "oak", 0.9)):
        tree(cv, x, y, s, k, x + y)
    bush(cv, 40, 70, 1.0, 129, "e86a8a")
    if L >= 3:
        playground(cv, 92, 92)
        lamp_post(cv, 72, 72, 32)
        cv.mark("light", 72, 72, 35)
        flower_patch(cv, 56, 100, 76, 120, 130)
    return cv


def b_statue(L):
    cv = Canvas(1, 120)

    def stone(u, v, L_, D):
        rgb = np.broadcast_to(C("d0c8b8"), u.shape + (3,)).copy()
        rgb[((np.floor(u / 8) + np.floor(v / 8)) % 2) == 0] *= 0.93
        return rgb, nores(u.shape), None
    cv.ground(stone)
    ped = wall("d8d0c0", windows=False, style=dict(plinth="a89a88", cornice="e8e0d0"))
    z = 0
    if L >= 3:
        cv.box(10, 10, 0, 54, 54, 4, flat("c8c0b0"), flat("b8b0a0"), flat("d8d0c0"))
        cv.box(14, 14, 4, 50, 50, 8, flat("c8c0b0"), flat("b8b0a0"), flat("d8d0c0"))
        z = 8
        flower_patch(cv, 2, 2, 12, 62, 131)
        lamp_post(cv, 58, 58, 30)
    w = [16, 20, 22][L - 1]
    ph = [16, 22, 24][L - 1]
    cv.box(32 - w / 2, 32 - w / 2, z, 32 + w / 2, 32 + w / 2, z + ph, ped, ped, flat("e0d8c8"))
    statue_figure(cv, 32, 32, z + ph, [0.8, 1.0, 1.1][L - 1], ["8a6a4a", "b08040", "e8c050"][L - 1])
    return cv


# ====================================================================== NEW IN v3
def b_bank(L):
    cv = Canvas(2, 170)
    lot(cv, "paved", 32)
    h = [40, 52, 52][L - 1]
    st = dict(frame="e8e0d0", fh=26, ww=10, wh=16, sp=16, cornice="d8ccb4", plinth="8a8070")
    left = wall("ece4d4", style=st, door=(46, 16, 22, "x", "glass"), signs=[(44, h - 12, "BANK", "2a4a3a", "f0d070", L >= 2)], seed=133)
    right = wall("e0d8c8", style=st, seed=134)
    building(cv, 14, 14, 112, 84, h, left, right, ("flat", "9a9488", "e8e0d0"))
    col = lambda a, v, nx, ny: (np.broadcast_to(C("f4f0e8"), a.shape + (3,)) * (0.9 + 0.1 * (np.floor(a * 6) % 2))[..., None],
                                nores(a.shape), None)
    for x in range(30, 100, 12):
        cv.cylinder(x, 92, 2.4, 0, h - 6, col)
    cv.box(24, 84, h - 6, 104, 98, h, flat("f4f0e8"), flat("e8e0d0"), flat("e8e0d0"))
    cv.gable(24, 84, 104, 98, h, 10, roof_tiles("e8e0d0", kind="slate"), flat("f4f0e8"), "y", 1)
    steps(cv, 26, 102, 98, 3)
    if L >= 2:
        building(cv, 30, 24, 96, 70, 22, wall("ece4d4", style=st, seed=135), wall("e0d8c8", style=st, seed=136),
                 ("flat", "9a9488", "e8e0d0"), z0=h)
    if L >= 3:
        dome(cv, 63, 47, h + 22, 16, "e8c050")
        flag(cv, 63, 47, h + 22 + 14, "3a8a5a")
    lamp_post(cv, 8, 112, 30)
    lamp_post(cv, 120, 112, 30)
    hedge(cv, 2, 4, 10, 80, 6, 137)
    return cv


def b_court(L):
    cv = Canvas(2, 170)
    lot(cv, "paved", 38)
    h = [36, 48, 48][L - 1]
    st = dict(brick=0.86, frame="f4f0e8", fh=24, ww=10, wh=14, sp=15, cornice="e8e0d0", plinth="6a5a50")
    left = wall("b86a4a", style=st, door=(40, 14, 20, "5a3a22"), signs=[(36, h - 11, "COURT", "f4f0e8", "5a2a1a", L >= 2)], seed=139)
    right = wall("a85a3a", style=st, seed=140)
    building(cv, 14, 16, 104, 82, h, left, right, ("hip", "4a5a6a", 18, "slate"))
    steps(cv, 36, 60, 82, 3)
    col = lambda a, v, nx, ny: solid_res(C("f4f0e8"), a.shape)
    for x in (36, 46, 52, 60):
        cv.cylinder(x, 88, 1.8, 0, 26, col)
    cv.box(32, 82, 26, 64, 92, 30, flat("f4f0e8"), flat("e8e0d0"), flat("e8e0d0"))
    if L >= 2:
        building(cv, 104, 30, 122, 70, 30, wall("b86a4a", style=st, seed=141, cols=1), wall("a85a3a", style=st, seed=142),
                 ("hip", "4a5a6a", 10, "slate"))
    if L >= 3:
        # clock tower
        tw = wall("b86a4a", style=dict(brick=0.86), windows=False, decals=[(2, 10, 14, 22, "f4f0e8")])
        cv.box(54, 40, h + 6, 70, 56, h + 40, tw, tw, flat("4a5a6a"))
        tower_cone(cv, 62, 48, 12, h + 40, 16, "4a5a6a")
    flower_patch(cv, 4, 96, 30, 124, 143)
    flower_patch(cv, 70, 96, 104, 124, 144)
    tree(cv, 116, 110, 0.9, "oak", 145)
    return cv


def enclosure(cv, x0, y0, x1, y1, kind="grass", seed=0):
    def fn(u, v, L_, D):
        if kind == "sand":
            rgb = np.broadcast_to(C("e0c890"), u.shape + (3,)) + ((hash2(np.floor(u), np.floor(v), seed) - 0.5) * 18)[..., None]
        elif kind == "snow":
            rgb = np.broadcast_to(C("e8eef4"), u.shape + (3,)) + ((hash2(np.floor(u), np.floor(v), seed) - 0.5) * 10)[..., None]
        else:
            rgb, _, _ = grass_fn(seed, 0.02)(u, v)
        return rgb, nores(u.shape), None
    cv.top(0.3, x0, y0, x1, y1, fn, shade=1.0)
    fence(cv, x0, y0, x1, y0, "8a6a4a", 6)
    fence(cv, x0, y1, x1, y1, "8a6a4a", 6)
    fence(cv, x0, y0, x0, y1, "8a6a4a", 6)
    fence(cv, x1, y0, x1, y1, "8a6a4a", 6)


def rock(cv, x, y, r=6, seed=0):
    w = int(2 * r + 2)
    ys, xs = np.mgrid[0:w, 0:w] + 0.5
    d = np.hypot(xs - w / 2, (ys - w / 2) * 1.2)
    H = np.where(d < r, np.sqrt(np.clip(r * r - d * d, 0, None)) * 0.7, -np.inf)
    cv.heightfield(x - w / 2, y - w / 2, H, lambda wx, wy, wz, nx, ny, nz: (
        np.broadcast_to(C("9a948c"), wx.shape + (3,)) * (0.9 + 0.2 * hash2(np.floor(wx / 2), np.floor(wy / 2), seed))[..., None],
        nores(wx.shape), None))


def b_zoo(L):
    cv = Canvas(2, 120)
    lot(cv, "grass", 46, lambda u, v: (np.abs(u - 64) < 7) | (np.abs(v - 64) < 7) & (u > 20), flowers=0.01)
    enclosure(cv, 6, 6, 56, 56, "grass", 147)
    rock(cv, 22, 20, 7, 1)
    tree(cv, 44, 16, 0.8, "oak", 148)
    enclosure(cv, 72, 6, 122, 56, "sand", 149)
    rock(cv, 100, 30, 9, 2)
    rock(cv, 112, 44, 5, 3)
    if L >= 2:
        enclosure(cv, 6, 72, 56, 122, "grass", 150)

        def water(u, v, L_, D):
            w = np.sin(u * 0.6 + v * 0.3)
            return np.where((w > 0.8)[..., None], C("a8d8f0"), C("4a8ac0")) * np.ones(u.shape + (3,)), nores(u.shape), None
        cv.top(0.6, 12, 84, 40, 110, water, extra=lambda u, v: ((u - 14) / 14) ** 2 + ((v - 13) / 13) ** 2 < 1)
        tree(cv, 48, 80, 0.8, "pine", 151)
    if L >= 3:
        enclosure(cv, 72, 72, 122, 122, "snow", 152)
        dome(cv, 97, 97, 0, 20, glass=True)
    # entrance arch with the sign
    post = wall("8a5a3a", windows=False, style=dict(plinth=None))
    cv.box(58, 116, 0, 62, 120, 26, post, post, flat("6a4a2a"))
    cv.box(66, 116, 0, 70, 120, 26, post, post, flat("6a4a2a"))
    sign = wall("3a7a3a", windows=False, style=dict(plinth=None), signs=[(3, 2, "ZOO", "3a7a3a", "f8f0c0", True)])
    cv.box(56, 117, 26, 72, 119, 34, sign, sign, flat("2a6a2a"))
    for k in range(4):
        cv.mark("pen%d" % k, *([(31, 31), (97, 31), (31, 97), (97, 97)][k]), 0)
    return cv


def b_ranch(L):
    cv = Canvas(2, 110)
    lot(cv, "grass", 51, flowers=0.01)
    barn(cv, 8, 8, 58, 48, 24, "8a3a2a")
    tank(cv, 70, 18, 8, 44, "b8b8b0")
    dome(cv, 70, 18, 44, 8, "8a8a90")
    fence(cv, 4, 60, 124, 60, "c8a070", 5)
    fence(cv, 4, 124, 124, 124, "c8a070", 5)
    fence(cv, 4, 60, 4, 124, "c8a070", 5)
    fence(cv, 124, 60, 124, 124, "c8a070", 5)

    def cow(x, y, seed, col="f4f0e8"):
        spots = lambda wx, wy, wz, nx, ny, nz: (np.where((hash2(np.floor(wx / 3), np.floor((wy + wz) / 3), seed) > 0.6)[..., None],
                                                         C("2a2a2a"), C(col)) * np.ones(wx.shape + (3,)), nores(wx.shape), None)
        cv.ellipsoid(x, y, 7, 7, 4, 3.6, spots)
        for (dx, dy) in ((-4, -2), (-4, 2), (4, -2), (4, 2)):
            cv.box(x + dx - 0.6, y + dy - 0.6, 0, x + dx + 0.6, y + dy + 0.6, 5, flat("e8e0d8"), flat("d8d0c8"), flat("e8e0d8"))
        cv.ellipsoid(x + 8, y, 9, 2.6, 2.2, 2.2, spots)
    n = [2, 3, 5][L - 1]
    for i, (x, y) in enumerate([(24, 80), (60, 100), (96, 78), (40, 112), (100, 108)][:n]):
        cow(x, y, 153 + i, "f4f0e8" if i % 3 else "a8784a")
    if L >= 2:
        def hay(a, v, nx, ny):
            return np.broadcast_to(C("e8c060"), a.shape + (3,)) * (0.9 + 0.1 * ((np.floor(v) % 3) == 0))[..., None], nores(a.shape), None
        for (x, y) in ((88, 20), (100, 30)):
            cv.cylinder(x, y, 5, 0, 8, hay, lambda a, b: solid_res(C("d8b050"), a.shape))
    if L >= 3:
        barn(cv, 86, 4, 122, 14, 16, "c8a040")
        units.car_body(cv, 80, 52, "px", "a83a2a", "pickup")
    return cv


def b_greenhouse(L):
    cv = Canvas(2, 90)
    lot(cv, "grass", 57)
    field(cv, 6, 96, 122, 124, "4f9a3e", "e84a3a", 58)
    g = glass_wall("f4f4f4", 59, fh=8, lit=0.25, panel=6)
    rows = [1, 2, 3][L - 1]
    for r in range(rows):
        y0 = 8 + r * 28
        cv.box(8, y0, 0, 82, y0 + 22, 14, g, g, flat("e8eef4"))
        cv.gable(8, y0, 82, y0 + 22, 14, 8, roof_tiles("c8e0e8", kind="metal"), g, "x", 0.5)
    if L >= 2:
        tank(cv, 104, 24, 8, 30, "6aa0c8")
    shed = wall("a87a4a", style=dict(siding=True), windows=False, door=(5, 10, 14, "6a4a2a"))
    building(cv, 92, 50, 122, 80, 18, shed, shed, ("gable", "6a5a4a", "x", 8, "metal"))
    crates(cv, 92, 84, 3, 60)
    return cv


def b_funfair(L):
    cv = Canvas(2, 210)
    lot(cv, "paved", 61)
    # carousel
    stripes = lambda a, v, nx, ny: (np.where(((np.floor(a * 4) % 2) == 0)[..., None], C("e84a5a"), C("f8f0e0")) * np.ones(a.shape + (3,)),
                                    nores(a.shape), None)
    cv.cylinder(34, 92, 18, 0, 4, lambda a, v, nx, ny: solid_res(C("c8a050"), a.shape),
                lambda a, b: solid_res(C("e8d0a0"), a.shape))
    cv.cylinder(34, 92, 2, 4, 22, lambda a, v, nx, ny: solid_res(C("e8c050"), a.shape))
    for k in range(8):
        ang = k * math.pi / 4
        x, y = 34 + math.cos(ang) * 12, 92 + math.sin(ang) * 12
        cv.cylinder(x, y, 0.6, 4, 22, lambda a, v, nx, ny: solid_res(C("e8c050"), a.shape))
        cv.ellipsoid(x, y, 10, 2.5, 2.5, 3, metal(["f8f0e0", "e8a040", "8ac0e8", "e86a8a"][k % 4]))
    w = 44
    ys, xs = np.mgrid[0:w, 0:w] + 0.5
    d = np.hypot(xs - w / 2, ys - w / 2)
    H = np.where(d < 21, 22 + 12 * (1 - d / 21), -np.inf)
    cv.heightfield(34 - w / 2, 92 - w / 2, H, lambda wx, wy, wz, nx, ny, nz: (
        np.where(((np.floor(np.arctan2(wy - 92, wx - 34) * 2.6) % 2) == 0)[..., None], C("e84a5a"), C("f8f0e0")) * np.ones(wx.shape + (3,)),
        nores(wx.shape), None), zmin=21, thick=3.0)
    for k in range(12):
        ang = k * math.pi / 6
        cv.ellipsoid(34 + math.cos(ang) * 21, 92 + math.sin(ang) * 21, 22, 1, 1, 1, lambda wx, wy, wz, nx, ny, nz: (
            np.broadcast_to(C("fff0b0"), wx.shape + (3,)).copy(), np.ones(wx.shape, bool),
            np.broadcast_to(np.array([255, 230, 150, 255.0]), wx.shape + (4,)).copy()))
    # ticket booth
    booth = wall("e8c050", windows=False, style=dict(plinth="8a6a3a"), decals=[(3, 11, 6, 12, "emit:fff0c0")])
    building(cv, 96, 98, 112, 112, 16, booth, booth, ("gable", "e84a5a", "x", 6))
    if L >= 2:
        # ferris wheel (vertical disc in the x-z plane)
        cx, cz, R = 78, 60, 46 if L == 3 else 38
        y = 30

        def wheel_mask(wx, wz):
            dx, dz = wx - cx, wz - cz
            r = np.hypot(dx, dz)
            ang = np.arctan2(dz, dx)
            ring = (np.abs(r - R) < 1.6) | (np.abs(r - R + 5) < 0.9)
            spokes = (r < R) & (np.abs(((ang * 8 / math.pi) + 0.5) % 1 - 0.5) < 0.6 / np.maximum(r, 1) * 8 / math.pi)
            return ring | spokes | (r < 3.5)
        cv.face_y(y, cx - R - 2, cx + R + 2, cz - R - 2, cz + R + 2,
                  lambda u, v, L_, H_: solid_res(C("f4f4f8"), u.shape), extra=wheel_mask)
        for k in range(10 if L == 3 else 8):
            ang = k * math.tau / (10 if L == 3 else 8)
            gx, gz = cx + math.cos(ang) * R, cz + math.sin(ang) * R
            col = ["e84a5a", "3a8ad8", "f0c040", "4ab06a", "b06ae0"][k % 5]
            cv.box(gx - 3, y - 3, gz - 7, gx + 3, y + 3, gz - 1, flat(col), flat(col), flat(C(col) * 1.1))
        for (x0, x1) in ((cx - 26, cx - 22), (cx + 22, cx + 26)):
            cv.box(x0, y - 6, 0, x1, y - 2, cz, flat("c8c8d0"), flat("b8b8c0"), flat("d8d8e0"))
            cv.box(x0, y + 2, 0, x1, y + 6, cz, flat("c8c8d0"), flat("b8b8c0"), flat("d8d8e0"))
    if L >= 3:
        # balloon seller and fairy lights
        for k, c in enumerate(("e84a5a", "3a8ad8", "f0c040", "4ab06a", "b06ae0")):
            bx, by = 58 + (k % 3) * 3, 70 + (k // 3) * 3
            cv.cylinder(bx, by, 0.3, 0, 22 + k, lambda a, v, nx, ny: solid_res(C("f4f4f4"), a.shape))
            cv.ellipsoid(bx, by, 25 + k, 2.4, 2.4, 3, metal(c))
        for x in range(10, 120, 6):
            cv.ellipsoid(x, 124, 14 + 3 * math.sin(x / 9), 0.9, 0.9, 0.9, lambda wx, wy, wz, nx, ny, nz: (
                np.broadcast_to(C("fff0b0"), wx.shape + (3,)).copy(), np.ones(wx.shape, bool),
                np.broadcast_to(np.array([255, 220, 140, 255.0]), wx.shape + (4,)).copy()))
    if L == 1:
        # spinning cups ride at the back
        cv.cylinder(92, 36, 20, 0, 3, lambda a, v, nx, ny: solid_res(C("8ac0e8"), a.shape),
                    lambda a, b: solid_res(C("c8e4f4"), a.shape))
        for k in range(6):
            ang = k * math.tau / 6
            cv.cylinder(92 + math.cos(ang) * 12, 36 + math.sin(ang) * 12, 4.5, 3, 9,
                        lambda a, v, nx, ny, k=k: solid_res(C(["e84a5a", "f0c040", "4ab06a"][k % 3]), a.shape),
                        lambda a, b: solid_res(C("f8f0e0"), a.shape))
        cv.cylinder(92, 36, 1.2, 3, 16, lambda a, v, nx, ny: solid_res(C("e8c050"), a.shape))
    for (x, y, c) in ((8, 64, "3a8ad8"), (8, 40, "4ab06a")):
        stall = wall("f8f0e0", windows=False, style=dict(plinth="8a6a3a"), decals=[(2, 10, 5, 9, "emit:fff0c0")])
        building(cv, x, y, x + 14, y + 12, 12, stall, stall, ("flat", "f8f0e0", "f8f0e0"))
        awning(cv, x, x + 14, y + 12, 12, 4, 2, c)
    umbrella_table(cv, 66, 112, "f0c040")
    tree(cv, 120, 120, 0.8, "sakura", 62)
    return cv


# ====================================================================== scaffold
def b_scaffold(n):
    cv = Canvas(n, 100 if n == 2 else 70)

    def dirt(u, v, L, D):
        return (np.broadcast_to(C("9a6a40"), u.shape + (3,)) + ((hash2(np.floor(u), np.floor(v), 2) - 0.5) * 22)[..., None],
                nores(u.shape), None)
    cv.ground(dirt)
    s = n * U
    hh = 44 if n == 1 else 70
    pole = flat("d8a040", 6)
    plank = flat("a87040", 12)
    wallc = wall("b8b0a0", style=dict(brick=0.85, plinth=None), windows=False)
    cv.box(10, 10, 0, s - 10, s - 10, hh * 0.45, wallc, wallc, flat("8a8278"))
    for (x, y) in ((6, 6), (s - 9, 6), (6, s - 9), (s - 9, s - 9), (s / 2, s - 9), (s - 9, s / 2)):
        cv.box(x, y, 0, x + 2.5, y + 2.5, hh, pole, pole, pole)
    for z in (hh * 0.35, hh * 0.7, hh * 0.98):
        cv.box(6, s - 9, z, s - 6, s - 5, z + 2, plank, plank, plank)
        cv.box(s - 9, 6, z, s - 5, s - 6, z + 2, plank, plank, plank)
    for (x, y) in ((12, s - 2), (s - 2, 14)):
        cv.box(x - 6, y - 6, 0, x, y, 5, flat("c8783a"), flat("a8582a"), flat("d8885a"))
    if n == 2:
        cv.box(s - 20, 14, 0, s - 16, 18, 96, pole, pole, pole)
        cv.box(16, 14, 92, s - 16, 18, 96, pole, pole, flat("f8c840"))
        cv.cylinder(30, 16, 0.4, 70, 92, lambda a, v, nx, ny: solid_res(C("2a2a2a"), a.shape))
        cv.box(26, 12, 64, 34, 20, 70, flat("6a6a74"), flat("5a5a64"), flat("7a7a84"))
        # cement mixer
        cv.cylinder(100, 100, 6, 0, 10, lambda a, v, nx, ny: solid_res(C("e86a2a"), a.shape),
                    lambda a, b: solid_res(C("8a8a8a"), a.shape))
    return cv


BUILDERS = {
    "house_small": b_house_small, "cottage": b_cottage, "bungalow": b_bungalow, "townhouse": b_townhouse,
    "villa": b_villa, "apartments": b_apartments, "condo": b_condo, "tower": b_tower,
    "bakery": b_bakery, "cafe": b_cafe, "flowershop": b_flowershop, "pizzeria": b_pizzeria, "boutique": b_boutique,
    "supermarket": b_supermarket, "restaurant": b_restaurant, "cinema": b_cinema, "mall": b_mall,
    "farm": b_farm, "orchard": b_orchard, "sawmill": b_sawmill, "workshop": b_workshop, "factory": b_factory,
    "logistics": b_logistics,
    "school": b_school, "fire_station": b_fire_station, "police": b_police, "hospital": b_hospital, "town_hall": b_town_hall,
    "tree": b_tree, "flowerbed": b_flowerbed, "lamp": b_lamp, "bench": b_bench, "fountain": b_fountain, "park": b_park,
    "statue": b_statue,
    "bank": b_bank, "court": b_court, "zoo": b_zoo, "ranch": b_ranch, "greenhouse": b_greenhouse, "funfair": b_funfair,
}
