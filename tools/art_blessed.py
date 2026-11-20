"""Sprites for the Blessed (white-cloaked LPC figures with laser weapons) and the seven hunt bosses.

usage: python3 art_blessed.py <assets_dir>     (after art_lpc.py; it adds to enemies/sizes.json)
"""
import json
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import art_lpc as AL
import lpc
from art_common import save

EN = None


def crop(a, pad=2):
    ys, xs = np.nonzero(a[:, :, 3])
    return a[max(0, ys.min() - pad):ys.max() + 1, max(0, xs.min() - pad):xs.max() + pad + 1]


def lum(a):
    return (0.3 * a[:, :, 0] + 0.59 * a[:, :, 1] + 0.11 * a[:, :, 2]) / 255.0


def ramp(a, cols, gain=1.0, mask=None):
    """Repaint by brightness onto a list of colors (dark -> light)."""
    out = a.copy()
    m = a[:, :, 3] > 0 if mask is None else mask
    l = np.clip(lum(a) * gain, 0, 0.999)
    idx = (l * len(cols)).astype(int)
    pal = np.array([AL._hx(c)[:3] for c in cols], dtype=np.uint8)
    out[m, :3] = pal[idx[m]]
    return out


def up(a, k):
    img = Image.fromarray(a, "RGBA")
    return np.array(img.resize((img.width * k, img.height * k), Image.NEAREST))


# ------------------------------------------------------------------ the Blessed

def blessed_recipe():
    return ("male", [("body", {"color": "light"}), ("heads_human_male", {"color": {"color_1": "light", "color_2": "blue"}}),
                     ("legs_pants", {"color": "white"}), ("feet_boots_basic", {"color": "white"}),
                     ("torso_clothes_robe", {"color": "white"}), ("cape_solid", {"color": "white"}),
                     ("facial_mask_plain", {"variant": "white"}), ("hat_hood_cloth", {"color": "white"}),
                     ("belt_leather", {"variant": "brass"})], {})


def blessed_image(style):
    body, items, opts = blessed_recipe()
    base = np.array(AL.battle_sheet((body, items, opts)))[:, 0:96].copy()
    wpn = np.array(AL.blessed_sheet(body, style, None))[:, 0:96]
    m = wpn[:, :, 3] > 0
    base[m] = wpn[m]
    # a soft pale shimmer on the cloth, and two lenses of light where the eyes would be
    cloth = (base[:, :, 3] > 0) & (lum(base) > 0.55)
    base[cloth, :3] = np.clip(base[cloth, :3].astype(int) * 0.9 + np.array([12, 22, 30]), 0, 255).astype(np.uint8)
    hood = np.array(lpc.compose(body, [("hat_hood_cloth", {"color": "white"})], "walk", 96))
    # find the face area: inside the hood's outline, under its top
    ys, xs = np.nonzero(base[:, :, 3])
    top = ys.min()
    face_y = top + 13
    xs_row = np.nonzero(base[face_y, :, 3])[0]
    if len(xs_row):
        cx = int(xs_row.min() + 5)
        for dx in (0, 4):
            base[face_y:face_y + 2, cx + dx:cx + dx + 2] = (150, 245, 255, 255)
    a = crop(base)
    a = a[:, ::-1].copy()          # enemies face right
    return a


# ------------------------------------------------------------------ hunt bosses

def quickfang():
    a = np.array(Image.open(f"{EN}/rat_wind.png").convert("RGBA"))
    a = ramp(a, ["#1a2224", "#4a5a5e", "#9ab0b4", "#d8e8ea", "#ffffff"], 1.25)
    a = up(a, 3)
    # speed streaks trailing behind
    out = np.zeros((a.shape[0], a.shape[1] + 30, 4), np.uint8)
    out[:, 30:] = a
    ys = np.nonzero(a[:, :, 3].any(axis=1))[0]
    for k, y in enumerate(range(ys.min() + 12, ys.max() - 10, 9)):
        ln = 14 + (k * 7) % 16
        out[y:y + 2, 30 - ln:30 + 4] = (200, 245, 240, 140)
    return out


def first_piece(a):
    """Keep only the leftmost figure when a sheet row holds several frames."""
    cols = a[:, :, 3].any(axis=0)
    xs = np.nonzero(cols)[0]
    if len(xs) == 0:
        return a
    start = xs[0]
    end = start
    while end + 1 < len(cols) and (cols[end + 1] or (end + 2 < len(cols) and cols[end + 2])):
        end += 1
    return a[:, start:end + 1]


def ironshell():
    a = first_piece(np.array(AL.monster_image("beetle", None, 1)))
    a = ramp(a, ["#14110e", "#3a3530", "#6a625a", "#9a9088", "#c8bea8"], 1.15)
    a = up(a, 4)
    # rust streaks and rivets on the shell
    rng = np.random.default_rng(3)
    ys, xs = np.nonzero(a[:, :, 3])
    for _ in range(40):
        i = rng.integers(len(ys))
        y, x = ys[i], xs[i]
        if lum(a)[y, x] > 0.35:
            a[y:y + 2, x:x + 2, :3] = (176, 120, 60) if rng.random() < 0.5 else (230, 200, 120)
    return a


def glass_wyrm():
    a = np.array(AL.monster_image("snake", None, 1))
    a = up(a, 4)
    l = lum(a)
    m = a[:, :, 3] > 0
    c0 = np.array([90, 170, 210], float)
    c1 = np.array([235, 250, 255], float)
    mix = np.clip(l * 1.4, 0, 1)[..., None]
    a[m, :3] = (c0 * (1 - mix[m]) + c1 * mix[m]).astype(np.uint8)
    a[m, 3] = 225
    # prismatic glints
    rng = np.random.default_rng(5)
    ys, xs = np.nonzero(m)
    for _ in range(35):
        i = rng.integers(len(ys))
        a[ys[i], xs[i]] = [(255, 255, 255, 255), (255, 140, 200, 255), (140, 255, 200, 255), (255, 240, 140, 255)][rng.integers(4)]
    return a


def gilded_mimic(assets):
    ch = np.array(Image.open(f"{assets}/ui/chest.png").convert("RGBA"))
    ch = ramp(ch, ["#2a1606", "#6a4410", "#b8862a", "#f0d070", "#fff4c0"], 1.2)
    ch = up(ch, 3)
    h, w = ch.shape[:2]
    out = np.zeros((h + 30, w + 20, 4), np.uint8)
    img = Image.fromarray(out, "RGBA")
    d = ImageDraw.Draw(img)
    # spider legs
    for i, lx in enumerate((14, 26, w - 6, w + 6)):
        d.line([(lx, h - 6), (lx + (-10 if i < 2 else 10), h + 10), (lx + (-6 if i < 2 else 6), h + 28)], fill=(40, 26, 14, 255), width=3)
        d.line([(lx, h - 6), (lx + (-10 if i < 2 else 10), h + 10)], fill=(120, 80, 30, 255), width=1)
    img.alpha_composite(Image.fromarray(ch, "RGBA"), (10, 0))
    d = ImageDraw.Draw(img)
    # a grinning mouth where the lid meets the box: teeth, tongue, eyes
    my = int(h * 0.45)
    d.rectangle([14, my - 3, w + 6, my + 6], fill=(30, 6, 8, 255))
    d.polygon([(w // 2, my + 2), (w // 2 + 16, my + 18), (w // 2 + 28, my + 6)], fill=(200, 60, 80, 255))
    for x in range(16, w + 6, 6):
        d.polygon([(x, my - 3), (x + 4, my - 3), (x + 2, my + 3)], fill=(240, 236, 220, 255))
        d.polygon([(x + 2, my + 6), (x + 6, my + 6), (x + 4, my)], fill=(240, 236, 220, 255))
    for ex in (w - 6, w + 4):
        d.rectangle([ex, my - 14, ex + 3, my - 11], fill=(255, 60, 40, 255))
    return np.array(img)


def mirror_moth():
    a = first_piece(np.array(AL.monster_image("bat", None, 1)))
    a = ramp(a, ["#1a1624", "#5a5470", "#a8a4c4", "#e4e2f4", "#ffffff"], 1.5)
    a = up(a, 4)
    m = a[:, :, 3] > 0
    rng = np.random.default_rng(9)
    ys, xs = np.nonzero(m & (lum(a) > 0.7))
    for _ in range(30):
        if len(ys):
            i = rng.integers(len(ys))
            a[ys[i]:ys[i] + 2, xs[i]:xs[i] + 2] = (255, 255, 255, 255)
    return a


def woolgorger():
    a = np.array(Image.open(f"{EN}/bear_stone.png").convert("RGBA"))
    a = up(a, 3)
    m = a[:, :, 3] > 0
    l = lum(a)
    rng = np.random.default_rng(11)
    noise = rng.random(l.shape) * 0.18
    body = m & (l > 0.18)
    tone = np.clip(l * 0.9 + 0.35 + noise, 0, 1)[..., None]
    cream = np.array([214, 196, 160], float)
    a[body, :3] = (cream * tone[body]).clip(0, 255).astype(np.uint8)
    face = m & (l <= 0.18)
    a[face, :3] = (36, 28, 24)
    # sheep bells around the neck
    ys, xs = np.nonzero(m)
    ny = ys.min() + int((ys.max() - ys.min()) * 0.42)
    for k, x in enumerate(range(xs.min() + 18, xs.max() - 10, 12)):
        if a[ny, x, 3]:
            a[ny:ny + 5, x:x + 4] = (200, 160, 60, 255)
            a[ny + 4, x + 1:x + 3] = (60, 40, 20, 255)
    return a


def lamp_shade():
    a = np.array(Image.open(f"{EN}/ghost_void.png").convert("RGBA"))
    a = up(a, 3)
    m = a[:, :, 3] > 0
    l = lum(a)
    eyes = m & (l > 0.93)
    a[m, :3] = (np.array([18, 10, 30], float) + np.array([60, 30, 90], float) * l[m, None]).astype(np.uint8)
    a[eyes, :3] = (255, 220, 80)
    img = Image.fromarray(a, "RGBA")
    d = ImageDraw.Draw(img)
    # a little paper lantern in its claw
    W, H = img.size
    lx, ly = W - 22, int(H * 0.55)
    d.ellipse([lx - 14, ly - 14, lx + 14, ly + 14], fill=(255, 210, 90, 70))
    d.rectangle([lx - 5, ly - 7, lx + 5, ly + 7], fill=(255, 220, 120, 255), outline=(120, 60, 20, 255))
    d.line([(lx, ly - 7), (lx, ly - 16)], fill=(40, 30, 30, 255), width=1)
    return np.array(img)


def map_icon(a, size=56):
    img = Image.fromarray(a, "RGBA")
    k = min(size / img.width, size / img.height, 1.0)
    img = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.NEAREST)
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    out.alpha_composite(img, ((64 - img.width) // 2, 64 - img.height - 2))
    return out


def build(assets):
    global EN
    EN = f"{assets}/enemies"
    sizes_path = f"{EN}/sizes.json"
    sizes = json.load(open(sizes_path)) if os.path.exists(sizes_path) else {}
    for kind, style in (("blessed_warden", "blade"), ("blessed_lancer", "rifle"), ("blessed_seraph", "staff")):
        a = blessed_image(style)
        save(Image.fromarray(a, "RGBA"), f"{EN}/u_{kind}.png")
        sizes[kind] = [a.shape[1], a.shape[0]]
        print("blessed", kind, a.shape[:2])
    for bid, fn in (("quickfang", quickfang), ("ironshell", ironshell), ("glass_wyrm", glass_wyrm),
                    ("gilded_mimic", lambda: gilded_mimic(assets)), ("mirror_moth", mirror_moth),
                    ("woolgorger", woolgorger), ("lamp_shade", lamp_shade)):
        a = fn()
        a = crop(a)
        save(Image.fromarray(a, "RGBA"), f"{EN}/u_{bid}.png")
        save(map_icon(a), f"{EN}/map_{bid}.png")
        sizes[bid] = [a.shape[1], a.shape[0]]
        print("hunt", bid, a.shape[:2])
    json.dump(sizes, open(sizes_path, "w"))
    # the treasure hunters themselves
    import zlib
    db = json.load(open(os.path.join(os.path.dirname(assets.rstrip("/")), "data", "db.json")))
    for hid, h in db.get("hunts", {}).items():
        for i, lk in enumerate(h["looks"]):
            r = AL.npc_recipe(lk, zlib.crc32(f"{hid}{i}".encode()))
            save(AL.map_sheet(r), f"{assets}/chars/npc_hunt_{hid}_{i}.png")
        print("hunters", hid)


if __name__ == "__main__":
    build(sys.argv[1])
