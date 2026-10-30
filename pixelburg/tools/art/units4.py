"""Vehicles (16 headings), people, animals and street props at real scale.

Everything is drawn at 2-3x and scaled down for clean small sprites.
Vehicles: per kind one atlas, 16 columns (heading k * 22.5 deg from +x towards +y) and rows
base / paint / lights / siren A / siren B. The paint row is white-shaded and tinted in game.
"""
import json
import math
import os

import numpy as np
from PIL import Image

from raster import Canvas, C, U, flat, solid_res, glow_res, nores, hash2

SS = 2  # supersampling for vehicles

# kind: length, width, height, (cabin u0, u1 as fraction of length from the back), beltline, style
CARS = {
    "sedan": dict(L=46, W=18, H=14.5, cab=(0.3, 0.72), belt=9.5, hood=9.5, trunk=10.0),
    "hatch": dict(L=40, W=17.5, H=15, cab=(0.12, 0.7), belt=9.5, hood=9.5, trunk=13.0),
    "suv": dict(L=48, W=19.5, H=18, cab=(0.1, 0.72), belt=11.5, hood=12.0, trunk=16.0),
    "pickup": dict(L=54, W=20, H=18, cab=(0.45, 0.75), belt=11.5, hood=12.0, trunk=11.0, bed=True),
    "van": dict(L=52, W=20, H=21, cab=(0.05, 0.85), belt=12.0, hood=13.0, trunk=21.0, van=True),
    "taxi": dict(L=46, W=18, H=14.5, cab=(0.3, 0.72), belt=9.5, hood=9.5, trunk=10.0, paint="f2c230", roofsign=True),
    "sports": dict(L=44, W=19, H=11.5, cab=(0.32, 0.66), belt=8.0, hood=7.5, trunk=8.5),
    "police": dict(L=46, W=18, H=14.5, cab=(0.3, 0.72), belt=9.5, hood=9.5, trunk=10.0, paint="f4f6f8", bar=True, stripe="2a4a9a"),
    "bus": dict(L=110, W=25, H=31, cab=(0.0, 1.0), belt=12.0, hood=31, trunk=31, bus=True, paint="e8eef2", stripe="2a7ac8"),
    "truck": dict(L=80, W=24, H=32, cab=(0.75, 0.97), belt=16, hood=20, trunk=32, truck=True, paint="e8e8ea"),
    "ambulance": dict(L=56, W=21, H=25, cab=(0.6, 0.86), belt=12, hood=13, trunk=25, truck=True, paint="f4f6f8", bar=True, stripe="d8342a"),
    "fire": dict(L=80, W=24, H=28, cab=(0.75, 0.97), belt=14, hood=18, trunk=26, truck=True, paint="c8282a", bar=True, ladder=True),
    "garbage": dict(L=72, W=23, H=30, cab=(0.78, 0.97), belt=14, hood=18, trunk=30, truck=True, paint="3a8a4a"),
    "delivery": dict(L=60, W=21, H=27, cab=(0.7, 0.92), belt=12, hood=14, trunk=27, truck=True, paint="f4f2ee", stripe="e8a830"),
}
SIREN = {"police": ("e8342a", "3a6ae8"), "ambulance": ("e8342a", "3a6ae8"), "fire": ("e8342a", "f8b030")}


def _car_fields(spec, theta, s):
    """Height field of a car heading `theta`, scaled by s. Returns (x0, y0, H, B, local fn)."""
    L, W = spec["L"] * s, spec["W"] * s
    R = int(math.hypot(L, W) / 2 + 3)
    n = 2 * R
    ys, xs = np.mgrid[0:n, 0:n] + 0.5
    dx, dy = xs - R, ys - R
    c, si = math.cos(theta), math.sin(theta)
    u = dx * c + dy * si          # along the car, + forward
    v = -dx * si + dy * c         # across
    un = (u + L / 2) / L          # 0 rear .. 1 front
    inside = (np.abs(u) < L / 2) & (np.abs(v) < W / 2)
    # round the corners a little
    cr = 2.5 * s
    cu = np.abs(u) - (L / 2 - cr)
    cvv = np.abs(v) - (W / 2 - cr)
    inside &= ~((cu > 0) & (cvv > 0) & (cu * cu + cvv * cvv > cr * cr))
    H = np.full(u.shape, -np.inf)
    hood, trunk, top = spec["hood"] * s, spec["trunk"] * s, spec["H"] * s
    c0, c1 = spec["cab"]
    body = np.where(un > c1, hood, np.where(un < c0, trunk, top))
    if not spec.get("bus") and not spec.get("van") and not spec.get("truck"):
        # sloped screens
        ramp_f = np.clip((c1 + 0.1 - un) / 0.1, 0, 1)
        ramp_b = np.clip((un - (c0 - 0.07)) / 0.07, 0, 1)
        inner = (un >= c0 - 0.07) & (un <= c1 + 0.1)
        body = np.where(inner, np.minimum(hood + (top - hood) * ramp_f, trunk + (top - trunk) * ramp_b), body)
        body = np.where((un > c0) & (un < c1), top, body)
    if spec.get("bed"):
        body = np.where(un < c0 - 0.02, np.where((np.abs(v) > W / 2 - 1.5 * s) | (un < 0.03), trunk, 7 * s), body)
    if spec.get("truck"):
        body = np.where(un > c1, hood, np.where(un >= c0, top * 0.82, trunk))
        body = np.where((un > c0 - 0.03) & (un < c0), 0.0, body)  # gap between cab and box
    # roof rounded edges
    edge = np.clip((W / 2 - np.abs(v)) / (2.0 * s), 0, 1)
    body = body - (1 - edge) * 1.5 * s
    H = np.where(inside, body, -np.inf)
    B = np.where(inside, 2.6 * s, np.inf)
    # wheels: dark blocks below the body at the four corners
    wb = L / 2 - (0.17 * L if not spec.get("bus") else 0.14 * L)
    wr = (3.3 if spec["L"] < 60 else 4.8) * s
    wheel = np.zeros(u.shape, bool)
    for wu in (wb, -wb):
        wheel |= (np.abs(u - wu) < wr) & (np.abs(v) > W / 2 - 3.2 * s) & (np.abs(v) < W / 2 + 0.2 * s)
    H = np.where(wheel, np.maximum(H, 2 * wr), H)
    B = np.where(wheel, 0.0, B)

    def local(wx, wy):
        ddx, ddy = wx - (R + X0[0]), wy - (R + X0[1])
        return ddx * c + ddy * si, -ddx * si + ddy * c
    X0 = [0, 0]
    return R, H, B, local, X0, wheel, u, v


def _car_color(spec, theta, s, paint, local, wheel_m, mode):
    """Material function. mode: 'base' (paint shows as given colour) or 'white'."""
    L, W = spec["L"] * s, spec["W"] * s
    c0, c1 = spec["cab"]
    belt, top = spec["belt"] * s, spec["H"] * s
    pc = C(paint)

    def fn(wx, wy, wz, nx, ny, nz):
        shape = wx.shape
        u, v = local(wx, wy)
        un = (u + L / 2) / L
        rgb = np.broadcast_to(pc, shape + (3,)).copy()
        ns = np.zeros(shape, bool)
        em = np.zeros(shape + (4,))
        tag = np.ones(shape, bool)      # paint pixels
        # windows on the cabin (sides and screens)
        if spec.get("bus"):
            win = (wz > belt) & (wz < top - 3 * s) & ((np.floor(u / (9 * s)) % 1) == 0) & (((u / s) % 12) > 1.2)
            win |= (un > 0.97) & (wz > belt * 0.8) & (wz < top - 2 * s)
        elif spec.get("truck"):
            win = (un > c0) & (wz > belt) & (wz < spec["hood"] * s + (top * 0.82 - spec["hood"] * s) * 0.85) & (un > c1 - 0.12) & (un < c1 + 0.02)
            win |= (un > c0 + 0.02) & (wz > belt) & (wz < top * 0.78) & (np.abs(v) > W / 2 - 1.5 * s) & (un > c0 + 0.03) & (un < c1)
        else:
            win = (un > c0 - 0.06) & (un < c1 + 0.09) & (wz > belt) & (wz < top - 1.2 * s)
            if spec.get("van"):
                win &= (un > 0.62) | (np.abs(v) < W / 2 - 1.0 * s)
        glass = C("26303c") + (np.clip(nz, 0, 1) * 38)[..., None] + (((u - wz) % (11 * s) < 2 * s) * 40)[..., None]
        rgb[win] = glass[win]
        tag &= ~win
        ns |= win
        # lights
        front = un > 0.985
        back = un < 0.015
        lamp_band = (wz > belt * 0.55) & (wz < belt * 0.85) & (np.abs(v) > W / 2 - 5 * s)
        hl = front & lamp_band
        tl = back & lamp_band
        rgb[hl] = C("f8f4e0")
        rgb[tl] = C("c8282a")
        em[hl] = (255, 248, 220, 255)
        em[tl] = (255, 60, 50, 230)
        tag &= ~(hl | tl)
        ns |= hl | tl
        # bumpers and sills
        bump = ((un > 0.975) | (un < 0.025)) & (wz < belt * 0.5)
        sill = (wz < 4.0 * s)
        rgb[bump | sill] = C("3a3c42")
        tag &= ~(bump | sill)
        # wheels
        tire = wz < 3.6 * s
        tire &= np.abs(v) > W / 2 - 3.4 * s
        rgb[tire] = C("1e1e22")
        hub = tire & (wz > 1.4 * s) & (wz < 2.6 * s)
        rgb[hub] = C("a8acb0")
        tag &= ~tire
        if spec.get("stripe"):
            st = (wz > belt * 0.7) & (wz < belt * 0.95) & ~win
            rgb[st] = C(spec["stripe"])
            tag &= ~st
        if spec.get("truck") and not spec.get("ladder"):
            boxm = un < spec["cab"][0] - 0.03
            if spec.get("paint") is None:
                pass
        if mode == "white":
            rgb[tag] = np.array([238, 238, 238.0])
        return rgb, ns, em
    return fn


def render_car(kind, k, s=SS):
    """One render: free paint is drawn pure magenta and split off afterwards."""
    spec = CARS[kind]
    theta = k * math.pi / 8
    R, H, B, local, X0, wheel, uu, vv = _car_fields(spec, theta, s)
    cv = Canvas(1, (spec["H"] + 16) * s, pad=10)
    cv.no_ao = True
    cx = cy = cv.size / 2
    X0[0], X0[1] = cx - R, cy - R
    paint = spec.get("paint", "ff00ff")
    fn = _car_color(spec, theta, s, paint, local, wheel, "base")
    cv.heightfield(cx - R, cy - R, H, fn, zmin=-1, step=1.0, bottom=np.where(np.isfinite(B), B, np.inf))
    return cv, spec


def _extras(cv, spec, theta, s, kind):
    """Roof light bar / taxi sign positions in the car frame: (world xy, z, half size, tag)."""
    c, si = math.cos(theta), math.sin(theta)
    cx = cy = cv.size / 2
    top = spec["H"] * s
    L = spec["L"] * s

    def at(u, v):
        return cx + u * c - v * si, cy + u * si + v * c
    items = []
    if spec.get("bar"):
        if spec.get("truck"):
            u0 = L * (spec["cab"][0] + 0.1) - L / 2
            z0 = top * 0.82
        else:
            u0 = L * (spec["cab"][0] + spec["cab"][1]) / 2 - L / 2
            z0 = top
        for k, vv in enumerate((-4.5 * s, -1.5 * s, 1.5 * s, 4.5 * s)):
            items.append((at(u0, vv), z0, 1.6 * s, "L" if k < 2 else "R"))
    if spec.get("roofsign"):
        items.append((at(L * 0.52 - L / 2, 0), top, 2.2 * s, "T"))
    return items


def gen_cars(out, kinds=None):
    meta = {}
    for kind, spec in CARS.items():
        if kinds and kind not in kinds:
            continue
        imgs = []
        cvs = []
        for k in range(16):
            cv, _ = render_car(kind, k)
            theta = k * math.pi / 8
            for (pos, z, r, tagc) in _extras(cv, spec, theta, SS, kind):
                col = {"L": "c83030", "R": "3050c8", "T": "f8e050"}[tagc]
                cv.box(pos[0] - r, pos[1] - r, z, pos[0] + r, pos[1] + r, z + 2.2 * SS, flat(col), flat(col), flat(col))
            A = np.array(cv.image(outline=False)).astype(int)
            alpha = A[..., 3] > 0
            base = A.copy()
            pnt = np.zeros_like(A)
            if "paint" not in spec:
                r_, g_, b_ = A[..., 0], A[..., 1], A[..., 2]
                paint = alpha & (g_ < 40) & (r_ > 40) & (np.abs(r_ - b_) < 30)
                lum = np.clip((r_ + b_) / 2 / 255 * 238, 0, 255)
                pnt[paint, 0] = lum[paint]
                pnt[paint, 1] = lum[paint]
                pnt[paint, 2] = lum[paint]
                pnt[paint, 3] = 255
                base[paint, 3] = 0
            pad = np.pad(alpha, 1)
            ring = (~alpha) & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
            base[ring] = (24, 22, 30, 200)
            glow = np.array(cv.emission_image()).astype(int)
            sir = [np.zeros_like(A), np.zeros_like(A)]
            if kind in SIREN:
                yy, xx = np.mgrid[0:alpha.shape[0], 0:alpha.shape[1]]
                for st in (0, 1):
                    ca, cb = SIREN[kind]
                    for (pos, z, r, tagc) in _extras(cv, spec, theta, SS, kind):
                        if (tagc == "L") != (st == 0):
                            continue
                        sx, sy = cv.screen(pos[0], pos[1], z + 1.1 * SS)
                        blob = (xx - sx) ** 2 + (yy - sy) ** 2 < (r * 2.4) ** 2
                        sir[st][blob] = np.append(C(ca if tagc == "L" else cb), 255)
            imgs.append([base, pnt, glow, sir[0], sir[1]])
            cvs.append(cv)
        allm = np.zeros(imgs[0][0].shape[:2], bool)
        for layers in imgs:
            for L_ in layers:
                allm |= L_[..., 3] > 0
        ys, xs = np.where(allm)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        cw, ch = (x1 - x0 + SS - 1) // SS, (y1 - y0 + SS - 1) // SS
        atlas = Image.new("RGBA", (cw * 16, ch * 5), (0, 0, 0, 0))
        for k, layers in enumerate(imgs):
            for r, L_ in enumerate(layers):
                im = Image.fromarray(np.clip(L_, 0, 255).astype(np.uint8)[y0:y1, x0:x1], "RGBA")
                chans = [c_.resize((cw, ch), Image.LANCZOS) for c_ in im.split()]
                atlas.alpha_composite(Image.merge("RGBA", chans), (k * cw, r * ch))
        atlas.save(os.path.join(out, "car_%s.png" % kind))
        sx, sy = cvs[0].screen(cvs[0].size / 2, cvs[0].size / 2, 0)
        meta[kind] = {"cell": [int(cw), int(ch)], "anchor": [round(float(sx - x0) / SS, 1), round(float(sy - y0) / SS, 1)],
                      "len": spec["L"], "fixed": "paint" in spec, "siren": kind in SIREN}
    return meta


# ====================================================================== people
PEOPLE = {
    # kind: (shirt, pants, hair, skin options, extras)
    "man": [("3a6aa8", "3a3a48", "3a2a20"), ("8a3a3a", "4a4a5a", "1e1a18"), ("4a8a5a", "2a3a5a", "8a6a40")],
    "woman": [("c84a6a", "2a3a5a", "6a3a20"), ("e8b040", "3a3a48", "2a1e18"), ("6a5ab8", "e8e4dc", "c8a050")],
    "grandpa": [("8a7a6a", "4a4a50", "d8d8d8")],
    "grandma": [("8a5a7a", "5a4a5a", "e8e8e8")],
    "boy": [("e8342a", "3a5a9a", "4a3020")],
    "girl": [("f08ab0", "4a6ac8", "c88a40")],
    "teen": [("2a2a30", "3a5a8a", "1e1a18")],
    "student": [("4aa8a8", "3a3a48", "6a4a30")],
    "business": [("2a2e3a", "2a2e3a", "2a2018")],
    "businesswoman": [("3a3a48", "3a3a48", "7a4a28")],
    "police": [("2a3a6a", "1e2438", "2a2018")],
    "doctor": [("f4f6f8", "6a8aa8", "4a3020")],
    "firefighter": [("c83a2a", "3a3a40", "2a2018")],
    "chef": [("f4f4f4", "3a3a40", "4a3020")],
    "farmer": [("5a7aa8", "6a5a3a", "8a6a40")],
    "builder": [("f0a030", "3a4a6a", "4a3020")],
    "postman": [("3a5aa8", "2a2e3a", "3a2a20")],
    "jogger": [("e8e8ea", "2a2a30", "6a4a30")],
}
SKINS = ["f0c8a8", "d8a880", "b07a58", "8a5a40"]
CELL = (24, 30)
PSS = 3


def _person(cv, kind, pal, frame, back, skin):
    """Draw one figure at the canvas centre facing +y (front) or -x (back)."""
    shirt, pants, hair = pal
    s = PSS
    kid = kind in ("boy", "girl")
    k = 0.72 if kid else 1.0
    old = kind in ("grandpa", "grandma")
    cx = cy = cv.size / 2
    walk = frame < 4
    ph = frame * math.pi / 2
    swing = math.sin(ph) * 2.2 * s * k if walk else 0
    # facing: front = +y (towards the viewer, lower left), back = -x
    fx, fy = (0, 1) if not back else (-1, 0)
    sx_, sy_ = -fy, fx   # sideways
    leg_h = 8.4 * s * k
    body_w = 3.6 * s * k
    sk = C(skin)
    def part(u, v, z0, z1, w, d, col):
        # u: sideways offset, v: forward offset
        x = cx + sx_ * u + fx * v
        y = cy + sy_ * u + fy * v
        hw = (abs(sx_) * w + abs(fx) * d) / 2
        hd = (abs(sy_) * w + abs(fy) * d) / 2
        c = flat(col, 3)
        cv.box(x - hw, y - hd, z0, x + hw, y + hd, z1, c, c, flat(C(col) * 1.08 if not isinstance(col, str) else C(col) * 1.08, 2))
    skirt = kind in ("woman", "girl", "grandma", "businesswoman")
    for side in (-1, 1):
        off = swing * side
        part(side * 0.9 * s * k, off, 0, 1.2 * s, 1.5 * s * k, 2.4 * s * k, "2a2420")       # shoes
        part(side * 0.9 * s * k, off * 0.8, 1.0 * s, leg_h, 1.5 * s * k, 1.6 * s * k, pants if not skirt else skin)
    if skirt:
        part(0, 0, leg_h * 0.55, leg_h + 0.5 * s, body_w * 1.1, 2.6 * s * k, pants)
    torso_h = 6.0 * s * k
    z_t = leg_h
    coat = kind in ("doctor", "chef")
    part(0, 0, z_t, z_t + torso_h, body_w, 2.2 * s * k, shirt)
    if kind in ("builder", "firefighter"):
        part(0, 0.15 * s, z_t + 1.5 * s, z_t + torso_h - 0.5 * s, body_w + 0.2 * s, 2.3 * s * k, "f8e040" if kind == "builder" else "e8d040")
    if kind in ("student", "postman"):
        part(0, -1.6 * s * k, z_t + 1.4 * s, z_t + torso_h - 0.6 * s, body_w * 0.8, 1.4 * s, "8a5a2a" if kind == "postman" else "c84a3a")
    if kind == "business":
        part(0, 0.2 * s, z_t + 2.0 * s, z_t + torso_h, 0.6 * s, 2.3 * s * k, "c83a3a")
    # arms
    for side in (-1, 1):
        a_off = -swing * side * 0.8
        if frame >= 10 and side == 1:
            # waving arm up
            part(side * (body_w / 2 + 0.6 * s), 0, z_t + torso_h - 1 * s, z_t + torso_h + 4.5 * s + (frame - 10) * 0.8 * s, 1.1 * s, 1.1 * s, skin)
        else:
            part(side * (body_w / 2 + 0.6 * s), a_off, z_t + 1.4 * s, z_t + torso_h - 0.3 * s, 1.1 * s * k, 1.3 * s * k, shirt)
            part(side * (body_w / 2 + 0.6 * s), a_off, z_t + 0.6 * s, z_t + 1.5 * s, 1.1 * s * k, 1.2 * s * k, skin)
    # head
    hz = z_t + torso_h + 2.0 * s * k
    hr = 1.6 * s * (k ** 0.6)
    cv.ellipsoid(cx, cy, hz, hr, hr, hr * 1.1, lambda *a: (np.broadcast_to(sk, a[0].shape + (3,)).copy(), nores(a[0].shape), None))
    hcol = C(hair)
    # hair: on top and at the back
    def hair_fn(wx, wy, wz, nx, ny, nz):
        rgb = np.broadcast_to(hcol, wx.shape + (3,)).copy()
        return rgb, nores(wx.shape), None
    long_hair = kind in ("woman", "girl", "businesswoman")
    cv.ellipsoid(cx - fx * 0.35 * s, cy - fy * 0.35 * s, hz + 0.45 * s, hr * 1.05, hr * 1.05, hr * 0.9, hair_fn, cut_z=hz + (0.1 if not back else -0.8) * s)
    if long_hair:
        cv.ellipsoid(cx - fx * 0.7 * s, cy - fy * 0.7 * s, hz - 1.2 * s, hr * 0.95, hr * 0.95, hr * 1.2, hair_fn)
    hat = {"police": "1e2438", "chef": "f8f8f8", "builder": "f8d030", "farmer": "c8a060", "firefighter": "e8c030", "postman": "3a5aa8"}.get(kind)
    if hat:
        cv.cylinder(cx, cy, hr * (1.2 if kind != "chef" else 0.9), hz + hr * 0.6, hz + hr * (1.3 if kind != "chef" else 2.4),
                    lambda a, v, nx, ny: solid_res(C(hat), a.shape), lambda a, b: solid_res(C(hat) * 1.1, a.shape))
    if old and kind == "grandpa":
        part(1.8 * s, 1.5 * s, 0, z_t + 2 * s, 0.6 * s, 0.6 * s, "6a4a30")  # walking stick


def gen_people(out):
    rows = []
    kinds = {}
    for kind, pals in PEOPLE.items():
        for p_i, pal in enumerate(pals):
            for sk_i in ((0, 2) if kind in ("man", "woman") else (p_i % 4,)):
                kinds.setdefault(kind, []).append(len(rows))
                rows.append((kind, pal, SKINS[sk_i]))
    W, H = CELL
    sheet = Image.new("RGBA", (W * 12, H * len(rows)), (0, 0, 0, 0))
    for r, (kind, pal, skin) in enumerate(rows):
        for col in range(12):
            back = col in (4, 5, 6, 7, 9)
            frame = col % 4 if col < 8 else (8 if col in (8, 9) else col)
            cv = Canvas(1, 30 * PSS, pad=4)
            cv.size = 40 * PSS
            cv.no_ao = True
            cv2 = Canvas(1, 30 * PSS, pad=4)
            cv2.no_ao = True
            _person(cv2, kind, pal, frame, back, skin)
            img = cv2.image(outline=False)
            # outline after scaling looks cleaner: scale first, then add a soft dark edge
            sx, sy = cv2.screen(cv2.size / 2, cv2.size / 2, 0)
            box = (int(sx - W * PSS / 2), int(sy - (H - 3) * PSS), int(sx + W * PSS / 2), int(sy + 3 * PSS))
            crop = img.crop(box).resize((W, H), Image.LANCZOS)
            a = np.array(crop)
            al = a[..., 3] > 60
            pad = np.pad(al, 1)
            ring = (~al) & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
            a[ring] = (24, 20, 28, 150)
            a[al, 3] = 255
            sheet.alpha_composite(Image.fromarray(a), (col * W, r * H))
    sheet.save(os.path.join(out, "people.png"))
    return {"cell": [W, H], "anchor": [W / 2, H - 3], "kinds": kinds}


# ====================================================================== animals
ANIMALS = {
    "deer": dict(L=16, H=13, body="a8704a", belly="e8d8c0", legs=1.0, antlers=True),
    "rabbit": dict(L=4.5, H=3.5, body="b8a898", belly="e8e0d8", legs=0.3, ears=True),
    "fox": dict(L=10, H=6, body="d8682a", belly="f4ece0", legs=0.6, tail=True),
    "boar": dict(L=13, H=8, body="5a4a40", belly="6a5a50", legs=0.6),
    "wolf": dict(L=13, H=8.5, body="8a8a90", belly="d8d8dc", legs=0.75, tail=True),
    "bear": dict(L=18, H=12, body="6a4a32", belly="7a5a40", legs=0.6),
    "dog": dict(L=8, H=6, body="c89a5a", belly="f0e0c8", legs=0.65, tail=True),
}


def _animal(cv, spec, frame, back):
    s = PSS
    cx = cy = cv.size / 2
    fx, fy = (0, 1) if not back else (-1, 0)
    L, Hh = spec["L"] * s, spec["H"] * s
    leg = Hh * 0.45 * spec["legs"] / max(spec["legs"], 0.5)
    leg = Hh * (0.5 if spec["legs"] > 0.5 else 0.3)
    body_z = leg + Hh * 0.22
    col = C(spec["body"])
    bf = lambda *a: (np.broadcast_to(col, a[0].shape + (3,)).copy() * (0.85 + 0.25 * np.clip(a[5], 0, 1))[..., None], nores(a[0].shape), None)
    ph = frame * math.pi / 2
    for side in (-1, 1):
        for end in (-1, 1):
            off = math.sin(ph + (0 if end * side > 0 else math.pi)) * L * 0.08 if frame < 4 else 0
            u = end * L * 0.3 + off
            v = side * L * 0.1
            x = cx + fx * u + (-fy) * v
            y = cy + fy * u + fx * v
            r = max(0.5 * s, L * 0.035)
            cv.box(x - r, y - r, 0, x + r, y + r, leg + Hh * 0.1, flat(spec["body"]), flat(spec["body"]), flat(spec["body"]))
    cv.ellipsoid(cx, cy, body_z, abs(fx) * L * 0.42 + abs(fy) * L * 0.18 + 0.01, abs(fy) * L * 0.42 + abs(fx) * L * 0.18 + 0.01, Hh * 0.24, bf)
    hx, hy = cx + fx * L * 0.45, cy + fy * L * 0.45
    hz = body_z + Hh * 0.28
    cv.ellipsoid(hx, hy, hz, L * 0.13, L * 0.13, L * 0.12, bf)
    if spec.get("antlers"):
        for side in (-1, 1):
            ax, ay = hx + (-fy) * side * L * 0.06, hy + fx * side * L * 0.06
            cv.box(ax - 0.4 * s, ay - 0.4 * s, hz, ax + 0.4 * s, ay + 0.4 * s, hz + Hh * 0.4, flat("e8d8b0"), flat("e8d8b0"), flat("e8d8b0"))
    if spec.get("ears"):
        for side in (-1, 1):
            ax, ay = hx + (-fy) * side * L * 0.05, hy + fx * side * L * 0.05
            cv.box(ax - 0.3 * s, ay - 0.3 * s, hz, ax + 0.3 * s, ay + 0.3 * s, hz + Hh * 0.6, flat(spec["body"]), flat(spec["body"]), flat(spec["body"]))
    if spec.get("tail"):
        tx, ty = cx - fx * L * 0.5, cy - fy * L * 0.5
        cv.ellipsoid(tx, ty, body_z + Hh * 0.05, L * 0.08, L * 0.08, L * 0.06, bf)


def gen_animals(out):
    meta = {}
    W, H = 40, 30
    for name, spec in ANIMALS.items():
        sheet = Image.new("RGBA", (W * 10, H), (0, 0, 0, 0))
        for col in range(10):
            back = col >= 5
            frame = col % 5
            cv = Canvas(1, 30 * PSS, pad=4)
            cv.no_ao = True
            _animal(cv, spec, frame if frame < 4 else 8, back)
            img = cv.image(outline=False)
            sx, sy = cv.screen(cv.size / 2, cv.size / 2, 0)
            box = (int(sx - W * PSS / 2), int(sy - (H - 6) * PSS), int(sx + W * PSS / 2), int(sy + 6 * PSS))
            crop = np.array(img.crop(box).resize((W, H), Image.LANCZOS))
            al = crop[..., 3] > 60
            pad = np.pad(al, 1)
            ring = (~al) & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
            crop[ring] = (24, 20, 28, 140)
            crop[al, 3] = 255
            sheet.alpha_composite(Image.fromarray(crop), (col * W, 0))
        sheet.save(os.path.join(out, "animal_%s.png" % name))
        meta[name] = {"cell": [W, H], "anchor": [W / 2, H - 6]}
    return meta


# ====================================================================== street props
def _prop(name, fn, out, meta, n=1, zmax=90):
    import render
    cv = Canvas(n, zmax, pad=30)
    fn(cv)
    m = render.save_sprite(name, cv, out)
    meta[name] = m


def gen_props(out):
    import kit
    meta = {}
    c = U / 2
    _prop("lamp_classic", lambda cv: kit.lamp_post(cv, c, c, 45, "classic"), out, meta)
    _prop("lamp_modern", lambda cv: kit.lamp_post(cv, c, c, 55, "modern"), out, meta)
    _prop("lamp_lantern", lambda cv: kit.lamp_post(cv, c, c, 50, "lantern"), out, meta)

    def tl(cv, axis):
        pole = flat("3a3c42")
        cv.box(c - 1.2, c - 1.2, 0, c + 1.2, c + 1.2, 34, pole, pole, pole)
        hous = flat("2a2c30")
        if axis == "x":
            cv.box(c - 4, c - 2.5, 26, c + 4, c + 2.5, 44, hous, hous, hous)
        else:
            cv.box(c - 2.5, c - 4, 26, c + 2.5, c + 4, 44, hous, hous, hous)
        cv.mark("red", c, c, 40.5)
        cv.mark("yellow", c, c, 35)
        cv.mark("green", c, c, 29.5)
    _prop("tlight_x", lambda cv: tl(cv, "x"), out, meta)
    _prop("tlight_y", lambda cv: tl(cv, "y"), out, meta)

    def sign(cv):
        p = flat("6a4a30")
        for dx in (-12, 12):
            cv.box(c + dx - 1, c - 1, 0, c + dx + 1, c + 1, 26, p, p, p)
        board = lambda u, v, L, H: (np.where(((v > 3) & (v < H - 3) & (u > 3) & (u < L - 3))[..., None], C("f4f0e4"), C("c8342a")) *
                                    np.ones(u.shape + (3,)), nores(u.shape), None)
        cv.box(c - 16, c - 1, 14, c + 16, c + 1, 34, board, board, flat("c8342a"))
    _prop("sale_sign", sign, out, meta)

    def stop(cv):
        p = flat("3a3c42")
        cv.box(c - 20, c - 6, 0, c - 19, c - 5, 26, p, p, p)
        cv.box(c + 19, c - 6, 0, c + 20, c - 5, 26, p, p, p)
        glass = lambda u, v, L, H: (np.broadcast_to(C("a8c8d8"), u.shape + (3,)).copy(), np.ones(u.shape, bool), None)
        cv.face_y(c - 6, c - 20, c + 20, 4, 24, glass)
        cv.box(c - 22, c - 8, 26, c + 22, c + 4, 27.5, flat("2a5aa8"), flat("2a5aa8"), flat("2a5aa8"))
    _prop("bus_stop", stop, out, meta)
    return meta


def gen(out):
    os.makedirs(out, exist_ok=True)
    np.seterr(all="ignore")
    meta = {"cars": gen_cars(out), "people": gen_people(out), "animals": gen_animals(out), "props": gen_props(out)}
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), separators=(",", ":"))
    return meta


if __name__ == "__main__":
    import sys
    gen(sys.argv[1])


# ====================================================================== cursors and small effects
def gen_misc(root):
    """Tile cursors at 320x160, light pools, water drops, headlight beams."""
    from PIL import ImageDraw
    ui = os.path.join(root, "ui")
    fx = os.path.join(root, "fx")
    un = os.path.join(root, "units")
    for d_ in (ui, fx, un):
        os.makedirs(d_, exist_ok=True)
    W, H = 320, 160
    for name, fill, line in (("cursor_ok", (90, 220, 120, 70), (120, 255, 150, 230)), ("cursor_bad", (240, 80, 70, 80), (255, 110, 100, 235)),
                             ("cursor_sel", (255, 220, 90, 60), (255, 236, 140, 240)), ("cursor_road", (90, 170, 255, 60), (140, 200, 255, 220))):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        poly = [(W / 2, 3), (W - 5, H / 2), (W / 2, H - 3), (5, H / 2)]
        dr.polygon(poly, fill=fill)
        dr.line(poly + [poly[0]], fill=line, width=4)
        im.save(os.path.join(ui, name + ".png"))
    # soft light pool on the ground (iso ellipse)
    n = 256
    ys, xs = np.mgrid[0:n // 2, 0:n] + 0.5
    d = np.hypot((xs - n / 2) / (n / 2), (ys - n / 4) / (n / 4))
    a = np.clip(1 - d, 0, 1) ** 1.6
    img = np.zeros((n // 2, n, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = 255, 214, 150
    img[..., 3] = (a * 200).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(fx, "light_pool.png"))
    # headlight beam pointing right (+x on screen), rotated in game
    w, h = 160, 64
    ys, xs = np.mgrid[0:h, 0:w] + 0.5
    t = xs / w
    spread = (ys - h / 2) / (h / 2 * (0.25 + 0.75 * t))
    a = np.clip(1 - np.abs(spread), 0, 1) * np.clip(1 - t, 0, 1) ** 1.2 * np.clip(t * 6, 0, 1)
    img = np.zeros((h, w, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = 255, 240, 200
    img[..., 3] = (a * 160).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(fx, "beam.png"))
    # water drop and small round light
    for name, size, col in (("drop", 4, (220, 240, 255)), ("lamp_dot", 6, (255, 255, 255))):
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse((0, 0, size - 1, size - 1), fill=col + (255,))
        im.save(os.path.join(fx if name == "drop" else un, name + ".png"))
    # glow dot for lamp heads
    n = 48
    ys, xs = np.mgrid[0:n, 0:n] + 0.5
    a = np.clip(1 - np.hypot(xs - n / 2, ys - n / 2) / (n / 2), 0, 1) ** 2
    img = np.zeros((n, n, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = 255, 230, 170
    img[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(fx, "lamp_head.png"))
