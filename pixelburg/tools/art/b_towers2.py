"""Fifteen more signature skyscrapers (ROADMAP 47), each with its own silhouette: stepped, twin with a sky bridge,
pyramid-topped, golden, green terraces, art-deco brick, wind turbines, observatory dome, slim needle, cross plan,
sail, ring gate, solar, crown, tripod. All 3x3 plots on a glass-and-stone podium plaza. builder(L, o) -> Canvas."""
import numpy as np

from raster import C, Canvas, flat, nores, glow_res
from arch import Orient, facade, Win, flat_top, roof_mat
import kit
from bkit import door, entry, ground, tree, bush, lamp, bench, box, slab, post, canopy, sign_board
from b_homes import spire

FH = 32


def _glow(col):
    return lambda u, v, LL, HH: glow_res(col, u.shape)


def _paint(col):
    return lambda u, v, LL, HH: (C(col) * np.ones(u.shape + (3,)), nores(u.shape), None)


def _curtain(col, tint, seed, floors, band="dce2e8", style="vertical", w=28, lit=0.5):
    win = Win(w=w, h=26, sill=3, sp=w + 3, margin=4, fh=FH, frame="8a96a2", style=style, tint=tint, group="work", top_skip=2)
    return facade("concrete", col, win=win, plinth=None, seed=seed, lit=lit,
                  bands=[(FH * k - 2, FH * k + 2, band) for k in range(floors + 3)])


def _podium(T, seed, col="c8ccd0", tint="7ab0d0", height=None):
    pod = height or 2 * FH + 8
    w = Win(w=30, h=44, sill=4, sp=34, margin=6, fh=pod, frame="8a96a2", style="vertical", tint=tint, group="work", top_skip=6)
    lob = facade("concrete", col, win=w, plinth=("4a4a50", 6), seed=seed, lit=0.9, doors=[(200, 60, 40, "double_glass")])
    lob2 = facade("concrete", col, win=w, plinth=("4a4a50", 6), seed=seed + 1, lit=0.7)
    box(T, 20, 90, 460, 420, 0, pod, front=lob, back=lob2, left=lob2, right=lob2, top=flat_top("8a8884", col, 5))
    canopy(T, 170, 300, 90, 40, 46, "2a2e34", "2a2e34", posts=False)
    door(T, 210, 60, 90, 40)
    entry(T, 240)
    return pod


def _plaza(T, name, seed, fg="e8eef4", bg="2a2e34", sx=200):
    ground(T, 10, 0, 470, 90, kit.paving("c4c0b8", 12.0, seed % 9 + 2))
    for k, ss in enumerate((50, 120, 360, 430)):
        tree(T, ss, 50, "maple" if seed % 2 else "lime", 0.7, seed + k)
    bench(T, 150, 45, "s")
    bench(T, 320, 45, "s")
    lamp(T, 90, 20, "modern", 60)
    lamp(T, 390, 20, "modern", 60, "light2")
    sign_board(T, sx, 90, 54, name, 11, bg, fg, depth=2)


def _canvas(H, o, extra=260):
    cv = Canvas(3, int(H + extra))
    return cv, Orient(cv, o)


def _tower(L, o, name, seed, col, tint, floors, crown=None, shaft=(90, 150, 390, 410), podcol="c8ccd0", band="dce2e8",
           top="7a7874", style="vertical", accent=None, steps=None, wing=None):
    fl = [floors[0], floors[1], floors[2]][L - 1]
    pod = 2 * FH + 8
    H = pod + fl * FH
    cv, T = _canvas(H, o)
    _podium(T, seed, podcol)
    cw = _curtain(col, tint, seed + 2, fl, band, style)
    s0, f0, s1, f1 = shaft
    if steps:   # setbacks: list of (inset, floors_from_top)
        z = pod
        cur = list(shaft)
        top_fl = fl
        for inset, nfl in steps:
            zh = z + (top_fl - nfl) * FH if False else z + (fl - nfl) * FH
            box(T, cur[0], cur[1], cur[2], cur[3], z, zh, all=cw, top=flat_top(top, band, 4))
            z = zh
            cur = [cur[0] + inset, cur[1] + inset, cur[2] - inset, cur[3] - inset]
        box(T, cur[0], cur[1], cur[2], cur[3], z, H, all=cw, top=flat_top(top, band, 4))
        s0, f0, s1, f1 = cur
    else:
        box(T, s0, f0, s1, f1, pod, H, all=cw, top=flat_top(top, band, 4))
    if accent:  # glowing vertical blades on the front corners
        for a in (shaft[0] + 4, shaft[2] - 8):
            T.box(a, shaft[1] - 1.2, a + 4, shaft[1], pod + 6, H - 6, all=_glow(accent), top=flat(accent))
    if crown:
        crown(T, s0, f0, s1, f1, H, seed)
    _plaza(T, name, seed)
    return cv


# ---------------------------------------------------------------- crowns
def c_spire(T, s0, f0, s1, f1, H, seed):
    T.box(s0 + 40, f0 + 40, s1 - 40, f1 - 40, H, H + 40, all=flat("b8c0c8", 3), top=flat_top("8a8884", "c8ccd0", 3))
    spire(T, (s0 + s1) / 2, (f0 + f1) / 2, H + 40, 110)


def c_pyramid(T, s0, f0, s1, f1, H, seed):
    T.hip(s0 + 6, f0 + 6, s1 - 6, f1 - 6, H, 90, roof_mat("6a9ab8", "tiles", seed), 0)
    spire(T, (s0 + s1) / 2, (f0 + f1) / 2, H + 90, 40)


def c_dome(T, s0, f0, s1, f1, H, seed):
    x, y = T.pt((s0 + s1) / 2, (f0 + f1) / 2)
    T.box(s0 + 30, f0 + 30, s1 - 30, f1 - 30, H, H + 18, all=flat("e4e8ec", 3), top=flat("c8ccd0"))
    T.cv.ellipsoid(x, y, H + 18, 80, 80, 66, lambda wx, wy, wz, nx, ny, nz: (np.broadcast_to(C("7ab0d8") + nz[..., None] * 40, wx.shape + (3,)).copy(), nores(wx.shape), None))
    spire(T, (s0 + s1) / 2, (f0 + f1) / 2, H + 80, 40)


def c_wind(T, s0, f0, s1, f1, H, seed):
    for k, (a, b) in enumerate(((s0 + 50, f0 + 60), (s1 - 50, f0 + 60), ((s0 + s1) / 2, f1 - 60))):
        x, y = T.pt(a, b)
        T.cv.cylinder(x, y, 3, H, H + 70, lambda aa, v, nx, ny: (np.broadcast_to(C("f0f0f0"), aa.shape + (3,)).copy(), nores(aa.shape), None))
        for ang in (0.3, 2.4, 4.5):
            dx, dy = np.cos(ang) * 46, np.sin(ang) * 46 * 0.5
            T.cv.box(x - 1.5 + dx / 2, y - 1.5 + dy / 2, H + 70, x + 1.5 + dx / 2, y + 1.5 + dy / 2, H + 72, flat("f8f8f8"), flat("f8f8f8"), flat("f8f8f8"))
            T.cv.box(x - 1.5 - dx / 2, y - 1.5 - dy / 2, H + 70, x + 1.5 - dx / 2, y + 1.5 - dy / 2, H + 72, flat("f8f8f8"), flat("f8f8f8"), flat("f8f8f8"))


def c_crown(T, s0, f0, s1, f1, H, seed):
    n = 7
    for k in range(n):
        a = s0 + 6 + k * (s1 - s0 - 18) / (n - 1)
        for b in (f0 + 6, f1 - 18):
            h = 40 if k % 2 == 0 else 24
            T.box(a, b, a + 12, b + 12, H, H + h, all=flat("e8c860", 3), top=flat("f4dc80"))
    T.box(s0 + 20, f0 + 20, s1 - 20, f1 - 20, H, H + 6, all=flat("e8c860", 3), top=flat("e8c860"))


def c_needle(T, s0, f0, s1, f1, H, seed):
    T.box(s0 + 10, f0 + 10, s1 - 10, f1 - 10, H, H + 30, all=flat("c8ccd0", 3), top=flat_top("8a8884", "e4e8ec", 3))
    spire(T, (s0 + s1) / 2, (f0 + f1) / 2, H + 30, 190)
    x, y = T.pt((s0 + s1) / 2, (f0 + f1) / 2)
    T.cv.ellipsoid(x, y, H + 100, 14, 14, 6, lambda wx, wy, wz, nx, ny, nz: glow_res("40e0ff", wx.shape))


def c_helipad(T, s0, f0, s1, f1, H, seed):
    T.box(s0 + 60, f0 + 60, s1 - 60, f1 - 60, H, H + 6, all=flat("4a4c52", 2), top=flat("4a4c52"))
    x, y = T.pt((s0 + s1) / 2, (f0 + f1) / 2)
    T.cv.ellipsoid(x, y, H + 7, 34, 17, 1.5, lambda wx, wy, wz, nx, ny, nz: (np.broadcast_to(C("e8c040"), wx.shape + (3,)).copy(), nores(wx.shape), None))


def c_garden(T, s0, f0, s1, f1, H, seed):
    for k in range(6):
        tree(T, s0 + 30 + k * ((s1 - s0 - 60) / 5), (f0 + f1) / 2 + (k % 2) * 40 - 20, "lime", 0.9, seed + k)
    for k in range(3):
        bush(T, s0 + 50 + k * 80, f0 + 40, 1.2, seed + 9 + k)


def c_dish(T, s0, f0, s1, f1, H, seed):
    T.box(s0 + 30, f0 + 30, s1 - 30, f1 - 30, H, H + 24, all=flat("b8c0c8", 3), top=flat_top("8a8884", "c8ccd0", 3))
    x, y = T.pt((s0 + s1) / 2, (f0 + f1) / 2)
    T.cv.ellipsoid(x, y, H + 36, 34, 34, 12, lambda wx, wy, wz, nx, ny, nz: (np.broadcast_to(C("f0f2f4") + nz[..., None] * 20, wx.shape + (3,)).copy(), nores(wx.shape), None))
    spire(T, (s0 + s1) / 2, (f0 + f1) / 2, H + 40, 50)


# ---------------------------------------------------------------- the 15 towers
def tower_stepped(L, o):
    return _tower(L, o, "STEP", 6101, "d4dae0", "4a7a9a", (22, 28, 34), c_garden, steps=[(24, 14), (24, 8)])


def tower_twin(L, o):
    fl = [24, 30, 36][L - 1]
    pod = 2 * FH + 8
    H = pod + fl * FH
    cv, T = _canvas(H, o)
    _podium(T, 6201)
    cw = _curtain("d0d6dc", "3a6a8a", 6203, fl)
    box(T, 60, 150, 190, 410, pod, H, all=cw, top=flat_top("7a7874", "dce2e8", 4))
    box(T, 290, 150, 420, 410, pod, H, all=cw, top=flat_top("7a7874", "dce2e8", 4))
    zb = pod + int(fl * 0.7) * FH
    T.box(190, 230, 290, 330, zb, zb + 2 * FH, all=_curtain("c0c8d0", "5a8aaa", 6204, 2), top=flat_top("7a7874", "dce2e8", 4))
    spire(T, 125, 280, H, 90)
    spire(T, 355, 280, H, 90)
    _plaza(T, "TWIN", 6201)
    return cv


def tower_pyramid(L, o):
    return _tower(L, o, "APEX", 6301, "c8d4dc", "3a6a8a", (24, 30, 36), c_pyramid, accent="ffd860")


def tower_gold(L, o):
    return _tower(L, o, "GOLD", 6401, "e4d8a8", "c89a30", (24, 30, 36), c_crown, band="f4dc80", podcol="e8d8a0", top="9a8a50", accent="ffd860")


def tower_green(L, o):
    return _tower(L, o, "ECO", 6501, "dce8d8", "4a8a5a", (22, 28, 34), c_garden, band="8ab870", podcol="d8e4d0", steps=[(14, 16), (14, 8)])


def tower_deco(L, o):
    return _tower(L, o, "DECO", 6601, "b86a50", "e8c880", (22, 28, 34), c_spire, band="e8c880", podcol="a85a40", top="6a3a2a",
                  steps=[(18, 14), (18, 8)])


def tower_wind(L, o):
    return _tower(L, o, "WIND", 6701, "e4ecf0", "5a9aba", (24, 30, 36), c_wind, band="b8d8e8")


def tower_dome(L, o):
    return _tower(L, o, "ORBIT", 6801, "d0d8e4", "3a5a8a", (24, 30, 36), c_dome, band="a8c0e0", accent="a070ff")


def tower_slim(L, o):
    return _tower(L, o, "NEEDLE", 6901, "c8ccd4", "6a8aa8", (30, 38, 46), c_needle, shaft=(170, 220, 310, 340), band="e8eef4", accent="40e0ff")


def tower_cross(L, o):
    fl = [24, 30, 36][L - 1]
    pod = 2 * FH + 8
    H = pod + fl * FH
    cv, T = _canvas(H, o)
    _podium(T, 7001)
    cw = _curtain("d4d8dc", "4a7a8a", 7003, fl)
    box(T, 90, 230, 390, 330, pod, H - 2 * FH, all=cw, top=flat_top("7a7874", "dce2e8", 4))
    box(T, 190, 150, 290, 410, pod, H, all=cw, top=flat_top("7a7874", "dce2e8", 4))
    c_dish(T, 190, 150, 290, 410, H, 7001)
    _plaza(T, "CROSS", 7001)
    return cv


def tower_sail(L, o):
    fl = [26, 32, 38][L - 1]
    pod = 2 * FH + 8
    H = pod + fl * FH
    cv, T = _canvas(H, o)
    _podium(T, 7101)
    cw = _curtain("e8f0f4", "6ab0d0", 7103, fl, band="ffffff")
    # a tall wall that gets lower towards the back - three stacked slabs form the sail
    for k, (f0, f1, hh) in enumerate(((150, 230, H), (230, 310, H - 5 * FH), (310, 410, H - 10 * FH))):
        box(T, 90, f0, 390, f1, pod, hh, all=cw, top=flat_top("7a7874", "ffffff", 4))
    T.box(88, 149, 96, 150, pod + 4, H, all=_glow("80d8ff"), top=flat("80d8ff"))
    spire(T, 240, 160, H, 60)
    _plaza(T, "SAIL", 7101)
    return cv


def tower_ring(L, o):
    fl = [24, 30, 36][L - 1]
    pod = 2 * FH + 8
    H = pod + fl * FH
    cv, T = _canvas(H, o)
    _podium(T, 7201)
    cw = _curtain("d8dce0", "4a6a8a", 7203, fl)
    box(T, 90, 150, 170, 410, pod, H, all=cw, top=flat_top("7a7874", "dce2e8", 4))
    box(T, 310, 150, 390, 410, pod, H, all=cw, top=flat_top("7a7874", "dce2e8", 4))
    box(T, 90, 150, 390, 410, H - 3 * FH, H, all=cw, top=flat_top("7a7874", "dce2e8", 4))
    T.box(170, 229, 178, 230, pod + 8, H - 3 * FH, all=_glow("b0a0ff"), top=flat("b0a0ff"))
    T.box(302, 229, 310, 230, pod + 8, H - 3 * FH, all=_glow("b0a0ff"), top=flat("b0a0ff"))
    spire(T, 130, 280, H, 60)
    spire(T, 350, 280, H, 60)
    _plaza(T, "GATE", 7201)
    return cv


def tower_solar(L, o):
    return _tower(L, o, "SOLAR", 7301, "2a3448", "1a2a4a", (24, 30, 36), c_helipad, band="5a7ab0", podcol="3a4458", top="2a3040", style="horizontal" if False else "vertical", accent="60ffa0")


def tower_tripod(L, o):
    fl = [24, 30, 36][L - 1]
    pod = 2 * FH + 8
    H = pod + fl * FH
    cv, T = _canvas(H, o)
    _podium(T, 7401)
    cw = _curtain("d4dae0", "4a7aaa", 7403, fl)
    for k, (a, b, hh) in enumerate(((80, 160, H), (200, 250, H - 4 * FH), (320, 160, H - 8 * FH))):
        box(T, a, b, a + 90, b + 130, pod, hh, all=cw, top=flat_top("7a7874", "dce2e8", 4))
        spire(T, a + 45, b + 65, hh, 40 + 20 * (2 - k))
    _plaza(T, "TRIO", 7401)
    return cv


def tower_crown(L, o):
    return _tower(L, o, "REGAL", 7501, "d8d0e0", "7a5aa8", (24, 30, 36), c_crown, band="f0e0ff", podcol="d0c8dc", accent="e060ff")


BUILDERS = {k: v for k, v in globals().items() if k.startswith("tower_")}
