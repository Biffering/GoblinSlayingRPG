"""Core game database for Six Hearths: elements, stats, gear, items, spells, enemies, summons, companions.

Everything here is exported to data/db.json and read by the game at runtime.
"""

ELEMENTS = ["fire", "water", "wind", "stone", "spirit", "void"]
ELEMENT_INFO = {
    "fire":   {"name": "Fire",   "color": "#ff4a32", "beats": "wind",   "prefix": "Cinder"},
    "water":  {"name": "Water",  "color": "#3a86ff", "beats": "fire",   "prefix": "Brine"},
    "wind":   {"name": "Wind",   "color": "#36d6c3", "beats": "stone",  "prefix": "Gale"},
    "stone":  {"name": "Stone",  "color": "#58c84e", "beats": "water",  "prefix": "Granite"},
    "spirit": {"name": "Spirit", "color": "#f4f2ff", "beats": "void",   "prefix": "Lumen"},
    "void":   {"name": "Void",   "color": "#9b4dff", "beats": "spirit", "prefix": "Null"},
}

# ------------------------------------------------------------------ party
# base stats at level 1 and growth per level
CHARACTERS = {
    "hero": {
        "name": "Wren", "title": "the Kindler", "innate": None,
        "base": {"hp": 64, "mp": 18, "str": 11, "def": 9, "mag": 9, "mdef": 9, "spd": 11, "dex": 10},
        "grow": {"hp": 22, "mp": 4.0, "str": 2.0, "def": 1.6, "mag": 1.8, "mdef": 1.6, "spd": 1.2, "dex": 1.6},
        "limit": "kindlers_wrath",
        "bio": "A Kindler: one who carries the elements of whatever they wear. Woke in the Nexus with no fire of their own.",
    },
    "kael": {
        "name": "Kael", "title": "Ashborn", "innate": "fire", "world": "fire",
        "base": {"hp": 78, "mp": 10, "str": 14, "def": 10, "mag": 6, "mdef": 7, "spd": 10, "dex": 10},
        "grow": {"hp": 27, "mp": 2.4, "str": 2.6, "def": 1.8, "mag": 1.0, "mdef": 1.2, "spd": 1.1, "dex": 1.4},
        "limit": "pit_fury", "bio": "Former champion of the Emberfall fighting pits. Hits hard, thinks later.",
    },
    "nerissa": {
        "name": "Nerissa", "title": "Lightkeeper", "innate": "water", "world": "water",
        "base": {"hp": 54, "mp": 26, "str": 7, "def": 8, "mag": 13, "mdef": 12, "spd": 10, "dex": 9},
        "grow": {"hp": 18, "mp": 5.6, "str": 1.1, "def": 1.3, "mag": 2.5, "mdef": 2.2, "spd": 1.2, "dex": 1.3},
        "limit": "lighthouse_beam", "bio": "Keeper of the Saltmere lighthouse, which has been dark since the tide-mother began to grieve.",
    },
    "pip": {
        "name": "Pip", "title": "Featherline", "innate": "wind", "world": "wind",
        "base": {"hp": 58, "mp": 16, "str": 9, "def": 8, "mag": 8, "mdef": 8, "spd": 15, "dex": 14},
        "grow": {"hp": 20, "mp": 3.6, "str": 1.5, "def": 1.3, "mag": 1.5, "mdef": 1.4, "spd": 1.9, "dex": 2.4},
        "limit": "thousand_feathers", "bio": "The fastest courier in Kitefall, grounded since sky pirates stole her glider-wings.",
    },
    "durga": {
        "name": "Durga", "title": "Flintmantle", "innate": "stone", "world": "stone",
        "base": {"hp": 86, "mp": 12, "str": 12, "def": 14, "mag": 6, "mdef": 10, "spd": 8, "dex": 9},
        "grow": {"hp": 30, "mp": 2.6, "str": 2.1, "def": 2.6, "mag": 1.0, "mdef": 1.7, "spd": 0.9, "dex": 1.2},
        "limit": "mountains_embrace", "bio": "Foreman of the Copperdeep miners. Her crew is still trapped below.",
    },
    "sol": {
        "name": "Sol", "title": "the Unremembered", "innate": "spirit", "world": "spirit",
        "base": {"hp": 60, "mp": 22, "str": 9, "def": 9, "mag": 12, "mdef": 13, "spd": 11, "dex": 10},
        "grow": {"hp": 20, "mp": 4.8, "str": 1.5, "def": 1.5, "mag": 2.2, "mdef": 2.3, "spd": 1.3, "dex": 1.4},
        "limit": "enlightenment", "bio": "A monk of Hallowmere who woke one morning unable to remember who he was trying to become.",
    },
    "vesper": {
        "name": "Vesper", "title": "Half-Faded", "innate": "void", "world": "void",
        "base": {"hp": 56, "mp": 20, "str": 9, "def": 8, "mag": 12, "mdef": 9, "spd": 14, "dex": 13},
        "grow": {"hp": 19, "mp": 4.4, "str": 1.5, "def": 1.3, "mag": 2.2, "mdef": 1.5, "spd": 1.8, "dex": 2.0},
        "limit": "fade", "bio": "A girl from Lastlight who watches herself from a few feet away. She can't remember her real name.",
    },
}

LIMITS = {
    "kindlers_wrath":    {"name": "Kindler's Wrath", "desc": "Strikes once for every element in your aura (at least once)."},
    "pit_fury":          {"name": "Pit Fury", "desc": "Four savage fire strikes on random foes."},
    "lighthouse_beam":   {"name": "Lighthouse Beam", "desc": "Water damage to all foes and heals the party."},
    "thousand_feathers": {"name": "Thousand Feathers", "desc": "Eight wind arrows rain on random foes."},
    "mountains_embrace": {"name": "Mountain's Embrace", "desc": "Party takes half damage for 3 turns; heals all."},
    "enlightenment":     {"name": "Enlightenment", "desc": "Fully heals and revives the whole party."},
    "fade":              {"name": "Fade", "desc": "A void strike that ignores all defenses."},
}

# ------------------------------------------------------------------ spells
# kind: dmg | heal | buff | revive | drain | hex
# target: one | all | ally | allies | self
SPELLS = {
    # fire
    "ember":       {"name": "Ember", "el": "fire", "kind": "dmg", "target": "one", "power": 1.0, "mp": 5, "lv": 1},
    "kindle":      {"name": "Kindle", "el": "fire", "kind": "buff", "stat": "str", "target": "ally", "power": 0.3, "mp": 8, "lv": 5, "desc": "Raises Strength."},
    "flare_wave":  {"name": "Flare Wave", "el": "fire", "kind": "dmg", "target": "all", "power": 0.72, "mp": 13, "lv": 10},
    "inferno":     {"name": "Inferno", "el": "fire", "kind": "dmg", "target": "one", "power": 2.0, "mp": 22, "lv": 18},
    # water
    "soothe":      {"name": "Soothe", "el": "water", "kind": "heal", "target": "ally", "power": 1.0, "mp": 6, "lv": 1},
    "splash":      {"name": "Splash", "el": "water", "kind": "dmg", "target": "one", "power": 1.0, "mp": 5, "lv": 2},
    "tidal_rush":  {"name": "Tidal Rush", "el": "water", "kind": "dmg", "target": "all", "power": 0.72, "mp": 13, "lv": 10},
    "rain_of_mercy": {"name": "Rain of Mercy", "el": "water", "kind": "heal", "target": "allies", "power": 0.7, "mp": 18, "lv": 13},
    "maelstrom":   {"name": "Maelstrom", "el": "water", "kind": "dmg", "target": "one", "power": 2.0, "mp": 22, "lv": 18},
    # wind
    "gust":        {"name": "Gust", "el": "wind", "kind": "dmg", "target": "one", "power": 1.0, "mp": 5, "lv": 1},
    "haste":       {"name": "Haste", "el": "wind", "kind": "buff", "stat": "spd", "target": "ally", "power": 0.4, "mp": 8, "lv": 5, "desc": "Raises Speed."},
    "cyclone":     {"name": "Cyclone", "el": "wind", "kind": "dmg", "target": "all", "power": 0.72, "mp": 13, "lv": 10},
    "tempest":     {"name": "Tempest", "el": "wind", "kind": "dmg", "target": "one", "power": 2.0, "mp": 22, "lv": 18},
    # stone
    "shard":       {"name": "Shard", "el": "stone", "kind": "dmg", "target": "one", "power": 1.0, "mp": 5, "lv": 1},
    "stoneskin":   {"name": "Stoneskin", "el": "stone", "kind": "buff", "stat": "def", "target": "ally", "power": 0.35, "mp": 8, "lv": 5, "desc": "Raises Defense and Magic Defense."},
    "quake":       {"name": "Quake", "el": "stone", "kind": "dmg", "target": "all", "power": 0.72, "mp": 13, "lv": 10},
    "avalanche":   {"name": "Avalanche", "el": "stone", "kind": "dmg", "target": "one", "power": 2.0, "mp": 22, "lv": 18},
    # spirit
    "mend":        {"name": "Mend", "el": "spirit", "kind": "heal", "target": "ally", "power": 1.0, "mp": 6, "lv": 1},
    "radiance":    {"name": "Radiance", "el": "spirit", "kind": "dmg", "target": "one", "power": 1.0, "mp": 5, "lv": 3},
    "revive":      {"name": "Revive", "el": "spirit", "kind": "revive", "target": "ally", "power": 0.4, "mp": 16, "lv": 8},
    "sanctify":    {"name": "Sanctify", "el": "spirit", "kind": "dmg", "target": "all", "power": 0.72, "mp": 13, "lv": 12},
    "judgment":    {"name": "Judgment", "el": "spirit", "kind": "dmg", "target": "one", "power": 2.2, "mp": 24, "lv": 20},
    # void
    "hex":         {"name": "Hex", "el": "void", "kind": "hex", "target": "one", "power": 0.9, "mp": 6, "lv": 1, "desc": "Damage and lowers Magic Defense."},
    "drain":       {"name": "Drain", "el": "void", "kind": "drain", "target": "one", "power": 0.9, "mp": 9, "lv": 5, "desc": "Steals HP."},
    "null_wave":   {"name": "Null Wave", "el": "void", "kind": "dmg", "target": "all", "power": 0.72, "mp": 13, "lv": 10},
    "oblivion":    {"name": "Oblivion", "el": "void", "kind": "dmg", "target": "one", "power": 2.2, "mp": 24, "lv": 20},
}

# ------------------------------------------------------------------ summons
SUMMONS = {
    "pyrestag":    {"name": "Pyrestag", "el": "fire", "mp": 26, "power": 1.6, "effect": "dmg",
                    "desc": "A stag whose antlers are a forest fire. Fire damage to all foes."},
    "marrowhale":  {"name": "Marrowhale", "el": "water", "mp": 28, "power": 1.4, "effect": "dmg_heal",
                    "desc": "A whale made of the sea's memory. Water damage to all, heals the party."},
    "galecrown":   {"name": "Galecrown Roc", "el": "wind", "mp": 26, "power": 1.5, "effect": "dmg_haste",
                    "desc": "A roc crowned in storm. Wind damage to all, hastes the party."},
    "basaltus":    {"name": "Old Basaltus", "el": "stone", "mp": 28, "power": 1.4, "effect": "dmg_guard",
                    "desc": "A tortoise older than mountains. Stone damage to all, guards the party."},
    "lanternmoth": {"name": "Lanternmoth", "el": "spirit", "mp": 30, "power": 1.3, "effect": "dmg_revive",
                    "desc": "A moth that carries lost lights home. Spirit damage, revives and heals."},
    "umbrahound":  {"name": "Umbra Hound", "el": "void", "mp": 28, "power": 1.5, "effect": "dmg_hex",
                    "desc": "A wolf made of a shadow's shadow. Void damage, weakens foes."},
    "aeon":        {"name": "Aeon, the Witness", "el": "spirit", "mp": 60, "power": 3.2, "effect": "dmg_fullheal",
                    "desc": "The eye that has watched every life. Overwhelming spirit damage, fully heals the party."},
    "nihil":       {"name": "Nihil, the Unmaker", "el": "void", "mp": 60, "power": 3.6, "effect": "dmg_pierce",
                    "desc": "What was here before anything. Void damage that ignores all defense."},
}

# ------------------------------------------------------------------ gear
# Gear stats scale with the level they were obtained at (stored per instance).
# kind: blade (Strength) | bow (Dexterity) | staff (Magic) | armor | acc
# q = quality multiplier
def gear(name, kind, el, q=1.0, bonus=None, desc="", price=1.0):
    return {"name": name, "kind": kind, "el": el, "q": q, "bonus": bonus or {}, "desc": desc, "price": price}

import content_gear as CG
GEAR, WORLD_GEAR_LISTS = CG.build()
WORLD_GEAR_NAMES = {w: CG.starter_set(l, GEAR) for w, l in WORLD_GEAR_LISTS.items()}

# ------------------------------------------------------------------ consumables & key items
ITEMS = {
    "potion":      {"name": "Potion", "kind": "use", "effect": "heal_pct", "v": 0.35, "price": 40, "target": "ally", "desc": "Restores 35% HP."},
    "hi_potion":   {"name": "Hi-Potion", "kind": "use", "effect": "heal_pct", "v": 0.7, "price": 120, "target": "ally", "desc": "Restores 70% HP."},
    "ether":       {"name": "Ether", "kind": "use", "effect": "mp_pct", "v": 0.4, "price": 110, "target": "ally", "desc": "Restores 40% MP."},
    "feather":     {"name": "Phoenix Feather", "kind": "use", "effect": "revive", "v": 0.35, "price": 200, "target": "ally", "desc": "Revives a fallen ally."},
    "elixir":      {"name": "Elixir", "kind": "use", "effect": "full", "v": 1.0, "price": 900, "target": "ally", "desc": "Fully restores HP and MP."},
    "stamina_tonic": {"name": "Stamina Tonic", "kind": "use", "effect": "boost", "stat": "spd", "v": 0.3, "price": 160, "target": "ally",
                      "desc": "+30% Speed for 5 battles. You'll glow."},
    "might_elixir":  {"name": "Elixir of Might", "kind": "use", "effect": "boost", "stat": "str", "v": 0.3, "price": 180, "target": "ally",
                      "desc": "+30% Strength for 5 battles. You'll glow."},
    "ward_elixir":   {"name": "Ironbark Draught", "kind": "use", "effect": "boost", "stat": "def", "v": 0.3, "price": 180, "target": "ally",
                      "desc": "+30% Defense & Magic Defense for 5 battles."},
    "sage_elixir":   {"name": "Sage's Draught", "kind": "use", "effect": "boost", "stat": "mag", "v": 0.3, "price": 180, "target": "ally",
                      "desc": "+30% Magic for 5 battles. You'll glow."},
    "keen_elixir":   {"name": "Hawkeye Drops", "kind": "use", "effect": "boost", "stat": "dex", "v": 0.3, "price": 160, "target": "ally",
                      "desc": "+30% Dexterity for 5 battles. You'll glow."},
    "smoke_bomb":    {"name": "Smoke Bomb", "kind": "use", "effect": "flee", "v": 1.0, "price": 60, "target": "none", "desc": "Escape from a normal battle."},
}

KEY_ITEMS = {
    "heart_fire":   {"name": "Fire Heartstone", "desc": "Warm again. Jealousy burned out."},
    "heart_water":  {"name": "Water Heartstone", "desc": "It no longer weeps."},
    "heart_wind":   {"name": "Wind Heartstone", "desc": "It hums like an open sky."},
    "heart_stone":  {"name": "Stone Heartstone", "desc": "Clean granite, no gold in it."},
    "heart_spirit": {"name": "Spirit Heartstone", "desc": "It is becoming something. Good."},
    "heart_void":   {"name": "Void Heartstone", "desc": "Quiet, but present."},
    "key_ash":      {"name": "Key of Ash", "desc": "One of two keys to the Throne of Nothing."},
    "key_bedrock":  {"name": "Key of Bedrock", "desc": "One of two keys to the Throne of Nothing."},
    "key_memory":   {"name": "Key of Memory", "desc": "One of two keys to the Sanctum of the Witness."},
    "key_breath":   {"name": "Key of Breath", "desc": "One of two keys to the Sanctum of the Witness."},
    "hestas_hammer": {"name": "Brannoc's Hammer", "desc": "A smith's hammer, handle worn to his grip."},
    "music_box":    {"name": "Little Music Box", "desc": "Plays three notes, then stops, like it's waiting."},
    "first_kite":   {"name": "Grandpa's First Kite", "desc": "Paper and reed. It still wants to fly."},
    "lucky_pick":   {"name": "Garrick's Lucky Pick", "desc": "Chipped. Lucky anyway."},
    "forge_bellows": {"name": "Great Bellows", "desc": "The lungs of Emberfall's forge."},
    "wind_bells":   {"name": "Wind-Bells of Kitefall", "desc": "They ring without wind now. Strange."},
    "glider_wings": {"name": "Glider-Wings", "desc": "Pip's wings. Patched, but whole."},
    "lighthouse_lens": {"name": "Lighthouse Lens", "desc": "It catches light even in the dark."},
    "true_name":    {"name": "A Name, Folded Small", "desc": "Vesper's name, written on paper. You don't read it."},
}

for k in GEAR:
    GEAR[k]["type"] = "gear"
for k in ITEMS:
    ITEMS[k]["type"] = "item"
for k in KEY_ITEMS:
    KEY_ITEMS[k]["type"] = "key"
    KEY_ITEMS[k]["kind"] = "key"

# ------------------------------------------------------------------ enemies
# Stats are multipliers on a "standard" creature of the scaled level.
TIERS = {
    "easy":   {"hp": 0.55, "atk": 0.72, "xp": 0.6, "gold": 0.6, "lv": -1},
    "medium": {"hp": 0.9,  "atk": 0.95, "xp": 1.0, "gold": 1.0, "lv": 0},
    "hard":   {"hp": 1.35, "atk": 1.18, "xp": 1.6, "gold": 1.5, "lv": 1},
    "mini":   {"hp": 4.6,  "atk": 1.26, "xp": 6.0, "gold": 5.0, "lv": 1},
    "boss":   {"hp": 7.0,  "atk": 1.36, "xp": 12.0, "gold": 10.0, "lv": 2},
    "omni":   {"hp": 19.0, "atk": 1.52,  "xp": 40.0, "gold": 30.0, "lv": 5},
    "king":   {"hp": 14.0, "atk": 1.45,  "xp": 50.0, "gold": 40.0, "lv": 3},
}

# def/mdef/spd/mag are relative; caster means it uses elemental spells
SPECIES = {
    # easy
    "rat":       {"name": "Rat", "tier": "easy", "def": 0.8, "mdef": 0.8, "spd": 1.2, "mag": 0.5, "caster": False, "size": "s"},
    "bum":       {"name": "Bum", "tier": "easy", "def": 0.9, "mdef": 0.9, "spd": 0.9, "mag": 0.5, "caster": False, "size": "m",
                  "skills": ["bottle_toss"]},
    "loiterer":  {"name": "Loiterer", "tier": "easy", "def": 0.9, "mdef": 1.0, "spd": 1.0, "mag": 0.6, "caster": False, "size": "m",
                  "skills": ["sucker_punch"]},
    "undead":    {"name": "Undead", "tier": "easy", "def": 1.0, "mdef": 0.7, "spd": 0.7, "mag": 0.8, "caster": True, "size": "m"},
    # medium
    "knight":    {"name": "Knight", "tier": "medium", "def": 1.45, "mdef": 0.75, "spd": 0.8, "mag": 0.5, "caster": False, "size": "m",
                  "skills": ["shield_bash"]},
    "elf":       {"name": "Elf", "tier": "medium", "def": 0.85, "mdef": 1.4, "spd": 1.2, "mag": 1.3, "caster": True, "size": "m"},
    "archer":    {"name": "Archer", "tier": "medium", "def": 0.9, "mdef": 1.0, "spd": 1.15, "mag": 0.6, "caster": False, "size": "m",
                  "skills": ["volley"]},
    "ghost":     {"name": "Ghost", "tier": "medium", "def": 2.2, "mdef": 0.7, "spd": 1.0, "mag": 1.1, "caster": True, "size": "m",
                  "note": "physical attacks barely touch it"},
    # hard
    "bear":      {"name": "Bear", "tier": "hard", "def": 1.15, "mdef": 0.9, "spd": 0.85, "mag": 0.4, "caster": False, "size": "l",
                  "skills": ["maul"]},
    "ogre":      {"name": "Ogre", "tier": "hard", "def": 1.0, "mdef": 0.8, "spd": 0.7, "mag": 0.5, "caster": False, "size": "l",
                  "skills": ["club_slam"]},
    "boar":      {"name": "Boar", "tier": "hard", "def": 1.1, "mdef": 0.9, "spd": 1.1, "mag": 0.4, "caster": False, "size": "l",
                  "skills": ["gore"]},
    "fknight":   {"name": "Future Knight", "tier": "hard", "def": 1.6, "mdef": 1.0, "spd": 0.95, "mag": 0.8, "caster": False, "size": "m",
                  "skills": ["plasma_cleave"]},
    "farcher":   {"name": "Future Archer", "tier": "hard", "def": 1.0, "mdef": 1.1, "spd": 1.3, "mag": 0.9, "caster": False, "size": "m",
                  "skills": ["laser_volley"]},
    # King Goblin's army (everywhere) and pirates (only near water)
    "goblin":    {"name": "Goblin", "tier": "easy", "def": 0.85, "mdef": 0.8, "spd": 1.25, "mag": 0.5, "caster": False, "size": "s",
                  "skills": ["goblin_stab"]},
    "goblin_shaman": {"name": "Goblin Shaman", "tier": "medium", "def": 0.8, "mdef": 1.3, "spd": 1.05, "mag": 1.35, "caster": True,
                      "size": "m"},
    "goblin_brute": {"name": "Goblin Brute", "tier": "hard", "def": 1.25, "mdef": 0.85, "spd": 0.9, "mag": 0.4, "caster": False,
                     "size": "l", "skills": ["brute_smash"]},
    "pirate":    {"name": "Pirate", "tier": "medium", "def": 1.0, "mdef": 0.9, "spd": 1.1, "mag": 0.5, "caster": False, "size": "m",
                  "skills": ["cutlass_flurry", "grog_toss"], "habitat": "coast"},
    "pirate_gunner": {"name": "Pirate Gunner", "tier": "hard", "def": 1.0, "mdef": 1.0, "spd": 1.0, "mag": 0.6, "caster": False,
                      "size": "m", "skills": ["cannon_shot"], "habitat": "coast"},
    "fbum":      {"name": "Future Bum", "tier": "hard", "def": 1.2, "mdef": 1.2, "spd": 1.0, "mag": 1.0, "caster": True, "size": "m",
                  "skills": ["cart_ram"]},
}

ENEMY_SKILLS = {
    "bottle_toss":   {"name": "Bottle Toss", "power": 1.1, "target": "one", "kind": "phys"},
    "sucker_punch":  {"name": "Sucker Punch", "power": 1.25, "target": "one", "kind": "phys"},
    "shield_bash":   {"name": "Shield Bash", "power": 1.0, "target": "one", "kind": "phys", "stun": 1},
    "volley":        {"name": "Volley", "power": 0.55, "target": "all", "kind": "phys"},
    "maul":          {"name": "Maul", "power": 1.5, "target": "one", "kind": "phys"},
    "club_slam":     {"name": "Club Slam", "power": 0.8, "target": "all", "kind": "phys"},
    "gore":          {"name": "Gore", "power": 1.6, "target": "one", "kind": "phys"},
    "plasma_cleave": {"name": "Plasma Cleave", "power": 0.75, "target": "all", "kind": "mag"},
    "laser_volley":  {"name": "Laser Volley", "power": 0.6, "target": "all", "kind": "mag"},
    "cart_ram":      {"name": "Shopping Cart Ram", "power": 1.4, "target": "one", "kind": "phys"},
    "goblin_stab":   {"name": "Sneaky Stab", "power": 1.3, "target": "one", "kind": "phys"},
    "brute_smash":   {"name": "Brute Smash", "power": 1.55, "target": "one", "kind": "phys"},
    "cutlass_flurry": {"name": "Cutlass Flurry", "power": 1.35, "target": "one", "kind": "phys"},
    "grog_toss":     {"name": "Grog Toss", "power": 1.1, "target": "one", "kind": "phys"},
    "cannon_shot":   {"name": "Cannon Shot", "power": 0.7, "target": "all", "kind": "phys"},
}

# Minibosses, bosses and omnipotents. "ai" is a list of moves picked by the battle AI.
# move kinds: attack | spell (el, power, target) | buff | dispel | heal | stun | silence | summon | steal_gold | drain | phase
def unique(name, sprite, el, tier, ai, **kw):
    d = {"name": name, "sprite": sprite, "el": el, "tier": tier, "ai": ai}
    d.update(kw)
    return d

UNIQUES = {
    # ---- companion quest minibosses
    "slagjaw": unique("Slagjaw the Pit Ogre", "ogre", "fire", "mini",
        [{"k": "attack", "w": 3}, {"k": "skill", "s": "club_slam", "w": 2}, {"k": "buff", "stat": "str", "w": 1, "say": "MORE! THE CROWD WANTS MORE!"}],
        size="xl", def_=1.1, mdef=0.8, spd=0.8),
    "gloomfin": unique("Gloomfin", "gloomfin", "water", "mini",
        [{"k": "attack", "w": 2}, {"k": "spell", "el": "water", "power": 0.8, "target": "all", "name": "Undertow", "w": 2},
         {"k": "silence", "w": 1, "name": "Lure-Light", "say": "The lure flickers... you forget the words."}],
        size="xl", def_=1.0, mdef=1.2, spd=1.0),
    "rook": unique("Captain Rook", "farcher", "wind", "mini",
        [{"k": "attack", "w": 2}, {"k": "skill", "s": "laser_volley", "w": 2}, {"k": "buff", "stat": "spd", "w": 1, "say": "Catch me if you can, groundlings!"}],
        size="l", def_=0.95, mdef=1.0, spd=1.4),
    "gravelmaw": unique("Gravelmaw", "gravelmaw", "stone", "mini",
        [{"k": "attack", "w": 2}, {"k": "spell", "el": "stone", "power": 0.75, "target": "all", "name": "Cave-In", "w": 2},
         {"k": "buff", "stat": "def", "w": 1, "say": "Gravelmaw burrows into the rock and hardens."}],
        size="xl", def_=1.5, mdef=0.9, spd=0.75),
    "mirror_wraith": unique("The Hollow Mirror", "mirror", "spirit", "mini",
        [{"k": "spell", "el": "spirit", "power": 1.0, "target": "one", "name": "Reflected Light", "w": 2},
         {"k": "spell", "el": "void", "power": 1.0, "target": "one", "name": "Reflected Dark", "w": 2},
         {"k": "dispel", "w": 1, "say": "\"Is that really you? Show me.\""}],
        size="l", def_=2.0, mdef=1.0, spd=1.0),
    "name_eater": unique("The Name-Eater", "name_eater", "void", "mini",
        [{"k": "attack", "w": 2}, {"k": "drain", "power": 1.0, "w": 2, "name": "Eat a Name"},
         {"k": "silence", "w": 1, "name": "Forget", "say": "\"What were you called again?\""}],
        size="xl", def_=1.0, mdef=1.0, spd=1.0),
    # ---- side quest minibosses
    "scrapjack": unique("Scrapjack", "fbum", "fire", "mini",
        [{"k": "attack", "w": 2}, {"k": "skill", "s": "cart_ram", "w": 2}, {"k": "steal_gold", "w": 1, "say": "\"Finders keepers!\""}],
        size="l", def_=1.2, mdef=1.1, spd=1.05),
    "drowned_captain": unique("The Drowned Captain", "ghost", "water", "mini",
        [{"k": "spell", "el": "water", "power": 1.0, "target": "one", "name": "Anchor Drop", "w": 2},
         {"k": "summon", "species": "ghost", "w": 1, "say": "\"All hands! ALL HANDS!\""}, {"k": "attack", "w": 1}],
        size="l", def_=2.2, mdef=0.8, spd=0.95),
    "sylvane": unique("Sylvane the Bell-Thief", "elf", "wind", "mini",
        [{"k": "spell", "el": "wind", "power": 1.0, "target": "one", "name": "Silent Gust", "w": 2},
         {"k": "spell", "el": "wind", "power": 0.7, "target": "all", "name": "Hush", "w": 2}, {"k": "silence", "w": 1, "name": "Stolen Chime"}],
        size="l", def_=0.9, mdef=1.4, spd=1.3),
    "iron_overseer": unique("The Iron Overseer", "fknight", "stone", "mini",
        [{"k": "attack", "w": 2}, {"k": "skill", "s": "plasma_cleave", "w": 2}, {"k": "stun", "w": 1, "name": "Quota Lash", "say": "\"Back to work.\""}],
        size="l", def_=1.7, mdef=1.0, spd=0.9),
    "penitent_bear": unique("The Penitent Bear", "bear", "spirit", "mini",
        [{"k": "attack", "w": 2}, {"k": "skill", "s": "maul", "w": 2}, {"k": "heal", "w": 1, "say": "The bear swallows a lantern and glows."}],
        size="xl", def_=1.2, mdef=1.0, spd=0.9),
    "mute_paladin": unique("The Mute Paladin", "knight", "void", "mini",
        [{"k": "attack", "w": 2}, {"k": "skill", "s": "shield_bash", "w": 2}, {"k": "silence", "w": 1, "name": "Oath of Silence"}],
        size="l", def_=1.6, mdef=0.9, spd=0.85),
    # ---- world bosses
    "vulkar": unique("Vulkar, the Green Flame", "vulkar", "fire", "boss",
        [{"k": "attack", "w": 2}, {"k": "spell", "el": "fire", "power": 1.1, "target": "one", "name": "Envious Brand", "w": 2},
         {"k": "spell", "el": "fire", "power": 0.75, "target": "all", "name": "Green Inferno", "w": 2},
         {"k": "dispel", "w": 1, "name": "Covet", "say": "\"That's MINE. Everything she had should have been MINE.\""}],
        size="boss", def_=1.1, mdef=1.0, spd=1.0, phases=[
            {"at": 0.5, "say": "\"Why did they always look at HER?\" The flames turn sickly green.", "buff": "str"}]),
    "maren": unique("Maren, Mother of Tides", "maren", "water", "boss",
        [{"k": "spell", "el": "water", "power": 0.75, "target": "all", "name": "Sorrow Tide", "w": 3},
         {"k": "drain", "power": 1.1, "w": 2, "name": "Grasp of Loss"}, {"k": "attack", "w": 1},
         {"k": "summon", "species": "ghost", "w": 1, "say": "\"Stay. Everyone stays. No one else leaves me.\""}],
        size="boss", def_=1.0, mdef=1.25, spd=0.95, phases=[
            {"at": 0.5, "say": "\"I kept the whole sea so I would never have to let go.\"", "buff": "mag"}]),
    "corvane": unique("Corvane, Keeper of Cages", "corvane", "wind", "boss",
        [{"k": "attack", "w": 2}, {"k": "spell", "el": "wind", "power": 0.75, "target": "all", "name": "Gale Lash", "w": 2},
         {"k": "stun", "w": 2, "name": "Gilded Cage", "turns": 2, "say": "\"Safer inside. Everyone is safer inside.\""}],
        size="boss", def_=1.0, mdef=1.0, spd=1.25, phases=[
            {"at": 0.45, "say": "Corvane's own cage cracks open. For a moment he looks... relieved.", "buff": "spd", "debuff_self": "def"}]),
    "ostrum": unique("King Ostrum, the Gilded", "ostrum", "stone", "boss",
        [{"k": "attack", "w": 2}, {"k": "spell", "el": "stone", "power": 0.75, "target": "all", "name": "Avalanche of Coin", "w": 2},
         {"k": "stun", "w": 1, "name": "Gild", "say": "\"Hold still. Gold doesn't flinch.\""},
         {"k": "steal_gold", "w": 1, "name": "Royal Tithe"}, {"k": "buff", "stat": "def", "w": 1, "name": "Gilded Skin"}],
        size="boss", def_=1.6, mdef=0.9, spd=0.8, phases=[
            {"at": 0.5, "say": "Gold drips from the cracks in the king. Underneath is ordinary stone.", "debuff_self": "def"}]),
    "iris": unique("Iris, the Unfinished", "iris", "spirit", "boss",
        [{"k": "spell", "el": "self", "power": 1.1, "target": "one", "name": "Sculpt", "w": 2},
         {"k": "spell", "el": "self", "power": 0.75, "target": "all", "name": "Potential", "w": 2},
         {"k": "shift", "w": 1, "say": "\"Not yet. I'm not finished. I'm never finished.\" Iris becomes something else."},
         {"k": "heal", "w": 1}],
        size="boss", def_=1.0, mdef=1.1, spd=1.05, shift=["spirit", "void"]),
    "nobody": unique("Nobody", "nobody", "void", "boss",
        [{"k": "attack", "w": 2}, {"k": "spell", "el": "void", "power": 0.75, "target": "all", "name": "Static", "w": 2},
         {"k": "silence", "w": 1, "name": "Numb"},
         {"k": "elsewhere", "w": 1, "say": "Nobody isn't here anymore. Your weapons pass through the place he was."}],
        size="boss", def_=1.0, mdef=1.0, spd=1.1),
    # ---- omnipotents
    "aeon": unique("Aeon, the Witness", "aeon", "spirit", "omni",
        [{"k": "spell", "el": "spirit", "power": 0.9, "target": "all", "name": "Gaze of Ages", "w": 3},
         {"k": "spell", "el": "spirit", "power": 1.5, "target": "one", "name": "Judgment", "w": 2},
         {"k": "dispel", "w": 1, "name": "Truth"}, {"k": "heal", "w": 1, "name": "Remembrance"},
         {"k": "stun", "w": 1, "name": "Behold", "say": "\"I have seen you before you were born.\""}],
        size="omni", def_=1.3, mdef=1.4, spd=1.15, phases=[
            {"at": 0.6, "say": "A thousand eyes open across the sky.", "buff": "mag"},
            {"at": 0.25, "say": "\"You have become. Show me who.\"", "buff": "spd"}]),
    "nihil": unique("Nihil, the Unmaker", "nihil", "void", "omni",
        [{"k": "spell", "el": "void", "power": 0.95, "target": "all", "name": "Event Horizon", "w": 3},
         {"k": "spell", "el": "void", "power": 1.6, "target": "one", "name": "Unmake", "w": 2},
         {"k": "drain", "power": 1.2, "w": 1, "name": "Consume"}, {"k": "silence", "w": 1, "name": "Unspeak"},
         {"k": "elsewhere", "w": 1, "say": "Nihil folds away from the world."}],
        size="omni", def_=1.4, mdef=1.3, spd=1.1, phases=[
            {"at": 0.6, "say": "The stars behind Nihil go out, one by one.", "buff": "mag"},
            {"at": 0.25, "say": "\"Before you, nothing. After you, nothing. Why fight?\"", "buff": "str"}]),
}

# Encounter pools by area kind: (tier weights) and group size
POOLS = {
    "field":   {"easy": 6, "medium": 4, "hard": 0, "size": [1, 3]},
    "cave":    {"easy": 3, "medium": 5, "hard": 2, "size": [2, 3]},
    "dungeon": {"easy": 1, "medium": 5, "hard": 4, "size": [2, 4]},
}

SHOP_ITEMS = ["potion", "hi_potion", "ether", "feather", "smoke_bomb",
              "stamina_tonic", "might_elixir", "ward_elixir", "sage_elixir", "keen_elixir"]


def export():
    return {
        "elements": ELEMENTS, "element_info": ELEMENT_INFO,
        "characters": CHARACTERS, "limits": LIMITS, "spells": SPELLS, "summons": SUMMONS,
        "gear": GEAR, "items": ITEMS, "key_items": KEY_ITEMS,
        "tiers": TIERS, "species": SPECIES, "enemy_skills": ENEMY_SKILLS, "uniques": UNIQUES,
        "pools": POOLS, "shop_items": SHOP_ITEMS, "world_gear": WORLD_GEAR_NAMES,
        "world_gear_lists": WORLD_GEAR_LISTS, "drop_table": CG.DROP_TABLE,
    }
