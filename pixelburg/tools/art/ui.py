"""Interface art: icons (16 and 32 px), round buttons, panels, bubble."""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw

import icons


def rgba(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def outline(img, col=(34, 26, 40, 255)):
    a = np.array(img)
    m = a[..., 3] > 0
    pad = np.pad(m, 1)
    e = ~m & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
    a[e] = col
    return Image.fromarray(a)


class Pen:
    """Draws in a 32-unit space scaled to the target size."""

    def __init__(self, size):
        self.s = size
        self.img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def p(self, *pts):
        k = self.s / 32
        return [round(v * k) for v in pts]

    def ellipse(self, box, fill, outline_=None, width=1):
        self.d.ellipse(self.p(*box), fill=rgba(fill) if fill else None, outline=rgba(outline_) if outline_ else None,
                       width=max(1, round(width * self.s / 32)))

    def rect(self, box, fill):
        self.d.rectangle(self.p(*box), fill=rgba(fill))

    def rrect(self, box, r, fill):
        self.d.rounded_rectangle(self.p(*box), radius=max(1, round(r * self.s / 32)), fill=rgba(fill))

    def poly(self, pts, fill):
        flat = []
        for (x, y) in pts:
            flat += self.p(x, y)
        self.d.polygon(flat, fill=rgba(fill))

    def line(self, pts, fill, width=2):
        flat = []
        for (x, y) in pts:
            flat += self.p(x, y)
        self.d.line(flat, fill=rgba(fill), width=max(1, round(width * self.s / 32)), joint="curve")

    def arc(self, box, a0, a1, fill, width=2):
        self.d.arc(self.p(*box), a0, a1, fill=rgba(fill), width=max(1, round(width * self.s / 32)))


def i_coin(p):
    p.ellipse((3, 3, 29, 29), "c8901c")
    p.ellipse((4, 3, 28, 27), "f0c040")
    p.ellipse((8, 7, 24, 23), None, "c8901c", 2)
    p.rect((14, 10, 18, 20), "c8901c")
    p.arc((6, 5, 22, 21), 190, 260, "fff4b0", 2)


def i_gem(p):
    p.poly([(9, 4), (23, 4), (29, 12), (16, 29), (3, 12)], "1e8a4a")
    p.poly([(9, 4), (23, 4), (26, 12), (6, 12)], "4ad07a")
    p.poly([(6, 12), (26, 12), (16, 29)], "2aa85a")
    p.poly([(12, 12), (20, 12), (16, 29)], "3ac06a")
    p.poly([(10, 5), (15, 5), (12, 11), (8, 11)], "b8f8d0")


def i_goods(p):
    p.rect((4, 10, 28, 28), "b07a40")
    p.rect((4, 10, 28, 14), "d09a58")
    p.rect((14, 10, 18, 28), "8a5a28")
    p.rect((5, 15, 13, 16), "c89050")
    p.rect((19, 15, 27, 16), "c89050")


def i_pop(p):
    p.ellipse((11, 3, 21, 13), "f0c09a")
    p.rect((11, 3, 21, 6), "6a3a1a")
    p.rrect((6, 14, 26, 30), 6, "3a7ad8")
    p.rect((14, 14, 18, 20), "f4f4f4")


def i_jobs(p):
    p.rrect((3, 10, 29, 28), 3, "8a5a3a")
    p.rect((11, 5, 21, 10), "5a3a2a")
    p.d.rectangle(p.p(13, 7, 19, 10), fill=(0, 0, 0, 0))
    p.rect((3, 17, 29, 19), "5a3a2a")
    p.rect((14, 15, 18, 21), "e8c040")


def i_happy(p):
    p.ellipse((2, 2, 30, 30), "e8b020")
    p.ellipse((3, 2, 29, 28), "f8d040")
    p.ellipse((10, 9, 13, 14), "3a2a1a")
    p.ellipse((19, 9, 22, 14), "3a2a1a")
    p.arc((8, 10, 24, 24), 20, 160, "3a2a1a", 2)


def i_star(p):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = 14 if k % 2 == 0 else 6
        pts.append((16 + r * math.cos(a), 17 + r * math.sin(a)))
    p.poly(pts, "f8c030")
    p.poly([(16, 4), (19, 13), (16, 15), (13, 13)], "fff0a0")


def i_build(p):
    p.line([(6, 27), (20, 13)], "8a5a3a", 4)
    p.poly([(15, 6), (24, 3), (29, 8), (26, 11), (22, 9), (18, 13), (14, 9)], "9aa4b0")
    p.poly([(15, 6), (24, 3), (26, 5), (17, 8)], "dce4ec")


def i_road(p):
    p.poly([(11, 3), (21, 3), (30, 29), (2, 29)], "4a4a54")
    p.poly([(11, 3), (12, 3), (4, 29), (2, 29)], "c8c0b0")
    p.poly([(20, 3), (21, 3), (30, 29), (28, 29)], "c8c0b0")
    for y in (5, 13, 21):
        p.rect((15, y, 17, y + 5), "f0e8d0")


def i_demolish(p):
    p.rect((2, 15, 22, 24), "e8b020")
    p.rect((6, 8, 16, 15), "e8b020")
    p.rect((8, 10, 14, 14), "8ac0e0")
    p.ellipse((3, 21, 11, 29), "2a2a2a")
    p.ellipse((14, 21, 22, 29), "2a2a2a")
    p.poly([(22, 14), (30, 9), (30, 26), (24, 26)], "9aa4b0")


def i_mission(p):
    p.rect((6, 4, 26, 29), "f4e4b8")
    p.rect((4, 2, 28, 6), "c89a5a")
    p.rect((4, 27, 28, 30), "c89a5a")
    for y in (10, 15, 20):
        p.rect((9, y, 22, y + 1), "a08a60")
    p.line([(17, 22), (20, 25), (27, 15)], "3ab04a", 3)


def i_land(p):
    p.poly([(16, 4), (30, 16), (16, 28), (2, 16)], "5aa840")
    p.poly([(16, 4), (30, 16), (16, 16)], "6ac04a")
    p.rect((15, 6, 17, 18), "6a4a2a")
    p.poly([(17, 6), (26, 9), (17, 12)], "e84a3a")


def i_gear(p):
    for k in range(8):
        a = k * math.pi / 4
        x, y = 16 + 11 * math.cos(a), 16 + 11 * math.sin(a)
        p.rect((x - 3, y - 3, x + 3, y + 3), "8a94a0")
    p.ellipse((5, 5, 27, 27), "9aa4b0")
    p.ellipse((11, 11, 21, 21), "4a4a54")


def i_ok(p):
    p.line([(4, 16), (12, 24), (28, 7)], "3ac04a", 5)


def i_cancel(p):
    p.line([(6, 6), (26, 26)], "e84a3a", 5)
    p.line([(26, 6), (6, 26)], "e84a3a", 5)


def i_lock(p):
    p.arc((8, 2, 24, 20), 180, 360, "9aa4b0", 3)
    p.rect((8, 11, 9, 14), "9aa4b0")
    p.rect((23, 11, 24, 14), "9aa4b0")
    p.rrect((5, 13, 27, 29), 3, "e8b020")
    p.rect((15, 18, 17, 24), "7a5a10")


def i_warn(p):
    p.poly([(16, 2), (31, 29), (1, 29)], "f8c030")
    p.rect((15, 10, 17, 21), "2a2a2a")
    p.rect((15, 24, 17, 26), "2a2a2a")


def i_noroad(p):
    p.ellipse((2, 2, 30, 30), "e84a3a")
    p.rect((7, 13, 25, 19), "f8f8f8")


def i_sound(p):
    p.poly([(3, 12), (9, 12), (17, 5), (17, 27), (9, 20), (3, 20)], "e8e8f0")
    p.arc((14, 9, 24, 23), -60, 60, "e8e8f0", 2)
    p.arc((14, 4, 30, 28), -60, 60, "e8e8f0", 2)


def i_music(p):
    p.ellipse((3, 21, 12, 28), "e8e8f0")
    p.ellipse((18, 18, 27, 25), "e8e8f0")
    p.rect((10, 5, 12, 25), "e8e8f0")
    p.rect((25, 3, 27, 22), "e8e8f0")
    p.poly([(10, 5), (27, 2), (27, 7), (10, 10)], "e8e8f0")


def i_globe(p):
    p.ellipse((2, 2, 30, 30), "3a8ad8")
    p.poly([(7, 7), (15, 8), (14, 15), (8, 17), (5, 12)], "6ac04a")
    p.poly([(18, 17), (25, 15), (27, 22), (20, 26)], "6ac04a")
    p.arc((4, 4, 28, 28), 200, 250, "a8d0f8", 2)


def i_upgrade(p):
    p.poly([(16, 2), (29, 15), (21, 15), (21, 29), (11, 29), (11, 15), (3, 15)], "3ac04a")
    p.poly([(16, 2), (29, 15), (25, 15), (16, 6)], "8af07a")


def i_speed(p):
    p.poly([(19, 1), (6, 18), (15, 18), (12, 31), (26, 12), (17, 12)], "f8c030")
    p.poly([(19, 1), (6, 18), (9, 18), (19, 5)], "fff0a0")


def i_sun(p):
    for k in range(8):
        a = k * math.pi / 4
        p.line([(16 + 9 * math.cos(a), 16 + 9 * math.sin(a)), (16 + 14 * math.cos(a), 16 + 14 * math.sin(a))], "f8a020", 2)
    p.ellipse((8, 8, 24, 24), "f8c030")
    p.ellipse((10, 9, 18, 16), "fff0a0")


def i_moon(p):
    p.ellipse((4, 4, 28, 28), "e8e8d0")
    p.d.ellipse(p.p(12, 1, 34, 23), fill=(0, 0, 0, 0))


def i_sunrise(p):
    p.rect((0, 22, 32, 24), "e8a040")
    p.d.pieslice(p.p(6, 10, 26, 32), 180, 360, fill=rgba("f8b030"))
    for a in (200, 240, 270, 300, 340):
        r = math.radians(a)
        p.line([(16 + 13 * math.cos(r), 21 + 13 * math.sin(r)), (16 + 16 * math.cos(r), 21 + 16 * math.sin(r))], "f8a020", 2)
    p.rect((2, 26, 30, 28), "e87a30")


def i_sunset(p):
    p.d.pieslice(p.p(6, 12, 26, 32), 180, 360, fill=rgba("f86a30"))
    p.rect((0, 22, 32, 24), "c84a50")
    p.rect((4, 26, 28, 27), "a84a70")
    p.rect((8, 29, 24, 30), "8a4a80")


def i_plus(p):
    p.rect((13, 4, 19, 28), "ffffff")
    p.rect((4, 13, 28, 19), "ffffff")


def i_info(p):
    p.ellipse((2, 2, 30, 30), "3a8ad8")
    p.rect((14, 13, 18, 25), "ffffff")
    p.rect((14, 7, 18, 10), "ffffff")


def i_clock(p):
    p.ellipse((2, 2, 30, 30), "f4f4f4")
    p.ellipse((2, 2, 30, 30), None, "6a6a74", 2)
    p.line([(16, 16), (16, 7)], "3a3a44", 2)
    p.line([(16, 16), (22, 19)], "3a3a44", 2)


ICONS = {"coin": i_coin, "gem": i_gem, "goods": i_goods, "pop": i_pop, "jobs": i_jobs, "happy": i_happy,
         "star": i_star, "build": i_build, "road": i_road, "demolish": i_demolish, "mission": i_mission,
         "land": i_land, "gear": i_gear, "ok": i_ok, "cancel": i_cancel, "lock": i_lock, "warn": i_warn,
         "noroad": i_noroad, "sound": i_sound, "music": i_music, "globe": i_globe, "upgrade": i_upgrade,
         "speed": i_speed, "sun": i_sun, "moon": i_moon, "sunrise": i_sunrise, "sunset": i_sunset,
         "plus": i_plus, "info": i_info, "clock": i_clock}


def gen_icons(out):
    names = list(ICONS)
    for size in (16, 32):
        sheet = Image.new("RGBA", (size * len(names), size), (0, 0, 0, 0))
        for k, n in enumerate(names):
            pen = Pen(size)
            ICONS[n](pen)
            img = pen.img
            img = outline(img)
            sheet.paste(img, (k * size, 0))
        sheet.save(os.path.join(out, "icons_%d.png" % size))
    json.dump(names, open(os.path.join(out, "icons.json"), "w"))


def gradient_circle(size, top, bottom, rim, pressed=False):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    a = np.zeros((size, size, 4))
    c = (size - 1) / 2
    ys, xs = np.mgrid[0:size, 0:size]
    d = np.hypot(xs - c, ys - c)
    t = (ys / size)[..., None]
    if pressed:
        top, bottom = [v * 0.85 for v in top], [v * 0.85 for v in bottom]
    fill = np.array(top) * (1 - t) + np.array(bottom) * t
    a[..., :3] = fill
    a[..., 3] = 255
    ring = (d > c - 3.5) & (d <= c - 1.2)
    a[ring, :3] = rim
    outer = d > c - 1.2
    a[outer, :3] = (34, 26, 40)
    a[d > c + 0.3, 3] = 0
    hl = (d < c - 6) & (ys < c - 2) & (np.hypot(xs - c * 0.8, ys - c * 0.55) < c * 0.55) & (np.hypot(xs - c * 0.8, ys - c * 0.85) > c * 0.6)
    if not pressed:
        a[hl, :3] = a[hl, :3] * 0.5 + 255 * 0.5
    return Image.fromarray(a.astype(np.uint8))


def panel(path, fill_top, fill_bot, border, light, size=24, r=4):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=r + 1, fill=(34, 26, 40, 255))
    d.rounded_rectangle((1, 1, size - 2, size - 2), radius=r, fill=rgba(border))
    inner = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    a = np.zeros((size, size, 4))
    for y in range(size):
        t = y / (size - 1)
        a[y, :, :3] = np.array(rgba(fill_top)[:3]) * (1 - t) + np.array(rgba(fill_bot)[:3]) * t
    a[..., 3] = 255
    inner = Image.fromarray(a.astype(np.uint8))
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle((3, 3, size - 4, size - 4), radius=max(1, r - 1), fill=255)
    img.paste(inner, (0, 0), m)
    d.line((5, 3, size - 6, 3), fill=rgba(light))
    img.save(path)


def gen_ui(out):
    os.makedirs(out, exist_ok=True)
    icons.gen_icons(out)
    colors = {"green": ((120, 210, 90), (50, 150, 50), (40, 110, 40)),
              "blue": ((110, 170, 240), (40, 100, 200), (30, 70, 150)),
              "red": ((240, 110, 90), (190, 50, 40), (140, 40, 30)),
              "orange": ((250, 190, 80), (220, 120, 30), (160, 90, 20)),
              "grey": ((180, 180, 190), (110, 110, 124), (80, 80, 92)),
              "purple": ((190, 130, 230), (120, 60, 180), (90, 40, 140))}
    for name, (top, bot, rim) in colors.items():
        gradient_circle(48, top, bot, rim).save(os.path.join(out, "round_%s.png" % name))
        gradient_circle(48, top, bot, rim, True).save(os.path.join(out, "round_%s_p.png" % name))
    panel(os.path.join(out, "panel.png"), "fbf4e2", "efe0bc", "c09050", "ffffff", 24, 5)
    panel(os.path.join(out, "panel_dark.png"), "3a3448", "2a2436", "4a4458", "5a5470", 24, 5)
    panel(os.path.join(out, "pill.png"), "3a3448", "241e30", "564e68", "6a6280", 16, 6)
    panel(os.path.join(out, "card.png"), "fffaf0", "f4e8d0", "d8b880", "ffffff", 16, 3)
    panel(os.path.join(out, "card_sel.png"), "fff4d0", "ffe8a8", "e8a030", "ffffff", 16, 3)
    for name, (top, bot, rim) in colors.items():
        def hx(c):
            return "%02x%02x%02x" % tuple(int(v) for v in c)
        panel(os.path.join(out, "btn_%s.png" % name), hx(top), hx(bot), hx(rim), hx([min(255, v + 60) for v in top]), 16, 3)
        panel(os.path.join(out, "btn_%s_h.png" % name), hx([min(255, v + 20) for v in top]), hx([min(255, v + 20) for v in bot]),
              hx(rim), "ffffff", 16, 3)
    # bubble
    img = Image.new("RGBA", (26, 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, 25, 25), fill=(34, 26, 40, 255))
    d.polygon([(9, 22), (17, 22), (13, 29)], fill=(34, 26, 40, 255))
    d.ellipse((1, 1, 24, 24), fill=(255, 255, 255, 255))
    d.polygon([(10, 22), (16, 22), (13, 27)], fill=(255, 255, 255, 255))
    d.arc((3, 3, 22, 22), 30, 150, fill=(208, 220, 236, 255), width=2)
    img.save(os.path.join(out, "bubble.png"))
