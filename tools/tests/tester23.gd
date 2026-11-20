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
	for id in ["kael", "nerissa"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa"]
	Main.inst._open_map("fire_town", 20, 12, 0)
	Main.inst.fader.alpha = 0.0
	await wait(2.6)
	var mp = Main.inst.map_node
	var p0: Vector2i = mp.ppos
	hold([KEY_RIGHT, KEY_DOWN], true)
	await wait(1.2)
	hold([KEY_RIGHT, KEY_DOWN], false)
	await wait(0.4)
	print("walk diag 1.2s: ", p0, " -> ", mp.ppos)
	p0 = mp.ppos
	hold([KEY_SHIFT, KEY_LEFT, KEY_DOWN], true)
	await wait(1.2)
	hold([KEY_SHIFT, KEY_LEFT, KEY_DOWN], false)
	await wait(0.4)
	print("run diag 1.2s: ", p0, " -> ", mp.ppos)
	p0 = mp.ppos
	hold([KEY_SHIFT, KEY_RIGHT], true)
	await wait(1.0)
	hold([KEY_SHIFT, KEY_RIGHT], false)
	await wait(0.3)
	print("run right 1.0s: ", p0, " -> ", mp.ppos)
	p0 = mp.ppos
	hold([KEY_RIGHT], true)
	await wait(1.0)
	hold([KEY_RIGHT], false)
	await wait(0.3)
	print("walk right 1.0s: ", p0, " -> ", mp.ppos)
	# into a wall corner: up+left toward buildings, should slide not stop
	p0 = mp.ppos
	hold([KEY_UP, KEY_LEFT], true)
	await wait(2.5)
	hold([KEY_UP, KEY_LEFT], false)
	await wait(0.3)
	print("up-left 2.5s (slides along walls): ", p0, " -> ", mp.ppos)
	print("T23 DONE")
	get_tree().quit()
