"""Shared pixel-art helpers: colors, an index-buffer painter with auto-outline and shading, sheets, aura maps."""
import math
import os
import random

import numpy as np
from PIL import Image


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(c1, c2, t):
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(3)) + (c1[3] if len(c1) > 3 else 255,)


def shade(c, f):
    """f < 0 darkens toward a cool shadow, f > 0 lightens toward warm light."""
    c = c[:3]
    if f < 0:
        tgt = (24, 18, 40)
        return mix(c + (255,), tgt + (255,), min(1.0, -f))
    tgt = (255, 250, 230)
    return mix(c + (255,), tgt + (255,), min(1.0, f))


class Canvas:
    """RGBA canvas with simple pixel-art primitives."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), dtype=np.uint8)

    def px(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            if len(c) == 4 and c[3] < 255:
                if c[3] == 0:
                    return
                dst = self.a[y, x].astype(float)
                al = c[3] / 255
                if dst[3] == 0:
                    self.a[y, x] = c
                else:
                    self.a[y, x, :3] = (dst[:3] * (1 - al) + np.array(c[:3]) * al).astype(np.uint8)
                    self.a[y, x, 3] = max(dst[3], c[3])
            else:
                self.a[y, x] = c[:3] + (255,) if len(c) == 3 else c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return tuple(int(v) for v in self.a[y, x])
        return (0, 0, 0, 0)

    def rect(self, x, y, w, h, c):
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                self.px(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(int(math.floor(cy - ry)), int(math.ceil(cy + ry)) + 1):
            for xx in range(int(math.floor(cx - rx)), int(math.ceil(cx + rx)) + 1):
                if rx > 0 and ry > 0 and ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.px(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            if w <= 1:
                self.px(round(x), round(y), c)
            else:
                self.ellipse(x, y, w / 2, w / 2, c)

    def poly(self, pts, c):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for yy in range(int(min(ys)), int(max(ys)) + 1):
            for xx in range(int(min(xs)), int(max(xs)) + 1):
                if _inside(xx + 0.5, yy + 0.5, pts):
                    self.px(xx, yy, c)

    def blit(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                c = tuple(int(v) for v in other.a[y, x])
                if c[3] > 0:
                    self.px(ox + x, oy + y, c)

    def flip(self):
        c = Canvas(self.w, self.h)
        c.a = self.a[:, ::-1].copy()
        return c

    def outline(self, color=(20, 14, 28, 255), diag=False):
        """Add a 1px dark outline around opaque pixels."""
        alpha = self.a[:, :, 3] > 0
        out = np.zeros_like(alpha)
        shifts = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if diag:
            shifts += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
        for dx, dy in shifts:
            s = np.zeros_like(alpha)
            ys = slice(max(dy, 0), self.h + min(dy, 0))
            yd = slice(max(-dy, 0), self.h + min(-dy, 0))
            xs = slice(max(dx, 0), self.w + min(dx, 0))
            xd = slice(max(-dx, 0), self.w + min(-dx, 0))
            s[ys, xs] = alpha[yd, xd]
            out |= s
        out &= ~alpha
        self.a[out] = color
        return self

    def rim_light(self, light=0.25, dark=0.3):
        """Lighten pixels whose upper-left neighbor is empty; darken lower-right edge pixels."""
        alpha = self.a[:, :, 3] > 0
        new = self.a.copy()
        for y in range(self.h):
            for x in range(self.w):
                if not alpha[y, x]:
                    continue
                c = tuple(int(v) for v in self.a[y, x])
                if c[:3] == (20, 14, 28):
                    continue
                up = alpha[y - 1, x] if y > 0 else False
                lf = alpha[y, x - 1] if x > 0 else False
                dn = alpha[y + 1, x] if y < self.h - 1 else False
                rt = alpha[y, x + 1] if x < self.w - 1 else False
                if not up or not lf:
                    new[y, x] = shade(c, light)
                elif not dn or not rt:
                    new[y, x] = shade(c, -dark)
        self.a = new
        return self

    def image(self):
        return Image.fromarray(self.a, "RGBA")


def _inside(x, y, pts):
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def sheet(frames, cols=None):
    """Pack equally-sized Canvas frames into one image (left to right, then down)."""
    cols = cols or len(frames)
    fw, fh = frames[0].w, frames[0].h
    rows = (len(frames) + cols - 1) // cols
    img = Image.new("RGBA", (fw * cols, fh * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        img.paste(f.image(), ((i % cols) * fw, (i // cols) * fh))
    return img


def aura_map(img, fw, fh, radius=4):
    """For each frame, encode distance (1..radius) from the silhouette in the red channel.

    red = distance/radius * 255 for ring pixels, alpha 255; 0 elsewhere. Distance is chebyshev-ish (rounded euclid).
    """
    a = np.array(img)
    alpha = a[:, :, 3] > 0
    H, W = alpha.shape
    out = np.zeros((H, W, 4), dtype=np.uint8)
    for fy in range(0, H, fh):
        for fx in range(0, W, fw):
            sub = alpha[fy:fy + fh, fx:fx + fw]
            ys, xs = np.nonzero(sub)
            if len(xs) == 0:
                continue
            pts = np.stack([xs, ys], 1)
            for y in range(fh):
                for x in range(fw):
                    if sub[y, x]:
                        continue
                    d = np.sqrt(((pts - (x, y)) ** 2).sum(1)).min()
                    if d <= radius + 0.3:
                        dd = max(1, int(round(d)))
                        out[fy + y, fx + x] = (int(dd / radius * 255), 0, 0, 255)
    return Image.fromarray(out, "RGBA")


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def noise_fill(cv, x, y, w, h, base, rnd, var=0.08, speck=None, speck_p=0.0):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            f = rnd.uniform(-var, var)
            c = shade(base, f)
            if speck and rnd.random() < speck_p:
                c = speck
            cv.px(xx, yy, c)
