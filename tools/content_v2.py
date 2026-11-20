"""Six Hearths v2 content: second areas, taverns, house residents, side dungeons, tavern food, new minibosses."""
from content_worlds import br, npc, look, quest, QUESTS

LAYOUT = {
    # town border, field cliffs, area-2 name/style/cliffs, side dungeon (name, entrance), music mood of interiors
    "fire":   {"border": "cliff", "field_cliffs": 2, "area2": ("Magma Tunnels", "underground", 0),
               "side": ("Brannoc's Vault", "house3"), "tavern": "The Bellows & Barrel"},
    "water":  {"border": "trees", "field_cliffs": 0, "area2": ("Weeping Falls", "outdoor", 1),
               "side": ("Grotto Behind the Falls", "waterfall"), "tavern": "The Salted Gull"},
    "wind":   {"border": "trees", "field_cliffs": 1, "area2": ("Cloud Steppes", "outdoor", 2),
               "side": ("The Old Belfry", "house4"), "tavern": "The Tangled String"},
    "stone":  {"border": "cliff", "field_cliffs": 1, "area2": ("Old Mine Shaft", "underground", 0),
               "side": ("The Forgotten Tunnel", "house3"), "tavern": "The Honest Tankard"},
    "spirit": {"border": "trees", "field_cliffs": 1, "area2": ("Lantern Stair", "outdoor", 2),
               "side": ("The Quiet Crypt", "house3"), "tavern": "The Last Candle"},
    "void":   {"border": "trees", "field_cliffs": 0, "area2": ("The Underside", "underground", 0),
               "side": ("The Room That Isn't", "house4"), "tavern": "The Somewhere"},
}

# ------------------------------------------------------------------ tavern food & drink (stat boosts)
TAVERN_ITEMS = {
    "fire": [("ember_stew", "Ember Stew", "str", 70, "Spicy enough to make you brave. +30% Strength for 4 battles."),
             ("cinder_cider", "Cinder Cider", "spd", 60, "Fizzes like sparks. +30% Speed for 4 battles."),
             ("forge_pie", "Forge-Baked Pie", "full", 150, "Baked in the great forge. Fully restores one ally.")],
    "water": [("deep_chowder", "Chowder of the Deep", "mag", 70, "Briny and wise. +30% Magic for 4 battles."),
              ("salt_tea", "Sea-Salt Tea", "def", 60, "Steadies you like a keel. +30% Defense for 4 battles."),
              ("captains_platter", "Captain's Platter", "full", 150, "A sailor's feast. Fully restores one ally.")],
    "wind": [("skyberry_tart", "Sky-Berry Tart", "spd", 70, "Light as air. +30% Speed for 4 battles."),
             ("updraft_ale", "Updraft Ale", "dex", 60, "Sharpens the eye. +30% Dexterity for 4 battles."),
             ("kite_feast", "Kite-Festival Feast", "full", 150, "Kitefall's holiday plate. Fully restores one ally.")],
    "stone": [("miner_pasty", "Miner's Pasty", "def", 70, "Dense enough to stop an arrow. +30% Defense for 4 battles."),
              ("copper_stout", "Copperdeep Stout", "str", 60, "Thick, dark, honest. +30% Strength for 4 battles."),
              ("lode_roast", "Lode Roast", "full", 150, "Slow-roasted in a mine oven. Fully restores one ally.")],
    "spirit": [("lantern_bread", "Lantern Bread", "mag", 70, "Glows a little when torn. +30% Magic for 4 battles."),
               ("dawn_tea", "Dawn Tea", "dex", 60, "Tastes like the first light. +30% Dexterity for 4 battles."),
               ("pilgrim_supper", "Pilgrim's Supper", "full", 150, "Simple and complete. Fully restores one ally.")],
    "void": [("something_soup", "Soup of Something", "spd", 70, "Nobody knows what's in it. +30% Speed for 4 battles."),
             ("starless_nectar", "Starless Nectar", "mag", 60, "Dark and sweet. +30% Magic for 4 battles."),
             ("remembering_meal", "A Remembering Meal", "full", 150, "Grandmother's recipe, probably. Fully restores one ally.")],
}


def tavern_item_defs():
    out = {}
    for w, rows in TAVERN_ITEMS.items():
        for iid, name, stat, price, desc in rows:
            if stat == "full":
                out[iid] = {"name": name, "kind": "use", "effect": "full", "v": 1.0, "price": price, "target": "ally", "desc": desc}
            else:
                out[iid] = {"name": name, "kind": "use", "effect": "boost", "stat": stat, "v": 0.3, "n": 4, "price": price,
                            "target": "ally", "desc": desc}
    return out


# ------------------------------------------------------------------ side dungeon minibosses
def _u(name, sprite, el, ai, **kw):
    d = {"name": name, "sprite": sprite, "el": el, "tier": "mini", "ai": ai}
    d.update(kw)
    return d


NEW_UNIQUES = {
    "ember_rat_king": _u("The Ember Rat King", "rat_king", "fire",
        [{"k": "attack", "w": 2}, {"k": "summon", "species": "rat", "w": 1, "say": "\"My children! My hungry children!\""},
         {"k": "spell", "el": "fire", "power": 0.7, "target": "all", "name": "Cinder Swarm", "w": 2}],
        size="xl", def_=1.1, mdef=0.9, spd=1.1),
    "falls_guardian": _u("The Falls Guardian", "falls_guardian", "water",
        [{"k": "attack", "w": 2}, {"k": "spell", "el": "water", "power": 0.75, "target": "all", "name": "Cascade", "w": 2},
         {"k": "buff", "stat": "def", "w": 1, "say": "Water pours over the guardian's stone shell."}],
        size="xl", def_=1.5, mdef=1.1, spd=0.8),
    "storm_harpy": _u("The Storm Harpy", "storm_harpy", "wind",
        [{"k": "attack", "w": 2}, {"k": "spell", "el": "wind", "power": 0.75, "target": "all", "name": "Bell-Shriek", "w": 2},
         {"k": "steal_gold", "w": 1, "say": "\"Shiny! Mine!\""}],
        size="l", def_=0.9, mdef=1.0, spd=1.45),
    "rustbiter": _u("Rustbiter", "rustbiter", "stone",
        [{"k": "attack", "w": 2}, {"k": "drain", "power": 1.0, "w": 2, "name": "Iron Hunger"},
         {"k": "skill", "s": "club_slam", "w": 1}],
        size="xl", def_=1.7, mdef=0.8, spd=0.85),
    "lantern_wraith": _u("The Lantern Wraith", "lantern_wraith", "spirit",
        [{"k": "spell", "el": "spirit", "power": 1.0, "target": "one", "name": "Pale Flame", "w": 2},
         {"k": "silence", "w": 1, "name": "Hush of the Crypt"}, {"k": "heal", "w": 1, "say": "The wraith's lantern brightens."}],
        size="l", def_=1.0, mdef=1.4, spd=1.05),
    "the_lingering": _u("The Lingering", "lingering", "void",
        [{"k": "attack", "w": 1}, {"k": "drain", "power": 1.0, "w": 2, "name": "Hold On"},
         {"k": "spell", "el": "void", "power": 0.75, "target": "all", "name": "Never Leave", "w": 2}],
        size="xl", def_=1.1, mdef=1.2, spd=1.0),
}

SIDE2 = {
    "fire": {"mini": "ember_rat_king", "quest": "side2_fire", "title": "The Smith's Vault",
             "desc": "Something gnaws beneath Widow Hesta's house. Brannoc's old vault has been taken by a king of ember rats.",
             "pre": ["A heap of glowing rats writhes on a throne of stolen tools. It wears a thimble for a crown.",
                     "EMBER RAT KING: \"Every tool down here is MINE now. The old smith's hoard! Mine!\""],
             "post": ["The rat king scatters into a hundred tiny, fleeing embers.",
                      "Brannoc's tools lie quiet again, finally cool."]},
    "water": {"mini": "falls_guardian", "quest": "side2_water", "title": "Behind the Water",
              "desc": "A door hides behind the Weeping Falls. A stone guardian has kept it for a century.",
              "pre": ["A figure of mossy stone stands up out of the pool. Water pours endlessly from its shoulders.",
                      "GUARDIAN: \"Turn back. What is behind the falls was hidden for a reason.\""],
              "post": ["The guardian sinks back into the pool, its water finally still.",
                       "GUARDIAN: \"...Then carry it gently. It was someone's.\""]},
    "wind": {"mini": "storm_harpy", "quest": "side2_wind", "title": "The Belfry Thief",
             "desc": "A harpy has made the old bell tower her nest and steals every kite that flies past.",
             "pre": ["A harpy perched on the great bell screeches. Her nest is woven entirely from kite strings.",
                     "HARPY: \"Mine, mine, all the pretty strings are MINE!\""],
             "post": ["The harpy flees through the belfry window, leaving the kites behind.",
                      "The bell rings once in the wind, like it's saying thank you."]},
    "stone": {"mini": "rustbiter", "quest": "side2_stone", "title": "Something Eats the Props",
              "desc": "Mine props keep vanishing. Something under the old house is eating iron, and the tunnel will collapse.",
              "pre": ["A huge armored worm coils around a pile of chewed mine-props. Rust flakes off its jaws.",
                      "It turns toward the smell of your weapons."],
              "post": ["Rustbiter curls up and goes still. Its shell is full of half-digested iron.",
                       "The tunnel creaks, then holds. Copperdeep is safe again."]},
    "spirit": {"mini": "lantern_wraith", "quest": "side2_spirit", "title": "The Quiet Crypt",
               "desc": "Beneath the chapter house is a crypt nobody visits. Lately, a light walks there at night.",
               "pre": ["A hooded wraith drifts between the tombs, carrying a lantern that burns white.",
                       "WRAITH: \"Shh. They're sleeping. They were never finished. Neither am I.\""],
               "post": ["The wraith sets its lantern down gently on a tomb, and fades.",
                        "The crypt feels warmer. Like someone finally left a light on."]},
    "void": {"mini": "the_lingering", "quest": "side2_void", "title": "The Room That Isn't",
             "desc": "There's a door upstairs in an empty house that opens onto a room that shouldn't exist.",
             "pre": ["Something made of half-remembered faces fills the room. It doesn't want you to go.",
                     "THE LINGERING: \"Stay. Stay. Everyone always leaves. You stay.\""],
             "post": ["The Lingering loosens, the faces drifting off one by one like smoke.",
                      "The room is just a room now. It even has a window."]},
}

# legendary rewards are filled in by build_data from the catalog (what's still unplaced)


def side2_giver(w, nid, name, lk, reward_line):
    S = SIDE2[w]
    q, flag = S["quest"], "beat_" + S["mini"]
    return npc(nid, name, "patron1", lk, [
        br([f"q:{q}=none"], S["intro"], [f"quest:{q}"]),
        br([f"q:{q}=active"], S["hint"]),
        br([f"q:{q}=ready"], S["thanks"] + [reward_line], [f"done:{q}", "give:gear:{REWARD}", "gold:300", "sfx:chest"]),
        br([f"q:{q}=done"], S["after"]),
    ])


SIDE2_TALK = {
    "fire": {"giver": ("orrin", "Old Furnace-Hand Orrin", look("elder", "#a0a0a0", "#5a3a2a", "#e08030", 2, beard=True)),
             "intro": ["Brannoc built a vault under his house, you know. Kept his best work down there.",
                       "Since he passed, something's moved in. Rats. Big ones. And they glow.",
                       "Hesta can't sleep for the gnawing. Her house is the one with the little garden, south side.",
                       "The cellar stairs are in the corner. Clear it out and I'll pay you in something better than gold."],
             "hint": ["The cellar stairs are in the corner of Hesta's house. Watch for the one with the crown."],
             "thanks": ["The gnawing's stopped? Ha! Hesta will sleep tonight.", "Brannoc wanted his best piece to go to someone who'd use it."],
             "after": ["Brannoc's vault is quiet. Good. Some places should be."]},
    "water": {"giver": ("linnea", "Fisher Linnea", look("woman", "#c07040", "#3a6a5a", "#f0e0a0", 1, hat="wide")),
              "intro": ["My grandmother swore there's a door behind the Weeping Falls. North of the Shoals.",
                        "You can walk along the ledge right behind the water. Look for the seam in the rock.",
                        "She said a guardian of stone keeps it. Bring me back proof and I'll give you her old charm."],
              "hint": ["Walk the ledge behind the Weeping Falls. The door is right in the middle."],
              "thanks": ["You found it! Grandmother wasn't just telling stories.", "Here. She'd want it to keep going places."],
              "after": ["I'm going to go see the falls myself. From the outside, though."]},
    "wind": {"giver": ("tess", "Kite-Maker Tess", look("woman", "#f0d060", "#c05a8a", "#40b0a0", 0)),
             "intro": ["Every kite I make, gone! Snatched right out of the sky!",
                       "There's a harpy in the old belfry. The stairs are in the empty house on the east side.",
                       "Get my kites back and I'll give you something that really flies."],
             "hint": ["The belfry stairs are in the empty house on the east side."],
             "thanks": ["My kites! And the strings are only a little chewed!", "Here, take this. You earned the sky."],
             "after": ["The sky's full of kites again. Look up sometime."]},
    "stone": {"giver": ("bram_s", "Foreman Gutch", look("man", "#4a3a2a", "#5a5a3a", "#d0a040", 2, hat="helm", beard=True)),
              "intro": ["Props are going missing. Iron ones. Bitten clean through.",
                        "There's an old tunnel under the house on the south side. Whatever's eating the iron is down there.",
                        "Kill it before the whole street falls in. The union will make it worth your while."],
              "hint": ["The tunnel starts in the cellar of the south-side house. Mind the rust."],
              "thanks": ["It's dead? Props are holding. You saved the street.", "Union pays its debts. Take this."],
              "after": ["Not one prop lost since. You're an honorary miner now."]},
    "spirit": {"giver": ("ysolde", "Sister Ysolde", look("robe", "#2a2a2a", "#e0e0f0", "#d0b050", 1, hat="hood")),
               "intro": ["There's a crypt under the chapter house. We stopped going down years ago.",
                         "Now a light walks there at night. The novices are frightened.",
                         "Will you go down and see what it wants? The stairs are in the house south of the plaza."],
               "hint": ["The crypt stairs are in the south house. Bring something bright."],
               "thanks": ["It's quiet now. Thank you for being gentle with it.", "This was on the altar for a hundred years. It wants to go with you."],
               "after": ["I went down today and lit a candle. It felt right."]},
    "void": {"giver": ("aldwin", "Lamplighter Aldwin", look("man", "#d0d0d0", "#3a3050", "#c090ff", 0, hat="cap")),
             "intro": ["The empty house on the east side. Upstairs. There's a door to a room that isn't there.",
                       "I measured it. The house is too small for that room.",
                       "Something lives in it and it wants company. Go up and tell it no for me."],
             "hint": ["Upstairs in the east house. Don't stay longer than you have to."],
             "thanks": ["You came back! People don't always, from that room.", "Take this. I found it on my doorstep after. I think it's a thank-you."],
             "after": ["The east house has a window now. On the room that isn't. Strange, but nicer."]},
}
for _w, _t in SIDE2_TALK.items():
    SIDE2[_w].update({k: v for k, v in _t.items() if k != "giver"})
    quest(SIDE2[_w]["quest"], SIDE2[_w]["title"], _w, "side", _t["giver"][1], SIDE2[_w]["desc"], "flag:beat_" + SIDE2[_w]["mini"])


# ------------------------------------------------------------------ tavern & house people
TAVERN_PEOPLE = {
    "fire": [
        ("barkeep_fire", "Barkeep Coal", look("man", "#1a1a1a", "#8a3a1a", "#f0c040", 2, beard=True), "keeper",
         ["Welcome to the Bellows & Barrel. Eat something hot, you'll fight hotter."]),
        ("bard_fire", "Lyre-Player Fenn", look("man", "#e0a040", "#a03060", "#f0e0a0", 0, hat="wide"), "bard",
         ["~ Down below the mountain, where the red rock runs... ~", "Ever notice how the best treasure's always under something? Floors. Waterfalls. People."]),
        ("patron_fire2", "Sooty Miner", look("man", "#3a2a1a", "#5a4a3a", "#a0a0a0", 2), "patron2",
         ["The Ashen Wilds trail goes down the mountain, then under it. The Magma Tunnels.",
          "That's the only way to the Envy Forge now. Bring water magic. Lots."]),
        ("patron_fire3", "Arm-Wrestler Brunna", look("woman", "#c04020", "#6a2a1a", "#e0c060", 2), "patron3",
         ["Monsters out there drop weapons sometimes. Their old owners', I'd guess.",
          "Tan-glow stuff's common. Magenta's rare. Gold?", "If you ever see a gold glow, hold onto it. That's legendary."]),
    ],
    "water": [
        ("barkeep_water", "Barkeep Moira", look("woman", "#3a2a2a", "#2a5a7a", "#f0f0e0", 1), "keeper",
         ["The Salted Gull! Chowder's fresh. Tea's fresher."]),
        ("bard_water", "Shanty-Singer Hob", look("man", "#d0d0d0", "#2a3a6a", "#e0e0e0", 1, beard=True), "bard",
         ["~ Oh the tide goes out, and the tide comes in... ~", "The waterfall in the north has a sound behind it. Like an echo with no wall."]),
        ("patron_water2", "Net-Mender Oswin", look("elder", "#e0e0e0", "#4a5a6a", "#d0a060", 1), "patron2",
         ["North past the Shoals is the Weeping Falls. The Cradle's beyond.",
          "Fire creatures out there are rare. It's mostly water. Bring wind... no, stone. Stone beats water."]),
        ("patron_water3", "Dock-Hand Pia", look("child", "#3a2a1a", "#c05050", "#f0f0f0", 2), "patron3",
         ["Mister Tobiah's house has a squeaky floorboard. He says it's nothing. It squeaks like it's hiding something."]),
    ],
    "wind": [
        ("barkeep_wind", "Barkeep Wren-Feather", look("man", "#f0e0a0", "#2a8a7a", "#ffffff", 0), "keeper",
         ["The Tangled String! Named for my kite. Still tangled. Have a tart."]),
        ("bard_wind", "Piper Lisle", look("woman", "#8a4a2a", "#e0b040", "#40a0c0", 1), "bard",
         ["~ Up where the strings all sing... ~", "The Cloud Steppes are all cliffs. Look for the carved steps; they always lead somewhere."]),
        ("patron_wind2", "Retired Courier", look("elder", "#c0c0c0", "#3a7a5a", "#e0c050", 1, hat="cap"), "patron2",
         ["Beyond the meadow are the Cloud Steppes, then the Aviary. Corvane's up top."]),
        ("patron_wind3", "Gambling Gull-Tamer", look("man", "#2a2a2a", "#6a6a8a", "#f0d060", 2), "patron3",
         ["Gear with the gold glow is the real prize. I've seen one in my life. Lost it in a bet."]),
    ],
    "stone": [
        ("barkeep_stone", "Barkeep Hollis", look("man", "#5a3a1a", "#6a5a4a", "#c0a040", 1, beard=True), "keeper",
         ["The Honest Tankard. No gold leaf on anything. Have a pasty."]),
        ("bard_stone", "Drum-Singer Ama", look("woman", "#1a1a1a", "#6a4a2a", "#c0e060", 3), "bard",
         ["~ Dig, dig, the mountain's deep... ~", "Somebody in town hides their savings under the floor. Every miner does. Every one."]),
        ("patron_stone2", "Tired Union Rep", look("man", "#3a3a3a", "#4a5a3a", "#e0c050", 2, hat="cap"), "patron2",
         ["The Old Mine Shaft runs under the Hollows. The Gilded Hall's at the bottom.",
          "Stone things hate wind. Bring a breeze."]),
        ("patron_stone3", "Pickaxe Collector", look("elder", "#d0d0d0", "#5a4a3a", "#a0a0a0", 1), "patron3",
         ["Monsters down there drop iron like it's nothing. Fight a few; you'll find a pick or a bow worth keeping."]),
    ],
    "spirit": [
        ("barkeep_spirit", "Barkeep Celestine", look("woman", "#f0e0a0", "#e0d0f0", "#c0a040", 0), "keeper",
         ["The Last Candle. We never put it out. Bread's warm."]),
        ("bard_spirit", "Hymn-Hummer Brother Abe", look("robe", "#4a3a2a", "#c0b080", "#8080e0", 1, hat="hood"), "bard",
         ["~ Light a lamp, and climb the stair... ~", "The Lantern Stair climbs forever. Every landing has a little shrine. Some have more."]),
        ("patron_spirit2", "Weary Pilgrim", look("man", "#6a4a2a", "#a0a0c0", "#f0f0f0", 1), "patron2",
         ["The Lantern Stair leads up from the fields to the Atelier. That's where Iris works."]),
        ("patron_spirit3", "Novice Tam", look("child", "#d0a060", "#f0f0ff", "#a0a0f0", 0), "patron3",
         ["The abbess has a secret in her house! I heard her say 'under the rug.' I didn't look. Much."]),
    ],
    "void": [
        ("barkeep_void", "Barkeep Nobody-in-Particular", look("man", "#4a4a5a", "#2a2238", "#a080e0", 0), "keeper",
         ["Welcome to the Somewhere. It's somewhere. Have a soup."]),
        ("bard_void", "Whistler Mote", look("woman", "#a0a0c0", "#3a2a5a", "#c0a0ff", 0), "bard",
         ["~ Hold the lamp and hold the line... ~", "Under the island there's an underside. You can walk upside-down there. Well. It feels like it."]),
        ("patron_void2", "Lamp-Oil Seller", look("elder", "#c0c0d0", "#3a3a4a", "#e0c050", 0, hat="wide"), "patron2",
         ["The Underside runs beneath the Drift. The Throne is past it. Don't let go of anything you love."]),
        ("patron_void3", "Forgetful Regular", look("man", "#3a2a3a", "#4a4060", "#8080a0", 1), "patron3",
         ["I buried something in my house once. Or someone else did. In the corner, by the bookshelf.",
          "I keep meaning to dig it up. I keep forgetting."]),
    ],
}

# Residents of the four houses: (id, name, look, spot "a"/"b", lines). house3/house4 may hold the side dungeon stairs.
HOUSE_PEOPLE = {
    "fire": {
        "house1": [("fire_h1", "Retired Pit-Fighter", look("man", "#6a6a6a", "#6a2a1a", "#c0c0c0", 2, beard=True),
                    ["I won forty fights in Slagjaw's pit. Lost one. That's the one I remember."])],
        "house2": [("fire_h2", "Glassblower Ivy", look("woman", "#e08040", "#3a6a5a", "#f0e080", 1),
                    ["I blow glass with dragon-breath bellows. Don't touch anything, it's all still 900 degrees."])],
        "house3": [("fire_h3", "Hesta's Cat", look("child", "#e08030", "#e08030", "#ffffff", 0),
                    ["Mrrp. (The cat stares at the cellar stairs and flattens its ears.)"])],
        "house4": [("fire_h4", "Smith's Apprentice", look("man", "#2a1a1a", "#5a3a2a", "#e0a040", 2),
                    ["Master Brannoc kept a spare stash under the floor. Under the loose board by the hearth, I think.",
                     "Don't tell Hesta I told you. Actually, tell her. She'd want you to have it."])],
    },
    "water": {
        "house1": [("water_h1", "Old Tobiah's Neighbor", look("elder", "#d0d0d0", "#2a5a7a", "#f0e0c0", 1),
                    ["Tobiah's floor squeaks something awful. I've told him for years to fix it."])],
        "house2": [("water_h2", "Sailmaker Duff", look("man", "#8a5a2a", "#e0e0d0", "#2a6a9a", 1, beard=True),
                    ["Every sail in Saltmere came through this door. Most of them came back, too."])],
        "house3": [("water_h3", "Little Brin", look("child", "#2a1a1a", "#40a0c0", "#f0f080", 2),
                    ["My mom says there's a cave behind the big waterfall. I'm not allowed to go. YOU could go."])],
        "house4": [("water_h4", "Tobiah's Grandson", look("man", "#3a2a1a", "#3a4a6a", "#e0c070", 1),
                    ["Grandpa hid something under the floor when the tide took Mum. He never dug it up.",
                     "If you find it... I think he'd want someone to."])],
    },
    "wind": {
        "house1": [("wind_h1", "Weather-Watcher", look("elder", "#f0f0f0", "#4a7a9a", "#e0e0a0", 0, hat="wide"),
                    ["Wind's from the east today. Means the Steppes will be gusty. Watch your footing on the cliffs."])],
        "house2": [("wind_h2", "Spinning Girl", look("child", "#f0c040", "#e05080", "#40c0b0", 0),
                    ["Wheee! I'm a pinwheel! Did you know there's a secret under the rug in the house next door?"])],
        "house3": [("wind_h3", "Feather-Duster Gerta", look("woman", "#a0a0a0", "#6a8a4a", "#f0f0f0", 1),
                    ["I dust every inch of this town. Every inch. I know where everything's hidden.",
                     "Under the rug in the west house. Loose board. You didn't hear it from me."])],
        "house4": [("wind_h4", "Belfry Keeper's Ghost? No, just Dust", look("elder", "#c0c0c0", "#8a8a8a", "#d0c0a0", 0),
                    ["This house is empty. The stairs go up to the old belfry. Nobody's rung that bell in years."])],
    },
    "stone": {
        "house1": [("stone_h1", "Miner's Widow Pell", look("woman", "#3a3a3a", "#5a4a3a", "#c0a040", 2),
                    ["My husband kept his savings under the floor, like everyone. I never found his."])],
        "house2": [("stone_h2", "Gem-Cutter Quill", look("man", "#d0d0d0", "#3a5a3a", "#80e0a0", 1),
                    ["Geodes are ugly until you break them. People too, I find."])],
        "house3": [("stone_h3", "Nervous Landlord", look("man", "#6a4a2a", "#8a6a4a", "#d0d0d0", 1, hat="cap"),
                    ["The cellar goes down to the Forgotten Tunnel. Something's chewing down there. I'm moving out."])],
        "house4": [("stone_h4", "Retired Prospector", look("elder", "#e0e0e0", "#6a4a2a", "#d0a040", 1, beard=True),
                    ["I always said, the best lode is right under your feet. In my case, literally. In the corner."])],
    },
    "spirit": {
        "house1": [("spirit_h1", "The Abbess", look("robe", "#d0d0d0", "#f0f0ff", "#d0b050", 0, hat="hood"),
                    ["Finishing is a kind of courage. So is starting.", "...What? No, there's nothing under the rug."])],
        "house2": [("spirit_h2", "Candle-Dipper Rue", look("woman", "#f0d0a0", "#a08ad0", "#ffffff", 0),
                    ["Every candle in Hallowmere, I dipped. Twelve thousand, and counting. And counting."])],
        "house3": [("spirit_h3", "Crypt-Warden Orm", look("man", "#4a4a4a", "#6a6a8a", "#c0c0e0", 1, beard=True),
                    ["The crypt stairs are behind me. I don't go down anymore. It's too... bright."])],
        "house4": [("spirit_h4", "Sleeping Pilgrim", look("man", "#8a6a4a", "#a0a0b0", "#e0e0e0", 1),
                    ["Zzz... the lantern... climb the stair... zzz..."])],
    },
    "void": {
        "house1": [("void_h1", "Woman Who Counts", look("woman", "#a0a0c0", "#3a3a5a", "#c0a0ff", 0),
                    ["One, two, three... I count my things every night so they don't drift off. One, two..."])],
        "house2": [("void_h2", "Clockless Clockmaker", look("man", "#d0d0d0", "#4a3a3a", "#e0c050", 0, beard=True),
                    ["Time doesn't pass here, exactly. I make clocks anyway. Somebody should keep it."])],
        "house3": [("void_h3", "Forgetful Regular's Wife", look("woman", "#4a3a3a", "#5a4a6a", "#e0e0e0", 1),
                    ["He buried something by the bookshelf and keeps forgetting. Go on, dig. He won't mind. He won't remember."])],
        "house4": [("void_h4", "Echo of a Tenant", look("elder", "#b0b0c0", "#2a2238", "#8070a0", 0),
                    ["...nt... upstairs... the room... isn't... there..."])],
    },
}

# which house hides a floorboard treasure (dig spot) in each world
HOUSE_HIDDEN = {"fire": "house4", "water": "house1", "wind": "house1", "stone": "house4", "spirit": "house1", "void": "house3"}


# ------------------------------------------------------------------ the final foe
NEW_UNIQUES["king_goblin"] = {
    "name": "King Goblin", "sprite": "king_goblin", "el": "void", "tier": "king",
    "ai": [{"k": "attack", "w": 2}, {"k": "skill", "s": "brute_smash", "w": 2},
           {"k": "spell", "el": "void", "power": 0.8, "target": "all", "name": "Crown of Spite", "w": 2},
           {"k": "summon", "species": "goblin", "w": 1, "say": "\"GUARDS! Somebody stab the hero!\""},
           {"k": "steal_gold", "w": 1, "name": "Royal Pilfer", "say": "\"Everything shiny belongs to the KING.\""},
           {"k": "buff", "stat": "str", "w": 1, "say": "King Goblin gulps down a jar of something green."}],
    "size": "boss", "def_": 1.25, "mdef": 1.15, "spd": 1.1,
    "phases": [{"at": 0.5, "say": "\"You broke my curses. ALL SIX. Do you know how long those took?!\" The crown blazes.", "buff": "mag"},
               {"at": 0.2, "say": "\"No, no, no... a goblin king doesn't lose to some... some SLAYER!\"", "buff": "spd"}],
}
KING = {
    "pre": ["A throne of stolen treasure rises out of the dark. Atop it sits a goblin wearing six crowns, one from every world.",
            "KING GOBLIN: \"So YOU'RE the one who keeps un-cursing my Hearths. Jealousy, grief, greed... I worked hard on those!\"",
            "KING GOBLIN: \"A sad world is an easy world to rob. Now hold still, little Kindler. I'll add your crown to the pile.\""],
    "post": ["King Goblin topples off his throne in a landslide of stolen coins.",
             "KING GOBLIN: \"Fine... FINE. Keep your warm, happy worlds. See if I care.\"",
             "He scurries into a crack in the wall. The six stolen crowns roll to your feet and fade into light.",
             "Somewhere far away, six Hearths burn a little brighter.",
             "The people of the six worlds will tell this story for a long time. The story of the one who slew the Goblin King.",
             "The story of the Goblin Slayer."],
}


# ------------------------------------------------------------------ Double Techs (two party members whose turns are both ready)
COMBOS = [
    {"a": "hero", "b": "kael", "name": "Ember Cross", "el": "fire", "power": 2.4, "target": "one", "mp": 6},
    {"a": "hero", "b": "nerissa", "name": "Tidal Blade", "el": "water", "power": 2.3, "target": "one", "mp": 6},
    {"a": "hero", "b": "pip", "name": "Gale Rush", "el": "wind", "power": 1.4, "target": "all", "mp": 8},
    {"a": "hero", "b": "durga", "name": "Rockbreaker", "el": "stone", "power": 2.6, "target": "one", "mp": 6},
    {"a": "hero", "b": "sol", "name": "Dawn Strike", "el": "spirit", "power": 2.4, "target": "one", "mp": 7},
    {"a": "hero", "b": "vesper", "name": "Night Fang", "el": "void", "power": 1.5, "target": "all", "mp": 8},
    {"a": "kael", "b": "durga", "name": "Mountain Fall", "el": "stone", "power": 2.9, "target": "one", "mp": 6},
    {"a": "kael", "b": "pip", "name": "Firestorm", "el": "fire", "power": 1.5, "target": "all", "mp": 9},
    {"a": "nerissa", "b": "sol", "name": "Healing Tide", "el": "water", "power": 1.1, "target": "allies", "mp": 9, "heal": True},
    {"a": "nerissa", "b": "vesper", "name": "Moon Tide", "el": "water", "power": 1.6, "target": "all", "mp": 9},
    {"a": "pip", "b": "vesper", "name": "Shadow Volley", "el": "void", "power": 1.6, "target": "all", "mp": 8},
    {"a": "durga", "b": "sol", "name": "Holy Quake", "el": "spirit", "power": 1.5, "target": "all", "mp": 9},
    {"a": "kael", "b": "vesper", "name": "Black Flame", "el": "fire", "power": 2.6, "target": "one", "mp": 7},
    {"a": "nerissa", "b": "pip", "name": "Typhoon", "el": "wind", "power": 1.5, "target": "all", "mp": 9},
    {"a": "sol", "b": "vesper", "name": "Twilight", "el": "spirit", "power": 1.6, "target": "all", "mp": 9},
]
