"""Parametric composer for Six Hearths: each track is a spec (key, mode, tempo, instruments, groove)
and a seeded melody generator writes motif-based tunes (A A' B A'') over the chord progression."""
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import synth as S
from synth import (Song, adsr, bp, clap, crash, expenv, hat, hp, kick, lp, noise, osc_saw, osc_sin, osc_sq,
                   osc_tri, pad, pluck, snare, stab, tom, tt, bass_saw, bass_tri, bass_acid, guitar, lead)

SR = 44100
MODES = {
    "major": [0, 2, 4, 5, 7, 9, 11], "minor": [0, 2, 3, 5, 7, 8, 10], "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10], "lydian": [0, 2, 4, 6, 7, 9, 11], "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "harmonic": [0, 2, 3, 5, 7, 8, 11], "locrian": [0, 1, 3, 5, 6, 8, 10],
}
ROOTS = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def mhz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


class Key:
    def __init__(self, root, mode, octave=4):
        self.base = 12 * (octave + 1) + ROOTS[root]
        self.sc = MODES[mode]

    def deg(self, d, octave=0):
        """Scale degree (0-based, can exceed 6 or go negative) -> midi."""
        o, i = divmod(d, 7)
        return self.base + 12 * (o + octave) + self.sc[i]

    def chord(self, d, octave=0, n=3):
        return [self.deg(d + 2 * k, octave) for k in range(n)]


# ------------------------------------------------------------------ extra instruments

def bell(f, d, bright=1.0):
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) + 0.5 * bright * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6) \
        + 0.25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 12)
    return x * np.exp(-t * 2.2) * adsr(d, 0.002, 0.0, 1.0, 0.05)


def flute(f, d, vib=0.012):
    t = tt(d)
    v = np.clip((t - 0.1) / 0.2, 0, 1) * vib
    fv = f * (1 + v * np.sin(2 * np.pi * 5.2 * t))
    x = osc_sin(fv, d) * 0.8 + osc_tri(fv, d) * 0.25
    breath = bp(noise(d), f * 0.9, min(f * 3, 16000)) * 0.08
    return (x + breath) * adsr(d, 0.04, 0.1, 0.8, min(0.08, d * 0.4))


def organ(notes, d):
    x = np.zeros(len(tt(d)))
    for m in notes:
        f = mhz(m)
        x += osc_sin(f, d) + 0.5 * osc_sin(f * 2, d) + 0.3 * osc_sin(f * 3, d) + 0.15 * osc_sin(f * 4, d)
    return x / (len(notes) * 2) * adsr(d, 0.02, 0.1, 0.85, 0.1)


def marimba(f, d):
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 30)
    return x * np.exp(-t * 7)


def harp(f, d):
    return lp(osc_tri(f, d), 5000) * expenv(d, 4.5) * adsr(d, 0.002, 0, 1, 0.03)


def choir(notes, d, cut=2200):
    x = np.zeros(len(tt(d)))
    t = tt(d)
    for m in notes:
        f = mhz(m)
        for det in (-0.004, 0.003, 0.0):
            fv = f * (1 + det) * (1 + 0.006 * np.sin(2 * np.pi * 5 * t + det * 100))
            x += osc_saw(fv, d)
    x = bp(x, 400, cut) * 0.6 + lp(x, 900) * 0.4
    return x / (len(notes) * 3) * adsr(d, 0.35, 0.2, 0.85, min(0.4, d * 0.3))


def piano(f, d):
    t = tt(d)
    x = osc_saw(f, d) * 0.5 + osc_sq(f * 1.001, d, 0.5) * 0.3 + osc_sin(f * 2, d) * 0.2
    x = lp(x, 2600) * np.exp(-t * 3.5)
    return x * adsr(d, 0.002, 0.0, 1.0, 0.05)


def strings(notes, d):
    return pad([mhz(m) for m in notes], d, cut=2000, attack=0.25)


def anvil(d=0.5):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((1180, 1), (1830, 0.6), (2610, 0.4), (3900, 0.2)))
    return x * np.exp(-t * 9) + hp(noise(0.02), 3000).tolist().__len__() * 0  # placeholder for shape


def anvil_hit(d=0.5):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((1180, 1), (1830, 0.6), (2610, 0.4), (3900, 0.2)))
    x = x * np.exp(-t * 9)
    x[:int(0.02 * SR)] += hp(noise(0.02), 3000) * 0.8
    return x


def shaker(d=0.08):
    return hp(noise(d), 6000) * expenv(d, 40) * adsr(d, 0.01, 0, 1, 0.01)


def taiko(d=0.5):
    return tom(70, d) * 1.3


def drip(f=1800):
    d = 0.15
    t = tt(d)
    return np.sin(2 * np.pi * (f + 900 * np.exp(-t * 40)) * t) * np.exp(-t * 30)


# ------------------------------------------------------------------ melody generator

RHYTHMS = [[4, 2, 2, 4, 4], [2, 2, 2, 2, 8], [3, 1, 4, 4, 4], [8, 4, 4], [4, 4, 8], [6, 2, 4, 4], [2, 2, 4, 2, 2, 4],
           [4, 4, 4, 4], [3, 3, 2, 8], [12, 4]]
CALM = [[8, 8], [12, 4], [4, 4, 8], [8, 4, 4], [16], [6, 2, 8]]


ARCH = [0.35, 0.5, 0.62, 0.78, 0.92, 0.8, 0.58, 0.3]


def make_bar(rnd, key, chord_deg, prev, calm, lo, hi, end_on_root=False, target=None):
    rh = rnd.choice(CALM if calm else RHYTHMS)
    notes = []
    pos = 0
    cur = prev
    if target is None:
        target = (lo + hi) / 2
    chord_tones = [chord_deg + 2 * k for k in range(3)]
    direction = 1 if target > cur else -1
    for i, ln in enumerate(rh):
        strong = pos % 8 == 0
        if strong or ln >= 8:
            cands = [ct + o for ct in chord_tones for o in (-7, 0, 7, 14) if lo <= ct + o <= hi]
            # aim at the phrase contour, with a little freedom
            aim = target + rnd.uniform(-1.5, 1.5)
            cands.sort(key=lambda c: abs(c - aim) + rnd.random() * 0.8)
            cur = cands[0] if cands else cur
        else:
            if abs(target - cur) > 1.5:
                direction = 1 if target > cur else -1
            elif rnd.random() < 0.35:
                direction = -direction
            step = direction * rnd.choice([1, 1, 1, 2]) if rnd.random() < 0.85 else 0
            cur = max(lo, min(hi, cur + step))
        if end_on_root and i == len(rh) - 1:
            cands = [chord_deg + o for o in (-7, 0, 7, 14) if lo <= chord_deg + o <= hi]
            cur = min(cands, key=lambda c: abs(c - cur)) if cands else cur
        rest = rnd.random() < (0.07 if not calm else 0.03) and i > 0 and not strong
        notes.append((pos, ln, None if rest else cur))
        pos += ln
    return notes, cur


def compose_melody(rnd, key, prog, bars, calm=False, lo=0, hi=9):
    """prog: chord degree per bar (cycled). Returns list of (step, length, degree|None) over all bars."""
    out = []
    cur = 4
    motif_a, motif_b = [], []
    for bar in range(bars):
        phrase_bar = bar % 8
        chord = prog[bar % len(prog)]
        target = lo + (hi - lo) * ARCH[phrase_bar] + (1.5 if bar >= 8 else 0)
        if phrase_bar in (0, 1) and (bar < 8 or not motif_a):
            notes, cur = make_bar(rnd, key, chord, cur, calm, lo, hi, target=target)
            motif_a.append(notes)
        elif phrase_bar in (2, 3) and len(motif_a) >= 2:
            # A': same rhythm as A, notes nudged toward the new chord
            src = motif_a[phrase_bar - 2]
            notes = [(p, l, (d + rnd.choice([0, 0, 1, -1]) if d is not None else None)) for p, l, d in src]
        elif phrase_bar in (4, 5):
            notes, cur = make_bar(rnd, key, chord, cur, calm, lo, hi, target=target)
            motif_b.append(notes)
        elif phrase_bar == 6 and motif_a:
            notes = motif_a[0]
        else:
            notes, cur = make_bar(rnd, key, chord, cur, calm, lo, hi, end_on_root=(phrase_bar == 7), target=target)
        for p, l, d in notes:
            out.append((bar * 16 + p, l, d))
    return out


# ------------------------------------------------------------------ track renderer

def render(spec):
    rnd = random.Random(spec["seed"])
    key = Key(spec["root"], spec["mode"], spec.get("octave", 4))
    bars = spec.get("bars", 16)
    s = Song(spec["bpm"], bars)
    prog = spec["prog"]          # chord degree per bar
    groove = spec.get("drums", "none")
    kicks = []
    for bar in range(bars):
        b0 = bar * 16
        chord = prog[bar % len(prog)]
        cn = key.chord(chord, -1)
        # ---- harmony
        hz = spec.get("harmony", "pad")
        if hz == "pad" and bar % 2 == 0:
            s.place(pad([mhz(m) for m in cn + [cn[0] + 12]], s.dur(32), cut=spec.get("pad_cut", 1500), attack=0.5), b0, "pad", gain=0.5)
        elif hz == "strings" and bar % 2 == 0:
            s.place(strings(cn + [cn[0] + 12], s.dur(32)), b0, "pad", gain=0.5)
        elif hz == "choir" and bar % 2 == 0:
            s.place(choir(cn + [cn[0] + 12], s.dur(32)), b0, "pad", gain=0.7)
        elif hz == "organ":
            s.place(organ(cn, s.dur(16)), b0, "pad", gain=0.55)
        elif hz == "stabs":
            for st in (2, 6, 10, 14):
                s.place(stab([mhz(m + 12) for m in cn], s.dur(1.6)), b0 + st, "pad", pan=0.2 if st % 4 else -0.2, gain=0.35)
            if bar % 4 == 0:
                s.place(pad([mhz(m) for m in cn], s.dur(64), cut=900, attack=1.0), b0, "pad2", gain=0.35)
        elif hz == "guitar":
            for st in range(0, 16, 2):
                s.place(guitar(mhz(cn[0]), s.dur(1.9), mute=(st % 8 != 0)), b0 + st, "gtr", pan=-0.4, gain=0.42)
                s.place(guitar(mhz(cn[0]) * 1.003, s.dur(1.9), mute=(st % 8 != 0)), b0 + st + 0.06, "gtr", pan=0.4, gain=0.38)
        # arpeggio layer
        arp = spec.get("arp")
        if arp:
            tones = cn + [cn[0] + 12, cn[1] + 12]
            pattern = [0, 1, 2, 3, 4, 3, 2, 1]
            step = spec.get("arp_step", 1)
            for i in range(0, 16, step):
                m = tones[pattern[(i // step) % 8]] + 12
                inst = {"harp": lambda f, d: harp(f, d), "marimba": marimba, "bell": lambda f, d: bell(f, d, 0.6),
                        "pluck": lambda f, d: pluck(f, d, 0.25, 4000, 14), "piano": piano,
                        "chip": lambda f, d: pluck(f, d, 0.125, 6000, 20)}[arp]
                s.place(inst(mhz(m), s.dur(step * 1.5)), b0 + i, "arp", pan=0.3 if (i // step) % 2 else -0.3,
                        gain=spec.get("arp_gain", 0.2))
        # ---- bass
        bs = spec.get("bass", "eighths")
        root = mhz(cn[0] - 12)
        if bs == "eighths":
            for i in range(8):
                s.place(bass_saw(root, s.dur(1.8), cut=600), b0 + i * 2, "bass", gain=0.7)
        elif bs == "quarters":
            for i in range(4):
                s.place(bass_saw(root if i % 2 == 0 else root * 1.5, s.dur(3.6), cut=500), b0 + i * 4, "bass", gain=0.65)
        elif bs == "oompah":
            for i in range(4):
                f = root if i % 2 == 0 else root * 1.5
                s.place(bass_tri(f, s.dur(1.5)), b0 + i * 4, "bass", gain=0.8)
        elif bs == "octave":
            for i in range(8):
                s.place(bass_tri(root * (1 if i % 2 == 0 else 2), s.dur(1.8)), b0 + i * 2, "bass", gain=0.75)
        elif bs == "drone":
            if bar % 4 == 0:
                s.place(lp(osc_saw(root, s.dur(64)) + osc_saw(root * 1.004, s.dur(64)), 300) * adsr(s.dur(64), 1.0, 0.5, 0.8, 1.0),
                        b0, "bass", gain=0.5)
        elif bs == "acid":
            pat = [0, 0, 12, 0, 3, 0, 7, 0, 0, 10, 0, 12, 5, 0, 3, 7]
            cut = 400 + 1400 * (0.5 - 0.5 * np.cos(2 * np.pi * bar / 8))
            for i in range(16):
                s.place(bass_acid(root * 2 ** (pat[i] / 12), s.dur(1.1), cut), b0 + i, "bass", gain=0.42)
        elif bs == "walking":
            sc = [0, 2, 4, 5, 7, 5, 4, 2]
            for i in range(4):
                s.place(bass_tri(mhz(key.deg(chord + sc[(bar * 4 + i) % 8] // 2, -2)), s.dur(3.6)), b0 + i * 4, "bass", gain=0.8)
        elif bs == "guitar_root":
            for i in range(8):
                s.place(bass_saw(root, s.dur(1.8), cut=900, drive=1.4), b0 + i * 2, "bass", gain=0.7)
        # ---- drums
        if groove == "soft":
            s.place(kick(0.3, 0.6), b0, "drums", gain=0.6)
            s.place(kick(0.3, 0.6), b0 + 10, "drums", gain=0.45)
            s.place(snare(0.3, 170), b0 + 8, "drums", gain=0.3)
            for i in range(0, 16, 4):
                s.place(shaker(), b0 + i + 2, "drums", pan=0.3, gain=0.25)
        elif groove == "shaker":
            for i in range(0, 16, 2):
                s.place(shaker(), b0 + i, "drums", pan=0.3 if i % 4 else -0.3, gain=0.2 + (0.1 if i % 4 == 0 else 0))
        elif groove == "march":
            for k in (0, 8):
                s.place(kick(0.3), b0 + k, "drums", gain=0.7)
            for k in (4, 12, 14):
                s.place(snare(0.15, 220), b0 + k, "drums", gain=0.5)
            for i in range(0, 16, 2):
                s.place(hat(), b0 + i, "drums", gain=0.15)
        elif groove == "rock":
            for k in (0, 6, 8, 11):
                s.place(kick(0.3, 1.2), b0 + k, "drums", gain=0.85)
                kicks.append(b0 + k)
            s.place(snare(), b0 + 4, "drums", gain=0.7)
            s.place(snare(), b0 + 12, "drums", gain=0.7)
            for i in range(0, 16, 2):
                s.place(hat(), b0 + i, "drums", pan=0.25, gain=0.25)
            if bar % 4 == 3:
                for j, k in enumerate(range(12, 16)):
                    s.place(tom(170 - j * 20), b0 + k, "drums", gain=0.5)
        elif groove == "double":
            for i in range(16):
                s.place(kick(0.18, 1.3), b0 + i, "drums", gain=0.5 if i % 4 else 0.75)
            s.place(snare(0.25, 180), b0 + 4, "drums", gain=0.8)
            s.place(snare(0.25, 180), b0 + 12, "drums", gain=0.8)
            for i in range(0, 16, 2):
                s.place(hat(), b0 + i, "drums", gain=0.2)
        elif groove == "techno":
            for q in range(4):
                s.place(kick(0.35, 1.2), b0 + q * 4, "drums", gain=0.9)
                kicks.append(b0 + q * 4)
                s.place(hat(True), b0 + q * 4 + 2, "drums", pan=0.3, gain=0.22)
            s.place(clap(), b0 + 4, "drums", gain=0.4)
            s.place(clap(), b0 + 12, "drums", gain=0.4)
        elif groove == "chip":
            for k in (0, 8, 10):
                s.place(kick(0.2), b0 + k, "drums", gain=0.7)
            for k in (4, 12):
                s.place(snare(0.15, 230), b0 + k, "drums", gain=0.55)
            for i in range(0, 16, 2):
                s.place(hat(), b0 + i, "drums", gain=0.2)
        elif groove == "taiko":
            for k in (0, 3, 8, 11):
                s.place(taiko(), b0 + k, "drums", gain=0.7 if k in (0, 8) else 0.45)
            s.place(snare(0.2, 200), b0 + 12, "drums", gain=0.35)
            for i in range(2, 16, 4):
                s.place(shaker(), b0 + i, "drums", gain=0.2)
        elif groove == "sparse":
            if bar % 2 == 0:
                s.place(kick(0.5, 0.5), b0, "drums", gain=0.5)
            if bar % 4 == 2:
                s.place(snare(0.4, 150), b0 + 8, "drums", gain=0.25)
        # dungeon flavor hits
        fl = spec.get("flavor")
        if fl == "anvil" and bar % 2 == 1:
            s.place(anvil_hit(), b0 + 6, "fx", pan=-0.4, gain=0.25)
        elif fl == "drips":
            for _ in range(2):
                s.place(drip(rnd.uniform(1400, 2600)), b0 + rnd.randrange(16), "fx", pan=rnd.uniform(-0.8, 0.8), gain=0.25)
        elif fl == "wind":
            if bar % 4 == 0:
                w = bp(noise(s.dur(64)), 300, 1600) * np.sin(np.linspace(0, np.pi, len(tt(s.dur(64))))) ** 2
                s.place(w, b0, "fx", gain=0.22)
        elif fl == "static":
            if rnd.random() < 0.5:
                s.place(hp(noise(0.06), 2000) * 0.5, b0 + rnd.randrange(16), "fx", pan=rnd.uniform(-0.6, 0.6), gain=0.2)
        elif fl == "chimes":
            if bar % 2 == 0:
                s.place(bell(mhz(cn[2] + 24), s.dur(8), 0.4), b0 + rnd.randrange(8), "fx", pan=rnd.uniform(-0.6, 0.6), gain=0.12)
        if bar % 8 == 0 and groove in ("rock", "double", "march", "chip"):
            s.place(crash(), b0, "drums", gain=0.4)
    # ---- melody
    mel = spec.get("lead")
    if mel:
        start_bar = spec.get("lead_from", 0)
        notes = compose_melody(rnd, key, prog, bars - start_bar, calm=spec.get("calm", False),
                               lo=spec.get("lo", 0), hi=spec.get("hi", 9))
        for st, ln, d in notes:
            if d is None:
                continue
            m = key.deg(d, spec.get("lead_oct", 0 if spec.get("hi", 9) >= 11 else 1))
            f = mhz(m)
            dur = s.dur(ln) * 0.92
            inst = {"pulse": lambda: lead(f, dur, 0.25, 0.009), "square": lambda: lead(f, dur, 0.5, 0.01),
                    "saw": lambda: lead(f, dur, kind="saw", vib=0.008, cut=3500), "tri": lambda: lead(f, dur, kind="tri"),
                    "flute": lambda: flute(f, dur), "bell": lambda: bell(f, dur), "piano": lambda: piano(f, dur),
                    "marimba": lambda: marimba(f, dur)}[mel]
            s.place(inst(), start_bar * 16 + st, "lead", pan=0.1, gain=spec.get("lead_gain", 0.3))
        s.echo("lead", delay_steps=3, fb=0.3, mix=spec.get("echo", 0.25))
    if "arp" in s.buses:
        s.echo("arp", delay_steps=3, fb=0.25, mix=0.2)
    if kicks and "pad" in s.buses and groove == "techno":
        s.pump("pad", kicks, depth=0.6)
    gains = {"pad": 1.0, "pad2": 1.0, "arp": 1.0, "bass": 0.9, "drums": spec.get("drum_gain", 1.0), "lead": 1.0, "gtr": 0.9, "fx": 1.0}
    return s.render(gains)


def jingle_victory():
    s = Song(150, 4)
    key = Key("C", "major", 4)
    melody = [(0, 2, 7), (2, 2, 7), (4, 2, 7), (6, 6, 7), (12, 4, 5), (16, 4, 6), (20, 4, 7), (24, 2, 6), (26, 6, 7)]
    for st, ln, d in melody:
        s.place(lead(mhz(key.deg(d, 1)), s.dur(ln) * 0.9, 0.25), st, "lead", gain=0.35)
        s.place(lead(mhz(key.deg(d - 2, 1)), s.dur(ln) * 0.9, 0.5), st, "lead", gain=0.18)
    for st, c in ((0, 0), (12, 3), (16, 4), (24, 0)):
        s.place(pad([mhz(m) for m in key.chord(c, -1)], s.dur(8), cut=2500, attack=0.05), st, "pad", gain=0.5)
        s.place(kick(0.3), st, "drums", gain=0.6)
    s.place(crash(), 24, "drums", gain=0.5)
    out = s.render({"lead": 1.0, "pad": 1.0, "drums": 1.0})
    return out[:, : int(SR * 3.4)]


def track_specs():
    T = {}
    T["title"] = dict(seed=1, root="D", mode="phrygian", bpm=74, prog=[0, 1, 0, 6, 0, 1, 5, 4], harmony="choir", arp="piano",
                      arp_step=4, arp_gain=0.12, bass="drone", drums="taiko", lead="saw", lead_gain=0.17, calm=True,
                      lead_from=4, flavor="anvil")
    T["nexus"] = dict(seed=2, root="D", mode="mixolydian", bpm=88, prog=[0, 6, 3, 4], harmony="pad", arp="bell", arp_step=2,
                      arp_gain=0.14, bass="quarters", drums="soft", lead="flute", calm=True, lead_from=2)
    T["battle"] = dict(seed=3, root="E", mode="minor", bpm=150, prog=[0, 0, 5, 6, 0, 0, 3, 4], harmony="guitar", bass="guitar_root",
                       drums="rock", lead="pulse", lead_gain=0.26, lo=2, hi=11)
    T["boss"] = dict(seed=4, root="C", mode="phrygian", bpm=164, prog=[0, 1, 0, 6, 0, 1, 5, 4], harmony="guitar", bass="guitar_root",
                     drums="double", lead="saw", lead_gain=0.22, lo=2, hi=11, arp="chip", arp_gain=0.1)
    T["omni"] = dict(seed=5, root="D", mode="harmonic", bpm=172, prog=[0, 5, 3, 4, 0, 5, 1, 4], harmony="choir", arp="chip",
                     arp_gain=0.12, bass="eighths", drums="double", lead="saw", lead_gain=0.24, lo=3, hi=12)
    T["gameover"] = dict(seed=6, root="A", mode="minor", bpm=66, bars=8, prog=[0, 5, 3, 4], harmony="pad", bass="drone",
                         lead="piano", calm=True, lead_gain=0.35)
    T["ending"] = dict(seed=7, root="F", mode="major", bpm=84, bars=24, prog=[0, 4, 5, 3, 0, 4, 3, 4], harmony="strings", arp="harp",
                       arp_step=2, bass="quarters", drums="soft", lead="flute", calm=True, lead_from=4, flavor="chimes")
    worlds = {
        "fire": dict(town=dict(root="D", mode="harmonic", bpm=92, prog=[0, 3, 4, 0, 5, 3, 4, 4], harmony="pad", arp="marimba",
                               arp_step=2, bass="oompah", drums="taiko", lead="marimba", lead_gain=0.32),
                     field=dict(root="E", mode="minor", bpm=132, prog=[0, 5, 3, 6, 0, 5, 3, 4], harmony="pad", arp="pluck",
                                bass="eighths", drums="taiko", lead="saw", lead_gain=0.24),
                     dungeon=dict(root="E", mode="phrygian", bpm=108, prog=[0, 1, 0, 6], harmony="organ", bass="drone",
                                  drums="sparse", lead="square", lead_gain=0.18, calm=True, lead_from=4, flavor="anvil")),
        "water": dict(town=dict(root="F", mode="major", bpm=84, prog=[0, 3, 5, 4, 0, 3, 1, 4], harmony="pad", arp="harp",
                                arp_step=2, bass="quarters", drums="shaker", lead="flute", calm=True),
                      field=dict(root="D", mode="dorian", bpm=118, prog=[0, 3, 0, 6, 0, 3, 4, 4], harmony="pad", arp="harp",
                                 bass="eighths", drums="soft", lead="tri", lead_gain=0.32),
                      dungeon=dict(root="Bb", mode="minor", bpm=86, prog=[0, 5, 3, 4], harmony="pad", pad_cut=900, bass="drone",
                                   drums="none", lead="bell", calm=True, lead_from=4, flavor="drips", echo=0.4)),
        "wind": dict(town=dict(root="G", mode="lydian", bpm=100, prog=[0, 1, 0, 4, 5, 1, 3, 4], harmony="pad", arp="pluck",
                               arp_step=2, bass="walking", drums="soft", lead="flute"),
                     field=dict(root="D", mode="major", bpm=144, prog=[0, 4, 5, 3, 0, 4, 3, 4], harmony="pad", arp="chip",
                                bass="octave", drums="chip", lead="pulse", lead_gain=0.26, lo=2, hi=11),
                     dungeon=dict(root="B", mode="lydian", bpm=110, prog=[0, 1, 3, 4], harmony="organ", arp="bell", arp_step=2,
                                  arp_gain=0.12, bass="quarters", drums="sparse", lead="flute", calm=True, flavor="wind")),
        "stone": dict(town=dict(root="C", mode="mixolydian", bpm=96, prog=[0, 6, 3, 4, 0, 6, 3, 0], harmony="pad", arp=None,
                                bass="oompah", drums="march", lead="saw", lead_gain=0.26),
                      field=dict(root="A", mode="minor", bpm=126, prog=[0, 3, 4, 0, 5, 3, 4, 4], harmony="strings", bass="eighths",
                                 drums="march", lead="square", lead_gain=0.24),
                      dungeon=dict(root="E", mode="minor", bpm=98, prog=[0, 5, 0, 4], harmony="pad", pad_cut=800, bass="drone",
                                   drums="sparse", lead="tri", calm=True, lead_from=2, flavor="anvil")),
        "spirit": dict(town=dict(root="E", mode="major", bpm=76, prog=[0, 3, 4, 3, 0, 5, 3, 4], harmony="choir", arp="bell",
                                 arp_step=2, arp_gain=0.12, bass="quarters", drums="none", lead="bell", calm=True, flavor="chimes"),
                       field=dict(root="A", mode="lydian", bpm=112, prog=[0, 1, 4, 3, 0, 1, 5, 4], harmony="pad", arp="harp",
                                  bass="eighths", drums="soft", lead="flute"),
                       dungeon=dict(root="C#", mode="minor", bpm=94, prog=[0, 5, 3, 4], harmony="organ", bass="drone",
                                    drums="sparse", lead="bell", calm=True, flavor="chimes", echo=0.35)),
        "void": dict(town=dict(root="F#", mode="minor", bpm=70, prog=[0, 5, 3, 4], harmony="pad", pad_cut=900, arp="piano",
                               arp_step=4, arp_gain=0.15, bass="drone", drums="none", lead="piano", calm=True, flavor="static"),
                     field=dict(root="B", mode="locrian", bpm=106, prog=[0, 1, 4, 5], harmony="stabs", arp="chip", arp_gain=0.12,
                                bass="acid", drums="techno", lead="square", lead_gain=0.18, lead_from=4, flavor="static"),
                     dungeon=dict(root="F#", mode="locrian", bpm=86, prog=[0, 1, 0, 4], harmony="pad", pad_cut=700, bass="drone",
                                  drums="sparse", lead="bell", calm=True, lead_from=4, flavor="static", echo=0.45)),
    }
    seed = 100
    for w, kinds in worlds.items():
        for k, spec in kinds.items():
            seed += 1
            spec = dict(spec)
            spec["seed"] = seed
            T[f"{w}_{k}"] = spec
    T["goblin_dungeon"] = dict(seed=880, root="G", mode="phrygian", bpm=118, prog=[0, 1, 0, 6, 0, 1, 5, 4], harmony="stabs",
                               arp="marimba", arp_step=1, arp_gain=0.13, bass="oompah", drums="march", lead="square",
                               lead_gain=0.22, bars=16, flavor="anvil")
    T["king_goblin"] = dict(seed=881, root="C", mode="harmonic", bpm=170, prog=[0, 1, 0, 6, 0, 5, 1, 4], harmony="guitar",
                            bass="guitar_root", drums="double", lead="saw", lead_gain=0.24, lo=2, hi=11, arp="chip", arp_gain=0.1)
    # building themes: each world's town key, rearranged for the mood of the room
    tavern_lead = {"fire": "marimba", "water": "flute", "wind": "pulse", "stone": "saw", "spirit": "bell", "void": "piano"}
    tavern_drums = {"fire": "taiko", "water": "shaker", "wind": "soft", "stone": "march", "spirit": "shaker", "void": "sparse"}
    for w, kinds in worlds.items():
        tw = kinds["town"]
        seed += 1
        T[f"{w}_shop"] = dict(seed=seed, root=tw["root"], mode="major" if tw["mode"] in ("major", "lydian", "mixolydian") else "dorian",
                              bpm=tw["bpm"] + 14, prog=[0, 3, 4, 0, 5, 3, 1, 4], harmony="pad", arp="marimba", arp_step=2,
                              arp_gain=0.14, bass="walking", drums="soft", lead="bell" if w != "fire" else "marimba",
                              lead_gain=0.28, calm=True, bars=16)
        seed += 1
        T[f"{w}_inn"] = dict(seed=seed, root=tw["root"], mode="major" if w != "void" else "dorian", bpm=64,
                             prog=[0, 5, 3, 4, 0, 3, 4, 0], harmony="strings" if w != "void" else "pad", arp="harp", arp_step=2,
                             arp_gain=0.12, bass="drone", drums="none", lead="flute", calm=True, lead_from=2, bars=16,
                             flavor="chimes" if w in ("spirit", "wind") else None)
        seed += 1
        T[f"{w}_tavern"] = dict(seed=seed, root=tw["root"], mode="mixolydian" if w not in ("void", "fire") else "dorian",
                                bpm=118 if w != "void" else 96, prog=[0, 3, 4, 0, 0, 3, 4, 4], harmony="pad", arp="pluck",
                                arp_step=1, arp_gain=0.12, bass="oompah", drums=tavern_drums[w], lead=tavern_lead[w],
                                lead_gain=0.3, bars=16)
    return T


if __name__ == "__main__":
    out, tmp = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    S.OUT, S.TMP = out, tmp
    os.makedirs(tmp, exist_ok=True)
    only = sys.argv[3:]
    specs = track_specs()
    for name, spec in specs.items():
        if only and name not in only:
            continue
        S.write(name, render(spec))
    if not only or "victory" in only:
        S.write("victory", jingle_victory())
