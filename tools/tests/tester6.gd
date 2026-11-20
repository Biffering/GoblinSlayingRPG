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
	await wait(0.5)
	GS.new_game()
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	for m in GS.roster.values():
		while m.level < 12:
			GS.give_xp(m, DB.xp_to_next(m.level))
		GS.full_heal(m)
	GS.gold = 5000
	GS.roster.hero.equip.weapon = {"id": "pitbreaker", "lv": 12}
	GS.roster.kael.equip.weapon = {"id": "magma_edge", "lv": 12}
	GS.add_item("gear:phoenix_longbow")
	GS.add_item("gear:salamander_coat")
	GS.add_item("gear:ember_ring")
	var tm: Dictionary = DB.map("fire_town")
	await goto("fire_town", int(tm.start[0]), int(tm.start[1]) + 4, 0)
	# walk a few steps so followers trail
	for i in 4:
		Input.action_press("down")
		await wait(0.2)
	Input.action_release("down")
	await wait(0.5)
	await shot("b01_fire_town")
	for k in ["tavern", "inn", "pawn", "house3"]:
		var im: Dictionary = DB.map("fire_" + k)
		await goto("fire_" + k, int(im.start[0]), int(im.start[1]), 3)
		await shot("b02_fire_" + k)
	# pawn shop UI
	var pm = Main.inst.map_node if "map_node" in Main.inst else null
	var Shop := load("res://scripts/shop.gd")
	var sh = Shop.new()
	sh.shop_id = "pawn_fire"
	get_tree().root.add_child(sh)
	await wait(0.3)
	await press("ok")
	await wait(0.2)
	for i in 3:
		await press("down")
	await shot("b03_pawn_shop")
	sh.queue_free()
	await wait(0.3)
	# waterfall ledge
	var wm: Dictionary = DB.map("water_area2")
	var cols: Array = wm.waterfall
	var ledge_y := -1
	for y in wm.h:
		if str(wm.tiles[y]).substr(int(cols[1]), 1) == "U":
			ledge_y = y
	await goto("water_area2", int(cols[1]), ledge_y, 3)
	await shot("b04_waterfall_ledge")
	await goto("wind_field", 23, 30, 3)
	await shot("b05_wind_field")
	var sm: Dictionary = DB.map("stone_town")
	await goto("stone_town", int(sm.start[0]), int(sm.start[1]) + 6, 0)
	await shot("b06_stone_town")
	# battle with marker and drop result
	var e1 := DB.make_enemy("rat", 12, "fire")
	var e2 := DB.make_enemy("rat", 12, "fire")
	Main.inst.battle([e1, e2], {"bg": "fire_out", "music": "battle", "flee": true})
	await wait(3.0)
	await shot("b07_battle_marker")
	await press("ok")
	await wait(0.2)
	await press("ok")
	await wait(2.5)
	await shot("b08_battle_after_hit")
	print("TEST6 DONE")
	get_tree().quit()
