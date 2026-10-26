"""Cars, people, traffic lights, animals and small world sprites."""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw

from raster import C, Canvas, flat, hash2
from props import nores, solid_res
import animals
import fx
import people

HEAD = np.array([255, 246, 210, 255.0])
TAIL = np.array([255, 50, 40, 255.0])
GLASS = C("2c3e56")
GLASS_HI = C("7aa0c8")

CAR_KINDS = {
    # kind: (length, width, body_h, cabin (a0, a1), cabin_h, colours)
    "sedan": (34, 16, 9, (10, 25), 7, ["d84a3a", "3a7ad8", "f0f0f0", "2a2a30", "4ab06a", "8a4ad0"]),
    "hatch": (28, 15, 9, (6, 21), 8, ["f08a2a", "6ac0e0", "e8e0c8", "c8304a"]),
    "taxi": (34, 16, 9, (10, 25), 7, ["f0c030"]),
    "van": (36, 17, 18, None, 0, ["f4f4f4", "4a6a9a"]),
    "pickup": (36, 17, 10, (14, 26), 8, ["5a7a4a", "a83a2a"]),
    "bus": (58, 18, 24, None, 0, ["e8b830", "d84a3a"]),
    "truck": (52, 18, 24, None, 0, ["3a6ad0"]),
    "sports": (34, 16, 7, (12, 24), 5, ["e83a2a", "f0c030", "2a2a32"]),
    "police": (34, 16, 9, (10, 25), 7, ["f4f4f4"]),
    "ambulance": (40, 18, 20, None, 0, ["f4f4f4"]),
    "fire": (56, 18, 22, None, 0, ["d8302a"]),
    "garbage": (48, 18, 22, None, 0, ["4a9a4a"]),
}
SIREN_KINDS = ("police", "ambulance", "fire")


def _res(rgb, em=None):
    return rgb, nores(rgb.shape[:2]), em


def car_body(cv, x, y, direction, col, kind="sedan", siren=None, headlights=True):
    """siren: None, "A" (red half lit) or "B" (blue half lit); headlights=False hides lamp emission."""
    length, wid, bh, cab, ch, _ = CAR_KINDS[kind]
    along_x = direction in ("px", "nx")
    forward = direction in ("px", "py")
    body = C(col)

    def to_world(a0, a1, b0, b1):
        if forward:
            A0, A1 = a0 - length / 2, a1 - length / 2
        else:
            A0, A1 = length / 2 - a1, length / 2 - a0
        B0, B1 = b0 - wid / 2, b1 - wid / 2
        if along_x:
            return x + A0, y + B0, x + A1, y + B1
        return x + B0, y + A0, x + B1, y + A1

    def side_fn(base, kindpart, a0, a1):
        def fn(u, v, L, H):
            a = (u if forward else (L - u)) + a0
            rgb = np.broadcast_to(base, u.shape + (3,)).copy()
            rgb *= (0.9 + 0.12 * np.clip(v / max(H, 1), 0, 1))[..., None]
            em = np.zeros(u.shape + (4,))
            if kindpart == "body":
                rgb[np.floor(v) <= 1] = base * 0.45
                rgb[np.floor(v) == np.floor(H) - 1] = base * 1.15
                for wa in (7.0, length - 8.0):
                    d = np.hypot(a - wa, v - 2.5)
                    rgb[d < 4.3] = C("1c1c22")
                    rgb[d < 2.0] = C("a8acb4")
                    rgb[(d >= 4.3) & (d < 5.3) & (v > 2.5)] = base * 0.55
                seam = (np.abs(a - (cab[0] + cab[1]) / 2) < 0.5) if cab else np.zeros(u.shape, bool)
                rgb[seam & (v > 3)] *= 0.75
                if kind == "taxi":
                    chk = (np.floor(v) == np.floor(H) - 3) & ((np.floor(a / 2) % 2) == 0)
                    rgb[chk] = C("2a2a2a")
                if kind in ("bus", "van", "truck"):
                    # windows band
                    win_lo, win_hi = (12, 20) if kind == "bus" else (10, 16)
                    if kind == "truck":
                        wmask = (a > length - 11) & (a < length - 3) & (v > 11) & (v < 18)
                    elif kind == "van":
                        wmask = (a > length - 16) & (a < length - 3) & (v > win_lo) & (v < win_hi)
                    else:
                        wmask = (a > 3) & (a < length - 4) & (v > win_lo) & (v < win_hi) & ((np.floor(a) % 9) != 0)
                    t = np.clip((v - win_lo) / 8, 0, 1)
                    g = GLASS * (1 - t[..., None]) + GLASS_HI * t[..., None]
                    rgb[wmask] = g[wmask]
                    if kind == "bus" and headlights:
                        em[wmask] = (255, 236, 180, 200)
                        rgb[(v > 4) & (v < 6)] = C("f4f4f4")
                    if kind == "truck":
                        box = a < length - 13
                        rgb[box] = C("ececec")
                        rgb[box & (np.floor(v) % 6 == 0)] = C("c8c8c8")
                        rgb[box & (v > 8) & (v < 11)] = base
                if kind == "police":
                    rgb[(v > 3.5) & (v < 6.5) & (a > 4) & (a < length - 4)] = C("2a4ab8")
                    rgb[(v > 4.2) & (v < 5.8) & (np.abs(a - length / 2) < 3)] = C("f4f4f4")
                if kind == "sports":
                    rgb[(np.floor(v) == 3) & (a > 3) & (a < length - 3)] = C("f8f8f8") if col != "f0c030" else C("2a2a2a")
                if kind in ("ambulance", "fire", "garbage"):
                    win_lo = 11
                    wmask = (a > length - 12) & (a < length - 3) & (v > win_lo) & (v < H - 3)
                    t = np.clip((v - win_lo) / 8, 0, 1)
                    g = GLASS * (1 - t[..., None]) + GLASS_HI * t[..., None]
                    rgb[wmask] = g[wmask]
                    if kind == "ambulance":
                        rgb[(v > 6) & (v < 9) & (a < length - 13)] = C("d8302a")
                        cx_ = length / 2 - 4
                        cross = ((np.abs(a - cx_) < 1.2) & (np.abs(v - 14) < 4)) | ((np.abs(a - cx_) < 4) & (np.abs(v - 14) < 1.2))
                        rgb[cross] = C("d8302a")
                    elif kind == "fire":
                        rgb[(v > 5) & (v < 7)] = C("f0e8d0")
                        rgb[(a < length - 13) & (v > 9) & ((np.floor(a) % 7) == 0)] = C("a8201a")
                    else:
                        box = a < length - 13
                        rgb[box & ((np.floor(a) % 5) == 0)] = base * 0.75
                        rgb[box & (v > 12) & (v < 15)] = C("f0f0e8")
            else:  # cabin
                gl = (v > 1) & (v < ch - 1.2) & (a > a0 + 1.5) & (a < a1 - 1.5) & (np.abs(a - (a0 + a1) / 2) > 0.8)
                t = np.clip(v / max(ch, 1), 0, 1)
                g = GLASS * (1 - t[..., None]) + GLASS_HI * t[..., None]
                rgb[gl] = g[gl]
            return rgb, nores(u.shape), em
        return fn

    def end_fn(base, front_face, part):
        def fn(u, v, L, H):
            rgb = np.broadcast_to(base, u.shape + (3,)).copy()
            em = np.zeros(u.shape + (4,))
            if part == "body":
                rgb[np.floor(v) <= 1] = base * 0.4
                lights = ((u < 3.5) | (u > L - 3.5)) & (v > H - 5) & (v < H - 2)
                if front_face:
                    rgb[(u > 4) & (u < L - 4) & (v > 2.5) & (v < H - 3)] = C("2a2a30")
                    rgb[lights] = C("fff4d0")
                    if headlights:
                        em[lights] = HEAD
                else:
                    rgb[lights] = C("e83a2a")
                    if headlights:
                        em[lights] = TAIL
                rgb[(np.floor(v) == 2)] = C("4a4a52")
                if kind in ("bus", "van", "truck", "ambulance", "fire", "garbage") and front_face:
                    ws = (u > 1.5) & (u < L - 1.5) & (v > H - 11) & (v < H - 2.5)
                    t = np.clip((v - (H - 11)) / 9, 0, 1)
                    g = GLASS * (1 - t[..., None]) + GLASS_HI * t[..., None]
                    rgb[ws] = g[ws]
                    lights2 = ((u < 3.5) | (u > L - 3.5)) & (v > 4) & (v < 7)
                    rgb[lights2] = C("fff4d0")
                    em[lights2] = HEAD if headlights else 0
                    em[ws] = 0
            else:
                ws = (u > 1) & (u < L - 1) & (v > 1) & (v < H - 1)
                t = np.clip(v / max(H, 1), 0, 1)
                g = GLASS * (1 - t[..., None]) + GLASS_HI * t[..., None]
                rgb[ws] = g[ws]
            return rgb, nores(u.shape), em
        return fn

    def roof_fn(base):
        def fn(u, v, L, D):
            rgb = np.broadcast_to(base * 1.12, u.shape + (3,)).copy()
            rgb[(u < 1) | (v < 1) | (u > L - 1) | (v > D - 1)] = base * 0.9
            return rgb, nores(u.shape), None
        return fn

    def draw_box(a0, a1, b0, b1, z0, z1, part, roof=None):
        x0, y0, x1, y1 = to_world(a0, a1, b0, b1)
        side = side_fn(body, part, a0, a1)
        visible_end_is_front = forward
        end = end_fn(body, visible_end_is_front, part)
        if along_x:
            cv.box(x0, y0, z0, x1, y1, z1, side, end, roof or roof_fn(body))
        else:
            cv.box(x0, y0, z0, x1, y1, z1, end, side, roof or roof_fn(body))

    # shadow under the car
    sx0, sy0, sx1, sy1 = to_world(-1, length + 1, -1, wid + 1)
    cv.top(0.3, sx0, sy0, sx1, sy1, lambda u, v, L, D: solid_res(C("2a2a34"), u.shape), shade=0.55)
    draw_box(0, length, 0, wid, 1.5, 1.5 + bh, "body")
    if cab:
        draw_box(cab[0], cab[1], 1.5, wid - 1.5, 1.5 + bh, 1.5 + bh + ch, "cabin")
    if kind == "taxi":
        lamp = lambda u, v, L, H: (np.broadcast_to(C("fff4a0"), u.shape + (3,)).copy(), np.ones(u.shape, bool),
                                   np.broadcast_to(np.array([255, 240, 150, 255.0 if headlights else 0.0]), u.shape + (4,)).copy())
        a = (cab[0] + cab[1]) / 2
        x0, y0, x1, y1 = to_world(a - 3, a + 3, wid / 2 - 2, wid / 2 + 2)
        cv.box(x0, y0, 1.5 + bh + ch, x1, y1, 1.5 + bh + ch + 2.5, lamp, lamp, lamp)
    if kind == "pickup":
        x0, y0, x1, y1 = to_world(2, cab[0], 2, wid - 2)
        cv.top(1.5 + bh - 0.5, x0, y0, x1, y1, lambda u, v, L, D: solid_res(C("4a3a2a"), u.shape))
    if kind in SIREN_KINDS:
        top_z = 1.5 + bh + (ch if cab else 0)
        a_mid = (cab[0] + cab[1]) / 2 if cab else length - 8
        for half, colr in ((0, "e8302a"), (1, "3a6af0")):
            lit = (siren == "A" and half == 0) or (siren == "B" and half == 1)
            c_ = C(colr) * (1.25 if lit else 0.8)
            em_v = np.append(C(colr) * 0.5 + 127, 255.0) if lit else np.zeros(4)

            def lb(u, v, L_, H_, c_=c_, em_v=em_v):
                return (np.broadcast_to(np.clip(c_, 0, 255), u.shape + (3,)).copy(), np.ones(u.shape, bool),
                        np.broadcast_to(em_v, u.shape + (4,)).copy())
            b0, b1 = (2, wid / 2) if half == 0 else (wid / 2, wid - 2)
            x0, y0, x1, y1 = to_world(a_mid - 2.5, a_mid + 2.5, b0, b1)
            cv.box(x0, y0, top_z, x1, y1, top_z + 2.5, lb, lb, lb)
    if kind == "fire":
        x0, y0, x1, y1 = to_world(4, length - 16, wid / 2 - 3, wid / 2 + 3)
        rail = flat("d8d8e0")
        cv.box(x0, y0, 1.5 + bh, x1, y1, 1.5 + bh + 3, rail, rail, lambda u, v, L_, D: (
            np.where((((np.floor(u) if along_x else np.floor(v)) % 4) == 0)[..., None], C("a8a8b0"), C("e8e8f0")) * np.ones(u.shape + (3,)),
            nores(u.shape), None))
    if kind == "garbage":
        x0, y0, x1, y1 = to_world(1, 4, 2, wid - 2)
        cv.box(x0, y0, 3, x1, y1, bh - 2, flat("3a7a3a"), flat("3a7a3a"), flat("2a5a2a"))
    if kind == "bus":
        x0, y0, x1, y1 = to_world(length / 2 - 6, length / 2 + 6, 4, wid - 4)
        cv.box(x0, y0, 1.5 + bh, x1, y1, 1.5 + bh + 3, flat("d8d8d8"), flat("c8c8c8"), flat("e8e8e8"))


def gen_cars(out_dir):
    meta = {}
    for kind, spec in CAR_KINDS.items():
        for ci, col in enumerate(spec[5]):
            for d in ("px", "nx", "py", "ny"):
                cv = Canvas(1, 40)
                car_body(cv, 32, 32, d, col, kind)
                img = cv.image()
                glow = cv.emission_image()
                bbox = img.getbbox()
                ax, ay = cv.screen(32, 32, 0)
                name = "car_%s_%d_%s" % (kind, ci, d)
                img.crop(bbox).save(os.path.join(out_dir, name + ".png"))
                glow.crop(bbox).save(os.path.join(out_dir, name + "_glow.png"))
                meta[name] = [round(ax - bbox[0]), round(ay - bbox[1])]
                if kind in SIREN_KINDS:
                    for s in ("A", "B"):
                        cv2 = Canvas(1, 40)
                        car_body(cv2, 32, 32, d, col, kind, siren=s, headlights=False)
                        cv2.emission_image().crop(bbox).save(os.path.join(out_dir, "%s_siren%s.png" % (name, s)))
    variants = {k: len(v[5]) for k, v in CAR_KINDS.items()}
    return meta, variants


# ====================================================================== traffic light
def gen_traffic_lights(out_dir):
    meta = {}
    for axis in ("x", "y"):
        cv = Canvas(1, 60)
        pole = lambda ang, v, nx, ny: (np.broadcast_to(C("4a4a54"), ang.shape + (3,)).copy(), nores(ang.shape), None)
        cv.cylinder(32, 32, 1.5, 0, 40, pole, lambda a, b: solid_res(C("3a3a44"), a.shape))
        cv.cylinder(32, 32, 3, 0, 2, pole)
        housing = flat("2a2a30", 3)

        def face(u, v, L, H):
            rgb = np.broadcast_to(C("22222a"), u.shape + (3,)).copy()
            for i, colr in enumerate(("5a1a1a", "5a4a1a", "1a4a24")):
                cz = H - 4 - i * 6
                dd = np.hypot(u - L / 2, v - cz)
                rgb[dd < 2.2] = C(colr)
                rgb[(dd >= 2.2) & (dd < 2.8) & (v > cz)] = C("44444e")
            return rgb, nores(u.shape), None
        if axis == "x":
            cv.box(30, 29, 40, 34, 35, 58, housing, face, flat("33333a"))
            pts = [cv.screen(34, 32, 58 - 4 - i * 6) for i in range(3)]
        else:
            cv.box(29, 30, 40, 35, 34, 58, face, housing, flat("33333a"))
            pts = [cv.screen(32, 34, 58 - 4 - i * 6) for i in range(3)]
        img = cv.image()
        bbox = img.getbbox()
        ax, ay = cv.screen(32, 32, 0)
        img.crop(bbox).save(os.path.join(out_dir, "traffic_light_%s.png" % axis))
        meta["traffic_light_%s" % axis] = {"anchor": [round(ax - bbox[0]), round(ay - bbox[1])],
                                           "lamps": [[round(p[0] - bbox[0], 1), round(p[1] - bbox[1], 1)] for p in pts]}
    # lamp dot (white, tinted in game)
    dot = Image.new("RGBA", (7, 7), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dot)
    dd.ellipse((1, 1, 5, 5), fill=(255, 255, 255, 255))
    dot.save(os.path.join(out_dir, "lamp_dot.png"))
    return meta


# ====================================================================== misc
def gen_sale_sign(out_dir):
    cv = Canvas(1, 40)
    wood = flat("b07a48", 6)
    cv.box(28, 31, 0, 30, 33, 22, wood, wood, wood)
    cv.box(34, 31, 0, 36, 33, 22, wood, wood, wood)

    def board(u, v, L, H):
        rgb = np.broadcast_to(C("f4ead2"), u.shape + (3,)).copy()
        rgb[(u < 1.5) | (u > L - 1.5) | (v < 1.5) | (v > H - 1.5)] = C("b07a48")
        d = np.hypot(u - L / 2, v - H / 2)
        rgb[d < 4.5] = C("e8b830")
        rgb[(d < 4.5) & (d > 3.5)] = C("b08820")
        rgb[(np.abs(u - L / 2) < 0.8) & (d < 3)] = C("b08820")
        return rgb, nores(u.shape), None
    cv.box(25, 32, 12, 39, 34, 24, board, wood, wood)
    img = cv.image()
    bbox = img.getbbox()
    ax, ay = cv.screen(32, 32, 0)
    img.crop(bbox).save(os.path.join(out_dir, "sale_sign.png"))
    return [round(ax - bbox[0]), round(ay - bbox[1])]


def gen_units(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cars, variants = gen_cars(out_dir)
    ppl = people.gen_people(out_dir)
    tl = gen_traffic_lights(out_dir)
    an = animals.gen_animals(out_dir)
    sign = gen_sale_sign(out_dir)
    lamps = fx.gen_lamp_props(out_dir)
    json.dump({"cars": cars, "car_variants": variants, "sirens": list(SIREN_KINDS), "traffic": tl, "sale_sign": sign,
               "people": ppl, "animals": an, "lamps": lamps},
              open(os.path.join(out_dir, "meta.json"), "w"), indent=1)
