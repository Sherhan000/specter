"""Night life (ROADMAP 43): a night club with neon stripes, a night market of lantern stalls and a karaoke bar with a
giant microphone. All 2x2 plots; the glow layer carries the neon. builder(L, o) -> Canvas."""
import numpy as np

from raster import C, Canvas, flat, nores, glow_res
from arch import Orient, facade, Win, flat_top
import kit
from bkit import (door, entry, ground, tree, bush, lamp, bench, box, slab, post, canopy, sign_board, pole_sign,
                  awning, roof_units, car_static)

PINK = "ff3fa8"
CYAN = "3fe0ff"
GOLD = "ffb030"


def _paint(col):
    return lambda u, v, LL, HH: (C(col) * np.ones(u.shape + (3,)), nores(u.shape), None)


def _glow(col):
    return lambda u, v, LL, HH: glow_res(col, u.shape)


def _neon_strip(T, s0, s1, f, z, col, h=3):
    T.box(s0, f - 1.6, s1, f, z, z + h, all=_glow(col), top=flat(col))


def nightclub(L, o):
    cv = Canvas(2, 170)
    T = Orient(cv, o)
    fh = 36
    H = [2, 2, 3][L - 1] * fh + 4
    win = Win(w=18, h=14, sill=14, sp=44, margin=18, fh=fh, frame="14101c", style="grid", group="work")
    fr = facade("concrete", "1c1824", win=win, doors=[(130, 44, 30, "double_glass")], seed=4301, plinth=("0c0a12", 4))
    sd = facade("concrete", "1c1824", win=win, seed=4302, plinth=("0c0a12", 4))
    box(T, 30, 80, 290, 200, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("2a2634", PINK, 4))
    # vertical neon stripes on the front face
    for k, s in enumerate((50, 96, 224, 270)):
        _neon_strip(T, s, s + 4, 80, 6, PINK if k % 2 == 0 else CYAN, H - 14)
    _neon_strip(T, 30, 290, 80, H - 4, CYAN, 3)
    _neon_strip(T, 30, 290, 80, 2, PINK, 3)
    # neon on the side walls too (the building is seen from any corner)
    for f in (100, 150, 190):
        T.box(29.4, f, 30, f + 4, 6, H - 8, all=_glow(CYAN if f == 150 else PINK))
        T.box(290, f, 290.6, f + 4, 6, H - 8, all=_glow(CYAN if f == 150 else PINK))
    # entrance block with a big sign
    T.box(110, 62, 210, 80, 0, 40, front=flat("14101c", 3), left=flat("14101c", 3), right=flat("14101c", 3),
          top=flat(PINK, 4))
    T.box(112, 61.5, 208, 62, 36, 40, all=_glow(PINK))
    door(T, 138, 44, 62, 30)
    entry(T, 160)
    sign_board(T, 160, 80, H + 2, "CLUB", 14, "0c0a12", PINK)
    # velvet-rope posts and a spotlight tower
    for s in (120, 140, 180, 200):
        post(T, s, 40, 0, 12, "d8b050", 1.8)
    T.box(124, 40, 196, 41.2, 7, 9, all=_paint("b01030"), top=flat("b01030"))
    post(T, 60, 40, 0, 60, "3a3a46", 2.0)
    T.box(54, 34, 66, 46, 58, 66, all=_glow("ffffff"), top=flat("ffffff"))
    roof_units(T, 60, 100, 270, 180, H, 4301, 4, stair=False)
    ground(T, 20, 0, 300, 62, kit.paving("2a2a36", 10.0, 43))
    lamp(T, 40, 20, "modern", 60)
    lamp(T, 280, 20, "modern", 60, "light2")
    if L >= 2:
        car_static(T, 250, 220, "s", PINK)
    if L >= 3:
        T.box(60, 100, 260, 180, H, H + 12, all=_paint("2a2634"), top=flat("14101c", 4))
        _neon_strip(T, 60, 260, 100, H + 4, CYAN, 3)
    return cv


def night_market(L, o):
    cv = Canvas(2, 150)
    T = Orient(cv, o)
    cols = ["e8503a", "f0a030", "3aa8e0", "58b050", "b050d0", "e8d040"]
    ground(T, 20, 20, 300, 270, kit.paving("8a7c68", 10.0, 44))
    n = 3 + L
    stalls = []
    for i in range(n):
        s0 = 36 + (i % 3) * 86
        f0 = 60 + (i // 3) * 100
        stalls.append((s0, f0))
    for i, (s0, f0) in enumerate(stalls):
        c = cols[i % len(cols)]
        T.box(s0, f0, s0 + 64, f0 + 40, 0, 16, all=flat("6a4a30", 3), top=flat("8a6a48", 4))
        for px in (s0 + 2, s0 + 62):
            post(T, px, f0 + 2, 0, 34, "4a3a2a", 2.2)
            post(T, px, f0 + 38, 0, 34, "4a3a2a", 2.2)
        T.box(s0 - 4, f0 - 4, s0 + 68, f0 + 44, 34, 38, all=flat(c, 3), top=flat(c, 4))
        T.box(s0 + 4, f0 - 4.5, s0 + 60, f0 - 4, 29, 34, all=_glow(GOLD))
        for k in range(4):
            T.box(s0 + 10 + k * 14, f0 + 4, s0 + 18 + k * 14, f0 + 10, 16, 20, all=_paint(cols[(i + k) % 6]), top=flat(cols[(i + k) % 6]))
    # lanterns on a wire across the market
    for k in range(9):
        s = 28 + k * 34
        post(T, s, 52, 34, 48, "2a2a2a", 0.8)
        T.box(s - 5, 47, s + 5, 57, 40, 52, all=_glow(cols[k % 6]), top=flat(cols[k % 6]))
    post(T, 24, 22, 0, 70, "3a3a44", 3.0)
    post(T, 296, 22, 0, 70, "3a3a44", 3.0)
    T.box(20, 20, 300, 24, 62, 70, all=_paint("14101c"), top=flat("14101c"))
    sign_board(T, 160, 20, 76, "MARKET", 13, "14101c", GOLD)
    for s in (60, 160, 260):
        lamp(T, s, 12, "lantern", 55)
    if L >= 2:
        tree(T, 300, 240, "lime", 0.8, 4401)
    if L >= 3:
        bench(T, 160, 250, "s")
    return cv


def karaoke(L, o):
    cv = Canvas(2, 160)
    T = Orient(cv, o)
    fh = 34
    H = [2, 3, 3][L - 1] * fh + 4
    win = Win(w=22, h=18, sill=9, sp=40, margin=14, fh=fh, frame="3a1c3a", style="grid", group="work")
    fr = facade("concrete", "7a2e6a", win=win, doors=[(124, 44, 30, "double_glass")], seed=4501, plinth=("3a1448", 4),
                bands=[(H - 6, H, GOLD)])
    sd = facade("concrete", "7a2e6a", win=win, seed=4502, plinth=("3a1448", 4), bands=[(H - 6, H, GOLD)])
    box(T, 30, 80, 290, 210, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("5a2858", GOLD, 4))
    # stage-like entrance with a glowing arch
    T.box(100, 60, 220, 80, 0, 38, front=flat("3a1448", 3), left=flat("3a1448", 3), right=flat("3a1448", 3),
          top=flat(GOLD, 4))
    T.box(102, 59.5, 218, 60, 33, 38, all=_glow(GOLD))
    door(T, 130, 44, 60, 30)
    entry(T, 152)
    # a giant microphone on the roof: pole, grid head, glow ring
    post(T, 160, 140, H, H + 34, "c8c8d4", 4.0)
    T.box(148, 128, 172, 152, H + 30, H + 54, all=_paint("2a2a38"), top=flat("3a3a48", 4))
    T.box(146, 126, 174, 154, H + 44, H + 47, all=_glow(PINK), top=flat(PINK))
    # music-note glowing panels on the front wall
    for k, s in enumerate((56, 250)):
        T.box(s - 14, 79.2, s + 14, 80, H - 40, H - 12, all=_glow(CYAN if k else PINK))
    sign_board(T, 160, 80, H - 2, "KARAOKE", 11, "3a1448", GOLD)
    canopy(T, 110, 210, 60, 14, 38, "7a2e6a", GOLD, posts=True)
    roof_units(T, 60, 90, 130, 200, H, 4501, 3, stair=False)
    ground(T, 20, 0, 300, 60, kit.paving("8a6a88", 10.0, 45))
    for s in (50, 270):
        bench(T, s, 30, "s")
    lamp(T, 90, 20, "modern", 60)
    lamp(T, 230, 20, "modern", 60, "light2")
    pole_sign(T, 300, 20, 74, "SING", 11, "3a1448", PINK)
    if L >= 2:
        tree(T, 290, 240, "lime", 0.8, 4503)
        car_static(T, 70, 240, "s", GOLD)
    return cv


BUILDERS = {"nightclub": nightclub, "night_market": night_market, "karaoke": karaoke}
