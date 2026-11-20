"""Working townsfolk: adds small work sites (ponds, fields, rock piles, anvils, graves, a seance circle...)
and the people who work them to every town, plus a few folk who stroll the streets.

usage: python3 ambient.py <maps_dir>      (run after build_data.py, before art_lpc.py)

Each ambient NPC gets "job" (an LPC work animation the game loops) and "jface" (which way they work),
or "wander" + "roam" for strollers. New tile chars, all blocking:
  s tilled soil   A anvil   G chopping stump   M gravestone
"""
import json
import random
import sys
from collections import deque

BLOCK = set(" T^~#RHWacflnwLPtCSKVBkuoqxXpjJzgeiyQsAGM")
PLAIN = set(".\"F")

# site footprints: rows of chars ('?' = leave as is but must be free), worker spots (dx, dy, face, job)
SITES = {
    "pond":    (["~~~~~~", "~~~~~~"], [(1, -1, "down", "fish"), (4, -1, "down", "fish")]),
    "pond1":   (["~~~~~", "~~~~~"], [(2, -1, "down", "fish")]),
    "field":   (["ssssss", "ssssss", "ssssss"], [(-1, 0, "right", "hoe"), (-1, 2, "right", "hoe"), (6, 1, "left", "water")]),
    "plot":    (["ssss", "ssss"], [(-1, 1, "right", "hoe"), (4, 0, "left", "water")]),
    "rocks":   (["^^^", "^^^"], [(-1, 1, "right", "mine"), (3, 0, "left", "mine")]),
    "anvil":   (["A"], [(-1, 0, "right", "smith")]),
    "stump":   (["G"], [(-1, 0, "right", "chop")]),
    "graves":  (["M?M?M"], [(1, 1, "down", "dig")]),
    "seance":  (["???", "?Q?", "???"], [(1, 0, "down", "seance"), (0, 1, "right", "seance"), (2, 1, "left", "seance"), (1, 2, "up", "seance")]),
    "shrine":  (["?S?"], [(0, 1, "right", "pray"), (2, 1, "left", "pray"), (1, 2, "up", "pray")]),
    "garden":  (["FFF"], [(-1, 0, "right", "water")]),
    "sand":    (["?"], [(0, 0, "down", "dig")]),
}

PLAN = {
    "fire":   ["rocks", "rocks", "anvil", "anvil"],
    "water":  ["pond", "pond", "pond1", "sand", "garden"],
    "wind":   ["field|plot", "plot", "plot", "stump", "garden"],
    "stone":  ["rocks", "rocks", "anvil", "graves", "stump"],
    "spirit": ["shrine", "plot", "garden", "garden"],
    "void":   ["seance", "graves", "graves"],
}

JOB_NAME = {"fish": "Fisher", "hoe": "Farmer", "water": "Gardener", "mine": "Miner", "smith": "Smith",
            "chop": "Woodcutter", "dig": "Gravedigger", "seance": "Medium", "pray": "Acolyte", "walk": "Townsfolk"}
JOB_NAME_W = {("water", "dig"): "Clam Digger", ("spirit", "hoe"): "Brother of the Garden", ("fire", "mine"): "Ash Miner",
              ("stone", "mine"): "Deep Miner", ("stone", "dig"): "Gravedigger", ("void", "walk"): "Hooded Stranger"}

LINES = {
    "fish": ["They bite at dusk. So do the things under the docks.", "Pulled up a goblin's boot this morning. Foot was still in it.",
             "Quiet. You'll scare them off.", "The water's been colder since the Hearth went dark.", "Pirates took my brother's boat. I took up fishing. Fair trade, I suppose."],
    "hoe": ["Soil's sour. Nothing grows right since the curse.", "Goblins steal the turnips. Then the chickens. Then the farmer.",
            "Dig, plant, pray. Dig, plant, pray.", "My grandmother worked this row. Her grandmother too. I'll not be the one who loses it."],
    "water": ["Flowers don't care about curses. Lucky them.", "A little water, a little patience.", "Mind the petals, slayer."],
    "mine": ["Every swing, the mountain swings back.", "Struck a goblin tunnel last week. Sealed it with three men inside. Not our men.",
             "Ore's black this deep. Black and warm.", "Hear that knocking? That's not us."],
    "smith": ["Steel for the walls. Steel for the gates. Steel for whoever's left.", "Bring me goblin iron. It's bad iron, but it's iron.",
              "Hold still, I'm working. Unless you've coin."],
    "chop": ["Firewood for the night watch. Nights are longer now.", "This tree had a face in it. Swear it did.", "Stand back. Axes don't care who they hit."],
    "dig": ["Busy season. Always busy season now.", "Six deep, no fewer. They climb out otherwise.", "Found a ring. Owner won't be needing it."],
    "seance": ["Shh. The circle is open.", "The dead are restless. They speak of a goblin king with a crown of teeth.",
               "Don't break the ring. Whatever you do, don't break the ring.", "They see you, slayer. They're... afraid of you."],
    "pray": ["Light keep us. Light keep us all.", "The old saints never answered. We pray anyway.", "Kneel with us, if you've a moment. Or a soul."],
    "walk": ["Keep your blade close after dark.", "Did you hear screaming last night? Me neither.", "The goblins are getting bolder.",
             "Market's thin. Caravans stopped coming.", "Who are you? You've got the look of someone who doesn't sleep.",
             "My uncle went to the Wilds. Came back wrong.", "Lovely weather. For a funeral."],
}

PALETTE = {
    "fire":   {"outfit": ["#5a2e1e", "#3a2a24", "#6a3a1a", "#4a2018"], "accent": ["#c06030", "#8a6040", "#d0a040"], "hair": ["#2a1a12", "#8a2b14", "#4a3020", "#1a1010"]},
    "water":  {"outfit": ["#2a4a6a", "#3a5a5a", "#1e3a4a", "#5a6a7a"], "accent": ["#d8c090", "#8ab0c0", "#c0a060"], "hair": ["#4a3020", "#d8a050", "#2a1a12", "#8a6a4a"]},
    "wind":   {"outfit": ["#5a6a3a", "#7a6a3a", "#4a5a2a", "#8a7a5a"], "accent": ["#d8c090", "#a08040", "#c0b070"], "hair": ["#d8a050", "#8a5a2a", "#4a3020", "#f0e0a0"]},
    "stone":  {"outfit": ["#5a5550", "#4a4038", "#6a6058", "#3a3430"], "accent": ["#8a7a6a", "#a09080", "#6a5a4a"], "hair": ["#3a3430", "#6a5a4a", "#2a2420", "#a09080"]},
    "spirit": {"outfit": ["#d8d0c0", "#c0b8a0", "#a09880", "#e8e0d0"], "accent": ["#d0a040", "#f0e0a0", "#c0c0e0"], "hair": ["#f0e0a0", "#d8d0c0", "#8a6a4a", "#4a3020"]},
    "void":   {"outfit": ["#2a1e3a", "#1a1424", "#3a2a4a", "#2a2430"], "accent": ["#6a4a8a", "#8a6aa0", "#4a3a5a"], "hair": ["#1a1010", "#e0e0f0", "#3a2a4a", "#2a1a12"]},
}


def look(world, job, rng):
    p = PALETTE[world]
    body = rng.choice(["man", "man", "woman", "woman", "elder"])
    if job in ("mine", "smith", "chop") and rng.random() < 0.6:
        body = "man"
    if job in ("seance", "pray"):
        body = rng.choice(["robe", "robe", "woman"])
    hat = None
    if job == "fish":
        hat = rng.choice(["wide", "cap", None])
    elif job in ("hoe", "water") and world in ("wind", "water"):
        hat = rng.choice(["wide", None])
    elif job == "mine":
        hat = "cap"
    elif job in ("seance", "dig") or world == "void":
        hat = rng.choice(["hood", "hood", None])
    return {"body": body, "hair": rng.choice(p["hair"]), "outfit": rng.choice(p["outfit"]), "accent": rng.choice(p["accent"]),
            "skin": rng.randrange(5), "hat": hat, "beard": body == "man" and rng.random() < 0.35}


def _taken(m):
    t = set()
    for k in ("npcs", "chests", "hidden", "entities", "signs"):
        for o in m.get(k, []):
            t.add((int(o["x"]), int(o["y"])))
    for e in m.get("exits", []):
        t.add((int(e["x"]), int(e["y"])))
    t.add(tuple(m["start"]))
    return t


def _reach(rows, sx, sy):
    H, W = len(rows), len(rows[0])
    seen = {(sx, sy)}
    q = deque([(sx, sy)])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in seen and rows[ny][nx] not in BLOCK:
                seen.add((nx, ny))
                q.append((nx, ny))
    return seen


def _goals(m, rows):
    """Tiles that must stay reachable: doors, exits, npcs, chests, signs' doors."""
    g = set()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == "d":
                g.add((x, y + 1))
    for k in ("npcs", "chests", "exits"):
        for o in m.get(k, []):
            x, y = int(o["x"]), int(o["y"])
            if k in ("npcs", "chests") or rows[y][x] in BLOCK:
                # stand next to it
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    if 0 <= y + dy < len(rows) and 0 <= x + dx < len(rows[0]) and rows[y + dy][x + dx] not in BLOCK:
                        g.add((x + dx, y + dy))
                        break
            else:
                g.add((x, y))
    return g


def place(m, rows, site, taken, rng):
    pat, workers = SITES[site]
    h, w = len(pat), len(pat[0])
    H, W = len(rows), len(rows[0])
    sx, sy = m["start"]
    goals = _goals(m, rows)
    cands = [(x, y) for y in range(1, H - 1) for x in range(1, W - 1)]
    rng.shuffle(cands)
    # prefer the open bands at the edges of town, away from the main street
    cands.sort(key=lambda p: -(abs(p[0] - 20) + (4 if 10 <= p[1] <= 12 or 18 <= p[1] <= 20 else 0)) + rng.random() * 8)
    # tall border trees hang over the last rows of the town: keep work sites where they can be seen
    low = H - 5 if "T" in rows[H - 1] else H - 1
    for x0, y0 in cands:
        cells = [(x0 + i, y0 + j) for j in range(h) for i in range(w)]
        spots = [(x0 + dx, y0 + dy) for dx, dy, _, _ in workers]
        foot = cells + spots
        if any(not (1 <= x < W - 1 and 1 <= y < low) for x, y in foot):
            continue
        # liquid may touch the town's border wall/trees; everything else needs open ground around it
        ok = True
        for x, y in foot:
            if rows[y][x] not in PLAIN or (x, y) in taken:
                ok = False
                break
        if not ok:
            continue
        margin = set()
        for x, y in foot:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    margin.add((x + dx, y + dy))
        margin -= set(foot)
        if any((p in taken) or rows[p[1]][p[0]] in "dO" for p in margin if 0 <= p[0] < W and 0 <= p[1] < H):
            continue
        if any(rows[p[1]][p[0]] not in BLOCK and rows[p[1]][p[0]] not in PLAIN and rows[p[1]][p[0]] != "," for p in margin
               if 0 <= p[0] < W and 0 <= p[1] < H):
            continue
        new = [list(r) for r in rows]
        for j in range(h):
            for i in range(w):
                c = pat[j][i]
                if c != "?":
                    new[y0 + j][x0 + i] = c
        new = ["".join(r) for r in new]
        blocked = set(spots)
        test = [list(r) for r in new]
        for x, y in blocked:
            test[y][x] = "#"
        test = ["".join(r) for r in test]
        reach = _reach(test, sx, sy)
        if not goals.issubset(reach | blocked):
            continue
        # workers must be reachable to be talked to
        if not all(any((x + dx, y + dy) in reach for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) for x, y in spots):
            continue
        rows[:] = new
        taken |= set(foot) | margin
        return [(x0 + dx, y0 + dy, f, j) for dx, dy, f, j in workers]
    return []


def npc(world, idx, job, x, y, face, rng, wander=False):
    nm = JOB_NAME_W.get((world, job), JOB_NAME[job])
    lines = rng.sample(LINES[job], 2 if rng.random() < 0.4 else 1)
    n = {"id": f"amb_{world}_{idx}", "name": nm, "look": look(world, job, rng),
         "script": [{"if": [], "say": lines}], "wander": wander, "face": face, "x": x, "y": y, "ambient": True}
    if wander:
        n["roam"] = 5
    else:
        n["job"] = job
        n["jface"] = face
    return n


def patch(path):
    m = json.load(open(path))
    world = m["world"]
    if world not in PLAN or m["kind"] != "town":
        return 0
    m["npcs"] = [n for n in m["npcs"] if not n.get("ambient")]
    rng = random.Random(f"amb:{world}")
    rows = list(m["tiles"])
    taken = _taken(m)
    added = []
    for alts in PLAN[world]:
        for site in alts.split("|"):
            got = place(m, rows, site, taken, rng)
            for x, y, f, j in got:
                added.append(npc(world, len(added), j, x, y, f, rng))
            if got:
                break
    # strollers on the streets
    streets = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "," and (x, y) not in taken
               and 8 <= y <= 20 and all(rows[y + dy][x + dx] != "d" for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    rng.shuffle(streets)
    for k in range(3 if world != "void" else 2):
        if not streets:
            break
        x, y = streets.pop()
        streets = [p for p in streets if abs(p[0] - x) + abs(p[1] - y) > 6]
        taken.add((x, y))
        added.append(npc(world, len(added), "walk", x, y, "down", rng, wander=True))
    m["tiles"] = rows
    m["npcs"] += added
    json.dump(m, open(path, "w"), indent=1)
    return len(added)


if __name__ == "__main__":
    import glob
    total = 0
    for p in sorted(glob.glob(f"{sys.argv[1]}/*_town.json")):
        n = patch(p)
        total += n
        print(p.split("/")[-1], n)
    print("ambient npcs", total)
