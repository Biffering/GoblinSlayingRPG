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
	GS.gold = 99999
	Main.inst._open_map("fire_town", 20, 20, 0)
	Main.inst.fader.alpha = 0.0
	await wait(2.4)
	var mp = Main.inst.map_node
	mp.menu.open()
	await wait(0.2)
	var mn = mp.menu
	mn.mode = "equip_list"
	mn.sub_idx = 0
	var lst = mn._candidates("weapon")
	for i in lst.size():
		if lst[i] != null and lst[i].id == "rubedo_lancer":
			mn.list_idx = i
	await wait(0.3)
	await shot("t1_equip")
	for i in lst.size():
		if lst[i] != null and lst[i].id == "quintessence_coil":
			mn.list_idx = i
	await wait(0.2)
	await shot("t2_equip")
	mn.active = false
	mn.visible = false
	var sh = load("res://scripts/shop.gd").new()
	sh.shop_id = "pawn_fire"
	mp.ui.add_child(sh)
	await wait(0.4)
	sh.mode = "sell"
	await wait(0.2)
	var sl = sh._sellable()
	for i in sl.size():
		if sl[i].id == "rubedo_lancer":
			sh.idx = i
	await wait(0.3)
	await shot("t3_shop")
	print("T28 DONE")
	get_tree().quit()
