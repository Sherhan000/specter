"""IT school "it-run" (ROADMAP 27): a modern two-wing campus - graphite and violet panels, a glass atrium with a glowing
code-bracket logo, a rooftop dish and server vents, a terrace with benches and bike racks. builder(L, o) -> Canvas, 2x2 plot."""
import numpy as np

from raster import C, Canvas, flat, nores, glow_res
from arch import Orient, facade, Win, flat_top
import kit
from bkit import (door, entry, ground, tree, bush, lamp, bench, box, slab, post, canopy, sign_board, pole_sign,
                  parking_lot, car_static, roof_units)

VIOLET = "6a3fd0"
MINT = "46e0c0"


def _paint(col):
    return lambda u, v, LL, HH: (C(col) * np.ones(u.shape + (3,)), nores(u.shape), None)


def _glow(col):
    return lambda u, v, LL, HH: glow_res(col, u.shape)


def _brackets(T, s, f, z, r):
    """A glowing '</>' emblem on a dark square panel, 2r wide."""
    def fn(u, v, LL, HH):
        x = (u - r) / r
        y = (v - r) / r
        out = np.zeros(u.shape + (3,)) + C("1c1a2e")
        c = C(MINT)
        lb = (np.abs(np.abs(y) - (0.62 - (x + 0.55)) ) < 0.13) & (x < -0.05) & (x > -0.75)
        lb = (np.abs(np.abs(y) - (x + 0.78) * 0.8) < 0.13) & (x > -0.78) & (x < -0.2)
        rb = (np.abs(np.abs(y) - (0.78 - x) * 0.8) < 0.13) & (x < 0.78) & (x > 0.2)
        sl = (np.abs(x - y * -0.35) < 0.1) & (np.abs(y) < 0.6)
        out[lb | rb] = c
        out[sl] = C("ffffff")
        return out, nores(u.shape), None
    T.box(s - r - 2, f - 1.8, s + r + 2, f, z - 2, z + 2 * r + 2, all=_paint(VIOLET), top=flat(VIOLET))
    T.panel(s - r, s + r, f - 1.9, z, z + 2 * r, fn, "s")


def it_run(L, o):
    cv = Canvas(2, 170)
    T = Orient(cv, o)
    fh = 34
    floors = [2, 3, 3][L - 1]
    H = floors * fh + 4
    win = Win(w=26, h=20, sill=8, sp=34, margin=10, fh=fh, frame="2a2a3a", style="grid", group="work")
    fr = facade("concrete", "3a3c4c", win=win, doors=[(112, 40, 30, "double_glass")], seed=2701, plinth=("22222c", 4),
                bands=[(H - 6, H, VIOLET)])
    sd = facade("concrete", "3a3c4c", win=win, seed=2702, plinth=("22222c", 4), bands=[(H - 6, H, VIOLET)])
    # main wing at the back, a lower classroom wing on the left
    box(T, 20, 70, 300, 150, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("6a6e7c", VIOLET, 4))
    box(T, 20, 150, 110, 250, 0, H - fh, all=sd, top=flat_top("6a6e7c", VIOLET, 4))
    roof_units(T, 130, 80, 290, 140, H, 2701, 5, stair=False)
    # glass atrium over the entrance
    T.box(96, 56, 204, 70, 0, H + 6, front=flat("bfe4ff", 3), left=flat("98aac8", 3), right=flat("98aac8", 3), back=flat("98aac8"),
          top=flat(VIOLET, 4))
    T.box(100, 55.5, 200, 56, 3, 30, all=_glow("dff0ff"))
    sign_board(T, 150, 56, H - 4, "IT-RUN", 11, "1c1a2e", MINT)
    _brackets(T, 60, 70, H - 22, 11)
    _brackets(T, 250, 70, H - 22, 11)
    # rooftop satellite dish and mast
    post(T, 270, 100, H, H + 26, "8a8a98", 2.0)
    T.box(262, 92, 280, 108, H + 24, H + 28, all=_paint("e8e8f0"), top=flat("e8e8f0"))
    door(T, 128, 40, 56, 30)
    entry(T, 150)
    canopy(T, 120, 180, 56, 12, 36, VIOLET, VIOLET, posts=True)
    ground(T, 20, 0, 300, 56, kit.paving("b4b6c2", 10.0, 27))
    parking_lot(T, 120, 160, 310, 306, "s", 26) if False else None
    for ss in (40, 270):
        bench(T, ss, 30, "s")
    lamp(T, 100, 20, "modern", 60)
    lamp(T, 220, 20, "modern", 60, "light2")
    pole_sign(T, 300, 20, 74, "IT-RUN", 11, "1c1a2e", MINT)
    tree(T, 290, 190, "lime", 0.8, 2703)
    tree(T, 60, 280, "lime", 0.8, 2704)
    if L >= 2:
        bush(T, 160, 24, 1.0, 2705)
        car_static(T, 240, 200, "s", VIOLET)
    if L >= 3:
        T.box(40, 160, 100, 240, H - fh, H - fh + 14, all=_paint("46e0c0"), top=flat("2a2a3a", 4))
        bench(T, 80, 36, "s")
    return cv


BUILDERS = {"it_run": it_run}
