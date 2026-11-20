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
	var pm: Dictionary = DB.map("fire_pawn")
	await goto("fire_pawn", 6, 4, 3)
	var mp = Main.inst.get_children().filter(func(c): return "npcs" in c)[0]
	mp._talk(mp._npc_by_id("pawn_fire_k"))
	await wait(1.0)
	var tries := 0
	while tries < 40 and mp.ui.get_children().filter(func(c): return "shop_id" in c).is_empty():
		await press("ok")
		await wait(0.25)
		tries += 1
	await wait(0.4)
	var shp = mp.ui.get_children().filter(func(c): return "shop_id" in c)[0]
	var g0 := GS.gold
	var n0 := GS.gear.size()
	await press("ok")          # Buy
	await wait(0.3)
	print("mode after Buy: ", shp.mode)
	await press("ok")          # buy Cinder Blade
	await wait(0.3)
	print("bought gear: gold ", g0, "->", GS.gold, " gear ", n0, "->", GS.gear.size())
	await press("back")
	await wait(0.2)
	await press("down")
	await wait(0.2)
	await press("ok")          # Sell
	await wait(0.3)
	print("mode after Sell: ", shp.mode)
	await press("back")
	await wait(0.2)
	await press("up")
	await wait(0.2)
	await press("ok")
	await wait(0.3)
	shp.idx = 12
	await wait(0.3)
	await shot("c01_pawn_buy")
	for i in 4:
		await press("back")
		await wait(0.2)
	await wait(0.5)
	var e1 := DB.make_enemy("rat", 12, "fire")
	Main.inst.battle([e1, DB.make_enemy("bum", 12, "fire")], {"bg": "fire_out", "music": "battle", "flee": true})
	await wait(3.0)
	await shot("c02_battle_hd")
	print("TEST6 DONE")
	get_tree().quit()
