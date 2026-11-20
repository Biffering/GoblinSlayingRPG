"""Map generators for Six Hearths. Produces tile grids (lists of strings) plus feature positions.

Tile legend (shared by every world; each world's tileset draws them differently):
  ' ' outside / nothing (blocks)     '.' ground        ',' path         '"' grass / decor ground
  'T' tree (blocks)                  '^' rock (blocks) '~' liquid (blocks, animated)
  '=' bridge                         '#' wall (blocks) '_' floor        'R' roof (blocks)
  'H' house wall (blocks)            'W' window wall   'd' door (blocks; towns have no interiors)
  'a' stall awning (blocks)          'c' counter (blocks; talk across it)
  'f' fence (blocks)                 'F' flowers       'l' lamp post (blocks)
  'n' bench (blocks)                 'w' plaza feature (blocks)        'L' landmark (blocks)
  'P' pillar (blocks)                't' wall torch (blocks, animated) 'b' bones / rubble
  'C' crystal (blocks, glows)        'S' statue (blocks)
  'O' portal (animated)              'E' cave / dungeon mouth          '>' stairs
"""
import random
from collections import deque

BLOCK = set(" T^~#RHWdacflnwLPtCS")


def walkable(ch):
    return ch not in BLOCK


class Grid:
    def __init__(self, w, h, fill="."):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]

    def __getitem__(self, xy):
        x, y = xy
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.g[y][x]
        return " "

    def __setitem__(self, xy, ch):
        x, y = xy
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = ch

    def rect(self, x, y, w, h, ch):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self[(xx, yy)] = ch

    def rows(self):
        return ["".join(r) for r in self.g]

    def reachable(self, start, extra_walk=()):
        seen = {start}
        q = deque([start])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in seen:
                    continue
                if not (0 <= n[0] < self.w and 0 <= n[1] < self.h):
                    continue
                if walkable(self[n]) or n in extra_walk:
                    seen.add(n)
                    q.append(n)
        return seen


# ------------------------------------------------------------------ town

TOWN_SPOTS = {
    # named spots where NPCs stand (x, y) for the unflipped layout
    "elder": (16, 8), "companion": (9, 14), "side": (21, 14), "story": (5, 20), "key": (27, 20),
    "flavor1": (13, 15), "flavor2": (19, 9), "flavor3": (12, 21), "flavor4": (26, 12),
    "pawn": (7, 10), "items": (24, 10), "inn": (11, 7),
}


def build_town(seed, flip=False):
    rnd = random.Random(seed)
    W, H = 32, 24
    g = Grid(W, H, ".")
    # border of trees with a few rocks
    for x in range(W):
        for y in (0, H - 1):
            g[(x, y)] = "T"
    for y in range(H):
        for x in (0, W - 1):
            g[(x, y)] = "T"
    for x in range(1, W - 1):
        if rnd.random() < 0.35:
            g[(x, 1)] = "T"
    # houses: roof rows, window row, door row
    def house(x, y, w, h):
        g.rect(x, y, w, h - 2, "R")
        for xx in range(x, x + w):
            g[(xx, y + h - 2)] = "W" if (xx - x) % 2 == 1 else "H"
            g[(xx, y + h - 1)] = "H"
        g[(x + w // 2, y + h - 1)] = "d"
    house(3, 2, 8, 5)       # inn
    house(21, 2, 8, 5)
    house(2, 15, 6, 5)
    house(25, 15, 5, 5)
    house(14, 17, 5, 4)
    # stalls: awning, keeper row (floor), counter
    def stall(x, y, w):
        g.rect(x, y, w, 1, "a")
        g[(x, y + 1)] = "f"
        g[(x + w - 1, y + 1)] = "f"
        g.rect(x + 1, y + 1, w - 2, 1, "_")
        g.rect(x, y + 2, w, 1, "c")
    stall(5, 9, 5)          # pawn shop, keeper at (7,10)
    stall(22, 9, 5)         # item shop, keeper at (24,10)
    # plaza + feature
    g.rect(13, 10, 6, 5, ",")
    g.rect(15, 11, 2, 2, "w")
    # paths
    g.rect(15, 15, 2, H - 15, ",")       # to south gate
    g.rect(15, 3, 2, 7, ",")             # to portal
    g.rect(7, 7, 1, 2, ",")              # inn door down
    g.rect(7, 12, 9, 1, ",")
    g.rect(17, 12, 8, 1, ",")
    g.rect(24, 7, 1, 2, ",")
    g.rect(5, 13, 1, 2, ",")
    g.rect(27, 13, 1, 2, ",")
    g.rect(5, 13, 23, 1, ",")
    # portal and gate
    g[(16, 3)] = "O"
    g[(15, 3)] = ","
    g[(15, H - 1)] = ","
    g[(16, H - 1)] = ","
    # decor: lamps, benches, flowers, grass
    for p in [(12, 9), (19, 9), (12, 15), (19, 15), (13, 4), (18, 4)]:
        g[p] = "l"
    for p in [(10, 10), (21, 10)]:
        g[p] = "n"
    for _ in range(70):
        x, y = rnd.randrange(1, W - 1), rnd.randrange(2, H - 1)
        if g[(x, y)] == ".":
            g[(x, y)] = rnd.choice('"""F')
    # garden fences
    for x in range(9, 13):
        g[(x, 19)] = "f"
    for x in range(20, 24):
        g[(x, 19)] = "f"
    for x in range(9, 13):
        if g[(x, 20)] == ".":
            g[(x, 20)] = "F"
    spots = dict(TOWN_SPOTS)
    exits = {"nexus": (16, 3), "field": (15, H - 1)}
    if flip:
        for row in g.g:
            row.reverse()
        spots = {k: (W - 1 - x, y) for k, (x, y) in spots.items()}
        exits = {k: (W - 1 - x, y) for k, (x, y) in exits.items()}
    for k, p in spots.items():
        if not walkable(g[p]):
            g[p] = "."
    return g, spots, exits


# ------------------------------------------------------------------ field

def _carve_path(g, a, b, rnd, ch=","):
    x, y = a
    bx, by = b
    pts = []
    guard = 0
    while (x, y) != (bx, by) and guard < 2000:
        guard += 1
        pts.append((x, y))
        if rnd.random() < 0.7:
            if abs(bx - x) > abs(by - y):
                x += 1 if bx > x else -1
            else:
                y += 1 if by > y else -1
        else:
            if rnd.random() < 0.5 and bx != x:
                x += 1 if bx > x else -1
            elif by != y:
                y += 1 if by > y else -1
    pts.append((bx, by))
    for p in pts:
        if g[p] in "~":
            g[p] = "="
        elif g[p] not in "OE>=":
            g[p] = ch
    return pts


def build_field(seed, landmark_offset, liquid=True):
    """Outdoor area. Returns grid and feature positions."""
    rnd = random.Random(seed)
    W, H = 46, 34
    g = Grid(W, H, ".")
    # noise-ish obstacle field
    blobs = []
    for _ in range(26):
        blobs.append((rnd.randrange(W), rnd.randrange(H), rnd.randrange(2, 5), rnd.choice("TTT^")))
    for y in range(H):
        for x in range(W):
            for bx, by, r, ch in blobs:
                if (x - bx) ** 2 + (y - by) ** 2 <= r * r and rnd.random() < 0.78:
                    g[(x, y)] = ch
                    break
            else:
                if rnd.random() < 0.18:
                    g[(x, y)] = '"'
                elif rnd.random() < 0.025:
                    g[(x, y)] = "F"
    if liquid:
        # a river or two ponds
        if rnd.random() < 0.5:
            x = rnd.randrange(12, W - 12)
            for y in range(H):
                x += rnd.choice((-1, 0, 0, 1))
                for dx in range(3):
                    g[(x + dx, y)] = "~"
        else:
            for _ in range(2):
                cx, cy, r = rnd.randrange(8, W - 8), rnd.randrange(8, H - 8), rnd.randrange(3, 5)
                for y in range(cy - r, cy + r + 1):
                    for x in range(cx - r - 1, cx + r + 2):
                        if ((x - cx) / (r + 1)) ** 2 + ((y - cy) / r) ** 2 <= 1:
                            g[(x, y)] = "~"
    # thick border
    for x in range(W):
        for y in (0, 1, H - 1):
            g[(x, y)] = "T" if rnd.random() < 0.8 else "^"
    for y in range(H):
        for x in (0, 1, W - 2, W - 1):
            g[(x, y)] = "T" if rnd.random() < 0.8 else "^"
    town = (W // 2, H - 1)
    cave = (3, rnd.randrange(8, 14))
    dungeon = (rnd.randrange(W - 16, W - 6), 2)
    landmark = (rnd.randrange(14, W - 14), rnd.randrange(12, H - 10))
    hub = (W // 2 + rnd.randrange(-4, 5), H // 2 + rnd.randrange(-2, 3))
    # clear around key points
    for p in (town, cave, dungeon, landmark, hub):
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                q = (p[0] + dx, p[1] + dy)
                if 2 <= q[0] < W - 2 and 2 <= q[1] < H - 1:
                    if g[q] in "T^~":
                        g[q] = "."
    g[cave] = "E"
    g[(cave[0] - 1, cave[1])] = "^"
    g[(cave[0], cave[1] - 1)] = "^"
    g[(cave[0], cave[1] + 1)] = "^"
    g[dungeon] = "E"
    g[(dungeon[0] - 1, dungeon[1])] = "^"
    g[(dungeon[0] + 1, dungeon[1])] = "^"
    g[(dungeon[0], dungeon[1] - 1)] = "^"
    g[town] = ","
    g[(town[0] - 1, town[1])] = ","
    # paths
    _carve_path(g, (town[0], town[1] - 1), hub, rnd)
    _carve_path(g, hub, (cave[0] + 1, cave[1]), rnd)
    _carve_path(g, hub, (dungeon[0], dungeon[1] + 1), rnd)
    _carve_path(g, hub, (landmark[0], landmark[1] + 2), rnd)
    g[landmark] = "L"
    hidden = (landmark[0] + landmark_offset[0], landmark[1] + landmark_offset[1])
    if g[hidden] in BLOCK:
        g[hidden] = '"'
    # make sure everything important is reachable; punch holes if needed
    start = (town[0], town[1] - 1)
    for target in [(cave[0] + 1, cave[1]), (dungeon[0], dungeon[1] + 1), hidden,
                   (landmark[0], landmark[1] + 1)]:
        if target not in g.reachable(start):
            _carve_path(g, start, target, rnd, ch='"')
    # pick open spots for chests / minibosses (reachable, off the path, not near exits)
    reach = g.reachable(start)
    open_spots = [p for p in reach if g[p] in '."F' and 3 < p[0] < W - 4 and 3 < p[1] < H - 3
                  and abs(p[0] - landmark[0]) + abs(p[1] - landmark[1]) > 3 and p != hidden]
    rnd.shuffle(open_spots)
    def far_apart(p, chosen, d=6):
        return all(abs(p[0] - c[0]) + abs(p[1] - c[1]) >= d for c in chosen)
    picks = []
    for p in open_spots:
        if far_apart(p, picks + [start, cave, dungeon]):
            picks.append(p)
        if len(picks) >= 8:
            break
    return g, {"town_exit": town, "cave": cave, "dungeon": dungeon, "landmark": landmark,
               "hidden": hidden, "spots": picks, "start": start}


# ------------------------------------------------------------------ caves & dungeons

def build_rooms(seed, W, H, cols, rows, decor="bP", torch=True):
    rnd = random.Random(seed)
    g = Grid(W, H, "#")
    cw, ch = (W - 2) // cols, (H - 2) // rows
    rooms = {}
    for cy in range(rows):
        for cx in range(cols):
            rw = rnd.randrange(max(4, cw // 2), cw - 1)
            rh = rnd.randrange(max(3, ch // 2), ch - 1)
            rx = 1 + cx * cw + rnd.randrange(0, cw - rw)
            ry = 1 + cy * ch + rnd.randrange(0, ch - rh)
            rooms[(cx, cy)] = (rx, ry, rw, rh)
            g.rect(rx, ry, rw, rh, "_")

    def center(r):
        return (r[0] + r[2] // 2, r[1] + r[3] // 2)

    # spanning tree over grid cells (random DFS) + a few loops
    cells = list(rooms)
    start = (cols // 2, rows - 1)
    seen = {start}
    stack = [start]
    edges = []
    while stack:
        c = stack[-1]
        nb = [(c[0] + dx, c[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        nb = [n for n in nb if n in rooms and n not in seen]
        if nb:
            n = rnd.choice(nb)
            seen.add(n)
            edges.append((c, n))
            stack.append(n)
        else:
            stack.pop()
    for _ in range(max(1, len(cells) // 4)):
        a = rnd.choice(cells)
        b = (a[0] + rnd.choice((-1, 1)), a[1]) if rnd.random() < 0.5 else (a[0], a[1] + rnd.choice((-1, 1)))
        if b in rooms and (a, b) not in edges and (b, a) not in edges:
            edges.append((a, b))
    for a, b in edges:
        (x1, y1), (x2, y2) = center(rooms[a]), center(rooms[b])
        if rnd.random() < 0.5:
            g.rect(min(x1, x2), y1, abs(x2 - x1) + 1, 1, "_")
            g.rect(x2, min(y1, y2), 1, abs(y2 - y1) + 1, "_")
        else:
            g.rect(x1, min(y1, y2), 1, abs(y2 - y1) + 1, "_")
            g.rect(min(x1, x2), y2, abs(x2 - x1) + 1, 1, "_")
    # degree of each room (dead ends get chests)
    deg = {c: 0 for c in rooms}
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    entrance_room = rooms[start]
    # end room: farthest cell from start on the tree (BFS)
    adj = {c: [] for c in rooms}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    dist = {start: 0}
    q = deque([start])
    while q:
        c = q.popleft()
        for n in adj[c]:
            if n not in dist:
                dist[n] = dist[c] + 1
                q.append(n)
    end = max(dist, key=lambda c: (dist[c], -c[1]))
    # entrance: carve a corridor down to the bottom edge
    ex, ey = center(entrance_room)
    ey2 = entrance_room[1] + entrance_room[3]
    g.rect(ex, ey2, 1, H - ey2, "_")
    exit_tile = (ex, H - 1)
    g[exit_tile] = ">"
    # decor
    for (rx, ry, rw, rh) in rooms.values():
        if rw >= 6 and rh >= 4 and rnd.random() < 0.6:
            for px, py in ((rx + 1, ry + 1), (rx + rw - 2, ry + 1), (rx + 1, ry + rh - 2), (rx + rw - 2, ry + rh - 2)):
                if rnd.random() < 0.7:
                    g[(px, py)] = rnd.choice(decor[1:]) if len(decor) > 1 else "P"
        for _ in range(rnd.randrange(0, 3)):
            p = (rnd.randrange(rx, rx + rw), rnd.randrange(ry, ry + rh))
            if g[p] == "_":
                g[p] = decor[0]
    if torch:
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if g[(x, y)] == "#" and g[(x, y + 1)] == "_" and rnd.random() < 0.12:
                    g[(x, y)] = "t"
    # make sure decor never blocks connectivity
    startp = (ex, H - 2)
    reach = g.reachable(startp)
    for r in rooms.values():
        c = center(r)
        if g[c] in BLOCK:
            g[c] = "_"
        if c not in reach:
            for yy in range(r[1], r[1] + r[3]):
                for xx in range(r[0], r[0] + r[2]):
                    if g[(xx, yy)] in "PC":
                        g[(xx, yy)] = "_"
    reach = g.reachable(startp)
    dead_ends = [rooms[c] for c in rooms if deg[c] == 1 and c not in (start, end)]
    others = [rooms[c] for c in rooms if c not in (start, end) and rooms[c] not in dead_ends]
    return g, {"exit": exit_tile, "start": (ex, H - 2), "end_room": rooms[end], "end_center": center(rooms[end]),
               "dead_ends": dead_ends, "rooms": others, "entrance_room": entrance_room, "reach": reach}


def free_spot_in_room(g, room, rnd, avoid=()):
    rx, ry, rw, rh = room
    cands = [(x, y) for y in range(ry, ry + rh) for x in range(rx, rx + rw)
             if g[(x, y)] in "_b" and (x, y) not in avoid]
    rnd.shuffle(cands)
    return cands[0] if cands else (rx + rw // 2, ry + rh // 2)


# ------------------------------------------------------------------ hub & sanctum

NEXUS = [
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTT",
    "TTTTTTTTT^^^^^^^^^^TTTTTTTTT",
    "TTTTTT^^^,,,,,,,,,,^^^TTTTTT",
    "TTTT^^,,,,,,,O,,,,,,,,^^TTTT",
    "TTT^,,,,,,\"\",,,,\"\",,,,,,^TTT",
    "TT^,,,O,,\"\"\"\",,\"\"\"\",,O,,,^TT",
    "TT^,,,,,\"FF\"\",,\"\"FF\",,,,,^TT",
    "T^,,,,,,,\"\"\",,,,\"\"\",,,,,,,^T",
    "T^,,l,,,,,,,,,,,,,,,,,,l,,^T",
    "T^,,,,,,,,,PPPPPP,,,,,,,,,^T",
    "T^,,,,,,,,,P____P,,,,,,,,,^T",
    "T^,,O,,,,,,P_ww_P,,,,,,O,,^T",
    "T^,,,,,,,,,P____P,,,,,,,,,^T",
    "T^,,,,,,,,,PP__PP,,,,,,,,,^T",
    "T^,,l,,,,,,,,,,,,,,,,,,l,,^T",
    "T^,,,,,,,\"\"\",,,,\"\"\",,,,,,,^T",
    "TT^,,,,,\"FF\"\",,\"\"FF\",,,,,^TT",
    "TT^,,,,,,\"\"\",,,,\"\"\",,,,,,^TT",
    "TTT^,,,,,,,,,,O,,,,,,,,,^TTT",
    "TTTT^^,,,,,,,,,,,,,,,,^^TTTT",
    "TTTTTT^^^,,,,,,,,,,^^^TTTTTT",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTT",
]
# portal positions in NEXUS (x, y) -> world
NEXUS_PORTALS = {"fire": (13, 3), "water": (22, 5), "wind": (24, 11), "stone": (14, 18),
                 "spirit": (4, 11), "void": (6, 5)}


def build_sanctum(seed):
    rnd = random.Random(seed)
    W, H = 19, 15
    g = Grid(W, H, "#")
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if ((x - W // 2) / 8.2) ** 2 + ((y - H // 2) / 6.3) ** 2 <= 1:
                g[(x, y)] = "_"
    for p in [(5, 4), (13, 4), (5, 10), (13, 10), (3, 7), (15, 7)]:
        g[p] = "C"
    g.rect(W // 2, H - 3, 1, 3, "_")
    g[(W // 2, H - 1)] = ">"
    for _ in range(10):
        p = (rnd.randrange(2, W - 2), rnd.randrange(2, H - 2))
        if g[p] == "_":
            g[p] = "b"
    return g, {"exit": (W // 2, H - 1), "start": (W // 2, H - 2), "center": (W // 2, 5)}


# =========================================================================== v2: bigger towns, interiors, levels

# New tiles:
#  'K' cliff (blocks)        'Y' carved stairs        'V' waterfall over cliff (blocks, drawn over everything)
#  'U' ledge behind falls    'Z' hidden door (exit; looks like cliff behind the water)
#  interiors: 'B' bed  'k' bookshelf  'u' table  'o' stool  'q' potion shelf  'x' barrel  'X' crate
#             'p' fireplace  'j' weapon rack  'J' armor stand  'z' plant  'g' bottle shelf  'e' keg
#             'm' door mat (exit)  'v' stairs (exit)  'i' painting  'y' window  'r' rug  'Q' candle stand
BLOCK2 = (BLOCK | set("KVBkuoqxXpjJzgeiyQ")) - set("d")


def walkable2(ch):
    return ch not in BLOCK2


def reach2(g, start):
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in seen or not (0 <= n[0] < g.w and 0 <= n[1] < g.h):
                continue
            if walkable2(g[n]):
                seen.add(n)
                q.append(n)
    return seen


TOWN2_SPOTS = {
    "elder": (20, 8), "companion": (15, 12), "side": (25, 12), "story": (12, 19), "key": (28, 19),
    "flavor1": (17, 18), "flavor2": (23, 9), "flavor3": (11, 11), "flavor4": (30, 11),
}
TOWN2_BUILDINGS = {
    # kind: (x, y, w, h)
    "inn": (3, 2, 9, 6), "tavern": (28, 2, 9, 6), "pawn": (3, 13, 8, 5), "items": (29, 13, 8, 5),
    "house1": (3, 21, 7, 5), "house2": (30, 21, 7, 5), "house3": (12, 22, 6, 5), "house4": (23, 22, 6, 5),
}


def build_town2(seed, flip=False, border="trees"):
    rnd = random.Random(seed)
    W, H = 40, 30
    g = Grid(W, H, ".")
    # border: mountain cliffs for fire/stone, trees elsewhere
    for x in range(W):
        for y in range(H):
            edge = x in (0, W - 1) or y in (0, H - 1)
            if edge:
                g[(x, y)] = "K" if border == "cliff" else "T"
    if border == "cliff":
        for x in range(1, W - 1):
            g[(x, 1)] = "K"
            if rnd.random() < 0.3:
                g[(x, H - 2)] = "^"
        for y in range(1, H - 1):
            if rnd.random() < 0.3:
                g[(1, y)] = "^"
            if rnd.random() < 0.3:
                g[(W - 2, y)] = "^"
    else:
        for x in range(1, W - 1):
            if rnd.random() < 0.35:
                g[(x, 1)] = "T"
    doors = {}
    for kind, (x, y, w, h) in TOWN2_BUILDINGS.items():
        g.rect(x, y, w, h - 2, "R")
        for xx in range(x, x + w):
            g[(xx, y + h - 2)] = "W" if (xx - x) % 2 == 1 else "H"
            g[(xx, y + h - 1)] = "H"
        d = (x + w // 2, y + h - 1)
        g[d] = "d"
        doors[kind] = d
        g[(d[0], d[1] + 1)] = ","
    # plaza + feature
    g.rect(14, 10, 12, 9, ",")
    g.rect(19, 13, 2, 2, "w")
    # main streets
    g.rect(19, 3, 2, 7, ",")
    g.rect(19, 19, 2, H - 19, ",")
    g.rect(4, 19, 33, 1, ",")
    g.rect(4, 9, 33, 1, ",")
    for kind, d in doors.items():
        # short lane from each door to the nearest street
        x, y = d
        street_y = 9 if y < 12 else 19
        if y + 1 > street_y:
            continue
        for yy in range(y + 1, street_y + 1):
            g[(x, yy)] = ","
    for kind in ("house3", "house4"):
        x, y = doors[kind]
        for yy in range(19, y + 1):
            if g[(x, yy)] not in "d":
                g[(x, yy)] = ","
    g[(20, 3)] = "O"
    g[(19, H - 1)] = ","
    g[(20, H - 1)] = ","
    for p in [(13, 9), (26, 9), (13, 19), (26, 19), (18, 4), (21, 4), (8, 11), (31, 11)]:
        if g[p] in ".,":
            g[p] = "l"
    for p in [(16, 11), (23, 11), (16, 17), (23, 17)]:
        g[p] = "n"
    for _ in range(110):
        x, y = rnd.randrange(2, W - 2), rnd.randrange(2, H - 2)
        if g[(x, y)] == ".":
            g[(x, y)] = rnd.choice('"""F')
    # little gardens
    for x in range(12, 18):
        if g[(x, 27)] == ".":
            g[(x, 27)] = "f"
    spots = dict(TOWN2_SPOTS)
    exits = {"nexus": (20, 3), "field": (19, H - 1)}
    if flip:
        for row in g.g:
            row.reverse()
        spots = {k: (W - 1 - x, y) for k, (x, y) in spots.items()}
        exits = {k: (W - 1 - x, y) for k, (x, y) in exits.items()}
        doors = {k: (W - 1 - x, y) for k, (x, y) in doors.items()}
    for k, p in spots.items():
        if not walkable2(g[p]):
            g[p] = "."
    return g, spots, exits, doors


# ------------------------------------------------------------------ interiors

INTERIOR_SIZE = {"inn": (16, 11), "tavern": (18, 12), "pawn": (14, 10), "items": (14, 10),
                 "house1": (12, 9), "house2": (12, 9), "house3": (12, 9), "house4": (12, 9)}


def build_interior(kind, seed, stairs=False):
    """Returns grid, named spots, mat (exit), hidden-spot candidates, chest spots, stairs position."""
    rnd = random.Random(seed)
    W, H = INTERIOR_SIZE[kind]
    g = Grid(W, H, "_")
    for x in range(W):
        g[(x, 0)] = "#"
        g[(x, 1)] = "#"
        g[(x, H - 1)] = "#"
    for y in range(H):
        g[(0, y)] = "#"
        g[(W - 1, y)] = "#"
    mat = (W // 2, H - 1)
    g[mat] = "m"
    spots, hidden, chests = {}, [], []
    st = None
    # wall decorations on the face row (row 1)
    def wall(x, ch):
        if 1 <= x < W - 1:
            g[(x, 1)] = ch
    for x in range(2, W - 2, 4):
        wall(x, rnd.choice("yi"))
    if kind == "inn":
        wall(W // 2, "p")
        g.rect(2, 3, 5, 1, "c")                # front desk
        g[(2, 2)] = "_"
        spots["keeper"] = (4, 2)
        for i, x in enumerate(range(9, W - 1, 3)):
            g[(x, 3)] = "B"
            g[(x, 4)] = "B"
            g[(x + 1, 3)] = "u"
        g.rect(W // 2 - 2, 6, 4, 3, "r")
        spots["guest"] = (3, 7)
        spots["guest2"] = (W - 3, 7)
        g[(1 + 1, H - 2)] = "z"
        g[(W - 3, H - 2)] = "z"
    elif kind == "tavern":
        wall(3, "g")
        wall(4, "g")
        wall(5, "g")
        wall(W - 4, "p")
        g.rect(2, 4, 6, 1, "c")                # bar
        g[(7, 3)] = "c"
        g[(7, 2)] = "c"
        spots["keeper"] = (4, 3)
        g[(2, 2)] = "e"
        g[(6, 2)] = "e"
        for (tx, ty) in [(11, 4), (14, 4), (11, 8), (14, 8), (4, 8)]:
            if tx < W - 1:
                g[(tx, ty)] = "u"
                for ox in (-1, 1):
                    if g[(tx + ox, ty)] == "_":
                        g[(tx + ox, ty)] = "o"
        g[(W - 2, H - 2)] = "x"
        g[(W - 2, H - 3)] = "x"
        g[(1, H - 2)] = "X"
        spots["bard"] = (W - 3, 3)
        spots["patron1"] = (12, 5)
        spots["patron2"] = (5, 9)
        spots["patron3"] = (15, 9)
        spots["patron4"] = (9, 6)
    elif kind == "pawn":
        g.rect(4, 3, 6, 1, "c")
        spots["keeper"] = (6, 2)
        for x in range(1, 4):
            g[(x, 2)] = "j"
        for x in range(10, W - 1):
            g[(x, 2)] = "J" if x % 2 else "j"
        g[(1, 5)] = "j"
        g[(1, 6)] = "J"
        g[(W - 2, 5)] = "X"
        g[(W - 2, 6)] = "X"
        g.rect(4, 5, 6, 3, "r")
        spots["helper"] = (11, 6)
    elif kind == "items":
        g.rect(4, 3, 6, 1, "c")
        spots["keeper"] = (6, 2)
        for x in list(range(1, 4)) + list(range(10, W - 1)):
            g[(x, 2)] = "q"
        g[(1, 6)] = "x"
        g[(1, 7)] = "x"
        g[(W - 2, 6)] = "z"
        g[(W - 2, 4)] = "q"
        g.rect(5, 5, 4, 3, "r")
        spots["helper"] = (11, 6)
    else:  # houses
        wall(2, "k")
        wall(3, "k")
        wall(W - 3, "p")
        g[(W - 3, 3)] = "B"
        g[(W - 3, 4)] = "B"
        g[(4, 4)] = "u"
        g[(3, 4)] = "o"
        g[(5, 4)] = "o"
        g.rect(4, 6, 4, 2, "r")
        g[(1, H - 2)] = rnd.choice("xzX")
        g[(W - 2, H - 2)] = rnd.choice("zQ")
        spots["a"] = (7, 3)
        spots["b"] = (3, 6)
        hidden = [(2, 1), (3, 1), (1, H - 2)]
        chests = [(W - 2, 6), (1, 3)]
        if stairs:
            st = (1, 2)
            g[st] = "v"
            g[(1, 3)] = "_"
            chests = [(W - 2, 6)]
    return g, spots, mat, hidden, chests, st


# ------------------------------------------------------------------ fields with cliffs, underground, waterfall

def add_cliffs(g, rnd, bands, protect=()):
    """Horizontal 2-row cliff bands with stair gaps wherever a path crosses."""
    W, H = g.w, g.h
    for y0 in bands:
        for x in range(2, W - 2):
            for y in (y0, y0 + 1):
                ch = g[(x, y)]
                if ch == "~":
                    g[(x, y)] = "V"   # the river pours over the cliff
                    continue
                if ch in ",=EOL" or (x, y) in protect:
                    g[(x, y)] = "Y" if ch in ",=" else ch
                elif ch in '."F^T_':
                    g[(x, y)] = "K"
        # an extra stairway somewhere along each band
        sx = rnd.randrange(6, W - 8)
        for y in (y0, y0 + 1):
            for x in (sx, sx + 1):
                g[(x, y)] = "Y"
        for x in (sx, sx + 1):
            for y in (y0 - 1, y0 + 2):
                if g[(x, y)] in "T^~":
                    g[(x, y)] = '"'


def build_field2(seed, style="outdoor", cliffs=0, liquid=True, waterfall=False):
    """Second outdoor/underground area: entrance at bottom, dungeon at top, optional waterfall."""
    rnd = random.Random(seed)
    W, H = 46, 34
    g = Grid(W, H, "_" if style == "underground" else ".")
    obstacle = "#" if style == "underground" else "T"
    for _ in range(28):
        bx, by, r = rnd.randrange(W), rnd.randrange(H), rnd.randrange(2, 5)
        ch = rnd.choice([obstacle, obstacle, "^"] if style != "underground" else ["#", "#", "^", "C"])
        for y in range(by - r, by + r + 1):
            for x in range(bx - r, bx + r + 1):
                if (x - bx) ** 2 + (y - by) ** 2 <= r * r and rnd.random() < 0.8:
                    g[(x, y)] = ch
    for y in range(H):
        for x in range(W):
            if g[(x, y)] in "._" and rnd.random() < 0.12:
                g[(x, y)] = '"' if style != "underground" else "b"
    if liquid:
        for _ in range(3 if style != "underground" else 2):
            cx, cy, r = rnd.randrange(8, W - 8), rnd.randrange(8, H - 8), rnd.randrange(2, 5)
            for y in range(cy - r, cy + r + 1):
                for x in range(cx - r - 1, cx + r + 2):
                    if ((x - cx) / (r + 1)) ** 2 + ((y - cy) / r) ** 2 <= 1:
                        g[(x, y)] = "~"
    border = "#" if style == "underground" else "T"
    for x in range(W):
        for y in (0, 1, H - 1):
            g[(x, y)] = border
    for y in range(H):
        for x in (0, 1, W - 2, W - 1):
            g[(x, y)] = border
    entry = (W // 2, H - 1)
    goal = (rnd.randrange(8, W - 8), 2)
    hub = (W // 2 + rnd.randrange(-5, 6), H // 2 + rnd.randrange(-3, 4))
    for p in (entry, goal, hub):
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                q = (p[0] + dx, p[1] + dy)
                if 2 <= q[0] < W - 2 and 2 <= q[1] < H - 1 and g[q] in "T^~#C":
                    g[q] = "_" if style == "underground" else "."
    g[entry] = ","
    g[(entry[0] - 1, entry[1])] = ","
    g[goal] = "E"
    for q in ((goal[0] - 1, goal[1]), (goal[0] + 1, goal[1]), (goal[0], goal[1] - 1)):
        g[q] = "^" if style != "underground" else "#"
    path_ch = ","
    _carve_path(g, (entry[0], entry[1] - 1), hub, rnd, path_ch)
    _carve_path(g, hub, (goal[0], goal[1] + 1), rnd, path_ch)
    extras = {}
    if waterfall:
        # cliff band with a waterfall in the middle; a ledge behind it hides a door
        y0 = 9
        x0 = rnd.randrange(8, 14)
        add_cliffs(g, rnd, [y0])
        for y in range(2, y0):
            for x in range(x0, x0 + 3):
                g[(x, y)] = "~"
        for x in range(x0, x0 + 3):
            g[(x, y0)] = "V"
            g[(x, y0 + 1)] = "V"
            g[(x, y0 + 2)] = "U"
        g[(x0 + 1, y0 + 1)] = "Z"
        for x in range(x0 - 2, x0 + 5):
            for y in range(y0 + 3, y0 + 6):
                g[(x, y)] = "~"
        for x in (x0 - 2, x0 - 1, x0 + 3, x0 + 4):
            g[(x, y0 + 2)] = "."
        # make sure both ends of the ledge connect to the hub
        _carve_path(g, hub, (x0 - 2, y0 + 2), rnd, '"')
        extras["waterfall_door"] = (x0 + 1, y0 + 1)
        extras["waterfall_cols"] = [x0, x0 + 1, x0 + 2]
    if cliffs:
        bands = [12 + i * 9 for i in range(cliffs)] if not waterfall else [22]
        add_cliffs(g, rnd, bands)
    start = (entry[0], entry[1] - 1)
    for target in [(goal[0], goal[1] + 1), hub] + ([extras["waterfall_door"]] if waterfall else []):
        if target not in reach2(g, start):
            pts = _carve_path(g, start, target, rnd, "Y")
    reach = reach2(g, start)
    open_spots = [p for p in reach if g[p] in '."_Fb' and 3 < p[0] < W - 4 and 3 < p[1] < H - 3]
    rnd.shuffle(open_spots)
    picks = []
    for p in open_spots:
        if all(abs(p[0] - c[0]) + abs(p[1] - c[1]) >= 6 for c in picks + [start, goal]):
            picks.append(p)
        if len(picks) >= 6:
            break
    return g, {"entry": entry, "start": start, "goal": goal, "spots": picks, **extras}


def build_field_v2(seed, landmark_offset, liquid=True, cliffs=0):
    """The first outdoor area, bigger, with a north exit to the second area and optional cliffs."""
    g, F = build_field(seed, landmark_offset, liquid)
    rnd = random.Random(seed + 77)
    # north exit to area two (alongside the old dungeon mouth, which now becomes the passage)
    F["north"] = F["dungeon"]
    if cliffs:
        protect = {F["landmark"], F["hidden"], (F["landmark"][0], F["landmark"][1] - 1)}
        bands = [y for y in (11, 21) if abs(y - F["landmark"][1]) > 3 and abs(y - F["hidden"][1]) > 2][:cliffs]
        add_cliffs(g, rnd, bands, protect)
        start = F["start"]
        for target in [(F["cave"][0] + 1, F["cave"][1]), (F["north"][0], F["north"][1] + 1), F["hidden"],
                       (F["landmark"][0], F["landmark"][1] + 1)]:
            if target not in reach2(g, start):
                _carve_path(g, start, target, rnd, "Y")
        reach = reach2(g, start)
        F["spots"] = [p for p in F["spots"] if p in reach and g[p] not in "KY"]
    return g, F
