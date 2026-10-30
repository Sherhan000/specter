"""New filling stations, each with its own look (the old red gas station stays in b_shops):
an electric charging station under a solar roof and a big highway fuel stop with a shop, a cafe and a car wash."""
import numpy as np

from raster import C, Canvas, flat, glow_res
from arch import Orient, facade, flat_top
import kit
from bkit import ground, tree, bush, lamp, bench, box, slab, post, sign_board, pole_sign, entry, door, car_static


def _glow(col, k=200):
    return lambda u, v, L, H: glow_res(col, u.shape, k)


def _cyl(T, s, f, r, z0, z1, col, noise=3):
    x, y = T.pt(s, f)
    side = flat(col, noise)
    T.cv.cylinder(x, y, r, z0, z1, lambda a, v, nx, ny: side(a * 20, v), lambda a, b: flat(col, noise)(a, b))


def _bays(T, s0, f0, s1, f1, n, col="f4f2ea"):
    """Painted bay lines across s (cars stand along f)."""
    w = (s1 - s0) / n
    for k in range(n + 1):
        s = s0 + k * w
        T.box(s - 0.8, f0, s + 0.8, f1, 0.4, 0.8, all=flat(col, 1), top=flat(col, 1))


# --------------------------------------------------------------------------- EV charging station
def _charger(T, s, f, body="f4f6f4", accent="2ab86a"):
    """A charging pillar: white column, glowing green screen and a cable hook."""
    slab(T, s - 6, f - 4, s + 6, f + 4, 0, 2, "c8ccc8")
    T.box(s - 4, f - 2.5, s + 4, f + 2.5, 2, 24, front=facade("plaster", body, plinth=None, decals=[(1.5, 12, 5, 7, "emit:7af0a8")]),
          back=flat(body), left=flat(accent, 2), right=flat(accent, 2), top=flat(accent, 2))
    T.box(s - 4, f - 3, s + 4, f - 2.5, 20, 24, all=_glow("7af0a8", 180), top=flat(accent, 2))
    post(T, s + 5, f, 8, 16, "2a2a30", 1.0)


def ev_station(L, o):
    """An electric car charging hub: a timber canopy with solar panels, green charging pillars,
    electric cars plugged in, a battery cabinet and a little lounge kiosk."""
    cv = Canvas(1, 100)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.paving("d6d8d2", 8.0, 41))
    ground(T, 8, 14, 152, 96, kit.asphalt_lot("4e545a", 42), 0.4)
    # green bays for electric cars
    for k in range(3):
        ground(T, 14 + k * 46, 18, 54 + k * 46, 92, flat("3a8a5a", 3), 0.5)
    _bays(T, 12, 18, 150, 92, 3)
    # chargers between the bays at the back
    for k in range(3):
        _charger(T, 34 + k * 46, 100)
    # solar canopy on slim posts
    cz = 40
    for ss in (14, 146):
        for ff in (24, 98):
            post(T, ss, ff, 0, cz, "8a6a44", 2.6)
    slab(T, 8, 16, 152, 104, cz, cz + 3, "a8804c", flat("8a6a44", 3))
    x0, y0, x1, y1 = T.rect(12, 20, 148, 100)
    kit.solar(cv, x0, y0, x1, y1, cz + 3, 4)
    T.box(8, 14, 152, 16, cz - 4, cz + 3, front=facade("plaster", "2ab86a", plinth=None, signs=[(72, 0.5, "EV CHARGE", 5, None, "ffffff", True)]),
          back=flat("2ab86a"), left=flat("2ab86a"), right=flat("2ab86a"), top=flat("2ab86a"))
    cv.mark("light", *T.pt(80, 58), cz - 2)
    # electric cars plugged in
    car_static(T, 34, 62, "f", "f4f6f8")
    if L >= 2:
        car_static(T, 126, 62, "f", "2a8ac8")
    if L >= 3:
        car_static(T, 80, 62, "f", "c83a3a")
    # battery cabinet and a lounge kiosk at the back
    box(T, 10, 112, 56, 150, 0, 20, front=facade("plaster", "e8ece8", plinth=None, decals=[(6, 6, 10, 8, "emit:7af0a8")]),
        back=flat("e8ece8"), left=flat("c8ccc8"), right=flat("c8ccc8"), top=flat_top("8a8e8a", "2ab86a", 2))
    lounge = facade("glass", "dfeee6", shop=(4, 56, 22), doors=[(62, 12, 22, "glass")], seed=411, plinth=("4a4e4a", 3), lit=1.0)
    lside = facade("plaster", "f2f4f0", seed=412)
    box(T, 70, 112, 150, 150, 0, 28, front=lounge, back=lside, left=lside, right=lside, top=flat_top("6a6e6a", "2ab86a", 2))
    x0, y0, x1, y1 = T.rect(76, 118, 144, 146)
    kit.solar(cv, x0, y0, x1, y1, 28, 3)
    door(T, 132, 12, 112, 22)
    pole_sign(T, 6, 6, 62, "EV", 12, "2ab86a", "ffffff")
    if L >= 2:
        bench(T, 112, 106, "s")
        bush(T, 64, 132, 0.6, 43, None)
    if L >= 3:
        tree(T, 152, 104, "lime", 0.6, 44)
        lamp(T, 60, 6, "modern", 42)
    entry(T, 132)
    return cv


# --------------------------------------------------------------------------- highway fuel stop
def _pump(T, s, f):
    """A tall blue fuel pump on a kerb island with a glowing price screen."""
    slab(T, s - 7, f - 16, s + 7, f + 16, 0, 2.5, "c8c8c8")
    T.box(s - 4, f - 6, s + 4, f + 6, 2.5, 22, front=facade("plaster", "f2f4f6", plinth=None, decals=[(1.5, 10, 9, 8, "emit:f0d060")]),
          back=facade("plaster", "f2f4f6", plinth=None, decals=[(1.5, 10, 9, 8, "emit:f0d060")]),
          left=flat("1e4a9a", 2), right=flat("1e4a9a", 2), top=flat("f0c020", 2))
    post(T, s - 5, f - 12, 2.5, 8, "e83a2a", 1.6)
    post(T, s + 5, f + 12, 2.5, 8, "e83a2a", 1.6)


def _tanker(T, s, f):
    """A fuel tanker truck parked along s."""
    T.box(s - 50, f - 9, s + 20, f + 9, 4, 8, all=flat("3a3a40", 2), top=flat("3a3a40", 2))
    T.box(s - 48, f - 8, s + 18, f + 8, 8, 24, all=flat("e2e4e8", 3), top=flat("d0d4da", 3))
    T.box(s - 48, f - 8.5, s + 18, f - 8, 14, 18, all=flat("1e4a9a", 2), top=flat("1e4a9a", 2))
    T.box(s + 22, f - 9, s + 40, f + 9, 3, 22, all=flat("1e4a9a", 3), top=flat("1e4a9a", 3))
    T.box(s + 36, f - 8, s + 40.5, f + 8, 12, 20, all=flat("3a4a5a", 2), top=flat("1e4a9a", 2))


def gas_highway(L, o):
    """A big blue-and-yellow highway fuel stop: a wide canopy over three pump islands, a shop with a cafe,
    a car wash with spinning brushes, an air post and a tall price pylon."""
    cv = Canvas(2, 130)
    T = Orient(cv, o)
    ground(T, 0, 0, 320, 320, kit.asphalt_lot("50535a", 51))
    ground(T, 0, 0, 320, 8, kit.paving("c8c2b4", 8.0, 52), 0.4)
    # big canopy over three pump islands
    cz = 54
    blue, yel = "1e4a9a", "f0c020"
    for ss in (30, 120, 210):
        for ff in (40, 120):
            post(T, ss, ff, 0, cz, "e8eaee", 4)
        _pump(T, ss + 6, 80)
    T.box(10, 26, 240, 136, cz, cz + 10, front=facade("plaster", blue, plinth=None, signs=[(115, 2, "PETROL  24/7", 6, None, yel, True)]),
          back=flat(blue), left=flat(blue), right=flat(blue), top=flat_top("d8dce2", yel, 3))
    T.box(10, 24, 240, 26, cz + 1, cz + 3, all=flat(yel, 2), top=flat(yel, 2))
    T.box(14, 30, 236, 132, cz - 1, cz, all=_glow("f4f0e0", 150), top=flat("d8dce2"))
    for ss in (60, 160):
        cv.mark("light", *T.pt(ss, 80), cz - 2)
    car_static(T, 60, 70, "f", "e8e8ea")
    if L >= 2:
        car_static(T, 150, 92, "f", "2a2c30")
    if L >= 3:
        car_static(T, 240 - 4, 70, "f", "c84a3a")
    # shop with a cafe at the back
    H = 34
    shop = facade("glass", "eef2f6", shop=(8, 150, 24), doors=[(166, 14, 26, "double_glass")], seed=511, plinth=("2a2a30", 4), lit=1.0,
                  bands=[(H - 8, H, blue)])
    side = facade("plaster", "f2f4f6", seed=512, plinth=("2a2a30", 4), bands=[(H - 8, H, blue)])
    box(T, 20, 190, 220, 300, 0, H, front=shop, back=side, left=side, right=side, top=flat_top("6a6e74", yel, 3))
    sign_board(T, 80, 190, H, "SHOP", 8, blue, yel)
    sign_board(T, 170, 190, H, "CAFE", 8, yel, blue)
    door(T, 166, 14, 190, 26)
    kit.ac_unit(cv, *T.pt(60, 250), H)
    kit.ac_unit(cv, *T.pt(180, 260), H)
    # tables outside the cafe
    for ss in (140, 200):
        _cyl(T, ss, 172, 1.2, 0, 9, "8a8a90")
        _cyl(T, ss, 172, 6, 9, 10.5, "f2eee6")
    # car wash on the right: open portal with blue brushes
    for ff in (170, 290):
        T.box(256, ff - 4, 312, ff, 0, 40, all=flat("e8eaee", 2), top=flat(blue, 2))
    T.box(256, 166, 312, 290, 40, 46, front=facade("plaster", blue, plinth=None, signs=[(28, 1.5, "WASH", 5, None, "ffffff", True)]),
          back=flat(blue), left=flat(blue), right=flat(blue), top=flat_top("8a8e94", yel, 2))
    for ss in (262, 306):
        _cyl(T, ss, 230, 5, 4, 36, "3a7ae8", 6)
    ground(T, 256, 166, 312, 290, flat("8a9aa8", 4), 0.5)
    if L >= 2:
        car_static(T, 284, 230, "f", "f0c020")
    # air & water post, bins
    T.box(250, 140, 258, 146, 0, 18, all=flat("e83a2a", 2), top=flat("e83a2a", 2))
    kit.bin_(cv, *T.pt(12, 180))
    # tall price pylon
    pole_sign(T, 300, 18, 120, "95", 12, blue, yel)
    T.box(300 - 14, 16, 300 + 14, 20, 72, 98, front=facade("plaster", "1a1a20", plinth=None, signs=[(14, 3, "92", 8, None, "7af0a8", True)]),
          back=flat("1a1a20"), left=flat("1a1a20"), right=flat("1a1a20"), top=flat(blue))
    if L >= 3:
        _tanker(T, 120, 160)
        tree(T, 10, 310, "lime", 0.7, 53)
        bush(T, 236, 306, 0.7, 54, None)
        lamp(T, 250, 10, "modern", 50)
    entry(T, 166)
    return cv


BUILDERS = {"ev_station": ev_station, "gas_highway": gas_highway}
