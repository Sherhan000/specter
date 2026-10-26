"""Five seamless stereo music loops (title, morning, day, evening, night), synthesised with numpy.

Instruments: Karplus-Strong guitar, FM electric piano, marimba, music box, airy flute, warm pad,
round bass and soft brushed drums. Melodies are built from short motifs that repeat and answer
each other, so every loop sounds like a written tune rather than random notes.
"""
import os
import subprocess
import wave

import numpy as np

SR = 32000


def nf(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def tt(dur):
    return np.arange(int(SR * dur)) / SR


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2, dur=None):
    t = np.arange(n) / SR
    dur = dur if dur is not None else n / SR
    e = np.where(t < a, t / max(a, 1e-4), np.where(t < a + d, 1 - (1 - s) * (t - a) / max(d, 1e-4), s))
    rel = np.clip((dur - t) / max(r, 1e-4), 0, 1)
    return e * np.where(t > dur - r, rel, 1)


# ---------------------------------------------------------------- instruments
def guitar(f, dur, bright=0.5, seed=0):
    """Karplus-Strong plucked string."""
    n = int(SR * dur)
    p = max(2, int(SR / f))
    rng = np.random.default_rng(seed + int(f))
    buf = rng.uniform(-1, 1, p)
    buf = np.convolve(buf, [0.5, 0.5], mode="same") if bright < 0.6 else buf
    out = np.zeros(n)
    decay = 0.996 if f < 200 else 0.994
    for i in range(n):
        j = i % p
        out[i] = buf[j]
        buf[j] = decay * 0.5 * (buf[j] + buf[(j + 1) % p])
    return out * adsr(n, 0.002, 0.05, 1.0, 0.05)


def epiano(f, dur):
    """FM Rhodes-like tine: ratio 1 modulator with a decaying index plus a soft bell partial."""
    t = tt(dur)
    idx = 1.8 * np.exp(-t * 4.5) + 0.25
    mod = np.sin(2 * np.pi * f * t) * idx
    car = np.sin(2 * np.pi * f * t + mod)
    tine = 0.25 * np.sin(2 * np.pi * f * 7.0 * t) * np.exp(-t * 14)
    return (car + tine) * adsr(len(t), 0.004, 0.6, 0.35, 0.25) * np.exp(-t * 0.6)


def marimba(f, dur):
    t = tt(dur)
    out = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 18) + \
        0.12 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t * 40)
    return out * adsr(len(t), 0.002, 0.1, 0.8, 0.1) * np.exp(-t * 5)


def musicbox(f, dur):
    t = tt(dur)
    out = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 6) + \
        0.18 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 9)
    return out * adsr(len(t), 0.001, 0.05, 1.0, 0.2) * np.exp(-t * 2.2)


def flute(f, dur, seed=0):
    t = tt(dur)
    vib = 1 + 0.005 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.15) / 0.3, 0, 1)
    ph = 2 * np.pi * f * np.cumsum(vib) / SR
    out = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.07 * np.sin(3 * ph)
    breath = np.random.default_rng(seed + int(f)).normal(0, 1, len(t))
    breath = np.convolve(breath, np.ones(12) / 12, mode="same") * 0.05
    return (out + breath) * adsr(len(t), 0.07, 0.1, 0.85, 0.12)


def pad(freqs, dur, warmth=0.6):
    t = tt(dur)
    out = np.zeros_like(t)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t)
    for f in freqs:
        for det in (-0.0035, 0.0, 0.0035):
            for k in range(1, 7):
                amp = (1.0 / k ** (2.2 - warmth)) * (1.0 if k < 3 else 0.6 + 0.4 * lfo)
                out += amp * np.sin(2 * np.pi * f * (1 + det) * k * t + k * 1.3 + det * 400)
    return out / (len(freqs) * 3) * adsr(len(t), min(1.2, dur / 3), 0.1, 1.0, min(1.0, dur / 3))


def bass(f, dur):
    t = tt(dur)
    out = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3)
    out = np.tanh(out * 1.4)
    return out * adsr(len(t), 0.008, 0.2, 0.7, 0.08)


def kick():
    t = tt(0.4)
    f = 48 + 70 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)


def brush(seed, dur=0.18, level=1.0):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, int(SR * dur))
    n = np.convolve(n, [1, -0.85], mode="same")
    t = np.arange(len(n)) / SR
    return n * np.exp(-t * 22) * 0.25 * level


def shaker(seed):
    rng = np.random.default_rng(seed)
    n = np.diff(rng.normal(0, 1, int(SR * 0.07)), prepend=0)
    t = np.arange(len(n)) / SR
    return n * np.minimum(1, t / 0.01) * np.exp(-t * 55) * 0.18


def snare(seed):
    t = tt(0.22)
    n = np.random.default_rng(seed).normal(0, 1, len(t))
    n = np.convolve(n, [0.5, 0.5], mode="same")
    return (n * 0.55 + np.sin(2 * np.pi * 185 * t) * 0.35) * np.exp(-t * 16)


# ---------------------------------------------------------------- arrangement
class Song:
    def __init__(self, bpm, bars, beats=4):
        self.beat = 60.0 / bpm
        self.n = int(round(SR * self.beat * beats * bars))
        self.L = np.zeros(self.n)
        self.R = np.zeros(self.n)

    def add(self, beat, sig, vol, pan=0.0, swing=0.0):
        if swing and (beat * 2) % 2 == 1:
            beat += swing
        s = int(round(beat * self.beat * SR))
        idx = (np.arange(len(sig)) + s) % self.n
        np.add.at(self.L, idx, sig * vol * (1 - max(0.0, pan)))
        np.add.at(self.R, idx, sig * vol * (1 + min(0.0, pan)))

    def reverb(self, seconds=1.8, mix=0.25, seed=5):
        """Circular convolution: the tail wraps around, so the loop is seamless."""
        for ch, sd in ((0, seed), (1, seed + 1)):
            x = self.L if ch == 0 else self.R
            ir_len = int(SR * seconds)
            rng = np.random.default_rng(sd)
            ir = rng.normal(0, 1, ir_len) * np.exp(-np.arange(ir_len) / SR * (6.9 / seconds))
            ir = np.convolve(ir, np.ones(16) / 16, mode="same")
            ir[: int(SR * 0.012)] = 0  # pre-delay
            ir /= np.sqrt(np.sum(ir ** 2))
            h = np.zeros(self.n)
            h[:ir_len] = ir
            wet = np.real(np.fft.ifft(np.fft.fft(x) * np.fft.fft(h)))
            out = x * (1 - mix) + wet * mix * 2.0
            if ch == 0:
                self.L = out
            else:
                self.R = out

    def master(self):
        st = np.stack([self.L, self.R], axis=1)
        st = np.tanh(st / (np.max(np.abs(st)) + 1e-9) * 1.25)
        st = st / (np.max(np.abs(st)) + 1e-9) * 0.9
        return st


CH = {
    "C": [48, 52, 55, 60, 64], "Cmaj7": [48, 52, 55, 59, 64], "Cadd9": [48, 55, 62, 64, 67],
    "G": [43, 50, 55, 59, 62], "G/B": [47, 50, 55, 59, 62], "G7": [43, 50, 53, 59, 65], "Gsus": [43, 50, 55, 60, 62],
    "Am": [45, 52, 57, 60, 64], "Am7": [45, 52, 55, 60, 64], "Amadd9": [45, 52, 59, 60, 64],
    "F": [41, 48, 53, 57, 60], "Fmaj7": [41, 48, 52, 57, 60], "Fadd9": [41, 48, 55, 57, 60],
    "Dm7": [38, 45, 53, 57, 60], "Dm9": [38, 45, 52, 53, 57], "Em7": [40, 47, 50, 55, 59],
    "E7": [40, 47, 50, 56, 59], "D": [38, 45, 50, 54, 57], "Bm7": [35, 42, 50, 54, 57], "Em": [40, 47, 52, 55, 59],
    "Cmaj9": [36, 43, 50, 52, 59], "Bbmaj7": [46, 50, 53, 57, 62],
}


def chord_tones(name, lo, hi):
    pcs = {n % 12 for n in CH[name]}
    return [n for n in range(lo, hi + 1) if n % 12 in pcs]


def snap(note, name, lo=60, hi=88):
    tones = chord_tones(name, lo, hi)
    return min(tones, key=lambda n: abs(n - note))


def phrase(song, inst, motif, start_bar, chords_for_bar, transpose=0, vol=0.5, pan=0.0, beats=4):
    """motif: list of (beat_offset, dur_beats, note); notes on strong beats snap to the chord."""
    for (b, d, n) in motif:
        bar = start_bar + int(b // beats)
        ch = chords_for_bar(bar)
        note = n + transpose
        if b % 1 == 0:
            note = snap(note, ch)
        song.add(start_bar * beats + b, inst(nf(note), d * song.beat * 1.1), vol, pan)


def gen_title(path):
    s = Song(100, 16)
    prog = ["C", "G/B", "Am", "F", "C", "G", "F", "G"] * 2
    cb = lambda bar: prog[bar % len(prog)]
    for bar, ch in enumerate(prog):
        s.add(bar * 4, pad([nf(n) for n in CH[ch][1:4]], s.beat * 4.2), 0.35)
        s.add(bar * 4, bass(nf(CH[ch][0]), s.beat * 1.8), 0.5)
        s.add(bar * 4 + 2.5, bass(nf(CH[ch][0] + 7), s.beat * 1.3), 0.32)
        for k, b in enumerate([0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]):
            tones = CH[ch][2:]
            s.add(bar * 4 + b, guitar(nf(tones[k % len(tones)] + 12), s.beat * 1.5, seed=bar * 8 + k), 0.16, -0.35 + 0.1 * (k % 3))
        s.add(bar * 4, kick(), 0.4)
        s.add(bar * 4 + 2, snare(bar), 0.18)
        for b in range(8):
            s.add(bar * 4 + b * 0.5, shaker(bar * 8 + b), 0.5 if b % 2 else 0.3, 0.3)
    a = [(0, 1, 76), (1, 0.5, 74), (1.5, 0.5, 72), (2, 1.5, 74), (3.5, 0.5, 72), (4, 1, 72), (5, 1, 69), (6, 2, 71)]
    b = [(0, 1, 72), (1, 1, 74), (2, 1, 76), (3, 1, 79), (4, 1.5, 77), (5.5, 0.5, 76), (6, 2, 74)]
    for start, m in ((0, a), (2, b), (4, a), (6, b), (8, a), (10, b), (12, a)):
        phrase(s, marimba, m, start, cb, 0, 0.42, 0.2)
    phrase(s, marimba, [(0, 2, 72), (2, 2, 67), (4, 4, 72)], 14, cb, 0, 0.42, 0.2)
    s.reverb(1.6, 0.22)
    write(path, s.master())


def gen_morning(path):
    s = Song(84, 16)
    prog = ["G", "D", "Em", "Cadd9", "G", "D", "Cadd9", "Gsus"] * 2
    cb = lambda bar: prog[bar % len(prog)]
    for bar, ch in enumerate(prog):
        s.add(bar * 4, pad([nf(n) for n in CH[ch][1:4]], s.beat * 4.2, 0.4), 0.28)
        s.add(bar * 4, bass(nf(CH[ch][0]), s.beat * 3.5), 0.38)
        arp = [0, 2, 3, 4, 3, 2, 4, 3]
        for k in range(8):
            s.add(bar * 4 + k * 0.5, guitar(nf(CH[ch][arp[k]] + 12), s.beat * 2.0, seed=bar * 9 + k), 0.2, -0.3 if k % 2 else 0.25)
    a = [(0, 1.5, 74), (1.5, 0.5, 76), (2, 2, 79), (4, 1, 78), (5, 1, 76), (6, 2, 74)]
    b = [(0, 1, 71), (1, 1, 74), (2, 1.5, 76), (3.5, 0.5, 74), (4, 2, 72), (6, 2, 71)]
    for start, m in ((2, a), (4, b), (6, a), (10, a), (12, b)):
        phrase(s, flute, m, start, cb, 0, 0.3, 0.1)
    for bar in (0, 8, 14):
        for k, n in enumerate([86, 83, 79, 81]):
            s.add(bar * 4 + k, musicbox(nf(n), 1.8), 0.12, 0.4)
    s.reverb(2.2, 0.3)
    write(path, s.master())


def gen_day(path):
    s = Song(94, 16)
    prog = ["Fmaj7", "Em7", "Dm7", "Cmaj7", "Fmaj7", "Em7", "Dm7", "G7"] * 2
    cb = lambda bar: prog[bar % len(prog)]
    for bar, ch in enumerate(prog):
        c = CH[ch]
        for b, dur in ((0, 1.4), (1.5, 0.9), (2.5, 1.4)):
            for n in c[1:]:
                s.add(bar * 4 + b, epiano(nf(n + 12), s.beat * dur), 0.11, -0.15, swing=0.08)
        s.add(bar * 4, bass(nf(c[0]), s.beat * 1.4), 0.5)
        s.add(bar * 4 + 1.5, bass(nf(c[0] + 12), s.beat * 0.45), 0.3, swing=0.08)
        s.add(bar * 4 + 2, bass(nf(c[0] + 7), s.beat * 1.4), 0.42)
        s.add(bar * 4, kick(), 0.5)
        s.add(bar * 4 + 2.5, kick(), 0.3, swing=0.08)
        s.add(bar * 4 + 1, snare(bar * 2), 0.22)
        s.add(bar * 4 + 3, snare(bar * 2 + 1), 0.22)
        for k in range(8):
            s.add(bar * 4 + k * 0.5, brush(bar * 8 + k, level=1.0 if k % 2 == 0 else 0.6), 0.6, 0.35, swing=0.08)
    a = [(0, 0.5, 72), (0.5, 0.5, 74), (1, 1, 76), (2, 0.5, 79), (2.5, 1.5, 76), (4, 1, 74), (5, 0.5, 72), (5.5, 2.5, 71)]
    b = [(0, 1, 69), (1, 0.5, 72), (1.5, 0.5, 74), (2, 2, 76), (4, 0.5, 74), (4.5, 0.5, 72), (5, 3, 74)]
    for start, m in ((2, a), (4, b), (6, a), (10, a), (12, b), (14, a)):
        phrase(s, marimba, m, start, cb, 0, 0.36, 0.25)
    s.reverb(1.4, 0.2)
    write(path, s.master())


def gen_evening(path):
    s = Song(76, 16)
    prog = ["Dm9", "G7", "Cmaj7", "Am7", "Dm9", "G7", "Cmaj9", "E7"] * 2
    cb = lambda bar: prog[bar % len(prog)]
    for bar, ch in enumerate(prog):
        c = CH[ch]
        for n in c[1:]:
            s.add(bar * 4, epiano(nf(n + 12), s.beat * 3.6), 0.12, -0.2)
        s.add(bar * 4 + 2.5, epiano(nf(c[3] + 24), s.beat * 1.2), 0.07, 0.3, swing=0.12)
        s.add(bar * 4, bass(nf(c[0]), s.beat * 2.0), 0.5)
        s.add(bar * 4 + 2, bass(nf(c[0] + 7), s.beat * 1.6), 0.38)
        for k in range(4):
            s.add(bar * 4 + k, brush(bar * 4 + k, 0.4, 0.9), 0.7, 0.3)
            s.add(bar * 4 + k + 0.66, brush(bar * 4 + k + 99, 0.12, 0.5), 0.5, 0.3)
        s.add(bar * 4, kick(), 0.32)
    a = [(0, 1.5, 77), (1.5, 0.5, 76), (2, 1, 74), (3, 1, 72), (4, 3, 74), (7, 1, 72)]
    b = [(0, 1, 76), (1, 1, 79), (2, 2, 76), (4, 1.5, 74), (5.5, 0.5, 72), (6, 2, 71)]
    for start, m in ((2, a), (4, b), (10, a), (12, b)):
        phrase(s, flute, m, start, cb, -12, 0.32, 0.1)
    s.reverb(2.4, 0.3)
    write(path, s.master())


def gen_night(path):
    s = Song(64, 16)
    prog = ["Amadd9", "Fmaj7", "Cmaj7", "G", "Amadd9", "Fmaj7", "Dm9", "Em7"] * 2
    cb = lambda bar: prog[bar % len(prog)]
    for bar, ch in enumerate(prog):
        c = CH[ch]
        s.add(bar * 4, pad([nf(n) for n in c[1:]], s.beat * 4.4, 0.25), 0.4)
        s.add(bar * 4, bass(nf(c[0]), s.beat * 3.8), 0.22)
    rng = np.random.default_rng(3)
    for bar, ch in enumerate(prog):
        tones = chord_tones(ch, 76, 91)
        for b in (0, 1.5, 2.5) if bar % 2 == 0 else (0.5, 2):
            if rng.random() < 0.85:
                s.add(bar * 4 + b, musicbox(nf(int(rng.choice(tones))), 2.5), 0.16, float(rng.uniform(-0.5, 0.5)))
    a = [(0, 2, 76), (2, 1, 74), (3, 1, 72), (4, 4, 71)]
    for start in (4, 12):
        phrase(s, flute, a, start, cb, -12, 0.2, -0.1)
    s.reverb(3.0, 0.42)
    write(path, s.master())


def write(path, st):
    data = (np.clip(st, -1, 1) * 32767).astype("<i2")
    tmp = path + ".wav"
    with wave.open(tmp, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    if path.endswith(".ogg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", "4", path], check=True)
        os.remove(tmp)
    else:
        os.replace(tmp, path)


def gen_music(out):
    os.makedirs(out, exist_ok=True)
    gen_title(os.path.join(out, "music_title.ogg"))
    gen_morning(os.path.join(out, "music_morning.ogg"))
    gen_day(os.path.join(out, "music_day.ogg"))
    gen_evening(os.path.join(out, "music_evening.ogg"))
    gen_night(os.path.join(out, "music_night.ogg"))
