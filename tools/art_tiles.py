"""World tilesets (16x16) for Six Hearths. Each world draws the same tile names its own way."""
import json
import math
import random

from art_common import Canvas, hexc, mix, shade, noise_fill, sheet, save

T = 16
TILE_NAMES = (
    ["outside"] + [f"ground{i}" for i in range(4)] + [f"path{i}" for i in range(2)] + [f"grass{i}" for i in range(2)]
    + [f"flower{i}" for i in range(2)] + [f"tree{i}" for i in range(2)] + [f"rock{i}" for i in range(2)]
    + [f"liquid{i}" for i in range(3)] + [f"liquid_edge{i}" for i in range(3)] + ["bridge", "wall_top", "wall_face0", "wall_face1"]
    + [f"floor{i}" for i in range(3)] + ["roof_top", "roof_mid", "roof_bot", "hwall", "window", "door", "awning", "counter",
                                         "fence", "lamp0", "lamp1", "bench"]
    + [f"feat_{p}{i}" for i in range(2) for p in ("tl", "tr", "bl", "br")]
    + ["landmark_top", "landmark_bot", "pillar", "torch0", "torch1", "torch2", "bones", "crystal0", "crystal1", "statue"]
    + [f"portal{i}" for i in range(4)] + ["cave_mouth", "stairs", "keeper_floor"]
)
import art_tiles2 as AT2
TILE_NAMES = list(TILE_NAMES) + list(AT2.NEW_TILES)
INDEX = {n: i for i, n in enumerate(TILE_NAMES)}

PAL = {
    "nexus": dict(ground="#3b4a5e", ground2="#34425a", path="#8a8fa8", grass="#6a8aa0", flower="#e0c0ff", tree="#2a5a5a",
                  trunk="#3a2a3a", rock="#5a5a78", liquid="#4a3a8a", liquid_hi="#a08aff", bridge="#7a6a5a",
                  wall="#3a3a52", floor="#5a5a74", roof="#6a4a8a", hwall="#a0a0b8", trim="#f0d070", accent="#f0d070",
                  awning2="#ffffff", light="#ffe9a0", crystal="#c0a0ff", portal="#ffffff"),
    "fire": dict(ground="#4a2c24", ground2="#3e241e", path="#7a6660", grass="#6a3a1a", flower="#ff8a2a", tree="#2a1a18",
                 trunk="#1a100e", rock="#2a2230", liquid="#ff6a1a", liquid_hi="#ffe060", bridge="#5a5a60",
                 wall="#3a2220", floor="#5a3a32", roof="#a8361e", hwall="#c09070", trim="#e0a040", accent="#e04a20",
                 awning2="#f0d090", light="#ffb040", crystal="#ff7a30", portal="#ff8a60", leaf="#c0401a"),
    "water": dict(ground="#d8c48a", ground2="#ccb87e", path="#a08a62", grass="#8aa86a", flower="#ff8aa8", tree="#3a8a4a",
                  trunk="#8a6a3a", rock="#c07a6a", liquid="#2a6ac8", liquid_hi="#a8e0ff", bridge="#8a6a42",
                  wall="#3a5a6a", floor="#6a8a8a", roof="#2a7a8a", hwall="#f0ece0", trim="#3a5a8a", accent="#2a8ab0",
                  awning2="#ffffff", light="#ffe8a0", crystal="#c0f0ff", portal="#80c0ff", leaf="#4aa85a"),
    "wind": dict(ground="#6aaa4a", ground2="#62a044", path="#c8b080", grass="#8ac85a", flower="#ffffff", tree="#3a8a3a",
                 trunk="#6a4a2a", rock="#e0e0d8", liquid="#a8d8ff", liquid_hi="#ffffff", bridge="#a0824a",
                 wall="#d8d0c0", floor="#e8e2d0", roof="#2a9a8a", hwall="#c09a6a", trim="#e0c050", accent="#30b0a0",
                 awning2="#f0f0f0", light="#fff0a0", crystal="#a0fff0", portal="#a0fff0", leaf="#5ab84a"),
    "stone": dict(ground="#6a6050", ground2="#625848", path="#8a8070", grass="#5a7a3a", flower="#c0a0e0", tree="#3a4a2a",
                  trunk="#4a3a2a", rock="#7a7a72", liquid="#3a5a4a", liquid_hi="#7aa08a", bridge="#7a5a3a",
                  wall="#4a4440", floor="#6a625a", roof="#5a6068", hwall="#a08a6a", trim="#d0a040", accent="#5a8a3a",
                  awning2="#e0d0a0", light="#ffd070", crystal="#ffd040", portal="#90e070", leaf="#4a6a2a"),
    "spirit": dict(ground="#c8c0e0", ground2="#beb6d8", path="#f0ecff", grass="#d8d0f0", flower="#fff0a0", tree="#f0f0ff",
                   trunk="#d0c8c0", rock="#b0b0d0", liquid="#a0e8ff", liquid_hi="#ffffff", bridge="#f0e8c0",
                   wall="#d8d0e8", floor="#ece8f8", roof="#e0c050", hwall="#f4f0e8", trim="#e0c050", accent="#a0a0f0",
                   awning2="#ffffff", light="#fffbe0", crystal="#ffffff", portal="#ffffff", leaf="#e8f8ff"),
    "goblin": dict(ground="#3a3a22", ground2="#32321c", path="#5a5236", grass="#4a5a20", flower="#c0d040", tree="#22301a",
                   trunk="#1a140c", rock="#3a3428", liquid="#5a7a1a", liquid_hi="#c0e040", bridge="#5a4630",
                   wall="#2e2a1e", floor="#4a4230", roof="#5a3a1a", hwall="#7a6a4a", trim="#e0c040", accent="#8ac030",
                   awning2="#e0d090", light="#d0f060", crystal="#f0c040", portal="#c0e040", leaf="#4a6a1a"),
    "void": dict(ground="#2a2236", ground2="#241e30", path="#4a4258", grass="#3a2e4a", flower="#b070ff", tree="#141018",
                 trunk="#0c0a10", rock="#3a3050", liquid="#0a0818", liquid_hi="#d0c0ff", bridge="#4a4058",
                 wall="#1c1826", floor="#342c42", roof="#4a2a6a", hwall="#6a6478", trim="#9050e0", accent="#7040c0",
                 awning2="#c0b0e0", light="#c090ff", crystal="#a060ff", portal="#b080ff", leaf="#5a2a8a"),
}


def P(pal, k):
    return hexc(pal[k])


def draw_tile(name, world, rnd):
    pal = PAL[world]
    c = Canvas(T, T)
    g = P(pal, "ground")
    if name == "outside":
        return c
    if name.startswith("ground"):
        i = int(name[-1])
        noise_fill(c, 0, 0, T, T, g, rnd, 0.05)
        for _ in range(2 + i):
            c.rect(rnd.randrange(T), rnd.randrange(T), 2, 1, P(pal, "ground2"))
        # little details per world
        for _ in range(3 + i):
            x, y = rnd.randrange(T), rnd.randrange(T)
            if world == "fire":
                c.px(x, y, P(pal, "flower") if rnd.random() < 0.15 else shade(g, -0.25))
            elif world == "water":
                c.px(x, y, shade(g, 0.25) if rnd.random() < 0.6 else hexc("#f0e8d0"))
            elif world == "void":
                c.px(x, y, hexc("#d0c0ff") if rnd.random() < 0.08 else shade(g, 0.12))
            elif world == "spirit":
                c.px(x, y, hexc("#ffffff"))
            else:
                c.px(x, y, shade(g, -0.2))
        if i == 3 and world in ("wind", "stone", "nexus"):
            c.rect(rnd.randrange(3, 10), rnd.randrange(3, 10), 3, 2, shade(g, -0.18))
        return c
    if name.startswith("path"):
        p = P(pal, "path")
        noise_fill(c, 0, 0, T, T, p, rnd, 0.05)
        if world in ("spirit", "nexus", "wind"):
            # cobbles
            for yy in range(0, T, 4):
                off = 2 if (yy // 4) % 2 else 0
                for xx in range(-off, T, 5):
                    c.rect(xx, yy, 1, 4, shade(p, -0.18))
                c.rect(0, yy, T, 1, shade(p, -0.14))
        elif world == "water":
            for yy in range(0, T, 4):
                c.rect(0, yy, T, 1, shade(p, -0.3))
                c.px(rnd.randrange(T), yy + 2, shade(p, -0.25))
        else:
            for _ in range(6):
                c.px(rnd.randrange(T), rnd.randrange(T), shade(p, rnd.choice((-0.2, 0.15))))
        return c
    if name.startswith("grass") or name.startswith("flower"):
        noise_fill(c, 0, 0, T, T, g, rnd, 0.05)
        gr = P(pal, "grass")
        for _ in range(9):
            x, y = rnd.randrange(1, T - 1), rnd.randrange(3, T)
            c.px(x, y, gr)
            c.px(x, y - 1, shade(gr, 0.15))
            if rnd.random() < 0.5:
                c.px(x + 1, y - 2, shade(gr, 0.25))
        if name.startswith("flower"):
            fl = P(pal, "flower")
            for _ in range(3 + int(name[-1])):
                x, y = rnd.randrange(2, T - 2), rnd.randrange(2, T - 2)
                c.px(x, y, fl)
                c.px(x - 1, y, shade(fl, -0.2))
                c.px(x + 1, y, shade(fl, -0.2))
                c.px(x, y - 1, shade(fl, 0.3))
                c.px(x, y + 1, shade(gr, -0.2))
        return c
    if name.startswith("tree"):
        i = int(name[-1])
        noise_fill(c, 0, 0, T, T, g, rnd, 0.05)
        tr, leaf = P(pal, "trunk"), P(pal, "tree")
        c.ellipse(8, 14.5, 5, 1.5, shade(g, -0.35))
        if world == "water":  # palm
            c.line(8, 15, 8 + (1 if i else -1), 6, tr, 2)
            for a in range(6):
                ang = a / 6 * math.tau + 0.3
                c.line(8, 5, 8 + math.cos(ang) * 6, 5 + math.sin(ang) * 3 + 2, hexc(pal["leaf"]), 2)
            c.px(8, 6, hexc("#6a4a2a"))
            c.px(7, 6, hexc("#6a4a2a"))
        elif world == "fire":  # charred tree with embers
            c.line(8, 15, 8, 5, tr, 2)
            c.line(8, 9, 4, 5, tr, 1)
            c.line(8, 8, 12, 4, tr, 1)
            c.line(8, 6, 6, 2, tr, 1)
            for _ in range(5):
                c.px(rnd.randrange(3, 13), rnd.randrange(1, 9), hexc(pal["leaf"]) if rnd.random() < 0.6 else hexc("#ffb040"))
        elif world == "void":  # bare black tree, violet glints
            c.line(8, 15, 8, 4, tr, 2)
            c.line(8, 10, 3, 6, tr, 1)
            c.line(8, 8, 13, 5, tr, 1)
            c.line(8, 5, 10, 1, tr, 1)
            c.line(5, 7, 4, 3, tr, 1)
            for _ in range(3):
                c.px(rnd.randrange(3, 13), rnd.randrange(1, 8), hexc("#b070ff"))
        elif world == "spirit":  # white birch with glowing leaves
            c.rect(7, 8, 2, 7, hexc("#f0ece0"))
            c.px(7, 10, hexc("#404040"))
            c.px(8, 13, hexc("#404040"))
            c.ellipse(8, 5.5, 6, 5, hexc("#e0e8ff"))
            c.ellipse(7, 4.5, 4, 3, hexc("#ffffff"))
            for _ in range(4):
                c.px(rnd.randrange(3, 13), rnd.randrange(1, 10), hexc("#fff0a0"))
        elif world == "stone":  # pine
            c.rect(7, 12, 2, 3, tr)
            for k, (y0, r) in enumerate([(3, 3), (6, 4.5), (9, 6)]):
                c.poly([(8, y0 - 2), (8 - r, y0 + 3), (8 + r, y0 + 3)], shade(leaf, 0.1 * (2 - k)))
        else:  # round leafy tree (wind, nexus)
            c.rect(7, 10, 2, 5, tr)
            c.ellipse(8, 6.5, 6.5 - i * 0.5, 5.5, leaf)
            c.ellipse(6.5, 5, 3.5, 2.5, shade(leaf, 0.2))
            c.ellipse(10, 9, 3, 2, shade(leaf, -0.2))
            if world == "wind":
                c.px(12, 4, hexc("#ffffff"))
        c.outline()
        return c
    if name.startswith("rock"):
        noise_fill(c, 0, 0, T, T, g, rnd, 0.05)
        r = P(pal, "rock")
        c.ellipse(8, 14.5, 6, 1.5, shade(g, -0.35))
        if world == "void":  # floating shard
            c.poly([(8, 2), (13, 8), (8, 12), (4, 7)], r)
            c.poly([(8, 2), (8, 12), (4, 7)], shade(r, 0.2))
            c.px(8, 6, hexc("#d0c0ff"))
            c.ellipse(8, 14.5, 3, 1, shade(g, -0.4))
        else:
            c.ellipse(8, 9.5, 6.5, 5.5 - int(name[-1]), r)
            c.ellipse(6.5, 7.5, 3, 2, shade(r, 0.22))
            c.ellipse(10, 12, 3, 1.5, shade(r, -0.2))
            if world == "stone":
                c.px(10, 8, hexc("#d0a040"))
            if world == "spirit":
                c.px(6, 7, hexc("#ffffff"))
        c.outline()
        return c
    if name.startswith("liquid"):
        f = int(name[-1])
        edge = "edge" in name
        lq, hi = P(pal, "liquid"), P(pal, "liquid_hi")
        noise_fill(c, 0, 0, T, T, lq, rnd, 0.03)
        if world == "fire":  # lava: bright crust cracks that churn
            for _ in range(5):
                x, y = (rnd.randrange(T) + f * 3) % T, rnd.randrange(T)
                c.ellipse(x, y, 2, 1, shade(lq, -0.25))
            for x in range(T):
                y = int(8 + math.sin((x + f * 5) / 2.2) * 3)
                c.px(x, y, hi)
        elif world == "void":  # starfield
            r2 = random.Random(77)
            for _ in range(7):
                x, y = r2.randrange(T), r2.randrange(T)
                tw = (x + y + f) % 3
                c.px(x, y, hexc("#ffffff") if tw == 0 else hexc("#8070c0"))
        elif world == "spirit":  # liquid light
            for x in range(T):
                y = int(8 + math.sin((x + f * 5) / 2.5) * 2)
                c.px(x, y, hi)
                c.px(x, (y + 6) % T, shade(lq, 0.3))
        else:  # water waves
            for k in range(3):
                y0 = 3 + k * 5
                for x in range(T):
                    if (x + f * 2 + k * 3) % 8 < 3:
                        c.px(x, y0 + (1 if (x + f) % 8 < 1 else 0), hi if world != "stone" else shade(lq, 0.25))
        if edge:
            # shoreline foam / crust along the top
            for x in range(T):
                c.px(x, 0, hi if world != "void" else hexc("#6050a0"))
                if (x + f) % 3 == 0:
                    c.px(x, 1, hi if world != "void" else hexc("#6050a0"))
            c.rect(0, 0, T, 1, shade(g, -0.2) if world not in ("void",) else hexc("#1a1428"))
        return c
    if name == "bridge":
        noise_fill(c, 0, 0, T, T, P(pal, "liquid"), rnd, 0.03)
        b = P(pal, "bridge")
        c.rect(0, 1, T, 14, b)
        for x in range(0, T, 4):
            c.rect(x, 1, 1, 14, shade(b, -0.3))
        c.rect(0, 1, T, 1, shade(b, 0.25))
        c.rect(0, 14, T, 1, shade(b, -0.4))
        return c
    if name == "wall_top":
        w = P(pal, "wall")
        noise_fill(c, 0, 0, T, T, shade(w, -0.25), rnd, 0.04)
        for _ in range(4):
            c.px(rnd.randrange(T), rnd.randrange(T), shade(w, -0.1))
        return c
    if name.startswith("wall_face"):
        w = P(pal, "wall")
        noise_fill(c, 0, 0, T, T, w, rnd, 0.05)
        # bricks
        for yy in range(0, T, 4):
            c.rect(0, yy, T, 1, shade(w, -0.25))
            off = 0 if (yy // 4) % 2 == 0 else 4
            for xx in range(off, T, 8):
                c.rect(xx, yy, 1, 4, shade(w, -0.25))
        c.rect(0, 0, T, 2, shade(w, 0.18))
        c.rect(0, T - 1, T, 1, shade(w, -0.45))
        if name.endswith("1"):
            if world == "stone":
                c.line(3, 6, 9, 9, P(pal, "crystal"))
                c.line(9, 9, 12, 7, P(pal, "crystal"))
            elif world == "water":
                c.ellipse(4, 12, 2, 1.5, hexc("#e0d0c0"))
                c.ellipse(11, 10, 1.5, 1, hexc("#e0d0c0"))
            elif world == "fire":
                c.line(4, 6, 6, 12, hexc("#ff6a1a"))
            elif world == "spirit":
                c.rect(2, 7, 12, 1, P(pal, "trim"))
            elif world == "void":
                c.px(5, 8, hexc("#b080ff"))
                c.px(11, 6, hexc("#b080ff"))
            else:
                c.rect(6, 6, 4, 4, shade(w, -0.15))
        return c
    if name.startswith("floor"):
        fl = P(pal, "floor")
        noise_fill(c, 0, 0, T, T, fl, rnd, 0.04)
        i = int(name[-1])
        if world in ("spirit", "wind", "nexus"):
            c.rect(0, 0, T, 1, shade(fl, -0.15))
            c.rect(0, 0, 1, T, shade(fl, -0.15))
            if i == 2:
                c.rect(5, 5, 6, 6, shade(fl, 0.15))
                c.rect(7, 7, 2, 2, P(pal, "trim"))
        elif world == "void":
            if i == 0:
                c.rect(0, 0, 8, 8, shade(fl, -0.12))
                c.rect(8, 8, 8, 8, shade(fl, -0.12))
            if i == 2:
                c.px(rnd.randrange(T), rnd.randrange(T), hexc("#b080ff"))
        else:
            for _ in range(2 + i):
                x0, y0 = rnd.randrange(T), rnd.randrange(T)
                c.line(x0, y0, x0 + rnd.randrange(-4, 5), y0 + rnd.randrange(-3, 4),
                       hexc("#ff7a30") if world == "fire" and i == 2 else shade(fl, -0.25))
        return c
    if name.startswith("roof"):
        r = P(pal, "roof")
        noise_fill(c, 0, 0, T, T, r, rnd, 0.03)
        for yy in range(1, T, 4):
            c.rect(0, yy, T, 1, shade(r, -0.25))
            off = 0 if (yy // 4) % 2 == 0 else 3
            for xx in range(off, T, 6):
                c.px(xx, yy + 1, shade(r, 0.2))
                c.px(xx, yy + 2, shade(r, 0.1))
        if name == "roof_top":
            c.rect(0, 0, T, 3, shade(r, 0.3))
            c.rect(0, 3, T, 1, shade(r, -0.35))
        if name == "roof_bot":
            c.rect(0, T - 3, T, 3, shade(r, -0.45))
            c.rect(0, T - 3, T, 1, shade(r, 0.1))
        return c
    if name in ("hwall", "window", "door"):
        hw = P(pal, "hwall")
        noise_fill(c, 0, 0, T, T, hw, rnd, 0.04)
        if world in ("stone", "wind", "fire"):
            # timber frame / bricks
            c.rect(0, 0, 2, T, shade(hw, -0.35))
            c.rect(0, 7, T, 1, shade(hw, -0.2))
        c.rect(0, T - 2, T, 2, shade(hw, -0.4))
        if name == "window":
            lt = P(pal, "light")
            c.rect(4, 3, 8, 8, shade(hw, -0.5))
            c.rect(5, 4, 6, 6, lt)
            c.rect(7, 4, 1, 6, shade(hw, -0.4))
            c.rect(5, 6, 6, 1, shade(hw, -0.4))
            c.px(5, 4, (255, 255, 255, 255))
        if name == "door":
            d = shade(P(pal, "trunk"), 0.25) if world != "spirit" else hexc("#c0a060")
            c.rect(4, 2, 8, 14, shade(d, -0.4))
            c.rect(5, 3, 6, 13, d)
            c.rect(5, 3, 6, 1, shade(d, 0.3))
            c.px(9, 9, P(pal, "trim"))
            c.rect(8, 3, 1, 13, shade(d, -0.25))
        return c
    if name == "awning":
        a1, a2 = P(pal, "accent"), P(pal, "awning2")
        for x in range(T):
            col = a1 if (x // 4) % 2 == 0 else a2
            c.rect(x, 0, 1, 12, col)
            c.px(x, 12 if (x % 4) in (1, 2) else 11, col)
        c.rect(0, 0, T, 1, shade(a1, 0.3))
        c.rect(0, 10, T, 1, shade(a1, -0.3))
        return c
    if name == "counter":
        noise_fill(c, 0, 0, T, T, g, rnd, 0.05)
        wd = shade(P(pal, "trunk"), 0.35) if world != "spirit" else hexc("#d8c8a0")
        c.rect(0, 2, T, 12, wd)
        c.rect(0, 2, T, 3, shade(wd, 0.3))
        c.rect(0, 13, T, 1, shade(wd, -0.5))
        for x in range(2, T, 5):
            c.rect(x, 6, 1, 7, shade(wd, -0.2))
        # goods on the counter
        c.rect(3, 0, 3, 3, P(pal, "accent"))
        c.ellipse(11, 1.5, 2, 1.5, P(pal, "trim"))
        return c
    if name == "keeper_floor":
        noise_fill(c, 0, 0, T, T, shade(g, -0.2), rnd, 0.04)
        return c
    if name == "fence":
        noise_fill(c, 0, 0, T, T, g, rnd, 0.05)
        f = shade(P(pal, "trunk"), 0.4) if world not in ("spirit", "void") else P(pal, "hwall")
        c.rect(0, 6, T, 2, f)
        c.rect(0, 11, T, 2, f)
        for x in (2, 8, 14):
            c.rect(x - 1, 3, 2, 12, f)
            c.px(x - 1, 3, shade(f, 0.3))
        c.outline()
        return c
    if name.startswith("lamp"):
        noise_fill(c, 0, 0, T, T, g, rnd, 0.05)
        c.ellipse(8, 15, 3, 1, shade(g, -0.35))
        post = hexc("#2a2a32")
        c.rect(7, 5, 2, 10, post)
        c.rect(5, 2, 6, 4, post)
        lt = P(pal, "light")
        c.rect(6, 3, 4, 2, lt if name == "lamp0" else shade(lt, -0.15))
        c.outline()
        return c
    if name == "bench":
        noise_fill(c, 0, 0, T, T, g, rnd, 0.05)
        wd = shade(P(pal, "trunk"), 0.4)
        c.rect(1, 7, 14, 3, wd)
        c.rect(1, 7, 14, 1, shade(wd, 0.3))
        c.rect(2, 10, 2, 4, shade(wd, -0.3))
        c.rect(12, 10, 2, 4, shade(wd, -0.3))
        c.outline()
        return c
    if name.startswith("feat_"):
        return None  # drawn as a 2x2 block below
    if name in ("landmark_top", "landmark_bot"):
        return None  # drawn as a 1x2 block below
    if name == "pillar":
        fl = P(pal, "floor")
        noise_fill(c, 0, 0, T, T, fl, rnd, 0.04)
        pw = shade(P(pal, "wall"), 0.35)
        c.ellipse(8, 14, 6, 2, shade(fl, -0.35))
        c.rect(4, 1, 8, 13, pw)
        c.rect(4, 1, 2, 13, shade(pw, 0.25))
        c.rect(10, 1, 2, 13, shade(pw, -0.3))
        c.rect(3, 0, 10, 2, shade(pw, 0.15))
        c.rect(3, 12, 10, 2, shade(pw, -0.1))
        if world in ("spirit", "wind"):
            c.rect(4, 6, 8, 1, P(pal, "trim"))
        c.outline()
        return c
    if name.startswith("torch"):
        f = int(name[-1])
        c = draw_tile("wall_face0", world, random.Random(5))
        c.rect(7, 8, 2, 6, hexc("#3a2a1a"))
        fl = [hexc("#ffe060"), hexc("#ff8a20"), hexc("#ff4a10")]
        if world == "void":
            fl = [hexc("#e0c0ff"), hexc("#a060ff"), hexc("#6030c0")]
        if world == "spirit":
            fl = [hexc("#ffffff"), hexc("#fff0a0"), hexc("#e0c050")]
        h = 4 + (f % 2)
        c.ellipse(8, 7 - f * 0.3, 2.5, h / 2 + 1, fl[2])
        c.ellipse(8, 7.5 - f * 0.3, 1.6, h / 2, fl[1])
        c.ellipse(8, 8, 0.9, 1.4, fl[0])
        return c
    if name == "bones":
        fl = P(pal, "floor")
        noise_fill(c, 0, 0, T, T, fl, rnd, 0.04)
        b = hexc("#e0d8c0") if world not in ("void",) else hexc("#8070a0")
        if world in ("water",):
            c.ellipse(5, 9, 2.5, 1.5, hexc("#f0e0d0"))
            c.ellipse(11, 6, 1.5, 1, hexc("#ff9a8a"))
        elif world in ("stone", "wind", "spirit", "nexus"):
            for _ in range(4):
                c.ellipse(rnd.randrange(3, 13), rnd.randrange(4, 13), 1.5, 1, shade(fl, -0.3))
        else:
            c.line(3, 10, 9, 8, b)
            c.ellipse(11, 9, 2, 1.7, b)
            c.px(10, 9, shade(fl, -0.5))
        return c
    if name.startswith("crystal"):
        fl = P(pal, "floor")
        noise_fill(c, 0, 0, T, T, fl, rnd, 0.04)
        cr = P(pal, "crystal")
        c.ellipse(8, 14, 5, 1.5, shade(fl, -0.3))
        c.poly([(8, 1), (11, 7), (9, 14), (6, 13), (5, 6)], cr)
        c.poly([(8, 1), (8, 14), (6, 13), (5, 6)], shade(cr, 0.3))
        c.poly([(12, 7), (14, 10), (12, 14), (10, 12)], shade(cr, -0.15))
        if name.endswith("1"):
            c.px(7, 4, (255, 255, 255, 255))
            c.px(6, 5, (255, 255, 255, 255))
            c.px(12, 9, (255, 255, 255, 255))
        c.outline()
        return c
    if name == "statue":
        fl = P(pal, "floor")
        noise_fill(c, 0, 0, T, T, fl, rnd, 0.04)
        s = shade(P(pal, "rock"), 0.15)
        c.rect(3, 12, 10, 3, shade(s, -0.2))
        c.rect(6, 5, 4, 7, s)
        c.ellipse(8, 3.5, 2.5, 2.5, s)
        c.rect(4, 6, 2, 4, shade(s, -0.1))
        c.rect(10, 6, 2, 4, shade(s, -0.1))
        c.outline()
        return c
    if name.startswith("portal"):
        f = int(name[-1])
        noise_fill(c, 0, 0, T, T, P(pal, "path"), rnd, 0.04)
        c.ellipse(8, 9, 7, 5.5, hexc("#1a1a2a"))
        for k in range(3):
            a0 = f * math.pi / 2 + k * math.tau / 3
            for t in range(10):
                a = a0 + t * 0.25
                r = 5.5 - t * 0.45
                c.px(round(8 + math.cos(a) * r), round(9 + math.sin(a) * r * 0.75), (255, 255, 255, 255 - t * 18))
        c.ellipse(8, 9, 1.5, 1.2, (255, 255, 255, 255))
        return c
    if name == "cave_mouth":
        noise_fill(c, 0, 0, T, T, g, rnd, 0.05)
        r = P(pal, "rock")
        c.ellipse(8, 9, 8, 7, shade(r, -0.1))
        c.ellipse(8, 11, 5.5, 5.5, hexc("#0a0810"))
        c.rect(3, 11, 11, 5, hexc("#0a0810"))
        c.ellipse(6, 5, 3, 2, shade(r, 0.2))
        return c
    if name == "stairs":
        fl = P(pal, "floor")
        noise_fill(c, 0, 0, T, T, fl, rnd, 0.04)
        for k in range(4):
            col = shade(fl, -0.15 * k - 0.1)
            c.rect(1, k * 4, 14, 4, col)
            c.rect(1, k * 4, 14, 1, shade(col, 0.25))
        return c
    raise ValueError(name)


def draw_feature(world, frame):
    """2x2 plaza feature (32x32)."""
    pal = PAL[world]
    rnd = random.Random(11)
    c = Canvas(32, 32)
    noise_fill(c, 0, 0, 32, 32, P(pal, "path"), rnd, 0.04)
    if world == "fire":  # brazier pit
        c.ellipse(16, 20, 13, 9, hexc("#3a3a40"))
        c.ellipse(16, 19, 11, 7, hexc("#1a1010"))
        fl = [hexc("#ff4a10"), hexc("#ff8a20"), hexc("#ffe060")]
        for k in range(7):
            x = 8 + k * 2.5
            h = 8 + ((k * 3 + frame * 5) % 6)
            c.ellipse(x, 18 - h / 2, 2.5, h / 2, fl[k % 2])
        c.ellipse(16, 16, 4, 5, fl[2])
    elif world == "water":  # fountain
        c.ellipse(16, 22, 14, 8, hexc("#c0c0b8"))
        c.ellipse(16, 21, 12, 6, hexc("#3a7ad0"))
        c.rect(14, 8, 4, 13, hexc("#d0d0c8"))
        c.ellipse(16, 8, 5, 2.5, hexc("#d0d0c8"))
        for k in range(5):
            y = 4 + ((k * 2 + frame * 3) % 8)
            c.px(12 + k * 2, y, hexc("#a8e0ff"))
            c.px(12 + k * 2, y + 1, hexc("#ffffff"))
        for x in range(6, 27, 3):
            c.px(x, 21 + (x + frame) % 2, hexc("#a8e0ff"))
    elif world == "wind":  # windmill
        c.rect(13, 12, 6, 18, hexc("#c09a6a"))
        c.rect(13, 12, 2, 18, hexc("#d8b484"))
        c.rect(15, 24, 2, 6, hexc("#6a4a2a"))
        cx, cy = 16, 11
        for k in range(4):
            a = k * math.pi / 2 + frame * math.pi / 4
            ex, ey = cx + math.cos(a) * 11, cy + math.sin(a) * 11
            c.line(cx, cy, ex, ey, hexc("#f0f0f0"), 2)
        c.ellipse(cx, cy, 2, 2, hexc("#6a4a2a"))
    elif world == "stone":  # miner statue on plinth
        c.rect(6, 22, 20, 8, hexc("#7a7a72"))
        c.rect(6, 22, 20, 2, hexc("#9a9a92"))
        s = hexc("#8a8a82")
        c.rect(12, 8, 8, 14, s)
        c.ellipse(16, 6, 3.5, 3.5, s)
        c.rect(11, 3, 10, 2, hexc("#d0a040"))
        c.line(20, 10, 27, 4, hexc("#6a5a3a"), 2)
        c.line(25, 2, 29, 7, s, 2)
        if frame:
            c.px(14, 5, hexc("#ffd070"))
    elif world == "spirit":  # shrine with a lantern
        c.rect(5, 24, 22, 6, hexc("#e8e0d0"))
        c.rect(8, 10, 16, 14, hexc("#f4f0e8"))
        c.poly([(4, 11), (16, 2), (28, 11)], hexc("#e0c050"))
        c.rect(12, 14, 8, 8, hexc("#3a3040"))
        lt = hexc("#fffbe0") if frame == 0 else hexc("#fff0a0")
        c.ellipse(16, 18, 3, 3.5, lt)
    elif world == "void":  # floating rock with a lamp
        dy = frame
        c.ellipse(16, 28, 8, 2, hexc("#120e1a"))
        c.poly([(6, 12 + dy), (26, 12 + dy), (20, 24 + dy), (12, 24 + dy)], hexc("#3a3050"))
        c.poly([(6, 12 + dy), (16, 12 + dy), (12, 24 + dy)], hexc("#4a4060"))
        c.rect(15, 2 + dy, 2, 10, hexc("#1a1a22"))
        c.ellipse(16, 3 + dy, 3, 2.5, hexc("#c090ff"))
    else:  # nexus: central beacon flame
        c.ellipse(16, 22, 12, 7, hexc("#2a2a3a"))
        fl = [hexc("#a08aff"), hexc("#c0a0ff"), hexc("#ffffff")]
        for k in range(5):
            x = 9 + k * 3.5
            h = 10 + ((k * 4 + frame * 5) % 7)
            c.ellipse(x, 20 - h / 2, 2.6, h / 2, fl[k % 2])
        c.ellipse(16, 15, 3, 5, fl[2])
    c.outline()
    return c


def draw_landmark(world):
    """1x2 landmark (16x32)."""
    pal = PAL[world]
    rnd = random.Random(21)
    c = Canvas(16, 32)
    noise_fill(c, 0, 16, 16, 16, P(pal, "ground"), rnd, 0.05)
    c.ellipse(8, 30, 7, 2, shade(P(pal, "ground"), -0.35))
    if world == "fire":  # cracked obelisk
        o = hexc("#3a3040")
        c.poly([(5, 30), (11, 30), (10, 6), (8, 2), (6, 6)], o)
        c.poly([(5, 30), (8, 30), (8, 2), (6, 6)], shade(o, 0.2))
        c.line(9, 8, 7, 14, hexc("#ff6a1a"))
        c.line(7, 14, 9, 20, hexc("#ff6a1a"))
        c.line(9, 20, 8, 26, hexc("#ffb040"))
    elif world == "water":  # whale ribs
        b = hexc("#f0ece0")
        for k, x in enumerate((3, 8, 13)):
            c.line(x, 30, x + (2 if x < 8 else -2 if x > 8 else 0), 8 + abs(x - 8), b, 2)
        c.line(2, 30, 14, 30, shade(b, -0.2), 1)
        c.line(4, 9, 12, 9, shade(b, -0.1))
    elif world == "wind":  # lone windmill
        c.rect(6, 12, 4, 18, hexc("#e0d0b0"))
        c.rect(6, 12, 1, 18, hexc("#f0e8d0"))
        c.rect(7, 26, 2, 4, hexc("#6a4a2a"))
        for a in (0.3, 0.3 + math.pi / 2, 0.3 + math.pi, 0.3 + 3 * math.pi / 2):
            c.line(8, 10, 8 + math.cos(a) * 7, 10 + math.sin(a) * 7, hexc("#ffffff"), 2)
        c.ellipse(8, 10, 1.5, 1.5, hexc("#6a4a2a"))
    elif world == "stone":  # split geode
        c.ellipse(8, 22, 7.5, 8, hexc("#6a6a62"))
        c.ellipse(8, 22, 5, 6, hexc("#8a4ac0"))
        c.ellipse(8, 22, 3, 4, hexc("#c090ff"))
        c.line(8, 14, 8, 30, hexc("#3a3a32"))
        c.px(6, 20, hexc("#ffffff"))
        c.px(10, 24, hexc("#ffffff"))
    elif world == "spirit":  # weeping angel facing east
        s = hexc("#e8e8f0")
        c.rect(4, 26, 9, 4, hexc("#c0c0d0"))
        c.poly([(5, 26), (11, 26), (10, 12), (6, 12)], s)
        c.ellipse(9, 9, 3, 3, s)
        c.poly([(5, 14), (1, 6), (3, 20)], hexc("#ffffff"))   # wing behind (west)
        c.px(11, 9, hexc("#404060"))
        c.line(11, 11, 12, 16, hexc("#a0e8ff"))               # tear on the east side
    elif world == "void":  # a door standing alone, facing south
        f = hexc("#2a2236")
        c.rect(3, 6, 10, 24, hexc("#4a3a5a"))
        c.rect(4, 7, 8, 23, hexc("#6a4a8a"))
        c.rect(5, 8, 6, 21, hexc("#100c18"))
        c.px(10, 19, hexc("#d0b0ff"))
        c.rect(3, 6, 10, 1, hexc("#8a6aaa"))
    else:
        c.rect(6, 10, 4, 20, hexc("#8a8aa0"))
    c.outline()
    return c


def build(world, out_dir):
    rnd = random.Random(hash(world) & 0xFFFF)
    tiles = []
    for n in TILE_NAMES:
        r = random.Random(INDEX[n] * 31 + len(world))
        t = AT2.draw_new(n, world, PAL[world], r) if n in AT2.NEW_TILES else draw_tile(n, world, r)
        tiles.append(t)
    for f in range(2):
        feat = draw_feature(world, f)
        for p, (ox, oy) in zip(("tl", "tr", "bl", "br"), ((0, 0), (16, 0), (0, 16), (16, 16))):
            c = Canvas(16, 16)
            c.a = feat.a[oy:oy + 16, ox:ox + 16].copy()
            tiles[INDEX[f"feat_{p}{f}"]] = c
    import art_kenney as AK
    if AK.available():
        kt = AK.kenney_tiles(world, PAL[world])
        for nm, arr in kt.items():
            c = Canvas(16, 16)
            c.a = arr
            tiles[INDEX[nm]] = c
        outdoor = ["lamp0", "lamp1", "bench", "counter", "awning", "bridge", "landmark_top", "landmark_bot",
                   "cliff_top", "portal0", "portal1", "portal2", "portal3"] + [f"feat_{p}{i}" for i in range(2) for p in ("tl", "tr", "bl", "br")]
        indoor = ["torch0", "torch1", "torch2", "bones", "crystal0", "crystal1", "stairs"]
        g = hexc(PAL[world]["ground"])
        fl = hexc(PAL[world]["floor"])
        for nm in outdoor:
            if nm in kt or nm.startswith("landmark"):
                continue
            tiles[INDEX[nm]].a = AK.swap_background(tiles[INDEX[nm]].a, g, kt["ground0"])
        for nm in indoor:
            if nm in kt:
                continue
            tiles[INDEX[nm]].a = AK.swap_background(tiles[INDEX[nm]].a, fl, kt["floor0"])
    lm = draw_landmark(world)
    top, bot = Canvas(16, 16), Canvas(16, 16)
    top.a = lm.a[0:16].copy()
    bot.a = lm.a[16:32].copy()
    tiles[INDEX["landmark_top"]] = top
    tiles[INDEX["landmark_bot"]] = bot
    if AK.available():
        kt = AK.kenney_tiles(world, PAL[world])
        g = hexc(PAL[world]["ground"])
        for nm in ("landmark_top", "landmark_bot"):
            tiles[INDEX[nm]].a = AK.swap_background(tiles[INDEX[nm]].a, g, kt["ground0"])
    img = sheet(tiles, cols=16)
    save(img, f"{out_dir}/tiles/{world}.png")
    return img


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    for w in PAL:
        build(w, out)
    with open(f"{out}/tiles/index.json", "w") as f:
        json.dump(INDEX, f)
    print(len(TILE_NAMES), "tiles per world")
