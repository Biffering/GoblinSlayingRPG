"""World content for Six Hearths: names, NPCs, dialogue scripts, quests, chests, riddles, bosses.

NPC scripts are lists of branches. The first branch whose "if" conditions all pass runs.
  conditions: "flag:x", "!flag:x", "q:id=none|active|ready|done", "item:x", "!item:x",
              "member:id", "!member:id", "party>=N", "hearts>=N"
  actions:    "set:x", "give:id[:n]", "take:id", "gold:n", "quest:id", "done:id", "recruit:id",
              "shop:id", "inn:price", "heal", "summon:id", "end", "sfx:name"
  "ask": {"q": "...", "yes": {"say": [...], "do": [...]}, "no": {...}}
"""

# --------------------------------------------------------------------------- helpers

def br(cond=None, say=None, do=None, ask=None):
    b = {"if": cond or [], "say": say or []}
    if do:
        b["do"] = do
    if ask:
        b["ask"] = ask
    return b


def npc(nid, name, spot, look, script, wander=False, face="down", cond=None):
    d = {"id": nid, "name": name, "spot": spot, "look": look, "script": script, "wander": wander, "face": face}
    if cond:
        d["cond"] = cond
    return d


def look(body, hair, outfit, accent, skin=1, hat=None, beard=False):
    return {"body": body, "hair": hair, "outfit": outfit, "accent": accent, "skin": skin, "hat": hat, "beard": beard}


def shopkeeper(nid, name, spot, lk, shop_id, line):
    return npc(nid, name, spot, lk, [br([], [line], ["shop:" + shop_id])])


def innkeeper(nid, name, spot, lk, price, line):
    return npc(nid, name, spot, lk, [br([], [line], ask={
        "q": f"Rest for {price} gold?",
        "yes": {"say": ["You sleep deeply. Everyone feels restored."], "do": [f"inn:{price}"]},
        "no": {"say": ["Come back when you're weary."]}})])


QUESTS = {}


def quest(qid, title, world, kind, giver, desc, objective):
    QUESTS[qid] = {"title": title, "world": world, "kind": kind, "giver": giver, "desc": desc, "objective": objective}


# --------------------------------------------------------------------------- the six worlds

WORLDS = {}

# ============================== FIRE: Cinderreach — jealousy ==============================
quest("main_fire", "The Green Flame", "fire", "main", "Ignatia",
      "Ignatia's brother Vulkar has become a monster of green fire in the Envy Forge, north of the Ashen Wilds.",
      "flag:beat_vulkar")
quest("comp_fire", "Chains of the Pit", "fire", "companion", "Kael",
      "Slagjaw, the ogre who owned Kael, still guards Kael's old blade deep in Smolder Hollow.", "flag:beat_slagjaw")
quest("side_fire", "The Bellows Thief", "fire", "side", "Tamsin",
      "A scavenger called Scrapjack stole the Great Bellows. He was last seen in the Ashen Wilds.", "item:forge_bellows")
quest("key_fire", "The Widow's Hammer", "fire", "key", "Hesta",
      "Hesta's late husband Brannoc lost his hammer in Smolder Hollow. She wants it back.", "item:hestas_hammer")

WORLDS["fire"] = {
    "name": "Cinderreach", "town": "Emberfall", "field": "Ashen Wilds", "cave": "Smolder Hollow", "dungeon": "The Envy Forge",
    "landmark": "a cracked obelisk", "riddle_offset": (-3, -1), "flip": False, "seed": 101,
    "summon": "pyrestag", "boss": "vulkar", "boss_flag": "beat_vulkar", "main_quest": "main_fire",
    "boss_pre": ["A man stands at the great anvil, hammering at nothing. His fire is green.",
                 "VULKAR: \"Did she send you? Of course she did. Everyone always does what Ignatia wants.\"",
                 "VULKAR: \"Fine. Watch me be better at something. Watch me be better at BURNING.\""],
    "boss_post": ["The green fire gutters out. Vulkar is just a tired man with soot on his face.",
                  "VULKAR: \"...I made her first hammer, you know. When we were kids. She still uses it.\"",
                  "The Fire Heartstone cools in your hand, warm as an ordinary hearth."],
    "mini_companion": {"id": "slagjaw", "where": "cave", "flag": "beat_slagjaw", "quest": "comp_fire",
                       "pre": ["A huge ogre lounges on a throne of chains. Kael's old blade is driven into it.",
                               "SLAGJAW: \"Little Kael! You came back to the pit! The crowd missed you.\"",
                               "KAEL: \"There's no crowd, Slagjaw. There never was. Just you.\""],
                       "post": ["Slagjaw collapses into the chains he collected.",
                                "KAEL: \"...I thought this would feel bigger.\" He pulls the blade free.",
                                "KAEL: \"It feels lighter. Good. Let's go.\""],
                       "reward": "pitbreaker"},
    "mini_side": {"id": "scrapjack", "where": "field", "flag": "beat_scrapjack", "quest": "side_fire",
                  "pre": ["A wiry man with a robotic arm is strapped to an enormous bellows.",
                          "SCRAPJACK: \"Finders keepers! I found it in a forge. Totally abandoned. Except for the people.\""],
                  "post": ["Scrapjack flees, leaving the Great Bellows behind. You'd better take it to Tamsin."],
                  "reward_item": "forge_bellows"},
    "key_chest_item": "hestas_hammer",
    "chests": {"field": ["potion:2", "gear:ashwood_bow", "ether"], "cave": ["hi_potion", "gear:magma_ring"],
               "dungeon": ["might_elixir", "feather", "elixir"]},
    "hidden_item": "goathorn_talisman",
    "npcs": [
        npc("ignatia", "Ignatia", "elder", look("woman", "#8a2b14", "#5a2e1e", "#e0a040", 1), [
            br(["q:main_fire=none"], [
                "I'm Ignatia, forgemistress of Emberfall. Everyone knows my name. That's the problem.",
                "My little brother Vulkar was a better smith than me when we were children. Nobody noticed. They only ever noticed me.",
                "He went to the old forge north of the Wilds, the one the Heart of Fire sleeps under, and asked it to make him matter.",
                "Now the fire in Cinderreach burns green and hungry. It eats anything anyone ever praised.",
                "Please. Go to the Envy Forge, north through the Ashen Wilds. Bring my brother back... or at least stop him."],
               ["quest:main_fire"]),
            br(["q:main_fire=active", "!flag:beat_vulkar"], [
                "The Envy Forge is at the north end of the Ashen Wilds. He'll be at the great anvil.",
                "Fire beasts flinch from water. If you have anything tidal, use it."]),
            br(["q:main_fire=ready"], [
                "You're back. And the fire... the fire is orange again.",
                "He's alive? He's... coming home? Then I'll stop being the only smith in this town. Good. I'm tired.",
                "Take the Heartstone. And this. It's the first thing he ever forged me, a gift I never thanked him for."],
               ["done:main_fire", "give:heart_fire", "gold:400", "give:hi_potion:2"]),
            br(["q:main_fire=done"], [
                "Vulkar and I are working the same anvil again. He still says I hold the tongs wrong.",
                "He's right. Don't tell him."]),
        ]),
        npc("kael", "Kael", "companion", look("man", "#2a1a12", "#7a2a18", "#d8c090", 2), [
            br(["!member:kael"], [
                "You're looking at the scars. Everyone does. I'm Kael. I fought in Emberfall's pits for eight years.",
                "Slagjaw, the ogre who ran the pits, kept the blades of every fighter he owned. Mine's still stuck in his throne, down in Smolder Hollow.",
                "I don't need the blade. I need to see him lose. You look like someone who's going somewhere hard."],
               ask={"q": "Let Kael join your party?",
                    "yes": {"say": ["KAEL: \"Good. I hit things. You point at what needs hitting. Simple.\"",
                                    "Kael joined the party! Slagjaw lurks at the bottom of Smolder Hollow, west of the Ashen Wilds."],
                            "do": ["recruit:kael", "quest:comp_fire", "sfx:recruit"]},
                    "no": {"say": ["KAEL: \"Suit yourself. I'll be here. I'm good at waiting. Pit taught me that.\""]}}),
        ], cond=["!member:kael"]),
        npc("tamsin", "Tamsin", "side", look("woman", "#d8a050", "#6a4a2a", "#a03020", 1), [
            br(["q:side_fire=none"], [
                "I'm Tamsin, apprentice at the great forge. Or I was. Someone stole the Great Bellows!",
                "Without its breath the forge can't get hot enough for real steel. A scavenger with a metal arm took it. Scrapjack, he calls himself.",
                "He's somewhere in the Ashen Wilds. If you get it back, I'll give you the mail I've been working on."],
               ["quest:side_fire"]),
            br(["q:side_fire=active", "!item:forge_bellows"], ["Scrapjack's out in the Ashen Wilds. Follow the sound of wheezing."]),
            br(["q:side_fire=ready"], [
                "THE BELLOWS! You found it! Listen to that breath...",
                "Here. Forgeheart Mail. I quenched it in the last of the old fire. It's yours."],
               ["take:forge_bellows", "done:side_fire", "give:gear:forgeheart_mail", "sfx:chest"]),
            br(["q:side_fire=done"], ["The forge is roaring again. Come back when you need something sharp."]),
        ]),
        npc("nan", "Old Nan Cinders", "story", look("elder", "#d0d0d0", "#6a2a4a", "#e0b070", 0), [
            br([], [
                "Sit, sit. Let an old woman tell you something nobody asked about.",
                "When I was a girl, I kept a one-horned goat. Nasty creature. Loved me, hated everyone else.",
                "Every evening she'd stand by the cracked obelisk out in the Ashen Wilds, like she was guarding it.",
                "Then at dusk she'd take three hops toward the sunset, and one toward the cold, and paw at the ash until dark.",
                "I never knew why. Sentimental old goat. Anyway. That's the story. Didn't go anywhere, did it?"]),
        ]),
        npc("hesta", "Widow Hesta", "key", look("elder", "#5a5a5a", "#2a2a2a", "#c04030", 1), [
            br(["q:key_fire=none"], [
                "My Brannoc was the smith before Ignatia. He went into Smolder Hollow for good ore and never came out.",
                "They say you can still hear him hammering down there, when the wind's right. I just want his hammer back.",
                "Bring it to me and I'll give you the thing he always said to keep safe. An old key, black as ash."],
               ["quest:key_fire"]),
            br(["q:key_fire=active", "!item:hestas_hammer"], ["His hammer's in Smolder Hollow. West of the Ashen Wilds. Please."]),
            br(["q:key_fire=ready"], [
                "...That's it. That's his grip, worn into the handle.",
                "Here. The Key of Ash. Brannoc said it was half of a lock at the end of everything. Strange man. I loved him."],
               ["take:hestas_hammer", "done:key_fire", "give:key_ash", "sfx:key"]),
            br(["q:key_fire=done"], ["I hang his hammer over the door now. The house sounds like him again."]),
        ]),
        shopkeeper("pawn_fire_k", "Pawnbroker Dross", "pawn", look("man", "#3a2a1a", "#4a3a2a", "#d09040", 2, beard=True), "pawn_fire",
                   "Blades, bows, staves. Hot off the anvil. Literally, careful."),
        shopkeeper("items_fire_k", "Apothecary Pell", "items", look("woman", "#e0e0e0", "#3a6a3a", "#e05030", 0, hat="hood"), "items",
                   "Potions, tonics, elixirs. The glowing ones make you glow. That's not a side effect, it's a feature."),
        innkeeper("inn_fire_k", "Innkeeper Bram", "inn", look("man", "#6a3a1a", "#8a5a2a", "#f0e0c0", 1, beard=True), 20,
                  "Welcome to the Hearthside. Beds are warm. Too warm, some say."),
        npc("fire_f1", "Gossiping Smith", "flavor1", look("man", "#1a1a1a", "#6a4a3a", "#a0a0a0", 2), [
            br([], ["Everything in the Wilds is made of fire now. Ash rats, cinder knights...",
                    "They all hate water. Douse 'em and they fold like wet paper."])], wander=True),
        npc("fire_f2", "Bored Guard", "flavor2", look("guard", "#4a2a1a", "#8a3020", "#c0c0c0", 1, hat="helm"), [
            br([], ["Ghosts in the Envy Forge? Don't bother swinging at them. Steel goes right through.",
                    "Hit 'em with magic. Learned that the hard way. Twice."])]),
        npc("fire_f3", "Child with Soot", "flavor3", look("child", "#3a2a1a", "#c05030", "#f0d040", 2), [
            br([], ["My mom says jealousy is like holding a coal to throw at someone. You get burned first.",
                    "I don't know what that means. I just like coal."])], wander=True),
        npc("fire_f4", "Traveling Bard", "flavor4", look("man", "#d0a040", "#6a2a6a", "#e0e0e0", 0, hat="wide"), [
            br(["!flag:beat_vulkar"], ["They say Vulkar's flames are the green of envy. I'd write a song about it, but I'm jealous of better songwriters."]),
            br([], ["The fire is orange again! I've written a song about it. It's mostly about me, though."])]),
    ],
    "pawn_stock": ["cinder_blade", "ember_bow", "pyre_staff", "scorchmail", "ember_ring", "iron_sword", "short_bow", "oak_staff"],
}

# ============================== WATER: Maretide — loss ==============================
quest("main_water", "The Tide That Won't Go Out", "water", "main", "Harbormaster Quill",
      "Maren, the Mother of Tides, grieves at the bottom of the Sunken Cradle, east of the Weeping Shoals.", "flag:beat_maren")
quest("comp_water", "The Dark Lighthouse", "water", "companion", "Nerissa",
      "The lighthouse lens was swallowed by Gloomfin, a huge angler fish in the Drowned Grotto.", "flag:beat_gloomfin")
quest("side_water", "Nets of the Drowned", "water", "side", "Odile",
      "The ghost of Captain Corrow haunts the Weeping Shoals and tangles every net.", "flag:beat_drowned_captain")
quest("key_water", "Three Notes", "water", "key", "Tobiah",
      "Old Tobiah's daughter left a music box in the Drowned Grotto before the tide took her.", "item:music_box")

WORLDS["water"] = {
    "name": "Maretide", "town": "Saltmere", "field": "Weeping Shoals", "cave": "Drowned Grotto", "dungeon": "The Sunken Cradle",
    "landmark": "a whale's bleached ribs", "riddle_offset": (2, 1), "flip": True, "seed": 202,
    "summon": "marrowhale", "boss": "maren", "boss_flag": "beat_maren", "main_quest": "main_water",
    "boss_pre": ["A woman made of water rocks an empty cradle. The whole sea sways with her.",
                 "MAREN: \"Shh. Shh. If the tide never goes out, nothing ever gets carried away.\"",
                 "MAREN: \"You want to take the water back? Then you'll have to take everything I've lost with it.\""],
    "boss_post": ["The cradle stops rocking. Maren looks at it for a long time.",
                  "MAREN: \"...It's empty. It's been empty for so long. I just didn't want to see.\"",
                  "She lets the tide go out. The Water Heartstone stops weeping."],
    "mini_companion": {"id": "gloomfin", "where": "cave", "flag": "beat_gloomfin", "quest": "comp_water",
                       "pre": ["Something huge drifts in the black water. A light dangles in front of its jaws. It's the lighthouse lens.",
                               "NERISSA: \"That's my light. You've been using MY light to lure things in.\""],
                       "post": ["Gloomfin sinks into the dark. The lens rolls free, still glowing.",
                                "NERISSA: \"I'll put it back where it belongs. And this, the lens frame, should be yours.\""],
                       "reward": "beacon_staff"},
    "mini_side": {"id": "drowned_captain", "where": "field", "flag": "beat_drowned_captain", "quest": "side_water",
                  "pre": ["A ghost in a rotted captain's coat stands at the waterline, hauling an invisible net.",
                          "CAPTAIN CORROW: \"Lost my whole crew to this sea. I'll not lose one more fish to it. Not ONE.\""],
                  "post": ["The captain fades, finally letting go of the rope. The nets of the Shoals come loose."]},
    "key_chest_item": "music_box",
    "chests": {"field": ["potion:2", "gear:kelp_mail", "ether"], "cave": ["hi_potion", "gear:riptide_blade"],
               "dungeon": ["sage_elixir", "feather", "elixir"]},
    "hidden_item": "pearl_of_tears",
    "npcs": [
        npc("quill", "Harbormaster Quill", "elder", look("man", "#c0c0c0", "#1a3a6a", "#e0d090", 1, hat="cap", beard=True), [
            br(["q:main_water=none"], [
                "Harbormaster Quill. Not that there's a harbor anymore. The tide came in a year ago and never went out.",
                "Maren, the Mother of Tides, lost her child to a storm. Since then she won't let the sea leave. Not even an inch.",
                "Everything she can't bear to lose, she drowns. Our docks. Our boats. Our goodbyes.",
                "Her lair is the Sunken Cradle, past the Weeping Shoals. Someone has to tell her it's time."],
               ["quest:main_water"]),
            br(["q:main_water=active", "!flag:beat_maren"], [
                "The Sunken Cradle is at the far end of the Weeping Shoals.",
                "Water folk hate stone. Ask any fisherman who's hit a reef."]),
            br(["q:main_water=ready"], [
                "Do you hear that? That's the tide going OUT. I'd forgotten the sound.",
                "Here, the Water Heartstone, and some coin. The harbor will be open by morning."],
               ["done:main_water", "give:heart_water", "gold:400", "give:ether:2"]),
            br(["q:main_water=done"], ["Ships are leaving again. Some of them won't come back. That's how the sea works."]),
        ]),
        npc("nerissa", "Nerissa", "companion", look("woman", "#2a6a8a", "#1a4a7a", "#f0f0e0", 0), [
            br(["!member:nerissa"], [
                "I keep the lighthouse on the point. Kept. It's been dark for a month.",
                "Something in the Drowned Grotto stole the lens. I've seen its light moving down there, luring sailors.",
                "I'm a healer, mostly. But I'm not afraid of the dark. Not my dark, anyway."],
               ask={"q": "Let Nerissa join your party?",
                    "yes": {"say": ["NERISSA: \"Then let's go turn the light back on.\"",
                                    "Nerissa joined the party! Gloomfin lurks in the Drowned Grotto, off the Weeping Shoals."],
                            "do": ["recruit:nerissa", "quest:comp_water", "sfx:recruit"]},
                    "no": {"say": ["NERISSA: \"I understand. I'll keep watch from here.\""]}}),
        ], cond=["!member:nerissa"]),
        npc("odile", "Odile the Netmender", "side", look("woman", "#8a5a3a", "#3a5a5a", "#d0c0a0", 2, hat="hood"), [
            br(["q:side_water=none"], [
                "Every net I cast in the Shoals comes back knotted into sailor's loops. Every one!",
                "It's Captain Corrow's ghost. He lost his crew out there and he won't stop hauling.",
                "Set him free and I'll give you the coat I wove for my husband. He'd want it worn."],
               ["quest:side_water"]),
            br(["q:side_water=active", "!flag:beat_drowned_captain"], ["Corrow walks the waterline in the Weeping Shoals. Magic works best on ghosts."]),
            br(["q:side_water=ready"], [
                "My nets came back empty this morning. Just empty! Wonderful!",
                "The Tideguard Coat. It's never lost a sailor. Don't be the first."],
               ["done:side_water", "give:gear:tideguard_coat", "sfx:chest"]),
            br(["q:side_water=done"], ["Fish for supper tonight. First time in a year."]),
        ]),
        npc("pell_m", "Old Mother Pell", "story", look("elder", "#e8e8e8", "#3a4a8a", "#e0a0a0", 1), [
            br([], [
                "My sweetheart proposed to me under the whale's ribs out in the Shoals, oh, sixty years ago.",
                "He was so nervous. After I said yes, he walked two strides toward the sunrise and one toward the warm water.",
                "Buried something there, he did. Said it was 'in case you'd said no.' A consolation prize, for himself.",
                "We never dug it up. Didn't need to. Silly man. I miss him."]),
        ]),
        npc("tobiah", "Old Tobiah", "key", look("elder", "#b0b0b0", "#2a3a4a", "#c0a060", 2, beard=True), [
            br(["q:key_water=none"], [
                "My girl loved the grotto. She'd sit at the bottom and wind her little music box. Three notes, over and over.",
                "The tide took her. The box is still down there, in the Drowned Grotto.",
                "Bring it back to me and I'll give you the key she found on the shore. She said it was 'the key to remembering.'"],
               ["quest:key_water"]),
            br(["q:key_water=active", "!item:music_box"], ["The Drowned Grotto. West of the Shoals. Mind the dark."]),
            br(["q:key_water=ready"], [
                "...Three notes. Then it stops, like it's waiting for the rest.",
                "Here. The Key of Memory. She'd want it to open something."],
               ["take:music_box", "done:key_water", "give:key_memory", "sfx:key"]),
            br(["q:key_water=done"], ["I wind it every night. Three notes. I hum the rest."]),
        ]),
        shopkeeper("pawn_water_k", "Pawnbroker Wessel", "pawn", look("man", "#5a3a2a", "#2a4a6a", "#e0c070", 1), "pawn_water",
                   "Salvaged, polished, priced to move. Like the tide used to."),
        shopkeeper("items_water_k", "Herbalist Ama", "items", look("woman", "#1a1a1a", "#2a6a5a", "#f0a0c0", 2), "items",
                   "Seaweed tonics and proper potions. The proper ones taste better."),
        innkeeper("inn_water_k", "Innkeeper Marlo", "inn", look("man", "#c08040", "#3a3a6a", "#e0e0e0", 0), 20,
                  "The Gull's Rest. Sleep to the sound of the tide. It never stops, so you'll sleep a lot."),
        npc("water_f1", "Fisherman", "flavor1", look("man", "#4a3a2a", "#4a6a8a", "#e0e0a0", 1, hat="cap"), [
            br([], ["The brine beasts out there? Hate rocks. Throw stone at 'em, they sink like... well, stones."])], wander=True),
        npc("water_f2", "Lonely Sailor", "flavor2", look("man", "#2a2a2a", "#1a2a4a", "#c0c0c0", 2), [
            br([], ["I had a boat. Then the tide came and wouldn't leave. Now I have a very wet house."])]),
        npc("water_f3", "Girl with Shells", "flavor3", look("child", "#c0602a", "#3a8ab0", "#f0f0f0", 1), [
            br([], ["I collect shells. Every shell used to be a home for something. That makes me sad and happy at the same time."])], wander=True),
        npc("water_f4", "Lighthouse Watcher", "flavor4", look("woman", "#3a2a2a", "#5a5a7a", "#f0d060", 1), [
            br(["!flag:beat_gloomfin"], ["The lighthouse has been dark for weeks. Ships keep running aground on the point."]),
            br([], ["The light's back on! Nerissa did it. Well, you helped."])]),
    ],
    "pawn_stock": ["tidecutter", "coral_bow", "brine_staff", "shellguard", "pearl_ring", "iron_sword", "short_bow", "oak_staff"],
}

# ============================== WIND: Skyreach — freedom ==============================
quest("main_wind", "The Keeper of Cages", "wind", "main", "Windspeaker Aloe",
      "Corvane has caged the winds of Skyreach in the Gilded Aviary, beyond the Whistling Heights.", "flag:beat_corvane")
quest("comp_wind", "Stolen Wings", "wind", "companion", "Pip",
      "Captain Rook and his sky pirates stole Pip's glider-wings. Rook nests in the Hollow Winds Cave.", "flag:beat_rook")
quest("side_wind", "The Silent Bells", "wind", "side", "Bellkeeper Amsel",
      "Sylvane the Bell-Thief stole Kitefall's wind-bells. She hides in the Whistling Heights.", "item:wind_bells")
quest("key_wind", "Grandpa's First Kite", "wind", "key", "Lark",
      "Lark's grandfather lost his first kite in the Hollow Winds Cave.", "item:first_kite")

WORLDS["wind"] = {
    "name": "Skyreach", "town": "Kitefall", "field": "Whistling Heights", "cave": "Hollow Winds Cave", "dungeon": "The Gilded Aviary",
    "landmark": "a lone windmill", "riddle_offset": (5, 0), "flip": False, "seed": 303,
    "summon": "galecrown", "boss": "corvane", "boss_flag": "beat_corvane", "main_quest": "main_wind",
    "boss_pre": ["Cages hang everywhere, each one holding a trapped breeze. In the center, a man in gold armor with broken wings.",
                 "CORVANE: \"I flew once. Higher than anyone. Then I fell. Do you know how far it is to the ground? I do.\"",
                 "CORVANE: \"Nobody falls if nobody flies. I'm keeping them SAFE. Why does nobody thank me?\""],
    "boss_post": ["The cages swing open. A thousand winds pour out, and the whole Aviary sings.",
                  "CORVANE: \"...It's loud. I forgot how loud the sky is.\" He almost smiles.",
                  "The Wind Heartstone hums like an open sky."],
    "mini_companion": {"id": "rook", "where": "cave", "flag": "beat_rook", "quest": "comp_wind",
                       "pre": ["A sky pirate in a mirrored visor lounges on a heap of stolen gliders.",
                               "ROOK: \"Pip! Little Pip, grounded at last. How's walking? Slow?\"",
                               "PIP: \"Give. Them. BACK.\""],
                       "post": ["Rook bails out through a crack in the cave roof. Pip hugs her wings.",
                                "PIP: \"They're torn, but I can patch them. And here, Rook's bow. He won't miss it. Probably.\""],
                       "reward": "featherline_bow"},
    "mini_side": {"id": "sylvane", "where": "field", "flag": "beat_sylvane", "quest": "side_wind",
                  "pre": ["An elf sits on a rock, cradling a bundle of silver bells. They don't make a sound.",
                          "SYLVANE: \"The bells told everyone when the wind was free. Corvane pays well for silence.\""],
                  "post": ["Sylvane drops the bells and vanishes on a breeze. The bells ring at once, loud and bright."],
                  "reward_item": "wind_bells"},
    "key_chest_item": "first_kite",
    "chests": {"field": ["potion:2", "gear:kestrel_blade", "ether"], "cave": ["hi_potion", "gear:storm_mail"],
               "dungeon": ["stamina_tonic", "feather", "elixir"]},
    "hidden_item": "weathervane_charm",
    "npcs": [
        npc("aloe", "Windspeaker Aloe", "elder", look("elder", "#f0f0f0", "#2a8a7a", "#f0e080", 0, hat="hood"), [
            br(["q:main_wind=none"], [
                "Listen. Do you hear anything? No wind. In Skyreach. That should frighten you.",
                "Corvane was our greatest flier until he fell. Now he cages every breeze so no one else can fall.",
                "Kitefall has no wind for its kites, and its people have stopped looking up.",
                "His Gilded Aviary is past the Whistling Heights. Free the winds. Free us."],
               ["quest:main_wind"]),
            br(["q:main_wind=active", "!flag:beat_corvane"], [
                "The Gilded Aviary is at the top of the Whistling Heights.",
                "Wind creatures fear fire. Fire eats air; it's that simple."]),
            br(["q:main_wind=ready"], [
                "THERE it is. Feel that? Every kite in Kitefall is up at once.",
                "Take the Wind Heartstone. You gave us back the sky."],
               ["done:main_wind", "give:heart_wind", "gold:400", "give:stamina_tonic:2"]),
            br(["q:main_wind=done"], ["Corvane runs the kite school now. He makes everyone wear three helmets. Progress."]),
        ]),
        npc("pip", "Pip", "companion", look("child", "#e0b030", "#2a9a8a", "#f05030", 1, hat="cap"), [
            br(["!member:pip"], [
                "Hi! I'm Pip! Fastest courier in Kitefall! Well. Fastest walking courier now.",
                "Captain Rook's sky pirates stole my glider-wings. They hide in the Hollow Winds Cave, off the Whistling Heights.",
                "I'm really good with a bow, though. Really, really good. Want to see?"],
               ask={"q": "Let Pip join your party?",
                    "yes": {"say": ["PIP: \"YES! Okay! Let's go! Which way? I'll race you!\"",
                                    "Pip joined the party! Captain Rook nests in the Hollow Winds Cave."],
                            "do": ["recruit:pip", "quest:comp_wind", "sfx:recruit"]},
                    "no": {"say": ["PIP: \"Aw. Okay! I'll be right here! Running in circles!\""]}}),
        ], cond=["!member:pip"]),
        npc("amsel", "Bellkeeper Amsel", "side", look("man", "#a0a0a0", "#4a6a5a", "#d0c060", 1, hat="wide"), [
            br(["q:side_wind=none"], [
                "The wind-bells! Someone stole the wind-bells! Kitefall has rung them for three hundred years!",
                "An elf called Sylvane. She's selling silence to Corvane. She's out in the Whistling Heights.",
                "Bring them home and you'll have my Zephyr Band. It rings when you run."],
               ["quest:side_wind"]),
            br(["q:side_wind=active", "!item:wind_bells"], ["Sylvane is somewhere in the Whistling Heights. Follow the silence."]),
            br(["q:side_wind=ready"], [
                "Ohhh. Hear them? Even without wind, they're trying. Bless you.",
                "Here's the Zephyr Band. Run often."],
               ["take:wind_bells", "done:side_wind", "give:gear:zephyr_band", "sfx:chest"]),
            br(["q:side_wind=done"], ["The bells ring every hour now. Some neighbors complain. I ring them louder."]),
        ]),
        npc("wick", "Wick", "story", look("child", "#2a1a0a", "#c0a040", "#3a6ab0", 2), [
            br([], [
                "Do you know about shadows? I know everything about shadows.",
                "At the end of the day, the shadow of the lone windmill out in the Heights gets SO long.",
                "I paced it once. Five whole steps from the bottom of the windmill to the end of the shadow!",
                "And right at the end of the shadow there was something sparkly in the ground. I was too scared to dig. It might have been a bug."]),
        ]),
        npc("lark", "Lark", "key", look("child", "#d06030", "#8a5ab0", "#f0e0a0", 0), [
            br(["q:key_wind=none"], [
                "My grandpa made the very first kite in Kitefall. He flew it into the Hollow Winds Cave and it never came out.",
                "He says it doesn't matter, but he looks at the cave every day.",
                "If you find it, I'll give you grandpa's key! He says it opens 'a door that breathes.' Weird, right?"],
               ["quest:key_wind"]),
            br(["q:key_wind=active", "!item:first_kite"], ["The Hollow Winds Cave is west of the Whistling Heights!"]),
            br(["q:key_wind=ready"], [
                "That's IT! Grandpa! GRANDPA!",
                "Here's the Key of Breath. Grandpa says thank you. He's crying a little. He says it's the wind."],
               ["take:first_kite", "done:key_wind", "give:key_breath", "sfx:key"]),
            br(["q:key_wind=done"], ["Grandpa flies his kite every day now. It has a lot of patches. It still flies."]),
        ]),
        shopkeeper("pawn_wind_k", "Pawnbroker Finch", "pawn", look("woman", "#3a6a3a", "#5a7a6a", "#e0e0e0", 1), "pawn_wind",
                   "Light gear for light feet. Everything here weighs less than your worries."),
        shopkeeper("items_wind_k", "Tonic-Seller Hob", "items", look("man", "#8a6a3a", "#6a8a3a", "#f0c040", 2, hat="cap"), "items",
                   "Stamina tonics! Speed in a bottle! Also regular potions, if you're boring."),
        innkeeper("inn_wind_k", "Innkeeper Dove", "inn", look("woman", "#f0f0f0", "#a0c0c0", "#e08080", 0), 20,
                  "The Updraft Inn. Our beds are stuffed with cloud-down. Real cloud."),
        npc("wind_f1", "Kite Flier", "flavor1", look("man", "#c0a060", "#3a8aaa", "#f0f0f0", 0), [
            br([], ["Gale beasts are all air and speed. Burn 'em. Fire eats wind."])], wander=True),
        npc("wind_f2", "Retired Guard", "flavor2", look("guard", "#6a6a6a", "#3a6a6a", "#c0c0c0", 1, hat="helm"), [
            br([], ["Fast enemies get more turns. Simple as that. If they're quicker than you, drink a Stamina Tonic."])]),
        npc("wind_f3", "Dreamy Child", "flavor3", look("child", "#f0d080", "#e080a0", "#ffffff", 0), [
            br([], ["When I grow up I'm going to be a bird. Mom says that's not a job. Birds don't have jobs. That's the point."])], wander=True),
        npc("wind_f4", "Grumpy Farmer", "flavor4", look("man", "#4a4a2a", "#7a6a3a", "#a0a0a0", 2, beard=True), [
            br([], ["No wind, no windmills. No windmills, no flour. No flour, no bread. I'm hungry and it's Corvane's fault."])]),
    ],
    "pawn_stock": ["gale_sabre", "swift_bow", "sky_staff", "featherweave", "wind_ring", "iron_sword", "short_bow", "oak_staff"],
}

# ============================== STONE: Gravenhold — corruption ==============================
quest("main_stone", "The Gilded King", "stone", "main", "Union Elder Marta",
      "King Ostrum sold the mountain's heart for gold and turned to gilded stone. He rules from the Gilded Throne.", "flag:beat_ostrum")
quest("comp_stone", "The Buried Crew", "stone", "companion", "Durga",
      "Durga's mining crew is trapped below the Glimmering Seam by Gravelmaw, a beast of the deep rock.", "flag:beat_gravelmaw")
quest("side_stone", "Rust in the Veins", "stone", "side", "Breck",
      "The Iron Overseer runs a forced dig in Rustvein Canyon. Breck wants him gone.", "flag:beat_iron_overseer")
quest("key_stone", "Garrick's Lucky Pick", "stone", "key", "Garrick",
      "Old Garrick dropped his lucky pick in the Glimmering Seam.", "item:lucky_pick")

WORLDS["stone"] = {
    "name": "Gravenhold", "town": "Copperdeep", "field": "Rustvein Canyon", "cave": "Glimmering Seam", "dungeon": "The Gilded Throne",
    "landmark": "a giant split geode", "riddle_offset": (0, -2), "flip": True, "seed": 404,
    "summon": "basaltus", "boss": "ostrum", "boss_flag": "beat_ostrum", "main_quest": "main_stone",
    "boss_pre": ["A king sits on a throne of coins. Gold runs in veins across his stone skin like a disease.",
                 "OSTRUM: \"Do you know what a mountain is worth? I do. To the copper. I had it appraised.\"",
                 "OSTRUM: \"Everything has a price. Let's find yours.\""],
    "boss_post": ["The gold flakes away. Underneath, King Ostrum is plain grey granite, cracked and very old.",
                  "OSTRUM: \"...I was a miner, once. Before the crown. I liked the smell of rock.\"",
                  "The Stone Heartstone is clean granite again, with no gold in it."],
    "mini_companion": {"id": "gravelmaw", "where": "cave", "flag": "beat_gravelmaw", "quest": "comp_stone",
                       "pre": ["A massive beast of grinding stone blocks a collapsed tunnel. Behind it, you hear voices calling for help.",
                               "DURGA: \"Hold on, lads! The foreman's here, and she's brought friends.\""],
                       "post": ["Gravelmaw crumbles. The tunnel opens, and twelve dusty miners stumble out cheering.",
                                "DURGA: \"Every one of them. Every single one.\" She hands you her family's old axe. \"You've earned the weight.\""],
                       "reward": "flintmantle_axe"},
    "mini_side": {"id": "iron_overseer", "where": "field", "flag": "beat_iron_overseer", "quest": "side_stone",
                  "pre": ["A figure in sleek future-armor stands over a chain-gang of exhausted miners.",
                          "OVERSEER: \"Quota is quota. The king wants more gold, the king gets more gold.\""],
                  "post": ["The Overseer's armor sparks and dies. The chained miners shake loose and run for Copperdeep."]},
    "key_chest_item": "lucky_pick",
    "chests": {"field": ["potion:2", "gear:bedrock_bow", "ether"], "cave": ["hi_potion", "gear:quartz_staff"],
               "dungeon": ["ward_elixir", "feather", "elixir"]},
    "hidden_item": "geode_heart",
    "npcs": [
        npc("marta", "Union Elder Marta", "elder", look("elder", "#a0a0a0", "#4a5a3a", "#d0a040", 2), [
            br(["q:main_stone=none"], [
                "Copperdeep used to mine to live. Now we mine for King Ostrum's hoard, and we never stop.",
                "He sold the Heart of Stone to the gold in the deep veins. The gold got into him. Now it's getting into everyone.",
                "The greedy ones go first. Then the tired ones. Then everyone else.",
                "He sits in the Gilded Throne at the end of Rustvein Canyon. End this."],
               ["quest:main_stone"]),
            br(["q:main_stone=active", "!flag:beat_ostrum"], [
                "The Gilded Throne is beyond Rustvein Canyon.",
                "Stone things crumble in the wind. Erosion's the oldest weapon there is."]),
            br(["q:main_stone=ready"], [
                "The gold's gone out of the walls. I can see real rock again. Beautiful, plain rock.",
                "The Stone Heartstone is yours, and the union's thanks. And this, which we're not calling a bribe."],
               ["done:main_stone", "give:heart_stone", "gold:600", "give:ward_elixir:2"]),
            br(["q:main_stone=done"], ["We voted to mine half as much and nap twice as much. It passed unanimously."]),
        ]),
        npc("durga", "Durga", "companion", look("woman", "#8a3a1a", "#5a6a3a", "#c0c0c0", 2, hat="helm"), [
            br(["!member:durga"], [
                "Durga Flintmantle. Foreman. My crew went into the Glimmering Seam on the king's orders. Twelve of them.",
                "A cave-in. And behind it, something that grinds. They're alive. I can hear them knocking.",
                "I hold the line. That's what I do. I'll hold it for you, too, if you help me dig."],
               ask={"q": "Let Durga join your party?",
                    "yes": {"say": ["DURGA: \"Right. Helmets on. We're going down.\"",
                                    "Durga joined the party! Gravelmaw blocks the tunnel deep in the Glimmering Seam."],
                            "do": ["recruit:durga", "quest:comp_stone", "sfx:recruit"]},
                    "no": {"say": ["DURGA: \"I'll keep knocking back to them. Don't take too long.\""]}}),
        ], cond=["!member:durga"]),
        npc("breck", "Breck", "side", look("man", "#3a2a1a", "#6a4a2a", "#a04030", 1, beard=True), [
            br(["q:side_stone=none"], [
                "Name's Breck. Union organizer. The king's got an Overseer running a chain-gang in Rustvein Canyon.",
                "Future-armor, they say. Shrugs off swords. But stone-born things can't stand a hard wind.",
                "Break those chains and I'll give you the Rootstone Ring. The union's been saving it for a hero. You'll do."],
               ["quest:side_stone"]),
            br(["q:side_stone=active", "!flag:beat_iron_overseer"], ["The Overseer's out in Rustvein Canyon. Bring the wind."]),
            br(["q:side_stone=ready"], [
                "They're home! All of them, and they're already complaining about the food. Perfect.",
                "The Rootstone Ring. Wear it with pride."],
               ["done:side_stone", "give:gear:rootstone_ring", "sfx:chest"]),
            br(["q:side_stone=done"], ["Solidarity, friend. Solidarity."]),
        ]),
        npc("old_vein", "Retired Prospector", "story", look("elder", "#d0d0d0", "#5a4a3a", "#90a060", 1, hat="cap", beard=True), [
            br([], [
                "Forty years I prospected these hills. Want to know rule one?",
                "Never dig where the gold tells you. Gold lies. Dig where the moss grows.",
                "Moss only grows on the cold side of things. Take that big split geode out in the canyon.",
                "Two strides out from its cold side, I left something there for whoever listened. Nobody ever listens."]),
        ]),
        npc("garrick", "Old Garrick", "key", look("elder", "#8a8a8a", "#3a3a3a", "#d09030", 2, beard=True), [
            br(["q:key_stone=none"], [
                "Lost my lucky pick in the Glimmering Seam. Fifty years I swung that thing. Never had a cave-in.",
                "First day without it, the Seam collapsed. Coincidence? Maybe. Get it back anyway.",
                "I'll trade you for it: an old key I dug up from the deepest bedrock. Felt wrong to keep it."],
               ["quest:key_stone"]),
            br(["q:key_stone=active", "!item:lucky_pick"], ["Glimmering Seam. West of Rustvein Canyon."]),
            br(["q:key_stone=ready"], [
                "Ha! There she is. Chipped, ugly, lucky.",
                "The Key of Bedrock. Whatever it opens, it's deep. Deeper than rock."],
               ["take:lucky_pick", "done:key_stone", "give:key_bedrock", "sfx:key"]),
            br(["q:key_stone=done"], ["No cave-ins since I got it back. Science."]),
        ]),
        shopkeeper("pawn_stone_k", "Pawnbroker Ingot", "pawn", look("man", "#c08030", "#5a5a5a", "#d0a040", 1, beard=True), "pawn_stone",
                   "Solid gear. Solid prices. No gold, though. We don't trust it anymore."),
        shopkeeper("items_stone_k", "Chemist Lode", "items", look("woman", "#2a2a2a", "#4a6a4a", "#e0e060", 2, hat="hood"), "items",
                   "Ironbark Draught's the local favorite. Toughens you right up."),
        innkeeper("inn_stone_k", "Innkeeper Tuff", "inn", look("man", "#6a4a2a", "#7a6a5a", "#c0c0c0", 2), 20,
                  "The Bedrock Bunks. Hard beds. Builds character."),
        npc("stone_f1", "Tired Miner", "flavor1", look("man", "#2a2a2a", "#5a5a4a", "#c08040", 1, hat="helm"), [
            br([], ["Granite beasts out in the canyon? Wind wears them down. Everything gets worn down eventually."])], wander=True),
        npc("stone_f2", "Union Guard", "flavor2", look("guard", "#4a3a2a", "#5a6a4a", "#c0c0c0", 2, hat="helm"), [
            br([], ["Future Knights shrug off steel. Their armor hates magic, though. Remember that."])]),
        npc("stone_f3", "Miner's Kid", "flavor3", look("child", "#4a2a1a", "#7a6a4a", "#e0e040", 2, hat="helm"), [
            br([], ["I found a shiny rock! Dad made me throw it away. He said shiny rocks make people mean."])], wander=True),
        npc("stone_f4", "Former Courtier", "flavor4", look("man", "#d0c080", "#8a6a2a", "#f0e080", 0), [
            br(["!flag:beat_ostrum"], ["I was a courtier. I polished gold. Every day the king asked, 'Is it enough?' It never was."]),
            br([], ["I polish rocks now. Ordinary rocks. They don't ask for anything."])]),
    ],
    "pawn_stock": ["granite_axe", "flint_bow", "geode_staff", "stoneplate", "stone_ring", "iron_sword", "short_bow", "oak_staff"],
}

# ============================== SPIRIT: Luminael — self-actualization ==============================
quest("main_spirit", "The Unfinished", "spirit", "main", "Abbess Clare",
      "Iris, a saint who could never finish becoming herself, reshapes everyone in the Ascent of the Unfinished.", "flag:beat_iris")
quest("comp_spirit", "The Hollow Mirror", "spirit", "companion", "Sol",
      "In the Mirror Caves, a mirror shows Sol a self that isn't his. He has to face it.", "flag:beat_mirror_wraith")
quest("side_spirit", "The Pilgrim's Lantern", "spirit", "side", "Pilgrim Maud",
      "A great bear eats the lanterns pilgrims carry through the Fields of Becoming.", "flag:beat_penitent_bear")
quest("omni_spirit", "The Witness", "spirit", "omni", "the sealed door",
      "Behind a door in the Ascent waits Aeon, the Witness. It needs the Keys of Memory and Breath, and four of you.", "flag:beat_aeon")

WORLDS["spirit"] = {
    "name": "Luminael", "town": "Hallowmere", "field": "Fields of Becoming", "cave": "Mirror Caves", "dungeon": "Ascent of the Unfinished",
    "landmark": "a weeping angel statue", "riddle_offset": (3, 0), "flip": False, "seed": 505,
    "summon": "lanternmoth", "boss": "iris", "boss_flag": "beat_iris", "main_quest": "main_spirit",
    "boss_pre": ["A woman of white light kneels over half-carved statues of people. Their faces are blank.",
                 "IRIS: \"Everyone could be so much MORE. I can see it. I just need to keep carving.\"",
                 "IRIS: \"I'll start with you. Hold still. I can almost see who you're supposed to be.\""],
    "boss_post": ["Iris's chisel falls. She looks at her hands, which are also unfinished.",
                  "IRIS: \"...If I'm never finished, then I never have to be judged. That was it. That was always it.\"",
                  "She lets herself be what she is, just for now. The Spirit Heartstone begins, very slowly, to become."],
    "mini_companion": {"id": "mirror_wraith", "where": "cave", "flag": "beat_mirror_wraith", "quest": "comp_spirit",
                       "pre": ["A tall mirror stands in the dark. In it, Sol is wearing a crown and smiling coldly.",
                               "THE MIRROR: \"This is who you were going to be. Powerful. Admired. Why did you stop?\"",
                               "SOL: \"I don't know. Maybe because I didn't want to be you.\""],
                       "post": ["The mirror cracks. In the pieces, a dozen different Sols, none of them crowned.",
                                "SOL: \"I don't remember who I was. But I get to choose who I am. That's better.\"",
                                "He offers you his prayer-bead staff. \"Each bead is a choice. Make good ones.\""],
                       "reward": "prayer_staff"},
    "mini_side": {"id": "penitent_bear", "where": "field", "flag": "beat_penitent_bear", "quest": "side_spirit",
                  "pre": ["A great bear glows from the inside, its belly full of swallowed lanterns.",
                          "It looks sorry. It eats another lantern anyway."],
                  "post": ["The bear coughs up a dozen lanterns and pads away, lighter and dimmer and somehow happier."]},
    "chests": {"field": ["potion:2", "gear:candle_mail", "ether"], "cave": ["hi_potion", "gear:vigil_blade"],
               "dungeon": ["sage_elixir", "feather", "elixir"]},
    "hidden_item": "wing_of_dawn",
    "seal": {"keys": ["key_memory", "key_breath"], "flag": "open_sanctum_spirit", "omni": "aeon", "omni_flag": "beat_aeon",
             "quest": "omni_spirit",
             "locked": ["A great white door. Two keyholes: one shaped like a memory, one shaped like a breath.",
                        "Carved beneath them, four figures hold hands. A door for four, then."],
             "open": ["The Keys of Memory and Breath turn together. The door sighs open onto light."],
             "pre": ["Something vast fills the sanctum. It is mostly eyes, and all of them are kind, and all of them are looking at you.",
                     "AEON: \"I have witnessed every life that has ever been lived. I am witnessing yours now.\"",
                     "AEON: \"Show me what you have become. All four of you. Hold nothing back; I will see it anyway.\""],
             "post": ["The eyes close one by one, satisfied.",
                      "AEON: \"Seen. Fully seen. I will come when you call, little Kindler.\"",
                      "You can now summon Aeon, the Witness!"]},
    "npcs": [
        npc("clare", "Abbess Clare", "elder", look("elder", "#f0f0f0", "#e0e0f0", "#e0c050", 0, hat="hood"), [
            br(["q:main_spirit=none"], [
                "Welcome to Hallowmere, where people come to become who they are meant to be.",
                "Our saint, Iris, helped them. She saw the best self in everyone and carved it out.",
                "But she could never see her own. So she never stopped carving. Now no one in Luminael is allowed to finish.",
                "She is at the top of the Ascent of the Unfinished. Please. Let her rest."],
               ["quest:main_spirit"]),
            br(["q:main_spirit=active", "!flag:beat_iris"], [
                "The Ascent is beyond the Fields of Becoming.",
                "Spirit and Void are each other's undoing. Bring the dark to fight the light."]),
            br(["q:main_spirit=ready"], [
                "I feel... finished. For today. That's all anyone needs, isn't it? To be finished for today.",
                "Take the Spirit Heartstone, and my blessing."],
               ["done:main_spirit", "give:heart_spirit", "gold:500", "give:elixir"]),
            br(["q:main_spirit=done"], ["Iris teaches sculpture now. Her students are told to stop when it's good enough."]),
        ]),
        npc("sol", "Sol", "companion", look("man", "#1a1a1a", "#e0d0a0", "#c04040", 1), [
            br(["!member:sol"], [
                "Peace to you. I am Sol. At least, that is the name on my robe.",
                "I woke one morning and could not remember who I had been trying to become. Everything I had worked toward was simply gone.",
                "There is a mirror in the Mirror Caves that shows people their true selves. I'm afraid to look. I'd be less afraid with company."],
               ask={"q": "Let Sol join your party?",
                    "yes": {"say": ["SOL: \"Thank you. Whoever I turn out to be, I think he'd like you.\"",
                                    "Sol joined the party! The Hollow Mirror waits in the Mirror Caves."],
                            "do": ["recruit:sol", "quest:comp_spirit", "sfx:recruit"]},
                    "no": {"say": ["SOL: \"Of course. I'll meditate on it. It's what I do instead of deciding.\""]}}),
        ], cond=["!member:sol"]),
        npc("maud", "Pilgrim Maud", "side", look("woman", "#8a6a4a", "#a09070", "#f0e080", 1, hat="hood"), [
            br(["q:side_spirit=none"], [
                "Pilgrims carry a lantern through the Fields of Becoming. It's the light of who they hope to be.",
                "But a great bear has started eating them. Lanterns, not pilgrims. Mostly.",
                "Make it stop and I'll give you the Halo Circlet. It was meant for a saint. I think you'll do."],
               ["quest:side_spirit"]),
            br(["q:side_spirit=active", "!flag:beat_penitent_bear"], ["The bear wanders the Fields of Becoming. It glows. You can't miss it."]),
            br(["q:side_spirit=ready"], [
                "The pilgrims are walking again, and their lanterns are lit.",
                "The Halo Circlet. Wear it humbly. Or don't. It's very shiny."],
               ["done:side_spirit", "give:gear:halo_circlet", "sfx:chest"]),
            br(["q:side_spirit=done"], ["Every lantern that passes is a person deciding to keep going."]),
        ]),
        npc("brother_ash", "Brother Tobin", "story", look("man", "#6a4a2a", "#d0c0a0", "#a08040", 1), [
            br([], [
                "There is an angel statue in the Fields. She weeps, always, for someone she lost.",
                "She faces the sunrise, because that's where he left from. She's waiting for him to come back.",
                "Her tears run down and pool three paces in front of her face. The grass there is greener than anywhere else.",
                "I used to sit there to pray. I found it peaceful. Something under the grass hums, I think. Probably my imagination."]),
        ]),
        npc("seer_hal", "Blind Seer Hal", "key", look("elder", "#c0c0c0", "#4a4a8a", "#f0f0f0", 0, beard=True), [
            br(["!item:key_memory", "!item:key_breath", "!flag:open_sanctum_spirit"], [
                "Behind a white door in the Ascent sleeps Aeon, the Witness, which has seen every life ever lived.",
                "The door wants two keys. One remembers. One breathes. Seek the old man of the sea and the child of the kites.",
                "And the Witness will only open its eyes for four. Bring a full company."]),
            br(["!flag:open_sanctum_spirit"], ["Memory and Breath. Four companions. Then the Witness will see you."]),
            br([], ["You have been seen. Few can bear it."]),
        ]),
        shopkeeper("pawn_spirit_k", "Pawnbroker Halcyon", "pawn", look("man", "#f0e0a0", "#c0c0e0", "#f0f0f0", 0), "pawn_spirit",
                   "Blessed blades, holy bows. Discounts for the recently enlightened."),
        shopkeeper("items_spirit_k", "Sister Wren", "items", look("woman", "#3a2a1a", "#e0e0e0", "#80a0e0", 1, hat="hood"), "items",
                   "Phoenix Feathers are our specialty. Everyone deserves a second chance."),
        innkeeper("inn_spirit_k", "Innkeeper Grace", "inn", look("woman", "#c08040", "#e0d0c0", "#f0c0c0", 0), 20,
                  "The Quiet Room. No talking after sundown. Or before. Mostly no talking."),
        npc("spirit_f1", "Meditating Monk", "flavor1", look("man", "#1a1a1a", "#e0c080", "#c04040", 2), [
            br([], ["The Lumen creatures are made of light. Darkness undoes them. Void, if you have it."])]),
        npc("spirit_f2", "Pilgrim", "flavor2", look("woman", "#6a4a2a", "#8a8a6a", "#f0e080", 1, hat="hood"), [
            br([], ["Ghosts here are half-light. Swords barely scratch them. Magic, friend. Magic."])], wander=True),
        npc("spirit_f3", "Curious Novice", "flavor3", look("child", "#e0c070", "#e0e0e0", "#a0c0f0", 0), [
            br([], ["The Abbess says I'm becoming a monk. I think I'm becoming hungry."])], wander=True),
        npc("spirit_f4", "Sculptor's Apprentice", "flavor4", look("man", "#8a3a1a", "#a0a0a0", "#d0d0d0", 1), [
            br(["!flag:beat_iris"], ["Iris told me my statue wasn't done. I've been carving the same nose for six years."]),
            br([], ["I finished my statue! It's not good. But it's DONE."])]),
    ],
    "pawn_stock": ["dawn_blade", "halo_bow", "lumen_staff", "pilgrim_vestments", "spirit_ring", "iron_sword", "short_bow", "oak_staff"],
}

# ============================== VOID: The Hollow — dissociation ==============================
quest("main_void", "Nobody Home", "void", "main", "Lamplighter Ines",
      "A man named Aldous stepped out of himself to escape his pain. What's left, Nobody, haunts the Unmoored Keep.", "flag:beat_nobody")
quest("comp_void", "The Name-Eater", "void", "companion", "Vesper",
      "Vesper's true name was eaten by the Name-Eater in the Echo Pits.", "flag:beat_name_eater")
quest("side_void", "Echo of a Song", "void", "side", "Lio",
      "The Mute Paladin stole every song in Lastlight. He walks The Drift.", "flag:beat_mute_paladin")
quest("omni_void", "The Throne of Nothing", "void", "omni", "the sealed door",
      "Behind a door in the Unmoored Keep sits Nihil, the Unmaker. It needs the Keys of Ash and Bedrock, and four of you.", "flag:beat_nihil")

WORLDS["void"] = {
    "name": "The Hollow", "town": "Lastlight", "field": "The Drift", "cave": "Echo Pits", "dungeon": "The Unmoored Keep",
    "landmark": "a door standing alone", "riddle_offset": (0, -4), "flip": True, "seed": 606,
    "summon": "umbrahound", "boss": "nobody", "boss_flag": "beat_nobody", "main_quest": "main_void",
    "boss_pre": ["A man stands at the window of the Keep, looking at nothing. You can see the room through him.",
                 "NOBODY: \"Oh. Visitors. I'd get up, but I'm not really... in here, at the moment.\"",
                 "NOBODY: \"It doesn't hurt if you're not there for it. You should try it. Let me show you.\""],
    "boss_post": ["Nobody flickers, then fills in, like ink soaking into paper. He's a man again. He's crying.",
                  "ALDOUS: \"It hurts. Oh, it hurts. ...But I can feel the floor. I forgot there was a floor.\"",
                  "The Void Heartstone goes quiet, but it's the quiet of someone who's still there."],
    "mini_companion": {"id": "name_eater", "where": "cave", "flag": "beat_name_eater", "quest": "comp_void",
                       "pre": ["Something made of crumpled paper and teeth crouches in the pit, chewing.",
                               "THE NAME-EATER: \"Mmm. Vesper. That's not your name. That's what you're called. Different taste.\"",
                               "VESPER: \"Give it back. I want to know who's been walking around in my body.\""],
                       "post": ["The Name-Eater unravels into a thousand scraps of names. One flutters to Vesper. She folds it small.",
                                "VESPER: \"...I'm not going to read it yet. Just knowing I have it is enough.\"",
                                "She presses a bow into your hands. \"Found it in the pit. Nobody remembers whose. Fitting.\""],
                       "reward": "unremembered_bow"},
    "mini_side": {"id": "mute_paladin", "where": "field", "flag": "beat_mute_paladin", "quest": "side_void",
                  "pre": ["A knight in black armor stands in the Drift, surrounded by a silence so thick you can't hear your own steps.",
                          "He raises his shield. He doesn't say anything. He can't."],
                  "post": ["The paladin's helm cracks. Every song he stole spills out at once, in a joyful, chaotic chorus."]},
    "chests": {"field": ["potion:2", "gear:gloom_ring", "ether"], "cave": ["hi_potion", "gear:echo_staff"],
               "dungeon": ["sage_elixir", "feather", "elixir"]},
    "hidden_item": "key_to_nowhere",
    "seal": {"keys": ["key_ash", "key_bedrock"], "flag": "open_sanctum_void", "omni": "nihil", "omni_flag": "beat_nihil",
             "quest": "omni_void",
             "locked": ["A black door with no handle. Two keyholes: one smells of ash, one is cold as bedrock.",
                        "Scratched into it: four lines, holding each other up. A door for four, then."],
             "open": ["The Keys of Ash and Bedrock turn. The door doesn't open so much as stop existing."],
             "pre": ["There is nothing here. The nothing is enormous, and it notices you.",
                     "NIHIL: \"Before the first star, I was here. After the last, I will be here. You are a brief interruption.\"",
                     "NIHIL: \"Interrupt me, then. All four of you. Let me see if you are louder than nothing.\""],
             "post": ["The nothing folds up, small enough to hold.",
                      "NIHIL: \"...Louder than nothing. Well. That is something. Call, and I will unmake for you.\"",
                      "You can now summon Nihil, the Unmaker!"]},
    "npcs": [
        npc("ines", "Lamplighter Ines", "elder", look("woman", "#3a2a4a", "#2a2a3a", "#f0c060", 1, hat="hood"), [
            br(["q:main_void=none"], [
                "You can see me? Good. In Lastlight, people are starting to drift. You look at them and they're just... a little bit somewhere else.",
                "It started with Aldous. He lost too much, too fast, so he stepped out of himself. Left his body to walk around empty.",
                "We call what's left Nobody. And the emptiness is catching. It's in the Unmoored Keep, past The Drift.",
                "Bring him back. Or bring us back. I don't know which one it is anymore."],
               ["quest:main_void"]),
            br(["q:main_void=active", "!flag:beat_nobody"], [
                "The Unmoored Keep is past The Drift. Watch for when he goes 'elsewhere' — steel can't touch him then. Magic can.",
                "Void-touched things fear the light. Spirit undoes them."]),
            br(["q:main_void=ready"], [
                "People are... here again. All of them. Crying, laughing. Being in the room.",
                "The Void Heartstone. Thank you for not drifting."],
               ["done:main_void", "give:heart_void", "gold:500", "give:elixir"]),
            br(["q:main_void=done"], ["Aldous lights the lamps with me now. Some nights are hard. He stays for them anyway."]),
        ]),
        npc("vesper", "Vesper", "companion", look("woman", "#d0d0e0", "#4a2a6a", "#a060f0", 0), [
            br(["!member:vesper"], [
                "Huh. You're looking right at me. Most people look at where I was a second ago.",
                "I'm Vesper. Or that's what I'm called. My real name got eaten. Literally. There's a thing in the Echo Pits that eats names.",
                "I watch myself from about three feet away, most days. It's useful in a fight, actually. I always see it coming."],
               ask={"q": "Let Vesper join your party?",
                    "yes": {"say": ["VESPER: \"Okay. I'm in. Both of me.\"",
                                    "Vesper joined the party! The Name-Eater lurks in the Echo Pits."],
                            "do": ["recruit:vesper", "quest:comp_void", "sfx:recruit"]},
                    "no": {"say": ["VESPER: \"Sure. I'll be over here. Ish.\""]}}),
        ], cond=["!member:vesper"]),
        npc("lio", "Lio the Singer", "side", look("man", "#c06030", "#6a3a8a", "#f0e0a0", 0, hat="wide"), [
            br(["q:side_void=none"], [
                "  ...  ",
                "Sorry. I was trying to sing. I can't. Nobody can. The Mute Paladin took every song in Lastlight.",
                "He walks The Drift in black armor, wrapped in silence. If you break it, I'll give you my cloak. It's woven from rests between notes."],
               ["quest:side_void"]),
            br(["q:side_void=active", "!flag:beat_mute_paladin"], ["The Paladin is somewhere in The Drift. Listen for where it's quietest."]),
            br(["q:side_void=ready"], [
                "LA LA LAAA! Oh, it's back! It's all back! I'm going to sing for a week!",
                "The Nullweave Cloak. Every silence in it is the good kind."],
               ["done:side_void", "give:gear:nullweave_cloak", "sfx:chest"]),
            br(["q:side_void=done"], ["(Lio is singing. Loudly. Constantly. Lastlight seems to forgive him.)"]),
        ]),
        npc("whisper", "The Doorwatcher", "story", look("elder", "#606060", "#2a2a3a", "#9060c0", 1, hat="hood"), [
            br([], [
                "In Lastlight we have a saying. 'The door opens to nowhere, so walk around it.'",
                "There's a door out in The Drift, standing all alone. No walls. It faces us, here in town, like it's waiting for someone to come home.",
                "Behind it, on the side it doesn't face, you take one step for every word of what you whisper to yourself on bad days.",
                "Mine is 'I am still here.' You figure out the rest."]),
        ]),
        npc("void_seer", "Hollow-Eyed Woman", "key", look("woman", "#202020", "#3a2a4a", "#9050e0", 2), [
            br(["!item:key_ash", "!item:key_bedrock", "!flag:open_sanctum_void"], [
                "There is a throne in the Unmoored Keep with nothing sitting on it. The nothing is Nihil.",
                "Its door takes two keys. One was burned. One was buried. A widow and a miner hold them, in other worlds.",
                "And four must stand together before the Unmaker, or it won't even notice you."]),
            br(["!flag:open_sanctum_void"], ["Ash and Bedrock. Four together. Then the nothing will listen."]),
            br([], ["You were louder than nothing. I heard it from here."]),
        ]),
        shopkeeper("pawn_void_k", "Pawnbroker Null", "pawn", look("man", "#101010", "#2a2a3a", "#9050e0", 1), "pawn_void",
                   "Things nobody remembers buying. Yours now. Probably."),
        shopkeeper("items_void_k", "Apothecary Shade", "items", look("woman", "#c0c0d0", "#3a2a4a", "#60c0a0", 0, hat="hood"), "items",
                   "Potions. Ethers. Something to keep you in your body."),
        innkeeper("inn_void_k", "Innkeeper Hush", "inn", look("man", "#4a4a5a", "#3a3a4a", "#c0c0c0", 1), 20,
                  "The Anchor. We tie a string to your toe so you don't drift in your sleep."),
        npc("void_f1", "Flickering Man", "flavor1", look("man", "#3a3a3a", "#4a4a6a", "#a0a0a0", 2), [
            br([], ["Null beasts can't stand the light. Spirit, if you've got it. It makes them... more there. Then they break."])], wander=True),
        npc("void_f2", "Anchored Guard", "flavor2", look("guard", "#2a2a2a", "#3a2a4a", "#a0a0c0", 1, hat="helm"), [
            br([], ["If someone's silenced, they can't cast. Items still work. Keep potions handy."])]),
        npc("void_f3", "Child Holding a String", "flavor3", look("child", "#6a4a2a", "#5a3a7a", "#f0f040", 1), [
            br([], ["I hold this string so I don't float away. It's tied to my mom. She holds a string tied to me. It works."])], wander=True),
        npc("void_f4", "Quiet Scholar", "flavor4", look("man", "#8a8a8a", "#2a2a4a", "#d0c080", 0, beard=True), [
            br([], ["Every world has the same sky above it. The sun sets in the west. The cold lives in the north.",
                    "Useful if you're ever following an old story somewhere."])]),
    ],
    "pawn_stock": ["null_edge", "hollow_bow", "abyss_staff", "shadeweave", "void_ring", "iron_sword", "short_bow", "oak_staff"],
}

# ============================== NEXUS (hub) ==============================
NEXUS_NPCS = [
    npc("keeper", "The Keeper", None, look("elder", "#f0f0f0", "#3a3a5a", "#f0d060", 0, hat="hood", beard=True), [
        br(["!flag:intro_done"], [
            "Ah. You're awake. Good. I was beginning to worry the portal had dropped you on your head.",
            "This is the Nexus, the crossroads between six worlds: Fire, Water, Wind, Stone, Spirit and Void.",
            "Each world has a Heart. And King Goblin's shamans have cursed every one of them with a feeling it can't put down.",
            "A sad world is an easy world to rob. That's all he wants: everything shiny, everywhere.",
            "Fire burns with jealousy. Water drowns in loss. Stone is rotting with greed. Wind is caged by fear of freedom.",
            "Spirit can't finish becoming. And Void has stopped being present at all.",
            "You're a Kindler. You have no element of your own, but you carry the element of whatever you wear. Weapons, armor, charms.",
            "Wear fire and you'll glow red. Wear water and you'll glow blue. Wear many, and you'll glow many colors. The stronger you grow, the brighter.",
            "Go through any portal, in any order. Free all six Hearts and the curses will lead us straight to King Goblin.",
            "The worlds will rise to meet your strength. Watch out for his goblins. They're everywhere now. And pirates near the water.",
            "Talk to people. Everyone, everywhere. You'd be surprised what a rambling story is hiding.",
            "Press X or Esc to open your menu. Take these. And come back to rest here whenever you like."],
           ["set:intro_done", "give:potion:4", "give:ether:2", "sfx:chest"]),
        br(["hearts>=6", "!flag:beat_king_goblin"], [
            "Six Heartstones. Six feelings, felt all the way through and set down.",
            "That's not defeating feelings, you know. That's what it looks like to feel them properly.",
            "And look: every Heartstone has the same little scratch on it. A goblin's mark. They all point the same way.",
            "King Goblin's Warren. I can open the way with the Heartstones. Get ready first: buy what you need, rest, choose your party.",
            "He's sly, he's greedy, and he has no shame at all. Spirit cuts through his dark crown best."],
           ask={"q": "Enter King Goblin's Warren?",
                "yes": {"say": ["The six Heartstones flare. The floor of the Nexus opens into a tunnel that smells like old cheese."],
                        "do": ["warp:goblin_warren"]},
                "no": {"say": ["Take your time. He isn't going anywhere. Well. He might. But probably not."]}}),
        br(["flag:beat_king_goblin", "!flag:ending_seen"], [
            "You did it. King Goblin is gone, and the six Hearths are warm again.",
            "They have a name for you out there now, you know. The Goblin Slayer.",
            "...Of course, the Witness and the Unmaker are still out there, if you're the sort who can't leave well enough alone."],
           ["set:ending_seen", "end"]),
        br([], ["Rest whenever you need to. The Nexus is always safe.",
                "Remember: what you wear decides what you can cast, and what you're weak and strong against."],
           ask={"q": "Rest at the Nexus fire? (free)",
                "yes": {"say": ["The fire is warm. Everyone feels restored."], "do": ["inn:0"]},
                "no": {"say": []}}),
    ]),
    shopkeeper("nexus_shop", "Wandering Merchant", None, look("merchant", "#6a4a2a", "#5a3a6a", "#e0c040", 1, hat="wide"),
               "nexus", "I sell a little of everything, everywhere. Mostly here, though."),
    npc("nexus_compass", "Old Compass", None, look("man", "#c0c0c0", "#4a5a6a", "#e0e0e0", 2, beard=True), [
        br([], ["Every world in the Hearths shares the same sky. The sun rises in the east and sets in the west.",
                "The cold comes from the north. The warmth from the south. Remember that when old folks start telling stories."])],
        wander=False),
    npc("nexus_sage", "Element Sage", None, look("woman", "#3a2a1a", "#2a6a6a", "#f0f0f0", 1, hat="hood"), [
        br([], ["Water quenches Fire. Fire devours Wind. Wind erodes Stone. Stone dams Water.",
                "Spirit and Void undo each other.",
                "Strike a foe with what beats its element and it takes far more damage. Hit it with its own element, and it shrugs.",
                "Wear an element and you resist it, but you'll be weaker to whatever beats it. Everything has a price."])]),
    npc("nexus_vet", "Scarred Veteran", None, look("guard", "#4a3a2a", "#5a5a5a", "#c0a040", 2, hat="helm"), [
        br([], ["Take a beating and your Limit gauge fills. When it's full, you can unleash a Limit Break. Saved my life a dozen times.",
                "Speed's everything in a fight. The faster you are, the more often you act."])]),
]
