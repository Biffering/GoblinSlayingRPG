"""The battle-worn GOBLIN SLAYER logo: heavy iron letters, chipped edges, cracks, scratches and rust."""
import math
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"


def build(out_dir, text="GOBLIN SLAYER", size=46, seed=7):
    rnd = random.Random(seed)
    f = ImageFont.truetype(FONT, size)
    pad = 8
    tmp = Image.new("L", (1, 1))
    bb = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=f)
    W, H = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), text, font=f, fill=255)
    mask = np.array(m) > 110
    # --- battle damage: chips bitten out of the edges
    ys, xs = np.nonzero(mask)
    edge = []
    for y, x in zip(ys, xs):
        if not (mask[y - 1, x] and mask[y + 1, x] and mask[y, x - 1] and mask[y, x + 1]):
            edge.append((y, x))
    for _ in range(int(len(edge) * 0.035)):
        y, x = edge[rnd.randrange(len(edge))]
        r = rnd.choice((1, 1, 2, 2, 3))
        ang = rnd.uniform(0, math.tau)
        for yy in range(y - r, y + r + 1):
            for xx in range(x - r, x + r + 1):
                # wedge-shaped notch
                if (yy - y) ** 2 + (xx - x) ** 2 <= r * r and rnd.random() < 0.85:
                    if 0 <= yy < H and 0 <= xx < W:
                        mask[yy, xx] = False
    # --- a few letters split right through
    cracks = []
    for _ in range(9):
        x = rnd.randrange(pad, W - pad)
        y = pad
        pts = [(x, y)]
        while y < H - pad:
            y += rnd.randint(2, 4)
            x += rnd.randint(-2, 2)
            pts.append((x, y))
        cracks.append(pts)
    crack_px = np.zeros_like(mask)
    for pts in cracks:
        full = rnd.random() < 0.45     # some cracks break the letter apart, others are just dark fissures
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(abs(x1 - x0), abs(y1 - y0), 1)
            for i in range(n + 1):
                x = round(x0 + (x1 - x0) * i / n)
                y = round(y0 + (y1 - y0) * i / n)
                if 0 <= x < W and 0 <= y < H and mask[y, x]:
                    if full:
                        mask[y, x] = False
                    else:
                        crack_px[y, x] = True
    # --- iron fill: bright steel at the top, dark at the bottom, rust blotches
    img = np.zeros((H, W, 4), np.uint8)
    top = np.array([236, 232, 220])
    mid = np.array([150, 150, 156])
    bot = np.array([70, 66, 74])
    rows = np.nonzero(mask.any(axis=1))[0]
    y0, y1 = rows.min(), rows.max()
    for y in range(H):
        t = (y - y0) / max(1, (y1 - y0))
        c = top * (1 - t * 2) + mid * (t * 2) if t < 0.5 else mid * (1 - (t - 0.5) * 2) + bot * ((t - 0.5) * 2)
        for x in range(W):
            if mask[y, x]:
                n = rnd.uniform(-10, 10)
                img[y, x, :3] = np.clip(c + n, 0, 255)
                img[y, x, 3] = 255
    # rust and grime
    for _ in range(40):
        cx, cy, r = rnd.randrange(W), rnd.randrange(H), rnd.uniform(1.5, 4.5)
        col = np.array(rnd.choice([(150, 70, 36), (120, 56, 30), (90, 60, 40)]))
        for yy in range(int(cy - r), int(cy + r) + 1):
            for xx in range(int(cx - r), int(cx + r) + 1):
                if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r and rnd.random() < 0.6:
                    img[yy, xx, :3] = (img[yy, xx, :3] * 0.35 + col * 0.65).astype(np.uint8)
    # scratches
    for _ in range(26):
        x, y = rnd.randrange(W), rnd.randrange(H)
        L = rnd.randint(3, 9)
        dx, dy = rnd.choice(((1, 1), (1, -1), (2, 1), (1, 0)))
        for i in range(L):
            xx, yy = x + dx * i, y + dy * i // max(1, abs(dx))
            if 0 <= yy < H and 0 <= xx < W and mask[yy, xx]:
                img[yy, xx, :3] = np.clip(img[yy, xx, :3].astype(int) + 70, 0, 255)
    img[crack_px, :3] = (40, 26, 30)
    # bevel: bright lip on top edges, dark lip on bottom edges
    for y in range(1, H - 1):
        for x in range(W):
            if not mask[y, x]:
                continue
            if not mask[y - 1, x]:
                img[y, x, :3] = np.clip(img[y, x, :3].astype(int) + 60, 0, 255)
            elif not mask[y + 1, x]:
                img[y, x, :3] = (img[y, x, :3] * 0.55).astype(np.uint8)
    # thick dark outline (2px) and a blood-red drop shadow underneath
    out = np.zeros((H + 4, W + 4, 4), np.uint8)
    big = np.zeros((H + 4, W + 4), bool)
    big[2:-2, 2:-2] = mask
    ring = np.zeros_like(big)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if abs(dx) + abs(dy) <= 3:
                ring |= np.roll(np.roll(big, dy, 0), dx, 1)
    shadow = np.roll(np.roll(ring, 3, 0), 2, 1) & ~ring
    out[shadow] = (90, 14, 18, 230)
    out[ring] = (24, 16, 20, 255)
    out[2:-2, 2:-2][mask] = img[mask]
    Image.fromarray(out, "RGBA").save(out_path(out_dir))
    return out.shape


def out_path(out_dir):
    return f"{out_dir}/ui/title_logo.png"


if __name__ == "__main__":
    print(build(sys.argv[1]))
