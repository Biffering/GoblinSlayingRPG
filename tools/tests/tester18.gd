extends Node
func _ready() -> void:
	_run.call_deferred()
func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout
func shot(n: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/sh/%s.png" % n)
func _run() -> void:
	await wait(0.3)
	GS.new_game()
	var spots := {"water": "fish", "fire": "smith", "void": "seance", "wind": "hoe", "wind2": "chop", "stone": "mine", "spirit": "pray"}
	for wk in spots:
		var w: String = wk.trim_suffix("2")
		var m: Dictionary = DB.map(w + "_town")
		var tgt: Dictionary = {}
		for n in m.npcs:
			if n.get("job", "") == spots[wk]:
				tgt = n
				break
		var px := int(tgt.x) + 2
		var py := int(tgt.y) + 2
		for o in [Vector2i(1, 2), Vector2i(2, 1), Vector2i(0, 2), Vector2i(3, 0), Vector2i(-2, 1), Vector2i(1, -2), Vector2i(2, 3)]:
			var ch: String = str(m.tiles[int(tgt.y) + o.y]).substr(int(tgt.x) + o.x, 1)
			if ch in [".", ",", "\"", "F"]:
				px = int(tgt.x) + o.x
				py = int(tgt.y) + o.y
				break
		Main.inst._open_map(w + "_town", px, py, 3)
		Main.inst.fader.alpha = 0.0
		var mp = Main.inst.map_node
		for k in 6:
			if not mp.walkable(mp.ppos):
				pass
		await wait(2.2)
		await shot("w_%s_a" % wk)
		await wait(0.55)
		await shot("w_%s_b" % wk)
		print(w, " npcs ", mp.npcs.size(), " at ", tgt.x, ",", tgt.y)
	print("T18 DONE")
	get_tree().quit()
