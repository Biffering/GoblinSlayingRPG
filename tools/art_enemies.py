"""Enemies (14 species x 6 elements), minibosses, bosses, omnipotents, summons and map icons. All face RIGHT."""
import json
import math
import random
import sys

import numpy as np
from PIL import Image

from art_common import Canvas, hexc, mix, shade, sheet, save

K = (20, 14, 28, 255)
EL = {
    "fire":   {"main": "#ff5a2a", "dark": "#8a1a10", "light": "#ffd060"},
    "water":  {"main": "#3a8aff", "dark": "#1a3a8a", "light": "#b0e8ff"},
    "wind":   {"main": "#40d8c0", "dark": "#1a7a6a", "light": "#e0fff8"},
    "stone":  {"main": "#6ab84a", "dark": "#3a5a2a", "light": "#c8e8a0"},
    "spirit": {"main": "#f0eee0", "dark": "#a8a0c8", "light": "#ffffff"},
    "void":   {"main": "#9a50ff", "dark": "#2a1450", "light": "#e0c8ff"},
}
SIZES = {"s": (36, 28), "m": (44, 48), "l": (60, 56), "xl": (76, 72), "boss": (100, 100), "omni": (136, 124)}


class S:
    """Draw in normalized coordinates (0..1) on a canvas."""

    def __init__(self, c):
        self.c = c
        self.W, self.H = c.w, c.h

    def X(self, x):
        return x * self.W

    def Y(self, y):
        return y * self.H

    def e(self, x, y, rx, ry, col):
        self.c.ellipse(self.X(x), self.Y(y), rx * self.W, ry * self.H, col)

    def r(self, x, y, w, h, col):
        self.c.rect(round(self.X(x)), round(self.Y(y)), max(1, round(w * self.W)), max(1, round(h * self.H)), col)

    def l(self, x0, y0, x1, y1, col, w=1.0):
        self.c.line(self.X(x0), self.Y(y0), self.X(x1), self.Y(y1), col, max(1, w * self.W / 40))

    def p(self, pts, col):
        self.c.poly([(self.X(x), self.Y(y)) for x, y in pts], col)

    def px(self, x, y, col):
        self.c.px(round(self.X(x)), round(self.Y(y)), col)


def tint(base, el, t=0.45):
    return mix(hexc(base), hexc(EL[el]["main"]), t)


def eyes(s, x, y, el, r=0.025, n=1, gap=0.06):
    glow = hexc(EL[el]["light"]) if el in ("void", "spirit", "fire") else hexc("#ffeeaa")
    for i in range(n):
        s.e(x - i * gap, y, r * 1.2, r * 1.2, K)
        s.px(x - i * gap, y, glow)


def element_fx(c, el, rnd, amount=1.0):
    """Particle-style decorations based on the silhouette."""
    a = c.a
    H, W = a.shape[:2]
    filled = a[:, :, 3] > 0
    top = []
    for x in range(W):
        for y in range(H):
            if filled[y, x]:
                top.append((x, y))
                break
    E = EL[el]
    n = int(len(top) * 0.25 * amount)
    if el == "fire":
        for (x, y) in rnd.sample(top, min(n, len(top))):
            h = rnd.randrange(2, 5)
            for k in range(h):
                col = hexc(E["light"]) if k == h - 1 else hexc(E["main"])
                c.px(x, y - 1 - k, col)
            c.px(x, y - 1, hexc("#ffb040"))
    elif el == "water":
        for _ in range(int(6 * amount)):
            x, y = rnd.choice(top)
            yy = y + rnd.randrange(4, max(5, H // 2))
            c.px(x + rnd.randrange(-3, 4), min(H - 2, yy), hexc(E["light"]))
            c.px(x + rnd.randrange(-3, 4), min(H - 1, yy + 1), hexc(E["main"]))
        for y in range(H):
            for x in range(W):
                if filled[y, x] and rnd.random() < 0.02:
                    c.px(x, y, hexc(E["light"]))
    elif el == "wind":
        for _ in range(int(3 * amount) + 1):
            cx, cy = rnd.randrange(W), rnd.randrange(H // 2, H)
            r = rnd.randrange(3, 6)
            for t in range(10):
                ang = t * 0.5
                c.px(round(cx + math.cos(ang) * r * (1 - t / 14)), round(cy + math.sin(ang) * r * 0.5 * (1 - t / 14)),
                     (255, 255, 255, 200))
    elif el == "stone":
        for _ in range(int(W * H / 160 * amount)):
            x, y = rnd.randrange(W), rnd.randrange(H)
            if filled[y, x] and tuple(a[y, x][:3]) != K[:3]:
                c.rect(x, y, 2, 2, hexc("#6a6a62"))
                c.px(x, y, hexc("#a0a098"))
                if rnd.random() < 0.4:
                    c.px(x + 2, y, hexc(E["main"]))
    elif el == "spirit":
        for _ in range(int(8 * amount)):
            x, y = rnd.randrange(W), rnd.randrange(H)
            if not filled[y, x]:
                c.px(x, y, (255, 255, 240, 220))
                if rnd.random() < 0.4:
                    c.px(x + 1, y, (255, 255, 240, 120))
                    c.px(x - 1, y, (255, 255, 240, 120))
                    c.px(x, y + 1, (255, 255, 240, 120))
                    c.px(x, y - 1, (255, 255, 240, 120))
    elif el == "void":
        for y in range(H):
            for x in range(W):
                if filled[y, x] and tuple(a[y, x][:3]) != K[:3] and rnd.random() < 0.05:
                    c.px(x, y, hexc(E["dark"]) if rnd.random() < 0.6 else hexc(E["light"]))
        for _ in range(int(6 * amount)):
            x, y = rnd.randrange(W), rnd.randrange(H)
            if not filled[y, x]:
                c.px(x, y, hexc(E["light"]))


def finish(c, el, rnd, fx=1.0, alpha=None):
    c.outline()
    c.rim_light(0.2, 0.25)
    element_fx(c, el, rnd, fx)
    if alpha is not None:
        c.a[:, :, 3] = (c.a[:, :, 3].astype(int) * alpha // 255).astype("uint8")
    return c


# ------------------------------------------------------------------ species

def humanoid(s, el, coat, skin="#e0b090", hat=None, hunch=0.0, legs="#3a3040", lean=0.0):
    """A generic right-facing humanoid figure in normalized space."""
    sk = hexc(skin)
    s.l(0.42, 0.62, 0.38, 0.95, hexc(legs), 5)
    s.l(0.55, 0.62, 0.62, 0.95, shade(hexc(legs), -0.2), 5)
    s.r(0.32, 0.93, 0.12, 0.05, hexc("#2a2020"))
    s.r(0.58, 0.93, 0.12, 0.05, hexc("#2a2020"))
    s.p([(0.36 + lean, 0.32 + hunch), (0.64 + lean, 0.32 + hunch), (0.66, 0.66), (0.34, 0.66)], coat)
    s.e(0.52 + lean + hunch * 0.6, 0.22 + hunch, 0.13, 0.11, sk)
    return sk


def d_rat(s, el, rnd):
    fur = tint("#7a6a62", el)
    s.l(0.15, 0.7, 0.02, 0.5, shade(fur, -0.2), 3)   # tail
    s.l(0.02, 0.5, 0.06, 0.32, shade(fur, -0.2), 2)
    s.e(0.45, 0.68, 0.3, 0.22, fur)
    s.e(0.75, 0.6, 0.16, 0.15, shade(fur, 0.1))
    s.p([(0.85, 0.55), (0.98, 0.64), (0.85, 0.7)], shade(fur, 0.1))
    s.e(0.68, 0.42, 0.06, 0.1, shade(fur, 0.2))
    s.e(0.68, 0.43, 0.03, 0.06, hexc("#e0a0a0"))
    s.px(0.98, 0.64, hexc("#e07080"))
    s.r(0.3, 0.86, 0.06, 0.08, shade(fur, -0.3))
    s.r(0.6, 0.86, 0.06, 0.08, shade(fur, -0.3))
    eyes(s, 0.8, 0.56, el, 0.03)


def d_bum(s, el, rnd):
    coat = tint("#6a5a3a", el, 0.35)
    humanoid(s, el, coat, "#d0a080", hunch=0.06)
    s.r(0.38, 0.45, 0.1, 0.08, tint("#8a3a2a", el))  # patch
    s.e(0.56, 0.21, 0.14, 0.06, tint("#3a3a60", el, 0.4))  # beanie
    s.r(0.5, 0.31, 0.12, 0.04, hexc("#6a6050"))  # stubble
    s.l(0.62, 0.45, 0.82, 0.52, coat, 4)
    s.r(0.8, 0.4, 0.07, 0.16, hexc("#4a8a4a"))  # bottle
    s.r(0.82, 0.36, 0.03, 0.05, hexc("#4a8a4a"))
    eyes(s, 0.6, 0.27, el, 0.022)


def d_loiterer(s, el, rnd):
    hood = tint("#4a4a5a", el, 0.4)
    humanoid(s, el, hood, "#c09070", lean=-0.04)
    s.e(0.5, 0.2, 0.15, 0.13, shade(hood, 0.1))
    s.e(0.56, 0.23, 0.08, 0.08, hexc("#c09070"))
    s.r(0.4, 0.5, 0.24, 0.06, shade(hood, -0.25))  # pocket
    s.r(0.56, 0.13, 0.16, 0.04, tint("#a03030", el, 0.3))  # cap brim
    eyes(s, 0.6, 0.23, el, 0.02)


def d_undead(s, el, rnd):
    bone = mix(hexc("#d8d0b8"), hexc(EL[el]["main"]), 0.25)
    rag = tint("#3a3a30", el, 0.3)
    s.l(0.44, 0.62, 0.4, 0.95, bone, 3)
    s.l(0.55, 0.62, 0.6, 0.95, bone, 3)
    s.p([(0.38, 0.32), (0.62, 0.32), (0.6, 0.64), (0.4, 0.64)], rag)
    for k in range(4):
        s.l(0.42, 0.38 + k * 0.06, 0.58, 0.38 + k * 0.06, bone, 2)
    s.e(0.52, 0.2, 0.12, 0.11, bone)
    s.r(0.55, 0.26, 0.08, 0.04, shade(bone, -0.35))
    s.l(0.6, 0.38, 0.85, 0.3, bone, 3)
    s.l(0.42, 0.38, 0.3, 0.5, bone, 3)
    eyes(s, 0.57, 0.19, el, 0.03, n=2, gap=0.07)


def d_knight(s, el, rnd):
    steel = mix(hexc("#a8acb8"), hexc(EL[el]["main"]), 0.2)
    humanoid(s, el, steel, legs="#6a6a78")
    s.e(0.52, 0.2, 0.14, 0.12, steel)
    s.r(0.55, 0.18, 0.14, 0.04, hexc("#202028"))     # visor slit
    s.l(0.45, 0.08, 0.35, 0.02, hexc(EL[el]["main"]), 3)  # plume
    s.e(0.34, 0.5, 0.1, 0.16, tint("#6a5a4a", el, 0.4))   # shield (back)
    s.e(0.34, 0.5, 0.04, 0.06, hexc(EL[el]["light"]))
    s.l(0.62, 0.45, 0.95, 0.25, hexc("#e0e0e8"), 3)   # sword
    s.l(0.6, 0.42, 0.66, 0.5, hexc("#c0a040"), 2)


def d_elf(s, el, rnd):
    robe = tint("#3a6a4a", el, 0.45)
    s.p([(0.4, 0.3), (0.62, 0.3), (0.72, 0.95), (0.3, 0.95)], robe)
    s.e(0.53, 0.2, 0.11, 0.1, hexc("#f0d0b0"))
    s.p([(0.62, 0.16), (0.76, 0.1), (0.63, 0.22)], hexc("#f0d0b0"))  # pointed ear
    s.p([(0.42, 0.1), (0.62, 0.1), (0.48, 0.5), (0.36, 0.45)], tint("#e0d090", el, 0.2))  # long hair
    s.l(0.72, 0.15, 0.72, 0.95, hexc("#6a4a2a"), 2)
    s.e(0.72, 0.13, 0.05, 0.05, hexc(EL[el]["main"]))
    s.px(0.71, 0.12, hexc(EL[el]["light"]))
    s.l(0.6, 0.38, 0.72, 0.42, robe, 3)
    eyes(s, 0.58, 0.19, el, 0.02)


def d_archer(s, el, rnd):
    cl = tint("#4a5a3a", el, 0.4)
    humanoid(s, el, cl, legs="#3a3a2a")
    s.e(0.5, 0.19, 0.15, 0.13, shade(cl, 0.1))
    s.e(0.56, 0.23, 0.08, 0.08, hexc("#e0b090"))
    for t in range(16):
        yy = 0.2 + t * 0.04
        xx = 0.8 + 0.08 * math.sin(t / 15 * math.pi)
        s.e(xx, yy, 0.015, 0.02, hexc("#8a5a2a"))
    s.l(0.8, 0.2, 0.66, 0.5, hexc("#f0f0f0"), 1)
    s.l(0.8, 0.8, 0.66, 0.5, hexc("#f0f0f0"), 1)
    s.l(0.62, 0.42, 0.78, 0.5, cl, 3)
    s.r(0.24, 0.3, 0.08, 0.25, hexc("#6a4a2a"))  # quiver
    eyes(s, 0.6, 0.23, el, 0.02)


def d_ghost(s, el, rnd):
    body = mix(hexc("#e8f0ff"), hexc(EL[el]["main"]), 0.35)
    s.e(0.5, 0.35, 0.26, 0.26, body)
    pts = [(0.24, 0.35), (0.76, 0.35)]
    for k in range(7):
        x = 0.76 - k * 0.085
        pts.append((x, 0.8 + (0.08 if k % 2 else 0)))
    s.p(pts, body)
    s.e(0.6, 0.32, 0.05, 0.07, K)
    s.e(0.44, 0.32, 0.05, 0.07, K)
    s.px(0.6, 0.31, hexc(EL[el]["light"]))
    s.px(0.44, 0.31, hexc(EL[el]["light"]))
    s.e(0.53, 0.47, 0.05, 0.06, K)
    s.l(0.72, 0.45, 0.92, 0.38, body, 4)


def d_bear(s, el, rnd):
    fur = tint("#6a4a2a", el, 0.4)
    s.e(0.45, 0.55, 0.36, 0.26, fur)
    s.e(0.78, 0.42, 0.16, 0.15, shade(fur, 0.1))
    s.e(0.9, 0.47, 0.07, 0.06, shade(fur, 0.3))
    s.px(0.96, 0.45, K)
    s.e(0.72, 0.28, 0.05, 0.05, shade(fur, 0.05))
    for x in (0.2, 0.38, 0.55, 0.7):
        s.r(x, 0.72, 0.1, 0.22, shade(fur, -0.2 if x in (0.38, 0.7) else 0))
        s.r(x, 0.92, 0.1, 0.04, hexc("#2a2020"))
    s.l(0.78, 0.5, 0.95, 0.52, hexc("#f0f0e0"), 1)
    eyes(s, 0.84, 0.39, el, 0.022)


def d_ogre(s, el, rnd):
    sk = tint("#7a8a4a", el, 0.4)
    s.l(0.4, 0.66, 0.36, 0.95, shade(sk, -0.2), 7)
    s.l(0.6, 0.66, 0.66, 0.95, shade(sk, -0.3), 7)
    s.e(0.5, 0.52, 0.27, 0.22, sk)
    s.r(0.28, 0.6, 0.44, 0.1, hexc("#6a4a2a"))
    s.e(0.56, 0.24, 0.15, 0.13, shade(sk, 0.1))
    s.p([(0.6, 0.3), (0.64, 0.2), (0.66, 0.31)], hexc("#f0f0e0"))
    s.l(0.68, 0.42, 0.85, 0.3, sk, 6)
    s.l(0.85, 0.35, 0.95, 0.02, hexc("#6a4a2a"), 6)
    s.e(0.94, 0.06, 0.07, 0.07, hexc("#5a3a1a"))
    eyes(s, 0.64, 0.21, el, 0.025)


def d_boar(s, el, rnd):
    hide = tint("#5a3a2a", el, 0.4)
    s.e(0.45, 0.55, 0.34, 0.24, hide)
    s.e(0.8, 0.58, 0.14, 0.14, shade(hide, 0.1))
    s.e(0.93, 0.62, 0.05, 0.05, hexc("#c08080"))
    s.p([(0.86, 0.68), (0.98, 0.5), (0.9, 0.7)], hexc("#f0f0e0"))
    for k in range(8):
        s.l(0.2 + k * 0.07, 0.36, 0.22 + k * 0.07, 0.26, shade(hide, -0.3), 2)
    for x in (0.22, 0.36, 0.55, 0.68):
        s.r(x, 0.72, 0.08, 0.22, shade(hide, -0.2))
    eyes(s, 0.82, 0.52, el, 0.022)


def d_fknight(s, el, rnd):
    arm = mix(hexc("#d8dce8"), hexc(EL[el]["main"]), 0.15)
    humanoid(s, el, arm, legs="#3a3e4a")
    s.e(0.53, 0.2, 0.13, 0.12, arm)
    s.r(0.52, 0.18, 0.16, 0.04, hexc(EL[el]["light"]))   # glowing visor
    s.r(0.36, 0.4, 0.28, 0.03, hexc(EL[el]["main"]))     # glow strip
    s.l(0.66, 0.45, 0.98, 0.15, hexc(EL[el]["light"]), 3)  # energy blade
    s.l(0.66, 0.45, 0.98, 0.15, hexc(EL[el]["main"]), 1)
    s.e(0.38, 0.33, 0.07, 0.05, shade(arm, -0.1))


def d_farcher(s, el, rnd):
    arm = mix(hexc("#3a3e4a"), hexc(EL[el]["main"]), 0.25)
    humanoid(s, el, arm, legs="#2a2e3a")
    s.r(0.3, 0.32, 0.08, 0.28, hexc("#5a5e6a"))   # jetpack
    s.e(0.33, 0.62, 0.04, 0.05, hexc(EL[el]["light"]))
    s.e(0.53, 0.2, 0.13, 0.12, arm)
    s.r(0.52, 0.17, 0.16, 0.05, hexc(EL[el]["main"]))
    for t in range(14):
        yy = 0.2 + t * 0.045
        xx = 0.82 + 0.07 * math.sin(t / 13 * math.pi)
        s.e(xx, yy, 0.012, 0.02, hexc("#c0c4d0"))
    s.l(0.82, 0.2, 0.82, 0.8, hexc(EL[el]["light"]), 1)
    s.l(0.62, 0.42, 0.8, 0.5, arm, 3)


def d_fbum(s, el, rnd):
    coat = tint("#5a4a3a", el, 0.3)
    humanoid(s, el, coat, "#c09070", hunch=0.05)
    s.l(0.62, 0.42, 0.78, 0.6, hexc("#9aa0b0"), 4)   # robotic arm
    s.e(0.78, 0.6, 0.03, 0.03, hexc(EL[el]["light"]))
    s.r(0.68, 0.6, 0.28, 0.2, hexc("#4a4e5a"))       # neon cart
    for k in range(4):
        s.l(0.69 + k * 0.07, 0.6, 0.69 + k * 0.07, 0.8, hexc(EL[el]["main"]), 1)
    s.e(0.72, 0.84, 0.03, 0.03, K)
    s.e(0.92, 0.84, 0.03, 0.03, K)
    s.r(0.5, 0.14, 0.15, 0.04, hexc(EL[el]["main"]))  # LED visor
    eyes(s, 0.6, 0.24, el, 0.02)


# ------------------------------------------------------------------ King Goblin's army and the pirates

def _goblin_body(s, el, skin, coat, hunch=0.06):
    sk = hexc(skin)
    s.l(0.44, 0.66, 0.4, 0.95, shade(sk, -0.25), 5)
    s.l(0.56, 0.66, 0.62, 0.95, shade(sk, -0.35), 5)
    s.p([(0.34, 0.4 + hunch), (0.66, 0.4 + hunch), (0.68, 0.7), (0.32, 0.7)], coat)
    s.e(0.56, 0.3 + hunch, 0.17, 0.14, sk)
    s.p([(0.42, 0.26 + hunch), (0.22, 0.14 + hunch), (0.44, 0.34 + hunch)], sk)       # big ears
    s.p([(0.7, 0.26 + hunch), (0.9, 0.16 + hunch), (0.7, 0.34 + hunch)], shade(sk, -0.1))
    s.p([(0.7, 0.3 + hunch), (0.82, 0.36 + hunch), (0.7, 0.38 + hunch)], shade(sk, -0.15))  # pointy nose
    s.l(0.56, 0.4 + hunch, 0.66, 0.39 + hunch, hexc("#f0f0e0"), 1)
    return sk


def d_goblin(s, el, rnd):
    _goblin_body(s, el, "#6aa040", tint("#6a4a2a", el, 0.35))
    s.l(0.68, 0.5, 0.92, 0.42, hexc("#c0c0c8"), 2)
    s.l(0.66, 0.52, 0.7, 0.5, hexc("#6a4a2a"), 2)
    eyes(s, 0.64, 0.33, "fire", 0.028)


def d_goblin_shaman(s, el, rnd):
    _goblin_body(s, el, "#5a9050", tint("#4a3a6a", el, 0.45), 0.04)
    s.p([(0.38, 0.22), (0.56, 0.0), (0.74, 0.22)], tint("#3a2a4a", el, 0.4))          # pointed hood
    s.l(0.74, 0.25, 0.82, 0.95, hexc("#7a5030"), 2)
    s.e(0.82, 0.2, 0.06, 0.06, hexc("#e0e0c8"))                                        # skull totem
    s.px(0.81, 0.2, K)
    for _ in range(4):
        s.px(rnd.uniform(0.7, 0.95), rnd.uniform(0.05, 0.3), hexc(EL[el]["light"]))
    eyes(s, 0.64, 0.31, el, 0.026)


def d_goblin_brute(s, el, rnd):
    sk = hexc("#5a8a3a")
    s.l(0.4, 0.66, 0.36, 0.95, shade(sk, -0.25), 8)
    s.l(0.6, 0.66, 0.66, 0.95, shade(sk, -0.35), 8)
    s.e(0.5, 0.52, 0.28, 0.22, sk)
    s.r(0.28, 0.62, 0.44, 0.08, tint("#5a3a2a", el, 0.4))
    s.e(0.6, 0.24, 0.16, 0.13, shade(sk, 0.1))
    s.p([(0.46, 0.22), (0.3, 0.1), (0.48, 0.28)], sk)
    s.p([(0.62, 0.32), (0.66, 0.24), (0.68, 0.33)], hexc("#f0f0e0"))
    s.l(0.7, 0.42, 0.88, 0.3, sk, 6)
    s.l(0.86, 0.36, 0.96, 0.04, hexc("#6a4a2a"), 5)
    for k in range(3):
        s.px(0.9 + k * 0.02, 0.06 + k * 0.05, hexc("#c0c0c8"))
    eyes(s, 0.66, 0.21, "fire", 0.028)


def _pirate(s, el, rnd, coat, gun=False):
    humanoid(s, el, coat, "#d8a070")
    s.r(0.38, 0.4, 0.26, 0.04, hexc("#f0f0e0"))                                       # striped shirt
    s.r(0.38, 0.48, 0.26, 0.04, hexc("#f0f0e0"))
    s.r(0.34, 0.6, 0.32, 0.05, hexc("#3a2a1a"))                                       # belt
    s.px(0.5, 0.62, hexc("#f0d060"))
    s.p([(0.34, 0.14), (0.7, 0.14), (0.64, 0.06), (0.4, 0.06)], hexc("#1a1a22"))      # tricorn
    s.r(0.3, 0.14, 0.46, 0.03, hexc("#1a1a22"))
    s.px(0.52, 0.09, hexc("#f0f0f0"))
    s.r(0.57, 0.2, 0.06, 0.04, hexc("#1a1a22"))                                       # eye patch
    s.r(0.46, 0.29, 0.14, 0.04, hexc("#4a2a1a"))                                      # beard
    if gun:
        s.l(0.62, 0.45, 0.95, 0.4, hexc("#5a3a2a"), 3)
        s.l(0.8, 0.41, 0.98, 0.38, hexc("#8a8a98"), 2)
        s.px(0.99, 0.38, hexc("#ffd060"))
    else:
        s.l(0.62, 0.46, 0.92, 0.32, hexc("#d0d4e0"), 2)                                # cutlass
        s.e(0.64, 0.46, 0.04, 0.04, hexc("#c0a040"))
    eyes(s, 0.66, 0.21, el, 0.02)


def d_pirate(s, el, rnd):
    _pirate(s, el, rnd, tint("#8a2a2a", el, 0.3))


def d_pirate_gunner(s, el, rnd):
    _pirate(s, el, rnd, tint("#2a3a6a", el, 0.3), gun=True)


def d_king_goblin(s, el, rnd):
    sk = hexc("#6aa040")
    robe = hexc("#6a1a6a")
    s.p([(0.24, 0.45), (0.76, 0.45), (0.88, 0.97), (0.12, 0.97)], robe)               # royal cloak
    for k in range(9):
        s.px(0.15 + k * 0.08, 0.95, hexc("#f0f0f0"))
        s.px(0.17 + k * 0.08, 0.93, hexc("#1a1a1a"))
    s.p([(0.34, 0.46), (0.66, 0.46), (0.7, 0.8), (0.3, 0.8)], hexc("#c09030"))        # gold armor
    s.r(0.3, 0.66, 0.4, 0.04, hexc("#8a5a1a"))
    s.e(0.5, 0.32, 0.18, 0.15, sk)
    s.p([(0.34, 0.28), (0.06, 0.12), (0.36, 0.38)], sk)
    s.p([(0.66, 0.28), (0.94, 0.12), (0.64, 0.38)], shade(sk, -0.1))
    s.p([(0.62, 0.34), (0.74, 0.42), (0.6, 0.44)], shade(sk, -0.15))
    s.l(0.42, 0.42, 0.6, 0.42, hexc("#f0f0e0"), 1)
    s.px(0.44, 0.44, hexc("#f0f0e0"))
    s.px(0.57, 0.44, hexc("#f0f0e0"))
    # a tottering stack of six stolen crowns
    cols = [EL[e]["main"] for e in ("fire", "water", "wind", "stone", "spirit", "void")]
    for k, c in enumerate(cols):
        y = 0.17 - k * 0.028
        x = 0.5 + (0.02 if k % 2 else -0.02)
        s.p([(x - 0.12, y + 0.03), (x - 0.1, y - 0.02), (x - 0.04, y + 0.01), (x, y - 0.03), (x + 0.04, y + 0.01),
             (x + 0.1, y - 0.02), (x + 0.12, y + 0.03)], hexc("#f0c040"))
        s.px(x, y, hexc(c))
    s.l(0.72, 0.5, 0.92, 0.6, robe, 5)
    s.l(0.92, 0.2, 0.92, 0.95, hexc("#c09030"), 2)                                     # scepter
    s.e(0.92, 0.18, 0.05, 0.05, hexc(EL["void"]["main"]))
    for _ in range(14):
        s.px(rnd.uniform(0.05, 0.95), rnd.uniform(0.85, 1.0), hexc("#f0d060"))         # pile of coins
    eyes(s, 0.56, 0.29, "fire", 0.026, n=2, gap=0.12)



SPECIES_DRAW = {"goblin": ("s", d_goblin), "goblin_shaman": ("m", d_goblin_shaman), "goblin_brute": ("l", d_goblin_brute),
                "pirate": ("m", d_pirate), "pirate_gunner": ("m", d_pirate_gunner), "rat": ("s", d_rat), "bum": ("m", d_bum), "loiterer": ("m", d_loiterer), "undead": ("m", d_undead),
                "knight": ("m", d_knight), "elf": ("m", d_elf), "archer": ("m", d_archer), "ghost": ("m", d_ghost),
                "bear": ("l", d_bear), "ogre": ("l", d_ogre), "boar": ("l", d_boar), "fknight": ("m", d_fknight),
                "farcher": ("m", d_farcher), "fbum": ("m", d_fbum)}

# ------------------------------------------------------------------ unique designs


def d_gloomfin(s, el, rnd):
    body = tint("#2a2a3a", el, 0.3)
    s.e(0.45, 0.55, 0.36, 0.3, body)
    s.p([(0.08, 0.55), (0.0, 0.3), (0.0, 0.8)], shade(body, -0.2))
    s.p([(0.62, 0.6), (0.95, 0.5), (0.9, 0.8)], hexc("#1a0a10"))  # jaw
    for k in range(5):
        s.p([(0.66 + k * 0.06, 0.57), (0.69 + k * 0.06, 0.66), (0.72 + k * 0.06, 0.57)], hexc("#f0f0e0"))
    s.l(0.62, 0.3, 0.78, 0.08, shade(body, 0.2), 2)
    s.l(0.78, 0.08, 0.92, 0.18, shade(body, 0.2), 2)
    s.e(0.93, 0.22, 0.06, 0.07, hexc("#fff8b0"))  # the stolen lens
    s.e(0.93, 0.22, 0.03, 0.035, hexc("#ffffff"))
    eyes(s, 0.62, 0.45, el, 0.03)


def d_gravelmaw(s, el, rnd):
    r = tint("#7a7468", el, 0.25)
    s.e(0.48, 0.58, 0.4, 0.32, r)
    for k in range(6):
        s.e(0.18 + k * 0.12, 0.32 + (k % 2) * 0.05, 0.08, 0.08, shade(r, 0.15))
    s.p([(0.72, 0.5), (0.99, 0.58), (0.74, 0.8)], hexc("#1a1010"))
    for k in range(4):
        s.p([(0.75 + k * 0.05, 0.56), (0.77 + k * 0.05, 0.66), (0.8 + k * 0.05, 0.56)], hexc("#d0c8b0"))
    for x in (0.2, 0.4, 0.6):
        s.r(x, 0.82, 0.12, 0.14, shade(r, -0.25))
    eyes(s, 0.76, 0.44, el, 0.03)


def d_mirror(s, el, rnd):
    frame = hexc("#d8c070")
    s.r(0.25, 0.05, 0.5, 0.88, frame)
    s.r(0.3, 0.1, 0.4, 0.78, hexc("#a8c0e0"))
    # cold crowned reflection
    s.e(0.5, 0.35, 0.07, 0.06, hexc("#e0e8f8"))
    s.p([(0.42, 0.42), (0.58, 0.42), (0.6, 0.8), (0.4, 0.8)], hexc("#5a5a8a"))
    s.r(0.44, 0.27, 0.12, 0.03, hexc("#f0d060"))
    for k in range(3):
        s.px(0.45 + k * 0.05, 0.25, hexc("#f0d060"))
    s.l(0.33, 0.15, 0.4, 0.3, hexc("#ffffff"), 1)
    s.r(0.2, 0.9, 0.6, 0.06, shade(frame, -0.3))


def d_name_eater(s, el, rnd):
    paper = hexc("#e8e0d0")
    for _ in range(26):
        x, y = rnd.uniform(0.2, 0.8), rnd.uniform(0.2, 0.85)
        s.p([(x, y), (x + rnd.uniform(0.05, 0.12), y + rnd.uniform(-0.04, 0.04)),
             (x + rnd.uniform(0.0, 0.1), y + rnd.uniform(0.06, 0.12))], shade(paper, rnd.uniform(-0.25, 0.05)))
    s.e(0.62, 0.5, 0.18, 0.12, hexc("#1a1018"))
    for k in range(6):
        s.p([(0.48 + k * 0.05, 0.42), (0.5 + k * 0.05, 0.5), (0.52 + k * 0.05, 0.42)], hexc("#f8f8f0"))
        s.p([(0.48 + k * 0.05, 0.6), (0.5 + k * 0.05, 0.52), (0.52 + k * 0.05, 0.6)], hexc("#f8f8f0"))
    for k in range(4):
        s.l(0.25 + k * 0.08, 0.3, 0.27 + k * 0.08, 0.34, hexc("#3a3040"), 1)  # scribbled letters
    eyes(s, 0.7, 0.3, el, 0.03, n=3, gap=0.08)


def d_vulkar(s, el, rnd):
    green = hexc("#60ff70")
    for k in range(18):  # envious green fire rising behind him
        x = 0.22 + k * 0.032
        h = rnd.uniform(0.25, 0.5) * (1 - abs(x - 0.5) * 1.2)
        s.e(x, 0.42 - h / 2, 0.03, h / 2, green if k % 2 else hexc("#20c040"))
    s.e(0.5, 0.18, 0.12, 0.16, hexc("#a0ffa0"))
    humanoid(s, el, hexc("#5a3a2a"), "#d09070", legs="#3a2a20")
    s.r(0.36, 0.34, 0.28, 0.3, hexc("#8a6a4a"))   # leather apron
    s.l(0.62, 0.4, 0.86, 0.22, hexc("#d09070"), 4)
    s.l(0.86, 0.22, 0.92, 0.05, hexc("#5a4a3a"), 3)
    s.r(0.86, 0.0, 0.12, 0.08, hexc("#4a4a50"))   # hammer head
    s.r(0.46, 0.1, 0.14, 0.05, hexc("#2a1a10"))   # hair
    for k in range(5):
        s.e(0.62 + k * 0.02, 0.36 - k * 0.04, 0.02, 0.04, green)
    eyes(s, 0.58, 0.22, "stone", 0.022)


def d_maren(s, el, rnd):
    w = hexc("#4a8ad0")
    s.p([(0.38, 0.25), (0.58, 0.25), (0.75, 0.97), (0.2, 0.97)], w)
    for k in range(6):
        s.l(0.25 + k * 0.08, 0.6, 0.22 + k * 0.08, 0.97, hexc("#a8e0ff"), 1)
    s.e(0.48, 0.17, 0.1, 0.1, hexc("#a8d8f0"))
    s.p([(0.38, 0.1), (0.58, 0.1), (0.66, 0.6), (0.3, 0.55)], hexc("#2a5a9a"))  # long hair
    s.e(0.48, 0.18, 0.06, 0.07, hexc("#c8e8f8"))
    s.e(0.7, 0.6, 0.15, 0.08, hexc("#8a6a4a"))   # cradle
    s.e(0.7, 0.57, 0.12, 0.05, hexc("#3a2a1a"))
    s.l(0.55, 0.4, 0.68, 0.55, w, 3)
    s.px(0.5, 0.2, hexc("#e0f8ff"))
    s.l(0.5, 0.21, 0.51, 0.27, hexc("#e0f8ff"), 1)


def d_corvane(s, el, rnd):
    gold = hexc("#e0b040")
    humanoid(s, el, gold, "#e0c0a0", legs="#8a6a2a")
    s.p([(0.38, 0.32), (0.1, 0.15), (0.05, 0.4), (0.2, 0.5)], hexc("#e8e8e0"))   # broken wing
    s.l(0.12, 0.25, 0.2, 0.45, hexc("#a0a098"), 1)
    s.p([(0.62, 0.32), (0.75, 0.25), (0.72, 0.45)], hexc("#c8c8c0"))
    s.e(0.53, 0.2, 0.13, 0.11, gold)
    s.p([(0.62, 0.2), (0.75, 0.24), (0.62, 0.26)], hexc("#d0a030"))  # beak-helm
    for k in range(4):  # cage bars held
        s.l(0.72 + k * 0.06, 0.45, 0.72 + k * 0.06, 0.75, hexc("#f0d060"), 1)
    s.r(0.7, 0.44, 0.22, 0.03, hexc("#f0d060"))
    s.r(0.7, 0.74, 0.22, 0.03, hexc("#f0d060"))
    s.e(0.81, 0.6, 0.04, 0.05, hexc("#a0fff0"))
    eyes(s, 0.6, 0.19, el, 0.02)


def d_ostrum(s, el, rnd):
    st = hexc("#8a8a82")
    s.r(0.15, 0.78, 0.7, 0.2, hexc("#c09030"))   # coin pile
    for k in range(10):
        s.e(0.18 + k * 0.07, 0.78 + (k % 3) * 0.04, 0.04, 0.025, hexc("#f0d060"))
    s.p([(0.32, 0.3), (0.68, 0.3), (0.74, 0.8), (0.26, 0.8)], st)
    s.e(0.5, 0.2, 0.14, 0.12, st)
    for k in range(5):
        s.r(0.38 + k * 0.05, 0.05, 0.04, 0.06, hexc("#f0d060"))
    s.r(0.36, 0.09, 0.28, 0.04, hexc("#f0d060"))
    for _ in range(9):  # gold veins
        x, y = rnd.uniform(0.32, 0.66), rnd.uniform(0.25, 0.75)
        s.l(x, y, x + rnd.uniform(-0.1, 0.1), y + rnd.uniform(0.05, 0.15), hexc("#f0c030"), 1)
    s.l(0.68, 0.4, 0.85, 0.2, st, 5)
    s.l(0.85, 0.2, 0.85, 0.02, hexc("#f0d060"), 2)
    eyes(s, 0.56, 0.19, "fire", 0.025)


def d_iris(s, el, rnd):
    light = hexc("#f8f4ff")
    s.p([(0.4, 0.25), (0.6, 0.25), (0.7, 0.9), (0.3, 0.9)], light)
    # unfinished: lower body is rough-cut stone
    for _ in range(20):
        x, y = rnd.uniform(0.3, 0.7), rnd.uniform(0.6, 0.95)
        s.e(x, y, 0.04, 0.03, hexc("#b0a8c8"))
    s.e(0.5, 0.17, 0.1, 0.1, light)
    s.e(0.5, 0.05, 0.14, 0.03, hexc("#fff4b0"))   # halo
    s.l(0.6, 0.4, 0.82, 0.35, light, 3)
    s.l(0.82, 0.35, 0.92, 0.25, hexc("#c0c0c8"), 2)  # chisel
    s.r(0.08, 0.6, 0.15, 0.35, hexc("#c0b8d8"))     # half-carved statue
    s.e(0.155, 0.55, 0.06, 0.06, hexc("#c0b8d8"))
    eyes(s, 0.55, 0.16, "spirit", 0.02)


def d_nobody(s, el, rnd):
    g = hexc("#8a80a0")
    humanoid(s, el, hexc("#5a5070"), "#a8a0b8", legs="#4a4060")
    for y in range(s.c.h):
        for x in range(s.c.w):
            if s.c.a[y, x, 3] and (x * 7 + y * 3) % 5 == 0:
                s.c.a[y, x] = (0, 0, 0, 0)
    for k in range(6):  # floating fragments
        x, y = rnd.uniform(0.6, 0.95), rnd.uniform(0.1, 0.8)
        s.r(x, y, 0.05, 0.04, g)
    s.r(0.4, 0.22, 0.2, 0.02, hexc("#ffffff"))  # static line across the face


def d_aeon(s, el, rnd):
    gold = hexc("#f0d060")
    for k in range(6):  # wings
        a = -0.9 + k * 0.36
        s.p([(0.5, 0.5), (0.5 + math.cos(a) * 0.48, 0.5 + math.sin(a) * 0.45),
             (0.5 + math.cos(a + 0.25) * 0.4, 0.5 + math.sin(a + 0.25) * 0.38)], hexc("#f8f4ff"))
        s.p([(0.5, 0.5), (0.5 - math.cos(a) * 0.48, 0.5 + math.sin(a) * 0.45),
             (0.5 - math.cos(a + 0.25) * 0.4, 0.5 + math.sin(a + 0.25) * 0.38)], hexc("#e8e4f8"))
    s.e(0.5, 0.5, 0.18, 0.2, hexc("#ffffff"))
    s.e(0.5, 0.16, 0.2, 0.04, gold)  # halo
    for k in range(9):  # eyes everywhere
        ang = k / 9 * math.tau
        x, y = 0.5 + math.cos(ang) * 0.3, 0.5 + math.sin(ang) * 0.28
        s.e(x, y, 0.035, 0.025, hexc("#ffffff"))
        s.e(x, y, 0.015, 0.02, hexc("#3a3060"))
    s.e(0.5, 0.5, 0.08, 0.06, hexc("#ffffff"))
    s.e(0.5, 0.5, 0.04, 0.05, gold)
    s.e(0.5, 0.5, 0.015, 0.03, hexc("#1a1030"))


def d_nihil(s, el, rnd):
    s.e(0.5, 0.52, 0.45, 0.42, hexc("#08060e"))
    for k in range(40):
        x, y = rnd.uniform(0.1, 0.9), rnd.uniform(0.15, 0.9)
        if ((x - 0.5) / 0.45) ** 2 + ((y - 0.52) / 0.42) ** 2 < 0.9:
            s.px(x, y, hexc("#ffffff") if rnd.random() < 0.6 else hexc("#c0a0ff"))
    for k in range(7):  # ring of teeth/horizon
        ang = k / 7 * math.tau + 0.2
        s.l(0.5 + math.cos(ang) * 0.3, 0.52 + math.sin(ang) * 0.28, 0.5 + math.cos(ang) * 0.48, 0.52 + math.sin(ang) * 0.45,
            hexc("#2a1450"), 4)
    s.e(0.5, 0.52, 0.12, 0.12, hexc("#000000"))
    s.e(0.5, 0.52, 0.16, 0.16, hexc("#9a50ff"))
    s.e(0.5, 0.52, 0.13, 0.13, hexc("#000000"))


# ------------------------------------------------------------------ v2 side-dungeon minibosses

def d_rat_king(s, el, rnd):
    # a heap of glowing rats knotted together, wearing a thimble crown
    for k in range(7):
        x, y = 0.22 + (k % 4) * 0.17 + rnd.uniform(-0.03, 0.03), 0.58 + (k // 4) * 0.17
        fur = tint("#6a5a52", el, 0.5 + 0.1 * (k % 2))
        s.e(x, y, 0.14, 0.1, fur)
        s.e(x + 0.1, y - 0.03, 0.06, 0.05, shade(fur, 0.15))
        s.px(x + 0.13, y - 0.04, hexc(EL[el]["light"]))
        s.l(x - 0.12, y + 0.02, x - 0.2, y + 0.12, shade(fur, -0.25), 2)
    s.e(0.6, 0.36, 0.2, 0.17, tint("#7a6a62", el, 0.45))
    s.e(0.76, 0.32, 0.08, 0.07, shade(tint("#7a6a62", el, 0.45), 0.2))
    s.p([(0.48, 0.2), (0.56, 0.06), (0.6, 0.2), (0.66, 0.05), (0.72, 0.2)], hexc("#d8c060"))
    s.r(0.48, 0.18, 0.24, 0.04, hexc("#c0a040"))
    eyes(s, 0.74, 0.3, el, 0.03)
    s.l(0.84, 0.36, 0.95, 0.38, hexc("#f0e0d0"), 1)


def d_falls_guardian(s, el, rnd):
    stone = hexc("#6a7a72")
    s.r(0.25, 0.3, 0.5, 0.55, stone)
    s.e(0.5, 0.25, 0.2, 0.15, shade(stone, 0.1))
    for x in (0.27, 0.62):
        s.r(x, 0.83, 0.12, 0.13, shade(stone, -0.2))
    s.l(0.25, 0.35, 0.1, 0.7, stone, 7)
    s.l(0.75, 0.35, 0.9, 0.7, stone, 7)
    for _ in range(12):
        s.px(rnd.uniform(0.27, 0.73), rnd.uniform(0.3, 0.8), hexc("#4a8a3a"))
    water = hexc(EL["water"]["main"])
    for k in range(6):
        x = 0.28 + k * 0.09
        s.l(x, 0.12, x + 0.01, 0.95, mix(water, hexc("#ffffff"), 0.3 * (k % 2)), 2)
    eyes(s, 0.58, 0.24, "water", 0.03, n=2, gap=0.14)


def d_storm_harpy(s, el, rnd):
    feather = tint("#7a6a8a", el, 0.4)
    s.p([(0.5, 0.35), (0.02, 0.1), (0.12, 0.45), (0.45, 0.55)], feather)
    s.p([(0.52, 0.38), (0.98, 0.12), (0.88, 0.48), (0.56, 0.56)], shade(feather, 0.12))
    for k in range(5):
        s.l(0.08 + k * 0.08, 0.18 + k * 0.06, 0.12 + k * 0.08, 0.42, shade(feather, -0.3), 1)
    s.e(0.5, 0.5, 0.11, 0.15, hexc("#d0b090"))
    s.e(0.52, 0.3, 0.09, 0.09, hexc("#e0c0a0"))
    s.p([(0.42, 0.25), (0.62, 0.18), (0.56, 0.42), (0.4, 0.4)], tint("#3a3050", el, 0.3))
    s.l(0.45, 0.65, 0.42, 0.9, hexc("#c0a040"), 2)
    s.l(0.56, 0.65, 0.6, 0.9, hexc("#c0a040"), 2)
    s.p([(0.38, 0.9), (0.46, 0.96), (0.42, 0.88)], K)
    eyes(s, 0.56, 0.29, el, 0.022)


def d_rustbiter(s, el, rnd):
    shell = tint("#8a5a3a", el, 0.3)
    for k in range(6):
        x = 0.12 + k * 0.13
        y = 0.68 - 0.18 * math.sin(k / 5 * math.pi)
        s.e(x, y, 0.11, 0.12, shade(shell, 0.1 * (k % 2)))
        s.l(x - 0.04, y + 0.1, x - 0.06, y + 0.2, shade(shell, -0.35), 1)
        s.px(x, y - 0.06, hexc("#c06030"))
    s.e(0.84, 0.42, 0.14, 0.15, shade(shell, 0.15))
    s.p([(0.92, 0.42), (1.0, 0.3), (0.96, 0.5)], hexc("#a0a0a8"))
    s.p([(0.92, 0.48), (1.0, 0.6), (0.94, 0.54)], hexc("#a0a0a8"))
    for _ in range(10):
        s.px(rnd.uniform(0.05, 0.9), rnd.uniform(0.4, 0.85), hexc("#c07030"))
    eyes(s, 0.86, 0.36, el, 0.025, n=2, gap=0.06)


def d_lantern_wraith(s, el, rnd):
    robe = mix(hexc("#2a2a3a"), hexc(EL[el]["dark"]), 0.4)
    pts = [(0.35, 0.18), (0.62, 0.18), (0.72, 0.55)]
    for k in range(6):
        pts.append((0.72 - k * 0.08, 0.92 - (0.06 if k % 2 else 0)))
    pts.append((0.28, 0.55))
    s.p(pts, robe)
    s.e(0.5, 0.2, 0.14, 0.13, shade(robe, -0.2))
    s.e(0.53, 0.22, 0.08, 0.08, K)
    s.px(0.5, 0.21, hexc("#ffffff"))
    s.px(0.56, 0.21, hexc("#ffffff"))
    s.l(0.62, 0.35, 0.86, 0.45, robe, 3)
    s.l(0.86, 0.45, 0.86, 0.55, hexc("#4a4a5a"), 1)
    s.r(0.81, 0.55, 0.1, 0.13, hexc("#c0a040"))
    s.r(0.83, 0.57, 0.06, 0.09, hexc("#fffbe0"))
    s.e(0.86, 0.62, 0.14, 0.14, hexc("#fffbe0", 60))


def d_lingering(s, el, rnd):
    smoke = mix(hexc("#4a4060"), hexc(EL[el]["main"]), 0.3)
    for k in range(14):
        s.e(rnd.uniform(0.2, 0.8), rnd.uniform(0.2, 0.85), rnd.uniform(0.08, 0.16), rnd.uniform(0.08, 0.14),
            shade(smoke, rnd.uniform(-0.2, 0.15)))
    for k in range(5):
        fx, fy = 0.3 + (k % 3) * 0.2, 0.3 + (k // 3) * 0.28
        s.e(fx, fy, 0.07, 0.08, hexc("#d8d0e8"))
        s.px(fx - 0.02, fy - 0.01, K)
        s.px(fx + 0.025, fy - 0.01, K)
        s.l(fx - 0.02, fy + 0.04, fx + 0.02, fy + 0.04, shade(hexc("#d8d0e8"), -0.4), 1)
    for k in range(4):
        s.l(0.3 + k * 0.12, 0.8, 0.25 + k * 0.14, 0.98, smoke, 3)



UNIQUE_DRAW = {"king_goblin": d_king_goblin, "rat_king": d_rat_king, "falls_guardian": d_falls_guardian, "storm_harpy": d_storm_harpy,
               "rustbiter": d_rustbiter, "lantern_wraith": d_lantern_wraith, "lingering": d_lingering,
               "gloomfin": d_gloomfin, "gravelmaw": d_gravelmaw, "mirror": d_mirror, "name_eater": d_name_eater,
               "vulkar": d_vulkar, "maren": d_maren, "corvane": d_corvane, "ostrum": d_ostrum, "iris": d_iris,
               "nobody": d_nobody, "aeon": d_aeon, "nihil": d_nihil}

# ------------------------------------------------------------------ summons (112x112)


def summon_pyrestag(s, rnd):
    body = hexc("#c04020")
    s.e(0.45, 0.55, 0.28, 0.17, body)
    s.e(0.75, 0.38, 0.1, 0.09, shade(body, 0.1))
    s.l(0.72, 0.4, 0.66, 0.5, body, 6)
    for x in (0.25, 0.35, 0.55, 0.65):
        s.l(x, 0.66, x + 0.02, 0.92, shade(body, -0.2), 4)
    for side in (-1, 1):  # burning antlers
        s.l(0.74, 0.3, 0.74 + side * 0.08, 0.1, hexc("#ffd060"), 3)
        s.l(0.74 + side * 0.04, 0.2, 0.74 + side * 0.14, 0.14, hexc("#ff8a20"), 2)
        s.l(0.74 + side * 0.07, 0.13, 0.74 + side * 0.06, 0.02, hexc("#ffe080"), 2)
    for k in range(10):
        s.e(0.25 + k * 0.05, 0.38 - (k % 3) * 0.03, 0.03, 0.06, hexc("#ffb040"))
    eyes(s, 0.79, 0.36, "fire", 0.02)


def summon_marrowhale(s, rnd):
    b = hexc("#2a5aa0")
    s.e(0.5, 0.5, 0.45, 0.24, b)
    s.e(0.5, 0.6, 0.38, 0.12, hexc("#a8c8e8"))
    s.p([(0.05, 0.5), (0.0, 0.25), (0.15, 0.45)], b)
    s.p([(0.05, 0.5), (0.0, 0.75), (0.15, 0.55)], b)
    for k in range(6):
        s.l(0.4 + k * 0.07, 0.42, 0.42 + k * 0.07, 0.62, hexc("#e8f0f8"), 1)  # rib-like memory lines
    s.e(0.82, 0.45, 0.025, 0.025, hexc("#ffffff"))
    for k in range(5):
        s.e(0.6 + k * 0.03, 0.18 - k * 0.03, 0.02, 0.03, hexc("#b0e8ff"))


def summon_galecrown(s, rnd):
    b = hexc("#2aa090")
    s.p([(0.5, 0.45), (0.0, 0.2), (0.15, 0.55)], hexc("#e8fff8"))
    s.p([(0.5, 0.45), (1.0, 0.2), (0.85, 0.55)], hexc("#d8f8f0"))
    s.e(0.5, 0.5, 0.12, 0.18, b)
    s.e(0.5, 0.28, 0.08, 0.08, shade(b, 0.15))
    s.p([(0.56, 0.28), (0.66, 0.3), (0.56, 0.33)], hexc("#f0c040"))
    for k in range(5):
        s.l(0.44 + k * 0.03, 0.2, 0.42 + k * 0.04, 0.1, hexc("#ffffff"), 1)  # storm crown
    s.p([(0.42, 0.66), (0.5, 0.9), (0.58, 0.66)], shade(b, -0.2))
    eyes(s, 0.53, 0.27, "wind", 0.018)


def summon_basaltus(s, rnd):
    shell = hexc("#5a6a4a")
    s.e(0.5, 0.55, 0.38, 0.28, shell)
    for k in range(7):
        s.e(0.25 + k * 0.08, 0.45 + (k % 2) * 0.08, 0.06, 0.05, shade(shell, 0.2))
    s.e(0.9, 0.62, 0.09, 0.08, hexc("#8a8a6a"))
    for x in (0.25, 0.4, 0.6, 0.75):
        s.r(x, 0.75, 0.08, 0.16, hexc("#7a7a5a"))
    s.r(0.42, 0.18, 0.12, 0.12, hexc("#8a9a7a"))  # little mountain on the shell
    s.p([(0.38, 0.32), (0.48, 0.12), (0.58, 0.32)], hexc("#a0a890"))
    s.px(0.48, 0.13, hexc("#ffffff"))
    eyes(s, 0.92, 0.6, "stone", 0.015)


def summon_lanternmoth(s, rnd):
    for side in (-1, 1):
        s.e(0.5 + side * 0.22, 0.38, 0.2, 0.2, hexc("#fff4c8"))
        s.e(0.5 + side * 0.16, 0.65, 0.12, 0.14, hexc("#f0e0b0"))
        s.e(0.5 + side * 0.24, 0.38, 0.06, 0.06, hexc("#ffd060"))
    s.e(0.5, 0.5, 0.06, 0.2, hexc("#c0a080"))
    s.l(0.48, 0.3, 0.4, 0.12, hexc("#c0a080"), 1)
    s.l(0.52, 0.3, 0.6, 0.12, hexc("#c0a080"), 1)
    s.e(0.5, 0.78, 0.05, 0.06, hexc("#ffffff"))


def summon_umbrahound(s, rnd):
    b = hexc("#1a1028")
    s.e(0.45, 0.55, 0.3, 0.16, b)
    s.e(0.78, 0.42, 0.12, 0.1, b)
    s.p([(0.85, 0.45), (0.99, 0.48), (0.86, 0.52)], b)
    s.p([(0.72, 0.34), (0.75, 0.2), (0.8, 0.34)], b)
    for x in (0.25, 0.35, 0.55, 0.65):
        s.l(x, 0.62, x - 0.03, 0.92, b, 4)
    s.l(0.15, 0.5, 0.02, 0.35, b, 4)
    for k in range(12):
        s.px(rnd.uniform(0.2, 0.8), rnd.uniform(0.4, 0.7), hexc("#9a50ff"))
    eyes(s, 0.82, 0.4, "void", 0.025)



SUMMON_DRAW = {"pyrestag": summon_pyrestag, "marrowhale": summon_marrowhale, "galecrown": summon_galecrown,
               "basaltus": summon_basaltus, "lanternmoth": summon_lanternmoth, "umbrahound": summon_umbrahound}


def render(draw, size_key, el, seed, flip=False, alpha=None):
    W, H = SIZES[size_key] if isinstance(size_key, str) else size_key
    c = Canvas(W, H)
    rnd = random.Random(seed)
    draw(S(c), el, rnd)
    finish(c, el, rnd, 1.0 if W < 80 else 1.6, alpha)
    return c


def build(out, db_path):
    db = json.load(open(db_path))
    count = 0
    meta = {}
    import art_kenney as AK
    tiny = AK.available()
    for sp, (size, fn) in SPECIES_DRAW.items():
        for el in EL:
            if tiny and sp in AK.SPECIES_SPRITE:
                img = AK.enemy_image(sp, el, size)
                if sp == "ghost":
                    a = img.getchannel("A").point(lambda v: v * 200 // 255)
                    img.putalpha(a)
                save(img, f"{out}/enemies/{sp}_{el}.png")
                meta[sp] = list(img.size)
            else:
                c = render(fn, size, el, hash((sp, el)) & 0xFFFF, alpha=190 if sp == "ghost" else None)
                save(c.image(), f"{out}/enemies/{sp}_{el}.png")
                meta[sp] = list(SIZES[size])
            count += 1
    for uid, u in db["uniques"].items():
        spr, el, size = u["sprite"], u["el"], u.get("size", "l")
        if tiny and (uid in AK.UNIQUE_SPRITE or (spr in AK.SPECIES_SPRITE and spr not in UNIQUE_DRAW)):
            img = AK.enemy_image(spr, el, size, uid if uid in AK.UNIQUE_SPRITE else None)
            if uid not in AK.UNIQUE_SPRITE and u["tier"] == "mini":
                # champions wear a little gold crown
                a = np.array(img)
                s_ = img.width // 16
                a[0:s_, img.width // 2 - 3 * s_:img.width // 2 + 3 * s_] = (240, 200, 60, 255)
                img = Image.fromarray(a, "RGBA")
            save(img, f"{out}/enemies/u_{uid}.png")
            save(AK.map_icon(spr, uid if uid in AK.UNIQUE_SPRITE else None), f"{out}/enemies/map_{uid}.png")
            meta["u_" + uid] = list(img.size)
            count += 2
            continue
        fn = UNIQUE_DRAW.get(spr) or SPECIES_DRAW[spr][1]
        c = render(fn, size, el, hash(uid) & 0xFFFF, alpha=200 if spr in ("ghost",) else None)
        if u["tier"] == "mini" and spr in SPECIES_DRAW:
            # champions wear a crown
            cs = S(c)
            for k in range(3):
                cs.px(0.5 + k * 0.04, 0.03, hexc("#f0d060"))
            cs.r(0.48, 0.05, 0.12, 0.02, hexc("#f0d060"))
        save(c.image(), f"{out}/enemies/u_{uid}.png")
        m = render(fn, "m", el, hash(uid) & 0xFFFF, alpha=200 if spr in ("ghost",) else None)
        save(m.image(), f"{out}/enemies/map_{uid}.png")
        meta["u_" + uid] = [c.w, c.h]
        count += 2
    for sid, fn in SUMMON_DRAW.items():
        c = Canvas(112, 112)
        rnd = random.Random(hash(sid) & 0xFFFF)
        fn(S(c), rnd)
        finish(c, db["summons"][sid]["el"], rnd, 1.4)
        save(c.image(), f"{out}/summons/{sid}.png")
        count += 1
    for sid in ("aeon", "nihil"):
        c = render(UNIQUE_DRAW[sid], (112, 112), db["summons"][sid]["el"], 99)
        save(c.image(), f"{out}/summons/{sid}.png")
    # sealed doors for the map
    for w, col in (("spirit", "#f4f0ff"), ("void", "#1a1028")):
        c = Canvas(16, 32)
        c.rect(1, 2, 14, 30, hexc(col))
        c.rect(2, 3, 12, 29, shade(hexc(col), -0.1 if w == "spirit" else 0.15))
        c.rect(1, 2, 14, 2, hexc("#e0c050" if w == "spirit" else "#9a50ff"))
        c.ellipse(5, 18, 1.5, 2, hexc("#3a3040"))
        c.ellipse(11, 18, 1.5, 2, hexc("#3a3040"))
        for k in range(4):
            c.rect(3 + k * 3, 25, 2, 4, hexc("#e0c050" if w == "spirit" else "#9a50ff"))
        c.outline()
        save(c.image(), f"{out}/enemies/seal_{w}.png")
    json.dump(meta, open(f"{out}/enemies/sizes.json", "w"))
    return count


if __name__ == "__main__":
    print(build(sys.argv[1], sys.argv[2]), "enemy images")
