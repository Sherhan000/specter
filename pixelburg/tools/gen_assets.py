#!/usr/bin/env python3
"""Generates Pixelburg's art into assets/.

Run from the project root:  python3 tools/gen_assets.py [buildings] [nature] [units] [ground] [sky] [only=id,id]
Without arguments everything is generated. Needs Pillow, numpy, scipy and pycairo.
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "art"))
ROOT = os.path.dirname(HERE)
A = os.path.join(ROOT, "assets")

MODULES = ["b_homes", "b_shops", "b_work", "b_civic", "b_towers"]


def d(*p):
    path = os.path.join(A, *p)
    os.makedirs(path, exist_ok=True)
    return path


def _builders():
    out = {}
    for m in MODULES:
        mod = __import__(m)
        for k, fn in mod.BUILDERS.items():
            out[k] = (m, k)
    return out


def _render_one(job):
    np.seterr(all="ignore")
    modname, bid, L, o, out = job
    import render
    mod = __import__(modname)
    if bid.startswith("scaffold"):
        cv = mod.scaffold(L)
        name = "scaffold_%d" % L
    else:
        cv = mod.BUILDERS[bid](L, o)
        name = "%s_%d_%d" % (bid, L, o)
    meta = render.save_sprite(name, cv, out)
    if hasattr(cv, "bays"):
        meta["bays"] = cv.bays
    return name, meta


def gen_buildings(only=None):
    out = d("buildings")
    jobs = []
    for bid, (m, k) in _builders().items():
        if only and bid not in only:
            continue
        for L in (1, 2, 3):
            for o in range(4):
                jobs.append((m, k, L, o, out))
    if not only:
        for n in (1, 2, 3):
            jobs.append(("b_civic", "scaffold", n, 0, out))
    meta_path = os.path.join(out, "meta.json")
    meta = json.load(open(meta_path)) if (only and os.path.exists(meta_path)) else {}
    with Pool(4) as p:
        for name, m in p.imap_unordered(_render_one, jobs, chunksize=2):
            meta[name] = m
    json.dump(meta, open(meta_path, "w"), separators=(",", ":"))
    print("buildings:", len(jobs))


def gen_ground():
    import ground
    import world
    ground.gen_textures(d("ground"))
    world.gen_world(d("world"))


if __name__ == "__main__":
    t = time.time()
    args = [a for a in sys.argv[1:] if not a.startswith("only=")]
    only = None
    for a in sys.argv[1:]:
        if a.startswith("only="):
            only = a[5:].split(",")
    every = not args
    if every or "ground" in args:
        gen_ground()
        print("ground", round(time.time() - t, 1))
    if every or "buildings" in args:
        gen_buildings(only)
        print("buildings", round(time.time() - t, 1))
    if every or "nature" in args:
        import nature4
        nature4.gen(d("nature"))
        print("nature", round(time.time() - t, 1))
    if every or "units" in args:
        import units4
        units4.gen(d("units"))
        print("units", round(time.time() - t, 1))
    if every or "ui" in args:
        import ui4
        ui4.gen(d("ui"))
        print("ui", round(time.time() - t, 1))
    if every or "sky" in args:
        import fx4
        import sky
        sky.gen(d("sky"))
        fx4.gen(A)
        print("sky", round(time.time() - t, 1))
    print("done", round(time.time() - t, 1))
