"""Homes at real scale. Each builder(L, o) returns a Canvas: L = level 1..3, o = orientation."""
import numpy as np

from raster import C, U, Canvas, flat, solid_res
from arch import Orient, facade, Win, roof_mat, flat_top
import kit
from bkit import (door, entry, ground, tree, bush, hedge, fence, flowerbed, mailbox, lamp, bench, bins, box, slab,
                  post, canopy, steps, balconies, roof_units, parking_lot, glass_rail)

S = U  # 160 units = 16 m


# ====================================================================== little house
def house_small(L, o):
    cv = Canvas(1, 150)
    T = Orient(cv, o)
    seed = 11
    wallc = ["efe4cc", "f2ead8", "f4efe6"][L - 1]
    roofc = ["b8503a", "a8473a", "5a5e66"][L - 1]
    shut = [None, "4a7a9a", "3e5e7a"][L - 1]
    win = Win(w=12, h=14, sill=9, sp=26, margin=14, fh=30, shutters=shut, boxes=L >= 2)
    s0, s1 = 30, 118 if L < 3 else 122
    f0, f1 = 46, 118 if L < 3 else 124
    wall_h = 32 if L == 1 else 36 if L == 2 else 62
    door_s = s0 + 30
    front = facade("plaster", wallc, win=win, doors=[(door_s - s0, 10, 22, "wood", "7a4a2a" if L < 3 else "3e5a6e")],
                   seed=seed, plinth=("8a8478", 5))
    side = facade("plaster", wallc, win=Win(w=12, h=14, sill=9, sp=26, margin=16, shutters=shut), seed=seed + 1)
    back = facade("plaster", wallc, win=Win(w=12, h=14, sill=9, sp=24, margin=12, shutters=shut),
                  doors=[(50, 10, 22, "glass")], seed=seed + 2)
    walls = dict(front=front, back=back, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, wall_h, **walls)
    rh = 34 if L < 3 else 36
    T.gable(s0, f0, s1, f1, wall_h, rh, roof_mat(roofc, "tiles" if L < 3 else "slate"), walls, ridge="s", o=5)
    cx, cy = T.pt(s1 - 22, (f0 + f1) / 2 + 4)
    kit.chimney(cv, cx - 3, cy - 3, wall_h + rh * 0.45, 22, "9a5a44", "chimney")
    canopy(T, door_s - 6, door_s + 16, f0, 14, 25)
    steps(T, door_s - 4, door_s + 14, f0, 2, 4)
    door(T, door_s, 10, f0, 22)
    ground(T, door_s - 2, 0, door_s + 12, f0 - 8, kit.paving("c8bcaa", 6.0))
    entry(T, door_s + 5)
    fence(T, 2, 158, 2, "s", gap=(door_s - 3, door_s + 13))
    mailbox(T, door_s + 18, 6)
    flowerbed(T, s0 + 2, f0 - 12, door_s - 8, f0 - 2, seed=1)
    if L == 1:
        bush(T, 140, 30, 1.0, 2, "e86a8a")
        tree(T, 136, 140, "fruit", 0.75, 4, "f4f0f0")
        bins(T, 14, 120)
    if L >= 2:
        g0, g1 = s1 + 2, 156
        gf0, gf1 = f0 + 6, f0 + 64
        gfront = facade("plaster", wallc, doors=[(4, g1 - g0 - 8, 22, "garage", "e8e4dc")], seed=seed + 4, plinth=("8a8478", 4))
        gside = facade("plaster", wallc, seed=seed + 5)
        box(T, g0, gf0, g1, gf1, 0, 28, front=gfront, back=gside, left=gside, right=gside, top=flat_top("7a7672", "c8c2b8"))
        ground(T, g0 + 2, 0, g1 - 2, gf0, kit.paving("b4aea4", 10.0, 3))
        bush(T, 14, 30, 1.1, 3, "f2c440")
        tree(T, 20, 138, "maple", 0.9, 5)
    if L >= 3:
        hedge(T, 2, 60, 8, 156, 14, 2)
        flowerbed(T, door_s + 16, f0 - 12, s1 - 2, f0 - 2, seed=2)
        x, y = T.pt(118, 140)
        kit.swing(cv, x - 12, y) if T.o in (0, 2) else kit.laundry(cv, x - 13, y, 26)
    return cv


# ====================================================================== cottage: two storeys, porch, gable to the street
def cottage(L, o):
    cv = Canvas(1, 190)
    T = Orient(cv, o)
    seed = 21
    mat = ["siding", "siding", "brick"][L - 1]
    wallc = ["d8e4ea", "f0e2c4", "b4644a"][L - 1]
    roofc = ["5a5e66", "6a4a3a", "3e4248"][L - 1]
    s0, s1, f0, f1 = 40, 112, 50, 136
    wall_h = 58
    win = Win(w=12, h=15, sill=9, sp=24, margin=12, fh=30, frame="f4f2ee", boxes=L >= 2)
    door_s = s0 + 30
    front = facade(mat, wallc, win=win, doors=[(door_s - s0, 10, 22, "wood", "3e5a6e" if L != 2 else "8a3a2a")], seed=seed)
    side = facade(mat, wallc, win=Win(w=12, h=15, sill=9, sp=26, margin=14, frame="f4f2ee"), seed=seed + 1)
    back = facade(mat, wallc, win=Win(w=12, h=15, sill=9, sp=24, margin=12, frame="f4f2ee"), doors=[(30, 10, 22, "glass")], seed=seed + 2)
    walls = dict(front=front, back=back, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, wall_h, **walls)
    gwin = facade(mat, wallc, win=Win(w=12, h=15, sill=4, sp=24, margin=24, fh=40, cols=1, frame="f4f2ee"), plinth=None, seed=seed + 3)
    T.gable(s0, f0, s1, f1, wall_h, 34, roof_mat(roofc, "shingle"), dict(front=gwin, back=gwin, left=side, right=side), ridge="f", o=5)
    cx, cy = T.pt(s0 + 10, f0 + 50)
    kit.chimney(cv, cx - 3, cy - 3, wall_h + 10, 34, "8a5a44", "chimney")
    # porch across the front
    pz = 28
    slab(T, s0 - 4, f0 - 20, s1 + 4, f0, 0, 4, "c8bca8")
    slab(T, s0 - 6, f0 - 22, s1 + 6, f0, pz, pz + 3, "f2eee6", flat("6a6e76" if L != 2 else "7a5a44", 3))
    for ps in (s0 - 3, door_s - 6, door_s + 16, s1 + 2):
        post(T, ps, f0 - 19, 4, pz, "f2eee6", 2.0)
    rail = lambda u, v, LL, H: solid_res(C("f2eee6"), u.shape)
    T.panel(s0 - 3, door_s - 6, f0 - 19, 4, 13, rail, "s", lambda u, v: ((u % 3) < 0.9) | (v > 7.5))
    T.panel(door_s + 16, s1 + 2, f0 - 19, 4, 13, rail, "s", lambda u, v: ((u % 3) < 0.9) | (v > 7.5))
    steps(T, door_s - 4, door_s + 14, f0 - 20, 2, 4)
    door(T, door_s, 10, f0, 22)
    ground(T, door_s - 2, 0, door_s + 12, f0 - 28, kit.paving("c4b8a4", 6.0))
    entry(T, door_s + 5)
    hedge(T, 2, 2, door_s - 6, 9, 10, 1)
    hedge(T, door_s + 16, 2, 158, 9, 10, 2)
    mailbox(T, door_s + 20, 12, "c84a3a")
    tree(T, 138, 120, "birch" if L != 3 else "oak", 0.9, 6)
    if L >= 2:
        flowerbed(T, s1 + 8, f0, 154, f0 + 40, seed=3)
        bush(T, 20, 120, 1.0, 7, "f4f0f0")
        x, y = T.pt(20, 150)
        kit.wheelie_bins(cv, x - 7, y - 3)
    if L >= 3:
        # bay window and a pergola in the back
        bay = facade(mat, wallc, win=Win(w=14, h=16, sill=8, sp=18, margin=3, frame="f4f2ee"), seed=seed + 6, plinth=("6a5a50", 4))
        box(T, s1 - 22, f0 + 30, s1 + 8, f0 + 60, 0, 28, front=bay, right=bay, back=bay, left=bay, top=flat("3e4248", 3))
        for (ps, pf) in ((50, 140), (110, 140), (50, 156), (110, 156)):
            post(T, ps, pf, 0, 26, "8a6a48", 2.0)
        for k in range(8):
            slab(T, 48, 139 + k * 2.4, 112, 140 + k * 2.4, 26, 27.5, "8a6a48")
    return cv


# ====================================================================== bungalow -> modern single-storey house
def bungalow(L, o):
    cv = Canvas(1, 150)
    T = Orient(cv, o)
    seed = 31
    wallc = ["f4f2ee", "eeeae4", "e8e6e2"][L - 1]
    wood = facade("wood", "a8784a", plinth=None, seed=seed + 9)
    s0, s1, f0, f1 = 22, 132, 46, 128
    h1 = 34
    big = Win(w=26, h=22, sill=4, sp=34, margin=10, fh=34, frame="3a3a40", style="vertical")
    door_s = s0 + 70
    front = facade("plaster", wallc, win=big, doors=[(door_s - s0, 12, 24, "wood", "6a4a30")], seed=seed, plinth=("6a6a70", 3))
    side = facade("plaster", wallc, win=Win(w=20, h=18, sill=8, sp=30, margin=14, fh=34, frame="3a3a40", style="vertical"), seed=seed + 1,
                  plinth=("6a6a70", 3))
    back = facade("plaster", wallc, win=Win(w=36, h=24, sill=2, sp=44, margin=8, fh=34, frame="3a3a40", style="vertical"), seed=seed + 2,
                  plinth=("6a6a70", 3))
    walls = dict(front=front, back=back, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, h1, **walls, top=flat_top("6e6c6a", "d8d4cc", 3))
    # wooden accent block at the entrance
    box(T, door_s - 10, f0 - 6, door_s + 26, f0 + 20, 0, h1 + 4, front=facade("wood", "a8784a", plinth=None,
        doors=[(10, 12, 24, "wood", "4a3424")], seed=seed + 7), back=wood, left=wood, right=wood, top=flat_top("5a5856", "c8c4bc", 2))
    door(T, door_s, 12, f0 - 6, 24)
    canopy(T, door_s - 14, door_s + 30, f0 - 6, 10, 30, "3a3a40", "3a3a40", posts=False)
    ground(T, door_s - 2, 0, door_s + 14, f0 - 6, kit.paving("8a8a8a", 10.0, 7, 0.6))
    entry(T, door_s + 6)
    # carport with a driveway
    ground(T, 136, 0, 158, 120, kit.paving("a8a49c", 12.0, 5))
    for pf in (20, 70):
        post(T, 156, pf, 0, 28, "3a3a40", 2.2)
    slab(T, 134, 16, 159, 76, 28, 30, "3a3a40")
    fence(T, 2, 132, 2, "s", "3a3a40", "rail", 8, gap=(door_s - 4, door_s + 16))
    bush(T, 12, 30, 0.9, 4)
    bush(T, 60, 28, 0.8, 5, "f2c440")
    tree(T, 20, 146, "birch", 0.9, 8)
    if L >= 2:
        roof_units(T, s0, f0, s1, f1, h1, seed, 1, stair=False)
        x0, y0, x1, y1 = T.rect(s0 + 10, f0 + 30, s0 + 60, f0 + 70)
        kit.solar(cv, x0, y0, x1, y1, h1 + 1, 6)
        x, y = T.pt(90, 150)
        kit.umbrella_table(cv, x, y, "3a7aa8")
    if L >= 3:
        # upper floor cube with a roof terrace
        up = facade("plaster", "3e4044", win=Win(w=30, h=22, sill=4, sp=38, margin=8, fh=34, frame="1e1e22", style="vertical"),
                    seed=seed + 3, plinth=None)
        box(T, s0 + 6, f0 + 20, s0 + 70, f1 - 4, h1, h1 * 2, all=up, top=flat_top("6e6c6a", "2e2e32", 2))
        T.panel(s0 + 72, s1, f0 + 2, h1, h1 + 10, glass_rail, "s")
        T.panel(f0 + 2, f1, s1, h1, h1 + 10, glass_rail, "f")
        x0, y0, x1, y1 = T.rect(80, 134, 150, 158)
        kit.pool(cv, x0, y0, x1, y1)
    return cv


# ====================================================================== townhouse: a terrace of narrow houses
def townhouse(L, o):
    cv = Canvas(2, 230)
    T = Orient(cv, o)
    n = 3 if L == 1 else 4
    floors = 2 if L == 1 else 3
    fh = 30
    H = floors * fh + 4
    unit = 300 / n
    cols = ["c4664a", "e8dcc0", "8a9aa8", "d8b07a", "b4644a"]
    f0, f1 = 60, 170
    for i in range(n):
        s0 = 10 + i * unit
        s1 = s0 + unit
        c = cols[(i + L) % len(cols)]
        mat = "brick" if c in ("c4664a", "b4644a") else "plaster"
        door_u = 8 if i % 2 == 0 else unit - 20
        front = facade(mat, c, win=Win(w=12, h=16, sill=9, sp=22, margin=8, fh=fh, frame="f4f2ee", boxes=L >= 2, shutters=None),
                       doors=[(door_u, 11, 24, "wood", ["2a3a5a", "6a2a2a", "2a5a3a", "1e1e22"][i % 4])], seed=40 + i,
                       cornice=("e8e2d6", 4) if L >= 2 else None, plinth=("6a6460", 6))
        side = facade(mat, c, seed=50 + i)
        back = facade(mat, c, win=Win(w=12, h=16, sill=9, sp=22, margin=8, fh=fh, frame="f4f2ee"), doors=[(unit / 2 - 6, 11, 24, "glass")],
                      seed=60 + i)
        walls = dict(front=front, back=back, left=side, right=side)
        if L == 3:
            box(T, s0, f0, s1, f1, 0, H, **walls, top=flat_top("7a7672", "d8d2c6", 3))
            # mansard storey with a dormer
            mans = facade("slate", "4a4e56", win=Win(w=12, h=14, sill=6, sp=22, margin=10, fh=30, frame="f4f2ee", cols=2), plinth=None, seed=70 + i)
            box(T, s0 + 2, f0 + 6, s1 - 2, f1 - 6, H, H + 28, front=mans, back=mans, left=flat("4a4e56"), right=flat("4a4e56"),
                top=flat_top("5a5e66", "8a8e96", 2))
        else:
            box(T, s0, f0, s1, f1, 0, H, **walls)
            T.gable(s0, f0, s1, f1, H, 30, roof_mat(["a8473a", "5a5e66"][L - 1], "tiles" if L == 1 else "slate", 3 + i),
                    walls, ridge="s", o=3)
        cx, cy = T.pt(s1 - 10, f0 + 50)
        kit.chimney(cv, cx - 3, cy - 3, H + (12 if L < 3 else 28), 18, "8a5a44", "chimney_%d" % i)
        steps(T, s0 + door_u - 2, s0 + door_u + 13, f0, 3, 4)
        ground(T, s0 + door_u, 0, s0 + door_u + 11, f0 - 12, kit.paving("c8c0b0", 8.0))
        fence(T, s0 + 2, s1 - 2, 4, "s", "2a2a30", "metal", 9, gap=(s0 + door_u - 1, s0 + door_u + 12))
        if i == 0:
            door(T, s0 + door_u, 11, f0, 24)
            entry(T, s0 + door_u + 5)
        bush(T, s0 + (unit - 18 if door_u < unit / 2 else 18), 30, 0.8, 10 + i, "e86a8a" if i % 2 else None)
        if L >= 2 and i % 2 == 0:
            tree(T, s0 + unit / 2, 230, "lime", 0.85, 20 + i)
        fence(T, 175, 318, s0, "f", "a88462", "boards", 12)
    fence(T, 175, 318, 310, "f", "a88462", "boards", 12)
    return cv


# ====================================================================== villa
def villa(L, o):
    cv = Canvas(2, 240)
    T = Orient(cv, o)
    seed = 81
    wallc = ["f2ead8", "f4eee4", "f6f2ea"][L - 1]
    roofc = ["a8473a", "8a4a3a", "4a4e56"][L - 1]
    fh = 34
    win = Win(w=14, h=20, sill=6, sp=30, margin=16, fh=fh, frame="f8f6f0", shutters="5a7a5a" if L < 3 else None, arch=L >= 2)
    s0, s1, f0, f1 = 60, 260, 110, 210
    H = 2 * fh + 4
    door_s = 150
    front = facade("plaster", wallc, win=win, doors=[(door_s - s0, 18, 28, "double", "5a3a24")], seed=seed, quoins="e0d6c0",
                   cornice=("e8e0cc", 5), plinth=("a89a84", 7))
    side = facade("plaster", wallc, win=win, seed=seed + 1, quoins="e0d6c0", cornice=("e8e0cc", 5), plinth=("a89a84", 7))
    back = facade("plaster", wallc, win=Win(w=16, h=24, sill=3, sp=32, margin=14, fh=fh, frame="f8f6f0"), doors=[(70, 16, 26, "glass"),
                  (120, 16, 26, "glass")], seed=seed + 2, cornice=("e8e0cc", 5), plinth=("a89a84", 7))
    walls = dict(front=front, back=back, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, H, **walls)
    T.hip(s0, f0, s1, f1, H, 36, roof_mat(roofc, "tiles"), o=7)
    # wing
    wing = facade("plaster", wallc, win=win, seed=seed + 3, cornice=("e8e0cc", 5), plinth=("a89a84", 7))
    box(T, 30, 150, 62, 250, 0, fh + 6, all=wing)
    T.hip(30, 150, 62, 250, fh + 6, 18, roof_mat(roofc, "tiles", 5), o=5)
    # portico
    slab(T, door_s - 22, f0 - 26, door_s + 40, f0, 0, 4, "d8d0c0")
    for ps in (door_s - 18, door_s - 4, door_s + 22, door_s + 36):
        T.cv.cylinder(*T.pt(ps, f0 - 22), 2.6, 4, fh + 2, lambda a, v, nx, ny: solid_res(C("f6f2ea"), a.shape))
    slab(T, door_s - 24, f0 - 28, door_s + 42, f0, fh + 2, fh + 7, "f6f2ea")
    door(T, door_s, 18, f0, 28)
    # drive and gate
    ground(T, door_s - 30, 0, door_s + 48, f0 - 26, kit.paving("d4c8b0", 10.0, 2))
    entry(T, door_s + 9)
    fence(T, 4, 316, 4, "s", "2a2a30", "metal", 14, gap=(door_s - 30, door_s + 48))
    for ps in (door_s - 32, door_s + 50):
        T.box(ps - 3, 1, ps + 3, 7, 0, 22, all=flat("e8e0cc", 3), top=flat("d8d0c0"))
    hedge(T, 4, 10, 10, 300, 16, 3)
    hedge(T, 306, 10, 316, 300, 16, 4)
    for k, (ss, ff) in enumerate(((40, 60), (270, 60), (290, 120))):
        tree(T, ss, ff, "spruce" if k == 2 else "lime", 0.9, 30 + k)
    flowerbed(T, door_s - 70, 40, door_s - 34, 70, 5)
    flowerbed(T, door_s + 52, 40, door_s + 88, 70, 6)
    if L >= 2:
        x0, y0, x1, y1 = T.rect(120, 236, 250, 290)
        kit.pool(cv, x0, y0, x1, y1)
        x, y = T.pt(90, 270)
        kit.umbrella_table(cv, x, y, "e8e4dc")
        bush(T, 270, 250, 1.2, 9, "f4f0f0")
    if L >= 3:
        # a fountain in the drive and a tower room
        x, y = T.pt(door_s + 9, 45)
        T.cv.cylinder(x, y, 14, 0, 4, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape),
                      lambda a, b: (np.broadcast_to(C("6ab8e0"), a.shape + (3,)).copy(), np.zeros(a.shape, bool), None))
        T.cv.cylinder(x, y, 3, 4, 14, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape))
        tw = facade("plaster", wallc, win=Win(w=12, h=18, sill=6, sp=20, margin=8, fh=fh, frame="f8f6f0", arch=True), seed=seed + 5,
                    cornice=("e8e0cc", 4), plinth=None)
        box(T, 220, 120, 252, 152, H, H + 30, all=tw)
        T.hip(220, 120, 252, 152, H + 30, 22, roof_mat(roofc, "tiles", 7), o=4)
    return cv


# ====================================================================== apartments: a classic five-storey block
def apartments(L, o):
    floors = [4, 5, 6][L - 1]
    fh = 30
    H = floors * fh + 6
    cv = Canvas(2, H + 80)
    T = Orient(cv, o)
    seed = 92
    wallc = ["d8c8a8", "e4d2b4", "cfd8de"][L - 1]
    mat = "brick" if L == 1 else "plaster"
    if L == 1:
        wallc = "b8705a"
    s0, s1, f0, f1 = 20, 300, 70, 220
    win = Win(w=14, h=16, sill=9, sp=26, margin=12, fh=fh, frame="f2efe8", group="flats")
    doors_ = [(60, 14, 24, "glass"), (206, 14, 24, "glass")]
    front = facade(mat, wallc, win=win, doors=doors_, seed=seed, plinth=("7a7268", 8),
                   bands=[(fh * k - 1, fh * k + 1, "d8d2c4") for k in range(1, floors)] if L >= 2 else (), cornice=("e8e2d6", 5))
    side = facade(mat, wallc, win=Win(w=14, h=16, sill=9, sp=26, margin=16, fh=fh, frame="f2efe8", group="flats"), seed=seed + 1,
                  plinth=("7a7268", 8), cornice=("e8e2d6", 5))
    back = facade(mat, wallc, win=win, seed=seed + 2, plinth=("7a7268", 8), cornice=("e8e2d6", 5))
    walls = dict(front=front, back=back, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, H, **walls, top=flat_top("807c78", "d8d2c6", 4))
    roof_units(T, s0, f0, s1, f1, H, seed, 4, tank=L == 1)
    # balconies between the stair windows
    bal_s = [s0 + 100, s0 + 150]
    balconies(T, bal_s, f0, range(1, floors), fh, 30, 12, "glass" if L >= 2 else "f2efe8")
    for ds in (s0 + 60, s0 + 206):
        canopy(T, ds - 6, ds + 20, f0, 14, 28, "e8e2d6", "6a6e76", posts=False)
        steps(T, ds - 4, ds + 18, f0, 2, 4)
        ground(T, ds - 2, 0, ds + 16, f0 - 8, kit.paving("b8b0a4", 8.0))
    door(T, s0 + 60, 14, f0, 24)
    door(T, s0 + 206, 14, f0, 24, "door2")
    entry(T, s0 + 67)
    # front garden strip, benches, lamps
    hedge(T, 20, 22, 70, 30, 9, 1)
    hedge(T, 110, 22, 210, 30, 9, 2)
    hedge(T, 250, 22, 300, 30, 9, 3)
    bench(T, 90, 40, "s")
    lamp(T, 100, 14, "modern", 45)
    tree(T, 10, 120, "lime", 0.95, 40)
    tree(T, 310, 250, "maple", 0.9, 41)
    # yard behind
    parking_lot(T, 20, 236, 300, 316, "s", 28)
    if L >= 2:
        x, y = T.pt(160, 270)
        kit.swing(cv, x - 12, y) if L == 2 else None
        bins(T, 300, 230)
    return cv


# ====================================================================== condo: modern stepped block
def condo(L, o):
    floors = [8, 10, 12][L - 1]
    fh = 30
    H = floors * fh + 4
    cv = Canvas(2, H + 80)
    T = Orient(cv, o)
    seed = 103
    c1, c2 = ["e8e6e2", "dcd8d0", "f2f0ec"][L - 1], ["5a6a7a", "3e4a58", "2e3238"][L - 1]
    win = Win(w=22, h=19, sill=5, sp=30, margin=8, fh=fh, frame="2e3238", style="vertical", group="flats")
    s0, s1, f0, f1 = 20, 200, 60, 230
    front = facade("concrete", c1, win=win, doors=[(70, 24, 26, "double_glass")], seed=seed, plinth=("4a4e56", 6))
    side = facade("concrete", c1, win=win, seed=seed + 1, plinth=("4a4e56", 6))
    walls = dict(front=front, back=side, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, H, **walls, top=flat_top("7a7874", "e8e6e2", 4))
    roof_units(T, s0, f0, s1, f1, H, seed, 3)
    balconies(T, [s0 + 10, s0 + 70, s0 + 130], f0, range(1, floors), fh, 40, 14, "glass", col="e8e6e2")
    # second, lower dark volume
    lf = max(4, floors - 4)
    H2 = lf * fh + 4
    dark = facade("metal", c2, win=Win(w=24, h=20, sill=5, sp=32, margin=8, fh=fh, frame="1e2024", style="vertical", group="flats"),
                  seed=seed + 2, plinth=("2a2c30", 6))
    box(T, 206, 100, 300, 260, 0, H2, all=dark, top=flat_top("6a6866", "3a3c40", 3))
    # roof garden on the low volume
    for k, (ss, ff) in enumerate(((230, 140), (270, 200))):
        x, y = T.pt(ss, ff)
        kit.tree(cv, x, y, "maple", 0.6, 60 + k, z=H2)
    canopy(T, s0 + 60, s0 + 104, f0, 22, 34, "2e3238", "2e3238", posts=True)
    door(T, s0 + 70, 24, f0, 26)
    entry(T, s0 + 82)
    ground(T, 10, 0, 310, f0, kit.paving("b4b0aa", 10.0, 9))
    for ss in (40, 160, 260):
        tree(T, ss, 30, "lime", 0.8, 70 + ss)
    bench(T, 120, 44, "s")
    lamp(T, 220, 20, "modern", 50)
    if L >= 3:
        # crown: a lit frame on top
        T.box(s0, f0, s0 + 4, f1, H, H + 24, all=flat("2e3238"))
        T.box(s1 - 4, f0, s1, f1, H, H + 24, all=flat("2e3238"))
        T.box(s0, f0, s1, f0 + 4, H + 20, H + 24, all=flat("2e3238"))
    return cv


# ====================================================================== tower: residential skyscraper
def tower(L, o):
    floors = [18, 24, 30][L - 1]
    fh = 30
    pod = 2 * fh
    H = pod + floors * fh
    cv = Canvas(2, H + 140)
    T = Orient(cv, o)
    seed = 117
    glass_t = ["4a7a9a", "3e6a8a", "5a7aa0"][L - 1]
    # podium with shops
    podf = facade("stone", "c8c0b4", shop=(20, 280, 26), doors=[(130, 30, 28, "double_glass")], plinth=None, seed=seed,
                  win=Win(w=24, h=18, sill=34, sp=30, margin=10, fh=60, frame="3a3a40", group="work"), lit=0.7)
    pods = facade("stone", "c8c0b4", win=Win(w=24, h=18, sill=34, sp=30, margin=10, fh=60, frame="3a3a40", group="work"), seed=seed + 1)
    box(T, 10, 30, 310, 310, 0, pod, front=podf, back=pods, left=pods, right=pods, top=flat_top("8a8884", "c8c0b4", 4))
    canopy(T, 120, 200, 30, 20, 34, "2e3238", "2e3238", posts=False)
    door(T, 140, 30, 30, 28)
    entry(T, 155)
    # shaft of glass
    cw = facade("concrete", "d8dce0", win=Win(w=26, h=24, sill=3, sp=29, margin=4, fh=fh, frame="9aa4ae", style="vertical",
                                              tint=glass_t, group="flats", top_skip=2), plinth=None, seed=seed + 2,
                bands=[(fh * k - 1.5, fh * k + 1.5, "e8ecf0") for k in range(floors + 2)])
    s0, s1, f0, f1 = 50, 270, 70, 280
    box(T, s0, f0, s1, f1, pod, H, all=cw, top=flat_top("7a7874", "d8dce0", 4))
    balconies(T, [s0 + 16, s0 + 110], f0, range(1, floors), fh, 70, 12, "glass", z_start=pod, col="e8ecf0")
    # crown
    top = H
    T.box(s0 + 30, f0 + 30, s1 - 30, f1 - 30, top, top + 40, all=facade("metal", "c8ccd0", plinth=None, seed=seed + 3),
          top=flat_top("8a8884", "c8ccd0", 3))
    if L >= 2:
        x, y = T.pt((s0 + s1) / 2, (f0 + f1) / 2)
        T.cv.cylinder(x, y, 1.5, top + 40, top + 100, lambda a, v, nx, ny: solid_res(C("c8ccd0"), a.shape))
        T.cv.ellipsoid(x, y, top + 100, 3, 3, 3, lambda wx, wy, wz, nx, ny, nz: (np.broadcast_to(C("ff4040"), wx.shape + (3,)).copy(),
                       np.ones(wx.shape, bool), np.broadcast_to(np.array([255, 60, 60, 255.0]), wx.shape + (4,)).copy()))
    for ss in (30, 290):
        tree(T, ss, 16, "lime", 0.7, 90 + ss)
    ground(T, 0, 0, 320, 30, kit.paving("c8c4bc", 12.0, 4))
    lamp(T, 100, 12, "modern", 50)
    lamp(T, 220, 12, "modern", 50, "light2")
    return cv


BUILDERS = {"house_small": house_small, "cottage": cottage, "bungalow": bungalow, "townhouse": townhouse,
            "villa": villa, "apartments": apartments, "condo": condo, "tower": tower}
