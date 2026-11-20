extends Node
## Broad automated test: menus, every map, a full quest chain with a boss, summons, save/load.

var shots_dir := "/tmp/sh"


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func press(action: String, hold_frames := 2) -> void:
	await get_tree().process_frame
	Input.action_press(action)
	for i in hold_frames:
		await get_tree().process_frame
	Input.action_release(action)
	for i in 2:
		await get_tree().process_frame


func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func shot(name: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [shots_dir, name])


func mapn():
	return Main.inst.map_node


func idle() -> bool:
	var m = mapn()
	return m != null and is_instance_valid(m) and not m.dialog.active and not m.busy and not Main.inst.busy and Main.inst.battle_node == null


func mash_until_free(max_s := 30.0) -> void:
	var t := 0.0
	while t < max_s:
		if Main.inst.battle_node != null:
			await auto_battle()
		if idle():
			await wait(0.25)
			if idle():
				return
		await press("ok")
		await wait(0.05)
		t += 0.12


func auto_battle(max_s := 200.0) -> void:
	var t := 0.0
	while Main.inst.battle_node != null and t < max_s:
		var b = Main.inst.battle_node
		if b.phase == "results":
			await press("ok")
		elif b.phase == "gameover":
			print("  !! game over in auto battle")
			await press("ok")   # retry
		elif b.menu_for != null and b.menu_state == "cmd":
			decide(b)
		await wait(0.08)
		t += 0.15
	if t >= max_s:
		print("  !! auto battle timed out")


func decide(b) -> void:
	var me = b.menu_for
	var m: Dictionary = me.m
	var allies: Array = b._living(b.party)
	var foes: Array = b._living(b.foes)
	var hurt = null
	for a in allies:
		if float(a.hp) / a.maxhp < 0.4 and (hurt == null or a.hp < hurt.hp):
			hurt = a
	var dead: Array = b.party.filter(func(x): return not x.alive())
	var spells: Array = b._spells(me)
	# revive
	if dead.size() > 0:
		if "revive" in spells and me.mp >= 16:
			b.pending = {"type": "spell", "id": "revive"}
			b._confirm({"targets": [dead[0]]})
			return
		if GS.items.get("feather", 0) > 0:
			b.pending = {"type": "item", "id": "feather"}
			b._confirm({"targets": [dead[0]]})
			return
	if hurt != null:
		for sid in ["rain_of_mercy", "soothe", "mend"]:
			if sid in spells and me.mp >= int(DB.d.spells[sid].mp):
				b.pending = {"type": "spell", "id": sid}
				b._confirm({"targets": allies if sid == "rain_of_mercy" else [hurt]})
				return
		for it in ["hi_potion", "potion"]:
			if GS.items.get(it, 0) > 0:
				b.pending = {"type": "item", "id": it}
				b._confirm({"targets": [hurt]})
				return
	if me.limit >= 100.0:
		b.pending = {"type": "limit"}
		b._confirm({"targets": [foes[0]]})
		return
	# summon if it would hit several foes
	if GS.summons.size() > 0 and foes.size() >= 2:
		for sid in GS.summons:
			if me.mp >= int(DB.d.summons[sid].mp) + 10:
				b.pending = {"type": "summon", "id": sid}
				b._confirm({"targets": []})
				return
	# exploit weakness with spells
	var tgt = foes[0]
	for f in foes:
		if f.hp < tgt.hp:
			tgt = f
	var best := ""
	var best_score := 0.0
	for sid in spells:
		var sp: Dictionary = DB.d.spells[sid]
		if sp.kind not in ["dmg", "hex", "drain"] or me.mp < int(sp.mp) + 4:
			continue
		var mult: float = DB.el_mult(sp.el, tgt.el)
		var score: float = mult * float(sp.power) * (foes.size() * 0.75 if sp.target == "all" else 1.0)
		if mult >= 1.5 or (tgt.e.get("sprite", "").begins_with("ghost") or tgt.id == "ghost"):
			score *= 1.5
		if score > best_score and score >= 1.4:
			best_score = score
			best = sid
	if best != "":
		var sp: Dictionary = DB.d.spells[best]
		b.pending = {"type": "spell", "id": best}
		b._confirm({"targets": foes if sp.target == "all" else [tgt]})
		return
	b.pending = {"type": "attack"}
	b._confirm({"targets": [tgt]})


func goto(mid: String, x: int, y: int) -> void:
	Main.inst.change_map(mid, x, y, 0)
	await wait(0.9)


func talk(id: String) -> void:
	var m = mapn()
	var n = m._npc_by_id(id)
	if n == null:
		print("  !! npc missing ", id)
		return
	m._talk(n)
	await wait(0.2)
	await mash_until_free()


func fight_entity(id: String) -> void:
	var m = mapn()
	for b in m.bosses:
		if b.data.id == id:
			if not b.visible:
				print("  !! entity hidden ", id)
				return
			# stand next to it facing it
			m.ppos = Vector2i(int(b.data.x), int(b.data.y) + 1)
			m.player.position = m._tile_px(m.ppos)
			m.face = 3
			m._entity(b)
			await wait(0.3)
			await mash_until_free(240.0)
			return
	print("  !! entity not found ", id)


func cheat_party(level: int) -> void:
	for id in ["kael", "nerissa", "pip"]:
		if not GS.roster.has(id):
			GS.recruit(id)
	for m in GS.roster.values():
		while m.level < level:
			GS.give_xp(m, DB.xp_to_next(m.level))
		var wg: Array = DB.d.world_gear["water"]
		var kind: int = {"hero": 0, "kael": 0, "pip": 1, "nerissa": 2}.get(m.id, 0)
		m.equip.weapon = {"id": wg[kind], "lv": level}
		m.equip.armor = {"id": wg[3], "lv": level}
		GS.full_heal(m)
	GS.items["potion"] = 8
	GS.items["hi_potion"] = 4
	GS.items["feather"] = 3


func _run() -> void:
	await wait(0.8)
	await press("ok")
	await wait(1.5)
	await mash_until_free()
	print("intro done, flags: ", GS.flags.keys())
	await press("right", 8)
	await wait(0.3)
	# ---- menus
	await press("back")
	await wait(0.4)
	await shot("m01_menu")
	await press("ok")   # Items
	await wait(0.2)
	await shot("m02_items")
	await press("back")
	await press("down")
	await press("down")  # Equip
	await press("ok")
	await press("ok")
	await wait(0.2)
	await shot("m03_equip")
	await press("back")
	await press("back")
	await press("down")  # Status
	await press("ok")
	await press("ok")
	await wait(0.2)
	await shot("m04_status")
	await press("back")
	await press("back")
	for k in 3:
		await press("down")  # Quests
	await press("ok")
	await wait(0.2)
	await shot("m05_quests")
	await press("back")
	for k in 2:
		await press("down")  # Config
	await press("ok")
	await wait(0.2)
	await shot("m06_config")
	await press("back")
	await press("down")  # Save
	await press("ok")
	await press("ok")
	await wait(0.3)
	await shot("m07_save")
	await press("back")
	await press("back")
	await wait(0.5)
	print("saved slot1: ", not GS.slot_summary(1).is_empty())
	# ---- visit every map
	for w in DB.d.world_order:
		for kind in ["town", "field", "cave", "dungeon", "sanctum"]:
			var mid: String = "%s_%s" % [w, kind]
			if not FileAccess.file_exists("res://data/maps/%s.json" % mid):
				continue
			var md := DB.map(mid)
			await goto(mid, int(md.start[0]), int(md.start[1]))
			if kind in ["town", "dungeon"] or (kind == "field" and w in ["wind", "void"]):
				await shot("v_%s" % mid)
	print("visited all maps")
	# ---- full fire quest chain with a strong party
	cheat_party(14)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	await goto("fire_town", 16, 9)
	await talk("ignatia")
	print("main_fire: ", GS.quest_state("main_fire"))
	await talk("tamsin")
	await talk("hesta")
	print("side_fire: ", GS.quest_state("side_fire"), " key_fire: ", GS.quest_state("key_fire"))
	var dg := DB.map("fire_dungeon")
	await goto("fire_dungeon", int(dg.start[0]), int(dg.start[1]))
	await shot("q01_dungeon")
	await fight_entity("vulkar")
	print("beat_vulkar: ", GS.flag("beat_vulkar"), " main_fire: ", GS.quest_state("main_fire"))
	await shot("q02_after_boss")
	await goto("fire_town", 16, 9)
	await talk("ignatia")
	print("main_fire: ", GS.quest_state("main_fire"), " heart: ", GS.has_item("heart_fire"), " hearts: ", GS.hearts())
	# side quest miniboss in field
	var fd := DB.map("fire_field")
	await goto("fire_field", int(fd.start[0]), int(fd.start[1]))
	await fight_entity("scrapjack")
	print("bellows: ", GS.has_item("forge_bellows"))
	await goto("fire_town", 16, 9)
	await talk("tamsin")
	print("side_fire: ", GS.quest_state("side_fire"))
	# cave: companion quest + summon chest + key item
	if not GS.roster.has("kael"):
		print("  !! kael missing")
	var cv := DB.map("fire_cave")
	await goto("fire_cave", int(cv.start[0]), int(cv.start[1]))
	var m = mapn()
	for c in m.chests:
		m.ppos = Vector2i(int(c.data.x), int(c.data.y) + 1)
		m.face = 3
		m._open_chest(c)
		await wait(0.2)
		await mash_until_free()
	print("summons: ", GS.summons, " hammer: ", GS.has_item("hestas_hammer"))
	GS.quests["comp_fire"] = "active"
	await fight_entity("slagjaw")
	print("comp_fire: ", GS.quest_state("comp_fire"))
	# ---- summon in battle
	GS.roster.hero.mp = 999
	var enemies := DB.random_group("fire", "dungeon", GS.avg_level(), RandomNumberGenerator.new())
	Main.inst.battle(enemies, {"bg": "fire_in", "music": "battle", "flee": true})
	await wait(2.0)
	var t := 0.0
	while Main.inst.battle_node != null and t < 20:
		var b = Main.inst.battle_node
		if b.menu_for != null and b.menu_for.id == "hero" and b.menu_state == "cmd":
			b.cmd_idx = 2
			await press("ok")
			await wait(0.2)
			await shot("b01_summon_menu")
			await press("ok")
			await wait(1.0)
			await shot("b02_summon")
			break
		elif b.menu_for != null:
			await press("ok")
		await wait(0.1)
		t += 0.1
	await auto_battle()
	# ---- riddle treasure
	await goto("fire_field", int(fd.start[0]), int(fd.start[1]))
	m = mapn()
	var h: Dictionary = m.m.hidden[0]
	m.ppos = Vector2i(int(h.x), int(h.y))
	m._dig(h)
	await wait(0.2)
	await mash_until_free()
	print("riddle treasure found: ", GS.flag("hidden_fire"))
	# ---- spirit seal: needs keys
	GS.items["key_memory"] = 1
	GS.items["key_breath"] = 1
	var sd := DB.map("spirit_dungeon")
	await goto("spirit_dungeon", int(sd.start[0]), int(sd.start[1]))
	await fight_entity("seal_spirit")
	await wait(1.5)
	print("sanctum map: ", mapn().mid if mapn() else "?")
	cheat_party(32)
	await fight_entity("aeon")
	print("beat_aeon: ", GS.flag("beat_aeon"), " summons: ", GS.summons)
	await shot("q03_after_omni")
	print("save: ", GS.save_game(2), " load: ", GS.load_game(2))
	print("TEST2 DONE")
	get_tree().quit()
