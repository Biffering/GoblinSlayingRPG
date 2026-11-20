extends Node
var shots_dir := "/tmp/sh"
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()
func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout
func shot(name: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [shots_dir, name])
func _run() -> void:
	for tm in [2.5, 4.0, 4.0, 3.5, 1.4, 0.95, 0.5, 1.0]:
		await wait(tm)
		await shot("i%05.1f" % Time.get_ticks_msec())
	# a battle with blood
	GS.new_game()
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	Main.inst._open_map("fire_field", 23, 30, 3)
	Main.inst.fader.alpha = 0.0
	await wait(1.0)
	Main.inst.battle([DB.make_enemy("goblin", 5, "fire"), DB.make_enemy("goblin_brute", 5, "fire")], {"bg": "fire_out", "music": "battle", "flee": true})
	await wait(1.5)
	var bb = Main.inst.battle_node
	var h = bb.party[0]
	bb.queue.append({"b": h, "act": {"type": "attack", "targets": [bb.foes[1]]}})
	h.queued = true
	await wait(0.62)
	await shot("j1_blood")
	await wait(0.4)
	await shot("j2_blood")
	print("TEST15 DONE")
	get_tree().quit()
