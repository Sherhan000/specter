"""Markets: a single stall, an open-air market with rows of awnings and a covered bazaar hall."""
import numpy as np

from raster import C, U, Canvas, flat
from arch import Orient, facade, Win, roof_mat, flat_top
import kit
from bkit import ground, tree, lamp, bench, box, slab, post, awning, sign_board, entry, door, canopy

AW = [("d8402e", "f6f2ea"), ("2e8a4a", "f6f2ea"), ("e8a82a", "f6f2ea"), ("2e6ab8", "f6f2ea"), ("a83a8a", "f6f2ea")]
PRODUCE = ["d8402e", "e8a82a", "6ab83a", "8a3a8a", "e87a2a", "f0d84a"]


def _stall(T, s, f, w, k, seed, h=30):
    """A wooden counter with crates of produce and a striped awning over it (facing the front)."""
    T.box(s, f, s + w, f + 14, 0, 12, all=flat("8a6440", 3), top=flat("b88a58", 3))
    for j in range(int(w // 10)):
        c = PRODUCE[(seed + j * 3 + k) % len(PRODUCE)]
        T.box(s + 2 + j * 10, f + 2, s + 9 + j * 10, f + 11, 12, 16, all=flat("a07a4a", 2), top=flat(c, 4))
    post(T, s + 1, f + 13, 0, h, "7a5a3a", 2.2)
    post(T, s + w - 1, f + 13, 0, h, "7a5a3a", 2.2)
    c1, c2 = AW[(seed + k) % len(AW)]
    awning(T, s - 1, s + w + 1, f + 15, h, 16, 7, c1, c2, 5.0)


def market_stall(L, o):
    """One market stall: a counter with produce, a striped awning and a crate stack beside it."""
    cv = Canvas(1, 70)
    T = Orient(cv, o)
    ground(T, 0, 0, 160, 160, kit.paving("c8bea8", 8.0, 4))
    _stall(T, 40, 50, 60, 0, 11)
    for k in range(3):
        T.box(112, 60 + k * 2, 132, 76 + k * 2, k * 10, k * 10 + 10, all=flat("a07a4a", 2), top=flat(PRODUCE[k * 2], 4))
    entry(T, 80)
    if L >= 2:
        T.box(20, 100, 36, 116, 0, 10, all=flat("8a6a44", 2), top=flat("e8a82a", 4))
        T.box(124, 110, 140, 126, 0, 8, all=flat("a07a4a", 2), top=flat("6ab83a", 4))
    if L >= 3:
        bench(T, 50, 120, "s", "8a6a40")
        lamp(T, 144, 20, "classic", 40)
    return cv


def market(L, o):
    """An open-air market: two rows of striped stalls around a paved square, crates, a tree and a lamp."""
    cv = Canvas(2, 80)
    T = Orient(cv, o)
    seed = 21
    ground(T, 0, 0, 320, 320, kit.paving("c4baa0", 10.0, 4))
    ground(T, 40, 60, 280, 260, kit.paving("d4c8ac", 10.0, 3))
    n = 3 + (L >= 2)
    for k in range(n):
        _stall(T, 52 + k * (216 // n), 200, 216 // n - 14, k, seed)
    for k in range(n):
        _stall(T, 52 + k * (216 // n), 96, 216 // n - 14, k + 2, seed + 5)
    for k in range(4):
        T.box(40 + k * 4, 140 + k * 14, 56 + k * 4, 154 + k * 14, 0, 9, all=flat("a07a4a", 2), top=flat(PRODUCE[(k + 1) % 6], 4))
    T.box(240, 140, 262, 170, 0, 12, all=flat("a07a4a", 2), top=flat("f0d84a", 4))
    pole = 18
    post(T, 160, 170, 0, 42, "6a4a2a", 3.2)
    T.box(130, 142, 190, 198, 42, 45, all=flat("e8e2d4", 2), top=flat("c8302a", 4))
    entry(T, 160)
    if L >= 2:
        tree(T, 20, 40, "lime", 0.7, 5)
        tree(T, 300, 40, "lime", 0.7, 6)
    if L >= 3:
        lamp(T, 40, 20, "classic", 44)
        lamp(T, 280, 20, "classic", 44)
        bench(T, 150, 30, "s", "8a6a40")
    return cv


def bazaar(L, o):
    """A covered bazaar: a long hall with a pitched roof, a big arched entrance with a sign and stalls on the forecourt."""
    H = 52
    cv = Canvas(3, H + 72)
    T = Orient(cv, o)
    seed = 31
    ground(T, 0, 0, 480, 480, kit.paving("c8c0ac", 10.0, 4))
    win = Win(w=16, h=14, sill=30, sp=40, margin=14, fh=H, frame="3a2a1e", style="vertical", tint="9ab8c8", group="shop")
    fr = facade("plaster", "e6cf9a", win=win, doors=[(190, 100, 40, "double_glass")], plinth=("7a5a44", 5), seed=seed, lit=0.9,
                cornice=("b8602e", 5))
    sd = facade("plaster", "e6cf9a", win=win, plinth=("7a5a44", 5), seed=seed + 1, lit=0.9, cornice=("b8602e", 5))
    box(T, 40, 190, 440, 440, 0, H, front=fr, back=sd, left=sd, right=sd)
    T.gable(40, 190, 440, 440, H, 36, roof_mat("b8602e", "tiles"), dict(all=sd), ridge="s", o=5)
    canopy(T, 180, 300, 190, 28, 40, "b8602e", "8a3a1e", posts=True)
    sign_board(T, 240, 188, 44, "BAZAAR", 12, "2a1a10", "ffd84a")
    door(T, 190, 100, 190, 40)
    entry(T, 240)
    n = 4 + (L >= 2)
    for k in range(n):
        _stall(T, 30 + k * (420 // n), 120, 420 // n - 18, k, seed)
    for k in range(3):
        T.box(40 + k * 14, 40 + k * 6, 56 + k * 14, 56 + k * 6, 0, 10, all=flat("a07a4a", 2), top=flat(PRODUCE[k], 4))
    if L >= 2:
        tree(T, 20, 60, "lime", 0.8, 8)
        tree(T, 460, 60, "lime", 0.8, 9)
    if L >= 3:
        lamp(T, 140, 70, "classic", 48)
        lamp(T, 340, 70, "classic", 48, "light2")
        bench(T, 240, 50, "s", "8a6a40")
    return cv


BUILDERS = {"market_stall": market_stall, "market": market, "bazaar": bazaar}
