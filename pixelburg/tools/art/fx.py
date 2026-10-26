"""Weather and effect sprites: rain, splashes, snow, lightning, fire, lamp light, speech bubble."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw

from raster import Canvas, C
from props import lamp_post


def save(img, out, name):
    img.save(os.path.join(out, name + ".png"))


def soft_circle(r, col, power=1.6, steps=6):
    s = r * 2
    ys, xs = np.mgrid[0:s, 0:s]
    d = np.hypot(xs + 0.5 - r, ys + 0.5 - r) / r
    a = np.zeros((s, s, 4), np.uint8)
    a[..., :3] = col[:3]
    a[..., 3] = (col[3] * np.round(np.clip(1 - d, 0, 1) ** power * steps) / steps).astype(np.uint8)
    return Image.fromarray(a)


def gen_fx(out):
    os.makedirs(out, exist_ok=True)
    meta = {}
    # smoke puff
    p = soft_circle(6, (236, 236, 240, 255), 0.01, 1)
    pa = np.array(p)
    pa[:6, :, :3] = np.minimum(255, pa[:6, :, :3].astype(int) + 10)
    save(Image.fromarray(pa), out, "puff")
    save(soft_circle(48, (255, 214, 140, 210)), out, "glow")
    # small lamp head glow and the light pool it casts on the ground (squashed ellipse)
    save(soft_circle(8, (255, 230, 160, 255), 1.2, 5), out, "lamp_head")
    pool = soft_circle(40, (255, 214, 140, 150), 1.4, 6).resize((80, 40), Image.NEAREST)
    save(pool, out, "light_pool")
    s = Image.new("RGBA", (9, 9), (0, 0, 0, 0))
    for i in range(9):
        s.putpixel((4, i), (255, 248, 200, 255 if abs(i - 4) < 3 else 160))
        s.putpixel((i, 4), (255, 248, 200, 255 if abs(i - 4) < 3 else 160))
    save(s, out, "spark")
    # rain streak (slanted), splash frames, snowflakes
    r = Image.new("RGBA", (4, 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(r)
    d.line((3, 0, 0, 13), fill=(200, 220, 255, 200))
    d.line((3, 0, 2, 4), fill=(240, 248, 255, 230))
    save(r, out, "rain")
    sp = Image.new("RGBA", (30, 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    for f in range(3):
        w = 2 + f * 3
        d.arc((f * 10 + 5 - w, 3 - w // 2, f * 10 + 5 + w, 3 + w // 2), 180, 360, fill=(220, 236, 255, 220 - f * 60))
    save(sp, out, "splash")
    for i, size in enumerate((3, 5, 7)):
        fl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        c = size // 2
        for k in range(size):
            fl.putpixel((c, k), (255, 255, 255, 230))
            fl.putpixel((k, c), (255, 255, 255, 230))
            if size >= 5 and 0 < k < size - 1:
                fl.putpixel((k, k), (240, 246, 255, 170))
                fl.putpixel((k, size - 1 - k), (240, 246, 255, 170))
        save(fl, out, "snow_%d" % i)
    # lightning bolts
    rng = np.random.default_rng(5)
    for i in range(3):
        w, h = 140, 420
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        pts = [(w / 2, 0)]
        x, y = w / 2, 0
        while y < h - 10:
            y += rng.uniform(18, 40)
            x = np.clip(x + rng.uniform(-22, 22), 10, w - 10)
            pts.append((x, min(y, h - 1)))
        branches = []
        for j in range(2, len(pts) - 2, 3):
            bx, by = pts[j]
            br = [(bx, by)]
            for k in range(3):
                bx += rng.uniform(-24, 24)
                by += rng.uniform(14, 30)
                br.append((bx, by))
            branches.append(br)
        for line, wid in [(pts, 7)] + [(b, 4) for b in branches]:
            d.line(line, fill=(150, 170, 255, 90), width=wid + 4)
        for line, wid in [(pts, 3)] + [(b, 2) for b in branches]:
            d.line(line, fill=(235, 240, 255, 255), width=wid)
        save(img, out, "lightning_%d" % i)
    # fire: 4 frames 20x28
    fire = Image.new("RGBA", (80, 28), (0, 0, 0, 0))
    for f in range(4):
        fr = np.zeros((28, 20, 4), np.uint8)
        ys, xs = np.mgrid[0:28, 0:20].astype(float)
        t = f * 1.7
        flick = np.sin(ys * 0.6 + t) * 1.6 + np.sin(ys * 0.27 - t * 1.3) * 1.2
        width = np.clip((ys - 2) / 26, 0, 1) ** 0.7 * 8.5
        dx = np.abs(xs - 10 - flick * (1 - ys / 28))
        m = dx < width
        heat = 1 - dx / np.maximum(width, 0.1)
        heat = heat * np.clip(ys / 26, 0, 1) ** 0.6
        cols = np.array([[200, 40, 20], [240, 110, 30], [255, 180, 50], [255, 236, 150]])
        idx = np.clip((heat * 4).astype(int), 0, 3)
        fr[..., :3] = cols[idx]
        fr[..., 3] = np.where(m, 240, 0)
        fire.paste(Image.fromarray(fr), (f * 20, 0))
    save(fire, out, "fire")
    # speech bubble 9-patch (24x24) with a separate tail
    b = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.rounded_rectangle((0, 0, 23, 23), radius=6, fill=(42, 32, 48, 255))
    d.rounded_rectangle((1, 1, 22, 22), radius=5, fill=(255, 252, 244, 255))
    d.line((3, 20, 20, 20), fill=(232, 224, 210, 255))
    save(b, out, "speech")
    t = Image.new("RGBA", (10, 7), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    d.polygon([(0, 0), (9, 0), (2, 6)], fill=(42, 32, 48, 255))
    d.polygon([(1, 0), (7, 0), (2, 4)], fill=(255, 252, 244, 255))
    save(t, out, "speech_tail")
    # rubble / smoke for damaged buildings
    save(soft_circle(10, (70, 66, 72, 200), 0.6, 3), out, "smoke_dark")
    return meta


def gen_lamp_props(out):
    """Quarter-tile street lamps (classic and modern) as world sprites."""
    meta = {}
    for style, h in (("classic", 30), ("modern", 34)):
        cv = Canvas(1, 50, pad=4)
        lamp_post(cv, 32, 32, h, style)
        img = cv.image()
        glow = cv.emission_image()
        bbox = img.getbbox()
        ax, ay = cv.screen(32, 32, 0)
        hx, hy = cv.screen(32 if style == "classic" else 39.5, 32, h + 3)
        img.crop(bbox).save(os.path.join(out, "lamp_%s.png" % style))
        glow.crop(bbox).save(os.path.join(out, "lamp_%s_glow.png" % style))
        meta["lamp_" + style] = {"anchor": [round(ax - bbox[0]), round(ay - bbox[1])],
                                 "head": [round(hx - bbox[0]), round(hy - bbox[1])]}
    return meta
