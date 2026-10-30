"""Signature towers, luxury hotels and public transport (bus stop, metro station) at real scale."""
import numpy as np

from raster import C, U, Canvas, flat, nores, hash2, glow_res
from arch import Orient, facade, Win, roof_mat, flat_top
import kit
from bkit import (door, entry, ground, tree, bush, hedge, flowerbed, lamp, bench, box, slab, post, canopy, steps, awning,
                  balconies, roof_units, sign_board, glass_rail)
from b_civic import column, flagpole
from b_homes import spire

S = U
WARM = np.array([255, 214, 140, 235.0])


# ====================================================================== helpers
def ring_glass(r, glass="6a8aa8", frame="e8e4dc", fh=30, sp=22, lit=0.5, seed=0, slab_col=None):
    """Side of a round glass tower: floors of windows following the curve, lit at random at night."""
    g, fr = C(glass), C(frame)
    sc = C(slab_col) if slab_col else fr

    def fn(a, z, nx, ny):
        arc = (a + np.pi) * r
        u = np.mod(arc, sp)
        v = np.mod(z, fh)
        col_i = np.floor(arc / sp)
        fl = np.floor(z / fh)
        win = (u > 2.5) & (u < sp - 2.5) & (v > 5) & (v < fh - 3)
        rgb = np.empty(a.shape + (3,))
        rgb[...] = fr
        sky = np.clip(0.55 + 0.45 * (v / fh), 0, 1)[..., None]
        rgb[win] = (g * (0.75 + 0.35 * sky) + 22 * (hash2(col_i, fl, seed + 3) - 0.5)[..., None])[win]
        rgb[v < 2.5] = sc
        em = np.zeros(a.shape + (4,))
        on = win & (hash2(col_i + 7, fl, seed) < lit)
        em[on] = WARM
        return rgb, nores(a.shape), em
    return fn


def gold3(col="e8b84a"):
    """Polished metal for domes (ellipsoid callback)."""
    c = C(col)

    def fn(wx, wy, wz, nx, ny, nz):
        k = (0.78 + 0.32 * nz + 0.25 * np.clip(nx + ny, 0, 1) ** 4)[..., None]
        return c * k, nores(wx.shape), None
    return fn


def glass3(col="7ab0d0", lit=True):
    """Glass dome, softly lit from inside at night."""
    c = C(col)

    def fn(wx, wy, wz, nx, ny, nz):
        rib = (np.abs(np.sin(np.arctan2(ny, nx) * 8)) < 0.12) | (np.mod(wz, 8) < 0.8)
        rgb = np.broadcast_to(c, wx.shape + (3,)) * (0.8 + 0.3 * nz)[..., None]
        rgb = np.where(rib[..., None], C("f2eee6"), rgb)
        em = np.zeros(wx.shape + (4,))
        if lit:
            em[~rib] = np.array([200, 230, 255, 140.0])
        return rgb, nores(wx.shape), em
    return fn


def solid_side(col, ribs=0):
    c = C(col)

    def fn(a, z, nx, ny):
        k = np.ones(a.shape) if not ribs else (0.9 + 0.1 * np.cos(a * ribs))
        return c * k[..., None], nores(a.shape), None
    return fn


def stripes_gold(sp=12, base="d8a840", dark="6a4a24"):
    """Art deco crown: gold ribs with lit slits between them."""
    def fn(u, v, L, H):
        k = np.mod(u, sp) / sp
        rib = (k < 0.55)
        rgb = np.where(rib[..., None], C(base) * (0.9 + 0.2 * (v / max(H, 1)))[..., None], C(dark))
        em = np.zeros(u.shape + (4,))
        em[~rib] = np.array([255, 226, 160, 255.0])
        return rgb * np.ones(u.shape + (1,)), nores(u.shape), em
    return fn


def palm(T, s, f, h=60, seed=0):
    x, y = T.pt(s, f)
    T.cv.cylinder(x, y, 2.4, 0, h, solid_side("8a6a44", ribs=40))
    rng = np.random.default_rng(seed)
    for k in range(7):
        a = k / 7 * 2 * np.pi + rng.uniform(0, 0.5)
        dx, dy = np.cos(a) * 11, np.sin(a) * 11
        T.cv.ellipsoid(x + dx, y + dy, h - 3, 13, 13, 3.5, lambda wx, wy, wz, nx, ny, nz: (
            C("3e8a3a") * (0.75 + 0.35 * nz)[..., None] * np.ones(wx.shape + (1,)), nores(wx.shape), None))
    T.cv.ellipsoid(x, y, h + 1, 6, 6, 5, lambda wx, wy, wz, nx, ny, nz: (
        C("4a9a42") * np.ones(wx.shape + (3,)), nores(wx.shape), None))


def umbrella(T, s, f, col="e84a3a"):
    x, y = T.pt(s, f)
    T.cv.cylinder(x, y, 0.8, 0, 22, solid_side("f2eee6"))
    T.cv.ellipsoid(x, y, 22, 10, 10, 4, lambda wx, wy, wz, nx, ny, nz: (
        np.where((np.mod(np.floor(np.arctan2(wy - y, wx - x) * 4 / np.pi), 2) == 0)[..., None], C(col), C("f6f2ea"))
        * (0.85 + 0.2 * nz)[..., None], nores(wx.shape), None), cut_z=22)


def lounger(T, s, f):
    slab(T, s - 4, f - 9, s + 4, f + 9, 1, 3, "f4f0e8")


def pool(T, s0, f0, s1, f1):
    x0, y0, x1, y1 = T.rect(s0, f0, s1, f1)
    kit.pool(T.cv, x0, y0, x1, y1)


def tier_ring(T, cx, cy, r, z, h=4, col="f2eee6"):
    T.cv.cylinder(cx, cy, r, z, z + h, solid_side(col), cap=lambda u, v: (C(col) * np.ones(u.shape + (3,)), nores(u.shape), None))


# ====================================================================== round_tower: a white drum with balcony rings and a golden dome
def round_tower(L, o):
    floors = [12, 15, 18][L - 1]
    fh = 30
    pod = fh + 8
    H = pod + floors * fh
    cv = Canvas(2, H + 190)
    T = Orient(cv, o)
    seed = 701
    podf = facade("stone", "e2d8c6", shop=(20, 120, 28), doors=[(140, 34, 30, "double_glass")], plinth=None, seed=seed, lit=0.7,
                  win=Win(w=22, h=18, sill=12, sp=30, margin=10, fh=pod, frame="3a3a40", group="work"))
    pods = facade("stone", "e2d8c6", win=Win(w=22, h=18, sill=12, sp=30, margin=10, fh=pod, frame="3a3a40", group="work"), seed=seed + 1)
    box(T, 20, 50, 300, 290, 0, pod, front=podf, back=pods, left=pods, right=pods, top=flat_top("6e9a5a", "e2d8c6", 5))
    canopy(T, 130, 190, 50, 22, 34, "2e3238", "2e3238", posts=False)
    door(T, 140, 34, 50, 30)
    entry(T, 157)
    cx, cy = T.pt(160, 170)
    r = 92
    glass = ["6a96b4", "5a8aac", "7aa0bc"][L - 1]
    T.cv.cylinder(cx, cy, r, pod, H, ring_glass(r, glass, "f4f0e8", fh, 22, 0.55, seed),
                  cap=lambda u, v: (C("d8d4cc") * np.ones(u.shape + (3,)), nores(u.shape), None))
    # white balcony rings every other floor
    for k in range(1, floors, 2):
        tier_ring(T, cx, cy, r + 7, pod + k * fh - 2, 3)
    # crown: a narrower lit drum, a golden dome and a mast
    T.cv.cylinder(cx, cy, r - 30, H, H + 26, ring_glass(r - 30, "a8d0e8", "f4f0e8", 26, 16, 0.95, seed + 2))
    tier_ring(T, cx, cy, r - 24, H + 26, 4, "e8e2d6")
    T.cv.ellipsoid(cx, cy, H + 30, r - 34, r - 34, 46, gold3(["e8b84a", "e8c060", "f0c868"][L - 1]), cut_z=H + 30)
    spire(T, 160, 170, H + 74, [40, 60, 80][L - 1], "e8c060")
    for ss in (40, 280):
        tree(T, ss, 26, "maple", 0.7, 711 + ss)
    ground(T, 0, 0, 320, 50, kit.paving("d0c8bc", 12.0, 4))
    lamp(T, 100, 16, "modern", 50)
    lamp(T, 220, 16, "modern", 50, "light2")
    return cv


# ====================================================================== deco_tower: stepped art deco tower with a glowing golden crown
def deco_tower(L, o):
    n1, n2, n3 = [(8, 4, 3), (10, 5, 4), (12, 6, 5)][L - 1]
    fh = 30
    pod = 2 * fh
    H1 = pod + n1 * fh
    H2 = H1 + n2 * fh
    H3 = H2 + n3 * fh
    cv = Canvas(2, H3 + 260)
    T = Orient(cv, o)
    seed = 721
    stone = "ece0c8"
    trim = "b08a4a"
    podf = facade("stone", "d8c8a8", shop=(20, 300, 30), doors=[(140, 40, 34, "double_glass")], plinth=None, seed=seed, lit=0.8,
                  win=Win(w=24, h=22, sill=30, sp=32, margin=10, fh=pod, frame=trim, group="work"),
                  bands=[(pod - 6, pod, trim)])
    pods = facade("stone", "d8c8a8", win=Win(w=24, h=22, sill=30, sp=32, margin=10, fh=pod, frame=trim, group="work"), seed=seed + 1,
                  bands=[(pod - 6, pod, trim)])
    box(T, 10, 30, 310, 310, 0, pod, front=podf, back=pods, left=pods, right=pods, top=flat_top("8a8884", stone, 4))
    canopy(T, 120, 200, 30, 24, 40, trim, "3a3028", posts=False)
    door(T, 140, 40, 30, 34)
    entry(T, 160)
    win = Win(w=10, h=22, sill=4, sp=16, margin=6, fh=fh, frame="4a4038", style="vertical", tint="5a7aa0", group="flats", top_skip=2)

    def tier(s0, f0, s1, f1, z0, z1, sd):
        bands = [(z1 - z0 - 6, z1 - z0, trim)]
        fa = facade("stone", stone, win=win, seed=sd, plinth=None, bands=bands)
        box(T, s0, f0, s1, f1, z0, z1, all=fa, top=flat_top("8a8884", stone, 4))
        # piers at the corners rise a little above each setback
        pier = facade("stone", "f4ead6", plinth=None, seed=sd + 1)
        for a in (s0, s1 - 12):
            for b in (f0, f1 - 12):
                T.box(a, b, a + 12, b + 12, z0, z1 + 12, all=pier, top=flat(trim))

    tier(40, 60, 280, 280, pod, H1, seed + 2)
    tier(70, 90, 250, 250, H1, H2, seed + 4)
    tier(100, 120, 220, 220, H2, H3, seed + 6)
    # crown: shrinking gold tiers with lit slits, then a needle
    z = H3
    for k, w in enumerate((56, 42, 30, 18)):
        h = 26 - k * 3
        T.box(160 - w, 170 - w, 160 + w, 170 + w, z, z + h, all=stripes_gold(10 - k), top=flat("c8983a"))
        z += h
    spire(T, 160, 170, z, [70, 90, 110][L - 1], "e8c060")
    for ss in (30, 290):
        tree(T, ss, 16, "lime", 0.7, 731 + ss)
    ground(T, 0, 0, 320, 30, kit.paving("cfc6b6", 12.0, 4))
    lamp(T, 90, 12, "classic", 48)
    lamp(T, 230, 12, "classic", 48, "light2")
    return cv


# ====================================================================== stack_tower: shifted glass blocks with green terraces
def stack_tower(L, o):
    blocks = [6, 8, 10][L - 1]
    fh = 30
    bh = 3 * fh
    pod = fh + 10
    cv = Canvas(2, pod + blocks * bh + 160)
    T = Orient(cv, o)
    seed = 741
    podf = facade("concrete", "d8d4cc", shop=(20, 300, 30), doors=[(140, 40, 32, "double_glass")], plinth=None, seed=seed, lit=0.8,
                  win=Win(w=24, h=20, sill=14, sp=32, margin=10, fh=pod, frame="2e3238", group="work"))
    box(T, 20, 40, 300, 300, 0, pod, all=podf, top=flat_top("5e8a4e", "d8d4cc", 5))
    door(T, 140, 40, 40, 32)
    entry(T, 160)
    cols = ["e8e4dc", "f4efe4", "dcd8d0"]
    glass = ["5a86a8", "4a7a9c", "6a92b0"][L - 1]
    z = pod
    shifts = [(0, 0), (34, -26), (-30, 30), (24, 30), (-34, -22), (30, 6), (-20, -30), (34, 26), (-26, 4), (10, -30)]
    for k in range(blocks):
        ds, df = shifts[k]
        s0, s1 = 70 + ds, 250 + ds
        f0, f1 = 80 + df, 260 + df
        w = Win(w=26, h=22, sill=4, sp=32, margin=6, fh=fh, frame="2e3238", style="vertical", tint=glass, group="flats", top_skip=2)
        fa = facade("concrete", cols[k % 3], win=w, seed=seed + k, plinth=None, bands=[(bh - 4, bh, "f6f2ea")])
        box(T, s0, f0, s1, f1, z, z + bh, all=fa, top=flat_top("5e8a4e", "f6f2ea", 5))
        # a terrace garden on every roof that sticks out
        for j in range(3):
            bush(T, s0 + 30 + j * 55, f1 - 22, 0.55, seed + 13 * k + j) if k < blocks - 1 else None
        z += bh
    # glass pavilion on top
    lan = facade("concrete", "e8ecf0", win=Win(w=22, h=28, sill=2, sp=26, margin=4, fh=34, frame="9aa4ae", style="vertical",
                                                tint="9ac0d8", group="work"), plinth=None, seed=seed + 50, lit=1.0)
    ds, df = shifts[blocks - 1]
    T.box(110 + ds, 120 + df, 210 + ds, 220 + df, z, z + 34, all=lan, top=flat_top("807c78", "e8e2d6", 3))
    for k, ss in enumerate((30, 290)):
        tree(T, ss, 20, "birch", 0.75, 751 + k)
    ground(T, 0, 0, 320, 40, kit.paving("c8c4bc", 12.0, 4))
    lamp(T, 90, 14, "modern", 50)
    lamp(T, 230, 14, "modern", 50, "light2")
    return cv


# ====================================================================== twin_towers: two glass towers joined by a sky bridge
def twin_towers(L, o):
    floors = [22, 27, 32][L - 1]
    fh = 30
    pod = 2 * fh
    H = pod + floors * fh
    cv = Canvas(3, H + 200)
    T = Orient(cv, o)
    seed = 761
    glass = ["5a8ab0", "4a7ca4", "6a96b8"][L - 1]
    podf = facade("stone", "d4ccc0", shop=(30, 450, 30), doors=[(215, 50, 34, "double_glass")], plinth=None, seed=seed, lit=0.8,
                  win=Win(w=26, h=22, sill=30, sp=34, margin=10, fh=pod, frame="3a3a40", group="work"))
    pods = facade("stone", "d4ccc0", win=Win(w=26, h=22, sill=30, sp=34, margin=10, fh=pod, frame="3a3a40", group="work"), seed=seed + 1)
    box(T, 20, 70, 460, 440, 0, pod, front=podf, back=pods, left=pods, right=pods, top=flat_top("5e8a4e", "7aa860", 6))
    canopy(T, 200, 280, 70, 26, 40, "2e3238", "2e3238", posts=False)
    door(T, 215, 50, 70, 34)
    entry(T, 240)
    r = 74
    for k, sc in enumerate((130, 350)):
        cx, cy = T.pt(sc, 260)
        T.cv.cylinder(cx, cy, r, pod, H, ring_glass(r, glass, "e4e8ec", fh, 20, 0.5, seed + 2 + k, "f4f6f8"),
                      cap=lambda u, v: (C("c8ccd0") * np.ones(u.shape + (3,)), nores(u.shape), None))
        # tiered crown with a glowing glass dome and a mast
        tier_ring(T, cx, cy, r - 10, H, 18, "e8ecf0")
        T.cv.cylinder(cx, cy, r - 22, H + 18, H + 40, ring_glass(r - 22, "a8d0e8", "e8ecf0", 22, 14, 0.9, seed + 8 + k))
        T.cv.ellipsoid(cx, cy, H + 40, r - 26, r - 26, 34, glass3("8ac0e0"), cut_z=H + 40)
        spire(T, sc, 260, H + 72, [50, 70, 90][L - 1], "d8dce0")
    # the sky bridge at two thirds of the height
    zb = pod + int(floors * 0.62) * fh
    br = facade("metal", "c8ccd0", win=Win(w=22, h=24, sill=6, sp=26, margin=4, fh=40, frame="8a929a", style="vertical",
                                            tint="8ab8d8", group="work"), plinth=None, seed=seed + 20, lit=1.0)
    T.box(170, 230, 310, 290, zb, zb + 40, all=br, top=flat_top("807c78", "c8ccd0", 3))
    for k, ss in enumerate((40, 120, 360, 440)):
        tree(T, ss, 36, "maple", 0.8, 771 + k)
    ground(T, 10, 0, 470, 70, kit.paving("c8c4bc", 12.0, 4))
    lamp(T, 140, 18, "modern", 55)
    lamp(T, 340, 18, "modern", 55, "light2")
    return cv


# ====================================================================== hotels
def hotel_boutique(L, o):
    """A Parisian-style boutique hotel: stone, black iron balconies, golden awnings and a mansard roof."""
    floors = [4, 5, 6][L - 1]
    fh = 32
    H = floors * fh + 10
    cv = Canvas(2, H + 140)
    T = Orient(cv, o)
    seed = 801
    stone = "efe4cc"
    win = Win(w=16, h=24, sill=8, sp=34, margin=14, fh=fh, frame="f6f2ea", style="cross", group="work", arch=True)
    bands = [(fh * k + 6, fh * k + 9, "dccdb0") for k in range(1, floors)]
    fr = facade("stone", stone, win=win, doors=[(130, 60, 34, "double_glass")], seed=seed, plinth=("b8aa90", 6), bands=bands,
                cornice=("f6efe0", 6), quoins="e2d4b8", lit=0.75)
    sd = facade("stone", stone, win=win, seed=seed + 1, plinth=("b8aa90", 6), bands=bands, cornice=("f6efe0", 6), lit=0.75)
    box(T, 20, 50, 300, 280, 0, H, front=fr, back=sd, left=sd, right=sd, top=flat_top("5a5a64", stone, 3))
    T.hip(20, 50, 300, 280, H, 46, roof_mat("4a5060", "slate"), o=5)
    # dormers with lit windows in the roof
    dorm = facade("plaster", "f2ead8", win=Win(w=12, h=16, sill=4, sp=40, margin=4, fh=22, frame="f6f2ea", group="work"), plinth=None,
                  seed=seed + 2, lit=0.9)
    for s in (60, 130, 200):
        T.box(s, 52, s + 40, 62, H + 6, H + 28, all=dorm, top=flat("4a5060"))
    balconies(T, [s for s in range(40, 280, 68)], 50, range(1, floors), fh, 34, 8, "2a2a30", col="e8dcc4")
    awning(T, 40, 280, 50, 34, 18, 8, "d8a840", "2a2a30", 8.0)
    canopy(T, 130, 190, 50, 30, 38, "2a2a30", "d8a840", posts=True)
    door(T, 130, 60, 50, 34)
    entry(T, 160)
    sign_board(T, 160, 48, H - 30, "HOTEL", 12, "2a2a30", "f4d070")
    flagpole(T, 30, 46, 70, "8a2a4a")
    flagpole(T, 290, 46, 70, "2a4a8a")
    for ss in (20, 300):
        bush(T, ss, 30, 0.7, seed + ss, "f4c0d0")
    ground(T, 0, 0, 320, 50, kit.paving("cfc4b0", 10.0, 4))
    lamp(T, 100, 18, "classic", 48)
    lamp(T, 220, 18, "classic", 48, "light2")
    return cv


def hotel_resort(L, o):
    """A white terraced resort: stepped wings around a big pool with palms and umbrellas."""
    tiers = [3, 4, 5][L - 1]
    fh = 30
    cv = Canvas(3, tiers * fh + 160)
    T = Orient(cv, o)
    seed = 821
    win = Win(w=26, h=22, sill=4, sp=34, margin=8, fh=fh, frame="e8e4dc", style="vertical", tint="6aa8c8", group="work", top_skip=2)
    for k in range(tiers):
        f0 = 250 + k * 34
        fa = facade("plaster", "f8f4ec", win=win, seed=seed + k, plinth=None, bands=[(fh - 4, fh, "e8c890")], lit=0.6)
        box(T, 30, f0, 450, 460, k * fh, (k + 1) * fh, all=fa, top=flat_top("c8b89a", "f8f4ec", 4))
        balconies(T, list(range(50, 430, 60)), f0, [0], fh, 46, 8, "glass", z_start=k * fh, col="f8f4ec")
        # planters along each terrace
        for j in range(4):
            bush(T, 70 + j * 110, f0 + 30, 0.5, seed + 9 * k + j, "f4a0c0")
    # lobby pavilion with a wave roof
    lob = facade("plaster", "f8f4ec", doors=[(30, 40, 30, "double_glass")], win=Win(w=24, h=22, sill=6, sp=30, margin=6, fh=40,
                                                                                    frame="e8e4dc", group="work"), plinth=None, seed=seed + 20)
    box(T, 190, 190, 290, 250, 0, 40, all=lob, top=flat("e8c890"))
    T.cv.ellipsoid(*T.pt(240, 220), 40, 64, 64, 18, lambda wx, wy, wz, nx, ny, nz: (
        C("e8c890") * (0.8 + 0.3 * nz)[..., None] * np.ones(wx.shape + (1,)), nores(wx.shape), None), cut_z=40)
    door(T, 220, 40, 190, 30)
    entry(T, 240)
    # the pool deck
    ground(T, 10, 0, 470, 250, kit.paving("e8dcc4", 10.0, 4))
    pool(T, 40, 70, 180, 180)
    pool(T, 300, 70, 440, 180)
    for (s, f) in ((30, 40), (190, 40), (290, 40), (450, 40), (30, 200), (450, 200)):
        palm(T, s, f, 64, seed + s + f)
    for k, s in enumerate((60, 110, 160, 320, 370, 420)):
        umbrella(T, s, 196, ["e84a3a", "2a8ad8", "f4c040"][k % 3])
        lounger(T, s, 214)
    sign_board(T, 240, 188, 46, "RESORT", 10, "2a6a8a", "f4f0e0")
    lamp(T, 200, 20, "modern", 48)
    lamp(T, 280, 20, "modern", 48, "light2")
    return cv


def hotel_palace(L, o):
    """A palace hotel: colonnade, two wings and a golden dome over the hall, a reflecting pool in front."""
    fl = [3, 3, 4][L - 1]
    fh = 36
    H = fl * fh + 8
    cv = Canvas(3, H + 200)
    T = Orient(cv, o)
    seed = 841
    stone = "f2e8d4"
    win = Win(w=16, h=26, sill=8, sp=30, margin=10, fh=fh, frame="f8f4ec", style="cross", group="work", arch=True)
    bands = [(fh * k + 4, fh * k + 8, "e2d2b2") for k in range(1, fl)]
    fr = facade("stone", stone, win=win, seed=seed, plinth=("c8b89a", 8), bands=bands, cornice=("fbf4e4", 8), quoins="e8dcc0", lit=0.8)
    # wings
    for (s0, s1) in ((20, 160), (320, 460)):
        box(T, s0, 200, s1, 450, 0, H, all=fr, top=flat_top("8a8478", stone, 4))
        T.hip(s0, 200, s1, 450, H, 30, roof_mat("4a6a7a", "slate"), o=4)
    # central hall with columns
    hall = facade("stone", stone, win=win, doors=[(120, 80, 40, "double_glass")], seed=seed + 1, plinth=("c8b89a", 8), bands=bands,
                  cornice=("fbf4e4", 8), lit=0.85)
    box(T, 140, 230, 340, 430, 0, H + 20, front=hall, back=fr, left=fr, right=fr, top=flat_top("8a8478", stone, 4))
    slab(T, 140, 196, 340, 230, H, H + 10, "fbf4e4")
    for s in range(150, 340, 26):
        column(T, s, 206, 0, H, 4.0, "fbf4e4")
    steps(T, 150, 330, 196, 4, 5, "e8dcc4")
    door(T, 200, 80, 230, 40)
    entry(T, 240)
    # dome on a drum
    cx, cy = T.pt(240, 330)
    T.cv.cylinder(cx, cy, 64, H + 20, H + 56, ring_glass(64, "a8c8e0", stone, 36, 26, 0.9, seed + 5))
    tier_ring(T, cx, cy, 70, H + 56, 6, "fbf4e4")
    T.cv.ellipsoid(cx, cy, H + 62, 62, 62, 70, gold3("e8b448"), cut_z=H + 62)
    T.cv.cylinder(cx, cy, 6, H + 128, H + 150, solid_side("e8c060"))
    T.cv.ellipsoid(cx, cy, H + 152, 7, 7, 7, gold3("f0c868"))
    for s in (20, 460):
        flagpole(T, s, 196, 80, "8a2a3a")
    # forecourt: reflecting pool, fountain-like jets as lamps, hedges
    ground(T, 0, 0, 480, 196, kit.paving("e2d6c0", 10.0, 4))
    pool(T, 150, 40, 330, 150)
    hedge(T, 20, 30, 130, 44, 12, seed + 7)
    hedge(T, 350, 30, 460, 44, 12, seed + 8)
    for s in (60, 100, 380, 420):
        tree(T, s, 120, "poplar", 0.9, seed + s)
    if L >= 2:
        sign_board(T, 240, 194, H + 22, "PALACE", 12, "2a2a3a", "f4d070")
    lamp(T, 140, 20, "classic", 50)
    lamp(T, 340, 20, "classic", 50, "light2")
    return cv


def hotel_sail(L, o):
    """A white tower curved like a sail, with a round helipad near the top, standing on a lagoon."""
    floors = [18, 22, 26][L - 1]
    fh = 28
    pod = 40
    H = pod + floors * fh
    cv = Canvas(3, H + 220)
    T = Orient(cv, o)
    seed = 861
    podf = facade("plaster", "f4f6f8", shop=(30, 230, 30), doors=[(110, 60, 34, "double_glass")], plinth=None, seed=seed, lit=0.8,
                  win=Win(w=26, h=24, sill=10, sp=32, margin=10, fh=pod, frame="9aa4ae", group="work"))
    box(T, 120, 300, 360, 450, 0, pod, all=podf, top=flat_top("8a9aa4", "f4f6f8", 4))
    # the sail: floors whose front bulges out in a curve, a white spine at the back
    glass = ["8ab8d8", "7aaccc", "9ac4e0"][L - 1]
    for k in range(floors):
        t = k / floors
        bulge = 150 * np.sqrt(max(0.0, 1.0 - (t * 1.05) ** 2)) * (0.55 + 0.45 * np.sin(np.pi * min(1.0, t + 0.2)))
        f0 = 300 - bulge
        w = Win(w=12, h=20, sill=3, sp=16, margin=4, fh=fh, frame="f4f6f8", style="vertical", tint=glass, group="work", top_skip=0)
        fa = facade("plaster", "f8fafc", win=w, seed=seed + 1 + (k % 3), plinth=None, bands=[(fh - 3, fh, "f8fafc")], lit=0.55)
        box(T, 150, f0, 330, 420, pod + k * fh, pod + (k + 1) * fh, front=fa, back=fa, left=fa, right=fa, top=flat("eef2f4"))
    spine = facade("plaster", "fbfcfd", plinth=None, seed=seed + 9)
    T.box(140, 400, 340, 440, pod, H + 70, all=spine, top=flat("f4f6f8"))
    for s in (140, 326):
        T.box(s, 300, s + 14, 400, pod, H + 30, all=spine, top=flat("f4f6f8"))
    # helipad on a cantilever
    zh = pod + int(floors * 0.8) * fh
    hx, hy = T.pt(390, 360)
    T.cv.cylinder(hx, hy, 42, zh, zh + 5, solid_side("e8eaec"),
                  cap=lambda u, v: (np.where(((np.abs(u) < 4) & (np.abs(v) < 16)) | ((np.abs(v) < 3) & (np.abs(u) < 12))
                                             | (np.abs(np.hypot(u, v) - 34) < 2), 1, 0)[..., None] * C("f4f4f4")
                                    + np.where(((np.abs(u) < 4) & (np.abs(v) < 16)) | ((np.abs(v) < 3) & (np.abs(u) < 12))
                                               | (np.abs(np.hypot(u, v) - 34) < 2), 0, 1)[..., None] * C("3a8a5a"),
                                    nores(u.shape), None))
    T.box(340, 350, 370, 370, zh - 30, zh, all=flat("e8eaec"), top=flat("e8eaec"))
    # night light: the sail glows
    T.box(230, 438, 250, 442, H - 40, H + 60, all=lambda u, v, LL, HH: glow_res("a8d8ff", u.shape), top=flat("f4f6f8"))
    # lagoon with a bridge
    ground(T, 0, 0, 480, 300, kit.paving("e8dcc4", 10.0, 4))
    pool(T, 20, 120, 460, 290)
    slab(T, 200, 60, 280, 300, 1, 4, "f4f0e8")
    door(T, 110, 60, 300, 34)
    entry(T, 240)
    for (s, f) in ((40, 40), (160, 40), (320, 40), (440, 40)):
        palm(T, s, f, 66, seed + s)
    lamp(T, 196, 30, "modern", 48)
    lamp(T, 284, 30, "modern", 48, "light2")
    return cv


def hotel_grand(L, o):
    """A grand hotel skyscraper: dark glass with golden fins, a lit crown and a big sign."""
    floors = [24, 30, 36][L - 1]
    fh = 30
    pod = 3 * fh
    H = pod + floors * fh
    cv = Canvas(3, H + 260)
    T = Orient(cv, o)
    seed = 881
    gold = "d8a840"
    podf = facade("stone", "2e2a2c", shop=(30, 450, 40), doors=[(200, 80, 40, "double_glass")], plinth=None, seed=seed, lit=0.9,
                  win=Win(w=28, h=30, sill=40, sp=36, margin=10, fh=pod, frame=gold, group="work"), bands=[(pod - 6, pod, gold)])
    pods = facade("stone", "2e2a2c", win=Win(w=28, h=30, sill=40, sp=36, margin=10, fh=pod, frame=gold, group="work"), seed=seed + 1,
                  bands=[(pod - 6, pod, gold)])
    box(T, 20, 70, 460, 450, 0, pod, front=podf, back=pods, left=pods, right=pods, top=flat_top("5e8a4e", "7aa860", 6))
    canopy(T, 160, 320, 70, 34, 46, gold, "2a2a30", posts=True)
    door(T, 200, 80, 70, 40)
    entry(T, 240)
    win = Win(w=26, h=26, sill=2, sp=30, margin=4, fh=fh, frame="3a3438", style="vertical", tint="3a4a64", group="work", top_skip=1)
    fa = facade("concrete", "2a2a30", win=win, seed=seed + 2, plinth=None, lit=0.55)
    a0, a1, b0, b1 = 90, 390, 140, 400
    box(T, a0, b0, a1, b1, pod, H, all=fa, top=flat_top("5a5658", "2a2a30", 3))
    # golden fins up every face
    fin = facade("metal", gold, plinth=None, seed=seed + 3)
    for s in range(a0, a1 + 1, 50):
        T.box(s - 3, b0 - 8, s + 3, b0, pod, H + 20, all=fin, top=flat(gold))
    for f in range(b0, b1 + 1, 52):
        T.box(a1, f - 3, a1 + 8, f + 3, pod, H + 20, all=fin, top=flat(gold))
    # crown: lit gold tiers and a mast
    z = H
    for k, (dx, dy) in enumerate(((120, 100), (90, 76), (60, 52))):
        cs, cf = (a0 + a1) / 2, (b0 + b1) / 2
        T.box(cs - dx, cf - dy, cs + dx, cf + dy, z, z + 30, all=stripes_gold(12, gold, "3a2a20"), top=flat_top("5a5658", gold, 3))
        z += 30
    spire(T, (a0 + a1) / 2, (b0 + b1) / 2, z, [90, 110, 130][L - 1], "e8c060")
    sign_board(T, 240, b0 - 8, H - 60, "GRAND HOTEL", 14, "2a2a30", "f4d070")
    for k, ss in enumerate((40, 110, 370, 440)):
        palm(T, ss, 30, 60, seed + k)
    ground(T, 10, 0, 470, 70, kit.paving("d8d0c0", 12.0, 4))
    lamp(T, 140, 18, "classic", 55)
    lamp(T, 340, 18, "classic", 55, "light2")
    return cv


# ====================================================================== transport
def bus_stop(L, o):
    """A glass bus shelter with a bench, a timetable column and a stop sign."""
    cv = Canvas(1, 120)
    T = Orient(cv, o)
    seed = 901
    ground(T, 0, 0, 160, 80, kit.paving("c8c4bc", 8.0, 4))
    # the shelter, open to the street
    for (s, f) in ((30, 24), (130, 24), (30, 50), (130, 50)):
        post(T, s, f, 0, 30, "4a5058", 2.2)
    T.panel(30, 130, 50, 4, 30, lambda u, v, LL, HH: (C("a8c8d8") * np.ones(u.shape + (3,)), nores(u.shape),
                                                     np.where((v > 20)[..., None], np.array([200, 230, 255, 90.0]), 0) * np.ones(u.shape + (4,))), "s")
    slab(T, 24, 18, 136, 56, 30, 33, "e84a3a", flat("c83a2a"))
    T.box(40, 52, 120, 56, 0, 30, all=lambda u, v, LL, HH: (np.where((v > 10)[..., None], C("2a6ab0"), C("f4f0e8")) * np.ones(u.shape + (3,)),
                                                           nores(u.shape), np.where((v > 10)[..., None], np.array([200, 220, 255, 200.0]), 0)
                                                           * np.ones(u.shape + (4,))), top=flat("4a5058"))
    bench(T, 80, 40, "s", "6a4a30")
    # stop sign: a pole with a yellow-green plate
    post(T, 145, 18, 0, 46, "8a8a90", 1.8)
    sign_board(T, 145, 20, 38, "BUS", 8, "2a9a4a", "ffffff")
    entry(T, 80)
    door(T, 70, 20, 30, 24)
    tree(T, 18, 70, "lime", 0.55, seed)
    if L >= 2:
        flowerbed(T, 100, 62, 150, 76, seed + 1)
    if L >= 3:
        lamp(T, 10, 12, "modern", 46)
    return cv


def metro_station(L, o):
    """A metro entrance: a glass pavilion over stairs going down and a slender tower with a glowing M."""
    H = [90, 110, 130][L - 1]
    cv = Canvas(1, H + 60)
    T = Orient(cv, o)
    seed = 921
    ground(T, 0, 0, 160, 160, kit.paving("cfc8bc", 8.0, 4))
    # the stairwell: a dark opening with steps, glass walls and a curved roof
    T.flat(30, 20, 110, 90, 0.6, lambda u, v, LL, D: (np.where((np.mod(v, 8) < 1.2)[..., None], C("8a8a90"), C("4a4a50"))
                                                       * (0.4 + 0.6 * (v / 70.0))[..., None] * np.ones(u.shape + (1,)), nores(u.shape), None))
    for (s, f) in ((28, 18), (112, 18), (28, 92), (112, 92)):
        post(T, s, f, 0, 34, "c8ccd0", 2.4)
    T.panel(18, 92, 28, 0, 30, lambda u, v, LL, HH: (C("a8c8d8") * np.ones(u.shape + (3,)), nores(u.shape), None), "f")
    T.panel(18, 92, 112, 0, 30, lambda u, v, LL, HH: (C("a8c8d8") * np.ones(u.shape + (3,)), nores(u.shape), None), "f")
    T.panel(28, 112, 92, 0, 34, lambda u, v, LL, HH: (C("a8c8d8") * np.ones(u.shape + (3,)), nores(u.shape),
                                                     np.where((v > 24)[..., None], np.array([200, 230, 255, 120.0]), 0) * np.ones(u.shape + (4,))), "s")
    slab(T, 22, 12, 118, 98, 34, 37, "c8ccd0", flat("8a929a"))
    # the tower
    tw = facade("concrete", "e8e4dc", win=Win(w=8, h=20, sill=4, sp=14, margin=4, fh=30, frame="3a3a40", style="vertical", tint="8ab8d8",
                                              group="work"), plinth=None, seed=seed, lit=0.8)
    T.box(118, 100, 150, 132, 0, H, all=tw, top=flat_top("8a8884", "e8e4dc", 2))
    # a glowing red M on every face of the top
    def m_sign(u, v, LL, HH):
        x = u / max(LL, 1)
        y = v / max(HH, 1)
        stroke = (np.abs(x - 0.18) < 0.07) | (np.abs(x - 0.82) < 0.07) | (np.abs(np.abs(x - 0.5) - 0.32 * y) < 0.07) & (y > 0.3)
        stroke &= (y > 0.12) & (y < 0.88)
        rgb = np.where(stroke[..., None], C("ffffff"), C("d8282a")) * np.ones(u.shape + (1,))
        em = np.zeros(u.shape + (4,))
        em[...] = np.array([255, 60, 50, 200.0])
        em[stroke] = np.array([255, 255, 255, 255.0])
        return rgb, np.ones(u.shape, bool), em
    T.box(114, 96, 154, 136, H, H + 36, all=m_sign, top=flat("b82020"))
    T.cv.mark("light", *T.pt(134, 116), H + 40)
    entry(T, 70)
    door(T, 50, 40, 20, 30)
    bench(T, 70, 120, "s", "6a6a70")
    tree(T, 20, 130, "lime", 0.6, seed + 1)
    if L >= 2:
        flowerbed(T, 30, 140, 100, 154, seed + 2)
    if L >= 3:
        lamp(T, 150, 10, "modern", 46)
    return cv


# ====================================================================== dushanbe_tower: the landmark
def crane(T, s, f, z0, h, jib=150):
    """A yellow tower crane standing on the unfinished top."""
    yel = flat("f0b820", 3)
    T.box(s - 5, f - 5, s + 5, f + 5, z0, z0 + h, all=yel, top=yel)
    T.box(s - 40, f - 3, s + jib, f + 3, z0 + h, z0 + h + 6, all=yel, top=yel)
    T.box(s - 40, f - 6, s - 20, f + 6, z0 + h - 10, z0 + h, all=flat("8a8a90"), top=flat("8a8a90"))
    T.box(s + jib - 6, f - 1, s + jib - 4, f + 1, z0 + h - 60, z0 + h, all=flat("4a4a50"), top=flat("4a4a50"))


def dushanbe_tower(L, o):
    """Dushanbe Tower: a slender glass shaft rising to a sloped blade crown, two rounded glass towers
    with roof gardens at its feet. Level 1 is still being built, level 2 is topped out, level 3 is finished and lit."""
    fh = 20                       # the 77 floors are drawn at reduced scale so the tower fits on screen
    floors = 77 if L >= 2 else 46
    pod = 60
    H = pod + floors * fh
    cv = Canvas(3, pod + 77 * fh + 340)
    T = Orient(cv, o)
    seed = 951
    glass = "2f6aa8"
    lit = [0.25, 0.4, 0.6][L - 1]
    # podium: mall and lobby with a green roof
    podf = facade("stone", "d8d4cc", shop=(30, 450, 34), doors=[(200, 80, 40, "double_glass")], plinth=None, seed=seed, lit=0.8,
                  win=Win(w=28, h=24, sill=30, sp=34, margin=10, fh=pod, frame="3a3a40", group="work"))
    box(T, 10, 60, 470, 460, 0, pod, all=podf, top=flat_top("5e8a4e", "7aa860", 6))
    canopy(T, 180, 300, 60, 30, 44, "2e3238", "2e3238", posts=False)
    door(T, 200, 80, 60, 40)
    entry(T, 240)
    # main shaft: square glass tower that slims in three steps
    win = Win(w=10, h=14, sill=3, sp=13, margin=3, fh=fh, frame="b8cce0", style="vertical", tint=glass, group="work", top_skip=0)
    steps_ = [(150, 330, 200, 380), (162, 318, 212, 368), (174, 306, 224, 356)]
    zs = [pod, pod + int(floors * 0.45) * fh, pod + int(floors * 0.75) * fh, H]
    for k in range(3):
        s0, s1, f0, f1 = steps_[k]
        fa = facade("concrete", "a8c4dc", win=win, seed=seed + k, plinth=None, lit=lit)
        box(T, s0, f0, s1, f1, zs[k], zs[k + 1], all=fa, top=flat_top("8a929a", "dce4ec", 3))
        # silver fins up the corners
        fin = flat("e8eef4", 3)
        for a in (s0 - 3, s1 - 5):
            T.box(a, f0 - 4, a + 8, f0 + 4, zs[k], zs[k + 1] + 6, all=fin, top=fin)
    s0, s1, f0, f1 = steps_[2]
    if L == 1:
        crane(T, 240, 290, H, 120)
    else:
        # the blade crown: glass rising in a slope to a sharp point, lit at night when finished
        n = 18
        for k in range(n):
            t = k / n
            cut = s0 + (s1 - s0) * t
            z0 = H + k * 16
            crown = facade("concrete", "c8dcec", win=Win(w=8, h=10, sill=3, sp=12, margin=2, fh=16, frame="e8eef4", style="vertical",
                                                         tint="8ac0e8", group="work", top_skip=0), plinth=None, seed=seed + 10, lit=1.0 if L == 3 else 0.2)
            T.box(cut, f0 + 6, s1, f1 - 6, z0, z0 + 16, all=crown, top=flat("e8eef4"))
        spire(T, s1 - 6, (f0 + f1) / 2, H + n * 16, 70, "e8eef4", beacon=True)
        if L == 3:
            T.box(s1 - 2, (f0 + f1) / 2 - 3, s1 + 2, (f0 + f1) / 2 + 3, H, H + n * 16, all=lambda u, v, LL, HH: glow_res("bfe4ff", u.shape), top=flat("e8eef4"))
    # two rounded glass towers with bulging, vase-like profiles and gardens on top
    for k, (sc, fc, hh, r0) in enumerate(((80, 330, 0.42, 58), (400, 330, 0.36, 54))):
        th = int(77 * hh) if L == 3 else int(77 * hh * (0.7 if L == 1 else 0.9))
        cx, cy = T.pt(sc, fc)
        segs = max(4, th // 3)
        for j in range(segs):
            t = j / segs
            r = r0 * (0.82 + 0.28 * np.sin(np.pi * (0.15 + 0.8 * t)))
            z0 = pod + j * 3 * fh
            T.cv.cylinder(cx, cy, r, z0, z0 + 3 * fh, ring_glass(r, "5a8ab8", "e4eaf0", fh, 16, lit, seed + 20 + k, "f4f6f8"))
            tier_ring(T, cx, cy, r + 3, z0 + 3 * fh - 2, 2, "f4f6f8")
        zt = pod + segs * 3 * fh
        rt = r0 * (0.82 + 0.28 * np.sin(np.pi * 0.95))
        T.cv.cylinder(cx, cy, rt, zt, zt + 2, solid_side("f4f6f8"), cap=lambda u, v: (C("6a9a50") * np.ones(u.shape + (3,)), nores(u.shape), None))
        for j in range(5):
            a = j / 5 * 2 * np.pi
            T.cv.ellipsoid(cx + np.cos(a) * rt * 0.5, cy + np.sin(a) * rt * 0.5, zt + 6, 10, 10, 9, lambda wx, wy, wz, nx, ny, nz: (
                C("4a8a3a") * (0.75 + 0.35 * nz)[..., None] * np.ones(wx.shape + (1,)), nores(wx.shape), None))
    # lake and park in front
    ground(T, 0, 0, 480, 60, kit.paving("d0c8bc", 12.0, 4))
    pool(T, 30, 6, 160, 54)
    pool(T, 320, 6, 450, 54)
    for k, ss in enumerate((180, 300)):
        tree(T, ss, 20, "maple", 0.75, seed + 30 + k)
    lamp(T, 200, 14, "modern", 55)
    lamp(T, 280, 14, "modern", 55, "light2")
    return cv


BUILDERS = {"dushanbe_tower": dushanbe_tower, "round_tower": round_tower, "deco_tower": deco_tower, "stack_tower": stack_tower, "twin_towers": twin_towers,
            "hotel_boutique": hotel_boutique, "hotel_resort": hotel_resort, "hotel_palace": hotel_palace, "hotel_sail": hotel_sail,
            "hotel_grand": hotel_grand, "bus_stop": bus_stop, "metro_station": metro_station}
