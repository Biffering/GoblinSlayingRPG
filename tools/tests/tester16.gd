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
	await wait(0.5)
	GS.new_game()
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	var i := 0
	for spot in [["fire_town", 20, 20], ["fire_field", 23, 30], ["water_field", 20, 20]]:
		Main.inst._open_map(spot[0], spot[1], spot[2], 0)
		Main.inst.fader.alpha = 0.0
		await wait(1.0)
		await shot("z%d" % i)
		i += 1
	print("T16 DONE")
	get_tree().quit()
