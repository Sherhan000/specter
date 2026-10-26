"""Soft interface sounds, city sounds and seamless weather / city ambience loops (numpy + scipy)."""
import os
import subprocess
import wave

import numpy as np
from scipy.signal import butter, lfilter, sosfilt

from music import marimba, musicbox, epiano, nf

SR = 32000


def t_(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.005, decay=0.0, r=0.02):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t * decay)
    return e * np.clip((n / SR - t) / max(r, 1e-4), 0, 1)


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def noise(d, seed=0):
    return np.random.default_rng(seed).normal(0, 1, int(SR * d))


def brown(d, seed=0):
    w = noise(d, seed)
    b = lfilter([1.0], [1.0, -0.995], w)
    return b / (np.max(np.abs(b)) + 1e-9)


def at(buf, pos, sig, vol=1.0, wrap=True):
    s = int(pos * SR)
    idx = np.arange(len(sig)) + s
    if wrap:
        np.add.at(buf, idx % len(buf), sig * vol)
    else:
        m = idx < len(buf)
        np.add.at(buf, idx[m], sig[m] * vol)


def seq(*parts, gap=0.0):
    out = []
    for p in parts:
        out.append(p)
        if gap:
            out.append(np.zeros(int(SR * gap)))
    return np.concatenate(out)


def save(path, x, peak=0.85):
    x = np.asarray(x, float)
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    data = (np.clip(x, -1, 1) * 32767).astype("<i2")
    tmp = path if path.endswith(".wav") else path + ".wav"
    with wave.open(tmp, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    if path.endswith(".ogg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", "3", path], check=True)
        os.remove(tmp)


def loop_fade(x, fade=1.0):
    """Make a loop seamless by cross-fading its end into its start."""
    n = int(SR * fade)
    head, body, tail = x[:n], x[n:-n] if n else x, x[-n:]
    w = np.linspace(0, 1, n)
    return np.concatenate([tail * (1 - w) + head * w, body])


# ---------------------------------------------------------------- interface
def ui_sounds(out):
    w = lambda name, x, p=0.8: save(os.path.join(out, name + ".wav"), x, p)
    w("tap", marimba(nf(84), 0.12) * env(int(SR * 0.12), 0.001, 30), 0.55)
    w("click", marimba(nf(91), 0.08), 0.45)
    w("coin", seq(musicbox(nf(88), 0.09), musicbox(nf(95), 0.5)) + 0.0, 0.7)
    w("gem", seq(musicbox(nf(88), 0.07), musicbox(nf(92), 0.07), musicbox(nf(95), 0.07), musicbox(nf(100), 0.7)), 0.75)
    g = marimba(nf(67), 0.15)
    w("goods", seq(g, marimba(nf(72), 0.35)) + np.concatenate([bp(noise(0.12, 2), 300, 2000) * env(int(SR * 0.12), 0.002, 30) * 0.4,
                                                                  np.zeros(int(SR * 0.38))]), 0.7)
    thud = np.sin(2 * np.pi * np.cumsum(70 + 60 * np.exp(-t_(0.35) * 20)) / SR) * np.exp(-t_(0.35) * 12)
    w("place", thud + lp(noise(0.35, 3), 900) * env(int(SR * 0.35), 0.002, 14) * 0.6, 0.8)
    chord = sum(epiano(nf(n), 0.9) for n in (72, 76, 79, 84))
    w("done", np.concatenate([marimba(nf(79), 0.1), marimba(nf(84), 0.1), chord]), 0.75)
    lv = np.concatenate([marimba(nf(n), 0.11) for n in (72, 76, 79, 84, 88)] + [sum(musicbox(nf(n), 1.2) for n in (84, 88, 91, 96))])
    w("levelup", lv, 0.8)
    w("upgrade", np.concatenate([marimba(nf(n), 0.08) for n in (67, 72, 76, 79, 84)] + [marimba(nf(91), 0.4)]), 0.7)
    err = sum(np.sin(2 * np.pi * f * t_(0.28)) for f in (196, 233)) * env(int(SR * 0.28), 0.005, 8)
    w("error", seq(err[: int(SR * 0.12)], err), 0.55)
    rubble = lp(brown(0.9, 6), 1200) * env(int(SR * 0.9), 0.003, 4) + bp(noise(0.9, 7), 800, 4000) * env(int(SR * 0.9), 0.002, 9) * 0.3
    w("demolish", rubble, 0.8)
    w("road", bp(noise(0.25, 8), 200, 3000) * env(int(SR * 0.25), 0.003, 16) + thud[: int(SR * 0.25)] * 0.4, 0.6)
    w("mail", seq(musicbox(nf(88), 0.16), musicbox(nf(95), 0.7)), 0.6)
    construct = np.zeros(int(SR * 1.2))
    for k in range(5):
        h = bp(noise(0.08, 20 + k), 1500, 6000) * env(int(SR * 0.08), 0.001, 40) + \
            np.sin(2 * np.pi * 1800 * t_(0.08)) * env(int(SR * 0.08), 0.001, 50) * 0.5
        at(construct, k * 0.22, h, 1.0, wrap=False)
    w("construct", construct, 0.6)


# ---------------------------------------------------------------- city sounds
def horn(freqs, d, honks):
    out = []
    for i, hd in enumerate(honks):
        t = t_(hd)
        s = sum(np.sign(np.sin(2 * np.pi * f * t)) * 0.4 + np.sin(2 * np.pi * f * t) for f in freqs)
        s = lp(s, 2200) * env(len(t), 0.01, 0, 0.03)
        out.append(s)
        out.append(np.zeros(int(SR * 0.07)))
    return np.concatenate(out)


def city_sounds(out):
    w = lambda name, x, p=0.8: save(os.path.join(out, name + ".wav"), x, p)
    w("horn_car", horn((415, 523), 0.14, (0.12, 0.2)), 0.6)
    w("horn_truck", horn((185, 233, 277), 0.5, (0.55,)), 0.7)
    t = t_(3.0)
    f = 950 + 380 * np.sin(2 * np.pi * t / 1.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    siren = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)) * env(len(t), 0.05, 0, 0.3)
    w("siren", lp(siren, 4000) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.4 * t)), 0.5)
    # door: creak + soft knock of the frame
    t = t_(0.7)
    cf = 420 + 260 * np.sin(2 * np.pi * 1.3 * t) + 80 * np.random.default_rng(3).normal(0, 1, len(t)).cumsum() / SR
    creak = np.sign(np.sin(2 * np.pi * np.cumsum(cf) / SR)) * bp(noise(0.7, 4), 300, 2500) * 0.3
    creak = bp(creak, 400, 3000) * env(len(t), 0.05, 2, 0.1)
    knock = np.sin(2 * np.pi * 110 * t_(0.25)) * np.exp(-t_(0.25) * 25) + lp(noise(0.25, 5), 700) * np.exp(-t_(0.25) * 30) * 0.5
    door = np.zeros(int(SR * 1.0))
    at(door, 0.0, creak, 0.7, wrap=False)
    at(door, 0.62, knock, 1.0, wrap=False)
    w("door", door, 0.6)
    # thunder: a crack followed by a long rolling rumble
    d = 4.5
    rum = lp(brown(d, 11), 160) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 0.7 * t_(d) + 1))) * env(int(SR * d), 0.08, 0.7, 0.8)
    crack = bp(noise(0.5, 12), 800, 6000) * env(int(SR * 0.5), 0.002, 9)
    thunder = rum
    at(thunder, 0.0, crack, 0.8, wrap=False)
    save(os.path.join(out, "thunder.ogg"), thunder, 0.9)


# ---------------------------------------------------------------- ambience loops
def rain_bed(d, seed, heavy=False):
    hiss = bp(noise(d, seed), 400, 9000) * 0.25
    patter = np.zeros(int(SR * d))
    rng = np.random.default_rng(seed + 1)
    drops = int(d * (900 if heavy else 380))
    drop = bp(noise(0.02, seed + 2), 1500, 8000) * env(int(SR * 0.02), 0.0005, 180)
    for _ in range(drops):
        at(patter, rng.uniform(0, d), drop, rng.uniform(0.05, 0.4))
    roof = lp(brown(d, seed + 3), 500) * 0.25
    return hiss + patter + roof


def ambience(out):
    d = 14.0
    save(os.path.join(out, "amb_rain.ogg"), loop_fade(rain_bed(d + 1, 30), 1.0), 0.5)
    storm = rain_bed(d + 1, 40, True) * 1.3
    wind = bp(noise(d + 1, 41), 120, 900) * (0.4 + 0.6 * (0.5 + 0.5 * np.sin(2 * np.pi * t_(d + 1) / 7.0))) * 0.5
    rumble = lp(brown(d + 1, 42), 120) * (0.5 + 0.5 * np.sin(2 * np.pi * t_(d + 1) / 5.0 + 2) ** 2) * 0.7
    save(os.path.join(out, "amb_storm.ogg"), loop_fade(storm + wind + rumble, 1.0), 0.6)
    # daytime town: distant traffic swells, a few birds, the odd far-away horn
    town = lp(brown(d + 1, 50), 400) * 0.35
    rng = np.random.default_rng(51)
    for _ in range(9):
        cd = rng.uniform(2.5, 4.5)
        car = bp(noise(cd, int(rng.integers(0, 999))), 80, 700) * np.sin(np.pi * t_(cd) / cd) ** 2
        at(town, rng.uniform(0, d), car, rng.uniform(0.3, 0.7))
    for _ in range(14):
        cd = rng.uniform(0.08, 0.18)
        tt = t_(cd)
        f0 = rng.uniform(2800, 4200)
        chirp = np.sin(2 * np.pi * np.cumsum(f0 + rng.uniform(600, 1400) * np.sin(2 * np.pi * rng.uniform(15, 30) * tt)) / SR)
        chirp *= np.sin(np.pi * tt / cd) ** 2
        start = rng.uniform(0, d)
        for k in range(int(rng.integers(1, 4))):
            at(town, start + k * cd * 1.3, chirp, rng.uniform(0.08, 0.18))
    save(os.path.join(out, "amb_city.ogg"), loop_fade(town, 1.0), 0.45)
    # night: crickets and a soft breeze
    night = bp(noise(d + 1, 60), 150, 1200) * 0.05
    for c in range(3):
        f = 4300 + c * 450
        period = 0.5 + c * 0.13
        pos = rng.uniform(0, 0.3)
        while pos < d + 1:
            chirp = np.sin(2 * np.pi * f * t_(0.05)) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 60 * t_(0.05)))) * np.sin(np.pi * t_(0.05) / 0.05)
            at(night, pos, chirp, 0.05 + 0.03 * c)
            pos += period * rng.uniform(0.9, 1.1)
    save(os.path.join(out, "amb_night.ogg"), loop_fade(night, 1.0), 0.35)


def gen_sfx(out):
    os.makedirs(out, exist_ok=True)
    ui_sounds(out)
    city_sounds(out)
    ambience(out)
