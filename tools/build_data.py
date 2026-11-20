"""Builds data/db.json and data/maps/*.json for Six Hearths."""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
import content_db as DB
import content_worlds as CW
import mapgen as MG

OUT = sys.argv[1]
os.makedirs(os.path.join(OUT, "maps"), exist_ok=True)

WORLD_ORDER = ["fire", "water", "wind", "stone", "spirit", "void"]
maps = {}
encounters = {}


def fix_unique(u):
    u = dict(u)
    if "def_" in u:
        u["def"] = u.pop("def_")
    return u


def check_walk(g, p, what):
    if not MG.walkable2(g[p]):
        raise SystemExit(f"{what} at {p} is on blocking tile {g[p]!r}")


def new_map(mid, name, world, kind, grid, music, bg=None, encounters_on=False):
    m = {"id": mid, "name": name, "world": world, "kind": kind, "w": grid.w, "h": grid.h,
         "tiles": grid.rows(), "music": music, "bg": bg, "encounters": encounters_on,
         "exits": [], "npcs": [], "chests": [], "hidden": [], "entities": []}
    maps[mid] = m
    return m


def add_exit(m, x, y, to, tx, ty, face="down"):
    m["exits"].append({"x": x, "y": y, "to": to, "tx": tx, "ty": ty, "face": face})


def item_spec(s):
    return s


def unique_encounter(uid, bg, music):
    eid = "enc_" + uid
    encounters[eid] = {"enemies": [uid], "music": music, "bg": bg, "flee": False}
    return eid


# ------------------------------------------------------------------ nexus
ng = MG.Grid(len(MG.NEXUS[0]), len(MG.NEXUS), ".")
for y, row in enumerate(MG.NEXUS):
    assert len(row) == ng.w, (y, len(row))
    for x, ch in enumerate(row):
        ng[(x, y)] = ch
portals = [(x, y) for y in range(ng.h) for x in range(ng.w) if ng[(x, y)] == "O"]
cx, cy = ng.w / 2, ng.h / 2
# clockwise from the top: fire, water, wind, stone, spirit, void
def ang(p):
    a = math.atan2(p[0] - cx, -(p[1] - cy))  # 0 = up, increasing clockwise
    return (a + 0.3) % (2 * math.pi)
portals.sort(key=ang)
order_cw = ["fire", "water", "wind", "stone", "spirit", "void"]
# portals sorted clockwise from top: top, top-right, right, bottom, left, top-left
nexus_portal = dict(zip(order_cw, portals))
nexus = new_map("nexus", "The Nexus", "nexus", "hub", ng, "nexus")
nexus["start"] = [14, 15]
nexus["portal_worlds"] = {w: list(p) for w, p in nexus_portal.items()}
nexus_spots = {"keeper": (13, 12), "nexus_shop": (8, 8), "nexus_compass": (20, 15), "nexus_sage": (7, 15), "nexus_vet": (20, 8)}
for n in CW.NEXUS_NPCS:
    p = nexus_spots[n["id"]]
    check_walk(ng, p, n["id"])
    d = dict(n)
    d["x"], d["y"] = p
    d.pop("spot")
    nexus["npcs"].append(d)
check_walk(ng, tuple(nexus["start"]), "nexus start")

# ------------------------------------------------------------------ worlds (v2: towns with interiors, two outdoor areas, two dungeon floors)
import content_v2 as V2
import content_gear as CG

DB.ITEMS.update(V2.tavern_item_defs())
for _k, _u in V2.NEW_UNIQUES.items():
    DB.UNIQUES[_k] = _u
GEAR = DB.GEAR
SIGNS = {"inn": "sign_inn", "tavern": "sign_tavern", "pawn": "sign_pawn", "items": "sign_items"}
TOWN_SPOT_REMAP = {"pawn": None, "items": None, "inn": None}   # keepers move indoors
tavern_shops = {}


def gear_of(w, tier, kinds=None):
    lists = DB.WORLD_GEAR_LISTS[w]
    out = []
    for k in ("weapons", "armor", "acc"):
        for gid in lists[k]:
            if GEAR[gid]["tier"] == tier and (kinds is None or GEAR[gid]["kind"] in kinds):
                out.append(gid)
    return out


def interior_map(w, kind, label, music, seed, stairs=False):
    g, sp, mat, hidden_c, chests_c, st = MG.build_interior(kind, seed, stairs)
    mid = f"{w}_{kind}"
    m = new_map(mid, label, w, "interior", g, music)
    m["start"] = [mat[0], mat[1] - 1]
    return m, g, sp, mat, hidden_c, chests_c, st


def place_npc(m, n, p, extra=None):
    d = dict(n)
    d["x"], d["y"] = p
    d.pop("spot", None)
    if extra:
        d.update(extra)
    m["npcs"].append(d)


def plain_npc(nid, name, lk, lines, wander=False):
    return {"id": nid, "name": name, "look": lk, "script": [{"if": [], "say": lines}], "wander": wander, "face": "down"}


def rooms_dungeon(mid, name, w, seed, Wd, Hd, cols, rows, music, decor="bPS"):
    g, D = MG.build_rooms(seed, Wd, Hd, cols, rows, decor=decor)
    m = new_map(mid, name, w, "dungeon", g, music, bg=f"{w}_in", encounters_on=True)
    m["start"] = list(D["start"])
    return m, g, D


for w in WORLD_ORDER:
    W = CW.WORLDS[w]
    L = V2.LAYOUT[w]
    rnd = random.Random(W["seed"])
    comp_id = [c for c, v in DB.CHARACTERS.items() if v.get("world") == w][0]
    # legendary placement plan: whatever the companion reward and riddle treasure don't already cover
    used = {W["mini_companion"]["reward"], W["hidden_item"]}
    legends = [g for g in gear_of(w, "legendary") if g not in used]
    rnd.shuffle(legends)
    rares = [g for g in gear_of(w, "rare") if g not in used]
    rnd.shuffle(rares)
    side2_reward, side_chest_leg, area2_leg, f2_leg, house_leg = (legends + legends)[:5]

    # ================================================================ town
    tg, spots, texits, doors = MG.build_town2(W["seed"], flip=W["flip"], border=L["border"])
    town = new_map(f"{w}_town", W["town"], w, "town", tg, f"{w}_town")
    px, py = texits["nexus"]
    town["start"] = [px, py + 1]
    npx, npy = nexus_portal[w]
    add_exit(town, px, py, "nexus", npx, npy + 1, "down")
    add_exit(nexus, npx, npy, town["id"], px, py + 1, "down")
    gx, gy = texits["field"]
    gate_tiles = [(gx, gy), (gx + (1 if not W["flip"] else -1), gy)]
    town["signs"] = []
    keepers = {}
    for n in W["npcs"]:
        if n["spot"] in TOWN_SPOT_REMAP:
            keepers[n["spot"]] = n
            continue
        p = spots[n["spot"]]
        check_walk(tg, p, n["id"])
        place_npc(town, n, p)

    # ================================================================ interiors
    names = {"inn": "Inn", "tavern": L["tavern"], "pawn": "Pawn Shop", "items": "Item Shop",
             "house1": "A Cozy House", "house2": "A Workshop", "house3": "A Quiet House", "house4": "An Old House"}
    music = {"inn": f"{w}_inn", "tavern": f"{w}_tavern", "pawn": f"{w}_shop", "items": f"{w}_shop"}
    side_house = L["side"][1] if L["side"][1].startswith("house") else None
    interiors = {}
    for k, d in doors.items():
        stairs = (k == side_house)
        im, ig, isp, mat, hid_c, ch_c, st = interior_map(w, k, f"{W['town']}: {names[k]}", music.get(k, f"{w}_town"),
                                                        W["seed"] * 10 + list(doors).index(k), stairs)
        interiors[k] = (im, ig, isp, ch_c, st)
        add_exit(town, d[0], d[1], im["id"], mat[0], mat[1] - 1, "up")
        add_exit(im, mat[0], mat[1], town["id"], d[0], d[1] + 1, "down")
        if k in SIGNS:
            town["signs"].append({"x": d[0] + 1, "y": d[1] - 1, "tile": SIGNS[k]})
        # keepers
        if k in ("inn", "pawn", "items"):
            place_npc(im, keepers[k], isp["keeper"])
    # inn guests & tavern
    inn = interiors["inn"]
    place_npc(inn[0], plain_npc(f"{w}_guest", "Sleepy Traveler", CW.look("man", "#5a4a3a", "#4a5a6a", "#c0b080", 1),
                                ["Best sleep I've had in weeks. Resting here heals everyone in your party, even the ones at home."]),
              inn[2]["guest"])
    tav = interiors["tavern"]
    tm, tsp = tav[0], tav[2]
    titems = [r[0] for r in V2.TAVERN_ITEMS[w]] + ["potion", "ether"]
    tavern_shops[f"tavern_{w}"] = {"name": L["tavern"], "items": titems, "gear": []}
    for nid, nm, lk, spot, lines in V2.TAVERN_PEOPLE[w]:
        if spot == "keeper":
            place_npc(tm, {"id": nid, "name": nm, "look": lk, "wander": False, "face": "down",
                           "script": [{"if": [], "say": lines, "do": [f"shop:tavern_{w}"]}]}, tsp["keeper"])
        else:
            place_npc(tm, plain_npc(nid, nm, lk, lines, wander=(spot == "patron4")), tsp[spot])
    # side-dungeon quest giver sits in the tavern
    S2 = V2.SIDE2[w]
    gid_, gname, glk = V2.SIDE2_TALK[w]["giver"]
    giver = V2.side2_giver(w, gid_, gname, glk, f"Take it. ({GEAR[side2_reward]['name']})")
    for b_ in giver["script"]:
        if "do" in b_:
            b_["do"] = [x.replace("{REWARD}", side2_reward) for x in b_["do"]]
    place_npc(tm, giver, tsp["patron1"])
    # houses: residents, chests, hidden floorboard treasure
    house_items = [f"gear:{rares[0]}", "hi_potion:2", "ether", f"gear:{rares[1]}", "elixir"]
    hi = 0
    for k in ("house1", "house2", "house3", "house4"):
        im, ig, isp, ch_c, st = interiors[k]
        for (nid, nm, lk, lines) in V2.HOUSE_PEOPLE[w][k]:
            place_npc(im, plain_npc(nid, nm, lk, lines, wander=True), isp["a"])
        for cp in ch_c[:1]:
            im["chests"].append({"id": f"{w}_{k}_c0", "x": cp[0], "y": cp[1], "item": house_items[hi % len(house_items)]})
            hi += 1
        if V2.HOUSE_HIDDEN[w] == k:
            hint_spot = {"fire": (ig.w - 3, 2), "water": (6, 5), "wind": (5, 7), "stone": (2, 2),
                         "spirit": (5, 7), "void": (2, 2)}[w]
            im["hidden"].append({"x": hint_spot[0], "y": hint_spot[1], "item": f"gear:{house_leg}", "flag": f"hidden_{w}_{k}",
                                 "text": "One of the floorboards is loose. You pry it up..."})
        if st:
            interiors[k] = (im, ig, isp, ch_c, st)

    # ================================================================ field (area 1)
    fg, F = MG.build_field_v2(W["seed"] + 1, W["riddle_offset"], cliffs=L["field_cliffs"])
    field = new_map(f"{w}_field", W["field"], w, "field", fg, f"{w}_field", bg=f"{w}_out", encounters_on=True)
    fx, fy = F["town_exit"]
    field["start"] = list(F["start"])
    for gt in gate_tiles:
        add_exit(town, gt[0], gt[1], field["id"], fx, fy - 1, "up")
    for dx in (0, -1):
        add_exit(field, fx + dx, fy, town["id"], gx, gy - 1, "up")
    field["landmark"] = list(F["landmark"])
    field["hidden"].append({"x": F["hidden"][0], "y": F["hidden"][1], "item": "gear:" + W["hidden_item"], "flag": f"hidden_{w}"})
    spots_f = list(F["spots"])
    for i, it in enumerate(W["chests"]["field"]):
        p = spots_f.pop(0)
        field["chests"].append({"id": f"{w}_field_c{i}", "x": p[0], "y": p[1], "item": it})
    ms = W["mini_side"]
    p = spots_f.pop(0)
    win = [f"set:{ms['flag']}"]
    if ms.get("reward_item"):
        win.append("give:" + ms["reward_item"])
    field["entities"].append({"id": ms["id"], "kind": "mini", "x": p[0], "y": p[1], "sprite": DB.UNIQUES[ms["id"]]["sprite"],
                              "name": DB.UNIQUES[ms["id"]]["name"], "world": w,
                              "cond": [f"q:{ms['quest']}=active", f"!flag:{ms['flag']}"],
                              "pre": ms["pre"], "post": ms["post"], "win_do": win,
                              "encounter": unique_encounter(ms["id"], f"{w}_out", "boss")})

    # ================================================================ cave (companion quest, summon)
    cg, C = MG.build_rooms(W["seed"] + 2, 28, 20, 3, 2, decor="bC")
    cave = new_map(f"{w}_cave", W["cave"], w, "cave", cg, f"{w}_field", bg=f"{w}_in", encounters_on=True)
    cave["start"] = list(C["start"])
    cvx, cvy = F["cave"]
    add_exit(field, cvx, cvy, cave["id"], C["start"][0], C["start"][1], "up")
    add_exit(cave, C["exit"][0], C["exit"][1], field["id"], cvx + 1, cvy, "right")
    usedp = set()
    mc = W["mini_companion"]
    ec = C["end_center"]
    usedp.add(ec)
    cave["entities"].append({"id": mc["id"], "kind": "mini", "x": ec[0], "y": ec[1], "sprite": DB.UNIQUES[mc["id"]]["sprite"],
                             "name": DB.UNIQUES[mc["id"]]["name"], "world": w,
                             "cond": [f"q:{mc['quest']}=active", f"!flag:{mc['flag']}"],
                             "need": [f"member:{comp_id}"],
                             "need_fail": [f"You sense {DB.CHARACTERS[comp_id]['name']} should be here for this."],
                             "pre": mc["pre"], "post": mc["post"],
                             "win_do": [f"set:{mc['flag']}", f"done:{mc['quest']}", f"give:gear:{mc['reward']}"],
                             "encounter": unique_encounter(mc["id"], f"{w}_in", "boss")})
    room_pool = C["dead_ends"] + C["rooms"]
    rnd.shuffle(room_pool)
    cave_items = [f"summon:{W['summon']}"]
    if W.get("key_chest_item"):
        cave_items.append(W["key_chest_item"])
    cave_items += W["chests"]["cave"]
    for i, it in enumerate(cave_items):
        room = room_pool[i % len(room_pool)]
        p = MG.free_spot_in_room(cg, room, rnd, avoid=usedp)
        usedp.add(p)
        cave["chests"].append({"id": f"{w}_cave_c{i}", "x": p[0], "y": p[1], "item": it})

    # ================================================================ area 2 (the road onward: tunnels, falls, steppes, stairs)
    a2name, a2style, a2cliffs = L["area2"]
    waterfall = L["side"][1] == "waterfall"
    ag, A = MG.build_field2(W["seed"] + 7, style=a2style, cliffs=a2cliffs, waterfall=waterfall)
    a2kind = "cave" if a2style == "underground" else "field"
    area2 = new_map(f"{w}_area2", a2name, w, a2kind, ag, f"{w}_field" if a2kind == "field" else f"{w}_dungeon",
                    bg=f"{w}_out" if a2kind == "field" else f"{w}_in", encounters_on=True)
    area2["start"] = list(A["start"])
    nx_, ny_ = F["north"]
    add_exit(field, nx_, ny_, area2["id"], A["start"][0], A["start"][1], "up")
    ex_, ey_ = A["entry"]
    for dx in (0, -1):
        add_exit(area2, ex_ + dx, ey_, field["id"], nx_, ny_ + 1, "down")
    a2spots = list(A["spots"])
    a2items = [f"gear:{area2_leg}", f"gear:{rares[2]}", "hi_potion", f"gear:{rares[3]}"]
    for i, it in enumerate(a2items):
        if not a2spots:
            break
        p = a2spots.pop(0)
        area2["chests"].append({"id": f"{w}_area2_c{i}", "x": p[0], "y": p[1], "item": it})

    # ================================================================ dungeon floor 1 -> floor 2 (boss)
    dungeon, dg, D = rooms_dungeon(f"{w}_dungeon", W["dungeon"], w, W["seed"] + 3, 40, 30, 4, 3, f"{w}_dungeon")
    gx2, gy2 = A["goal"]
    add_exit(area2, gx2, gy2, dungeon["id"], D["start"][0], D["start"][1], "up")
    add_exit(dungeon, D["exit"][0], D["exit"][1], area2["id"], gx2, gy2 + 1, "down")
    d2, dg2, D2 = rooms_dungeon(f"{w}_dungeon2", W["dungeon"] + ": Depths", w, W["seed"] + 5, 36, 28, 3, 3, f"{w}_dungeon")
    sx_, sy_ = D["end_center"]
    dg.g[sy_][sx_] = ">"
    dungeon["tiles"] = dg.rows()
    add_exit(dungeon, sx_, sy_, d2["id"], D2["start"][0], D2["start"][1], "up")
    add_exit(d2, D2["exit"][0], D2["exit"][1], dungeon["id"], sx_, sy_ + 1, "down")
    usedp = {(sx_, sy_)}
    rooms_d = D["dead_ends"] + D["rooms"]
    rnd.shuffle(rooms_d)
    for i, it in enumerate(W["chests"]["dungeon"]):
        room = rooms_d[i % len(rooms_d)]
        p = MG.free_spot_in_room(dg, room, rnd, avoid=usedp)
        usedp.add(p)
        dungeon["chests"].append({"id": f"{w}_dungeon_c{i}", "x": p[0], "y": p[1], "item": it})
    bc = D2["end_center"]
    boss = DB.UNIQUES[W["boss"]]
    if "King Goblin's mark" not in W["boss_post"][-1]:
        W["boss_post"] = list(W["boss_post"]) + ["Beside the Heart, a crude goblin totem crumbles to dust. King Goblin's mark."]
    d2["entities"].append({"id": W["boss"], "kind": "boss", "x": bc[0], "y": bc[1], "sprite": boss["sprite"],
                           "name": boss["name"], "world": w,
                           "cond": [f"q:{W['main_quest']}=active", f"!flag:{W['boss_flag']}"],
                           "pre": W["boss_pre"], "post": W["boss_post"],
                           "win_do": [f"set:{W['boss_flag']}"],
                           "encounter": unique_encounter(W["boss"], f"{w}_in", "boss")})
    used2 = {bc}
    rooms_d2 = D2["dead_ends"] + D2["rooms"]
    rnd.shuffle(rooms_d2)
    seal_room = rooms_d2.pop(0) if W.get("seal") else None
    for i, it in enumerate([f"gear:{f2_leg}", "elixir", f"gear:{rares[4 % len(rares)]}"]):
        room = rooms_d2[i % len(rooms_d2)]
        p = MG.free_spot_in_room(dg2, room, rnd, avoid=used2)
        used2.add(p)
        d2["chests"].append({"id": f"{w}_dungeon2_c{i}", "x": p[0], "y": p[1], "item": it})

    # ================================================================ sanctum (spirit & void) behind a seal on floor 2
    if W.get("seal"):
        Sl = W["seal"]
        sp = MG.free_spot_in_room(dg2, seal_room, rnd, avoid=used2)
        sg, SN = MG.build_sanctum(W["seed"] + 4)
        sanc = new_map(f"{w}_sanctum", "Sanctum of the Witness" if w == "spirit" else "Throne of Nothing",
                       w, "sanctum", sg, f"{w}_dungeon", bg=f"{w}_sanctum")
        sanc["start"] = list(SN["start"])
        add_exit(sanc, SN["exit"][0], SN["exit"][1], d2["id"], sp[0], sp[1] + 1, "down")
        d2["entities"].append({"id": f"seal_{w}", "kind": "seal", "x": sp[0], "y": sp[1], "sprite": f"seal_{w}",
                               "name": "Sealed Door", "world": w, "cond": [],
                               "keys": Sl["keys"], "flag": Sl["flag"], "quest": Sl["quest"],
                               "locked": Sl["locked"], "open": Sl["open"],
                               "to": sanc["id"], "tx": SN["start"][0], "ty": SN["start"][1]})
        om = DB.UNIQUES[Sl["omni"]]
        oc = SN["center"]
        sanc["entities"].append({"id": Sl["omni"], "kind": "omni", "x": oc[0], "y": oc[1], "sprite": om["sprite"],
                                 "name": om["name"], "world": w, "cond": [f"!flag:{Sl['omni_flag']}"],
                                 "need": ["party>=4"],
                                 "need_fail": ["It doesn't even notice you. You'll need four companions to stand before it."],
                                 "pre": Sl["pre"], "post": Sl["post"],
                                 "win_do": [f"set:{Sl['omni_flag']}", f"summon:{Sl['omni']}", f"done:{Sl['quest']}"],
                                 "encounter": unique_encounter(Sl["omni"], f"{w}_sanctum", "omni")})

    # ================================================================ side dungeon (hidden: cellar stairs or behind the falls)
    sname = L["side"][0]
    sdm, sdg, SD = rooms_dungeon(f"{w}_side", sname, w, W["seed"] + 9, 30, 22, 3, 2, f"{w}_dungeon", decor="bPC")
    if side_house:
        im, ig, isp, ch_c, st = interiors[side_house]
        add_exit(im, st[0], st[1], sdm["id"], SD["start"][0], SD["start"][1], "up")
        add_exit(sdm, SD["exit"][0], SD["exit"][1], im["id"], st[0] + 1, st[1], "right")
    else:
        zx, zy = A["waterfall_door"]
        add_exit(area2, zx, zy, sdm["id"], SD["start"][0], SD["start"][1], "up")
        add_exit(sdm, SD["exit"][0], SD["exit"][1], area2["id"], zx, zy + 1, "down")
        area2["waterfall"] = A["waterfall_cols"]
    mini = S2["mini"]
    ecx = SD["end_center"]
    sdm["entities"].append({"id": mini, "kind": "mini", "x": ecx[0], "y": ecx[1], "sprite": DB.UNIQUES[mini]["sprite"],
                            "name": DB.UNIQUES[mini]["name"], "world": w, "cond": [f"!flag:beat_{mini}"],
                            "pre": S2["pre"], "post": S2["post"], "win_do": [f"set:beat_{mini}"],
                            "encounter": unique_encounter(mini, f"{w}_in", "boss")})
    used3 = {ecx}
    rooms_s = SD["dead_ends"] + SD["rooms"]
    rnd.shuffle(rooms_s)
    for i, it in enumerate([f"gear:{side_chest_leg}", "hi_potion:2", f"gear:{rares[5 % len(rares)]}", "ether:2"]):
        room = rooms_s[i % len(rooms_s)]
        p = MG.free_spot_in_room(sdg, room, rnd, avoid=used3)
        used3.add(p)
        sdm["chests"].append({"id": f"{w}_side_c{i}", "x": p[0], "y": p[1], "item": it})

    # ---- point the main-quest giver at the new route
    for n in town["npcs"]:
        for b_ in n["script"]:
            if f"q:{W['main_quest']}=active" in b_.get("if", []):
                b_["say"] = list(b_["say"]) + [f"The way there is long: through the {W['field']}, then the {a2name}, and down into its depths."]

    # pawn shop: the world's common gear plus a couple of plain Nexus pieces
    W["pawn_stock"] = CG.commons(DB.WORLD_GEAR_LISTS[w], GEAR) + ["iron_sword", "short_bow", "oak_staff"]

# ------------------------------------------------------------------ King Goblin's Warren (opens after all six Hearts)
wg, WD = MG.build_rooms(9090, 44, 32, 4, 3, decor="bPS")
warren = new_map("goblin_warren", "King Goblin's Warren", "goblin", "dungeon", wg, "goblin_dungeon", bg="goblin_in", encounters_on=True)
warren["start"] = list(WD["start"])
warren["habitat"] = ["warren"]
add_exit(warren, WD["exit"][0], WD["exit"][1], "nexus", 14, 15, "down")
tx_, ty_ = WD["end_center"]
wg.g[ty_][tx_] = ">"
warren["tiles"] = wg.rows()
thg, TH = MG.build_sanctum(9191)
throne = new_map("goblin_throne", "The Hoard Throne", "goblin", "sanctum", thg, "goblin_dungeon", bg="goblin_in")
throne["start"] = list(TH["start"])
add_exit(warren, tx_, ty_, "goblin_throne", TH["start"][0], TH["start"][1], "up")
add_exit(throne, TH["exit"][0], TH["exit"][1], "goblin_warren", tx_, ty_ + 1, "down")
kg = DB.UNIQUES["king_goblin"]
throne["entities"].append({"id": "king_goblin", "kind": "boss", "x": TH["center"][0], "y": TH["center"][1], "sprite": kg["sprite"],
                           "name": kg["name"], "world": "void", "cond": ["!flag:beat_king_goblin"], "music": "king_goblin",
                           "pre": V2.KING["pre"], "post": V2.KING["post"], "win_do": ["set:beat_king_goblin", "gold:2000"],
                           "encounter": unique_encounter("king_goblin", "goblin_in", "king_goblin")})
rw = random.Random(77)
usedw = {(tx_, ty_)}
rooms_w = WD["dead_ends"] + WD["rooms"]
rw.shuffle(rooms_w)
for i, it in enumerate(["elixir", "hi_potion:3", "ether:3", "feather:2", "elixir"]):
    p = MG.free_spot_in_room(wg, rooms_w[i % len(rooms_w)], rw, avoid=usedw)
    usedw.add(p)
    warren["chests"].append({"id": f"warren_c{i}", "x": p[0], "y": p[1], "item": it})
QUESTS_EXTRA = {"main_king": {"title": "Origin of the Goblin Slayer", "world": "nexus", "kind": "main", "giver": "The Keeper",
                              "desc": "King Goblin cursed all six Hearths. Free them, then enter his Warren from the Nexus.",
                              "objective": "flag:beat_king_goblin"}}
CW.QUESTS.update(QUESTS_EXTRA)
for n in nexus["npcs"]:
    if n["id"] == "keeper":
        for b_ in n["script"]:
            if "set:intro_done" in b_.get("do", []):
                b_["do"] = list(b_["do"]) + ["quest:main_king"]
            if "set:ending_seen" in b_.get("do", []):
                b_["do"] = ["done:main_king"] + list(b_["do"])

# where pirates roam: the water world and any wilds with a lot of open water
for mid, m in maps.items():
    if m.get("encounters"):
        tags = list(m.get("habitat", []))
        wet = sum(row.count("~") for row in m["tiles"]) / float(m["w"] * m["h"])
        if m["world"] == "water" or (m["world"] in ("wind", "stone", "spirit") and wet > 0.06):
            tags.append("coast")
        m["habitat"] = tags

# ------------------------------------------------------------------ shops
shops = {"items": {"name": "Item Shop", "items": DB.SHOP_ITEMS, "gear": []},
         "nexus": {"name": "Wandering Merchant", "items": ["potion", "ether", "feather", "smoke_bomb"],
                   "gear": ["iron_sword", "short_bow", "oak_staff", "leather_coat", "copper_band"]}}
for w in WORLD_ORDER:
    shops[f"pawn_{w}"] = {"name": "Pawn Shop", "items": [], "gear": CW.WORLDS[w]["pawn_stock"]}
shops.update(tavern_shops)

# ------------------------------------------------------------------ db
db = DB.export()
db["uniques"] = {k: fix_unique(v) for k, v in db["uniques"].items()}
db["quests"] = CW.QUESTS
db["shops"] = shops
db["encounters"] = encounters
db["worlds"] = {w: {k: CW.WORLDS[w][k] for k in ("name", "town", "field", "cave", "dungeon", "landmark")} for w in WORLD_ORDER}
for w in WORLD_ORDER:
    db["worlds"][w]["area2"] = V2.LAYOUT[w]["area2"][0]
    db["worlds"][w]["side"] = V2.LAYOUT[w]["side"][0]
    db["worlds"][w]["tavern"] = V2.LAYOUT[w]["tavern"]
db["world_order"] = WORLD_ORDER
db["combos"] = V2.COMBOS

# ------------------------------------------------------------------ the Blessed and the seven hunts
import content_blessed as BL
for gid_, (nm, kind, style, el, bonus, fx, desc) in BL.BLESSED_GEAR.items():
    db["gear"][gid_] = {"name": nm, "kind": kind, "style": style, "el": el, "tier": "blessed", "q": 1.7,
                        "bonus": bonus, "fx": fx, "desc": desc, "type": "gear", "price": 1.0}
db["blessed_gear"] = list(BL.BLESSED_GEAR)
db["tiers"]["blessed"] = BL.BLESSED_TIER
db["tiers"]["hunt"] = BL.HUNT_TIER
for k, u in BL.BLESSED_UNIQUES.items():
    db["uniques"][k] = fix_unique(u)
db["enemy_skills"].update(BL.BLESSED_SKILLS)
db["blessed_lines"] = {"appear": BL.BLESSED_LINES, "first": BL.BLESSED_FIRST, "salvage": BL.BLESSED_SALVAGE}
db["hunts"] = {}
for hid, h in BL.HUNTS.items():
    b = dict(h["boss"])
    bid = b.pop("id")
    b["tier"] = "hunt"
    b["hunt"] = hid
    if bid in BL.HUNT_WEAK_EL:
        b["weak_el"] = BL.HUNT_WEAK_EL[bid]
    db["uniques"][bid] = fix_unique(b)
    hh = {k: v for k, v in h.items() if k != "boss"}
    hh["boss"] = bid
    db["hunts"][hid] = hh
db["hunt_reward"] = BL.HUNT_REWARD

with open(os.path.join(OUT, "db.json"), "w") as f:
    json.dump(db, f, indent=1)
for mid, m in maps.items():
    # validate: everything reachable from start
    g = MG.Grid(m["w"], m["h"])
    for y, row in enumerate(m["tiles"]):
        for x, ch in enumerate(row):
            g[(x, y)] = ch
    start = tuple(m["start"])
    reach = MG.reach2(g, start)
    for kind in ("exits", "npcs", "chests", "hidden", "entities"):
        for e in m[kind]:
            p = (e["x"], e["y"])
            ok = p in reach or any((p[0] + dx, p[1] + dy) in reach for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if not ok and not (kind == "npcs" and m["kind"] in ("town", "interior")):
                raise SystemExit(f"{mid}: {kind} {e.get('id', '')} at {p} unreachable")
    # npcs behind counters are fine (talk across)
    with open(os.path.join(OUT, "maps", mid + ".json"), "w") as f:
        json.dump(m, f, indent=1)
print(f"maps: {len(maps)}  encounters: {len(encounters)}  quests: {len(CW.QUESTS)}")
print("nexus portals:", nexus_portal)
