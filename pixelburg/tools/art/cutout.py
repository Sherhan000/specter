"""Cut character portraits out of green-screen pictures and expression sheets.

Usage: python3 tools/art/cutout.py <source dir> <assets/portraits dir>
Sources: <who>_<expr>.jpg|png (one pose) and sheet_<who>.jpg|png (several poses, see SHEETS).
Every result is a transparent PNG, 640x640, the figure centred and standing on the bottom edge.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = 640
# poses on each sheet, row by row, left to right
SHEETS = {
    "alina": (1, ["worried", "angry", "smug", "think"]),
    "boris": (2, ["smile", "talk", "happy", "surprised", "worried", "angry", "smug", "think"]),
    "viktor": (2, ["smile", "talk", "happy", "surprised", "worried", "angry", "smug", "think"]),
    "marina": (2, ["smile", "talk", "happy", "surprised", "worried", "angry", "smug", "think"]),
    "oleg": (2, ["smile", "talk", "happy", "surprised", "worried", "angry", "smug", "think"]),
    "zina": (2, ["smile", "talk", "happy", "surprised", "worried", "angry", "smug", "think"]),
}


def key(img):
    """Green screen to alpha, with despill so no green fringe remains."""
    a = np.asarray(img.convert("RGB")).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    d = g - np.maximum(r, b)
    alpha = np.clip((140.0 - d) / 100.0, 0, 1)
    alpha = ndimage.median_filter(alpha, 3)
    spill = g > np.maximum(r, b)
    a[..., 1] = np.where(spill, np.maximum(r, b) + (g - np.maximum(r, b)) * 0.15, g)
    rgba = np.dstack([np.clip(a, 0, 255), alpha * 255]).astype(np.uint8)
    return rgba


def place(rgba, out_path):
    """Crop to the figure and put it on a square canvas, standing on the bottom edge."""
    m = rgba[..., 3] > 20
    ys, xs = np.where(m)
    if len(xs) == 0:
        return
    crop = rgba[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1]
    img = Image.fromarray(crop)
    k = min(OUT * 0.96 / img.width, OUT * 0.98 / img.height)
    img = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS)
    canvas = Image.new("RGBA", (OUT, OUT), (0, 0, 0, 0))
    canvas.alpha_composite(img, ((OUT - img.width) // 2, OUT - img.height))
    canvas.save(out_path)


def split_sheet(rgba, rows, cols):
    """Group connected figures by the cell their centre falls into."""
    h, w = rgba.shape[:2]
    mask = rgba[..., 3] > 20
    labels, n = ndimage.label(mask)
    cells = [np.zeros_like(rgba) for _ in range(rows * cols)]
    sizes = ndimage.sum(mask, labels, range(1, n + 1))
    centres = ndimage.center_of_mass(mask, labels, range(1, n + 1))
    merged = False
    for i in range(n):
        if sizes[i] < 40:
            continue
        cy, cx = centres[i]
        sl = labels == i + 1
        span = np.where(sl.any(axis=0))[0]
        if span.max() - span.min() > w / cols * 1.35:
            merged = True
        idx = min(rows - 1, int(cy / (h / rows))) * cols + min(cols - 1, int(cx / (w / cols)))
        cells[idx][sl] = rgba[sl]
    if merged:
        # figures touch each other: fall back to plain equal cells
        cells = []
        for r in range(rows):
            for c in range(cols):
                cell = np.zeros_like(rgba)
                y0, y1 = int(r * h / rows), int((r + 1) * h / rows)
                x0, x1 = int(c * w / cols), int((c + 1) * w / cols)
                cell[y0:y1, x0:x1] = rgba[y0:y1, x0:x1]
                cells.append(cell)
    return cells


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    for f in sorted(os.listdir(src)):
        name, ext = os.path.splitext(f)
        if ext.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        rgba = key(Image.open(os.path.join(src, f)))
        if name.startswith("sheet_"):
            who = name[6:]
            rows, exprs = SHEETS[who]
            for expr, cell in zip(exprs, split_sheet(rgba, rows, len(exprs) // rows)):
                place(cell, os.path.join(dst, "%s_%s.png" % (who, expr)))
                print(who, expr)
        else:
            place(rgba, os.path.join(dst, name + ".png"))
            print(name)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
