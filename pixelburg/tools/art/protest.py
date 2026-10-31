"""Protest placards (ROADMAP 28): signs on a stick that protesters hold over their heads.

assets/units/placards.png: one row of frames FW x FH, drawn at 2x (the game shows them at half size).
Each placard has its own colour and picture: a slogan, a raised fist, a crossed-out coin (taxes),
a house (homes), a heart, a megaphone-style "!" and a scale of justice (rights).
"""
import os

from PIL import Image, ImageDraw

S = 4                     # supersampling while drawing
FW, FH = 32, 44           # frame size in the png (2x of the in-game size)
BOARD = (3, 2, 29, 22)    # board rectangle inside a frame
STICK = (15, 20, 17, 43)

INK = (40, 34, 38, 255)
STICK_C = (150, 104, 60, 255)
STICK_D = (104, 70, 40, 255)


def _r(d, box, fill, outline=None, w=1):
    x0, y0, x1, y1 = box
    d.rectangle((x0 * S, y0 * S, x1 * S - 1, y1 * S - 1), fill=fill, outline=outline, width=w * S if outline else 0)


def _poly(d, pts, fill):
    d.polygon([(x * S, y * S) for x, y in pts], fill=fill)


def _line(d, pts, fill, w=1.0):
    d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(w * S))


def _ell(d, box, fill=None, outline=None, w=1.0):
    x0, y0, x1, y1 = box
    d.ellipse((x0 * S, y0 * S, x1 * S, y1 * S), fill=fill, outline=outline, width=int(w * S) if outline else 0)


def _board(d, color, edge):
    _r(d, STICK, STICK_C)
    _r(d, (STICK[0] + 1, STICK[1], STICK[2], STICK[3]), STICK_D)
    x0, y0, x1, y1 = BOARD
    _r(d, (x0 + 1, y0 + 1, x1 + 1, y1 + 1), (0, 0, 0, 70))            # shadow
    _r(d, BOARD, color, edge, 1)
    _r(d, (x0 + 1, y0 + 1, x1 - 1, y0 + 2), (255, 255, 255, 60))      # top light


def _slogan(d):
    _board(d, (246, 242, 230, 255), (120, 110, 96, 255))
    for i, (w, c) in enumerate([(20, (200, 40, 40, 255)), (16, INK), (18, (200, 40, 40, 255))]):
        y = 6 + i * 5
        _r(d, (16 - w // 2, y, 16 + w // 2, y + 3), c)


def _fist(d):
    _board(d, (248, 206, 60, 255), (150, 110, 20, 255))
    skin = (60, 40, 30, 255)
    _r(d, (11, 7, 21, 15), skin)           # knuckles
    for x in (11, 14, 17):
        _line(d, [(x + 2.5, 7.2), (x + 2.5, 11)], (248, 206, 60, 255), 0.6)
    _r(d, (13, 15, 19, 21), skin)          # wrist
    _r(d, (9, 9, 12, 14), skin)            # thumb


def _no_tax(d):
    _board(d, (226, 64, 54, 255), (130, 30, 26, 255))
    gold = (255, 210, 70, 255)
    _ell(d, (9.5, 5, 22.5, 18), fill=gold, outline=(170, 120, 20, 255), w=1)
    _r(d, (15, 8, 17, 15), (170, 120, 20, 255))
    _line(d, [(8, 19), (24, 4)], (255, 255, 255, 255), 2.2)


def _house(d):
    _board(d, (70, 132, 210, 255), (30, 66, 120, 255))
    _poly(d, [(8, 12), (16, 5), (24, 12)], (230, 80, 60, 255))
    _r(d, (10, 12, 22, 20), (250, 244, 230, 255))
    _r(d, (14.5, 15, 17.5, 20), (110, 70, 40, 255))
    _r(d, (11, 13, 14, 15.5), (120, 190, 240, 255))
    _r(d, (19, 13, 21, 15.5), (120, 190, 240, 255))


def _heart(d):
    _board(d, (110, 196, 110, 255), (40, 110, 50, 255))
    red = (220, 40, 70, 255)
    _ell(d, (9, 6, 16.5, 13.5), fill=red)
    _ell(d, (15.5, 6, 23, 13.5), fill=red)
    _poly(d, [(9.3, 11), (22.7, 11), (16, 19.5)], red)
    _ell(d, (11, 7.5, 13.5, 10), fill=(255, 180, 190, 255))


def _alarm(d):
    _board(d, (250, 250, 250, 255), (90, 90, 96, 255))
    _r(d, (4, 3, 28, 6), (220, 40, 40, 255))
    _r(d, (4, 19, 28, 22), (220, 40, 40, 255))
    _r(d, (14.5, 7.5, 17.5, 15), INK)
    _r(d, (14.5, 16, 17.5, 18.5), INK)


def _justice(d):
    _board(d, (150, 96, 200, 255), (80, 40, 120, 255))
    gold = (255, 220, 110, 255)
    _r(d, (15, 6, 17, 19), gold)
    _r(d, (8, 7, 24, 8.5), gold)
    _r(d, (12, 19, 20, 20.5), gold)
    for cx in (9.5, 22.5):
        _line(d, [(cx, 8.5), (cx - 2.5, 13)], gold, 0.6)
        _line(d, [(cx, 8.5), (cx + 2.5, 13)], gold, 0.6)
        _poly(d, [(cx - 3.5, 13), (cx + 3.5, 13), (cx + 2, 15), (cx - 2, 15)], gold)


DESIGNS = [_slogan, _fist, _no_tax, _house, _heart, _alarm, _justice]
# which placards fit each protest cause (frame indices); kept in sync with ProtestView.BY_CAUSE
BY_CAUSE = {"rob": [5, 6], "tax": [2, 0], "demolish": [3, 0], "mood": [4, 1], "rules": [6, 5]}
GENERIC = [0, 1]


def _frame(draw_fn):
    big = Image.new("RGBA", (FW * S, FH * S), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big))
    return big.resize((FW, FH), Image.LANCZOS)


def gen(out_dir):
    sheet = Image.new("RGBA", (FW * len(DESIGNS), FH), (0, 0, 0, 0))
    for i, fn in enumerate(DESIGNS):
        sheet.alpha_composite(_frame(fn), (i * FW, 0))
    sheet.save(os.path.join(out_dir, "placards.png"))
    return sheet


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    gen(os.path.join(here, "..", "..", "assets", "units"))
