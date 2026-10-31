"""Crime and order (ROADMAP 25): a private guard agency that protects banks and a city prison.
Own names and looks only. builder(L, o) -> Canvas."""
import numpy as np

from raster import C, Canvas, flat, nores, glow_res
from arch import Orient, facade, Win, flat_top
import kit
from bkit import door, entry, ground, tree, bush, box, post, sign_board, car_static, lamp, pole_sign


def _paint(col):
    return lambda u, v, LL, HH: (C(col) * np.ones(u.shape + (3,)), nores(u.shape), None)


def _glow(col):
    return lambda u, v, LL, HH: glow_res(col, u.shape)


def _shield(T, s, f, z, col="e8b830", rim="2a2c34"):
    """A shield emblem on a front wall: a rim, the shield and a stripe down the middle."""
    T.panel(s - 9, s + 9, f - 0.6, z, z + 18, _paint(rim), "s")
    T.panel(s - 7, s + 7, f - 1.0, z + 4, z + 16, _paint(col), "s")
    T.panel(s - 5, s + 5, f - 1.0, z + 2, z + 4, _paint(col), "s")
    T.panel(s - 1.2, s + 1.2, f - 1.3, z + 3, z + 15, _paint(rim), "s")


def _van(T, s, f, along="s"):
    """An armoured cash van: a dark grey box body with a gold stripe and a blue beacon."""
    car_static(T, s, f, along, "4a4c54")
    if along == "s":
        T.box(s - 10, f - 5, s + 12, f + 5, 12, 17, all=_paint("3a3c44"), top=flat("4a4c54"))
        T.box(s - 10, f - 5.3, s + 12, f - 4.6, 7, 9, all=_paint("e8b830"))
        T.box(s - 2, f - 2, s + 2, f + 2, 17, 19, all=_glow("3a6ae8"), top=flat("3a6ae8"))
    else:
        T.box(s - 5, f - 10, s + 5, f + 12, 12, 17, all=_paint("3a3c44"), top=flat("4a4c54"))
        T.box(s - 2, f - 2, s + 2, f + 2, 17, 19, all=_glow("3a6ae8"), top=flat("3a6ae8"))


# ====================================================================== guard agency
def security_office(L, o):
    """Guard agency "Shchit" (Shield): a graphite two-storey office with gold trim and a big shield on the front,
    a camera on the corner, an armoured cash van at the curb (two at level 3), a barrier and a guard booth."""
    cv = Canvas(1, 130)
    T = Orient(cv, o)
    seed = 2501
    win = Win(w=16, h=14, sill=10, sp=30, margin=16, fh=28, frame="e8b830", style="vertical", group="work")
    fr = facade("concrete", "3e4048", win=win, doors=[(18, 16, 24, "glass")], seed=seed, plinth=("2a2c34", 5),
                bands=[(27, 29, "e8b830")])
    sd = facade("concrete", "3e4048", win=win, seed=seed + 1, plinth=("2a2c34", 5), bands=[(27, 29, "e8b830")])
    s0, s1, f0, f1 = 24, 136, 54, 128
    H = 56 if L < 3 else 70
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("6a6c72", "2a2c34", 3))
    sign_board(T, (s0 + s1) / 2 + 14, f0, H - 12, "SHCHIT", 7, "2a2c34", "e8b830")
    _shield(T, 104, f0, 30)
    door(T, s0 + 18, 16, f0, 24)
    entry(T, s0 + 26)
    # camera on the corner, its red light glows
    T.box(s1 - 6, f0 - 6, s1 + 2, f0 + 2, H - 8, H - 4, all=_paint("d8dce0"), top=flat("d8dce0"))
    T.box(s1 - 2, f0 - 7, s1, f0 - 5, H - 7, H - 5, all=_glow("e8342a"))
    # rooftop aerial with a beacon
    post(T, 50, 100, H, H + 18, "8a8c90", 1.2)
    T.box(48, 98, 52, 102, H + 18, H + 21, all=_glow("e8342a"), top=flat("e8342a"))
    ground(T, 2, 2, 158, f0, kit.paving("8a8c92", 8.0, seed, 0.5))
    _van(T, 112, 26, "s")
    if L >= 2:
        # guard booth with a barrier
        box(T, 8, 34, 22, 48, 0, 22, all=_paint("e8e8ec"), top=flat_top("2a2c34", "e8e8ec", 2))
        T.box(8, 33.5, 22, 34, 12, 18, all=_glow("cfe8ff"))
        T.panel(22, 62, 30, 10, 12.5, lambda u, v, LL, HH: (np.where((np.mod(u, 8) < 4)[..., None], C("e8b830"), C("2a2c34"))
                                                          * np.ones(u.shape + (1,)), nores(u.shape), None), "s")
    if L >= 3:
        _van(T, 70, 26, "s")
        lamp(T, 150, 12, "modern", 46)
    return cv


# ====================================================================== prison
def prison(L, o):
    """City prison: a grey cell block with barred windows behind a high wall with a dark wire top,
    watch towers with glowing searchlights on the corners, a steel gate with a guard post and an exercise yard."""
    cv = Canvas(2, 170)
    T = Orient(cv, o)
    seed = 2511
    # yard surface inside the walls
    ground(T, 10, 10, 310, 310, kit.paving("a8a49c", 14.0, seed, 0.4))
    # cell block
    win = Win(w=10, h=14, sill=10, sp=20, margin=14, fh=26, frame="4a4c52", style="vertical", group="work")
    blk = facade("concrete", "c8c4bc", win=win, seed=seed, plinth=("6a6660", 6), bands=[(25, 27, "9a968e")])
    s0, s1, f0, f1 = 70, 250, 150, 270
    H = 64 if L == 1 else 84 if L == 2 else 104
    box(T, s0, f0, s1, f1, 0, H, front=blk, back=blk, left=blk, right=blk, top=flat_top("8a8780", "6a6660", 4))
    sign_board(T, (s0 + s1) / 2, f0, H - 14, "PRISON", 8, "3a3c42", "f0ece4")
    door(T, (s0 + s1) / 2 - 14, 28, f0, 28)
    # exercise yard: a court with lines and a hoop
    T.box(100, 60, 220, 130, 0, 0.6, all=_paint("b86a4a"), top=lambda u, v, LL, HH: (
        np.where(((np.mod(u, 60) < 1.5) | (np.mod(v, 70) < 1.5))[..., None], C("f0ece4"), C("b86a4a")) * np.ones(u.shape + (1,)),
        nores(u.shape), None))
    post(T, 160, 64, 0, 26, "4a4c52", 1.4)
    T.box(154, 62, 166, 66, 24, 32, all=_paint("f0ece4"), top=flat("f0ece4"))
    # high wall round the plot with a dark wire top, a gap for the gate at the front
    wall = facade("concrete", "b0aca4", seed=seed + 3, plinth=("6a6660", 4))
    WH = 34
    for a0, a1 in ((4, 130), (190, 316)):
        T.box(a0, 4, a1, 10, 0, WH, front=wall, back=wall, left=wall, right=wall, top=flat("8a8780"))
    T.box(4, 310, 316, 316, 0, WH, front=wall, back=wall, left=wall, right=wall, top=flat("8a8780"))
    T.box(4, 10, 10, 310, 0, WH, front=wall, back=wall, left=wall, right=wall, top=flat("8a8780"))
    T.box(310, 10, 316, 310, 0, WH, front=wall, back=wall, left=wall, right=wall, top=flat("8a8780"))
    for s in range(8, 316, 14):
        post(T, s, 7, WH, WH + 6, "3a3c42", 0.8)
    T.box(4, 6, 130, 8, WH + 4, WH + 5, all=_paint("3a3c42"))
    T.box(190, 6, 316, 8, WH + 4, WH + 5, all=_paint("3a3c42"))
    # steel gate with stripes and a guard post
    T.panel(130, 190, 7, 0, WH - 4, lambda u, v, LL, HH: (
        np.where((np.mod(u, 10) < 1.4)[..., None], C("2a2c32"), C("5a5e66")) * np.ones(u.shape + (1,)), nores(u.shape), None), "s")
    T.box(130, 4, 190, 10, WH - 4, WH, all=_paint("e8b830"), top=flat("e8b830"))
    box(T, 196, 12, 222, 36, 0, 24, all=_paint("e8e8ec"), top=flat_top("3a3c42", "e8e8ec", 2))
    T.box(196, 11.5, 222, 12, 13, 20, all=_glow("cfe8ff"))
    # watch towers on the corners with searchlights
    for s, f in ((14, 14), (306, 14), (14, 306), (306, 306))[:2 if L == 1 else 4]:
        T.box(s - 8, f - 8, s + 8, f + 8, 0, 62, all=_paint("9a968e"), top=flat("8a8780"))
        T.box(s - 12, f - 12, s + 12, f + 12, 62, 64, all=_paint("5a5e66"), top=flat("5a5e66"))
        for ps, pf in ((-11, -11), (11, -11), (-11, 11), (11, 11)):
            post(T, s + ps, f + pf, 64, 76, "5a5e66", 1.0)
        T.box(s - 13, f - 13, s + 13, f + 13, 76, 79, all=_paint("3a3c42"), top=flat("4a4c52"))
        T.box(s - 3, f - 13, s + 3, f - 11, 66, 71, all=_glow("fff2c0"))
    if L >= 2:
        pole_sign(T, 236, 2, 40, "P", 10, "3a3c42", "f0ece4")
        car_static(T, 270, 30, "s", "f4f6f8")
        T.box(266, 26, 274, 34, 14, 16, all=_glow("3a6ae8"), top=flat("3a6ae8"))
    if L >= 3:
        lamp(T, 120, 2, "modern", 50)
        bush(T, 300, 2, 0.8, seed)
    return cv


BUILDERS = {"security_office": security_office, "prison": prison}
