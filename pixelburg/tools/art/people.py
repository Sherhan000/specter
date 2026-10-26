"""Pixel-art residents: 18 kinds x 2 colour variants.

Each row of the sheet holds 12 frames of 16x24 px:
  0-3 walk towards the camera, 4-7 walk away, 8 idle front, 9 idle back, 10-11 waving.
Front frames face down-left; the game flips them for down-right.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw

FW, FH = 16, 24
FRAMES = 12

SKIN = ["f2c6a0", "e0a882", "b87a52", "8a5636", "f6d2b4"]
OUT = (34, 26, 40, 255)


def rgb(h, f=1.0):
    h = h.lstrip("#")
    c = [min(255, max(0, int(int(h[i:i + 2], 16) * f))) for i in (0, 2, 4)]
    return (c[0], c[1], c[2], 255)


# kind: hair, hair style, top, top2 (trim), bottom, shoes, extras
KINDS = [
    # name, adult?, palette variants [(hair, top, bottom), ...], style dict
    ("man", True, [("4a2e1c", "3a7ad8", "3a3a5a"), ("1e1a1a", "6ab06a", "4a3a2a")], dict(hair="short")),
    ("woman", True, [("8a4a24", "e86a8a", "e86a8a"), ("e0b050", "8a6ad8", "8a6ad8")], dict(hair="long", dress=True)),
    ("business", True, [("2a2220", "2e3446", "2e3446"), ("6a4a32", "4a4a52", "4a4a52")], dict(hair="short", tie="c83a3a", shirt="f4f4f4")),
    ("businesswoman", True, [("2a1a14", "2e3446", "2e3446"), ("c89050", "7a2a3a", "2e2e36")], dict(hair="bun", shirt="f4f4f4", skirt=True)),
    ("boy", False, [("5a3a20", "e8a030", "3a5a8a"), ("1e1a1a", "d84a3a", "3a3a4a")], dict(hair="short", cap="3a6ad0")),
    ("girl", False, [("a84a2a", "f0c8e0", "e86a9a"), ("2a1a14", "a8e0f0", "4a8ad8")], dict(hair="tails", dress=True)),
    ("grandpa", True, [("d8d8d8", "8a7a5a", "5a5a5a"), ("e8e8e8", "5a6a8a", "4a4a4a")], dict(hair="bald", cane=True, beard=True)),
    ("grandma", True, [("e0e0e8", "9a4a6a", "5a4a6a"), ("d8d0d0", "4a7a6a", "6a5a4a")], dict(hair="bun", shawl="c8a070", skirt=True)),
    ("police", True, [("2a2220", "24345e", "1e2a4a"), ("4a2e1c", "24345e", "1e2a4a")], dict(hair="short", cap="1a2444", badge=True)),
    ("doctor", True, [("2a1a14", "f8f8f8", "5ab0a0"), ("c89050", "f8f8f8", "5ab0a0")], dict(hair="short", coat=True, shirt="5ab0a0")),
    ("firefighter", True, [("4a2e1c", "c8402a", "c8402a"), ("1e1a1a", "c8402a", "c8402a")], dict(hair="short", helmet="f0c030", stripes="f0f040")),
    ("builder", True, [("4a2e1c", "f08a2a", "3a5a8a"), ("8a4a24", "f08a2a", "3a3a4a")], dict(hair="short", helmet="f0d030", stripes="f8f8c0", shirt="4a6a9a")),
    ("chef", True, [("2a1a14", "f8f8f8", "3a3a3a"), ("8a4a24", "f8f8f8", "3a3a3a")], dict(hair="short", toque=True)),
    ("farmer", True, [("8a5a2a", "c84a3a", "3a5a9a"), ("d8a040", "6aa0d0", "3a5a9a")], dict(hair="short", straw=True, overalls=True)),
    ("jogger", True, [("1e1a1a", "f0f0f0", "2a2a3a"), ("e0b050", "e84a7a", "2a2a3a")], dict(hair="pony", shorts=True, band="e83a3a")),
    ("student", True, [("4a2e1c", "6a6a7a", "3a4a6a"), ("2a1a14", "4a8a5a", "3a3a3a")], dict(hair="short", hoodie=True, pack="c8783a")),
    ("postman", True, [("4a2e1c", "3a5ab0", "2a3a6a"), ("8a4a24", "3a5ab0", "2a3a6a")], dict(hair="short", cap="2a3a7a", bag="8a5a2a")),
    ("teen", True, [("1e1a1a", "3a3a46", "4a6aa8"), ("a84a2a", "e8d040", "4a6aa8")], dict(hair="pony", jacket=True)),
]


class P:
    def __init__(self):
        self.img = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def r(self, x0, y0, x1, y1, c):
        if x1 >= x0 and y1 >= y0:
            self.d.rectangle((x0, y0, x1, y1), fill=c)

    def p(self, x, y, c):
        if 0 <= x < FW and 0 <= y < FH:
            self.img.putpixel((x, y), c)


def draw(kind_i, var, frame):
    name, adult, pals, st = KINDS[kind_i]
    hair_c, top_c, bot_c = pals[var]
    skin = SKIN[(kind_i * 3 + var * 2) % len(SKIN)]
    if name in ("grandpa", "grandma"):
        skin = SKIN[(var * 2) % 2]
    p = P()
    back = 4 <= frame <= 7 or frame == 9
    walk = frame < 8
    step = frame % 4 if walk else 0
    wave = frame - 10 if frame >= 10 else -1
    # vertical layout
    if adult:
        hy, ty, ly, fy = 3, 10, 17, 22   # head top, torso top, legs top, feet row
    else:
        hy, ty, ly, fy = 9, 15, 19, 22
    bob = 1 if step in (1, 3) else 0
    hy -= bob
    ty -= bob
    ly -= bob
    skin_c, skin_d = rgb(skin), rgb(skin, 0.86)
    top, top_d, top_l = rgb(top_c), rgb(top_c, 0.78), rgb(top_c, 1.12)
    bot, bot_d = rgb(bot_c), rgb(bot_c, 0.78)
    hair, hair_d = rgb(hair_c), rgb(hair_c, 0.75)
    shoe = rgb("2a2024") if name not in ("jogger",) else rgb("f4f4f4")
    # ------------------------------------------------ legs
    la = [0, 1, 0, -1][step]          # +: left foot forward (lower), right foot lifted
    left_len = (fy - ly) + (1 if la > 0 else 0) - (1 if la < 0 else 0)
    right_len = (fy - ly) - (1 if la > 0 else 0) + (1 if la < 0 else 0)
    if not walk:
        left_len = right_len = fy - ly
    skirt = st.get("dress") or st.get("skirt")
    leg_c = skin_c if (skirt or st.get("shorts")) else bot
    leg_d = skin_d if (skirt or st.get("shorts")) else bot_d
    p.r(5, ly, 7, ly + left_len - 1, leg_c)
    p.r(8, ly, 10, ly + right_len - 1, leg_d)
    if st.get("shorts"):
        p.r(5, ly, 10, ly + 2, bot)
        p.r(8, ly, 10, ly + 2, bot_d)
    p.r(5, ly + left_len, 7, ly + left_len, shoe)
    p.r(8, ly + right_len, 10, ly + right_len, shoe)
    if not back:
        p.p(4, ly + left_len, shoe)
    # ------------------------------------------------ torso
    tw0, tw1 = (4, 11) if adult else (5, 10)
    tb = ly - 1
    if st.get("coat"):
        p.r(tw0, ty, tw1, ly + 3, top)
        p.r(tw1 - 1, ty, tw1, ly + 3, top_d)
        if not back:
            p.r(7, ty + 1, 8, tb, rgb(st["shirt"]))
            p.p(5, ty + 4, rgb("c8d0d8"))
    elif skirt:
        p.r(tw0, ty, tw1, tb, top)
        p.r(tw1 - 1, ty, tw1, tb, top_d)
        sk = bot if st.get("skirt") else top
        skd = bot_d if st.get("skirt") else top_d
        p.r(tw0, ly - 1, tw1, ly + 3, sk)
        p.r(tw0 - 1, ly + 2, tw1 + 1, ly + 3, sk)
        p.r(tw1, ly - 1, tw1 + 1, ly + 3, skd)
    else:
        p.r(tw0, ty, tw1, tb, top)
        p.r(tw1 - 1, ty, tw1, tb, top_d)
        p.r(tw0, ty, tw0, tb, top_l)
        p.r(tw0, tb, tw1, tb, bot if not st.get("overalls") else bot)
    if st.get("overalls"):
        p.r(tw0 + 1, ty + 2, tw1 - 1, tb, bot)
        if not back:
            p.p(tw0 + 1, ty, bot)
            p.p(tw1 - 1, ty, bot)
            p.p(tw0 + 1, ty + 1, bot)
            p.p(tw1 - 1, ty + 1, bot)
    if st.get("stripes"):
        p.r(tw0, ty + 4, tw1, ty + 4, rgb(st["stripes"]))
        if name == "builder" and not back:
            p.r(tw0 + 1, ty, tw0 + 1, ty + 3, rgb(st["stripes"]))
            p.r(tw1 - 1, ty, tw1 - 1, ty + 3, rgb(st["stripes"]))
    if not back:
        if st.get("shirt") and not st.get("coat") and name not in ("builder",):
            p.r(7, ty, 8, ty + 2, rgb(st["shirt"]))
        if st.get("tie"):
            p.r(7, ty + 1, 8, ty + 4, rgb(st["tie"]))
            p.p(7, ty + 5, rgb(st["tie"], 0.8))
        if st.get("badge"):
            p.p(5, ty + 2, rgb("f0d040"))
        if st.get("hoodie"):
            p.p(6, ty + 1, rgb("f4f4f4"))
            p.p(9, ty + 1, rgb("f4f4f4"))
        if st.get("jacket"):
            p.r(7, ty, 8, tb, rgb("f4f4f4"))
        if st.get("pack"):
            p.p(tw0, ty + 1, rgb(st["pack"], 0.7))
            p.p(tw1, ty + 1, rgb(st["pack"], 0.7))
        if st.get("bag"):
            for i in range(5):
                p.p(tw0 + 1 + i, ty + i, rgb(st["bag"], 0.7))
    else:
        if st.get("pack"):
            p.r(tw0 + 1, ty + 1, tw1 - 1, ty + 5, rgb(st["pack"]))
            p.r(tw0 + 1, ty + 5, tw1 - 1, ty + 5, rgb(st["pack"], 0.75))
        if st.get("hoodie"):
            p.r(tw0 + 1, ty, tw1 - 1, ty + 1, top_d)
    if st.get("bag") and not back:
        p.r(tw1 - 1, tb - 1, tw1 + 1, tb + 2, rgb(st["bag"]))
    if st.get("shawl"):
        p.r(tw0, ty, tw1, ty + 2, rgb(st["shawl"]))
        p.r(tw1 - 1, ty + 1, tw1, ty + 2, rgb(st["shawl"], 0.8))
    # ------------------------------------------------ arms
    sw = [0, 1, 0, -1][step] if walk else 0
    arm_len = (tb - ty) - 1
    sleeve, sleeve_d = top, top_d
    if st.get("shorts") or name == "jogger":
        sleeve, sleeve_d = skin_c, skin_d
    ax_l, ax_r = tw0 - 1, tw1 + 1
    if wave >= 0 and not back:
        # left arm down, right arm raised and waving
        p.r(ax_l, ty + 1, ax_l, ty + arm_len, sleeve)
        p.p(ax_l, ty + arm_len + 1, skin_c)
        top_y = ty - 4 + (1 if wave else 0)
        hx = ax_r + (1 if wave else 0)
        p.r(ax_r, ty - 1, ax_r, ty + 1, sleeve_d)
        p.r(hx, top_y + 1, hx, ty - 1, sleeve_d)
        p.r(hx, top_y - 1, hx + 1 if wave else hx, top_y, skin_c)
    else:
        p.r(ax_l, ty + 1 + max(0, sw), ax_l, ty + arm_len + max(0, sw), sleeve)
        p.p(ax_l, ty + arm_len + 1 + max(0, sw), skin_c)
        p.r(ax_r, ty + 1 + max(0, -sw), ax_r, ty + arm_len + max(0, -sw), sleeve_d)
        p.p(ax_r, ty + arm_len + 1 + max(0, -sw), skin_d)
    if st.get("cane") and not back:
        cx = ax_r + 1
        p.r(cx, ty + arm_len, cx, fy, rgb("6a4a2a"))
        p.p(cx - 1, ty + arm_len, rgb("6a4a2a"))
    # ------------------------------------------------ head
    hx0, hx1 = 5, 10
    p.r(7, ty - 1, 8, ty - 1, skin_d)
    p.r(hx0, hy + 1, hx1, ty - 2, skin_c)
    p.r(hx0 + 1, hy, hx1 - 1, hy, skin_c)
    p.r(hx1, hy + 2, hx1, ty - 2, skin_d)
    hs = st.get("hair", "short")
    if back:
        if hs != "bald":
            p.r(hx0, hy, hx1, ty - 2, hair)
            p.r(hx1, hy + 1, hx1, ty - 2, hair_d)
        else:
            p.r(hx0, hy + 3, hx1, ty - 2, hair)
            p.r(hx0 + 1, hy, hx1 - 1, hy + 2, skin_c)
    else:
        if hs == "bald":
            p.p(hx0, hy + 2, hair)
            p.p(hx1, hy + 2, hair)
            p.p(hx0, hy + 3, hair)
            p.p(hx1, hy + 3, hair)
        else:
            p.r(hx0, hy, hx1, hy + 1, hair)
            p.r(hx0 + 1, hy - 1, hx1 - 1, hy - 1, hair)
            p.p(hx0, hy + 2, hair)
            p.p(hx1, hy + 2, hair_d)
            p.p(hx0 + 1, hy + 2, hair_d)
        # eyes, cheeks, mouth
        ey = hy + 3
        eye = rgb("2a1a22")
        p.p(hx0 + 1, ey, eye)
        p.p(hx1 - 2, ey, eye)
        if adult or True:
            p.p(hx0 + 1, ey + 2, rgb("f09a9a") if name in ("woman", "girl", "businesswoman", "grandma", "teen") else skin_c)
        p.p(hx0 + 3, ey + 2, rgb(skin, 0.7))
        if st.get("glasses") or name == "grandpa":
            p.r(hx0, ey, hx0 + 2, ey, rgb("3a3a44"))
            p.r(hx1 - 3, ey, hx1 - 1, ey, rgb("3a3a44"))
            p.p(hx0 + 1, ey, eye)
            p.p(hx1 - 2, ey, eye)
        if st.get("beard"):
            p.r(hx0 + 1, ey + 2, hx1 - 1, ty - 2, hair)
            p.p(hx0 + 3, ey + 2, rgb(skin, 0.7))
    if hs == "long":
        side = hair_d if back else hair
        p.r(hx0 - 1, hy + 1, hx0 - 1, ty + 2, hair)
        p.r(hx1 + 1, hy + 1, hx1 + 1, ty + 2, hair_d)
        if back:
            p.r(hx0, ty - 2, hx1, ty + 2, side)
    elif hs == "bun":
        p.r(hx0 + 2, hy - 3, hx1 - 2, hy - 1, hair)
        p.p(hx1 - 2, hy - 2, hair_d)
    elif hs == "tails":
        p.r(hx0 - 2, hy + 2, hx0 - 1, hy + 5, hair)
        p.r(hx1 + 1, hy + 2, hx1 + 2, hy + 5, hair_d)
        p.p(hx0 - 1, hy + 2, rgb("e84a7a"))
        p.p(hx1 + 1, hy + 2, rgb("e84a7a"))
    elif hs == "pony":
        if back:
            p.r(7, hy + 2, 8, ty + 1, hair_d)
        else:
            p.r(hx1 + 1, hy + 1, hx1 + 1, hy + 5, hair_d)
    # ------------------------------------------------ headwear
    if st.get("cap"):
        c = rgb(st["cap"])
        p.r(hx0, hy - 1, hx1, hy + 1, c)
        if not back:
            p.r(hx0 - 1, hy + 1, hx1 - 2, hy + 1, rgb(st["cap"], 0.75))
        if st.get("badge") and not back:
            p.p(7, hy, rgb("f0d040"))
    if st.get("helmet"):
        c = rgb(st["helmet"])
        p.r(hx0 - 1, hy - 1, hx1 + 1, hy + 1, c)
        p.r(hx0, hy - 2, hx1, hy - 2, c)
        p.r(hx1, hy - 1, hx1 + 1, hy + 1, rgb(st["helmet"], 0.8))
    if st.get("toque"):
        w = rgb("fcfcfc")
        p.r(hx0, hy - 4, hx1, hy, w)
        p.r(hx0 - 1, hy - 5, hx1 + 1, hy - 3, w)
        p.r(hx1, hy - 5, hx1 + 1, hy, rgb("d8d8e0"))
    if st.get("straw"):
        s = rgb("e8c868")
        p.r(hx0 - 2, hy + 1, hx1 + 2, hy + 1, s)
        p.r(hx0, hy - 2, hx1, hy, s)
        p.r(hx0, hy, hx1, hy, rgb("c83a2a"))
    if st.get("band"):
        p.r(hx0, hy + 1, hx1, hy + 1, rgb(st["band"]))
    if st.get("hoodie") and back:
        p.r(hx0, ty - 2, hx1, ty - 1, top_d)
    # ------------------------------------------------ outline
    a = np.array(p.img)
    m = a[..., 3] > 0
    pad = np.pad(m, 1)
    edge = ~m & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
    a[edge] = OUT
    return Image.fromarray(a)


def gen_people(out_dir):
    rows = []
    for k in range(len(KINDS)):
        for v in range(2):
            rows.append((k, v))
    sheet = Image.new("RGBA", (FW * FRAMES, FH * len(rows)), (0, 0, 0, 0))
    for ri, (k, v) in enumerate(rows):
        for f in range(FRAMES):
            sheet.paste(draw(k, v, f), (f * FW, ri * FH))
    sheet.save(os.path.join(out_dir, "people.png"))
    meta = {"frame": [FW, FH], "frames": FRAMES, "kinds": {}}
    for ri, (k, v) in enumerate(rows):
        meta["kinds"].setdefault(KINDS[k][0], []).append(ri)
    meta["adult"] = {KINDS[k][0]: KINDS[k][1] for k in range(len(KINDS))}
    return meta
