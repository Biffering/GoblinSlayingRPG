"""Extra tiles for Six Hearths v2: cliffs, carved stairs, waterfalls, door signs and building interiors.

Appended to each world's tileset after the original tiles."""
import math

from art_common import Canvas, hexc, mix, shade, noise_fill

T = 16

NEW_TILES = (
    ["cliff_top", "cliff_face0", "cliff_face1", "cliff_stairs", "hidden_door", "ledge"]
    + [f"fall{i}" for i in range(3)] + [f"veil{i}" for i in range(3)] + [f"splash{i}" for i in range(3)]
    + ["sign_inn", "sign_tavern", "sign_pawn", "sign_items", "sign_house"]
    + ["iwall_top", "iwall_face0", "iwall_face1", "ifloor0", "ifloor1", "ifloor2", "icounter", "rug",
       "bed_top", "bed_bot", "bookshelf", "table", "stool", "potion_shelf", "barrel", "crate",
       "fireplace0", "fireplace1", "weapon_rack", "armor_stand", "plant", "bottle_shelf", "keg", "mat",
       "stairs_down", "painting", "window_in", "candle0", "candle1"]
)

# interior palettes: wall, floor, wood, cloth, stone accent
IPAL = {
    "nexus":  dict(iwall="#4a4a66", ifloor="#6a5a4a", wood="#7a5a3a", cloth="#6a4a8a", metal="#b0b0c8", plant="#4a8a6a"),
    "fire":   dict(iwall="#5a3428", ifloor="#6a4a34", wood="#6a3a22", cloth="#b0402a", metal="#a8a0a0", plant="#8a6a2a"),
    "water":  dict(iwall="#d8d0b8", ifloor="#8a6a4a", wood="#9a7a52", cloth="#2a7aa8", metal="#c0d8e0", plant="#3a9a5a"),
    "wind":   dict(iwall="#e0d4b0", ifloor="#b08a5a", wood="#a07a48", cloth="#30a898", metal="#d0d0c8", plant="#5ab84a"),
    "stone":  dict(iwall="#6a6258", ifloor="#5a4a3a", wood="#5a422a", cloth="#5a7a3a", metal="#c8a050", plant="#4a7a3a"),
    "spirit": dict(iwall="#ece6f4", ifloor="#c8b490", wood="#c0a070", cloth="#8a8ae0", metal="#f0d870", plant="#a8e0c8"),
    "goblin": dict(iwall="#3a3422", ifloor="#4a3e28", wood="#5a4228", cloth="#6a8a2a", metal="#c0a040", plant="#6a8a2a"),
    "void":   dict(iwall="#2c2638", ifloor="#3a3044", wood="#4a3a52", cloth="#7040c0", metal="#a090c8", plant="#6a3a9a"),
}

OUT = (20, 14, 28, 255)


def _wood_planks(c, base, rnd, vertical=False):
    noise_fill(c, 0, 0, T, T, base, rnd, 0.04)
    for k in range(0, T, 4):
        if vertical:
            c.rect(k, 0, 1, T, shade(base, -0.25))
        else:
            c.rect(0, k, T, 1, shade(base, -0.25))
            off = (k // 4 * 7) % T
            c.rect(off, k, 1, 4, shade(base, -0.2))
    for _ in range(4):
        c.px(rnd.randrange(T), rnd.randrange(T), shade(base, 0.12))


def draw_new(name, world, pal, rnd):
    ip = IPAL[world]
    c = Canvas(T, T)
    P = lambda k: hexc(pal[k])
    I = lambda k: hexc(ip[k])
    g = P("ground")
    rock = P("rock") if world not in ("spirit",) else hexc("#b8b0d0")
    if world == "void":
        rock = hexc("#3a3050")
    cliff = mix(rock, P("wall"), 0.4)

    # ---------------------------------------------------------------- outdoors
    if name == "cliff_top":
        noise_fill(c, 0, 0, T, T, shade(cliff, 0.08), rnd, 0.05)
        top = P("grass") if world not in ("void", "fire") else shade(g, 0.1)
        c.rect(0, 0, T, 4, top)
        for x in range(T):
            c.px(x, 4 + (1 if (x * 7) % 5 == 0 else 0), shade(top, -0.3))
        for _ in range(4):
            x, y = rnd.randrange(T), rnd.randrange(7, T)
            c.line(x, y, x + rnd.randrange(-2, 3), y + 3, shade(cliff, -0.25))
        return c
    if name.startswith("cliff_face") or name == "hidden_door":
        noise_fill(c, 0, 0, T, T, cliff, rnd, 0.06)
        # vertical rock strata
        for x in range(0, T, 5):
            c.line(x + rnd.randrange(2), 0, x + rnd.randrange(2), T, shade(cliff, -0.28))
        for _ in range(5):
            c.px(rnd.randrange(T), rnd.randrange(T), shade(cliff, 0.2))
        c.rect(0, T - 2, T, 2, shade(cliff, -0.45))
        if name == "cliff_face1":
            # moss / ember veins / crystals depending on the world
            accent = {"fire": "#ff6a1a", "stone": "#ffd040", "void": "#b080ff", "spirit": "#ffffff"}.get(world)
            if accent:
                c.line(4, 4, 7, 10, hexc(accent))
                c.line(7, 10, 10, 8, hexc(accent))
            else:
                for _ in range(6):
                    c.px(rnd.randrange(T), rnd.randrange(8), P("grass"))
        if name == "hidden_door":
            # a narrow dark seam: only noticeable if you look closely
            c.rect(6, 4, 4, 12, shade(cliff, -0.42))
            c.rect(7, 5, 2, 11, shade(cliff, -0.6))
            c.px(9, 9, shade(cliff, 0.3))
        return c
    if name == "cliff_stairs":
        noise_fill(c, 0, 0, T, T, shade(cliff, -0.1), rnd, 0.04)
        for k in range(4):
            col = shade(cliff, 0.18 - k * 0.08)
            c.rect(1, k * 4, 14, 3, col)
            c.rect(1, k * 4, 14, 1, shade(col, 0.3))
            c.rect(1, k * 4 + 3, 14, 1, shade(col, -0.4))
        c.rect(0, 0, 1, T, shade(cliff, -0.4))
        c.rect(15, 0, 1, T, shade(cliff, -0.4))
        return c
    if name == "ledge":
        wet = shade(cliff, -0.2)
        noise_fill(c, 0, 0, T, T, wet, rnd, 0.05)
        for _ in range(6):
            c.px(rnd.randrange(T), rnd.randrange(T), shade(P("liquid"), 0.3))
        c.rect(0, 0, T, 1, shade(wet, -0.4))
        return c
    if name.startswith("fall") or name.startswith("veil") or name.startswith("splash"):
        f = int(name[-1])
        lq, hi = P("liquid"), P("liquid_hi")
        if world in ("fire",):
            lq, hi = hexc("#ff7a20"), hexc("#ffe080")
        if name.startswith("fall"):
            for x in range(T):
                for y in range(T):
                    s = ((y + f * 5 + (x * 3) % 7) % 8)
                    col = mix(lq, hi, 0.55 if s < 2 else (0.2 if s < 5 else 0.0))
                    c.px(x, y, col)
            for x in (2, 7, 12):
                c.line(x, (f * 5) % T, x, (f * 5) % T + 4, hi)
            return c
        if name.startswith("veil"):
            # translucent falling water drawn over the ledge (you're behind it)
            for x in range(T):
                for y in range(T):
                    s = ((y + f * 5 + (x * 5) % 9) % 9)
                    a = 120 if s < 3 else 80
                    col = mix(lq, hi, 0.6 if s < 2 else 0.25)
                    c.px(x, y, col[:3] + (a,))
            return c
        # splash foam at the bottom of the fall
        noise_fill(c, 0, 0, T, T, lq, rnd, 0.03)
        for _ in range(14):
            x, y = rnd.randrange(T), rnd.randrange(T)
            c.ellipse((x + f * 3) % T, y, 1.5, 1, hi)
        return c
    if name.startswith("sign_"):
        kind = name[5:]
        board = shade(I("wood"), 0.15)
        c.rect(7, 0, 2, 3, shade(board, -0.5))
        c.rect(1, 3, 14, 11, OUT)
        c.rect(2, 4, 12, 9, board)
        c.rect(2, 4, 12, 1, shade(board, 0.3))
        ink = (40, 26, 20, 255)
        gold = hexc("#ffd060")
        if kind == "inn":      # bed
            c.rect(4, 8, 8, 2, hexc("#f0f0f0"))
            c.rect(4, 7, 3, 2, hexc("#ffffff"))
            c.rect(4, 10, 1, 2, ink)
            c.rect(11, 10, 1, 2, ink)
            c.rect(4, 10, 8, 1, ink)
        elif kind == "tavern":  # mug
            c.rect(5, 6, 5, 6, hexc("#e0a030"))
            c.rect(5, 6, 5, 2, hexc("#ffffff"))
            c.rect(10, 7, 2, 1, ink)
            c.rect(11, 7, 1, 4, ink)
            c.rect(10, 10, 2, 1, ink)
        elif kind == "pawn":    # sword & shield
            c.line(5, 11, 11, 5, hexc("#d8d8e8"))
            c.line(4, 12, 6, 10, ink)
            c.ellipse(10, 9.5, 2.5, 3, hexc("#c04030"))
            c.px(10, 9, gold)
        elif kind == "items":   # potion
            c.rect(7, 5, 2, 2, ink)
            c.ellipse(8, 9.5, 3, 3, hexc("#e04060"))
            c.px(7, 8, hexc("#ffffff"))
        else:                   # house number plate
            c.rect(5, 7, 6, 4, shade(board, -0.3))
        return c

    # ---------------------------------------------------------------- interiors
    iw, fl, wd, cl, mt = I("iwall"), I("ifloor"), I("wood"), I("cloth"), I("metal")
    if name == "iwall_top":
        noise_fill(c, 0, 0, T, T, shade(iw, -0.55), rnd, 0.03)
        c.rect(0, T - 1, T, 1, shade(iw, -0.7))
        return c
    if name.startswith("iwall_face"):
        noise_fill(c, 0, 0, T, T, iw, rnd, 0.03)
        if world in ("fire", "stone", "void"):
            for yy in range(0, T, 4):
                c.rect(0, yy, T, 1, shade(iw, -0.18))
                off = 0 if (yy // 4) % 2 == 0 else 4
                for xx in range(off, T, 8):
                    c.rect(xx, yy, 1, 4, shade(iw, -0.18))
        else:
            # wainscot: plaster above, wood panels below
            c.rect(0, 9, T, 7, shade(wd, 0.1))
            c.rect(0, 9, T, 1, shade(wd, 0.4))
            for xx in range(0, T, 8):
                c.rect(xx + 1, 11, 6, 4, shade(wd, -0.12))
        c.rect(0, 0, T, 1, shade(iw, -0.4))
        c.rect(0, T - 1, T, 1, shade(iw, -0.5))
        if name.endswith("1"):
            c.rect(6, 3, 4, 3, shade(iw, -0.12))  # a patch / plaque
        return c
    if name.startswith("ifloor"):
        i = int(name[-1])
        if world in ("stone", "void"):
            noise_fill(c, 0, 0, T, T, fl, rnd, 0.05)
            c.rect(0, 0, T, 1, shade(fl, -0.25))
            c.rect(0, 0, 1, T, shade(fl, -0.25))
            c.rect(8, 8, 8, 1, shade(fl, -0.2))
            c.rect(8, 8, 1, 8, shade(fl, -0.2))
        else:
            _wood_planks(c, fl, rnd)
        if i == 1:
            c.px(rnd.randrange(T), rnd.randrange(T), shade(fl, -0.4))
        if i == 2:
            c.rect(rnd.randrange(10), rnd.randrange(10), 3, 1, shade(fl, 0.15))
        return c
    if name == "icounter":
        c.rect(0, 2, T, 13, shade(wd, -0.1))
        c.rect(0, 2, T, 4, shade(wd, 0.25))
        c.rect(0, 2, T, 1, shade(wd, 0.45))
        c.rect(0, 14, T, 1, shade(wd, -0.6))
        for x in range(2, T, 5):
            c.rect(x, 7, 1, 7, shade(wd, -0.3))
        return c
    if name == "rug":
        noise_fill(c, 0, 0, T, T, cl, rnd, 0.03)
        for k in range(0, T, 4):
            c.px(k + 2, 2, shade(cl, 0.35))
            c.px(k + 2, 13, shade(cl, 0.35))
        c.rect(5, 5, 6, 6, shade(cl, -0.2))
        c.rect(7, 7, 2, 2, shade(cl, 0.4))
        return c
    if name == "bed_top":
        c.rect(1, 1, 14, 15, OUT)
        c.rect(2, 2, 12, 14, shade(wd, 0.1))
        c.rect(3, 4, 10, 12, hexc("#f4f0e8"))
        c.rect(4, 5, 8, 4, hexc("#ffffff"))
        c.rect(4, 8, 8, 1, hexc("#d8d0c8"))
        c.rect(3, 12, 10, 4, cl)
        c.rect(3, 12, 10, 1, shade(cl, 0.35))
        return c
    if name == "bed_bot":
        c.rect(1, 0, 14, 14, OUT)
        c.rect(2, 0, 12, 12, cl)
        c.rect(2, 0, 1, 12, shade(cl, -0.25))
        c.rect(13, 0, 1, 12, shade(cl, -0.25))
        for x in range(4, 13, 3):
            c.px(x, 5, shade(cl, 0.3))
        c.rect(2, 11, 12, 3, shade(wd, -0.1))
        c.rect(2, 11, 12, 1, shade(wd, 0.3))
        return c
    if name == "bookshelf":
        c.rect(0, 0, T, T, OUT)
        c.rect(1, 1, 14, 14, shade(wd, -0.2))
        books = [hexc("#c04040"), hexc("#3a6ac0"), hexc("#d8a030"), hexc("#3a9a5a"), cl, hexc("#8a5ac0")]
        for row in range(3):
            y0 = 2 + row * 5
            c.rect(1, y0 + 4, 14, 1, shade(wd, 0.2))
            x = 2
            while x < 14:
                w = rnd.choice((1, 2, 2))
                h = rnd.choice((3, 4, 4))
                col = rnd.choice(books)
                c.rect(x, y0 + 4 - h, w, h, col)
                c.px(x, y0 + 4 - h, shade(col, 0.3))
                x += w + (1 if rnd.random() < 0.2 else 0)
        return c
    if name == "table":
        c.rect(1, 3, 14, 9, OUT)
        c.rect(2, 4, 12, 6, shade(wd, 0.2))
        c.rect(2, 4, 12, 1, shade(wd, 0.45))
        c.rect(2, 10, 12, 1, shade(wd, -0.4))
        c.rect(2, 11, 2, 4, shade(wd, -0.3))
        c.rect(12, 11, 2, 4, shade(wd, -0.3))
        # a plate / mug / candle
        c.ellipse(6, 6.5, 2, 1.2, hexc("#f0ece0"))
        c.rect(10, 5, 2, 3, hexc("#e0a030"))
        c.px(10, 5, hexc("#ffffff"))
        return c
    if name == "stool":
        c.ellipse(8, 9, 4, 2.5, OUT)
        c.ellipse(8, 9, 3, 1.6, shade(wd, 0.25))
        c.rect(5, 11, 1, 4, shade(wd, -0.35))
        c.rect(10, 11, 1, 4, shade(wd, -0.35))
        return c
    if name in ("potion_shelf", "bottle_shelf"):
        c.rect(0, 0, T, T, OUT)
        c.rect(1, 1, 14, 14, shade(wd, -0.25))
        cols = [hexc("#e04060"), hexc("#40a0f0"), hexc("#60d070"), hexc("#f0c040"), hexc("#b060f0")]
        if name == "bottle_shelf":
            cols = [hexc("#5a8a3a"), hexc("#7a3a2a"), hexc("#c0a040"), hexc("#3a5a2a")]
        for row in range(2):
            y0 = 7 + row * 7
            c.rect(1, y0, 14, 1, shade(wd, 0.25))
            for k in range(4):
                x = 2 + k * 3 + (row % 2)
                col = cols[(k + row * 2) % len(cols)]
                if name == "potion_shelf":
                    c.ellipse(x + 0.5, y0 - 2, 1.4, 1.6, col)
                    c.px(x, y0 - 4, shade(col, -0.3))
                    c.px(x - 0.5 + 1, y0 - 3, (255, 255, 255, 255))
                else:
                    c.rect(x, y0 - 4, 2, 4, col)
                    c.px(x, y0 - 6, col)
                    c.px(x, y0 - 5, col)
                    c.px(x, y0 - 4, shade(col, 0.4))
        return c
    if name == "barrel":
        c.ellipse(8, 9, 6, 7, OUT)
        c.ellipse(8, 9, 5, 6, shade(wd, 0.05))
        for y in (5, 12):
            c.rect(3, y, 10, 1, mt)
        c.ellipse(8, 4, 4.5, 2, shade(wd, 0.3))
        c.rect(5, 6, 1, 8, shade(wd, -0.25))
        return c
    if name == "crate":
        c.rect(1, 2, 14, 13, OUT)
        c.rect(2, 3, 12, 11, shade(wd, 0.1))
        c.rect(2, 3, 12, 1, shade(wd, 0.4))
        c.line(2, 3, 13, 13, shade(wd, -0.3))
        c.line(13, 3, 2, 13, shade(wd, -0.3))
        c.rect(2, 8, 12, 1, shade(wd, -0.2))
        return c
    if name.startswith("fireplace"):
        f = int(name[-1])
        st = shade(iw, -0.25) if world not in ("fire", "void") else hexc("#4a4048")
        noise_fill(c, 0, 0, T, T, st, rnd, 0.06)
        c.rect(0, 0, T, 2, shade(st, 0.3))
        c.rect(3, 5, 10, 11, hexc("#140c0c"))
        flame = hexc("#ff7a20") if world != "void" else hexc("#a060ff")
        hot = hexc("#ffe070") if world != "void" else hexc("#e0d0ff")
        for k in range(5):
            h = 3 + ((k * 3 + f * 2) % 4)
            c.rect(4 + k * 2, 15 - h, 2, h, flame)
            c.px(4 + k * 2 + (f % 2), 15 - h + 1, hot)
        c.rect(4, 14, 8, 1, hexc("#4a2a1a"))
        return c
    if name == "weapon_rack":
        c.rect(1, 13, 14, 2, OUT)
        c.rect(1, 2, 1, 13, shade(wd, -0.2))
        c.rect(14, 2, 1, 13, shade(wd, -0.2))
        c.rect(1, 4, 14, 1, shade(wd, 0.1))
        c.rect(1, 12, 14, 1, shade(wd, 0.1))
        c.line(4, 1, 4, 12, mt)
        c.line(4, 9, 4, 12, shade(wd, -0.3))
        c.rect(3, 9, 3, 1, hexc("#d0a040"))
        c.line(8, 2, 8, 12, shade(wd, 0.2))
        c.line(7, 2, 9, 2, hexc("#c04030"))
        c.line(11, 2, 13, 11, mt)
        c.line(11, 2, 12, 1, mt)
        return c
    if name == "armor_stand":
        c.rect(7, 12, 2, 3, shade(wd, -0.3))
        c.rect(4, 14, 8, 1, shade(wd, -0.3))
        c.rect(3, 4, 10, 8, OUT)
        c.rect(4, 5, 8, 6, mt)
        c.rect(4, 5, 8, 1, shade(mt, 0.4))
        c.rect(7, 5, 2, 6, shade(mt, -0.2))
        c.ellipse(8, 2.5, 2.5, 2, mt)
        c.px(7, 2, shade(mt, 0.5))
        return c
    if name == "plant":
        pot = hexc("#b0603a")
        c.rect(5, 10, 6, 5, OUT)
        c.rect(6, 10, 4, 4, pot)
        c.rect(6, 10, 4, 1, shade(pot, 0.3))
        pl = I("plant")
        for k in range(7):
            a = -math.pi / 2 + (k - 3) * 0.45
            c.line(8, 10, 8 + math.cos(a) * 5, 9 + math.sin(a) * 7, shade(pl, 0.1 * (k % 2)))
        return c
    if name == "keg":
        c.ellipse(8, 8, 7, 6, OUT)
        c.ellipse(8, 8, 6, 5, shade(wd, 0.1))
        c.ellipse(8, 8, 3, 2.5, shade(wd, 0.35))
        c.ellipse(8, 8, 1.2, 1, mt)
        c.rect(3, 13, 2, 2, shade(wd, -0.4))
        c.rect(11, 13, 2, 2, shade(wd, -0.4))
        return c
    if name == "mat":
        _wood_planks(c, fl, rnd)
        c.rect(2, 4, 12, 10, shade(cl, -0.1))
        c.rect(3, 5, 10, 8, shade(cl, 0.15))
        c.rect(0, 15, T, 1, (10, 8, 14, 255))
        return c
    if name == "stairs_down":
        c.rect(0, 0, T, T, (10, 8, 14, 255))
        for k in range(4):
            col = shade(fl, -0.15 - k * 0.15)
            c.rect(1 + k, 1 + k * 4, 14 - k * 2, 3, col)
            c.rect(1 + k, 1 + k * 4, 14 - k * 2, 1, shade(col, 0.3))
        return c
    if name == "painting":
        c.rect(2, 2, 12, 10, OUT)
        c.rect(3, 3, 10, 8, hexc("#d0a040"))
        sky = mix(P("liquid_hi"), (255, 255, 255, 255), 0.3)
        c.rect(4, 4, 8, 6, sky)
        c.rect(4, 8, 8, 2, P("grass"))
        c.ellipse(9, 6, 2, 1.5, P("accent"))
        return c
    if name == "window_in":
        c.rect(3, 2, 10, 10, OUT)
        sky = mix(P("liquid_hi"), (255, 255, 255, 255), 0.4)
        if world in ("void",):
            sky = hexc("#2a1a4a")
        c.rect(4, 3, 8, 8, sky)
        c.rect(7, 3, 2, 8, shade(wd, 0.1))
        c.rect(4, 6, 8, 1, shade(wd, 0.1))
        c.rect(3, 11, 10, 2, shade(wd, 0.3))
        c.px(5, 4, (255, 255, 255, 255))
        return c
    if name.startswith("candle"):
        f = int(name[-1])
        c.rect(7, 6, 2, 9, shade(mt, -0.3))
        c.rect(5, 14, 6, 1, shade(mt, -0.3))
        c.rect(7, 4, 2, 3, hexc("#f4ecd0"))
        flame = hexc("#ffc040") if world != "void" else hexc("#c090ff")
        c.px(7 + f, 2, flame)
        c.px(8 - f, 3, flame)
        c.px(7, 3, hexc("#ffffff"))
        return c
    raise ValueError(name)
