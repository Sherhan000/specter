"""Shops, offices and hotels at real scale."""
import numpy as np

from raster import C, U, Canvas, flat, solid_res, glow_res, nores
from arch import Orient, facade, Win, roof_mat, flat_top, text_mask
import kit
from b_homes import spire
from bkit import (door, entry, ground, tree, bush, hedge, fence, flowerbed, mailbox, lamp, bench, bins, box, slab,
                  post, canopy, steps, balconies, roof_units, parking_lot, glass_rail, awning, sign_board, pole_sign, blade_sign)

S = U


def _shop_house(L, o, seed, sign, wallc, mat, aw, sign_bg, sign_fg, roofc=None, upper_win=None, floors=None,
                gable=None, frame="f2efe8"):
    """A town-centre building: shop on the ground floor, flats above."""
    floors = floors or [1, 2, 3][L - 1]
    fh = 34
    gf = 40
    H = gf + (floors - 1) * fh + 4
    cv = Canvas(1, H + 90)
    T = Orient(cv, o)
    s0, s1, f0, f1 = 14, 146, 40, 150
    win = upper_win or Win(w=12, h=17, sill=10, sp=24, margin=12, fh=fh, frame=frame, boxes=L >= 2, group="flats")
    sw = text_mask(sign, 9).shape[1]
    front = facade(mat, wallc, shop=(8, 82, 22), doors=[(92, 12, 24, "glass")], seed=seed, plinth=("6a6460", 4),
                   signs=[(48, 28, sign, 7, sign_bg, sign_fg, True)],
                   bands=[(gf - 2, gf, "e8e2d6")], cornice=("e8e2d6", 4) if not gable else None)
    upper_front = facade(mat, wallc, win=win, seed=seed + 1, plinth=None, cornice=("e8e2d6", 4) if not gable else None)
    side = facade(mat, wallc, win=Win(w=12, h=17, sill=10, sp=24, margin=14, fh=fh, frame=frame, group="flats"), seed=seed + 2,
                  plinth=("6a6460", 4))
    back = facade(mat, wallc, win=Win(w=12, h=17, sill=10, sp=24, margin=12, fh=fh, frame=frame, group="flats"),
                  doors=[(20, 10, 22, "panel", "6a6a70")], seed=seed + 3, plinth=("6a6460", 4))
    walls = dict(front=front, back=back, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, gf, **walls, top=flat_top("7a7672", "c8c2b8"))
    if floors > 1:
        uw = dict(front=upper_front, back=back, left=side, right=side)
        box(T, s0, f0, s1, f1, gf, H, **uw, top=flat_top("807c78", "d8d2c6", 3))
        if gable:
            T.gable(s0, f0, s1, f1, H, 30, roof_mat(gable, "tiles"), uw, ridge="s", o=4)
        else:
            roof_units(T, s0, f0, s1, f1, H, seed, 2, stair=False)
    elif gable:
        T.gable(s0, f0, s1, f1, gf, 30, roof_mat(gable, "tiles"), walls, ridge="s", o=4)
    if aw:
        awning(T, s0 + 6, s0 + 88, f0, 25, 14, 6, aw[0], aw[1])
    if floors > 1:
        blade_sign(T, s1 - 6, f0, gf + 8, sign, sign_bg, sign_fg)
    door(T, s0 + 92, 12, f0, 24)
    entry(T, s0 + 98)
    ground(T, 0, 0, 160, f0, kit.paving("c8c0b2", 8.0, seed))
    return cv, T, H


def bakery(L, o):
    cv, T, H = _shop_house(L, o, 201, "BAKERY", "f0e2c4", "plaster", ("8a5a34", "f4ead8"), "6a3e24", "f8e8c0", gable="a8473a")
    bench(T, 150, 22, "f")
    x, y = T.pt(124, 20)
    kit.umbrella_table(cv, x, y, "8a5a34") if L >= 2 else None
    bins(T, 150, 160)
    return cv


def cafe(L, o):
    cv, T, H = _shop_house(L, o, 211, "CAFE", "e8f0e4" if L < 3 else "d8e8e0", "plaster", ("2e7a4a", "f6f2ea"), "2e5a3e", "f6f2ea")
    for k, (ss, ff) in enumerate(((30, 18), (64, 18), (130, 18))[: 2 + (L >= 2)]):
        x, y = T.pt(ss, ff)
        kit.umbrella_table(cv, x, y, ["2e7a4a", "f6f2ea", "2e7a4a"][k])
    fence(T, 6, 112, 3, "s", "2e3a32", "rail", 8)
    tree(T, 150, 150, "lime", 0.8, 3)
    return cv


def flowershop(L, o):
    cv, T, H = _shop_house(L, o, 221, "FLOWERS", "f6e8ee", "plaster", ("d86a8a", "f8f0f2"), "b44a6a", "fff4f8", gable="5a5e66")
    for k in range(4):
        x0, y0, x1, y1 = T.rect(14 + k * 22, 10, 32 + k * 22, 30)
        kit.flowerbed(cv, x0, y0, x1, y1, k, "8a6a48", 6)
    bush(T, 140, 20, 0.8, 4, "f4d040")
    return cv


def pizzeria(L, o):
    cv, T, H = _shop_house(L, o, 231, "PIZZA", "c8705a", "brick", ("c8342a", "f6f2ea"), "1e6a3a", "f6f2ea")
    x, y = T.pt(40, 18)
    kit.umbrella_table(cv, x, y, "c8342a")
    if L >= 2:
        x, y = T.pt(100, 18)
        kit.umbrella_table(cv, x, y, "1e6a3a")
    lamp(T, 150, 12, "classic", 42)
    return cv


def boutique(L, o):
    cv, T, H = _shop_house(L, o, 241, "BOUTIQUE", "ece6dc", "stone", None, "1e1e22", "e8c860",
                           upper_win=Win(w=14, h=20, sill=8, sp=26, margin=14, fh=34, frame="f8f6f0", arch=True, group="flats"),
                           floors=[2, 3, 4][L - 1])
    canopy(T, 20, 112, 40, 10, 32, "1e1e22", "1e1e22", posts=False)
    for ss in (12, 118):
        x, y = T.pt(ss, 30)
        kit.bush(cv, x, y, 0.7, ss, None)
        T.box(ss - 6, 24, ss + 6, 36, 0, 8, all=flat("2a2a30"), top=flat("4a3a2a"))
    return cv


def pharmacy(L, o):
    cv, T, H = _shop_house(L, o, 251, "PHARMACY", "f4f6f4", "plaster", None, "1e8a4a", "ffffff", floors=[1, 2, 3][L - 1])
    # glowing green cross on the corner
    x, y = T.pt(140, 38)
    cross = lambda u, v, LL, HH: glow_res("2ad46a", u.shape)
    z = 44 if L > 1 else 30
    T.box(134, 34, 146, 36, z, z + 12, all=cross, top=flat("1e8a4a"))
    T.box(136, 34, 144, 36, z - 2, z + 14, all=cross, top=flat("1e8a4a"))
    bench(T, 150, 24, "f")
    return cv


def gas_station(L, o):
    cv = Canvas(1, 120)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.asphalt_lot("5c5e64", 4))
    # canopy over two pump islands
    cz = 46
    T.box(10, 20, 150, 90, cz, cz + 8, front=facade("plaster", "e8342a", plinth=None, signs=[(70, 1.5, "FUEL", 5, None, "ffffff", True)]),
          back=flat("e8342a"), left=flat("e8342a"), right=flat("e8342a"), top=flat_top("d8dcdf", "e8342a", 3))
    for ss in (40, 120):
        for ff in (30, 80):
            post(T, ss, ff, 0, cz, "e8e8ea", 3)
        slab(T, ss - 10, 40, ss + 10, 70, 0, 2.5, "c8c8c8")
        T.box(ss - 4, 48, ss + 4, 54, 2.5, 20, front=facade("plaster", "f0f0f2", plinth=None, decals=[(1, 7, 10, 15, "emit:9ad8f0")]),
              back=flat("f0f0f2"), left=flat("d8342a"), right=flat("d8342a"), top=flat("e8342a"))
    # glow under the canopy
    x0, y0, x1, y1 = T.rect(14, 24, 146, 86)
    T.cv.mark("light", *T.pt(80, 55), cz - 2)
    shop = facade("plaster", "f4f2ee", shop=(6, 70, 24), doors=[(76, 12, 24, "glass")], seed=261, plinth=("6a6460", 3),
                  signs=[(50, 28, "SHOP", 6, None, "e8342a", True)])
    sside = facade("plaster", "f4f2ee", seed=262)
    box(T, 20, 108, 150, 156, 0, 36, front=shop, back=sside, left=sside, right=sside, top=flat_top("7a7672", "e8342a", 2))
    door(T, 96, 12, 108, 24)
    entry(T, 80)
    pole_sign(T, 152, 8, 70, "GAS", 10, "e8342a", "ffffff")
    if L >= 2:
        x, y = T.pt(10, 130)
        kit.wheelie_bins(cv, x, y)
    return cv


# ====================================================================== big shops
def supermarket(L, o):
    cv = Canvas(2, 150)
    T = Orient(cv, o)
    H = [44, 50, 56][L - 1]
    s0, s1, f0, f1 = 20, 300, 150, 300
    front = facade("concrete", "e8e6e0", shop=(30, 250, 30), doors=[(118, 40, 30, "double_glass")], plinth=("6a6a70", 3), seed=271,
                   bands=[(34, H, "2a7a4a")], signs=[(140, 36, "SUPERMARKET", 9, None, "ffffff", True)])
    side = facade("metal", "dcdad4", seed=272, plinth=("6a6a70", 3))
    walls = dict(front=front, back=side, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, H, **walls, top=flat_top("8a8884", "2a7a4a", 4))
    roof_units(T, s0, f0, s1, f1, H, 271, 6, stair=False)
    canopy(T, 120, 200, f0, 16, 34, "2a7a4a", "2a7a4a", posts=True)
    door(T, 138, 40, f0, 30)
    entry(T, 160)
    parking_lot(T, 10, 0, 310, 132, "s", 26)
    ground(T, 10, 132, 310, f0, kit.paving("c8c4bc", 10.0, 3))
    for ss in (20, 300):
        tree(T, ss, 70, "lime", 0.8, 7 + ss)
    lamp(T, 100, 66, "modern", 60)
    lamp(T, 220, 66, "modern", 60, "light2")
    # trolleys shelter
    slab(T, 240, 136, 290, 146, 18, 20, "2a7a4a")
    if L >= 2:
        bench(T, 60, 140, "s")
    return cv


def restaurant(L, o):
    cv = Canvas(2, 170)
    T = Orient(cv, o)
    fh = 36
    floors = [1, 2, 2][L - 1]
    H = floors * fh + 6
    s0, s1, f0, f1 = 40, 280, 90, 260
    win = Win(w=18, h=24, sill=6, sp=32, margin=14, fh=fh, frame="2a2a30", arch=True, group="work")
    front = facade("brick", "8a3e30", win=win, doors=[(108, 24, 30, "double", "3a2418")], seed=281, plinth=("3a3a40", 6),
                   cornice=("e8e2d6", 5), signs=[(120, 34, "RESTAURANT", 7, None, "f8e0a0", True)], lit=0.9)
    side = facade("brick", "8a3e30", win=win, seed=282, plinth=("3a3a40", 6), cornice=("e8e2d6", 5), lit=0.9)
    walls = dict(front=front, back=side, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, H, **walls)
    T.hip(s0, f0, s1, f1, H, 30, roof_mat("4a4e56", "slate"), o=5)
    canopy(T, 140, 180, f0, 18, 34, "1e1e22", "1e1e22", posts=True)
    door(T, 148, 24, f0, 30)
    entry(T, 160)
    # terrace with tables under string lights
    ground(T, 20, 0, 300, f0, kit.bricks_pave("a8785a"))
    for k, ss in enumerate((60, 100, 220, 260)):
        x, y = T.pt(ss, 40)
        kit.umbrella_table(cv, x, y, "f4f0e8" if k % 2 else "1e1e22")
    fence(T, 20, 130, 8, "s", "1e1e22", "rail", 9)
    fence(T, 190, 300, 8, "s", "1e1e22", "rail", 9)
    for k, ss in enumerate((30, 290)):
        tree(T, ss, 120, "lime", 0.9, k + 10)
    if L >= 3:
        hedge(T, 20, 270, 300, 280, 12, 3)
    return cv


def cinema(L, o):
    cv = Canvas(2, 200)
    T = Orient(cv, o)
    H = [70, 80, 90][L - 1]
    s0, s1, f0, f1 = 20, 300, 80, 300
    front = facade("plaster", "3a2a4a", doors=[(100, 80, 28, "double_glass")], seed=291, plinth=("1e1e22", 4),
                   decals=[(30, 70, 8, 60, "e8d0a0"), (34, 66, 12, 56, "c8344a"), (210, 250, 8, 60, "e8d0a0"), (214, 246, 12, 56, "3a6ac8")],
                   signs=[(140, H - 22, "CINEMA", 14, None, "ffd84a", True)])
    side = facade("concrete", "4a3a5a", seed=292, plinth=("1e1e22", 4))
    walls = dict(front=front, back=side, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, H, **walls, top=flat_top("6a6866", "3a2a4a", 4))
    roof_units(T, s0, f0, s1, f1, H, 291, 4, stair=False)
    # marquee with bulbs
    mq = facade("plaster", "1e1e22", plinth=None, signs=[(55, 4, "PREMIERE", 7, None, "ffffff", True)],
                decals=[(k * 6, k * 6 + 2, 16, 18, "emit:fff0a0") for k in range(20)] + [(k * 6 + 3, k * 6 + 5, 0, 2, "emit:fff0a0") for k in range(20)])
    T.box(100, f0 - 24, 210, f0, 34, 52, front=mq, back=mq, left=flat("1e1e22"), right=flat("1e1e22"), top=flat("2a2a30"))
    door(T, 120, 80, f0, 28)
    entry(T, 160)
    ground(T, 10, 0, 310, f0, kit.paving("4a4a50", 10.0, 2))
    for ss in (40, 280):
        lamp(T, ss, 30, "classic", 45, "light%d" % ss)
    if L >= 2:
        T.mark("smoke", 0, 0, 0) if False else None
    return cv


def mall(L, o):
    cv = Canvas(3, 200)
    T = Orient(cv, o)
    floors = [2, 3, 3][L - 1]
    fh = 40
    H = floors * fh + 6
    s0, s1, f0, f1 = 30, 450, 190, 450
    front = facade("concrete", "e4e2dc", shop=(20, 400, 32), doors=[(180, 60, 32, "double_glass")], seed=301, plinth=("5a5a60", 4),
                   win=Win(w=36, h=26, sill=8, sp=44, margin=10, fh=fh, frame="3a3a40", style="vertical", group="work"), lit=0.8,
                   signs=[(210, H - 18, "MALL", 14, None, "ffffff", True)], bands=[(fh - 2, fh + 2, "c8c4bc")])
    side = facade("concrete", "dcdad4", win=Win(w=36, h=26, sill=8, sp=44, margin=10, fh=fh, frame="3a3a40", style="vertical", group="work"),
                  seed=302, plinth=("5a5a60", 4), lit=0.6)
    walls = dict(front=front, back=side, left=side, right=side)
    box(T, s0, f0, s1, f1, 0, H, **walls, top=flat_top("8a8884", "e4e2dc", 5))
    # glass atrium over the entrance
    atr = facade("concrete", "c8ccd0", win=Win(w=20, h=36, sill=2, sp=22, margin=4, fh=40, frame="9aa4ae", style="vertical", group="work",
                                             tint="7ab0d0"), plinth=None, seed=303, lit=0.9)
    box(T, 170, f0 - 30, 290, f0 + 60, 0, H + 20, all=atr, top=flat_top("9ab8d0", "c8ccd0", 3))
    roof_units(T, s0, f0 + 70, s1, f1, H, 301, 8, stair=True)
    door(T, 210, 60, f0 - 30, 32)
    entry(T, 240)
    parking_lot(T, 10, 0, 470, 150, "s", 26)
    ground(T, 10, 150, 470, f0, kit.paving("c8c4bc", 12.0, 3))
    for k, ss in enumerate((40, 130, 340, 430)):
        tree(T, ss, 75, "lime", 0.8, 20 + k)
    for k, ss in enumerate((90, 380)):
        lamp(T, ss, 75, "modern", 70, "light%d" % k)
    pole_sign(T, 20, 170, 120, "MALL", 14, "2a5aa8", "ffffff")
    return cv


def hotel(L, o):
    floors = [6, 9, 12][L - 1]
    fh = 32
    pod = 44
    H = pod + floors * fh
    cv = Canvas(2, H + 110)
    T = Orient(cv, o)
    podf = facade("stone", "d8ccb4", shop=(20, 110, 28), doors=[(130, 40, 32, "double_glass")], seed=311, plinth=None,
                  bands=[(pod - 4, pod, "b8a888")])
    pods = facade("stone", "d8ccb4", seed=312, bands=[(pod - 4, pod, "b8a888")])
    box(T, 20, 60, 300, 280, 0, pod, front=podf, back=pods, left=pods, right=pods, top=flat_top("8a8884", "d8ccb4", 3))
    win = Win(w=16, h=18, sill=8, sp=26, margin=12, fh=fh, frame="e8e4dc", group="flats")
    tw = facade("plaster", ["e8dcc4", "dcd0b8", "f0ece4"][L - 1], win=win, seed=313, plinth=None, cornice=("b8a888", 6),
                bands=[(fh * k - 1, fh * k + 1, "d8ccb4") for k in range(1, floors)])
    s0, s1, f0, f1 = 50, 270, 90, 250
    box(T, s0, f0, s1, f1, pod, H, all=tw, top=flat_top("807c78", "b8a888", 4))
    balconies(T, [s0 + 20, s0 + 160], f0, range(0, floors), fh, 40, 10, "e8e4dc", z_start=pod + 2)
    # lit name on the roof
    sign_board(T, (s0 + s1) / 2, f0 + 20, H, "HOTEL", 18, "1e1e22", "ffd84a")
    canopy(T, 120, 200, 60, 30, 36, "1e1e22", "c8a050", posts=True)
    for k, ss in enumerate((110, 210)):
        post(T, ss, 24, 0, 60, "d8d8d8", 1.2)
        T.box(ss, 23, ss + 12, 24, 44, 58, all=flat(["c8342a", "2a5aa8"][k]))
    door(T, 150, 40, 60, 32)
    entry(T, 160)
    ground(T, 10, 0, 310, 60, kit.paving("d4ccbc", 10.0, 5))
    for k, ss in enumerate((30, 290)):
        tree(T, ss, 30, "spruce", 0.6, 30 + k)
    if L >= 3:
        roof_units(T, s0, f0 + 60, s1, f1, H, 311, 3, stair=False)
    return cv


def office(L, o):
    floors = [6, 9, 13][L - 1]
    fh = 34
    H = floors * fh + 4
    cv = Canvas(2, H + 100)
    T = Orient(cv, o)
    tint = ["5a8aa8", "4a7a9a", "3a6a8a"][L - 1]
    cw = facade("concrete", "c8d0d8", win=Win(w=30, h=28, sill=3, sp=33, margin=4, fh=fh, frame="8a96a2", style="vertical", tint=tint,
                                              group="work", top_skip=2), plinth=None, seed=321, lit=0.45,
                bands=[(fh * k - 2, fh * k + 2, "dce2e8") for k in range(floors + 1)])
    entr = facade("concrete", "c8d0d8", win=Win(w=30, h=28, sill=3, sp=33, margin=4, fh=fh, frame="8a96a2", style="vertical", tint=tint,
                                                group="work", top_skip=2), doors=[(90, 40, 30, "double_glass")], plinth=None, seed=322,
                  lit=0.45, bands=[(fh * k - 2, fh * k + 2, "dce2e8") for k in range(floors + 1)])
    s0, s1, f0, f1 = 40, 280, 70, 270
    box(T, s0, f0, s1, f1, 0, H, front=entr, back=cw, left=cw, right=cw, top=flat_top("7a7874", "dce2e8", 4))
    roof_units(T, s0, f0, s1, f1, H, 321, 5, stair=True)
    canopy(T, 120, 180, f0, 20, 34, "2a2e34", "2a2e34", posts=False)
    door(T, 130, 40, f0, 30)
    entry(T, 150)
    ground(T, 10, 0, 310, f0, kit.paving("b8b4ac", 12.0, 6))
    # fountain basin and young trees on the plaza
    for k, ss in enumerate((40, 110, 210, 280)):
        tree(T, ss, 30, "maple", 0.65, 40 + k)
    bench(T, 160, 30, "s")
    if L >= 2:
        sign_board(T, (s0 + s1) / 2, f0 + 2, H - 30, "OFFICE", 12, "2a2e34", "e8eef4", depth=2)
    return cv


# ====================================================================== sky_office: glass office skyscraper
def sky_office(L, o):
    floors = [24, 30, 36][L - 1]
    fh = 32
    pod = 2 * fh + 8
    H = pod + floors * fh
    cv = Canvas(3, H + 240)
    T = Orient(cv, o)
    seed = 351
    tint = ["4a7a9a", "3a6a8a", "2e5a7e"][L - 1]
    # glass lobby podium with a big canopy
    lob = facade("concrete", "c8ccd0", win=Win(w=30, h=44, sill=4, sp=34, margin=6, fh=pod, frame="8a96a2", style="vertical",
                                               tint="7ab0d0", group="work", top_skip=6), plinth=("4a4a50", 6), seed=seed, lit=0.9,
                 doors=[(200, 60, 40, "double_glass")])
    lob2 = facade("concrete", "c8ccd0", win=Win(w=30, h=44, sill=4, sp=34, margin=6, fh=pod, frame="8a96a2", style="vertical",
                                                tint="7ab0d0", group="work", top_skip=6), plinth=("4a4a50", 6), seed=seed + 1, lit=0.7)
    box(T, 20, 90, 460, 420, 0, pod, front=lob, back=lob2, left=lob2, right=lob2, top=flat_top("8a8884", "c8ccd0", 5))
    canopy(T, 170, 300, 90, 40, 46, "2a2e34", "2a2e34", posts=False)
    door(T, 210, 60, 90, 40)
    entry(T, 240)
    # curtain-wall shaft with floor lines
    win = Win(w=28, h=26, sill=3, sp=31, margin=4, fh=fh, frame="8a96a2", style="vertical", tint=tint, group="work", top_skip=2)
    cw = facade("concrete", "c8d0d8", win=win, plinth=None, seed=seed + 2, lit=0.5,
                bands=[(fh * k - 2, fh * k + 2, "dce2e8") for k in range(floors + 3)])
    s0, s1, f0, f1 = 90, 390, 150, 410
    box(T, s0, f0, s1, f1, pod, H, all=cw, top=flat_top("7a7874", "dce2e8", 4))
    # light stone fins on the corners that rise above the roof like a crown
    fin = facade("concrete", "e4e8ec", plinth=None, seed=seed + 3)
    for a in (s0 - 6, s1 - 8):
        for b in (f0 - 6, f1 - 8):
            T.box(a, b, a + 14, b + 14, pod, H + 50, all=fin, top=flat_top("8a8884", "e4e8ec", 3))
    # mechanical crown, louvres and mast
    cr = facade("metal", "b8c0c8", plinth=None, seed=seed + 4, win=Win(w=10, h=26, sill=6, sp=16, margin=6, fh=40, frame="6a727a",
                                                                          group="work"), lit=0.9)
    T.box(s0 + 50, f0 + 50, s1 - 50, f1 - 50, H, H + 56, all=cr, top=flat_top("8a8884", "c8ccd0", 3))
    spire(T, (s0 + s1) / 2, (f0 + f1) / 2, H + 56, 90)
    sign_board(T, (s0 + s1) / 2 - 36, f0 - 2, H - 44, "OFFICE", 14, "2a2e34", "e8eef4", depth=2)
    # plaza
    ground(T, 10, 0, 470, 90, kit.paving("c4c0b8", 12.0, 6))
    for k, ss in enumerate((50, 120, 360, 430)):
        tree(T, ss, 50, "maple", 0.7, 80 + k)
    bench(T, 150, 45, "s")
    bench(T, 320, 45, "s")
    lamp(T, 90, 20, "modern", 60)
    lamp(T, 390, 20, "modern", 60, "light2")
    return cv


BUILDERS = {"bakery": bakery, "cafe": cafe, "flowershop": flowershop, "pizzeria": pizzeria, "boutique": boutique,
            "pharmacy": pharmacy, "gas_station": gas_station, "supermarket": supermarket, "restaurant": restaurant,
            "cinema": cinema, "mall": mall, "hotel": hotel, "office": office, "sky_office": sky_office}
