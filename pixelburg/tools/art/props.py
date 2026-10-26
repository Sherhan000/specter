"""Textures and small props shared by buildings, nature and units."""
import math

import numpy as np

from raster import C, hash2, flat, value_noise

GLASS_DAY_TOP = C("a8d0ec")
GLASS_DAY = C("5a8ab4")
GLASS_DAY_DK = C("3e6688")
WARM = [C("ffd27a"), C("ffc65a"), C("ffe0a0"), C("dfe8ff")]

FONT = {
    "A": ["010", "101", "111", "101", "101"], "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"], "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"], "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"], "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"], "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"], "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "111", "101"], "O": ["010", "101", "101", "101", "010"],
    "P": ["110", "101", "110", "100", "100"], "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"], "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"], "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"], "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"], "+": ["000", "010", "111", "010", "000"],
    " ": ["000", "000", "000", "000", "000"], "1": ["010", "110", "010", "010", "111"],
    "2": ["110", "001", "010", "100", "111"], "4": ["101", "101", "111", "001", "001"],
}


def text_mask(text):
    cols = []
    for ch in text:
        g = FONT.get(ch, FONT[" "])
        cols.append(np.array([[c == "1" for c in row] for row in g]))
        cols.append(np.zeros((5, 1), bool))
    return np.hstack(cols[:-1]) if cols else np.zeros((5, 1), bool)


def nores(shape):
    return np.zeros(shape, bool)


def solid_res(col, shape):
    return np.broadcast_to(np.asarray(col, float), shape + (3,)).copy(), nores(shape), None


# ====================================================================== walls
DEFAULT_STYLE = dict(fh=26, ww=10, wh=13, wy=8, sp=18, mg=8, frame="f4f0e8", shutter=None, box=None,
                     brick=None, siding=False, band=None, plinth="8a8478", cornice=None, glass="day")


def wall(base, style=None, door=None, shop=None, signs=(), decals=(), seed=0, lit=0.6, cols=None,
         top_skip=4, windows=True, doors=()):
    """Facade texture. Callback fn(u, v, L, H) with u along the wall, v upwards."""
    st = dict(DEFAULT_STYLE)
    if style:
        st.update(style)
    base = C(base)
    frame = C(st["frame"])
    doors = list(doors) + ([door] if door else [])

    def fn(u, v, L, Hh):
        ui, vi = np.floor(u), np.floor(v)
        shape = u.shape
        rgb = np.broadcast_to(base, shape + (3,)).copy()
        rgb += ((hash2(ui, vi, seed + 7) - 0.5) * 7)[..., None]
        ns = nores(shape)
        em = np.zeros(shape + (4,))
        # vertical light gradient (sky light)
        rgb *= (0.94 + 0.08 * np.clip(v / max(Hh, 1), 0, 1))[..., None]
        if st["brick"]:
            row = np.floor(vi / 4)
            mortar = (vi % 4 == 0) | (((ui + (row % 2) * 4) % 8) == 0)
            rgb[mortar] *= st["brick"]
            tone = hash2(np.floor((ui + (row % 2) * 4) / 8), row, seed + 3)
            rgb *= (0.95 + 0.1 * tone)[..., None]
        if st["siding"]:
            rgb[(vi % 5) == 0] *= 0.86
            rgb[(vi % 5) == 1] *= 1.05
        if st["band"]:
            fh = st["fh"]
            band = ((vi % fh) == fh - 1) | ((vi % fh) == fh - 2)
            rgb[band & (vi < Hh - 2)] = C(st["band"])
        if st["plinth"]:
            pl = vi < 4
            rgb[pl] = C(st["plinth"])
            rgb[vi == 4] *= 0.8
        if st["cornice"]:
            cm = vi >= Hh - 3
            rgb[cm] = C(st["cornice"])
            rgb[vi == np.floor(Hh) - 4] *= 0.75
        # windows
        if windows:
            fh, ww, wh, wy, sp, mg = st["fh"], st["ww"], st["wh"], st["wy"], st["sp"], st["mg"]
            n = int((L - 2 * mg + sp - ww) // sp)
            if cols is not None:
                n = min(n, cols)
            if n > 0:
                total = n * sp - (sp - ww)
                start = np.floor((L - total) / 2)
                cu = ui - start
                col = np.floor(cu / sp)
                cin = cu - col * sp
                fl = np.floor(vi / fh)
                vin = vi - fl * fh
                inw = (cu >= 0) & (col < n) & (cin < ww) & (vin >= wy) & (vin < wy + wh) & (vi < Hh - top_skip)
                for (du0, dw, dh, *_r) in doors:
                    inw &= ~((ui >= du0 - 3) & (ui < du0 + dw + 3) & (vi < dh + 3))
                if shop is not None:
                    inw &= ~((ui >= shop[0] - 2) & (ui < shop[1] + 2) & (vi < shop[3] + 3))
                fr = inw & ((cin == 0) | (cin == ww - 1) | (vin == wy) | (vin == wy + wh - 1))
                mull = inw & ~fr & ((cin == ww // 2) | (vin == wy + wh // 2 + 1))
                glass = inw & ~fr & ~mull
                t = np.clip((vin - wy) / wh, 0, 1)
                g = GLASS_DAY_DK * (1 - t[..., None]) + GLASS_DAY * t[..., None]
                streak = ((cin + vin) % 7 == 0) | ((cin + vin) % 7 == 1)
                g = np.where(streak[..., None], GLASS_DAY_TOP, g)
                rgb[glass] = g[glass]
                ns |= glass
                rgb[fr | mull] = frame
                sill = (cu >= -1) & (col < n) & (cin < ww + 1) & (vin == wy - 1) & (vi < Hh - top_skip) & ~(vi < 6)
                rgb[sill] = frame * 0.82
                lintel = (cu >= 0) & (col < n) & (cin < ww) & (vin == wy + wh) & (vi < Hh - top_skip)
                rgb[lintel & ~inw] *= 0.8
                if st["shutter"]:
                    sh = (cu >= 0) & (col < n) & (vin >= wy) & (vin < wy + wh) & (vi < Hh - top_skip) & \
                        (((cin >= -3) & (cin < 0)) | ((cin >= ww) & (cin < ww + 3)))
                    shc = np.broadcast_to(C(st["shutter"]), shape + (3,)) * (1 - 0.15 * ((vi % 2) == 0))[..., None]
                    rgb[sh] = shc[sh]
                if st["box"]:
                    bx = (cu >= -1) & (col < n) & (cin < ww + 1) & (vin >= wy - 4) & (vin < wy - 1) & (vi > 6) & (vi < Hh - top_skip)
                    rgb[bx] = C("8a5a3a")
                    fl_ = bx & (vin == wy - 2) & (hash2(ui, vi, 5) > 0.45)
                    flc = np.stack([C("e84a5a"), C("f0c040"), C("f6f0f0"), C("c06ae0")])
                    rgb[fl_] = flc[(hash2(ui, fl, 6) * 4).astype(int) % 4][fl_]
                    rgb[bx & (vin == wy - 3) & ~fl_] = C("4f923e")
                kind_w = hash2(col + 17, fl + 29, seed + 4)
                plant = glass & (kind_w < 0.16) & (vin <= wy + 3)
                pc = np.where((hash2(ui, vi, seed + 2) > 0.5)[..., None], C("4f9a3e"), C("6ab84a")) * np.ones(shape + (3,))
                rgb[plant] = pc[plant]
                rgb[plant & (vin == wy + 1) & (hash2(ui, vi, 3) > 0.7)] = C("e86a8a")
                ns &= ~plant
                blinds = glass & (kind_w > 0.84) & (vin >= wy + wh // 2) & ((vin % 2) == 0)
                rgb[blinds] = C("e8e4d8")
                ns &= ~blinds
                lit_w = glass & (hash2(col + 3, fl + 11, seed) < lit)
                pick = (hash2(col + 5, fl + 2, seed + 9) * 4).astype(int) % 4
                wc = np.stack(WARM)[pick]
                curtain = lit_w & ((cin == 1) | (cin == ww - 2))
                em[lit_w] = np.dstack([wc, np.full(shape, 255.0)])[lit_w]
                em[curtain, :3] *= 0.7
        if shop is not None:
            u0, u1, v0, v1 = shop
            sm = (ui >= u0) & (ui < u1) & (vi >= v0) & (vi < v1)
            fr = sm & ((ui == u0) | (ui == u1 - 1) | (vi == v0) | (vi == v1 - 1) | ((ui - u0) % 12 == 0))
            gl = sm & ~fr
            t = np.clip((vi - v0) / max(1, v1 - v0), 0, 1)
            g = GLASS_DAY_DK * (1 - t[..., None]) + GLASS_DAY * t[..., None]
            rgb[gl] = g[gl]
            # shelves with goods behind the glass
            shelf = gl & (((vi - v0) % 5) == 1)
            rgb[shelf] = C("8a6a4a")
            goods = gl & (((vi - v0) % 5) == 2) & (hash2(ui, vi, 8) > 0.35)
            gcol = np.stack([C("e86a4a"), C("f0d050"), C("6ab04a"), C("f0f0f0"), C("4a8ad8")])
            rgb[goods] = gcol[(hash2(ui, vi, 9) * 5).astype(int) % 5][goods]
            refl = gl & (((ui - vi) % 9) < 2)
            rgb[refl] = rgb[refl] * 0.6 + GLASS_DAY_TOP * 0.4
            rgb[fr] = frame
            ns |= gl
            em[gl] = (255, 226, 160, 235)
        for d in doors:
            du0, dw, dh, dc = d[0], d[1], d[2], d[3]
            kind = d[4] if len(d) > 4 else "wood"
            dm = (ui >= du0) & (ui < du0 + dw) & (vi < dh)
            dfr = dm & ((ui == du0) | (ui == du0 + dw - 1) | (vi == dh - 1))
            if kind == "glass":
                rgb[dm] = GLASS_DAY
                rgb[dm & ((ui - du0) == dw // 2)] = frame
                em[dm & ~dfr] = (255, 230, 170, 220)
                ns |= dm & ~dfr
            else:
                rgb[dm] = C(dc)
                panel = dm & ~dfr & (((vi % 6) == 0) | ((ui - du0) == dw // 2))
                rgb[panel] = C(dc) * 0.78
                rgb[dm & (ui == du0 + dw - 3) & (vi == dh // 2)] = C("e8c860")
                ns &= ~dm
            rgb[dfr] = frame * 0.85
            # small lamp above the door
            lamp = (ui >= du0 + dw // 2 - 1) & (ui <= du0 + dw // 2) & (vi >= dh + 2) & (vi < dh + 4)
            rgb[lamp] = C("f8e8b0")
            em[lamp] = (255, 240, 180, 255)
        for (su0, sv0, text, bg, fg, neon) in signs:
            tm = text_mask(text)
            th, tw = tm.shape
            pu0, pv0 = su0 - 2, sv0 - 2
            pw, ph = tw + 4, th + 4
            panel = (ui >= pu0) & (ui < pu0 + pw) & (vi >= pv0) & (vi < pv0 + ph)
            rgb[panel] = C(bg)
            rgb[panel & ((ui == pu0) | (ui == pu0 + pw - 1) | (vi == pv0) | (vi == pv0 + ph - 1))] = C(bg) * 0.7
            tu = (ui - su0).astype(int)
            tv = (th - 1 - (vi - sv0)).astype(int)
            inside = (tu >= 0) & (tu < tw) & (tv >= 0) & (tv < th)
            on = np.zeros(shape, bool)
            on[inside] = tm[tv[inside], tu[inside]]
            rgb[on] = C(fg)
            ns |= on
            if neon:
                em[on] = np.append(C(fg), 255)
        for (u0, u1, v0, v1, c) in decals:
            dm = (ui >= u0) & (ui < u1) & (vi >= v0) & (vi < v1)
            if c.startswith("emit:"):
                cc = C(c[5:])
                rgb[dm] = cc
                ns |= dm
                em[dm] = np.append(cc, 255)
            else:
                rgb[dm] = C(c)
        ao = (vi < 2) & ~ns
        rgb[ao] *= 0.85
        return rgb, ns, em
    fn.doors = doors
    return fn


# ====================================================================== roofs
def roof_tiles(base, seed=3, kind="tiles"):
    base = C(base)

    def fn(along, across, maxacross):
        ai, ci = np.floor(along), np.floor(across)
        row = np.floor(across / 4)
        rgb = np.broadcast_to(base, along.shape + (3,)).copy()
        if kind == "tiles":
            rgb += ((hash2(np.floor((along + row * 3) / 6), row, seed) - 0.5) * 26)[..., None]
            rgb[ci % 4 == 0] *= 0.74
            rgb[(ci % 4 == 3)] *= 1.08
            rgb[(((ai + row * 3) % 6) == 0) & (ci % 4 != 0)] *= 0.86
        elif kind == "metal":
            rgb[(ai % 6) == 0] *= 0.8
            rgb[(ai % 6) == 1] *= 1.12
        elif kind == "slate":
            rgb += ((hash2(np.floor((along + row * 2) / 4), row, seed) - 0.5) * 16)[..., None]
            rgb[ci % 3 == 0] *= 0.8
        rgb[across < 1.5] = base * 0.7
        rgb[across > maxacross - 1.5] = base * 0.5
        return rgb, nores(along.shape), None
    return fn


def flat_roof(base="8a8a8a", rim="c8c0b0", seed=5, rim_w=3):
    base, rimc = C(base), C(rim)

    def fn(u, v, L, D):
        rgb = np.broadcast_to(base, u.shape + (3,)).copy()
        rgb += ((hash2(np.floor(u), np.floor(v), seed) - 0.5) * 12)[..., None]
        edge = (u < rim_w) | (v < rim_w) | (u > L - rim_w) | (v > D - rim_w)
        rgb[edge] = rimc
        inner = ~edge & ((u < rim_w + 1.5) | (v < rim_w + 1.5))
        rgb[inner] *= 0.75
        return rgb, nores(u.shape), None
    return fn


# ====================================================================== grounds
GRASS = [C("5a9a3e"), C("64a646"), C("6eb04c"), C("7aba54"), C("8ec660")]


def grass_fn(seed=1, flowers=0.0):
    def fn(u, v, *_):
        h = hash2(np.floor(u / 2), np.floor(v / 2), seed)
        h2 = hash2(np.floor(u / 7), np.floor(v / 7), seed + 1)
        idx = np.clip((h * 0.7 + h2 * 0.5) * 3.6, 0, 4).astype(int)
        rgb = np.stack(GRASS)[idx].copy()
        blade = hash2(np.floor(u), np.floor(v), seed + 2) > 0.93
        rgb[blade] = GRASS[4] * 1.06
        if flowers > 0:
            fl = hash2(np.floor(u), np.floor(v), seed + 3) > 1 - flowers
            fc = np.stack([C("f6f0e0"), C("f0d050"), C("e86a8a"), C("b08ae0")])
            rgb[fl] = fc[(hash2(np.floor(u), np.floor(v), seed + 4) * 4).astype(int) % 4][fl]
        return rgb, nores(u.shape), None
    return fn


def paving(base="c8bca8", tile=8, seed=2):
    base = C(base)

    def fn(u, v, *_):
        rgb = np.broadcast_to(base, u.shape + (3,)).copy()
        rgb += ((hash2(np.floor(u / tile), np.floor(v / tile), seed) - 0.5) * 14)[..., None]
        line = ((np.floor(u) % tile) == 0) | ((np.floor(v) % tile) == 0)
        rgb[line] *= 0.86
        return rgb, nores(u.shape), None
    return fn


def lot(cv, kind="grass", seed=1, path=None, flowers=0.01):
    g = grass_fn(seed, flowers)
    pav = paving()

    def fn(u, v, L, D):
        if kind == "grass":
            rgb, ns, _ = g(u, v)
        elif kind == "paved":
            rgb, ns, _ = pav(u, v)
        elif kind == "asphalt":
            rgb = np.broadcast_to(C("6a6a74"), u.shape + (3,)).copy()
            rgb += ((hash2(np.floor(u), np.floor(v), 3) - 0.5) * 9)[..., None]
            ns = nores(u.shape)
        else:
            rgb, ns, _ = g(u, v)
        if path is not None:
            pm = path(u, v)
            pr, _, _ = pav(u, v)
            rgb[pm] = pr[pm]
        return rgb, ns, None
    cv.ground(fn)


# ====================================================================== props
def leaf_fn(pal, seed=0, blossom=None):
    pal = [C(c) if isinstance(c, str) else c for c in pal]

    def fn(wx, wy, wz, nx, ny, nz):
        h = hash2(np.floor(wx / 2), np.floor((wy + wz) / 2), seed)
        lum = nx * -0.25 + ny * 0.55 + nz * 0.8 + (h - 0.5) * 0.7
        idx = np.clip(((lum + 0.6) / 1.7) * len(pal), 0, len(pal) - 1).astype(int)
        rgb = np.stack(pal)[idx]
        if blossom is not None:
            b = hash2(np.floor(wx), np.floor(wy + wz), seed + 4) > 0.86
            rgb[b] = C(blossom)
        return rgb, np.ones(wx.shape, bool), None
    return fn


def trunk_fn(col="6a4426"):
    c = C(col)

    def side(ang, v, nx, ny):
        rgb = np.broadcast_to(c, ang.shape + (3,)).copy()
        rgb[(np.floor(v) % 5 == 0) & (hash2(np.floor(ang * 5), np.floor(v), 2) > 0.5)] *= 0.8
        return rgb, nores(ang.shape), None
    return side


LEAF_GREEN = ["1e4524", "285a2c", "35722f", "468a3a", "5ea248", "7cbc58"]
LEAF_DARK = ["183a20", "214c28", "2c602f", "3a7436", "4e8a42"]
LEAF_PINK = ["7a3456", "a04a72", "c86a92", "e292b4", "f6bed2"]
LEAF_AUTUMN = ["7a3018", "a84a1a", "d0702a", "e89a3a", "f4c050"]
LEAF_BIRCH = ["3a6a2a", "4f8a36", "6aa648", "8cc25a", "b0d878"]


def tree(cv, x, y, scale=1.0, kind="oak", seed=0):
    rng = np.random.default_rng(seed)
    s = scale
    if kind == "pine":
        cv.cylinder(x, y, 2.2 * s, 0, 14 * s, trunk_fn("5a3a22"))
        layers = [(10 * s, 15 * s, 22 * s), (22 * s, 12 * s, 20 * s), (33 * s, 9 * s, 17 * s), (43 * s, 6 * s, 13 * s)]
        for (z0, r, hh) in layers:
            w = int(2 * r + 3)
            ys, xs = np.mgrid[0:w, 0:w] + 0.5
            d = np.hypot(xs - w / 2, ys - w / 2)
            H = np.where(d < r, z0 + hh * (1 - d / r) + (hash2(xs.astype(int), ys.astype(int), seed) - 0.5) * 1.5, -np.inf)
            cv.heightfield(x - w / 2, y - w / 2, H, leaf_fn(LEAF_DARK, seed), zmin=z0 - 1, thick=5.0)
        return
    trunk_c = "d8d4cc" if kind == "birch" else "6a4426"
    th = 18 * s
    cv.cylinder(x, y, 2.6 * s, 0, th, trunk_fn(trunk_c))
    pal = {"oak": LEAF_GREEN, "sakura": LEAF_PINK, "autumn": LEAF_AUTUMN, "birch": LEAF_BIRCH}[kind]
    blossom = "fff0f6" if kind == "sakura" else None
    blobs = [(0, 0, th + 12 * s, 13 * s)]
    for i in range(5):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(5, 9) * s
        blobs.append((math.cos(a) * d, math.sin(a) * d, th + rng.uniform(6, 16) * s, rng.uniform(7, 10) * s))
    for (dx, dy, z, r) in blobs:
        cv.ellipsoid(x + dx, y + dy, z, r, r, r * 0.9, leaf_fn(pal, seed + int(z), blossom))


def bush(cv, x, y, s=1.0, seed=0, flowers=None):
    rng = np.random.default_rng(seed)
    for i in range(3):
        dx, dy = rng.uniform(-4, 4) * s, rng.uniform(-4, 4) * s
        cv.ellipsoid(x + dx, y + dy, 4 * s, 6 * s, 6 * s, 5 * s, leaf_fn(LEAF_GREEN, seed + i, flowers))


def lamp_post(cv, x, y, h=34, style="classic"):
    pole = trunk_fn("3a3a46")
    cv.cylinder(x, y, 1.6, 0, h, pole, lambda a, b: solid_res(C("3a3a46"), a.shape))
    cv.cylinder(x, y, 3.0, 0, 3, pole)
    lamp = lambda *a: (np.broadcast_to(C("fff0b8"), a[0].shape + (3,)).copy(), np.ones(a[0].shape, bool),
                       np.broadcast_to(np.array([255, 236, 170, 255.0]), a[0].shape + (4,)).copy())
    if style == "classic":
        cv.box(x - 3.5, y - 3.5, h, x + 3.5, y + 3.5, h + 7, lamp, lamp, flat("2a2a34"))
        cv.box(x - 4.5, y - 4.5, h + 7, x + 4.5, y + 4.5, h + 9, flat("2a2a34"), flat("2a2a34"), flat("3a3a46"))
    else:
        cv.box(x - 1, y - 1, h, x + 9, y + 1, h + 2, flat("3a3a46"))
        cv.box(x + 5, y - 2, h - 2, x + 10, y + 2, h, lamp, lamp, flat("3a3a46"))


def fence(cv, x0, y0, x1, y1, col="f4f0e8", h=6):
    c = flat(col, 3)
    if abs(x1 - x0) > abs(y1 - y0):
        for x in np.arange(x0, x1 + 0.1, 5):
            cv.box(x, y0 - 0.8, 0, x + 1.6, y0 + 0.8, h, c, c, c)
        cv.box(x0, y0 - 0.5, h - 3, x1 + 1.6, y0 + 0.5, h - 2, c, c, c)
    else:
        for y in np.arange(y0, y1 + 0.1, 5):
            cv.box(x0 - 0.8, y, 0, x0 + 0.8, y + 1.6, h, c, c, c)
        cv.box(x0 - 0.5, y0, h - 3, x0 + 0.5, y1 + 1.6, h - 2, c, c, c)


def ac_unit(cv, x, y, z):
    cv.box(x, y, z, x + 7, y + 6, z + 5, flat("c8ccd0", 3), flat("a8acb0", 3), flat("dce0e4", 3))


def solar(cv, x0, y0, x1, y1, z):
    def fn(u, v, L, D):
        rgb = np.broadcast_to(C("2a3a6a"), u.shape + (3,)).copy()
        grid = ((np.floor(u) % 5) == 0) | ((np.floor(v) % 5) == 0)
        rgb[grid] = C("8a9ac8")
        return rgb, nores(u.shape), None
    cv.box(x0, y0, z, x1, y1, z + 1.5, flat("6a6a74"), flat("5a5a64"), fn)


def water_tank(cv, x, y, z, r=6, h=12):
    leg = flat("5a4a3a")
    for (dx, dy) in ((-r + 1, -r + 1), (r - 2, -r + 1), (-r + 1, r - 2), (r - 2, r - 2)):
        cv.box(x + dx, y + dy, z, x + dx + 1.5, y + dy + 1.5, z + 6, leg, leg, leg)
    cv.cylinder(x, y, r, z + 6, z + 6 + h, trunk_fn("8a6a4a"), lambda a, b: solid_res(C("6a4a3a"), a.shape))


def umbrella_table(cv, x, y, col="e85a4a"):
    cv.cylinder(x, y, 2.5, 0, 6, lambda a, v, nx, ny: solid_res(C("f4f4f4"), a.shape))
    cv.cylinder(x, y, 0.6, 6, 15, lambda a, v, nx, ny: solid_res(C("8a8a8a"), a.shape))
    w = 15
    ys, xs = np.mgrid[0:w, 0:w] + 0.5
    d = np.hypot(xs - w / 2, ys - w / 2)
    H = np.where(d < 7, 18 - d * 0.5, -np.inf)
    stripes = lambda wx, wy, wz, nx, ny, nz: (np.where(((np.floor(np.arctan2(wy - y, wx - x) * 2.5) % 2) == 0)[..., None],
                                                       C(col), C("f8f4ec")) * np.ones(wx.shape + (3,)), nores(wx.shape), None)
    cv.heightfield(x - w / 2, y - w / 2, H, stripes, zmin=14, thick=2.0)


def bench(cv, x, y, axis="x"):
    wood, metal = flat("b07a48", 6), flat("3a3a44")
    if axis == "x":
        cv.box(x, y, 3, x + 14, y + 4, 4.5, wood, wood, wood)
        cv.box(x, y, 4.5, x + 14, y + 1, 9, wood, wood, wood)
        for dx in (1, 12):
            cv.box(x + dx, y + 1, 0, x + dx + 1, y + 4, 3, metal, metal, metal)
    else:
        cv.box(x, y, 3, x + 4, y + 14, 4.5, wood, wood, wood)
        cv.box(x, y, 4.5, x + 1, y + 14, 9, wood, wood, wood)
        for dy in (1, 12):
            cv.box(x + 1, y + dy, 0, x + 4, y + dy + 1, 3, metal, metal, metal)


def flower_patch(cv, x0, y0, x1, y1, seed=0, border="c8b8a0"):
    def fn(u, v, L, D):
        rgb = np.broadcast_to(C("5a3a20"), u.shape + (3,)).copy()
        h = hash2(np.floor(u / 2), np.floor(v / 2), seed)
        cols = np.stack([C("e84a5a"), C("f0c040"), C("f6f0f0"), C("b06ae0"), C("f08a3a")])
        fl = h > 0.38
        idx = (hash2(np.floor(u / 2), np.floor(v / 2), seed + 1) * 5).astype(int) % 5
        rgb[fl] = cols[idx][fl]
        leaf = (h > 0.18) & ~fl
        rgb[leaf] = C("4f923e")
        hl = fl & ((np.floor(u) + np.floor(v)) % 2 == 0)
        rgb[hl] = rgb[hl] * 1.15
        return rgb, nores(u.shape), None
    cv.box(x0, y0, 0, x1, y1, 3, flat(border), flat(border), fn)


def parked_car(cv, x, y, direction="px", col="d84a3a", kind="sedan"):
    import units
    units.car_body(cv, x, y, direction, col, kind)


def hedge(cv, x0, y0, x1, y1, h=7, seed=0):
    """Trimmed hedge with leafy texture."""
    def leaf(u, v, *_):
        hh = hash2(np.floor(u / 1.5), np.floor(v / 1.5), seed)
        rgb = np.where((hh > 0.6)[..., None], C("4f9a3e"), np.where((hh > 0.25)[..., None], C("3f8434"), C("2f6a2a")))
        rgb = rgb * np.ones(u.shape + (3,))
        rgb[hash2(np.floor(u), np.floor(v), seed + 1) > 0.95] = C("8cc45a")
        return rgb, nores(u.shape), None
    cv.box(x0, y0, 0, x1, y1, h, leaf, leaf, leaf)


def mailbox(cv, x, y, col="3a6ad0"):
    cv.box(x, y, 0, x + 1.2, y + 1.2, 6, flat("6a6a70"), flat("5a5a60"), flat("6a6a70"))
    cv.box(x - 1.5, y - 1, 6, x + 2.5, y + 2.2, 9, flat(col), flat(col), flat(col))


def dormer(cv, x0, x1, y_face, z_base, depth=8, h=9, roofc="a84a32", wallc="f0e8d8"):
    """Small roof window sticking out of a sloped roof towards +y."""
    from raster import Canvas  # noqa: F401  (documentation of the type only)
    w = wall(wallc, style=dict(ww=6, wh=6, wy=1, sp=10, mg=2, plinth=None), cols=1, top_skip=0)
    cv.box(x0, y_face - depth, z_base, x1, y_face, z_base + h, w, w, flat(roofc))
    cv.gable(x0, y_face - depth, x1, y_face, z_base + h, 5, roof_tiles(roofc), w, "y", 1.5)
