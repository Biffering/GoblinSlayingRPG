extends Node
func _ready() -> void:
	_run.call_deferred()
func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout
func shot(n: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/shx/%s.png" % n)
func _run() -> void:
	await wait(0.3)
	GS.new_game()
	for id in ["kael", "nerissa"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa"]
	for spot in [["fire_cave", 0, 0], ["stone_dungeon", 0, 0], ["fire_tavern", 0, 0], ["water_town", 20, 20], ["wind_field", 20, 30], ["void_town", 20, 20]]:
		var mm: Dictionary = DB.map(spot[0])
		var sx: int = int(mm.start[0]) if spot[1] == 0 else spot[1]
		var sy: int = int(mm.start[1]) if spot[2] == 0 else spot[2]
		GS.weather = {"kind": "sunny"} if spot[0] != "void_town" else {"kind": "motes"}
		Main.inst._open_map(spot[0], sx, sy, 3)
		Main.inst.fader.alpha = 0.0
		await wait(2.0)
		await shot("l_" + spot[0])
	print("T26 DONE")
	get_tree().quit()
