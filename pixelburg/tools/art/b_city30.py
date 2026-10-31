"""Twenty more city objects, each with its own look: car places (car wash, auto repair, car dealer, car plant),
small shops, neighbourhood services, leisure and street decoration. builder(L, o) -> Canvas."""
import numpy as np

from raster import C, U, Canvas, flat, nores, hash2, glow_res
from arch import Orient, facade, Win, roof_mat, flat_top
import kit
from bkit import (door, entry, ground, tree, bush, hedge, fence, flowerbed, mailbox, lamp, bench, bins, box, slab,
                  post, canopy, steps, awning, glass_rail, parking_lot, sign_board, pole_sign, car_static, blade_sign)
from b_towers import solid_side

CAR_COLS = ["c84a3a", "2a6ab0", "f4f2ee", "3a3c42", "e8b830", "4a8a5a", "8a3a8a", "d86a2a"]


def _paint(col):
    return lambda u, v, LL, HH: (C(col) * np.ones(u.shape + (3,)), nores(u.shape), None)


def _ball(T, s, f, z, r, col, seed=0):
    x, y = T.pt(s, f)
    T.cv.ellipsoid(x, y, z, r, r, r, lambda wx, wy, wz, nx, ny, nz: (
        C(col) * (0.7 + 0.35 * nz)[..., None] * np.ones(wx.shape + (1,)), nores(wx.shape), None))


def _cars_row(T, s0, f, n, step=26, along="f", seed=0):
    for k in range(n):
        car_static(T, s0 + k * step, f, along, CAR_COLS[(k + seed) % len(CAR_COLS)])


def _small_shop(L, o, seed, text, wall, mat, sign_bg, sign_fg, roof=None, floors=1, H0=34, win_col="f2efe8"):
    """A one-plot shop: glazed front, a sign over it, optional upper floors and a roof."""
    cv = Canvas(1, 150)
    T = Orient(cv, o)
    s0, s1, f0, f1 = 18, 142, 44, 128
    H = H0 + (floors - 1) * 30
    upper = Win(w=14, h=16, sill=8, sp=26, margin=14, fh=30, frame=win_col, group="flats")
    fr = facade(mat, wall, win=upper if floors > 1 else None, shop=(10, 114, 26), doors=[(52, 16, 24, "glass")],
                seed=seed, plinth=("5a5652", 3), skip=[(0, 124, 0, H0)] if floors > 1 else ())
    sd = facade(mat, wall, win=Win(w=14, h=16, sill=8, sp=28, margin=16, fh=30, frame=win_col), seed=seed + 1, plinth=("5a5652", 3))
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("8e8c88", wall, 3))
    if roof:
        T.gable(s0 - 3, f0 - 3, s1 + 3, f1 + 3, H, 24, roof_mat(roof, "tiles"), dict(front=fr, back=sd, left=sd, right=sd), ridge="s", o=4)
    sign_board(T, (s0 + s1) / 2, f0, 27, text, 8, sign_bg, sign_fg)
    door(T, s0 + 52, 16, f0, 24)
    entry(T, s0 + 60)
    ground(T, 2, 2, 158, f0, kit.paving("c8c0b4", 8.0, seed))
    return cv, T, H


# ====================================================================== shops
def bookshop(L, o):
    """A bookshop in an old brick house: a green shop front with books on display, a blade sign, a reading bench,
    a cart of second-hand books outside; later a reading room upstairs."""
    cv, T, H = _small_shop(L, o, 1501, "BOOKS", "9a4a36", "brick", "1e4a3a", "f0d890", roof="4a4e58", floors=[1, 2, 2][L - 1])
    awning(T, 26, 134, 44, 34, 10, 5, "1e4a3a", "e8e0c8")
    # a cart of books
    T.box(110, 18, 140, 30, 4, 12, all=_paint("6a4a30"), top=lambda u, v, LL, D: (
        np.where((np.mod(u, 3) < 2.2)[..., None], np.array([C("c83a2a"), C("2a5aa8"), C("e8c050")])[(np.floor(u / 3) % 3).astype(int)],
                 C("3a2a20")) * np.ones(u.shape + (1,)), nores(u.shape), None))
    for s in (112, 138):
        post(T, s, 24, 0, 4, "3a3a40", 2)
    bench(T, 40, 20, "s", "1e4a3a")
    if L >= 3:
        lamp(T, 20, 14, "classic", 44)
    return cv


def barber(L, o):
    """A barber shop: a black-and-white front, a spinning red-white-blue barber pole, a chair in the window."""
    cv, T, H = _small_shop(L, o, 1511, "BARBER", "2a2a30", "tile", "f4f2ee", "1e1e22", floors=[1, 1, 2][L - 1], win_col="f4f2ee")

    def pole(a, z, nx, ny):
        k = np.mod(z * 0.8 + a * 2.5, 6)
        rgb = np.where((k < 2)[..., None], C("d8342a"), np.where((k < 4)[..., None], C("f8f8f8"), C("2a4ab0"))) * np.ones(a.shape + (1,))
        return rgb, nores(a.shape), None
    x, y = T.pt(24, 40)
    T.cv.cylinder(x, y, 3, 8, 30, pole, cap=lambda u, v: (C("d8d8dc") * np.ones(u.shape + (3,)), nores(u.shape), None))
    _ball(T, 24, 40, 31, 3, "e8e8ec")
    canopy(T, 60, 104, 44, 10, 26, "2a2a30", "1e1e22", posts=False)
    for s in (120, 136):
        x, y = T.pt(s, 20)
        T.cv.cylinder(x, y, 4, 0, 8, solid_side("2a2a30"))
        bush(T, s, 20, 0.45, s)
    if L >= 2:
        bench(T, 116, 30, "s", "2a2a30")
    return cv


def ice_cream(L, o):
    """An ice-cream parlour: a pastel pink-and-mint striped house with a giant cone on the roof,
    a scalloped awning and little tables with parasols."""
    cv, T, H = _small_shop(L, o, 1521, "ICE CREAM", "f8d8e4", "plaster", "4ac0a8", "ffffff")
    awning(T, 26, 134, 44, 33, 12, 6, "f08ab0", "f8f6f0", 8.0)
    # giant cone on the roof: a waffle cone and three scoops
    cx, cy = T.pt(80, 86)

    def waffle(a, z, nx, ny):
        g = (np.mod(a * 8 + z * 0.6, 3) < 0.6) | (np.mod(a * 8 - z * 0.6, 3) < 0.6)
        return np.where(g[..., None], C("a8703a"), C("e0a860")) * np.ones(a.shape + (1,)), nores(a.shape), None
    for i in range(10):
        r = 3 + i * 1.3
        T.cv.cylinder(cx, cy, r, H + i * 3, H + i * 3 + 3, waffle)
    for k, col in enumerate(("f8f0e0", "f08ab0", "8ad8b8")):
        T.cv.ellipsoid(cx + (k - 1) * 6, cy - (k - 1) * 6, H + 34 + (k == 1) * 6, 9, 9, 8, lambda wx, wy, wz, nx, ny, nz, c=col: (
            C(c) * (0.75 + 0.3 * nz)[..., None] * np.ones(wx.shape + (1,)), nores(wx.shape), None))
    _ball(T, 80, 86, H + 50, 2.5, "c8282a")
    for s, col in ((30, "8ad8b8"), (128, "f08ab0")):
        x, y = T.pt(s, 20)
        kit.umbrella_table(cv, x, y, col)
    return cv


def car_wash(L, o):
    """A car wash: a blue tunnel with big spinning brushes and a car inside, a pay pylon and a vacuum station."""
    cv = Canvas(1, 110)
    T = Orient(cv, o)
    seed = 1531
    ground(T, 2, 2, 158, 158, kit.asphalt_lot("5a5c62", 4))
    # the tunnel at the back: its front face is a dark opening with strip curtains, the sign above
    def mouth(u, v, LL, HH):
        rgb = np.broadcast_to(C("2a6ab0"), u.shape + (3,)).copy()
        hole = (u > 8) & (u < LL - 8) & (v < 30)
        rgb[hole] = np.where((np.mod(u[hole], 4) < 2)[..., None], C("1e2a3a"), C("3a5a7a")) * np.ones((1, 1))
        return rgb, hole, None
    wall = facade("metal", "2a6ab0", seed=seed, plinth=None)
    T.box(36, 90, 124, 150, 0, 40, front=mouth, back=wall, left=wall, right=wall, top=flat_top("d8dce0", "2a6ab0", 3, gravel=False))
    sign_board(T, 80, 90, 31, "CAR WASH", 6, "f4f6f8", "2a6ab0")
    # wash bay in front: a gantry with spray bars, two big spinning brushes and a soapy car between them
    ground(T, 40, 20, 120, 90, lambda u, v, LL, D: (np.where((hash2(np.floor(u / 2), np.floor(v / 2), 5) > 0.55)[..., None],
                                                            C("f4f8fc"), C("8ab0d0")) * np.ones(u.shape + (1,)), nores(u.shape), None), z=0.5)
    for s in (40, 120):
        post(T, s, 50, 0, 36, "d8dce0", 3)
    T.box(38, 48, 122, 52, 34, 38, all=_paint("d8dce0"), top=flat("e8e8ec"))
    car_static(T, 80, 62, "f", "c84a3a")
    for s, col in ((56, "e8342a"), (104, "2a8ae8")):
        x, y = T.pt(s, 40)
        T.cv.cylinder(x, y, 7, 2, 30, lambda a, z, nx, ny, c=col: (
            C(c) * (0.75 + 0.3 * (np.mod(a * 10 + z, 2) < 1))[..., None] * np.ones(a.shape + (1,)), nores(a.shape), None))
        _ball(T, s, 40, 31, 3, "d8dce0")
    for k in range(3):
        _ball(T, 70 + k * 10, 66 + k * 3, 16 + k * 2, 4, "f8fcff")
    pole_sign(T, 16, 20, 40, "WASH", 7, "2a6ab0", "ffffff")
    door(T, 64, 32, 90, 30)
    entry(T, 80)
    if L >= 2:
        # vacuum station: a post with a hose arm
        post(T, 140, 50, 0, 22, "e8b830", 3)
        T.box(140, 50, 152, 52, 20, 22, all=_paint("2a2a30"))
        car_static(T, 144, 90, "f", "f4f2ee")
    if L >= 3:
        pole_sign(T, 16, 120, 50, "24/7", 8, "e8b830", "1e1e22")
    return cv


def auto_repair(L, o):
    """An auto repair shop (garage): a wide workshop with two roller doors, one car up on a lift inside,
    tyre stacks, an oil drum and cars waiting on the forecourt."""
    cv = Canvas(1, 120)
    T = Orient(cv, o)
    seed = 1541
    fr = facade("concrete", "d8d4cc", doors=[(8, 44, 32, "shutter", "8a8c90"), (64, 44, 32, "garage", "e8b830")], seed=seed,
                plinth=None, bands=[(36, 40, "e8b830")])
    sd = facade("concrete", "d8d4cc", win=Win(w=16, h=10, sill=24, sp=30, margin=12, fh=40, frame="5a5c62"), seed=seed + 1, plinth=None)
    s0, s1, f0, f1 = 10, 130, 66, 150
    box(T, s0, f0, s1, f1, 0, 46, front=fr, back=sd, left=sd, right=sd, top=flat_top("8a8c90", "d8d4cc", 3))
    sign_board(T, (s0 + s1) / 2, f0, 47, "AUTO SERVICE", 6, "1e1e22", "e8b830")
    # inside the open door: a car up on the lift
    T.box(s0 + 14, f0 + 4, s0 + 48, f0 + 30, 0, 12, all=_paint("e8b830"), top=flat("3a3a40"))
    car_static(T, s0 + 31, f0 + 20, "s", "2a6ab0")
    door(T, s0 + 64, 44, f0, 32)
    entry(T, s0 + 86)
    ground(T, 2, 2, 158, f0, kit.asphalt_lot("62646a", 4))
    # tyre stacks and an oil drum
    for k, s in enumerate((140, 148)):
        x, y = T.pt(s, 76 + k * 12)
        for i in range(4):
            T.cv.cylinder(x, y, 5, i * 3, i * 3 + 3, solid_side("1e1e22"), cap=lambda u, v: (
                np.where((np.hypot(u, v) < 2.5)[..., None], C("5a5c62"), C("2a2a2e")) * np.ones(u.shape + (1,)), nores(u.shape), None))
    x, y = T.pt(142, 110)
    T.cv.cylinder(x, y, 5, 0, 13, solid_side("2a5ab8", ribs=3), cap=lambda u, v: (C("3a3a40") * np.ones(u.shape + (3,)), nores(u.shape), None))
    car_static(T, 40, 30, "s", "c84a3a")
    if L >= 2:
        car_static(T, 100, 30, "s", "4a8a5a")
    if L >= 3:
        pole_sign(T, 148, 20, 50, "TYRES", 7, "e8b830", "1e1e22")
    return cv


def car_dealer(L, o):
    """A car dealership: a glass showroom with shiny cars inside, a forecourt of new cars under flags
    and a tall brand pylon."""
    cv = Canvas(2, 150)
    T = Orient(cv, o)
    seed = 1551

    def glass(u, v, LL, HH):
        rgb = np.broadcast_to(C("8ab0c8"), u.shape + (3,)).copy()
        rgb += ((v / max(HH, 1)) * 30)[..., None]
        mull = (np.mod(u, 32) < 1.6) | (v < 2) | (v > HH - 3)
        rgb[mull] = C("d8dce0")
        em = np.zeros(u.shape + (4,))
        em[~mull] = np.array([235, 245, 255, 110.0])
        return rgb, nores(u.shape), em
    s0, s1, f0, f1 = 40, 300, 170, 300
    H = 46 if L < 3 else 72
    box(T, s0, f0, s1, f1, 0, H, front=glass, left=glass, right=facade("concrete", "e8e8ec", seed=seed, plinth=None),
        back=facade("concrete", "e8e8ec", seed=seed, plinth=None), top=flat_top("d8dce0", "2a2a30", 4))
    T.box(s0 - 4, f0 - 8, s1 + 4, f0 + 4, H, H + 4, all=_paint("2a2a30"), top=flat("2a2a30"))
    sign_board(T, (s0 + s1) / 2, f0 - 8, H - 2, "AUTO CITY", 10, "2a2a30", "f4f6f8")
    for k in range(4):
        car_static(T, s0 + 40 + k * 56, f0 + 40, "f", CAR_COLS[k])
    door(T, (s0 + s1) / 2 - 15, 30, f0, 30)
    entry(T, (s0 + s1) / 2)
    # forecourt with new cars in a row and bunting flags
    ground(T, 4, 4, 316, f0, kit.paving("d8dce0", 16.0, seed, 0.4))
    _cars_row(T, 40, 60, [3, 4, 5][L - 1], 50, "f", 2)
    for s in range(20, 300, 40):
        post(T, s, 120, 0, 34, "d8dce0", 1.4)
    for s in range(20, 260, 40):
        for i in range(6):
            col = ["e8342a", "2a6ae8", "e8b830"][(s // 40 + i) % 3]
            T.box(s + 4 + i * 6, 119, s + 8 + i * 6, 121, 26 - i * 0.6 - (i * (5 - i)) * 0.3, 30 - i * 0.6 - (i * (5 - i)) * 0.3,
                  all=_paint(col), top=flat(col))
    pole_sign(T, 300, 30, 80, "AC", 16, "2a2a30", "e8b830")
    tree(T, 20, 300, "maple", 0.8, seed)
    return cv


# ====================================================================== services
def police_post(L, o):
    """A small police post: a white-and-blue cabin with a light bar on the roof, a barrier, a patrol car and a flag."""
    cv = Canvas(1, 110)
    T = Orient(cv, o)
    seed = 1561
    fr = facade("plaster", "f4f6f8", win=Win(w=18, h=16, sill=10, sp=34, margin=18, fh=30, frame="2a4a9a", group="work"),
                doors=[(56, 12, 24, "glass")], seed=seed, plinth=("2a4a9a", 6), bands=[(26, 30, "2a4a9a")])
    sd = facade("plaster", "f4f6f8", win=Win(w=18, h=16, sill=10, sp=34, margin=18, fh=30, frame="2a4a9a", group="work"), seed=seed + 1,
                plinth=("2a4a9a", 6), bands=[(26, 30, "2a4a9a")])
    s0, s1, f0, f1 = 30, 130, 56, 118
    box(T, s0, f0, s1, f1, 0, 34, front=fr, back=sd, left=sd, right=sd, top=flat_top("8a8c90", "f4f6f8", 3))
    sign_board(T, (s0 + s1) / 2, f0, 35, "POLICE", 7, "2a4a9a", "ffffff")
    # light bar on the roof
    T.box(70, 80, 80, 90, 34, 40, all=lambda u, v, LL, HH: glow_res("e8342a", u.shape), top=flat("e8342a"))
    T.box(80, 80, 90, 90, 34, 40, all=lambda u, v, LL, HH: glow_res("3a6ae8", u.shape), top=flat("3a6ae8"))
    door(T, s0 + 56, 12, f0, 24)
    entry(T, s0 + 62)
    ground(T, 2, 2, 158, f0, kit.paving("c8ccd0", 8.0, seed))
    # barrier arm, red and white
    post(T, 140, 30, 0, 12, "f4f6f8", 3)
    T.panel(100, 140, 30, 10, 13, lambda u, v, LL, HH: (np.where((np.mod(u, 8) < 4)[..., None], C("e8342a"), C("f8f8f8"))
                                                       * np.ones(u.shape + (1,)), nores(u.shape), None), "s")
    # flag pole
    post(T, 16, 40, 0, 60, "d8dce0", 1.6)
    T.panel(40, 56, 17, 46, 58, lambda u, v, LL, HH: (np.where((v > 8)[..., None], C("f8f8f8"), np.where((v > 4)[..., None], C("2a4ab0"),
                                                       C("d8342a"))) * np.ones(u.shape + (1,)), nores(u.shape), None), "f")
    if L >= 2:
        car_static(T, 120, 136, "s", "f4f6f8")
        T.box(116, 132, 124, 140, 14, 16, all=lambda u, v, LL, HH: glow_res("3a6ae8", u.shape), top=flat("3a6ae8"))
    if L >= 3:
        lamp(T, 24, 10, "modern", 46)
    return cv


def clinic(L, o):
    """A neighbourhood clinic: a light green two-storey house with a glowing red cross, a ramp to the door,
    a canopy for the ambulance and a bench under a tree."""
    cv = Canvas(1, 120)
    T = Orient(cv, o)
    seed = 1571
    wall = "e8f4ec"
    win = Win(w=16, h=16, sill=8, sp=28, margin=12, fh=30, frame="2a8a5a", group="work")
    fr = facade("plaster", wall, win=win, doors=[(40, 18, 24, "double_glass")], seed=seed, plinth=("8a9a90", 4))
    sd = facade("plaster", wall, win=win, seed=seed + 1, plinth=("8a9a90", 4))
    s0, s1, f0, f1 = 20, 130, 54, 136
    H = 30 * [1, 2, 2][L - 1] + 4
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("8e8c88", wall, 3))
    cross = lambda u, v, LL, HH: glow_res("e8342a", u.shape)
    z = H - 16
    T.box(s1 - 22, f0 - 2, s1 - 6, f0, z + 5, z + 10, all=cross, top=flat("e8342a"))
    T.box(s1 - 16.5, f0 - 2, s1 - 11.5, f0, z, z + 15, all=cross, top=flat("e8342a"))
    canopy(T, s0 + 34, s0 + 64, f0, 18, 28, "f4f6f8", "2a8a5a")
    # ramp to the door
    T.box(s0 + 64, f0 - 18, s0 + 80, f0, 0, 3, all=flat("c8ccd0"), top=flat("d8dce0"))
    door(T, s0 + 40, 18, f0, 24)
    entry(T, s0 + 49)
    ground(T, 2, 2, 158, f0, kit.paving("d8dce0", 8.0, seed))
    tree(T, 140, 20, "maple", 0.75, seed)
    bench(T, 120, 24, "s", "2a8a5a")
    if L >= 2:
        car_static(T, 30, 24, "s", "f4f6f8")
        T.box(26, 20, 34, 28, 14, 16, all=lambda u, v, LL, HH: glow_res("e8342a", u.shape), top=flat("e8342a"))
    return cv


# ====================================================================== leisure
def bowling(L, o):
    """A bowling alley: a long purple hall with a giant bowling pin and ball on the roof and neon BOWLING letters."""
    cv = Canvas(2, 150)
    T = Orient(cv, o)
    seed = 1581
    wall = "4a2a6a"
    fr = facade("concrete", wall, shop=(60, 200, 28), doors=[(116, 30, 26, "double_glass")], seed=seed, plinth=None,
                bands=[(40, 44, "e8b830")])
    sd = facade("concrete", wall, seed=seed + 1, plinth=None, bands=[(40, 44, "e8b830")])
    s0, s1, f0, f1 = 20, 300, 130, 300
    H = 50
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("6a6c72", wall, 4))
    sign_board(T, (s0 + s1) / 2, f0, H - 2, "BOWLING", 12, "1e1a28", "f08ab0")
    # the giant pin: stacked white rings with a red neck band
    x, y = T.pt(80, 210)
    prof = [(0, 7), (4, 10), (8, 12), (12, 12), (16, 10), (20, 7), (24, 5), (28, 5), (32, 7), (36, 8), (40, 7), (44, 4)]
    for z0, r in prof:
        col = "d8342a" if z0 in (24, 28) else "f8f6f2"
        T.cv.cylinder(x, y, r, H + z0, H + z0 + 4, solid_side(col))
    _ball(T, 80, 210, H + 50, 4, "f8f6f2")
    # the ball
    bx, by = T.pt(140, 230)
    T.cv.ellipsoid(bx, by, H + 14, 14, 14, 14, lambda wx, wy, wz, nx, ny, nz: (
        np.where(((nx - 0.2) ** 2 + (nz - 0.5) ** 2 < 0.02)[..., None], C("1e1e22"), C("2a5ad8"))
        * (0.7 + 0.35 * nz)[..., None] * np.ones(wx.shape + (1,)), nores(wx.shape), None))
    door(T, s0 + 116, 30, f0, 26)
    entry(T, s0 + 131)
    parking_lot(T, 4, 4, 316, f0 - 20)
    _cars_row(T, 40, 60, [2, 3, 4][L - 1], 60, "f", 3)
    for s in (12, 308):
        lamp(T, s, f0 - 14, "modern", 50)
    return cv


def mini_golf(L, o):
    """Mini golf: nine little green holes with obstacles (a windmill, a loop, a bridge), flags and a ticket hut."""
    cv = Canvas(2, 100)
    T = Orient(cv, o)
    seed = 1591
    ground(T, 2, 2, 318, 318, kit.paving("d8d0c0", 12.0, seed))

    def green(u, v, LL, D):
        rgb = np.broadcast_to(C("4aa85a"), u.shape + (3,)).copy()
        rgb *= (0.94 + 0.08 * (np.mod(u + v, 8) < 4))[..., None]
        rim = (u < 2) | (v < 2) | (u > LL - 2) | (v > D - 2)
        rgb[rim] = C("f4f2ee")
        return rgb, nores(u.shape), None
    holes = [(20, 40, 110, 80), (130, 40, 220, 80), (240, 40, 300, 140), (20, 110, 80, 220), (110, 110, 210, 150),
             (110, 180, 210, 220), (240, 170, 300, 300), (20, 250, 120, 300), (140, 250, 220, 300)]
    for k, (a0, b0, a1, b1) in enumerate(holes[:[6, 8, 9][L - 1]]):
        T.box(a0, b0, a1, b1, 0, 3, all=_paint("f4f2ee"), top=green)
        hx, hf = a1 - 10, (b0 + b1) / 2
        post(T, hx, hf, 3, 20, "f4f2ee", 0.8)
        col = ["e8342a", "e8b830", "2a6ae8"][k % 3]
        T.box(hx, hf - 0.5, hx + 7, hf + 0.5, 15, 20, all=_paint(col), top=flat(col))
    # windmill obstacle on hole 1
    T.box(56, 52, 72, 68, 3, 26, all=_paint("c8342a"), top=flat("c8342a"))
    T.gable(54, 50, 74, 70, 26, 8, roof_mat("4a4e58", "tiles"), _paint("c8342a"), ridge="s", o=1)
    for a in range(4):
        ang = a * np.pi / 2 + 0.4
        T.box(64 + 9 * np.cos(ang) - 2, 49, 64 + 9 * np.cos(ang) + 2, 51, 22 + 9 * np.sin(ang) - 2, 22 + 9 * np.sin(ang) + 2,
              all=_paint("f4f2ee"))
    # a loop on hole 5: a ring standing up
    T.panel(150, 170, 130, 3, 22, _paint("e8b830"), "s", lambda u, v: np.hypot(u - 10, v - 10) > 8.5)
    # ticket hut
    hut = facade("wood", "f4d080", doors=[(8, 10, 20, "glass")], seed=seed + 1, plinth=None)
    T.box(240, 220, 290, 250, 0, 24, all=hut)
    T.gable(236, 216, 294, 254, 24, 10, roof_mat("4ab0a0", "metal"), hut, ridge="s", o=2)
    sign_board(T, 265, 220, 24, "MINI GOLF", 5, "2a6a3a", "ffffff")
    door(T, 248, 10, 220, 20)
    entry(T, 160)
    for s in (100, 230):
        tree(T, s, 240, "maple", 0.6, seed + s)
    return cv


def open_stage(L, o):
    """An open-air stage: a shell-shaped arched roof over the stage, speaker stacks, coloured spot lights,
    rows of benches for the audience and food stands."""
    cv = Canvas(2, 150)
    T = Orient(cv, o)
    seed = 1601
    ground(T, 2, 2, 318, 318, kit.lawn_stripes(seed))
    # stage platform at the back, facing the front
    slab(T, 60, 210, 260, 290, 0, 10, "6a4a30", lambda u, v, LL, D: (
        C("8a6040") * (1 - 0.12 * (np.mod(u, 6) < 0.8))[..., None] * np.ones(u.shape + (1,)), nores(u.shape), None))
    # the shell roof: arched ribs stepping back
    for i in range(6):
        h = 70 - i * 6
        w = 110 - i * 8
        T.panel(160 - w, 160 + w, 250 + i * 8, 10 + h - 6, 10 + h, _paint("f4f2ee" if i % 2 == 0 else "e8e4dc"), "s")
        T.box(160 - w, 250 + i * 8, 160 - w + 4, 258 + i * 8, 10, 10 + h, all=_paint("f4f2ee"))
        T.box(160 + w - 4, 250 + i * 8, 160 + w, 258 + i * 8, 10, 10 + h, all=_paint("f4f2ee"))
    T.box(50, 290, 270, 298, 0, 76, all=_paint("2a2a30"), top=flat("2a2a30"))
    # speakers
    for s in (66, 240):
        T.box(s, 214, s + 16, 228, 10, 40, all=lambda u, v, LL, HH: (np.where((np.hypot(np.mod(u, 8) - 4, np.mod(v, 10) - 5) < 3)[..., None],
                                                                              C("4a4a52"), C("1e1e22")) * np.ones(u.shape + (1,)), nores(u.shape), None),
              top=flat("1e1e22"))
    # coloured spot lights on the front rib
    for k, s in enumerate(range(80, 250, 24)):
        col = ["e8342a", "2a6ae8", "e8b830", "4ac87a", "c84ae8"][k % 5]
        T.box(s, 246, s + 6, 250, 70, 76, all=lambda u, v, LL, HH, c=col: glow_res(c, u.shape), top=flat("2a2a30"))
    # audience benches
    for r in range(4 if L < 3 else 6):
        for s0_ in (40, 170):
            slab(T, s0_, 30 + r * 26, s0_ + 110, 38 + r * 26, 0, 6, "8a5a34")
    entry(T, 160)
    door(T, 145, 30, 210, 30)
    if L >= 2:
        stand = facade("wood", "f4d080", seed=seed + 2, plinth=None)
        T.box(286, 40, 314, 80, 0, 22, all=stand)
        awning(T, 286, 314, 40, 24, 8, 4, "e8342a", "f8f6f0")
        T.box(286, 100, 314, 140, 0, 22, all=stand)
        awning(T, 286, 314, 100, 24, 8, 4, "2a8ae8", "f8f6f0")
    for s in (16, 304):
        tree(T, s, 260, "maple", 0.8, seed + s)
    return cv


def skate_park(L, o):
    """A skate park: a concrete bowl, a half-pipe with coping, a grind rail and funbox, graffiti on a wall."""
    cv = Canvas(2, 100)
    T = Orient(cv, o)
    seed = 1611
    ground(T, 2, 2, 318, 318, kit.paving("b8b8b4", 40.0, seed, 0.3))
    # half-pipe: two curved ramps made of steps, a flat bottom
    for i in range(10):
        z = 28 * (1 - np.cos(i / 9 * np.pi / 2))
        for f0 in (180 + i * 4, 290 - i * 4):
            T.box(40, f0, 200, f0 + 4, 0, z + 2, all=_paint("c8c8c4"), top=flat("d0d0cc"))
    for f in (218, 252):
        T.box(40, f - 1.5, 200, f + 1.5, 30, 32, all=_paint("8a8c90"), top=flat("a8acb0"))
    # graffiti wall at the back
    def graffiti(u, v, LL, HH):
        h = hash2(np.floor(u / 10), np.floor(v / 8), 3)
        cols = np.array([C("e8342a"), C("2a8ae8"), C("e8b830"), C("4ac87a"), C("c84ae8")])
        rgb = cols[(h * 5).astype(int) % 5].copy()
        blob = np.hypot(np.mod(u, 20) - 10, np.mod(v, 16) - 8) < 6 + 2 * h
        rgb[~blob] = C("b8b8b4")
        return rgb, nores(u.shape), None
    T.box(30, 300, 290, 308, 0, 24, front=graffiti, all=_paint("b8b8b4"), top=flat("a8a8a4"))
    # grind rail and funbox
    T.box(230, 60, 236, 160, 0, 4, all=_paint("8a8c90"))
    for f in (64, 156):
        post(T, 233, f, 0, 10, "4a4c52", 1.6)
    T.box(232, 60, 234, 160, 10, 11.5, all=_paint("e8b830"), top=flat("e8b830"))
    # funbox with a ramp on each side
    slab(T, 80, 60, 160, 110, 0, 12, "c8c8c4")
    for i in range(5):
        T.box(80 - (i + 1) * 4, 60, 80 - i * 4, 110, 0, 12 - (i + 1) * 2.4, all=_paint("c8c8c4"), top=flat("d0d0cc"))
        T.box(160 + i * 4, 60, 160 + (i + 1) * 4, 110, 0, 12 - (i + 1) * 2.4, all=_paint("c8c8c4"), top=flat("d0d0cc"))
    entry(T, 160)
    door(T, 150, 20, 4, 20)
    if L >= 2:
        # a concrete bowl
        bx, by = T.pt(270, 230)
        T.cv.cylinder(bx, by, 24, 0, 2, solid_side("a8a8a4"), cap=lambda u, v: (
            C("c8c8c4") * (0.7 + 0.3 * np.clip(np.hypot(u, v) / 24, 0, 1))[..., None] * np.ones(u.shape + (1,)),
            nores(u.shape), None))
    if L >= 3:
        for s in (14, 306):
            lamp(T, s, 20, "modern", 50)
    tree(T, 300, 40, "maple", 0.7, seed)
    return cv


# ====================================================================== decoration
def gazebo(L, o):
    """A white wooden gazebo: an octagonal pavilion on a stone base with a pointed roof, benches inside,
    climbing roses and a gravel path."""
    cv = Canvas(1, 110)
    T = Orient(cv, o)
    seed = 1621
    ground(T, 2, 2, 158, 158, kit.lawn_stripes(seed))
    ground(T, 70, 0, 90, 50, kit.gravel("d8d0c0"))
    cx, cy = T.pt(80, 86)
    T.cv.cylinder(cx, cy, 40, 0, 5, solid_side("b8b0a4"), cap=lambda u, v: (C("d8d0c4") * np.ones(u.shape + (3,)), nores(u.shape), None))
    for k in range(8):
        a = k * np.pi / 4 + np.pi / 8
        x, y = cx + 34 * np.cos(a), cy + 34 * np.sin(a)
        T.cv.cylinder(x, y, 1.6, 5, 36, solid_side("f8f6f2"))
    T.cv.cylinder(cx, cy, 38, 36, 40, solid_side("f8f6f2"), cap=lambda u, v: (C("f8f6f2") * np.ones(u.shape + (3,)), nores(u.shape), None))
    roof = ["4a7a5a", "8a3a2a", "3a5a8a"][L - 1]
    for i in range(12):
        T.cv.cylinder(cx, cy, 40 - i * 3.3, 40 + i * 2.2, 42.2 + i * 2.2, solid_side(roof),
                      cap=lambda u, v: (C(roof) * np.ones(u.shape + (3,)), nores(u.shape), None))
    T.cv.cylinder(cx, cy, 1.4, 66, 76, solid_side("e8c050"))
    # benches inside, a round table
    T.cv.cylinder(cx, cy, 8, 5, 13, solid_side("8a5a34"), cap=lambda u, v: (C("9a6a40") * np.ones(u.shape + (3,)), nores(u.shape), None))
    door(T, 70, 20, 50, 30)
    entry(T, 80)
    for s, f in ((30, 50), (130, 50)):
        bush(T, s, f, 0.7, seed + s, "e85a7a")
    if L >= 2:
        flowerbed(T, 20, 10, 60, 24, seed)
        flowerbed(T, 100, 10, 140, 24, seed + 1)
    if L >= 3:
        lamp(T, 64, 30, "lantern", 34)
        lamp(T, 96, 30, "lantern", 34, "light2")
    return cv


def clock_tower(L, o):
    """A town clock tower: a slim brick tower with four big clock faces that glow at night,
    a little copper spire and a bell under arches."""
    cv = Canvas(1, 220)
    T = Orient(cv, o)
    seed = 1631
    ground(T, 20, 20, 140, 140, kit.paving("c8bcaa", 10.0, seed))
    brick = facade("brick", "a85a40", seed=seed, plinth=("8a8478", 8), bands=[(60, 63, "e8e0d0"), (100, 103, "e8e0d0")])
    T.box(58, 58, 102, 102, 0, 120, all=brick, top=flat("8a8478"))

    def clock(u, v, LL, HH):
        cu, cvv = u - LL / 2, v - HH / 2
        r = np.hypot(cu, cvv)
        rgb = np.broadcast_to(C("e8e0d0"), u.shape + (3,)).copy()
        face = r < 15
        rgb[face] = C("f8f4e0")
        ring = (r > 13.5) & (r < 15)
        rgb[ring] = C("2a2a30")
        ang = np.arctan2(cvv, cu)
        ticks = face & (r > 11) & (np.mod(ang * 6 / np.pi + 0.1, 1) < 0.2)
        rgb[ticks] = C("2a2a30")
        hands = face & (((np.abs(cu) < 1) & (cvv > 0) & (cvv < 11)) | ((np.abs(cvv) < 1) & (cu > 0) & (cu < 8)))
        rgb[hands] = C("1e1e22")
        em = np.zeros(u.shape + (4,))
        em[face & ~ring & ~ticks & ~hands] = np.array([255, 240, 200, 200.0])
        return rgb, face, em
    T.box(56, 56, 104, 104, 120, 156, all=clock, top=flat("e8e0d0"))
    # belfry with arches
    T.box(60, 60, 100, 100, 156, 182, all=lambda u, v, LL, HH: (C("a85a40") * np.ones(u.shape + (3,)), nores(u.shape), None),
          top=flat("8a8478"))
    T.panel(60, 100, 59.5, 160, 178, _paint("2a2a30"), "s", lambda u, v: ~((np.mod(u, 13) > 3) & (v < 14 - np.maximum(0, np.abs(np.mod(u, 13) - 8) - 2))))
    T.hip(56, 56, 104, 104, 182, 36, roof_mat("4a9a8a", "metal"), o=2)
    _ball(T, 80, 80, 222, 2.5, "e8c050")
    door(T, 72, 16, 58, 26)
    entry(T, 80)
    for s in (30, 130):
        bench(T, s, 40, "f", "2a4a3a")
    if L >= 2:
        flowerbed(T, 24, 110, 56, 136, seed)
        flowerbed(T, 104, 110, 136, 136, seed + 1)
    if L >= 3:
        for s in (24, 136):
            lamp(T, s, 24, "classic", 44)
    return cv


def flag_pole(L, o):
    """A flag square: a tall white flagpole with a big flag in the wind on a round stone base, flower rings
    and smaller flags around it."""
    cv = Canvas(1, 200)
    T = Orient(cv, o)
    seed = 1641
    ground(T, 10, 10, 150, 150, kit.paving("d8d0c0", 10.0, seed))
    cx, cy = T.pt(80, 80)
    T.cv.cylinder(cx, cy, 30, 0, 4, solid_side("b8b0a4"), cap=lambda u, v: (C("c8c0b4") * np.ones(u.shape + (3,)), nores(u.shape), None))
    T.cv.cylinder(cx, cy, 14, 4, 10, solid_side("9a948a"), cap=lambda u, v: (C("aaa49a") * np.ones(u.shape + (3,)), nores(u.shape), None))
    T.cv.cylinder(cx, cy, 1.8, 10, 190, solid_side("f4f4f4"))
    _ball(T, 80, 80, 192, 3, "e8c050")

    def flag(u, v, LL, HH):
        # three stripes: red, white with a gold crown, green
        rgb = np.where((v > HH * 0.7)[..., None], C("d8342a"), np.where((v > HH * 0.3)[..., None], C("f8f8f8"), C("2a8a4a"))) * np.ones(u.shape + (1,))
        crown = (v > HH * 0.42) & (v < HH * 0.58) & (np.abs(u - LL * 0.45) < 5)
        rgb[crown] = C("e8b830")
        rgb *= (0.88 + 0.14 * np.sin(u / 6))[..., None]
        return rgb, nores(u.shape), None
    T.panel(82, 140, 80, 150, 188, flag, "s")
    if L >= 2:
        for k in range(6):
            a = k * np.pi / 3
            x, y = cx + 26 * np.cos(a), cy + 26 * np.sin(a)
            T.cv.cylinder(x, y, 4, 4, 8, solid_side("7a5a3a"))
            kit.bush(cv, x, y, 0.35, seed + k, ["e8342a", "f4f4f4", "2a8a4a"][k % 3])
    if L >= 3:
        for s in (20, 140):
            post(T, s, 20, 0, 60, "f4f4f4", 1.2)
            T.panel(20, 40, s, 46, 58, lambda u, v, LL, HH: (np.where((np.mod(u, 10) < 5)[..., None], C("2a8a4a"), C("f8f8f8")) * np.ones(u.shape + (1,)),
                                                             nores(u.shape), None), "f")
    entry(T, 80)
    door(T, 70, 20, 50, 20)
    return cv


def art_sculpture(L, o):
    """A modern art sculpture: a big mirror-steel ring twisted like a ribbon on a dark plinth, coloured cubes
    around it and a reflecting pool."""
    cv = Canvas(1, 160)
    T = Orient(cv, o)
    seed = 1651
    ground(T, 10, 10, 150, 150, kit.paving("e8e8ea", 20.0, seed, 0.4))
    slab(T, 40, 40, 120, 120, 0, 10, "2a2a30")
    cx, cy = T.pt(80, 80)

    def steel(wx, wy, wz, nx, ny, nz):
        k = 0.55 + 0.45 * np.abs(ny) + 0.3 * np.clip(nz, 0, 1)
        rgb = np.stack([180 * k + 40, 200 * k + 40, 220 * k + 30], -1)
        return rgb, nores(wx.shape), None
    for i in range(36):
        a = i / 36 * 2 * np.pi
        tw = 0.6 + 0.4 * np.cos(a * 2)
        x = cx + 40 * np.cos(a) * tw
        y = cy + 40 * np.cos(a) * (1 - tw) * 0.6
        z = 64 + 50 * np.sin(a)
        T.cv.ellipsoid(x, y, z, 7, 7, 7, steel)
    for k, (s, f, col) in enumerate(((22, 22, "e8342a"), (138, 30, "2a6ae8"), (26, 138, "e8b830"))):
        T.box(s - 9, f - 9, s + 9, f + 9, 0, 18, all=_paint(col), top=flat(col))
    if L >= 2:
        x0, y0, x1, y1 = T.rect(116, 100, 150, 150)
        kit.pool(cv, x0, y0, x1, y1)
    if L >= 3:
        for s in (20, 140):
            lamp(T, s, 80, "modern", 40)
    entry(T, 80)
    door(T, 70, 20, 50, 20)
    return cv


def bike_rental(L, o):
    """A bike-sharing station: a green docking rack with a row of rental bikes, a payment totem with a screen,
    a canopy with solar panels."""
    cv = Canvas(1, 90)
    T = Orient(cv, o)
    seed = 1661
    ground(T, 6, 6, 154, 154, kit.paving("c8ccd0", 10.0, seed))
    # canopy on two posts with solar panels
    for s in (24, 136):
        post(T, s, 110, 0, 34, "4a4c52", 2.4)
    slab(T, 16, 80, 144, 130, 34, 36, "4a4c52")
    x0, y0, x1, y1 = T.rect(18, 82, 142, 128)
    kit.solar(cv, x0, y0, x1, y1, 36, 3)
    # the docking rail and bikes
    T.box(20, 98, 140, 101, 0, 6, all=_paint("3a9a5a"), top=flat("3a9a5a"))
    n = [5, 7, 9][L - 1]
    for k in range(n):
        s = 26 + k * 13
        x, y = T.pt(s, 92)
        kit.parked_bike(cv, x, y)
        T.box(s - 1, 96, s + 1, 98, 0, 10, all=_paint("3a9a5a"))
    # payment totem
    T.box(144, 60, 152, 66, 0, 30, all=lambda u, v, LL, HH: (np.where(((v > 16) & (v < 26) & (u > 1) & (u < LL - 1))[..., None],
                                                                     C("8ad8f8"), C("3a9a5a")) * np.ones(u.shape + (1,)), nores(u.shape),
                                                            np.where(((v > 16) & (v < 26))[..., None], np.array([140, 220, 255, 180.0]), 0.0)
                                                            * np.ones(u.shape + (1,))), top=flat("3a9a5a"))
    pole_sign(T, 20, 30, 40, "BIKE", 7, "3a9a5a", "ffffff")
    entry(T, 80)
    door(T, 70, 20, 60, 20)
    bush(T, 120, 30, 0.6, seed)
    return cv


def picnic(L, o):
    """A picnic spot: wooden tables with benches on the grass, a brick barbecue with smoke, a striped blanket
    with a basket and shady trees."""
    cv = Canvas(1, 100)
    T = Orient(cv, o)
    seed = 1671
    ground(T, 2, 2, 158, 158, kit.lawn_stripes(seed))
    for s, f in ((40, 50), (110, 100)):
        slab(T, s - 16, f - 8, s + 16, f + 8, 10, 12, "9a6a40")
        for d in (-12, 12):
            post(T, s + d, f, 0, 10, "7a5034", 2)
        for d in (-13, 13):
            slab(T, s - 16, f + d - 2.5, s + 16, f + d + 2.5, 5, 7, "8a5a34")
    # brick barbecue with a glowing grill
    T.box(110, 30, 136, 44, 0, 14, all=facade("brick", "a85a40", seed=seed, plinth=None), top=lambda u, v, LL, D: (
        np.where((np.mod(u, 3) < 1)[..., None], C("2a2a2e"), C("e86a2a")) * np.ones(u.shape + (1,)), nores(u.shape),
        np.where((np.mod(u, 3) >= 1)[..., None], np.array([255, 120, 40, 180.0]), 0.0) * np.ones(u.shape + (1,))))
    # striped blanket
    T.flat(30, 100, 70, 130, 0.6, lambda u, v, LL, D: (np.where((np.mod(u, 8) < 4)[..., None], C("d8342a"), C("f8f4ec"))
                                                         * np.ones(u.shape + (1,)), nores(u.shape), None))
    T.box(44, 108, 54, 116, 0.6, 7, all=_paint("c8a060"), top=flat("a87a40"))
    tree(T, 140, 140, "oak", 0.9, seed)
    tree(T, 18, 140, "maple", 0.8, seed + 1)
    if L >= 2:
        bins(T, 150, 20)
        x, y = T.pt(84, 140)
        kit.umbrella_table(cv, x, y, "4ab0a0")
    if L >= 3:
        lamp(T, 80, 14, "lantern", 32)
    entry(T, 80)
    door(T, 70, 20, 20, 20)
    return cv


# ====================================================================== industry
def textile_mill(L, o):
    """A textile mill: a long red-brick hall with a saw-tooth roof of north lights, a tall chimney,
    bales of cotton and rolls of bright cloth in the yard, a delivery truck."""
    cv = Canvas(2, 200)
    T = Orient(cv, o)
    seed = 1681
    win = Win(w=16, h=22, sill=8, sp=24, margin=12, fh=40, frame="e8e0d0", arch=True, group="work")
    fr = facade("brick", "a04a36", win=win, doors=[(100, 30, 30, "shutter", "5a5c62")], seed=seed, plinth=("5a5652", 5))
    sd = facade("brick", "a04a36", win=win, seed=seed + 1, plinth=("5a5652", 5))
    s0, s1, f0, f1 = 20, 300, 140, 300
    H = 46
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat("6a6c72"))
    # saw-tooth roof: glass on one slope, slate on the other
    for f in range(f0, f1, 32):
        T.gable(s0, f, s1, f + 32, H, 18, roof_mat("4a4e58", "slate"), _paint("8ab0c8"), ridge="s", o=0)
    cx, cy = T.pt(280, 280)
    T.cv.cylinder(cx, cy, 9, 0, 150, solid_side("a04a36", ribs=30))
    T.cv.cylinder(cx, cy, 10.5, 140, 150, solid_side("2a2a30"))
    sign_board(T, 160, f0, 34, "TEXTILE", 8, "e8e0d0", "a04a36")
    door(T, s0 + 100, 30, f0, 30)
    entry(T, s0 + 115)
    ground(T, 4, 4, 316, f0, kit.asphalt_lot("62646a", 4))
    # cotton bales and cloth rolls
    for k in range(5):
        T.box(20 + k * 22, 90, 38 + k * 22, 110, 0, 14, all=_paint("f4f2ec"), top=flat("ece8de"))
    for k, col in enumerate(("d8342a", "2a6ae8", "e8b830", "4ac87a", "c84ae8", "f08ab0")[:[3, 5, 6][L - 1]]):
        x, y = T.pt(200 + k * 16, 100)
        T.cv.cylinder(x, y, 6, 0, 26, solid_side(col))
    car_static(T, 240, 40, "s", "f4f2ee")
    return cv


def car_plant(L, o):
    """A car plant: a huge white assembly hall with the logo, a glass office block, a test track with a car on it,
    a yard full of new cars in rows and a transporter truck."""
    cv = Canvas(3, 150)
    T = Orient(cv, o)
    seed = 1691
    wall = "eef0f2"
    hall = facade("metal", wall, seed=seed, plinth=None, bands=[(50, 56, "2a5ab8")], doors=[(40, 60, 40, "shutter", "8a8c90")])
    box(T, 40, 220, 440, 460, 0, 70, all=hall, top=flat_top("c8ccd0", wall, 4))
    if L >= 2:
        x0, y0, x1, y1 = T.rect(60, 240, 420, 440)
        kit.solar(cv, x0, y0, x1, y1, 70, 4)
    sign_board(T, 300, 220, 58, "AUTO CITY", 9, "2a5ab8", "ffffff")
    # glass office block on the front corner
    off = facade("concrete", "d8dce0", win=Win(w=28, h=22, sill=4, sp=32, margin=6, fh=30, frame="2a2a30", style="vertical",
                                               tint="6a8aa8", group="work"), doors=[(20, 20, 26, "double_glass")], seed=seed + 1, plinth=None)
    box(T, 40, 150, 160, 220, 0, 90, all=off, top=flat_top("8a8c90", "d8dce0", 3))
    door(T, 60, 20, 150, 26)
    entry(T, 70)
    # test track: an oval of asphalt with a car on it
    ground(T, 200, 20, 460, 200, lambda u, v, LL, D: (np.where(
        (np.abs(np.hypot((u - LL / 2) / (LL / 2 - 10), (v - D / 2) / (D / 2 - 10)) - 0.82) < 0.12)[..., None],
        C("4a4c52"), C("6aa04a")) * np.ones(u.shape + (1,)), nores(u.shape), None))
    car_static(T, 330, 36, "s", "e8342a")
    # yard of new cars
    ground(T, 20, 20, 190, 140, kit.asphalt_lot("62646a", 4))
    for r in range(3):
        _cars_row(T, 40, 40 + r * 34, [3, 5, 6][L - 1], 28, "f", r)
    # car transporter: a cab and a two-deck trailer with cars
    T.box(180, 176, 206, 200, 3, 26, all=_paint("2a5ab8"), top=flat("2a5ab8"))
    T.box(206, 178, 330, 198, 3, 7, all=_paint("4a4c52"), top=flat("5a5c62"))
    T.box(206, 178, 330, 198, 22, 24, all=_paint("4a4c52"), top=flat("5a5c62"))
    for k in range(3):
        car_static(T, 226 + k * 40, 188, "s", CAR_COLS[k + 3])
    return cv


BUILDERS = {"bookshop": bookshop, "barber": barber, "ice_cream": ice_cream, "car_wash": car_wash, "auto_repair": auto_repair,
            "car_dealer": car_dealer, "police_post": police_post, "clinic": clinic, "bowling": bowling, "mini_golf": mini_golf,
            "open_stage": open_stage, "skate_park": skate_park, "gazebo": gazebo, "clock_tower": clock_tower, "flag_pole": flag_pole,
            "art_sculpture": art_sculpture, "bike_rental": bike_rental, "picnic": picnic, "textile_mill": textile_mill,
            "car_plant": car_plant}
