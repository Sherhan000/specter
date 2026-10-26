"""Side-view animals (facing right): 4 walk frames + 1 idle frame each."""
import os

import numpy as np
from PIL import Image, ImageDraw

OUT = (34, 26, 40, 255)


def rgb(h, f=1.0, a=255):
    h = h.lstrip("#")
    c = [min(255, max(0, int(int(h[i:i + 2], 16) * f))) for i in (0, 2, 4)]
    return (c[0], c[1], c[2], a)


def outline(img):
    a = np.array(img)
    m = a[..., 3] > 0
    pad = np.pad(m, 1)
    edge = ~m & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
    a[edge] = OUT
    return Image.fromarray(a)


def legs(d, xs, top, bottom, frame, col, col_d):
    """Quadruped legs: xs = [back_far, back_near, front_far, front_near]."""
    sw = [0, 1, 0, -1][frame] if frame < 4 else 0
    for i, x in enumerate(xs):
        far = i in (0, 2)
        off = sw if i in (0, 3) else -sw
        c = col_d if far else col
        d.line((x, top, x + off, bottom), fill=c)
        d.line((x + 1, top, x + 1 + off, bottom), fill=c)


def quad(spec, frame):
    """Generic four-legged animal from an ellipse body, head and tail description."""
    W, H = spec["size"]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body, dark, belly = rgb(spec["col"]), rgb(spec["col"], 0.75), rgb(spec.get("belly", spec["col"]))
    bx0, by0, bx1, by1 = spec["body"]
    bob = 1 if frame in (1, 3) else 0
    idle = frame == 4
    legs(d, spec["legs"], by1 - 2 + bob, H - 1, frame, body, dark)
    if spec.get("hooves"):
        for x in spec["legs"]:
            d.point((x, H - 1), fill=rgb("2a2020"))
            d.point((x + 1, H - 1), fill=rgb("2a2020"))
    d.ellipse((bx0, by0 + bob, bx1, by1 + bob), fill=body)
    d.ellipse((bx0 + 2, (by0 + by1) // 2 + 1 + bob, bx1 - 3, by1 + bob), fill=belly)
    d.line((bx0 + 3, by0 + bob, bx1 - 4, by0 + bob), fill=rgb(spec["col"], 1.15))
    # tail
    tx, ty = spec["tail"]
    if spec.get("bushy_tail"):
        d.ellipse((tx - 5, ty - 2 + bob, tx + 1, ty + 3 + bob), fill=body)
        d.point((tx - 5, ty + bob), fill=rgb(spec.get("tail_tip", "f4f0e8")))
        d.point((tx - 4, ty + bob), fill=rgb(spec.get("tail_tip", "f4f0e8")))
    else:
        d.line((tx, ty + bob, tx - 2, ty + 2 + bob), fill=dark)
    # head
    hx, hy = spec["head"]
    if idle and spec.get("grazes"):
        hy += 4
    hw, hh = spec["head_size"]
    d.line((bx1 - 4, by0 + 2 + bob, hx, hy + hh // 2), fill=body, width=spec.get("neck", 3))
    d.ellipse((hx - hw // 2, hy, hx + hw // 2, hy + hh), fill=body)
    sx, sy = spec["snout"]
    d.ellipse((hx + sx - 2, hy + sy, hx + sx + 2, hy + sy + 2), fill=rgb(spec.get("snout_col", spec["col"]), 0.9))
    d.point((hx + sx + 2, hy + sy + 1), fill=rgb("1a1414"))
    d.point((hx + 1, hy + 2), fill=rgb("1a1414"))
    for (ex, ey) in spec.get("ears", []):
        d.line((hx + ex, hy + 1, hx + ex, hy + ey), fill=dark)
        d.point((hx + ex + 1, hy + ey + 1), fill=body)
    if spec.get("antlers"):
        c = rgb("8a6a3a")
        d.line((hx - 1, hy, hx - 3, hy - 5), fill=c)
        d.line((hx - 3, hy - 5, hx - 5, hy - 6), fill=c)
        d.line((hx - 2, hy - 3, hx, hy - 6), fill=c)
        d.line((hx + 1, hy, hx + 2, hy - 4), fill=c)
    if spec.get("tusk"):
        d.point((hx + sx, hy + sy + 3), fill=rgb("f4f0e8"))
    if spec.get("spots"):
        for (x, y) in spec["spots"]:
            d.point((x, y + bob), fill=rgb("f4ece0"))
    if spec.get("mane"):
        d.line((bx1 - 6, by0 + bob, hx - 2, hy), fill=dark, width=2)
    return outline(img)


SPECS = {
    "deer": dict(size=(26, 22), col="b8743e", belly="e4c49a", body=(4, 8, 19, 15), legs=[6, 8, 15, 17], tail=(5, 9),
                 head=(21, 3), head_size=(6, 5), snout=(3, 2), ears=[(-2, -2)], antlers=True, grazes=True, hooves=True,
                 spots=[(9, 10), (12, 9), (15, 10)], neck=3),
    "fox": dict(size=(24, 14), col="e0742a", belly="f4e8d8", body=(5, 4, 16, 10), legs=[7, 8, 13, 14], tail=(6, 6),
                head=(18, 2), head_size=(5, 4), snout=(3, 2), ears=[(-1, -2), (1, -2)], bushy_tail=True, neck=2),
    "wolf": dict(size=(26, 16), col="7a7e86", belly="c8ccd0", body=(5, 4, 18, 11), legs=[7, 9, 14, 16], tail=(6, 6),
                 head=(20, 2), head_size=(6, 5), snout=(3, 2), ears=[(-1, -2), (1, -2)], bushy_tail=True, tail_tip="5a5e66",
                 mane=True, neck=3),
    "boar": dict(size=(24, 15), col="5a4232", belly="6a5040", body=(3, 3, 18, 12), legs=[6, 8, 13, 15], tail=(4, 5),
                 head=(19, 4), head_size=(6, 6), snout=(3, 3), snout_col="8a6a5a", ears=[(-1, -2)], tusk=True, mane=True,
                 hooves=True, grazes=True, neck=4),
    "bear": dict(size=(30, 21), col="6a4428", belly="7a5232", body=(3, 4, 23, 16), legs=[6, 9, 18, 21], tail=(4, 8),
                 head=(24, 4), head_size=(8, 7), snout=(4, 3), snout_col="a07a52", ears=[(-3, -1), (2, -1)], neck=5,
                 grazes=True),
    "dog": dict(size=(16, 11), col="c89a5a", belly="f0dcc0", body=(2, 3, 11, 8), legs=[4, 5, 9, 10], tail=(3, 3),
                head=(12, 1), head_size=(4, 4), snout=(2, 2), ears=[(-1, 1)], neck=2),
}


def rabbit(frame):
    img = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body, belly = rgb("b8a898"), rgb("eee4d8")
    hop = [0, 2, 3, 1, 0][frame]
    y = 4 - hop
    d.ellipse((1, y + 3, 8, y + 8), fill=body)
    d.ellipse((2, y + 6, 7, y + 8), fill=belly)
    d.ellipse((6, y + 1, 10, y + 5), fill=body)
    d.line((7, y + 1, 7, y - 3), fill=body, width=2)
    d.point((8, y - 2), fill=rgb("e8b0b0"))
    d.point((9, y + 3), fill=rgb("1a1414"))
    d.point((10, y + 4), fill=rgb("e88a8a"))
    d.ellipse((0, y + 4, 2, y + 6), fill=rgb("f8f4f0"))
    d.line((6, y + 8, 8 + (hop > 1), y + 9), fill=body)
    return outline(img)


def gen_animals(out_dir):
    meta = {}
    for name, spec in list(SPECS.items()) + [("rabbit", None)]:
        frames = [quad(spec, f) if spec else rabbit(f) for f in range(5)]
        w, h = frames[0].size
        sheet = Image.new("RGBA", (w * 5, h), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            sheet.paste(f, (i * w, 0))
        sheet.save(os.path.join(out_dir, "animal_%s.png" % name))
        meta[name] = [w, h]
    # birds: 2 frames
    b = Image.new("RGBA", (18, 7), (0, 0, 0, 0))
    for (x, y) in ((0, 2), (1, 1), (2, 1), (3, 2), (4, 3), (5, 2), (6, 1), (7, 1), (8, 2)):
        b.putpixel((x, y), (40, 40, 52, 255))
    for (x, y) in ((9, 4), (10, 4), (11, 3), (12, 3), (13, 4), (14, 3), (15, 3), (16, 4), (17, 4)):
        b.putpixel((x, y), (40, 40, 52, 255))
    b.save(os.path.join(out_dir, "bird.png"))
    return meta
