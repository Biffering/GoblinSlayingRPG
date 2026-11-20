extends Node
## Visual check of v2: towns, interiors, signs, followers, waterfall ledge, battle marker, tier colors, shop.

var shots_dir := "/tmp/sh"


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func press(action: String) -> void:
	await get_tree().process_frame
	Input.action_press(action)
	await get_tree().process_frame
	await get_tree().process_frame
	Input.action_release(action)
	await get_tree().process_frame


func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func shot(name: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [shots_dir, name])


func goto(mid: String, x: int, y: int, f: int = 3) -> void:
	Main.inst._open_map(mid, x, y, f)
	Main.inst.fader.alpha = 0.0
	await wait(1.0)


func _run() -> void:
	await wait(3.0)
	await shot("e00_title")
	await wait(2.3)
	await shot("e01_title")
	GS.new_game()
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	var i := 0
	for pair in [["water_field", "storm"], ["fire_field", "ash"], ["spirit_town", "snow"], ["wind_field", "breeze"], ["stone_field", "sunny"], ["void_field", "motes"]]:
		var mid: String = pair[0]
		GS.weather = {"kind": pair[1], "t": 0.0, "dur": 999.0, "world": DB.map(mid).world}
		var mm: Dictionary = DB.map(mid)
		await goto(mid, int(mm.start[0]), int(mm.start[1]) - (5 if mid.ends_with("town") else 0), 3)
		await wait(4.5)
		await shot("e1%d_%s" % [i, pair[1]])
		i += 1
	GS.weather = {"kind": "rain", "t": 0.0, "dur": 999.0, "world": "water"}
	await goto("water_field", int(DB.map("water_field").start[0]), int(DB.map("water_field").start[1]), 3)
	await wait(1.0)
	Main.inst.battle([DB.make_enemy("pirate", 10, "water"), DB.make_enemy("goblin", 10, "water")], {"bg": "water_out", "music": "battle", "flee": true})
	await wait(3.2)
	await shot("e20_rain_battle")
	print("TEST13 DONE")
	get_tree().quit()
