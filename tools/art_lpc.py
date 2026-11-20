"""Goblin Slayer's LPC characters: the hooded hero, companions, townsfolk, goblins, pirates, monsters and bosses.

Map sheets: 64x64 frames, 9 columns (stand + 8 walk frames), rows down/left/right/up.
Battle sheets: 96x96 frames facing left, laid out as BATTLE_FRAMES (key poses, then attack/cast sequences).
"""
import colorsys
import json
import os
import sys
import zlib

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import lpc

MONSTERS = os.environ.get("SOT_DIR", os.path.expanduser("~/lpc_tiles/sourceoftales")) + "/sprites/monsters"
LPC_ROW = {"up": 0, "left": 1, "down": 2, "right": 3}
MAP_ROWS = [2, 1, 3, 0]          # our order: down, left, right, up
BF = 96                           # battle frame size

# key poses 0..9, then sequences
BATTLE_FRAMES = ([("idle", 1, 0), ("idle", 1, 1), ("combat_idle", 1, 0), ("slash", 1, 4), ("spellcast", 1, 5),
                  ("walk", 1, 0), ("hurt", 0, 5), ("spellcast", 2, 4), ("shoot", 1, 8), ("thrust", 1, 5)]
                 + [("slash", 1, c) for c in range(6)]
                 + [("shoot", 1, c) for c in (0, 2, 4, 5, 6, 7, 8, 10)]
                 + [("thrust", 1, c) for c in range(8)]
                 + [("spellcast", 1, c) for c in range(7)])
SEQ = {"slash": (10, 6), "shoot": (16, 8), "thrust": (24, 8), "spellcast": (32, 7)}

EL_TINT = {"fire": "#ff6a3a", "water": "#4a9aff", "wind": "#40e0c8", "stone": "#7ac050", "spirit": "#fff4d0", "void": "#a060ff"}
SKIN = ["light", "light", "amber", "bronze", "brown"]


def _hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def nearest(material, hexcol, skip=()):
    _, pals = lpc.palettes(material)
    tr, tg, tb = _hx(hexcol)
    th, ts, tv = colorsys.rgb_to_hsv(tr / 255, tg / 255, tb / 255)
    best, bd = None, 1e9
    for name, cols in pals.items():
        if name in skip or len(cols) < 4:
            continue
        r, g, b = _hx(cols[len(cols) // 2])
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        dh = min(abs(h - th), 1 - abs(h - th)) * (2.0 if ts > 0.2 and s > 0.2 else 0.3)
        d = dh * 3 + abs(s - ts) + abs(v - tv) * 1.4
        if d < bd:
            best, bd = name, d
    return best


# ------------------------------------------------------------------ the cast

def hero_items(tier):
    it = [("body", {"color": "light"}), ("heads_human_male", {"color": {"color_1": "light", "color_2": "red"}}),
          ("legs_pants", {"color": "black"}), ("feet_boots_basic", {"color": "black"}),
          ("torso_armour_leather", {"color": {"color_1": "charcoal"}}), ("belt_leather", {"variant": "charcoal"}),
          ("cape_solid", {"color": "black" if tier < 3 else "maroon"}),
          ("hat_hood_cloth", {"color": "charcoal"})]
    if tier >= 1:
        it.append(("shoulders_pauldrons", {"color": "iron"}))
    if tier >= 2:
        it.insert(4, ("torso_chainmail", {"color": "iron"}))
    if tier >= 3:
        it[-2 if tier < 1 else -1] = ("shoulders_pauldrons", {"color": "gold"})
    return "male", it, {"glow_eyes": True, "scar": True}


PARTY = {
    "kael": ("muscular", [("body", {"color": "bronze"}), ("heads_human_male", {"color": {"color_1": "bronze", "color_2": "brown"}}),
                          ("hair_buzzcut", {"color": "black"}), ("wound_eye_right", {}), ("legs_pants", {"color": "leather"}),
                          ("feet_boots_basic", {"color": "brown"}), ("torso_clothes_vest_open", {"color": "red"}),
                          ("hat_bandana", {"color": "red"})], {}),
    "nerissa": ("female", [("body", {"color": "light"}), ("heads_human_female", {"color": {"color_1": "light", "color_2": "blue"}}),
                           ("hair_long", {"color": "blue"}), ("legs_skirts_plain", {"color": "navy"}),
                           ("feet_boots_basic", {"color": "white"}), ("torso_clothes_blouse_longsleeve", {"variant": "white"}),
                           ("neck_necklace_beaded_small", {})], {}),
    "pip": ("teen", [("body", {"color": "light"}), ("heads_human_male_small", {"color": {"color_1": "light", "color_2": "green"}}),
                     ("hair_spiked", {"color": "blonde"}), ("legs_pants", {"color": "teal"}), ("feet_boots_basic", {"color": "brown"}),
                     ("torso_clothes_tunic", {"color": "teal"}), ("wings_feathered", {"color": "white"}),
                     ("hat_cap_leather_feather", {"color": "red"}), ("facial_glasses_round", {})], {}),
    "durga": ("muscular", [("body", {"color": "bronze"}), ("heads_human_male", {"color": {"color_1": "bronze", "color_2": "green"}}),
                           ("beards_beard", {"color": "orange"}), ("legs_armour", {"color": "iron"}), ("feet_boots_rim", {"color": "brown"}),
                           ("torso_armour_leather", {"color": {"color_1": "forest"}}), ("hat_helmet_barbarian_viking", {"color": "iron"})], {}),
    "sol": ("male", [("body", {"color": "light"}), ("heads_human_male", {"color": {"color_1": "light", "color_2": "brown"}}),
                     ("torso_clothes_longsleeve", {"color": "yellow"}), ("legs_pants", {"color": "orange"}),
                     ("feet_boots_basic", {"color": "brown"}),
                     ("neck_necklace_beaded_large", {}), ("belt_leather", {"variant": "brown"})], {}),
    "vesper": ("female", [("body", {"color": "light"}), ("heads_human_female", {"color": {"color_1": "light", "color_2": "purple"}}),
                          ("hair_xlong", {"color": "white"}), ("torso_clothes_robe", {"color": "purple"}),
                          ("feet_boots_basic", {"color": "black"}), ("neck_amulet_star", {})], {"fade": True}),
}
PARTY_WEAPON = {"hero": "blade", "kael": "blade", "durga": "blade", "nerissa": "staff", "sol": "staff", "pip": "bow", "vesper": "bow"}
WEAPON_ITEM = {"blade": ("weapon_sword_longsword", {"variant": "longsword"}),
               "bow": ("weapon_ranged_bow_normal", {"variant": "light"}),
               "staff": ("weapon_magic_simple", {"variant": "simple"})}


def party_recipe(cid, tier=0):
    if cid == "hero":
        return hero_items(tier)
    return PARTY[cid]


# ------------------------------------------------------------------ townsfolk from the dialogue data's looks

HAIR_STYLES = {"male": ["hair_plain", "hair_messy1", "hair_parted", "hair_bedhead", "hair_buzzcut", "hair_spiked", "hair_mop", "hair_page"],
               "female": ["hair_long", "hair_bob", "hair_ponytail", "hair_braid", "hair_pixie", "hair_loose", "hair_bangslong", "hair_wavy"],
               "teen": ["hair_messy1", "hair_spiked", "hair_bangsshort", "hair_pigtails"]}


def npc_recipe(lk, seed):
    bodyk = lk.get("body", "man")
    body = {"woman": "female", "child": "teen", "elder": "male", "guard": "male", "merchant": "male", "robe": "male"}.get(bodyk, "male")
    if bodyk == "elder" and seed % 2:
        body = "female"
    skin = SKIN[min(4, lk.get("skin", 1))]
    head = {"male": "heads_human_male", "female": "heads_human_female", "teen": "heads_human_child"}[body]
    if bodyk == "elder":
        head = "heads_human_male_elderly" if body == "male" else "heads_human_female_elderly"
    if body == "teen":
        head = "heads_human_male_small"
    eyes = ["brown", "blue", "green", "gray"][seed % 4]
    out_c = nearest("cloth", lk.get("outfit", "#6a5a4a"))
    acc_c = nearest("cloth", lk.get("accent", "#c0a060"))
    hair_c = "white" if bodyk == "elder" else nearest("hair", lk.get("hair", "#4a3020"))
    it = [("body", {"color": skin}), (head, {"color": {"color_1": skin, "color_2": eyes}})]
    styles = HAIR_STYLES["teen" if body == "teen" else body]
    if lk.get("hat") not in ("helm", "hood"):
        it.append((styles[seed % len(styles)], {"color": hair_c}))
    if lk.get("beard") and body == "male":
        it.append(("beards_beard", {"color": hair_c}))
    if body == "female" or bodyk == "robe":
        it.append(("legs_skirts_plain" if body == "female" else "legs_pants", {"color": acc_c if body == "female" else "brown"}))
    else:
        it.append(("legs_pants", {"color": ["brown", "leather", "slate", "charcoal", "walnut"][seed % 5]}))
    it.append(("feet_boots_basic", {"color": ["brown", "black", "leather"][seed % 3]}))
    if bodyk == "guard":
        it += [("torso_armour_plate", {"color": "iron"}), ("hat_helmet_nasal", {"color": "iron"})]
    elif bodyk == "robe":
        it += [("torso_clothes_robe", {"color": out_c})]
    elif body == "female":
        it += [("torso_clothes_blouse", {"variant": out_c if out_c in lpc.definition("torso_clothes_blouse").get("variants", []) else "white"})]
    elif body == "teen":
        it += [("torso_clothes_tunic", {"color": out_c})]
    else:
        it += [(["torso_clothes_longsleeve", "torso_clothes_tunic", "torso_clothes_shortsleeve"][seed % 3], {"color": out_c})]
        if seed % 4 == 0:
            it.append(("torso_clothes_vest", {"color": acc_c}))
    hat = lk.get("hat")
    if hat == "hood":
        it.append(("hat_hood_cloth", {"color": out_c}))
    elif hat == "cap":
        it.append(("hat_cap_leather", {"color": acc_c}))
    elif hat == "wide":
        it.append(("hat_cap_cavalier", {"color": acc_c}))
    elif hat == "crown":
        it.append(("hat_formal_crown", {"color": "gold"}))
    if bodyk == "merchant":
        it.append(("hat_formal_bowler", {"color": acc_c}))
    return body, it, {}


# ------------------------------------------------------------------ enemies

def _skin(el, default):
    return {"fire": "bronze", "water": "blue", "wind": "pale_green", "stone": "olive", "spirit": "light", "void": "lavender"}.get(el, default)


def species_recipe(sp, el):
    goblin = {"fire": "green", "water": "dark_green", "wind": "pale_green", "stone": "olive", "spirit": "bright_green", "void": "zombie_green"}
    cl = {"fire": "red", "water": "blue", "wind": "teal", "stone": "forest", "spirit": "white", "void": "purple"}[el]
    R = {
        "goblin": ("teen", [("body", {"color": goblin[el]}), ("heads_goblin", {"color": goblin[el]}), ("legs_pants", {"color": "leather"}),
                            ("torso_clothes_vest", {"color": cl}), ("weapon_sword_dagger", {"variant": "dagger"})]),
        "goblin_shaman": ("teen", [("body", {"color": goblin[el]}), ("heads_goblin", {"color": goblin[el]}), ("torso_clothes_robe", {"color": cl}),
                                   ("hat_magic_wizard", {"color": cl}), ("weapon_magic_simple", {"variant": "simple"})]),
        "goblin_brute": ("muscular", [("body", {"color": goblin[el]}), ("heads_orc_male", {"color": goblin[el]}), ("legs_pants", {"color": "leather"}),
                                      ("torso_armour_leather", {"color": {"color_1": cl}}), ("feet_boots_basic", {"color": "brown"})]),
        "pirate": ("male", [("body", {"color": "amber"}), ("heads_human_male", {"color": {"color_1": "amber", "color_2": "brown"}}),
                            ("beards_beard", {"color": "black"}), ("legs_pants", {"color": "navy"}), ("feet_boots_basic", {"color": "black"}),
                            ("torso_clothes_longsleeve", {"color": cl}), ("torso_clothes_vest", {"color": "black"}),
                            ("hat_tricorne", {"color": "black"}), ("weapon_sword_dagger", {"variant": "dagger"})]),
        "pirate_gunner": ("male", [("body", {"color": "light"}), ("heads_human_male", {"color": {"color_1": "light", "color_2": "blue"}}),
                                   ("legs_pants", {"color": "brown"}), ("feet_boots_basic", {"color": "black"}),
                                   ("torso_clothes_longsleeve", {"color": "white"}), ("torso_clothes_vest", {"color": cl}),
                                   ("hat_bandana_pirate", {"color": "red"}), ("weapon_ranged_crossbow", {"variant": "crossbow"})]),
        "bum": ("male", [("body", {"color": "light"}), ("heads_human_male_plump", {"color": {"color_1": "light", "color_2": "brown"}}),
                         ("hair_messy1", {"color": "gray"}), ("beards_beard", {"color": "gray"}), ("legs_pants", {"color": "brown"}),
                         ("torso_clothes_longsleeve", {"color": cl}), ("hat_cap_leather", {"color": "brown"})]),
        "loiterer": ("male", [("body", {"color": "amber"}), ("heads_human_male", {"color": {"color_1": "amber", "color_2": "gray"}}),
                              ("legs_pants", {"color": "charcoal"}), ("feet_boots_basic", {"color": "black"}),
                              ("torso_clothes_longsleeve", {"color": "charcoal"}), ("hat_hood_cloth", {"color": cl}),
                              ("weapon_sword_dagger", {"variant": "dagger"})]),
        "undead": ("male", [("body_zombie", {"color": "zombie"}), ("heads_zombie", {"color": "zombie"}),
                            ("legs_pants", {"color": "slate"}), ("torso_clothes_shortsleeve", {"color": cl})]),
        "knight": ("male", [("body", {"color": "light"}), ("heads_human_male", {"color": {"color_1": "light", "color_2": "blue"}}),
                            ("legs_armour", {"color": "steel"}), ("torso_armour_plate", {"color": "steel"}),
                            ("hat_helmet_greathelm", {"color": "steel"}), ("cape_solid", {"color": cl}),
                            ("weapon_sword_longsword", {"variant": "longsword"})]),
        "elf": ("female", [("body", {"color": "light"}), ("heads_human_female", {"color": {"color_1": "light", "color_2": "green"}}),
                           ("hair_long", {"color": "platinum"}), ("torso_clothes_robe", {"color": cl}),
                           ("weapon_magic_simple", {"variant": "simple"})]),
        "archer": ("male", [("body", {"color": "amber"}), ("heads_human_male", {"color": {"color_1": "amber", "color_2": "green"}}),
                            ("hair_parted", {"color": "brown"}), ("legs_pants", {"color": "leather"}),
                            ("torso_armour_leather", {"color": {"color_1": "leather"}}), ("hat_hood_cloth", {"color": cl}),
                            ("weapon_ranged_bow_normal", {"variant": "light"})]),
        "ghost": ("male", [("body", {"color": "fur_white"}), ("heads_skeleton", {}), ("torso_clothes_robe", {"color": "white"}),
                           ("hat_hood_cloth", {"color": "white"})]),
        "bear": ("muscular", [("body", {"color": "fur_brown"}), ("heads_wolf_male", {"color": "fur_brown"}),
                              ("legs_pants", {"color": "brown"})]),
        "ogre": ("muscular", [("body", {"color": "olive"}), ("heads_troll", {"color": "olive"}), ("legs_pants", {"color": "leather"}),
                              ("torso_clothes_vest_open", {"color": cl})]),
        "boar": ("muscular", [("body", {"color": "fur_brown"}), ("heads_boarman", {"color": "fur_brown"}),
                              ("legs_pants", {"color": "leather"}), ("torso_armour_leather", {"color": {"color_1": cl}})]),
        "fknight": ("male", [("body", {"color": "light"}), ("heads_human_male", {"color": {"color_1": "light", "color_2": "red"}}),
                             ("legs_armour", {"color": "silver"}), ("torso_armour_plate", {"color": "silver"}),
                             ("hat_helmet_xeon", {"color": "silver"}), ("weapon_sword_longsword", {"variant": "longsword"})]),
        "farcher": ("male", [("body", {"color": "light"}), ("heads_lizard_male", {"color": "dark_green"}),
                             ("torso_armour_legion", {"color": "bronze"}), ("legs_armour", {"color": "bronze"}),
                             ("weapon_ranged_crossbow", {"variant": "crossbow"})]),
        "fbum": ("male", [("body", {"color": "light"}), ("heads_frankenstein", {"color": "green"}), ("legs_pants", {"color": "slate"}),
                          ("torso_jacket_trench", {"color": cl}), ("hat_formal_tophat", {"color": "black"})]),
        "rat": ("teen", [("body", {"color": "fur_grey"}), ("heads_rat", {"color": "fur_grey"}), ("legs_pants", {"color": "brown"}),
                         ("torso_clothes_vest", {"color": cl})]),
    }
    return R[sp]


MONSTER_SPRITES = {"slime": "slime", "bat": "bat", "bee": "bee", "snake": "snake", "worm": "small_worm", "eyeball": "eyeball", "beetle": "beetle"}

# bosses and uniques built as LPC characters (the rest keep their hand-drawn art)
UNIQUE_RECIPES = {
    "king_goblin": ("muscular", [("body", {"color": "green"}), ("heads_goblin", {"color": "green"}), ("legs_armour", {"color": "gold"}),
                                 ("torso_armour_plate", {"color": "gold"}), ("cape_solid", {"color": "purple"}),
                                 ("hat_formal_crown", {"color": "gold"}), ("weapon_blunt_mace", {"variant": "mace"})], 2),
    "vulkar": ("muscular", [("body", {"color": "bronze"}), ("heads_human_male", {"color": {"color_1": "bronze", "color_2": "green"}}),
                            ("hair_spiked", {"color": "green"}), ("legs_pants", {"color": "charcoal"}), ("torso_armour_leather", {"color": {"color_1": "red"}}),
                            ("shoulders_pauldrons", {"color": "brass"}), ("weapon_sword_longsword", {"variant": "longsword"})], 2),
    "maren": ("female", [("body", {"color": "blue"}), ("heads_human_female", {"color": {"color_1": "blue", "color_2": "blue"}}),
                         ("hair_xlong_wavy", {"color": "blue"}), ("torso_clothes_robe", {"color": "navy"}), ("neck_necklace_beaded_large", {})], 2),
    "corvane": ("male", [("body", {"color": "light"}), ("heads_human_male_gaunt", {"color": {"color_1": "light", "color_2": "yellow"}}),
                         ("hair_long", {"color": "black"}), ("torso_jacket_frock", {"color": "teal"}), ("legs_pants", {"color": "black"}),
                         ("wings_feathered", {"color": "black"}), ("weapon_magic_simple", {"variant": "simple"})], 2),
    "ostrum": ("muscular", [("body", {"color": "light"}), ("heads_human_male_plump", {"color": {"color_1": "light", "color_2": "brown"}}),
                            ("beards_beard", {"color": "gray"}), ("torso_armour_plate", {"color": "gold"}), ("legs_armour", {"color": "gold"}),
                            ("cape_solid", {"color": "maroon"}), ("hat_formal_crown", {"color": "gold"})], 2),
    "iris": ("female", [("body", {"color": "light"}), ("heads_human_female", {"color": {"color_1": "light", "color_2": "yellow"}}),
                        ("hair_princess", {"color": "platinum"}), ("torso_clothes_robe", {"color": "white"}), ("wings_lunar", {})], 2),
    "nobody": ("male", [("body", {"color": "fur_white"}), ("heads_skeleton", {}), ("torso_clothes_robe", {"color": "black"}),
                        ("hat_hood_cloth", {"color": "black"}), ("weapon_magic_simple", {"variant": "simple"})], 2),
    "aeon": ("male", [("body", {"color": "light"}), ("heads_human_male", {"color": {"color_1": "light", "color_2": "yellow"}}),
                      ("hair_long", {"color": "white"}), ("torso_armour_plate", {"color": "gold"}), ("legs_armour", {"color": "gold"}),
                      ("wings_feathered", {"color": "white"}), ("weapon_sword_longsword", {"variant": "longsword"})], 3),
    "nihil": ("male", [("body", {"color": "fur_black"}), ("heads_skeleton", {}), ("torso_armour_plate", {"color": "dark"}),
                       ("cape_solid", {"color": "purple"}), ("wings_bat", {"color": "black"}), ("hat_helmet_horned", {"color": "dark"})], 3),
}


# ------------------------------------------------------------------ rendering

def _compose(body, items, anim, frame):
    return lpc.compose(body, items, anim, frame=frame)


def _post(sheet, opts, body, items, anim, frame):
    if opts.get("glow_eyes"):
        # the eyes burn red through the shadow of the hood
        bare = [i for i in items if i[0] not in ("facial_mask_plain",)]
        ref = _compose(body, bare, anim, frame)
        red = (ref[:, :, 0].astype(int) > 150) & (ref[:, :, 1] < 90) & (ref[:, :, 2] < 90) & (ref[:, :, 3] > 0)
        # only pixels that sit in the face area (under the hood) count as eyes
        hood = _compose(body, [i for i in items if i[0] in ("hat_hood_cloth",)], anim, frame)[:, :, 3] > 0
        head = _compose(body, [i for i in items if i[0].startswith("heads_")], anim, frame)[:, :, 3] > 0
        m = red & ~hood & head
        sheet[m] = (255, 60, 40, 255)
        if opts.get("scar"):
            _scar(sheet, m, hood, frame)
    if opts.get("fade"):
        h = sheet.shape[0]
        ys, xs = np.nonzero(sheet[:, :, 3])
        for y, x in zip(ys, xs):
            fy = y % frame
            if fy > frame * 0.8 and (x + y) % 2 == 0:
                sheet[y, x, 3] = 110
    return sheet


def _scar(sheet, eyes, hood, frame):
    """An old blade scar: brow to cheek, straight through the eye on the left of the picture."""
    pale, deep = (226, 168, 158, 255), (128, 62, 60, 255)
    H, W = eyes.shape
    for cy in range(0, H, frame):
        for cx in range(0, W, frame):
            ys, xs = np.nonzero(eyes[cy:cy + frame, cx:cx + frame])
            if len(xs) == 0:
                continue
            ex = xs.min()
            ey = int(ys[xs == ex].mean())
            for k in range(-3, 5):
                x = cx + ex + (1 if k > 1 else 0)
                y = cy + ey + k
                if 0 <= y < H and 0 <= x + 1 < W and sheet[y, x, 3] > 0 and not hood[y, x]:
                    if not eyes[y, x]:
                        sheet[y, x] = pale
                    if sheet[y, x + 1, 3] > 0 and not hood[y, x + 1] and not eyes[y, x + 1]:
                        sheet[y, x + 1] = deep


def anim_sheet(recipe, anim, frame):
    body, items, opts = recipe
    s = _compose(body, items, anim, frame)
    return _post(s, opts, body, items, anim, frame)


def map_sheet(recipe):
    walk = anim_sheet(recipe, "walk", 64)
    rows = [walk[r * 64:(r + 1) * 64] for r in MAP_ROWS]
    return Image.fromarray(np.concatenate(rows, axis=0), "RGBA")


def battle_sheet(recipe, items_override=None):
    body, items, opts = recipe
    if items_override is not None:
        items = items_override
    cache = {}
    frames = []
    for anim, row, col in BATTLE_FRAMES:
        if anim not in cache:
            s = _compose(body, items, anim, BF)
            if items_override is None:
                s = _post(s, opts, body, items, anim, BF)
            cache[anim] = s
        f = lpc.frame_of(cache[anim], anim, row, col, BF)
        if (anim, row, col) == ("walk", 1, 0) and len(frames) == 5:
            f = np.roll(f, 3, axis=1)          # hurt: knocked back
            m = (f[:, :, 3] > 0)
            f[m, :3] = (f[m, :3] * 0.6 + 255 * 0.4).astype(np.uint8)
        frames.append(f)
    return Image.fromarray(np.concatenate(frames, axis=1), "RGBA")


def tint(a, col, amount):
    c = np.array(_hx(col), dtype=float)
    out = a.copy()
    m = a[:, :, 3] > 0
    p = a[m, :3].astype(float)
    lum = (0.3 * p[:, 0] + 0.59 * p[:, 1] + 0.11 * p[:, 2]) / 255.0
    dark = lum < 0.16
    tgt = c[None, :] * (0.4 + 0.9 * lum[:, None])
    q = np.clip(p * (1 - amount) + tgt * amount, 0, 255)
    q[dark] = p[dark]
    out[m, :3] = q.astype(np.uint8)
    return out


def weapon_sheet(body, kind, el):
    img = np.array(battle_sheet((body, [], {}), [WEAPON_ITEM[kind]]))
    if el:
        img = tint(img, EL_TINT[el], 0.45)
    return Image.fromarray(img, "RGBA")


def enemy_image(recipe, el, scale=1, tint_amt=0.0):
    body, items = recipe[0], recipe[1]
    s = _compose(body, items, "combat_idle", BF)
    f = lpc.frame_of(s, "combat_idle", LPC_ROW["right"], 0, BF)
    if not f[:, :, 3].any():
        s = _compose(body, items, "walk", BF)
        f = lpc.frame_of(s, "walk", LPC_ROW["right"], 0, BF)
    if tint_amt and el:
        f = tint(f, EL_TINT[el], tint_amt)
    # crop to content with a little margin so the battle layout can size it
    ys, xs = np.nonzero(f[:, :, 3])
    f = f[max(0, ys.min() - 2):ys.max() + 1, max(0, xs.min() - 2):min(BF, xs.max() + 3)]
    img = Image.fromarray(f, "RGBA")
    if scale > 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    return img


def enemy_map_icon(recipe):
    body, items = recipe[0], recipe[1]
    s = _compose(body, items, "walk", 64)
    f = lpc.frame_of(s, "walk", LPC_ROW["down"], 0, 64)
    return Image.fromarray(f, "RGBA")


def monster_image(name, el, scale=2):
    a = np.array(Image.open(f"{MONSTERS}/{MONSTER_SPRITES[name]}.png").convert("RGBA"))
    fw = a.shape[1] // 3
    fh = a.shape[0] // 4
    f = a[3 * fh:4 * fh, 0:fw]        # facing right
    if el:
        f = tint(f, EL_TINT[el], 0.3)
    img = Image.fromarray(f, "RGBA")
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


# ------------------------------------------------------------------ build everything into the game's assets

UNIQUE_FROM_SPECIES_EXTRA = {
    "rat_king": ("rat", [("hat_formal_crown", {"color": "gold"})]),
    "storm_harpy": ("elf", [("wings_feathered", {"color": "gray"})]),
    "lantern_wraith": ("ghost", []),
}
UNIQUE_MONSTER = {"gloomfin": ("eyeball", 3), "rustbiter": ("worm", 4), "gravelmaw": ("beetle", 2)}


def build(out, db_path, maps_dir):
    import glob
    sys.path.insert(0, os.path.dirname(__file__))
    from art_common import aura_map, save
    db = json.load(open(db_path))
    os.makedirs(f"{out}/chars", exist_ok=True)
    os.makedirs(f"{out}/battle", exist_ok=True)
    os.makedirs(f"{out}/weapons", exist_ok=True)
    cast = {"hero_t%d" % t: party_recipe("hero", t) for t in range(4)}
    cast.update({c: party_recipe(c) for c in PARTY})
    for cid, r in cast.items():
        ms = map_sheet(r)
        save(ms, f"{out}/chars/{cid}.png")
        save(aura_map(ms, 64, 64, 3), f"{out}/chars/{cid}_aura.png")
        bs = battle_sheet(r)
        save(bs, f"{out}/battle/{cid}.png")
        save(aura_map(bs, BF, BF, 4), f"{out}/battle/{cid}_aura.png")
        print("party", cid)
    for cid in ["hero"] + list(PARTY):
        body = party_recipe(cid)[0]
        for kind in ("blade", "bow", "staff"):
            for el in [None] + list(EL_TINT):
                save(weapon_sheet(body, kind, el), f"{out}/weapons/{cid}_{kind}_{el or 'none'}.png")
    json.dump({}, open(f"{out}/battle/hands.json", "w"))
    # townsfolk
    seen = set()
    for path in glob.glob(f"{maps_dir}/*.json"):
        m = json.load(open(path))
        for n in m["npcs"]:
            if n["id"] in seen:
                continue
            seen.add(n["id"])
            r = party_recipe(n["id"]) if n["id"] in PARTY else npc_recipe(n["look"], zlib.crc32(n["id"].encode()))
            save(map_sheet(r), f"{out}/chars/npc_{n['id']}.png")
            if n.get("job"):
                save(job_sheet(r, n["job"], n.get("jface", "down")), f"{out}/chars/npc_{n['id']}_job.png")
    print("npcs", len(seen))
    # enemies
    meta = json.load(open(f"{out}/enemies/sizes.json")) if os.path.exists(f"{out}/enemies/sizes.json") else {}
    for sp in db["species"]:
        try:
            species_recipe(sp, "fire")
        except KeyError:
            continue
        for el in EL_TINT:
            img = enemy_image(species_recipe(sp, el), el, 1, 0.12)
            if sp == "ghost":
                img.putalpha(img.getchannel("A").point(lambda v: v * 190 // 255))
            save(img, f"{out}/enemies/{sp}_{el}.png")
        meta[sp] = list(img.size)
    for uid, u in db["uniques"].items():
        spr, el = u["sprite"], u["el"]
        img = icon = None
        if uid in UNIQUE_RECIPES:
            b, it, sc = UNIQUE_RECIPES[uid]
            img, icon = enemy_image((b, it), None, sc), enemy_map_icon((b, it))
        elif uid in UNIQUE_FROM_SPECIES_EXTRA or spr in UNIQUE_FROM_SPECIES_EXTRA:
            base, extra = UNIQUE_FROM_SPECIES_EXTRA.get(uid) or UNIQUE_FROM_SPECIES_EXTRA[spr]
            b, it = species_recipe(base, el)
            img, icon = enemy_image((b, it + extra), el, 2, 0.15), enemy_map_icon((b, it + extra))
        elif uid in UNIQUE_MONSTER:
            mname, sc = UNIQUE_MONSTER[uid]
            img = monster_image(mname, el, sc)
            icon = monster_image(mname, el, 2)
        else:
            try:
                b, it = species_recipe(spr, el)
            except KeyError:
                continue      # hand-drawn special monsters keep their art
            sc = 2 if u.get("size") in ("xl", "boss") else 1
            img, icon = enemy_image((b, it + [("hat_formal_crown", {"color": "gold"})] if u["tier"] == "mini" else it), el, max(1, sc), 0.15), \
                enemy_map_icon((b, it))
        save(img, f"{out}/enemies/u_{uid}.png")
        save(icon, f"{out}/enemies/map_{uid}.png")
        meta["u_" + uid] = list(img.size)
    json.dump(meta, open(f"{out}/enemies/sizes.json", "w"))
    lpc.write_credits(f"{out}/licenses/LPC_CREDITS.csv")
    print("enemies done; credits:", len(lpc.CREDITS), "missing:", lpc.MISSING)




# ------------------------------------------------------------------ townsfolk at work

LPC_ROW = {"up": 0, "left": 1, "down": 2, "right": 3}
# job -> (body animation, tool items); "rod" is assembled by hand (13-frame cast/wait/reel)
JOBS = {
    "hoe": ("thrust", [("tool_hoe", {})]),
    "water": ("thrust", [("tool_watering_can", {})]),
    "dig": ("thrust", [("tool_shovel", {})]),
    "mine": ("slash", [("tool_pickaxe", {})]),
    "chop": ("slash", [("tool_axe", {})]),
    "smith": ("slash", [("tool_hammer", {})]),
    "seance": ("spellcast", []),
    "pray": ("spellcast", []),
    "fish": ("rod", []),
}
ROD_MAP = [0, 1, 2, 3, 4, 5, 4, 4, 4, 5, 4, 2, 3]
JOB_H = 120        # 128 wide cells, cropped so the bottom lines up with the 64px walk sheet


def job_sheet(recipe, job, face):
    """One row of 128x120 frames: this townsperson doing their work, facing `face`."""
    body, items, opts = recipe
    items = [i for i in items if not i[0].startswith(("weapon_", "shield_"))]
    anim, tools = JOBS[job]
    r = LPC_ROW[face]
    if anim == "rod":
        base = anim_sheet((body, items, opts), "thrust", 128)
        rod = [np.array(Image.open(os.path.join(lpc.SHEETS, "tools/fishing_rod", f"{l}.png")).convert("RGBA")) for l in ("bg", "fg")]
        lpc.definition("tool_rod")
        frames = []
        for j, bf in enumerate(ROD_MAP):
            f = np.zeros((128, 128, 4), np.uint8)
            for layer, src in ((rod[0], None), (None, base), (rod[1], None)):
                if layer is not None:
                    cell = np.zeros((128, 128, 4), np.uint8)
                    piece = layer[r * 128:(r + 1) * 128, j * 128:(j + 1) * 128]
                    # tool cells are centered on the 64px body grid; our body sits 24px lower (see compose)
                    cell[24:128] = piece[0:104]
                else:
                    cell = lpc.frame_of(src, "thrust", r, bf, 128)
                m = cell[:, :, 3] > 0
                f[m] = cell[m]
            frames.append(f[:JOB_H])
    elif anim == "slash":
        # swing tools: cell k pairs with body slash frame k; the game plays them in LPC's tool order 5,4,3,1,0
        base = anim_sheet((body, items, opts), "slash", 128)
        layers = sorted(lpc.layers_for(tools[0][0], body, "slash"), key=lambda l: l[0])
        frames = []
        for k in range(6):
            f = np.zeros((128, 128, 4), np.uint8)
            stack = [(z, a) for z, a, fs in layers if fs == 128 and z < 100] + [(100, None)] + \
                    [(z, a) for z, a, fs in layers if fs == 128 and z >= 100]
            for z, a in stack:
                if a is None:
                    cell = lpc.frame_of(base, "slash", r, k, 128)
                else:
                    cell = np.zeros((128, 128, 4), np.uint8)
                    c = k
                    cell[24:128] = a[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128][0:104]
                m = cell[:, :, 3] > 0
                f[m] = cell[m]
            frames.append(f[:JOB_H])
    else:
        sheet = anim_sheet((body, items + tools, opts), anim, 128)
        n = lpc.ANIM_FRAMES[anim]
        frames = [lpc.frame_of(sheet, anim, r, c, 128)[:JOB_H] for c in range(n)]
    return Image.fromarray(np.concatenate(frames, axis=1), "RGBA")



# ------------------------------------------------------------------ Blessed (laser) weapons

ENERGY = {"fire": "#ff7a40", "water": "#50b8ff", "wind": "#50ffd8", "stone": "#a8ff60", "spirit": "#fff0b0", "void": "#c070ff", None: "#a0f0ff"}
BRASS = [(58, 36, 14), (120, 80, 26), (184, 134, 42), (240, 208, 112)]
IRON = [(24, 22, 26), (58, 54, 62), (100, 96, 108), (150, 146, 158)]
BLESSED_ITEM = {"blade": ("weapon_sword_glowsword", {"variant": "blue"}),
                "rifle": ("weapon_ranged_crossbow", {"variant": "crossbow"}),
                "pistol": ("weapon_ranged_crossbow", {"variant": "crossbow"}),
                "staff": ("weapon_magic_diamond", {"variant": "brass"})}


def _ramp(lum, ramp):
    i = np.clip((lum * (len(ramp) - 0.001)).astype(int), 0, len(ramp) - 1)
    return np.array(ramp, dtype=np.uint8)[i]


def _energy(lum, col):
    """Saturated energy color, burning to a white-hot core only at the brightest pixels."""
    c = np.array(_hx(col)[:3], dtype=float)
    l = np.clip(np.asarray(lum, dtype=float), 0, 1)
    if l.size and l.max() > l.min():
        l = (l - l.min()) / (l.max() - l.min())
    w = l[..., None]
    base = np.clip(c * (0.8 + 0.35 * w) + 25, 0, 255)
    core = (255 - base) * np.clip((w - 0.5) / 0.5, 0, 1) ** 1.2 * 0.9
    return np.clip(base + core, 0, 255).astype(np.uint8)


def blessed_sheet(body, style, el):
    """A Blessed weapon overlay (39 battle frames): brass, dark iron and glowing energy."""
    a = np.array(battle_sheet((body, [], {}), [BLESSED_ITEM[style]])).copy()
    rgb = a[:, :, :3].astype(float)
    alpha = a[:, :, 3] > 0
    lum = (0.3 * rgb[:, :, 0] + 0.59 * rgb[:, :, 1] + 0.11 * rgb[:, :, 2]) / 255.0
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    energy = ENERGY.get(el, ENERGY[None])
    if style == "blade":
        glow = alpha & (b > r + 30)
        a[glow, :3] = _energy(lum[glow] * 1.3, energy)
        hilt = alpha & ~glow
        a[hilt, :3] = _ramp(lum[hilt] * 1.2, BRASS)
    elif style in ("rifle", "pistol"):
        wood = alpha & (r > b + 25)
        a[wood, :3] = _ramp(lum[wood] * 1.4, BRASS)
        metal = alpha & ~wood
        a[metal, :3] = _ramp(lum[metal], IRON)
        # energy coils: the brightest strip of each frame (the old string and bolt) carries the charge
        hot = metal & (lum > 0.55)
        a[hot, :3] = _energy(np.full(hot.sum(), 0.9), energy)
        F = BF
        for f in range(a.shape[1] // F):
            cell = a[:, f * F:(f + 1) * F]
            m = cell[:, :, 3] > 0
            if not m.any():
                continue
            ys, xs = np.nonzero(m)
            if style == "pistol":
                # a brass sidearm drawn in the hand: barrel, drum, grip, glowing muzzle coil
                row = int(np.bincount(ys).argmax())
                hand_x = int(xs.max())
                cell[:] = 0
                if f in (0, 1, 2, 5, 6, 7) or f >= 32:
                    continue           # holstered outside the attack poses
                ink = (14, 10, 8, 255)
                x0, x1 = hand_x - 15, hand_x + 1
                cell[row - 2:row + 2, x0:x1] = ink
                cell[row - 1:row + 1, x0 + 1:x1 - 1] = (*BRASS[2], 255)
                cell[row - 1, x0 + 1:x1 - 1] = (*BRASS[3], 255)
                cell[row - 3:row + 3, hand_x - 9:hand_x - 4] = ink          # drum
                cell[row - 2:row + 2, hand_x - 8:hand_x - 5] = (*BRASS[1], 255)
                cell[row - 2, hand_x - 8:hand_x - 5] = (*BRASS[3], 255)
                cell[row + 1:row + 7, hand_x - 3:hand_x + 1] = ink           # grip
                cell[row + 2:row + 6, hand_x - 2:hand_x] = (*IRON[2], 255)
                ec = _hx(energy)[:3]
                cell[row - 2:row + 2, x0 - 1:x0 + 2] = (*ec, 255)            # muzzle coil
                cell[row - 1, x0] = (255, 255, 255, 255)
                for xx in (x0 + 4, x0 + 7):
                    cell[row - 1:row + 1, xx] = (*ec, 255)
            else:
                # coil rings along the barrel
                row = np.bincount(ys).argmax()
                for xx in range(xs.min() + 3, xs.max() - 3, 4):
                    if m[row, xx]:
                        cell[max(0, row - 1):row + 2, xx] = (*_hx(energy)[:3], 255)
    elif style == "staff":
        a[alpha, :3] = _ramp(lum[alpha] * 1.15, BRASS)
        F = BF
        for f in range(a.shape[1] // F):
            cell = a[:, f * F:(f + 1) * F]
            m = cell[:, :, 3] > 0
            if not m.any():
                continue
            ys, xs = np.nonzero(m)
            # the head of the staff (its far end from the hand) burns with energy
            top = ys.min() + (ys.max() - ys.min()) * 0.32
            left = xs.min() + (xs.max() - xs.min()) * 0.32
            head = m & ((np.arange(F)[:, None] < top) | ((np.arange(F)[None, :] < left) & (xs.max() - xs.min() > ys.max() - ys.min())))
            l2 = (0.3 * cell[:, :, 0] + 0.59 * cell[:, :, 1] + 0.11 * cell[:, :, 2]) / 255.0
            cell[head, :3] = _energy(l2[head] * 1.2, energy)
    return Image.fromarray(a, "RGBA")


def build_blessed(out):
    sys.path.insert(0, os.path.dirname(__file__))
    from art_common import save
    for cid in ["hero"] + list(PARTY):
        body = party_recipe(cid)[0]
        for style in BLESSED_ITEM:
            for el in [None] + list(EL_TINT):
                save(blessed_sheet(body, style, el), f"{out}/weapons/{cid}_blessed_{style}_{el or 'none'}.png")
        print("blessed", cid)


if __name__ == "__main__":
    if sys.argv[1] == "blessed":
        build_blessed(sys.argv[2])
    else:
        build(sys.argv[1], sys.argv[2], sys.argv[3])
