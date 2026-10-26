"""Smooth vector character portraits (cairo) for dialogues: the assistant Alina and story characters.

Every character is drawn from parameters (skin, hair style, outfit...) in several expressions.
Players can replace any portrait with their own art: put a 512x512 PNG with the same file name
into assets/portraits/ (see docs/PORTRAIT_PROMPTS.md).
"""
import math
import os

import cairo

SIZE = 1024


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def shade(h, f, a=1.0):
    r, g, b, _ = hexc(h)
    return (min(1, r * f), min(1, g * f), min(1, b * f), a)


def path(ctx, pts, close=True):
    """pts: list of points; tuples of 2 = line_to, of 6 = curve_to (c1, c2, end)."""
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        if len(p) == 2:
            ctx.line_to(*p)
        else:
            ctx.curve_to(*p)
    if close:
        ctx.close_path()


def fill_grad(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, col in stops:
        g.add_color_stop_rgba(off, *col)
    ctx.set_source(g)


def ellipse(ctx, cx, cy, rx, ry, rot=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def outline_fill(ctx, fill, line=None, width=6):
    ctx.set_source_rgba(*fill) if isinstance(fill, tuple) else ctx.set_source(fill)
    ctx.fill_preserve()
    if line:
        ctx.set_source_rgba(*line)
        ctx.set_line_width(width)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
    else:
        ctx.new_path()


LINE = hexc("3a2228")


# ====================================================================== parts
def background(ctx, top, bottom):
    fill_grad(ctx, 0, 0, 0, SIZE, [(0, hexc(top)), (1, hexc(bottom))])
    ctx.rectangle(0, 0, SIZE, SIZE)
    ctx.fill()
    # soft town silhouettes
    ctx.set_source_rgba(1, 1, 1, 0.18)
    for (x, w, h) in ((40, 150, 260), (200, 120, 340), (330, 170, 220), (700, 140, 300), (830, 160, 240)):
        ctx.rectangle(x, SIZE - 260 - h, w, h + 260)
        ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.25)
    for (cx, cy, r) in ((180, 170, 70), (260, 150, 90), (340, 175, 60), (780, 120, 60), (840, 105, 80)):
        ellipse(ctx, cx, cy, r, r * 0.6)
        ctx.fill()
    # light vignette
    g = cairo.RadialGradient(SIZE / 2, SIZE * 0.45, SIZE * 0.2, SIZE / 2, SIZE / 2, SIZE * 0.75)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.25)
    ctx.set_source(g)
    ctx.rectangle(0, 0, SIZE, SIZE)
    ctx.fill()


def body(ctx, c):
    """Shoulders, outfit and neck."""
    skin = c["skin"]
    male = c["male"]
    nw = 58 if not male else 72
    # neck
    path(ctx, [(512 - nw, 540), (512 - nw - 4, 680), (512, 730), (512 + nw + 4, 680), (512 + nw, 540)])
    outline_fill(ctx, hexc(skin), LINE, 5)
    path(ctx, [(512 - nw, 575), (512, 640), (512 + nw, 575), (512 + nw, 610), (512, 670), (512 - nw, 610)])
    ctx.set_source_rgba(*shade(skin, 0.82, 0.7))
    ctx.fill()
    out = c["outfit"]
    sh = 300 if not male else 250
    # blouse / shirt under the jacket
    path(ctx, [(512 - 120, 690), (512, 700), (512 + 120, 690), (512 + 130, 1024), (512 - 130, 1024)])
    outline_fill(ctx, hexc(out["shirt"]), LINE, 5)
    # collar of the shirt
    for sgn in (-1, 1):
        path(ctx, [(512 + sgn * nw, 672), (512 + sgn * (nw + 34), 720), (512 + sgn * 12, 760), (512, 712)])
        outline_fill(ctx, shade(out["shirt"], 0.96), LINE, 4)
    if out.get("tie"):
        path(ctx, [(500, 712), (524, 712), (532, 742), (522, 900), (512, 930), (502, 900), (492, 742)])
        outline_fill(ctx, hexc(out["tie"]), LINE, 4)
    # jacket halves
    for sgn in (-1, 1):
        x = lambda v: 512 + sgn * v
        path(ctx, [(x(nw + 6), 668), (x(nw + 90), 676, x(sh - 40), 700, x(sh), 760),
                   (x(sh + 40), 830, x(sh + 60), 930, x(sh + 70), 1024), (x(70), 1024), (x(40), 840)])
        fill_grad(ctx, 0, 660, 0, 1024, [(0, hexc(out["jacket"])), (1, shade(out["jacket"], 0.72))])
        ctx.fill_preserve()
        ctx.set_source_rgba(*LINE)
        ctx.set_line_width(6)
        ctx.stroke()
        # lapel
        path(ctx, [(x(nw + 6), 668), (x(nw + 44), 700), (x(nw + 20), 760), (x(80), 880), (x(40), 840)])
        outline_fill(ctx, shade(out["jacket"], 1.14), LINE, 5)
    if out.get("badge"):
        path(ctx, [(660, 800), (690, 790), (700, 820), (690, 850), (660, 860), (650, 830)])
        outline_fill(ctx, hexc("f2c94c"), LINE, 4)
    if out.get("necklace"):
        ctx.set_source_rgba(*hexc("e8c860"))
        ctx.set_line_width(3)
        ctx.arc(512, 610, 72, 0.22 * math.pi, 0.78 * math.pi)
        ctx.stroke()
        ellipse(ctx, 512, 684, 8, 10)
        ctx.set_source_rgba(*hexc("6ac8f0"))
        ctx.fill()
    if out.get("shawl"):
        path(ctx, [(170, 1024), (230, 760, 380, 690, 512, 700), (644, 690, 794, 760, 854, 1024)])
        outline_fill(ctx, hexc(out["shawl"]), LINE, 6)
        ctx.set_source_rgba(1, 1, 1, 0.35)
        for k in range(6):
            ctx.arc(300 + k * 85, 860, 16, 0, 2 * math.pi)
            ctx.fill()


def hair_back(ctx, c):
    h = c["hair"]
    st = c["hair_style"]
    col = hexc(h)
    if st == "long":
        path(ctx, [(318, 330), (260, 520, 250, 780, 320, 960), (400, 990, 450, 860, 455, 700), (569, 700),
                   (574, 860, 624, 990, 704, 960), (774, 780, 764, 520, 706, 330), (640, 150, 384, 150, 318, 330)])
    elif st == "bob":
        path(ctx, [(318, 330), (285, 470, 300, 600, 350, 650), (470, 650), (554, 650), (674, 650),
                   (724, 600, 739, 470, 706, 330), (640, 150, 384, 150, 318, 330)])
    elif st == "bun":
        ellipse(ctx, 512, 175, 92, 78)
        fill_grad(ctx, 0, 95, 0, 255, [(0, shade(h, 1.15)), (1, col)])
        ctx.fill_preserve()
        ctx.set_source_rgba(*LINE)
        ctx.set_line_width(6)
        ctx.stroke()
        return
    else:
        return
    fill_grad(ctx, 0, 200, 0, 980, [(0, shade(h, 1.05)), (1, shade(h, 0.78))])
    ctx.fill_preserve()
    ctx.set_source_rgba(*LINE)
    ctx.set_line_width(6)
    ctx.stroke()


def face(ctx, c):
    skin = c["skin"]
    male = c["male"]
    w = 150 if not male else 165
    chin = 612 if not male else 628
    path(ctx, [(512 - w, 330), (512 - w - 4, 440, 512 - w + 22, 520, 512 - 78, 575),
               (512 - 40, 606, 512 - 20, chin, 512, chin),
               (512 + 20, chin, 512 + 40, 606, 512 + 78, 575),
               (512 + w - 22, 520, 512 + w + 4, 440, 512 + w, 330),
               (512 + w, 205, 512 - w, 205, 512 - w, 330)])
    g = cairo.LinearGradient(350, 0, 680, 0)
    g.add_color_stop_rgba(0, *hexc(skin))
    g.add_color_stop_rgba(0.65, *hexc(skin))
    g.add_color_stop_rgba(1, *shade(skin, 0.9))
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.set_source_rgba(*LINE)
    ctx.set_line_width(5)
    ctx.stroke()
    for sgn in (-1, 1):
        ellipse(ctx, 512 + sgn * (w + 2), 430, 20, 34)
        outline_fill(ctx, hexc(skin), LINE, 5)
    if c.get("earrings"):
        for sgn in (-1, 1):
            ellipse(ctx, 512 + sgn * (w + 4), 472, 7, 7)
            ctx.set_source_rgba(*hexc("f0d070"))
            ctx.fill()
    if not male or c.get("blush"):
        for sgn in (-1, 1):
            g = cairo.RadialGradient(512 + sgn * 98, 500, 4, 512 + sgn * 98, 500, 52)
            g.add_color_stop_rgba(0, 1, 0.5, 0.5, 0.38)
            g.add_color_stop_rgba(1, 1, 0.5, 0.5, 0.0)
            ctx.set_source(g)
            ellipse(ctx, 512 + sgn * 98, 500, 56, 36)
            ctx.fill()
    if c.get("wrinkles"):
        ctx.set_source_rgba(*shade(skin, 0.7, 0.7))
        ctx.set_line_width(3)
        for sgn in (-1, 1):
            ctx.move_to(512 + sgn * 62, 520)
            ctx.curve_to(512 + sgn * 72, 540, 512 + sgn * 70, 556, 512 + sgn * 58, 566)
            ctx.stroke()
    if c.get("beard"):
        path(ctx, [(512 - 112, 500), (512 - 96, 600, 470, chin + 26, 512, chin + 28), (554, chin + 26, 608, 600, 624, 500),
                   (592, 560, 560, 572, 512, 572), (464, 572, 432, 560, 400, 500)])
        outline_fill(ctx, hexc(c["hair"]), None)
    ctx.set_source_rgba(*shade(skin, 0.75))
    ctx.set_line_width(4)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(518, 478)
    ctx.curve_to(524, 496, 524, 506, 512, 510)
    ctx.stroke()


def eyes(ctx, c, expr):
    male = c["male"]
    iris = c["eyes"]
    for sgn in (-1, 1):
        cx, cy = 512 + sgn * 74, 430
        if expr == "happy":
            ctx.set_source_rgba(*LINE)
            ctx.set_line_width(9)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.arc(cx, cy + 16, 34, math.pi * 1.15, math.pi * 1.85)
            ctx.stroke()
            continue
        open_ = 1.12 if expr == "surprised" else (0.82 if expr in ("smug", "angry") else 1.0)
        rx, ry = (44, 50 * open_) if not male else (32, 30 * open_)
        ellipse(ctx, cx, cy, rx, ry)
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.fill()
        ir = 34 if not male else 22
        g = cairo.LinearGradient(cx, cy - ir * 1.2, cx, cy + ir * 1.2)
        g.add_color_stop_rgba(0, *shade(iris, 0.45))
        g.add_color_stop_rgba(0.55, *hexc(iris))
        g.add_color_stop_rgba(1, *shade(iris, 1.45))
        ctx.save()
        ellipse(ctx, cx, cy, rx, ry)
        ctx.clip()
        ellipse(ctx, cx + sgn * 2, cy + 4, ir, ir * (1.18 if not male else 1.05))
        ctx.set_source(g)
        ctx.fill()
        ellipse(ctx, cx + sgn * 2, cy + 6, ir * 0.42, ir * 0.5)
        ctx.set_source_rgba(0.1, 0.06, 0.08, 1)
        ctx.fill()
        # upper lid shadow
        ellipse(ctx, cx, cy - ry * 0.9, rx * 1.1, ry * 0.45)
        ctx.set_source_rgba(0.2, 0.1, 0.12, 0.12)
        ctx.fill()
        ctx.restore()
        ellipse(ctx, cx - 9, cy - 10, 10, 11)
        ctx.set_source_rgba(1, 1, 1, 0.95)
        ctx.fill()
        ellipse(ctx, cx + 11, cy + 16, 5, 5)
        ctx.fill()
        # upper lash line
        ctx.set_source_rgba(*LINE)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_width(10 if not male else 6)
        ctx.arc(cx, cy + ry * 0.45, rx * 1.12, math.pi * 1.13, math.pi * 1.87)
        ctx.stroke()
        if not male:
            ctx.set_line_width(5)
            ex = cx + sgn * rx * 1.02
            ctx.move_to(ex, cy - ry * 0.35)
            ctx.line_to(ex + sgn * 16, cy - ry * 0.6)
            ctx.stroke()
            ctx.move_to(ex - sgn * 6, cy - ry * 0.55)
            ctx.line_to(ex + sgn * 6, cy - ry * 0.85)
            ctx.stroke()
        ctx.set_line_width(3)
        ctx.arc(cx, cy - ry * 0.35, rx * 0.95, math.pi * 0.22, math.pi * 0.78)
        ctx.stroke()
        if not male:
            ctx.set_line_width(2.5)
            for k in (-0.5, 0.0, 0.5):
                a = math.pi * (0.5 + k * 0.35)
                px, py = cx + math.cos(a) * rx * 0.92, cy - ry * 0.35 + math.sin(a) * rx * 0.95
                ctx.move_to(px, py)
                ctx.line_to(px + math.cos(a) * 7, py + math.sin(a) * 7)
                ctx.stroke()
        # crease
        ctx.set_source_rgba(*shade(c["skin"], 0.7))
        ctx.set_line_width(3)
        ctx.arc(cx, cy + ry * 0.3, rx * 1.25, math.pi * 1.25, math.pi * 1.75)
        ctx.stroke()
    tilt = {"worried": -14, "surprised": 0, "angry": 16, "smug": 8}.get(expr, 3)
    lift = -12 if expr == "surprised" else 0
    ctx.set_source_rgba(*shade(c["hair"], 0.7))
    ctx.set_line_width(6 if not male else 11)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for sgn in (-1, 1):
        x0, x1 = 512 + sgn * 38, 512 + sgn * 118
        y_in = 360 + lift + tilt
        y_out = 352 + lift - (tilt if (expr != "smug" or sgn == -1) else -tilt)
        ctx.move_to(x0, y_in)
        ctx.curve_to(x0 + sgn * 25, y_in - 14, x1 - sgn * 25, y_out - 14, x1, y_out)
        ctx.stroke()
    if c.get("glasses"):
        ctx.set_source_rgba(*hexc("3a3a44"))
        ctx.set_line_width(6)
        for sgn in (-1, 1):
            ellipse(ctx, 512 + sgn * 76, 432, 52, 44)
            ctx.stroke()
        ctx.move_to(490, 430)
        ctx.line_to(534, 430)
        ctx.stroke()


def mouth(ctx, c, expr):
    y = 556 if not c["male"] else 566
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if expr in ("talk", "surprised"):
        w, h = (26, 24) if expr == "talk" else (16, 24)
        path(ctx, [(512 - w, y - 4), (512 - w / 2, y - 9, 512 + w / 2, y - 9, 512 + w, y - 4),
                   (512 + w * 0.8, y + h, 512 - w * 0.8, y + h, 512 - w, y - 4)])
        outline_fill(ctx, hexc("8a2a3a"), LINE, 4)
        ellipse(ctx, 512, y + h * 0.65, w * 0.55, h * 0.25)
        ctx.set_source_rgba(*hexc("f08a90"))
        ctx.fill()
        return
    ctx.set_source_rgba(*LINE)
    ctx.set_line_width(5)
    if expr in ("worried", "angry"):
        ctx.move_to(490, y + 8)
        ctx.curve_to(504, y - 4, 520, y - 4, 534, y + 8)
        ctx.stroke()
        return
    if expr == "smug":
        ctx.move_to(486, y + 2)
        ctx.curve_to(512, y + 10, 536, y + 2, 552, y - 10)
        ctx.stroke()
        return
    w = 30 if expr == "happy" else 24
    path(ctx, [(512 - w, y - 4), (512 - w / 2, y + 22, 512 + w / 2, y + 22, 512 + w, y - 4),
               (512 + w / 2, y + 4, 512 - w / 2, y + 4, 512 - w, y - 4)])
    outline_fill(ctx, hexc("8a2a3a"), LINE, 4)
    if not c["male"]:
        path(ctx, [(512 - w * 0.55, y + 9), (512, y + 20, 512, y + 20, 512 + w * 0.55, y + 9),
                   (512, y + 14, 512, y + 14, 512 - w * 0.55, y + 9)])
        ctx.set_source_rgba(*hexc("f08a96"))
        ctx.fill()
    if not c["male"]:
        ctx.set_source_rgba(1, 0.6, 0.65, 0.6)
        ctx.set_line_width(4)
        ctx.move_to(504, y + 30)
        ctx.line_to(520, y + 30)
        ctx.stroke()


def hair_front(ctx, c):
    h = c["hair"]
    st = c["hair_style"]
    col = hexc(h)
    if st == "long":
        # side locks falling over the shoulders
        for sgn in (-1, 1):
            x = lambda v: 512 + sgn * v
            path(ctx, [(x(148), 300), (x(200), 420, x(165), 560, x(215), 700), (x(232), 760, x(205), 820, x(178), 830),
                       (x(190), 780, x(150), 700, x(128), 620), (x(108), 540, x(122), 430, x(104), 350)])
            fill_grad(ctx, 0, 330, 0, 790, [(0, shade(h, 1.05)), (1, shade(h, 0.85))])
            ctx.fill_preserve()
            ctx.set_source_rgba(*LINE)
            ctx.set_line_width(5)
            ctx.stroke()
    if st in ("long", "bob"):
        path(ctx, [(340, 395), (318, 235, 420, 160, 530, 165), (665, 170, 720, 262, 695, 395),
                   (672, 336, 650, 300, 622, 286), (624, 330, 600, 352, 582, 378),
                   (574, 335, 556, 310, 540, 298), (530, 340, 506, 368, 470, 384),
                   (480, 340, 470, 318, 460, 304), (430, 340, 395, 372, 340, 395)])
    elif st == "bun":
        path(ctx, [(355, 375), (340, 240, 420, 200, 512, 200), (604, 200, 684, 240, 669, 375),
                   (630, 300, 580, 268, 512, 268), (444, 268, 394, 300, 355, 375)])
    elif st == "short":
        path(ctx, [(350, 400), (325, 230, 420, 160, 520, 168), (650, 170, 712, 250, 680, 400),
                   (665, 320, 640, 290, 600, 280), (560, 312, 470, 312, 420, 292), (385, 312, 365, 350, 350, 400)])
    elif st == "slick":
        path(ctx, [(352, 380), (335, 220, 430, 170, 540, 175), (650, 182, 702, 250, 676, 380),
                   (655, 285, 600, 245, 500, 250), (420, 255, 375, 295, 352, 380)])
    elif st == "cap":
        path(ctx, [(338, 345), (338, 200, 430, 158, 512, 158), (594, 158, 686, 200, 686, 345), (512, 315)])
        outline_fill(ctx, hexc("2a3a6a"), LINE, 6)
        path(ctx, [(338, 345), (512, 305), (690, 345), (712, 368), (512, 335), (316, 368)])
        outline_fill(ctx, hexc("1a2440"), LINE, 6)
        ellipse(ctx, 512, 240, 26, 30)
        outline_fill(ctx, hexc("f2c94c"), LINE, 4)
        return
    else:
        return
    fill_grad(ctx, 0, 160, 0, 390, [(0, shade(h, 1.22)), (1, col)])
    ctx.fill_preserve()
    ctx.set_source_rgba(*LINE)
    ctx.set_line_width(6)
    ctx.stroke()
    # strands + shine
    ctx.set_source_rgba(*shade(h, 0.7))
    ctx.set_line_width(3)
    for (x0, y0, x1, y1) in ((440, 220, 400, 340), (520, 200, 470, 350), (590, 210, 640, 330)):
        ctx.move_to(x0, y0)
        ctx.curve_to(x0 - 10, y0 + 40, x1 + 10, y1 - 40, x1, y1)
        ctx.stroke()
    ctx.set_source_rgba(1, 1, 1, 0.38)
    ctx.set_line_width(12)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.arc(512, 340, 150, math.pi * 1.27, math.pi * 1.43)
    ctx.stroke()
    ctx.arc(512, 340, 150, math.pi * 1.53, math.pi * 1.6)
    ctx.stroke()


def frame(ctx, ring):
    ctx.set_operator(cairo.OPERATOR_DEST_IN)
    r = 120
    ctx.new_path()
    ctx.arc(r, r, r, math.pi, 1.5 * math.pi)
    ctx.arc(SIZE - r, r, r, 1.5 * math.pi, 2 * math.pi)
    ctx.arc(SIZE - r, SIZE - r, r, 0, 0.5 * math.pi)
    ctx.arc(r, SIZE - r, r, 0.5 * math.pi, math.pi)
    ctx.close_path()
    ctx.set_source_rgba(0, 0, 0, 1)
    ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.new_path()
    ctx.arc(r, r, r - 8, math.pi, 1.5 * math.pi)
    ctx.arc(SIZE - r, r, r - 8, 1.5 * math.pi, 2 * math.pi)
    ctx.arc(SIZE - r, SIZE - r, r - 8, 0, 0.5 * math.pi)
    ctx.arc(r, SIZE - r, r - 8, 0.5 * math.pi, math.pi)
    ctx.close_path()
    ctx.set_source_rgba(*hexc(ring))
    ctx.set_line_width(16)
    ctx.stroke()


CHARACTERS = {
    "alina": dict(male=False, skin="f7d5c0", hair="7a4630", hair_style="long", eyes="5a8a6a", earrings=True,
                  outfit=dict(jacket="8ab8e0", shirt="ffffff", necklace=True), bg=("bfe6ff", "ffe9d6"), ring="f2c94c"),
    "boris": dict(male=True, skin="f0c8a8", hair="b8b8b8", hair_style="short", eyes="6a5a40", glasses=True, beard=True,
                  outfit=dict(jacket="7a5a3a", shirt="f4f0e8", tie="2a6a4a"), bg=("ffe6b8", "f4d0a0"), ring="c89a5a"),
    "viktor": dict(male=True, skin="e8c0a0", hair="1e1a22", hair_style="slick", eyes="4a4a6a",
                   outfit=dict(jacket="2a2a34", shirt="e8e8f0", tie="b82a2a"), bg=("6a5a7a", "2a2436"), ring="b82a2a"),
    "marina": dict(male=False, skin="f8dcc8", hair="e8c06a", hair_style="bob", eyes="3a7ab0", earrings=True,
                   outfit=dict(jacket="d8443a", shirt="fff4e8"), bg=("ffd6d0", "fff0e0"), ring="d8443a"),
    "oleg": dict(male=True, skin="e8bc98", hair="4a3424", hair_style="cap", eyes="4a6a8a",
                 outfit=dict(jacket="2a3a6a", shirt="c8d8f0", tie="1a2440", badge=True), bg=("c8dcf8", "a8c0e8"), ring="2a3a6a"),
    "zina": dict(male=False, skin="f0ccb4", hair="d8d8d8", hair_style="bun", eyes="6a6a5a", glasses=True, wrinkles=True,
                 outfit=dict(jacket="8a5a8a", shirt="f4f0e8", shawl="c86a8a"), bg=("f8e6f0", "e8d0e0"), ring="8a5a8a"),
}
EXPRESSIONS = ["smile", "talk", "happy", "surprised", "worried", "angry", "smug"]


def render(name, expr, out_path, size=512):
    c = CHARACTERS[name]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    background(ctx, *c["bg"])
    hair_back(ctx, c)
    body(ctx, c)
    face(ctx, c)
    eyes(ctx, c, expr)
    mouth(ctx, c, expr)
    hair_front(ctx, c)
    frame(ctx, c["ring"])
    tmp = out_path + ".tmp.png"
    surf.write_to_png(tmp)
    from PIL import Image
    Image.open(tmp).resize((size, size), Image.LANCZOS).save(out_path)
    os.remove(tmp)


def gen_portraits(out):
    os.makedirs(out, exist_ok=True)
    for name in CHARACTERS:
        for e in EXPRESSIONS:
            render(name, e, os.path.join(out, "%s_%s.png" % (name, e)))
