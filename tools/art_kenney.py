"""Builds Goblin Slayer's art from Kenney's Tiny packs (CC0) plus Tiny Creatures by Clint Bellanger (CC0).

Every world uses the same Tiny tiles, recolored to that world's palette, so the six worlds keep their own look.
Anything the packs don't have (cliffs, waterfalls, portals, furniture...) falls back to the hand-drawn tiles.
"""
import colorsys
import os

import numpy as np
from PIL import Image

KENNEY = os.environ.get("KENNEY_DIR", os.path.expanduser("~/kenney"))
PACKS = {
    "town": ("kenney_tiny-town/Tilemap/tilemap_packed.png", 12),
    "dungeon": ("kenney_tiny-dungeon/Tilemap/tilemap_packed.png", 12),
    "farm": ("kenney_tiny-farm/Tilemap/tilemap_packed.png", 12),
    "battle": ("kenney_tiny-battle/Tilemap/tilemap_packed.png", 18),
    "ski": ("kenney_tiny-ski/Tilemap/tilemap_packed.png", 12),
    "creatures": ("tiny-creatures/tiny-creatures/Tilemap/tilemap_packed.png", 10),
}
OUTLINE = (63, 38, 49)
_cache = {}


def available():
    return all(os.path.exists(os.path.join(KENNEY, p)) for p, _ in PACKS.values())


def tile(pack, idx):
    if pack not in _cache:
        path, cols = PACKS[pack]
        _cache[pack] = (np.array(Image.open(os.path.join(KENNEY, path)).convert("RGBA")), cols)
    a, cols = _cache[pack]
    x, y = (idx % cols) * 16, (idx // cols) * 16
    return a[y:y + 16, x:x + 16].copy()


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def family(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if v < 0.32 and s < 0.5:
        return "outline"
    if s < 0.16:
        return "grey"
    hd = h * 360
    if 65 <= hd < 170:
        return "green"
    if 170 <= hd < 260:
        return "blue"
    if 15 <= hd < 52:
        return "orange"
    if 260 <= hd < 330:
        return "purple"
    return "red"


def recolor(a, targets, keep_outline=True):
    """targets: {family: '#rrggbb'}. The family's median shade becomes the target; lighter/darker pixels keep their contrast."""
    if not targets:
        return a
    out = a.copy()
    fam = {}
    for y in range(a.shape[0]):
        for x in range(a.shape[1]):
            if a[y, x, 3] == 0:
                continue
            r, g, b = (a[y, x, :3] / 255.0)
            f = family(r, g, b)
            if f in targets:
                fam.setdefault(f, []).append((y, x, colorsys.rgb_to_hsv(r, g, b)))
    for f, px in fam.items():
        th, ts, tv = colorsys.rgb_to_hsv(*hexrgb(targets[f]))
        vs = sorted(p[2][2] for p in px)
        ss = sorted(p[2][1] for p in px)
        mv, ms = vs[len(vs) // 2], max(0.05, ss[len(ss) // 2])
        for y, x, (h, s, v) in px:
            nv = min(1.0, max(0.0, tv * (v / max(0.05, mv))))
            ns = min(1.0, max(0.0, ts * (s / ms)))
            r, g, b = colorsys.hsv_to_rgb(th, ns, nv)
            out[y, x, :3] = (int(r * 255), int(g * 255), int(b * 255))
    return out


def tint(a, col, amount):
    """Blend every non-outline pixel toward a color (used to make element variants of creatures)."""
    out = a.copy()
    c = np.array([int(v * 255) for v in hexrgb(col)], dtype=float)
    for y in range(a.shape[0]):
        for x in range(a.shape[1]):
            if a[y, x, 3] == 0:
                continue
            p = a[y, x, :3].astype(float)
            if family(*(p / 255.0)) == "outline":
                continue
            lum = (0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2]) / 255.0
            tgt = c * (0.45 + 0.9 * lum)
            out[y, x, :3] = np.clip(p * (1 - amount) + tgt * amount, 0, 255).astype(np.uint8)
    return out


def shift(a, dx):
    return np.roll(a, dx, axis=1)


def flip(a):
    return a[:, ::-1].copy()


def over(base, top):
    out = base.copy()
    m = top[:, :, 3] > 0
    out[m] = top[m]
    return out


# ------------------------------------------------------------------ world tiles

def world_targets(world, pal):
    """Per-world recolor rules for ground, leaves, dirt, stone, roofs and liquids."""
    g = pal["ground"]
    # lift the darker world grounds a little so Tiny tiles keep their cheerful contrast
    light_ground = {"fire": "#7a4a38", "void": "#4a3c5c", "stone": "#8a7c62", "nexus": "#5a6a82", "goblin": "#5a5a32"}.get(world, g)
    leaves = {"fire": None, "spirit": "#f4f0ff", "void": "#5a3a8a", "water": "#4aa85a", "stone": "#4a6a2a",
              "goblin": "#4a6a1a"}.get(world, pal["tree"])
    return {
        "ground": {"green": light_ground},
        "leaves": ({"green": leaves} if leaves else {}),
        "dirt": {"orange": pal["path"]},
        "liquid": {"blue": pal["liquid"]},
        "stone": {"grey": pal["wall"], "blue": pal["wall"]},
        "roof": {"red": pal["roof"], "grey": pal["roof"], "blue": pal["roof"]},
        "wood": {"orange": pal.get("trunk", "#6a4a2a")},
        "floor": {"orange": pal["floor"], "grey": pal["floor"]},
        "hwall": {"orange": pal["hwall"], "grey": pal["hwall"]},
    }


def kenney_tiles(world, pal):
    """name -> 16x16 RGBA array, for every tile the Tiny packs can provide."""
    T = world_targets(world, pal)
    rc = lambda a, *keys: recolor(a, {k: v for key in keys for k, v in T[key].items()})
    out = {}
    grass = rc(tile("town", 0), "ground")
    out["ground0"] = grass
    out["ground1"] = rc(tile("town", 1), "ground")
    out["ground2"] = grass
    out["ground3"] = rc(tile("town", 1), "ground")
    out["grass0"] = rc(tile("town", 1), "ground")
    out["grass1"] = flip(rc(tile("town", 1), "ground"))
    out["flower0"] = rc(tile("town", 2), "ground")
    out["flower1"] = flip(rc(tile("town", 2), "ground"))
    out["path0"] = rc(tile("town", 25), "dirt")
    out["path1"] = flip(rc(tile("town", 25), "dirt"))
    if world == "fire":
        out["tree0"], out["tree1"] = tile("town", 3), tile("town", 15)          # autumn-red trees in the ash
    else:
        out["tree0"] = rc(tile("town", 4), "leaves")
        out["tree1"] = rc(tile("town", 16), "leaves")
    out["rock0"] = rc(tile("farm", 89), "stone") if world in ("void", "spirit", "goblin") else tile("farm", 89)
    out["rock1"] = rc(tile("farm", 77), "stone") if world in ("void", "spirit", "goblin") else tile("farm", 77)
    water = rc(tile("battle", 37), "liquid")
    edge = rc(rc(tile("battle", 19), "liquid"), "ground")
    for f in range(3):
        out[f"liquid{f}"] = shift(water, f * 5)
        e = edge.copy()
        e[7:] = shift(edge, f * 5)[7:]
        out[f"liquid_edge{f}"] = e
    out["fence"] = rc(tile("town", 45), "wood") if world in ("void", "spirit") else tile("town", 45)
    # town buildings
    roof_top, roof_mid = (tile("town", 52), tile("town", 64)) if world in ("fire", "water", "wind", "nexus") else (tile("town", 48), tile("town", 60))
    out["roof_top"] = rc(roof_top, "roof")
    out["roof_mid"] = rc(roof_mid, "roof")
    out["roof_bot"] = rc(roof_mid, "roof")
    stone_house = world in ("stone", "spirit", "void", "goblin")
    out["hwall"] = rc(tile("town", 76 if stone_house else 72), "hwall")
    out["window"] = rc(tile("town", 88 if stone_house else 84), "hwall")
    out["door"] = rc(tile("town", 89 if stone_house else 85), "hwall")
    out["keeper_floor"] = rc(tile("town", 109), "floor")
    out["cave_mouth"] = over(grass, tile("town", 113))
    # dungeons and caves
    out["wall_face0"] = rc(tile("dungeon", 40), "stone")
    out["wall_face1"] = rc(tile("dungeon", 28), "stone")
    dark = "#" + "".join(f"{max(0, int(int(pal['wall'][i:i + 2], 16) * 0.55)):02x}" for i in (1, 3, 5))
    out["wall_top"] = recolor(tile("dungeon", 0), {"red": dark, "orange": dark})
    out["floor0"] = rc(tile("dungeon", 48), "floor")
    out["floor1"] = rc(tile("dungeon", 49), "floor")
    out["floor2"] = rc(tile("dungeon", 42), "floor")
    out["pillar"] = rc(tile("dungeon", 57), "stone")
    out["statue"] = tile("dungeon", 41)
    out["stairs"] = rc(tile("dungeon", 38), "stone")
    # interiors
    out["ifloor0"] = rc(tile("dungeon", 48), "floor")
    out["ifloor1"] = rc(tile("dungeon", 49), "floor")
    out["ifloor2"] = rc(tile("dungeon", 50), "floor")
    out["table"] = tile("dungeon", 72)
    out["stool"] = tile("dungeon", 73)
    out["bookshelf"] = tile("dungeon", 63)
    out["barrel"] = tile("dungeon", 82)
    out["keg"] = tile("farm", 85)
    out["crate"] = tile("farm", 90)
    out["armor_stand"] = tile("dungeon", 74)
    out["plant"] = tile("farm", 83) if world in ("wind", "water", "spirit") else tile("farm", 39)
    out["weapon_rack"] = over(over(np.zeros((16, 16, 4), np.uint8), shift(tile("dungeon", 104), -4)), shift(tile("dungeon", 118), 4))
    return out


# ------------------------------------------------------------------ characters

# Tiny human sprites for townsfolk, grouped by the body type the dialogue data asks for
NPC_POOL = {
    "man": [("dungeon", 85), ("dungeon", 86), ("dungeon", 88), ("dungeon", 98), ("dungeon", 112), ("farm", 108), ("dungeon", 87)],
    "woman": [("dungeon", 99), ("creatures", 67), ("dungeon", 100)],
    "elder": [("dungeon", 100), ("dungeon", 111), ("dungeon", 84), ("creatures", 90)],
    "child": [("ski", 82), ("ski", 70), ("farm", 108)],
    "guard": [("dungeon", 96), ("dungeon", 97), ("creatures", 16)],
    "merchant": [("dungeon", 86), ("farm", 109), ("dungeon", 88)],
    "robe": [("dungeon", 84), ("creatures", 65), ("creatures", 75)],
}


def npc_sprite(lk, seed):
    pool = NPC_POOL.get(lk.get("body", "man"), NPC_POOL["man"])
    if lk.get("hat") == "helm":
        pool = NPC_POOL["guard"]
    pack, idx = pool[seed % len(pool)]
    a = tile(pack, idx)
    # dress them in their own colors so every townsperson looks different
    tg = {}
    out = lk.get("outfit")
    if out:
        tg["blue"] = out
        tg["purple"] = out
        tg["green"] = out
    if lk.get("accent"):
        tg["red"] = lk["accent"]
    return recolor(a, tg)


def sheet_from_sprite(a, fw=20, fh=20):
    """A 3x4 walk sheet (down, left, right, up) from one Tiny sprite: mirrored for facing, a hop for walking."""
    frames = []
    for d in range(4):
        base = flip(a) if d == 1 else a
        for f in range(3):
            fr = np.zeros((fh, fw, 4), np.uint8)
            dy = -1 if f in (1, 2) else 0
            ox, oy = (fw - 16) // 2, fh - 16 - 1 + dy
            src = base
            if f == 2:
                src = flip(base) if d in (0, 3) else base
            fr[oy:oy + 16, ox:ox + 16] = np.where(src[:, :, 3:4] > 0, src, fr[oy:oy + 16, ox:ox + 16])
            frames.append(fr)
    rows = [np.concatenate(frames[r * 3:(r + 1) * 3], axis=1) for r in range(4)]
    return Image.fromarray(np.concatenate(rows, axis=0), "RGBA")


# ------------------------------------------------------------------ enemies

SPECIES_SPRITE = {
    "rat": ("dungeon", 123), "bum": ("dungeon", 111), "loiterer": ("creatures", 19), "undead": ("creatures", 0),
    "knight": ("creatures", 16), "elf": ("creatures", 12), "archer": ("dungeon", 112), "ghost": ("dungeon", 121),
    "bear": ("creatures", 163), "ogre": ("creatures", 14), "boar": ("creatures", 160), "fknight": ("creatures", 97),
    "farcher": ("creatures", 87), "fbum": ("creatures", 9),
    "goblin": ("creatures", 10), "goblin_shaman": ("creatures", 75), "goblin_brute": ("creatures", 11),
    "pirate": ("dungeon", 85), "pirate_gunner": ("dungeon", 88),
}
UNIQUE_SPRITE = {"king_goblin": ("creatures", 96)}
SCALE = {"s": 2, "m": 3, "l": 4, "xl": 4, "boss": 6, "omni": 7}
EL_TINT = {"fire": "#ff6a3a", "water": "#4a9aff", "wind": "#40e0c8", "stone": "#7ac050", "spirit": "#fff4d0", "void": "#a060ff"}


def pirate_gear(a, gunner):
    a = a.copy()
    hat, band, o = (30, 28, 40, 255), (200, 60, 50, 255), (63, 38, 49, 255)
    # a big black tricorn with a red band and a white skull dot
    a[0, 5:11] = o
    a[1, 4:12] = o
    a[1, 5:11] = hat
    a[2, 3:13] = hat
    a[2, 2] = a[2, 13] = o
    a[3, 1:15] = hat
    a[3, 0] = a[3, 15] = o
    a[4, 1:15] = o
    a[3, 4:12] = band
    a[2, 7:9] = (240, 240, 240, 255)
    if not gunner:
        for k in range(5):                      # cutlass
            a[min(15, 8 + k), min(15, 12 + k // 2)] = (220, 224, 236, 255)
    else:
        for k in range(5):                      # musket
            a[9, min(15, 10 + k)] = (110, 80, 60, 255)
        a[8, 15] = (150, 150, 160, 255)
    return a


def enemy_image(spr_id, el, size_key, unique_id=None):
    """Battle sprite: the Tiny creature tinted by element and scaled up with crisp pixels, facing right."""
    pack, idx = UNIQUE_SPRITE.get(unique_id) or SPECIES_SPRITE[spr_id]
    a = tile(pack, idx)
    if spr_id in ("pirate", "pirate_gunner"):
        a = pirate_gear(recolor(a, {"blue": "#8a2a2a" if spr_id == "pirate" else "#2a3a6a"}), spr_id == "pirate_gunner")
    if not unique_id:
        a = tint(a, EL_TINT.get(el, "#ffffff"), 0.28)
    s = SCALE.get(size_key, 3)
    img = Image.fromarray(a, "RGBA").resize((16 * s, 16 * s), Image.NEAREST)
    return img


def map_icon(spr_id, unique_id=None):
    pack, idx = UNIQUE_SPRITE.get(unique_id) or SPECIES_SPRITE[spr_id]
    return Image.fromarray(tile(pack, idx), "RGBA").resize((32, 32), Image.NEAREST)


def swap_background(proc, base_color, replacement, tol=46):
    """Hand-drawn tiles were painted on the old ground; swap those pixels for the Tiny ground so they sit on it cleanly."""
    a = proc.copy()
    bc = np.array(base_color[:3], dtype=float)
    d = np.sqrt(((a[:, :, :3].astype(float) - bc) ** 2).sum(axis=2))
    m = (d < tol) & (a[:, :, 3] > 0)
    a[m] = replacement[m]
    return a
