"""Residents' own brands (all names and emblems are invented for the game): every brand has its colours,
a sign word and a simple emblem, and opens three kinds of places: a kiosk, a shop and a 2x2 flagship.
builder(L, o) -> Canvas; ids are <brand>_kiosk, <brand>_shop, <brand>_flag."""
import math

import numpy as np

from raster import C, Canvas, flat, nores
from arch import Orient, facade, Win, flat_top
import kit
from bkit import (door, entry, ground, tree, bush, lamp, bench, box, slab, post, awning, sign_board, car_static, canopy)
from b_city30 import _small_shop

# sign: Latin word on the sign; main / dark / light: brand colours; logo: emblem shape
BRANDS = {
    "ezhik": dict(sign="EZHIK", main="e87aa8", dark="6a3a2a", light="fbe6ee", logo="heart", mat="plaster"),
    "kot": dict(sign="KOT", main="2a7a6a", dark="1e3a34", light="f4e6c8", logo="cup", mat="wood"),
    "listik": dict(sign="LISTIK", main="3a9a4a", dark="1e5a2a", light="eef6e4", logo="leaf", mat="plaster"),
    "zaryadik": dict(sign="ZARYADIK", main="2a5ad8", dark="1a2a5a", light="e8eef8", logo="bolt", mat="metal"),
    "nitka": dict(sign="NITKA", main="7a3a9a", dark="2a1a3a", light="f2e8f4", logo="diamond", mat="tile"),
    "pixelburger": dict(sign="PIXELBURGER", main="d83a2a", dark="3a1a14", light="f8c830", logo="star", mat="tile"),
}


# ====================================================================== emblems
def _poly(x, y, pts):
    """Even-odd point-in-polygon test for arrays x, y."""
    inside = np.zeros(x.shape, bool)
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        cond = ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / ((y1 - y0) or 1e-9) + x0)
        inside ^= cond
    return inside


def _star_pts(r0=0.95, r1=0.42):
    return [((r0 if k % 2 == 0 else r1) * math.cos(math.pi / 2 + k * math.pi / 5),
             (r0 if k % 2 == 0 else r1) * math.sin(math.pi / 2 + k * math.pi / 5)) for k in range(10)]


def emblem(shape, x, y):
    """Mask of an emblem in unit coordinates (x right, y up, about -1..1)."""
    if shape == "heart":
        a, b = x * 1.25, y * 1.25 + 0.25
        return (a * a + b * b - 1) ** 3 - a * a * b ** 3 <= 0
    if shape == "star":
        return _poly(x, y, _star_pts())
    if shape == "leaf":
        u, w = (x + y) / 1.414, (y - x) / 1.414
        body = (u / 0.92) ** 2 + (w / 0.48) ** 2 <= 1
        vein = (np.abs(w) < 0.06) & (np.abs(u) < 0.8)
        stem = (np.abs(w) < 0.07) & (u < -0.8) & (u > -1.2)
        return (body & ~vein) | stem
    if shape == "cup":
        body = (np.abs(x + 0.12) < 0.5) & (y > -0.7) & (y < 0.15)
        handle = ((x - 0.42) ** 2 + (y + 0.25) ** 2 < 0.3 ** 2) & ((x - 0.42) ** 2 + (y + 0.25) ** 2 > 0.16 ** 2) & (x > 0.38)
        saucer = (np.abs(x + 0.12) < 0.75) & (y > -0.86) & (y < -0.74)
        steam = (y > 0.3) & (y < 0.9) & ((np.abs(x + 0.32 - 0.12 * np.sin(y * 9)) < 0.07) | (np.abs(x + 0.02 - 0.12 * np.sin(y * 9 + 2)) < 0.07))
        return body | handle | saucer | steam
    if shape == "bolt":
        return _poly(x, y, [(0.15, 0.95), (-0.55, -0.1), (-0.05, -0.1), (-0.2, -0.95), (0.55, 0.15), (0.05, 0.15), (0.35, 0.95)])
    if shape == "diamond":
        top = _poly(x, y, [(-0.85, 0.3), (-0.45, 0.75), (0.45, 0.75), (0.85, 0.3)])
        bottom = _poly(x, y, [(-0.85, 0.22), (0.85, 0.22), (0.0, -0.9)])
        return top | bottom
    return x * x + y * y < 0.8


def logo_face(br, round_bg=True, glow=True):
    """A wall texture with the brand's emblem: light disc on the brand colour, emblem in the brand colour."""
    main, light, shape = C(br["main"]), C(br["light"]), br["logo"]

    def fn(u, v, L, H):
        s = min(L, H) / 2.0
        x = (u - L / 2.0) / (s * 0.82)
        y = (v - H / 2.0) / (s * 0.82)
        rgb = np.broadcast_to(main, u.shape + (3,)).copy()
        disc = (x * x + y * y) < 1.18 if round_bg else np.ones(u.shape, bool)
        rgb[disc] = light
        m = emblem(shape, x * 1.25, y * 1.25) & disc
        rgb[m] = main
        em = None
        if glow:
            em = np.zeros(u.shape + (4,))
            em[disc] = np.append(light, 150)
            em[m] = np.append(main, 230)
        return rgb, nores(u.shape), em
    return fn


def logo_cube(T, s, f, z, w, br, depth=4.0):
    """A square light box with the emblem on every side."""
    lf = logo_face(br)
    T.box(s - w / 2, f - depth / 2, s + w / 2, f + depth / 2, z, z + w, front=lf, back=lf, left=flat(br["main"], 2),
          right=flat(br["main"], 2), top=flat(br["main"], 2))


def logo_pylon(T, s, f, h, br, w=22):
    """A tall pylon in brand colours with the emblem at the top."""
    T.box(s - 3, f - 3, s + 3, f + 3, 0, h - w, all=flat(br["dark"], 2), top=flat(br["dark"], 2))
    logo_cube(T, s, f, h - w, w, br, 5)


def _brand_ground(T, s1, f1, seed):
    ground(T, 0, 0, s1, f1, kit.paving("d0c8bc", 8.0, seed))


def _seed(bid):
    return sum(ord(c) for c in bid) * 7


# ====================================================================== kiosk (1x1)
def kiosk(br, bid):
    def build(L, o):
        sd = _seed(bid)
        cv = Canvas(1, 130)
        T = Orient(cv, o)
        _brand_ground(T, 160, 160, sd)
        s0, s1, f0, f1 = 36, 124, 56, 118
        H = 32
        fr = facade("plaster", br["light"], shop=(6, 82, 24), doors=[(60, 14, 24, "glass")], seed=sd, plinth=(br["dark"], 3),
                    bands=[(H - 5, H, br["main"])])
        sd_w = facade(br["mat"], br["main"], seed=sd + 1, plinth=(br["dark"], 3), bands=[(H - 5, H, br["light"])])
        box(T, s0, f0, s1, f1, 0, H, front=fr, back=sd_w, left=sd_w, right=sd_w, top=flat_top("8a8884", br["main"], 3))
        slab(T, s0 - 4, f0 - 6, s1 + 4, f1 + 4, H, H + 3, br["dark"], flat(br["main"], 2))
        sign_board(T, (s0 + s1) / 2 - 10, f0 - 6, H + 3, br["sign"], 8, br["main"], br["light"] if br["light"] != br["main"] else "ffffff")
        logo_cube(T, s1 - 14, f0 + 4, H + 3, 20, br)
        awning(T, s0 + 4, s1 - 4, f0, 24, 10, 5, br["main"], br["light"])
        door(T, s0 + 60, 14, f0, 24)
        entry(T, s0 + 67)
        if L >= 2:
            bench(T, 20, 40, "f", br["dark"])
            bush(T, 140, 30, 0.5, sd + 2)
        if L >= 3:
            logo_pylon(T, 16, 14, 64, br, 18)
            bush(T, 142, 70, 0.55, sd + 5, "f4d040")
            lamp(T, 140, 14, "modern", 44)
        return cv
    return build


# ====================================================================== shop (1x1)
def shop(br, bid):
    def build(L, o):
        sd = _seed(bid) + 11
        fg = br["light"] if br["light"] != br["main"] else "ffffff"
        cv, T, H = _small_shop(L, o, sd, br["sign"], br["light"], br["mat"], br["main"], fg, floors=[1, 2, 2][L - 1])
        awning(T, 26, 134, 44, 33, 12, 6, br["main"], br["light"], 7.0)
        # emblem light box on the roof edge and a blade with the emblem on the corner
        logo_cube(T, 80, 52, H, 28, br, 5)
        T.box(14, 40, 18, 46, 10, 40, all=flat(br["dark"], 2), top=flat(br["dark"], 2))
        T.box(10, 30, 18, 34, 18, 38, front=logo_face(br), back=logo_face(br), left=flat(br["main"]), right=flat(br["main"]),
              top=flat(br["main"]))
        if L >= 2:
            for s in (120, 140):
                x, y = T.pt(s, 22)
                bush(T, s, 22, 0.45, sd + s, br["main"] if br["logo"] in ("heart", "diamond") else None)
            bench(T, 40, 22, "s", br["dark"])
        if L >= 3:
            slab(T, 22, 50, 138, 124, H, H + 2, "d8d2c6")
            for s in (40, 120):
                x, y = T.pt(s, 110)
                kit.ac_unit(cv, x, y, H + 2)
            lamp(T, 150, 14, "modern", 44)
        return cv
    return build


# ====================================================================== flagship (2x2)
def flagship(br, bid):
    def build(L, o):
        sd = _seed(bid) + 23
        cv = Canvas(2, 190)
        T = Orient(cv, o)
        _brand_ground(T, 320, 320, sd)
        # car park in front
        ground(T, 16, 12, 200, 104, kit.asphalt_lot("54565c", sd, ("u", 0.0, 26.0, 6.0, 44.0)), 0.4)
        s0, s1, f0, f1 = 24, 296, 130, 296
        H = [46, 70, 94][L - 1]
        fl = [1, 2, 3][L - 1]
        upper = Win(w=22, h=18, sill=6, sp=30, margin=14, fh=24, frame=br["light"], group="flats")
        fr = facade("plaster", br["light"], win=upper if fl > 1 else None, shop=(14, 258, 32), doors=[(118, 36, 30, "double")],
                    seed=sd, plinth=(br["dark"], 4), skip=[(0, 272, 0, 46)] if fl > 1 else (),
                    bands=[(42, 46, br["main"])] + ([(H - 4, H, br["main"])] if fl > 1 else []))
        side = facade(br["mat"], br["main"], seed=sd + 1, plinth=(br["dark"], 4), bands=[(42, 46, br["light"])])
        box(T, s0, f0, s1, f1, 0, H, front=fr, back=side, left=side, right=side, top=flat_top("8a8884", br["main"], 3))
        canopy(T, s0 + 100, s0 + 172, f0, 18, 36, br["main"], br["dark"])
        sign_board(T, (s0 + s1) / 2 - 40, f0, 34 if fl == 1 else H - 20, br["sign"], 14, br["main"],
                   br["light"] if br["light"] != br["main"] else "ffffff")
        # big emblem on the roof
        logo_cube(T, s1 - 50, f0 + 18, H, 52, br, 6)
        # brand-coloured parapet, glass skylights and roof units
        for a in ((s0, f0, s1, f0 + 3), (s0, f1 - 3, s1, f1), (s0, f0, s0 + 3, f1), (s1 - 3, f0, s1, f1)):
            T.box(*a, H, H + 5, all=flat(br["main"], 2), top=flat(br["light"], 2))
        for ss in (s0 + 40, s0 + 100, s0 + 160):
            T.box(ss, f0 + 50, ss + 36, f0 + 120, H, H + 4, all=flat(br["dark"], 2), top=flat("8ab8d0", 6))
        for ss in (s0 + 30, s0 + 210):
            x, y = T.pt(ss, 250)
            kit.ac_unit(cv, x, y, H)
        door(T, s0 + 118, 36, f0, 30)
        entry(T, s0 + 136 if s0 + 136 > 200 else 230)
        # parked cars and the brand pylon
        for k, col in enumerate(["c84a3a", "2a6ab0", "f4f2ee"][:L + 1]):
            car_static(T, 40 + k * 52, 60, "f", col)
        logo_pylon(T, 296, 24, 110, br, 28)
        tree(T, 220, 20, "lime", 0.6, sd + 3)
        tree(T, 300, 110, "oak", 0.6, sd + 4)
        if L >= 2:
            for ss in (210, 250):
                bench(T, ss, 116, "s", br["dark"])
            awning(T, s0 + 10, s0 + 96, f0, 34, 12, 6, br["main"], br["light"], 8.0)
        if L >= 3:
            logo_cube(T, s0 + 40, f0 + 18, H, 34, br, 5)
            lamp(T, 210, 70, "modern", 50)
            lamp(T, 10, 110, "modern", 50)
            bush(T, 260, 116, 0.6, sd + 9, "f4d040")
        return cv
    return build


BUILDERS = {}
for _bid, _br in BRANDS.items():
    BUILDERS[_bid + "_kiosk"] = kiosk(_br, _bid + "_kiosk")
    BUILDERS[_bid + "_shop"] = shop(_br, _bid + "_shop")
    BUILDERS[_bid + "_flag"] = flagship(_br, _bid + "_flag")
