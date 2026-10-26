"""Small isometric rasteriser used to draw every Pixelburg sprite.

World units: 10 units = 1 metre, one tile is U = 160 units (16 m) on x and y.
Screen: sx = wx - wy, sy = (wx + wy) / 2 - wz.

Every primitive writes colour, depth (wx + wy + wz, bigger = closer) and an emission
layer (shop windows, signs, lamps) plus a "rooms" layer: four channels of window light
that the game switches on and off per household. Primitives drawn while `cv.ground` is
active go to a separate ground layer (lawns, paths, parking lots) that the game draws
under everything else, so people can walk over it. A height map of the body is kept to
cast soft shadows on the ground.
"""
import math

import numpy as np
from PIL import Image
from scipy import ndimage

U = 160
M = 10.0  # units per metre

LIGHT = np.array([-0.35, 0.5, 0.8])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
AMB, DIF = 0.62, 0.46
SUN_RISE = LIGHT[2] / math.hypot(LIGHT[0], LIGHT[1])     # height gained per unit towards the sun
SUN_DIR = np.array([LIGHT[0], LIGHT[1]]) / math.hypot(LIGHT[0], LIGHT[1])


def shade_n(nx, ny, nz):
    return AMB + DIF * np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0.0, 1.0)


SH_X = float(shade_n(1, 0, 0))
SH_Y = float(shade_n(0, 1, 0))
SH_TOP = float(shade_n(0, 0, 1))


def C(h):
    if not isinstance(h, str):
        return np.asarray(h, float)
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def hash2(a, b, seed=0):
    a = np.asarray(a).astype(np.int64)
    b = np.asarray(b).astype(np.int64)
    v = (a * 73856093) ^ (b * 19349663) ^ (seed * 83492791)
    v = (v ^ (v >> 13)) * 1274126177
    return ((v ^ (v >> 16)) & 0xFFFF) / 65536.0


def _h3(ix, iy, iz, seed):
    v = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    v = (v ^ (v >> 13)) * 1274126177
    return ((v ^ (v >> 16)) & 0xFFFF) / 65536.0


def noise3(x, y, z, seed=0):
    """Smooth 3D value noise in [0,1] for arrays of world positions."""
    xi, yi, zi = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64), np.floor(z).astype(np.int64)
    fx, fy, fz = x - xi, y - yi, z - zi
    fx, fy, fz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                out = out + w * _h3(xi + dx, yi + dy, zi + dz, seed)
    return out


def value_noise(w, h, scale, seed=0, octaves=4):
    """Fractal value noise in [0,1], shape (h, w)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, total = 1.0, 0.0
    for o in range(octaves):
        s = max(1, int(scale / (2 ** o)))
        gw, gh = w // s + 2, h // s + 2
        g = rng.random((gh, gw))
        ys, xs = np.mgrid[0:h, 0:w] / s
        x0, y0 = xs.astype(int), ys.astype(int)
        fx, fy = xs - x0, ys - y0
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
        b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
        out += (a * (1 - fy) + b * fy) * amp
        total += amp
        amp *= 0.5
    return out / total


def nores(shape):
    return np.zeros(shape, bool)


def solid_res(col, shape):
    return np.broadcast_to(C(col), shape + (3,)).copy(), nores(shape), None


def flat(col, noise=4.0, seed=1, scale=1.0):
    col = C(col)

    def fn(u, v, *_):
        n = (hash2(np.floor(u / scale), np.floor(v / scale), seed) - 0.5) * noise
        return col + n[..., None], np.zeros(u.shape, bool), None
    return fn


def flat3(col, noise=4.0, seed=1):
    """Same as flat but for (wx, wy, wz, ...) callbacks."""
    f = flat(col, noise, seed)
    return lambda wx, wy, wz, *rest: f(wx + wz, wy)


def glow_res(col, shape, alpha=255):
    c = C(col)
    em = np.zeros(shape + (4,))
    em[...] = np.append(c, alpha)
    return np.broadcast_to(c, shape + (3,)).copy(), np.ones(shape, bool), em


class Layer:
    def __init__(self, H, W):
        self.rgb = np.zeros((H, W, 3))
        self.a = np.zeros((H, W), bool)
        self.depth = np.full((H, W), -1e9)
        self.emit = np.zeros((H, W, 4))
        self.rooms = np.zeros((H, W, 4))


class Canvas:
    def __init__(self, n, zmax, pad=40, extra_w=0):
        self.n = n
        self.size = n * U
        self.pad = pad
        self.W = 2 * self.size + 2 * pad + 2 * extra_w
        self.ox = self.size + pad + extra_w
        self.top_m = int(math.ceil(zmax)) + pad
        self.H = self.top_m + self.size + pad
        self.oy = self.top_m
        self.body = Layer(self.H, self.W)
        self.base = Layer(self.H, self.W)
        self.cur = self.body
        self.points = {}
        # height map of the body for shadows, 1 unit per cell, with a margin around the lot
        self.hm_m = 60
        hs = self.size + 2 * self.hm_m
        self.hm = np.full((hs, hs), -np.inf)
        self.room_group = None   # current rooms channel for window light (0..3) or None
        self.no_ao = False

    # ------------------------------------------------------------------ layers
    class _Ground:
        def __init__(self, cv):
            self.cv = cv

        def __enter__(self):
            self.cv.cur = self.cv.base

        def __exit__(self, *a):
            self.cv.cur = self.cv.body

    @property
    def ground(self):
        return Canvas._Ground(self)

    # aliases used by older helpers
    @property
    def rgb(self):
        return self.body.rgb

    @property
    def a(self):
        return self.body.a

    # ------------------------------------------------------------------ core
    def screen(self, wx, wy, wz=0.0):
        return (self.ox + wx - wy, self.oy + (wx + wy) / 2 - wz)

    def region(self, x0, y0, z0, x1, y1, z1):
        sx0, sx1 = x0 - y1, x1 - y0
        sy0, sy1 = (x0 + y0) / 2 - z1, (x1 + y1) / 2 - z0
        c0 = max(0, int(math.floor(sx0 + self.ox)) - 1)
        c1 = min(self.W, int(math.ceil(sx1 + self.ox)) + 1)
        r0 = max(0, int(math.floor(sy0 + self.oy)) - 1)
        r1 = min(self.H, int(math.ceil(sy1 + self.oy)) + 1)
        if c0 >= c1 or r0 >= r1:
            return None
        ys, xs = np.mgrid[r0:r1, c0:c1]
        return (slice(r0, r1), slice(c0, c1), xs + 0.5 - self.ox, ys + 0.5 - self.oy)

    def put(self, reg, mask, depth, res, shade, world=None):
        rgb, ns = res[0], res[1]
        em = res[2] if len(res) > 2 else None
        rooms = res[3] if len(res) > 3 else None
        L = self.cur
        rs, cs = reg[0], reg[1]
        D = L.depth[rs, cs]
        m = mask & (depth > D)
        if not m.any():
            return
        sh = shade if np.isscalar(shade) else shade[..., None]
        if world is not None and L is self.body and not self.no_ao:
            wz = world[2]
            ao = 0.72 + 0.28 * np.clip(np.asarray(wz) / 9.0, 0, 1)
            sh = sh * (ao[..., None] if np.ndim(ao) else ao)
        out = np.where(ns[..., None], rgb, rgb * sh)
        L.rgb[rs, cs][m] = np.clip(out[m], 0, 255)
        L.a[rs, cs][m] = True
        D[m] = depth[m]
        E = L.emit[rs, cs]
        E[m] = em[m] if em is not None else 0
        R = L.rooms[rs, cs]
        R[m] = rooms[m] if rooms is not None else 0
        if world is not None and L is self.body:
            wx, wy, wz = (np.broadcast_to(np.asarray(w, float), m.shape) for w in world)
            ix = np.floor(wx[m]).astype(int) + self.hm_m
            iy = np.floor(wy[m]).astype(int) + self.hm_m
            ok = (ix >= 0) & (iy >= 0) & (ix < self.hm.shape[1]) & (iy < self.hm.shape[0])
            np.maximum.at(self.hm, (iy[ok], ix[ok]), wz[m][ok])

    # ------------------------------------------------------------------ primitives
    def face_x(self, x, y0, y1, z0, z1, fn, extra=None, shade=SH_X):
        reg = self.region(x, y0, z0, x, y1, z1)
        if reg is None:
            return
        sx, sy = reg[2], reg[3]
        wy = x - sx
        wz = (x + wy) / 2 - sy
        m = (wy >= y0) & (wy < y1) & (wz >= z0) & (wz < z1)
        if extra is not None:
            m &= extra(wy, wz)
        self.put(reg, m, x + wy + wz, fn(wy - y0, wz - z0, y1 - y0, z1 - z0), shade, (x, wy, wz))

    def face_y(self, y, x0, x1, z0, z1, fn, extra=None, shade=SH_Y):
        reg = self.region(x0, y, z0, x1, y, z1)
        if reg is None:
            return
        sx, sy = reg[2], reg[3]
        wx = sx + y
        wz = (wx + y) / 2 - sy
        m = (wx >= x0) & (wx < x1) & (wz >= z0) & (wz < z1)
        if extra is not None:
            m &= extra(wx, wz)
        self.put(reg, m, wx + y + wz, fn(wx - x0, wz - z0, x1 - x0, z1 - z0), shade, (wx, y, wz))

    def plane(self, A, bx, by, bounds, region, fn, shade=None):
        """Plane wz = A + bx*wx + by*wy, inside region(wx, wy). bounds = (x0,y0,z0,x1,y1,z1)."""
        if abs(1 - bx - by) < 1e-3:
            return  # seen edge-on
        reg = self.region(*bounds)
        if reg is None:
            return
        sx, sy = reg[2], reg[3]
        wy = (sy - sx / 2 + A + bx * sx) / (1 - bx - by)
        wx = sx + wy
        wz = A + bx * wx + by * wy
        m = region(wx, wy) & (wz >= bounds[2] - 0.01) & (wz <= bounds[5] + 0.01)
        if shade is None:
            nrm = np.array([-bx, -by, 1.0])
            nrm /= np.linalg.norm(nrm)
            shade = float(shade_n(*nrm))
        self.put(reg, m, wx + wy + wz, fn(wx, wy, wz), shade, (wx, wy, wz))

    def top(self, z, x0, y0, x1, y1, fn, shade=SH_TOP, extra=None):
        def region(wx, wy):
            m = (wx >= x0) & (wx < x1) & (wy >= y0) & (wy < y1)
            return m & extra(wx - x0, wy - y0) if extra is not None else m
        self.plane(z, 0, 0, (x0, y0, z, x1, y1, z), region,
                   lambda wx, wy, wz: fn(wx - x0, wy - y0, x1 - x0, y1 - y0), shade)

    def box(self, x0, y0, z0, x1, y1, z1, left, right=None, top=None):
        right = right or left
        top = top or flat("8a8a8a")
        self.face_y(y1, x0, x1, z0, z1, left)
        self.face_x(x1, y0, y1, z0, z1, right)
        self.top(z1, x0, y0, x1, y1, top)

    def ground_fill(self, fn, x0=0, y0=0, x1=None, y1=None, z=0.0):
        x1 = self.size if x1 is None else x1
        y1 = self.size if y1 is None else y1
        with self.ground:
            self.top(z, x0, y0, x1, y1, fn, shade=1.0)

    def heightfield(self, x0, y0, H, fn, zmin=0.0, step=0.5, thick=np.inf, floor=-np.inf, bottom=None):
        """H[iy, ix] = surface height at (x0 + ix, y0 + iy); -inf where empty.
        The solid reaches down `thick` units, to `floor`, or to the `bottom` array."""
        h, w = H.shape
        x1, y1 = x0 + w, y0 + h
        zmax = float(np.nanmax(np.where(np.isfinite(H), H, -1e9)))
        reg = self.region(x0, y0, zmin, x1, y1, zmax)
        if reg is None:
            return
        sx, sy = reg[2], reg[3]
        hit = np.full(sx.shape, np.nan)
        s = x1 + y1
        lo = x0 + y0
        while s >= lo:
            wx = (s + sx) / 2
            wy = (s - sx) / 2
            ix = np.floor(wx - x0).astype(int)
            iy = np.floor(wy - y0).astype(int)
            ok = (ix >= 0) & (iy >= 0) & (ix < w) & (iy < h) & np.isnan(hit)
            if ok.any():
                hh = np.full(sx.shape, -np.inf)
                hh[ok] = H[iy[ok], ix[ok]]
                wz_ = s / 2 - sy
                inside = ok & (wz_ <= hh) & (wz_ >= hh - thick) & (wz_ >= floor)
                if bottom is not None:
                    bb = np.full(sx.shape, np.inf)
                    bb[ok] = bottom[iy[ok], ix[ok]]
                    inside &= wz_ >= bb
                hit[inside] = s
            s -= step
        m = ~np.isnan(hit)
        if not m.any():
            return
        sh = np.where(m, hit, 0)
        wx = (sh + sx) / 2
        wy = (sh - sx) / 2
        wz = sh / 2 - sy
        Hf = np.where(np.isfinite(H), H, zmin - 50)
        gy, gx = np.gradient(Hf)
        ix = np.clip(np.floor(wx - x0).astype(int), 0, w - 1)
        iy = np.clip(np.floor(wy - y0).astype(int), 0, h - 1)
        nx, ny = -gx[iy, ix], -gy[iy, ix]
        nz = np.ones(sx.shape)
        ln = np.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny, nz = nx / ln, ny / ln, nz / ln
        res = fn(wx, wy, wz, nx, ny, nz)
        self.put(reg, m, sh + wz, res, shade_n(nx, ny, nz), (wx, wy, wz))

    def ellipsoid(self, cx, cy, cz, rx, ry, rz, fn, cut_z=None):
        reg = self.region(cx - rx, cy - ry, cz - rz, cx + rx, cy + ry, cz + rz)
        if reg is None:
            return
        sx, sy = reg[2], reg[3]
        ks = (sx / 2 - cx, -sx / 2 - cy, -sy - cz)
        rs = (rx, ry, rz)
        A = sum(1 / r ** 2 for r in rs)
        B = 2 * sum(k / r ** 2 for k, r in zip(ks, rs))
        Cc = sum(k * k / r ** 2 for k, r in zip(ks, rs)) - 1
        disc = B * B - 4 * A * Cc
        m = disc >= 0
        u = (-B + np.sqrt(np.where(m, disc, 0))) / (2 * A)
        qx, qy, qz = ks[0] + u, ks[1] + u, ks[2] + u
        if cut_z is not None:
            m &= (qz + cz) >= cut_z
        nx, ny, nz = qx / rx ** 2, qy / ry ** 2, qz / rz ** 2
        ln = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
        nx, ny, nz = nx / ln, ny / ln, nz / ln
        wx, wy, wz = qx + cx, qy + cy, qz + cz
        res = fn(wx, wy, wz, nx, ny, nz)
        self.put(reg, m, 2 * u + wz, res, shade_n(nx, ny, nz), (wx, wy, wz))

    def cylinder(self, cx, cy, r, z0, z1, side, cap=None):
        reg = self.region(cx - r, cy - r, z0, cx + r, cy + r, z1)
        if reg is None:
            return
        sx, sy = reg[2], reg[3]
        a, b = sx / 2 - cx, -sx / 2 - cy
        disc = (a + b) ** 2 - 2 * (a * a + b * b - r * r)
        m = disc >= 0
        u = (-(a + b) + np.sqrt(np.where(m, disc, 0))) / 2
        wz = u - sy
        side_m = m & (wz >= z0) & (wz <= z1)
        px, py = a + u, b + u
        nx, ny = px / r, py / r
        ang = np.arctan2(py, px)
        res = side(ang, wz - z0, nx, ny)
        self.put(reg, side_m, 2 * u + wz, res, shade_n(nx, ny, 0), (px + cx, py + cy, wz))
        if cap is not None:
            uc = z1 + sy
            cx_, cy_ = a + uc, b + uc
            cm = (cx_ * cx_ + cy_ * cy_ <= r * r)
            self.put(reg, cm, 2 * uc + z1, cap(cx_, cy_), SH_TOP, (cx_ + cx, cy_ + cy, z1))

    def mark(self, name, wx, wy, wz):
        self.points[name] = self.screen(wx, wy, wz)

    # ------------------------------------------------------------------ output
    @staticmethod
    def _outline(rgb, a, width=1, strength=0.4):
        rgb = rgb.copy()
        a = a.copy()
        for _ in range(width):
            pad = np.pad(a, 1)
            neigh = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
            edge = (~a) & neigh
            src = np.pad(rgb, ((1, 1), (1, 1), (0, 0)))
            acc = np.zeros_like(rgb)
            cnt = np.zeros(a.shape)
            for dy, dx in ((0, 1), (2, 1), (1, 0), (1, 2)):
                na = pad[dy:dy + a.shape[0], dx:dx + a.shape[1]]
                acc += src[dy:dy + a.shape[0], dx:dx + a.shape[1]] * na[..., None]
                cnt += na
            col = acc / np.maximum(cnt, 1)[..., None] * strength + np.array([22, 18, 30]) * (1 - strength)
            rgb[edge] = col[edge]
            a = a | edge
        return rgb, a

    def image(self, outline=True):
        rgb, a = self.body.rgb, self.body.a
        if outline:
            rgb, a = self._outline(rgb, a, 1, 0.45)
        out = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
        return Image.fromarray(out, "RGBA").copy()

    def base_image(self):
        L = self.base
        out = np.dstack([np.clip(L.rgb, 0, 255), L.a * 255]).astype(np.uint8)
        return Image.fromarray(out, "RGBA").copy()

    def emission_image(self, layer=None):
        L = layer or self.body
        e = np.clip(L.emit, 0, 255).astype(np.uint8)
        return Image.fromarray(e, "RGBA").copy()

    def rooms_image(self):
        r = np.clip(self.body.rooms, 0, 255).astype(np.uint8)
        return Image.fromarray(r, "RGBA").copy()

    def shadow_image(self, strength=0.42):
        """Soft shadow the body casts on the ground, as an alpha mask in canvas space.
        Returns (image, (x offset, y offset)) since the shadow can reach past the canvas."""
        hm = self.hm
        if not np.isfinite(hm).any():
            return None, (0, 0)
        hmax = float(np.max(hm[np.isfinite(hm)]))
        reach = int(hmax / SUN_RISE) + 4
        m0 = self.hm_m
        size = hm.shape[0]
        # ground grid: the lot plus its margin, stretched the way the shadows fall (away from the sun)
        gx0 = -m0 - int(reach * max(0.0, SUN_DIR[0]))
        gx1 = size - m0 + int(reach * max(0.0, -SUN_DIR[0])) + 1
        gy0 = -m0 - int(reach * max(0.0, SUN_DIR[1]))
        gy1 = size - m0 + int(reach * max(0.0, -SUN_DIR[1])) + 1
        ys, xs = np.mgrid[gy0:gy1, gx0:gx1].astype(float) + 0.5
        shadow = np.zeros(xs.shape)
        hmf = np.where(np.isfinite(hm), hm, -1e9)
        steps = max(8, min(90, reach // 3))
        for i in range(1, steps + 1):
            t = reach * i / steps
            px = xs + SUN_DIR[0] * t
            py = ys + SUN_DIR[1] * t
            ix = np.floor(px).astype(int) + m0
            iy = np.floor(py).astype(int) + m0
            ok = (ix >= 0) & (iy >= 0) & (ix < size) & (iy < size)
            h = np.full(xs.shape, -1e9)
            h[ok] = hmf[iy[ok], ix[ok]]
            shadow = np.maximum(shadow, (h > t * SUN_RISE + 0.5).astype(float))
        shadow = ndimage.gaussian_filter(shadow, 1.6)
        # project the ground grid to the screen: sx = wx - wy, sy = (wx + wy) / 2
        sx0 = gx0 - (gy1 - 1)
        sx1 = (gx1 - 1) - gy0
        sy0 = (gx0 + gy0) / 2
        sy1 = (gx1 + gy1) / 2
        W = int(sx1 - sx0) + 2
        H = int(sy1 - sy0) + 2
        yy, xx = np.mgrid[0:H, 0:W].astype(float)
        sxs = xx + sx0 + 0.5
        sys_ = yy + sy0 + 0.5
        wx = sys_ + sxs / 2
        wy = sys_ - sxs / 2
        ix = np.floor(wx - gx0).astype(int)
        iy = np.floor(wy - gy0).astype(int)
        ok = (ix >= 0) & (iy >= 0) & (ix < shadow.shape[1]) & (iy < shadow.shape[0])
        out = np.zeros((H, W))
        out[ok] = shadow[iy[ok], ix[ok]]
        alpha = np.clip(out * strength * 255, 0, 255).astype(np.uint8)
        img = np.zeros((H, W, 4), np.uint8)
        img[..., 0] = 14
        img[..., 1] = 16
        img[..., 2] = 38
        img[..., 3] = alpha
        # canvas pixel of screen origin: ox + sx, oy + sy
        return Image.fromarray(img, "RGBA"), (self.ox + sx0, self.oy + sy0)
