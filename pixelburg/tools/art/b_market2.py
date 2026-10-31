"""Supermarkets (ROADMAP 26): "Amid", "Anis", "Yovar". Names on the signs as given; the buildings and the logos are
the game's own. Amid - a blue-white glass hall with a round logo; Anis - a warm brick market hall with a star logo
and a gable roof; Yovar - a yellow-teal discount warehouse with a saw-tooth roof and a hexagon logo.
builder(L, o) -> Canvas, 2x2 plot."""
import math

import numpy as np

from raster import C, Canvas, flat, nores, glow_res
from arch import Orient, facade, Win, flat_top, roof_mat
import kit
from bkit import (door, entry, ground, tree, bush, lamp, bench, box, slab, post, canopy, awning, sign_board, pole_sign,
                  parking_lot, car_static, roof_units)


def _paint(col):
    return lambda u, v, LL, HH: (C(col) * np.ones(u.shape + (3,)), nores(u.shape), None)


def _glow(col):
    return lambda u, v, LL, HH: glow_res(col, u.shape)


def _logo(T, s, f, z, r, kind, c1, c2, rim="ffffff"):
    """A round-ish emblem panel on a wall, 2r wide: kind 'disc' (disc + chevron), 'star' (8-point star), 'hex' (hexagon + Y)."""
    def fn(u, v, LL, HH):
        x = (u - r) / r
        y = (v - r) / r
        d = np.hypot(x, y)
        a = np.arctan2(y, x)
        out = np.zeros(u.shape + (3,)) + C(rim)
        if kind == "disc":
            out[d < 0.82] = C(c1)
            ch = (np.abs(x) < 0.55) & (np.abs(y + 0.4 - np.abs(x) * 1.2) < 0.2)       # a chevron (the "A" roof)
            out[ch & (d < 0.82)] = C(c2)
            out[(np.abs(y + 0.2) < 0.09) & (np.abs(x) < 0.3) & (d < 0.82)] = C(c2)
            m = d < 0.95
        elif kind == "star":
            rad = 0.62 + 0.33 * np.abs(np.cos(a * 4))
            out[d < rad] = C(c1)
            out[d < 0.2] = C(c2)
            m = d < 1.0
            out[(d >= rad) & m] = C(c2)
        else:
            hx = np.maximum(np.abs(x) * 0.866 + np.abs(y) * 0.5, np.abs(y))
            out[hx < 0.9] = C(c1)
            yy = ((np.abs(x + (y - 0.1) * 0.0) < 0.14) & (y < 0.1)) | ((np.abs(np.abs(x) - (y - 0.1) * 0.75) < 0.15) & (y >= 0.1) & (y < 0.7))
            out[yy & (hx < 0.9)] = C(c2)
            m = hx < 1.0
        return out, ~m & False, None
    T.box(s - r - 2, f - 1.8, s + r + 2, f, z - 2, z + 2 * r + 2, all=_paint(c1), top=flat(c1))
    T.panel(s - r, s + r, f - 1.9, z, z + 2 * r, fn, "s")


def _trolleys(T, s0, f0, s1, f1, col):
    slab(T, s0, f0, s1, f1, 14, 16, col)
    for s in range(int(s0) + 2, int(s1) - 1, 8):
        post(T, s, f0 + 2, 0, 14, "9a9ca2", 1.0)
        post(T, s, f1 - 2, 0, 14, "9a9ca2", 1.0)


# ============================================================================ Amid: blue-white glass hall
def amid(L, o):
    cv = Canvas(2, 160)
    T = Orient(cv, o)
    H = [46, 52, 60][L - 1]
    s0, s1, f0, f1 = 20, 300, 150, 300
    front = facade("concrete", "f4f6fa", shop=(30, 250, 34), doors=[(118, 40, 32, "double_glass")], plinth=("5a6a8a", 3), seed=2601,
                   bands=[(36, H, "1f5fbf")])
    side = facade("metal", "e4e8f0", seed=2602, plinth=("5a6a8a", 3), bands=[(H - 6, H, "1f5fbf")])
    box(T, s0, f0, s1, f1, 0, H, front=front, back=side, left=side, right=side, top=flat_top("9aa4b4", "1f5fbf", 4))
    roof_units(T, s0, f0, s1, f1, H, 2601, 6, stair=False)
    # a taller glass entrance block with a slanted look: a box sticking out of the wall
    T.box(100, f0 - 14, 200, f0, 0, H + 8, front=flat("cfe6ff", 3), left=flat("aebed8", 3), right=flat("aebed8", 3), back=flat("aebed8"),
          top=flat("1f5fbf", 4))
    T.box(104, f0 - 14.5, 196, f0 - 14, 3, 34, all=_glow("dff0ff"))
    sign_board(T, 150, f0 - 14, H - 4, "AMID", 11, "1f5fbf", "ffffff")
    _logo(T, 70, f0, H + 2, 11, "disc", "1f5fbf", "ffffff")
    _logo(T, 250, f0, H + 2, 11, "disc", "1f5fbf", "ffffff")
    door(T, 138, 40, f0 - 14, 30)
    entry(T, 150)
    parking_lot(T, 10, 0, 310, 120, "s", 26)
    ground(T, 10, 120, 310, f0 - 14, kit.paving("c8ccd4", 10.0, 26))
    for ss in (20, 300):
        tree(T, ss, 70, "lime", 0.8, 11 + ss)
    pole_sign(T, 40, 128, 70, "AMID", 11, "1f5fbf", "ffffff")
    lamp(T, 100, 70, "modern", 60)
    lamp(T, 220, 70, "modern", 60, "light2")
    _trolleys(T, 232, 128, 288, 142, "1f5fbf")
    if L >= 2:
        bench(T, 60, 134, "s")
        car_static(T, 70, 30, "s", "f4f6fa")
    if L >= 3:
        car_static(T, 200, 30, "s", "1f5fbf")
        T.box(40, f0 - 2, 90, f0 - 0.5, 4, 8, all=_paint("1f5fbf"))
    return cv


# ============================================================================ Anis: warm brick market hall, gable roof
def anis(L, o):
    cv = Canvas(2, 190)
    T = Orient(cv, o)
    fh = 44
    H = [46, 52, 58][L - 1]
    s0, s1, f0, f1 = 24, 296, 140, 296
    win = Win(w=16, h=22, sill=14, sp=36, margin=18, fh=fh, frame="f4ecd8", arch=True, group="work")
    front = facade("brick", "b0653c", win=win, doors=[(118, 40, 32, "double_glass")], plinth=("5a3a28", 4), seed=2611,
                   cornice=("f0e2c4", 5), shop=(30, 250, 34))
    side = facade("brick", "b0653c", win=win, seed=2612, plinth=("5a3a28", 4), cornice=("f0e2c4", 5))
    box(T, s0, f0, s1, f1, 0, H, front=front, back=side, left=side, right=side)
    T.hip(s0, f0, s1, f1, H, 34, roof_mat("7a3a28", "tile"), o=4)
    # striped awning along the shop windows and a star logo over the door
    awning(T, 40, 112, f0, 34, 12, 6, "e8a030", "f8f0dc", 6.0)
    awning(T, 208, 280, f0, 34, 12, 6, "e8a030", "f8f0dc", 6.0)
    canopy(T, 118, 202, f0, 16, 38, "f0e2c4", "7a3a28", posts=True)
    sign_board(T, 160, f0, H - 10, "ANIS", 11, "3a2a24", "f8d878")
    _logo(T, 70, f0, H + 2, 11, "star", "e8a030", "7a2a1c", "f8f0dc")
    _logo(T, 250, f0, H + 2, 11, "star", "e8a030", "7a2a1c", "f8f0dc")
    door(T, 138, 40, f0, 32)
    entry(T, 160)
    # crates of fruit by the wall and a bike rack-like trolley bay
    for k, ss in enumerate((50, 70, 90)):
        T.box(ss - 7, f0 - 14, ss + 7, f0 - 4, 0, 8, all=_paint("a87a48"), top=flat(["d84a3a", "e8b830", "78a838"][k], 6))
    ground(T, 12, 90, 308, f0, kit.bricks_pave("c0a080"))
    parking_lot(T, 10, 0, 310, 90, "s", 26)
    for ss in (24, 296):
        tree(T, ss, 100, "oak" if L > 1 else "lime", 0.8, 21 + ss)
    pole_sign(T, 296, 96, 70, "ANIS", 11, "3a2a24", "f8d878")
    lamp(T, 120, 96, "classic", 56)
    lamp(T, 200, 96, "classic", 56)
    _trolleys(T, 224, 110, 280, 124, "7a3a28")
    if L >= 2:
        bench(T, 40, 110, "s")
        bush(T, 20, 130, 0.9, 2613)
    if L >= 3:
        car_static(T, 100, 30, "s", "e8a030")
        post(T, 30, 100, 0, 40, "7a3a28", 2.0)
    return cv


# ============================================================================ Yovar: yellow-teal discount warehouse
def yovar(L, o):
    cv = Canvas(2, 150)
    T = Orient(cv, o)
    H = [40, 44, 50][L - 1]
    s0, s1, f0, f1 = 14, 306, 150, 300
    front = facade("metal", "f2c830", shop=(40, 240, 26), doors=[(130, 44, 30, "double_glass")], plinth=("2a5a62", 4), seed=2621,
                   bands=[(30, H, "187a86")])
    side = facade("metal", "e8c230", seed=2622, plinth=("2a5a62", 4), bands=[(H - 8, H, "187a86")])
    box(T, s0, f0, s1, f1, 0, H, front=front, back=side, left=side, right=side, top=flat_top("5a6a70", "187a86", 4))
    # saw-tooth roof: glazed slopes stepping up along the building
    n = 5
    w = (s1 - s0 - 20) / n
    for i in range(n):
        a = s0 + 10 + i * w
        T.box(a, f0 + 12, a + w - 3, f1 - 12, H, H + 10, all=_paint("e8e0c8"), top=flat("187a86", 4))
        T.box(a + w - 6, f0 + 12, a + w - 3, f1 - 12, H, H + 10, front=_paint("dff0f2"), left=_paint("dff0f2"), right=_paint("dff0f2"),
              back=_paint("dff0f2"), top=flat("dff0f2"))
    T.box(40, f0 - 2, 130, f0, H - 24, H - 4, front=_paint("187a86"), left=_paint("187a86"), right=_paint("187a86"), top=flat("187a86"))
    sign_board(T, 85, f0 - 2, H - 22, "YOVAR", 11, "187a86", "f8e060")
    _logo(T, 250, f0, H + 2, 12, "hex", "187a86", "f8e060", "f8e060")
    door(T, 130, 44, f0, 30)
    entry(T, 152)
    # a wide shed over the entrance and a loading bay on the side
    canopy(T, 124, 180, f0, 14, 34, "187a86", "187a86", posts=True)
    T.box(s1 - 2, 200, s1 + 12, 270, 0, 22, all=_paint("5a6a70"), top=flat("4a5a60"))
    T.box(s1 + 12, 206, s1 + 40, 264, 0, 20, all=_paint("e8e0c8"), top=flat("187a86"))
    ground(T, 10, 128, 310, f0, kit.paving("b8b4a8", 10.0, 62))
    parking_lot(T, 10, 0, 310, 128, "s", 26)
    pole_sign(T, 44, 134, 78, "YOVAR", 11, "187a86", "f8e060")
    lamp(T, 150, 100, "modern", 60)
    lamp(T, 260, 100, "modern", 60, "light2")
    _trolleys(T, 200, 132, 250, 144, "187a86")
    if L >= 2:
        car_static(T, 250, 40, "s", "f2c830")
        tree(T, 300, 90, "lime", 0.8, 627)
    if L >= 3:
        car_static(T, 120, 40, "s", "187a86")
        bench(T, 90, 138, "s")
    return cv


BUILDERS = {"amid": amid, "anis": anis, "yovar": yovar}
