extends Node
func _ready() -> void:
	_run.call_deferred()
func wait(s: float) -> void:
	await get_tree().create_timer(s, true, false, true).timeout
func shot(n: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/shx/%s.png" % n)
func fight(world: String, el_enemy: String, sid: String, tag: String) -> void:
	Main.inst._open_map(world + "_field", 20, 20, 0)
	Main.inst.fader.alpha = 0.0
	await wait(0.8)
	var e1 := DB.make_enemy("goblin_brute", 8, el_enemy)
	var e2 := DB.make_enemy("goblin", 8, el_enemy)
	e1.hp = 1
	e2.hp = 1
	Main.inst.battle([e1, e2], {"bg": "%s_out" % world, "music": "battle", "flee": true})
	await wait(2.2)
	var bb = Main.inst.battle_node
	bb.ready_list.clear()
	for p in bb.party:
		p.gauge = 0.0
	for f in bb.foes:
		f.gauge = -100000.0
	var h = bb.party[0]
	# a heavy sword blow on the second goblin first
	bb._do_attack(h, [bb.foes[1]], 3.0)
	await wait(0.55)
	await shot("x_%s_0hit" % tag)
	await wait(1.0)
	bb._do_spell(h, sid, [bb.foes[0]], false)
	await wait(0.8)
	await shot("x_%s_1boom" % tag)
	await wait(0.3)
	await shot("x_%s_2" % tag)
	await wait(0.3)
	await shot("x_%s_3" % tag)
	await wait(0.35)
	await shot("x_%s_4" % tag)
	await wait(5.0)
	# leave the results screen
	for k in 6:
		var ev := InputEventKey.new(); ev.physical_keycode = KEY_Z; ev.pressed = true
		Input.parse_input_event(ev)
		await wait(0.1)
		ev = ev.duplicate(); ev.pressed = false
		Input.parse_input_event(ev)
		await wait(0.5)
func _run() -> void:
	await wait(0.3)
	GS.new_game()
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	var spec := OS.get_environment("EL").split(",")
	await fight(spec[0], spec[0], spec[1], spec[2])
	print("T21 DONE")
	get_tree().quit()
