extends Node2D
## Corner minimap and full-screen map, drawn in the game's iron-and-leather style.
## Colors come from the world's own tiles, so each map looks like a little painting of the place.
## Fields, caves and dungeons are hidden under fog until you walk near; towns and rooms are known.

var map            # the Map scene
var img: Image
var tex: ImageTexture
var seen: PackedByteArray
var base_cols: Dictionary = {}   # tile char -> Color
var last_pos := Vector2i(-99, -99)
var full := false
var full_t := 0.0
var t := 0.0
# player-placed pins on the full map
var cur := Vector2i.ZERO           # map cursor (tile)
var picking := false               # icon picker open
var pick_idx := 0
var pick_on := -1                  # index of the pin being edited, or -1 for a new one

## Pins the player can drop: id, label, color.
const PINS := [
	["fight", "Fight", Color(1.0, 0.55, 0.25)],
	["hard", "Hard Enemy", Color(0.85, 0.2, 0.25)],
	["farm", "Farming Spot", Color(0.55, 0.9, 0.35)],
	["loot", "Loot", Color(1.0, 0.85, 0.3)],
	["secret", "Secret", Color(0.45, 0.85, 1.0)],
	["rest", "Rest Spot", Color(1.0, 0.55, 0.75)],
	["note", "Note", Color(0.92, 0.9, 0.85)],
]
const MAX_PINS := 40

const MINI := Rect2(384, 6, 90, 66)       # frame on screen
const MINI_PX := 3                         # pixels per tile in the corner map
const REVEAL := 8                          # tiles of fog lifted around you
const FOGGY := ["field", "cave", "dungeon", "area2", "side"]
const FOG := Color(0.05, 0.035, 0.035)


func setup(m) -> void:
	map = m
	img = Image.create(m.W, m.H, false, Image.FORMAT_RGBA8)
	_sample_colors()
	_load_seen()
	for y in m.H:
		for x in m.W:
			img.set_pixel(x, y, _cell_color(x, y))
	tex = ImageTexture.create_from_image(img)


func _foggy() -> bool:
	return str(map.m.kind) in FOGGY or str(map.m.id).ends_with("_area2") or str(map.m.id).begins_with("goblin")


func _load_seen() -> void:
	var key: String = "map:" + str(map.m.id)
	seen = PackedByteArray()
	seen.resize(map.W * map.H)
	if not _foggy():
		seen.fill(1)
		return
	var s: String = str(GS.flags.get(key, ""))
	if s != "":
		var raw := Marshalls.base64_to_raw(s)
		for i in min(raw.size() * 8, seen.size()):
			seen[i] = (raw[i >> 3] >> (i & 7)) & 1


func _save_seen() -> void:
	if not _foggy():
		return
	var raw := PackedByteArray()
	raw.resize(ceili(seen.size() / 8.0))
	for i in seen.size():
		if seen[i]:
			raw[i >> 3] |= 1 << (i & 7)
	GS.flags["map:" + str(map.m.id)] = Marshalls.raw_to_base64(raw)


## Average color of a tile picture, a little darkened so markers pop.
func _avg(texture: Texture2D, r: Rect2) -> Color:
	if texture == null:
		return Color(0.3, 0.3, 0.3)
	var im := texture.get_image()
	if im == null:
		return Color(0.3, 0.3, 0.3)
	var acc := Vector3.ZERO
	var n := 0.0
	var step := 4
	for y in range(int(r.position.y), int(r.end.y), step):
		for x in range(int(r.position.x), int(r.end.x), step):
			if x < im.get_width() and y < im.get_height():
				var c := im.get_pixel(x, y)
				if c.a > 0.3:
					acc += Vector3(c.r, c.g, c.b)
					n += 1.0
	if n == 0.0:
		return Color(0.2, 0.2, 0.2)
	acc /= n
	return Color(acc.x, acc.y, acc.z)


func _sample_colors() -> void:
	var ts: Texture2D = map.ts
	var named := {".": "ground0", "\"": "grass0", "F": "flower0", "^": "rock0", "=": "bridge", "#": "wall_top",
		"_": "floor0", "K": "cliff_top", "R": "roof_mid", "H": "hwall", "W": "hwall", "d": "door", "l": "lamp0",
		"n": "bench", "f": "fence", "c": "counter", "Q": "candle0", "S": "statue", "P": "pillar", "C": "crystal0",
		"b": "bones", "E": "cave_mouth", "O": "portal0", ">": "stairs", "v": "stairs_down", "w": "feat_tl0", "Y": "cliff_stairs"}
	if map.m.kind == "interior":
		named["_"] = "ifloor0"
		named["#"] = "iwall_top"
		named["."] = "ifloor0"
	for ch in named:
		base_cols[ch] = _avg(ts, Art.tile_rect(named[ch]))
	base_cols["~"] = _avg(map.tex_liquid, Rect2(32, 96, 32, 32)) if map.tex_liquid else Color(0.2, 0.35, 0.6)
	base_cols["V"] = base_cols["~"].lightened(0.3)
	base_cols[","] = _avg(map.tex_path, Rect2(32, 96, 32, 32)) if map.tex_path else base_cols["."].lightened(0.15)
	base_cols["T"] = _avg(map.tex_trees, Rect2(0, 0, 96, 110)).darkened(0.25) if map.tex_trees else Color(0.12, 0.3, 0.12)
	base_cols["s"] = Color(0.27, 0.17, 0.1)
	base_cols["A"] = Color(0.35, 0.34, 0.38)
	base_cols["G"] = Color(0.55, 0.4, 0.22)
	base_cols["M"] = Color(0.45, 0.45, 0.5)
	base_cols[" "] = Color(0, 0, 0, 0)


func _cell_color(x: int, y: int) -> Color:
	if not seen[y * map.W + x]:
		return FOG
	var ch: String = map.tile_at(Vector2i(x, y))
	var c: Color = base_cols.get(ch, base_cols.get(".", Color(0.3, 0.3, 0.3)))
	if ch == " ":
		return Color(0, 0, 0, 1)
	# roofs read as roofs, doors as bright notches
	if ch == "R" and map.tile_at(Vector2i(x, y - 1)) != "R":
		c = c.lightened(0.15)
	if ch == "d":
		c = Color(0.95, 0.8, 0.45)
	if ch in ["T", "^", "K", "#", "R", "H", "W"]:
		# a darker rim where solid things meet open ground: gives the map some depth
		if map.tile_at(Vector2i(x, y + 1)) in [".", ",", "\"", "F", "_"]:
			c = c.darkened(0.25)
	return c


func _process(delta: float) -> void:
	t += delta
	if map == null:
		return
	if map.ppos != last_pos:
		last_pos = map.ppos
		_reveal(map.ppos)
	if full:
		full_t = minf(1.0, full_t + delta * 6.0)
	queue_redraw()


func _reveal(p: Vector2i) -> void:
	if not _foggy():
		return
	var changed := false
	for dy in range(-REVEAL, REVEAL + 1):
		for dx in range(-REVEAL, REVEAL + 1):
			if dx * dx + dy * dy > REVEAL * REVEAL + 2:
				continue
			var x := p.x + dx
			var y := p.y + dy
			if x < 0 or y < 0 or x >= map.W or y >= map.H:
				continue
			var i: int = y * map.W + x
			if not seen[i]:
				seen[i] = 1
				img.set_pixel(x, y, Color(0, 0, 0, 0))
				changed = true
	if changed:
		for dy in range(-REVEAL, REVEAL + 1):
			for dx in range(-REVEAL, REVEAL + 1):
				var x := p.x + dx
				var y := p.y + dy
				if x >= 0 and y >= 0 and x < map.W and y < map.H and seen[y * map.W + x]:
					img.set_pixel(x, y, _cell_color(x, y))
		tex.update(img)
		_save_seen()


# ------------------------------------------------------------------ the player's own pins

func pins() -> Array:
	var v = GS.flags.get("pins:" + str(map.m.id), [])
	return v if v is Array else []


func _set_pins(a: Array) -> void:
	GS.flags["pins:" + str(map.m.id)] = a


func _pin_at(p: Vector2i) -> int:
	var a := pins()
	for i in a.size():
		if int(a[i][0]) == p.x and int(a[i][1]) == p.y:
			return i
	return -1


func _pin_info(kind: String) -> Array:
	for p in PINS:
		if p[0] == kind:
			return p
	return PINS[PINS.size() - 1]


func open_full() -> void:
	full = true
	full_t = 0.0
	picking = false
	cur = map.ppos


## Runs one frame of full-map input. Returns true when the map should close.
func full_input() -> bool:
	if picking:
		var opts := PINS.size() + (1 if pick_on >= 0 else 0)
		var v := Inp.vert()
		if v:
			pick_idx = wrapi(pick_idx + v, 0, opts)
			Audio.sfx("cursor")
		if Inp.ok():
			var a := pins()
			if pick_idx >= PINS.size():
				a.remove_at(pick_on)
				Audio.sfx("cancel")
			else:
				var entry := [cur.x, cur.y, PINS[pick_idx][0]]
				if pick_on >= 0:
					a[pick_on] = entry
				elif a.size() < MAX_PINS:
					a.append(entry)
				Audio.sfx("confirm")
			_set_pins(a)
			picking = false
		elif Inp.back() or Inp.map_key():
			picking = false
			Audio.sfx("cancel")
		return false
	var h := Inp.horiz()
	var vv := Inp.vert()
	if h or vv:
		cur = Vector2i(clampi(cur.x + h, 0, map.W - 1), clampi(cur.y + vv, 0, map.H - 1))
	if Inp.ok():
		pick_on = _pin_at(cur)
		pick_idx = 0
		if pick_on >= 0:
			for i in PINS.size():
				if PINS[i][0] == str(pins()[pick_on][2]):
					pick_idx = i
		picking = true
		Audio.sfx("cursor")
		return false
	if Inp.back() or Inp.map_key():
		return true
	return false


## A pin: a little banner on a post, with its symbol.
func _pin(p: Vector2, kind: String, big: bool) -> void:
	var info := _pin_info(kind)
	var c: Color = info[2]
	var ink := Color(0.04, 0.02, 0.02)
	var k := 2.0 if big else 1.0
	if not big:
		# corner map: a bright dot with a dark ring, readable at 3px per tile
		draw_rect(Rect2(p - Vector2(2, 2), Vector2(5, 5)), ink)
		draw_rect(Rect2(p - Vector2(1, 1), Vector2(3, 3)), c)
		return
	# post
	draw_rect(Rect2(p + Vector2(-1, -14), Vector2(2, 14)), ink)
	draw_rect(Rect2(p + Vector2(-0.5, -13), Vector2(1, 13)), Color(0.75, 0.7, 0.6))
	# banner
	var b := Rect2(p + Vector2(0, -15), Vector2(11, 9))
	draw_rect(b.grow(1), ink)
	draw_rect(b, c)
	draw_rect(Rect2(b.position, Vector2(b.size.x, 1)), c.lightened(0.4))
	var g := b.position + Vector2(3, 2)
	match kind:
		"fight":       # crossed swords
			for i in 5:
				draw_rect(Rect2(g + Vector2(i, i), Vector2(1, 1)), ink)
				draw_rect(Rect2(g + Vector2(4 - i, i), Vector2(1, 1)), ink)
		"hard":        # skull
			draw_rect(Rect2(g + Vector2(0, 0), Vector2(5, 3)), Color(0.95, 0.92, 0.85))
			draw_rect(Rect2(g + Vector2(1, 3), Vector2(3, 2)), Color(0.95, 0.92, 0.85))
			draw_rect(Rect2(g + Vector2(1, 1), Vector2(1, 1)), ink)
			draw_rect(Rect2(g + Vector2(3, 1), Vector2(1, 1)), ink)
		"farm":        # coin pouch
			draw_rect(Rect2(g + Vector2(1, 1), Vector2(3, 4)), Color(0.55, 0.35, 0.15))
			draw_rect(Rect2(g + Vector2(0, 2), Vector2(5, 2)), Color(0.55, 0.35, 0.15))
			draw_rect(Rect2(g + Vector2(2, 0), Vector2(1, 1)), ink)
			draw_rect(Rect2(g + Vector2(2, 2), Vector2(1, 1)), Color(1, 0.85, 0.3))
		"loot":        # star
			draw_rect(Rect2(g + Vector2(2, 0), Vector2(1, 5)), ink)
			draw_rect(Rect2(g + Vector2(0, 2), Vector2(5, 1)), ink)
			draw_rect(Rect2(g + Vector2(1, 1), Vector2(3, 3)), ink)
		"secret":      # question mark
			draw_rect(Rect2(g + Vector2(1, 0), Vector2(3, 1)), ink)
			draw_rect(Rect2(g + Vector2(3, 1), Vector2(1, 1)), ink)
			draw_rect(Rect2(g + Vector2(2, 2), Vector2(1, 1)), ink)
			draw_rect(Rect2(g + Vector2(2, 4), Vector2(1, 1)), ink)
		"rest":        # heart
			draw_rect(Rect2(g + Vector2(0, 0), Vector2(2, 2)), ink)
			draw_rect(Rect2(g + Vector2(3, 0), Vector2(2, 2)), ink)
			draw_rect(Rect2(g + Vector2(0, 1), Vector2(5, 2)), ink)
			draw_rect(Rect2(g + Vector2(1, 3), Vector2(3, 1)), ink)
			draw_rect(Rect2(g + Vector2(2, 4), Vector2(1, 1)), ink)
		_:             # note: lines of writing
			for i in 3:
				draw_rect(Rect2(g + Vector2(0, i * 2), Vector2(5 - (i % 2), 1)), ink)
	draw_rect(Rect2(p - Vector2(1, 1) * k, Vector2(2, 2) * k), ink)


# ------------------------------------------------------------------ markers

## [{"p": Vector2i, "kind": "quest"|"turnin"|"npc"|"chest"|"exit"|"boss"}]
func _markers() -> Array:
	var out := []
	for e in map.m.exits:
		var ep := Vector2i(int(e.x), int(e.y))
		if map.tile_at(ep) != "d":
			out.append({"p": ep, "kind": "exit"})
	for c in map.chests:
		if not c.opened:
			out.append({"p": Vector2i(int(c.data.x), int(c.data.y)), "kind": "chest"})
	for b in map.bosses:
		if b.visible and b.data.kind != "seal" and not GS.flag(str(b.data.get("flag", "_"))):
			out.append({"p": Vector2i(int(b.data.x), int(b.data.y)), "kind": "boss", "always": str(b.data.kind) == "hunt"})
	for n in map.npcs:
		if not n.actor.visible:
			continue
		out.append({"p": n.pos, "kind": _npc_kind(n.data)})
	return out


func _npc_kind(d: Dictionary) -> String:
	for branch in d.get("script", []):
		if GS.check(branch.get("if", [])):
			for c in branch.get("if", []):
				if str(c).ends_with("=ready"):
					return "turnin"
			var acts: Array = branch.get("do", [])
			if branch.has("ask"):
				acts = acts + branch.ask.get("yes", {}).get("do", [])
			for a in acts:
				var s := str(a)
				if s.begins_with("quest:") or s.begins_with("recruit:") or s.begins_with("hunt_start:"):
					return "quest"
			return "npc"
	return "npc"


func _marker(p: Vector2, kind: String, big: bool) -> void:
	var k := 2.0 if big else 1.0
	var ink := Color(0.04, 0.02, 0.02)
	match kind:
		"npc":
			if big:
				draw_rect(Rect2(p - Vector2(2, 2), Vector2(4, 4)), ink)
				draw_rect(Rect2(p - Vector2(1, 1), Vector2(2, 2)), Color(0.85, 0.8, 0.72))
			else:
				draw_rect(Rect2(p, Vector2(1, 1)), Color(0.85, 0.8, 0.72, 0.8))
		"quest", "turnin":
			var c := Art.YELLOW if kind == "quest" else Color(0.55, 1.0, 0.6)
			var bob := roundf(sin(t * 4.0) * k)
			draw_rect(Rect2(p + Vector2(-1.5 * k, -5 * k + bob), Vector2(3 * k, 7 * k)), ink)
			draw_rect(Rect2(p + Vector2(-0.5 * k, -4 * k + bob), Vector2(k, 3 * k)), c)
			draw_rect(Rect2(p + Vector2(-0.5 * k, 0 + bob), Vector2(k, k)), c)
		"chest":
			draw_rect(Rect2(p - Vector2(1.5, 1.5) * k, Vector2(3, 3) * k), ink)
			draw_rect(Rect2(p - Vector2(0.5, 0.5) * k, Vector2(1, 1) * k * 1.5), Color(1, 0.8, 0.3))
		"exit":
			var pts := PackedVector2Array([p + Vector2(0, -2.5) * k, p + Vector2(2.5, 0) * k, p + Vector2(0, 2.5) * k, p + Vector2(-2.5, 0) * k])
			draw_colored_polygon(pts, ink)
			pts = PackedVector2Array([p + Vector2(0, -1.5) * k, p + Vector2(1.5, 0) * k, p + Vector2(0, 1.5) * k, p + Vector2(-1.5, 0) * k])
			draw_colored_polygon(pts, Color(0.55, 0.85, 1.0, 0.7 + 0.3 * sin(t * 3.0)))
		"boss":
			var pulse := 0.6 + 0.4 * sin(t * 5.0)
			draw_circle(p, 3.0 * k, ink)
			draw_circle(p, 2.0 * k, Color(0.9, 0.15, 0.1, pulse))
			draw_rect(Rect2(p + Vector2(-1, -0.5) * k, Vector2(0.8, 0.8) * k), ink)
			draw_rect(Rect2(p + Vector2(0.4, -0.5) * k, Vector2(0.8, 0.8) * k), ink)


func _player(p: Vector2, big: bool) -> void:
	var k := 2.2 if big else 1.2
	var d: Vector2 = Vector2(map.DIRS[map.face])
	var side := Vector2(-d.y, d.x)
	var tip := p + d * 3.0 * k
	var a := p - d * 2.0 * k + side * 2.2 * k
	var b := p - d * 2.0 * k - side * 2.2 * k
	var glow := 0.5 + 0.5 * sin(t * 6.0)
	draw_circle(p, 4.5 * k, Color(1, 0.2, 0.1, 0.12 + 0.1 * glow))
	draw_colored_polygon(PackedVector2Array([tip + d, a + (a - p).normalized(), b + (b - p).normalized()]), Color(0.04, 0.02, 0.02))
	draw_colored_polygon(PackedVector2Array([tip, a, b]), Color(1.0, 0.9, 0.55))
	draw_rect(Rect2(p - Vector2(0.5, 0.5) * k, Vector2(1, 1) * k), Color(1, 0.25, 0.15))


# ------------------------------------------------------------------ drawing

func _draw() -> void:
	if map == null or tex == null:
		return
	if is_instance_valid(Main.inst.battle_node):
		return       # no map over a fight
	var show_mini: bool = GS.settings.get("minimap", true) and not full and not map.dialog.active and not map.menu.active
	if show_mini and not map.m.kind == "interior":
		_draw_mini()
	if full:
		_draw_full()


func _draw_mini() -> void:
	var r := MINI
	Art.window(self, r)
	var inner := r.grow(-5)
	draw_rect(inner, FOG)
	var tiles := (inner.size / MINI_PX).floor()
	var c := Vector2(map.player.position) / float(map.TS)
	var src_pos := (c - tiles / 2.0)
	src_pos.x = clampf(src_pos.x, minf(0.0, (map.W - tiles.x) / 2.0), maxf(0.0, map.W - tiles.x))
	src_pos.y = clampf(src_pos.y, minf(0.0, (map.H - tiles.y) / 2.0), maxf(0.0, map.H - tiles.y))
	src_pos = src_pos.round()
	# draw only the part of the map image that exists
	var s0 := Vector2(maxf(0.0, src_pos.x), maxf(0.0, src_pos.y))
	var s1 := Vector2(minf(map.W, src_pos.x + tiles.x), minf(map.H, src_pos.y + tiles.y))
	if s1.x > s0.x and s1.y > s0.y:
		var dst := Rect2(inner.position + (s0 - src_pos) * MINI_PX, (s1 - s0) * MINI_PX)
		draw_texture_rect_region(tex, dst, Rect2(s0, s1 - s0))
	var to_screen := func(tp: Vector2) -> Vector2:
		return (inner.position + (tp - src_pos) * MINI_PX).round()
	for mk in _markers():
		if not seen[mk.p.y * map.W + mk.p.x] and mk.kind not in ["quest", "turnin"] and not mk.get("always", false):
			continue
		var sp: Vector2 = to_screen.call(Vector2(mk.p) + Vector2(0.5, 0.5))
		if inner.grow(-1).has_point(sp):
			_marker(sp, mk.kind, false)
	for pn in pins():
		var sp2: Vector2 = to_screen.call(Vector2(float(pn[0]), float(pn[1])) + Vector2(0.5, 0.5))
		if inner.grow(-2).has_point(sp2):
			_pin(sp2, str(pn[2]), false)
	_player(to_screen.call(c + Vector2(0, -0.3)), false)
	# inner shadow so the map sits inside the frame
	draw_rect(Rect2(inner.position, Vector2(inner.size.x, 1)), Color(0, 0, 0, 0.5))
	draw_rect(Rect2(inner.position, Vector2(1, inner.size.y)), Color(0, 0, 0, 0.5))
	var label := "M: Map   Shift: %s" % ("Walk" if GS.settings.get("auto_run", false) else "Run")
	Art.text(self, Vector2(r.end.x - Art.width(label, 8) - 2, r.end.y + 1), label, Color(0.8, 0.75, 0.7, 0.75), 8)


func _draw_full() -> void:
	var a := full_t
	draw_rect(Rect2(0, 0, 480, 270), Color(0, 0, 0, 0.6 * a))
	var frame := Rect2(14, 10, 452, 250)
	Art.window(self, frame)
	# title plaque
	var world_name: String = str(DB.d.worlds[map.world].name) if DB.d.worlds.has(map.world) and DB.d.worlds[map.world].has("name") else ""
	var title := str(map.m.name)
	Art.text_center(self, Vector2(240, frame.position.y + 6), title, Art.YELLOW, 14)
	if world_name != "" and world_name != title:
		Art.text_center(self, Vector2(240, frame.position.y + 22), world_name, Art.GREY, 9)
	var area := Rect2(frame.position.x + 12, frame.position.y + 36, frame.size.x - 24, frame.size.y - 64)
	var sc := floorf(minf(area.size.x / map.W, area.size.y / map.H))
	sc = clampf(sc, 2.0, 12.0)
	var size := Vector2(map.W, map.H) * sc
	var o := (area.position + (area.size - size) / 2.0).round()
	# parchment-dark backing with a thin iron rim
	draw_rect(Rect2(o - Vector2(3, 3), size + Vector2(6, 6)), Color(0.04, 0.03, 0.03))
	draw_rect(Rect2(o - Vector2(2, 2), size + Vector2(4, 4)), Color(0.42, 0.39, 0.43))
	draw_rect(Rect2(o - Vector2(1, 1), size + Vector2(2, 2)), Color(0.04, 0.03, 0.03))
	draw_texture_rect(tex, Rect2(o, size), false, Color(1, 1, 1, a))
	# a faint grid, like a surveyor's chart
	var gc := Color(0, 0, 0, 0.12)
	for gx in range(0, map.W + 1, 4):
		draw_rect(Rect2(o.x + gx * sc, o.y, 1, size.y), gc)
	for gy in range(0, map.H + 1, 4):
		draw_rect(Rect2(o.x, o.y + gy * sc, size.x, 1), gc)
	for mk in _markers():
		if not seen[mk.p.y * map.W + mk.p.x] and mk.kind not in ["quest", "turnin"] and not mk.get("always", false):
			continue
		_marker((o + (Vector2(mk.p) + Vector2(0.5, 0.5)) * sc).round(), mk.kind, true)
	for pn in pins():
		_pin((o + (Vector2(float(pn[0]), float(pn[1])) + Vector2(0.5, 0.8)) * sc).round(), str(pn[2]), true)
	var c := Vector2(map.player.position) / float(map.TS) + Vector2(0, -0.3)
	_player((o + c * sc).round(), true)
	# the pin cursor: blinking corner brackets around one tile
	var cr := Rect2(o + Vector2(cur) * sc, Vector2(sc, sc)).grow(2)
	var cc := Color(1, 0.95, 0.7, 0.65 + 0.35 * sin(t * 8.0))
	var L := 4.0
	for corner in [cr.position, Vector2(cr.end.x, cr.position.y), Vector2(cr.position.x, cr.end.y), cr.end]:
		var sx := 1.0 if corner.x == cr.position.x else -1.0
		var sy := 1.0 if corner.y == cr.position.y else -1.0
		draw_rect(Rect2(corner + Vector2(minf(0.0, sx * L), minf(0.0, sy * 1.0)), Vector2(L, 1)).abs(), cc)
		draw_rect(Rect2(corner + Vector2(minf(0.0, sx * 1.0), minf(0.0, sy * L)), Vector2(1, L)).abs(), cc)
	var under := _pin_at(cur)
	if under >= 0 and not picking:
		var nm: String = _pin_info(str(pins()[under][2]))[1]
		Art.text(self, (cr.position + Vector2(cr.size.x + 4, -2)).round(), nm, Art.WHITE, 9)
	# legend
	var ly := frame.end.y - 22
	var items := [["quest", "Quest"], ["turnin", "Report"], ["npc", "Person"], ["chest", "Treasure"], ["exit", "Exit"], ["boss", "Danger"]]
	var x := frame.position.x + 22
	for it in items:
		_marker(Vector2(x, ly + 7), it[0], true)
		Art.text(self, Vector2(x + 9, ly), it[1], Art.GREY, 9)
		x += 18 + Art.width(it[1], 9) + 10
	var explored := ""
	if _foggy():
		var n := 0
		for v in seen:
			n += v
		explored = "Explored %d%%" % int(round(100.0 * n / max(1, seen.size())))
		Art.text_right(self, Vector2(frame.end.x - 14, ly), explored, Art.GREY, 9)
	Art.text_right(self, Vector2(frame.end.x - 14, frame.position.y + 8), "M / X: close", Color(0.7, 0.66, 0.6), 8)
	Art.text(self, Vector2(frame.position.x + 14, frame.position.y + 8), "Arrows: move   Z: place pin", Color(0.7, 0.66, 0.6), 8)
	Art.text(self, Vector2(frame.position.x + 14, frame.position.y + 18), "Pins %d/%d" % [pins().size(), MAX_PINS], Color(0.6, 0.56, 0.52), 8)
	if picking:
		_draw_picker(frame)


func _draw_picker(frame: Rect2) -> void:
	var opts := PINS.size() + (1 if pick_on >= 0 else 0)
	var r := Rect2(frame.end.x - 142, frame.position.y + 36, 128, 24 + opts * 20)
	Art.window(self, r)
	Art.text(self, r.position + Vector2(10, 5), "Change pin" if pick_on >= 0 else "Place a pin", Art.YELLOW, 9)
	for i in opts:
		var y := r.position.y + 18 + i * 20
		if i < PINS.size():
			_pin(Vector2(r.position.x + 12, y + 18), PINS[i][0], true)
			Art.text(self, Vector2(r.position.x + 46, y + 4), PINS[i][1], Art.WHITE if i == pick_idx else Art.GREY)
		else:
			Art.text(self, Vector2(r.position.x + 46, y + 4), "Remove pin", Art.RED if i == pick_idx else Art.GREY)
		if i == pick_idx:
			Art.cursor(self, Vector2(r.position.x + 46, y + 4))
