extends Node
func _ready() -> void:
	_run.call_deferred()
func wait(s: float) -> void:
	await get_tree().create_timer(s, true, false, true).timeout
func shot(n: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/shx/%s.png" % n)
func _run() -> void:
	await wait(0.3)
	GS.new_game()
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	print("kit: ", GS.gear.map(func(g): return g.id))
	GS.roster.hero.equip.weapon = {"id": "rubedo_lancer", "lv": 1}
	GS.roster.kael.equip.weapon = {"id": "calcined_arcblade", "lv": 1}
	var mode := OS.get_environment("MODE")
	Main.inst._open_map("fire_field", 23, 30, 3)
	Main.inst.fader.alpha = 0.0
	await wait(0.8)
	if mode == "normal":
		Main.inst.battle([DB.make_enemy("goblin_brute", 5, "fire"), DB.make_enemy("goblin", 5, "fire")], {"bg": "fire_out", "music": "battle", "flee": true})
	else:
		Main.inst.battle([DB.make_enemy("blessed_warden", 6, "fire"), DB.make_enemy("blessed_lancer", 6, "fire"), DB.make_enemy("blessed_seraph", 6, "fire")], {"bg": "fire_out", "music": "battle", "flee": true})
	await wait(2.0)
	var bb = Main.inst.battle_node
	for f in bb.foes:
		f.gauge = -100000.0
	bb.ready_list.clear()
	for p in bb.party:
		p.gauge = 0.0
	await shot("b_%s_0" % mode)
	if mode == "normal":
		bb._do_attack(bb.party[0], [bb.foes[0]])
		await wait(0.42)
		await shot("b_normal_1beam")
		await wait(0.25)
		await shot("b_normal_2")
		await wait(0.35)
		await shot("b_normal_3")
		await wait(0.5)
		await shot("b_normal_4")
		await wait(1.0)
		bb._do_attack(bb.party[1], [bb.foes[1]])
		await wait(0.55)
		await shot("b_normal_5blade")
		await wait(0.4)
		await shot("b_normal_6")
	else:
		await wait(2.0)
		await shot("b_blessed_intro")
		bb.foes[0].hp = 99999
		bb.foes[0].maxhp = 99999
		for k in 4:
			bb._do_attack(bb.party[2], [bb.foes[0]])
			await wait(0.5)
			await shot("b_blessed_tp%d" % k)
			await wait(0.7)
		bb._do_attack(bb.party[0], [bb.foes[1]])
		await wait(0.5)
		await shot("b_blessed_gun")
	print("T24 DONE")
	get_tree().quit()
