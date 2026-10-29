"""Smooth vector UI icons (cairo): gradients, outlines and highlights, rendered at 64 px."""
import json
import math
import os

import cairo
from PIL import Image

S = 64
OUT_LINE = (0.13, 0.1, 0.16, 1)


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def lin(ctx, y0, y1, c0, c1, x0=0, x1=0):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    g.add_color_stop_rgba(0, *hexc(c0))
    g.add_color_stop_rgba(1, *hexc(c1))
    return g


def fs(ctx, fill, w=3.0, line=OUT_LINE):
    """Fill current path with colour/gradient, then outline it."""
    if isinstance(fill, str):
        ctx.set_source_rgba(*hexc(fill))
    else:
        ctx.set_source(fill)
    ctx.fill_preserve()
    ctx.set_source_rgba(*line)
    ctx.set_line_width(w)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def circ(ctx, x, y, r):
    ctx.new_sub_path()
    ctx.arc(x, y, r, 0, 2 * math.pi)


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def shine(ctx, x, y, rx, ry, a=0.45):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.fill()


def stroke(ctx, col, w, cap=cairo.LINE_CAP_ROUND):
    ctx.set_source_rgba(*hexc(col)) if isinstance(col, str) else ctx.set_source_rgba(*col)
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


# ====================================================================== icons
def coin(c):
    circ(c, 32, 33, 26)
    fs(c, lin(c, 6, 60, "ffe27a", "d99a14"))
    circ(c, 32, 33, 19)
    fs(c, lin(c, 14, 52, "f2b630", "ffe48a"), 2.5, hexc("b07a10"))
    c.move_to(32, 22)
    c.line_to(32, 44)
    stroke(c, "b07a10", 5)
    shine(c, 23, 21, 7, 4, 0.7)


def gem(c):
    poly(c, [(18, 10), (46, 10), (58, 24), (32, 58), (6, 24)])
    fs(c, lin(c, 10, 58, "7af0a8", "138a48"))
    poly(c, [(18, 10), (46, 10), (52, 24), (12, 24)])
    c.set_source_rgba(*hexc("b8ffd4", 0.7))
    c.fill()
    poly(c, [(24, 24), (40, 24), (32, 56)])
    c.set_source_rgba(*hexc("2ac06a", 0.6))
    c.fill()
    for (a, b) in (((12, 24), (52, 24)), ((24, 24), (32, 56)), ((40, 24), (32, 56)), ((24, 24), (18, 10)), ((40, 24), (46, 10))):
        c.move_to(*a)
        c.line_to(*b)
    stroke(c, (0.1, 0.4, 0.2, 0.6), 1.5)
    shine(c, 22, 15, 5, 3, 0.85)


def goods(c):
    rrect(c, 8, 20, 48, 38, 4)
    fs(c, lin(c, 20, 58, "e0a868", "a86c30"))
    poly(c, [(8, 20), (18, 8), (46, 8), (56, 20)])
    fs(c, lin(c, 8, 20, "f4c890", "d09a58"))
    c.rectangle(28, 8, 8, 50)
    c.set_source_rgba(*hexc("8a5424", 0.55))
    c.fill()
    c.rectangle(14, 30, 10, 3)
    c.rectangle(40, 30, 10, 3)
    c.set_source_rgba(1, 1, 1, 0.35)
    c.fill()


def person(c, shirt="3a7ad8"):
    circ(c, 32, 19, 12)
    fs(c, lin(c, 7, 31, "ffd8b8", "e8a878"))
    c.move_to(20, 15)
    c.curve_to(22, 4, 42, 4, 44, 15)
    c.curve_to(38, 10, 28, 10, 20, 15)
    fs(c, "6a3a1a", 2)
    c.move_to(10, 60)
    c.curve_to(10, 40, 20, 33, 32, 33)
    c.curve_to(44, 33, 54, 40, 54, 60)
    c.close_path()
    fs(c, lin(c, 33, 60, shirt, "1e4a9a" if shirt == "3a7ad8" else shirt))
    shine(c, 27, 14, 4, 3, 0.5)


def pop(c):
    person(c)


def jobs(c):
    rrect(c, 6, 22, 52, 34, 5)
    fs(c, lin(c, 22, 56, "a87048", "6a4024"))
    rrect(c, 22, 12, 20, 12, 3)
    c.set_source_rgba(0, 0, 0, 0)
    fs(c, "6a4024")
    c.rectangle(6, 36, 52, 4)
    c.set_source_rgba(*hexc("4a2c18"))
    c.fill()
    rrect(c, 27, 32, 10, 12, 2)
    fs(c, "f2c94c", 2)


def face_icon(c, happy=True):
    circ(c, 32, 32, 27)
    fs(c, lin(c, 5, 59, "ffe066", "f0a020") if happy else lin(c, 5, 59, "c8d0e0", "8090b0"))
    for x in (22, 42):
        circ(c, x, 26, 4)
        c.set_source_rgba(*OUT_LINE)
        c.fill()
    if happy:
        c.arc(32, 32, 15, 0.2 * math.pi, 0.8 * math.pi)
    else:
        c.arc(32, 52, 13, 1.25 * math.pi, 1.75 * math.pi)
    stroke(c, OUT_LINE, 4)
    shine(c, 22, 15, 7, 4, 0.6)


def star(c):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = 28 if k % 2 == 0 else 12
        pts.append((32 + r * math.cos(a), 34 + r * math.sin(a)))
    poly(c, pts)
    fs(c, lin(c, 6, 60, "fff07a", "f0a010"))
    shine(c, 27, 22, 6, 4, 0.7)


def build(c):
    c.move_to(14, 54)
    c.line_to(36, 32)
    stroke(c, "6a4024", 9)
    c.move_to(14, 54)
    c.line_to(36, 32)
    stroke(c, "b07848", 5)
    poly(c, [(30, 14), (46, 6), (58, 18), (52, 24), (44, 18), (36, 26), (26, 20)])
    fs(c, lin(c, 6, 26, "e8eef4", "8a94a4"))


def road(c):
    poly(c, [(22, 6), (42, 6), (60, 58), (4, 58)])
    fs(c, lin(c, 6, 58, "6a6a76", "3a3a44"))
    for y in (10, 26, 42):
        poly(c, [(30.5, y), (33.5, y), (34.5, y + 9), (29.5, y + 9)])
        c.set_source_rgba(*hexc("f8e070"))
        c.fill()
    c.move_to(21, 8)
    c.line_to(6, 56)
    c.move_to(43, 8)
    c.line_to(58, 56)
    stroke(c, "f4f0e8", 2.5)


def demolish(c):
    rrect(c, 4, 30, 40, 18, 3)
    fs(c, lin(c, 30, 48, "ffd04a", "e09010"))
    rrect(c, 12, 14, 22, 18, 3)
    fs(c, lin(c, 14, 32, "ffd04a", "e09010"))
    rrect(c, 16, 18, 14, 10, 2)
    fs(c, "8ad0f0", 2)
    for x in (12, 34):
        circ(c, x, 50, 8)
        fs(c, "2a2a30", 2.5)
        circ(c, x, 50, 3)
        c.set_source_rgba(*hexc("a0a0a8"))
        c.fill()
    poly(c, [(44, 30), (60, 20), (60, 52), (48, 52)])
    fs(c, lin(c, 20, 52, "d8dce4", "8a90a0"))


def mission(c):
    rrect(c, 12, 8, 40, 50, 4)
    fs(c, lin(c, 8, 58, "fff6dc", "f0d8a0"))
    for y in (20, 30, 40):
        c.move_to(20, y)
        c.line_to(44, y)
    stroke(c, "c0a070", 2.5)
    c.move_to(30, 46)
    c.line_to(38, 54)
    c.line_to(56, 34)
    stroke(c, OUT_LINE, 9)
    c.move_to(30, 46)
    c.line_to(38, 54)
    c.line_to(56, 34)
    stroke(c, "4ad060", 5)


def land(c):
    poly(c, [(32, 8), (60, 32), (32, 56), (4, 32)])
    fs(c, lin(c, 8, 56, "8ae060", "3a9a3a"))
    poly(c, [(32, 8), (60, 32), (32, 32)])
    c.set_source_rgba(1, 1, 1, 0.18)
    c.fill()
    c.move_to(30, 38)
    c.line_to(30, 12)
    stroke(c, "6a4024", 3)
    poly(c, [(31, 12), (48, 17), (31, 23)])
    fs(c, "e84a3a", 2)


def gear(c):
    pts = []
    for k in range(16):
        a = k * math.pi / 8
        r = 28 if k % 2 == 0 else 21
        pts.append((32 + r * math.cos(a - 0.15), 32 + r * math.sin(a - 0.15)))
        pts.append((32 + r * math.cos(a + 0.15), 32 + r * math.sin(a + 0.15)))
    poly(c, pts)
    fs(c, lin(c, 4, 60, "d8dee8", "7a8494"))
    circ(c, 32, 32, 9)
    fs(c, "4a4a56", 2.5)


def ok(c):
    c.move_to(10, 34)
    c.line_to(26, 50)
    c.line_to(54, 16)
    stroke(c, OUT_LINE, 13)
    c.move_to(10, 34)
    c.line_to(26, 50)
    c.line_to(54, 16)
    stroke(c, "5ae06a", 8)


def cancel(c):
    for (a, b) in (((14, 14), (50, 50)), ((50, 14), (14, 50))):
        c.move_to(*a)
        c.line_to(*b)
        stroke(c, OUT_LINE, 13)
    for (a, b) in (((14, 14), (50, 50)), ((50, 14), (14, 50))):
        c.move_to(*a)
        c.line_to(*b)
        stroke(c, "ff6a5a", 8)


def lock(c):
    c.arc(32, 26, 13, math.pi, 2 * math.pi)
    stroke(c, OUT_LINE, 9)
    c.arc(32, 26, 13, math.pi, 2 * math.pi)
    stroke(c, "b8c0cc", 5)
    rrect(c, 12, 26, 40, 32, 5)
    fs(c, lin(c, 26, 58, "ffd84a", "d89010"))
    circ(c, 32, 40, 4)
    c.set_source_rgba(*hexc("7a5010"))
    c.fill()
    c.rectangle(30, 40, 4, 9)
    c.fill()


def warn(c):
    c.move_to(32, 6)
    c.line_to(60, 56)
    c.line_to(4, 56)
    c.close_path()
    fs(c, lin(c, 6, 56, "ffe066", "f0a010"))
    c.move_to(32, 22)
    c.line_to(32, 40)
    stroke(c, OUT_LINE, 6)
    circ(c, 32, 48, 3.5)
    c.set_source_rgba(*OUT_LINE)
    c.fill()


def noroad(c):
    circ(c, 32, 32, 27)
    fs(c, lin(c, 5, 59, "ff7a6a", "c8281a"))
    rrect(c, 14, 27, 36, 10, 2)
    fs(c, "ffffff", 2)


def sound(c):
    poly(c, [(6, 24), (18, 24), (32, 10), (32, 54), (18, 40), (6, 40)])
    fs(c, lin(c, 10, 54, "f4f6fa", "b8c0d0"))
    for r in (10, 18):
        c.arc(34, 32, r, -0.3 * math.pi, 0.3 * math.pi)
        stroke(c, "f4f6fa", 4)


def music(c):
    poly(c, [(22, 12), (54, 6), (54, 14), (22, 20)])
    fs(c, "f4f6fa", 2)
    c.move_to(24, 16)
    c.line_to(24, 46)
    c.move_to(52, 10)
    c.line_to(52, 40)
    stroke(c, "f4f6fa", 4)
    for (x, y) in ((17, 48), (45, 42)):
        c.save()
        c.translate(x, y)
        c.scale(8, 6)
        c.arc(0, 0, 1, 0, 2 * math.pi)
        c.restore()
        fs(c, "f4f6fa", 2)


def globe(c):
    circ(c, 32, 32, 27)
    fs(c, lin(c, 5, 59, "6ac0ff", "1a6ac8"))
    poly(c, [(14, 16), (30, 18), (28, 30), (18, 34), (12, 26)])
    c.set_source_rgba(*hexc("6ad060"))
    c.fill()
    poly(c, [(36, 36), (50, 32), (54, 44), (42, 52)])
    c.fill()
    shine(c, 22, 15, 7, 4, 0.5)


def upgrade(c):
    poly(c, [(32, 4), (58, 30), (42, 30), (42, 58), (22, 58), (22, 30), (6, 30)])
    fs(c, lin(c, 4, 58, "8af07a", "2a9a3a"))
    poly(c, [(32, 8), (50, 26), (44, 26)])
    c.set_source_rgba(1, 1, 1, 0.45)
    c.fill()


def speed(c):
    poly(c, [(38, 2), (12, 36), (30, 36), (24, 62), (52, 24), (34, 24)])
    fs(c, lin(c, 2, 62, "fff07a", "f0a010"))


def sun(c):
    for k in range(8):
        a = k * math.pi / 4
        c.move_to(32 + 18 * math.cos(a), 32 + 18 * math.sin(a))
        c.line_to(32 + 28 * math.cos(a), 32 + 28 * math.sin(a))
    stroke(c, "f8a020", 5)
    circ(c, 32, 32, 14)
    fs(c, lin(c, 18, 46, "fff07a", "f8a020"))


def moon(c):
    circ(c, 30, 34, 25)
    fs(c, lin(c, 8, 58, "fffbe0", "d8d0a0"))
    c.save()
    circ(c, 30, 34, 26.6)
    c.clip()
    c.set_operator(cairo.OPERATOR_CLEAR)
    circ(c, 44, 24, 20)
    c.fill()
    c.set_operator(cairo.OPERATOR_OVER)
    circ(c, 44, 24, 20)
    c.set_source_rgba(*OUT_LINE)
    c.set_line_width(3)
    c.stroke()
    c.restore()


def horizon(c, top, bottom, sky):
    rrect(c, 4, 8, 56, 48, 8)
    fs(c, lin(c, 8, 56, sky[0], sky[1]))
    c.arc(32, 42, 14, math.pi, 2 * math.pi)
    c.close_path()
    fs(c, lin(c, 28, 42, top, bottom), 2)
    c.rectangle(6, 42, 52, 12)
    c.set_source_rgba(*hexc("3a6a3a"))
    c.fill()


def sunrise(c):
    horizon(c, "fff07a", "f8a020", ("8ac8f8", "ffd0a0"))


def sunset(c):
    horizon(c, "ffb060", "e84a3a", ("6a4a8a", "ff8a6a"))


def plus(c):
    for (a, b) in (((32, 10), (32, 54)), ((10, 32), (54, 32))):
        c.move_to(*a)
        c.line_to(*b)
        stroke(c, OUT_LINE, 14)
    for (a, b) in (((32, 10), (32, 54)), ((10, 32), (54, 32))):
        c.move_to(*a)
        c.line_to(*b)
        stroke(c, "ffffff", 9)


def info(c):
    circ(c, 32, 32, 27)
    fs(c, lin(c, 5, 59, "6ab0ff", "1a5ac0"))
    c.move_to(32, 28)
    c.line_to(32, 48)
    stroke(c, "ffffff", 7)
    circ(c, 32, 18, 4.5)
    c.set_source_rgba(1, 1, 1, 1)
    c.fill()


def clock(c):
    circ(c, 32, 32, 27)
    fs(c, lin(c, 5, 59, "ffffff", "d8dce8"))
    c.move_to(32, 32)
    c.line_to(32, 14)
    c.move_to(32, 32)
    c.line_to(44, 38)
    stroke(c, "3a3a46", 4)


def finance(c):
    rrect(c, 6, 8, 52, 48, 6)
    fs(c, lin(c, 8, 56, "ffffff", "e0e6f0"))
    for i, (h, col) in enumerate(((14, "e86a5a"), (24, "f0c040"), (34, "4ac060"))):
        rrect(c, 14 + i * 13, 48 - h, 9, h, 2)
        fs(c, col, 2)
    c.move_to(12, 30)
    c.line_to(26, 22)
    c.line_to(38, 26)
    c.line_to(52, 12)
    stroke(c, "3a7ad8", 3)


def bank(c):
    poly(c, [(32, 4), (60, 20), (4, 20)])
    fs(c, lin(c, 4, 20, "f4e0b0", "d8b070"))
    for x in (12, 24, 36, 48):
        c.rectangle(x - 3, 22, 7, 24)
    fs(c, lin(c, 22, 46, "ffffff", "c8ccd8"), 2)
    rrect(c, 4, 46, 56, 10, 2)
    fs(c, lin(c, 46, 56, "f4e0b0", "c8a060"))


def law(c):
    c.move_to(32, 8)
    c.line_to(32, 54)
    stroke(c, "8a6a3a", 5)
    c.move_to(10, 16)
    c.line_to(54, 16)
    stroke(c, "8a6a3a", 4)
    for x in (14, 50):
        c.move_to(x, 16)
        c.line_to(x - 9, 34)
        c.move_to(x, 16)
        c.line_to(x + 9, 34)
        stroke(c, "a88a5a", 2)
        c.arc(x, 34, 10, 0, math.pi)
        c.close_path()
        fs(c, lin(c, 34, 44, "ffe066", "d89010"), 2)
    rrect(c, 20, 52, 24, 8, 2)
    fs(c, "8a6a3a", 2)


def reputation(c):
    c.move_to(32, 4)
    c.line_to(56, 12)
    c.line_to(54, 34)
    c.curve_to(52, 48, 42, 56, 32, 60)
    c.curve_to(22, 56, 12, 48, 10, 34)
    c.line_to(8, 12)
    c.close_path()
    fs(c, lin(c, 4, 60, "8ab8ff", "2a5ab8"))
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = 14 if k % 2 == 0 else 6
        pts.append((32 + r * math.cos(a), 31 + r * math.sin(a)))
    poly(c, pts)
    fs(c, "ffe066", 2)


def tax(c):
    circ(c, 32, 32, 27)
    fs(c, lin(c, 5, 59, "ffb070", "e05a2a"))
    circ(c, 22, 22, 6)
    circ(c, 42, 42, 6)
    c.set_source_rgba(1, 1, 1, 1)
    c.fill()
    c.move_to(44, 18)
    c.line_to(20, 46)
    stroke(c, "ffffff", 5)


def cloud_shape(c, x=0, y=0, k=1.0):
    c.new_sub_path()
    for (cx, cy, r) in ((22, 34, 12), (34, 26, 15), (46, 34, 11), (34, 38, 12)):
        c.arc(x + cx * k, y + cy * k, r * k, 0, 2 * math.pi)
        c.new_sub_path()


def cloud_fill(c, x, y, grad, w=3.0):
    cloud_shape(c, x, y)
    c.set_source_rgba(*OUT_LINE)
    c.set_line_width(w * 2)
    c.stroke()
    cloud_shape(c, x, y)
    c.set_source(grad)
    c.fill()


def cloud(c):
    cloud_fill(c, 0, 0, lin(c, 10, 50, "ffffff", "c8d4e8"))


def rain(c):
    cloud_fill(c, 0, -6, lin(c, 4, 44, "d8e0ec", "8a98b0"))
    for x in (20, 32, 44):
        c.move_to(x, 44)
        c.line_to(x - 4, 56)
    stroke(c, "4a9af0", 3.5)


def storm(c):
    cloud_fill(c, 0, -8, lin(c, 4, 44, "8a90a8", "4a5068"))
    poly(c, [(34, 36), (24, 50), (32, 50), (26, 62), (42, 44), (34, 44)])
    fs(c, "ffe066", 2)


def snow(c):
    for k in range(3):
        a = k * math.pi / 3
        c.move_to(32 + 24 * math.cos(a), 32 + 24 * math.sin(a))
        c.line_to(32 - 24 * math.cos(a), 32 - 24 * math.sin(a))
    stroke(c, OUT_LINE, 8)
    for k in range(3):
        a = k * math.pi / 3
        c.move_to(32 + 24 * math.cos(a), 32 + 24 * math.sin(a))
        c.line_to(32 - 24 * math.cos(a), 32 - 24 * math.sin(a))
    stroke(c, "dff0ff", 4)


def fog(c):
    for i, y in enumerate((20, 32, 44)):
        c.move_to(8 + i * 4, y)
        c.line_to(56 - i * 3, y)
    stroke(c, OUT_LINE, 8)
    for i, y in enumerate((20, 32, 44)):
        c.move_to(8 + i * 4, y)
        c.line_to(56 - i * 3, y)
    stroke(c, "e0e6f0", 4)


def windy(c):
    cloud_fill(c, -6, -10, lin(c, 4, 40, "ffffff", "c8d4e8"), w=2.6)
    for (x0, y0, x1, cy) in ((6, 38, 46, 38), (10, 48, 54, 48), (14, 58, 44, 58)):
        c.move_to(x0, y0)
        c.curve_to(x0 + 10, y0 - 6, x1 - 10, cy + 6, x1, cy)
        stroke(c, OUT_LINE, 6)
    for (x0, y0, x1, cy) in ((6, 38, 46, 38), (10, 48, 54, 48), (14, 58, 44, 58)):
        c.move_to(x0, y0)
        c.curve_to(x0 + 10, y0 - 6, x1 - 10, cy + 6, x1, cy)
        stroke(c, "8aa0c0", 3)


def heat(c):
    c.save()
    c.translate(0, -8)
    c.scale(0.72, 0.72)
    sun(c)
    c.restore()
    for (x0, y1) in ((12, 62), (32, 63), (52, 62)):
        c.move_to(x0, y1)
        c.curve_to(x0 - 5, y1 - 7, x0 + 5, y1 - 12, x0, y1 - 18)
        stroke(c, "ffffff", 2.2)
    for (x0, y1) in ((12, 62), (32, 63), (52, 62)):
        c.move_to(x0, y1)
        c.curve_to(x0 - 5, y1 - 7, x0 + 5, y1 - 12, x0, y1 - 18)
        stroke(c, "f8a020", 1.1)


def paw(c):
    c.save()
    c.translate(32, 42)
    c.scale(14, 11)
    c.arc(0, 0, 1, 0, 2 * math.pi)
    c.restore()
    fs(c, lin(c, 30, 54, "c8946a", "8a5a3a"))
    for (x, y) in ((16, 26), (26, 16), (38, 16), (48, 26)):
        circ(c, x, y, 6.5)
        fs(c, lin(c, y - 6, y + 6, "c8946a", "8a5a3a"), 2.5)


def zoo(c):
    rrect(c, 6, 22, 52, 36, 4)
    fs(c, lin(c, 22, 58, "8ae060", "3a9a3a"))
    for x in range(12, 56, 8):
        c.move_to(x, 22)
        c.line_to(x, 58)
    stroke(c, "6a4024", 2.5)
    poly(c, [(4, 22), (32, 6), (60, 22)])
    fs(c, lin(c, 6, 22, "f08a4a", "c84a2a"))


def move(c):
    for (a, b) in (((32, 6), (32, 58)), ((6, 32), (58, 32))):
        c.move_to(*a)
        c.line_to(*b)
        stroke(c, OUT_LINE, 9)
        c.move_to(*a)
        c.line_to(*b)
        stroke(c, "ffffff", 5)
    for (x, y, a) in ((32, 6, -math.pi / 2), (32, 58, math.pi / 2), (6, 32, math.pi), (58, 32, 0)):
        poly(c, [(x + 6 * math.cos(a), y + 6 * math.sin(a)),
                 (x + 9 * math.cos(a + 2.4), y + 9 * math.sin(a + 2.4)),
                 (x + 9 * math.cos(a - 2.4), y + 9 * math.sin(a - 2.4))])
        fs(c, "ffffff", 2)


def rotate(c):
    """A circular arrow turning clockwise."""
    for col, w in ((OUT_LINE, 10), ("ffffff", 6)):
        c.new_sub_path()
        c.arc(32, 33, 19, math.radians(-60), math.radians(200))
        stroke(c, col, w, cairo.LINE_CAP_BUTT)
    a = math.radians(-60)
    x, y = 32 + 19 * math.cos(a), 33 + 19 * math.sin(a)
    poly(c, [(x + 11, y + 1), (x - 7, y - 8), (x - 3, y + 11)])
    fs(c, "ffffff", 2.5)


def link(c):
    for (x, y) in ((22, 26), (42, 38)):
        c.save()
        c.translate(x, y)
        c.rotate(-0.6)
        rrect(c, -14, -8, 28, 16, 8)
        c.restore()
        stroke(c, OUT_LINE, 9)
        c.save()
        c.translate(x, y)
        c.rotate(-0.6)
        rrect(c, -14, -8, 28, 16, 8)
        c.restore()
        stroke(c, "f2c94c", 5)


def closed(c):
    rrect(c, 8, 14, 48, 42, 4)
    fs(c, lin(c, 14, 56, "c8b8a0", "8a7a62"))
    rrect(c, 22, 30, 20, 26, 2)
    fs(c, "6a4a2a", 2)
    rrect(c, 4, 22, 56, 14, 3)
    fs(c, "e84a3a", 2.5)
    c.move_to(12, 29)
    c.line_to(52, 29)
    stroke(c, "ffffff", 3)


def evict(c):
    person(c, "8a8a96")
    c.move_to(40, 44)
    c.line_to(58, 44)
    stroke(c, OUT_LINE, 9)
    c.move_to(40, 44)
    c.line_to(58, 44)
    stroke(c, "ff6a5a", 5)


def police(c):
    c.move_to(32, 4)
    c.line_to(54, 12)
    c.line_to(52, 36)
    c.curve_to(50, 50, 40, 58, 32, 60)
    c.curve_to(24, 58, 14, 50, 12, 36)
    c.line_to(10, 12)
    c.close_path()
    fs(c, lin(c, 4, 60, "6a8ae0", "1e3a8a"))
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = 13 if k % 2 == 0 else 6
        pts.append((32 + r * math.cos(a), 31 + r * math.sin(a)))
    poly(c, pts)
    fs(c, "ffe066", 2)


def fire(c):
    c.move_to(32, 4)
    c.curve_to(44, 18, 54, 28, 52, 42)
    c.curve_to(50, 54, 42, 60, 32, 60)
    c.curve_to(20, 60, 12, 52, 12, 40)
    c.curve_to(12, 28, 22, 24, 24, 12)
    c.curve_to(28, 20, 30, 22, 32, 4)
    fs(c, lin(c, 4, 60, "ffd04a", "e8401a"))
    c.move_to(32, 30)
    c.curve_to(40, 38, 42, 44, 40, 50)
    c.curve_to(38, 56, 26, 56, 24, 50)
    c.curve_to(22, 44, 28, 40, 32, 30)
    c.set_source_rgba(*hexc("fff4a0"))
    c.fill()


def bell(c):
    c.move_to(32, 6)
    c.curve_to(48, 6, 50, 22, 50, 34)
    c.line_to(56, 46)
    c.line_to(8, 46)
    c.line_to(14, 34)
    c.curve_to(14, 22, 16, 6, 32, 6)
    fs(c, lin(c, 6, 46, "ffe066", "e09010"))
    circ(c, 32, 52, 6)
    fs(c, "e09010", 2.5)


def mail(c):
    rrect(c, 4, 14, 56, 38, 4)
    fs(c, lin(c, 14, 52, "ffffff", "dce2ec"))
    c.move_to(6, 16)
    c.line_to(32, 36)
    c.line_to(58, 16)
    stroke(c, OUT_LINE, 3)
    circ(c, 50, 16, 9)
    fs(c, "e84a3a", 2)


def backup(c):
    cloud_fill(c, 0, -4, lin(c, 6, 50, "ffffff", "b8c8e0"))
    poly(c, [(32, 22), (42, 34), (36, 34), (36, 46), (28, 46), (28, 34), (22, 34)])
    fs(c, "3a8ad8", 2)


def trophy(c):
    c.move_to(18, 8)
    c.line_to(46, 8)
    c.curve_to(46, 30, 40, 38, 32, 38)
    c.curve_to(24, 38, 18, 30, 18, 8)
    fs(c, lin(c, 8, 38, "fff07a", "e09010"))
    for sgn in (-1, 1):
        c.arc(32 + sgn * 18, 16, 8, 0, 2 * math.pi)
        stroke(c, "e09010", 4)
    rrect(c, 28, 38, 8, 10, 1)
    fs(c, "e09010", 2)
    rrect(c, 18, 48, 28, 10, 2)
    fs(c, "8a5a2a", 2)


def heart(c):
    c.move_to(32, 56)
    c.curve_to(4, 36, 6, 8, 22, 10)
    c.curve_to(28, 10, 32, 16, 32, 20)
    c.curve_to(32, 16, 36, 10, 42, 10)
    c.curve_to(58, 8, 60, 36, 32, 56)
    fs(c, lin(c, 8, 56, "ff8a9a", "d8283a"))
    shine(c, 20, 18, 6, 4, 0.6)


def calendar(c):
    rrect(c, 6, 10, 52, 48, 5)
    fs(c, lin(c, 10, 58, "ffffff", "dce2ec"))
    rrect(c, 6, 10, 52, 14, 5)
    fs(c, "e84a3a", 2.5)
    for i in range(3):
        for j in range(4):
            c.rectangle(12 + j * 11, 30 + i * 9, 6, 5)
    c.set_source_rgba(*hexc("8a90a0"))
    c.fill()


def shop(c):
    rrect(c, 8, 26, 48, 32, 3)
    fs(c, lin(c, 26, 58, "fff4e0", "e0d0b0"))
    for i in range(6):
        poly(c, [(6 + i * 9, 16), (15 + i * 9, 16), (15 + i * 9, 28), (6 + i * 9, 28)])
        c.set_source_rgba(*hexc("e84a3a" if i % 2 == 0 else "ffffff"))
        c.fill()
    rrect(c, 6, 14, 52, 14, 2)
    stroke(c, OUT_LINE, 2.5)
    rrect(c, 26, 38, 12, 20, 1)
    fs(c, "6a8ad0", 2)


def chat(c):
    rrect(c, 4, 8, 56, 38, 10)
    fs(c, lin(c, 8, 46, "ffffff", "dce4f0"))
    poly(c, [(16, 44), (14, 58), (30, 44)])
    fs(c, "dce4f0", 2.5)
    for x in (20, 32, 44):
        circ(c, x, 27, 4)
        c.set_source_rgba(*hexc("5a6a8a"))
        c.fill()


def door(c):
    rrect(c, 14, 6, 36, 54, 3)
    fs(c, lin(c, 6, 60, "b07a48", "6a4024"))
    circ(c, 42, 34, 3)
    c.set_source_rgba(*hexc("ffe066"))
    c.fill()


ICONS = {"coin": coin, "gem": gem, "goods": goods, "pop": pop, "jobs": jobs,
         "happy": lambda c: face_icon(c, True), "unhappy": lambda c: face_icon(c, False),
         "star": star, "build": build, "road": road, "demolish": demolish, "mission": mission, "land": land,
         "gear": gear, "ok": ok, "cancel": cancel, "lock": lock, "warn": warn, "noroad": noroad, "sound": sound,
         "music": music, "globe": globe, "upgrade": upgrade, "speed": speed, "sun": sun, "moon": moon,
         "sunrise": sunrise, "sunset": sunset, "plus": plus, "info": info, "clock": clock, "finance": finance,
         "bank": bank, "law": law, "reputation": reputation, "tax": tax, "cloud": cloud, "rain": rain,
         "storm": storm, "snow": snow, "fog": fog, "windy": windy, "heat": heat, "paw": paw, "zoo": zoo, "move": move, "link": link,
         "closed": closed, "evict": evict, "police": police, "fire": fire, "bell": bell, "mail": mail,
         "backup": backup, "trophy": trophy, "heart": heart, "calendar": calendar, "shop": shop, "chat": chat,
         "door": door, "rotate": rotate}


def render_icon(fn, size):
    k = 4  # supersample
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S * k, S * k)
    c = cairo.Context(surf)
    c.scale(k, k)
    fn(c)
    img = Image.frombuffer("RGBA", (S * k, S * k), bytes(surf.get_data()), "raw", "BGRA", 0, 1)
    # cairo stores premultiplied alpha
    import numpy as np
    a = np.array(img).astype(float)
    alpha = a[..., 3:4] / 255.0
    a[..., :3] = np.where(alpha > 0, a[..., :3] / np.maximum(alpha, 1e-6), 0)
    img = Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
    return img.resize((size, size), Image.LANCZOS)


def gen_icons(out):
    names = list(ICONS)
    for size in (16, 32, 64):
        sheet = Image.new("RGBA", (size * len(names), size), (0, 0, 0, 0))
        for i, n in enumerate(names):
            sheet.paste(render_icon(ICONS[n], size), (i * size, 0))
        sheet.save(os.path.join(out, "icons_%d.png" % size))
    json.dump(names, open(os.path.join(out, "icons.json"), "w"))
