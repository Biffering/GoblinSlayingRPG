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
	Main.inst.goto_title()
	await wait(1.5)
	await shot("u0_title")
	GS.new_game()
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	Main.inst._open_map("fire_town", 20, 20, 0)
	Main.inst.fader.alpha = 0.0
	await wait(3.0)
	var mp = Main.inst.map_node
	mp.dialog.say(["The goblins came down from the ridge at night. Nobody in Emberfall sleeps anymore."], "Elder")
	await wait(1.5)
	await shot("u1_dialog")
	Input.action_press("ui_accept")
	await wait(0.1)
	Input.action_release("ui_accept")
	await wait(0.5)
	mp.menu.open()
	await wait(0.6)
	await shot("u2_menu")
	mp.menu.visible = false
	var sh = load("res://scripts/shop.gd").new()
	sh.shop_id = "pawn_fire"
	mp.ui.add_child(sh)
	await wait(0.5)
	sh.mode = "buy"
	await wait(0.4)
	await shot("u4_shop")
	sh.queue_free()
	Main.inst.battle([DB.make_enemy("goblin", 5, "fire"), DB.make_enemy("goblin_brute", 5, "fire")], {"bg": "fire_out", "music": "battle", "flee": true})
	await wait(2.5)
	await shot("u3_battle")
	var bb = Main.inst.battle_node
	var h = bb.party[0]
	bb.queue.append({"b": h, "act": {"type": "attack", "targets": [bb.foes[1]]}})
	h.queued = true
	await wait(0.7)
	await shot("u5_hit")
	print("T17 DONE")
	get_tree().quit()
