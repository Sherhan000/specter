"""Cafes and fast food, each with its own look: a coffee kiosk with a giant cup, a shawarma grill, a burger bar,
a donut shop, a food-truck court, a Tajik teahouse (chaikhana) and a drive-thru."""
import numpy as np

from raster import C, U, Canvas, flat, solid_res, glow_res, nores
from arch import Orient, facade, Win, roof_mat, flat_top
import kit
from bkit import ground, tree, bush, lamp, bench, bins, box, slab, post, awning, sign_board, pole_sign, entry, door, \
    canopy, car_static, parking_lot


def _cyl(T, s, f, r, z0, z1, col, cap=None, noise=3):
    """An upright cylinder at a front-relative point (cap colour defaults to the side colour)."""
    x, y = T.pt(s, f)
    side = flat(col, noise)
    top = flat(cap or col, noise)
    T.cv.cylinder(x, y, r, z0, z1, lambda a, v, nx, ny: side(a * 20, v), lambda a, b: top(a, b))


def _glow_cyl(T, s, f, r, z0, z1, col):
    x, y = T.pt(s, f)
    T.cv.cylinder(x, y, r, z0, z1, lambda a, v, nx, ny: glow_res(col, a.shape, 200), lambda a, b: glow_res(col, a.shape, 200))


def _dome(T, s, f, r, z, h, col, noise=3):
    """Top half of an ellipsoid (a bun, a cup lid)."""
    x, y = T.pt(s, f)
    fn = flat(col, noise)
    T.cv.ellipsoid(x, y, z, r, r, h, lambda wx, wy, wz, *n: fn(wx + wz, wy), cut_z=z)


def _stool(T, s, f, col="d8402e"):
    post(T, s, f, 0, 10, "8a8a90", 1.2)
    _cyl(T, s, f, 3.2, 10, 12, col)


def _table(T, s, f, top="f2eee6", leg="8a8a90", r=6):
    post(T, s, f, 0, 9, leg, 1.2)
    _cyl(T, s, f, r, 9, 10.5, top)


def _chair(T, s, f, col):
    T.box(s - 2.5, f - 2.5, s + 2.5, f + 2.5, 0, 6, all=flat(col, 2), top=flat(col, 2))


# --------------------------------------------------------------------------- coffee kiosk
def coffee_kiosk(L, o):
    """A round teal kiosk with a walk-up window and a giant coffee cup on the roof, stools and a menu stand."""
    cv = Canvas(1, 96)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.paving("d8cfc0", 6.0, 5))
    ground(T, 30, 50, 130, 150, kit.paving("b8a48a", 6.0, 6), 0.4)
    teal, cream, brown = "2e8a86", "f4ead8", "5a3a24"
    x, y = T.pt(80, 100)

    def wall(a, v, nx, ny):
        rgb = np.where(((v > 14) & (v < 30))[..., None], C("1e2a2e"), C(teal)) * np.ones(a.shape + (3,))
        rgb = np.where(((v >= 30) & (v < 33))[..., None], C(cream), rgb)
        win = (v > 14) & (v < 30)
        em = np.zeros(a.shape + (4,))
        em[win] = np.append(C("ffcf80"), 150)
        return rgb, win, em
    cv.cylinder(x, y, 30, 0, 40, wall, lambda a, b: solid_res(C(cream), a.shape))
    _cyl(T, 80, 100, 33, 40, 43, brown)
    door(T, 70, 18, 70, 30)
    # counter shelf at the window
    T.box(56, 64, 104, 70, 13, 15, all=flat(cream, 2), top=flat(cream, 2))
    # the giant cup: white body, brown sleeve, lid and a handle
    _cyl(T, 80, 100, 15, 43, 66, "f6f2ea")
    _cyl(T, 80, 100, 15.5, 49, 58, brown)
    _cyl(T, 80, 100, 16.5, 66, 69, "e8e2d6")
    _dome(T, 80, 100, 14, 69, 5, "f6f2ea")
    T.box(95, 97, 100, 103, 50, 62, all=flat("f6f2ea", 2), top=flat("f6f2ea", 2))
    # steam
    for k in range(3):
        _dome(T, 76 + k * 4, 100, 3.0 - k * 0.6, 76 + k * 6, 2.5, "eef2f4", 1)
    for k in range(3 if L >= 2 else 2):
        _stool(T, 60 + k * 20, 54, ["d8402e", "e8a82a", "2e8a86"][k])
    T.box(126, 50, 128, 54, 0, 22, all=flat("3a3a40", 2), top=flat("3a3a40", 2))
    T.box(120, 48, 134, 50, 10, 24, all=flat("1e1e22", 2), top=flat("1e1e22", 2))
    entry(T, 80)
    if L >= 2:
        _table(T, 26, 30)
        _table(T, 134, 30)
        bins(T, 20, 110)
    if L >= 3:
        lamp(T, 144, 140, "modern", 40)
        tree(T, 18, 140, "lime", 0.6, 7)
    return cv


# --------------------------------------------------------------------------- shawarma
def shawarma(L, o):
    """An open grill stall: a yellow-and-black counter, two glowing vertical spits, a menu board, plastic tables."""
    cv = Canvas(1, 76)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.paving("c8c2b4", 7.0, 9))
    yel, blk = "f0c020", "26221e"
    wall = facade("tile", "f2eee6", plinth=("3a3a3a", 4), seed=41, lit=0.7)
    T.box(28, 96, 132, 148, 0, 42, all=wall, top=flat_top("6a6460", "a8a296", 2))
    # open front: dark back room, counter, grills
    T.box(32, 92, 128, 96, 0, 40, all=flat("3a2e26", 3), top=flat("3a2e26", 2))
    T.box(26, 70, 134, 92, 0, 16, all=flat(blk, 2), top=flat("c8c8cc", 3))
    T.box(26, 70, 134, 72, 4, 12, all=flat(yel, 2), top=flat(yel, 2))
    for s in (52, 76):
        post(T, s, 84, 16, 40, "8a8a90", 1.0)
        _glow_cyl(T, s + 4, 88, 2.5, 16, 38, "ff6a2a")
        _cyl(T, s, 84, 6, 20, 36, "9a5a2a", "b87a3a", 6)
    T.box(96, 78, 124, 88, 16, 22, all=flat("e8e4dc", 2), top=flat("6ab83a", 4))
    # canopy and sign
    slab(T, 22, 60, 138, 96, 42, 45, yel, flat(yel, 3))
    sign_board(T, 80, 60, 45, "SHAWARMA", 9, blk, yel)
    post(T, 24, 62, 0, 42, blk, 2.0)
    post(T, 136, 62, 0, 42, blk, 2.0)
    door(T, 104, 18, 96, 30)
    entry(T, 80)
    # plastic tables and chairs
    for k, s in enumerate((36, 84) if L == 1 else (30, 76, 122)):
        _table(T, s, 36, "f2eee6", "f2eee6", 7)
        _chair(T, s - 10, 36, "d8402e")
        _chair(T, s + 10, 36, "2e6ab8")
    if L >= 2:
        T.box(140, 120, 150, 130, 0, 16, all=flat("3a6ab8", 2), top=flat("e8e8ea", 2))
    if L >= 3:
        lamp(T, 150, 20, "modern", 40)
        bins(T, 12, 120)
    return cv


# --------------------------------------------------------------------------- burger bar
def burger_bar(L, o):
    """A boxy red-and-yellow burger bar with a full glass front and a giant burger on the roof."""
    cv = Canvas(1, 104)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.paving("d4ccbe", 8.0, 11))
    H = 40
    win = Win(w=16, h=18, sill=10, sp=22, margin=10, fh=H, frame="2a2a2e", style="vertical", tint="f8e0a0", group="shop")
    front = facade("metal", "d8302a", shop=(6, 112, 28), doors=[(48, 22, 30, "glass")], plinth=("2a2a2e", 4), seed=51, lit=1.0,
                   bands=[(32, 36, "f0c020")])
    side = facade("metal", "d8302a", win=win, plinth=("2a2a2e", 4), seed=52, lit=1.0, bands=[(32, 36, "f0c020")])
    box(T, 20, 50, 140, 150, 0, H, front=front, back=side, left=side, right=side, top=flat_top("4a4a4e", "f0c020", 3))
    door(T, 68, 22, 50, 30)
    # giant burger: bottom bun, patty, cheese, lettuce, top bun with seeds
    s, f = 80, 100
    _cyl(T, s, f, 22, H, H + 6, "d8963a", "e0a448")
    _cyl(T, s, f, 23, H + 6, H + 12, "5a3420")
    T.box(s - 20, f - 20, s + 20, f + 20, H + 12, H + 13.5, all=flat("f4c430", 2), top=flat("f4c430", 2))
    _cyl(T, s, f, 24, H + 13.5, H + 15.5, "5aa83a")
    _cyl(T, s, f, 22, H + 15.5, H + 18, "d8963a")
    _dome(T, s, f, 22, H + 18, 14, "e0a448")
    for k in range(7):
        a = k * 0.9
        _dome(T, s + np.cos(a) * 12, f + np.sin(a) * 12, 1.4, H + 27, 1.0, "fff4d8", 1)
    sign_board(T, 80, 50, H, "BURGERS", 8, "f0c020", "d8302a")
    canopy(T, 22, 138, 50, 10, 30, "f0c020", "d8302a", posts=False)
    entry(T, 79)
    _stool(T, 30, 30, "f0c020")
    _table(T, 40, 26, "d8302a")
    if L >= 2:
        _table(T, 120, 26, "d8302a")
        _stool(T, 110, 30, "f0c020")
        _stool(T, 130, 30, "f0c020")
    if L >= 3:
        pole_sign(T, 150, 20, 66, "BURGER", 9, "d8302a", "f0c020")
        bins(T, 8, 120)
    return cv


# --------------------------------------------------------------------------- donut shop
def _torus(T, s, f, R, r, z, top, icing, sprinkles=True):
    """A donut lying flat: dough ring with icing and sprinkles on top."""
    x, y = T.pt(s, f)
    w = int(2 * (R + r) + 4)
    x0, y0 = x - w / 2, y - w / 2
    ys, xs = np.mgrid[0:w, 0:w] + 0.5
    d = np.hypot(xs - w / 2, ys - w / 2)
    q = r * r - (d - R) ** 2
    Hh = np.where(q > 0, z + np.sqrt(np.clip(q, 0, None)), -np.inf)
    dough, ice = C(top), C(icing)
    cols = [C("f6f2ea"), C("2e8ad8"), C("f0c020"), C("6ab83a"), C("d8402e")]

    def fn(wx, wy, wz, nx, ny, nz):
        rgb = np.where((wz > z + r * 0.35)[..., None], ice, dough) * np.ones(wx.shape + (3,))
        if sprinkles:
            h = np.floor(wx * 0.7) * 7.0 + np.floor(wy * 0.7) * 13.0
            pick = (np.sin(h) * 43758.5) % 1.0
            sp = (wz > z + r * 0.55) & (pick > 0.9)
            for i, c in enumerate(cols):
                m = sp & (np.floor(pick * 1000) % 5 == i)
                rgb[m] = c
        return rgb, nores(wx.shape), None
    T.cv.heightfield(x0, y0, Hh, fn, zmin=z - r, thick=2 * r)


def donut_shop(L, o):
    """A pastel-pink shop with a scalloped mint awning and a giant sprinkled donut standing on the roof."""
    cv = Canvas(1, 100)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.paving("eee4e0", 7.0, 13))
    pink, mint = "f2a8c0", "8ad8c0"
    H = 38
    win = Win(w=14, h=16, sill=12, sp=26, margin=14, fh=H, frame="f6f2ea", style="arch", arch=True, tint="ffe8c8", group="shop")
    front = facade("plaster", pink, shop=(10, 84, 24), doors=[(92, 20, 28, "glass")], plinth=("c8708a", 4), seed=61, lit=1.0,
                   cornice=("f6f2ea", 4))
    side = facade("plaster", pink, win=win, plinth=("c8708a", 4), seed=62, lit=1.0, cornice=("f6f2ea", 4))
    box(T, 22, 46, 138, 148, 0, H, front=front, back=side, left=side, right=side, top=flat_top("e8d8dc", "f6f2ea", 3))
    door(T, 114, 20, 46, 28)
    awning(T, 26, 110, 46, 30, 14, 6, mint, "f6f2ea", 7.0)
    # the donut on a short stand
    post(T, 80, 100, H, H + 12, "f6f2ea", 3.0)
    _torus(T, 80, 100, 18, 9, H + 20, "d8a060", "e86aa0")
    sign_board(T, 60, 46, H, "DONUTS", 8, "f6f2ea", "c84a7a")
    entry(T, 80)
    for k, s in enumerate((30, 60) if L == 1 else (30, 60, 130)):
        _table(T, s, 26, "f6f2ea", "c8708a")
        _chair(T, s, 16, mint)
    if L >= 2:
        for k in range(3):
            x0, y0, x1, y1 = T.rect(142, 60 + k * 26, 154, 80 + k * 26)
            kit.flowerbed(cv, x0, y0, x1, y1, k + 3, "c8708a", 6)
    if L >= 3:
        lamp(T, 8, 10, "lantern", 40)
        bench(T, 100, 14, "s", "f2a8c0")
    return cv


# --------------------------------------------------------------------------- food trucks
TRUCKS = [("d8402e", "f6f2ea", "TACO"), ("2e6ab8", "f0c020", "HOT DOG"), ("6ab83a", "f6f2ea", "WOK"), ("e8a82a", "26221e", "PIZZA")]


def _truck(T, s, f, col, trim, text, along="s"):
    """A food truck parked with its serving hatch facing the court (towards -f)."""
    T.box(s, f, s + 64, f + 30, 4, 34, all=flat(col, 3), top=flat("e8e4dc", 3))
    T.box(s + 64, f, s + 80, f + 30, 4, 24, all=flat(col, 3), top=flat(col, 3))
    T.box(s + 66, f - 0.5, s + 78, f, 14, 22, all=flat("3a4a5a", 2), top=flat("3a4a5a", 2))
    # hatch: glowing opening and a raised flap
    T.box(s + 8, f - 0.6, s + 56, f, 14, 28, all=lambda u, v, L, H: glow_res("ffd890", u.shape, 120), top=flat("f6f2ea", 2))
    T.box(s + 6, f - 12, s + 58, f, 30, 32, all=flat(trim, 2), top=flat(trim, 3))
    T.box(s + 6, f - 6, s + 58, f, 12, 14, all=flat("c8c8cc", 2), top=flat("d8d8dc", 2))
    sign_board(T, s + 32, f + 15, 34, text, 7, trim, col, depth=1.0)
    for ss in (s + 14, s + 68):
        for ff in (f + 2, f + 28):
            x, y = T.pt(ss, ff)
            T.cv.cylinder(x, y, 5, 0, 8, lambda a, v, nx, ny: solid_res(C("1e1e22"), a.shape))


def food_trucks(L, o):
    """A food-truck court: trucks in a row, picnic tables under string lights, a tree in a planter."""
    cv = Canvas(2, 86)
    T = Orient(cv, o)
    ground(T, 0, 0, 320, 320, kit.asphalt_lot("5a5c62", 4))
    ground(T, 10, 10, 310, 190, kit.paving("d8cfbe", 9.0, 17), 0.4)
    n = 3 if L == 1 else 4
    for k in range(n):
        tc, tr, tx = TRUCKS[k]
        if k < 3:
            _truck(T, 14 + k * 100, 220, tc, tr, tx)
        else:
            _truck(T, 230, 60, tc, tr, tx)
    # picnic tables
    for k, (s, f) in enumerate(((50, 120), (130, 120), (210, 120), (90, 60))[: 3 + (L >= 2)]):
        T.box(s, f, s + 40, f + 16, 10, 12, all=flat("a8825a", 2), top=flat("c8a070", 3))
        T.box(s, f - 8, s + 40, f - 3, 5, 7, all=flat("8a6a44", 2), top=flat("b08a5a", 3))
        T.box(s, f + 19, s + 40, f + 24, 5, 7, all=flat("8a6a44", 2), top=flat("b08a5a", 3))
        post(T, s + 4, f + 8, 0, 10, "6a4a2a", 2.0)
        post(T, s + 36, f + 8, 0, 10, "6a4a2a", 2.0)
    # string lights between poles
    poles = [(20, 30), (20, 196), (300, 196), (300, 30)]
    for s, f in poles:
        post(T, s, f, 0, 54, "3a3a40", 2.0)
    for (s0, f0), (s1, f1) in zip(poles, poles[1:]):
        for k in range(1, 14):
            t = k / 14
            sag = 8 * (1 - (2 * t - 1) ** 2)
            ss, ff = s0 + (s1 - s0) * t, f0 + (f1 - f0) * t
            x, y = T.pt(ss, ff)
            col = ["ffd84a", "ff8a4a", "fff4c8"][k % 3]
            T.cv.box(x - 1.2, y - 1.2, 50 - sag, x + 1.2, y + 1.2, 52.4 - sag,
                     lambda u, v, *_: glow_res(col, u.shape, 230), lambda u, v, *_: glow_res(col, u.shape, 230),
                     lambda u, v, *_: glow_res(col, u.shape, 230))
    T.box(150, 40, 174, 64, 0, 10, all=flat("8a8478", 3), top=flat("5a4a34", 6))
    tree(T, 162, 52, "lime", 0.7, 12)
    entry(T, 160)
    door(T, 22, 48, 220, 14)
    if L >= 3:
        bins(T, 300, 230)
        bench(T, 280, 20, "s", "3a3a40")
    return cv


# --------------------------------------------------------------------------- chaikhana
CARPETS = [("a8202a", "e8b84a"), ("2a3a8a", "e8d8b0"), ("8a2a5a", "f0c020")]


def _carpet(u, v, L, D, c1, c2):
    border = (u < 3) | (v < 3) | (u > L - 3) | (v > D - 3)
    diamond = (np.abs(u - L / 2) / (L / 2) + np.abs(v - D / 2) / (D / 2)) < 0.55
    rgb = np.where((border | diamond)[..., None], C(c2), C(c1)) * np.ones(u.shape + (3,))
    return rgb, nores(u.shape), None


def _topchan(T, s, f, w, d, k, teapot=True):
    """A raised wooden platform with a carpet, cushions, a low table and a teapot."""
    wood = flat("8a5a30", 3)
    for ss, ff in ((s + 2, f + 2), (s + w - 2, f + 2), (s + 2, f + d - 2), (s + w - 2, f + d - 2)):
        post(T, ss, ff, 0, 12, "6a4024", 2.5)
    T.box(s, f, s + w, f + d, 12, 15, all=wood, top=flat("a8703a", 3))
    c1, c2 = CARPETS[k % len(CARPETS)]
    T.box(s + 3, f + 3, s + w - 3, f + d - 3, 15, 15.6, all=flat(c1, 2),
          top=lambda u, v, L, D: _carpet(u, v, L, D, c1, c2))
    # back rail
    T.box(s, f + d - 2, s + w, f + d, 15, 24, all=flat("7a4a26", 3), top=flat("a8703a", 3))
    for i in range(int(w // 14)):
        T.box(s + 4 + i * 14, f + d - 9, s + 14 + i * 14, f + d - 3, 15.6, 21, all=flat(c2, 3), top=flat(c2, 3))
    T.box(s + w / 2 - 10, f + d / 2 - 7, s + w / 2 + 10, f + d / 2 + 7, 15.6, 20, all=flat("6a4024", 2), top=flat("8a5a30", 3))
    if teapot:
        _cyl(T, s + w / 2 - 3, f + d / 2, 2.6, 20, 24, "e8e8f0", "2a6ab8")
        _dome(T, s + w / 2 - 3, f + d / 2, 2.6, 24, 1.6, "2a6ab8", 1)
        for j in range(3):
            _cyl(T, s + w / 2 + 3 + j * 2.5, f + d / 2 - 3 + j * 2.5, 1.1, 20, 21.6, "f6f2ea", "c88a3a")


def _carved_post(T, s, f, z0, z1):
    post(T, s, f, z0, z1, "8a5a30", 4.0)
    for k in range(4):
        z = z0 + 8 + k * (z1 - z0 - 12) / 3
        T.box(s - 2.8, f - 2.8, s + 2.8, f + 2.8, z, z + 2, all=flat("c89a50", 2), top=flat("c89a50", 2))
    T.box(s - 5, f - 5, s + 5, f + 5, z1 - 4, z1, all=flat("c89a50", 3), top=flat("c89a50", 3))


def chaikhana(L, o):
    """A Tajik teahouse: carved wooden columns hold a wide painted roof over topchans with carpets, a samovar,
    a grapevine pergola and roses."""
    cv = Canvas(2, 78)
    T = Orient(cv, o)
    ground(T, 0, 0, 320, 320, kit.paving("d8c8a8", 10.0, 23))
    ground(T, 30, 106, 290, 300, kit.bricks_pave("b88a64", 24), 0.4)
    H = 46
    # kitchen block at the back
    win = Win(w=14, h=18, sill=12, sp=34, margin=16, fh=H, frame="6a4024", style="arch", arch=True, tint="ffe0a8", group="shop")
    wall = facade("plaster", "f2ead8", win=win, plinth=("8a6a4a", 5), seed=71, lit=0.9, bands=[(H - 8, H - 4, "2a8aa8")])
    back = facade("plaster", "f2ead8", win=win, doors=[(130, 30, 34, "double", "6a4024")], plinth=("8a6a4a", 5), seed=72, lit=0.9,
                  bands=[(H - 8, H - 4, "2a8aa8")])
    box(T, 40, 250, 280, 300, 0, H, front=back, back=wall, left=wall, right=wall, top=flat_top("8a7a64", "c8b89a", 3))
    door(T, 170, 30, 250, 34)
    # veranda: carved posts and a deep painted roof with turquoise trim
    for s in (40, 120, 200, 280):
        _carved_post(T, s, 186, 0, H)

    def ceiling(u, v, L, D):
        stripe = (np.floor(u / 10) % 2) == 0
        rgb = np.where(stripe[..., None], C("2a8aa8"), C("c84a2a")) * np.ones(u.shape + (3,))
        return rgb, nores(u.shape), None
    T.box(30, 176, 290, 252, H, H + 3, all=flat("2a8aa8", 2), top=ceiling)
    T.box(26, 172, 294, 254, H + 3, H + 6, all=flat("c89a50", 3), top=flat("c89a50", 3))
    T.hip(26, 172, 294, 254, H + 6, 14, roof_mat("2a8a7a", "tiles"), o=2)
    sign_board(T, 160, 172, H + 2, "CHAIKHANA", 9, "2a8aa8", "f6e8b0")
    # topchans under the roof
    for k in range(3):
        _topchan(T, 48 + k * 80, 194, 64, 48, k)
    for k in range(1 if L == 1 else 2):
        _topchan(T, 70 + k * 120, 116, 60, 44, k + 1)
    # samovar
    _cyl(T, 270, 150, 6, 0, 3, "8a6a3a")
    _cyl(T, 270, 150, 5, 3, 18, "c8902a")
    _dome(T, 270, 150, 5, 18, 3, "c8902a", 2)
    post(T, 270, 150, 20, 26, "3a3a40", 1.4)
    # grapevine pergola over the front path
    for s in (110, 210):
        for f in (30, 96):
            post(T, s, f, 0, 40, "6a4024", 2.2)
    for k in range(9):
        T.box(108, 28 + k * 8, 212, 31 + k * 8, 40, 42, all=flat("6a4024", 2), top=flat("4a8a2a", 8))
    if L >= 2:
        for f in (50, 76):
            for s in (130, 160, 190):
                _dome(T, s, f, 3, 36, 4, "6a2a6a", 2)
        for s in (40, 280):
            bush(T, s, 60, 0.8, 9 + s, "d8304a")
    if L >= 3:
        _topchan(T, 230, 40, 60, 44, 0)
        tree(T, 40, 30, "oak", 0.9, 14)
        lamp(T, 96, 10, "lantern", 44)
    entry(T, 160)
    return cv


# --------------------------------------------------------------------------- drive-thru
def drive_thru(L, o):
    """A fast-food restaurant with a drive-thru lane around it: menu board, pick-up window, parking and a tall pole sign."""
    cv = Canvas(2, 110)
    T = Orient(cv, o)
    ground(T, 0, 0, 320, 320, kit.asphalt_lot("4e5056", 4))
    # drive lane painted around the building, kerb island
    ground(T, 70, 120, 290, 290, kit.paving("c8c2b4", 8.0, 27), 0.4)
    ground(T, 0, 0, 320, 34, kit.paving("d0c8ba", 8.0, 28), 0.4)
    H = 36
    win = Win(w=26, h=20, sill=8, sp=32, margin=10, fh=H, frame="2a2a2e", style="vertical", tint="f8e8b0", group="shop")
    front = facade("concrete", "f2eee6", shop=(10, 150, 26), doors=[(162, 28, 28, "double_glass")], plinth=("2a2a2e", 4), seed=81,
                   lit=1.0, bands=[(H - 10, H, "2a6a3a")])
    side = facade("concrete", "f2eee6", win=win, plinth=("2a2a2e", 4), seed=82, lit=1.0, bands=[(H - 10, H, "2a6a3a")])
    pick = facade("concrete", "f2eee6", shop=(40, 70, 18), plinth=("2a2a2e", 4), seed=83, lit=1.0, bands=[(H - 10, H, "2a6a3a")])
    box(T, 90, 140, 270, 270, 0, H, front=front, back=side, left=side, right=pick, top=flat_top("5a5a5e", "e8a82a", 3))
    # sloped orange fascia on the front, tower with the logo
    T.box(86, 136, 274, 146, H, H + 8, all=flat("e8a82a", 2), top=flat("f0c020", 3))
    T.box(200, 180, 250, 230, H, H + 26, all=flat("2a6a3a", 3), top=flat_top("4a4a4e", "f0c020", 2))
    sign_board(T, 225, 180, H + 8, "FAST FOOD", 8, "2a6a3a", "f0c020")
    door(T, 252, 28, 140, 28)
    # pick-up window canopy on the right, menu board on the lane
    T.box(270, 170, 300, 220, 30, 33, all=flat("e8a82a", 2), top=flat("e8a82a", 3))
    T.box(296, 260, 300, 290, 0, 30, all=flat("2a2a2e", 2), top=flat("2a2a2e", 2))
    T.box(292, 262, 296, 288, 10, 28, all=lambda u, v, L, H: glow_res("f8e0a0", u.shape, 160), top=flat("2a2a2e", 2))
    # lane arrows (painted)
    for f in (90, 230):
        T.box(302, f, 310, f + 14, 0.3, 0.8, all=flat("f6f2ea", 1), top=flat("f6f2ea", 1))
    car_static(T, 305, 195, "f", "2a5aa8")
    if L >= 2:
        car_static(T, 305, 125, "f", "c84a3a")
    parking_lot(T, 10, 40, 64, 300, "f", 26.0)
    car_static(T, 37, 80, "s", "e8e8ea")
    if L >= 3:
        car_static(T, 37, 160, "s", "2a2c30")
    pole_sign(T, 30, 20, 100, "FAST", 14, "d8302a", "f0c020")
    _table(T, 120, 110, "e8a82a")
    _table(T, 160, 110, "e8a82a")
    if L >= 2:
        canopy(T, 104, 186, 136, 26, 28, "f2eee6", "e8a82a", posts=True)
    if L >= 3:
        tree(T, 80, 60, "lime", 0.7, 15)
        lamp(T, 200, 20, "modern", 46)
    entry(T, 266)
    return cv


BUILDERS = {"coffee_kiosk": coffee_kiosk, "shawarma": shawarma, "burger_bar": burger_bar, "donut_shop": donut_shop,
            "food_trucks": food_trucks, "chaikhana": chaikhana, "drive_thru": drive_thru}
