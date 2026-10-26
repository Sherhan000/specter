"""Architecture kit at real scale (10 units = 1 m): facades, roofs, oriented blocks.

Facades are authored as seen from outside, left to right: u along the wall, v up from its
foot. A facade callback returns (rgb, no_shade_mask, emission, rooms) where `rooms` holds the
window light of four groups (one per channel) that the game switches per household.

`Orient` places everything in front-relative coordinates: s runs across the front (left to
right as seen from the street), f from the front edge inwards. Rendering a building in the
four orientations gives correct lighting and readable signs whichever way it faces.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from raster import C, U, M, Canvas, flat, hash2, nores, solid_res, glow_res, SH_X, SH_Y, SH_TOP

FONT_PATH = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
_FONTS = {}

WARM = np.array([[255, 214, 140], [255, 200, 120], [255, 226, 168], [236, 238, 255]], float)


# ====================================================================== text
def text_mask(text, height):
    """Boolean mask of `text` rendered `height` units tall (Inter Bold)."""
    key = (text, height)
    if key in _FONTS:
        return _FONTS[key]
    px = max(6, int(height * 1.35))
    font = ImageFont.truetype(FONT_PATH, px)
    l, t, r, b = font.getbbox(text)
    img = Image.new("L", (r - l + 2, b - t + 2), 0)
    ImageDraw.Draw(img).text((1 - l, 1 - t), text, fill=255, font=font)
    arr = np.array(img) > 110
    ys, xs = np.where(arr)
    arr = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(xs) else arr
    # scale to the wanted height
    h = max(3, int(round(height)))
    w = max(1, int(round(arr.shape[1] * h / arr.shape[0])))
    arr = np.array(Image.fromarray(arr.astype(np.uint8) * 255).resize((w, h), Image.LANCZOS)) > 100
    _FONTS[key] = arr
    return arr


# ====================================================================== materials
def _mat(kind, col, seed):
    base = C(col)

    def paint(ui, vi, u, v, rgb):
        if kind == "plaster":
            rgb += ((hash2(np.floor(u / 2), np.floor(v / 2), seed) - 0.5) * 6)[..., None]
        elif kind == "brick":
            row = np.floor(v / 3.0)
            off = (row % 2) * 3.5
            bu = np.floor((u + off) / 7.0)
            tone = hash2(bu, row, seed + 3)
            rgb *= (0.9 + 0.18 * tone)[..., None]
            mortar = ((v % 3.0) < 0.6) | (((u + off) % 7.0) < 0.6)
            rgb[mortar] = rgb[mortar] * 0.5 + C("d8d0c4") * 0.5
        elif kind == "siding":
            rgb *= (1.0 - 0.13 * ((v % 3.0) < 0.7))[..., None]
            rgb += ((hash2(np.floor(u / 40), np.floor(v / 3), seed) - 0.5) * 6)[..., None]
        elif kind == "wood":
            rgb *= (1.0 - 0.16 * ((u % 4.0) < 0.6))[..., None]
            rgb += ((hash2(np.floor(u / 4), np.floor(v / 30), seed) - 0.5) * 14)[..., None]
        elif kind == "stone":
            row = np.floor(v / 6.0)
            off = (row % 2) * 6
            bu = np.floor((u + off) / 12.0)
            rgb *= (0.92 + 0.12 * hash2(bu, row, seed + 5))[..., None]
            joint = ((v % 6.0) < 0.6) | (((u + off) % 12.0) < 0.6)
            rgb[joint] *= 0.72
        elif kind == "concrete":
            rgb += ((hash2(np.floor(u / 3), np.floor(v / 3), seed) - 0.5) * 7)[..., None]
            joint = ((v % 30.0) < 0.5) | ((u % 40.0) < 0.5)
            rgb[joint] *= 0.82
        elif kind == "metal":
            rib = (u % 4.0)
            rgb *= (0.86 + 0.2 * (rib < 2.0))[..., None]
        elif kind == "tile":
            joint = ((v % 5.0) < 0.5) | ((u % 5.0) < 0.5)
            rgb[joint] *= 0.82
            rgb += ((hash2(np.floor(u / 5), np.floor(v / 5), seed) - 0.5) * 10)[..., None]
        return rgb
    return base, paint


# ====================================================================== facades
class Win:
    """Window layout of a facade, in units (10 = 1 m)."""

    def __init__(self, w=12, h=15, sill=9, sp=None, margin=12, fh=30, frame="f2efe8", style="cross",
                 shutters=None, boxes=False, lintel=True, top_skip=6, cols=None, arch=False, balcony_door=None,
                 tint=None, group="home"):
        self.w, self.h, self.sill = w, h, sill
        self.sp = sp or w * 2.2
        self.margin, self.fh = margin, fh
        self.frame = C(frame)
        self.style = style
        self.shutters = C(shutters) if shutters else None
        self.boxes = boxes
        self.lintel = lintel
        self.top_skip = top_skip
        self.cols = cols
        self.arch = arch
        self.tint = C(tint) if tint else None
        self.group = group


def facade(mat="plaster", col="eae2d0", win=None, doors=(), shop=None, signs=(), bands=(), plinth=("8a8478", 5),
           cornice=None, seed=0, lit=0.55, decals=(), skip=(), ground_win=True, quoins=None):
    """A wall texture.

    doors: (u0, width, height, kind, colour) kind wood|glass|double|garage|shutter|panel
    shop: (u0, u1, height) a glazed shop front with goods behind the glass
    signs: (u_centre, v_bottom, text, height, bg, fg, glow)
    bands: (v0, v1, colour) horizontal bands (floor slabs, friezes)
    skip: (u0, u1, v0, v1) areas without windows
    decals: (u0, u1, v0, v1, colour or 'emit:colour')
    """
    base, paint = _mat(mat, col, seed)
    doors = list(doors)

    def fn(u, v, L, Hh):
        ui, vi = np.floor(u), np.floor(v)
        shape = u.shape
        rgb = np.broadcast_to(base, shape + (3,)).copy()
        rgb = paint(ui, vi, u, v, rgb)
        rgb *= (0.95 + 0.07 * np.clip(v / max(Hh, 1), 0, 1))[..., None]
        ns = nores(shape)
        em = np.zeros(shape + (4,))
        rooms = np.zeros(shape + (4,))
        if quoins:
            q = ((u < 4) | (u > L - 4)) & ((np.floor(v / 6) % 2) == 0)
            rgb[q] = C(quoins)
        for (v0, v1, bc) in bands:
            bm = (v >= v0) & (v < v1)
            rgb[bm] = C(bc) + ((hash2(ui, vi, 3) - 0.5) * 4)[bm][..., None]
            rgb[bm & (v < v0 + 1)] *= 0.8
        if plinth:
            pc, ph = plinth
            pm = v < ph
            rgb[pm] = C(pc) + ((hash2(np.floor(u / 2), np.floor(v / 2), 4) - 0.5) * 8)[pm][..., None]
            rgb[(v >= ph) & (v < ph + 1)] *= 0.82
        if cornice:
            cc, ch = cornice
            cm = v >= Hh - ch
            rgb[cm] = C(cc)
            rgb[cm & (v < Hh - ch + 1.2)] *= 0.72
        blocked = np.zeros(shape, bool)
        for (u0, w, h, *_r) in doors:
            blocked |= (u >= u0 - 3) & (u < u0 + w + 3) & (v < h + 4)
        if shop is not None:
            blocked |= (u >= shop[0] - 3) & (u < shop[1] + 3) & (v < shop[2] + 5)
        for (u0, u1, v0, v1) in skip:
            blocked |= (u >= u0) & (u < u1) & (v >= v0) & (v < v1)
        for (uc, v0, text, th, *_r) in signs:
            tm = text_mask(text, th)
            hw = tm.shape[1] / 2 + 4
            blocked |= (u >= uc - hw) & (u < uc + hw) & (v >= v0 - 3) & (v < v0 + th + 3)
        # ------------------------------------------------ windows
        if win is not None:
            w_, h_, fh = win.w, win.h, win.fh
            n = int((L - 2 * win.margin - w_) // win.sp) + 1
            if win.cols is not None:
                n = min(n, win.cols)
            if n > 0:
                total = (n - 1) * win.sp + w_
                start = (L - total) / 2
                cu = u - start
                col_i = np.floor(cu / win.sp + 1e-6)
                cin = cu - col_i * win.sp
                fl = np.floor(v / fh)
                vin = v - fl * fh
                rowok = (v < Hh - win.top_skip) & ((fl > 0) | ground_win)
                inw = (cu >= 0) & (col_i < n) & (cin < w_) & (vin >= win.sill) & (vin < win.sill + h_) & rowok & ~blocked
                if win.arch:
                    cx = cin - w_ / 2
                    top = win.sill + h_ - w_ / 2
                    inw &= ~((vin > top) & (cx * cx + (vin - top) ** 2 > (w_ / 2) ** 2))
                fx = cin
                fy = vin - win.sill
                frame = inw & ((fx < 1.2) | (fx > w_ - 1.2) | (fy < 1.2) | (fy > h_ - 1.2))
                if win.style == "cross":
                    mull = inw & ~frame & ((np.abs(fx - w_ / 2) < 0.6) | (np.abs(fy - h_ * 0.62) < 0.6))
                elif win.style == "vertical":
                    mull = inw & ~frame & (np.abs(fx - w_ / 2) < 0.6)
                elif win.style == "grid":
                    mull = inw & ~frame & ((np.abs(((fx - 1) % ((w_ - 2) / 3)) ) < 0.6) | (np.abs(((fy - 1) % ((h_ - 2) / 3))) < 0.6))
                else:
                    mull = nores(shape)
                glass = inw & ~frame & ~mull
                t = np.clip(fy / h_, 0, 1)
                gl = C("40607e") * (1 - t[..., None]) + C("8eb4d2") * t[..., None]
                if win.tint is not None:
                    gl = gl * 0.6 + win.tint * 0.4
                # sky reflection streak
                streak = (((fx * 0.8 + fy) % 13.0) < 2.2)
                gl = np.where(streak[..., None], gl * 0.6 + C("dceaf4") * 0.4, gl)
                kind = hash2(col_i + 31, fl + 7, seed + 11)
                # curtains, blinds, plants behind the glass
                cur = glass & (kind < 0.45) & ((fx < 3.2) | (fx > w_ - 3.2))
                curc = np.stack([C("e8dcc8"), C("d89a8a"), C("a8b8d8"), C("e8d090")])[(hash2(col_i, fl, seed) * 4).astype(int) % 4]
                gl = np.where(cur[..., None], curc * 0.85, gl)
                blind = glass & (kind > 0.8) & (fy > h_ * 0.55) & ((np.floor(fy) % 2) == 0)
                gl = np.where(blind[..., None], C("e6e2d6"), gl)
                rgb[glass] = gl[glass]
                ns |= glass & ~cur & ~blind
                rgb[frame | mull] = win.frame
                # deep reveal: shadow along the top and left of the opening
                rev = glass & ((fy > h_ - 2.4) | (fx < 2.0))
                rgb[rev] *= 0.78
                sill = (cu >= -1.5) & (col_i < n) & (cin < w_ + 1.5) & (vin >= win.sill - 2) & (vin < win.sill) & rowok & ~blocked
                rgb[sill] = win.frame * 0.9
                rgb[sill & (vin < win.sill - 1.2)] *= 0.7
                if win.lintel:
                    lin = (cu >= -1) & (col_i < n) & (cin < w_ + 1) & (vin >= win.sill + h_) & (vin < win.sill + h_ + 1.5) & rowok & ~blocked
                    rgb[lin] *= 0.8
                if win.shutters is not None:
                    shm = (cu >= 0) & (col_i < n) & (vin >= win.sill) & (vin < win.sill + h_) & rowok & ~blocked & \
                        (((cin >= -5) & (cin < -0.5)) | ((cin >= w_ + 0.5) & (cin < w_ + 5)))
                    shc = win.shutters * (1 - 0.18 * ((np.floor(vin) % 2) == 0))[..., None]
                    rgb[shm] = shc[shm]
                if win.boxes:
                    bx = (cu >= -1) & (col_i < n) & (cin < w_ + 1) & (vin >= win.sill - 5) & (vin < win.sill - 2) & rowok & ~blocked & (fl > 0)
                    rgb[bx] = C("7a5034")
                    flw = (cu >= -1) & (col_i < n) & (cin < w_ + 1) & (vin >= win.sill - 2) & (vin < win.sill + 1.5) & rowok & ~blocked & (fl > 0)
                    fl_on = flw & (hash2(ui, vi, 5) > 0.35)
                    fc = np.stack([C("e04a5a"), C("f2c440"), C("f6f0f0"), C("b45ad8"), C("4f9a3e")])
                    rgb[fl_on] = fc[(hash2(ui, vi, 6) * 5).astype(int) % 5][fl_on]
                # window light at night: rooms layer (houses, flats) or plain warm light (work places)
                lit_w = glass & (hash2(col_i + 3, fl + 11, seed) < (lit if win.group not in ("home", "flats") else 1.0))
                if win.group in ("home", "flats"):
                    if win.group == "home":
                        grp = np.where(fl == 0, 0, 1)
                        extra = hash2(col_i + 9, fl + 1, seed + 2)
                        grp = np.where(extra < 0.22, 2, np.where(extra > 0.85, 3, grp))
                    else:
                        grp = (hash2(col_i, fl, seed + 5) * 4).astype(int) % 4
                    for k in range(4):
                        mk = lit_w & (grp == k)
                        rooms[mk, k] = np.where(cur[mk], 170, 255)
                else:
                    pick = (hash2(col_i + 5, fl + 2, seed + 9) * 4).astype(int) % 4
                    wc = WARM[pick]
                    e = np.dstack([wc, np.full(shape, 235.0)])
                    em[lit_w] = e[lit_w]
                    em[lit_w & cur, :3] *= 0.75
        # ------------------------------------------------ shop front
        if shop is not None:
            u0, u1, sh = shop
            sm = (u >= u0) & (u < u1) & (v < sh)
            fr = sm & ((u < u0 + 1.5) | (u > u1 - 1.5) | (v > sh - 1.5) | (((u - u0) % 20) < 1.2) | (v < 4))
            gl = sm & ~fr
            t = np.clip(v / sh, 0, 1)
            g = C("3e5a72") * (1 - t[..., None]) + C("86aac4") * t[..., None]
            rgb[gl] = g[gl]
            shelf = gl & ((np.floor(v) % 6) == 4) & (v > 6)
            rgb[shelf] = C("7a5a40")
            goods = gl & ((np.floor(v) % 6) < 3) & (v > 6) & (v < sh - 4) & (hash2(ui, np.floor(v / 6), 8) > 0.3)
            gc = np.stack([C("e86a4a"), C("f0d050"), C("6ab04a"), C("f4f0e8"), C("4a8ad8"), C("d85a9a")])
            rgb[goods] = gc[(hash2(np.floor(u / 2), np.floor(v / 6), 9) * 6).astype(int) % 6][goods]
            refl = gl & ((((u - v) % 17) < 3))
            rgb[refl] = rgb[refl] * 0.55 + C("e0ecf4") * 0.45
            rgb[fr] = C("3a3a40")
            ns |= gl
            em[gl] = (255, 230, 170, 225)
        # ------------------------------------------------ doors
        for d in doors:
            u0, w, h, kind, dc = d[0], d[1], d[2], d[3], C(d[4]) if len(d) > 4 else C("7a4a2a")
            dm = (u >= u0) & (u < u0 + w) & (v < h)
            dfr = dm & ((u < u0 + 1.2) | (u > u0 + w - 1.2) | (v > h - 1.2))
            if kind in ("glass", "double_glass"):
                rgb[dm] = C("4a6a84")
                rgb[dm & (np.abs(u - u0 - w / 2) < 0.7)] = C("3a3a40")
                rgb[dm & ((u - v * 0.6) % 9 < 1.5)] = C("9ab8cc")
                em[dm & ~dfr] = (255, 230, 170, 210)
                ns |= dm & ~dfr
                rgb[dfr] = C("3a3a40")
            elif kind == "garage":
                rgb[dm] = dc
                rgb[dm & ((np.floor(v) % 5) == 0)] *= 0.78
                rgb[dfr] = dc * 0.7
            elif kind == "shutter":
                rgb[dm] = dc
                rgb[dm & ((np.floor(v) % 2) == 0)] *= 0.86
                rgb[dfr] = C("4a4a50")
            else:
                rgb[dm] = dc
                pan = dm & ~dfr & ((np.abs(u - u0 - w / 2) < 0.6) | (np.abs(v - h * 0.5) < 0.6) | (np.abs(v - h * 0.85) < 0.5))
                rgb[pan] = dc * 0.75
                if kind == "double":
                    rgb[dm & (np.abs(u - u0 - w / 2) < 0.6)] = dc * 0.6
                knob = dm & (np.abs(u - (u0 + w - 2.5)) < 0.8) & (np.abs(v - h * 0.48) < 0.8)
                rgb[knob] = C("e8c860")
                rgb[dfr] = C("f0ebe0") * 0.86
            # recessed: a dark line along the top
            rgb[dm & (v > h - 0.8)] *= 0.6
            # lamp over the entrance
            if kind != "garage":
                lamp = (np.abs(u - (u0 + w / 2)) < 1.2) & (v >= h + 2.5) & (v < h + 5)
                rgb[lamp] = C("f8ecc0")
                em[lamp] = (255, 236, 176, 255)
                ns |= lamp
        # ------------------------------------------------ signs
        for sg in signs:
            uc, v0, text, th, bg, fg, glow = sg[:7]
            tm = text_mask(text, th)
            hh, ww = tm.shape
            pu0 = uc - ww / 2 - 3
            pm = (u >= pu0) & (u < pu0 + ww + 6) & (v >= v0 - 2) & (v < v0 + hh + 2)
            if bg:
                rgb[pm] = C(bg)
                rgb[pm & ((v < v0 - 1.2) | (v > v0 + hh + 0.8))] *= 0.7
            tu = np.floor(u - (uc - ww / 2)).astype(int)
            tv = np.floor(v0 + hh - 1 - v + 0.999).astype(int)
            inside = (tu >= 0) & (tu < ww) & (tv >= 0) & (tv < hh)
            on = np.zeros(shape, bool)
            on[inside] = tm[tv[inside], tu[inside]]
            rgb[on] = C(fg)
            ns |= on
            if glow:
                em[on] = np.append(C(fg), 255)
        for (u0, u1, v0, v1, c) in decals:
            dm = (u >= u0) & (u < u1) & (v >= v0) & (v < v1)
            if c.startswith("emit:"):
                cc = C(c[5:])
                rgb[dm] = cc
                ns |= dm
                em[dm] = np.append(cc, 255)
            else:
                rgb[dm] = C(c)
        return rgb, ns, em, rooms
    fn.doors = doors
    return fn


# ====================================================================== roofs & tops
def roof_mat(col, kind="tiles", seed=3):
    """Pitched roof surface: fn(along, across, maxacross) for gable/hip helpers."""
    base = C(col)

    def fn(along, across, maxacross):
        shape = along.shape
        rgb = np.broadcast_to(base, shape + (3,)).copy()
        if kind == "tiles":
            row = np.floor(across / 3.2)
            off = (row % 2) * 2.5
            t = hash2(np.floor((along + off) / 5.0), row, seed)
            rgb *= (0.88 + 0.2 * t)[..., None]
            rgb[(across % 3.2) < 0.8] *= 0.72
        elif kind == "shingle":
            row = np.floor(across / 2.6)
            off = (row % 2) * 3
            t = hash2(np.floor((along + off) / 6.0), row, seed)
            rgb *= (0.9 + 0.14 * t)[..., None]
            rgb[(across % 2.6) < 0.6] *= 0.75
        elif kind == "metal":
            rgb *= (0.9 + 0.14 * ((along % 5.0) < 1.0))[..., None]
        elif kind == "slate":
            row = np.floor(across / 3.0)
            off = (row % 2) * 3
            t = hash2(np.floor((along + off) / 6.0), row, seed)
            rgb *= (0.86 + 0.18 * t)[..., None]
            rgb[(across % 3.0) < 0.5] *= 0.7
        ridge = across < 1.6
        rgb[ridge] = base * 0.8
        eave = across > maxacross - 1.6
        rgb[eave] = base * 0.62
        return rgb, nores(shape), None
    return fn


def flat_top(col="8e8c88", rim="cfcac0", rim_w=3.0, seed=5, gravel=True):
    base, rimc = C(col), C(rim)

    def fn(u, v, L, D):
        shape = u.shape
        rgb = np.broadcast_to(base, shape + (3,)).copy()
        if gravel:
            rgb += ((hash2(np.floor(u), np.floor(v), seed) - 0.5) * 16)[..., None]
        edge = (u < rim_w) | (v < rim_w) | (u > L - rim_w) | (v > D - rim_w)
        rgb[edge] = rimc
        inner = (u >= rim_w) & (v >= rim_w) & (u < rim_w + 1.5) | (v >= rim_w) & (u >= rim_w) & (v < rim_w + 1.5)
        rgb[inner & ~edge] *= 0.72
        return rgb, nores(shape), None
    return fn


# ====================================================================== oriented building
class Orient:
    """Front-relative placement. o: 0 front faces +y, 1 +x, 2 -y, 3 -x."""

    def __init__(self, cv, o):
        self.cv = cv
        self.o = o
        self.S = cv.size

    def pt(self, s, f):
        S = self.S
        o = self.o
        if o == 0:
            return s, S - f
        if o == 1:
            return S - f, S - s
        if o == 2:
            return S - s, f
        return f, s

    def rect(self, s0, f0, s1, f1):
        xa, ya = self.pt(s0, f0)
        xb, yb = self.pt(s1, f1)
        return min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb)

    def sides(self):
        """Which building side is seen on the +y face and on the +x face."""
        return {0: ("front", "right"), 1: ("left", "front"), 2: ("back", "left"), 3: ("right", "back")}[self.o]

    def axis(self, a):
        """World axis for a front-relative axis: 's' runs across the front, 'f' front to back."""
        if self.o in (0, 2):
            return "x" if a == "s" else "y"
        return "y" if a == "s" else "x"

    def box(self, s0, f0, s1, f1, z0, z1, front=None, back=None, left=None, right=None, top=None, all=None):
        x0, y0, x1, y1 = self.rect(s0, f0, s1, f1)
        walls = {"front": front or all, "back": back or all or front, "left": left or all or right, "right": right or all or left}
        ny, nx = self.sides()
        fy = walls[ny] or flat("cccccc")
        fx = walls[nx] or flat("cccccc")
        self.cv.face_y(y1, x0, x1, z0, z1, fy)
        self.cv.face_x(x1, y0, y1, z0, z1, _flip_u(fx))
        self.cv.top(z1, x0, y0, x1, y1, top or flat("8a8a8a"))

    def gable(self, s0, f0, s1, f1, z, rh, roof, walls, ridge="s", o=4.0):
        """Pitched roof with the ridge along `ridge`; walls: facades by side for the gable end
        (a single facade is used for every side)."""
        x0, y0, x1, y1 = self.rect(s0, f0, s1, f1)
        ax = self.axis(ridge)
        if callable(walls):
            end = walls
        else:
            side = self.sides()[1] if ax == "x" else self.sides()[0]
            end = walls.get(side) or walls.get("all") or flat("cccccc")
        self.cv.gable(x0, y0, x1, y1, z, rh, roof, _flip_u(end) if ax == "x" else end, ax, o)

    def hip(self, s0, f0, s1, f1, z, rh, roof, o=4.0):
        x0, y0, x1, y1 = self.rect(s0, f0, s1, f1)
        self.cv.hip(x0, y0, x1, y1, z, rh, roof, o)

    def panel(self, a0, a1, b, z0, z1, fn, along="s", extra=None):
        """A vertical panel spanning a0..a1 along `along` at the other coordinate b.
        fn(u, v, L, H) and extra(u, v) use u measured from a0."""
        p0 = self.pt(a0, b) if along == "s" else self.pt(b, a0)
        p1 = self.pt(a1, b) if along == "s" else self.pt(b, a1)
        L = abs(a1 - a0)
        if abs(p0[1] - p1[1]) < 1e-6:
            y = p0[1]
            x0, x1 = min(p0[0], p1[0]), max(p0[0], p1[0])
            rev = p0[0] > p1[0]
            loc = (lambda w: x1 - w) if rev else (lambda w: w - x0)
            ex = (lambda wx, wz: extra(loc(wx), wz - z0)) if extra else None
            self.cv.face_y(y, x0, x1, z0, z1, lambda u, v, LL, H: fn(L - u if rev else u, v, L, H), extra=ex)
        else:
            x = p0[0]
            y0, y1 = min(p0[1], p1[1]), max(p0[1], p1[1])
            rev = p0[1] > p1[1]
            loc = (lambda w: y1 - w) if rev else (lambda w: w - y0)
            ex = (lambda wy, wz: extra(loc(wy), wz - z0)) if extra else None
            self.cv.face_x(x, y0, y1, z0, z1, lambda u, v, LL, H: fn(L - u if rev else u, v, L, H), extra=ex)

    def flat(self, s0, f0, s1, f1, z, fn, ground=False):
        """A horizontal surface (fn(u, v, L, D) in world-aligned u/v)."""
        x0, y0, x1, y1 = self.rect(s0, f0, s1, f1)
        if ground:
            with self.cv.ground:
                self.cv.top(z, x0, y0, x1, y1, fn, shade=1.0)
        else:
            self.cv.top(z, x0, y0, x1, y1, fn)

    def mark(self, name, s, f, z):
        x, y = self.pt(s, f)
        self.cv.mark(name, x, y, z)

    def grid(self, s, f):
        """Grid offset (in tiles) of a front-relative point."""
        x, y = self.pt(s, f)
        return [round(x / U, 4), round(y / U, 4)]


def _flip_u(fn):
    def g(u, v, L, H):
        return fn(L - u, v, L, H)
    if hasattr(fn, "doors"):
        g.doors = fn.doors
    return g


# gable and hip on the canvas (world axes)
def _gable(cv, x0, y0, x1, y1, z, rh, roof, wall, axis="x", o=4.0):
    if axis == "x":
        ym, half = (y0 + y1) / 2, (y1 - y0) / 2
        k = rh / half
        zb = z - k * o
        cv.plane(z + rh + k * ym, 0, -k, (x0 - o, ym, zb, x1 + o, y1 + o, z + rh),
                 lambda wx, wy: (wx >= x0 - o) & (wx < x1 + o) & (wy >= ym) & (wy < y1 + o),
                 lambda wx, wy, wz: roof(wx - x0, np.abs(wy - ym), half + o))
        cv.plane(z + rh - k * ym, 0, k, (x0 - o, y0 - o, zb, x1 + o, ym, z + rh),
                 lambda wx, wy: (wx >= x0 - o) & (wx < x1 + o) & (wy >= y0 - o) & (wy < ym),
                 lambda wx, wy, wz: roof(wx - x0, np.abs(wy - ym), half + o))
        cv.face_x(x1, y0, y1, z, z + rh, wall,
                  extra=lambda wy, wz: (wz - z) <= rh * (1 - np.abs(wy - ym) / half))
        # thickness of the roof at the gable end
        cv.face_x(x1 + o, y0 - o, y1 + o, zb, z + rh + 1.5, flat("5a4a40"),
                  extra=lambda wy, wz: (np.abs(wz - (z + rh - k * np.abs(wy - ym))) < 1.6))
    else:
        xm, half = (x0 + x1) / 2, (x1 - x0) / 2
        k = rh / half
        zb = z - k * o
        cv.plane(z + rh + k * xm, -k, 0, (xm, y0 - o, zb, x1 + o, y1 + o, z + rh),
                 lambda wx, wy: (wy >= y0 - o) & (wy < y1 + o) & (wx >= xm) & (wx < x1 + o),
                 lambda wx, wy, wz: roof(wy - y0, np.abs(wx - xm), half + o))
        cv.plane(z + rh - k * xm, k, 0, (x0 - o, y0 - o, zb, xm, y1 + o, z + rh),
                 lambda wx, wy: (wy >= y0 - o) & (wy < y1 + o) & (wx >= x0 - o) & (wx < xm),
                 lambda wx, wy, wz: roof(wy - y0, np.abs(wx - xm), half + o))
        cv.face_y(y1, x0, x1, z, z + rh, wall,
                  extra=lambda wx, wz: (wz - z) <= rh * (1 - np.abs(wx - xm) / half))
        cv.face_y(y1 + o, x0 - o, x1 + o, zb, z + rh + 1.5, flat("5a4a40"),
                  extra=lambda wx, wz: (np.abs(wz - (z + rh - k * np.abs(wx - xm))) < 1.6))


def _hip(cv, x0, y0, x1, y1, z, rh, roof, o=4.0):
    xa, ya, xb, yb = x0 - o, y0 - o, x1 + o, y1 + o
    w, h = int(xb - xa) + 1, int(yb - ya) + 1
    ys, xs = np.mgrid[0:h, 0:w] + 0.5
    xm, ym = (xb - xa) / 2, (yb - ya) / 2
    k = rh / min(xm - o, ym - o) if min(xm - o, ym - o) > 0 else 1
    H = z - k * o + k * np.minimum(xm - np.abs(xs - xm), ym - np.abs(ys - ym))
    H = np.minimum(H, z + rh)
    cv.heightfield(xa, ya, H, lambda wx, wy, wz, nx, ny, nz: roof(wx - x0 + (wy - y0) * 0.37, (z + rh - wz) * 1.3, rh * 1.3 + o * 1.3),
                   zmin=z - k * o - 1, thick=3.0)


Canvas.gable = _gable
Canvas.hip = _hip
