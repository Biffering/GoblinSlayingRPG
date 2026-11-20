"""Weather ambience for Goblin Slayer: seamless loops (birds, breeze, rain, storm, ash crackle, night hum) and thunder."""
import os
import subprocess
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(__file__))
from sfxlib import bp, env, hp, lp, noise, sine, sweep

SR = 44100
rng = np.random.default_rng(11)


def t_of(d):
    return np.arange(int(SR * d)) / SR


def seamless(x, xfade=1.0):
    """Crossfade the tail into the head so the loop has no click."""
    n = int(SR * xfade)
    head, tail = x[:n].copy(), x[-n:]
    w = np.linspace(0, 1, n)
    x = x[:-n].copy()
    x[:n] = head * w + tail * (1 - w)
    return x


def place(buf, s, t):
    i = int(t * SR)
    j = min(len(buf), i + len(s))
    buf[i:j] += s[:j - i]


def chirp(f0, f1, d):
    s = sine(sweep(f0, f1, d), d) * env(d, attack=0.004, decay_pow=1.5)
    return s


def birds(dur=12.0):
    out = np.zeros(int(SR * dur))
    t = 0.3
    while t < dur - 1.0:
        kind = rng.integers(3)
        base = rng.uniform(2600, 4200)
        if kind == 0:      # tweet-tweet
            for k in range(rng.integers(2, 5)):
                place(out, chirp(base, base * 1.35, 0.06) * 0.5, t + k * 0.11)
        elif kind == 1:    # falling whistle
            place(out, chirp(base * 1.3, base * 0.8, 0.22) * 0.4, t)
        else:              # trill
            d = 0.35
            tt = t_of(d)
            s = np.sin(2 * np.pi * (base * tt + 30 * np.sin(2 * np.pi * 28 * tt) / (2 * np.pi))) * env(d, attack=0.02)
            place(out, s * 0.3, t)
        t += rng.uniform(0.5, 1.8)
    leaves = lp(noise(dur), 1800) * 0.05
    return seamless(out + leaves)


def wind(dur=10.0, strength=1.0):
    n = noise(dur)
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * t_of(dur) / dur * 3 + 0.5) * np.sin(2 * np.pi * t_of(dur) / dur * 2)
    s = bp(n, 250, 1400) * gust * 0.7 * strength + bp(n, 1500, 4000) * (gust ** 3) * 0.12 * strength
    return seamless(s)


def rain(dur=8.0, heavy=False):
    n = noise(dur)
    s = hp(lp(n, 7000), 600) * (0.55 if not heavy else 0.85)
    drops = np.zeros(int(SR * dur))
    for _ in range(int(dur * (40 if not heavy else 90))):
        d = 0.012
        place(drops, hp(noise(d), 2500) * env(d, attack=0) * rng.uniform(0.2, 0.6), rng.uniform(0, dur - 0.02))
    low = lp(n, 300) * (0.25 if heavy else 0.1)
    return seamless(s + drops + low)


def ash(dur=8.0):
    out = lp(noise(dur), 500) * 0.25
    for _ in range(int(dur * 30)):
        d = 0.006
        place(out, hp(noise(d), 3000) * env(d, attack=0) * rng.uniform(0.2, 0.9), rng.uniform(0, dur - 0.01))
    return seamless(out)


def hum(dur=10.0):
    tt = t_of(dur)
    s = (np.sin(2 * np.pi * 55 * tt) * 0.3 + np.sin(2 * np.pi * 82.5 * tt) * 0.15) * (0.7 + 0.3 * np.sin(2 * np.pi * tt / dur * 2))
    return seamless(s + bp(noise(dur), 2000, 6000) * 0.03)


def thunder(seed):
    r = np.random.default_rng(seed)
    d = 3.5
    n = noise(d)
    crack = hp(noise(0.25), 900) * env(0.25, attack=0, decay_pow=3) * 0.9
    rumble = lp(n, 160) * env(d, attack=0.06, decay_pow=1.2) * 2.4
    rumble2 = lp(n, 420) * env(d, attack=0.15, decay_pow=2.0) * 0.8
    out = rumble + rumble2
    place(out, crack, r.uniform(0.0, 0.1))
    # rolling echoes
    for k in range(3):
        place(out, lp(noise(0.8), 250) * env(0.8, attack=0.1) * 0.6, 0.6 + k * 0.7 + r.uniform(0, 0.3))
    return out


def write(out_dir, name, x, ogg=True, peak=-3.0):
    x = x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak / 20)
    wav = os.path.join("/tmp", name + ".wav")
    wavfile.write(wav, SR, (x * 32767).astype(np.int16))
    if ogg:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "4",
                        os.path.join(out_dir, name + ".ogg")], check=True)
    else:
        os.replace(wav, os.path.join(out_dir, name + ".wav"))
    print(name)


if __name__ == "__main__" and len(sys.argv) == 2:
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    write(out, "amb_birds", birds())
    write(out, "amb_breeze", wind(10, 0.8))
    write(out, "amb_gale", wind(10, 1.0) + wind(10, 0.6)[::-1] * 0.5)
    write(out, "amb_rain", rain(8))
    write(out, "amb_storm", rain(8, heavy=True) + wind(8, 0.5))
    write(out, "amb_ash", ash())
    write(out, "amb_hum", hum())
    write(out, "thunder1", thunder(1), ogg=False, peak=-1.0)
    write(out, "thunder2", thunder(2), ogg=False, peak=-1.0)


def clash():
    """The loud CHINK of two blades meeting: inharmonic metal partials, a spark of noise and a ringing tail."""
    d = 2.2
    tt = t_of(d)
    out = np.zeros_like(tt)
    for f, a, dec in [(1870, 0.9, 2.2), (2960, 0.7, 2.8), (4410, 0.55, 3.5), (5230, 0.4, 4.0), (7020, 0.3, 5.5), (930, 0.5, 3.0)]:
        out += a * np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * np.exp(-tt * dec)
    out += hp(noise(d), 3000) * np.exp(-tt * 40) * 1.6
    out += lp(noise(d), 200) * np.exp(-tt * 18) * 1.2
    # a short slapback echo, like a canyon
    e = np.zeros_like(out)
    k = int(0.11 * SR)
    e[k:] = out[:-k] * 0.35
    return out + e


def stab():
    d = 0.35
    tt = t_of(d)
    return lp(noise(d), 1500) * np.exp(-tt * 14) + np.sin(2 * np.pi * 110 * tt) * np.exp(-tt * 20) * 0.8


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[2] == "clash":
    write(sys.argv[1], "sword_clash", clash(), ogg=False, peak=-0.5)
    write(sys.argv[1], "impact", stab(), ogg=False, peak=-2.0)
