"""Render a map JSON with its tileset to PNG for previewing (mimics the engine's tile choice rules)."""
import json, sys, random
from PIL import Image
A = sys.argv[1]; mid = sys.argv[2]; out = sys.argv[3]
m = json.load(open(f"{A}/../data/maps/{mid}.json"))
idx = json.load(open(f"{A}/tiles/index.json"))
world = m["world"]
ts = Image.open(f"{A}/tiles/{world}.png")
def tile(name):
    i = idx[name]; return ts.crop(((i % 16) * 16, (i // 16) * 16, (i % 16) * 16 + 16, (i // 16) * 16 + 16))
rows = m["tiles"]; W, H = m["w"], m["h"]
def at(x, y):
    return rows[y][x] if 0 <= x < W and 0 <= y < H else " "
img = Image.new("RGBA", (W * 16, H * 16), (0, 0, 0, 255))
def h(x, y, n): return (x * 7349 + y * 1931) % n
CH = {".": lambda x, y: f"ground{h(x,y,4)}", ",": lambda x, y: f"path{h(x,y,2)}", '"': lambda x, y: f"grass{h(x,y,2)}",
      "F": lambda x, y: f"flower{h(x,y,2)}", "T": lambda x, y: f"tree{h(x,y,2)}", "^": lambda x, y: f"rock{h(x,y,2)}",
      "~": lambda x, y: ("liquid_edge0" if at(x, y - 1) not in "~=" else "liquid0"), "=": lambda x, y: "bridge",
      "#": lambda x, y: ("wall_top" if at(x, y + 1) in "#t " else f"wall_face{h(x,y,3)//2}"), "_": lambda x, y: f"floor{h(x,y,3)}",
      "R": lambda x, y: ("roof_top" if at(x, y - 1) != "R" else ("roof_bot" if at(x, y + 1) != "R" else "roof_mid")),
      "H": lambda x, y: "hwall", "W": lambda x, y: "window", "d": lambda x, y: "door", "a": lambda x, y: "awning",
      "c": lambda x, y: "counter", "f": lambda x, y: "fence", "l": lambda x, y: "lamp0", "n": lambda x, y: "bench",
      "P": lambda x, y: "pillar", "t": lambda x, y: "torch0", "b": lambda x, y: "bones", "C": lambda x, y: "crystal0",
      "S": lambda x, y: "statue", "O": lambda x, y: "portal0", "E": lambda x, y: "cave_mouth", ">": lambda x, y: "stairs",
      "L": lambda x, y: "landmark_bot", " ": lambda x, y: "outside"}
for y in range(H):
    for x in range(W):
        ch = at(x, y)
        if ch == "w":
            fx = 0 if at(x - 1, y) != "w" else 1; fy = 0 if at(x, y - 1) != "w" else 1
            name = "feat_" + ("t" if fy == 0 else "b") + ("l" if fx == 0 else "r") + "0"
        elif ch in "_" and m["kind"] == "town":
            name = "keeper_floor"
        else:
            name = CH.get(ch, lambda x, y: "ground0")(x, y)
        # underlay ground for transparent tiles
        base = "floor0" if m["kind"] in ("cave", "dungeon", "sanctum") else "ground0"
        img.paste(tile(base), (x * 16, y * 16))
        t = tile(name); img.alpha_composite(t, (x * 16, y * 16))
        if ch == "L":
            img.alpha_composite(tile("landmark_top"), (x * 16, (y - 1) * 16))
img.save(out)
