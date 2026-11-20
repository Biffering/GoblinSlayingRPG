extends Node
## Visual check of auras at high level, hero tier 3, boost glow, boss phase text and the ending.

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


func _run() -> void:
	await wait(0.5)
	GS.new_game()
	for id in ["kael", "nerissa", "vesper"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "vesper"]
	var lv := {"hero": 30, "kael": 12, "nerissa": 22, "vesper": 4}
	for m in GS.roster.values():
		while m.level < lv[m.id]:
			GS.give_xp(m, DB.xp_to_next(m.level))
	var h: Dictionary = GS.roster.hero
	h.equip.weapon = {"id": "cinder_blade", "lv": 30}
	h.equip.armor = {"id": "shellguard", "lv": 30}
	h.equip.acc = {"id": "wind_ring", "lv": 30}
	GS.roster.kael.equip.acc = {"id": "ember_ring", "lv": 12}
	GS.roster.nerissa.equip.acc = {"id": "spirit_ring", "lv": 22}
	GS.roster.nerissa.boosts = {"mag": 5}
	for m in GS.roster.values():
		GS.full_heal(m)
	Main.inst._open_map("void_field", 23, 30, 3)
	Main.inst.fader.alpha = 0.0
	await wait(1.2)
	await shot("a01_map_aura")
	var boss := DB.make_enemy("iris", 24, "spirit")
	Main.inst.battle([boss], {"bg": "fire_in", "music": "boss", "flee": false})
	await wait(2.5)
	await shot("a02_battle_auras")
	# hit the boss below half health to trigger her phase line
	var b = Main.inst.battle_node
	b.foes[0].hp = int(b.foes[0].maxhp * 0.55)
	await wait(0.6)
	await shot("a03_battle_auras2")
	b.finished.emit("flee")
	await wait(2.0)
	Main.inst.show_ending()
	await wait(9.0)
	await shot("a04_ending")
	print("TEST5 DONE")
	get_tree().quit()
