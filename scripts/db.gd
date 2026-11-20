extends Node
## Read-only game database loaded from data/db.json, plus the formulas that turn data into numbers.

var d: Dictionary = {}
var maps_cache: Dictionary = {}

const STATS := ["hp", "mp", "str", "def", "mag", "mdef", "spd", "dex"]


func _ready() -> void:
	var f := FileAccess.open("res://data/db.json", FileAccess.READ)
	d = JSON.parse_string(f.get_as_text())


func map(id: String) -> Dictionary:
	if not maps_cache.has(id):
		var f := FileAccess.open("res://data/maps/%s.json" % id, FileAccess.READ)
		maps_cache[id] = JSON.parse_string(f.get_as_text())
	return maps_cache[id]


# ------------------------------------------------------------------ elements

func el_color(el) -> Color:
	if el == null or el == "" or not d.element_info.has(el):
		return Color(0.8, 0.8, 0.85)
	return Color(d.element_info[el].color)


func el_name(el) -> String:
	if el == null or el == "":
		return "None"
	return d.element_info[el].name


func beats(a, b) -> bool:
	if a == null or b == null or a == "" or b == "":
		return false
	return d.element_info[a].beats == b


func beater_of(el) -> String:
	for k in d.element_info:
		if d.element_info[k].beats == el:
			return k
	return ""


## Damage multiplier when element `atk` hits a target whose own element is `tgt` (enemies).
func el_mult(atk, tgt) -> float:
	if atk == null or atk == "" or tgt == null or tgt == "":
		return 1.0
	if beats(atk, tgt):
		return 1.75
	if atk == tgt:
		return 0.5
	return 1.0


# ------------------------------------------------------------------ items & gear

func info(id: String) -> Dictionary:
	if d.gear.has(id):
		return d.gear[id]
	if d.items.has(id):
		return d.items[id]
	if d.key_items.has(id):
		return d.key_items[id]
	return {"name": id, "kind": "?", "type": "?"}


func is_gear(id: String) -> bool:
	return d.gear.has(id)


func gear_slot(kind: String) -> String:
	if kind in ["blade", "bow", "staff"]:
		return "weapon"
	return kind  # armor | acc


## Stats a piece of gear gives when worn by someone of `wearer_level` (gear grows with you; quality decides how much).
func gear_stats(inst, wearer_level: int = -1) -> Dictionary:
	if inst == null:
		return {}
	var g: Dictionary = d.gear[inst.id]
	var lv: float = float(wearer_level if wearer_level > 0 else GS.avg_level())
	var q: float = float(g.q)
	var s := {}
	match g.kind:
		"blade", "bow":
			s["atk"] = int(round((6.0 + 2.6 * lv) * q))
		"staff":
			s["atk"] = int(round((4.0 + 1.8 * lv) * q))
			s["matk"] = int(round((5.0 + 2.4 * lv) * q))
		"armor":
			s["wdef"] = int(round((4.0 + 1.7 * lv) * q))
			s["wmdef"] = int(round((3.0 + 1.5 * lv) * q))
		"acc":
			s["wdef"] = int(round((1.0 + 0.5 * lv) * q))
			s["wmdef"] = int(round((1.0 + 0.5 * lv) * q))
	return s


func gear_price(inst) -> int:
	var g: Dictionary = d.gear[inst.id]
	var base := 140.0
	if g.kind == "armor":
		base = 130.0
	elif g.kind == "acc":
		base = 110.0
	var q := float(g.q)
	var tier_mult := {"common": 1.0, "rare": 2.2, "legendary": 5.0, "blessed": 9.0}
	return int(round(base * q * q * float(tier_mult.get(tier(inst.id), 1.0)) * float(g.get("price", 1.0)) / 10.0) * 10)


func tier(id: String) -> String:
	if not d.gear.has(id):
		return ""
	return str(d.gear[id].get("tier", "common"))


const TIER_COLORS := {"common": Color(0.85, 0.74, 0.55), "rare": Color(1.0, 0.35, 0.85), "legendary": Color(1.0, 0.82, 0.25),
	"blessed": Color(0.55, 0.95, 1.0)}


## Name color for an item: tan / magenta / shimmering gold.
func tier_color(id: String, t: float = -1.0) -> Color:
	var tr_id := tier(id)
	if tr_id == "":
		return Color.WHITE
	var c: Color = TIER_COLORS[tr_id]
	if tr_id == "legendary":
		var tt: float = t if t >= 0.0 else Time.get_ticks_msec() / 1000.0
		var sh := 0.5 + 0.5 * sin(tt * 3.2)
		c = c.lerp(Color(1.0, 0.97, 0.75), sh * 0.6)
	elif tr_id == "blessed":
		# a cold electric flicker
		var tt: float = t if t >= 0.0 else Time.get_ticks_msec() / 1000.0
		var sh := 0.5 + 0.5 * sin(tt * 7.0) * sin(tt * 2.3)
		c = c.lerp(Color(1, 1, 1), sh * 0.7)
	return c


func tier_name(id: String) -> String:
	return {"common": "Common", "rare": "Rare", "legendary": "Legendary", "blessed": "Blessed"}.get(tier(id), "")


func is_blessed(id: String) -> bool:
	return tier(id) == "blessed"


func gear_grade(_id: String) -> String:
	return ""


func gear_label(inst) -> String:
	return d.gear[inst.id].name


const FX_NAMES := {"crit": "Critical +%d%%", "mp_hit": "MP on hit +%d%%", "regen": "Regen %d%% HP/turn",
	"first": "Quick start +%d", "drain": "Drain %d%% of damage", "dodge": "Evade +%d%%", "spell": "Spell power +%d%%",
	"limit": "Limit gauge +%d%%", "gold": "Gold +%d%%", "xp": "EXP +%d%%", "guard": "Damage taken -%d%%",
	"pierce": "Ignores %d%% of defense"}


const FX_SHORT := {"crit": "Crit +%d%%", "mp_hit": "MP/hit +%d%%", "regen": "Regen %d%%", "first": "Quick +%d",
	"drain": "Drain %d%%", "dodge": "Evade +%d%%", "spell": "Spell +%d%%", "limit": "Limit +%d%%", "gold": "Gold +%d%%",
	"xp": "EXP +%d%%", "guard": "Guard %d%%", "pierce": "Pierce %d%%"}
const STAT_SHORT := {"hp": "HP", "mp": "MP", "str": "STR", "def": "DEF", "mag": "MAG", "mdef": "MDF", "spd": "SPD", "dex": "DEX"}


## Shorthand for tight spaces: "STR +16%", "Pierce 35%", "Crit +10%".
func gear_bonus_short(id: String) -> Array:
	var g: Dictionary = d.gear[id]
	var out := []
	for k in g.bonus:
		out.append("%s +%d%%" % [STAT_SHORT.get(k, k.to_upper()), int(round(float(g.bonus[k]) * 100.0))])
	var fx: Dictionary = g.get("fx", {})
	for k in fx:
		var v := float(fx[k])
		out.append(FX_SHORT.get(k, k.capitalize() + " %d") % (int(v) if k == "first" else int(round(v * 100.0))))
	return out


## Human-readable lines for a gear piece's bonuses and special effects.
func gear_bonus_lines(id: String) -> Array:
	var g: Dictionary = d.gear[id]
	var out := []
	var names := {"hp": "Max HP", "mp": "Max MP", "str": "Strength", "def": "Defense", "mag": "Magic",
		"mdef": "Magic Def.", "spd": "Speed", "dex": "Dexterity"}
	for k in g.bonus:
		out.append("%s +%d%%" % [names.get(k, k), int(round(float(g.bonus[k]) * 100.0))])
	var fx: Dictionary = g.get("fx", {})
	for k in fx:
		var v := float(fx[k])
		out.append(FX_NAMES.get(k, k + " %d") % (int(v) if k == "first" else int(round(v * 100.0))))
	return out


## Random gear found after a battle against `tier` enemies of `world`. Returns "" if nothing dropped.
func roll_drop(world: String, enemy_tier: String, rng: RandomNumberGenerator) -> String:
	if not d.drop_table.has(enemy_tier) or not d.world_gear_lists.has(world):
		return ""
	var row: Array = d.drop_table[enemy_tier]
	if rng.randf() >= float(row[0]):
		return ""
	var w: Array = row[1]
	var r := rng.randf() * (float(w[0]) + float(w[1]) + float(w[2]))
	var want := "common"
	if r >= float(w[0]) + float(w[1]):
		want = "legendary"
	elif r >= float(w[0]):
		want = "rare"
	var pool := []
	var lists: Dictionary = d.world_gear_lists[world]
	for k in lists:
		for id in lists[k]:
			if tier(id) == want:
				pool.append(id)
	if pool.is_empty():
		return ""
	return pool[rng.randi() % pool.size()]


func icon_for(id: String) -> String:
	if d.gear.has(id):
		return d.gear[id].kind
	if d.key_items.has(id):
		return "key"
	match id:
		"potion", "hi_potion":
			return "potion"
		"ether":
			return "ether"
		"feather":
			return "feather"
		"elixir":
			return "elixir"
		"smoke_bomb":
			return "bomb"
	return "tonic"


# ------------------------------------------------------------------ characters

func char_base(cid: String) -> Dictionary:
	return d.characters[cid]


func xp_to_next(level: int) -> int:
	return int(20 + 18 * pow(level, 1.5))


# ------------------------------------------------------------------ spells

func spells_for(elements: Array, level: int) -> Array:
	var out := []
	for sid in d.spells:
		var sp: Dictionary = d.spells[sid]
		if sp.el in elements and int(sp.lv) <= level:
			out.append(sid)
	out.sort_custom(func(a, b): return [elements.find(d.spells[a].el), int(d.spells[a].lv)] < [elements.find(d.spells[b].el), int(d.spells[b].lv)])
	return out


func spell_heal(mag: float, level: int, power: float, pieces: int) -> int:
	return int(round(power * (mag * 2.0 + 15.0 + level * 2.0) * (1.0 + 0.15 * max(0, pieces - 1))))


# ------------------------------------------------------------------ enemies

func make_enemy(kind: String, level: int, world: String) -> Dictionary:
	## kind is a species id ("rat") or a unique id ("vulkar").
	var u: Dictionary
	var unique: bool = d.uniques.has(kind)
	var el: String = world
	var tier_id: String
	var sprite: String
	var nm_: String
	if unique:
		u = d.uniques[kind]
		el = u.el
		tier_id = u.tier
		sprite = "u_" + kind
		nm_ = u.name
	else:
		u = d.species[kind]
		tier_id = u.tier
		sprite = "%s_%s" % [kind, world]
		nm_ = "%s %s" % [d.element_info[world].prefix, u.name]
	var t: Dictionary = d.tiers[tier_id]
	var L: int = max(1, level + int(t.lv))
	var early := clampf(0.72 + 0.07 * level, 0.72, 1.0) if tier_id in ["easy", "medium", "hard"] else clampf(0.8 + 0.05 * level, 0.8, 1.0)
	var plus := 1.0 + 0.2 * GS.ng          # New Game+: everything hits harder
	var hp := int((40.0 + 16.0 * L) * float(t.hp) * early * plus)
	var atk := (14.0 + 4.2 * L) * float(t.atk) * early * (1.0 + 0.12 * GS.ng)
	var e := {
		"kind": kind, "unique": unique, "name": nm_, "el": el, "tier": tier_id, "level": L, "sprite": sprite,
		"hp": hp, "maxhp": hp,
		"str": int(atk), "mag": int(atk * float(u.get("mag", 1.0)) * (1.0 if unique else 1.0)),
		"def": int((8.0 + 3.0 * L) * float(u.get("def", 1.0))),
		"mdef": int((8.0 + 3.0 * L) * float(u.get("mdef", 1.0))),
		"spd": int((9.0 + 1.25 * L) * float(u.get("spd", 1.0))),
		"dex": int(10 + 1.5 * L),
		"caster": bool(u.get("caster", unique)),
		"skills": u.get("skills", []), "ai": u.get("ai", []), "phases": u.get("phases", []), "shift": u.get("shift", []),
		"xp": int((10.0 + 4.0 * L) * float(t.xp)), "gold": int((6.0 + 3.0 * L) * float(t.gold)),
		"size": u.get("size", "m"),
	}
	if unique and tier_id in ["boss", "omni", "king"]:
		e["mag"] = int(atk * 1.05)
	# hunt bosses are built around one glaring strength and one glaring weakness
	var hpm := float(u.get("hp_mul", 1.0))
	var atm := float(u.get("atk_mul", 1.0))
	e["hp"] = max(1, int(e.hp * hpm))
	e["maxhp"] = e.hp
	e["str"] = int(e.str * atm)
	e["mag"] = int(e.mag * atm)
	e["blessed"] = bool(u.get("blessed", false))
	e["style"] = str(u.get("style", ""))
	e["weak_el"] = str(u.get("weak_el", ""))
	e["weak_mult"] = float(u.get("weak_mult", 1.75))
	e["hunt"] = str(u.get("hunt", ""))
	return e


func random_group(world: String, area: String, level: int, rng: RandomNumberGenerator, tags: Array = []) -> Array:
	var pool: Dictionary = d.pools[area]
	var by_tier := {"easy": [], "medium": [], "hard": []}
	var warren := tags.has("warren")
	for sp in d.species:
		var hab: String = str(d.species[sp].get("habitat", ""))
		if warren:
			# King Goblin's own tunnels: nothing but goblins
			if not sp.begins_with("goblin"):
				continue
		elif hab != "" and not tags.has(hab):
			continue
		by_tier[d.species[sp].tier].append(sp)
		# pirates crowd the coasts
		if hab == "coast":
			by_tier[d.species[sp].tier].append(sp)
	for k in by_tier:
		if by_tier[k].is_empty():
			by_tier[k] = by_tier["easy"] if not by_tier["easy"].is_empty() else ["goblin"]
	# small groups and gentler foes until the party has a few levels
	var max_n: int = mini(int(pool.size[1]), 1 + floori(level / 2.0))
	var n := rng.randi_range(mini(int(pool.size[0]), max_n), max_n)
	var out := []
	var we := float(pool.easy)
	var wm := float(pool.medium) * clampf((level - 1) / 4.0, 0.2, 1.0)
	var wh := float(pool.hard) * clampf((level - 3) / 5.0, 0.0, 1.0)
	var total := we + wm + wh
	for i in n:
		var r := rng.randf() * total
		var tier_id := "easy"
		if r >= we:
			tier_id = "medium" if r < we + wm else "hard"
		var list: Array = by_tier[tier_id]
		var el := world
		if not d.element_info.has(el):
			el = d.world_order[rng.randi() % d.world_order.size()]
		out.append(make_enemy(list[rng.randi() % list.size()], level, el))
	# hard enemies take up more room: at most 3 in a group with any large ones
	var large := out.filter(func(e): return e.size == "l")
	while out.size() > 3 and large.size() > 0:
		out.pop_back()
		large = out.filter(func(e): return e.size == "l")
	return out
