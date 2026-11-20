extends Node
func _ready() -> void:
	_run.call_deferred()
func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout
func shot(n: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/sh/%s.png" % n)
func key(k: int) -> void:
	var ev := InputEventKey.new(); ev.physical_keycode = k; ev.pressed = true
	Input.parse_input_event(ev)
	await wait(0.06)
	ev = ev.duplicate(); ev.pressed = false
	Input.parse_input_event(ev)
	await wait(0.18)
func _run() -> void:
	await wait(0.3)
	GS.new_game()
	Main.inst._open_map("fire_field", 23, 30, 3)
	Main.inst.fader.alpha = 0.0
	await wait(2.6)
	var mp = Main.inst.map_node
	await key(KEY_M)
	for i in 3:
		await key(KEY_RIGHT)
	await key(KEY_UP)
	await key(KEY_Z)
	await key(KEY_DOWN)
	await key(KEY_DOWN)
	await wait(0.2)
	await shot("p1_picker")
	await key(KEY_Z)
	for i in 4:
		await key(KEY_LEFT)
	await key(KEY_UP)
	await key(KEY_UP)
	await key(KEY_Z)
	await key(KEY_DOWN)
	await key(KEY_Z)
	await key(KEY_RIGHT)
	await key(KEY_RIGHT)
	await key(KEY_RIGHT)
	await key(KEY_RIGHT)
	await key(KEY_DOWN)
	await key(KEY_DOWN)
	await wait(0.2)
	await shot("p2_placed")
	await key(KEY_Z)
	await wait(0.2)
	await shot("p3_edit")
	await key(KEY_X)
	await key(KEY_X)
	await wait(0.4)
	print("pins: ", mp.minimap.pins(), " busy ", mp.busy, " full ", mp.minimap.full)
	await shot("p4_mini")
	print("T22 DONE")
	get_tree().quit()
