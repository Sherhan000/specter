"""Interface art for the smooth look: a 128 px icon atlas, round buttons and the collect bubble.
Panels, pills and rectangular buttons are drawn by the game itself (rounded style boxes)."""
import json
import math
import os

import cairo
import numpy as np
from PIL import Image

import icons

CELL = 128
COLS = 16


def _surface_to_image(surf):
    img = Image.frombuffer("RGBA", (surf.get_width(), surf.get_height()), bytes(surf.get_data()), "raw", "BGRA", 0, 1)
    a = np.array(img).astype(float)
    alpha = a[..., 3:4] / 255.0
    a[..., :3] = np.where(alpha > 0, a[..., :3] / np.maximum(alpha, 1e-6), 0)
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"))


def gen_icon_atlas(out):
    names = list(icons.ICONS)
    rows = math.ceil(len(names) / COLS)
    sheet = Image.new("RGBA", (CELL * COLS, CELL * rows), (0, 0, 0, 0))
    for i, n in enumerate(names):
        sheet.paste(icons.render_icon(icons.ICONS[n], CELL), ((i % COLS) * CELL, (i // COLS) * CELL))
    sheet.save(os.path.join(out, "icons_128.png"))
    json.dump({"names": names, "cell": CELL, "cols": COLS}, open(os.path.join(out, "icons_atlas.json"), "w"))


COLORS = {"green": ("4cc274", "22995a", "17784a"),
          "blue": ("5aa2f4", "2f74d6", "2359aa"),
          "red": ("f2716a", "d6453c", "a8302a"),
          "orange": ("ffbe4a", "f08c1a", "c06a10"),
          "grey": ("8d96a8", "5d6678", "474e5e"),
          "purple": ("a67ef0", "7a4fd6", "5c3aa8")}


def _hex(h, a=1.0):
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def round_button(top, bottom, rim, pressed=False, size=128):
    k = 2
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size * k, size * k)
    c = cairo.Context(surf)
    c.scale(k, k)
    cx, cy, r = size / 2, size / 2 - (0 if pressed else 2), size / 2 - 8
    # soft drop shadow
    for i in range(8, 0, -1):
        c.arc(size / 2, size / 2 + 4, r + i * 0.6, 0, 2 * math.pi)
        c.set_source_rgba(0, 0, 0, 0.035 if not pressed else 0.02)
        c.fill()
    # rim
    c.arc(cx, cy, r, 0, 2 * math.pi)
    c.set_source_rgba(*_hex(rim))
    c.fill()
    # face
    g = cairo.LinearGradient(0, cy - r, 0, cy + r)
    g.add_color_stop_rgba(0, *_hex(top if not pressed else bottom))
    g.add_color_stop_rgba(1, *_hex(bottom if not pressed else rim))
    c.arc(cx, cy - (1.5 if not pressed else 0), r - 3, 0, 2 * math.pi)
    c.set_source(g)
    c.fill()
    # thin light ring and a soft highlight
    c.arc(cx, cy - 1.5, r - 4.5, 0, 2 * math.pi)
    c.set_source_rgba(1, 1, 1, 0.28 if not pressed else 0.12)
    c.set_line_width(1.6)
    c.stroke()
    if not pressed:
        c.save()
        c.translate(cx, cy - r * 0.45)
        c.scale(r * 0.62, r * 0.32)
        c.arc(0, 0, 1, 0, 2 * math.pi)
        c.restore()
        hg = cairo.LinearGradient(0, cy - r * 0.8, 0, cy - r * 0.1)
        hg.add_color_stop_rgba(0, 1, 1, 1, 0.32)
        hg.add_color_stop_rgba(1, 1, 1, 1, 0.0)
        c.set_source(hg)
        c.fill()
    return _surface_to_image(surf).resize((size, size), Image.LANCZOS)


def bubble(out):
    w, h = 104, 120
    k = 2
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w * k, h * k)
    c = cairo.Context(surf)
    c.scale(k, k)
    cx, cy, r = w / 2, 50, 44
    for i in range(6, 0, -1):
        c.arc(cx, cy + 4, r + i * 0.7, 0, 2 * math.pi)
        c.set_source_rgba(0, 0, 0, 0.04)
        c.fill()
    c.move_to(cx - 14, cy + r - 8)
    c.line_to(cx, h - 6)
    c.line_to(cx + 14, cy + r - 8)
    c.close_path()
    c.set_source_rgba(1, 1, 1, 1)
    c.fill()
    c.arc(cx, cy, r, 0, 2 * math.pi)
    c.set_source_rgba(1, 1, 1, 1)
    c.fill()
    c.arc(cx, cy, r - 1, 0, 2 * math.pi)
    c.set_source_rgba(0.75, 0.8, 0.88, 1)
    c.set_line_width(2)
    c.stroke()
    _surface_to_image(surf).resize((w, h), Image.LANCZOS).save(os.path.join(out, "bubble.png"))


def gen(out):
    os.makedirs(out, exist_ok=True)
    gen_icon_atlas(out)
    for name, (top, bottom, rim) in COLORS.items():
        round_button(top, bottom, rim).save(os.path.join(out, "round_%s.png" % name))
        round_button(top, bottom, rim, True).save(os.path.join(out, "round_%s_p.png" % name))
    bubble(out)


if __name__ == "__main__":
    import sys
    gen(sys.argv[1])
