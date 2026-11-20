"""The Blessed (white-cloaked beings and their laser weapons) and the seven legendary treasure hunts.

Nothing here explains the Blessed. Their weapons, their words and the hunters' stories leave a trail
for the player to follow: salt, sulfur, quicksilver; black, white, red; lead that remembers being gold.
"""

# ------------------------------------------------------------------ Blessed weapons
# id: (name, kind, style, element, bonus, fx, description)
#   kind is the slot type the party already understands (blade / bow / staff); style picks the art.
BLESSED_GEAR = {
    "azoth_edge":        ("Azoth Edge", "blade", "blade", "spirit", {"str": 0.16, "mag": 0.08}, {"pierce": 0.35, "crit": 0.1},
                          "The blade isn't metal. It is the idea of cutting, held still."),
    "calcined_arcblade": ("Calcined Arcblade", "blade", "blade", "fire", {"str": 0.18, "spd": 0.06}, {"pierce": 0.35, "drain": 0.06},
                          "Burned until only the truth was left. Then burned again."),
    "quicksilver_saber": ("Quicksilver Saber", "blade", "blade", "water", {"str": 0.15, "dex": 0.1}, {"pierce": 0.35, "first": 30},
                          "It runs if you set it down. Keep a hand on it."),
    "rubedo_lancer":     ("Rubedo Assault Laser", "bow", "rifle", "fire", {"dex": 0.18, "str": 0.06}, {"pierce": 0.4, "crit": 0.12},
                          "The last color of the Work. It sings red when it fires."),
    "albedo_repeater":   ("Albedo Repeater", "bow", "rifle", "wind", {"dex": 0.16, "spd": 0.1}, {"pierce": 0.4, "first": 25},
                          "Washed white, then fired until it forgot what it was washed of."),
    "nigredo_pistol":    ("Nigredo Ray Pistol", "bow", "pistol", "void", {"dex": 0.15, "mag": 0.08}, {"pierce": 0.35, "drain": 0.06},
                          "Black first. It is always black first."),
    "cinnabar_pistol":   ("Cinnabar Sidearm", "bow", "pistol", "stone", {"dex": 0.14, "def": 0.08}, {"pierce": 0.35, "guard": 0.06},
                          "Red earth tamed into a spark. The grip is still warm from another hand."),
    "quintessence_coil": ("Quintessence Coil", "staff", "staff", "spirit", {"mag": 0.18, "mp": 0.1}, {"pierce": 0.3, "spell": 0.18},
                          "The fifth thing. The one that sits between the other four."),
    "athanor_staff":     ("Athanor Staff", "staff", "staff", "water", {"mag": 0.16, "mdef": 0.08}, {"pierce": 0.3, "regen": 0.03},
                          "A furnace small enough to carry. It has never once gone out."),
}

# ------------------------------------------------------------------ the Blessed themselves
# Uniques (so they keep their own names and moves). "blessed": they blink away from ordinary weapons.
def _b(name, sprite_style, el, ai, **kw):
    d = {"name": name, "sprite": "blessed_" + sprite_style, "el": el, "tier": "blessed", "ai": ai, "blessed": True, "style": sprite_style}
    d.update(kw)
    return d

BLESSED_UNIQUES = {
    "blessed_warden": _b("Blessed Warden", "blade", "spirit",
        [{"k": "attack", "w": 3, "name": "Arc Cut"}, {"k": "blink", "w": 1}, {"k": "skill", "s": "white_sweep", "w": 2}],
        size="m", def_=1.25, mdef=1.25, spd=1.25),
    "blessed_lancer": _b("Blessed Lancer", "rifle", "fire",
        [{"k": "skill", "s": "lance_beam", "w": 3}, {"k": "attack", "w": 1, "name": "Burst Fire"}, {"k": "blink", "w": 1}],
        size="m", def_=1.0, mdef=1.15, spd=1.15),
    "blessed_seraph": _b("Blessed Seraph", "staff", "spirit",
        [{"k": "spell", "el": "spirit", "power": 1.0, "target": "one", "name": "White Lance", "w": 2},
         {"k": "heal", "w": 1, "say": "A ring of light closes over the Blessed's wounds."}, {"k": "blink", "w": 1}],
        size="m", def_=0.95, mdef=1.5, spd=1.1, caster=True),
}
BLESSED_SKILLS = {
    "white_sweep": {"name": "White Sweep", "power": 0.7, "target": "all", "kind": "phys"},
    "lance_beam":  {"name": "Lance Beam", "power": 0.8, "target": "all", "kind": "mag"},
}
BLESSED_TIER = {"hp": 2.4, "atk": 1.3, "xp": 6.0, "gold": 6.0, "lv": 2}

# what they say (one line, at random, when they appear) — fragments, never explanations
BLESSED_LINES = [
    "The white figures don't speak. Their lenses turn toward you, one after another.",
    "A smell of salt and hot brass. Something hums under the white cloth.",
    "\"Lead remembers what it was.\"",
    "\"The Work is unfinished. You are part of the unfinished.\"",
    "\"Black. White. Red. Then gold.\"",
    "\"Solve. Coagula.\"",
    "They flicker, here and then a step to the left, as if the world can't decide where they stand.",
    "\"We were the base matter once. Be still. It hurts less.\"",
]
BLESSED_FIRST = ["Three figures in white step out of nothing. Where they stand, the grass bleaches pale.",
                 "One of them lifts a weapon of brass and glass. It hums like a held breath."]
# after a win, when their gear can be salvaged
BLESSED_SALVAGE = ["Among the white cloth there's a weapon still humming. It's warm, and it fits your hand too well.",
                   "The white cloth is empty. Only a brass weapon remains, its glass still lit from inside.",
                   "Their weapon doesn't break when they do. It waits, as if it had been waiting for you."]

# ------------------------------------------------------------------ the seven legendary hunts
# Each: the two seekers, their story (with the boss's weakness hidden in it), the boss, and their thanks.
HUNT_TIER = {"hp": 10.0, "atk": 1.45, "xp": 30.0, "gold": 0.0, "lv": 3}

def _hunt(seekers, looks, story, ask, accept, decline, boss, pre, post, thanks):
    return {"seekers": seekers, "looks": looks, "story": story, "ask": ask, "accept": accept, "decline": decline,
            "boss": boss, "pre": pre, "post": post, "thanks": thanks}

HUNTS = {
    "biscuit": _hunt(["Bram", "Tilly"],
        [{"body": "child", "hair": "#8a5a2a", "outfit": "#5a6a3a", "accent": "#d8c090", "skin": 1},
         {"body": "child", "hair": "#d8a050", "outfit": "#a04040", "accent": "#f0e0a0", "skin": 1}],
        ["TILLY: \"Mister! Have you seen a ferret? White, with one brown ear? His name's Biscuit.\"",
         "BRAM: \"Something took him. It came down the hill so fast the grass didn't even bend. Just a blur and a squeal.\"",
         "TILLY: \"I hit it with my slingshot. Just once. It screamed like I'd cut it in half and dropped Biscuit's collar.\"",
         "BRAM: \"It's living in the old fox den. There's a treasure pile in there too, we saw it glinting. Shiny stuff, real shiny.\""],
        "Help Bram and Tilly get Biscuit back? (They'll split the treasure with you.)",
        ["BRAM: \"Really?! It's out here somewhere. Look for where the grass is all flattened.\"",
         "TILLY: \"You don't have to hit it hard. Just hit it.\""],
        ["TILLY: \"...Okay. We'll keep looking ourselves.\""],
        {"id": "quickfang", "name": "Quickfang", "el": "wind", "sprite": "quickfang",
         "ai": [{"k": "attack", "w": 3, "name": "Blur Bite"}, {"k": "attack", "w": 2, "name": "Thousand Nips"},
                {"k": "buff", "stat": "spd", "w": 1, "say": "Quickfang darts in circles, faster and faster."}],
         "size": "l", "def_": 0.5, "mdef": 0.5, "spd": 3.2, "hp_mul": 0.12, "atk_mul": 0.85},
        ["A white weasel the size of a wolf, eyes like wet glass. A ferret's collar hangs from its teeth.",
         "It's gone before you can blink. Then it's behind you."],
        ["Quickfang squeals and folds up like a wet rag. A white ferret scrambles out of the den, very annoyed."],
        ["TILLY: \"BISCUIT!\" The ferret climbs up her sleeve and sulks.",
         "BRAM: \"The treasure's all yours, mister. Well, half. Okay, MOST. Biscuit's all we wanted.\""]),

    "music_box": _hunt(["Odo", "Merrin"],
        [{"body": "elder", "hair": "#e0e0e0", "outfit": "#4a5a6a", "accent": "#c0a060", "skin": 0, "beard": True},
         {"body": "elder", "hair": "#f0f0f0", "outfit": "#7a4a5a", "accent": "#e0c0a0", "skin": 0}],
        ["MERRIN: \"Fifty years, our music box played us to sleep. Odo carved it for me the week we married.\"",
         "ODO: \"A great shelled beast swallowed it whole. Then our cart. Then most of the fence.\"",
         "MERRIN: \"It's the slowest creature alive. We walked away from it eating breakfast, and it still hadn't reached us by lunch.\"",
         "ODO: \"I hit it with my hammer. The hammer broke. But when Merrin sang the old spell-songs at it, it groaned and its shell went soft.\"",
         "MERRIN: \"It sleeps on a hoard. Old soldiers' gear, coins, a whole lifetime of shiny things it ate.\""],
        "Help Odo and Merrin get their music box back? (They'll split the hoard with you.)",
        ["ODO: \"Don't hurry. It certainly won't.\"", "MERRIN: \"Sing to it, dear. Magic, I mean. Swords just annoy it.\""],
        ["MERRIN: \"Of course. We'll wait. We've gotten good at waiting.\""],
        {"id": "ironshell", "name": "The Ironshell", "el": "stone", "sprite": "ironshell",
         "ai": [{"k": "attack", "w": 2, "name": "Crushing Bite"}, {"k": "skill", "s": "club_slam", "w": 1},
                {"k": "doze", "w": 2, "say": "The Ironshell blinks, very slowly. It seems to have forgotten what it was doing."}],
         "size": "xl", "def_": 4.0, "mdef": 0.35, "spd": 0.22, "hp_mul": 1.1, "atk_mul": 1.5},
        ["A tortoise as big as a house, shell plated with swallowed iron. Somewhere inside it, faintly, a music box is playing."],
        ["The Ironshell sighs, a long tired sound, and coughs up a fence post, a cart wheel... and a small carved box."],
        ["MERRIN: \"Oh, listen, Odo. It still plays.\"", "ODO: \"Take the rest. We've got all we need now.\""]),

    "ring": _hunt(["Hal", "Junie"],
        [{"body": "man", "hair": "#2a1a12", "outfit": "#5a3a2a", "accent": "#c0a060", "skin": 3},
         {"body": "woman", "hair": "#4a3020", "outfit": "#e0d0b0", "accent": "#a04040", "skin": 2}],
        ["JUNIE: \"We were going to be married at the spring festival. Hal saved two years for the ring.\"",
         "HAL: \"A glittering serpent took it right off the table. It bit straight through my shield like it was bread.\"",
         "JUNIE: \"But Hal threw a rock at it and its whole tail chipped off. It's made of glass, I swear. Gorgeous and awful.\"",
         "HAL: \"It keeps a nest of stolen jewelry. If you help, we'll share it. I just want the ring.\""],
        "Help Hal and Junie get their ring back? (They'll share the nest's treasure.)",
        ["HAL: \"Don't let it bite you. It will hurt. A lot.\"", "JUNIE: \"Hit it first, and hit it hard.\""],
        ["HAL: \"Yeah. I wouldn't fight it either.\""],
        {"id": "glass_wyrm", "name": "The Glass Wyrm", "el": "water", "sprite": "glass_wyrm",
         "ai": [{"k": "attack", "w": 2, "name": "Shatterfang"}, {"k": "skill", "s": "brute_smash", "w": 2},
                {"k": "spell", "el": "water", "power": 1.0, "target": "all", "name": "Prism Spray", "w": 1}],
         "size": "xl", "def_": 0.12, "mdef": 0.3, "spd": 1.3, "hp_mul": 0.55, "atk_mul": 2.4},
        ["A serpent of clear glass, light breaking into colors along its coils. A gold ring glints deep in its belly."],
        ["The Glass Wyrm cracks from tail to fang and falls apart like a dropped chandelier. A gold ring rolls to your boots."],
        ["JUNIE: \"Hal. Hal, it's not even scratched.\"", "HAL: \"The festival's back on. Take your share, you've earned the whole nest.\""]),

    "doll": _hunt(["Nim", "Pell"],
        [{"body": "child", "hair": "#2a1a12", "outfit": "#3a5a7a", "accent": "#f0e0a0", "skin": 4},
         {"body": "child", "hair": "#c04030", "outfit": "#6a4a2a", "accent": "#e0c0a0", "skin": 0}],
        ["NIM: \"My doll's name is Lady Button. She has one eye and a very good hat.\"",
         "PELL: \"She was in a treasure chest we found. Except the chest had teeth. And it ate her.\"",
         "NIM: \"We camped by it all night, crying. When the campfire popped and a spark hit it, it SCREAMED and ran off on little legs.\"",
         "PELL: \"It's full of treasure. Real treasure. And Lady Button. Mostly Lady Button.\""],
        "Help Nim and Pell rescue Lady Button? (They'll share whatever's inside the chest.)",
        ["PELL: \"It's tough. Really, really tough. Our sticks just went boing.\"", "NIM: \"But it hates fire. Remember the fire.\""],
        ["NIM: \"...Lady Button will understand.\""],
        {"id": "gilded_mimic", "name": "The Gilded Mimic", "el": "wind", "sprite": "gilded_mimic",
         "ai": [{"k": "attack", "w": 2, "name": "Lid Slam"}, {"k": "steal_gold", "w": 1, "name": "Gobble", "say": "\"MINE,\" says the chest."},
                {"k": "skill", "s": "brute_smash", "w": 2}, {"k": "buff", "stat": "def", "w": 1, "say": "The Mimic snaps its lid shut and hunkers down."}],
         "size": "l", "def_": 2.6, "mdef": 2.0, "spd": 0.9, "hp_mul": 1.2, "atk_mul": 1.2, "weak_mult": 3.5},
        ["A treasure chest on spider legs, gilded and grinning. A small one-eyed doll peers out from between its teeth."],
        ["The Gilded Mimic bursts open in a shower of coins and splinters. Lady Button lands hat-first in the grass."],
        ["NIM: \"Lady Button! Your hat's fine!\"", "PELL: \"You can have the treasure. All of it. We just wanted her back.\""]),

    "hat": _hunt(["Gorrin", "Wil"],
        [{"body": "elder", "hair": "#c0c0c0", "outfit": "#5a4a3a", "accent": "#8a6a4a", "skin": 2, "hat": "wide"},
         {"body": "man", "hair": "#8a5a2a", "outfit": "#4a5a4a", "accent": "#c0a060", "skin": 2}],
        ["WIL: \"My grandpa's lucky hat. He's worn it through three wars and a bad marriage.\"",
         "GORRIN: \"A big silver moth came down out of the moon and took it. Took it right off my head!\"",
         "WIL: \"I'm a fair hand at spells. Every one I threw bounced straight back and singed my own eyebrows off.\"",
         "GORRIN: \"So I whacked it with a frying pan, and it fell right out of the air. Moths. Soft as butter, under all that shine.\"",
         "WIL: \"It's got a nest full of shiny things. Bring the hat home and you can have the rest.\""],
        "Help Gorrin and Wil get the lucky hat back? (They'll give you the rest of the nest.)",
        ["GORRIN: \"Leave the magic at home. Bring a pan.\"", "WIL: \"Or a sword. A sword's basically a sharp pan.\""],
        ["GORRIN: \"Hmph. Luck's gone anyway, I suppose.\""],
        {"id": "mirror_moth", "name": "The Mirror Moth", "el": "spirit", "sprite": "mirror_moth",
         "ai": [{"k": "spell", "el": "spirit", "power": 1.1, "target": "all", "name": "Moon Dust", "w": 2},
                {"k": "silence", "w": 1, "name": "Silver Glare"}, {"k": "attack", "w": 1, "name": "Wing Slap"}],
         "size": "xl", "def_": 0.28, "mdef": 4.5, "spd": 1.2, "hp_mul": 0.9, "atk_mul": 1.4},
        ["A moth with mirror-bright wings wide as a barn door. A battered old hat is stuck to one of its legs."],
        ["The Mirror Moth's wings crack like ice on a pond. The hat drifts down and lands perfectly on Gorrin's head."],
        ["GORRIN: \"Ha! Luck's back!\"", "WIL: \"Take the rest, please. And thank you for saving my eyebrows. What's left of them.\""]),

    "flock": _hunt(["Corin", "Dale"],
        [{"body": "man", "hair": "#d8a050", "outfit": "#7a6a3a", "accent": "#d8c090", "skin": 1, "hat": "wide"},
         {"body": "man", "hair": "#d8a050", "outfit": "#6a5a3a", "accent": "#a08040", "skin": 1, "beard": True}],
        ["CORIN: \"Forty sheep we had. Now we've got eleven, a dog, and nightmares.\"",
         "DALE: \"Something huge and woolly eats them whole. We should run, but it doesn't even chase. It just eats, and then it naps.\"",
         "CORIN: \"Naps right in the middle of a fight. I watched it fall asleep with a ewe halfway in its mouth.\"",
         "DALE: \"It gets fatter and meaner with every one. But it takes its sweet time between bites.\"",
         "CORIN: \"There's a lot of coin and gear from the shepherds who tried before us. Help us, and it's yours to share.\""],
        "Help Corin and Dale stop the beast eating their flock? (They'll share what the other shepherds left.)",
        ["DALE: \"Hit it while it sleeps. That's what I'd do, if I were brave.\"", "CORIN: \"You'll want to finish it fast. It heals while it eats.\""],
        ["CORIN: \"Eleven sheep. Ten by tomorrow, probably.\""],
        {"id": "woolgorger", "name": "The Woolgorger", "el": "stone", "sprite": "woolgorger",
         "ai": [{"k": "attack", "w": 2, "name": "Gulp"}, {"k": "skill", "s": "brute_smash", "w": 1},
                {"k": "heal", "w": 1, "say": "The Woolgorger chews something woolly and looks very pleased."},
                {"k": "doze", "w": 3, "say": "The Woolgorger yawns enormously... and falls asleep."}],
         "size": "xl", "def_": 1.6, "mdef": 1.4, "spd": 0.8, "hp_mul": 1.6, "atk_mul": 2.0},
        ["A mountain of dirty wool with a mouth. Bells from a dozen lost sheep clank around its neck."],
        ["The Woolgorger sags over with a final enormous snore and doesn't get up. Somewhere underneath, a sheep bleats."],
        ["DALE: \"We're down to eleven sheep, but we've got eleven sheep!\"", "CORIN: \"Take the shepherds' gear. They'd want it used.\""]),

    "lantern": _hunt(["Ama", "Ivy"],
        [{"body": "woman", "hair": "#1a1010", "outfit": "#3a2a4a", "accent": "#e0c060", "skin": 3},
         {"body": "child", "hair": "#1a1010", "outfit": "#4a3a5a", "accent": "#f0e0a0", "skin": 3}],
        ["IVY: \"Our little brother made a lantern for the night market. It was the brightest one there.\"",
         "AMA: \"A shadow took it. A real shadow, standing up on its own, with yellow eyes. It moves faster than you can turn your head.\"",
         "IVY: \"It hits so hard. But when Ama lit a prayer candle, it flinched like the light was burning it.\"",
         "AMA: \"It hoards every light it steals. Lanterns, lamps, gold, glass. Help us, and you can share whatever's in its dark.\""],
        "Help Ama and Ivy get their brother's lantern back? (They'll share the shadow's hoard.)",
        ["AMA: \"Bring light. Holy light, if you have it.\"", "IVY: \"And don't let it hit you first.\""],
        ["IVY: \"He made it out of paper and a jam jar. He'll make another. ...He'll cry first.\""],
        {"id": "lamp_shade", "name": "The Lantern Thief", "el": "void", "sprite": "lamp_shade",
         "ai": [{"k": "attack", "w": 2, "name": "Night Claw"}, {"k": "spell", "el": "void", "power": 1.2, "target": "all", "name": "Swallow the Light", "w": 2},
                {"k": "drain", "power": 1.0, "w": 1, "name": "Snuff"}],
         "size": "xl", "def_": 1.3, "mdef": 1.3, "spd": 2.0, "hp_mul": 0.8, "atk_mul": 1.8, "weak_mult": 3.5},
        ["A shadow stands up out of the ground, taller than any man. In its claws, a little paper lantern still glows."],
        ["The Lantern Thief comes apart like smoke in sunlight. A paper lantern bobs gently to the ground, still lit."],
        ["IVY: \"It's still lit. It's still LIT!\"", "AMA: \"Take the rest of the hoard. We only came for this one light.\""]),
}

# the weakness a hunt boss is built around, for the game's notes (the hunters only hint at it)
HUNT_WEAK_EL = {"gilded_mimic": "fire", "lamp_shade": "spirit"}

# what the hoard holds (rolled when you win): gold range and how many pieces of each kind
HUNT_REWARD = {"gold": [999, 9999], "weapons": 1, "armor": 1, "acc": 1, "items": [["elixir", 2], ["hi_potion", 3], ["ether", 2]]}
