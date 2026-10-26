"""Saves a rendered Canvas as game sprites and composes previews.

Every layer is cropped to its content and stored with its offset from the anchor: the bottom
vertex of the footprint (grid point (x + n, y + n)). Layers:
  name.png          the body (y-sorted with people and cars)
  name_base.png     ground layer: paths, patios, parking (drawn under everything)
  name_sh.png       cast shadow, quarter resolution
  name_glow.png     always-on light at night (signs, shop windows, lamps)
  name_rooms.png    window light of four room groups, half resolution
"""
import os

import numpy as np
from PIL import Image

from raster import U


def _crop(img, any_channel=False):
    if any_channel:
        a = np.array(img).max(axis=2)
        ys, xs = np.where(a > 0)
        if len(xs) == 0:
            return None, None
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    else:
        bbox = img.getbbox()
        if bbox is None:
            return None, None
    return img.crop(bbox), bbox


def save_sprite(name, cv, out):
    ax, ay = cv.ox, cv.oy + cv.size          # anchor in canvas pixels
    meta = {"size": cv.n}
    body, bb = _crop(cv.image())
    if body is None:
        return None
    body.save(os.path.join(out, name + ".png"))
    meta["o"] = [bb[0] - ax, bb[1] - ay]
    meta["w"] = [body.width, body.height]
    meta["height"] = int(ay - bb[1] - cv.size)
    base, b2 = _crop(cv.base_image())
    if base is not None:
        base.save(os.path.join(out, name + "_base.png"))
        meta["base"] = [b2[0] - ax, b2[1] - ay]
    glow = cv.emission_image()
    g, b3 = _crop(glow)
    if g is not None:
        g.save(os.path.join(out, name + "_glow.png"))
        meta["glow"] = [b3[0] - ax, b3[1] - ay]
    rooms = cv.rooms_image()
    r, b4 = _crop(rooms, True)
    if r is not None and np.array(r).max() > 0:
        # resize each channel on its own: RGBA resizing would premultiply by the 4th group
        size2 = (max(1, r.width // 2), max(1, r.height // 2))
        r2 = Image.merge("RGBA", [ch.resize(size2, Image.BOX) for ch in r.split()])
        r2.save(os.path.join(out, name + "_rooms.png"))
        meta["rooms"] = [b4[0] - ax, b4[1] - ay, r.width / r2.width]
    sh, off = cv.shadow_image()
    if sh is not None:
        s, b5 = _crop(sh)
        if s is not None:
            k = 4
            s2 = s.resize((max(1, s.width // k), max(1, s.height // k)), Image.BOX)
            s2.save(os.path.join(out, name + "_sh.png"))
            meta["sh"] = [off[0] + b5[0] - ax, off[1] + b5[1] - ay, s.width / s2.width]
    meta["points"] = {k: [round(x - ax, 1), round(y - ay, 1)] for k, (x, y) in cv.points.items()}
    for k in ("door_g", "entry_g"):
        if hasattr(cv, k):
            meta[k] = getattr(cv, k)
    return meta


def compose(meta, out, name, night=False, rooms_on=(1, 1, 0, 0)):
    """Preview image of one saved sprite on grass, as the game would draw it."""
    n = meta["size"]
    W, H = 2 * n * U + 400, 2 * n * U + meta["height"] + 400
    canvas = Image.new("RGBA", (W, H), (98, 152, 66, 255))
    ax, ay = W // 2, H - 120
    def paste(img, ox, oy, scale=1):
        if scale != 1:
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.BILINEAR)
        canvas.alpha_composite(img, (int(ax + ox), int(ay + oy)))
    if "base" in meta:
        paste(Image.open(os.path.join(out, name + "_base.png")), *meta["base"])
    if "sh" in meta:
        paste(Image.open(os.path.join(out, name + "_sh.png")), meta["sh"][0], meta["sh"][1], meta["sh"][2])
    paste(Image.open(os.path.join(out, name + ".png")), *meta["o"])
    if night:
        arr = np.array(canvas).astype(float)
        arr[..., :3] *= np.array([0.32, 0.36, 0.55])
        canvas = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        add = np.zeros((H, W, 3))
        if "glow" in meta:
            g = np.array(Image.open(os.path.join(out, name + "_glow.png"))).astype(float)
            x0, y0 = int(ax + meta["glow"][0]), int(ay + meta["glow"][1])
            add[y0:y0 + g.shape[0], x0:x0 + g.shape[1]] += g[..., :3] * g[..., 3:4] / 255
        if "rooms" in meta:
            r = Image.open(os.path.join(out, name + "_rooms.png"))
            sz = (int(r.width * meta["rooms"][2]), int(r.height * meta["rooms"][2]))
            r = np.dstack([np.array(ch.resize(sz, Image.BILINEAR)) for ch in r.split()]).astype(float)
            lvl = (r * np.array(rooms_on)).max(axis=2) / 255
            x0, y0 = int(ax + meta["rooms"][0]), int(ay + meta["rooms"][1])
            add[y0:y0 + r.shape[0], x0:x0 + r.shape[1]] += lvl[..., None] * np.array([255, 205, 130])
        arr = np.array(canvas).astype(float)
        arr[..., :3] += add
        canvas = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return canvas
