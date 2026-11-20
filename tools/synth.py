"""Composes and renders looping retro music tracks for Squad Surge.

Each track is rendered as an exact loop (note tails wrap to the start), written as
WAV and then encoded to OGG Vorbis by ffmpeg.
"""
import os
import subprocess
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
OUT = "."
TMP = "/tmp"
rng = np.random.default_rng(42)

NOTE_IDX = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
            "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def hz(n):
    if isinstance(n, (int, float)):
        return float(n)
    name, octv = n[:-1], int(n[-1])
    return 440.0 * 2 ** ((12 * (octv + 1) + NOTE_IDX[name] - 69) / 12)


def shift(n, semis):
    return hz(n) * 2 ** (semis / 12)


# ------------------------------------------------------------------ DSP helpers

def tt(d):
    return np.arange(max(1, int(SR * d))) / SR


def ph(f, d):
    n = max(1, int(SR * d))
    f = np.broadcast_to(np.asarray(f, dtype=float), (n,))
    return np.cumsum(f) / SR


def osc_saw(f, d):
    return 2 * (ph(f, d) % 1) - 1


def osc_sq(f, d, duty=0.5):
    return np.where(ph(f, d) % 1 < duty, 1.0, -1.0)


def osc_tri(f, d):
    return 4 * np.abs(ph(f, d) % 1 - 0.5) - 1


def osc_sin(f, d):
    return np.sin(2 * np.pi * ph(f, d))


def noise(d):
    return rng.uniform(-1, 1, max(1, int(SR * d)))


def _sos(kind, c, order=2):
    if kind == "band":
        lo, hi = c
        return butter(order, [max(20, lo), min(hi, SR / 2 - 200)], "band", fs=SR, output="sos")
    return butter(order, min(max(c, 20), SR / 2 - 200), kind, fs=SR, output="sos")


def lp(x, c, order=2):
    return sosfilt(_sos("low", c, order), x)


def hp(x, c, order=2):
    return sosfilt(_sos("high", c, order), x)


def bp(x, lo, hi, order=2):
    return sosfilt(_sos("band", (lo, hi), order), x)


def expenv(d, k):
    """Exponential decay; k = decays per second."""
    return np.exp(-tt(d) * k)


def adsr(d, a=0.005, dc=0.08, s=0.7, r=0.05):
    n = len(tt(d))
    e = np.full(n, s, dtype=float)
    na, nd, nr = int(SR * a), int(SR * dc), min(int(SR * r), n)
    na = min(na, n)
    if na:
        e[:na] = np.linspace(0, 1, na)
    nd = min(nd, n - na)
    if nd > 0:
        e[na:na + nd] = np.linspace(1, s, nd)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def resonant_lp(x, c, q=0.6):
    """Low-pass with a fake resonance bump (adds a band-pass around the cutoff)."""
    return lp(x, c) + q * bp(x, c * 0.8, c * 1.25)


# ------------------------------------------------------------------ instruments

def kick(d=0.32, punch=1.0):
    f = 45 + 110 * np.exp(-tt(d) * 30)
    body = osc_sin(f, d) * expenv(d, 9)
    click = hp(noise(0.006), 2000) * 0.4 * punch
    out = body.copy()
    out[:len(click)] += click
    return np.tanh(out * 1.6)


def snare(d=0.2, tone=190):
    n = bp(noise(d), 1200, 9000) * expenv(d, 18)
    t = osc_sin(tone * (1 + 0.5 * np.exp(-tt(d) * 40)), d) * expenv(d, 30) * 0.6
    return n + t


def clap(d=0.25):
    out = np.zeros(len(tt(d)))
    for i, off in enumerate([0, 0.011, 0.022]):
        s = int(off * SR)
        burst = bp(noise(d - off), 900, 5000) * expenv(d - off, 40 if i < 2 else 14)
        out[s:s + len(burst)] += burst[:len(out) - s]
    return out


def hat(open_=False):
    d = 0.22 if open_ else 0.045
    return hp(noise(d), 7000) * expenv(d, 14 if open_ else 70)


def crash(d=1.6):
    return hp(noise(d), 4500) * expenv(d, 2.6) * 0.8


def tom(f=110, d=0.25):
    return osc_sin(f * (1 + 0.6 * np.exp(-tt(d) * 25)), d) * expenv(d, 12)


def bass_saw(n, d, cut=700, drive=1.0):
    f = hz(n)
    x = osc_saw(f, d) * 0.7 + osc_sq(f / 2, d) * 0.3
    x = lp(x, cut, order=4)
    return np.tanh(x * 1.5 * drive) * adsr(d, 0.003, 0.08, 0.75, 0.02)


def bass_acid(n, d, cut, res=0.9):
    f = hz(n)
    x = osc_saw(f, d)
    cenv = cut * (0.45 + 1.4 * np.exp(-tt(d) * 18))
    # block-wise time-varying filter
    out = np.zeros_like(x)
    blocks = 6
    edges = np.linspace(0, len(x), blocks + 1).astype(int)
    for i in range(blocks):
        c = cenv[min(edges[i], len(cenv) - 1)]
        seg = x[max(0, edges[i] - 128):edges[i + 1]]
        fseg = resonant_lp(seg, c, res)
        out[edges[i]:edges[i + 1]] = fseg[-(edges[i + 1] - edges[i]):]
    return np.tanh(out * 2.0) * adsr(d, 0.002, 0.05, 0.8, 0.015)


def bass_tri(n, d):
    return osc_tri(hz(n), d) * adsr(d, 0.002, 0.02, 0.9, 0.015)


def pluck(n, d, duty=0.25, cut=5000, decay=10):
    return lp(osc_sq(hz(n), d, duty), cut) * expenv(d, decay) * adsr(d, 0.001, 0.0, 1.0, 0.01)


def lead(n, d, duty=0.25, vib=0.007, kind="pulse", cut=6000):
    f = hz(n)
    t = tt(d)
    vibenv = np.clip((t - 0.12) / 0.15, 0, 1) * vib
    fv = f * (1 + vibenv * np.sin(2 * np.pi * 5.5 * t))
    if kind == "pulse":
        x = osc_sq(fv, d, duty)
    elif kind == "saw":
        x = osc_saw(fv, d) * 0.6 + osc_saw(fv * 1.006, d) * 0.4
    else:
        x = osc_tri(fv, d)
    return lp(x, cut) * adsr(d, 0.006, 0.08, 0.7, min(0.06, d * 0.4))


def pad(notes, d, cut=1400, attack=0.4):
    x = np.zeros(len(tt(d)))
    for n in notes:
        f = hz(n)
        for det in (-0.006, 0.0, 0.0065):
            x += osc_saw(f * (1 + det), d)
    x = lp(x / (len(notes) * 3), cut, order=2)
    return x * adsr(d, attack, 0.2, 0.85, min(0.4, d * 0.3))


def stab(notes, d, cut=2500):
    x = sum(osc_saw(hz(n), d) + osc_saw(hz(n) * 1.008, d) for n in notes) / (2 * len(notes))
    return lp(x, cut) * expenv(d, 9) * adsr(d, 0.002, 0.0, 1.0, 0.02)


def guitar(root, d, mute=False, drive=7.0):
    """Distorted power chord: root + fifth + octave."""
    f = hz(root)
    x = np.zeros(len(tt(d)))
    for mult, g in ((1.0, 1.0), (1.4983, 0.8), (2.0, 0.6)):
        x += g * (osc_saw(f * mult * 1.003, d) + osc_saw(f * mult * 0.997, d))
    x = np.tanh(x * drive / 4)
    x = lp(x, 1300 if mute else 3200, order=2)
    x = hp(x, 90)
    if mute:
        e = expenv(d, 22)
    else:
        e = adsr(d, 0.003, 0.15, 0.75, 0.03)
    return x * e


# ------------------------------------------------------------------ song container

class Song:
    def __init__(self, bpm, bars):
        self.step = 60.0 / bpm / 4  # 16th note
        self.bars = bars
        self.n = int(round(bars * 16 * self.step * SR))
        self.buses = {}

    def bus(self, name):
        if name not in self.buses:
            self.buses[name] = np.zeros((2, self.n))
        return self.buses[name]

    def place(self, sig, step, bus="main", pan=0.0, gain=1.0):
        b = self.bus(bus)
        start = int(round(step * self.step * SR)) % self.n
        sig = np.asarray(sig) * gain
        lg = np.cos((pan + 1) * np.pi / 4) * np.sqrt(2)
        rg = np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
        # wrap tails around to the start for a seamless loop
        pos, rem = start, sig
        while len(rem):
            take = min(len(rem), self.n - pos)
            b[0, pos:pos + take] += rem[:take] * lg
            b[1, pos:pos + take] += rem[:take] * rg
            rem = rem[take:]
            pos = 0

    def dur(self, steps):
        return steps * self.step

    def echo(self, bus, delay_steps=3, fb=0.35, mix=0.4, cut=3500):
        b = self.bus(bus)
        d = int(round(delay_steps * self.step * SR))
        wet = np.zeros_like(b)
        src = b.copy()
        for i in range(1, 6):
            g = mix * fb ** (i - 1)
            if g < 0.02:
                break
            shifted = np.roll(src, d * i, axis=1)
            # ping-pong
            if i % 2:
                shifted = shifted[::-1]
            wet += shifted * g
        wet[0] = lp(wet[0], cut)
        wet[1] = lp(wet[1], cut)
        self.buses[bus] = b + wet

    def pump(self, bus, kick_steps, depth=0.6, release=0.18):
        """Sidechain-style ducking keyed to kick positions."""
        env = np.ones(self.n)
        rel = np.exp(-tt(release * 2.5) * (1 / release) * 2)
        shape = 1 - depth * rel
        for s in kick_steps:
            start = int(round(s * self.step * SR)) % self.n
            idx = (start + np.arange(len(shape))) % self.n
            env[idx] = np.minimum(env[idx], shape)
        self.buses[bus] *= env

    def render(self, gains):
        out = np.zeros((2, self.n))
        for name, b in self.buses.items():
            out += b * gains.get(name, 1.0)
        # gentle master glue: soft clip + normalize
        out = np.tanh(out / (np.max(np.abs(out)) + 1e-9) * 1.4)
        out = out / (np.max(np.abs(out)) + 1e-9) * 0.89
        return out


def parse_line(text):
    """'E5:2 G5:2 -:4 A5:8' -> list of (step_offset, length, note)."""
    events, pos = [], 0
    for tok in text.split():
        n, ln = tok.split(":")
        ln = float(ln)
        if n != "-":
            events.append((pos, ln, n))
        pos += ln
    return events, pos


def write(name, audio):
    wav = os.path.join(TMP, name + ".wav")
    wavfile.write(wav, SR, (audio.T * 32767).astype(np.int16))
    ogg = os.path.join(OUT, name + ".ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "5", ogg], check=True)
    print(f"{name}.ogg  {audio.shape[1] / SR:.1f}s  {os.path.getsize(ogg) // 1024} KB")


