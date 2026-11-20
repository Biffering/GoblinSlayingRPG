extends Node
## Headless balance simulator: plays many battles with a sensible AI and reports win rates.

var results := {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func setup_party(ids: Array, level: int, world: String) -> void:
	GS.new_game()
	for id in ids:
		if id != "hero":
			GS.recruit(id)
	GS.party = ids.duplicate()
	var wg: Array = DB.d.world_gear[world]
	for id in ids:
		var m: Dictionary = GS.roster[id]
		while m.level < level:
			GS.give_xp(m, DB.xp_to_next(m.level))
		# sensible shop gear from a world whose element beats this one, like a player who planned ahead
		var beat := DB.beater_of(world)
		var bg: Array = DB.d.world_gear[beat]
		var kind: int = {"hero": 0, "kael": 0, "durga": 0, "pip": 1, "vesper": 1, "nerissa": 2, "sol": 2}[id]
		m.equip.weapon = {"id": bg[kind], "lv": level}
		m.equip.armor = {"id": wg[3], "lv": level}
		m.equip.acc = {"id": "hearth_pendant" if id == "hero" else wg[4], "lv": level}
		GS.full_heal(m)
	GS.items = {"potion": 6, "hi_potion": 2, "ether": 2, "feather": 2}


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


func fight(enemies: Array, bg: String, flee := false) -> Dictionary:
	var before_hp := 0
	for m in GS.active_members():
		before_hp += m.hp
	GS.snapshot()
	Main.inst.battle(enemies, {"bg": bg, "music": "battle", "flee": flee})
	var w0 := 0.0
	while Main.inst.battle_node == null and w0 < 10.0:
		await wait(0.05)
		w0 += 0.05
	var t := 0.0
	var turns := 0
	var res := "timeout"
	while t < 400.0:
		var b = Main.inst.battle_node
		if b == null:
			break
		if b.phase == "results":
			res = "win"
			Input.action_press("ok")
			await get_tree().process_frame
			await get_tree().process_frame
			Input.action_release("ok")
		elif b.phase == "gameover":
			res = "lose"
			b._finish_battle("title_sim")
			break
		elif b.menu_for != null and b.menu_state == "cmd":
			decide(b)
			turns += 1
		await get_tree().process_frame
		t += get_process_delta_time()
	# wait for main to clean up
	var w := 0.0
	while (Main.inst.battle_node != null or Main.inst.in_battle or Main.inst.busy) and w < 10.0:
		await wait(0.1)
		w += 0.1
	Main.inst.busy = false
	var after_hp := 0
	for m in GS.active_members():
		after_hp += max(0, m.hp)
	return {"res": res, "turns": turns, "hp_lost": before_hp - after_hp}


func _run() -> void:
	Engine.time_scale = 10.0
	await wait(1.0)
	# need a map underneath for Main.battle
	GS.new_game()
	Main.inst._open_map("nexus", 14, 15, 0)
	await wait(0.5)
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	var scenarios := [
		["L1 solo field", ["hero"], 1, "fire", "field", 8],
		["L3 duo field", ["hero", "kael"], 3, "water", "field", 8],
		["L6 trio cave", ["hero", "kael", "nerissa"], 6, "wind", "cave", 8],
		["L10 quad dungeon", ["hero", "kael", "nerissa", "pip"], 10, "stone", "dungeon", 8],
		["L18 quad dungeon", ["hero", "kael", "nerissa", "pip"], 18, "void", "dungeon", 6],
	]
	for sc in scenarios:
		var wins := 0
		var tot_turns := 0
		var lost := 0
		for i in sc[5]:
			setup_party(sc[1], sc[2], sc[3])
			GS.location.map = "nexus"
			var en := DB.random_group(sc[3], sc[4], GS.avg_level(), rng)
			var r: Dictionary = await fight(en, "%s_out" % sc[3])
			if r.res == "win":
				wins += 1
			tot_turns += r.turns
			lost += r.hp_lost
		print("%-18s wins %d/%d  avg party turns %.1f  avg HP lost %d" % [sc[0], wins, sc[5], float(tot_turns) / sc[5], lost / sc[5]])
	# bosses and minibosses
	var bosses := [["slagjaw", "fire", 8, ["hero", "kael", "nerissa"]], ["gloomfin", "water", 8, ["hero", "kael", "nerissa"]],
				   ["vulkar", "fire", 12, ["hero", "kael", "nerissa", "pip"]], ["maren", "water", 14, ["hero", "kael", "nerissa", "pip"]],
				   ["corvane", "wind", 16, ["hero", "kael", "nerissa", "pip"]], ["ostrum", "stone", 18, ["hero", "kael", "nerissa", "pip"]],
				   ["iris", "spirit", 20, ["hero", "kael", "nerissa", "pip"]], ["nobody", "void", 22, ["hero", "kael", "nerissa", "pip"]],
				   ["aeon", "spirit", 30, ["hero", "kael", "nerissa", "pip"]], ["nihil", "void", 32, ["hero", "kael", "nerissa", "pip"]]]
	for bs in bosses:
		var wins := 0
		var turns := 0
		var n := 3
		for i in n:
			setup_party(bs[3], bs[2], bs[1])
			if bs[0] in ["aeon", "nihil"]:
				GS.summons = ["pyrestag", "marrowhale", "lanternmoth"]
				GS.items["elixir"] = 3
			var e := DB.make_enemy(bs[0], GS.avg_level(), bs[1])
			var r: Dictionary = await fight([e], "%s_in" % bs[1])
			if r.res == "win":
				wins += 1
			turns += r.turns
		print("%-10s L%-2d wins %d/%d  avg party turns %.1f" % [bs[0], bs[2], wins, n, float(turns) / n])
	print("SIM DONE")
	get_tree().quit()
