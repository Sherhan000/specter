"""Farms and industry at real scale."""
import math

import numpy as np

from raster import C, U, Canvas, flat, solid_res, glow_res, nores, hash2
from arch import Orient, facade, Win, roof_mat, flat_top, text_mask
import kit
from bkit import (door, entry, ground, tree, bush, hedge, fence, flowerbed, lamp, bench, bins, box, slab, post, canopy,
                  steps, roof_units, parking_lot, sign_board, pole_sign, car_static)

S = U


def silo(T, s, f, r=14, h=90, col="d8dcdf", dome=True):
    x, y = T.pt(s, f)
    side = lambda a, v, nx, ny: (C(col) * (0.88 + 0.12 * ((np.floor(v / 6) % 2) == 0))[..., None] *
                                 (0.92 + 0.08 * np.cos(a * 12))[..., None], nores(a.shape), None)
    T.cv.cylinder(x, y, r, 0, h, side, lambda a, b: solid_res(C(col) * 0.9, a.shape))
    if dome:
        T.cv.ellipsoid(x, y, h, r, r, r * 0.6, lambda wx, wy, wz, nx, ny, nz: solid_res(C("a8acb0"), wx.shape), cut_z=h)


def hay(T, s, f, r=7):
    x, y = T.pt(s, f)
    T.cv.cylinder(x, y, r, 0, 10, lambda a, v, nx, ny: (C("d8b860") * (0.85 + 0.2 * hash2(np.floor(a * 8), np.floor(v), 1))[..., None],
                                                         nores(a.shape), None), lambda a, b: solid_res(C("c8a850"), a.shape))


def crates(T, s, f, n=4, seed=0):
    rng = np.random.default_rng(seed)
    for i in range(n):
        ds, df = rng.uniform(0, 16), rng.uniform(0, 16)
        z = 0 if i < 3 else 8
        c = flat("b8864a", 10)
        T.box(s + ds, f + df, s + ds + 8, f + df + 8, z, z + 8, all=c, top=flat("c8965a", 8))


def logs(T, s0, f0, length=60, n=3, along="s"):
    end = lambda u, v, L, H: (np.where((((u % 5) - 2.5) ** 2 + ((v % 5) - 2.5) ** 2 < 4)[..., None], C("d8b080"), C("7a4a28")) *
                              np.ones(u.shape + (3,)), nores(u.shape), None)
    bark = flat("6a4228", 10)
    for i in range(n):
        if along == "s":
            T.box(s0 + i * 2, f0 + i * 2.5, s0 + length - i * 2, f0 + 15 - i * 2.5, i * 5, i * 5 + 5, front=end, back=end, left=bark, right=bark, top=bark)
        else:
            T.box(s0 + i * 2.5, f0 + i * 2, s0 + 15 - i * 2.5, f0 + length - i * 2, i * 5, i * 5 + 5, front=bark, back=bark, left=end, right=end, top=bark)


def planks(T, s0, f0, w=30, d=14, h=10):
    side = lambda u, v, L, H: (C("d8b884") * (1 - 0.18 * ((np.floor(v) % 2) == 0))[..., None], nores(u.shape), None)
    T.box(s0, f0, s0 + w, f0 + d, 0, h, all=side, top=flat("e0c490", 6))


def cow(T, s, f, along="s", col="f4f0ea", spot="2a2a2a", seed=0):
    x, y = T.pt(s, f)
    rng = np.random.default_rng(seed)
    body = lambda wx, wy, wz, nx, ny, nz: ((np.where((hash2(np.floor(wx / 4), np.floor((wy + wz) / 4), seed) < 0.35)[..., None], C(spot), C(col))
                                           * np.ones(wx.shape + (3,))), nores(wx.shape), None)
    ax = T.axis(along)
    lx, ly = (9, 4.5) if ax == "x" else (4.5, 9)
    T.cv.ellipsoid(x, y, 10, lx, ly, 5, body)
    hx, hy = (x + 9, y) if ax == "x" else (x, y + 9)
    T.cv.ellipsoid(hx, hy, 12, 3, 3, 3, lambda *a: solid_res(C(col), a[0].shape))
    leg = flat("3a3030")
    for dx in (-5, 5):
        for dy in (-2, 2):
            if ax == "x":
                T.cv.box(x + dx - 0.8, y + dy - 0.8, 0, x + dx + 0.8, y + dy + 0.8, 7, leg, leg, leg)
            else:
                T.cv.box(x + dy - 0.8, y + dx - 0.8, 0, x + dy + 0.8, y + dx + 0.8, 7, leg, leg, leg)


def tractor(T, s, f, along="s"):
    x, y = T.pt(s, f)
    ax = T.axis(along)
    red, blk = flat("c8342a", 4), flat("2a2a2e", 3)
    if ax == "x":
        T.cv.box(x - 14, y - 7, 6, x + 6, y + 7, 16, red, red, red)
        T.cv.box(x - 14, y - 7, 16, x - 2, y + 7, 30, flat("3a4a5a"), flat("3a4a5a"), red)
        for (dx, r) in ((-10, 9), (6, 6)):
            for dy in (-8, 8):
                T.cv.box(x + dx - r, y + dy - 2, 0, x + dx + r, y + dy + 2, r * 2, blk, blk, blk)
    else:
        T.cv.box(x - 7, y - 14, 6, x + 7, y + 6, 16, red, red, red)
        T.cv.box(x - 7, y - 14, 16, x + 7, y - 2, 30, flat("3a4a5a"), flat("3a4a5a"), red)
        for (dy, r) in ((-10, 9), (6, 6)):
            for dx in (-8, 8):
                T.cv.box(x + dx - 2, y + dy - r, 0, x + dx + 2, y + dy + r, r * 2, blk, blk, blk)


def barn(T, s0, f0, s1, f1, h, col="a8342a", roofc="5a5e66", door_w=40):
    trim = "f4f0e8"
    fr = facade("wood", col, doors=[((s1 - s0 - door_w) / 2, door_w, h - 8, "double", "8a2a22")], plinth=None, seed=7,
                decals=[(((s1 - s0 - door_w) / 2) - 2, ((s1 - s0 + door_w) / 2) + 2, h - 8, h - 6, trim)])
    sd = facade("wood", col, win=Win(w=10, h=10, sill=24, sp=40, margin=20, fh=60, frame=trim, group="work"), plinth=None, seed=8)
    walls = dict(front=fr, back=fr, left=sd, right=sd)
    T.box(s0, f0, s1, f1, 0, h, **walls)
    T.gable(s0, f0, s1, f1, h, (s1 - s0) * 0.38, roof_mat(roofc, "metal"), dict(front=facade("wood", col, plinth=None, seed=9),
            back=facade("wood", col, plinth=None, seed=9), left=sd, right=sd), ridge="f", o=5)


# ====================================================================== farm
def farm(L, o):
    cv = Canvas(2, 170)
    T = Orient(cv, o)
    # fields
    crops = [("5a9a3a", 0.55), ("d8b850", 0.7), ("6aa848", 0.5)]
    for k, (s0, s1) in enumerate(((10, 150), (170, 310))):
        if L == 1 and k == 1:
            ground(T, s0, 170, s1, 310, kit.soil_rows("u", "6e5236", "6e5236", 10, 7 + k, 0.3))
        else:
            c, w = crops[(k + L) % 3]
            ground(T, s0, 170, s1, 310, kit.soil_rows("u" if k == 0 else "v", "6e5236", c, 9, 7 + k, w))
    fence(T, 6, 314, 166, "s", "8a6a48", "rail", 9)
    barn(T, 20, 40, 120, 150, 50)
    door(T, 50, 40, 40, 42)
    entry(T, 70)
    silo(T, 150, 70, 14, 80 if L < 3 else 100)
    if L >= 2:
        silo(T, 182, 70, 14, 80)
    # farmhouse
    fw = facade("plaster", "f2ead8", win=Win(w=12, h=14, sill=9, sp=26, margin=14, fh=30, shutters="5a7a5a"), doors=[(30, 10, 22, "wood", "6a4a2a")],
                seed=401)
    box(T, 220, 40, 300, 120, 0, 32, all=fw)
    T.gable(220, 40, 300, 120, 32, 30, roof_mat("a8473a", "tiles"), dict(all=fw), ridge="s", o=4)
    ground(T, 40, 0, 100, 40, kit.gravel())
    ground(T, 240, 0, 262, 40, kit.paving("c8bca8", 6.0))
    for k in range(3 + L):
        hay(T, 140 + k * 16, 140)
    tractor(T, 180, 20, "s")
    tree(T, 300, 150, "oak", 0.9, 401)
    return cv


def orchard(L, o):
    cv = Canvas(2, 140)
    T = Orient(cv, o)
    fruit = ["e84a3a", "f0c040", "e86a2a"][L - 1]
    ground(T, 10, 70, 310, 314, kit.paving("7a9a4a", 40.0, 2, 0.0))
    rows = 5 if L < 3 else 6
    for i in range(rows):
        for j in range(5):
            s = 30 + j * 60
            f = 96 + i * 40
            if f > 300:
                continue
            x, y = T.pt(s, f)
            kit.tree(T.cv, x, y, "fruit", 0.6, i * 7 + j, fruit)
    shed = facade("wood", "9a6a40", doors=[(20, 26, 24, "double", "6a4428")], plinth=None, seed=411)
    box(T, 20, 10, 110, 60, 0, 30, all=shed)
    T.gable(20, 10, 110, 60, 30, 18, roof_mat("5a5e66", "metal"), dict(all=shed), ridge="s", o=3)
    door(T, 40, 26, 10, 24)
    entry(T, 53)
    crates(T, 130, 20, 4 + L, 3)
    crates(T, 170, 30, 3, 4)
    fence(T, 6, 314, 66, "s", "8a6a48", "rail", 9, gap=(130, 170))
    if L >= 2:
        tractor(T, 250, 30, "s")
    return cv


def greenhouse(L, o):
    cv = Canvas(2, 140)
    T = Orient(cv, o)
    gl = lambda u, v, LL, H: ((np.where((((u % 12) < 0.8) | ((v % 14) < 0.8))[..., None], C("e8ecf0"), C("a8d0b8")) *
                               np.ones(u.shape + (3,))), ((u % 12) >= 0.8) & ((v % 14) >= 0.8), None)
    n = 2 if L == 1 else 3
    for k in range(n):
        s0 = 16 + k * 98
        T.box(s0, 60, s0 + 86, 300, 0, 26, all=gl, top=flat("a8d0b8"))
        T.gable(s0, 60, s0 + 86, 300, 26, 22, lambda a, b, m: (np.where((((a % 14) < 0.8))[..., None], C("e8ecf0"), C("b8dcc8")) *
                                                                    np.ones(a.shape + (3,)), nores(a.shape), None), dict(all=gl), ridge="f", o=1)
    pack = facade("metal", "e8e8ea", doors=[(30, 30, 26, "shutter", "c8ccd0")], plinth=None, seed=421)
    box(T, 210 if n == 2 else 230, 10, 310, 52, 0, 32, all=pack, top=flat_top("8a8884", "e8e8ea", 2))
    door(T, 250, 30, 10, 26)
    entry(T, 260)
    ground(T, 10, 0, 200, 56, kit.gravel())
    crates(T, 60, 16, 4, 5)
    return cv


def ranch(L, o):
    cv = Canvas(2, 150)
    T = Orient(cv, o)
    # stable
    st = facade("wood", "8a5a34", doors=[(10 + k * 30, 16, 24, "double", "5a3a20") for k in range(4)], plinth=None, seed=431)
    box(T, 20, 30, 170, 90, 0, 34, all=st)
    T.gable(20, 30, 170, 90, 34, 22, roof_mat("4a4e56", "metal"), dict(all=st), ridge="s", o=4)
    door(T, 30, 16, 30, 24)
    entry(T, 38)
    silo(T, 200, 50, 12, 70, "c8b090")
    # paddock
    ground(T, 10, 120, 310, 312, kit.paving("8a9a50", 30.0, 3, 0.0))
    for a0, a1, b, al in ((10, 310, 120, "s"), (10, 310, 312, "s"), (120, 312, 10, "f"), (120, 312, 310, "f")):
        fence(T, a0, a1, b, al, "e8e4dc", "rail", 10)
    for k in range(2 + L):
        cow(T, 50 + k * 60, 170 + (k % 2) * 60, "s" if k % 2 else "f", seed=k)
    x0, y0, x1, y1 = T.rect(240, 140, 290, 152)
    T.box(240, 140, 290, 152, 0, 6, all=flat("8a8a90"), top=flat("4a8ab8"))
    for k in range(L + 1):
        hay(T, 230 + k * 16, 100)
    return cv


# ====================================================================== industry
def sawmill(L, o):
    cv = Canvas(2, 170)
    T = Orient(cv, o)
    hall = facade("wood", "9a6a40", doors=[(20, 40, 34, "shutter", "7a7a80")], plinth=("5a5a60", 4), seed=441,
                  win=Win(w=16, h=10, sill=30, sp=34, margin=70, fh=60, frame="e8e4dc", group="work"))
    box(T, 20, 30, 200, 140, 0, 46, all=hall)
    T.gable(20, 30, 200, 140, 46, 26, roof_mat("6a6e76", "metal"), dict(all=hall), ridge="s", o=4)
    door(T, 40, 40, 30, 34)
    entry(T, 60)
    x, y = T.pt(170, 110)
    cv.mark("smoke", x, y, 80)
    T.box(160, 100, 172, 112, 46, 80, all=flat("5a5a60"), top=flat("2a2a2a"))
    ground(T, 10, 150, 310, 312, kit.gravel("9a8a70"))
    for k in range(2 + L):
        logs(T, 30 + (k % 2) * 140, 170 + (k // 2) * 40, 110, 3)
    planks(T, 220, 40, 40, 20, 12)
    planks(T, 220, 80, 40, 20, 8 + 4 * L)
    if L >= 2:
        # gantry crane over the yard
        for (ss, ff) in ((24, 160), (24, 300), (296, 160), (296, 300)):
            post(T, ss, ff, 0, 60, "e8b830", 3)
        slab(T, 20, 228, 300, 236, 60, 64, "e8b830")
    return cv


def workshop(L, o):
    cv = Canvas(2, 150)
    T = Orient(cv, o)
    br = facade("brick", "a8583a", doors=[(30, 36, 32, "shutter", "8a8a90"), (110, 36, 32, "shutter", "8a8a90")], plinth=("4a4a50", 4), seed=451,
                win=Win(w=20, h=14, sill=36, sp=30, margin=10, fh=60, frame="e8e4dc", group="work"))
    side = facade("brick", "a8583a", win=Win(w=20, h=16, sill=12, sp=30, margin=12, fh=60, frame="e8e4dc", group="work"), seed=452)
    box(T, 20, 40, 300, 200, 0, 50, front=br, back=side, left=side, right=side, top=flat_top("7a7672", "a8583a", 3))
    # saw-tooth roof lights
    for k in range(5):
        f = 52 + k * 30
        T.box(30, f, 290, f + 4, 50, 66, all=lambda u, v, LL, H: (np.broadcast_to(C("9ac0d8"), u.shape + (3,)).copy(), np.ones(u.shape, bool), None),
              top=flat("5a5e66"))
        T.box(30, f + 4, 290, f + 22, 50, 52, all=flat("5a5e66"), top=flat("5a5e66"))
    door(T, 30, 36, 40, 32)
    entry(T, 48)
    ground(T, 10, 0, 310, 40, kit.asphalt_lot("62646a"))
    car_static(T, 230, 20, "s", "e8e8ea")
    crates(T, 160, 210, 5, 9)
    ground(T, 10, 204, 310, 312, kit.gravel("8a8478"))
    if L >= 2:
        x, y = T.pt(260, 250)
        kit.water_tank(cv, x, y, 0, 12, 30)
    if L >= 3:
        T.box(200, 230, 240, 300, 0, 26, all=facade("metal", "c8ccd0", plinth=None, seed=453), top=flat("8a8e94"))
    return cv


def factory(L, o):
    cv = Canvas(2, 230)
    T = Orient(cv, o)
    H = 60 + L * 6
    hall = facade("metal", "c8ccd0", doors=[(40, 50, 40, "shutter", "8a8e94")], plinth=("4a4e56", 6), seed=461,
                  win=Win(w=40, h=10, sill=H - 18, sp=50, margin=20, fh=200, frame="5a5e66", group="work"), bands=[(H - 30, H - 28, "e8342a")])
    side = facade("metal", "c8ccd0", win=Win(w=40, h=10, sill=H - 18, sp=50, margin=20, fh=200, frame="5a5e66", group="work"), plinth=("4a4e56", 6),
                  seed=462)
    box(T, 20, 60, 230, 300, 0, H, front=hall, back=side, left=side, right=side, top=flat_top("8a8e94", "c8ccd0", 3))
    offs = facade("brick", "b8664a", win=Win(w=14, h=16, sill=9, sp=24, margin=10, fh=30, frame="e8e4dc", group="work"),
                  doors=[(20, 14, 24, "glass")], seed=463, plinth=("4a4e56", 4), signs=[(40, 66, "FACTORY", 7, None, "ffffff", True)])
    box(T, 236, 60, 310, 160, 0, 74, all=offs, top=flat_top("7a7672", "b8664a", 3))
    door(T, 256, 14, 60, 24)
    entry(T, 263)
    # chimneys with smoke
    for k, (ss, ff) in enumerate(((60, 200), (110, 200))[: 1 + (L >= 2)]):
        x, y = T.pt(ss, ff)
        brick = facade("brick", "8a4a3a", plinth=None, bands=[(150, 156, "e8e4dc")])
        cv.cylinder(x, y, 9, H, 170, lambda a, v, nx, ny: brick(a * 10, v + H, 100, 200)[:3] if False else
                    (C("8a4a3a") * (0.9 + 0.12 * (((np.floor(v / 3) + np.floor(a * 6)) % 2) == 0))[..., None], nores(a.shape), None),
                    lambda a, b: solid_res(C("2a2222"), a.shape))
        cv.mark("smoke%d" % k, x, y, 172)
    # tanks
    for k in range(L):
        x, y = T.pt(270, 200 + k * 40)
        kit.water_tank(cv, x, y, 0, 16, 34)
    ground(T, 10, 0, 310, 60, kit.asphalt_lot("62646a", lines=("u", 20, 30, 10, 50)))
    return cv


def logistics(L, o):
    cv = Canvas(3, 160)
    T = Orient(cv, o)
    H = 56
    docks = [(20 + k * 60, 40, 36, "shutter", "8a8e94") for k in range(6)]
    wh = facade("metal", "d8dce0", doors=docks, plinth=("4a4e56", 6), seed=471, bands=[(H - 12, H - 6, "2a5aa8")],
                signs=[(390, 26, "LOGISTICS", 8, None, "2a5aa8", True)])
    side = facade("metal", "d8dce0", plinth=("4a4e56", 6), seed=472, bands=[(H - 12, H - 6, "2a5aa8")])
    box(T, 20, 180, 460, 440, 0, H, front=wh, back=side, left=side, right=side, top=flat_top("8a8e94", "d8dce0", 3))
    roof_units(T, 20, 180, 460, 440, H, 471, 6, stair=False)
    for k in range(6):
        slab(T, 18 + k * 60, 170, 64 + k * 60, 180, 0, 12, "6a6e76")
    door(T, 20, 40, 180, 36)
    entry(T, 240)
    ground(T, 10, 0, 470, 180, kit.asphalt_lot("5e6066", lines=("u", 20, 60, 100, 170)))
    # trucks at the docks and containers
    for k in range(2 + L):
        s = 40 + k * 120
        T.box(s - 12, 110, s + 12, 168, 0, 34, all=flat(["e8e8ea", "c8342a", "2a5aa8", "e8b830", "3a8a4a"][k % 5], 4),
              top=flat("d8dcdf"))
        T.box(s - 11, 80, s + 11, 108, 0, 26, all=flat("3a4a5a", 3), top=flat("2a2a30"))
    for k in range(L):
        T.box(380, 20 + k * 30, 460, 46 + k * 30, 0, 26, all=flat(["c8642a", "2a7a8a", "8a3a3a"][k], 6), top=flat("9a9a9a"))
    return cv


def warehouse(L, o):
    cv = Canvas(2, 120)
    T = Orient(cv, o)
    H = 40 + L * 4
    wh = facade("metal", "b8bcc0", doors=[(30, 40, 32, "shutter", "8a8e94"), (180, 40, 32, "shutter", "8a8e94")], plinth=("4a4e56", 4), seed=481,
                bands=[(H - 8, H - 4, "e8a830")])
    side = facade("metal", "b8bcc0", plinth=("4a4e56", 4), seed=482, bands=[(H - 8, H - 4, "e8a830")])
    box(T, 20, 70, 300, 290, 0, H, front=wh, back=side, left=side, right=side, top=flat_top("8a8e94", "b8bcc0", 3))
    door(T, 30, 40, 70, 32)
    entry(T, 50)
    ground(T, 10, 0, 310, 70, kit.asphalt_lot("5e6066"))
    for k in range(2 + L):
        T.box(110 + k * 18, 20, 124 + k * 18, 34, 0, 10 + (k % 2) * 8, all=flat("c8965a", 8), top=flat("d8a66a"))
    if L >= 2:
        T.box(240, 12, 300, 50, 0, 26, all=flat("2a7a8a", 6), top=flat("8a8a8a"))
    return cv


BUILDERS = {"farm": farm, "orchard": orchard, "greenhouse": greenhouse, "ranch": ranch, "sawmill": sawmill,
            "workshop": workshop, "factory": factory, "logistics": logistics, "warehouse": warehouse}
