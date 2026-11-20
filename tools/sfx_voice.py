"""Monster voices and explosions for battle, made by simple formant (vowel) synthesis.

usage: python3 sfx_voice.py <sounds_dir>
grunt1-3   short "hnh!"/"ugh!" when an enemy takes a big hit
groan1-2   long "euuugghhh" when a critical or a weakness lands, or as they fall
shriek1    a high hurt screech (small creatures)
boom, boom_big   explosions for elemental weakness blasts
"""
import sys
import wave
import numpy as np
from scipy.signal import lfilter, butter

SR = 22050
rng = np.random.default_rng(7)

# vowel formants (F1, F2, F3) in Hz
V = {"eh": (530, 1840, 2480), "uh": (640, 1190, 2390), "oo": (300, 870, 2240), "ah": (730, 1090, 2440),
     "ae": (660, 1720, 2410), "er": (490, 1350, 1690)}


def write(path, x, gain=0.9):
    x = x / (np.max(np.abs(x)) + 1e-9) * gain
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def resonator(x, f, bw):
    """Two-pole resonant filter (a formant)."""
    r = np.exp(-np.pi * bw / SR)
    th = 2 * np.pi * f / SR
    return lfilter([1 - r], [1, -2 * r * np.cos(th), r * r], x)


def glottal(f0, n, jitter=0.02, fry=0.0):
    """Buzzy pulse train with wobble; `fry` adds the rattly sub-harmonic of a growl."""
    f = f0 * (1 + jitter * np.cumsum(rng.normal(0, 1, n)) / np.sqrt(np.arange(1, n + 1)))
    ph = np.cumsum(f / SR)
    saw = 2 * (ph % 1.0) - 1
    pulse = np.where((ph % 1.0) < 0.35, 1.0, -0.2) * 0.6 + saw * 0.4
    if fry:
        pulse *= 1 - fry + fry * (0.5 + 0.5 * np.sign(np.sin(np.pi * ph)))
    return pulse


def voice(dur, f0_from, f0_to, vowels, breath=0.25, fry=0.3, shape=(0.03, 0.6)):
    n = int(SR * dur)
    t = np.linspace(0, 1, n)
    f0 = f0_from * (f0_to / f0_from) ** t
    src = np.zeros(n)
    # sample the f0 curve through the pulse generator in chunks to follow the glide
    ph = np.cumsum(f0 / SR)
    saw = 2 * (ph % 1.0) - 1
    src = np.where((ph % 1.0) < 0.33, 1.0, -0.25) * 0.65 + saw * 0.35
    if fry:
        src *= 1 - fry + fry * (0.5 + 0.5 * np.sign(np.sin(np.pi * ph)))
    src += rng.normal(0, breath, n)
    # glide between vowels
    out = np.zeros(n)
    k = len(vowels)
    seg = n // k
    for i, vw in enumerate(vowels):
        a, b = i * seg, n if i == k - 1 else (i + 1) * seg + seg // 2
        b = min(n, b)
        piece = src[a:b]
        y = sum(resonator(piece, f, bw) * g for f, bw, g in zip(V[vw], (90, 120, 180), (1.0, 0.55, 0.25)))
        win = np.ones(b - a)
        fade = min(seg // 2, b - a)
        if i > 0:
            win[:fade] = np.linspace(0, 1, fade)
        if i < k - 1:
            win[-(seg // 2):] = np.linspace(1, 0, seg // 2)
        out[a:b] += y * win
    att, rel = shape
    env = np.minimum(1, t / max(1e-3, att)) * np.clip((1 - t) / max(1e-3, rel), 0, 1) ** 1.3
    out *= env
    # a little grit, then low-pass so it sits under the music
    out = np.tanh(out * 3.0)
    bb, aa = butter(2, 3800 / (SR / 2))
    return lfilter(bb, aa, out)


def boom(dur, low=55, bright=0.4):
    n = int(SR * dur)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    bb, aa = butter(2, 900 / (SR / 2))
    rumble = lfilter(bb, aa, noise) * np.exp(-t * 3.0)
    thump = np.sin(2 * np.pi * (low * (1 + 2 * np.exp(-t * 18))) * t) * np.exp(-t * 6.0)
    crack = noise * np.exp(-t * 40.0) * bright
    x = rumble * 1.5 + thump * 1.2 + crack
    return np.tanh(x * 1.6)


def laser(dur=0.32):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = 2600 * np.exp(-t * 9.0) + 380
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.45 * np.sign(np.sin(ph * 0.5)) + 0.25 * np.sin(ph * 3.01)
    x *= np.exp(-t * 7.0)
    x += rng.normal(0, 1, n) * np.exp(-t * 60.0) * 0.6
    return np.tanh(x * 1.4)


def laser_swing(dur=0.42):
    n = int(SR * dur)
    t = np.arange(n) / SR
    hum = np.sign(np.sin(2 * np.pi * 96 * t)) * 0.4 + np.sin(2 * np.pi * 192 * t) * 0.5
    sweep = np.sin(2 * np.pi * np.cumsum(500 + 1800 * np.sin(np.pi * t / dur)) / SR) * 0.5
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    x = (hum * (0.6 + 0.4 * np.sin(2 * np.pi * 22 * t)) + sweep) * env
    bb, aa = butter(2, 5000 / (SR / 2))
    return np.tanh(lfilter(bb, aa, x) * 1.5)


def build(out):
    write(f"{out}/grunt1.wav", voice(0.26, 150, 105, ["uh", "er"], fry=0.35, shape=(0.02, 0.55)))
    write(f"{out}/grunt2.wav", voice(0.22, 125, 90, ["ah", "uh"], fry=0.5, shape=(0.015, 0.5)))
    write(f"{out}/grunt3.wav", voice(0.3, 170, 115, ["eh", "uh"], fry=0.25, shape=(0.02, 0.6)))
    write(f"{out}/groan1.wav", voice(0.95, 140, 72, ["eh", "uh", "oo"], breath=0.3, fry=0.55, shape=(0.05, 0.45)))
    write(f"{out}/groan2.wav", voice(1.1, 118, 62, ["ae", "uh", "uh", "oo"], breath=0.35, fry=0.65, shape=(0.06, 0.5)))
    write(f"{out}/shriek1.wav", voice(0.45, 520, 300, ["ae", "eh"], breath=0.2, fry=0.15, shape=(0.01, 0.6)))
    write(f"{out}/boom.wav", boom(0.9))
    write(f"{out}/boom_big.wav", boom(1.6, 42, 0.6))
    write(f"{out}/laser.wav", laser())
    write(f"{out}/laser_swing.wav", laser_swing())


if __name__ == "__main__":
    build(sys.argv[1])
