"""UI pieces (window, cursor, icons) and battle backgrounds."""
import math
import random
import sys

from art_common import Canvas, hexc, mix, shade, save

K = (20, 14, 28, 255)


def window(top, bot, border="#f0f0f8"):
    c = Canvas(24, 24)
    t, b = hexc(top), hexc(bot)
    for y in range(24):
        col = mix(t, b, y / 23)
        c.rect(0, y, 24, 1, col)
    bc = hexc(border)
    c.rect(0, 0, 24, 1, K)
    c.rect(0, 23, 24, 1, K)
    c.rect(0, 0, 1, 24, K)
    c.rect(23, 0, 1, 24, K)
    c.rect(1, 1, 22, 1, bc)
    c.rect(1, 22, 22, 1, shade(bc, -0.35))
    c.rect(1, 1, 1, 22, bc)
    c.rect(22, 1, 1, 22, shade(bc, -0.35))
    c.rect(2, 2, 20, 1, shade(bc, -0.55))
    c.rect(2, 2, 1, 20, shade(bc, -0.55))
    for p in ((0, 0), (23, 0), (0, 23), (23, 23)):
        c.a[p[1], p[0]] = (0, 0, 0, 0)
    return c


def cursor():
    c = Canvas(14, 11)
    w = hexc("#ffffff")
    pts = ["..KKKK........", ".KwwwwKKKKKK..", "KwwwwwwwwwwwK.", "KwwwwwKKKKKK..", "KwwwwwwK......",
           "KwwwwwwK......", "KwwwwwwK......", ".KwwwwK.......", "..KKKK........", "..............", ".............."]
    for y, row in enumerate(pts):
        for x, ch in enumerate(row):
            if ch == "K":
                c.px(x, y, K)
            elif ch == "w":
                c.px(x, y, w if y < 4 else hexc("#d8d8e8"))
    return c


ICONS = ["blade", "bow", "staff", "armor", "acc", "potion", "ether", "feather", "elixir", "tonic", "key", "summon",
         "fire", "water", "wind", "stone", "spirit", "void", "gold", "bomb"]
EL_COL = {"fire": "#ff5a2a", "water": "#3a8aff", "wind": "#40d8c0", "stone": "#6ab84a", "spirit": "#f8f4e8", "void": "#9a50ff"}


def icon(name):
    c = Canvas(10, 10)
    if name == "blade":
        c.line(2, 8, 8, 2, hexc("#d0d4e0"), 1)
        c.line(3, 8, 8, 3, hexc("#8a8e9a"), 1)
        c.line(1, 6, 4, 9, hexc("#d0a040"))
        c.px(1, 9, hexc("#6a4a2a"))
    elif name == "bow":
        for t in range(9):
            c.px(round(3 + 3 * math.sin(t / 8 * math.pi)), t, hexc("#a06a3a"))
        c.line(3, 0, 3, 8, hexc("#f0f0f0"))
    elif name == "staff":
        c.line(2, 9, 7, 3, hexc("#8a5a2a"), 1)
        c.ellipse(7.5, 2.5, 2, 2, hexc("#a0c0ff"))
    elif name == "armor":
        c.poly([(1, 1), (9, 1), (8, 9), (2, 9)], hexc("#a0a4b0"))
        c.rect(4, 1, 2, 3, hexc("#5a5e6a"))
    elif name == "acc":
        c.ellipse(5, 5, 3.5, 3.5, hexc("#f0c040"))
        c.ellipse(5, 5, 1.8, 1.8, (0, 0, 0, 0))
        c.a[4:7, 4:7] = 0
        c.px(5, 1, hexc("#ffffff"))
    elif name in ("potion", "ether", "elixir", "tonic"):
        col = {"potion": "#e04040", "ether": "#4080ff", "elixir": "#f0d040", "tonic": "#40d080"}[name]
        c.rect(4, 0, 2, 3, hexc("#d0d0d0"))
        c.ellipse(5, 6, 3.5, 3.5, hexc(col))
        c.px(3, 5, hexc("#ffffff"))
    elif name == "feather":
        c.line(2, 9, 7, 1, hexc("#ff8040"), 2)
        c.line(2, 9, 6, 3, hexc("#ffe080"), 1)
    elif name == "key":
        c.ellipse(3, 3, 2.5, 2.5, hexc("#f0c040"))
        c.line(4, 4, 8, 8, hexc("#f0c040"))
        c.px(7, 8, hexc("#f0c040"))
        c.px(8, 6, hexc("#f0c040"))
    elif name == "summon":
        c.poly([(5, 0), (9, 5), (5, 9), (1, 5)], hexc("#c080ff"))
        c.px(4, 3, hexc("#ffffff"))
    elif name in EL_COL:
        col = hexc(EL_COL[name])
        if name == "fire":
            c.poly([(5, 0), (8, 6), (5, 9), (2, 6)], col)
            c.ellipse(5, 6.5, 1.5, 2, hexc("#ffe060"))
        elif name == "water":
            c.poly([(5, 0), (8, 6), (5, 9), (2, 6)], col)
            c.px(4, 5, hexc("#ffffff"))
        elif name == "wind":
            c.line(1, 3, 7, 3, col)
            c.line(2, 6, 9, 6, col)
            c.px(8, 2, col)
            c.px(9, 5, col)
        elif name == "stone":
            c.poly([(1, 8), (3, 2), (7, 1), (9, 6), (7, 9)], col)
        elif name == "spirit":
            c.ellipse(5, 5, 3, 3, col)
            for a in range(8):
                c.px(round(5 + math.cos(a * math.pi / 4) * 4.5), round(5 + math.sin(a * math.pi / 4) * 4.5), col)
        else:
            c.ellipse(5, 5, 4, 4, col)
            c.ellipse(5, 5, 2, 2, hexc("#100818"))
    elif name == "gold":
        c.ellipse(5, 5, 3.5, 3.5, hexc("#f0c040"))
        c.rect(4, 3, 2, 4, hexc("#c09020"))
    elif name == "bomb":
        c.ellipse(5, 6, 3.5, 3.5, hexc("#505060"))
        c.line(6, 2, 8, 0, hexc("#ffb040"))
    c.outline()
    return c


# ------------------------------------------------------------------ battle backgrounds (480x176)

BW, BH = 480, 176
BG = {
    "fire":   dict(sky=("#2a0a0a", "#a03a1a"), far="#3a1410", mid="#24100e", ground=("#4a2620", "#2a1410"), glow="#ff6a1a"),
    "water":  dict(sky=("#5aa8e8", "#d0eeff"), far="#3a7aa8", mid="#2a6a7a", ground=("#d8c48a", "#a89060"), glow="#ffffff"),
    "wind":   dict(sky=("#3a8ae0", "#c8f0ff"), far="#a8d0e8", mid="#5a9a4a", ground=("#7aba5a", "#4a8a3a"), glow="#ffffff"),
    "stone":  dict(sky=("#5a4a3a", "#c0a070"), far="#6a5a4a", mid="#4a4036", ground=("#7a6a56", "#4a4034"), glow="#ffd070"),
    "spirit": dict(sky=("#a8a0e8", "#fff8f0"), far="#d8d0f8", mid="#b8b0e0", ground=("#e0d8f4", "#b8b0d8"), glow="#ffffff"),
    "goblin": dict(sky=("#0a0c04", "#2a3010"), far="#1e220e", mid="#14180a", ground=("#3a3a22", "#1a1a0e"), glow="#c0e040"),
    "void":   dict(sky=("#05040a", "#2a1a40"), far="#1a1028", mid="#120c1c", ground=("#2a2236", "#120e1a"), glow="#9a50ff"),
}


def backdrop(world, kind, seed):
    rnd = random.Random(seed)
    p = BG[world]
    c = Canvas(BW, BH)
    horizon = 100
    if kind == "out":
        top, bot = hexc(p["sky"][0]), hexc(p["sky"][1])
        for y in range(horizon):
            c.rect(0, y, BW, 1, mix(top, bot, (y / horizon) ** 1.3))
        if world == "void":
            for _ in range(160):
                c.px(rnd.randrange(BW), rnd.randrange(horizon), hexc("#ffffff") if rnd.random() < 0.7 else hexc("#c0a0ff"))
        if world in ("water", "wind", "spirit"):
            for _ in range(7):
                cx, cy = rnd.randrange(BW), rnd.randrange(10, 60)
                for k in range(4):
                    c.ellipse(cx + k * 14 - 20, cy + rnd.randrange(-3, 4), 18, 7, (255, 255, 255, 170))
        if world == "fire":
            c.ellipse(380, 30, 26, 26, hexc("#ff9a40"))
            c.ellipse(380, 30, 20, 20, hexc("#ffd080"))
        # far mountains
        far = hexc(p["far"])
        h = rnd.uniform(40, 60)
        for x in range(BW):
            h += rnd.uniform(-2.2, 2.2)
            h = max(25, min(75, h))
            c.rect(x, horizon - int(h), 1, int(h), far)
        if world == "fire":
            for _ in range(3):  # volcano glow
                x = rnd.randrange(40, BW - 40)
                c.line(x, horizon - 50, x + rnd.randrange(-20, 20), horizon, hexc(p["glow"]), 2)
        mid = hexc(p["mid"])
        h = rnd.uniform(15, 25)
        for x in range(BW):
            h += rnd.uniform(-1.6, 1.6)
            h = max(8, min(35, h))
            c.rect(x, horizon - int(h), 1, int(h), mid)
            if world in ("wind", "stone", "water") and rnd.random() < 0.06:  # little trees on the ridge
                c.ellipse(x, horizon - h - 3, 3, 4, shade(mid, -0.15))
        if world == "water":
            for y in range(horizon - 6, horizon + 6):
                c.rect(0, y, BW, 1, mix(hexc("#2a6ac8"), hexc("#5aa8e8"), (y - horizon + 6) / 12))
        g0, g1 = hexc(p["ground"][0]), hexc(p["ground"][1])
        for y in range(horizon, BH):
            t = (y - horizon) / (BH - horizon)
            c.rect(0, y, BW, 1, mix(g1, g0, t))
        for _ in range(500):
            y = rnd.randrange(horizon, BH)
            x = rnd.randrange(BW)
            c.px(x, y, shade(mix(g1, g0, (y - horizon) / (BH - horizon)), rnd.choice((-0.15, 0.12))))
        if world == "void":
            for _ in range(60):
                c.px(rnd.randrange(BW), rnd.randrange(horizon, BH), hexc("#9a50ff"))
    else:  # interior: cave / dungeon / sanctum
        wall = shade(hexc(p["mid"]), 0.15 if world not in ("spirit",) else -0.05)
        if world in ("spirit",):
            wall = hexc("#cfc8e8")
        if world == "wind":
            wall = hexc("#e0d8c0")
        c.rect(0, 0, BW, BH, shade(wall, -0.35))
        # back wall with bricks / rock
        for y in range(0, horizon, 8):
            off = 0 if (y // 8) % 2 == 0 else 12
            for x in range(-off, BW, 24):
                col = shade(wall, rnd.uniform(-0.15, 0.1) - (1 - y / horizon) * 0.3)
                c.rect(x + 1, y + 1, 22, 6, col)
        # pillars
        for x in range(30, BW, 110):
            col = shade(wall, 0.2)
            c.rect(x, 0, 18, horizon + 6, col)
            c.rect(x, 0, 4, horizon + 6, shade(col, 0.2))
            c.rect(x + 14, 0, 4, horizon + 6, shade(col, -0.25))
            # torch / glow on pillar
            gl = hexc(p["glow"])
            c.ellipse(x + 9, 46, 10, 10, gl[:3] + (60,))
            c.ellipse(x + 9, 46, 4, 6, gl)
            c.ellipse(x + 9, 47, 2, 3, hexc("#ffffff"))
        if kind == "sanctum":
            for _ in range(90):
                c.px(rnd.randrange(BW), rnd.randrange(horizon), hexc(p["glow"]))
            c.ellipse(BW // 2, 44, 60, 40, hexc(p["glow"])[:3] + (50,))
        g0, g1 = hexc(p["ground"][0]), hexc(p["ground"][1])
        for y in range(horizon, BH):
            t = (y - horizon) / (BH - horizon)
            c.rect(0, y, BW, 1, mix(shade(g1, -0.2), shade(g0, -0.1), t))
        for y in range(horizon + 4, BH, 10):
            c.rect(0, y, BW, 1, shade(g0, -0.3))
        for _ in range(300):
            c.px(rnd.randrange(BW), rnd.randrange(horizon, BH), shade(g0, rnd.choice((-0.25, 0.1))))
    return c


def chest(open_):
    c = Canvas(16, 16)
    wd, band = hexc("#8a5a2a"), hexc("#e0b040")
    c.ellipse(8, 14.5, 7, 1.5, (0, 0, 0, 90))
    c.rect(2, 7, 12, 7, wd)
    c.rect(2, 7, 12, 1, shade(wd, 0.25))
    c.rect(2, 13, 12, 1, shade(wd, -0.35))
    if open_:
        c.rect(2, 3, 12, 4, shade(wd, -0.45))
        c.rect(3, 4, 10, 3, hexc("#1a1008"))
        c.rect(2, 2, 12, 2, shade(wd, 0.1))
    else:
        c.rect(2, 3, 12, 4, shade(wd, 0.1))
        c.rect(2, 3, 12, 1, shade(wd, 0.35))
        c.rect(7, 6, 2, 3, band)
    c.rect(4, 3 if not open_ else 2, 1, 11 if not open_ else 12, band)
    c.rect(11, 3 if not open_ else 2, 1, 11 if not open_ else 12, band)
    c.outline()
    return c


def tiny_chests(out):
    import art_kenney as AK
    if AK.available():
        from PIL import Image as _I
        _I.fromarray(AK.tile("dungeon", 89), "RGBA").save(f"{out}/ui/chest.png")
        _I.fromarray(AK.tile("dungeon", 91), "RGBA").save(f"{out}/ui/chest_open.png")


def build(out):
    save(chest(False).image(), f"{out}/ui/chest.png")
    save(chest(True).image(), f"{out}/ui/chest_open.png")
    save(window("#3a4ac0", "#121a6a").image(), f"{out}/ui/window.png")
    save(window("#2a2a3a", "#0a0a14", "#c8c8d8").image(), f"{out}/ui/window_dark.png")
    save(window("#6a3a10", "#2a1004", "#ffd070").image(), f"{out}/ui/window_gold.png")
    save(cursor().image(), f"{out}/ui/cursor.png")
    from art_common import sheet
    save(sheet([icon(n) for n in ICONS], cols=len(ICONS)), f"{out}/ui/icons.png")
    for w in BG:
        save(backdrop(w, "out", hash(w) & 0xFFFF).image(), f"{out}/bg/{w}_out.png")
        save(backdrop(w, "in", hash(w + "i") & 0xFFFF).image(), f"{out}/bg/{w}_in.png")
    for w in ("spirit", "void"):
        save(backdrop(w, "sanctum", 7).image(), f"{out}/bg/{w}_sanctum.png")
    import json
    json.dump(ICONS, open(f"{out}/ui/icons.json", "w"))


if __name__ == "__main__":
    build(sys.argv[1])
    tiny_chests(sys.argv[1])
    print("ui + backgrounds done")
