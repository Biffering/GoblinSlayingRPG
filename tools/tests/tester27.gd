extends Node
func _ready() -> void:
	_run.call_deferred()
func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout
func hold(keys: Array, down: bool) -> void:
	for k in keys:
		var ev := InputEventKey.new(); ev.physical_keycode = k; ev.pressed = down
		Input.parse_input_event(ev)
func _run() -> void:
	await wait(0.3)
	GS.new_game()
	print("stash: ", GS.gear.size(), " ", GS.gear.map(func(g): return g.id))
	# put a wandering hunter right in front of the hero, then walk into them
	GS.flags["hunt_active"] = {"id": "flock", "map": "wind_field", "x": 20, "y": 27, "accepted": false, "gold": 1000}
	Main.inst._open_map("wind_field", 20, 30, 3)
	Main.inst.fader.alpha = 0.0
	await wait(2.4)
	var mp = Main.inst.map_node
	var h = mp.npcs.filter(func(n): return n.data.get("hunter", false))[0]
	h.data.wander = true
	h.wander_t = 99.0
	# place them directly above the hero
	var keys := {Vector2i(0, -1): KEY_UP, Vector2i(1, 0): KEY_RIGHT, Vector2i(-1, 0): KEY_LEFT, Vector2i(0, 1): KEY_DOWN}
	var dir := Vector2i(0, -1)
	for d in keys:
		if mp.BLOCK.find(mp.tile_at(mp.ppos + d)) < 0 and mp.BLOCK.find(mp.tile_at(mp.ppos + d * 2)) < 0:
			dir = d
			break
	var spot: Vector2i = mp.ppos + dir
	h.pos = spot
	h.actor.position = mp._tile_px(spot)
	var p0: Vector2i = mp.ppos
	print("tile above: '", mp.tile_at(spot), "' busy ", mp.busy, " main busy ", Main.inst.busy, " walkable-if-empty ", mp.BLOCK.find(mp.tile_at(spot)) < 0)
	hold([keys[dir]], true)
	await wait(0.6)
	hold([keys[dir]], false)
	await wait(0.4)
	print("hero ", p0, " -> ", mp.ppos, "   hunter moved from ", spot, " to ", h.pos)
	print("T27 DONE")
	get_tree().quit()
