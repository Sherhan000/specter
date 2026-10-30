"""Airport: a glass terminal, a control tower, a runway with markings and airliners on the apron."""
from raster import C, U, Canvas, flat
from arch import Orient, facade, Win
from bkit import ground, lamp, box, slab, post, sign_board, entry, tree, parking_lot

S = U * 4


def _runway(T):
    ground(T, 0, 0, S, S, flat("a8aaa4", 6))
    ground(T, 10, 440, S - 10, 580, flat("4a4c50", 6), 0.5)
    for k in range(14):
        s = 40 + k * 42
        ground(T, s, 507, s + 22, 513, flat("f4f4f0", 1), 0.7)
    for k in range(5):
        for s in (20, S - 44):
            ground(T, s, 452 + k * 24, s + 24, 462 + k * 24, flat("f4f4f0", 1), 0.7)
    ground(T, 480, 230, 520, 440, flat("5a5c60", 5), 0.45)
    ground(T, 497, 240, 503, 440, flat("e8c83a", 1), 0.6)
    ground(T, 40, 230, 470, 430, flat("8e908c", 6), 0.45)
    for k in range(4):
        ground(T, 60 + k * 100, 236, 64 + k * 100, 424, flat("e8c83a", 1), 0.6)


def _plane(T, s, f, sc=1.0, col="2a6ab8"):
    """An airliner nose to +s: fuselage, wings with engines, tail fin and stabilisers."""
    body = dict(all=flat("f4f4f2", 3), top=flat("ffffff", 4))
    L, R = 180 * sc, 12 * sc
    T.box(s, f - R, s + L, f + R, 8 * sc, 30 * sc, **body)
    T.box(s + L, f - R * 0.7, s + L + 14 * sc, f + R * 0.7, 10 * sc, 26 * sc, **body)
    T.box(s + 20 * sc, f - R - 0.5, s + L - 20 * sc, f + R + 0.5, 20 * sc, 23 * sc, all=flat(col, 2), top=flat(col, 3))
    T.box(s + L - 4 * sc, f - R * 0.6, s + L + 10 * sc, f + R * 0.6, 22 * sc, 27 * sc, all=flat("3a4a5a", 2), top=flat("3a4a5a", 2))
    wing = dict(all=flat("dcdcda", 2), top=flat("e8e8e6", 3))
    T.box(s + 70 * sc, f - 75 * sc, s + 110 * sc, f + 75 * sc, 15 * sc, 19 * sc, **wing)
    for df in (-42, 42):
        T.box(s + 82 * sc, f + (df - 7) * sc, s + 112 * sc, f + (df + 7) * sc, 4 * sc, 15 * sc,
              all=flat("b8bcc0", 2), top=flat("c8ccd0", 3))
    T.box(s - 10 * sc, f - 3 * sc, s + 22 * sc, f + 3 * sc, 30 * sc, 64 * sc, all=flat(col, 2), top=flat(col, 3))
    T.box(s - 8 * sc, f - 30 * sc, s + 18 * sc, f + 30 * sc, 28 * sc, 32 * sc, **wing)
    for ds in (40, 100):
        T.box(s + ds * sc, f - 4 * sc, s + (ds + 6) * sc, f + 4 * sc, 0, 8 * sc, all=flat("3a3a3a", 2), top=flat("3a3a3a", 2))


def airport(L, o):
    """An airport: glass terminal with a sign, control tower, runway, taxiway, apron with an airliner."""
    cv = Canvas(4, 190)
    T = Orient(cv, o)
    _runway(T)
    parking_lot(T, 30, 20, 300, 80)
    # terminal
    win = Win(w=26, h=30, sill=6, sp=30, margin=10, fh=42, frame="e8ecf0", style="vertical", tint="6a9ac8", group="work")
    fr = facade("plaster", "dfe4ea", win=win, doors=[(150, 60, 34, "double_glass")], seed=11, lit=0.8)
    sd = facade("plaster", "dfe4ea", win=win, seed=12, lit=0.8)
    box(T, 60, 100, 440, 220, 0, 52, front=fr, back=sd, left=sd, right=sd)
    slab(T, 50, 90, 450, 230, 52, 58, "e8ecf0", top=flat("c8ccd2", 4))
    T.box(150, 80, 330, 100, 30, 34, all=flat("e8ecf0", 2), top=flat("c8ccd2", 3))
    for s in (156, 324):
        post(T, s, 84, 0, 30, "d8dce0", 2.0)
    sign_board(T, 240, 100, 62, "AIRPORT", 14, "1e3a6a", "ffffff")
    # control tower
    T.box(480, 120, 520, 160, 0, 120, all=flat("e4e6ea", 4), top=flat("c8ccd2", 3))
    T.box(468, 108, 532, 172, 120, 142, all=flat("5a8ab8", 2), top=flat("5a8ab8", 2))
    T.box(464, 104, 536, 176, 142, 150, all=flat("e8ecf0", 2), top=flat("b8bcc4", 3))
    post(T, 500, 140, 150, 176, "d8d8dc", 1.6)
    T.box(497, 137, 503, 143, 174, 178, all=flat("e83a2a", 1), top=flat("ff5a3a", 2))
    _plane(T, 150, 330, 1.0, "2a6ab8")
    entry(T, 180)
    if L >= 2:
        _plane(T, 380, 520, 0.8, "c83a3a")
        T.box(440, 150, 470, 200, 0, 30, all=flat("c8ccd0", 3), top=flat("a8acb0", 3))
    if L >= 3:
        T.box(200, 220, 222, 300, 34, 46, all=flat("d8dce0", 2), top=flat("b8bcc0", 3))
        post(T, 211, 290, 0, 34, "a8acb0", 3.0)
        for s in (20, 320, 600):
            lamp(T, s, 100, "modern", 60)
        tree(T, 330, 40, "oak", 1.1, seed=3)
        tree(T, 600, 40, "oak", 1.1, seed=4)
    return cv


BUILDERS = {"airport": airport}
