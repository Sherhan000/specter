"""Beach: an umbrella with sunbeds, a thatched beach bar and a lifeguard tower, all standing on sand."""
from raster import C, U, Canvas, flat
from arch import Orient, facade, Win, roof_mat
import kit
from bkit import ground, lamp, box, slab, post, awning, sign_board, entry, tree

SAND = ("e6d29c", "dcc68c")


def _sand(T, w):
    ground(T, 0, 0, w, w, flat(SAND[0], 8))
    ground(T, 6, 6, w - 6, w - 6, flat(SAND[1], 8), 0.4)


def _umbrella(T, s, f, c1, c2, h=34, r=22):
    """Pole and a stepped square canopy in two colours."""
    post(T, s, f, 0, h, "f2eee6", 2.0)
    for k in range(4):
        rr = r - k * 5
        col = c1 if k % 2 == 0 else c2
        T.box(s - rr, f - rr, s + rr, f + rr, h - 4 + k * 3, h - 1 + k * 3, all=flat(col, 2), top=flat(col, 3))


def _bed(T, s, f, col="f6f2ea"):
    T.box(s, f, s + 30, f + 12, 3, 7, all=flat("c8a878", 2), top=flat(col, 3))
    T.box(s, f, s + 8, f + 12, 7, 11, all=flat("c8a878", 2), top=flat(col, 3))
    for x in (s + 2, s + 26):
        T.box(x, f + 1, x + 2, f + 3, 0, 3, all=flat("8a6a40", 2), top=flat("8a6a40", 2))
        T.box(x, f + 9, x + 2, f + 11, 0, 3, all=flat("8a6a40", 2), top=flat("8a6a40", 2))


def beach_umbrella(L, o):
    """A beach umbrella over two sunbeds and a towel."""
    cv = Canvas(1, 76)
    T = Orient(cv, o)
    _sand(T, 160)
    _bed(T, 36, 56, "f6f2ea")
    _bed(T, 36, 92, "e8a82a")
    _umbrella(T, 80, 80, "d8402e", "f6f2ea")
    T.box(104, 50, 130, 66, 0, 1.5, all=flat("2e8a8a", 2), top=flat("2e8aa8", 3))
    entry(T, 80)
    if L >= 2:
        T.box(110, 100, 126, 116, 0, 8, all=flat("c8d8e8", 2), top=flat("4a8ac8", 4))
    if L >= 3:
        _umbrella(T, 130, 130, "2e6ab8", "f6f2ea", 30, 14)
    return cv


def beach_bar(L, o):
    """A beach bar: a wooden hut with a thatched roof, a counter with stools and umbrellas."""
    cv = Canvas(2, 76)
    T = Orient(cv, o)
    _sand(T, 320)
    wood = flat("a8825a", 3)
    T.box(70, 150, 250, 270, 0, 4, all=flat("8a6a44", 3), top=flat("a8825a", 3))
    win = Win(w=14, h=14, sill=14, sp=40, margin=14, fh=36, frame="5a3a1e", style="vertical", tint="9ab8c8", group="shop")
    fr = facade("plaster", "e8d8b0", win=win, doors=[(140, 40, 36, "double_glass")], seed=7, lit=0.9)
    sd = facade("plaster", "e8d8b0", win=win, seed=8, lit=0.9)
    box(T, 80, 160, 240, 260, 4, 44, front=fr, back=sd, left=sd, right=sd)
    T.gable(70, 150, 250, 270, 44, 34, roof_mat("c8a050", "tiles"), dict(all=sd), ridge="s", o=10)
    # counter with stools in front
    T.box(90, 110, 230, 128, 0, 16, all=wood, top=flat("c8a878", 3))
    for k in range(4):
        T.box(104 + k * 32, 92, 112 + k * 32, 100, 0, 11, all=flat("8a3a2a", 2), top=flat("d8402e", 3))
    awning(T, 86, 234, 150, 38, 20, 8, "2e8a8a", "f6f2ea", 6.0)
    sign_board(T, 160, 148, 44, "BAR", 12, "2a1a10", "ffd84a")
    _umbrella(T, 40, 70, "e8a82a", "f6f2ea")
    _umbrella(T, 280, 70, "d8402e", "f6f2ea")
    entry(T, 160)
    if L >= 2:
        _bed(T, 24, 190)
        _bed(T, 270, 190)
    if L >= 3:
        lamp(T, 24, 24, "classic", 44)
        lamp(T, 296, 24, "classic", 44)
    return cv


def lifeguard_tower(L, o):
    """A lifeguard tower on stilts: red and white cabin, ladder, flag and a rescue buoy."""
    cv = Canvas(1, 90)
    T = Orient(cv, o)
    _sand(T, 160)
    for sx, fx in ((56, 56), (104, 56), (56, 104), (104, 104)):
        post(T, sx, fx, 0, 34, "f2eee6", 4.0)
    T.box(48, 48, 112, 112, 34, 38, all=flat("f2eee6", 2), top=flat("c8a878", 3))
    T.box(52, 52, 108, 108, 38, 62, all=flat("f6f2ea", 3), top=flat("d8402e", 3))
    T.box(52, 52, 108, 62, 46, 54, all=flat("9ab8c8", 2), top=flat("9ab8c8", 2))
    T.box(46, 46, 114, 114, 62, 66, all=flat("d8402e", 2), top=flat("d8402e", 3))
    for k in range(6):
        T.box(112 + k * 3, 70, 116 + k * 3, 78, k * 5, k * 5 + 4, all=flat("f2eee6", 2), top=flat("f2eee6", 3))
    post(T, 80, 80, 66, 84, "f2eee6", 2.0)
    T.box(80, 78, 96, 80, 74, 84, all=flat("d8402e", 2), top=flat("d8402e", 2))
    T.box(120, 120, 132, 132, 0, 3, all=flat("d8402e", 2), top=flat("f6f2ea", 3))
    entry(T, 80)
    return cv


BUILDERS = {"beach_umbrella": beach_umbrella, "beach_bar": beach_bar, "lifeguard_tower": lifeguard_tower}
