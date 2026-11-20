extends Node
func _ready() -> void:
	_run.call_deferred()
func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout
func shot(n: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/sh/%s.png" % n)
func press(a: String) -> void:
	Input.action_press(a)
	await get_tree().process_frame
	await get_tree().process_frame
	Input.action_release(a)
	await wait(0.4)
func _run() -> void:
	await wait(0.3)
	GS.new_game()
	for id in ["kael", "nerissa"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa"]
	for spot in [["fire_town", 20, 20, "town"], ["water_field", 20, 20, "field"]]:
		Main.inst._open_map(spot[0], spot[1], spot[2], 0)
		Main.inst.fader.alpha = 0.0
		await wait(2.6)
		var mp = Main.inst.map_node
		# walk a few steps so fog lifts
		for k in 5:
			Input.action_press("right")
			await wait(0.32)
		Input.action_release("right")
		await wait(0.5)
		await shot("mm_%s_mini" % spot[3])
		for k in 12:
			mp.ppos += Vector2i(1, 0) if k < 6 else Vector2i(0, 1)
			mp.player.position = mp._tile_px(mp.ppos)
			await wait(0.05)
		await wait(0.3)
		await shot("mm_%s_mini" % spot[3])
		mp._open_full_map()
		await wait(0.6)
		await shot("mm_%s_full" % spot[3])
		await press("map")
		print(spot[0], " busy after close: ", mp.busy)
	print("T19 DONE")
	get_tree().quit()
