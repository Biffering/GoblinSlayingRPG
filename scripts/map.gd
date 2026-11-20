extends Node2D
## Exploration: tiles, the player, NPCs, chests, bosses, exits, random encounters, and talking.

const Dialog := preload("res://scripts/dialog.gd")
const Menu := preload("res://scripts/menu.gd")
const Shop := preload("res://scripts/shop.gd")
const Weather := preload("res://scripts/weather.gd")
const Minimap := preload("res://scripts/minimap.gd")

const DIRS := [Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1)]  # down, left, right, up
const BLOCK := " T^~#RHWacflnwLPtCSKVBkuoqxXpjJzgeiyQsAGM"
const SCREEN := Vector2(480, 270)
## Exploring camera zoom: 1.0 = old close-up; 0.75 shows a third more world each way.
const ZOOM := 0.75
const VIEW := SCREEN / ZOOM
## People on the map are drawn a little under full LPC size so they sit better against 32px buildings.
const PEOPLE := 0.8
const TS := 32                      # tile size (LPC art)
const WF := 9                       # walk sheet columns: stand + 8 walking frames

var mid := ""
var m: Dictionary
var world := ""
var tiles: Array = []
var W := 0
var H := 0
var ts: Texture2D
var start := Vector2i.ZERO
var start_face := 0

var world_node: Node2D
var tile_layer: TileLayer
var ents: Node2D
var player: Actor2D
var ppos := Vector2i.ZERO
var face := 0
var moving := false
var walk_t := 0.0
var npcs: Array = []      # {data, actor, pos, home, wander_t, face, job...}
var work_fx: Array = []   # little particles from townsfolk at work: {p, v, t, life, col, size}
const FACE_IDX := {"down": 0, "left": 1, "right": 2, "up": 3}
const JOB_FRAMES := {"hoe": 8, "water": 8, "dig": 8, "mine": 6, "chop": 6, "smith": 6, "seance": 7, "pray": 7, "fish": 13}
const JOB_FPS := {"hoe": 9.0, "water": 8.0, "dig": 9.0, "mine": 8.0, "chop": 8.0, "smith": 10.0, "seance": 7.0, "pray": 5.0, "fish": 8.0}
var chests: Array = []
var bosses: Array = []
var ui: CanvasLayer
var dialog
var menu
var banner_text := ""
var banner_t := 0.0
var hud: HUD
var rng := RandomNumberGenerator.new()
var encounter_steps := 0
var cam := Vector2.ZERO
var busy := false
var anim_t := 0.0
var sparkles: Array = []
var weather_layer: CanvasLayer
var minimap
# lighting: a darkness pass with holes, a glow pass, and the lights that feed them
var light_layer: CanvasLayer
var dark_rect: ColorRect
var glow_rect: ColorRect
var static_lights: Array = []    # {p: world px, r: radius px, c: Color, s: strength, f: flicker}
var motes: Array = []            # dust floating in torchlight / sunbeams outdoors
var ambient := Color(0, 0, 0, 0)
var vignette := 0.3
var torch := 0.0                 # radius of the light the hero carries (0 = none)
var weather


class TileLayer extends Node2D:
	var map

	func _process(_d: float) -> void:
		queue_redraw()

	func _draw() -> void:
		map._draw_tiles(self)


class Overlay extends Node2D:
	var map

	func _process(_d: float) -> void:
		queue_redraw()

	func _draw() -> void:
		map._draw_overlay(self)


class HUD extends Node2D:
	var map

	func _process(_d: float) -> void:
		queue_redraw()

	func _draw() -> void:
		map._draw_hud(self)


class Chest extends Node2D:
	var data: Dictionary
	var opened := false

	func _draw() -> void:
		var t := Art.tex("res://assets/ui/chest_open.png" if opened else "res://assets/ui/chest.png")
		draw_texture(t, Vector2(-16, -32))


class Boss extends Node2D:
	var data: Dictionary
	var tex: Texture2D
	var t := 0.0

	func _process(d: float) -> void:
		t += d
		queue_redraw()

	func _draw() -> void:
		if tex == null:
			return
		var bob := roundf(sin(t * 2.0) * 1.0)
		draw_rect(Rect2(-14, -4, 28, 5), Color(0, 0, 0, 0.3))
		draw_texture(tex, Vector2(-tex.get_width() * 0.5, -tex.get_height() + bob))


func setup(map_id: String, x: int, y: int, f: int) -> void:
	mid = map_id
	start = Vector2i(x, y)
	start_face = f


func _ready() -> void:
	rng.randomize()
	m = DB.map(mid)
	world = m.world
	tiles = m.tiles
	W = int(m.w)
	H = int(m.h)
	ts = Art.tileset(world)
	_load_terrain()
	world_node = Node2D.new()
	world_node.scale = Vector2(ZOOM, ZOOM)
	add_child(world_node)
	tile_layer = TileLayer.new()
	tile_layer.map = self
	world_node.add_child(tile_layer)
	ents = Node2D.new()
	ents.y_sort_enabled = true
	world_node.add_child(ents)
	var ov := Overlay.new()
	ov.map = self
	world_node.add_child(ov)
	# chests
	for c in m.chests:
		var ch := Chest.new()
		ch.data = c
		ch.opened = GS.flag("chest:" + c.id)
		ch.position = _tile_px(Vector2i(int(c.x), int(c.y)))
		ents.add_child(ch)
		chests.append(ch)
	# npcs
	for n in m.npcs:
		_spawn_npc(n)
	_setup_hunt()
	# bosses / minibosses / seals
	for e in m.entities:
		_spawn_boss(e)


	# player
	player = Actor2D.new()
	player.scale = Vector2(PEOPLE, PEOPLE)
	ents.add_child(player)
	ppos = start
	face = start_face
	_refresh_player()
	player.position = _tile_px(ppos)
	trail = [{"p": player.position, "f": face * WF}]
	_place_followers()
	# weather (outdoors only)
	GS.weather_world = world
	GS.weather_on = m.kind in ["town", "field"] and Weather.BY_WORLD.has(world)
	_setup_lighting()
	weather_layer = CanvasLayer.new()
	weather_layer.layer = 8
	add_child(weather_layer)
	weather = Weather.new()
	weather_layer.add_child(weather)
	# ui
	ui = CanvasLayer.new()
	ui.layer = 10
	add_child(ui)
	hud = HUD.new()
	hud.map = self
	ui.add_child(hud)
	dialog = Dialog.new()
	ui.add_child(dialog)
	menu = Menu.new()
	menu.map = self
	ui.add_child(menu)
	_refresh_visibility()
	_reset_encounter()
	_update_camera(true)
	minimap = Minimap.new()
	ui.add_child(minimap)
	ui.move_child(minimap, hud.get_index() + 1)     # above the HUD, under dialog and menus
	minimap.setup(self)
	banner_text = m.name
	banner_t = 2.4
	Audio.music(m.music)
	GS.location = {"map": mid, "x": ppos.x, "y": ppos.y, "face": face}
	GS.changed.connect(_refresh_player)
	if mid == "nexus" and not GS.flag("intro_done"):
		_intro.call_deferred()


func _intro() -> void:
	busy = true
	await get_tree().create_timer(0.6).timeout
	await dialog.say(["...", "Warmth. A crackling fire. Someone humming.", "You open your eyes."])
	busy = false
	var keeper = _npc_by_id("keeper")
	if keeper:
		await _talk(keeper)


func _npc_by_id(id: String):
	for n in npcs:
		if n.data.id == id:
			return n
	return null


func _refresh_player() -> void:
	if not is_instance_valid(player):
		return
	var tier := GS.hero_tier()
	player.setup("res://assets/chars/hero_t%d.png" % tier, Vector2(64, 64), WF, "res://assets/chars/hero_t%d_aura.png" % tier)
	player.shadow_w = 10
	var h: Dictionary = GS.roster.hero
	var colors := GS.aura_colors(h)
	player.set_aura(colors, GS.aura_strength(h), GS.aura_radius(h))
	player.set_glow(not h.boosts.is_empty())
	player.set_frame(face * WF)
	_refresh_followers()


## Party members walk in a line behind the leader.
var followers: Array = []   # Actor2D
var trail: Array = []       # recent leader positions (pixels) and facings


func _refresh_followers() -> void:
	var ids: Array = GS.party.slice(1)
	while followers.size() > ids.size():
		followers.pop_back().queue_free()
	for i in ids.size():
		var a: Actor2D
		if i < followers.size():
			a = followers[i]
		else:
			a = Actor2D.new()
			a.scale = Vector2(PEOPLE, PEOPLE)
			ents.add_child(a)
			followers.append(a)
			a.position = player.position
		var cid: String = ids[i]
		var mm: Dictionary = GS.roster[cid]
		a.setup("res://assets/chars/%s.png" % cid, Vector2(64, 64), WF, "res://assets/chars/%s_aura.png" % cid)
		a.shadow_w = 10
		a.set_aura(GS.aura_colors(mm), GS.aura_strength(mm), GS.aura_radius(mm))
		a.set_glow(not mm.boosts.is_empty())


func _push_trail() -> void:
	if not trail.is_empty() and trail[0].p.distance_to(player.position) < 0.5:
		trail[0].f = player.frame
	else:
		trail.push_front({"p": player.position, "f": player.frame})
	while trail.size() > 200:
		trail.pop_back()
	_place_followers()


## Each follower stands about one tile further back along the leader's path.
func _place_followers() -> void:
	for i in followers.size():
		var want := 24.0 * (i + 1)
		var acc := 0.0
		var pos: Vector2 = player.position
		var fr: int = player.frame
		var found := false
		for k in range(1, trail.size()):
			var seg: float = trail[k - 1].p.distance_to(trail[k].p)
			if acc + seg >= want:
				var t: float = (want - acc) / max(0.001, seg)
				pos = trail[k - 1].p.lerp(trail[k].p, t).round()
				fr = int(trail[k].f)
				found = true
				break
			acc += seg
			pos = trail[k].p
			fr = int(trail[k].f)
		followers[i].position = pos
		followers[i].set_frame(fr)
		followers[i].visible = found


func _spawn_npc(n: Dictionary) -> Dictionary:
	var a := Actor2D.new()
	a.scale = Vector2(PEOPLE, PEOPLE)
	a.setup("res://assets/chars/npc_%s.png" % n.id, Vector2(64, 64), WF)
	a.shadow_w = 10
	var p := Vector2i(int(n.x), int(n.y))
	a.position = _tile_px(p)
	var fd: int = FACE_IDX.get(str(n.get("face", "down")), 0)
	a.set_frame(fd * WF)
	ents.add_child(a)
	var nd := {"data": n, "actor": a, "pos": p, "home": p, "wander_t": rng.randf_range(1.0, 4.0), "face": fd,
		"home_face": fd, "look_t": rng.randf_range(3.0, 9.0), "job": str(n.get("job", "")), "seq": [], "si": 0, "ft": 0.0}
	if nd.job != "" and ResourceLoader.exists("res://assets/chars/npc_%s_job.png" % n.id):
		_npc_to_work(nd)
		nd.si = rng.randi() % 6
	else:
		nd.job = ""
	npcs.append(nd)
	return nd


# ------------------------------------------------------------------ legendary treasure hunts

const HUNT_KINDS := ["field", "area2"]


func _hunt_state() -> Dictionary:
	var v = GS.flags.get("hunt_active", {})
	return v if v is Dictionary else {}


func _outdoor() -> bool:
	return str(m.kind) in HUNT_KINDS or str(m.id).ends_with("_area2")


## A walkable, reachable tile at least `min_d` steps from `from` (and at most `max_d`).
func _open_tile(from: Vector2i, min_d: int, max_d: int) -> Vector2i:
	var seen := {from: 0}
	var q := [from]
	var cands := []
	while not q.is_empty():
		var p: Vector2i = q.pop_front()
		var dd: int = seen[p]
		if dd >= min_d and dd <= max_d and tile_at(p) in [".", "\"", "F", ","] and not _occupied(p):
			cands.append(p)
		if dd >= max_d:
			continue
		for d4 in DIRS:
			var n: Vector2i = p + d4
			if not seen.has(n) and n.x >= 0 and n.y >= 0 and n.x < W and n.y < H and walkable(n):
				seen[n] = dd + 1
				q.append(n)
	if cands.is_empty():
		return Vector2i(-1, -1)
	return cands[rng.randi() % cands.size()]


## Treasure hunters sometimes wander the wilds. Once you agree to help, their quarry waits here for you.
func _setup_hunt() -> void:
	if not DB.d.has("hunts") or not _outdoor():
		return
	var st := _hunt_state()
	if not st.is_empty() and str(st.get("map", "")) != mid:
		if not bool(st.get("accepted", false)):
			GS.flags.erase("hunt_active")       # they wandered on
			st = {}
		else:
			return
	if st.is_empty():
		var open := []
		for hid in DB.d.hunts:
			if not GS.flag("hunt_%s_done" % hid):
				open.append(hid)
		if open.is_empty() or rng.randf() > 0.35:
			return
		var hid: String = open[rng.randi() % open.size()]
		var p := _open_tile(start, 3, 7)
		if p.x < 0:
			return
		st = {"id": hid, "map": mid, "x": p.x, "y": p.y, "accepted": false, "gold": rng.randi_range(999, 9999)}
		GS.flags["hunt_active"] = st
	_spawn_hunters(st)
	if bool(st.get("accepted", false)):
		_spawn_quarry(st)


func _spawn_hunters(st: Dictionary) -> void:
	var hid := str(st.id)
	var h: Dictionary = DB.d.hunts[hid]
	var names: Array = h.seekers
	var first := Vector2i(int(st.x), int(st.y))
	var spots := [first, first + Vector2i(1, 0)]
	if not walkable(spots[1]):
		spots[1] = first + Vector2i(0, 1)
	for i in 2:
		var on := "flag:hunt_%s_on" % hid
		var script := [
			{"if": ["!" + on], "say": h.story,
			 "ask": {"q": h.ask, "yes": {"say": h.accept, "do": ["set:hunt_%s_on" % hid, "hunt_start:" + hid]}, "no": {"say": h.decline}}},
			{"if": [on], "say": h.accept},
		]
		var n := {"id": "hunt_%s_%d" % [hid, i], "name": str(names[i]), "script": script, "wander": true, "roam": 2,
				  "face": "down", "x": spots[i].x, "y": spots[i].y, "hunter": true, "cond": ["!flag:hunt_%s_done" % hid]}
		_spawn_npc(n)


func _spawn_quarry(st: Dictionary) -> void:
	var hid := str(st.id)
	var h: Dictionary = DB.d.hunts[hid]
	if not st.has("bx"):
		var p := _open_tile(Vector2i(int(st.x), int(st.y)), 12, 40)
		if p.x < 0:
			p = _open_tile(Vector2i(int(st.x), int(st.y)), 6, 40)
		st["bx"] = p.x
		st["by"] = p.y
		GS.flags["hunt_active"] = st
	var e := {"kind": "hunt", "id": str(h.boss), "x": int(st.bx), "y": int(st.by), "pre": h.pre, "post": h.post + h.thanks,
			  "flag": "hunt_%s_done" % hid, "need": [], "music": "boss", "win_do": _hunt_rewards(hid, int(st.gold)),
			  "cond": ["!flag:hunt_%s_done" % hid]}
	_spawn_boss(e)


## The hoard: a heap of gold, a legendary weapon, armor and charm from this world, and good medicine.
func _hunt_rewards(hid: String, gold: int) -> Array:
	var r: Dictionary = DB.d.get("hunt_reward", {})
	var out := ["set:hunt_%s_done" % hid, "clear:hunt_%s_on" % hid, "hunt_end:" + hid, "gold:%d" % gold]
	var wl: Dictionary = DB.d.world_gear_lists.get(world, {})
	var rr := RandomNumberGenerator.new()
	rr.seed = hash(hid + mid)
	for slot in [["weapons", int(r.get("weapons", 1))], ["armor", int(r.get("armor", 1))], ["acc", int(r.get("acc", 1))]]:
		var pool := []
		for gid in wl.get(slot[0], []):
			if DB.tier(gid) == "legendary":
				pool.append(gid)
		if pool.is_empty():
			for gid in wl.get(slot[0], []):
				if DB.tier(gid) == "rare":
					pool.append(gid)
		for k in int(slot[1]):
			if not pool.is_empty():
				out.append("give:gear:" + str(pool[rr.randi() % pool.size()]))
	for it in r.get("items", []):
		out.append("give:%s:%d" % [str(it[0]), int(it[1])])
	return out


# ------------------------------------------------------------------ light and shadow

const DARK_KINDS := ["cave", "dungeon", "sanctum"]


func _setup_lighting() -> void:
	light_layer = CanvasLayer.new()
	light_layer.layer = 7          # over the world, under weather and the HUD
	add_child(light_layer)
	dark_rect = ColorRect.new()
	glow_rect = ColorRect.new()
	for r in [glow_rect, dark_rect]:
		r.size = SCREEN
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		light_layer.add_child(r)
	var dm := ShaderMaterial.new()
	dm.shader = load("res://shaders/light_dark.gdshader")
	dark_rect.material = dm
	var gm := ShaderMaterial.new()
	gm.shader = load("res://shaders/light_glow.gdshader")
	glow_rect.material = gm
	# what kind of place is this?
	var kind := str(m.kind)
	var underground := kind in DARK_KINDS or str(mid).begins_with("goblin")
	if underground:
		ambient = Color(0.01, 0.01, 0.03, 0.76 if world != "fire" else 0.68)
		torch = 118.0
		vignette = 0.45
	elif kind == "interior":
		ambient = Color(0.06, 0.03, 0.02, 0.34)
		torch = 0.0
		vignette = 0.42
	else:
		ambient = Color(0.02, 0.02, 0.05, 0.0)
		vignette = 0.32
		torch = 0.0
	# every tile that gives off light
	static_lights.clear()
	for y in H:
		for x in W:
			var ch := tile_at(Vector2i(x, y))
			var c := Vector2(x * TS + TS * 0.5, y * TS + TS * 0.5)
			match ch:
				"t":
					static_lights.append({"p": c, "r": 120.0, "c": Color(1.0, 0.6, 0.25), "s": 1.0, "f": 0.18})
				"p":
					static_lights.append({"p": c, "r": 150.0, "c": Color(1.0, 0.55, 0.2), "s": 1.0, "f": 0.2})
				"Q":
					static_lights.append({"p": c, "r": 80.0, "c": Color(1.0, 0.75, 0.4), "s": 0.85, "f": 0.12})
				"l":
					static_lights.append({"p": c + Vector2(0, -10), "r": 96.0, "c": Color(1.0, 0.8, 0.45), "s": 0.8, "f": 0.05})
				"C":
					static_lights.append({"p": c, "r": 90.0, "c": Color(0.45, 0.85, 1.0), "s": 0.8, "f": 0.0})
				"O":
					static_lights.append({"p": c, "r": 120.0, "c": Color(0.7, 0.6, 1.0), "s": 0.9, "f": 0.08})
				"y":
					static_lights.append({"p": c + Vector2(0, 20), "r": 90.0, "c": Color(0.75, 0.85, 1.0), "s": 0.6, "f": 0.0})
				"~":
					# glowing lava in fire caves lights the walls around it
					if world == "fire" and underground and (x + y) % 2 == 0:
						static_lights.append({"p": c, "r": 70.0, "c": Color(1.0, 0.4, 0.1), "s": 0.55, "f": 0.1})
				"V":
					if underground:
						static_lights.append({"p": c, "r": 60.0, "c": Color(0.5, 0.8, 1.0), "s": 0.35, "f": 0.0})
	motes.clear()
	for i in 40:
		motes.append({"p": Vector2(rng.randf() * VIEW.x, rng.randf() * VIEW.y), "v": Vector2(rng.randf_range(-6, 6), rng.randf_range(-8, -2)),
					  "ph": rng.randf() * TAU})


## Outdoors, the weather and the world set how dark it is.
func _outdoor_ambient() -> Color:
	var k := str(GS.weather.get("kind", "")) if GS.weather_on else ""
	var a := 0.0
	var col := Color(0.02, 0.02, 0.06)
	match k:
		"storm":
			a = 0.36
		"rain", "gale":
			a = 0.22
		"cloudy", "snow":
			a = 0.12
		"ash":
			a = 0.2
			col = Color(0.08, 0.03, 0.02)
		"motes":
			a = 0.3
	if world == "void":
		a = maxf(a, 0.34)
		col = Color(0.04, 0.0, 0.08)
	if world == "nexus":
		a = maxf(a, 0.3)
		col = Color(0.03, 0.0, 0.06)
	return Color(col.r, col.g, col.b, a)


func _update_lighting(delta: float) -> void:
	if dark_rect == null:
		return
	light_layer.visible = not is_instance_valid(Main.inst.battle_node)
	var amb := ambient
	if str(m.kind) in ["town", "field", "hub"] or _outdoor():
		amb = _outdoor_ambient()
	var lights := PackedVector4Array()
	var cols := PackedVector4Array()
	var origin := world_node.position
	var me: Vector2 = player.position * ZOOM + origin
	var dark: float = amb.a
	# the hero's torch, with a lazy flicker
	if torch > 0.0:
		var fl := 1.0 + 0.05 * sin(anim_t * 9.0) + 0.03 * sin(anim_t * 23.0)
		lights.append(Vector4(me.x, me.y - 14.0, torch * ZOOM * fl, 1.0))
		cols.append(Vector4(1.0, 0.62, 0.3, 0.32))
	# the brightest nearby lights; lamps only matter when it's dark enough to need them
	var near := []
	for L in static_lights:
		var sp: Vector2 = L.p * ZOOM + origin
		var rr: float = L.r * ZOOM
		if sp.x < -rr or sp.y < -rr or sp.x > SCREEN.x + rr or sp.y > SCREEN.y + rr:
			continue
		near.append([sp.distance_squared_to(me), sp, rr, L])
	near.sort_custom(func(a, b): return a[0] < b[0])
	for e in near:
		if lights.size() >= 48:
			break
		var L: Dictionary = e[3]
		var f: float = 1.0 + float(L.f) * (sin(anim_t * 7.3 + L.p.x * 0.13) * 0.6 + sin(anim_t * 13.1 + L.p.y) * 0.4)
		var glow: float = 0.55 if dark > 0.25 else 0.25
		lights.append(Vector4(e[1].x, e[1].y, e[2] * f, float(L.s) * (1.0 if dark > 0.05 else 0.0)))
		cols.append(Vector4(L.c.r, L.c.g, L.c.b, glow * float(L.s)))
	var n := lights.size()
	while lights.size() < 48:
		lights.append(Vector4.ZERO)
		cols.append(Vector4.ZERO)
	var dm: ShaderMaterial = dark_rect.material
	dm.set_shader_parameter("ambient", amb)
	dm.set_shader_parameter("vignette", vignette)
	dm.set_shader_parameter("count", n)
	dm.set_shader_parameter("lights", lights)
	var gm: ShaderMaterial = glow_rect.material
	gm.set_shader_parameter("count", n)
	gm.set_shader_parameter("lights", lights)
	gm.set_shader_parameter("colors", cols)
	# dust drifting in the air
	for mo in motes:
		mo.p += mo.v * delta
		mo.ph += delta
		if mo.p.y < -4:
			mo.p = Vector2(rng.randf() * VIEW.x, VIEW.y + 4)
		mo.p.x = fposmod(mo.p.x, VIEW.x)


## Drop shadows: the sun hangs to the upper left, so solid things shade the ground below and to the right.
func _draw_shadows(ci: Node2D, x0: int, y0: int, x1: int, y1: int) -> void:
	if str(m.kind) in DARK_KINDS:
		return
	var sh := Color(0.0, 0.0, 0.02, 0.26)
	var soft := Color(0.0, 0.0, 0.02, 0.13)
	var tall := "RHWd"
	for y in range(max(0, y0), min(H, y1)):
		for x in range(max(0, x0), min(W, x1)):
			var ch := tile_at(Vector2i(x, y))
			if ch in tall or ch == "#" or ch == "K" or ch == "^" or ch == "x" or ch == "X" or ch == "k" or ch == "S" or ch == "A":
				continue
			var o := Vector2(x * TS, y * TS)
			var above := tile_at(Vector2i(x, y - 1))
			var left := tile_at(Vector2i(x - 1, y))
			var al := tile_at(Vector2i(x - 1, y - 1))
			# under a building, wall or cliff: a band of shade at the foot
			if above in tall or above == "K" or (above == "#" and m.kind != "interior"):
				ci.draw_rect(Rect2(o, Vector2(TS, 9)), sh)
				ci.draw_rect(Rect2(o + Vector2(0, 9), Vector2(TS, 6)), soft)
			elif m.kind == "interior" and above == "#":
				ci.draw_rect(Rect2(o, Vector2(TS, 7)), Color(0, 0, 0, 0.22))
			# to the right of something tall: a long sideways shadow
			if left in tall or left == "K" or (left == "#" and m.kind != "interior"):
				ci.draw_rect(Rect2(o, Vector2(8, TS)), sh)
				ci.draw_rect(Rect2(o + Vector2(8, 0), Vector2(6, TS)), soft)
			elif al in tall and not (above in tall):
				ci.draw_rect(Rect2(o, Vector2(8, 10)), soft)
			# rocks, crates, statues and furniture: a little pool of shade
			if left in "^xXSAkG" and left != "":
				ci.draw_rect(Rect2(o + Vector2(0, TS - 12), Vector2(10, 10)), soft)


## Atmosphere over everything: sunbeams outdoors on clear days, dust in the torchlight underground.
func _draw_atmosphere(ci: Node2D) -> void:
	var kind := str(m.kind)
	var k := str(GS.weather.get("kind", "")) if GS.weather_on else ""
	var cam_px := cam
	if kind in ["field", "town"] and k in ["sunny", "breeze", ""] and world not in ["void"]:
		# slow diagonal shafts of light drifting across the ground
		for i in 4:
			var bx := fposmod(i * 260.0 + anim_t * 6.0 - cam_px.x * 0.25, VIEW.x + 300.0) - 150.0 + cam_px.x
			var a := 0.065 + 0.025 * sin(anim_t * 0.4 + i * 1.7)
			var top := cam_px.y - 20.0
			var pts := PackedVector2Array([Vector2(bx, top), Vector2(bx + 46, top), Vector2(bx - 140, top + VIEW.y + 40), Vector2(bx - 186, top + VIEW.y + 40)])
			ci.draw_colored_polygon(pts, Color(1.0, 0.95, 0.75, a))
	var underground := kind in DARK_KINDS or str(mid).begins_with("goblin")
	if underground or kind == "interior":
		for mo in motes:
			var p: Vector2 = cam_px + mo.p
			var d := p.distance_to(player.position + Vector2(0, -14))
			var lit := clampf(1.0 - d / 120.0, 0.0, 1.0)
			if lit > 0.02:
				var tw := 0.5 + 0.5 * sin(mo.ph * 2.0)
				ci.draw_rect(Rect2(p.round(), Vector2(1, 1)), Color(1.0, 0.85, 0.6, lit * (0.4 + 0.4 * tw)))


func _spawn_boss(e: Dictionary) -> Boss:
	var b := Boss.new()
	b.data = e
	var path := "res://assets/enemies/map_%s.png" % e.id
	if e.kind == "seal":
		path = "res://assets/enemies/%s.png" % e.sprite
	b.tex = Art.tex(path)
	b.position = _tile_px(Vector2i(int(e.x), int(e.y)))
	ents.add_child(b)
	bosses.append(b)
	return b


func _tile_px(p: Vector2i) -> Vector2:
	return Vector2(p.x * TS + TS * 0.5, p.y * TS + TS - 2)


func tile_at(p: Vector2i) -> String:
	if p.x < 0 or p.y < 0 or p.x >= W or p.y >= H:
		return " "
	return tiles[p.y][p.x]


func _occupied(p: Vector2i) -> bool:
	for n in npcs:
		if n.actor.visible and n.pos == p:
			return true
	for c in chests:
		if Vector2i(int(c.data.x), int(c.data.y)) == p:
			return true
	for b in bosses:
		if b.visible and Vector2i(int(b.data.x), int(b.data.y)) == p:
			return true
	return false


func walkable(p: Vector2i) -> bool:
	var ch := tile_at(p)
	if BLOCK.find(ch) >= 0:
		return false
	return not _occupied(p)


func _refresh_visibility() -> void:
	for n in npcs:
		n.actor.visible = GS.check(n.data.get("cond", []))
	for b in bosses:
		b.visible = GS.check(b.data.get("cond", []))
		if b.data.kind == "seal":
			b.visible = true


func _reset_encounter() -> void:
	encounter_steps = rng.randi_range(18, 34) if m.kind == "field" else rng.randi_range(14, 28)


# ------------------------------------------------------------------ update

func _process(delta: float) -> void:
	anim_t += delta
	if banner_t > 0:
		banner_t -= delta
	_update_npcs(delta)
	_update_camera()
	_update_lighting(delta)
	if busy or Main.inst.busy or dialog.active or menu.active or moving:
		return
	if Inp.back():
		_open_menu()
		return
	if Inp.map_key():
		_open_full_map()
		return
	if Inp.ok():
		_interact()
		return
	# eight-way movement: two directions together walk diagonally
	var dx := (1 if Inp.held("right") else 0) - (1 if Inp.held("left") else 0)
	var dy := (1 if Inp.held("down") else 0) - (1 if Inp.held("up") else 0)
	if dx != 0 or dy != 0:
		_try_move(Vector2i(dx, dy))
	else:
		player.set_frame(face * WF)


const WALK_T := 0.2       # seconds per tile, walking
const RUN_T := 0.1        # seconds per tile, running


func _dir_index(v: Vector2i) -> int:
	return DIRS.find(v)


func _running() -> bool:
	var held := Inp.held("run")
	return not held if GS.settings.get("auto_run", false) else held


## Wandering folk step out of your way. If there's no room to step aside, you squeeze past each other.
func _make_way(p: Vector2i) -> void:
	for n in npcs:
		if n.pos != p or not n.actor.visible or not n.data.get("wander", false):
			continue
		if n.get("moving", false) or n.get("talking", false) or n.job != "":
			return
		var dir := p - ppos
		var side := Vector2i(dir.y, dir.x) if dir.x == 0 or dir.y == 0 else Vector2i(dir.x, 0)
		var other := -side if dir.x == 0 or dir.y == 0 else Vector2i(0, dir.y)
		var cands := [p + side, p + other, p + dir, p + side + dir, p + other + dir]
		if rng.randf() < 0.5:
			cands = [p + other, p + side, p + dir, p + other + dir, p + side + dir]
		n.wander_t = rng.randf_range(2.5, 4.0)       # and don't wander straight back
		for c in cands:
			if c != ppos and walkable(c):
				var d := DIRS.find(Vector2i(signi(c.x - p.x), 0) if c.x != p.x else Vector2i(0, signi(c.y - p.y)))
				_walk_npc(n, max(0, d), c, 0.16)
				return
		# boxed in: swap places
		var back := DIRS.find(Vector2i(signi(ppos.x - p.x), signi(ppos.y - p.y)))
		_walk_npc(n, max(0, back), ppos, 0.2 if not _running() else 0.1)
		return


func _try_move(step: Vector2i) -> void:
	_make_way(ppos + step)
	if step.x != 0 and step.y != 0:
		_make_way(ppos + Vector2i(step.x, 0))
		_make_way(ppos + Vector2i(0, step.y))
	# face: keep the current facing if it's part of the move, else face sideways on diagonals
	if step.x != 0 and step.y != 0:
		if face != _dir_index(Vector2i(step.x, 0)) and face != _dir_index(Vector2i(0, step.y)):
			face = _dir_index(Vector2i(step.x, 0))
	else:
		face = _dir_index(step)
	var target: Vector2i = ppos + step
	if step.x != 0 and step.y != 0:
		var hx := ppos + Vector2i(step.x, 0)
		var hy := ppos + Vector2i(0, step.y)
		# no squeezing between two corners: a diagonal needs both sides open, otherwise slide along the wall
		if not (walkable(target) and walkable(hx) and walkable(hy)):
			var first := hx if face == _dir_index(Vector2i(step.x, 0)) else hy
			var second := hy if first == hx else hx
			if walkable(first):
				target = first
			elif walkable(second):
				target = second
			else:
				player.set_frame(face * WF)
				return
			face = _dir_index(target - ppos)
	elif not walkable(target):
		player.set_frame(face * WF)
		return
	moving = true
	var run := _running()
	var dur := RUN_T if run else WALK_T
	if (target - ppos).x != 0 and (target - ppos).y != 0:
		dur *= 1.41      # same speed along a diagonal
	var from := player.position
	var to := _tile_px(target)
	var t := 0.0
	var step_frame := GS.steps % 2
	if run and _on_screen(from):
		# kick up a little dust
		var gc := Color(0.55, 0.45, 0.35, 0.7) if world != "water" else Color(0.85, 0.8, 0.6, 0.7)
		for i in 3:
			_fx(from + Vector2(rng.randf_range(-5, 5), -1), Vector2(-(to - from).x * rng.randf_range(0.6, 1.4), rng.randf_range(-22, -8)), 0.35, gc, 2.0)
	while t < dur:
		await get_tree().process_frame
		t += get_process_delta_time()
		player.position = from.lerp(to, clampf(t / dur, 0.0, 1.0)).round()
		# eight-frame walk cycle, four frames per tile
		player.set_frame(face * WF + 1 + (step_frame * 4 + int(clampf(t / dur, 0.0, 0.99) * 4.0)) % 8)
		_push_trail()
	player.position = to
	ppos = target
	GS.steps += 1
	GS.location = {"map": mid, "x": ppos.x, "y": ppos.y, "face": face}
	moving = false
	await _after_step()


func _after_step() -> void:
	for e in m.exits:
		if int(e.x) == ppos.x and int(e.y) == ppos.y:
			Audio.sfx("portal" if tile_at(ppos) == "O" else "door")
			GS.save_game(0)  # autosave
			Main.inst.change_map(e.to, int(e.tx), int(e.ty), _face_from(str(e.face)))
			busy = true
			return
	if m.encounters and m.kind in ["field", "cave", "dungeon"]:
		encounter_steps -= 1
		if encounter_steps <= 0:
			_reset_encounter()
			await _random_battle()


func _face_from(s: String) -> int:
	match s:
		"down":
			return 0
		"left":
			return 1
		"right":
			return 2
		"up":
			return 3
	return 0


func _random_battle() -> void:
	busy = true
	var area: String = m.kind
	var enemies := DB.random_group(world, area, GS.avg_level(), rng, m.get("habitat", []))
	# now and then, figures in white step out of nowhere
	if DB.d.uniques.has("blessed_warden") and rng.randf() < minf(0.12, 0.04 + 0.015 * GS.hearts()):
		enemies = []
		var kinds := ["blessed_warden", "blessed_lancer", "blessed_seraph"]
		for i in rng.randi_range(1, 3):
			enemies.append(DB.make_enemy(kinds[rng.randi() % kinds.size()], GS.avg_level(), world))
	await Main.inst.battle(enemies, {"bg": m.bg, "music": "battle", "flee": true})
	busy = false


func _update_npcs(delta: float) -> void:
	_update_work_fx(delta)
	for n in npcs:
		if not n.actor.visible:
			continue
		if n.get("talking", false):
			continue
		if n.job != "":
			_work_step(n, delta)
			continue
		if not n.data.get("wander", false):
			# folk who stand about still glance around now and then
			n.look_t -= delta
			if n.look_t <= 0.0 and not dialog.active and not busy:
				if n.face == n.home_face:
					n.face = [1, 2, 0, 3][rng.randi() % 4] if rng.randf() < 0.85 else n.home_face
					n.look_t = rng.randf_range(1.2, 2.4)
				else:
					n.face = n.home_face
					n.look_t = rng.randf_range(4.0, 10.0)
				n.actor.set_frame(n.face * WF)
			continue
		if dialog.active or busy:
			continue
		n.wander_t -= delta
		if n.wander_t > 0 or n.get("moving", false):
			continue
		var roam: float = float(n.data.get("roam", 2.5))
		# strollers keep walking a few steps in one direction before pausing
		n.wander_t = rng.randf_range(0.05, 0.25) if roam > 3.0 and rng.randf() < 0.7 else rng.randf_range(1.5, 4.0)
		var d: int = n.get("wdir", rng.randi() % 4)
		if rng.randf() < 0.35:
			d = rng.randi() % 4
		n.wdir = d
		var tgt: Vector2i = n.pos + DIRS[d]
		if (tgt - n.home).length() > roam or not walkable(tgt) or tgt == ppos:
			n.actor.set_frame(d * WF)
			n.wdir = rng.randi() % 4
			n.wander_t = rng.randf_range(0.6, 2.0)
			continue
		_walk_npc(n, d, tgt)


# ------------------------------------------------------------------ townsfolk at work

func _npc_to_work(n: Dictionary) -> void:
	n.actor.setup("res://assets/chars/npc_%s_job.png" % n.data.id, Vector2(128, 120), int(JOB_FRAMES[n.job]))
	n.seq = _job_cycle(n.job)
	n.si = 0
	n.ft = 0.0
	n.actor.set_frame(int(n.seq[0]))


func _npc_to_walk_sheet(n: Dictionary) -> void:
	n.actor.setup("res://assets/chars/npc_%s.png" % n.data.id, Vector2(64, 64), WF)


## One loop of a job's animation, as frame indices into its work sheet (holds are repeated frames).
func _job_cycle(job: String) -> Array:
	var c: Array = []
	match job:
		"hoe", "dig":
			c = [0, 1, 2, 3, 4, 5, 6, 7, 7]
			for i in rng.randi_range(2, 6):
				c.push_front(0)
		"water":
			c = [0, 1, 2, 3, 4]
			for i in rng.randi_range(8, 14):
				c.append(4)
			c += [5, 6, 7, 0, 0, 0, 0, 0, 0]
		"mine", "chop", "smith":
			c = [5, 5, 4, 4, 3, 1, 0, 0, 0, 0]
			if rng.randf() < 0.25:
				for i in rng.randi_range(6, 14):
					c.append(0)        # catch a breath
		"fish":
			c = [0, 1, 2, 3, 4, 5]
			for i in rng.randi_range(24, 60):
				c.append(6)            # line in the water, waiting
			c += [9, 10, 9, 10, 11, 12, 0, 0, 0, 0]
		"seance", "pray":
			c = [0, 1, 2, 3, 4, 5, 6]
			for i in rng.randi_range(10, 22):
				c.append(6 if i % 4 < 2 else 5)
			c += [4, 3, 2, 1, 0, 0, 0, 0, 0, 0]
		_:
			c = [0]
	return c


func _work_step(n: Dictionary, delta: float) -> void:
	n.ft += delta
	var step: float = 1.0 / float(JOB_FPS.get(n.job, 8.0))
	while n.ft >= step:
		n.ft -= step
		n.si += 1
		if n.si >= n.seq.size():
			n.seq = _job_cycle(n.job)
			n.si = 0
		var f: int = int(n.seq[n.si])
		n.actor.set_frame(f)
		_work_event(n, f)


func _work_dir(n: Dictionary) -> Vector2:
	return Vector2(DIRS[int(n.home_face)])


## Sparks, chips and splashes at the moment a tool lands.
func _work_event(n: Dictionary, f: int) -> void:
	if not _on_screen(n.actor.position):
		return
	var d := _work_dir(n)
	var hit: Vector2 = n.actor.position + (d * 22.0 + Vector2(0, -8)) * PEOPLE
	match n.job:
		"smith":
			if f == 3:
				for i in 7:
					_fx(hit + Vector2(0, -6), Vector2(rng.randf_range(-60, 60), rng.randf_range(-90, -30)), 0.45, Color(1.0, rng.randf_range(0.55, 0.9), 0.2), 1.5)
				if (n.actor.position - player.position).length() < 200:
					Audio.sfx("sword_clash", -26.0, rng.randf_range(1.5, 1.8), 0.0)
		"mine":
			if f == 3:
				var rc := Color(0.55, 0.5, 0.48) if world != "fire" else Color(0.45, 0.32, 0.28)
				for i in 5:
					_fx(hit, Vector2(rng.randf_range(-50, 50) - d.x * 30, rng.randf_range(-70, -20)), 0.5, rc, 2.0)
				if world == "fire" and rng.randf() < 0.5:
					_fx(hit, Vector2(rng.randf_range(-20, 20), -60), 0.6, Color(1, 0.5, 0.1), 1.5)
		"chop":
			if f == 3:
				for i in 4:
					_fx(hit, Vector2(rng.randf_range(-40, 40), rng.randf_range(-70, -30)), 0.55, Color(0.75, 0.55, 0.3), 2.0)
		"hoe", "dig":
			if f == 5:
				for i in 4:
					_fx(hit + Vector2(0, 8), Vector2(rng.randf_range(-35, 35), rng.randf_range(-45, -15)), 0.4, Color(0.36, 0.24, 0.14), 2.0)
		"water":
			if f == 4:
				for i in 2:
					_fx(hit + Vector2(d.x * 6, 6), Vector2(rng.randf_range(-8, 8), rng.randf_range(10, 40)), 0.35, Color(0.6, 0.8, 1.0, 0.9), 1.5)
		"fish":
			if f == 6 and rng.randf() < 0.06:
				n.ripple = 1.0
		"seance":
			if f >= 5 and rng.randf() < 0.5:
				var c: Vector2 = n.actor.position + d * TS + Vector2(0, -10)
				_fx(c + Vector2(rng.randf_range(-12, 12), 0), Vector2(rng.randf_range(-8, 8), rng.randf_range(-30, -12)), 1.4, Color(0.7, 0.45, 1.0, 0.8), 2.0)
		"pray":
			if f >= 5 and rng.randf() < 0.3:
				_fx(n.actor.position + Vector2(rng.randf_range(-10, 10), -32), Vector2(0, rng.randf_range(-18, -8)), 1.2, Color(1, 0.95, 0.7, 0.8), 1.5)


func _fx(p: Vector2, v: Vector2, life: float, col: Color, size: float) -> void:
	if work_fx.size() < 160:
		work_fx.append({"p": p, "v": v, "t": 0.0, "life": life, "col": col, "size": size})


func _update_work_fx(delta: float) -> void:
	for i in range(work_fx.size() - 1, -1, -1):
		var e: Dictionary = work_fx[i]
		e.t += delta
		if e.t >= e.life:
			work_fx.remove_at(i)
			continue
		e.p += e.v * delta
		if e.col.b < 0.9 or e.col.r > 0.9:
			e.v.y += 220.0 * delta       # sparks and chips fall; wisps float
	for n in npcs:
		if n.has("ripple"):
			n.ripple = max(0.0, n.ripple - delta * 0.8)


func _on_screen(p: Vector2) -> bool:
	return Rect2(cam - Vector2(64, 64), VIEW + Vector2(128, 128)).has_point(p)


## Under the characters: the seance ring and the fishing lines' bobbers.
func _draw_work_under(ci: Node2D) -> void:
	var rings := {}
	for n in npcs:
		if n.job == "" or not n.actor.visible:
			continue
		if n.job == "seance":
			var c: Vector2i = n.pos + DIRS[int(n.home_face)]
			rings[c] = true
		elif n.job == "fish":
			var f: int = n.actor.frame
			if f == 6:
				var d := _work_dir(n)
				var b: Vector2 = n.actor.position + d * 40.0 * PEOPLE + Vector2(0, -2 + sin(anim_t * 3.0 + n.home.x) * 1.0)
				var rp: float = n.get("ripple", 0.0)
				ci.draw_arc(b, 4.0 + (1.0 - rp) * 4.0, 0, TAU, 12, Color(0.85, 0.95, 1.0, 0.25 + rp * 0.4), 1.0)
				ci.draw_rect(Rect2(b + Vector2(-1, -3 - rp * 2.0), Vector2(2, 2)), Color(0.95, 0.2, 0.15))
				ci.draw_rect(Rect2(b + Vector2(-1, -1 - rp * 2.0), Vector2(2, 1)), Color(0.95, 0.95, 0.9))
	for c in rings:
		var p := Vector2(c.x * TS + TS * 0.5, c.y * TS + TS * 0.5 + 4)
		var pulse := 0.5 + 0.5 * sin(anim_t * 2.2)
		ci.draw_circle(p, 34.0, Color(0.35, 0.1, 0.55, 0.12 + pulse * 0.08))
		ci.draw_arc(p, 30.0, 0, TAU, 32, Color(0.75, 0.45, 1.0, 0.35 + pulse * 0.3), 1.5)
		ci.draw_arc(p, 22.0, anim_t * 0.6, anim_t * 0.6 + TAU * 0.8, 24, Color(0.75, 0.45, 1.0, 0.25), 1.0)
		for k in 5:
			var ang := anim_t * 0.6 + k * TAU / 5.0
			ci.draw_rect(Rect2(p + Vector2(cos(ang), sin(ang) * 0.6) * 30.0 - Vector2(1, 1), Vector2(2, 2)), Color(0.9, 0.7, 1.0, 0.8))


## Over the characters: sparks, chips, drops, wisps.
func _draw_work_over(ci: Node2D) -> void:
	for e in work_fx:
		var a: float = 1.0 - e.t / e.life
		var c: Color = e.col
		ci.draw_rect(Rect2(e.p.round(), Vector2(e.size, e.size)), Color(c.r, c.g, c.b, c.a * a))


## Work-site props drawn in code: tilled soil, an anvil, a chopping stump, gravestones.
func _draw_prop(ci: Node2D, ch: String, x: int, y: int) -> void:
	var o := Vector2(x * TS, y * TS)
	var hsh := (x * 7349 + y * 1931) % 97
	var ink := Color(0.06, 0.04, 0.04)
	match ch:
		"s":
			ci.draw_rect(Rect2(o, Vector2(TS, TS)), Color(0.27, 0.17, 0.1))
			for r in 4:
				var yy := o.y + 4 + r * 8
				ci.draw_rect(Rect2(o.x, yy, TS, 3), Color(0.19, 0.11, 0.06))
				ci.draw_rect(Rect2(o.x, yy + 3, TS, 1), Color(0.36, 0.24, 0.14))
				for k in 3:
					var sx := o.x + 4 + k * 11 + (r * 5 + hsh) % 4
					var sc := Color(0.35, 0.6, 0.2) if world != "spirit" else Color(0.85, 0.85, 0.7)
					if world == "void":
						sc = Color(0.45, 0.3, 0.55)
					ci.draw_rect(Rect2(sx, yy - 2, 1, 3), sc.darkened(0.2))
					ci.draw_rect(Rect2(sx - 1, yy - 3, 3, 1), sc)
			if tile_at(Vector2i(x, y - 1)) != "s":
				ci.draw_rect(Rect2(o, Vector2(TS, 1)), Color(0.14, 0.08, 0.04))
		"A":
			var hot := 0.6 + 0.4 * sin(anim_t * 4.0)
			ci.draw_rect(Rect2(o + Vector2(11, 20), Vector2(10, 10)), ink)
			ci.draw_rect(Rect2(o + Vector2(12, 20), Vector2(8, 9)), Color(0.26, 0.25, 0.28))
			ci.draw_rect(Rect2(o + Vector2(7, 28), Vector2(18, 3)), ink)
			ci.draw_rect(Rect2(o + Vector2(8, 28), Vector2(16, 2)), Color(0.3, 0.29, 0.32))
			ci.draw_colored_polygon(PackedVector2Array([o + Vector2(2, 13), o + Vector2(27, 13), o + Vector2(27, 20), o + Vector2(9, 20)]), ink)
			ci.draw_colored_polygon(PackedVector2Array([o + Vector2(4, 14), o + Vector2(26, 14), o + Vector2(26, 19), o + Vector2(10, 19)]), Color(0.38, 0.37, 0.41))
			ci.draw_rect(Rect2(o + Vector2(6, 14), Vector2(20, 1)), Color(0.62, 0.6, 0.66))
			ci.draw_rect(Rect2(o + Vector2(12, 12), Vector2(10, 2)), Color(1.0, 0.35 + 0.25 * hot, 0.1))
			ci.draw_circle(o + Vector2(17, 12), 7.0, Color(1, 0.4, 0.1, 0.12 * hot))
		"G":
			ci.draw_circle(o + Vector2(16, 22), 11.0, ink)
			ci.draw_rect(Rect2(o + Vector2(5, 18), Vector2(22, 10)), ink)
			ci.draw_rect(Rect2(o + Vector2(6, 18), Vector2(20, 9)), Color(0.36, 0.22, 0.12))
			ci.draw_circle(o + Vector2(16, 18), 10.0, Color(0.62, 0.45, 0.26))
			ci.draw_arc(o + Vector2(16, 18), 6.0, 0, TAU, 12, Color(0.45, 0.3, 0.16), 1.0)
			ci.draw_arc(o + Vector2(16, 18), 3.0, 0, TAU, 8, Color(0.45, 0.3, 0.16), 1.0)
			for k in 3:
				ci.draw_rect(Rect2(o + Vector2(3 + k * 9 + hsh % 3, 29), Vector2(3, 2)), Color(0.7, 0.52, 0.3))
		"M":
			ci.draw_rect(Rect2(o + Vector2(6, 24), Vector2(20, 6)), Color(0.22, 0.15, 0.1))
			ci.draw_rect(Rect2(o + Vector2(9, 6), Vector2(14, 20)), ink)
			ci.draw_circle(o + Vector2(16, 9), 7.0, ink)
			ci.draw_rect(Rect2(o + Vector2(10, 8), Vector2(12, 17)), Color(0.42, 0.42, 0.46))
			ci.draw_circle(o + Vector2(16, 9), 6.0, Color(0.42, 0.42, 0.46))
			ci.draw_rect(Rect2(o + Vector2(10, 8), Vector2(2, 17)), Color(0.55, 0.55, 0.6))
			ci.draw_rect(Rect2(o + Vector2(15, 9), Vector2(2, 9)), Color(0.24, 0.24, 0.27))
			ci.draw_rect(Rect2(o + Vector2(12, 12), Vector2(8, 2)), Color(0.24, 0.24, 0.27))
			if hsh % 3 == 0:
				ci.draw_rect(Rect2(o + Vector2(19, 18), Vector2(3, 7)), Color(0.25, 0.35, 0.2, 0.8))


func _walk_npc(n: Dictionary, d: int, tgt: Vector2i, dur := 0.3) -> void:
	n.moving = true
	var occupied_before: Vector2i = n.pos
	n.pos = tgt  # reserve the tile
	var from: Vector2 = _tile_px(occupied_before)
	var to: Vector2 = _tile_px(tgt)
	var t := 0.0
	while t < dur:
		await get_tree().process_frame
		if not is_instance_valid(n.actor):
			return
		t += get_process_delta_time()
		n.actor.position = from.lerp(to, clampf(t / dur, 0.0, 1.0)).round()
		n.actor.set_frame(d * WF + 1 + int(clampf(t / dur, 0.0, 0.99) * 8.0))
	n.actor.position = to
	n.actor.set_frame(d * WF)
	n.moving = false


func _update_camera(_snap := false) -> void:
	var target := player.position - Vector2(0, 16) - VIEW / 2.0
	var mapsz := Vector2(W * TS, H * TS)
	for i in 2:
		if mapsz[i] <= VIEW[i]:
			target[i] = -(VIEW[i] - mapsz[i]) / 2.0
		else:
			target[i] = clampf(target[i], 0.0, mapsz[i] - VIEW[i])
	cam = target
	world_node.position = (-cam * ZOOM).round()


# ------------------------------------------------------------------ drawing

func _tile_name(x: int, y: int) -> String:
	var ch := tile_at(Vector2i(x, y))
	var hsh := (x * 7349 + y * 1931) % 97
	var fr3 := int(anim_t * 3.0) % 3
	match ch:
		".":
			return "ground%d" % (hsh % 4)
		",":
			return "path%d" % (hsh % 2)
		"\"":
			return "grass%d" % (hsh % 2)
		"F":
			return "flower%d" % (hsh % 2)
		"T":
			return "tree%d" % (hsh % 2)
		"^":
			return "rock%d" % (hsh % 2)
		"~":
			if tile_at(Vector2i(x, y - 1)) == "V":
				return "splash%d" % fr3
			var edge := tile_at(Vector2i(x, y - 1)) not in ["~", "=", "V"]
			return ("liquid_edge%d" if edge else "liquid%d") % fr3
		"=":
			return "bridge"
		"#":
			if m.kind == "interior":
				return "iwall_face%d" % (1 if hsh % 5 == 0 else 0) if y == 1 else "iwall_top"
			return "wall_top" if tile_at(Vector2i(x, y + 1)) in ["#", "t", " "] else "wall_face%d" % (1 if hsh % 5 == 0 else 0)
		"_":
			if m.kind == "interior":
				return "ifloor%d" % (hsh % 3)
			return "keeper_floor" if m.kind == "town" else "floor%d" % (hsh % 3)
		"K":
			return "cliff_top" if tile_at(Vector2i(x, y + 1)) in ["K", " "] else "cliff_face%d" % (1 if hsh % 4 == 0 else 0)
		"Y":
			return "cliff_stairs"
		"V":
			return "fall%d" % fr3
		"U":
			return "ledge"
		"Z":
			return "hidden_door"
		"B":
			return "bed_bot" if tile_at(Vector2i(x, y - 1)) == "B" else "bed_top"
		"k":
			return "bookshelf"
		"u":
			return "table"
		"o":
			return "stool"
		"q":
			return "potion_shelf"
		"x":
			return "barrel"
		"X":
			return "crate"
		"p":
			return "fireplace%d" % (int(anim_t * 5.0) % 2)
		"j":
			return "weapon_rack"
		"J":
			return "armor_stand"
		"z":
			return "plant"
		"g":
			return "bottle_shelf"
		"e":
			return "keg"
		"m":
			return "mat"
		"v":
			return "stairs_down"
		"i":
			return "painting"
		"y":
			return "window_in"
		"r":
			return "rug"
		"Q":
			return "candle%d" % (int(anim_t * 6.0 + hsh) % 2)
		"R":
			if tile_at(Vector2i(x, y - 1)) != "R":
				return "roof_top"
			return "roof_bot" if tile_at(Vector2i(x, y + 1)) != "R" else "roof_mid"
		"H":
			return "hwall"
		"W":
			return "window"
		"d":
			return "door"
		"a":
			return "awning"
		"c":
			return "icounter" if m.kind == "interior" else "counter"
		"f":
			return "fence"
		"l":
			return "lamp%d" % (int(anim_t * 2.0 + hsh) % 2)
		"n":
			return "bench"
		"w":
			var fx := 0 if tile_at(Vector2i(x - 1, y)) != "w" else 1
			var fy := 0 if tile_at(Vector2i(x, y - 1)) != "w" else 1
			return "feat_%s%s%d" % ["t" if fy == 0 else "b", "l" if fx == 0 else "r", int(anim_t * 4.0) % 2]
		"L":
			return "landmark_bot"
		"P":
			return "pillar"
		"t":
			return "torch%d" % (int(anim_t * 8.0 + hsh) % 3)
		"b":
			return "bones"
		"C":
			return "crystal%d" % (1 if int(anim_t * 2.0 + hsh) % 4 == 0 else 0)
		"S":
			return "statue"
		"O":
			return "portal%d" % (int(anim_t * 8.0) % 4)
		"E":
			return "cave_mouth"
		">":
			return "stairs"
	return "outside"


var tex_liquid: Texture2D
var tex_liquid2: Texture2D
var tex_path: Texture2D
var tex_trees: Texture2D


func _load_terrain() -> void:
	tex_liquid = Art.tex("res://assets/tiles/%s_liquid.png" % world)
	tex_liquid2 = Art.tex("res://assets/tiles/%s_liquid2.png" % world)
	tex_path = Art.tex("res://assets/tiles/%s_path.png" % world)
	tex_trees = Art.tex("res://assets/tiles/%s_trees.png" % world)


## LPC terrain blocks (3x6 tiles) drawn in quarter-tiles, so shores and paths of any shape get smooth edges.
const _Q := {  # quadrant -> [inner corner tile, vertical edge tile, horizontal edge tile, outer corner tile]  (tile coords in the block)
	"nw": [Vector2i(2, 1), Vector2i(0, 3), Vector2i(1, 2), Vector2i(0, 2)],
	"ne": [Vector2i(1, 1), Vector2i(2, 3), Vector2i(1, 2), Vector2i(2, 2)],
	"sw": [Vector2i(2, 0), Vector2i(0, 3), Vector2i(1, 4), Vector2i(0, 4)],
	"se": [Vector2i(1, 0), Vector2i(2, 3), Vector2i(1, 4), Vector2i(2, 4)],
}


func _same(x: int, y: int, set_chars: String) -> bool:
	var c := tile_at(Vector2i(x, y))
	return c == " " or set_chars.find(c) >= 0


func _autotile(ci: Node2D, tex: Texture2D, x: int, y: int, set_chars: String) -> void:
	if tex == null:
		return
	var h := 16
	for q in ["nw", "ne", "sw", "se"]:
		var dx := -1 if q.ends_with("w") else 1
		var dy := -1 if q.begins_with("n") else 1
		var hz := _same(x + dx, y, set_chars)
		var vt := _same(x, y + dy, set_chars)
		var dg := _same(x + dx, y + dy, set_chars)
		var piece: Vector2i
		var pick: Array = _Q[q]
		if hz and vt:
			piece = pick[0] if not dg else Vector2i(1 + ((x * 7 + y * 3) % 2) * 0, 3)
			if dg:
				# plain center: use the varied fill tiles on the bottom row
				piece = Vector2i((x * 7 + y * 13) % 3, 5)
		elif vt:
			piece = pick[1]
		elif hz:
			piece = pick[2]
		else:
			piece = pick[3]
		var qx := 0 if q.ends_with("w") else h
		var qy := 0 if q.begins_with("n") else h
		ci.draw_texture_rect_region(tex, Rect2(x * TS + qx, y * TS + qy, h, h), Rect2(piece.x * TS + qx, piece.y * TS + qy, h, h))


func _draw_tiles(ci: Node2D) -> void:
	var x0 := int(floor(cam.x / TS)) - 1
	var y0 := int(floor(cam.y / TS)) - 1
	var x1 := x0 + int(VIEW.x / TS) + 3
	var y1 := y0 + int(VIEW.y / TS) + 6
	var indoor: bool = m.kind in ["cave", "dungeon", "sanctum"]
	var base_name := "floor0" if indoor else "ground0"
	if m.kind == "interior":
		base_name = "ifloor0"
	var wall_base := Art.tile_rect("iwall_face0")
	var liquid := tex_liquid if int(anim_t * 1.5) % 2 == 0 or tex_liquid2 == null else tex_liquid2
	for y in range(max(0, y0), min(H, y1)):
		for x in range(max(0, x0), min(W, x1)):
			var dest := Rect2(x * TS, y * TS, TS, TS)
			var ch := tile_at(Vector2i(x, y))
			if ch == " ":
				ci.draw_rect(dest, Color.BLACK)
				continue
			var hsh := (x * 7349 + y * 1931) % 97
			var base := Art.tile_rect(base_name if indoor or m.kind == "interior" else "ground%d" % (hsh % 4))
			ci.draw_texture_rect_region(ts, dest, wall_base if (m.kind == "interior" and y == 1) else base)
			if ch == "~" and liquid:
				_autotile(ci, liquid, x, y, "~=V")
				continue
			if ch == "," and not indoor and m.kind != "interior" and tex_path:
				_autotile(ci, tex_path, x, y, ",=EOYd")
				continue
			if ch == "T" and tex_trees:
				# forest floor; every other tile grows a full tree (drawn as a tall decal below)
				ci.draw_rect(dest, Color(0.0, 0.05, 0.0, 0.18))
				continue
			if ch in ["s", "A", "G", "M"]:
				_draw_prop(ci, ch, x, y)
				continue
			var nm := _tile_name(x, y)
			if ch == "O":
				# portals glow in the color of where they lead
				var col := Color.WHITE
				for e in m.exits:
					if int(e.x) == x and int(e.y) == y:
						var tw: String = DB.map(e.to).world
						col = DB.el_color(tw) if tw != "nexus" else Color(0.75, 0.65, 1.0)
				var pulse := 0.5 + 0.5 * sin(anim_t * 3.0)
				ci.draw_rect(Rect2(x * TS - 4, y * TS - 2, TS + 8, TS + 4), Color(col.r, col.g, col.b, 0.18 + 0.12 * pulse))
				ci.draw_texture_rect_region(ts, dest, Art.tile_rect(nm), col.lerp(Color.WHITE, 0.3))
				continue
			ci.draw_texture_rect_region(ts, dest, Art.tile_rect(nm))
			if ch == "r":
				var rc := Color(0, 0, 0, 0.35)
				if tile_at(Vector2i(x, y - 1)) != "r":
					ci.draw_rect(Rect2(x * TS, y * TS, TS, 2), rc)
				if tile_at(Vector2i(x, y + 1)) != "r":
					ci.draw_rect(Rect2(x * TS, y * TS + TS - 2, TS, 2), rc)
				if tile_at(Vector2i(x - 1, y)) != "r":
					ci.draw_rect(Rect2(x * TS, y * TS, 2, TS), rc)
				if tile_at(Vector2i(x + 1, y)) != "r":
					ci.draw_rect(Rect2(x * TS + TS - 2, y * TS, 2, TS), rc)
			if ch == "L":
				ci.draw_texture_rect_region(ts, Rect2(x * TS, (y - 1) * TS, TS, TS), Art.tile_rect("landmark_top"))
		# trees whose trunks stand on this row
		if tex_trees:
			for x in range(max(0, x0 - 1), min(W, x1 + 1)):
				if tile_at(Vector2i(x, y)) == "T" and _tree_here(x, y):
					_draw_tree(ci, x, y, false)
	_draw_shadows(ci, x0, y0, x1, y1)
	# shop signs hang beside the doors
	for sg in m.get("signs", []):
		ci.draw_texture_rect_region(ts, Rect2(int(sg.x) * TS, int(sg.y) * TS, TS, TS), Art.tile_rect(str(sg.tile)))
	_draw_work_under(ci)
	# sparkles from found treasure
	for s in sparkles:
		var a: float = s.t
		ci.draw_rect(Rect2(s.p + Vector2(-1, -14 - a * 16), Vector2(2, 2)), Color(1, 1, 0.8, 1.0 - a))


func _tree_here(x: int, y: int) -> bool:
	# thin the canopy: big LPC trees are three tiles wide
	if (x + y * 2) % 3 == 0:
		return true
	# lone trees (no forest around) always grow
	return tile_at(Vector2i(x - 1, y)) != "T" and tile_at(Vector2i(x + 1, y)) != "T"


## One tree decal: 96x160, trunk on the bottom tile. `canopy` draws only the leaves (above characters).
func _draw_tree(ci: Node2D, x: int, y: int, canopy: bool) -> void:
	var v := (x * 31 + y * 17) % 2
	var src := Rect2(v * 96, 0, 96, 160)
	var dst := Rect2(x * TS + TS * 0.5 - 48, y * TS + TS - 160, 96, 160)
	if canopy:
		# everything above the trunk's bottom 44 px goes over the characters
		src.size.y -= 44
		dst.size.y -= 44
	ci.draw_texture_rect_region(tex_trees, dst, src)


## Drawn above characters: tree canopies, and the falling-water veil over ledges behind waterfalls.
func _draw_overlay(ci: Node2D) -> void:
	_draw_work_over(ci)
	_draw_atmosphere(ci)
	var x0 := int(floor(cam.x / TS)) - 2
	var y0 := int(floor(cam.y / TS)) - 1
	var fr3 := int(anim_t * 3.0) % 3
	for y in range(max(0, y0), min(H, y0 + int(VIEW.y / TS) + 7)):
		for x in range(max(0, x0), min(W, x0 + int(VIEW.x / TS) + 5)):
			var ch := tile_at(Vector2i(x, y))
			if ch == "T" and tex_trees and _tree_here(x, y):
				_draw_tree(ci, x, y, true)
			if ch == "Z":
				ci.draw_texture_rect_region(ts, Rect2(x * TS, y * TS, TS, TS), Art.tile_rect("veil%d" % fr3))
			if ch == "U":
				ci.draw_texture_rect_region(ts, Rect2(x * TS, y * TS - 16, TS, TS), Art.tile_rect("veil%d" % fr3))
				ci.draw_texture_rect_region(ts, Rect2(x * TS, y * TS + 16, TS, 16), Rect2(Art.tile_rect("veil%d" % ((fr3 + 1) % 3)).position, Vector2(TS, 16)))


func _draw_hud(ci: Node2D) -> void:
	if banner_t > 0 and not dialog.active:
		var a := clampf(banner_t, 0.0, 1.0)
		var w := Art.width(banner_text, 16, Art.font) + 24
		var r := Rect2(240 - w / 2, 10, w, 24)
		ci.draw_rect(r, Color(0.02, 0.02, 0.06, 0.65 * a))
		ci.draw_rect(Rect2(r.position.x, r.end.y - 1, r.size.x, 1), Color(1, 1, 1, 0.5 * a))
		Art.text_center(ci, Vector2(240, 14), banner_text, Color(1, 1, 1, a), 16)
	if m.kind == "town" or m.kind == "hub":
		pass


# ------------------------------------------------------------------ interaction

func _open_full_map() -> void:
	busy = true
	Audio.sfx("cursor")
	minimap.open_full()
	await get_tree().process_frame
	while true:
		await get_tree().process_frame
		if minimap.full_input():
			break
	Audio.sfx("cancel")
	minimap.full = false
	busy = false


func _facing_tile() -> Vector2i:
	return ppos + DIRS[face]


func _interact() -> void:
	var t := _facing_tile()
	if tile_at(t) == "c":
		t += DIRS[face]  # talk across the counter
	for n in npcs:
		if n.actor.visible and n.pos == t:
			await _talk(n)
			return
	for c in chests:
		if Vector2i(int(c.data.x), int(c.data.y)) == _facing_tile():
			await _open_chest(c)
			return
	for b in bosses:
		if b.visible and Vector2i(int(b.data.x), int(b.data.y)) == _facing_tile():
			await _entity(b)
			return
	for h in m.hidden:
		var hp := Vector2i(int(h.x), int(h.y))
		if (hp == ppos or hp == _facing_tile()) and not GS.flag(h.flag):
			await _dig(h)
			return
	if tile_at(_facing_tile()) == "L":
		var lm: String = DB.d.worlds[world].landmark if DB.d.worlds.has(world) else "a strange landmark"
		await dialog.say(["%s. It looks like it's been here forever." % lm.capitalize()])


func _talk(n: Dictionary) -> void:
	busy = true
	# face the player
	var d: Vector2i = ppos - n.pos
	var fd := 0
	if d.x < 0:
		fd = 1
	elif d.x > 0:
		fd = 2
	elif d.y < 0:
		fd = 3
	n.talking = true
	if n.job != "":
		_npc_to_walk_sheet(n)
	n.actor.set_frame(fd * WF)
	var data: Dictionary = n.data
	for branch in data.script:
		if GS.check(branch.get("if", [])):
			await dialog.say(branch.get("say", []), data.name)
			if branch.has("do"):
				await run_actions(branch.do, data.name)
			if branch.has("ask"):
				var r: int = await dialog.ask(branch.ask.q, ["Yes", "No"], data.name)
				var sub: Dictionary = branch.ask.yes if r == 0 else branch.ask.no
				await dialog.say(sub.get("say", []), data.name)
				await run_actions(sub.get("do", []), data.name)
			break
	n.talking = false
	if n.job != "":
		_npc_to_work(n)
	elif not n.data.get("wander", false):
		n.face = fd
		n.look_t = rng.randf_range(2.0, 4.0)
	_refresh_visibility()
	busy = false


func run_actions(actions: Array, who: String = "") -> void:
	if actions.is_empty():
		return
	var results := GS.apply(actions)
	for r in results:
		if r.has("msg"):
			if r.has("sfx"):
				Audio.sfx(r.sfx)
			await dialog.say([r.msg])
		elif r.has("ui"):
			await _ui_action(r.ui, who)
	_refresh_player()


func _ui_action(s: String, who: String) -> void:
	var i := s.find(":")
	var k := s if i < 0 else s.substr(0, i)
	var v := "" if i < 0 else s.substr(i + 1)
	match k:
		"hunt_start":
			var st := _hunt_state()
			st["accepted"] = true
			GS.flags["hunt_active"] = st
			_spawn_quarry(st)
			Audio.sfx("quest")
			await dialog.say(["Something stirs far off in %s. Check your map." % str(m.name)])
		"hunt_end":
			GS.flags.erase("hunt_active")
			for n in npcs:
				if n.data.get("hunter", false):
					n.actor.visible = false
					n.data["cond"] = ["flag:_never"]
			for b in bosses:
				if str(b.data.get("kind", "")) == "hunt":
					b.visible = false
		"shop":
			var shop := Shop.new()
			shop.shop_id = v
			ui.add_child(shop)
			await shop.closed
			shop.queue_free()
		"inn":
			var price := int(v)
			if GS.gold < price:
				await dialog.say(["You don't have enough gold."], who)
				return
			GS.gold -= price
			await Main.inst.fade_out(0.4)
			for mm in GS.roster.values():
				GS.full_heal(mm)
			Audio.sfx("rest")
			await get_tree().create_timer(0.8).timeout
			await Main.inst.fade_in(0.4)
		"sfx":
			Audio.sfx(v)
		"end":
			await Main.inst.show_ending()
		"warp":
			var dm: Dictionary = DB.map(v)
			Audio.sfx("portal")
			GS.save_game(0)
			busy = true
			Main.inst.change_map(v, int(dm.start[0]), int(dm.start[1]), 3)


func _open_chest(c: Chest) -> void:
	if c.opened:
		await dialog.say(["It's empty."])
		return
	busy = true
	c.opened = true
	c.queue_redraw()
	GS.flags["chest:" + c.data.id] = true
	Audio.sfx("chest")
	var got := GS.add_item(str(c.data.item))
	var spec := str(c.data.item)
	if spec.begins_with("summon:"):
		Audio.sfx("summon_get")
		await dialog.say(["Found %s!" % got, "It hums in your hand, warm and alive. You can now call on it in battle (Summon)."])
	else:
		await dialog.say(["Found %s!" % got])
	_refresh_player()
	busy = false


func _dig(h: Dictionary) -> void:
	busy = true
	GS.flags[h.flag] = true
	Audio.sfx("dig")
	await dialog.say([str(h.get("text", "You notice the ground here is different. You dig with your hands..."))])
	var got := GS.add_item(str(h.item))
	Audio.sfx("treasure")
	for i in 8:
		sparkles.append({"p": _tile_px(Vector2i(int(h.x), int(h.y))) + Vector2(randf_range(-6, 6), 0), "t": randf() * 0.3})
	_animate_sparkles()
	await dialog.say(["Found %s!" % got, "Whoever hid this wanted it to be found by someone who listened."])
	busy = false


func _animate_sparkles() -> void:
	while not sparkles.is_empty():
		await get_tree().process_frame
		for s in sparkles:
			s.t += get_process_delta_time() * 0.8
		sparkles = sparkles.filter(func(s): return s.t < 1.0)


func _entity(b: Boss) -> void:
	busy = true
	var e: Dictionary = b.data
	if e.kind == "seal":
		await _seal(e)
		busy = false
		return
	if not GS.check(e.get("need", [])):
		await dialog.say(e.get("need_fail", ["Not yet."]))
		busy = false
		return
	await dialog.say(e.pre)
	var enemy := DB.make_enemy(e.id, GS.avg_level(), world if DB.d.element_info.has(world) else "void")
	var music: String = str(e.get("music", "omni" if e.kind == "omni" else "boss"))
	var bg: String = m.bg if m.bg != null else "%s_in" % world
	var res: String = await Main.inst.battle([enemy], {"bg": bg, "music": music, "flee": false, "boss": e.kind != "mini"})
	if res == "win":
		var results := GS.apply(e.win_do)
		_refresh_visibility()
		await dialog.say(e.post)
		for r in results:
			if r.has("msg"):
				if r.has("sfx"):
					Audio.sfx(r.sfx)
				await dialog.say([r.msg])
			elif r.has("ui"):
				await _ui_action(r.ui, "")
		_refresh_player()
	busy = false


func _seal(e: Dictionary) -> void:
	if not GS.quests.has(e.quest):
		GS.apply(["quest:" + e.quest])
		Audio.sfx("quest")
	if GS.flag(e.flag):
		await dialog.say(["The door stands open."])
		Main.inst.change_map(e.to, int(e.tx), int(e.ty), 3)
		busy = true
		return
	var has_all := true
	for k in e["keys"]:
		if not GS.has_item(k):
			has_all = false
	if not has_all:
		await dialog.say(e.locked)
		return
	await dialog.say(e.open)
	GS.flags[e.flag] = true
	Audio.sfx("door_open")
	Main.inst.change_map(e.to, int(e.tx), int(e.ty), 3)
	busy = true


func _open_menu() -> void:
	busy = true
	Audio.sfx("menu_open")
	await menu.open()
	_refresh_player()
	_refresh_visibility()
	busy = false
