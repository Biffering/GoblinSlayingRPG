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
	GS.flags["hunt_active"] = {"id": "doll", "map": "wind_field", "x": 22, "y": 28, "accepted": false, "gold": 4321}
	Main.inst._open_map("wind_field", 20, 30, 3)
	Main.inst.fader.alpha = 0.0
	await wait(2.5)
	var mp = Main.inst.map_node
	var hunters = mp.npcs.filter(func(n): return n.data.get("hunter", false))
	print("hunters: ", hunters.size(), " at ", hunters.map(func(n): return n.pos))
	await shot("h0_hunters")
	# accept the hunt (what saying yes does)
	GS.flags["hunt_doll_on"] = true
	mp._ui_action("hunt_start:doll", "Nim")
	await wait(0.4)
	Input.action_press("ok"); await wait(0.1); Input.action_release("ok")
	await wait(0.6)
	var st = GS.flags.hunt_active
	print("quarry at ", st.get("bx"), ",", st.get("by"), "  bosses: ", mp.bosses.size())
	var boss = mp.bosses.filter(func(b): return str(b.data.get("kind", "")) == "hunt")[0]
	print("rewards: ", boss.data.win_do)
	mp._open_full_map()
	await wait(0.6)
	await shot("h1_map")
	mp.minimap.full = false
	mp.busy = false
	# the boss itself
	var e := DB.make_enemy("gilded_mimic", 10, "wind")
	print("mimic hp ", e.hp, " def ", e.def, " spd ", e.spd, " weak ", e.weak_el, " x", e.weak_mult)
	var q := DB.make_enemy("quickfang", 10, "wind")
	print("quickfang hp ", q.hp, " spd ", q.spd, "   ironshell spd ", DB.make_enemy("ironshell", 10, "stone").spd, " def ", DB.make_enemy("ironshell", 10, "stone").def)
	Main.inst.battle([e], {"bg": "wind_out", "music": "boss", "flee": false, "boss": true})
	await wait(2.2)
	await shot("h2_mimic")
	var res := GS.apply(boss.data.win_do)
	print("apply: ", res.map(func(r): return r.get("msg", r.get("ui", ""))))
	print("T25 DONE")
	get_tree().quit()
