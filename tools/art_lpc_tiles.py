"""32px LPC tilesets for Goblin Slayer, built from the Source of Tales tile library (CC-BY-SA 3.0 / GPL 3).

Every world gets the same tile names as before (so maps don't change), now 32x32, recolored to the world's palette.
Anything LPC doesn't provide falls back to the old hand-drawn tile doubled. Also writes the autotile terrain
blocks (water/lava, dirt paths) and big tree decals that the map draws with a canopy you can walk behind.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import art_kenney as AK
from art_tiles import PAL, TILE_NAMES, INDEX

SOT = os.environ.get("SOT_DIR", os.path.expanduser("~/lpc_tiles/sourceoftales")) + "/tiles"
T = 32


def img(name):
    return np.array(Image.open(f"{SOT}/{name}.png").convert("RGBA"))


def crop(name, c, r, w=1, h=1):
    return img(name)[r * T:(r + h) * T, c * T:(c + w) * T].copy()


def over(base, top):
    out = base.copy()
    m = top[:, :, 3] > 0
    a = top[:, :, 3:4].astype(float) / 255.0
    out[m, :3] = (top[m, :3] * a[m] + base[m, :3] * (1 - a[m])).astype(np.uint8)
    out[m, 3] = 255
    return out


def rc(a, targets):
    return AK.recolor(a, {k: v for k, v in targets.items() if v})


# per-world look: which terrain is the ground, what the water is, which trees grow
WORLD = {
    "fire":   {"ground": ("dirt2", {"orange": "#8a4a30"}), "liquid": ("lava", {}), "path": ("dirt", {"orange": "#5a3a2a"}),
               "tree": "autumn", "roof": "red", "wall": "#6a3a2a"},
    "water":  {"ground": ("sand", {}), "liquid": ("water", {}), "path": ("dirt", {}), "tree": "palm", "roof": "red", "wall": None},
    "wind":   {"ground": ("grass", {}), "liquid": ("water", {"blue": "#5aa8e0"}), "path": ("dirt", {}), "tree": "round",
               "roof": "red", "wall": None},
    "stone":  {"ground": ("dirt2", {}), "liquid": ("water", {"blue": "#3a6a5a"}), "path": ("dirt", {"orange": "#7a6a56"}),
               "tree": "pine", "roof": "slate", "wall": None},
    "spirit": {"ground": ("grass", {"green": "#d8d4ec"}), "liquid": ("water", {"blue": "#9ad8f0"}), "path": ("dirt", {"orange": "#f0e8d0"}),
               "tree": "blossom", "roof": "slate", "wall": "#c8c0e0"},
    "void":   {"ground": ("grass_night", {"green": "#3a2e4a", "blue": "#3a2e4a"}), "liquid": ("water", {"blue": "#2a1a4a"}),
               "path": ("dirt_night", {"orange": "#4a4058", "grey": "#4a4058"}), "tree": "pine_dark", "roof": "slate", "wall": "#3a3048"},
    "nexus":  {"ground": ("grass_night", {}), "liquid": ("water", {"blue": "#4a3a8a"}), "path": ("cement", {}), "tree": "pine",
               "roof": "slate", "wall": None},
    "goblin": {"ground": ("dirt", {"orange": "#5a5a32"}), "liquid": ("water", {"blue": "#5a7a1a"}), "path": ("dirt2", {"orange": "#6a5a3a"}),
               "tree": "pine_dark", "roof": "slate", "wall": "#4a4228"},
}


def terrain(name, targets):
    return rc(img(name), targets)


def tree_decals(kind):
    """Two tree sprites, each in a 96x160 cell, bottom-centered (trunk on the bottom row)."""
    o = img("outside")
    cells = []
    if kind in ("pine", "pine_dark"):
        a = o[0:160, 14 * T:16 * T]
        b = o[0:160, 14 * T:16 * T][:, ::-1]
    elif kind == "round":
        a = o[2 * T:7 * T, 16 * T:19 * T]
        b = o[6 * T:10 * T, 17 * T:20 * T]
    elif kind == "autumn":
        a = o[10 * T:14 * T, 17 * T:20 * T]
        b = np.array(Image.open(f"{SOT}/whitheredtree1.png").convert("RGBA"))
    elif kind == "palm":
        a = o[9 * T:14 * T, 14 * T:17 * T]
        b = a[:, ::-1]
    else:  # blossom
        cb = img("cherry_blossom_trees")
        a = cb[:, 0:112]
        b = cb[:, 112:224]
    for t in (a, b):
        cell = np.zeros((160, 96, 4), np.uint8)
        h, w = t.shape[:2]
        h, w = min(h, 160), min(w, 96)
        t = t[-h:, :w]
        cell[160 - h:, (96 - w) // 2:(96 - w) // 2 + w] = t
        if kind == "pine_dark":
            cell = rc(cell, {"green": "#3a2a5a"})
        cells.append(cell)
    return np.concatenate(cells, axis=1)


GREENERY = {
    "fire":   (["#4a3a22", "#6a5630", "#8a7240"], ["#e05020", "#f09030", "#ffd060"]),
    "water":  (["#5a7a34", "#7a9a4a", "#a0b860"], ["#f0a0b0", "#ffffff", "#f0d0a0"]),
    "wind":   (["#2a6a22", "#3a8a2a", "#5aa840"], ["#f0d040", "#ffffff", "#8aa8f0"]),
    "stone":  (["#4a5a30", "#5a6a3a", "#7a8a4a"], ["#d0c060", "#e0e0d0", "#c08060"]),
    "spirit": (["#9098b8", "#b0b8d0", "#e0e4f0"], ["#ffffff", "#f0d080", "#c0d8ff"]),
    "void":   (["#3a2c52", "#4a3a6a", "#6a5a8a"], ["#b070f0", "#e0b0ff", "#70e0d0"]),
    "goblin": (["#3a3a1a", "#4a4a22", "#6a6a30"], ["#c0c040", "#a04030", "#e0e0a0"]),
    "nexus":  (["#3a2c52", "#4a3a6a", "#6a5a8a"], ["#b070f0", "#e0b0ff", "#70e0d0"]),
}


def _h(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def greenery(base, world, seed, flowers):
    """Grass tufts (and a few flowers) painted over the world's own ground, LPC-style dark outlines."""
    import random
    rng = random.Random(seed)
    g, fl = GREENERY.get(world, GREENERY["wind"])
    gs = [_h(c) for c in g]
    t = base.copy()
    ink = tuple(int(v * 0.45) for v in gs[0][:3]) + (255,)
    spots = [(rng.randrange(4, 26), rng.randrange(10, 30)) for _ in range(5 if not flowers else 3)]
    for cx, cy in spots:
        for b in range(rng.randint(3, 5)):
            x = cx + b * 2 - 3 + rng.randint(-1, 1)
            h = rng.randint(3, 7)
            lean = rng.choice((-1, 0, 1))
            for k in range(h):
                xx = x + (lean if k > h // 2 else 0)
                yy = cy - k
                if 0 <= xx < 31 and 0 <= yy < 32:
                    t[yy, xx] = gs[min(2, k * 3 // h)]
                    if xx + 1 < 32 and k < h - 1 and t[yy, xx + 1][3] and tuple(t[yy, xx + 1]) not in gs:
                        t[yy, xx + 1] = ink
        if cy + 1 < 32:
            for xx in range(max(0, cx - 3), min(32, cx + 7)):
                t[cy + 1, xx] = ink
    if flowers:
        fs = [_h(c) for c in fl]
        for _ in range(rng.randint(4, 6)):
            x, y = rng.randrange(3, 29), rng.randrange(4, 26)
            c = rng.choice(fs)
            ctr = (255, 230, 120, 255) if c[:3] != (255, 230, 120) else (200, 120, 40, 255)
            t[y + 2:y + 5, x] = gs[1]
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                t[y + dy, x + dx] = c
            t[y, x] = ctr
            t[y + 1, x + 1] = ink
    return t


def planks(world, v):
    """A 32px wooden floor in LPC-style shading (four boards, staggered seams, a knot here and there)."""
    import random
    from art_tiles2 import IPAL
    base = np.array(AK.hexrgb(IPAL.get(world, IPAL["wind"])["ifloor"])) * 255
    if world in ("stone", "void", "goblin"):
        base = base * 1.05
    rnd = random.Random(world + str(v))
    a = np.zeros((T, T, 4), np.uint8)
    for b in range(4):
        tone = 1.0 + rnd.uniform(-0.07, 0.07)
        for y in range(b * 8, b * 8 + 8):
            for x in range(T):
                k = tone * (1.06 if y == b * 8 + 1 else (0.78 if y == b * 8 + 7 else 1.0)) * (1 + rnd.uniform(-0.03, 0.03))
                a[y, x, :3] = np.clip(base * k, 0, 255)
                a[y, x, 3] = 255
        seam = (b * 11 + v * 7) % T
        a[b * 8:b * 8 + 7, seam, :3] = np.clip(base * 0.7, 0, 255)
        if rnd.random() < 0.5:
            kx = rnd.randrange(3, T - 3)
            a[b * 8 + 3:b * 8 + 5, kx:kx + 2, :3] = np.clip(base * 0.75, 0, 255)
    return a


def build(out):
    for world in PAL:
        W = WORLD.get(world, WORLD["wind"])
        old = Image.open(f"{out}/tiles/{world}.png").convert("RGBA")
        cols = 16
        n = len(TILE_NAMES)
        rows = (n + cols - 1) // cols
        sheet = np.zeros((rows * T, cols * T, 4), np.uint8)
        # 1) every old tile, doubled
        oa = np.array(old)
        for i in range(n):
            x, y = (i % cols) * 16, (i // cols) * 16
            t = oa[y:y + 16, x:x + 16]
            if t.shape[0] < 16 or t.shape[1] < 16:
                continue
            t2 = np.repeat(np.repeat(t, 2, axis=0), 2, axis=1)
            sheet[(i // cols) * T:(i // cols + 1) * T, (i % cols) * T:(i % cols + 1) * T] = t2
        gname, gt = W["ground"]
        ground_block = terrain(gname, gt)
        g_center = [ground_block[5 * T:6 * T, c * T:(c + 1) * T] for c in range(3)] + [ground_block[3 * T:4 * T, T:2 * T]]
        new = {}
        for i in range(4):
            new[f"ground{i}"] = g_center[i]
        # grass tufts and flower patches, drawn over this world's ground so they never show as flat squares
        new["grass0"] = greenery(g_center[0], world, 11, False)
        new["grass1"] = greenery(g_center[2], world, 23, False)
        new["flower0"] = greenery(g_center[1], world, 37, True)
        new["flower1"] = greenery(g_center[3], world, 41, True)
        keeper = rc(img("cement")[5 * T:6 * T, 0:T], {})
        new["keeper_floor"] = keeper
        # rocks sit on the ground
        rocks = img("rock")
        new["rock0"] = over(g_center[0], rocks[:, 0:T])
        new["rock1"] = over(g_center[1], rocks[:, T:2 * T])
        # buildings
        if W["roof"] == "red":
            new["roof_top"], new["roof_mid"], new["roof_bot"] = crop("house", 1, 0), crop("house", 1, 1), crop("house", 1, 2)
        else:
            new["roof_top"], new["roof_mid"], new["roof_bot"] = crop("house", 1, 3), crop("house", 1, 4), crop("house", 1, 5)
        wall = crop("house", 4, 5)
        if W["wall"]:
            wall = rc(wall, {"grey": W["wall"], "blue": W["wall"], "purple": W["wall"]})
        new["hwall"] = wall
        new["window"] = over(wall, crop("house", 10, 7))
        new["door"] = over(wall, crop("house", 3, 1))
        new["counter"] = over(g_center[0], crop("cabinets", 3, 9))
        new["icounter"] = crop("cabinets", 3, 9)
        # dungeon pieces
        dw = crop("dungeon", 1, 1)
        if W["wall"]:
            dw = rc(dw, {"red": W["wall"], "orange": W["wall"]})
        new["wall_face0"], new["wall_face1"] = dw, (rc(crop("dungeon", 0, 1), {"red": W["wall"], "orange": W["wall"]}) if W["wall"] else crop("dungeon", 0, 1))
        new["wall_top"] = crop("dungeon", 0, 4)
        ft = {"blue": PAL[world]["floor"], "grey": PAL[world]["floor"], "purple": PAL[world]["floor"]}
        cf = rc(crop("castlefloors", 6, 6), ft)
        new["floor0"], new["floor1"], new["floor2"] = cf, rc(crop("castlefloors", 7, 6), ft), rc(crop("castlefloors", 6, 5), ft)
        # interiors
        new["ifloor0"], new["ifloor1"], new["ifloor2"] = planks(world, 0), planks(world, 1), planks(world, 2)
        new["iwall_face0"] = crop("inside", 1, 1)
        new["iwall_face1"] = crop("inside", 2, 1)
        new["iwall_top"] = crop("dungeon", 0, 4)
        new["bookshelf"] = crop("cabinets", 1, 0)
        new["bottle_shelf"] = crop("cabinets", 3, 0)
        new["barrel"] = crop("barrel", 0, 0)
        new["keg"] = crop("barrel", 1, 0)
        new["fireplace0"] = crop("fireplace", 2, 2)
        new["fireplace1"] = crop("fireplace", 2, 2)
        new["armor_stand"] = crop("cabinets", 3, 3)
        new["stairs"] = crop("stairs", 1, 1) if img("stairs").shape[0] >= 64 else None
        new["bridge"] = crop("bridges", 4, 4)
        new["statue"] = over(g_center[0], crop("foodog_statue", 0, 1))
        new["sign_inn"] = crop("signs", 0, 0)
        new["sign_pawn"] = crop("signs", 1, 0)
        new["sign_items"] = crop("signs", 2, 0)
        for f in range(3):
            t = crop("campfire", f % 3, 0)
            new[f"torch{f}"] = t
        # cliffs and falls
        mt = img("mountains_new")
        face = mt[2 * T:3 * T, 5 * T:6 * T]
        top = mt[1 * T:2 * T, 5 * T:6 * T]
        if W["wall"]:
            face = rc(face, {"orange": W["wall"], "red": W["wall"]})
            top = rc(top, {"orange": W["wall"], "red": W["wall"]})
        new["cliff_face0"] = over(g_center[0], face)
        new["cliff_face1"] = over(g_center[0], face)
        new["cliff_top"] = over(g_center[0], top)
        new["hidden_door"] = over(g_center[0], face)
        new["cave_mouth"] = over(g_center[0], mt[6 * T:7 * T, 1 * T:2 * T])
        wf = img("waterfall")
        for f in range(3):
            new[f"fall{f}"] = rc(np.roll(wf[T:2 * T, T:2 * T], f * 8, axis=0), {"blue": PAL[world]["liquid"]} if world != "water" else {})
        # hand-drawn fallbacks were painted on the old ground/floor: put them on the new LPC ground/floor instead
        def colors_of(name):
            i = INDEX[name]
            t = oa[(i // cols) * 16:(i // cols) * 16 + 16, (i % cols) * 16:(i % cols) * 16 + 16]
            return {tuple(int(v) for v in p[:3]) for p in t.reshape(-1, 4) if p[3] > 0}
        bg_sets = [(colors_of("ground0") | colors_of("ground1") | colors_of("grass0"), new["ground0"]),
                   (colors_of("floor0") | colors_of("floor1") | colors_of("floor2"), new["floor0"]),
                   (colors_of("ifloor0") | colors_of("ifloor1"), new["ifloor0"])]
        for nm in TILE_NAMES:
            if nm in new or nm.startswith(("ground", "floor", "ifloor", "liquid", "fall", "veil", "splash", "iwall", "wall_", "roof", "cliff")):
                continue
            i = INDEX[nm]
            ty, tx = (i // cols) * T, (i % cols) * T
            tile = sheet[ty:ty + T, tx:tx + T]
            for cset, repl in bg_sets:
                if not cset:
                    continue
                cs = np.array(sorted(cset))
                rgb = tile[:, :, :3].reshape(-1, 1, 3).astype(int)
                hit = (np.abs(rgb - cs[None, :, :]).sum(axis=2) <= 6).any(axis=1).reshape(T, T) & (tile[:, :, 3] > 0)
                if hit.mean() > 0.12:
                    tile[hit] = repl[hit]
            sheet[ty:ty + T, tx:tx + T] = tile
        for k, v in new.items():
            if v is None or k not in INDEX:
                continue
            i = INDEX[k]
            v = v[:T, :T]
            if v.shape[:2] != (T, T):
                continue
            sheet[(i // cols) * T:(i // cols + 1) * T, (i % cols) * T:(i % cols + 1) * T] = v
        Image.fromarray(sheet, "RGBA").save(f"{out}/tiles/{world}.png")
        # autotile terrains and tree decals
        lname, lt = W["liquid"]
        Image.fromarray(terrain(lname, lt), "RGBA").save(f"{out}/tiles/{world}_liquid.png")
        Image.fromarray(terrain(lname if lname != "water" else "water_anim", lt), "RGBA").save(f"{out}/tiles/{world}_liquid2.png")
        pname, pt = W["path"]
        Image.fromarray(terrain(pname, pt), "RGBA").save(f"{out}/tiles/{world}_path.png")
        Image.fromarray(tree_decals(W["tree"]), "RGBA").save(f"{out}/tiles/{world}_trees.png")
        print("tiles", world)
    json.dump({"tile": T}, open(f"{out}/tiles/meta.json", "w"))
    ch = img("chests")
    Image.fromarray(ch[0:T, 0:T], "RGBA").save(f"{out}/ui/chest.png")
    Image.fromarray(ch[2 * T:3 * T, 0:T], "RGBA").save(f"{out}/ui/chest_open.png")


if __name__ == "__main__":
    build(sys.argv[1])
