extends Node
## Automated play-tester: drives the real UI with simulated key presses and saves screenshots.

var shots_dir := "/tmp/sh"
var step_name := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	DirAccess.make_dir_recursive_absolute(shots_dir)
	_run.call_deferred()


func press(action: String, hold_frames := 2) -> void:
	await get_tree().process_frame
	Input.action_press(action)
	for i in hold_frames:
		await get_tree().process_frame
	Input.action_release(action)
	for i in 2:
		await get_tree().process_frame


func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func shot(name: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png("%s/%s.png" % [shots_dir, name])
	print("SHOT ", name)


func map_node():
	return Main.inst.map_node


func dialog_active() -> bool:
	var m = map_node()
	return m != null and is_instance_valid(m) and m.dialog.active


func mash_until_free(max_s := 20.0) -> void:
	## Press OK until no dialog is open and the map is idle.
	var t := 0.0
	while t < max_s:
		var m = map_node()
		if m and is_instance_valid(m) and not m.dialog.active and not m.busy and not Main.inst.busy and Main.inst.battle_node == null:
			await wait(0.2)
			if not m.dialog.active and not m.busy:
				return
		await press("ok")
		await wait(0.08)
		t += 0.15


func auto_battle(max_s := 120.0, pattern: Array = []) -> String:
	## While a battle runs: choose commands. pattern is a list of command indices to try in order.
	var t := 0.0
	var i := 0
	while Main.inst.battle_node != null and t < max_s:
		var b = Main.inst.battle_node
		if b.phase == "results":
			await press("ok")
		elif b.phase == "gameover":
			print("GAMEOVER reached")
			await press("down")
			await press("down")
			await press("ok")
		elif b.menu_for != null and b.menu_state == "cmd":
			var c: int = pattern[i % pattern.size()] if pattern.size() > 0 else 0
			i += 1
			for k in c:
				await press("down")
			await press("ok")
		elif b.menu_for != null:
			if b.banner_t > 0 and b.banner.begins_with("Not enough"):
				await press("back")
				await press("back")
			else:
				await press("ok")
		await wait(0.1)
		t += 0.16
	return "done"


func _run() -> void:
	await wait(1.0)
	await shot("01_title")
	await press("ok")          # New Game
	await wait(2.0)
	await shot("02_intro")
	await mash_until_free()
	await shot("03_nexus")
	# walk a little
	for k in 3:
		await press("down", 10)
	await shot("04_nexus_walk")
	# menu
	await press("back")
	await wait(0.3)
	await shot("05_menu")
	await press("down")        # Magic
	await press("down")        # Equip
	await press("ok")
	await press("ok")          # pick hero
	await wait(0.2)
	await shot("06_equip")
	await press("ok")          # weapon slot list
	await wait(0.2)
	await shot("07_equip_list")
	await press("back")
	await press("back")
	await press("down")        # Status (cursor moved?) -> go back to main
	await press("back")
	await press("back")
	await wait(0.3)
	# jump to the fire town
	Main.inst.change_map("fire_town", 16, 5, 0)
	await wait(1.5)
	await shot("08_fire_town")
	var m = map_node()
	var kael = m._npc_by_id("kael")
	m._talk(kael)
	await wait(0.3)
	await shot("09_dialog")
	# press OK through dialog; the ask defaults to Yes
	await mash_until_free()
	print("party after kael: ", GS.party)
	await shot("10_after_recruit")
	# shop
	var pawn = m._npc_by_id("pawn_fire_k")
	m._talk(pawn)
	await wait(0.2)
	await press("ok")   # dismiss the line
	await wait(0.3)
	await press("ok")   # Buy
	await wait(0.2)
	await shot("11_shop")
	await press("ok")   # buy first item
	await wait(0.2)
	await press("back")
	await press("back")
	await press("back")
	await wait(0.5)
	# random battle in the field
	Main.inst.change_map("fire_field", 23, 32, 3)
	await wait(1.5)
	await shot("12_field")
	GS.summons.append("pyrestag")
	GS.items["might_elixir"] = 2
	var enemies := DB.random_group("fire", "field", GS.avg_level(), RandomNumberGenerator.new())
	Main.inst.battle(enemies, {"bg": "fire_out", "music": "battle", "flee": true})
	await wait(2.2)
	await shot("13_battle_start")
	# first turn: open Magic menu to screenshot it, then attack
	var t := 0.0
	while Main.inst.battle_node != null and Main.inst.battle_node.menu_for == null and t < 10:
		await wait(0.1)
		t += 0.1
	await shot("14_battle_cmd")
	await press("down")
	await press("ok")
	await wait(0.2)
	await shot("15_battle_magic")
	await press("back")
	await press("up")
	await auto_battle(60.0, [0, 0, 1, 0])
	await wait(1.5)
	print("after battle: hero lv ", GS.roster.hero.level, " xp ", GS.roster.hero.xp, " gold ", GS.gold)
	await shot("16_after_battle")
	# boss test
	var boss := DB.make_enemy("vulkar", GS.avg_level(), "fire")
	Main.inst.battle([boss], {"bg": "fire_in", "music": "boss", "flee": false})
	await wait(2.5)
	await shot("17_boss")
	await auto_battle(150.0, [0, 0, 0, 1])
	await wait(1.5)
	await shot("18_post_boss")
	print("boss result: hero hp ", GS.roster.hero.hp)
	# save / load roundtrip
	print("save ok: ", GS.save_game(3))
	print("load ok: ", GS.load_game(3))
	print("TEST DONE")
	get_tree().quit()
