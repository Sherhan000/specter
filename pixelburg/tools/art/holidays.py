"""Seasonal holiday decorations (ROADMAP 31): New Year, Navruz, Halloween, City Day.
Run: python3 tools/art/holidays.py  ->  assets/holidays/*.png (sprites stand on the bottom-centre of the image)."""
import math
import os

import cairo

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "holidays")


def col(h, a=1.0):
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def canvas(w, h):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(s)
    c.set_antialias(cairo.ANTIALIAS_BEST)
    return s, c


def shadow(c, x, y, rx, ry):
    c.save()
    c.translate(x, y)
    c.scale(rx, ry)
    c.arc(0, 0, 1, 0, 2 * math.pi)
    c.restore()
    c.set_source_rgba(0, 0, 0, 0.28)
    c.fill()


def poly(c, pts, fill, line=None, lw=2):
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    c.close_path()
    c.set_source_rgba(*col(fill))
    if line:
        c.fill_preserve()
        c.set_source_rgba(*col(line))
        c.set_line_width(lw)
        c.stroke()
    else:
        c.fill()


def circle(c, x, y, r, fill, line=None, lw=2):
    c.arc(x, y, r, 0, 2 * math.pi)
    c.set_source_rgba(*col(fill))
    if line:
        c.fill_preserve()
        c.set_source_rgba(*col(line))
        c.set_line_width(lw)
        c.stroke()
    else:
        c.fill()


def rect(c, x, y, w, h, fill, line=None, lw=2):
    poly(c, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, line, lw)


def star(c, x, y, r, fill, pts=5):
    p = []
    for i in range(pts * 2):
        a = -math.pi / 2 + i * math.pi / pts
        rr = r if i % 2 == 0 else r * 0.45
        p.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    poly(c, p, fill, "8a6a10", 1.5)


def fir_tree():
    s, c = canvas(220, 320)
    shadow(c, 110, 304, 70, 14)
    rect(c, 98, 262, 24, 40, "6a4a2a", "3a2410")
    tiers = [(250, 100, "1e6a3a"), (200, 82, "238040"), (150, 64, "2a9a4a"), (104, 46, "34ac56")]
    for y, hw, f in tiers:
        poly(c, [(110, y - 78), (110 + hw, y), (110 - hw, y)], f, "104a24", 2)
    # garlands and baubles
    cols = ["e03a3a", "f0c030", "3a7ae0", "e060c0"]
    for k, (y, hw, _) in enumerate(tiers):
        c.set_source_rgba(*col("f8e8a0"))
        c.set_line_width(3)
        c.move_to(110 - hw * 0.8, y - 8)
        c.curve_to(110 - hw * 0.3, y + 16, 110 + hw * 0.3, y - 2, 110 + hw * 0.8, y - 8)
        c.stroke()
        for i in range(5):
            bx = 110 - hw * 0.7 + i * hw * 0.35
            circle(c, bx, y - 2 + (8 if i % 2 else 0), 6, cols[(i + k) % 4], "ffffff", 1)
    star(c, 110, 24, 22, "ffd840")
    for gx, gc in [(70, "e03a3a"), (112, "3a7ae0"), (150, "f0c030")]:
        rect(c, gx - 14, 290, 28, 20, gc, "202020", 1.5)
        rect(c, gx - 3, 290, 6, 20, "ffffff")
    return s


def snowman():
    s, c = canvas(130, 170)
    shadow(c, 65, 158, 40, 9)
    circle(c, 65, 124, 32, "f4f8ff", "9ab0c8")
    circle(c, 65, 78, 24, "f4f8ff", "9ab0c8")
    circle(c, 65, 40, 18, "f8fbff", "9ab0c8")
    rect(c, 48, 22, 34, 6, "2a2a3a")
    rect(c, 54, 4, 22, 20, "2a2a3a")
    rect(c, 54, 16, 22, 5, "d03030")
    circle(c, 59, 38, 2.5, "202020")
    circle(c, 71, 38, 2.5, "202020")
    poly(c, [(65, 42), (86, 46), (65, 49)], "ff8a20")
    for y in (70, 84, 98):
        circle(c, 65, y, 3, "303030")
    c.set_source_rgba(*col("6a4a2a"))
    c.set_line_width(4)
    c.move_to(42, 76)
    c.line_to(14, 56)
    c.move_to(88, 76)
    c.line_to(116, 56)
    c.stroke()
    rect(c, 44, 56, 42, 8, "d03030")
    return s


def garland():
    s, c = canvas(240, 70)
    c.set_source_rgba(*col("2a2a2a"))
    c.set_line_width(2.5)
    c.move_to(4, 10)
    c.curve_to(70, 50, 170, 50, 236, 10)
    c.stroke()
    cols = ["ff4040", "ffd040", "40c0ff", "60e060", "ff70d0"]
    for i in range(9):
        t = (i + 0.5) / 9
        x = 4 + 232 * t
        y = 10 + 3 * 40 * t * (1 - t) + 4
        circle(c, x, y + 5, 11, cols[i % 5])
        c.set_source_rgba(1, 1, 1, 0.25)
        c.arc(x - 3, y + 2, 3, 0, 6.3)
        c.fill()
    return s


def sumalak():
    s, c = canvas(190, 190)
    shadow(c, 95, 176, 62, 12)
    # fire
    for dx, hh, f in [(-22, 44, "ff7a20"), (0, 56, "ffa030"), (22, 42, "ff6a18")]:
        poly(c, [(95 + dx - 14, 160), (95 + dx, 160 - hh), (95 + dx + 14, 160)], f)
    poly(c, [(80, 160), (95, 128), (110, 160)], "ffe070")
    for lx in (50, 130):
        c.set_source_rgba(*col("5a3a1a"))
        c.set_line_width(7)
        c.move_to(lx - 14, 172)
        c.line_to(lx + 14, 160)
        c.stroke()
    # kazan
    c.save()
    c.translate(95, 100)
    c.scale(62, 46)
    c.arc(0, 0, 1, 0, math.pi)
    c.restore()
    c.set_source_rgba(*col("2e2e34"))
    c.fill_preserve()
    c.set_source_rgba(*col("14141a"))
    c.set_line_width(3)
    c.stroke()
    c.save()
    c.translate(95, 100)
    c.scale(66, 15)
    c.arc(0, 0, 1, 0, 2 * math.pi)
    c.restore()
    c.set_source_rgba(*col("4a3a22"))
    c.fill_preserve()
    c.set_source_rgba(*col("1a1a1a"))
    c.set_line_width(3)
    c.stroke()
    # steam
    c.set_source_rgba(1, 1, 1, 0.55)
    c.set_line_width(6)
    for sx in (78, 98, 116):
        c.move_to(sx, 86)
        c.curve_to(sx - 12, 64, sx + 12, 50, sx, 24)
        c.stroke()
    return s


def swing():
    s, c = canvas(200, 190)
    shadow(c, 100, 178, 80, 10)
    c.set_source_rgba(*col("7a4a20"))
    c.set_line_width(9)
    for x0, x1 in [(20, 56), (180, 144)]:
        c.move_to(x0, 176)
        c.line_to(100, 18)
        c.line_to(180 - (x0 - 20), 176)
    c.stroke()
    rect(c, 40, 10, 120, 10, "8a5a2a", "4a2a10")
    c.set_source_rgba(*col("d8d0b8"))
    c.set_line_width(3)
    c.move_to(80, 20)
    c.line_to(76, 128)
    c.move_to(120, 20)
    c.line_to(124, 128)
    c.stroke()
    rect(c, 64, 126, 72, 10, "e05050", "7a2020")
    return s


def flowers():
    s, c = canvas(170, 90)
    shadow(c, 85, 76, 70, 11)
    rect(c, 18, 56, 134, 18, "7a5a3a", "3a2410")
    cols = ["e03a5a", "ffd040", "f070c0", "ff8030", "ffffff"]
    for i in range(8):
        x = 28 + i * 16
        c.set_source_rgba(*col("2a8a3a"))
        c.set_line_width(3)
        c.move_to(x, 58)
        c.line_to(x, 30 + (i % 3) * 6)
        c.stroke()
        top = 30 + (i % 3) * 6
        circle(c, x, top, 8, cols[i % 5], "7a2a3a", 1)
        circle(c, x, top, 3, "ffe080")
    return s


def pumpkin():
    s, c = canvas(110, 100)
    shadow(c, 55, 88, 40, 8)
    for dx in (-18, 0, 18):
        c.save()
        c.translate(55 + dx, 52)
        c.scale(22 if dx else 26, 32)
        c.arc(0, 0, 1, 0, 2 * math.pi)
        c.restore()
        c.set_source_rgba(*col("f08a18"))
        c.fill_preserve()
        c.set_source_rgba(*col("a04a08"))
        c.set_line_width(2)
        c.stroke()
    rect(c, 51, 14, 8, 12, "3a6a20")
    poly(c, [(42, 44), (50, 36), (52, 48)], "3a1a00")
    poly(c, [(68, 44), (60, 36), (58, 48)], "3a1a00")
    poly(c, [(55, 52), (50, 58), (60, 58)], "3a1a00")
    c.set_source_rgba(*col("3a1a00"))
    c.set_line_width(3)
    c.move_to(38, 66)
    for x in range(42, 74, 8):
        c.line_to(x, 74 if (x // 8) % 2 else 66)
    c.line_to(72, 66)
    c.stroke()
    return s


def lantern():
    s, c = canvas(80, 170)
    shadow(c, 40, 160, 22, 6)
    rect(c, 37, 40, 6, 118, "2a2a30")
    rect(c, 20, 6, 40, 4, "2a2a30")
    poly(c, [(22, 22), (58, 22), (50, 8), (30, 8)], "2a2a30")
    rect(c, 24, 22, 32, 34, "ffb030", "2a2a30", 3)
    circle(c, 40, 40, 9, "fff0a0")
    c.set_source_rgba(1, 0.7, 0.2, 0.25)
    c.arc(40, 40, 34, 0, 6.3)
    c.fill()
    poly(c, [(22, 56), (58, 56), (50, 64), (30, 64)], "2a2a30")
    return s


def flag():
    s, c = canvas(100, 220)
    shadow(c, 50, 210, 22, 6)
    rect(c, 45, 12, 6, 196, "d8d8e0", "8a8a98", 1.5)
    circle(c, 48, 10, 6, "ffd040", "8a6a10", 1.5)
    rect(c, 51, 16, 44, 14, "e03a3a")
    rect(c, 51, 30, 44, 14, "ffffff")
    rect(c, 51, 44, 44, 14, "2a9a4a")
    c.set_source_rgba(*col("303040"))
    c.set_line_width(1.5)
    c.rectangle(51, 16, 44, 42)
    c.stroke()
    return s


def bunting():
    s, c = canvas(240, 70)
    c.set_source_rgba(*col("3a3a3a"))
    c.set_line_width(2)
    c.move_to(4, 8)
    c.curve_to(70, 30, 170, 30, 236, 8)
    c.stroke()
    cols = ["e03a3a", "ffd040", "3a9ae0", "ffffff", "2a9a4a"]
    for i in range(10):
        t = (i + 0.5) / 10
        x = 4 + 232 * t
        y = 8 + 3 * 22 * t * (1 - t) * 1.0 + 4
        poly(c, [(x - 9, y), (x + 9, y), (x, y + 26)], cols[i % 5], "303040", 1)
    return s


def chimney_ghost():
    s, c = canvas(100, 130)
    shadow(c, 50, 120, 28, 6)
    c.set_source_rgba(1, 1, 1, 0.92)
    c.move_to(18, 110)
    c.line_to(18, 50)
    c.curve_to(18, 6, 82, 6, 82, 50)
    c.line_to(82, 110)
    for i in range(4):
        c.curve_to(82 - 8 - i * 16, 122, 82 - 8 - i * 16 - 6, 100, 82 - 16 - i * 16, 110)
    c.close_path()
    c.fill_preserve()
    c.set_source_rgba(*col("9aa0b8"))
    c.set_line_width(2)
    c.stroke()
    circle(c, 38, 52, 6, "202030")
    circle(c, 62, 52, 6, "202030")
    c.set_source_rgba(*col("202030"))
    c.arc(50, 72, 7, 0, 6.3)
    c.fill()
    return s


SPRITES = {"fir_tree": fir_tree, "snowman": snowman, "garland": garland, "sumalak": sumalak, "swing": swing,
           "flowers": flowers, "pumpkin": pumpkin, "lantern": lantern, "flag": flag, "bunting": bunting, "ghost": chimney_ghost}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in SPRITES.items():
        fn().write_to_png(os.path.join(OUT, name + ".png"))
    print("holidays:", len(SPRITES), "sprites")
