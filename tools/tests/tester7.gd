extends Node
## Final flow checks (headless): inn, menu item use, all six bosses' quest turn-ins, the ending, title continue.


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func press(action: String) -> void:
	await get_tree().process_frame
	Input.action_press(action)
	await get_tree().process_frame
	await get_tree().process_frame
	Input.action_release(action)
	await get_tree().process_frame


func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func mapn():
	return Main.inst.map_node


func idle() -> bool:
	var m = mapn()
	return m != null and is_instance_valid(m) and not m.dialog.active and not m.busy and not Main.inst.busy and Main.inst.battle_node == null


func mash(max_s := 40.0) -> void:
	var t := 0.0
	while t < max_s:
		var b = Main.inst.battle_node
		if b != null:
			if b.phase == "results":
				await press("ok")
			elif b.phase == "gameover":
				print("  !! lost a boss fight; retrying")
				b._finish_battle("retry")
			elif b.menu_for != null and b.menu_state == "cmd":
				decide(b)
			await get_tree().process_frame
			t += get_process_delta_time()
			continue
		if idle():
			await wait(0.2)
			if idle():
				return
		await press("ok")
		t += 0.1


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


func _run() -> void:
	Engine.time_scale = 6.0
	await wait(0.5)
	await press("ok")
	await wait(1.0)
	await mash()
	# inn at a town costs gold and heals
	var im := DB.map("water_inn")
	Main.inst.change_map("water_inn", int(im.start[0]), int(im.start[1]), 3)
	await wait(1.0)
	GS.roster.hero.hp = 1
	var g0 := GS.gold
	var m = mapn()
	m._talk(m._npc_by_id("inn_water_k"))
	await mash()
	print("inn: hp ", GS.roster.hero.hp, " gold ", g0, "->", GS.gold)
	# menu potion use
	GS.roster.hero.hp = 5
	m._open_menu()
	await wait(0.2)
	await press("ok")   # Items
	await press("ok")   # Potion
	await press("ok")   # target hero
	await wait(0.1)
	await press("back")
	await press("back")
	await press("back")
	await wait(0.3)
	print("potion via menu: hp ", GS.roster.hero.hp, " potions ", GS.items.get("potion", 0))
	# make the party strong and finish every world's main quest
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	for mm in GS.roster.values():
		while mm.level < 40:
			GS.give_xp(mm, DB.xp_to_next(mm.level))
		mm.equip.weapon = {"id": "pitbreaker", "lv": 40}
		GS.full_heal(mm)
	print("party: ", GS.party)
	var givers := {"fire": "ignatia", "water": "quill", "wind": "aloe", "stone": "marta", "spirit": "clare", "void": "ines"}
	for w in DB.d.world_order:
		var tm := DB.map(w + "_town")
		Main.inst.change_map(w + "_town", int(tm.start[0]), int(tm.start[1]), 0)
		await wait(1.0)
		m = mapn()
		m._talk(m._npc_by_id(givers[w]))
		await mash()
		var counter: Array = DB.d.world_gear[DB.beater_of(w)]
		for mm in GS.roster.values():
			var kind: int = {"hero": 0, "kael": 0, "pip": 1, "nerissa": 2}.get(mm.id, 0)
			mm.equip.weapon = {"id": counter[kind], "lv": 40}
			mm.equip.armor = {"id": DB.d.world_gear[w][3], "lv": 40}
			GS.full_heal(mm)
		GS.items["potion"] = 10
		GS.items["hi_potion"] = 5
		GS.items["feather"] = 4
		var dg := DB.map(w + "_dungeon2")
		Main.inst.change_map(w + "_dungeon2", int(dg.start[0]), int(dg.start[1]), 0)
		await wait(1.0)
		m = mapn()
		print("  in ", m.mid, " bosses: ", m.bosses.map(func(x): return [x.data.id, x.visible]), " q=", GS.quest_state("main_" + w))
		for b in m.bosses:
			if b.data.kind == "boss":
				m.ppos = Vector2i(int(b.data.x), int(b.data.y) + 1)
				m.face = 3
				m._entity(b)
				await wait(0.3)
				await mash(200.0)
				var bb = Main.inst.battle_node
				if bb:
					print("  battle state: phase=", bb.phase, " acting=", bb.acting, " ended=", bb.ended, " menu_for=", bb.menu_for, " ready=", bb.ready_list.size(), " queue=", bb.queue.size(), " foes=", bb.foes.map(func(f): return [f.name, f.hp, f.gauge, f.queued]), " party=", bb.party.map(func(p): return [p.name, p.hp, p.gauge, p.queued]))
				print("  after boss: busy=", Main.inst.busy, " in_battle=", Main.inst.in_battle, " battle=", Main.inst.battle_node, " boss_flag=", GS.flag("beat_" + str(DB.d.uniques.keys().filter(func(k): return DB.d.uniques[k].tier == "boss" and DB.d.uniques[k].el == w)[0])))
		for mm in GS.roster.values():
			GS.full_heal(mm)
		Main.inst.change_map(w + "_town", int(tm.start[0]), int(tm.start[1]), 0)
		await wait(1.0)
		m = mapn()
		m._talk(m._npc_by_id(givers[w]))
		await mash()
		print(w, ": ", GS.quest_state("main_" + w), " heart ", GS.has_item("heart_" + w))
	print("hearts: ", GS.hearts())
	# ending
	Main.inst.change_map("nexus", 14, 15, 3)
	await wait(1.0)
	m = mapn()
	m._talk(m._npc_by_id("keeper"))
	await wait(0.5)
	var t := 0.0
	while not GS.flag("ending_seen") and t < 60:
		await press("ok")
		t += 0.1
	await wait(2.0)
	t = 0.0
	while Main.inst.busy and t < 120:
		await press("ok")
		await wait(0.5)
		t += 0.5
	print("ending seen: ", GS.flag("ending_seen"), " back on map: ", mapn() != null and mapn().visible)
	# save, back to title, continue
	GS.save_game(1)
	Main.inst.goto_title()
	await wait(1.5)
	await press("down")
	await press("ok")    # Continue
	await press("down")  # slot 1
	await press("ok")
	await wait(2.0)
	print("continued into: ", mapn().mid if mapn() else "nothing", " hearts ", GS.hearts())
	print("TEST4 DONE")
	get_tree().quit()
