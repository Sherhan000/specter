"""Cuts hand-made icon sheets (4 x 4 icons on a magenta #FF00FF background) into single icons.

    python3 tools/art/cut_icons.py sheet1.png sheet2.png sheet3.png sheet4.png
    python3 tools/art/cut_icons.py 5=sheet5.png      (only sheet 5)

Sheet k uses the k-th row of names in icon_sheet_names.json. Each icon is keyed out, trimmed,
centred on a transparent square and saved as assets/ui/icons/<name>.png (256 px); the game then
prefers it over the generated icon of the same name."""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("ICON_OUT", os.path.join(HERE, "..", "..", "assets", "ui", "icons"))
SIZE = 256


def key_magenta(rgb):
    """Alpha from the distance to magenta, and the magenta spill removed from the edges."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # magenta has high red and blue, low green
    mag = np.clip((np.minimum(r, b) - g) / 255.0, 0, 1)
    alpha = np.clip(1.0 - (mag - 0.25) / 0.45, 0, 1)
    out = rgb.copy()
    spill = np.minimum(r, b) - g
    fix = (spill > 0) & (alpha < 1)
    out[..., 0] = np.where(fix, np.minimum(r, g + (r - g) * alpha), r)
    out[..., 2] = np.where(fix, np.minimum(b, g + (b - g) * alpha), b)
    return out, alpha


def cut(sheet_path, names):
    img = np.asarray(Image.open(sheet_path).convert("RGB")).astype(float)
    h, w = img.shape[:2]
    rgb, alpha = key_magenta(img)
    for i, name in enumerate(names):
        r, c = divmod(i, 4)
        y0, y1 = int(h * r / 4), int(h * (r + 1) / 4)
        x0, x1 = int(w * c / 4), int(w * (c + 1) / 4)
        a = alpha[y0:y1, x0:x1]
        # keep the biggest connected shape group: drop stray specks
        lab, n = ndimage.label(a > 0.5)
        if n == 0:
            print("empty cell", name)
            continue
        sizes = ndimage.sum(np.ones_like(a), lab, range(1, n + 1))
        keep = np.isin(lab, [k + 1 for k, s in enumerate(sizes) if s > sizes.max() * 0.02])
        keep = ndimage.binary_dilation(keep, iterations=3)
        a = a * keep
        ys, xs = np.where(a > 0.05)
        cy0, cy1, cx0, cx1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        cell = np.dstack([rgb[y0:y1, x0:x1], a * 255])[cy0:cy1, cx0:cx1]
        icon = Image.fromarray(np.clip(cell, 0, 255).astype(np.uint8), "RGBA")
        side = max(icon.width, icon.height)
        square = Image.new("RGBA", (int(side * 1.08), int(side * 1.08)), (0, 0, 0, 0))
        square.paste(icon, ((square.width - icon.width) // 2, (square.height - icon.height) // 2))
        square.resize((SIZE, SIZE), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))
        print("icon", name)


def main(paths):
    rows = json.load(open(os.path.join(HERE, "icon_sheet_names.json")))
    os.makedirs(OUT, exist_ok=True)
    for k, p in enumerate(paths):
        # "5=sheet.png" cuts a sheet with the names of row 5; plain paths go in order
        if "=" in p and p.split("=", 1)[0].isdigit():
            n, p = p.split("=", 1)
            cut(p, rows[int(n) - 1])
        else:
            cut(p, rows[k])


if __name__ == "__main__":
    main(sys.argv[1:])
