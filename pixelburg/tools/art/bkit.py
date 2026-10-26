"""Oriented building helpers shared by every building module (front-relative s / f coordinates)."""
import math

import numpy as np

from raster import C, U, Canvas, flat, solid_res, glow_res, nores, hash2
from arch import Orient, facade, Win, roof_mat, flat_top, text_mask
import kit

S = U


def door(T, s0, w, f, h, name="door"):
    """Remember the main entrance: its screen corners for the door animation and the grid point."""
    T.mark(name + "_a", s0, f, 0)
    T.mark(name + "_b", s0 + w, f, 0)
    T.mark(name + "_t", s0, f, h)
    if name == "door":
        T.cv.door_g = T.grid(s0 + w / 2, f)


def entry(T, s):
    """Where the lot meets the sidewalk."""
    T.cv.entry_g = T.grid(s, 0)


def ground(T, s0, f0, s1, f1, fn, z=0.3):
    T.flat(s0, f0, s1, f1, z, fn, ground=True)


def tree(T, s, f, kind="oak", sc=1.0, seed=0, blossom=None):
    x, y = T.pt(s, f)
    if kind == "spruce":
        kit.conifer(T.cv, x, y, "spruce", sc, seed)
    elif kind == "pine":
        kit.pine(T.cv, x, y, sc, seed)
    elif kind == "poplar":
        kit.poplar(T.cv, x, y, sc, seed)
    else:
        kit.tree(T.cv, x, y, kind, sc, seed, blossom)


def bush(T, s, f, sc=1.0, seed=0, flowers=None):
    x, y = T.pt(s, f)
    kit.bush(T.cv, x, y, sc, seed, flowers)


def hedge(T, s0, f0, s1, f1, h=12, seed=0):
    x0, y0, x1, y1 = T.rect(s0, f0, s1, f1)
    kit.hedge(T.cv, x0, y0, x1, y1, h, seed)


def fence(T, a0, a1, b, along="s", col="f4f0e8", kind="picket", h=10, gap=None):
    """Fence along s (at f=b) or along f (at s=b), optional gate gap (g0, g1)."""
    parts = [(a0, a1)] if gap is None else [(a0, gap[0]), (gap[1], a1)]
    c = C(col)

    def fn(u, v, L, H):
        rgb = np.broadcast_to(c, u.shape + (3,)).copy()
        rgb *= (0.9 + 0.12 * hash2(np.floor(u / 3), 0, 1))[..., None]
        return rgb, nores(u.shape), None
    if kind == "picket":
        ext = lambda a, z: ((a % 3.0) < 1.8) | ((z > 3) & (z < 4.5)) | ((z > h - 3.5) & (z < h - 2))
    elif kind == "metal":
        ext = lambda a, z: ((a % 4.0) < 0.7) | (z > h - 1.0) | ((z > 1.0) & (z < 1.8)) | ((a % 32) < 1.2)
    elif kind == "rail":
        ext = lambda a, z: ((a % 2.2) < 0.5) | (z > h - 1.2) | ((a % 30) < 1.0)
    elif kind == "glass":
        ext = lambda a, z: z >= 0
    else:
        ext = lambda a, z: (a % 4.0) < 3.6
    for a, b2 in parts:
        if b2 - a > 0.5:
            T.panel(a, b2, b, 0 if kind != "glass" else 0, h, fn if kind != "glass" else glass_rail, along, ext)


def glass_rail(u, v, L, H):
    rgb = np.broadcast_to(C("9ec4d8"), u.shape + (3,)).copy()
    rgb[(v > H - 1.2) | (u < 0.8) | (u > L - 0.8)] = C("d8dce0")
    rgb[((u - v) % 11) < 1.5] = C("d4e6f0")
    return rgb, nores(u.shape), None


def flowerbed(T, s0, f0, s1, f1, seed=0):
    x0, y0, x1, y1 = T.rect(s0, f0, s1, f1)
    with T.cv.ground:
        kit.flowerbed(T.cv, x0, y0, x1, y1, seed)


def mailbox(T, s, f, col="3a6ad0"):
    x, y = T.pt(s, f)
    kit.mailbox(T.cv, x, y, col)


def lamp(T, s, f, style="classic", h=45, name="light"):
    x, y = T.pt(s, f)
    kit.lamp_post(T.cv, x, y, h, style, name)


def bench(T, s, f, along="s", col="9a6a40"):
    x, y = T.pt(s, f)
    ax = T.axis(along)
    if ax == "x":
        kit.bench(T.cv, x - 8, y - 2.5, "x", col)
    else:
        kit.bench(T.cv, x - 2.5, y - 8, "y", col)


def bins(T, s, f):
    x, y = T.pt(s, f)
    kit.wheelie_bins(T.cv, x - 7, y - 3)


def box(T, s0, f0, s1, f1, z0, z1, **walls):
    T.box(s0, f0, s1, f1, z0, z1, **walls)


def slab(T, s0, f0, s1, f1, z0, z1, col="e8e4dc", top=None):
    T.box(s0, f0, s1, f1, z0, z1, all=flat(col, 3), top=top or flat(col, 3))


def post(T, s, f, z0, z1, col="f2eee6", w=1.6):
    T.box(s - w / 2, f - w / 2, s + w / 2, f + w / 2, z0, z1, all=flat(col, 2), top=flat(col, 2))


def canopy(T, s0, s1, f_face, depth, z, col="e8e2d6", top_col="7a5a44", posts=True):
    """Flat canopy over an entrance, sticking out of the front face."""
    slab(T, s0, f_face - depth, s1, f_face, z, z + 2.5, col, flat(top_col, 4))
    if posts:
        post(T, s0 + 1.5, f_face - depth + 1.5, 0, z)
        post(T, s1 - 1.5, f_face - depth + 1.5, 0, z)


def steps(T, s0, s1, f_face, n=2, depth=4, col="c8c0b0"):
    for i in range(n):
        T.box(s0, f_face - depth * (n - i), s1, f_face, 0, (i + 1) * 1.8, all=flat(col, 4), top=flat(C(col) * 1.06, 4))


def awning(T, s0, s1, f_face, z, depth=14, drop=7, c1="d84a3a", c2="f6f2ea", w=6.0):
    """Striped shop awning on the front."""
    a, b = C(c1), C(c2)

    def stripe(u):
        return np.where(((np.floor(u / w) % 2) == 0)[..., None], a, b) * np.ones(u.shape + (3,))
    # sloped cloth: approximated by a stack of thin slabs stepping down
    n = 6
    for i in range(n):
        f0 = f_face - depth * (i + 1) / n
        f1 = f_face - depth * i / n
        zz = z - drop * (i + 1) / n
        def fn(u, v, L, H, i=i):
            return stripe(u), nores(u.shape), None
        T.box(s0, f0, s1, f1, zz, zz + 1.6, front=fn, back=fn, left=flat(c1), right=flat(c1),
              top=lambda u, v, L, D: (stripe(u + v * 0), nores(u.shape), None))
    # valance
    def val(u, v, L, H):
        return stripe(u), nores(u.shape), None
    T.panel(s0, s1, f_face - depth, z - drop - 4, z - drop, val, "s",
            extra=lambda u, v: v > 1.5 * (np.abs((u % w) - w / 2) / (w / 2)))


def balconies(T, s_list, f_face, floors, fh=30, w=26, depth=12, rail="glass", z_start=None, col="e8e4dc"):
    """A balcony per floor at each s in s_list, sticking out of the front face."""
    for fl in floors:
        z = (z_start if z_start is not None else 0) + fl * fh
        for s0 in s_list:
            slab(T, s0, f_face - depth, s0 + w, f_face, z, z + 2, col)
            if rail == "glass":
                T.panel(s0, s0 + w, f_face - depth, z + 2, z + 11, glass_rail, "s")
                T.panel(f_face - depth, f_face, s0 + w, z + 2, z + 11, glass_rail, "f")
                T.panel(f_face - depth, f_face, s0, z + 2, z + 11, glass_rail, "f")
            else:
                railf = lambda u, v, L, H: solid_res(C(rail), u.shape)
                ext = lambda u, v: ((u % 2.4) < 0.6) | (v > 7.8)
                T.panel(s0, s0 + w, f_face - depth, z + 2, z + 11, railf, "s", ext)
                T.panel(f_face - depth, f_face, s0 + w, z + 2, z + 11, railf, "f", ext)
                T.panel(f_face - depth, f_face, s0, z + 2, z + 11, railf, "f", ext)


def roof_units(T, s0, f0, s1, f1, z, seed=0, n=3, tank=False, stair=True):
    """AC units, vents and a stair hut on a flat roof."""
    rng = np.random.default_rng(seed)
    if stair:
        ss = s0 + (s1 - s0) * 0.62
        ff = f0 + (f1 - f0) * 0.35
        w = facade("plaster", "d8d2c6", plinth=None, doors=[(4, 9, 20, "panel", "6a6a70")])
        T.box(ss, ff, ss + 26, ff + 22, z, z + 26, all=w, top=flat_top("8a8884", "c8c2b8", 2))
    for i in range(n):
        s = rng.uniform(s0 + 8, s1 - 18)
        f = rng.uniform(f0 + 8, f1 - 16)
        x, y = T.pt(s, f)
        kit.ac_unit(T.cv, x - 5, y - 4, z, 10, 8, 7)
    if tank:
        x, y = T.pt(s0 + (s1 - s0) * 0.25, f0 + (f1 - f0) * 0.6)
        kit.water_tank(T.cv, x, y, z, 8, 14)


def parking_lot(T, s0, f0, s1, f1, along="s", step=26.0, z=0.4, col="5a5c62"):
    """Asphalt parking with painted bays. Bays line up along `along`."""
    x0, y0, x1, y1 = T.rect(s0, f0, s1, f1)
    ax = T.axis(along)
    lines = ("u" if ax == "x" else "v", 0.0, step, 6.0, 44.0)
    with T.cv.ground:
        T.cv.top(z, x0, y0, x1, y1, kit.asphalt_lot(col, 4, lines), shade=1.0)


def sign_board(T, s_center, f, z, text, th=10, bg="2a3a5a", fg="f4f0e0", glow=True, depth=1.5):
    """A sign mounted on a wall at f (facing the front)."""
    tm = text_mask(text, th)
    w = tm.shape[1] + 8
    fn = facade("plaster", bg, plinth=None, signs=[(w / 2, 4, text, th, None, fg, glow)])
    T.box(s_center - w / 2, f - depth, s_center + w / 2, f, z, z + th + 8, front=fn, back=flat(bg), left=flat(bg), right=flat(bg),
          top=flat(bg))
    return w


def pole_sign(T, s, f, z_top, text, th=12, bg="d84a3a", fg="ffffff"):
    post(T, s, f, 0, z_top - th - 8, "8a8a90", 2.4)
    tm = text_mask(text, th)
    w = tm.shape[1] + 8
    fn = facade("plaster", bg, plinth=None, signs=[(w / 2, 4, text, th, None, fg, True)])
    T.box(s - w / 2, f - 2, s + w / 2, f + 2, z_top - th - 8, z_top, front=fn, back=fn, left=flat(bg), right=flat(bg), top=flat(bg))


def car_static(T, s, f, along="s", col="c84a3a"):
    """A parked car as part of a building (only on decorative lots)."""
    x, y = T.pt(s, f)
    ax = T.axis(along)
    l, w, h = 44, 18, 14
    body = flat(col, 4)
    glass = flat("3a4a5a", 3)
    if ax == "x":
        T.cv.box(x - l / 2, y - w / 2, 3, x + l / 2, y + w / 2, 9, body, body, body)
        T.cv.box(x - l / 4, y - w / 2 + 1, 9, x + l / 5, y + w / 2 - 1, 14, glass, glass, flat(col, 3))
    else:
        T.cv.box(x - w / 2, y - l / 2, 3, x + w / 2, y + l / 2, 9, body, body, body)
        T.cv.box(x - w / 2 + 1, y - l / 4, 9, x + w / 2 - 1, y + l / 5, 14, glass, glass, flat(col, 3))


def blade_sign(T, s, f_face, z, text, bg="2a3a5a", fg="f4f0e0", th=6):
    """A sign sticking out of the wall, readable from the side."""
    tm = text_mask(text, th)
    w = tm.shape[1] + 8
    fn = facade("plaster", bg, plinth=None, signs=[(w / 2, (14 - th) / 2, text, th, None, fg, True)])
    T.box(s - 1, f_face - w - 3, s + 1, f_face - 3, z, z + 14, front=flat(bg), back=flat(bg), left=fn, right=fn, top=flat(bg))
    post(T, s, f_face - 1.5, z + 6, z + 8, "3a3a40", 1.0)
