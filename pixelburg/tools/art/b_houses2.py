"""Houses from around the world, dachas with big plots and a tower of stacked villas. builder(L, o) -> Canvas."""
import numpy as np

from raster import C, U, Canvas, flat, nores, hash2, glow_res
from arch import Orient, facade, Win, roof_mat, flat_top
import kit
from bkit import (door, entry, ground, tree, bush, hedge, fence, flowerbed, mailbox, lamp, bench, bins, box, slab,
                  post, canopy, steps, balconies, glass_rail)
from b_towers import pool, palm, solid_side


# ====================================================================== American suburban house
def house_american(L, o):
    """White clapboard two-storey house with a columned front porch, a garage and a lawn behind a picket fence."""
    cv = Canvas(1, 170)
    T = Orient(cv, o)
    seed = 1101
    wallc = ["f4f2ec", "eef0f2", "e8eef4"][L - 1]
    roofc = ["5a5e66", "4a4e58", "6a5040"][L - 1]
    win = Win(w=12, h=16, sill=8, sp=24, margin=12, fh=30, shutters="2a4a6a", frame="ffffff")
    fr = facade("wood", wallc, win=win, doors=[(28, 11, 22, "wood", "8a2a2a")], seed=seed, plinth=("9a948a", 4),
                bands=[(30, 32, "ffffff")])
    sd = facade("wood", wallc, win=win, seed=seed + 1, plinth=("9a948a", 4), bands=[(30, 32, "ffffff")])
    s0, s1, f0, f1 = 20, 104, 56, 124
    H = 58 if L >= 2 else 34
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd)
    T.gable(s0, f0, s1, f1, H, 30, roof_mat(roofc, "shingle"), dict(front=fr, back=sd, left=sd, right=sd), ridge="s", o=5)
    # porch along the front with white columns
    slab(T, s0, f0 - 20, s1, f0, 0, 4, "e8e2d6")
    slab(T, s0 - 2, f0 - 22, s1 + 2, f0, 26, 29, "ffffff", flat(roofc))
    for s in (s0 + 2, s0 + 40, s1 - 4):
        post(T, s, f0 - 19, 4, 26, "ffffff", 2.4)
    T.panel(s0, s1, f0 - 20, 4, 11, lambda u, v, LL, HH: (C("ffffff") * np.ones(u.shape + (3,)), nores(u.shape), None), "s",
            lambda u, v: ((u % 4) < 1.2) | (v > 6))
    steps(T, s0 + 24, s0 + 42, f0 - 20, 2, 4, "e8e2d6")
    door(T, s0 + 28, 11, f0, 22)
    entry(T, s0 + 33)
    # garage with a driveway
    g = facade("wood", wallc, doors=[(4, 40, 22, "garage", "f4f2ec")], seed=seed + 3, plinth=("9a948a", 4))
    box(T, s1 + 2, f0 + 4, 156, f0 + 60, 0, 26, all=g, top=flat_top("6a6c72", "ffffff", 2))
    ground(T, s1 + 4, 0, 154, f0 + 4, kit.paving("b8b4ac", 12.0, 3))
    ground(T, s0 + 26, 0, s0 + 40, f0 - 22, kit.paving("c8c0b0", 6.0))
    fence(T, 2, s1, 2, "s", "ffffff", gap=(s0 + 24, s0 + 42))
    mailbox(T, s0 + 50, 8, "2a4a8a")
    if L >= 2:
        bush(T, 10, 40, 1.0, seed, "e86a8a")
        tree(T, 20, 140, "maple", 0.9, seed + 1)
    if L >= 3:
        x, y = T.pt(80, 146)
        kit.swing(cv, x - 12, y)
        flowerbed(T, s0 + 46, f0 - 34, s1 - 4, f0 - 24, seed + 2)
    return cv


# ====================================================================== Asian house: tiled hip roof, wood and paper screens, garden
def house_asian(L, o):
    """A Japanese-style house: dark wood frame, paper screens, a wide tiled hip roof with upturned eaves, a stone garden."""
    cv = Canvas(1, 160)
    T = Orient(cv, o)
    seed = 1121
    wood = ["6a4a32", "5a3e2a", "4a3424"][L - 1]

    def screens(u, v, LL, HH):
        rgb = np.broadcast_to(C("f2ece0"), u.shape + (3,)).copy()
        frame = (np.mod(u, 24) < 2.5) | (v < 3) | (v > HH - 3) | (np.abs(v - HH * 0.5) < 1.0)
        grid = (np.mod(u, 6) < 0.8) | (np.mod(v, 6) < 0.8)
        rgb[grid] = C("c8b8a0")
        rgb[frame] = C(wood)
        em = np.zeros(u.shape + (4,))
        em[~frame & ~grid] = np.array([255, 226, 170, 150.0])
        return rgb, nores(u.shape), em
    s0, s1, f0, f1 = 34, 126, 50, 120
    H = 40 if L < 3 else 64
    slab(T, s0 - 8, f0 - 10, s1 + 8, f1 + 6, 0, 6, "8a7e70")   # raised stone platform
    box(T, s0, f0, s1, f1, 6, H, all=screens, top=flat(wood))
    for s in range(s0, s1 + 1, 23):
        post(T, s, f0 - 1, 6, H, wood, 3)
    if L >= 3:
        # a skirt roof between the two floors
        T.hip(s0 - 4, f0 - 6, s1 + 4, f1 + 4, 38, 6, roof_mat("4a505a", "tiles"), o=7)
    T.hip(s0 - 6, f0 - 8, s1 + 6, f1 + 6, H, 18, roof_mat("4a505a", "tiles"), o=7)
    # ridge ornaments
    for s in (s0 + 6, s1 - 6):
        x, y = T.pt(s, (f0 + f1) / 2)
        T.cv.ellipsoid(x, y, H + 18, 3, 3, 4, lambda wx, wy, wz, nx, ny, nz: (C("2a2e36") * np.ones(wx.shape + (3,)), nores(wx.shape), None))
    door(T, s0 + 36, 20, f0, 22)
    entry(T, s0 + 46)
    # garden: gravel, stepping stones, a stone lantern, a blossoming tree
    ground(T, 4, 0, 156, f0 - 10, kit.gravel("d8d2c4"))
    for k in range(4):
        x0, y0 = T.pt(s0 + 44, 8 + k * 9)
        T.cv.cylinder(x0, y0, 4, 0, 1.5, solid_side("9a948a"), cap=lambda u, v: (C("aaa49a") * np.ones(u.shape + (3,)), nores(u.shape), None))
    lx, ly = T.pt(20, 24)
    T.cv.cylinder(lx, ly, 2, 0, 12, solid_side("8a8478"))
    T.box(14, 18, 26, 30, 12, 18, all=lambda u, v, LL, HH: glow_res("ffe0a0", u.shape), top=flat("6a645a"))
    T.box(12, 16, 28, 32, 18, 21, all=flat("6a645a"), top=flat("6a645a"))
    tree(T, 140, 26, "fruit", 0.8, seed, "f4b8c8")
    if L >= 2:
        bush(T, 120, 10, 0.8, seed + 1)
        tree(T, 140, 140, "pine", 0.8, seed + 2)
    if L >= 3:
        pool(T, 96, 6, 124, 30)
    return cv


# ====================================================================== Tajik house: courtyard, carved ayvan, flat roof
def house_tajik(L, o):
    """A traditional Tajik house: whitewashed walls, a flat roof, an ayvan veranda on carved painted columns,
    blue doors and windows, a courtyard with a tapchan, an apricot tree and a grapevine."""
    cv = Canvas(1, 140)
    T = Orient(cv, o)
    seed = 1141
    wallc = ["efe6d4", "f4ecdc", "f6f0e4"][L - 1]
    blue = "2a6ab0"
    win = Win(w=12, h=16, sill=9, sp=24, margin=14, fh=30, frame=blue, style="cross")
    fr = facade("plaster", wallc, win=win, doors=[(42, 12, 22, "double", blue)], seed=seed, plinth=("b8a888", 6))
    sd = facade("plaster", wallc, win=win, seed=seed + 1, plinth=("b8a888", 6))
    s0, s1, f0, f1 = 40, 150, 90, 150
    H = 32 if L < 3 else 60
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("a89478", wallc, 4))
    # ayvan: a deep veranda with carved columns painted in bands
    def column_paint(a, z, nx, ny):
        band = np.mod(z, 8) < 2
        rgb = np.where(band[..., None], C("c8342a"), C("b07a40")) * np.ones(a.shape + (3,))
        rgb = np.where((np.mod(z, 8) > 5)[..., None], C(blue), rgb)
        return rgb, nores(a.shape), None
    slab(T, s0, f0 - 26, s1, f0, 0, 3, "c8b898")
    for s in (s0 + 4, s0 + 40, s0 + 76, s1 - 4):
        x, y = T.pt(s, f0 - 23)
        T.cv.cylinder(x, y, 2.2, 3, 28, column_paint)
    slab(T, s0 - 2, f0 - 28, s1 + 2, f0, 28, 32, "8a5a34", flat("a89478"))
    # carved, painted frieze along the edge of the veranda roof
    T.panel(s0 - 2, s1 + 2, f0 - 28, 24, 28, lambda u, v, LL, HH: (np.where(((np.mod(u, 6) < 3) ^ (v > 2))[..., None], C("2a6ab0"), C("e8c050"))
                                                                   * np.ones(u.shape + (3,)), nores(u.shape), None), "s")
    door(T, s0 + 42, 12, f0, 22)
    # courtyard wall (duval) with a blue gate
    duval = facade("plaster", "e2d4b8", seed=seed + 3, plinth=None)
    T.box(2, 2, 60, 6, 0, 18, all=duval, top=flat("c8b898"))
    T.box(84, 2, 158, 6, 0, 18, all=duval, top=flat("c8b898"))
    T.box(60, 2, 84, 5, 0, 22, all=lambda u, v, LL, HH: (C(blue) * (0.9 + 0.1 * (np.mod(u, 4) < 2))[..., None] * np.ones(u.shape + (1,)),
                                                        nores(u.shape), None), top=flat(blue))
    entry(T, 72)
    ground(T, 6, 6, 156, f0 - 26, kit.paving("d8c8a8", 10.0, 3))
    # tapchan: a raised wooden platform with a red carpet and a low table
    slab(T, 100, 30, 146, 58, 0, 9, "8a5a34")
    T.flat(102, 32, 144, 56, 9.2, lambda u, v, LL, D: (np.where((np.mod(u + v, 8) < 4)[..., None], C("b8282a"), C("8a1a24"))
                                                       * np.ones(u.shape + (1,)), nores(u.shape), None))
    slab(T, 116, 38, 130, 50, 9, 13, "6a4028")
    tree(T, 20, 40, "fruit", 0.85, seed, "f8e0a0")     # apricot
    if L >= 2:
        # grapevine trellis over the yard
        for s in (14, 54):
            post(T, s, 70, 0, 30, "6a4a30", 1.6)
        T.flat(10, 50, 58, 74, 30, lambda u, v, LL, D: (np.where((hash2(np.floor(u / 3), np.floor(v / 3), 7) > 0.35)[..., None], C("4a8a3a"),
                                                                  C("6a4a30")) * np.ones(u.shape + (1,)), nores(u.shape), None))
    if L >= 3:
        flowerbed(T, 64, 12, 96, 24, seed + 4)
    return cv


# ====================================================================== dacha: a little country house on a big plot
def dacha(L, o):
    """A wooden dacha on a big plot: vegetable beds, fruit trees, a greenhouse, a well, a picket fence."""
    cv = Canvas(2, 140)
    T = Orient(cv, o)
    seed = 1161
    wood = ["9a6a40", "8a5a34", "a87a4a"][L - 1]
    win = Win(w=12, h=14, sill=9, sp=26, margin=12, fh=30, frame="ffffff", shutters="4a8a5a")
    fr = facade("wood", wood, win=win, doors=[(20, 11, 22, "wood", "5a3a24")], seed=seed, plinth=("6a5a4a", 4))
    sd = facade("wood", wood, win=win, seed=seed + 1, plinth=("6a5a4a", 4))
    s0, s1, f0, f1 = 200, 290, 200, 280
    H = 30 if L < 3 else 50
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd)
    T.gable(s0, f0, s1, f1, H, 30, roof_mat(["5a7a5a", "8a3a2a", "4a5a7a"][L - 1], "metal"), dict(front=fr, back=sd, left=sd, right=sd),
            ridge="s", o=6)
    slab(T, s0, f0 - 16, s1 - 30, f0, 0, 4, "a8946a")      # little veranda
    for s in (s0 + 2, s1 - 32):
        post(T, s, f0 - 14, 4, 24, "8a6a44", 2)
    slab(T, s0 - 2, f0 - 18, s1 - 28, f0, 24, 26, wood, flat("6a5a4a"))
    door(T, s0 + 20, 11, f0, 22)
    entry(T, 250)
    # the plot: grass, vegetable beds in rows, a path to the gate
    ground(T, 4, 4, 316, 316, kit.paving("8aa858", 12.0, 2))

    def beds(u, v, LL, D):
        row = np.mod(v, 14) < 9
        rgb = np.where(row[..., None], C("6a4a30"), C("8aa858")) * np.ones(u.shape + (1,))
        sprout = row & (np.mod(u, 7) < 3) & (np.mod(v, 14) > 2) & (np.mod(v, 14) < 7)
        rgb[sprout] = C("4a9a3a")
        return rgb, nores(u.shape), None
    ground(T, 24, 120, 170, 290, beds, z=0.5)
    ground(T, 240, 0, 258, f0 - 16, kit.paving("c8b898", 6.0), z=0.6)
    # greenhouse
    gh = lambda u, v, LL, HH: (C("c8e0e8") * np.ones(u.shape + (3,)), nores(u.shape), None)
    T.box(24, 30, 120, 90, 0, 20, all=gh, top=flat("d8ecf0"))
    T.gable(24, 30, 120, 90, 20, 12, roof_mat("d8ecf0", "metal"), gh, ridge="s", o=1)
    # fruit trees and a well
    for k, (s, f) in enumerate(((150, 40), (190, 100), (290, 120), (130, 300))):
        tree(T, s, f, "fruit", 0.8, seed + k, ["f4f0f0", "f4b8c8", "f8e0a0", "f4f0f0"][k])
    wx, wy = T.pt(290, 40)
    T.cv.cylinder(wx, wy, 8, 0, 10, solid_side("8a8478"))
    for d in (-6, 6):
        post(T, 290 + d, 40, 10, 24, "6a4a30", 1.4)
    T.box(282, 34, 298, 46, 24, 27, all=flat("8a3a2a"), top=flat("8a3a2a"))
    fence(T, 4, 316, 4, "s", "c8a878", gap=(236, 262))
    fence(T, 4, 316, 316, "s", "c8a878")
    fence(T, 4, 316, 4, "f", "c8a878")
    fence(T, 4, 316, 316, "f", "c8a878")
    if L >= 2:
        bench(T, 180, 230, "f", "8a5a34")
    if L >= 3:
        x, y = T.pt(160, 250)
        kit.swing(cv, x - 12, y)
    return cv


# ====================================================================== sky_villa: a tower of stacked villas
def sky_villa(L, o):
    """A luxury tower of stacked villas: each two-storey villa has stone walls, warm wood, a terracotta roof edge,
    a terrace with a private pool and a garden; the villas turn as they rise; a penthouse villa crowns it."""
    villas = [5, 7, 9][L - 1]
    fh = 30
    vh = 2 * fh
    cv = Canvas(2, villas * vh + 200)
    T = Orient(cv, o)
    seed = 1181
    stone = "ece2d0"
    wood = "8a5a34"
    win = Win(w=26, h=24, sill=4, sp=32, margin=8, fh=fh, frame=wood, style="vertical", tint="6a8aa8", group="flats", top_skip=2)
    ground(T, 0, 0, 320, 320, kit.paving("d8d0c0", 12.0, 4))
    # core with the lifts
    core = facade("stone", "d8cfc0", plinth=None, seed=seed)
    box(T, 130, 150, 190, 210, 0, villas * vh + 10, all=core, top=flat("c8bfb0"))
    lobby = facade("stone", stone, doors=[(60, 50, 30, "double_glass")], win=Win(w=24, h=22, sill=6, sp=30, margin=8, fh=40,
                                                                                       frame=wood, group="work"), plinth=None, seed=seed + 1)
    box(T, 50, 70, 270, 250, 0, 40, all=lobby, top=flat_top("6e9a5a", stone, 5))
    door(T, 110, 50, 70, 30)
    entry(T, 135)
    shifts = [(0, 0), (30, 20), (-20, 30), (-30, -10), (20, -30), (30, 25), (-25, 20), (-30, -20), (10, -30)]
    for k in range(villas):
        z = 40 + k * vh
        ds, df = shifts[k]
        s0, s1, f0, f1 = 60 + ds, 260 + ds, 90 + df, 230 + df
        fa = facade("stone", stone, win=win, seed=seed + 2 + k, plinth=None, bands=[(fh - 2, fh + 2, wood)])
        # the villa covers part of the floor, the rest is its terrace
        box(T, s0 + 70, f0, s1, f1, z, z + vh, all=fa, top=flat("b8643a"))
        slab(T, s0, f0, s1, f1, z - 4, z, "f4ece0")
        pool(T, s0 + 6, f0 + 10, s0 + 64, f0 + 60)
        bush(T, s0 + 20, f1 - 20, 0.6, seed + k, "e86a8a")
        T.panel(s0, s0 + 70, f0, z, z + 9, glass_rail, "s")
        T.panel(f0, f1, s0, z, z + 9, glass_rail, "f")
        # terracotta eaves around the villa roof
        T.box(s0 + 66, f0 - 4, s1 + 4, f1 + 4, z + vh, z + vh + 3, all=flat("b8643a"), top=flat("c8744a"))
    # penthouse with a hip roof
    zt = 40 + villas * vh
    pf = facade("stone", stone, win=Win(w=26, h=26, sill=4, sp=32, margin=8, fh=34, frame=wood, style="vertical", tint="8ab0c8",
                                        group="work"), plinth=None, seed=seed + 40, lit=0.9)
    box(T, 100, 120, 220, 240, zt, zt + 34, all=pf, top=flat("b8643a"))
    T.hip(94, 114, 226, 246, zt + 34, 26, roof_mat("b8643a", "tiles"), o=6)
    for k, (s, f) in enumerate(((20, 30), (300, 30), (20, 300), (300, 300))):
        palm(T, s, f, 56, seed + k)
    lamp(T, 100, 16, "modern", 50)
    lamp(T, 220, 16, "modern", 50, "light2")
    return cv


BUILDERS = {"house_american": house_american, "house_asian": house_asian, "house_tajik": house_tajik, "dacha": dacha,
            "sky_villa": sky_villa}
