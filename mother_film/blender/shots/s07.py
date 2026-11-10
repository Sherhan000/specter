"""S07 (0:36-0:43) The sky weeps. Rain over the whole world; the mountains tremble; lightning splits the sky."""
import bpy, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
import common as C, clay as K, fx

FRAMES = 168
START = 864
STRIKE = 34        # 0:37.4 in the mix


def flash(f):
    k = f - STRIKE
    tab = {0: 1.0, 1: 0.85, 2: 0.45, 3: 0.12, 4: 0.9, 5: 0.55, 6: 0.25, 15: 0.3, 16: 0.15}
    v = max(tab.get(k, 0.0), 0.22 * math.exp(-(k - 6) / 6.0) if k >= 6 else 0.0)
    for c, a in ((-22, 0.10), (78, 0.16), (80, 0.09), (118, 0.12)):          # far-off flickers
        v = max(v, a * math.exp(-((k - c) / 1.5) ** 2))
    return v


def build(sc, quality):
    C.set_look(sc, 'AgX', 'Medium High Contrast')
    rs = np.random.RandomState(11)

    def hf(X, Y):
        band = np.exp(-((Y - 30) / 16.0) ** 2)
        r = fx.fbm2(X * 0.035 + 13, Y * 0.035 + 2, seed=21, octaves=7, ridged=True)
        big = fx.fbm2(X * 0.016 + 4, Y * 0.016 + 1, seed=24, octaves=3)
        peaks = np.clip(r * 0.55 + 0.45 + big * 0.7, 0, None) ** 2.1
        valley = fx.fbm2(X * 0.06, Y * 0.06, seed=28, octaves=5) * 0.9
        return band * peaks * 30.0 + valley * (1 - band)
    ter = fx.terrain('world', (-90, 90), (-70, 62), 640, 470, hf)
    tm = K.clay('worldclay', 'rock', wet=0.75, coords='object', scale=0.085, tex='cliff_side', bump=1.6)
    K.assign(ter, tm)
    houses, win = fx.village('village', 150, (-34, 34), (-34, 2), hf, seed=5)
    K.assign(houses, K.clay('houses', 'buff', wet=0.6, coords='object', scale=0.5))
    sky, sky_flash = fx.storm_sky('sky', (360, 130), (0, 95, 40), bolt_uv=(0.47, 0.5), ambient=0.07, seed=8)
    bolt_obs, bolt_set, main = fx.lightning(sc, rs, (3, 70, 100), (-2, 70, 6), width=0.45, branches=9)
    strike = C.light(sc, 'POINT', (0, 66, 50), 0, color=(0.7, 0.8, 1.0), size=4.0, name='strike')
    moon = C.light(sc, 'SUN', (0, 0, 50), 0.5, color=(0.42, 0.56, 1.0), rot=(50, 0, 165), size=0.3, name='moon')
    curtains = [fx.rain_curtain(f'curtain{i}', (200, 70), (0, y, 30), seed=i, strength=s_, tiles=(t_, 1.6))
                for i, (y, s_, t_) in enumerate(((-8, 0.10, 9), (12, 0.08, 7), (40, 0.06, 5)))]
    rain = fx.Rain(sc, 3600, (-9, 2.0, -7), (9, 18, 7), width=0.007, seed=2, strength=0.32, slant=(0.12, 0.0))
    cam = C.camera(sc, (0, -62, 20), (0, 20, 9), lens=30, fstop=None, name='cam')
    sm = fx.smooth

    def update(f):
        t = f / 24.0
        low = fx.env(START + f, 'low', 1)
        I = flash(f)
        bolt_set(I if (I > 0.4 and abs(f - STRIKE - 2.5) < 4) else 0.0)
        sky_flash.default_value = 0.03 + 1.7 * I
        strike.data.energy = 3.2e5 * I
        p = sm(f, -20, FRAMES + 30)
        cam.location = Vector((3 - 5 * p, -62 + 34 * p, 20 - 11.5 * p))
        C.look_at(cam, Vector((0, 22, 10 + 2 * p)))
        quake = max(low, 0.6 * math.exp(-max(0, f - STRIKE) / 30.0) if f >= STRIKE else 0.0)
        fx.shake(cam, f, 0.0015 + 0.006 * quake, seed=4)
        rain.ob.location = cam.location
        rain.update(f, intensity=0.75 + 0.25 * sm(f, 0, 60), speed=11.0)
        for i, (ob, set_) in enumerate(curtains):
            set_(t, 1.0 + 4.0 * I, speed=1.5 + 0.2 * i)

    return dict(frames=FRAMES, update=update)
