# Goblin Slayer

A pixel-art, turn-based RPG in the spirit of Chrono Trigger and Final Fantasy IV–VII, built in **Godot 4.5**.

You are Wren, a hooded **Kindler** with red eyes and an old scar: someone with no element of your own who carries the element of whatever you wear.
Six worlds hang around the Nexus. **King Goblin** has cursed each world's Heart with a feeling it can't put down, because a sad world is an easy world to rob. Free all six Hearts, follow the goblin marks into his Warren and end him. Out in the worlds, people start calling you something new: the Goblin Slayer.

| World | Town | Its Heart is cursed with | Boss |
|---|---|---|---|
| Cinderreach (Fire) | Emberfall | Jealousy | Vulkar, the Green Flame |
| Maretide (Water) | Saltmere | Loss | Maren, Mother of Tides |
| Skyreach (Wind) | Kitefall | Fear of freedom | Corvane, Keeper of Cages |
| Gravenhold (Stone) | Copperdeep | Corruption | King Ostrum, the Gilded |
| Luminael (Spirit) | Hallowmere | Never finishing becoming yourself | Iris, the Unfinished |
| The Hollow (Void) | Lastlight | Dissociation | Nobody |
| King Goblin's Warren | opens from the Nexus once all six Hearts are free | | **King Goblin** |

Go through any portal, in any order. Enemies rise to meet your level. Goblins roam every world, and pirates raid the coasts. Finish the game to unlock **New Game+**.

## Running it
1. Install **Godot 4.5** or newer (standard build).
2. In the Project Manager, click **Import** and select `project.godot`.
3. Press **F5**. On a Mac, the game runs inside the editor's **Game** tab.

## Controls
| Action | Keyboard | Gamepad |
|---|---|---|
| Move (8 directions) | Arrow keys / WASD | D-pad / left stick |
| Run | Hold Shift (or C) | X / right stick |
| Map | M | Select / Y |
| Talk / confirm | Z, Space or Enter | A |
| Menu / cancel | X, Esc or Backspace | B / Start |
| Next ready fighter (battle) | Tab / Q / E | Shoulder buttons |

## How it works

**Weather.** Outdoors, the weather changes every minute or two, and each world has its own kinds: sunshine with birdsong, breezes, gales, overcast skies, rain, thunderstorms with lightning, ashfall and ember storms in Cinderreach, snow in Luminael, and drifting void motes in the Hollow. Weather affects battle too. Rain makes Water attacks 20% stronger and Fire 20% weaker, storms boost Wind and Water, sunshine boosts Fire, and so on. The battle banner tells you what's in effect.

**Battles (FF7-style Active Time Battle).** Every fighter has a TIME gauge that fills based on Speed. When a party member's gauge is full, their command menu opens. Faster fighters act more often. Under Menu → Config you can choose **Wait**, where time pauses while you choose, or **Active**, where enemies keep acting.

**Limit Breaks.** Taking damage fills the pink LIMIT gauge. When it's full, *Attack* becomes *Limit*, and each character has their own Limit Break. Wren's, *Kindler's Wrath*, strikes once for every element in their aura.

**Elements.** Water quenches Fire. Fire devours Wind. Wind erodes Stone. Stone dams Water. Spirit and Void undo each other.
Hitting a foe with the element that beats its own deals 1.75x damage ("WEAK!"). Hitting it with its own element deals half.
Every enemy's element icon is shown next to its name.

**Gear decides everything.** Your weapon, armor and accessory each may carry an element.
- Your **spells** come from the elements you wear. Companions also always know their home element.
- Your weapon's element becomes your attack element.
- Elemental armor and accessories make you **resist** that element, but **weaker** to whatever beats it.
- Weapons: **blades** use Strength, **bows** use Dexterity, and **staves** use Magic and boost spells. Equip companions however you like to make them casters, archers or brawlers.
- Gear grows with whoever wears it. Every world has **40 pieces**: 12 weapons (4 blades, 4 bows, 4 staves), 8 armors and 20 accessories. The full list is in `GEAR_CATALOG.md`.
- **Tiers.** *Common* gear has a tan name. *Rare* gear has a magenta name and its weapons glow magenta in battle. *Legendary* gear has a shimmering gold name and its weapons glow gold. Rare and legendary pieces bring special effects: extra crits, MP on hit, regeneration, a quick start, life drain, evasion, spell power, faster Limit, more gold or EXP, or less damage taken.
- **Where gear comes from.** Pawn shops sell every common piece from their world. Commons give solid stat boosts and are worth buying. Rares and legendaries are found in chests, behind waterfalls, under floorboards, at the bottom of side dungeons and as quest rewards. Any fight can also drop a weapon or armor: tougher enemies drop better gear, and bosses always drop something.
- **MP on hit.** Each physical Attack restores a little MP (3% of max MP, more with *MP on hit* gear).

**Auras.** Everyone glows with the colors of their equipped elements: red Fire, blue Water, teal Wind, green Stone, white Spirit, violet Void. One element gives one color, and mixed gear gives two or three colors. The aura gets brighter and wider as the character levels up, and it pulses slowly. Wren's outfit also changes as they grow stronger, at levels 8, 16 and 25.

**Towns.** Every building can be entered: an **Inn** (rest to heal everyone), a **Tavern** (world-specific food and drink with 4-battle stat boosts, plus gossip and a side-dungeon quest), the **Pawn Shop** (weapons, armor and accessories), the **Item Shop** (potions and elixirs), and four homes. Each shop, inn and tavern has its own music for its world. Residents drop hints, and some homes hide treasure under the floor or stairs down to a secret dungeon.

**Worlds have levels.** Each world runs: town, then the first wilds (with cliffs and carved stairs), then a second area, then a dungeon with a deeper second floor where the boss waits. The second areas are: Cinderreach's mountain trail down into the underground **Magma Tunnels**, Maretide's **Weeping Falls** (walk the ledge behind the waterfall to find a hidden door), Kitefall's **Cloud Steppes**, Copperdeep's **Old Mine Shaft**, Hallowmere's **Lantern Stair** and the Hollow's **Underside**.

**Side dungeons.** Brannoc's Vault, the Grotto Behind the Falls, the Old Belfry, the Forgotten Tunnel, the Quiet Crypt and the Room That Isn't. Each has its own miniboss, legendary treasure and a quest from someone in the tavern.

**In battle,** a small spinning yellow triangle floats over whoever is choosing a command.

**Boost elixirs.** Item shops sell Stamina Tonics, Elixirs of Might, Ironbark Draughts, Sage's Draughts and Hawkeye Drops. Each gives +30% to a stat for 5 battles, and the drinker shimmers gold while it lasts.

**Companions.** Each world has someone who can join you, and each one has a personal quest with a miniboss and a signature weapon:
Kael (Fire), Nerissa (Water), Pip (Wind), Durga (Stone), Sol (Spirit), Vesper (Void). Up to 4 fight at once; swap them under **Menu → Formation**. Benched members still get half XP.

**Quests.** Every world has a main quest that ends in a boss fight, a companion quest, a side quest whose miniboss unlocks strong gear, and often a key quest. Talk to everyone.
Some people tell rambling stories. Those stories are directions to buried treasure, measured from a landmark out in the wilds. Hint: the sun sets in the west and the cold lives in the north.

**Summons.** A summon stone hides in each world's cave. Summon from the battle menu (costs MP).
There are two more: beat **Aeon, the Witness** (behind a sealed door in Luminael, which needs the Keys of Memory and Breath) and **Nihil, the Unmaker** (behind a sealed door in the Hollow, which needs the Keys of Ash and Bedrock). You need all four party members for those fights.

**Safety.** Towns and the Nexus have no battles. Inns, and the Keeper's fire in the Nexus, restore everyone. Save from the menu at any time (3 slots), and the game autosaves whenever you change areas. If you lose, you can retry the battle immediately.

**Exploring.** Walk in eight directions, run, and press **M** for the full map. A corner minimap shows quest givers (gold **!**), people waiting on a finished quest (green **!**), chests, exits and danger. Fields, caves and dungeons are fogged until you explore them, and you can drop your own pins (Fight, Hard Enemy, Farming Spot, Loot, Secret, Rest Spot, Note) with the map open. Townsfolk work: fishing, farming, mining, hammering at anvils, chopping wood, digging graves, holding seances. Wanderers step out of your way.

**Light and shadow.** Caves and dungeons are dark except for your torch, wall torches, crystals and lava. Interiors are warm and candlelit. Buildings and cliffs cast soft shadows, sunbeams drift across clear days, and storms and the void bring gloom.

**Battle feel.** Big hits freeze time for a split second, knock enemies back, shake the screen and make them grunt or groan. Hitting a weakness with a spell sets off an elemental explosion, and finishing an enemy that way burns it to ash, melts it, blows it away, shatters it, vaporizes it or swallows it into the void.

**The Blessed.** Figures cloaked in white sometimes step out of nowhere in the wilds. They teleport away from ordinary weapons. Defeat them and salvage their tech: **Blessed** weapons (arc blades, assault lasers, ray pistols, coil staffs) that tear through ordinary creatures with triple, unresistable *Overload* damage and disintegrate what they kill. Against the Blessed themselves, they're only a fair fight. Menu → Config → **Practice Stash** hands you twelve of them if you'd like to try them early (it makes the game much easier).

**Legendary hunts.** Seven pairs of treasure hunters wander the outdoor areas, each missing something: a pet ferret, a music box, a wedding ring, a doll, a lucky hat, a flock, a paper lantern. Their story hides the weakness of the beast that took it. Help them and split the hoard: 999 to 9,999 gold, legendary gear and rare medicine.

## Project layout

- `project.godot`: open this in Godot 4.5 or newer.
- `scripts/`: game code. `battle.gd` (Active Time Battle), `map.gd` (exploration, events, lighting), `minimap.gd`, `menu.gd`, `shop.gd`, `game_state.gd` (party, stats, saves), `db.gd` (data loading and formulas), `intro.gd`, `title.gd`, `ending.gd`.
- `data/db.json` and `data/maps/*.json`: every item, spell, enemy, quest and map, generated by the tools.
- `assets/`: art, music (`.ogg`), sound effects (`.wav`), fonts and license files.
- `shaders/`: auras, hit flashes, weapon glow and the lighting passes.
- `tools/`: the Python generators that built the data, art, music and sound, plus test scripts. Godot ignores this folder. See `tools/README.md`.

## Credits and licenses

- **Art:** Liberated Pixel Cup (LPC) artists, via the LPC Universal Spritesheet Character Generator and **Source of Tales**. Licensed CC-BY-SA 3.0 / GPL 3 (some parts OGA-BY 3.0 or CC0). The full per-file list of authors is in `assets/licenses/LPC_CREDITS.csv`. CC-BY-SA is share-alike: keep the credits file, credit the artists, and share changed versions of those images under the same license.
- **Older art:** Kenney (www.kenney.nl) Tiny packs and Tiny Creatures by Clint Bellanger, both CC0.
- **Fonts:** Inter and Press Start 2P, under the SIL Open Font License (license files in `assets/fonts/`).
- **Music, sound effects, effects art and code:** generated for this project.
- **Code license:** choose one before publishing (MIT is a common choice for game code). The art licenses above apply to the art regardless.
