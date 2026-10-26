"""Public buildings, leisure and decor at real scale."""
import math

import numpy as np

from raster import C, U, Canvas, flat, solid_res, glow_res, nores, hash2
from arch import Orient, facade, Win, roof_mat, flat_top, text_mask
import kit
from bkit import (door, entry, ground, tree, bush, hedge, fence, flowerbed, lamp, bench, bins, box, slab, post, canopy,
                  steps, roof_units, parking_lot, sign_board, pole_sign, car_static, balconies, glass_rail)
from b_work import cow

S = U


def column(T, s, f, z0, z1, r=3.0, col="f2eee6"):
    x, y = T.pt(s, f)
    side = lambda a, v, nx, ny: (C(col) * (0.92 + 0.08 * np.cos(a * 16))[..., None], nores(a.shape), None)
    T.cv.cylinder(x, y, r, z0, z1, side)
    T.box(s - r - 1, f - r - 1, s + r + 1, f + r + 1, z1 - 2, z1, all=flat(col), top=flat(col))
    T.box(s - r - 1, f - r - 1, s + r + 1, f + r + 1, z0, z0 + 2, all=flat(col), top=flat(col))


def portico(T, s0, s1, f_face, depth, h, n=6, col="f2eee6", pediment=True, text=None):
    """Classical porch: columns, an entablature with an inscription and a triangular pediment."""
    slab(T, s0 - 4, f_face - depth - 6, s1 + 4, f_face, 0, 6, "d8d0c0")
    for i in range(n):
        s = s0 + 4 + i * (s1 - s0 - 8) / (n - 1)
        column(T, s, f_face - depth + 2, 6, h, 3.2, col)
    ent = facade("stone", col, plinth=None, signs=[((s1 - s0) / 2, 3, text, 6, None, "3a3a40", False)] if text else ())
    T.box(s0 - 2, f_face - depth - 2, s1 + 2, f_face, h, h + 12, front=ent, back=flat(col), left=flat(col), right=flat(col), top=flat(col))
    if pediment:
        T.gable(s0 - 2, f_face - depth - 2, s1 + 2, f_face + 30, h + 12, 20, roof_mat("8a8e94", "metal"),
                dict(front=facade("stone", col, plinth=None)), ridge="f", o=2)


def flagpole(T, s, f, h=90, col="2a5aa8"):
    post(T, s, f, 0, h, "d8d8dc", 1.4)
    x, y = T.pt(s, f)
    T.panel(f, f + 22, s, h - 16, h - 2, lambda u, v, L, H: (np.where((v > 7)[..., None], C("f4f4f4"), C(col)) * np.ones(u.shape + (3,)),
                                                                nores(u.shape), None), "f")


def court_ground(T, s0, f0, s1, f1, col="c8583a", line="f4f0e8", kind="track"):
    """Sports surface with markings (ground layer)."""
    def fn(u, v, L, D):
        shape = u.shape
        rgb = np.broadcast_to(C(col), shape + (3,)).copy()
        rgb += ((hash2(np.floor(u), np.floor(v), 3) - 0.5) * 8)[..., None]
        m = (u < 2) | (v < 2) | (u > L - 2) | (v > D - 2) | (np.abs(u - L / 2) < 0.8)
        if kind == "pitch":
            rgb = np.broadcast_to(C("4f9a3a"), shape + (3,)).copy()
            rgb *= (0.92 + 0.1 * ((np.floor(u / 16) % 2) == 0))[..., None]
            circ = np.abs(np.hypot(u - L / 2, v - D / 2) - min(L, D) * 0.15) < 0.8
            m = m | circ
        elif kind == "track":
            inner = (u > 14) & (v > 14) & (u < L - 14) & (v < D - 14)
            rgb[inner] = C("4f9a3a")
            m = m | ((np.abs(u - 14) < 0.7) | (np.abs(v - 14) < 0.7)) & ~inner
        rgb[m] = C(line)
        return rgb, nores(shape), None
    ground(T, s0, f0, s1, f1, fn)


# ====================================================================== education
def school(L, o):
    cv = Canvas(2, 170)
    T = Orient(cv, o)
    floors = [2, 3, 3][L - 1]
    fh = 34
    H = floors * fh + 4
    win = Win(w=18, h=20, sill=8, sp=26, margin=10, fh=fh, frame="f4f2ee", style="grid", group="work")
    fr = facade("brick", "b8664a", win=win, doors=[(110, 26, 28, "double_glass")], seed=501, plinth=("6a6460", 6),
                cornice=("e8e2d6", 5), signs=[(123, 33.5, "SCHOOL", 6, "f4f0e8", "2a3a5a", False)])
    sd = facade("brick", "b8664a", win=win, seed=502, plinth=("6a6460", 6), cornice=("e8e2d6", 5))
    box(T, 20, 60, 260, 150, 0, H, front=fr, back=sd, left=sd, right=sd)
    T.hip(20, 60, 260, 150, H, 26, roof_mat("5a5e66", "slate"), o=4)
    box(T, 180, 150, 260, 300, 0, H, all=sd)
    T.hip(180, 150, 260, 300, H, 22, roof_mat("5a5e66", "slate", 5), o=4)
    canopy(T, 124, 160, 60, 14, 32, "2a3a5a", "2a3a5a", posts=True)
    door(T, 130, 26, 60, 28)
    entry(T, 143)
    ground(T, 20, 0, 300, 60, kit.paving("c4bcae", 10.0, 3))
    court_ground(T, 20, 160, 170, 306, "c8583a", kind="track")
    flagpole(T, 60, 30, 80)
    for k, ss in enumerate((280, 300)):
        tree(T, ss, 100 + k * 60, "lime", 0.8, 50 + k)
    fence(T, 16, 176, 156, "s", "3a5a3a", "metal", 14)
    if L >= 3:
        x, y = T.pt(250, 30)
        kit.swing(cv, x - 12, y) if T.o in (0, 2) else None
    return cv


def kindergarten(L, o):
    cv = Canvas(1, 110)
    T = Orient(cv, o)
    cols = ["f6c84a", "8ac8e8", "f08a6a"]
    win = Win(w=16, h=16, sill=8, sp=28, margin=12, fh=34, frame="ffffff", group="work")
    fr = facade("plaster", cols[L - 1], win=win, doors=[(60, 14, 24, "glass")], seed=511, plinth=("6a6460", 4),
                bands=[(28, 31, "ffffff")])
    box(T, 14, 30, 146, 96, 0, 34, all=fr, top=flat_top("7a7672", "ffffff", 3))
    door(T, 74, 14, 30, 24)
    entry(T, 80)
    ground(T, 74, 0, 90, 30, kit.paving("c8c0b0", 6.0))
    # playground behind
    ground(T, 10, 104, 150, 156, lambda u, v, LL, D: (np.broadcast_to(C("c85a4a"), u.shape + (3,)).copy() +
                                                     ((hash2(np.floor(u), np.floor(v), 2) - 0.5) * 10)[..., None], nores(u.shape), None))
    x, y = T.pt(40, 130)
    kit.swing(cv, x - 12, y) if T.o in (0, 2) else kit.swing(cv, x, y - 12)
    x0, y0, x1, y1 = T.rect(100, 112, 130, 142)
    T.box(100, 112, 130, 142, 0, 3, all=flat("b07a48"), top=flat("ead7a0", 10))
    fence(T, 6, 154, 100, "s", "f4f0e8", "picket", 9)
    bush(T, 140, 16, 0.8, 3, "f4d040")
    return cv


def library(L, o):
    cv = Canvas(2, 180)
    T = Orient(cv, o)
    H = [44, 56, 68][L - 1]
    win = Win(w=16, h=30, sill=8, sp=28, margin=16, fh=H, frame="f2eee6", arch=True, group="work")
    fr = facade("stone", "e0d6c2", win=win, doors=[(110, 24, 32, "double", "5a3a24")], seed=521, plinth=("a89a84", 8), cornice=("f2eee6", 6))
    box(T, 40, 90, 280, 260, 0, H, front=fr, back=fr, left=fr, right=fr, top=flat_top("8a8e94", "f2eee6", 4))
    portico(T, 120, 200, 90, 26, H - 12, 4, "f2eee6", True, "LIBRARY")
    door(T, 150, 24, 90, 32)
    entry(T, 160)
    ground(T, 40, 0, 280, 60, kit.paving("d4ccbc", 10.0, 2))
    steps(T, 110, 210, 60, 2, 3)
    for k, ss in enumerate((30, 290)):
        tree(T, ss, 60, "lime", 0.9, 60 + k)
    bench(T, 70, 30, "s")
    bench(T, 250, 30, "s")
    return cv


def museum(L, o):
    cv = Canvas(2, 230)
    T = Orient(cv, o)
    H = 56
    fr = facade("stone", "e8e0cc", win=Win(w=14, h=26, sill=14, sp=40, margin=20, fh=H, frame="f2eee6", arch=True, group="work"),
                seed=531, plinth=("a89a84", 10), cornice=("f2eee6", 8))
    box(T, 30, 90, 290, 290, 0, H, all=fr, top=flat_top("8a8e94", "f2eee6", 4))
    portico(T, 100, 220, 90, 30, H, 6, "f6f2ea", True, "MUSEUM")
    door(T, 150, 24, 90, 34)
    entry(T, 160)
    # dome
    x, y = T.pt(160, 190)
    T.cv.cylinder(x, y, 46, H, H + 24, lambda a, v, nx, ny: (C("e8e0cc") * (0.9 + 0.1 * ((np.floor(a * 8) % 2) == 0))[..., None], nores(a.shape), None))
    T.cv.ellipsoid(x, y, H + 24, 46, 46, 40 if L >= 2 else 30, lambda wx, wy, wz, nx, ny, nz: solid_res(C("6a9a8a") if L < 3 else C("c8a040"), wx.shape),
                   cut_z=H + 24)
    ground(T, 20, 0, 300, 60, kit.paving("d8d0c0", 12.0, 4))
    steps(T, 96, 224, 60, 3, 3)
    for k, ss in enumerate((40, 280)):
        x, y = T.pt(ss, 30)
        T.box(ss - 8, 22, ss + 8, 38, 0, 12, all=flat("d8d0c0"), top=flat("c8c0b0"))
        kit.chimney if False else None
    return cv


# ====================================================================== safety
def fire_station(L, o):
    cv = Canvas(2, 200)
    T = Orient(cv, o)
    H = 64
    doors_ = [(20 + k * 52, 40, 40, "garage", "c8342a") for k in range(2 + (L >= 2))]
    fr = facade("brick", "a8483a", doors=doors_, seed=541, plinth=("4a4a50", 4),
                win=Win(w=14, h=16, sill=9, sp=26, margin=12, fh=32, frame="f4f0e8", group="work"), cornice=("e8e2d6", 5),
                signs=[(80, 48, "FIRE STATION", 7, "e8e2d6", "c8342a", False)])
    sd = facade("brick", "a8483a", win=Win(w=14, h=16, sill=9, sp=26, margin=12, fh=32, frame="f4f0e8", group="work"), seed=542,
                plinth=("4a4a50", 4), cornice=("e8e2d6", 5))
    box(T, 20, 80, 220, 260, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("7a7672", "a8483a", 4))
    # drill tower
    tw = facade("brick", "a8483a", win=Win(w=10, h=14, sill=10, sp=20, margin=6, fh=30, frame="f4f0e8", group="work"), seed=543)
    box(T, 230, 120, 270, 160, 0, 130, all=tw, top=flat_top("4a4a50", "a8483a", 2))
    door(T, 20, 40, 80, 40)
    entry(T, 40)
    ground(T, 10, 0, 230, 80, kit.asphalt_lot("62646a"))
    ground(T, 236, 0, 300, 80, kit.paving("c4bcae", 8.0))
    flagpole(T, 280, 40, 90, "c8342a")
    if L >= 3:
        T.box(140, 20, 190, 60, 0, 30, all=flat("c8342a", 4), top=flat("e8e8ea"))
    return cv


def police(L, o):
    cv = Canvas(2, 190)
    T = Orient(cv, o)
    floors = [2, 3, 3][L - 1]
    H = floors * 34 + 4
    win = Win(w=20, h=18, sill=8, sp=30, margin=12, fh=34, frame="2a3a5a", style="vertical", group="work")
    fr = facade("concrete", "e4e6ea", win=win, doors=[(110, 30, 28, "double_glass")], seed=551, plinth=("2a3a5a", 6),
                bands=[(H - 14, H - 2, "2a4a8a")], signs=[(125, H - 12, "POLICE", 8, None, "ffffff", True)])
    sd = facade("concrete", "e4e6ea", win=win, seed=552, plinth=("2a3a5a", 6), bands=[(H - 14, H - 2, "2a4a8a")])
    box(T, 30, 80, 290, 230, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("7a7874", "e4e6ea", 4))
    roof_units(T, 30, 80, 290, 230, H, 551, 3)
    canopy(T, 130, 180, 80, 16, 32, "2a4a8a", "2a4a8a", posts=True)
    door(T, 140, 30, 80, 28)
    entry(T, 155)
    ground(T, 120, 0, 190, 80, kit.paving("c4c4c4", 8.0))
    parking_lot(T, 200, 0, 310, 76, "s", 26)
    flagpole(T, 100, 40, 80)
    for k, ss in enumerate((30, 70)):
        tree(T, ss, 40, "lime", 0.7, 70 + k)
    return cv


def hospital(L, o):
    cv = Canvas(2, 260)
    T = Orient(cv, o)
    floors = [3, 5, 7][L - 1]
    fh = 34
    H = floors * fh + 4
    win = Win(w=22, h=18, sill=9, sp=30, margin=10, fh=fh, frame="9aa4ae", style="vertical", group="work")
    fr = facade("plaster", "f4f6f8", win=win, doors=[(100, 40, 30, "double_glass")], seed=561, plinth=("8a96a2", 6),
                bands=[(fh * k - 2, fh * k + 1, "c8d4e0") for k in range(1, floors)])
    sd = facade("plaster", "f4f6f8", win=win, seed=562, plinth=("8a96a2", 6), bands=[(fh * k - 2, fh * k + 1, "c8d4e0") for k in range(1, floors)])
    box(T, 30, 90, 290, 260, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("8a8e94", "f4f6f8", 4))
    # red cross signs
    cross = lambda u, v, LL, HH: glow_res("e8342a", u.shape)
    for (a, b) in ((0, 0),):
        T.box(146, 86, 174, 90, H - 32, H - 22, all=cross, top=flat("e8342a"))
        T.box(155, 86, 165, 90, H - 41, H - 13, all=cross, top=flat("e8342a"))
    canopy(T, 90, 230, 90, 30, 34, "f4f6f8", "9aa4ae", posts=True)
    door(T, 130, 40, 90, 30)
    entry(T, 150)
    ground(T, 20, 0, 300, 90, kit.asphalt_lot("62646a", lines=("u", 10, 26, 0, 40)))
    T.box(240, 20, 262, 66, 0, 24, all=flat("f4f6f8", 3), top=flat("e8342a"))  # ambulance
    if L >= 3:
        # helipad on the roof
        x0, y0, x1, y1 = T.rect(90, 120, 230, 230)
        T.flat(90, 120, 230, 230, H + 1, lambda u, v, LL, D: (np.where((np.abs(np.hypot(u - LL / 2, v - D / 2) - 50) < 3)[..., None] |
                                                                     ((np.abs(u - LL / 2) < 3) & (np.abs(v - D / 2) < 20))[..., None] |
                                                                     ((np.abs(v - D / 2) < 3) & (np.abs(u - LL / 2) < 3))[..., None],
                                                                     C("f4f0e8"), C("4a4e56")) * np.ones(u.shape + (3,)), nores(u.shape), None))
    for k, ss in enumerate((20, 300)):
        tree(T, ss, 120, "lime", 0.85, 80 + k)
    return cv


# ====================================================================== money and law
def bank(L, o):
    cv = Canvas(2, 200)
    T = Orient(cv, o)
    H = [60, 70, 80][L - 1]
    fr = facade("stone", "e0d8c8", win=Win(w=16, h=26, sill=10, sp=34, margin=16, fh=40, frame="2a2a30", arch=True, group="work"),
                seed=571, plinth=("8a8478", 10), cornice=("f2eee6", 8), doors=[(110, 30, 34, "double", "2a2418")])
    box(T, 40, 90, 280, 260, 0, H, all=fr, top=flat_top("8a8e94", "f2eee6", 4))
    portico(T, 100, 220, 90, 28, H - 14, 6, "f4f0e8", True, "BANK")
    door(T, 145, 30, 90, 34)
    entry(T, 160)
    ground(T, 30, 0, 290, 62, kit.paving("d4ccbc", 12.0, 4))
    steps(T, 96, 224, 62, 2, 3)
    for k, ss in enumerate((50, 270)):
        lamp(T, ss, 30, "classic", 45, "light%d" % k)
    return cv


def court(L, o):
    cv = Canvas(2, 240)
    T = Orient(cv, o)
    H = 64
    fr = facade("stone", "d8d0c0", win=Win(w=14, h=30, sill=12, sp=34, margin=16, fh=H, frame="2a2a30", arch=True, group="work"),
                seed=581, plinth=("8a8478", 10), cornice=("f2eee6", 8))
    box(T, 30, 100, 290, 280, 0, H, all=fr, top=flat_top("8a8e94", "f2eee6", 4))
    portico(T, 90, 230, 100, 30, H - 4, 8, "f4f0e8", True, "COURT")
    door(T, 145, 30, 100, 34)
    entry(T, 160)
    x, y = T.pt(160, 200)
    T.cv.cylinder(x, y, 30, H, H + 20, lambda a, v, nx, ny: solid_res(C("e8e0cc"), a.shape))
    T.cv.ellipsoid(x, y, H + 20, 30, 30, 26, lambda wx, wy, wz, nx, ny, nz: solid_res(C("6a8a7a"), wx.shape), cut_z=H + 20)
    ground(T, 30, 0, 290, 70, kit.paving("d4ccbc", 12.0, 5))
    steps(T, 86, 234, 70, 3, 3)
    flagpole(T, 50, 40, 90, "2a5aa8")
    return cv


def town_hall(L, o):
    cv = Canvas(3, 320)
    T = Orient(cv, o)
    H = 80
    win = Win(w=18, h=30, sill=10, sp=36, margin=20, fh=40, frame="f2eee6", arch=True, group="work")
    fr = facade("stone", "e8dcc0", win=win, seed=591, plinth=("8a8478", 10), cornice=("f2eee6", 8), quoins="d8ccb0")
    box(T, 40, 160, 440, 400, 0, H, all=fr)
    T.hip(40, 160, 440, 400, H, 40, roof_mat("4a5a5a", "slate"), o=6)
    portico(T, 170, 310, 160, 30, H - 6, 6, "f6f2ea", True, "TOWN HALL")
    door(T, 225, 30, 160, 36)
    entry(T, 240)
    # clock tower
    tw = facade("stone", "e8dcc0", plinth=None, cornice=("f2eee6", 6), seed=592,
                decals=[(10, 50, 150, 190, "f8f4e8"), (29, 31, 160, 182, "2a2a30"), (20, 40, 169, 171, "2a2a30")])
    box(T, 210, 240, 270, 300, H, H + 140, all=tw)
    T.hip(210, 240, 270, 300, H + 140, 40, roof_mat("4a6a6a", "metal"), o=3)
    # plaza with a fountain and flags
    ground(T, 20, 0, 460, 160, kit.paving("d8d0c0", 14.0, 6))
    x, y = T.pt(240, 70)
    T.cv.cylinder(x, y, 30, 0, 6, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape),
                  lambda a, b: (np.broadcast_to(C("5ab0d8"), a.shape + (3,)).copy(), nores(a.shape), None))
    T.cv.cylinder(x, y, 5, 6, 24, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape))
    T.cv.mark("fountain", x, y, 26)
    for k, ss in enumerate((90, 390)):
        flagpole(T, ss, 120, 100, ["2a5aa8", "c8342a"][k])
        tree(T, ss, 40, "lime", 0.9, 90 + k)
    for k, ss in enumerate((150, 330)):
        lamp(T, ss, 120, "classic", 45, "light%d" % k)
    return cv


def post_office(L, o):
    cv = Canvas(1, 120)
    T = Orient(cv, o)
    floors = [1, 2, 2][L - 1]
    H = floors * 36 + 4
    fr = facade("plaster", "f2e8c8", win=Win(w=16, h=20, sill=8, sp=28, margin=10, fh=36, frame="2a4a8a", group="work"),
                doors=[(56, 22, 26, "double_glass")], seed=601, plinth=("4a4a50", 4), bands=[(30, 34, "2a4a8a")],
                signs=[(67, 32 if floors > 1 else 30, "POST", 5, None, "f8d040", True)] if floors > 1 else [(67, 28, "POST", 5, "2a4a8a", "f8d040", True)])
    box(T, 14, 40, 146, 140, 0, H, all=fr, top=flat_top("7a7672", "2a4a8a", 3))
    door(T, 70, 22, 40, 26)
    entry(T, 81)
    ground(T, 0, 0, 160, 40, kit.paving("c8c0b0", 8.0))
    for k in range(2):
        x, y = T.pt(30 + k * 14, 20)
        kit.mailbox(cv, x, y, "f8c840")
    return cv


# ====================================================================== sport and fun
def gym(L, o):
    cv = Canvas(2, 160)
    T = Orient(cv, o)
    H = 54
    fr = facade("metal", "3a4a5a", win=Win(w=40, h=26, sill=8, sp=50, margin=10, fh=60, frame="1e2228", style="vertical", group="work"),
                doors=[(100, 30, 28, "double_glass")], seed=611, plinth=("1e2228", 4), signs=[(115, 40, "SPORT", 9, None, "f8d040", True)])
    sd = facade("metal", "3a4a5a", seed=612, plinth=("1e2228", 4))
    box(T, 20, 60, 220, 300, 0, H, front=fr, back=sd, left=sd, right=sd)
    T.cv.mark("light", *T.pt(120, 60), H)
    # barrel roof
    for k in range(10):
        z = H + 14 * math.sin((k + 0.5) / 10 * math.pi)
        T.box(20 + k * 20, 60, 40 + k * 20, 300, H, z, all=flat("5a6a7a"), top=flat("6a7a8a"))
    door(T, 120, 30, 60, 28)
    entry(T, 135)
    court_ground(T, 228, 20, 312, 160, "3a7aa8", kind="court")
    fence(T, 226, 314, 18, "s", "3a3a40", "metal", 20)
    court_ground(T, 228, 170, 312, 312, "4a8a4a", kind="court")
    ground(T, 20, 0, 220, 60, kit.paving("b8b4ac", 10.0, 7))
    return cv


def stadium(L, o):
    cv = Canvas(3, 200)
    T = Orient(cv, o)
    court_ground(T, 90, 90, 390, 390, kind="pitch")
    tiers = 3 + L
    seat_cols = ["c8342a", "2a5aa8", "e8e8ea"]
    for k in range(tiers):
        h0 = k * 9
        d = 12
        c = seat_cols[k % 3]
        stand = lambda u, v, LL, HH, c=c: (np.where(((np.floor(u / 4) % 2) == 0)[..., None], C(c), C(c) * 0.85) * np.ones(u.shape + (3,)), nores(u.shape), None)
        # four stands stepping back and up
        T.box(80 - k * d, 80 - (k + 1) * d, 400 + k * d, 80 - k * d, h0, h0 + 9, all=stand, top=flat(c))
        T.box(80 - k * d, 400 + k * d, 400 + k * d, 400 + (k + 1) * d, h0, h0 + 9, all=stand, top=flat(c))
        T.box(80 - (k + 1) * d, 80 - k * d, 80 - k * d, 400 + k * d, h0, h0 + 9, all=stand, top=flat(c))
        T.box(400 + k * d, 80 - k * d, 400 + (k + 1) * d, 400 + k * d, h0, h0 + 9, all=stand, top=flat(c))
    zt = tiers * 9
    for k, (ss, ff) in enumerate(((40, 40), (440, 40), (40, 440), (440, 440))):
        post(T, ss, ff, 0, zt + 70, "c8ccd0", 3)
        T.box(ss - 10, ff - 2, ss + 10, ff + 2, zt + 62, zt + 74, all=lambda u, v, LL, HH: glow_res("f8f8f0", u.shape), top=flat("8a8e94"))
        T.cv.mark("light%d" % k, *T.pt(ss, ff), zt + 68)
    door(T, 220, 40, 80 - tiers * 12, 20)
    entry(T, 240)
    sign_board(T, 240, 80 - tiers * 12 - 2, zt + 2, "STADIUM", 12, "1e2228", "f8f8f0")
    return cv


def zoo(L, o):
    cv = Canvas(3, 160)
    T = Orient(cv, o)
    # paths
    ground(T, 220, 0, 260, 480, kit.paving("c8b890", 10.0, 2))
    ground(T, 20, 220, 460, 260, kit.paving("c8b890", 10.0, 3))
    pens = [(30, 30, 210, 210), (270, 30, 450, 210), (30, 270, 210, 450), (270, 270, 450, 450)]
    looks = ["b8a870", "7a9a4a", "8a9a5a", "a89a70"]
    for k, (s0, f0, s1, f1) in enumerate(pens[: 2 + L]):
        ground(T, s0, f0, s1, f1, kit.gravel(looks[k]))
        fence(T, s0, s1, f0, "s", "8a6a48", "rail", 12)
        fence(T, f0, f1, s0, "f", "8a6a48", "rail", 12)
        fence(T, f0, f1, s1, "f", "8a6a48", "rail", 12)
        fence(T, s0, s1, f1, "s", "8a6a48", "rail", 12)
        x0, y0, x1, y1 = T.rect(s0 + 20, f0 + 100, s0 + 70, f0 + 150)
        kit.pool(cv, x0, y0, x1, y1) if k % 2 == 0 else None
        tree(T, s1 - 30, f1 - 30, ["oak", "pine", "birch", "lime"][k], 0.8, 100 + k)
        rock = lambda wx, wy, wz, nx, ny, nz: solid_res(C("9a948a") * (0.85 + 0.2 * nz[..., None]), wx.shape)
        T.cv.ellipsoid(*T.pt(s0 + 120, f0 + 40), 8, 18, 14, 12, rock)
        cv.points["pen%d" % k] = T.grid((s0 + s1) / 2, (f0 + f1) / 2)
    # entrance arch
    gate = facade("stone", "a89a84", plinth=None, signs=[(40, 26, "ZOO", 10, None, "f8f4e8", True)])
    T.box(200, 0, 280, 10, 30, 44, front=gate, back=gate, left=flat("a89a84"), right=flat("a89a84"), top=flat("8a7a64"))
    for ss in (200, 270):
        T.box(ss, 0, ss + 10, 10, 0, 44, all=facade("stone", "a89a84", plinth=None), top=flat("8a7a64"))
    door(T, 220, 40, 5, 30)
    entry(T, 240)
    kiosk = facade("wood", "8a5a34", shop=(4, 26, 14), plinth=None, seed=621)
    box(T, 290, 236, 330, 256, 0, 26, all=kiosk, top=flat("2e7a4a"))
    return cv


def funfair(L, o):
    cv = Canvas(3, 260)
    T = Orient(cv, o)
    ground(T, 10, 10, 470, 470, kit.paving("d8c8a0", 14.0, 4))
    # ferris wheel
    cx_s, cx_f = 140, 300
    R = 80 + L * 8
    hub = R + 20
    x, y = T.pt(cx_s, cx_f)
    ax = T.axis("s")
    for k in (-1, 1):
        if ax == "x":
            T.cv.box(x - 3, y + k * 12 - 2, 0, x + 3, y + k * 12 + 2, hub, flat("e8e8ea"), flat("e8e8ea"), flat("e8e8ea"))
        else:
            T.cv.box(x + k * 12 - 2, y - 3, 0, x + k * 12 + 2, y + 3, hub, flat("e8e8ea"), flat("e8e8ea"), flat("e8e8ea"))
    ring = lambda u, v, LL, HH: (np.broadcast_to(C("e8e8ea"), u.shape + (3,)).copy(), nores(u.shape), None)
    def wheel_mask(a, z):
        r = np.hypot(a - R, z - hub)
        ang = np.arctan2(z - hub, a - R)
        spokes = (np.abs(((ang + math.pi) % (math.pi / 6)) - math.pi / 12) * r < 1.2) & (r < R)
        return (np.abs(r - R) < 2.0) | (np.abs(r - R * 0.92) < 1.2) | spokes
    T.panel(cx_s - R, cx_s + R, cx_f, hub - R, hub + R, ring, "s", lambda u, v: wheel_mask(u, v + hub - R))
    cols = ["e8342a", "f8c040", "2a8ad8", "3aa85a"]
    for k in range(12):
        a = k / 12 * 2 * math.pi
        ss = cx_s + math.cos(a) * R
        zz = hub + math.sin(a) * R - 12
        T.box(ss - 5, cx_f - 5, ss + 5, cx_f + 5, zz, zz + 10, all=flat(cols[k % 4]), top=flat(cols[k % 4]))
    cv.mark("wheel", *T.pt(cx_s, cx_f), hub)
    # carousel
    x, y = T.pt(340, 140)
    T.cv.cylinder(x, y, 40, 0, 6, lambda a, v, nx, ny: solid_res(C("e8d8b0"), a.shape), lambda a, b: solid_res(C("c8a870"), a.shape))
    T.cv.cylinder(x, y, 4, 6, 40, lambda a, v, nx, ny: solid_res(C("f8c040"), a.shape))
    w = 90
    ys, xs = np.mgrid[0:w, 0:w] + 0.5
    d = np.hypot(xs - w / 2, ys - w / 2)
    ang = np.arctan2(ys - w / 2, xs - w / 2)
    Hh = np.where(d < 42, 54 - d * 0.35, -np.inf)
    stripes = (np.floor((ang + math.pi) / (math.pi / 8)) % 2) == 0
    T.cv.heightfield(x - w / 2, y - w / 2, Hh, lambda wx, wy, wz, nx, ny, nz: (
        np.where(stripes[np.clip((wy - (y - w / 2)).astype(int), 0, w - 1), np.clip((wx - (x - w / 2)).astype(int), 0, w - 1)][..., None],
                 C("e8342a"), C("f8f0e0")), nores(wx.shape), None), zmin=36, thick=4.0)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        T.cv.box(x + math.cos(a) * 30 - 3, y + math.sin(a) * 30 - 3, 8, x + math.cos(a) * 30 + 3, y + math.sin(a) * 30 + 3, 20,
                 flat("f4f0e8"), flat("e8e4dc"), flat("f4f0e8"))
    cv.mark("light", x, y, 50)
    # stalls
    for k in range(2 + L):
        s0 = 260 + (k % 3) * 70
        f0 = 300 + (k // 3) * 80
        stall = facade("wood", ["f8c040", "e86a8a", "6ac8e8", "8ad86a", "f88a4a"][k % 5], shop=(4, 46, 16), plinth=None, seed=630 + k)
        box(T, s0, f0, s0 + 54, f0 + 36, 0, 26, all=stall, top=flat("e8342a"))
    # gate
    gate = facade("plaster", "e8342a", plinth=None, signs=[(50, 24, "FUNFAIR", 8, None, "fff0a0", True)])
    T.box(190, 0, 290, 10, 32, 46, front=gate, back=gate, left=flat("e8342a"), right=flat("e8342a"), top=flat("f8c040"))
    for ss in (190, 280):
        T.box(ss, 0, ss + 10, 10, 0, 46, all=flat("f8c040"), top=flat("e8342a"))
    door(T, 210, 60, 5, 30)
    entry(T, 240)
    return cv


# ====================================================================== parking
def parking(L, o):
    cv = Canvas(2, 90)
    T = Orient(cv, o)
    parking_lot(T, 6, 6, 314, 314, "s", 26)
    ground(T, 6, 140, 314, 180, kit.asphalt_lot("5a5c62"))
    booth = facade("plaster", "f4f2ee", win=Win(w=14, h=12, sill=10, sp=20, margin=4, fh=30, frame="3a3a40", group="work"), plinth=None, seed=641)
    box(T, 10, 4, 34, 26, 0, 26, all=booth, top=flat("2a5aa8"))
    pole_sign(T, 40, 8, 60, "P", 18, "2a5aa8", "ffffff")
    for k, ss in enumerate((100, 220)):
        lamp(T, ss, 160, "modern", 60, "light%d" % k)
    if L >= 2:
        for k, ss in enumerate((60, 160, 260)):
            tree(T, ss, 316, "lime", 0.6, 650 + k)
    door(T, 34, 6, 4, 20)
    entry(T, 160)
    # bays for the life simulation: two rows facing the aisle
    bays = []
    for row, (f0, f1) in enumerate(((20, 136), (184, 300))):
        for k in range(11):
            s = 19 + k * 26
            bays.append(T.grid(s, (f0 + f1) / 2) + [0 if row == 0 else 1])
    cv.bays = bays
    return cv


# ====================================================================== decor
def tree_lot(L, o):
    cv = Canvas(1, 140)
    T = Orient(cv, o)
    kinds = ["oak", "lime", "maple"]
    pts = [(80, 80), (40, 120), (120, 40)]
    for k in range(L):
        s, f = pts[k]
        tree(T, s, f, kinds[k], 1.0 - 0.1 * k, 700 + k)
    if L >= 3:
        bench(T, 110, 120, "s")
    return cv


def flowerbed(L, o):
    cv = Canvas(1, 60)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.paving("d4ccbc", 10.0, 2))
    import bkit
    for k, (s0, f0, s1, f1) in enumerate(((14, 14, 70, 70), (90, 14, 146, 70), (14, 90, 70, 146), (90, 90, 146, 146))[: 2 + L - (L == 3)]):
        bkit.flowerbed(T, s0, f0, s1, f1, 710 + k)
    bench(T, 80, 80, "s")
    if L >= 2:
        bins(T, 146, 146)
    if L >= 3:
        lamp(T, 80, 10, "classic", 42)
    return cv


def square(L, o):
    """Small square with benches (replaces the single bench)."""
    cv = Canvas(1, 120)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.paving("c8c0b2", 8.0, 3))
    bench(T, 50, 40, "s")
    bench(T, 110, 40, "s")
    tree(T, 80, 110, "lime", 0.8, 720)
    if L >= 2:
        bench(T, 40, 110, "f")
        lamp(T, 140, 20, "classic", 42)
    if L >= 3:
        bins(T, 140, 140)
    return cv


def fountain(L, o):
    cv = Canvas(1, 100)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.paving("d4ccbc", 10.0, 5))
    x, y = T.pt(80, 80)
    r = 40 + L * 6
    T.cv.cylinder(x, y, r, 0, 7, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape),
                  lambda a, b: (C("4aa8d8") + (np.sin(np.hypot(a, b) * 0.6) * 18)[..., None], nores(a.shape), None))
    T.cv.cylinder(x, y, 6, 7, 26, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape))
    T.cv.cylinder(x, y, 16, 26, 29, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape),
                  lambda a, b: solid_res(C("6ac0e8"), a.shape))
    if L >= 3:
        T.cv.cylinder(x, y, 3, 29, 44, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape))
    cv.mark("fountain", x, y, 30 if L < 3 else 44)
    for k, (ss, ff) in enumerate(((20, 20), (140, 140))):
        bench(T, ss + 10, ff, "s")
    return cv


def statue(L, o):
    cv = Canvas(1, 160)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.paving("d8d0c0", 12.0, 6))
    T.box(55, 55, 105, 105, 0, 22, all=facade("stone", "c8c0b0", plinth=None), top=flat("d8d0c0"))
    T.box(62, 62, 98, 98, 22, 30, all=facade("stone", "c8c0b0", plinth=None), top=flat("d8d0c0"))
    col = ["8a7a60", "6a8a7a", "c8a040"][L - 1]
    x, y = T.pt(80, 80)
    m = lambda wx, wy, wz, nx, ny, nz: solid_res(C(col) * (0.8 + 0.3 * nz[..., None]), wx.shape)
    T.cv.ellipsoid(x, y, 46, 8, 7, 16, m)
    T.cv.ellipsoid(x, y, 66, 5, 5, 6, m)
    T.cv.box(x + 6, y - 2, 52, x + 9, y + 2, 82, flat(col), flat(col), flat(col))
    T.cv.ellipsoid(x + 7.5, y, 86, 3, 3, 4, lambda *a: glow_res("ffb040", a[0].shape))
    T.cv.mark("light", x + 7.5, y, 86)
    for k, (ss, ff) in enumerate(((20, 30), (140, 30))):
        bush(T, ss, ff, 0.7, 730 + k, "f4d040" if k else "e86a8a")
    return cv


def park(L, o):
    cv = Canvas(2, 150)
    T = Orient(cv, o)
    # winding paths
    def paths(u, v, LL, D):
        shape = u.shape
        rgb = np.broadcast_to(C("d4c49c"), shape + (3,)).copy()
        rgb += ((hash2(np.floor(u), np.floor(v), 5) - 0.5) * 14)[..., None]
        return rgb, nores(shape), None
    def path_mask(u, v):
        c1 = np.abs(v - (160 + 50 * np.sin(u / 60))) < 9
        c2 = np.abs(u - (160 + 40 * np.sin(v / 70 + 1))) < 9
        return c1 | c2
    x0, y0, x1, y1 = T.rect(0, 0, 320, 320)
    with T.cv.ground:
        T.cv.top(0.3, x0, y0, x1, y1, paths, shade=1.0, extra=lambda u, v: path_mask(u, v))
    # pond
    if L >= 2:
        def water(u, v, LL, D):
            return (C("4a9ac0") + ((np.sin(u * 0.2 + v * 0.13) * 10))[..., None], nores(u.shape), None)
        with T.cv.ground:
            px0, py0, px1, py1 = T.rect(200, 200, 300, 290)
            T.cv.top(0.4, px0, py0, px1, py1, water, shade=1.0,
                     extra=lambda u, v: ((u - 50) / 50) ** 2 + ((v - 45) / 45) ** 2 < 1)
    kinds = ["oak", "lime", "maple", "birch", "spruce"]
    spots = [(50, 50), (270, 40), (40, 270), (110, 90), (250, 130), (80, 220), (180, 280), (300, 300), (150, 30)]
    for k, (ss, ff) in enumerate(spots[: 5 + L]):
        tree(T, ss, ff, kinds[k % 5], 0.85 + 0.1 * ((k * 7) % 3) / 2, 740 + k)
    for k, (ss, ff, al) in enumerate(((130, 150, "s"), (200, 175, "s"), (175, 110, "f"))):
        bench(T, ss, ff, al)
    for k, (ss, ff) in enumerate(((150, 200), (100, 160))):
        lamp(T, ss, ff, "classic", 42, "light%d" % k)
    bush(T, 20, 140, 1.0, 1, "e86a8a")
    bush(T, 300, 200, 1.0, 2, "f4d040")
    door(T, 150, 20, 0, 20)
    entry(T, 160)
    return cv


def playground(L, o):
    cv = Canvas(1, 90)
    T = Orient(cv, o)
    ground(T, 6, 6, 154, 154, lambda u, v, LL, D: (np.broadcast_to(C("c8603e" if L < 3 else "3a8ac8"), u.shape + (3,)).copy() +
                                                  ((hash2(np.floor(u), np.floor(v), 3) - 0.5) * 10)[..., None], nores(u.shape), None))
    x, y = T.pt(40, 40)
    kit.swing(cv, x - 12, y) if T.o in (0, 2) else kit.swing(cv, x, y - 12)
    # slide tower
    for (ss, ff) in ((100, 90), (120, 90), (100, 110), (120, 110)):
        post(T, ss, ff, 0, 22, "3a6ac8", 1.6)
    slab(T, 98, 88, 122, 112, 20, 22, "f8c040")
    T.box(104, 112, 116, 150, 0, 4, all=flat("e8342a"), top=flat("e8342a"))
    T.box(46, 100, 76, 130, 0, 3, all=flat("b07a48"), top=flat("ead7a0", 10))
    fence(T, 4, 156, 4, "s", "f4f0e8", "picket", 8, gap=(70, 90))
    if L >= 2:
        bench(T, 140, 60, "f")
    return cv


def plaza(L, o):
    cv = Canvas(2, 130)
    T = Orient(cv, o)
    ground(T, 0, 0, 320, 320, kit.paving("d8d0c2" if L < 3 else "c8b8a0", 16.0, 7))
    x, y = T.pt(160, 160)
    T.cv.cylinder(x, y, 50, 0, 8, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape),
                  lambda a, b: (C("4aa8d8") + (np.sin(np.hypot(a, b) * 0.5) * 16)[..., None], nores(a.shape), None))
    T.cv.cylinder(x, y, 8, 8, 30, lambda a, v, nx, ny: solid_res(C("e8e4dc"), a.shape))
    cv.mark("fountain", x, y, 32)
    for k, (ss, ff) in enumerate(((50, 50), (270, 50), (50, 270), (270, 270))):
        T.box(ss - 14, ff - 14, ss + 14, ff + 14, 0, 6, all=flat("c8c0b0"), top=flat("6a4a30"))
        tree(T, ss, ff, "lime", 0.8, 760 + k)
    for k, (ss, ff, al) in enumerate(((160, 80, "s"), (160, 240, "s"), (80, 160, "f"), (240, 160, "f"))):
        bench(T, ss, ff, al)
    for k, (ss, ff) in enumerate(((110, 110), (210, 210))):
        lamp(T, ss, ff, "classic", 44, "light%d" % k)
    door(T, 150, 20, 0, 20)
    entry(T, 160)
    return cv


def pond(L, o):
    cv = Canvas(2, 140)
    T = Orient(cv, o)
    def water(u, v, LL, D):
        rgb = C("3a8ab0") + ((np.sin(u * 0.15 + v * 0.11) + np.sin(u * 0.07 - v * 0.17)) * 8)[..., None]
        return rgb, nores(u.shape), None
    x0, y0, x1, y1 = T.rect(40, 60, 280, 280)
    with T.cv.ground:
        T.cv.top(0.4, x0 - 6, y0 - 6, x1 + 6, y1 + 6, lambda u, v, LL, D: (np.broadcast_to(C("c8b890"), u.shape + (3,)).copy(), nores(u.shape), None),
                 shade=1.0, extra=lambda u, v: ((u - 126) / 126) ** 2 + ((v - 116) / 116) ** 2 < 1)
        T.cv.top(0.6, x0, y0, x1, y1, water, shade=1.0, extra=lambda u, v: ((u - 120) / 120) ** 2 + ((v - 110) / 110) ** 2 < 1)
    for k, (ss, ff) in enumerate(((40, 40), (290, 70), (30, 290), (300, 290))):
        tree(T, ss, ff, ["lime", "birch", "oak", "maple"][k], 0.9, 780 + k)
    # reeds and ducks
    for k in range(10):
        ss, ff = 60 + (k * 37) % 200, 80 + (k * 53) % 180
        x, y = T.pt(ss, ff)
    for k, (ss, ff) in enumerate(((150, 150), (180, 170), (130, 190))[: L]):
        x, y = T.pt(ss, ff)
        T.cv.ellipsoid(x, y, 2, 4, 2.5, 2.5, lambda *a: solid_res(C("f4f0e8"), a[0].shape))
        T.cv.ellipsoid(x + 3, y, 5, 1.6, 1.6, 1.6, lambda *a: solid_res(C("2a6a3a"), a[0].shape))
    bench(T, 160, 30, "s")
    lamp(T, 100, 20, "classic", 42)
    door(T, 150, 20, 0, 20)
    entry(T, 160)
    return cv


BUILDERS = {"school": school, "kindergarten": kindergarten, "library": library, "museum": museum,
            "fire_station": fire_station, "police": police, "hospital": hospital, "bank": bank, "court": court,
            "town_hall": town_hall, "post_office": post_office, "gym": gym, "stadium": stadium, "zoo": zoo,
            "funfair": funfair, "parking": parking, "tree": tree_lot, "flowerbed": flowerbed, "bench": square,
            "fountain": fountain, "statue": statue, "park": park, "playground": playground, "plaza": plaza, "pond": pond}


# ====================================================================== construction site
def scaffold(n):
    cv = Canvas(n, 90 + 40 * n)
    T = Orient(cv, 0)
    S2 = n * U
    ground(T, 6, 6, S2 - 6, S2 - 6, kit.gravel("a8987c"))
    # fence panels around the site
    for a0, a1, b, al in ((4, S2 - 4, 4, "s"), (4, S2 - 4, S2 - 4, "s"), (4, S2 - 4, 4, "f"), (4, S2 - 4, S2 - 4, "f")):
        fence(T, a0, a1, b, al, "e8e4dc", "glass" if False else "boards", 14)
    # rising frame of the new building
    h = 40 + 20 * n
    s0, s1 = 30, S2 - 30
    for k in range(int((s1 - s0) / 30) + 1):
        for j in range(int((s1 - s0) / 30) + 1):
            if k in (0, int((s1 - s0) / 30)) or j in (0, int((s1 - s0) / 30)):
                post(T, s0 + k * 30, s0 + j * 30, 0, h, "c8c0b0", 2.2)
    for z in range(30, h + 1, 30):
        slab(T, s0 - 2, s0 - 2, s1 + 2, s1 + 2, z - 2, z, "c8c0b0")
    # yellow crane
    cs, cf = S2 - 22, 22
    post(T, cs, cf, 0, h + 70, "e8b830", 3.5)
    slab(T, cs - 90 * n, cf - 3, cs + 30, cf + 3, h + 66, h + 72, "e8b830")
    post(T, cs - 60 * n, cf, h + 30, h + 66, "3a3a40", 0.6)
    T.box(cs - 60 * n - 6, cf - 6, cs - 60 * n + 6, cf + 6, h + 22, h + 30, all=flat("8a6a48"), top=flat("9a7a58"))
    for k in range(n + 1):
        T.box(20 + k * 30, S2 - 40, 40 + k * 30, S2 - 20, 0, 10, all=flat("c8965a", 8), top=flat("d8a66a"))
    return cv
