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
	await wait(1.5)
	await shot("d00_title")
	GS.new_game()
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	for m in GS.roster.values():
		while m.level < 20:
			GS.give_xp(m, DB.xp_to_next(m.level))
		GS.full_heal(m)
	await goto("goblin_warren", int(DB.map("goblin_warren").start[0]), int(DB.map("goblin_warren").start[1]), 3)
	await shot("d01_warren")
	await goto("goblin_throne", int(DB.map("goblin_throne").start[0]), int(DB.map("goblin_throne").start[1]) - 3, 3)
	await shot("d02_throne")
	Main.inst.battle([DB.make_enemy("king_goblin", 25, "void")], {"bg": "goblin_in", "music": "king_goblin", "flee": false})
	await wait(3.0)
	await shot("d03_king_battle")
	Main.inst.battle_node.finished.emit("flee")
	await wait(1.5)
	Main.inst.battle([DB.make_enemy("pirate", 12, "water"), DB.make_enemy("pirate_gunner", 12, "water"), DB.make_enemy("goblin", 12, "water")], {"bg": "water_out", "music": "battle", "flee": true})
	await wait(3.0)
	await shot("d04_pirates")
	Main.inst.battle_node.finished.emit("flee")
	await wait(1.5)
	await goto("water_town", int(DB.map("water_town").start[0]), int(DB.map("water_town").start[1]) + 5, 0)
	await shot("d05_water_town")
	await goto("void_field", 23, 30, 3)
	await shot("d06_void_field")
	await goto("spirit_town", int(DB.map("spirit_town").start[0]), int(DB.map("spirit_town").start[1]) + 5, 0)
	await shot("d07_spirit_town")
	await goto("stone_dungeon", int(DB.map("stone_dungeon").start[0]), int(DB.map("stone_dungeon").start[1]), 3)
	await shot("d08_stone_dungeon")
	print("TEST12 DONE")
	get_tree().quit()
