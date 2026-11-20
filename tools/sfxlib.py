"""Synthesizes retro sound effects for Squad Surge as 16-bit mono WAV files."""
import sys
import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
OUT = "."
rng = np.random.default_rng(7)


def t_of(dur):
    return np.arange(int(SR * dur)) / SR


def phase(freq, dur):
    """freq: scalar or array (per-sample) -> phase in cycles."""
    n = int(SR * dur)
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    return np.cumsum(f) / SR


def sine(freq, dur):
    return np.sin(2 * np.pi * phase(freq, dur))


def square(freq, dur, duty=0.5):
    return np.where((phase(freq, dur) % 1.0) < duty, 1.0, -1.0)


def tri(freq, dur):
    p = phase(freq, dur) % 1.0
    return 4 * np.abs(p - 0.5) - 1


def saw(freq, dur):
    return 2 * (phase(freq, dur) % 1.0) - 1


def noise(dur):
    return rng.uniform(-1, 1, int(SR * dur))


def sweep(f0, f1, dur, curve="exp"):
    x = t_of(dur) / dur
    if curve == "exp":
        return f0 * (f1 / f0) ** x
    return f0 + (f1 - f0) * x


def env(dur, attack=0.002, decay_pow=1.0, release=None):
    n = int(SR * dur)
    x = np.linspace(0, 1, n, endpoint=False)
    e = (1 - x) ** decay_pow
    a = int(SR * attack)
    if a > 0:
        e[:a] *= np.linspace(0, 1, a)
    return e


def adsr(dur, a=0.005, d=0.05, s=0.7, r=0.1):
    n = int(SR * dur)
    e = np.full(n, s)
    na, nd, nr = int(SR * a), int(SR * d), int(SR * r)
    e[:na] = np.linspace(0, 1, na) if na else e[:na]
    e[na:na + nd] = np.linspace(1, s, len(e[na:na + nd]))
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lp(x, cutoff, order=2):
    sos = butter(order, min(cutoff, SR / 2 - 100), "low", fs=SR, output="sos")
    return sosfilt(sos, x)


def hp(x, cutoff, order=2):
    sos = butter(order, cutoff, "high", fs=SR, output="sos")
    return sosfilt(sos, x)


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], "band", fs=SR, output="sos")
    return sosfilt(sos, x)


def sweep_lp(x, c0, c1):
    """Crude time-varying low-pass: blocks with decreasing cutoff."""
    out = np.zeros_like(x)
    blocks = 24
    edges = np.linspace(0, len(x), blocks + 1).astype(int)
    for i in range(blocks):
        c = c0 * (c1 / c0) ** (i / (blocks - 1))
        seg = x[max(0, edges[i] - 256):edges[i + 1]]
        f = lp(seg, c)
        out[edges[i]:edges[i + 1]] = f[-(edges[i + 1] - edges[i]):]
    return out


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def seq(*parts, gap=0.0):
    g = np.zeros(int(SR * gap))
    out = []
    for p in parts:
        out += [p, g]
    return np.concatenate(out)


def at(x, offset, total=None):
    pad = np.zeros(int(SR * offset))
    return np.concatenate([pad, x])


def crush(x, bits=6):
    q = 2 ** bits
    return np.round(x * q) / q


def note(n):
    """Note name like 'C5', 'F#4' -> Hz."""
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    name, octave = n[:-1], int(n[-1])
    midi = 12 * (octave + 1) + names[name]
    return 440 * 2 ** ((midi - 69) / 12)


def fade_tail(x, ms=8):
    n = int(SR * ms / 1000)
    x = x.copy()
    x[-n:] *= np.linspace(1, 0, n)
    return x


def save(name, x, peak_db=-1.0):
    x = fade_tail(np.asarray(x, dtype=float))
    x = x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak_db / 20)
    wavfile.write(os.path.join(OUT, name + ".wav"), SR, (x * 32767).astype(np.int16))
    print(f"{name}.wav  {len(x) / SR:.2f}s")


# ---------------------------------------------------------------- gameplay

def s_shoot():
    d = 0.075
    tone = square(sweep(1500, 420, d), d, duty=0.25) * env(d, decay_pow=2)
    hiss = hp(noise(0.02), 3000) * env(0.02, decay_pow=3) * 0.4
    return lp(mix(tone * 0.7, hiss), 6000)


def s_hit():
    d = 0.045
    click = hp(noise(d), 1800) * env(d, attack=0, decay_pow=4)
    blip = tri(sweep(1100, 700, d), d) * env(d, decay_pow=2) * 0.6
    return mix(click * 0.7, blip)


def s_enemy_die():
    d = 0.22
    n = sweep_lp(noise(d), 5000, 300) * env(d, attack=0, decay_pow=2)
    body = sine(sweep(520, 70, d), d) * env(d, decay_pow=1.5)
    return crush(mix(n * 0.8, body * 0.9), 7)


def s_brute_die():
    d = 0.45
    n = sweep_lp(noise(d), 3500, 120) * env(d, attack=0, decay_pow=1.6)
    body = square(sweep(240, 40, d), d) * env(d, decay_pow=2) * 0.5
    thump = sine(sweep(120, 40, 0.2), 0.2) * env(0.2, decay_pow=1.5)
    return crush(mix(n, body, thump), 6)


def s_crate_hit():
    d = 0.07
    body = tri(sweep(260, 150, d), d) * env(d, attack=0, decay_pow=3)
    knock = bp(noise(0.03), 600, 2500) * env(0.03, attack=0, decay_pow=4) * 0.6
    return mix(body, knock)


def s_powerup():
    notes = ["C5", "E5", "G5", "C6", "E6"]
    parts = []
    for i, nm in enumerate(notes):
        d = 0.055 if i < len(notes) - 1 else 0.28
        f = note(nm) * (1 + 0.012 * np.sin(2 * np.pi * 18 * t_of(d)))
        parts.append(square(f, d, duty=0.25) * adsr(d, a=0.002, d=0.02, s=0.6, r=min(0.2, d * 0.6)))
    arp = np.concatenate(parts)
    sparkle = mix(*[at(sine(note(nm) * 2, 0.12) * env(0.12, decay_pow=3) * 0.25, 0.22 + 0.04 * i)
                    for i, nm in enumerate(["C6", "G6", "E6", "C7"])])
    return mix(arp * 0.7, sparkle)


def s_squad_hurt():
    d = 0.3
    growl = saw(sweep(260, 55, d), d) * env(d, decay_pow=1.3)
    growl = np.tanh(growl * 3) * 0.6
    n = lp(noise(0.12), 1500) * env(0.12, attack=0, decay_pow=2)
    return lp(mix(growl, n), 3000)


def s_shield_block():
    d = 0.4
    partials = [(1250, 1.0), (1930, 0.6), (2710, 0.45), (3820, 0.25)]
    ring = mix(*[sine(f, d) * a * env(d, attack=0, decay_pow=3 + i) for i, (f, a) in enumerate(partials)])
    clank = hp(noise(0.02), 2500) * env(0.02, attack=0, decay_pow=3) * 0.8
    return mix(ring, clank)


def s_boss_alarm():
    parts = []
    for i in range(6):
        f = 620 if i % 2 == 0 else 880
        d = 0.2
        parts.append(square(f, d, duty=0.5) * adsr(d, a=0.005, d=0.02, s=0.8, r=0.03))
    alarm = np.concatenate(parts)
    alarm = lp(alarm, 3500)
    rumble = sine(55, len(alarm) / SR) * 0.5 * np.linspace(0.3, 1, len(alarm))
    return mix(alarm * 0.7, rumble) * np.minimum(1, np.linspace(1.6, 0, len(alarm)) * 1.5)


def s_boss_hit():
    d = 0.12
    thud = sine(sweep(140, 60, d), d) * env(d, attack=0, decay_pow=2)
    crack = lp(noise(0.05), 2500) * env(0.05, attack=0, decay_pow=3) * 0.6
    return mix(thud, crack)


def s_boss_die():
    d = 2.0
    boom = sweep_lp(noise(d), 6000, 80) * env(d, attack=0, decay_pow=2.2)
    rumble = sine(sweep(70, 28, d), d) * env(d, decay_pow=1.2) * 0.9
    crackles = np.zeros(int(SR * d))
    for _ in range(18):
        pos = rng.uniform(0.05, 1.3)
        cl = hp(noise(0.03), 1500) * env(0.03, attack=0, decay_pow=3) * rng.uniform(0.2, 0.6)
        s = int(pos * SR)
        crackles[s:s + len(cl)] += cl[:len(crackles) - s]
    return np.tanh(mix(boom, rumble, crackles) * 1.4)


# ---------------------------------------------------------------- jingles

def voice(nm, d, kind="square", duty=0.5, vib=0.0, rel=0.08):
    f = note(nm)
    if vib:
        f = f * (1 + vib * np.sin(2 * np.pi * 6 * t_of(d)))
    if kind == "square":
        w = square(f, d, duty)
    elif kind == "tri":
        w = tri(f, d)
    else:
        w = saw(f, d)
    return w * adsr(d, a=0.004, d=0.04, s=0.75, r=min(rel, d * 0.5))


def melody(notes, kind="square", duty=0.5, vib=0.0):
    return np.concatenate([voice(n, d, kind, duty, vib) for n, d in notes])


def s_victory():
    lead = melody([("G4", 0.11), ("C5", 0.11), ("E5", 0.11), ("G5", 0.22), ("E5", 0.11), ("G5", 0.7)],
                  duty=0.25, vib=0.006)
    bass = melody([("C3", 0.33), ("G2", 0.33), ("C3", 0.8)], kind="tri")
    harm = at(voice("C6", 0.7, "square", 0.125, vib=0.006) * 0.35, 0.77)
    return lp(mix(lead * 0.6, bass * 0.7, harm), 7000)


def s_defeat():
    lead = melody([("G4", 0.25), ("F#4", 0.25), ("F4", 0.25), ("E4", 0.8)], kind="saw", vib=0.0)
    # sad "wah" droop on the last note
    tail_len = int(SR * 0.8)
    lead[-tail_len:] *= np.linspace(1, 0.2, tail_len)
    bass = melody([("C3", 0.75), ("C2", 0.8)], kind="tri")
    return lp(mix(lead * 0.5, bass * 0.7), 2200)


def s_level_start():
    whoosh = bp(noise(0.45), 400, 4000) * np.sin(np.linspace(0, np.pi, int(SR * 0.45))) ** 2 * 0.35
    notes = mix(at(voice("C5", 0.1, duty=0.25), 0.1), at(voice("G5", 0.25, duty=0.25), 0.2))
    return mix(whoosh, notes * 0.6)


# ---------------------------------------------------------------- UI / tally

def s_tally_tick():
    d = 0.03
    return square(1050, d, 0.25) * env(d, attack=0.001, decay_pow=2)


def s_tally_row():
    d = 0.35
    return mix(sine(1568, d) * env(d, attack=0, decay_pow=3),
               sine(3136, d) * env(d, attack=0, decay_pow=5) * 0.3,
               hp(noise(0.01), 4000) * 0.3)


def s_tally_total():
    ching1 = mix(sine(2093, 0.5) * env(0.5, attack=0, decay_pow=3), sine(2637, 0.5) * env(0.5, attack=0, decay_pow=4) * 0.6)
    ching2 = mix(sine(2637, 0.7) * env(0.7, attack=0, decay_pow=3), sine(3136, 0.7) * env(0.7, attack=0, decay_pow=4) * 0.6)
    shimmer = hp(noise(0.5), 6000) * env(0.5, attack=0.01, decay_pow=2) * 0.25
    clunk = lp(noise(0.05), 1200) * env(0.05, attack=0, decay_pow=3) * 0.8
    return mix(clunk, ching1 * 0.6, at(ching2 * 0.7, 0.09), at(shimmer, 0.09))


def s_coins():
    a = square(note("B5"), 0.07, 0.5) * adsr(0.07, a=0.001, d=0.01, s=0.8, r=0.005)
    b = square(note("E6"), 0.35, 0.5) * env(0.35, attack=0.001, decay_pow=1.5)
    return lp(np.concatenate([a, b]), 8000) * 0.8


def s_click():
    d = 0.03
    return mix(tri(sweep(1800, 900, d), d) * env(d, attack=0, decay_pow=4),
               hp(noise(0.006), 3000) * 0.5)


def s_new_best():
    notes = ["E6", "G6", "C7", "E7", "G7"]
    parts = [sine(note(nm), 0.06) * env(0.06, decay_pow=1) for nm in notes]
    run = np.concatenate(parts)
    ring = at(sine(note("C7"), 0.5) * env(0.5, attack=0, decay_pow=3) * 0.6, len(run) / SR)
    return mix(run, ring)


# ---------------------------------------------------------------- super weapon

def s_super_spawn():
    notes = ["E6", "B6", "E7", "G#7"]
    run = np.concatenate([sine(note(n), 0.05) * env(0.05, decay_pow=1) for n in notes])
    ring = at(mix(sine(note("E7"), 0.6) * env(0.6, attack=0, decay_pow=3),
                  sine(note("B7"), 0.6) * env(0.6, attack=0, decay_pow=4) * 0.5), len(run) / SR)
    shimmer = hp(noise(0.6), 7000) * env(0.6, attack=0.05, decay_pow=2) * 0.2
    return mix(run, ring * 0.7, shimmer)


def s_super_pickup():
    d = 0.7
    rise = square(sweep(200, 2400, d), d, duty=0.3) * np.linspace(0.3, 1, int(SR * d)) * 0.4
    rise = lp(rise, 5000)
    chord = mix(*[at(saw(note(n), 0.9) * env(0.9, attack=0.01, decay_pow=1.5) * 0.25, 0.55)
                  for n in ["C5", "E5", "G5", "C6", "E6"]])
    return mix(rise, lp(chord, 6000))


def s_super_blast():
    d = 2.2
    boom = sweep_lp(noise(d), 9000, 90) * env(d, attack=0, decay_pow=2.5)
    sub = sine(sweep(90, 25, d), d) * env(d, decay_pow=1.4)
    whoosh = bp(noise(1.0), 300, 3000) * np.sin(np.linspace(0, np.pi, int(SR * 1.0))) ** 2 * 0.5
    return np.tanh(mix(boom * 1.2, sub * 1.1, at(whoosh, 0.1)) * 1.5)


def s_super_zap():
    d = 0.06
    z = square(sweep(2600, 700, d), d, duty=0.5) * env(d, attack=0, decay_pow=2)
    return lp(z, 7000) * 0.8


def s_explosion():
    d = 0.5
    n = sweep_lp(noise(d), 7000, 150) * env(d, attack=0, decay_pow=2.2)
    thump = sine(sweep(160, 40, 0.25), 0.25) * env(0.25, decay_pow=1.5)
    return crush(np.tanh(mix(n, thump) * 1.6), 7)


