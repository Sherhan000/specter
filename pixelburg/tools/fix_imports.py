#!/usr/bin/env python3
"""Sets texture import options after Godot created the .import files.

Ground textures repeat and are seen from far away: they need mipmaps. World sprites get
mipmaps too so the city stays clean when zoomed out. Data maps must stay exact.
Run, then let Godot reimport (godot --headless --import).
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIPMAPS = ["assets/ground/*.png", "assets/buildings/*.png", "assets/nature/*.png", "assets/units/*.png",
           "assets/fx/*.png", "assets/props/*.png", "assets/sky/*.png", "assets/ui/*.png"]
EXACT = ["assets/world/*.png"]
# big sprite sets are stored as lossy WebP to keep the download small; layers whose colour
# channels carry data (room light groups) must stay lossless
LOSSY = ["assets/buildings/*.png", "assets/nature/*.png", "assets/sky/*.png", "assets/portraits/*.png"]
LOSSLESS = ["assets/buildings/*_rooms.png"]


def set_param(text, key, value):
    if re.search(r"^%s=.*$" % re.escape(key), text, re.M):
        return re.sub(r"^%s=.*$" % re.escape(key), "%s=%s" % (key, value), text, flags=re.M)
    return text


def main():
    changed = 0
    for pattern, mip in [(p, True) for p in MIPMAPS] + [(p, False) for p in EXACT]:
        for f in glob.glob(os.path.join(ROOT, pattern + ".import")):
            t = open(f).read()
            n = set_param(t, "mipmaps/generate", "true" if mip else "false")
            n = set_param(n, "process/fix_alpha_border", "true")
            if n != t:
                open(f, "w").write(n)
                changed += 1
    lossless = set()
    for pattern in LOSSLESS:
        lossless.update(glob.glob(os.path.join(ROOT, pattern + ".import")))
    for pattern in LOSSY:
        for f in glob.glob(os.path.join(ROOT, pattern + ".import")):
            t = open(f).read()
            n = set_param(t, "compress/mode", "0" if f in lossless else "1")
            n = set_param(n, "compress/lossy_quality", "0.86")
            if n != t:
                open(f, "w").write(n)
                changed += 1
    print("import files changed:", changed)
    return changed


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)
