"""Forest and nature sprites at real scale: tree clumps that fill one forest tile, single
trees for the land, undergrowth. Clumps carry their own soft shadow."""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

from raster import Canvas, U, C, flat, solid_res, nores
import kit


def _save(cv, name, out, meta, shadow=True):
    ax, ay = cv.ox, cv.oy + cv.size
    body = cv.image()
    ox, oy = 0, 0
    if shadow:
        sh, off = cv.shadow_image(0.36)
        if sh is not None:
            x0, y0 = min(0, int(off[0])), min(0, int(off[1]))
            x1, y1 = max(body.width, int(off[0]) + sh.width), max(body.height, int(off[1]) + sh.height)
            big = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
            big.alpha_composite(sh, (int(off[0]) - x0, int(off[1]) - y0))
            big.alpha_composite(body, (-x0, -y0))
            body, ox, oy = big, x0, y0
    bb = body.getbbox()
    body = body.crop(bb)
    body.save(os.path.join(out, name + ".png"))
    meta[name] = {"o": [bb[0] + ox - ax, bb[1] + oy - ay], "w": [body.width, body.height]}


def _clump(seed, mix):
    """A forest tile: 3-5 trees. mix: 'leaf', 'pine' or 'mixed'."""
    rng = np.random.default_rng(seed)
    cv = Canvas(1, 160, pad=60)
    n = rng.integers(5, 8)
    spots = []
    for i in range(n):
        for _ in range(30):
            x, y = rng.uniform(14, 146), rng.uniform(14, 146)
            if all((x - a) ** 2 + (y - b) ** 2 > 36 ** 2 for a, b in spots):
                spots.append((x, y))
                break
    spots.sort(key=lambda p: p[0] + p[1])
    for i, (x, y) in enumerate(spots):
        r = rng.random()
        if mix == "pine" or (mix == "mixed" and r < 0.5):
            if rng.random() < 0.75:
                kit.conifer(cv, x, y, "spruce", rng.uniform(0.9, 1.3), seed * 10 + i)
            else:
                kit.pine(cv, x, y, rng.uniform(0.9, 1.1), seed * 10 + i)
        else:
            kind = ["oak", "maple", "birch", "lime", "oak"][rng.integers(0, 5)]
            kit.tree(cv, x, y, kind, rng.uniform(1.0, 1.35), seed * 10 + i)
    # a little undergrowth
    for i in range(rng.integers(1, 4)):
        kit.bush(cv, rng.uniform(15, 145), rng.uniform(15, 145), rng.uniform(0.6, 1.0), seed * 7 + i)
    return cv


def _single(seed, kind):
    rng = np.random.default_rng(seed)
    cv = Canvas(1, 160, pad=60)
    if kind == "spruce":
        kit.conifer(cv, 80, 80, "spruce", rng.uniform(0.9, 1.1), seed)
    elif kind == "pair":
        kit.tree(cv, 60, 70, ["oak", "lime"][seed % 2], 0.95, seed)
        kit.tree(cv, 110, 105, ["birch", "maple"][seed % 2], 0.85, seed + 1)
    else:
        kit.tree(cv, 80, 80, kind, rng.uniform(0.95, 1.15), seed)
    return cv


def _under(seed, kind):
    rng = np.random.default_rng(seed)
    cv = Canvas(1, 40, pad=20)
    if kind == "bushes":
        for i in range(3):
            kit.bush(cv, rng.uniform(40, 120), rng.uniform(40, 120), rng.uniform(0.7, 1.1), seed + i, "e8e4dc" if i == 0 and seed % 2 else None)
    elif kind == "rocks":
        for i in range(3):
            r = rng.uniform(6, 14)
            cv.ellipsoid(rng.uniform(50, 110), rng.uniform(50, 110), r * 0.4, r, r * 0.8, r * 0.7,
                         lambda wx, wy, wz, nx, ny, nz: solid_res(C("9a948a") * (0.8 + 0.3 * nz[..., None]), wx.shape))
    elif kind == "stump":
        cv.cylinder(80, 80, 6, 0, 7, kit.trunk_fn(), lambda a, b: solid_res(C("c8a070"), a.shape))
        cv.box(90, 70, 0, 130, 77, 6, flat("6a4a30", 8), flat("5a3a22", 8), flat("7a5a38", 8))
    return cv


def gen(out):
    os.makedirs(out, exist_ok=True)
    np.seterr(all="ignore")
    meta = {}
    k = 0
    for mix, n in (("leaf", 8), ("mixed", 6), ("pine", 6)):
        for i in range(n):
            _save(_clump(100 + k, mix), "clump_%d" % k, out, meta)
            k += 1
    kinds = ["oak", "maple", "birch", "lime", "spruce", "pair", "oak", "pair"]
    for i, kd in enumerate(kinds):
        _save(_single(300 + i, kd), "tree_%d" % i, out, meta)
    for i, kd in enumerate(("bushes", "bushes", "rocks", "stump")):
        _save(_under(400 + i, kd), "under_%d" % i, out, meta)
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), separators=(",", ":"))
    return meta


if __name__ == "__main__":
    import sys
    gen(sys.argv[1])
