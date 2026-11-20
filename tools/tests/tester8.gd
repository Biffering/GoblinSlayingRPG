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


func step_exit(m, mid_to: String) -> bool:
	for e in m.m.exits:
		if e.to == mid_to:
			m.ppos = Vector2i(int(e.x), int(e.y))
			await m._after_step()
			await wait(1.2)
			return mapn().mid == mid_to
	print("  no exit ", m.mid, " -> ", mid_to)
	return false


func _run() -> void:
	Engine.time_scale = 6.0
	await wait(0.5)
	await press("ok")
	await wait(1.0)
	await mash()
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	for mm in GS.roster.values():
		while mm.level < 30:
			GS.give_xp(mm, DB.xp_to_next(mm.level))
		GS.full_heal(mm)
	GS.gold = 3000
	for w in DB.d.world_order:
		var tm := DB.map(w + "_town")
		Main.inst.change_map(w + "_town", int(tm.start[0]), int(tm.start[1]), 0)
		await wait(1.0)
		var m = mapn()
		var ok := await step_exit(m, w + "_tavern")
		m = mapn()
		var giver = null
		for n in m.npcs:
			if n.data.script.size() > 0 and str(n.data.script[0].get("do", [""])).contains("side2_"):
				giver = n
		m._talk(giver)
		await mash()
		var q: String = "side2_" + w
		print(w, ": tavern ok=", ok, " quest=", GS.quest_state(q))
		# find the side dungeon entrance
		var side_from := ""
		for mid in [w + "_house3", w + "_house4", w + "_area2"]:
			for e in DB.map(mid).exits:
				if e.to == w + "_side":
					side_from = mid
		Main.inst.change_map(side_from, int(DB.map(side_from).start[0]), int(DB.map(side_from).start[1]), 3)
		await wait(1.0)
		m = mapn()
		ok = await step_exit(m, w + "_side")
		m = mapn()
		for b in m.bosses:
			if b.data.kind == "mini" and b.visible:
				m.ppos = Vector2i(int(b.data.x), int(b.data.y) + 1)
				m.face = 3
				m._entity(b)
				await wait(0.3)
				await mash(200.0)
		print("  via ", side_from, " entered=", ok, " quest=", GS.quest_state(q))
		Main.inst.change_map(w + "_tavern", int(DB.map(w + "_tavern").start[0]), int(DB.map(w + "_tavern").start[1]), 3)
		await wait(1.0)
		m = mapn()
		var before := GS.gear.size()
		m._talk(m._npc_by_id(giver.data.id))
		await mash()
		print("  reward: quest=", GS.quest_state(q), " new gear=", GS.gear.slice(before).map(func(g): return [g.id, DB.tier(g.id)]))
		# the road: field -> area2 -> dungeon -> depths
		Main.inst.change_map(w + "_field", int(DB.map(w + "_field").start[0]), int(DB.map(w + "_field").start[1]), 3)
		await wait(1.0)
		var r1 := await step_exit(mapn(), w + "_area2")
		var r2 := await step_exit(mapn(), w + "_dungeon")
		var r3 := await step_exit(mapn(), w + "_dungeon2")
		var r4 := await step_exit(mapn(), w + "_dungeon")
		print("  road: area2=", r1, " dungeon=", r2, " depths=", r3, " back=", r4)
	# tavern shop and gear drops
	var gid := ""
	var rng := RandomNumberGenerator.new()
	var counts := {"common": 0, "rare": 0, "legendary": 0}
	for i in 2000:
		gid = DB.roll_drop("fire", "medium", rng)
		if gid != "":
			counts[DB.tier(gid)] += 1
	print("drops from 2000 medium fights: ", counts)
	print("tavern shop: ", DB.d.shops.tavern_fire.items)
	print("TEST8 DONE")
	get_tree().quit()
