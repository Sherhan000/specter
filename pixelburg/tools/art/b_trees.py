"""New kinds of trees placed as decoration: each kind has its own look (roadmap 13).
Higher levels add trees and a small thing beneath them."""
import numpy as np

from raster import C, Canvas, flat, solid_res, nores
from arch import Orient
import kit
from bkit import bush, bench, box, lamp


def _plant(T, fn, s, f, sc, seed):
    x, y = T.pt(s, f)
    fn(T.cv, x, y, sc, seed)


def _grove(L, o, fn, spots, zmax=150, seed=0):
    """spots: (s, f, scale) - the first L+(extra) are used, more with every level."""
    cv = Canvas(1, zmax)
    T = Orient(cv, o)
    for k, (s, f, sc) in enumerate(spots[L - 1]):
        _plant(T, fn, s, f, sc, seed + k)
    return cv, T


def _birch(cv, x, y, s, seed):
    kit.tree(cv, x, y, "birch", s, seed)


def _pines(cv, x, y, s, seed):
    if seed % 2:
        kit.conifer(cv, x, y, "spruce", s * 0.9, seed)
    else:
        kit.pine(cv, x, y, s, seed)


def _poplar(cv, x, y, s, seed):
    kit.poplar(cv, x, y, s, seed)


def _apple_box(T, s, f):
    T.box(s, f, s + 10, f + 8, 0, 6, all=flat("b8864a", 10), top=flat("c8965a", 8))
    x, y = T.pt(s + 5, f + 4)
    for i in range(4):
        T.cv.ellipsoid(x - 3 + i * 2, y - 1 + (i % 2) * 2, 7, 1.8, 1.8, 1.8,
                       lambda wx, wy, wz, nx, ny, nz: solid_res(C("d8302a") * (0.75 + 0.35 * nz[..., None]), wx.shape))


def _stone_lantern(T, s, f):
    """Japanese stone lantern (toro) under the sakura."""
    st, top = flat("9a968e", 8), flat("aaa69e", 6)
    T.box(s - 4, f - 4, s + 4, f + 4, 0, 3, all=st, top=top)
    T.box(s - 1.5, f - 1.5, s + 1.5, f + 1.5, 3, 14, all=st, top=top)
    T.box(s - 4, f - 4, s + 4, f + 4, 14, 20, all=flat("8a867e", 8), top=top)
    T.box(s - 6, f - 6, s + 6, f + 6, 20, 23, all=st, top=top)
    T.box(s - 1.5, f - 1.5, s + 1.5, f + 1.5, 23, 26, all=st, top=top)


def _tapchan(T, s, f):
    """Wooden tapchan with a red rug and a low table, under the chinar."""
    wood = flat("8a5a34", 8)
    T.box(s, f, s + 30, f + 24, 0, 8, all=wood, top=flat("9a6a40", 6))

    def rug(u, v, L, D):
        rgb = np.broadcast_to(C("b8302a"), u.shape + (3,)).copy()
        edge = (u < 3) | (v < 3) | (u > L - 3) | (v > D - 3)
        rgb[edge] = C("e8c050")
        mid = (np.abs(u - L / 2) + np.abs(v - D / 2)) < 6
        rgb[mid] = C("2a4a8a")
        return rgb, nores(u.shape), None
    T.box(s + 2, f + 2, s + 28, f + 22, 8, 9, all=flat("b8302a", 4), top=rug)
    T.box(s + 11, f + 8, s + 19, f + 16, 9, 13, all=wood, top=flat("6a4428", 6))


def _lounger(T, s, f):
    T.box(s, f, s + 8, f + 22, 0, 4, all=flat("f4f0e8", 4), top=flat("3a8ad0", 4))


def tree_pine(L, o):
    spots = [[(80, 80, 1.0)], [(60, 70, 1.0), (115, 110, 0.95)], [(55, 65, 1.05), (115, 110, 0.95), (40, 125, 0.8)]]
    cv, T = _grove(L, o, _pines, spots, 170, 1300)
    return cv


def tree_birch(L, o):
    spots = [[(65, 75, 1.0), (105, 100, 0.85)], [(55, 60, 1.0), (105, 95, 0.9), (60, 120, 0.8)],
             [(50, 55, 1.0), (105, 70, 0.9), (60, 115, 0.85), (115, 125, 0.75)]]
    cv, T = _grove(L, o, _birch, spots, 140, 1310)
    return cv


def tree_sakura(L, o):
    spots = [[(80, 80, 0.9)], [(80, 80, 1.0)], [(65, 70, 1.05), (125, 125, 0.7)]]
    cv, T = _grove(L, o, kit.sakura, spots, 100, 1320)
    if L >= 2:
        _stone_lantern(T, 130, 40)
    return cv


def tree_apple(L, o):
    spots = [[(80, 80, 1.0)], [(60, 65, 1.0), (115, 110, 0.9)], [(50, 55, 1.0), (115, 70, 0.9), (70, 120, 0.9)]]
    cv, T = _grove(L, o, kit.apple, spots, 100, 1330)
    if L >= 2:
        _apple_box(T, 125, 130)
    if L >= 3:
        _apple_box(T, 135, 140)
    return cv


def tree_willow(L, o):
    spots = [[(80, 80, 0.85)], [(80, 80, 1.0)], [(75, 75, 1.1)]]
    cv, T = _grove(L, o, kit.willow, spots, 110, 1340)
    if L >= 2:
        bush(T, 140, 30, 0.8, 1341)
        bush(T, 25, 140, 0.8, 1342)
    if L >= 3:
        bench(T, 130, 135, "s")
    return cv


def tree_palm(L, o):
    spots = [[(80, 80, 1.0)], [(60, 70, 1.0), (115, 105, 0.85)], [(55, 60, 1.05), (115, 95, 0.85), (60, 125, 0.75)]]
    cv, T = _grove(L, o, kit.palm, spots, 140, 1350)
    if L >= 3:
        _lounger(T, 125, 20)
    return cv


def tree_chinar(L, o):
    spots = [[(80, 80, 0.85)], [(80, 80, 1.0)], [(75, 75, 1.1)]]
    cv, T = _grove(L, o, kit.chinar, spots, 140, 1360)
    if L >= 2:
        _tapchan(T, 105, 110)
    if L >= 3:
        lamp(T, 20, 140, "lantern", 38)
    return cv


def tree_poplar(L, o):
    spots = [[(50, 50, 0.95), (110, 110, 0.9)], [(40, 40, 1.0), (80, 80, 0.95), (120, 120, 0.9)],
             [(30, 30, 1.0), (65, 65, 0.95), (100, 100, 0.95), (135, 135, 0.9)]]
    cv, T = _grove(L, o, _poplar, spots, 150, 1370)
    return cv


def tree_autumn(L, o):
    spots = [[(80, 80, 1.0)], [(60, 65, 1.0), (115, 110, 0.85)], [(50, 55, 1.0), (115, 75, 0.85), (70, 120, 0.85)]]
    cv, T = _grove(L, o, kit.autumn, spots, 110, 1380)
    if L >= 3:
        bench(T, 125, 135, "s")
    return cv


BUILDERS = {"tree_pine": tree_pine, "tree_birch": tree_birch, "tree_sakura": tree_sakura, "tree_apple": tree_apple,
            "tree_willow": tree_willow, "tree_palm": tree_palm, "tree_chinar": tree_chinar, "tree_poplar": tree_poplar,
            "tree_autumn": tree_autumn}
