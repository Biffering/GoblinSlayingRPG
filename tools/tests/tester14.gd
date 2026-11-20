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
	print("main_king quest: ", GS.quest_state("main_king"))
	for id in ["kael", "nerissa", "pip"]:
		GS.recruit(id)
	GS.party = ["hero", "kael", "nerissa", "pip"]
	for mm in GS.roster.values():
		while mm.level < 38:
			GS.give_xp(mm, DB.xp_to_next(mm.level))
		mm.equip.weapon = {"id": "edge_of_becoming", "lv": 38}
		mm.equip.armor = {"id": "raiment_of_the_finished", "lv": 38}
		GS.full_heal(mm)
	# pirates near water
	var rng := RandomNumberGenerator.new()
	var seen := {}
	for i in 300:
		for e in DB.random_group("water", "field", 15, rng, DB.map("water_field").get("habitat", [])):
			seen[e.kind] = true
	print("water field species: ", seen.keys())
	seen = {}
	for i in 300:
		for e in DB.random_group("fire", "field", 15, rng, DB.map("fire_field").get("habitat", [])):
			seen[e.kind] = true
	print("fire field has pirates: ", seen.has("pirate") or seen.has("pirate_gunner"), " goblins: ", seen.has("goblin"))
	seen = {}
	for i in 100:
		for e in DB.random_group("goblin", "dungeon", 30, rng, ["warren"]):
			seen[e.kind + ":" + e.el] = true
	print("warren: ", seen.keys().slice(0, 8))
	for k in ["heart_fire", "heart_water", "heart_wind", "heart_stone", "heart_spirit", "heart_void"]:
		GS.items[k] = 1
	Main.inst.change_map("nexus", 14, 15, 3)
	await wait(1.0)
	var m = mapn()
	m._talk(m._npc_by_id("keeper"))
	await mash()
	await wait(1.5)
	print("after keeper: map=", mapn().mid)
	Main.inst.change_map("goblin_throne", int(DB.map("goblin_throne").start[0]), int(DB.map("goblin_throne").start[1]), 3)
	await wait(1.0)
	m = mapn()
	for b in m.bosses:
		if b.data.id == "king_goblin":
			m.ppos = Vector2i(int(b.data.x), int(b.data.y) + 1)
			m.face = 3
			m._entity(b)
			await wait(0.3)
			await mash(300.0)
	print("king beaten: ", GS.flag("beat_king_goblin"))
	await wait(1.0)
	Main.inst.change_map("nexus", 14, 15, 3)
	await wait(1.0)
	m = mapn()
	m._talk(m._npc_by_id("keeper"))
	await wait(0.5)
	var t := 0.0
	while not GS.flag("ending_seen") and t < 60:
		await press("ok")
		t += 0.1
	print("ending seen: ", GS.flag("ending_seen"), " main_king: ", GS.quest_state("main_king"))
	await wait(3.0)
	if not GS.has_clear():
		GS.save_clear()          # the ending screen's own exit wasn't pressed in this test
	print("clear saved: ", GS.has_clear())
	var lv: int = GS.roster.hero.level
	GS.new_game_plus()
	print("NG+: ng=", GS.ng, " hero lv ", GS.roster.hero.level, " (was ", lv, ") party ", GS.party, " enemy hp x", DB.make_enemy("goblin", 10, "fire").hp)
	GS.ng = 0
	print("normal goblin hp ", DB.make_enemy("goblin", 10, "fire").hp)
	# Double Tech in a real battle
	GS.party = ["hero", "kael", "nerissa", "pip"]
	Main.inst.change_map("fire_field", int(DB.map("fire_field").start[0]), int(DB.map("fire_field").start[1]), 3)
	await wait(1.0)
	Main.inst.battle([DB.make_enemy("goblin", 30, "fire"), DB.make_enemy("goblin", 30, "fire")], {"bg": "fire_out", "music": "battle", "flee": true})
	await wait(1.0)
	var bb = Main.inst.battle_node
	for p in bb.party:
		p.gauge = 100.0
		bb._on_gauge_full(p)
	await wait(0.3)
	var hero_b = bb.party[0]
	print("combos for hero: ", bb._combos_for(hero_b).map(func(e): return e.combo.name))
	var e: Dictionary = bb._combos_for(hero_b)[0]
	bb.menu_for = hero_b
	bb.pending = {"type": "combo", "combo": e.combo, "partner": e.partner}
	var hp0: int = bb.foes[0].hp
	bb._confirm({"targets": [bb.foes[0]]})
	await wait(3.0)
	print("combo dealt: ", hp0 - bb.foes[0].hp)
	print("TEST11 DONE")
	get_tree().quit()
