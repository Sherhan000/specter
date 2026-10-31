"""Cheap starter homes, each with its own look: a log izba, an adobe village house, a brick cottage, an A-frame cabin,
a shipping-container house, a whitewashed Mediterranean house and a two-family duplex. builder(L, o) -> Canvas."""
import numpy as np

from raster import C, U, Canvas, flat, nores, hash2, glow_res
from arch import Orient, facade, Win, roof_mat, flat_top
import kit
from bkit import (door, entry, ground, tree, bush, hedge, fence, flowerbed, mailbox, lamp, bench, bins, box, slab,
                  post, canopy, steps, glass_rail)
from b_towers import solid_side


def _logs(fn, col, d=4.0):
    """Round horizontal logs over a facade: shade the bare wall in bands, leave windows and doors alone."""
    base = C(col)

    def g(u, v, L, H):
        out = fn(u, v, L, H)
        rgb = out[0]
        wall = np.all(np.abs(rgb - base) < 34, axis=-1) & ~out[1]
        t = np.mod(v, d) / d
        k = 0.72 + 0.34 * np.sin(np.pi * t)
        k = k * (0.94 + 0.1 * hash2(np.floor(u / 30), np.floor(v / d), 9))
        rgb = rgb.copy()
        rgb[wall] *= k[wall][..., None]
        return (rgb,) + tuple(out[1:])
    if hasattr(fn, "doors"):
        g.doors = fn.doors
    return g


def _stone(col):
    return lambda u, v: (C(col) * np.ones(u.shape + (3,)), nores(u.shape), None)


def _woodpile(T, s0, f0, s1, f1, h):
    """Stacked firewood: a box with cut log ends on its faces."""
    def ends(u, v, LL, HH):
        cu, cv_ = np.mod(u, 3.2) - 1.6, np.mod(v, 3.2) - 1.6
        r = np.hypot(cu, cv_)
        rgb = np.where((r < 1.3)[..., None], C("d8b07a"), C("5a3a24")) * np.ones(u.shape + (1,))
        rgb[r < 0.5] = C("b88a58")
        return rgb, nores(u.shape), None
    T.box(s0, f0, s1, f1, 0, h, all=ends, top=flat("7a5034"))
    T.box(s0 - 2, f0 - 2, s1 + 2, f1 + 2, h, h + 2, all=flat("5a4a3a"), top=flat("4a3e32"))


# ====================================================================== log izba
def house_log(L, o):
    """A Russian log izba: round-log walls with jutting corner ends, white carved window frames with blue shutters,
    a steep metal gable facing the street, a woodpile and a birch; later a bench, a well and a little bathhouse."""
    cv = Canvas(1, 150)
    T = Orient(cv, o)
    seed = 1301
    logc = ["8a5a34", "7e5230", "94643a"][L - 1]
    win = Win(w=12, h=15, sill=9, sp=26, margin=14, fh=30, frame="f6f2ea", shutters="3a78b8", boxes=L >= 2)
    fr = _logs(facade("wood", logc, win=win, doors=[(36, 11, 22, "wood", "5a3a22")], seed=seed, plinth=("6a6258", 5)), logc)
    sd = _logs(facade("wood", logc, win=win, seed=seed + 1, plinth=("6a6258", 5)), logc)
    s0, s1, f0, f1 = 34, 116, 50, 124
    H = 30 if L < 3 else 36
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd)
    # log ends sticking out at the corners
    for s, f in ((s0, f0), (s1, f0), (s0, f1), (s1, f1)):
        T.box(s - 3, f - 3, s + 3, f + 3, 0, H, all=_logs(flat(logc), logc), top=flat("c8a070"))
    roofc = ["4a7a5a", "8a3a2a", "3a5a8a"][L - 1]
    T.gable(s0 - 4, f0 - 4, s1 + 4, f1 + 4, H, 40, roof_mat(roofc, "metal"), dict(front=fr, back=sd, left=sd, right=sd),
            ridge="f", o=5)
    cx, cy = T.pt(s1 - 26, (f0 + f1) / 2 + 8)
    kit.chimney(cv, cx - 3, cy - 3, H + 22, 22, "9a5a44", "chimney")
    # a little porch with a gable canopy
    slab(T, s0 + 30, f0 - 12, s0 + 52, f0, 0, 5, "8a6a44")
    steps(T, s0 + 33, s0 + 49, f0 - 12, 2, 3, "8a6a44")
    for s in (s0 + 31, s0 + 51):
        post(T, s, f0 - 11, 5, 26, "6a4a30", 2)
    T.gable(s0 + 28, f0 - 13, s0 + 54, f0, 26, 8, roof_mat(roofc, "metal"), flat("6a4a30"), ridge="f", o=2)
    door(T, s0 + 36, 11, f0, 22)
    entry(T, s0 + 41)
    ground(T, s0 + 34, 0, s0 + 48, f0 - 14, kit.paving("a89a84", 7.0))
    ground(T, 4, 4, 156, f0 - 14, kit.gravel("9aa86a"), z=0.25)
    fence(T, 2, 156, 2, "s", "9a8c78", gap=(s0 + 32, s0 + 50))
    _woodpile(T, 124, 60, 136, 104, 14)
    tree(T, 18, 30, "birch", 0.85, seed)
    if L >= 2:
        bench(T, s0 + 8, f0 - 8, "s", "7a5034")
        # a log well with a little roof
        wx, wy = T.pt(140, 26)
        T.cv.cylinder(wx, wy, 7, 0, 10, solid_side("7a5034", ribs=18))
        for d in (-5, 5):
            post(T, 140 + d, 26, 10, 22, "5a3a24", 1.4)
        T.gable(132, 20, 148, 32, 22, 6, roof_mat(roofc, "metal"), flat("5a3a24"), ridge="s", o=1)
    if L >= 3:
        # a small bathhouse (banya) in the back corner with a smoking stovepipe
        bh = _logs(facade("wood", logc, doors=[(6, 8, 18, "wood", "5a3a22")], seed=seed + 4, plinth=None), logc)
        T.box(8, 128, 30, 152, 0, 20, all=bh)
        T.gable(6, 126, 32, 154, 20, 12, roof_mat("6a6c72", "metal"), bh, ridge="s", o=1)
        px, py = T.pt(14, 140)
        kit.chimney(cv, px - 2, py - 2, 26, 10, "4a4a4a", "chimney_2")
        flowerbed(T, 60, 8, 96, 18, seed + 2)
    return cv


# ====================================================================== adobe village house
def house_adobe(L, o):
    """A clay village house: thick ochre mud walls, a flat earthen roof on poplar beams that poke out of the walls,
    small deep windows, a carved wooden door, a tandoor oven and a low clay yard wall; later hay on the roof
    and an upper room (balakhona) with a wooden balcony."""
    cv = Canvas(1, 130)
    T = Orient(cv, o)
    seed = 1321
    clay = ["c49a68", "caa272", "d0aa7a"][L - 1]
    win = Win(w=10, h=12, sill=10, sp=28, margin=16, fh=30, frame="6a4a2c", style="grid", lintel=True)
    fr = facade("plaster", clay, win=win, doors=[(30, 12, 22, "double", "7a4a28")], seed=seed, plinth=("9a7a54", 5))
    sd = facade("plaster", clay, win=win, seed=seed + 1, plinth=("9a7a54", 5))
    s0, s1, f0, f1 = 30, 130, 60, 130
    H = 30
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("a8865a", clay, 3, gravel=False))
    # poplar roof beams poking out of the front wall
    for s in range(s0 + 8, s1 - 4, 14):
        T.box(s, f0 - 5, s + 3, f0, H - 5, H - 2, all=flat("6a4a30"), top=flat("7a5a3a"))
    door(T, s0 + 30, 12, f0, 22)
    entry(T, s0 + 36)
    # a clay yard wall with an opening, the yard of beaten earth
    duval = facade("plaster", "b89064", seed=seed + 3, plinth=None)
    T.box(2, 2, s0 + 26, 6, 0, 14, all=duval, top=flat("a8865a"))
    T.box(s0 + 46, 2, 158, 6, 0, 14, all=duval, top=flat("a8865a"))
    ground(T, 6, 6, 156, f0, kit.paving("c8ae86", 14.0, 4, 0.3))
    # tandoor: a clay oven, its mouth dark
    tx, ty = T.pt(136, 34)
    T.cv.cylinder(tx, ty, 8, 0, 14, solid_side("b8865a"), cap=lambda u, v: (
        np.where((np.hypot(u, v) < 4)[..., None], C("2a1e18"), C("c8966a")) * np.ones(u.shape + (1,)), nores(u.shape), None))
    tree(T, 14, 36, "fruit", 0.8, seed, "f8e0a0")
    if L >= 2:
        # hay on the roof and a reed mat bench
        T.cv.ellipsoid(*T.pt(s1 - 26, f1 - 20), H + 2, 14, 12, 9, lambda wx, wy, wz, nx, ny, nz: (
            C("d8b85a") * (0.8 + 0.25 * nz)[..., None] * np.ones(wx.shape + (1,)), nores(wx.shape), None))
        slab(T, 90, 20, 122, 40, 0, 7, "8a5a34", flat("b8282a"))
    if L >= 3:
        # balakhona: an upper room with a wooden balcony on the street side
        up = facade("plaster", clay, win=Win(w=12, h=14, sill=8, sp=24, margin=10, fh=30, frame="6a4a2c", style="cross"),
                    seed=seed + 5, plinth=None)
        box(T, s0 + 6, f0 + 10, s0 + 56, f1 - 10, H, H + 26, all=up, top=flat_top("a8865a", clay, 3, gravel=False))
        slab(T, s0 + 6, f0, s0 + 56, f0 + 10, H, H + 2, "7a5434")
        T.panel(s0 + 6, s0 + 56, f0, H + 2, H + 10, lambda u, v, LL, HH: (C("6a4a2c") * np.ones(u.shape + (3,)), nores(u.shape), None),
                "s", lambda u, v: ((u % 5) < 1.4) | (v > 6.5))
        for s in range(s0 + 10, s0 + 56, 12):
            T.box(s, f0 + 5, s + 3, f0 + 10, H + 21, H + 24, all=flat("6a4a30"), top=flat("7a5a3a"))
    return cv


# ====================================================================== brick cottage
def house_brick(L, o):
    """A small red-brick house: white window frames with flower boxes, a slate hip roof, a gabled porch on posts,
    a clipped hedge along the street; later a garden shed and a second floor with solar panels."""
    cv = Canvas(1, 160)
    T = Orient(cv, o)
    seed = 1341
    brick = ["b0503a", "a84a36", "9a4434"][L - 1]
    win = Win(w=13, h=16, sill=8, sp=26, margin=13, fh=30, frame="f8f6f0", style="cross", boxes=True)
    fr = facade("brick", brick, win=win, doors=[(40, 11, 22, "panel", "1e4a3a")], seed=seed, plinth=("5a5652", 5))
    sd = facade("brick", brick, win=win, seed=seed + 1, plinth=("5a5652", 5))
    s0, s1, f0, f1 = 28, 128, 52, 122
    H = 32 if L < 3 else 60
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd)
    T.hip(s0 - 5, f0 - 5, s1 + 5, f1 + 5, H, 28, roof_mat("4a4e58", "slate"), o=5)
    cx, cy = T.pt(s0 + 20, (f0 + f1) / 2)
    kit.chimney(cv, cx - 3, cy - 3, H + 12, 22, "8a3e2e", "chimney")
    # gabled porch on two white posts
    steps(T, s0 + 36, s0 + 56, f0, 2, 4, "b8b0a4")
    for s in (s0 + 37, s0 + 55):
        post(T, s, f0 - 13, 0, 25, "f8f6f0", 2)
    T.gable(s0 + 34, f0 - 15, s0 + 58, f0, 25, 9, roof_mat("4a4e58", "slate"), flat("f8f6f0"), ridge="f", o=2)
    door(T, s0 + 40, 11, f0, 22)
    entry(T, s0 + 45)
    ground(T, s0 + 39, 0, s0 + 53, f0 - 8, kit.bricks_pave("a86a50"))
    hedge(T, 6, 4, s0 + 34, 12, 10, seed)
    hedge(T, s0 + 60, 4, 154, 12, 10, seed + 1)
    mailbox(T, s0 + 62, 18, "c83a2a")
    bush(T, 14, 40, 0.8, seed, "f4d040")
    if L >= 2:
        # a garden shed with a lean-to tin roof
        sh = facade("wood", "6a8a6a", doors=[(4, 10, 18, "wood", "4a6a4a")], seed=seed + 3, plinth=None)
        T.box(132, 120, 154, 148, 0, 20, all=sh, top=flat("8a8c90"))
        flowerbed(T, 80, 18, 120, 30, seed + 2)
    if L >= 3:
        x0, y0, x1, y1 = T.rect(s0 + 50, f0 + 4, s1 - 6, (f0 + f1) / 2)
        kit.solar(cv, x0, y0, x1, y1, H + 8)
        tree(T, 146, 30, "maple", 0.8, seed + 4)
    return cv


# ====================================================================== A-frame cabin
def house_aframe(L, o):
    """An A-frame cabin: a steep shingle roof down to the ground, a glazed triangular front with wooden mullions,
    a deck with a railing, pines and a fire pit; later deck chairs and a canoe."""
    cv = Canvas(1, 170)
    T = Orient(cv, o)
    seed = 1361
    wood = ["b07a48", "a8703e", "9a6436"][L - 1]

    def glass_end(u, v, LL, HH):
        rgb = np.broadcast_to(C("6a8aa0"), u.shape + (3,)).copy()
        rgb += ((v / max(HH, 1)) * 30)[..., None]
        mull = (np.mod(u, 14) < 1.8) | (np.mod(v, 18) < 1.8) | (u < 3) | (u > LL - 3)
        rgb[mull] = C(wood)
        em = np.zeros(u.shape + (4,))
        em[~mull] = np.array([255, 214, 150, 130.0])
        return rgb, nores(u.shape), em
    sd = facade("wood", wood, seed=seed + 1, plinth=("6a5a4a", 3))
    fr = facade("wood", wood, win=Win(w=18, h=12, sill=3, sp=28, margin=8, fh=30, frame=wood, style="grid", tint="7a9ab0"),
                doors=[(36, 12, 22, "glass")], seed=seed, plinth=("6a5a4a", 3))
    s0, s1, f0, f1 = 34, 126, 62, 132
    H = 14
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd)
    roofc = ["3a3e44", "4a3a34", "2e4a3a"][L - 1]
    T.gable(s0 - 6, f0 - 4, s1 + 6, f1 + 2, H, 92 if L < 3 else 102, roof_mat(roofc, "shingle"),
            dict(front=glass_end, back=sd, left=sd, right=sd), ridge="f", o=8)
    door(T, s0 + 36, 12, f0, 22)
    entry(T, s0 + 42)
    # wooden deck with a rail and steps
    slab(T, s0 - 2, f0 - 26, s1 + 2, f0, 0, 5, "b88a58", lambda u, v, LL, D: (
        C("b88a58") * (1 - 0.14 * (np.mod(u, 5) < 0.7))[..., None] * np.ones(u.shape + (1,)), nores(u.shape), None))
    T.panel(s0 - 2, s0 + 32, f0 - 26, 5, 14, lambda u, v, LL, HH: (C(wood) * np.ones(u.shape + (3,)), nores(u.shape), None),
            "s", lambda u, v: ((u % 5) < 1.2) | (v > 7.5))
    T.panel(s0 + 52, s1 + 2, f0 - 26, 5, 14, lambda u, v, LL, HH: (C(wood) * np.ones(u.shape + (3,)), nores(u.shape), None),
            "s", lambda u, v: ((u % 5) < 1.2) | (v > 7.5))
    steps(T, s0 + 34, s0 + 50, f0 - 26, 2, 4, "a87a4a")
    ground(T, s0 + 36, 0, s0 + 48, f0 - 34, kit.gravel("b8ac94"))
    ground(T, 4, 4, 156, 156, kit.paving("7a9a5a", 16.0, 6, 0.2), z=0.2)
    tree(T, 14, 40, "pine", 0.9, seed)
    tree(T, 144, 110, "spruce", 0.8, seed + 1)
    # fire pit: a ring of stones with glowing embers
    fx, fy = T.pt(130, 28)
    T.cv.cylinder(fx, fy, 8, 0, 3, solid_side("8a8478"), cap=lambda u, v: (
        np.where((np.hypot(u, v) < 5)[..., None], C("e86a2a"), C("9a948a")) * np.ones(u.shape + (1,)), nores(u.shape),
        np.where((np.hypot(u, v) < 5)[..., None], np.array([255, 140, 60, 200.0]), 0.0) * np.ones(u.shape + (1,))))
    for k in range(3):
        a = k * 2.1
        T.box(130 + 13 * np.cos(a) - 2, 28 + 13 * np.sin(a) - 4, 130 + 13 * np.cos(a) + 2, 28 + 13 * np.sin(a) + 4, 0, 4,
              all=flat("7a5034"), top=flat("8a6040"))
    if L >= 2:
        for s in (s0 + 4, s0 + 18):
            T.box(s, f0 - 20, s + 8, f0 - 12, 5, 10, all=flat("d84a3a"), top=flat("e85a4a"))
            T.box(s, f0 - 13, s + 8, f0 - 11, 10, 18, all=flat("d84a3a"), top=flat("e85a4a"))
        bush(T, 150, 60, 0.7, seed + 2)
    if L >= 3:
        # a canoe on trestles by the side
        T.box(8, 70, 24, 72, 0, 8, all=flat("6a4a30"))
        T.box(8, 110, 24, 112, 0, 8, all=flat("6a4a30"))
        rx, ry = (26, 6) if T.axis("f") == "x" else (6, 26)
        T.cv.ellipsoid(*T.pt(16, 91), 10, rx, ry, 4, lambda wx, wy, wz, nx, ny, nz: (
            C("2a7ab8") * (0.75 + 0.3 * nz)[..., None] * np.ones(wx.shape + (1,)), nores(wx.shape), None))
        lamp(T, s0 + 60, 10, "lantern", 30)
    return cv


# ====================================================================== shipping-container house
def house_container(L, o):
    """A house of shipping containers: an orange one on the ground and a blue one turned across it on top,
    corrugated steel, big glass ends, an outside steel stair, a deck with planters; later a third green container
    and a roof garden."""
    cv = Canvas(1, 150)
    T = Orient(cv, o)
    seed = 1381
    tint = "7a9ab4"
    gw = Win(w=26, h=20, sill=4, sp=34, margin=8, fh=26, frame="2a2c30", style="vertical", tint=tint)
    lo_fr = facade("metal", "d8642a", win=gw, doors=[(54, 12, 22, "glass")], seed=seed, plinth=None)
    lo_sd = facade("metal", "d8642a", win=Win(w=14, h=12, sill=10, sp=30, margin=14, fh=26, frame="2a2c30", tint=tint),
                   seed=seed + 1, plinth=None)
    s0, s1, f0, f1 = 24, 136, 62, 94
    box(T, s0, f0, s1, f1, 0, 26, front=lo_fr, back=lo_sd, left=lo_sd, right=lo_sd, top=flat("b8562a"))
    up_c = ["2a6ab0", "2a6ab0", "3a5a9a"][L - 1]
    up = facade("metal", up_c, win=Win(w=24, h=18, sill=4, sp=32, margin=6, fh=26, frame="2a2c30", style="vertical", tint=tint),
                seed=seed + 2, plinth=None)
    # the upper container turns across the lower one and overhangs the front as a carport
    box(T, 76, 40, 108, 150, 26, 52, all=up, top=flat("245a96"))
    T.panel(40, 150, 76, 22, 26, lambda u, v, LL, HH: (C("3a3c42") * np.ones(u.shape + (3,)), nores(u.shape), None), "f")
    door(T, s0 + 54, 12, f0, 22)
    entry(T, s0 + 60)
    # an outside steel stair to the upper deck
    for i in range(8):
        T.box(40 + i * 4, f0 - 10, 44 + i * 4, f0 - 2, i * 3.2, i * 3.2 + 2, all=flat("4a4c52"), top=flat("5a5c62"))
    slab(T, s0, f0 + 2, 74, f1 - 2, 26, 27, "8a6a4a")
    T.panel(s0, 74, f0 + 2, 27, 36, glass_rail, "s")
    # deck with planters
    slab(T, s0, f0 - 18, s1, f0, 0, 3, "a88058", lambda u, v, LL, D: (
        C("a88058") * (1 - 0.14 * (np.mod(v, 5) < 0.7))[..., None] * np.ones(u.shape + (1,)), nores(u.shape), None))
    for s in (s0 + 2, s1 - 14):
        T.box(s, f0 - 16, s + 12, f0 - 8, 3, 10, all=flat("4a4c52"), top=flat("4a3a2a"))
        bush(T, s + 6, f0 - 12, 0.5, seed + s, "f4d040")
    ground(T, s0 + 56, 0, s0 + 68, f0 - 18, kit.paving("9a9c9e", 6.0))
    ground(T, 4, 100, 156, 156, kit.gravel("8a8c86"), z=0.25)
    bins(T, 146, 74)
    tree(T, 14, 30, "birch", 0.75, seed)
    if L >= 2:
        car = "c84a3a"
        T.box(82, 108, 102, 144, 2, 12, all=flat(car), top=flat("e86a5a"))
        T.box(84, 116, 100, 134, 12, 18, all=flat("6a8aa0"), top=flat(car))
    if L >= 3:
        gr = facade("metal", "4a8a4a", win=Win(w=20, h=16, sill=4, sp=30, margin=8, fh=26, frame="2a2c30", tint=tint),
                    seed=seed + 3, plinth=None)
        box(T, 112, 100, 150, 150, 0, 26, all=gr, top=flat("3a7a3a"))
        x0, y0, x1, y1 = T.rect(78, 44, 106, 146)
        T.flat(78, 44, 106, 146, 52.3, lambda u, v, LL, D: (np.where((hash2(np.floor(u / 4), np.floor(v / 4), 3) > 0.4)[..., None],
                                                                       C("4a8a3a"), C("6aa04a")) * np.ones(u.shape + (1,)), nores(u.shape), None))
        bush(T, 92, 120, 0.5, seed + 9, "e86a8a")
    return cv


# ====================================================================== whitewashed Mediterranean house
def house_med(L, o):
    """A whitewashed Mediterranean house: white cubes with rounded parapets, a blue door and blue shutters,
    an outside stair to a roof terrace, bougainvillea over the wall and terracotta pots; later a pergola
    on the terrace and a second cube with a little blue dome."""
    cv = Canvas(1, 140)
    T = Orient(cv, o)
    seed = 1401
    white = "f6f4ee"
    blue = "2a5ab8"
    win = Win(w=11, h=14, sill=9, sp=24, margin=14, fh=30, frame=blue, shutters=blue, style="cross")
    fr = facade("plaster", white, win=win, doors=[(24, 11, 22, "wood", blue)], seed=seed, plinth=("8ab0d8", 3))
    sd = facade("plaster", white, win=win, seed=seed + 1, plinth=("8ab0d8", 3))
    s0, s1, f0, f1 = 30, 112, 56, 126
    H = 32
    box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat("e8e0d4"))
    # a parapet round the roof terrace with a blue cap
    for a in ((s0, f0, s1, f0 + 3), (s0, f1 - 3, s1, f1), (s0, f0, s0 + 3, f1), (s1 - 3, f0, s1, f1)):
        T.box(*a, H, H + 7, all=flat(white), top=flat("4a7ac8"))
    door(T, s0 + 24, 11, f0, 22)
    entry(T, s0 + 29)
    steps(T, s0 + 21, s0 + 39, f0, 2, 4, "e8e4dc")
    # outside stair along the right side up to the terrace
    for i in range(9):
        T.box(s1, f0 + 4 + i * 6, s1 + 12, f0 + 10 + i * 6, 0, 4 + i * 3.4, all=flat(white), top=flat("ece6dc"))
    # bougainvillea spilling over the front wall
    for k, s in enumerate((s0 + 6, s0 + 54)):
        bx, by = T.pt(s, f0 - 2)
        T.cv.ellipsoid(bx, by, 26, 9, 4, 8, lambda wx, wy, wz, nx, ny, nz, k=k: (
            np.where((hash2(np.floor(wx / 2), np.floor(wz / 2), 5 + k) > 0.45)[..., None], C("d83a8a"), C("3a7a3a"))
            * (0.8 + 0.25 * nz)[..., None] * np.ones(wx.shape + (1,)), nores(wx.shape), None))
    ground(T, 4, 4, 156, f0, kit.paving("ece6da", 9.0, 7))
    # terracotta pots with plants
    for k, s in enumerate((s0 - 10, s0 + 46, s0 + 60)):
        px, py = T.pt(s, f0 - 8)
        T.cv.cylinder(px, py, 4, 0, 7, solid_side("c8643a"))
        bush(T, s, f0 - 8, 0.4, seed + k, "e8483a")
    tree(T, 140, 26, "fruit", 0.75, seed, "f8f0d0")   # a lemon tree
    if L >= 2:
        # pergola with vines on the terrace
        for s, f in ((s0 + 10, f0 + 10), (s0 + 50, f0 + 10), (s0 + 10, f0 + 44), (s0 + 50, f0 + 44)):
            post(T, s, f, H, H + 24, "e8e0d4", 2.2)
        T.flat(s0 + 8, f0 + 8, s0 + 52, f0 + 46, H + 24, lambda u, v, LL, D: (
            np.where((hash2(np.floor(u / 3), np.floor(v / 3), 11) > 0.5)[..., None], C("4a8a3a"), C("a88a5a"))
            * np.ones(u.shape + (1,)), nores(u.shape), None))
        bench(T, s0 + 30, f0 + 30, "s", "4a7ac8")
    if L >= 3:
        cube = facade("plaster", white, win=Win(w=11, h=14, sill=9, sp=24, margin=10, fh=30, frame=blue, shutters=blue),
                      seed=seed + 4, plinth=None)
        box(T, s0 + 56, f0 + 30, s1 - 4, f1 - 4, H, H + 28, all=cube, top=flat("e8e0d4"))
        dx, dy = T.pt((s0 + 56 + s1 - 4) / 2, (f0 + 30 + f1 - 4) / 2)
        T.cv.ellipsoid(dx, dy, H + 28, 11, 11, 11, lambda wx, wy, wz, nx, ny, nz: (
            C("2a5ab8") * (0.7 + 0.35 * nz)[..., None] * np.ones(wx.shape + (1,)), nores(wx.shape), None), cut_z=H + 28)
    return cv


# ====================================================================== two-family duplex
def house_duplex(L, o):
    """A duplex for two families: one gabled house split down the middle, each half in its own colour of siding,
    its own door with a canopy, its own chimney, mailbox and patch of lawn with a low fence between them."""
    cv = Canvas(1, 160)
    T = Orient(cv, o)
    seed = 1421
    ca = ["f0d890", "f0d890", "e8c870"][L - 1]
    cb = ["a8d0b0", "a8c8e0", "a8d0b0"][L - 1]
    win = Win(w=12, h=15, sill=9, sp=22, margin=10, fh=30, frame="ffffff", style="cross", boxes=L >= 2)
    s0, s1, f0, f1 = 18, 142, 56, 122
    m = (s0 + s1) / 2
    H = 32 if L < 3 else 60
    fa = facade("siding", ca, win=win, doors=[(m - s0 - 22, 10, 22, "wood", "8a3a2a")], seed=seed, plinth=("7a7470", 5))
    fb = facade("siding", cb, win=win, doors=[(8, 10, 22, "wood", "2a4a7a")], seed=seed + 1, plinth=("7a7470", 5))
    sa = facade("siding", ca, win=win, seed=seed + 2, plinth=("7a7470", 5))
    sb = facade("siding", cb, win=win, seed=seed + 3, plinth=("7a7470", 5))
    box(T, s0, f0, m, f1, 0, H, front=fa, back=sa, left=sa, right=sa)
    box(T, m, f0, s1, f1, 0, H, front=fb, back=sb, left=sb, right=sb)
    roofc = ["6a4a3a", "5a5e66", "7a3a2e"][L - 1]
    T.gable(s0 - 4, f0 - 5, s1 + 4, f1 + 5, H, 30, roof_mat(roofc, "shingle"), dict(front=fa, back=sa, left=sa, right=sb),
            ridge="s", o=5)
    # the party wall shows as a white trim strip on the front
    T.panel(m - 1.5, m + 1.5, f0 - 0.3, 0, H, lambda u, v, LL, HH: (C("ffffff") * np.ones(u.shape + (3,)), nores(u.shape), None), "s")
    for s in (s0 + 24, s1 - 24):
        cx, cy = T.pt(s, (f0 + f1) / 2 + 6)
        kit.chimney(cv, cx - 3, cy - 3, H + 14, 18, "8a5a44", "chimney" if s < m else "chimney_2")
    da, db = m - 22, m + 8
    canopy(T, da - 4, da + 14, f0, 12, 25, "ffffff", roofc)
    canopy(T, db - 4, db + 14, f0, 12, 25, "ffffff", roofc)
    steps(T, da - 2, da + 12, f0, 2, 4)
    steps(T, db - 2, db + 12, f0, 2, 4)
    door(T, da, 10, f0, 22)
    door(T, db, 10, f0, 22, "door2")
    entry(T, da + 5)
    ground(T, da - 1, 0, da + 11, f0 - 8, kit.paving("c8bcaa", 6.0))
    ground(T, db - 1, 0, db + 11, f0 - 8, kit.paving("c8bcaa", 6.0))
    fence(T, 4, f0 - 8, m, "f", "ffffff", h=8)
    fence(T, 2, 158, 2, "s", "ffffff", gap=(da - 2, db + 12))
    mailbox(T, da - 8, 8, "c83a2a")
    mailbox(T, db + 18, 8, "2a5ab8")
    bush(T, 20, 30, 0.7, seed, "e86a8a")
    bush(T, 140, 30, 0.7, seed + 1, "f4d040")
    if L >= 2:
        x, y = T.pt(30, 140)
        kit.swing(cv, x - 12, y)
        kit.laundry(cv, *T.pt(116, 140), 26)
    if L >= 3:
        flowerbed(T, s0 + 4, f0 - 20, da - 10, f0 - 10, seed + 2)
        flowerbed(T, db + 22, f0 - 20, s1 - 4, f0 - 10, seed + 3)
    return cv


BUILDERS = {"house_log": house_log, "house_adobe": house_adobe, "house_brick": house_brick, "house_aframe": house_aframe,
            "house_container": house_container, "house_med": house_med, "house_duplex": house_duplex}
