# Tools

These Python scripts generated the game's data, maps, art, music and sound. You don't need them to play; they're here so everything can be rebuilt or changed. Godot ignores this folder (`.gdignore`).

## Setup

- Python 3 with `numpy`, `Pillow` and `scipy`: `pip3 install numpy pillow scipy`
- `ffmpeg` for the music (`.ogg`) files.
- The source art packs, which aren't included here. Point the scripts at them with environment variables:
  - `LPC_DIR`: a checkout of the [LPC Universal Spritesheet Character Generator](https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator)
  - `SOT_DIR`: the Source of Tales tile and monster art
  - `KENNEY_DIR`: Kenney's Tiny packs (only for the older art scripts)

## Rebuild order

Run from this folder, with `GAME` set to the project root (`..`).

| Step | Command | What it makes |
|---|---|---|
| 1 | `python3 build_data.py $GAME/data` | `db.json` and every map: worlds, quests, gear, the Blessed and the hunts |
| 2 | `python3 ambient.py $GAME/data/maps` | work sites and working townsfolk in each town (run after step 1) |
| 3 | `python3 art_tiles.py $GAME/assets` | base tilesets |
| 4 | `python3 art_lpc_tiles.py $GAME/assets` | 32px LPC tilesets, liquids, paths, trees, chests |
| 5 | `python3 art_lpc.py $GAME/assets $GAME/data/db.json $GAME/data/maps` | party, townsfolk, work animations, enemies, bosses (about 2 minutes) |
| 6 | `python3 art_lpc.py blessed $GAME/assets` | the 196 Blessed weapon sheets |
| 7 | `python3 art_blessed.py $GAME/assets` | the Blessed, the seven hunt bosses and the hunters |
| 8 | `python3 art_ui.py $GAME/assets`, then `python3 art_ui_lpc.py $GAME/assets` | icons and backgrounds, then the iron-and-leather windows and sword cursor |
| 9 | `python3 art_title.py $GAME/assets` | the battle-worn title logo |
| 10 | `python3 music_rpg.py $GAME/assets/music /tmp/music_tmp` | all music |
| 11 | `python3 sfx_rpg.py $GAME/assets/sounds`, `python3 sfx_weather.py $GAME/assets/sounds`, `python3 sfx_voice.py $GAME/assets/sounds` | sound effects, weather loops, monster voices, lasers, explosions |

`art_enemies.py`, `art_chars.py`, `art_party.py` and `art_kenney.py` are the older (pre-LPC) art pipeline. Don't run them after step 5; they'd overwrite the LPC sprites.

## Where things live

| File | Holds |
|---|---|
| `content_worlds.py` | the six worlds' story, NPCs and quests |
| `content_db.py` | characters, spells, enemies, items |
| `content_gear.py` | the 240-piece gear catalog |
| `content_v2.py` | taverns, homes, side dungeons, combo techs |
| `content_blessed.py` | Blessed weapons, the Blessed and the seven legendary hunts |
| `mapgen.py` | map layouts |
| `lpc.py` | the LPC sprite compositor |

## Tests

`tests/` holds the GDScript test scenes used during development (screenshots of battles, maps, menus; movement and hunt checks). To run one, copy it into a copy of the project as an autoload and start Godot, for example:

```
GODOT=/path/to/Godot tests/run.sh tests/tester24.gd
```

Screenshots are written to `/tmp/shx` or `/tmp/sh`.
