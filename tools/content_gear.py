"""Gear catalog for Six Hearths: per world 12 weapons (4 blades, 4 bows, 4 staves), 8 armor, 20 accessories.

Tiers: common (tan), rare (magenta), legendary (gold glow).
Stats grow with the wearer's level; tier sets the quality multiplier. Bonuses are percent stat boosts;
effects are special battle abilities.

effects:
  crit   +chance of a critical hit        mp_hit +MP restored on each physical hit (fraction of max MP)
  regen  heal this fraction of max HP each turn   first  start battles with this much TIME gauge (0-100)
  drain  heal this fraction of physical damage    dodge  chance to evade physical attacks
  spell  +spell damage / healing                   limit  Limit gauge fills this much faster
  gold   +gold from battles                        xp     +experience for the wearer
  guard  take this much less damage
"""
import random

TIER_Q = {"common": (1.0, 1.08), "rare": (1.22, 1.28), "legendary": (1.42, 1.5)}

# world -> stat bias for bonuses, effect pool, flavor
THEME = {
    "fire":   {"stats": ["str", "str", "spd", "hp", "dex"], "effects": ["crit", "drain", "limit", "first"],
               "flavor": ["Forged in Emberfall's lesser furnaces.", "Smells of ash and hard work.", "Still faintly warm.",
                          "Pit fighters swear by these.", "Hammered out on a black anvil."]},
    "water":  {"stats": ["mag", "mp", "mdef", "hp", "mag"], "effects": ["regen", "mp_hit", "spell", "guard"],
               "flavor": ["Salvaged from the drowned docks.", "It never quite dries.", "Smells like a calm morning tide.",
                          "Saltmere's fishers trade these.", "Polished by a thousand waves."]},
    "wind":   {"stats": ["spd", "dex", "spd", "mag", "dex"], "effects": ["first", "dodge", "crit", "limit"],
               "flavor": ["Light enough to forget you're carrying it.", "A Kitefall courier's favorite.",
                          "It hums when you run.", "Woven with a thread of breeze.", "Feather-light, kite-strong."]},
    "stone":  {"stats": ["def", "hp", "str", "def", "mdef"], "effects": ["guard", "regen", "gold", "limit"],
               "flavor": ["Copperdeep-made. It will outlive you.", "Heavy, honest, unglamorous.", "Cut from ungilded rock.",
                          "The union stamps every one.", "Built like a mine-prop."]},
    "spirit": {"stats": ["mdef", "mag", "mp", "hp", "mdef"], "effects": ["regen", "spell", "xp", "guard"],
               "flavor": ["Blessed by a tired pilgrim.", "It glows faintly at dawn.", "Hallowmere novices carry these.",
                          "Quietly certain of itself.", "Light, in a shape you can hold."]},
    "void":   {"stats": ["mag", "spd", "dex", "mag", "mp"], "effects": ["drain", "spell", "crit", "dodge"],
               "flavor": ["Nobody remembers who made it.", "It's heavier when you're not looking.",
                          "Lastlight lamplighters swear it's real.", "It casts no shadow.", "Holds on to you, a little."]},
}

# name, kind, tier, optional fixed bonus dict, optional fixed effect dict, optional description
CATALOG = {
    "fire": {
        "weapons": [
            ("Cinder Blade", "blade", "common"), ("Ashsteel Saber", "blade", "common"), ("Magma Edge", "blade", "rare"),
            ("Pitbreaker", "blade", "legendary", {"str": 0.14}, {"crit": 0.1, "limit": 0.3}, "Kael's old pit blade, finally unchained."),
            ("Ember Bow", "bow", "common"), ("Smokewood Bow", "bow", "common"), ("Ashwood Bow", "bow", "rare"),
            ("Phoenix Longbow", "bow", "legendary", {"dex": 0.14, "spd": 0.06}, {"crit": 0.12, "first": 30}, "Its arrows leave a trail of rising sparks."),
            ("Pyre Staff", "staff", "common"), ("Kindling Rod", "staff", "common"), ("Brazier Staff", "staff", "rare"),
            ("Forgemaster's Scepter", "staff", "legendary", {"mag": 0.14, "str": 0.06}, {"spell": 0.15, "drain": 0.05}, "Ignatia's old master carved runes of every flame into it."),
        ],
        "armor": [
            ("Scorchmail", "common"), ("Ashcloth Tunic", "common"), ("Bellows Leather", "common"), ("Cinder Scale", "common"),
            ("Forgeheart Mail", "rare", {"str": 0.06, "hp": 0.06}, None, "Still warm from Emberfall's great forge."),
            ("Magma Plate", "rare"), ("Emberweave Robe", "rare"),
            ("Salamander Coat", "legendary", {"hp": 0.12, "str": 0.08}, {"regen": 0.03, "guard": 0.08}, "Shed by a salamander older than the town."),
        ],
        "acc": [
            ("Ember Ring", "common"), ("Coal Charm", "common"), ("Spark Earring", "common"), ("Ash Bracelet", "common"),
            ("Tinder Pendant", "common"), ("Smoke Brooch", "common"), ("Warm Stone", "common"), ("Cinder Band", "common"),
            ("Forge Token", "common"), ("Pit Fighter's Wrap", "common"),
            ("Magma Ring", "rare"), ("Salamander Scale", "rare"), ("Blazing Sigil", "rare"), ("Furnace Heart", "rare"),
            ("Ember Crown", "rare"), ("Phoenix Feather Pin", "rare"), ("Bellows Gem", "rare"),
            ("Goat-Horn Talisman", "legendary", {"str": 0.12, "spd": 0.08}, {"crit": 0.1, "first": 25}, "Smells faintly of goat. Worth it."),
            ("Eye of the Envious", "legendary", {"str": 0.1, "mag": 0.1}, {"drain": 0.08, "limit": 0.4}, "Green at the center. It wants what you have."),
            ("Hearth of Brannoc", "legendary", {"hp": 0.12, "def": 0.08}, {"regen": 0.04, "gold": 0.2}, "A smith's heart, still keeping the fire."),
        ],
    },
    "water": {
        "weapons": [
            ("Tidecutter", "blade", "common"), ("Coral Saber", "blade", "common"), ("Riptide Blade", "blade", "rare"),
            ("Abyssal Cutlass", "blade", "legendary", {"str": 0.1, "mp": 0.1}, {"mp_hit": 0.06, "drain": 0.06}, "Recovered from a ship that sank twice."),
            ("Coral Bow", "bow", "common"), ("Driftwood Longbow", "bow", "common"), ("Gull's Wing Bow", "bow", "rare"),
            ("Leviathan Bow", "bow", "legendary", {"dex": 0.12, "mag": 0.06}, {"mp_hit": 0.05, "crit": 0.08}, "Strung with something that still swims in your dreams."),
            ("Brine Staff", "staff", "common"), ("Kelp Wand", "staff", "common"), ("Pearl Rod", "staff", "rare"),
            ("Beacon Staff", "staff", "legendary", {"mag": 0.12, "mp": 0.12}, {"spell": 0.15, "regen": 0.02}, "Topped with the lighthouse's first lens."),
        ],
        "armor": [
            ("Shellguard", "common"), ("Sailcloth Coat", "common"), ("Fisher's Oilskin", "common"), ("Scale Vest", "common"),
            ("Tideguard Coat", "rare", {"mp": 0.08, "mdef": 0.06}, None, "Woven from nets that never lost a sailor."),
            ("Kelp Mail", "rare"), ("Nacre Plate", "rare"),
            ("Mantle of the Deep", "legendary", {"mdef": 0.12, "mp": 0.1}, {"regen": 0.04, "guard": 0.08}, "The weight of the whole sea, made gentle."),
        ],
        "acc": [
            ("Pearl Ring", "common"), ("Shell Charm", "common"), ("Sea-Glass Pendant", "common"), ("Anchor Pin", "common"),
            ("Tide Bracelet", "common"), ("Salt Crystal", "common"), ("Fishhook Earring", "common"), ("Rope Bangle", "common"),
            ("Sailor's Knot", "common"), ("Driftwood Token", "common"),
            ("Mermaid's Comb", "rare"), ("Beacon Prism", "rare"), ("Whalebone Charm", "rare"), ("Siren's Locket", "rare"),
            ("Coral Crown", "rare"), ("Undertow Band", "rare"), ("Tidecaller's Shell", "rare"),
            ("Pearl of Tears", "legendary", {"mag": 0.12, "mp": 0.12}, {"spell": 0.12, "mp_hit": 0.04}, "Formed from one tear, cried for a very long time."),
            ("Maren's Lullaby", "legendary", {"mdef": 0.12, "hp": 0.08}, {"regen": 0.05, "guard": 0.06}, "Hum it and the hurt goes quiet."),
            ("Heart of the Falls", "legendary", {"mag": 0.1, "spd": 0.08}, {"mp_hit": 0.06, "first": 20}, "Found behind the falling water, where nobody looks."),
        ],
    },
    "wind": {
        "weapons": [
            ("Gale Sabre", "blade", "common"), ("Feather Dirk", "blade", "common"), ("Kestrel Blade", "blade", "rare"),
            ("Skysplitter", "blade", "legendary", {"spd": 0.12, "str": 0.08}, {"first": 40, "crit": 0.1}, "Cuts the sky open so the light can get in."),
            ("Swift Bow", "bow", "common"), ("Reedline Bow", "bow", "common"), ("Hawkeye Bow", "bow", "rare"),
            ("Featherline Bow", "bow", "legendary", {"spd": 0.12, "dex": 0.1}, {"first": 30, "dodge": 0.08}, "Strung with a thread of the wind itself."),
            ("Sky Staff", "staff", "common"), ("Pinwheel Wand", "staff", "common"), ("Cloudspire Rod", "staff", "rare"),
            ("Staff of the Open Sky", "staff", "legendary", {"mag": 0.12, "spd": 0.08}, {"spell": 0.14, "first": 25}, "Corvane's own staff. It never wanted to be held."),
        ],
        "armor": [
            ("Featherweave", "common"), ("Courier's Jacket", "common"), ("Glider Vest", "common"), ("Breezecloth Robe", "common"),
            ("Stormwoven Mail", "rare"), ("Windrider Coat", "rare"), ("Updraft Mantle", "rare"),
            ("Wings of Kitefall", "legendary", {"spd": 0.14, "dex": 0.08}, {"dodge": 0.12, "first": 25}, "You won't fly. But you'll forget you can't."),
        ],
        "acc": [
            ("Wind Ring", "common"), ("Feather Charm", "common"), ("Kite-String Bracelet", "common"), ("Bell Earring", "common"),
            ("Compass Rose Pin", "common"), ("Cloud Pendant", "common"), ("Courier's Badge", "common"), ("Whistle Charm", "common"),
            ("Breeze Band", "common"), ("Pinwheel Token", "common"),
            ("Zephyr Band", "rare", {"spd": 0.12}, None, "Rings softly when you move fast."),
            ("Hawk Talon", "rare"), ("Gale Crown", "rare"), ("Storm Sigil", "rare"), ("Skyglass Monocle", "rare"),
            ("Updraft Feather", "rare"), ("Belfry Bell", "rare"),
            ("Weathervane Charm", "legendary", {"spd": 0.12, "dex": 0.1}, {"dodge": 0.1, "crit": 0.06}, "Always points toward somewhere better."),
            ("Cage-Breaker's Ring", "legendary", {"spd": 0.1, "str": 0.1}, {"first": 35, "limit": 0.35}, "Forged from the last lock of the Gilded Aviary."),
            ("Roc's Eye", "legendary", {"dex": 0.14, "mag": 0.06}, {"crit": 0.12, "dodge": 0.06}, "It still sees from very high up."),
        ],
    },
    "stone": {
        "weapons": [
            ("Granite Axe", "blade", "common"), ("Miner's Pick", "blade", "common"), ("Quartz Cleaver", "blade", "rare"),
            ("Flintmantle Axe", "blade", "legendary", {"str": 0.12, "def": 0.1}, {"guard": 0.08, "limit": 0.3}, "Durga's family axe. Heavy as a promise."),
            ("Flint Bow", "bow", "common"), ("Ironwood Bow", "bow", "common"), ("Bedrock Bow", "bow", "rare"),
            ("Mountain's Spine", "bow", "legendary", {"dex": 0.12, "def": 0.08}, {"crit": 0.1, "guard": 0.06}, "Carved from a ridge that used to be a dragon, or so they say."),
            ("Geode Staff", "staff", "common"), ("Copper Rod", "staff", "common"), ("Quartz Staff", "staff", "rare"),
            ("Ungilded Scepter", "staff", "legendary", {"mag": 0.12, "def": 0.08}, {"spell": 0.14, "gold": 0.25}, "King Ostrum's scepter, scraped back to honest stone."),
        ],
        "armor": [
            ("Stoneplate", "common"), ("Miner's Coat", "common"), ("Copper Mail", "common"), ("Tunnel Leathers", "common"),
            ("Granite Plate", "rare"), ("Union Overalls", "rare"), ("Seamstone Mail", "rare"),
            ("Mountainheart Plate", "legendary", {"def": 0.16, "hp": 0.12}, {"guard": 0.12, "regen": 0.03}, "Wearing it feels like standing on bedrock."),
        ],
        "acc": [
            ("Stone Ring", "common"), ("Copper Bracelet", "common"), ("Moss Charm", "common"), ("Miner's Lamp", "common"),
            ("Iron Nail Pendant", "common"), ("Pebble Pouch", "common"), ("Union Badge", "common"), ("Slate Token", "common"),
            ("Gravel Band", "common"), ("Hardhat Charm", "common"),
            ("Rootstone Ring", "rare", {"def": 0.1, "hp": 0.06}, None, "Cut from the mountain's oldest root."),
            ("Lode Compass", "rare"), ("Emerald Shard", "rare"), ("Bedrock Sigil", "rare"), ("Garnet Eye", "rare"),
            ("Prospector's Pan", "rare"), ("Golem Core", "rare"),
            ("Geode Heart", "legendary", {"def": 0.12, "mdef": 0.12}, {"guard": 0.1, "regen": 0.03}, "Ugly outside. Breathtaking inside."),
            ("Ungilded Crown", "legendary", {"hp": 0.12, "str": 0.08}, {"gold": 0.3, "limit": 0.3}, "A crown with all the greed scraped off."),
            ("Rustbiter's Fang", "legendary", {"str": 0.12, "def": 0.08}, {"drain": 0.07, "crit": 0.08}, "It chewed through iron. Now it works for you."),
        ],
    },
    "spirit": {
        "weapons": [
            ("Dawn Blade", "blade", "common"), ("Pilgrim's Sword", "blade", "common"), ("Vigil Blade", "blade", "rare"),
            ("Edge of Becoming", "blade", "legendary", {"str": 0.1, "mdef": 0.1}, {"xp": 0.2, "crit": 0.08}, "It gets a little sharper every time you grow."),
            ("Halo Bow", "bow", "common"), ("Candlewood Bow", "bow", "common"), ("Lantern Bow", "bow", "rare"),
            ("Dawnbreaker", "bow", "legendary", {"dex": 0.12, "mag": 0.08}, {"spell": 0.1, "first": 25}, "Every arrow is a sunrise."),
            ("Lumen Staff", "staff", "common"), ("Prayer Rod", "staff", "common"), ("Choir Staff", "staff", "rare"),
            ("Prayer-Bead Staff", "staff", "legendary", {"mag": 0.12, "mdef": 0.1}, {"spell": 0.15, "regen": 0.03}, "Each bead is a thing Sol chose to remember."),
        ],
        "armor": [
            ("Pilgrim Vestments", "common"), ("Novice Robe", "common"), ("Lantern Coat", "common"), ("Chapel Mail", "common"),
            ("Candlelit Mail", "rare"), ("Saint's Mantle", "rare"), ("Abbess's Robe", "rare"),
            ("Raiment of the Finished", "legendary", {"mdef": 0.14, "hp": 0.1}, {"regen": 0.05, "xp": 0.15}, "It fits perfectly, today."),
        ],
        "acc": [
            ("Spirit Ring", "common"), ("Candle Charm", "common"), ("Prayer Beads", "common"), ("Pilgrim Badge", "common"),
            ("Halo Pin", "common"), ("Lantern Token", "common"), ("Choir Bell", "common"), ("White Ribbon", "common"),
            ("Vigil Pendant", "common"), ("Dawn Band", "common"),
            ("Halo Circlet", "rare", {"mdef": 0.1, "mp": 0.08}, None, "A lantern-light you can wear."),
            ("Angel's Tear", "rare"), ("Saint's Relic", "rare"), ("Mirror Shard", "rare"), ("Lumen Sigil", "rare"),
            ("Moth-Wing Pin", "rare"), ("Abbey Crown", "rare"),
            ("Wing of Dawn", "legendary", {"mag": 0.1, "mdef": 0.1, "hp": 0.06}, {"regen": 0.04, "spell": 0.08}, "A single feather of morning."),
            ("Iris's Chisel", "legendary", {"mag": 0.12, "dex": 0.08}, {"xp": 0.25, "spell": 0.1}, "Good enough is a finished thing."),
            ("Lantern of the Crypt", "legendary", {"mdef": 0.12, "mp": 0.1}, {"regen": 0.04, "guard": 0.08}, "It lights the way back up."),
        ],
    },
    "void": {
        "weapons": [
            ("Null Edge", "blade", "common"), ("Hollow Knife", "blade", "common"), ("Echo Blade", "blade", "rare"),
            ("Edge of Nothing", "blade", "legendary", {"str": 0.1, "mag": 0.08}, {"drain": 0.1, "crit": 0.1}, "There's no blade. There's just the cut."),
            ("Hollow Bow", "bow", "common"), ("Drift Bow", "bow", "common"), ("Starless Bow", "bow", "rare"),
            ("Unremembered Bow", "bow", "legendary", {"dex": 0.12, "mag": 0.08}, {"dodge": 0.1, "crit": 0.08}, "Nobody remembers making it."),
            ("Abyss Staff", "staff", "common"), ("Shade Rod", "staff", "common"), ("Echo Staff", "staff", "rare"),
            ("Staff of the Unmoored", "staff", "legendary", {"mag": 0.14, "spd": 0.06}, {"spell": 0.16, "drain": 0.05}, "It floats a finger's width above your palm."),
        ],
        "armor": [
            ("Shadeweave", "common"), ("Drifter's Cloak", "common"), ("Anchor Coat", "common"), ("Static Mail", "common"),
            ("Nullweave Cloak", "rare", {"mag": 0.06, "spd": 0.04}, None, "Woven from the silence between songs."),
            ("Starfall Robe", "rare"), ("Hollow Plate", "rare"),
            ("Mantle of Presence", "legendary", {"mdef": 0.12, "hp": 0.1}, {"dodge": 0.08, "regen": 0.04}, "Wearing it, you are very definitely here."),
        ],
        "acc": [
            ("Void Ring", "common"), ("Anchor Charm", "common"), ("String Bracelet", "common"), ("Shade Pin", "common"),
            ("Echo Earring", "common"), ("Dusk Token", "common"), ("Lamp Charm", "common"), ("Static Band", "common"),
            ("Hollow Bead", "common"), ("Quiet Pendant", "common"),
            ("Gloom Ring", "rare"), ("Name Locket", "rare"), ("Starless Gem", "rare"), ("Echo Sigil", "rare"),
            ("Anchor Crown", "rare"), ("Doorframe Splinter", "rare"), ("Lastlight Lantern", "rare"),
            ("Key to Nowhere", "legendary", {"mag": 0.12, "spd": 0.08}, {"spell": 0.12, "dodge": 0.06}, "Opens a door that isn't there."),
            ("Aldous's Mask", "legendary", {"mag": 0.1, "mdef": 0.1}, {"drain": 0.08, "guard": 0.08}, "It remembers his face so he doesn't have to."),
            ("Mirror of the Room", "legendary", {"spd": 0.1, "dex": 0.1}, {"dodge": 0.1, "first": 30}, "In it, you're standing somewhere else."),
        ],
    },
}

NEUTRAL = {
    "iron_sword": ("Iron Sword", "blade", 0.95, {}, "Plain, honest steel."),
    "short_bow": ("Short Bow", "bow", 0.95, {}, "A hunter's first bow."),
    "oak_staff": ("Oak Staff", "staff", 0.95, {}, "Smells like rain on bark."),
    "leather_coat": ("Leather Coat", "armor", 0.95, {}, "Stitched, patched, trusted."),
    "copper_band": ("Copper Band", "acc", 0.95, {"hp": 0.06}, "Turns your finger green. Worth it."),
    "driftwood_sword": ("Driftwood Sword", "blade", 0.85, {}, "Washed up in the Nexus with you."),
    "travel_coat": ("Traveler's Coat", "armor", 0.85, {}, "It has been many places. So have you, apparently."),
}


ID_OVERRIDE = {"Goat-Horn Talisman": "goathorn_talisman", "Prayer-Bead Staff": "prayer_staff",
               "Candlelit Mail": "candle_mail", "Stormwoven Mail": "storm_mail"}


def gid(name):
    if name in ID_OVERRIDE:
        return ID_OVERRIDE[name]
    return name.lower().replace(" ", "_").replace("'", "").replace("-", "_")


def _bonus(rnd, world, tier, kind):
    th = THEME[world]
    stats = list(th["stats"])
    rnd.shuffle(stats)
    b = {}
    if kind in ("blade", "bow", "staff"):
        main = {"blade": "str", "bow": "dex", "staff": "mag"}[kind]
        b[main] = {"common": 0.06, "rare": 0.09, "legendary": 0.13}[tier]
        extra = {"common": 0, "rare": 1, "legendary": 1}[tier]
    elif kind == "armor":
        extra = {"common": 1, "rare": 2, "legendary": 2}[tier]
    else:
        extra = {"common": 1, "rare": 2, "legendary": 2}[tier]
    amt = {"common": (0.06, 0.1), "rare": (0.08, 0.12), "legendary": (0.1, 0.15)}[tier]
    for s in stats:
        if extra <= 0:
            break
        if s in b:
            continue
        b[s] = round(rnd.uniform(*amt) * (1.6 if s in ("hp", "mp") else 1.0), 2)
        extra -= 1
    return b


def _effect(rnd, world, tier):
    if tier == "common":
        return {}
    pool = THEME[world]["effects"]
    e = rnd.choice(pool)
    scale = {"rare": 0.6, "legendary": 1.0}[tier]
    base = {"crit": 0.1, "mp_hit": 0.05, "regen": 0.04, "first": 35, "drain": 0.08, "dodge": 0.1, "spell": 0.12,
            "limit": 0.35, "gold": 0.25, "xp": 0.2, "guard": 0.1}[e]
    v = base * scale
    return {e: int(v) if e == "first" else round(v, 2)}


def build():
    gear = {}
    world_lists = {}
    for w, cat in CATALOG.items():
        rnd = random.Random("gear-" + w)
        lists = {"weapons": [], "armor": [], "acc": []}
        for row in cat["weapons"]:
            name, kind, tier = row[0], row[1], row[2]
            fixed_b = row[3] if len(row) > 3 else None
            fixed_e = row[4] if len(row) > 4 else None
            desc = row[5] if len(row) > 5 else rnd.choice(THEME[w]["flavor"])
            q = round(rnd.uniform(*TIER_Q[tier]), 2)
            gear[gid(name)] = {"name": name, "kind": kind, "el": w, "tier": tier, "q": q,
                               "bonus": fixed_b if fixed_b is not None else _bonus(rnd, w, tier, kind),
                               "fx": fixed_e if fixed_e is not None else (_effect(rnd, w, tier) if rnd.random() < 0.6 else {}),
                               "desc": desc}
            lists["weapons"].append(gid(name))
        for row in cat["armor"]:
            name, tier = row[0], row[1]
            fixed_b = row[2] if len(row) > 2 else None
            fixed_e = row[3] if len(row) > 3 else None
            desc = row[4] if len(row) > 4 else rnd.choice(THEME[w]["flavor"])
            q = round(rnd.uniform(*TIER_Q[tier]), 2)
            gear[gid(name)] = {"name": name, "kind": "armor", "el": w, "tier": tier, "q": q,
                               "bonus": fixed_b if fixed_b is not None else _bonus(rnd, w, tier, "armor"),
                               "fx": fixed_e if fixed_e is not None else (_effect(rnd, w, tier) if tier != "common" and rnd.random() < 0.5 else {}),
                               "desc": desc}
            lists["armor"].append(gid(name))
        for row in cat["acc"]:
            name, tier = row[0], row[1]
            fixed_b = row[2] if len(row) > 2 else None
            fixed_e = row[3] if len(row) > 3 else None
            desc = row[4] if len(row) > 4 else rnd.choice(THEME[w]["flavor"])
            q = round(rnd.uniform(*TIER_Q[tier]), 2)
            gear[gid(name)] = {"name": name, "kind": "acc", "el": w, "tier": tier, "q": q,
                               "bonus": fixed_b if fixed_b is not None else _bonus(rnd, w, tier, "acc"),
                               "fx": fixed_e if fixed_e is not None else (_effect(rnd, w, tier) if tier != "common" else {}),
                               "desc": desc}
            lists["acc"].append(gid(name))
        world_lists[w] = lists
    for k, (name, kind, q, bonus, desc) in NEUTRAL.items():
        gear[k] = {"name": name, "kind": kind, "el": None, "tier": "common", "q": q, "bonus": bonus, "fx": {}, "desc": desc}
    gear["hearth_pendant"] = {"name": "Hearth Pendant", "kind": "acc", "el": "spirit", "tier": "common", "q": 0.95,
                              "bonus": {"mdef": 0.05}, "fx": {}, "desc": "Warm to the touch. It lets you call on Spirit."}
    for g in gear.values():
        g["type"] = "gear"
        g["price"] = 1.0
    return gear, world_lists


def starter_set(lists, gear):
    """First common blade, bow, staff, armor, acc of a world (what companions join with)."""
    out = []
    for kind in ("blade", "bow", "staff"):
        out.append(next(i for i in lists["weapons"] if gear[i]["kind"] == kind and gear[i]["tier"] == "common"))
    out.append(next(i for i in lists["armor"] if gear[i]["tier"] == "common"))
    out.append(next(i for i in lists["acc"] if gear[i]["tier"] == "common"))
    return out


def commons(lists, gear):
    return [i for k in ("weapons", "armor", "acc") for i in lists[k] if gear[i]["tier"] == "common"]


# random battle drops: (chance of any gear drop, weights common/rare/legendary)
DROP_TABLE = {"easy": (0.05, (90, 10, 0)), "medium": (0.08, (78, 20, 2)), "hard": (0.12, (60, 35, 5)),
              "mini": (0.65, (25, 63, 12)), "boss": (1.0, (0, 70, 30)), "omni": (1.0, (0, 0, 100))}


if __name__ == "__main__":
    g, wl = build()
    from collections import Counter
    print(len(g), "gear items")
    for w, l in wl.items():
        c = Counter(g[i]["tier"] for k in l for i in l[k])
        print(w, {k: len(v) for k, v in l.items()}, dict(c))
    assert len(set(g)) == len(g)
