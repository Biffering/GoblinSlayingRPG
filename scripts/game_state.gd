extends Node
## Everything that changes during play: party, inventory, quests, flags, location. Saved to user://.

signal changed

const MAX_PARTY := 4
const BOOST_BATTLES := 5
var ng := 0                       # New Game+ cycle (0 = first playthrough)
const CLEAR_PATH := "user://goblin_slayer_clear.json"
var weather: Dictionary = {}      # {"kind", "t", "dur", "world"}: changes over time outdoors
var weather_on := false           # true on outdoor maps (towns and wilds)
var weather_world := ""

var roster: Dictionary = {}       # id -> member dictionary
var party: Array = []             # active member ids, in order (hero first)
var items: Dictionary = {}        # consumable + key item id -> count
var gear: Array = []              # unequipped gear instances {id, lv}
var gold: int = 0
var flags: Dictionary = {}
var quests: Dictionary = {}       # id -> "active" | "done"
var summons: Array = []
var location := {"map": "nexus", "x": 14, "y": 15, "face": 3}
var play_time: float = 0.0
var steps: int = 0
var settings := {"battle_mode": "wait", "text_speed": 1, "music": 0.8, "sfx": 0.9, "minimap": true, "auto_run": false}
var _snapshot: Dictionary = {}
var started := false


func _process(delta: float) -> void:
	if started:
		play_time += delta


# ------------------------------------------------------------------ new game

func new_game() -> void:
	roster.clear()
	party.clear()
	items.clear()
	gear.clear()
	flags.clear()
	quests.clear()
	summons.clear()
	gold = 150
	play_time = 0.0
	steps = 0
	add_member("hero", 1)
	var h: Dictionary = roster.hero
	h.equip.weapon = {"id": "driftwood_sword", "lv": 1}
	h.equip.armor = {"id": "travel_coat", "lv": 1}
	h.equip.acc = {"id": "hearth_pendant", "lv": 1}
	full_heal(h)
	location = {"map": "nexus", "x": 14, "y": 15, "face": 3}
	started = true
	changed.emit()


## A stash of Blessed weapons to practice with: enough laser blades, guns and staffs to arm the whole party.
## Given once per save, new or old.
const BLESSED_STASH := ["azoth_edge", "calcined_arcblade", "quicksilver_saber", "azoth_edge",
	"rubedo_lancer", "albedo_repeater", "nigredo_pistol", "cinnabar_pistol",
	"quintessence_coil", "athanor_staff", "quintessence_coil", "athanor_staff"]


## Saves made under the game's earlier working titles are copied across once.
func _migrate_old_saves() -> void:
	var names := ["settings", "clear"]
	for i in range(0, 10):
		names.append(str(i))
	for n in names:
		var new := "user://goblin_slayer_%s.json" % n
		for prefix in ["six_hearths", "demon_slayer"]:
			var old := "user://%s_%s.json" % [prefix, n]
			if FileAccess.file_exists(old) and not FileAccess.file_exists(new):
				DirAccess.copy_absolute(old, new)


func grant_blessed_stash() -> void:
	if flags.get("blessed_stash", false):
		return
	for gid in BLESSED_STASH:
		if DB.d.gear.has(gid):
			gear.append({"id": gid, "lv": max(1, avg_level())})
	flags["blessed_stash"] = true


func add_member(cid: String, level: int) -> Dictionary:
	var m := {"id": cid, "level": level, "xp": 0, "hp": 1, "mp": 0, "limit": 0.0,
			  "equip": {"weapon": null, "armor": null, "acc": null}, "boosts": {}}
	roster[cid] = m
	if party.size() < MAX_PARTY and not party.has(cid):
		party.append(cid)
	full_heal(m)
	return m


func recruit(cid: String) -> void:
	if roster.has(cid):
		return
	var lv: int = max(1, roster.hero.level - 1)
	var m := add_member(cid, lv)
	# companions arrive with gear of their own world at their level
	var w: String = DB.d.characters[cid].world
	var wg: Array = DB.d.world_gear[w]
	var best := {"kael": 0, "durga": 0, "pip": 1, "vesper": 1, "nerissa": 2, "sol": 2}
	m.equip.weapon = {"id": wg[best[cid]], "lv": lv}
	m.equip.armor = {"id": wg[3], "lv": lv}
	full_heal(m)
	changed.emit()


# ------------------------------------------------------------------ stats

func elements_of(m: Dictionary) -> Array:
	## Elements from equipped gear, in slot order (weapon, armor, accessory).
	var out := []
	for slot in ["weapon", "armor", "acc"]:
		var inst = m.equip[slot]
		if inst != null:
			var el = DB.d.gear[inst.id].el
			if el != null and el != "":
				out.append(el)
	return out


func aura_colors(m: Dictionary) -> Array:
	var els := elements_of(m)
	var uniq := []
	for e in els:
		if not uniq.has(e):
			uniq.append(e)
	if uniq.is_empty():
		var inn = DB.d.characters[m.id].innate
		if inn != null:
			uniq.append(inn)
	return uniq


func aura_strength(m: Dictionary) -> float:
	return clampf(0.35 + float(m.level) * 0.024, 0.35, 1.0)


func aura_radius(m: Dictionary) -> float:
	return clampf(1.0 + floor(float(m.level) / 9.0), 1.0, 4.0)


func hero_tier() -> int:
	var lv: int = roster.hero.level if roster.has("hero") else 1
	if lv >= 25:
		return 3
	if lv >= 16:
		return 2
	if lv >= 8:
		return 1
	return 0


func spell_elements(m: Dictionary) -> Array:
	var els := []
	for e in elements_of(m):
		if not els.has(e):
			els.append(e)
	var inn = DB.d.characters[m.id].innate
	if inn != null and not els.has(inn):
		els.append(inn)
	return els


func element_pieces(m: Dictionary, el: String) -> int:
	var n := 0
	for e in elements_of(m):
		if e == el:
			n += 1
	if DB.d.characters[m.id].innate == el:
		n += 1
	return n


func stats(m: Dictionary) -> Dictionary:
	var c: Dictionary = DB.d.characters[m.id]
	var lv := float(m.level - 1)
	var s := {}
	for k in DB.STATS:
		s[k] = float(c.base[k]) + float(c.grow[k]) * lv
	var pct := {}
	s["atk"] = 0.0
	s["matk"] = 0.0
	s["wdef"] = 0.0
	s["wmdef"] = 0.0
	for slot in ["weapon", "armor", "acc"]:
		var inst = m.equip[slot]
		if inst == null:
			continue
		var gs := DB.gear_stats(inst, int(m.level))
		for k in gs:
			s[k] += float(gs[k])
		var b: Dictionary = DB.d.gear[inst.id].bonus
		for k in b:
			pct[k] = pct.get(k, 0.0) + float(b[k])
	for k in pct:
		s[k] *= 1.0 + pct[k]
	# special effects from gear (crit, mp_hit, regen, ...)
	var fx := {}
	for slot in ["weapon", "armor", "acc"]:
		var inst = m.equip[slot]
		if inst == null:
			continue
		var gf: Dictionary = DB.d.gear[inst.id].get("fx", {})
		for k in gf:
			fx[k] = fx.get(k, 0.0) + float(gf[k])
	s["fx"] = fx
	for k in m.boosts:
		var v := 0.3
		if k == "def":
			s["def"] *= 1.0 + v
			s["mdef"] *= 1.0 + v
		else:
			s[k] *= 1.0 + v
	for k in DB.STATS:
		s[k] = int(round(s[k]))
	s["maxhp"] = s.hp
	s["maxmp"] = s.mp
	var w = m.equip.weapon
	s["wkind"] = DB.d.gear[w.id].kind if w != null else "blade"
	s["wel"] = DB.d.gear[w.id].el if w != null else null
	# resistances from armor & accessory elements
	var res := {}
	for slot in ["armor", "acc"]:
		var inst = m.equip[slot]
		if inst == null:
			continue
		var el = DB.d.gear[inst.id].el
		if el == null:
			continue
		res[el] = res.get(el, 0.0) + 0.2
		var bt := DB.beater_of(el)
		res[bt] = res.get(bt, 0.0) - 0.15
	s["res"] = res
	return s


func full_heal(m: Dictionary) -> void:
	var s := stats(m)
	m.hp = s.maxhp
	m.mp = s.maxmp


func clamp_member(m: Dictionary) -> void:
	var s := stats(m)
	m.hp = clampi(m.hp, 0, s.maxhp)
	m.mp = clampi(m.mp, 0, s.maxmp)


func active_members() -> Array:
	return party.map(func(id): return roster[id])


func avg_level() -> int:
	var t := 0.0
	for id in party:
		t += roster[id].level
	return max(1, int(round(t / max(1, party.size()))))


## Adds xp to a member; returns an array of {level, gains} for each level gained.
func give_xp(m: Dictionary, amount: int) -> Array:
	var ups := []
	m.xp += amount
	while m.xp >= DB.xp_to_next(m.level):
		m.xp -= DB.xp_to_next(m.level)
		var before := stats(m)
		m.level += 1
		var after := stats(m)
		var gains := {}
		for k in DB.STATS:
			gains[k] = after[k] - before[k]
		m.hp += gains.hp
		m.mp += gains.mp
		ups.append({"level": m.level, "gains": gains})
	return ups


func tick_boosts() -> void:
	for m in roster.values():
		for k in m.boosts.keys():
			m.boosts[k] -= 1
			if m.boosts[k] <= 0:
				m.boosts.erase(k)


# ------------------------------------------------------------------ inventory

func add_item(spec: String) -> String:
	## spec: "potion", "potion:2", "gear:cinder_blade", "summon:pyrestag". Returns a message.
	var parts := spec.split(":")
	if parts[0] == "gear":
		var inst := {"id": parts[1], "lv": item_level(parts[1])}
		gear.append(inst)
		return DB.gear_label(inst)
	if parts[0] == "summon":
		if not summons.has(parts[1]):
			summons.append(parts[1])
		return "the Summon Stone of %s" % DB.d.summons[parts[1]].name
	var n := 1
	if parts.size() > 1:
		n = int(parts[1])
	if DB.is_gear(parts[0]):
		for i in n:
			gear.append({"id": parts[0], "lv": item_level(parts[0])})
		return DB.d.gear[parts[0]].name
	items[parts[0]] = items.get(parts[0], 0) + n
	var nm: String = DB.info(parts[0]).name
	return nm if n == 1 else "%s x%d" % [nm, n]


func item_level(_gid: String) -> int:
	## Found gear scales with the party's strength.
	return avg_level()


func take_item(id: String, n: int = 1) -> void:
	if items.has(id):
		items[id] -= n
		if items[id] <= 0:
			items.erase(id)


func has_item(id: String) -> bool:
	if items.get(id, 0) > 0:
		return true
	for g in gear:
		if g.id == id:
			return true
	return false


func equip(m: Dictionary, slot: String, inst) -> void:
	var old = m.equip[slot]
	if inst != null:
		gear.erase(inst)
	if old != null:
		gear.append(old)
	m.equip[slot] = inst
	clamp_member(m)
	changed.emit()


# ------------------------------------------------------------------ quests / flags / conditions

func flag(f: String) -> bool:
	return flags.get(f, false)


func quest_state(qid: String) -> String:
	var st: String = quests.get(qid, "none")
	if st == "active":
		var obj: String = DB.d.quests[qid].objective
		var p := obj.split(":")
		if (p[0] == "flag" and flag(p[1])) or (p[0] == "item" and has_item(p[1])):
			return "ready"
	return st


func hearts() -> int:
	var n := 0
	for w in DB.d.world_order:
		if has_item("heart_" + w):
			n += 1
	return n


func check(conds: Array) -> bool:
	for c in conds:
		if not check_one(str(c)):
			return false
	return true


func check_one(c: String) -> bool:
	var neg := c.begins_with("!")
	if neg:
		c = c.substr(1)
	var ok := false
	if c.begins_with("flag:"):
		ok = flag(c.substr(5))
	elif c.begins_with("item:"):
		ok = has_item(c.substr(5))
	elif c.begins_with("member:"):
		ok = roster.has(c.substr(7))
	elif c.begins_with("q:"):
		var p := c.substr(2).split("=")
		ok = quest_state(p[0]) == p[1]
	elif c.begins_with("party>="):
		ok = party.size() >= int(c.substr(7))
	elif c.begins_with("hearts>="):
		ok = hearts() >= int(c.substr(8))
	return ok != neg


## Applies state actions. Returns a list of {"msg": text} / {"ui": action} for the caller to show or handle.
func apply(actions: Array) -> Array:
	var out := []
	for a in actions:
		var s := str(a)
		var i := s.find(":")
		var k := s if i < 0 else s.substr(0, i)
		var v := "" if i < 0 else s.substr(i + 1)
		match k:
			"set":
				flags[v] = true
			"clear":
				flags.erase(v)
			"give":
				var got := add_item(v)
				out.append({"msg": "Received %s!" % got, "sfx": "chest"})
			"take":
				var p := v.split(":")
				if DB.is_gear(p[0]):
					for g in gear:
						if g.id == p[0]:
							gear.erase(g)
							break
				else:
					take_item(p[0])
			"gold":
				gold += int(v)
				out.append({"msg": "Received %d gold." % int(v), "sfx": "coins"})
			"quest":
				if not quests.has(v):
					quests[v] = "active"
					out.append({"msg": "New quest: %s" % DB.d.quests[v].title, "sfx": "quest"})
			"done":
				if quests.get(v, "") != "done":
					quests[v] = "done"
					out.append({"msg": "Quest complete: %s" % DB.d.quests[v].title, "sfx": "quest_done"})
			"recruit":
				recruit(v)
				if not party.has(v):
					out.append({"msg": "%s is waiting at the Nexus. (Your party is full; use Formation.)" % DB.d.characters[v].name})
			"summon":
				if not summons.has(v):
					summons.append(v)
			"heal":
				for m in roster.values():
					full_heal(m)
			_:
				out.append({"ui": s})
	changed.emit()
	return out


# ------------------------------------------------------------------ snapshots (battle retry) & saving

func to_dict() -> Dictionary:
	return {"roster": roster, "party": party, "items": items, "gear": gear, "gold": gold, "flags": flags,
			"quests": quests, "summons": summons, "location": location, "play_time": play_time, "steps": steps,
			"settings": settings, "version": 1, "ng": ng}


func from_dict(d: Dictionary) -> void:
	ng = int(d.get("ng", 0))
	roster = d.roster
	party = d.party
	items = d.items
	gear = d.gear
	gold = int(d.gold)
	flags = d.flags
	quests = d.quests
	summons = d.summons
	location = d.location
	play_time = float(d.play_time)
	steps = int(d.get("steps", 0))
	settings.merge(d.get("settings", {}), true)
	# JSON turns ints into floats; normalise the numbers we compare
	for m in roster.values():
		m.level = int(m.level)
		m.xp = int(m.xp)
		m.hp = int(m.hp)
		m.mp = int(m.mp)
		for slot in m.equip:
			if m.equip[slot] != null:
				m.equip[slot].lv = int(m.equip[slot].lv)
		for k in m.boosts:
			m.boosts[k] = int(m.boosts[k])
	for g in gear:
		g.lv = int(g.lv)
	for k in items:
		items[k] = int(items[k])
	location.x = int(location.x)
	location.y = int(location.y)

	location.face = int(location.face)
	started = true
	changed.emit()


func snapshot() -> void:
	_snapshot = to_dict().duplicate(true)


func restore_snapshot() -> void:
	if not _snapshot.is_empty():
		from_dict(_snapshot.duplicate(true))


func save_path(slot: int) -> String:
	return "user://goblin_slayer_%d.json" % slot


func save_game(slot: int) -> bool:
	var f := FileAccess.open(save_path(slot), FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(to_dict()))
	return true


func load_game(slot: int) -> bool:
	if not FileAccess.file_exists(save_path(slot)):
		return false
	var f := FileAccess.open(save_path(slot), FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text())
	if typeof(d) != TYPE_DICTIONARY:
		return false
	from_dict(d)
	return true


func slot_summary(slot: int) -> Dictionary:
	if not FileAccess.file_exists(save_path(slot)):
		return {}
	var f := FileAccess.open(save_path(slot), FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text())
	if typeof(d) != TYPE_DICTIONARY:
		return {}
	var lv := int(d.roster.hero.level)
	var mp: String = d.location.map
	var nm := mp
	if FileAccess.file_exists("res://data/maps/%s.json" % mp):
		nm = DB.map(mp).name
	var heart_count := 0
	for w in DB.d.world_order:
		if d.items.has("heart_" + w):
			heart_count += 1
	return {"level": lv, "place": nm, "time": float(d.play_time), "hearts": heart_count, "party": d.party}


func load_settings() -> void:
	_migrate_old_saves()
	if FileAccess.file_exists("user://goblin_slayer_settings.json"):
		var f := FileAccess.open("user://goblin_slayer_settings.json", FileAccess.READ)
		var d = JSON.parse_string(f.get_as_text())
		if typeof(d) == TYPE_DICTIONARY:
			settings.merge(d, true)


## After the credits: keep the party's levels, gear, items, gold and summons for New Game+.
func save_clear() -> void:
	var d := {"roster": roster, "gear": gear, "items": items, "gold": gold, "summons": summons, "ng": ng + 1,
			  "party": party}
	var f := FileAccess.open(CLEAR_PATH, FileAccess.WRITE)
	f.store_string(JSON.stringify(d))


func has_clear() -> bool:
	return FileAccess.file_exists(CLEAR_PATH)


func new_game_plus() -> void:
	# no cleared game on record (or an unreadable one): just start fresh
	var fa := FileAccess.open(CLEAR_PATH, FileAccess.READ)
	var parsed = JSON.parse_string(fa.get_as_text()) if fa != null else null
	if not (parsed is Dictionary) or not parsed.has("roster"):
		new_game()
		return
	var d: Dictionary = parsed
	new_game()
	ng = int(d.get("ng", 1))
	roster = d.roster
	for id in roster:
		var m: Dictionary = roster[id]
		m.level = int(m.level)
		m.xp = int(m.xp)
		m.hp = int(m.hp)
		m.mp = int(m.mp)
		for k in m.boosts:
			m.boosts[k] = int(m.boosts[k])
		full_heal(m)
	party = d.get("party", ["hero"])     # your whole team comes along, levels and all
	gear = d.gear
	items = d.items
	for k in items:
		items[k] = int(items[k])
	gold = int(d.gold)
	summons = d.summons
	flags["intro_done"] = false
	changed.emit()


func save_settings() -> void:
	var f := FileAccess.open("user://goblin_slayer_settings.json", FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(settings))
