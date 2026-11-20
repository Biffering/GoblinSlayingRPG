extends Node
func _ready() -> void:
	_run.call_deferred()
func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout
func _run() -> void:
	await wait(0.3)
	GS.new_game()
	Main.inst._open_map("fire_town", 20, 20, 0)
	Main.inst.fader.alpha = 0.0
	await wait(2.6)
	var mp = Main.inst.map_node
	print("main busy ", Main.inst.busy, " map busy ", mp.busy, " block ", Inp.block_frames)
	var ev := InputEventKey.new()
	ev.physical_keycode = KEY_M
	ev.pressed = true
	Input.parse_input_event(ev)
	await wait(0.1)
	ev = ev.duplicate(); ev.pressed = false
	Input.parse_input_event(ev)
	await wait(0.4)
	print("full open: ", mp.minimap.full)
	ev = InputEventKey.new(); ev.physical_keycode = KEY_M; ev.pressed = true
	Input.parse_input_event(ev)
	await wait(0.1)
	ev = ev.duplicate(); ev.pressed = false
	Input.parse_input_event(ev)
	await wait(0.4)
	print("full after 2nd: ", mp.minimap.full, " busy ", mp.busy)
	print("T20 DONE")
	get_tree().quit()
