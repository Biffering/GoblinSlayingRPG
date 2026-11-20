extends Node2D
## FF7-style Active Time Battle. Speed fills each fighter's gauge; full gauge = a turn.
## Party commands: Attack / Limit, Magic, Summon, Item, Defend, Flee.

signal finished(result: String)

const WeatherFX := preload("res://scripts/weather.gd")

const FIELD_H := 176
const CMD_ATTACK := "Attack"

var enemies_in: Array = []
var opts: Dictionary = {}
var party: Array = []      # Battler
var foes: Array = []       # Battler
var bg_tex: Texture2D
var ui: BattleUI
var fx_layer: FX
var rng := RandomNumberGenerator.new()
var acting := false
var ended := false
var queue: Array = []      # [{"b": Battler, "act": Dictionary}]
var ready_list: Array = [] # party Battlers waiting for a command
var menu_for = null        # Battler whose command menu is open
var menu_state := ""       # "" | cmd | spell | summon | item | target
var cmd_idx := 0
var sub_idx := 0
var pending: Dictionary = {}
var target_side := "foe"
var target_idx := 0
var banner := ""
var banner_t := 0.0
var message := ""
var shake := 0.0
var t := 0.0
var result_lines: Array = []
var gameover_idx := 0
var phase := "fight"
var phys_hit := false      # set while a weapon/claw blow lands, for the blood spray
var splats: Array = []     # blood drops left on the ground for a moment       # fight | results | gameover


# ------------------------------------------------------------------ battlers

var dying := 0             # enemies still playing a death animation
var overload := false      # set while a Blessed weapon's blow lands on an ordinary creature


class Battler:
	var kill_el := ""      # element of the weakness blow that felled this enemy, for a themed death
	var side := "party"
	var id := ""
	var name := ""
	var m: Dictionary
	var e: Dictionary
	var st: Dictionary = {}
	var hp := 1
	var maxhp := 1
	var mp := 0
	var maxmp := 0
	var el = null
	var gauge := 0.0
	var status := {}
	var node
	var home := Vector2.ZERO
	var limit := 0.0
	var phase_i := 0
	var queued := false
	var level := 1

	func alive() -> bool:
		return hp > 0

	func spd() -> float:
		var s := float(st.spd)
		if status.has("spd"):
			s *= 1.4
		return s


class EnemySprite extends Node2D:
	var tex: Texture2D
	var mat: ShaderMaterial
	var fade := 1.0
	var bob := 0.0
	var t := 0.0

	func _ready() -> void:
		mat = Art.body_material()
		material = mat

	func _process(d: float) -> void:
		t += d
		queue_redraw()

	func _draw() -> void:
		if tex == null:
			return
		var w := tex.get_width()
		var h := tex.get_height()
		draw_rect(Rect2(-w * 0.35, -3, w * 0.7, 4), Color(0, 0, 0, 0.3 * fade))
		var b := roundf(sin(t * 1.6 + bob) * 1.0)
		draw_texture(tex, Vector2(-w * 0.5, -h + b), Color(1, 1, 1, fade))


class FX extends Node2D:
	var parts: Array = []
	var nums: Array = []
	var lines: Array = []
	var flashes: Array = []
	var rings: Array = []      # {pos, r0, r1, life, max, col, w}
	var cols: Array = []       # light pillars / geysers: {pos, w, h, life, max, col}
	var summon: Dictionary = {}

	func _process(d: float) -> void:
		for p in parts:
			p.life -= d
			p.pos += p.vel * d
			p.vel += p.get("acc", Vector2.ZERO) * d
		parts = parts.filter(func(p): return p.life > 0)
		for n in nums:
			n.t += d
		nums = nums.filter(func(n): return n.t < 1.1)
		for l in lines:
			l.life -= d
		lines = lines.filter(func(l): return l.life > 0)
		for f in flashes:
			f.life -= d
		flashes = flashes.filter(func(f): return f.life > 0)
		for r in rings:
			r.life -= d
		rings = rings.filter(func(r): return r.life > 0)
		for c in cols:
			c.life -= d
		cols = cols.filter(func(c): return c.life > 0)
		queue_redraw()

	func _draw() -> void:
		for f in flashes:
			draw_rect(Rect2(0, 0, 480, 270), Color(f.col.r, f.col.g, f.col.b, f.a * f.life / f.max))
		if not summon.is_empty():
			var tex: Texture2D = summon.tex
			draw_texture(tex, summon.pos, Color(1, 1, 1, summon.a))
		for c in cols:
			var k: float = clampf(c.life / c.max, 0.0, 1.0)
			var grow: float = 1.0 - pow(k, 3.0)
			var h: float = c.h * minf(1.0, grow * 1.6)
			for j in 3:
				var w: float = c.w * (1.0 - j * 0.3) * (0.6 + 0.4 * k)
				var cc: Color = c.col.lerp(Color.WHITE, j * 0.35)
				draw_rect(Rect2(c.pos.x - w / 2, c.pos.y - h, w, h), Color(cc.r, cc.g, cc.b, (0.35 + j * 0.2) * k))
		for r in rings:
			var k: float = 1.0 - clampf(r.life / r.max, 0.0, 1.0)
			var rad: float = lerpf(r.r0, r.r1, 1.0 - pow(1.0 - k, 2.0))
			draw_arc(r.pos, rad, 0, TAU, 40, Color(r.col.r, r.col.g, r.col.b, (1.0 - k) * r.col.a), r.w * (1.0 - k * 0.6))
		for l in lines:
			var a: float = l.life / l.max
			draw_line(l.a, l.b, Color(l.col.r, l.col.g, l.col.b, a), l.w)
		for p in parts:
			var a: float = clampf(p.life / p.max, 0.0, 1.0)
			var s: float = p.size * (0.5 + 0.5 * a)
			draw_rect(Rect2((p.pos - Vector2(s, s) / 2).round(), Vector2(ceil(s), ceil(s))), Color(p.col.r, p.col.g, p.col.b, a))
		for n in nums:
			var y: float = -18.0 * n.t
			if n.t < 0.25:
				y = -sin(n.t / 0.25 * PI) * 10.0
			else:
				y = -min(6.0, (n.t - 0.25) * 8.0)
			var col: Color = n.col
			col.a = clampf((1.1 - n.t) * 3.0, 0.0, 1.0)
			var p: Vector2 = n.pos + Vector2(0, y)
			# big hits punch in large and settle
			var base: int = 17 if n.get("big", false) else 12
			var fs: int = base + (int(round(8.0 * (1.0 - n.t / 0.14))) if n.t < 0.14 and n.get("big", false) else 0)
			var w := Art.width(n.text, fs)
			var o2 := 2 if n.get("big", false) else 1
			for o in [Vector2(-o2, 0), Vector2(o2, 0), Vector2(0, -o2), Vector2(0, o2), Vector2(o2, o2)]:
				Art.text(self, p - Vector2(w / 2, fs - 12) + o, n.text, Color(0.05, 0.0, 0.0, col.a), fs, null, false)
			Art.text(self, p - Vector2(w / 2, fs - 12), n.text, col, fs, null, false)
			if n.has("tag"):
				var ts: int = 10 if n.get("big", false) else 8
				var tw := Art.width(n.tag, ts)
				for o in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1)]:
					Art.text(self, p + Vector2(-tw / 2, -10 - (fs - 12) - ts + 8) + o, n.tag, Color(0.05, 0, 0, col.a), ts, null, false)
				Art.text(self, p + Vector2(-tw / 2, -10 - (fs - 12) - ts + 8), n.tag, Color(n.tagcol.r, n.tagcol.g, n.tagcol.b, col.a), ts, null, false)


class BattleUI extends Node2D:
	var b

	func _process(_d: float) -> void:
		queue_redraw()

	func _draw() -> void:
		b._draw_ui(self)


func setup(enemies: Array, o: Dictionary) -> void:
	enemies_in = enemies
	opts = o


func _ready() -> void:
	rng.randomize()
	var bg: String = opts.get("bg", "fire_out")
	bg_tex = Art.tex("res://assets/bg/%s.png" % bg)
	if bg_tex == null:
		bg_tex = Art.tex("res://assets/bg/fire_out.png")
	_build_party()
	_build_foes(enemies_in)
	fx_layer = FX.new()
	fx_layer.z_index = 200       # sparks, explosions and damage numbers draw over every fighter
	add_child(fx_layer)
	var layer := CanvasLayer.new()
	layer.layer = 5
	add_child(layer)
	if GS.weather_on:
		var wl := CanvasLayer.new()
		wl.layer = 4
		add_child(wl)
		var wn = WeatherFX.new()
		wn.in_battle = true
		wl.add_child(wn)
	ui = BattleUI.new()
	ui.b = self
	layer.add_child(ui)
	var music: String = opts.get("music", "battle")
	Audio.music(music, 0.4)
	Inp.block(4)
	var names := []
	for f in foes:
		names.append(f.name)
	_banner("%s!" % (names[0] if foes.size() == 1 else "Enemies appear"))
	var blessed_here := false
	for f in foes:
		if f.e.get("blessed", false):
			blessed_here = true
	if blessed_here:
		_blessed_intro()
	if GS.weather_on:
		_weather_banner()


func _build_party() -> void:
	var i := 0
	for m in GS.active_members():
		var b := Battler.new()
		b.side = "party"
		b.id = m.id
		b.m = m
		b.name = DB.d.characters[m.id].name
		b.st = GS.stats(m)
		b.hp = m.hp
		b.maxhp = b.st.maxhp
		b.mp = m.mp
		b.maxmp = b.st.maxmp
		b.limit = float(m.get("limit", 0.0))
		b.level = m.level
		b.gauge = rng.randf_range(10, 45) + b.st.spd * 0.6
		b.gauge = min(95.0, b.gauge + float(b.st.get("fx", {}).get("first", 0.0)))
		var a := Actor2D.new()
		var sheet: String = m.id if m.id != "hero" else "hero_t%d" % GS.hero_tier()
		a.setup("res://assets/battle/%s.png" % sheet, Vector2(96, 96), 39, "res://assets/battle/%s_aura.png" % sheet)
		a.shadow_w = 12
		a.offset = Vector2(0, 11)        # feet sit exactly on `home`
		var w = m.equip.weapon
		if w != null:
			var gd: Dictionary = DB.d.gear[w.id]
			var el = gd.el if gd.el != null else "none"
			if DB.is_blessed(w.id):
				a.weapon_tex = Art.tex("res://assets/weapons/%s_blessed_%s_%s.png" % [m.id, str(gd.get("style", "blade")), el])
			else:
				a.weapon_tex = Art.tex("res://assets/weapons/%s_%s_%s.png" % [m.id, gd.kind, el])
			a.set_weapon_tier(DB.tier(w.id))
		a.set_aura(GS.aura_colors(m), GS.aura_strength(m), GS.aura_radius(m))
		a.set_glow(not m.boosts.is_empty())
		# a diagonal line standing on the same ground as the enemies
		b.home = Vector2(334 + i * 19, 108 + i * 20)
		a.position = b.home
		a.z_index = i
		add_child(a)
		b.node = a
		if b.hp <= 0:
			a.set_frame(6)
		party.append(b)
		i += 1


const SLOTS := {
	1: [Vector2(140, 158)],
	2: [Vector2(170, 132), Vector2(92, 162)],
	3: [Vector2(184, 120), Vector2(118, 162), Vector2(58, 122)],
	4: [Vector2(200, 116), Vector2(146, 162), Vector2(88, 118), Vector2(40, 164)],
}


func _build_foes(list: Array) -> void:
	var n: int = min(4, list.size())
	for i in n:
		_add_foe(list[i], SLOTS[n][i])


func _add_foe(e: Dictionary, pos: Vector2) -> Battler:
	var b := Battler.new()
	b.side = "foe"
	b.id = e.kind
	b.e = e
	b.name = e.name
	b.st = {"str": e.str, "mag": e.mag, "def": e.def, "mdef": e.mdef, "spd": e.spd, "dex": e.dex}
	b.hp = e.hp
	b.maxhp = e.maxhp
	b.el = e.el
	b.level = e.level
	b.gauge = rng.randf_range(0, 40)
	var s := EnemySprite.new()
	s.tex = Art.tex("res://assets/enemies/%s.png" % e.sprite)
	s.bob = rng.randf() * 6.0
	b.home = pos
	s.position = pos
	s.z_index = int(pos.y / 10)
	add_child(s)
	b.node = s
	foes.append(b)
	return b


# ------------------------------------------------------------------ main loop

func _process(delta: float) -> void:
	t += delta
	for sp in splats:
		sp.t -= delta
	splats = splats.filter(func(sp): return sp.t > 0)
	if banner_t > 0:
		banner_t -= delta
	if shake > 0:
		shake = max(0.0, shake - delta * 20.0)
		position = Vector2(rng.randf_range(-shake, shake), rng.randf_range(-shake, shake)).round()
	else:
		position = Vector2.ZERO
	queue_redraw()
	if phase == "results":
		return
	if phase == "gameover":
		_gameover_input()
		return
	if ended:
		return
	var paused: bool = acting or (GS.settings.battle_mode == "wait" and menu_for != null)
	if not paused:
		for b in party + foes:
			if not b.alive() or b.gauge >= 100.0 or b.queued:
				continue
			b.gauge = min(100.0, b.gauge + delta * (b.spd() + 25.0) * 0.95)
			if b.gauge >= 100.0:
				_on_gauge_full(b)
	if menu_for != null:
		_menu_input()
	elif not ready_list.is_empty():
		_open_menu(ready_list[0])
	if not acting and not queue.is_empty():
		var q: Dictionary = queue.pop_front()
		_run_action(q.b, q.act)


func _on_gauge_full(b: Battler) -> void:
	if b.status.has("stun"):
		_tick(b, "stun")
		b.gauge = 0.0
		_pop(b, "Stunned", Color(1, 0.9, 0.4))
		return
	if b.side == "party":
		if not ready_list.has(b):
			ready_list.append(b)
			Audio.sfx("atb", -10.0)
	else:
		b.queued = true
		queue.append({"b": b, "act": _enemy_ai(b)})


func _tick(b: Battler, k: String) -> void:
	if b.status.has(k):
		b.status[k] -= 1
		if b.status[k] <= 0:
			b.status.erase(k)


func _end_turn(b: Battler) -> void:
	b.gauge = 0.0
	b.queued = false
	var rg := _fx(b, "regen")
	if rg > 0.0 and b.alive() and b.hp < b.maxhp:
		_heal(b, max(1, int(b.maxhp * rg)))
	for k in b.status.keys():
		if k in ["stun"]:
			continue
		if k == "guard":
			b.status.erase(k)
			continue
		_tick(b, k)


## Gear special effect total for a party member (0 for enemies).
func _fx(b: Battler, k: String) -> float:
	if b.side != "party":
		return 0.0
	return float(b.st.get("fx", {}).get(k, 0.0))


func _living(list: Array) -> Array:
	return list.filter(func(x): return x.alive())


# ------------------------------------------------------------------ command menu

func _commands(b: Battler) -> Array:
	var c := [("Limit" if b.limit >= 100.0 else CMD_ATTACK), "Magic", "Summon", "Item", "Defend"]
	if not _combos_for(b).is_empty():
		c.insert(2, "Combo")
	if opts.get("flee", true):
		c.append("Flee")
	return c


func _open_menu(b: Battler) -> void:
	if not b.alive():
		ready_list.erase(b)
		return
	menu_for = b
	menu_state = "cmd"
	cmd_idx = 0
	b.node.set_frame(2)
	Audio.sfx("cursor", -8.0)


func _close_menu() -> void:
	if menu_for:
		menu_for.node.set_frame(0)
		ready_list.erase(menu_for)
	menu_for = null
	menu_state = ""


## Chrono Trigger-style Double Techs: available when a partner's turn is also ready.
func _combos_for(b: Battler) -> Array:
	var out := []
	for cb in DB.d.get("combos", []):
		var other := ""
		if cb.a == b.id:
			other = cb.b
		elif cb.b == b.id:
			other = cb.a
		else:
			continue
		for p in ready_list:
			if p != b and p.id == other and p.alive() and not p.queued:
				out.append({"combo": cb, "partner": p})
	return out


func _spells(b: Battler) -> Array:
	return DB.spells_for(GS.spell_elements(b.m), b.m.level)


func _usable_items() -> Array:
	var out := []
	for id in GS.items:
		if DB.d.items.has(id):
			out.append(id)
	return out


func _menu_input() -> void:
	var b: Battler = menu_for
	if not b.alive():
		_close_menu()
		return
	match menu_state:
		"cmd":
			var cmds := _commands(b)
			var v := Inp.vert()
			var h := Inp.horiz()
			if v:
				var col := floori(cmd_idx / 3.0)
				cmd_idx = col * 3 + wrapi(cmd_idx % 3 + v, 0, 3)
				cmd_idx = min(cmd_idx, cmds.size() - 1)
				Audio.sfx("cursor", -6.0)
			if h:
				cmd_idx = clampi(cmd_idx + h * 3, 0, cmds.size() - 1)
				Audio.sfx("cursor", -6.0)
			if Inp.tab() and ready_list.size() > 1:
				# FF7-style: skip to the next ready character
				ready_list.erase(b)
				ready_list.append(b)
				b.node.set_frame(0)
				menu_for = null
				return
			if Inp.ok():
				var c: String = cmds[cmd_idx]
				match c:
					CMD_ATTACK:
						pending = {"type": "attack"}
						_begin_target("foe", false)
					"Limit":
						pending = {"type": "limit"}
						var lid: String = DB.d.characters[b.id].limit
						if lid in ["lighthouse_beam", "mountains_embrace", "enlightenment", "pit_fury", "thousand_feathers"]:
							_confirm({"targets": []})
						else:
							_begin_target("foe", false)
					"Combo":
						menu_state = "combo"
						sub_idx = 0
						Audio.sfx("confirm")
					"Magic":
						if b.status.has("silence"):
							Audio.sfx("buzzer")
							_banner("Silenced!")
						elif _spells(b).is_empty():
							Audio.sfx("buzzer")
							_banner("No spells. Equip elemental gear!")
						else:
							menu_state = "spell"
							sub_idx = 0
							Audio.sfx("confirm")
					"Summon":
						if GS.summons.is_empty():
							Audio.sfx("buzzer")
							_banner("No summons yet.")
						elif b.status.has("silence"):
							Audio.sfx("buzzer")
							_banner("Silenced!")
						else:
							menu_state = "summon"
							sub_idx = 0
							Audio.sfx("confirm")
					"Item":
						if _usable_items().is_empty():
							Audio.sfx("buzzer")
							_banner("No items.")
						else:
							menu_state = "item"
							sub_idx = 0
							Audio.sfx("confirm")
					"Defend":
						pending = {"type": "defend"}
						_confirm({"targets": [b]})
					"Flee":
						pending = {"type": "flee"}
						_confirm({"targets": []})
		"combo":
			var cl := _combos_for(b)
			if cl.is_empty():
				menu_state = "cmd"
				return
			var v := Inp.vert()
			if v:
				sub_idx = wrapi(sub_idx + v, 0, cl.size())
				Audio.sfx("cursor", -6.0)
			if Inp.back():
				menu_state = "cmd"
				Audio.sfx("cancel")
			elif Inp.ok():
				var e: Dictionary = cl[clampi(sub_idx, 0, cl.size() - 1)]
				var cb: Dictionary = e.combo
				var p: Battler = e.partner
				if b.mp < int(cb.mp) or p.mp < int(cb.mp):
					Audio.sfx("buzzer")
					_banner("Not enough MP (each needs %d)." % int(cb.mp))
					return
				pending = {"type": "combo", "combo": cb, "partner": p}
				match str(cb.target):
					"one":
						_begin_target("foe", false)
					"all":
						_begin_target("foe", true)
					_:
						_begin_target("party", true)
		"spell", "summon", "item":
			var lst: Array = _spells(b) if menu_state == "spell" else (GS.summons if menu_state == "summon" else _usable_items())
			var v := Inp.vert()
			if v:
				sub_idx = wrapi(sub_idx + v, 0, lst.size())
				Audio.sfx("cursor", -6.0)
			if Inp.back():
				menu_state = "cmd"
				Audio.sfx("cancel")
			elif Inp.ok():
				var id: String = lst[sub_idx]
				if menu_state == "spell":
					var sp: Dictionary = DB.d.spells[id]
					if b.mp < int(sp.mp):
						Audio.sfx("buzzer")
						_banner("Not enough MP.")
						return
					pending = {"type": "spell", "id": id}
					match sp.target:
						"one":
							_begin_target("foe", false)
						"all":
							_begin_target("foe", true)
						"ally":
							_begin_target("party", false)
						"allies":
							_begin_target("party", true)
						_:
							_confirm({"targets": [b]})
				elif menu_state == "summon":
					var sd: Dictionary = DB.d.summons[id]
					if b.mp < int(sd.mp):
						Audio.sfx("buzzer")
						_banner("Not enough MP.")
						return
					pending = {"type": "summon", "id": id}
					_confirm({"targets": []})
				else:
					var it: Dictionary = DB.d.items[id]
					pending = {"type": "item", "id": id}
					if it.effect == "flee":
						if not opts.get("flee", true):
							Audio.sfx("buzzer")
							_banner("Can't escape!")
							return
						_confirm({"targets": []})
					else:
						_begin_target("party", false)
		"target":
			var lst: Array = _target_list()
			if lst.is_empty():
				menu_state = "cmd"
				return
			var v := Inp.vert()
			var h := Inp.horiz()
			if v and not pending.get("all", false):
				target_idx = wrapi(target_idx + v, 0, lst.size())
				Audio.sfx("cursor", -6.0)
			if h:
				var want := "foe" if h < 0 else "party"
				if want != target_side:
					target_side = want
					target_idx = 0
					Audio.sfx("cursor", -6.0)
			if Inp.back():
				menu_state = "cmd"
				Audio.sfx("cancel")
			elif Inp.ok():
				lst = _target_list()
				var targets: Array = lst if pending.get("all", false) else [lst[target_idx]]
				_confirm({"targets": targets})


func _target_list() -> Array:
	var side: Array = foes if target_side == "foe" else party
	var lst: Array = _living(side)
	if target_side == "party" and pending.get("type", "") in ["item", "spell"]:
		# items and revive can target the fallen
		var revive := false
		if pending.type == "item":
			revive = DB.d.items[pending.id].effect in ["revive", "full"]
		elif pending.type == "spell":
			revive = DB.d.spells[pending.id].kind == "revive"
		if revive:
			lst = side.duplicate()
	return lst


func _begin_target(side: String, all: bool) -> void:
	target_side = side
	target_idx = 0
	pending["all"] = all
	menu_state = "target"
	Audio.sfx("confirm")
	# for heals, start on the most hurt ally
	if side == "party":
		var lst := _target_list()
		var best := 0
		for i in lst.size():
			if float(lst[i].hp) / lst[i].maxhp < float(lst[best].hp) / lst[best].maxhp:
				best = i
		target_idx = best


func _confirm(extra: Dictionary) -> void:
	var b: Battler = menu_for
	var act := pending.duplicate()
	act.merge(extra, true)
	Audio.sfx("confirm")
	b.queued = true
	if act.type == "combo":
		var p: Battler = act.partner
		p.queued = true
		ready_list.erase(p)
	queue.append({"b": b, "act": act})
	_close_menu()


# ------------------------------------------------------------------ actions

func _run_action(b: Battler, act: Dictionary) -> void:
	if ended or not b.alive():
		b.queued = false
		return
	acting = true
	match act.type:
		"attack":
			await _do_attack(b, act.targets)
		"limit":
			await _do_limit(b, act.targets)
		"spell":
			await _do_spell(b, act.id, act.targets, b.side == "party")
		"summon":
			await _do_summon(b, act.id)
		"item":
			await _do_item(b, act.id, act.targets)
		"defend":
			b.status["guard"] = 1
			_banner("%s defends." % b.name)
			Audio.sfx("defend")
			b.limit = min(100.0, b.limit + 4.0)
			await _wait(0.4)
		"flee":
			await _do_flee(b, false)
		"enemy":
			await _do_enemy(b, act)
		"combo":
			await _do_combo(b, act)
	if ended:
		acting = false
		return
	if b.side == "party" and act.type != "defend":
		b.limit = min(100.0, b.limit + 3.0 * (1.0 + _fx(b, "limit")))
	_end_turn(b)
	await _check_end()
	acting = false


func _do_combo(b: Battler, act: Dictionary) -> void:
	var cb: Dictionary = act.combo
	var p: Battler = act.partner
	if not p.alive():
		p.queued = false
		await _do_attack(b, act.targets)
		return
	b.mp -= int(cb.mp)
	p.mp -= int(cb.mp)
	var el: String = cb.el
	_banner("%s!" % cb.name)
	Audio.sfx("limit")
	# both heroes charge in together
	for x in [b, p]:
		x.node.set_frame(2)
		x.node.set_glow(true)
	_move(b.node, b.home + Vector2(-40, 0), 0.14)
	await _move(p.node, p.home + Vector2(-40, 0), 0.14)
	_play_seq(b, {"bow": "shoot", "staff": "thrust"}.get(str(b.st.wkind), "slash"))
	await _play_seq(p, {"bow": "shoot", "staff": "thrust"}.get(str(p.st.wkind), "slash"))
	if cb.get("heal", false):
		var amt := int((_spell_power(b, el) + _spell_power(p, el)) * float(cb.power) * 1.2)
		for tg in _living(party):
			_burst(_center(tg), "heal", 16)
			_heal(tg, amt)
		Audio.sfx("heal")
	else:
		var targets := _retarget(act.targets, foes)
		for tg in targets:
			_burst(_center(tg), el, 30)
			fx_layer.flashes.append({"col": DB.el_color(el), "life": 0.25, "max": 0.25, "a": 0.35})
		shake = 4.0
		Audio.sfx("spell_" + el)
		await _wait(0.25)
		var a: float = (max(_phys_power(b), _spell_power(b, el)) + max(_phys_power(p), _spell_power(p, el))) * 0.62
		for tg in targets:
			if not tg.alive():
				continue
			var mult := _el_mult(el, tg)
			var dmg := _formula(a, (_def_of(tg, false) + _def_of(tg, true)) * 0.5) * float(cb.power) * rng.randf_range(0.95, 1.05) * mult
			_hurt(tg, int(dmg), el, mult)
	await _wait(0.35)
	for x in [b, p]:
		if is_instance_valid(x.node):
			x.node.set_glow(not x.m.boosts.is_empty())
			x.node.set_frame(0 if x.alive() else 6)
	_move(b.node, b.home, 0.12)
	await _move(p.node, p.home, 0.12)
	p.limit = min(100.0, p.limit + 3.0)
	_end_turn(p)


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _retarget(targets: Array, side: Array) -> Array:
	var out := targets.filter(func(x): return x.alive())
	if out.is_empty() and targets.size() > 0:
		var liv := _living(side)
		if liv.size() > 0:
			out = [liv[rng.randi() % liv.size()]]
	return out


func _phys_power(b: Battler) -> float:
	if b.side == "foe":
		return float(b.st.str) * (1.3 if b.status.has("str") else 1.0)
	var s: Dictionary = b.st
	var base := 0.0
	match s.wkind:
		"bow":
			base = s.dex * 0.95
		"staff":
			base = s.mag * 0.5 + s.str * 0.3
		_:
			base = s.str
	if b.status.has("str"):
		base *= 1.3
	return base + float(s.atk)


func _def_of(b: Battler, magic: bool) -> float:
	var d: float
	if magic:
		d = float(b.st.mdef) + (float(b.st.wmdef) if b.side == "party" else 0.0)
		if b.status.has("mdef_down"):
			d *= 0.65
	else:
		d = float(b.st.def) + (float(b.st.wdef) if b.side == "party" else 0.0)
	if b.status.has("def"):
		d *= 1.35
	return d


func _el_mult(el, target: Battler) -> float:
	if el == null or el == "":
		return 1.0
	if target.side == "foe":
		if str(target.e.get("weak_el", "")) == str(el):
			return float(target.e.get("weak_mult", 3.5))
		return DB.el_mult(el, target.el)
	var res: Dictionary = target.st.get("res", {})
	return clampf(1.0 - float(res.get(el, 0.0)), 0.3, 1.6)


func _formula(a: float, d: float) -> float:
	return 1.15 * a * a / max(1.0, a + d)


## Applies damage and shows feedback. Returns damage dealt.
func _hurt(target: Battler, dmg: int, el, mult: float, crit := false) -> int:
	dmg = int(dmg * WeatherFX.mult(el))
	if target.status.has("guard"):
		dmg = int(dmg * 0.5)
	if target.status.has("bulwark"):
		dmg = int(dmg * 0.5)
	var gfx := _fx(target, "guard")
	if gfx > 0.0:
		dmg = int(dmg * (1.0 - min(0.5, gfx)))
	dmg = max(1, dmg)
	target.hp = max(0, target.hp - dmg)
	if phys_hit:
		_blood(target, dmg, crit)
	var tag := ""
	var tagcol := Color.WHITE
	if mult >= 1.5:
		tag = "WEAK!"
		tagcol = Color(1, 0.85, 0.3)
	elif mult <= 0.6:
		tag = "resist"
		tagcol = Color(0.7, 0.7, 0.8)
	if overload and tag != "WEAK!":
		tag = "OVERLOAD"
		tagcol = Color(0.6, 0.97, 1.0)
	if crit:
		tag = "CRITICAL!"
		tagcol = Color(1, 0.5, 0.3)
	var weak: bool = mult >= 1.5 and el != null and DB.d.element_info.has(str(el))
	var big: bool = crit or weak or overload or dmg >= target.maxhp * 0.3
	var numcol := Color(1, 1, 1) if target.side == "foe" else Color(1, 0.75, 0.75)
	if crit:
		numcol = Color(1.0, 0.86, 0.35)
	elif weak:
		numcol = Color(1.0, 0.95, 0.6)
	_pop(target, str(dmg), numcol, tag, tagcol, big)
	_flash_node(target)
	if target.side == "foe":
		_impact(target, el, big, crit)
		if weak:
			target.kill_el = str(el) if not target.alive() else ""
			_explode(target, str(el), not phys_hit)
		if overload and not target.alive():
			target.kill_el = "blessed"
		if big:
			_voice(target, crit or weak or not target.alive())
	if target.side == "party":
		target.limit = min(100.0, target.limit + float(dmg) / max(1, target.maxhp) * 125.0 * (1.0 + _fx(target, "limit")))
		target.node.set_frame(5)
		shake = 2.0 if dmg < target.maxhp * 0.2 else 4.0
		_reset_frame_later(target)
	if mult >= 1.5:
		Audio.sfx("weak", -2.0)
	Audio.sfx("hit" if el == null else "hit_" + str(el), -2.0)
	if not target.alive():
		_on_ko(target)
	else:
		_check_phase(target)
	return dmg


## A little blood from weapon and claw hits (bone dust for skeletons and spirits).
func _blood(b: Battler, dmg: int, crit: bool) -> void:
	var nm := b.name.to_lower()
	var bloodless := nm.contains("ghost") or nm.contains("skeleton") or nm.contains("undead") or nm.contains("nobody") or nm.contains("guardian")
	var col := Color(0.62, 0.02, 0.04) if not bloodless else Color(0.85, 0.85, 0.8)
	var c := _center(b)
	var away := -1.0 if b.side == "foe" else 1.0      # spray away from the attacker
	var n: int = 6 + mini(10, floori(dmg / 20.0)) + (6 if crit else 0)
	for i in n:
		var v := Vector2(away * rng.randf_range(30, 110), rng.randf_range(-110, -20))
		fx_layer.parts.append({"pos": c + Vector2(rng.randf_range(-4, 4), rng.randf_range(-6, 4)), "vel": v,
							   "acc": Vector2(0, 320), "life": rng.randf_range(0.35, 0.6), "max": 0.6,
							   "col": col.lerp(Color(0.35, 0.0, 0.02), rng.randf()) if not bloodless else col, "size": rng.randf_range(1.5, 3.0)})
	if not bloodless:
		for i in 2 + (2 if crit else 0):
			splats.append({"p": b.node.position + Vector2(away * rng.randf_range(4, 24), rng.randf_range(-2, 3)),
						   "r": rng.randf_range(1.5, 3.5), "t": 2.5})


## Every blow on an enemy: a ring, sparks, a little knockback. Big ones get hit-stop and a white pop.
func _impact(b: Battler, el, big: bool, crit: bool) -> void:
	var c := _center(b)
	var col := DB.el_color(el) if el != null and DB.d.element_info.has(str(el)) else Color(1, 0.95, 0.85)
	fx_layer.rings.append({"pos": c, "r0": 4.0, "r1": 26.0 if big else 15.0, "life": 0.28, "max": 0.28, "col": col.lerp(Color.WHITE, 0.4), "w": 3.0 if big else 2.0})
	var rays := 10 if big else 5
	for i in rays:
		var a := rng.randf() * TAU
		var d := Vector2(cos(a), sin(a))
		var r1 := rng.randf_range(6, 10)
		var r2 := r1 + rng.randf_range(10, 26 if big else 14)
		fx_layer.lines.append({"a": c + d * r1, "b": c + d * r2, "col": col.lerp(Color.WHITE, 0.6), "w": 2.0 if big else 1.0, "life": 0.16, "max": 0.16})
	for i in (14 if big else 6):
		var a := rng.randf() * TAU
		fx_layer.parts.append({"pos": c, "vel": Vector2(cos(a), sin(a)) * rng.randf_range(60, 160), "acc": Vector2(0, 160),
							   "life": rng.randf_range(0.2, 0.4), "max": 0.4, "col": col.lerp(Color(1, 1, 0.8), rng.randf()), "size": 2.0})
	if big:
		shake = max(shake, 5.0 if crit else 4.0)
		if crit:
			fx_layer.flashes.append({"col": Color(1, 0.95, 0.85), "a": 0.35, "life": 0.12, "max": 0.12})
		_hitstop(0.09 if crit else 0.06)
	_knock(b, 10.0 if big else 4.0)


func _knock(b: Battler, px: float) -> void:
	var n: Node2D = b.node
	if not is_instance_valid(n):
		return
	var tw := create_tween()
	tw.tween_property(n, "position", b.home + Vector2(-px, 0), 0.05)
	tw.tween_property(n, "position", b.home, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


## A heartbeat of frozen time so a heavy blow feels heavy.
func _hitstop(sec: float) -> void:
	Engine.time_scale = 0.06
	await get_tree().create_timer(sec, true, false, true).timeout
	Engine.time_scale = 1.0


func _exit_tree() -> void:
	Engine.time_scale = 1.0


## Grunts on heavy hits, long groans on crits, weaknesses and death blows. Bigger beasts sound deeper.
func _voice(b: Battler, groan: bool) -> void:
	var h := _foe_h(b)
	var pitch := clampf(1.35 - (h - 30.0) / 90.0, 0.62, 1.45) * rng.randf_range(0.93, 1.07)
	var nm := b.name.to_lower()
	if nm.contains("ghost") or nm.contains("wisp") or nm.contains("spirit"):
		pitch *= 1.25
	if h < 34 and not groan:
		Audio.sfx("shriek1", -6.0, pitch * 0.9, 0.0)
	elif groan:
		Audio.sfx("groan%d" % (1 + rng.randi() % 2), -1.0, pitch, 0.0)
	else:
		Audio.sfx("grunt%d" % (1 + rng.randi() % 3), -2.0, pitch, 0.0)


## A weakness struck: the element bursts out of the enemy.
func _explode(b: Battler, el: String, spell: bool) -> void:
	var c := _center(b)
	var feet: Vector2 = b.home
	var k := 1.0 if spell else 0.65
	var col := DB.el_color(el)
	fx_layer.flashes.append({"col": col.lerp(Color.WHITE, 0.3), "a": 0.4 * k, "life": 0.25, "max": 0.25})
	fx_layer.rings.append({"pos": c, "r0": 6.0, "r1": 58.0 * k, "life": 0.45, "max": 0.45, "col": col.lerp(Color.WHITE, 0.5), "w": 4.0})
	fx_layer.rings.append({"pos": c, "r0": 2.0, "r1": 36.0 * k, "life": 0.35, "max": 0.35, "col": Color(1, 1, 1, 0.9), "w": 2.0})
	shake = max(shake, 7.0 * k)
	Audio.sfx("boom_big" if spell else "boom", -3.0 if spell else -6.0, rng.randf_range(0.9, 1.1), 0.0)
	if spell:
		_hitstop(0.08)
	var n := int(36 * k)
	match el:
		"fire":
			fx_layer.cols.append({"pos": feet, "w": 30.0 * k, "h": 90.0 * k, "life": 0.6, "max": 0.6, "col": Color(1, 0.45, 0.1)})
			for i in n:
				var a := rng.randf() * TAU
				fx_layer.parts.append({"pos": c, "vel": Vector2(cos(a), sin(a) * 0.7) * rng.randf_range(60, 190) + Vector2(0, -40), "acc": Vector2(0, -60),
									   "life": rng.randf_range(0.4, 0.8), "max": 0.8, "col": [Color(1, 0.3, 0.05), Color(1, 0.65, 0.15), Color(1, 0.95, 0.5)][i % 3], "size": rng.randf_range(3, 6)})
			for i in int(10 * k):
				fx_layer.parts.append({"pos": c + Vector2(rng.randf_range(-14, 14), 0), "vel": Vector2(rng.randf_range(-12, 12), rng.randf_range(-40, -20)),
									   "life": 1.0, "max": 1.0, "col": Color(0.2, 0.17, 0.16), "size": 6.0})
		"water":
			fx_layer.cols.append({"pos": feet, "w": 22.0 * k, "h": 110.0 * k, "life": 0.7, "max": 0.7, "col": Color(0.35, 0.65, 1.0)})
			for i in n:
				fx_layer.parts.append({"pos": feet + Vector2(rng.randf_range(-10, 10), -rng.randf_range(0, 80) * k), "vel": Vector2(rng.randf_range(-110, 110), rng.randf_range(-200, -40)),
									   "acc": Vector2(0, 420), "life": rng.randf_range(0.5, 0.9), "max": 0.9, "col": [Color(0.3, 0.6, 1.0), Color(0.75, 0.92, 1.0), Color(1, 1, 1)][i % 3], "size": rng.randf_range(2, 4)})
			fx_layer.rings.append({"pos": feet, "r0": 4.0, "r1": 46.0 * k, "life": 0.6, "max": 0.6, "col": Color(0.7, 0.9, 1.0), "w": 2.0})
		"wind":
			for i in n + 10:
				var a := float(i) / (n + 10) * TAU * 3.0
				var r := 6.0 + i * 0.9
				fx_layer.parts.append({"pos": feet + Vector2(cos(a) * r * 0.8, -i * 1.6 * k), "vel": Vector2(-sin(a), cos(a) * 0.25) * 170.0,
									   "life": rng.randf_range(0.4, 0.7), "max": 0.7, "col": [Color(0.3, 0.95, 0.85), Color(0.9, 1, 1), Color(0.6, 0.85, 0.5)][i % 3], "size": 2.5})
			for i in 5:
				var y := c.y + rng.randf_range(-24, 24)
				fx_layer.lines.append({"a": Vector2(c.x + 50, y), "b": Vector2(c.x - 50, y + rng.randf_range(-12, 12)), "col": Color(0.9, 1, 1), "w": 2.0, "life": 0.25, "max": 0.25})
		"stone":
			for i in 7:
				var x := feet.x + (i - 3) * 9.0 * k + rng.randf_range(-3, 3)
				var hh := rng.randf_range(24, 56) * k
				fx_layer.lines.append({"a": Vector2(x, feet.y + 2), "b": Vector2(x + rng.randf_range(-6, 6), feet.y - hh), "col": Color(0.55, 0.47, 0.38), "w": 5.0, "life": 0.55, "max": 0.55})
				fx_layer.lines.append({"a": Vector2(x, feet.y + 2), "b": Vector2(x + rng.randf_range(-3, 3), feet.y - hh * 0.8), "col": Color(0.8, 0.72, 0.6), "w": 2.0, "life": 0.55, "max": 0.55})
			for i in n:
				fx_layer.parts.append({"pos": c, "vel": Vector2(rng.randf_range(-150, 150), rng.randf_range(-220, -60)), "acc": Vector2(0, 480),
									   "life": rng.randf_range(0.5, 0.9), "max": 0.9, "col": [Color(0.45, 0.4, 0.35), Color(0.62, 0.55, 0.45), Color(0.4, 0.7, 0.3)][i % 3], "size": rng.randf_range(3, 6)})
		"spirit":
			fx_layer.cols.append({"pos": feet, "w": 34.0 * k, "h": 180.0, "life": 0.8, "max": 0.8, "col": Color(1, 0.95, 0.7)})
			for i in 12:
				var a := float(i) / 12.0 * TAU
				fx_layer.lines.append({"a": c + Vector2(cos(a), sin(a)) * 10, "b": c + Vector2(cos(a), sin(a)) * 60 * k, "col": Color(1, 1, 0.85), "w": 2.0, "life": 0.4, "max": 0.4})
			for i in n:
				fx_layer.parts.append({"pos": c + Vector2(rng.randf_range(-20, 20), rng.randf_range(-20, 20)), "vel": Vector2(rng.randf_range(-10, 10), rng.randf_range(-90, -30)),
									   "life": rng.randf_range(0.6, 1.0), "max": 1.0, "col": [Color(1, 1, 0.9), Color(1, 0.9, 0.5)][i % 2], "size": 2.5})
		"void":
			fx_layer.rings.append({"pos": c, "r0": 70.0 * k, "r1": 3.0, "life": 0.45, "max": 0.45, "col": Color(0.65, 0.3, 1.0), "w": 4.0})
			for i in n:
				var a := rng.randf() * TAU
				var r := rng.randf_range(40, 70) * k
				var p := c + Vector2(cos(a), sin(a)) * r
				fx_layer.parts.append({"pos": p, "vel": (c - p) * 2.4 + Vector2(-sin(a), cos(a)) * 60.0,
									   "life": 0.42, "max": 0.42, "col": [Color(0.65, 0.3, 1.0), Color(0.12, 0.03, 0.25), Color(0.9, 0.7, 1.0)][i % 3], "size": 3.0})
			_void_pop(c, k)


func _void_pop(c: Vector2, k: float) -> void:
	await _wait(0.42)
	fx_layer.rings.append({"pos": c, "r0": 2.0, "r1": 64.0 * k, "life": 0.35, "max": 0.35, "col": Color(0.15, 0.02, 0.3, 1.0), "w": 6.0})
	fx_layer.flashes.append({"col": Color(0.3, 0.05, 0.5), "a": 0.35 * k, "life": 0.2, "max": 0.2})


func _reset_frame_later(b: Battler) -> void:
	await _wait(0.35)
	if is_instance_valid(b.node) and b.alive():
		b.node.set_frame(0)


func _heal(target: Battler, amt: int) -> void:
	var before := target.hp
	target.hp = min(target.maxhp, target.hp + amt)
	_pop(target, str(target.hp - before), Color(0.5, 1.0, 0.55))
	if target.side == "party" and target.hp > 0:
		target.node.set_frame(0)


func _on_ko(b: Battler) -> void:
	b.gauge = 0.0
	b.status.clear()
	ready_list.erase(b)
	if menu_for == b:
		_close_menu()
	if b.side == "party":
		b.node.set_frame(6)
		Audio.sfx("ko")
	else:
		if b.kill_el == "blessed":
			_disintegrate(b)
		elif b.kill_el != "":
			_elem_death(b, b.kill_el)
		else:
			Audio.sfx("enemy_die")
			_fade_out(b)
			_burst(b.node.position + Vector2(0, -16), b.el, 18)


func _fade_out(b: Battler) -> void:
	var s: EnemySprite = b.node
	for i in 10:
		s.mat.set_shader_parameter("flash", 0.8 if i % 2 == 0 else 0.2)
		s.fade = 1.0 - i / 10.0
		await _wait(0.04)
	s.visible = false


## Struck down by Blessed tech: the whole screen goes white and the creature comes apart into light.
func _disintegrate(b: Battler) -> void:
	var s: EnemySprite = b.node
	dying += 1
	var c := _center(b)
	var h := _foe_h(b)
	var w := float(s.tex.get_width()) if s.tex else 40.0
	var feet: Vector2 = s.position
	var col := Color(0.6, 0.97, 1.0)
	_hitstop(0.14)
	Audio.sfx("boom_big", 0.0, 0.8, 0.0)
	Audio.sfx("laser", 0.0, 0.55, 0.0)
	shake = 11.0
	fx_layer.flashes.append({"col": Color(1, 1, 1), "a": 0.85, "life": 0.18, "max": 0.18})
	# a pillar of light from the sky
	fx_layer.cols.append({"pos": feet + Vector2(0, 4), "w": w + 26.0, "h": 280.0, "life": 1.1, "max": 1.1, "col": col})
	fx_layer.cols.append({"pos": feet + Vector2(0, 4), "w": (w + 26.0) * 0.4, "h": 280.0, "life": 0.9, "max": 0.9, "col": Color(1, 1, 1)})
	# the body burns white, swells, and holds for a heartbeat
	s.mat.set_shader_parameter("flash", 1.0)
	var tw := create_tween()
	tw.tween_property(s, "scale", Vector2(1.18, 1.12), 0.12)
	await _wait(0.16)
	# shockwaves and rays across the field
	for i in 3:
		fx_layer.rings.append({"pos": c, "r0": 8.0 + i * 6.0, "r1": 120.0 + i * 50.0, "life": 0.55 + i * 0.15, "max": 0.55 + i * 0.15, "col": col.lerp(Color.WHITE, i * 0.3), "w": 5.0 - i})
	for i in 20:
		var a := float(i) / 20.0 * TAU + rng.randf() * 0.2
		var d := Vector2(cos(a), sin(a))
		fx_layer.lines.append({"a": c + d * 14.0, "b": c + d * rng.randf_range(90, 220), "col": Color(1, 1, 1) if i % 2 == 0 else col, "w": 2.0, "life": 0.35, "max": 0.35})
	fx_layer.flashes.append({"col": col, "a": 0.45, "life": 0.35, "max": 0.35})
	# the body comes apart into motes, bottom to top, that spiral up into the light
	s.visible = false
	var rows := 12
	for r in rows:
		for k in 8:
			var p := feet + Vector2(rng.randf_range(-w * 0.45, w * 0.45), -h * (float(r) / rows) - rng.randf_range(0, h / rows))
			var out := (p - c).normalized()
			fx_layer.parts.append({"pos": p, "vel": out * rng.randf_range(30, 120) + Vector2(rng.randf_range(-20, 20), rng.randf_range(-160, -60)),
								   "acc": Vector2(0, -60), "life": rng.randf_range(0.8, 1.5), "max": 1.5,
								   "col": [Color(1, 1, 1), col, Color(0.4, 0.8, 1.0)][k % 3], "size": rng.randf_range(2, 4)})
		if r % 3 == 0:
			await _wait(0.03)
	_pop(b, "", col, "DISINTEGRATED", col, true)
	# a scorched ring on the ground, and sparks that linger
	for i in 10:
		splats.append({"p": feet + Vector2(rng.randf_range(-w * 0.5, w * 0.5), rng.randf_range(-3, 3)), "r": rng.randf_range(2, 4.5), "t": 3.5, "ash": true})
	for i in 6:
		await _wait(0.08)
		fx_layer.parts.append({"pos": feet + Vector2(rng.randf_range(-w * 0.4, w * 0.4), -2), "vel": Vector2(rng.randf_range(-10, 10), rng.randf_range(-60, -30)),
							   "life": 0.6, "max": 0.6, "col": col, "size": 2.0})
	s.scale = Vector2.ONE
	dying -= 1


## Felled by its weakness: burned to ash, melted, blown away, shattered, burned to light or swallowed by the void.
func _elem_death(b: Battler, el: String) -> void:
	var s: EnemySprite = b.node
	dying += 1
	var c := _center(b)
	var h := _foe_h(b)
	var w := float(s.tex.get_width()) if s.tex else 40.0
	match el:
		"fire":
			Audio.sfx("hit_fire", 0.0, 0.8, 0.0)
			for i in 14:
				s.mat.set_shader_parameter("tint", Color(1, 0.45, 0.1).lerp(Color(0.08, 0.05, 0.04), i / 14.0))
				s.mat.set_shader_parameter("tint_amount", 0.5 + i * 0.035)
				for j in 4:
					fx_layer.parts.append({"pos": s.position + Vector2(rng.randf_range(-w * 0.4, w * 0.4), -rng.randf_range(0, h)), "vel": Vector2(rng.randf_range(-10, 10), rng.randf_range(-70, -30)),
										   "life": 0.5, "max": 0.5, "col": [Color(1, 0.35, 0.05), Color(1, 0.7, 0.2)][j % 2], "size": rng.randf_range(2, 4)})
				await _wait(0.05)
			# crumble to ash from the top down
			for i in 10:
				s.fade = 1.0 - i / 10.0
				for j in 5:
					fx_layer.parts.append({"pos": s.position + Vector2(rng.randf_range(-w * 0.4, w * 0.4), -h * (1.0 - i / 10.0) + rng.randf_range(0, 6)),
										   "vel": Vector2(rng.randf_range(-15, 15), rng.randf_range(10, 40)), "acc": Vector2(0, 120), "life": 0.6, "max": 0.6,
										   "col": [Color(0.25, 0.22, 0.2), Color(0.45, 0.4, 0.36), Color(1, 0.5, 0.1)][j % 3], "size": 2.5})
				await _wait(0.04)
			for i in 6:
				splats.append({"p": s.position + Vector2(rng.randf_range(-w * 0.3, w * 0.3), rng.randf_range(-2, 2)), "r": rng.randf_range(2, 4), "t": 3.0, "ash": true})
		"water":
			Audio.sfx("hit_water", 0.0, 0.7, 0.0)
			s.mat.set_shader_parameter("tint", Color(0.3, 0.55, 1.0))
			s.mat.set_shader_parameter("tint_amount", 0.55)
			var tw := create_tween().set_parallel()
			tw.tween_property(s, "scale", Vector2(1.5, 0.05), 0.75).set_ease(Tween.EASE_IN)
			tw.tween_property(s, "fade", 0.2, 0.75)
			for i in 15:
				fx_layer.parts.append({"pos": s.position + Vector2(rng.randf_range(-w * 0.5, w * 0.5), -rng.randf_range(0, h * (1.0 - i / 15.0))), "vel": Vector2(rng.randf_range(-60, 60), rng.randf_range(-60, 0)),
									   "acc": Vector2(0, 300), "life": 0.5, "max": 0.5, "col": [Color(0.4, 0.7, 1.0), Color(0.8, 0.95, 1.0)][i % 2], "size": 2.5})
				await _wait(0.05)
			fx_layer.rings.append({"pos": s.position, "r0": 4.0, "r1": w * 0.8, "life": 0.7, "max": 0.7, "col": Color(0.7, 0.9, 1.0), "w": 2.0})
		"wind":
			Audio.sfx("hit_wind", 0.0, 0.8, 0.0)
			s.mat.set_shader_parameter("tint", Color(0.85, 1.0, 0.95))
			s.mat.set_shader_parameter("tint_amount", 0.35)
			var tw := create_tween().set_parallel()
			tw.tween_property(s, "position", s.position + Vector2(-300, -150), 0.9).set_ease(Tween.EASE_IN)
			tw.tween_property(s, "rotation", -TAU * 2.0, 0.9)
			tw.tween_property(s, "scale", Vector2(0.35, 0.35), 0.9)
			for i in 18:
				fx_layer.parts.append({"pos": s.position + Vector2(rng.randf_range(-10, 10), -h * 0.5 * s.scale.y), "vel": Vector2(rng.randf_range(60, 140), rng.randf_range(-20, 40)),
									   "life": 0.5, "max": 0.5, "col": [Color(0.4, 0.75, 0.3), Color(0.9, 1, 1), Color(0.55, 0.45, 0.25)][i % 3], "size": 2.5})
				await _wait(0.05)
		"stone":
			Audio.sfx("hit_stone", 0.0, 0.7, 0.0)
			for i in 8:
				s.mat.set_shader_parameter("tint", Color(0.55, 0.53, 0.5))
				s.mat.set_shader_parameter("tint_amount", i / 8.0 * 0.95)
				await _wait(0.05)
			await _wait(0.25)
			Audio.sfx("hit_stone", 2.0, 1.2, 0.0)
			s.visible = false
			for i in 22:
				var p := s.position + Vector2(rng.randf_range(-w * 0.4, w * 0.4), -rng.randf_range(0, h))
				fx_layer.parts.append({"pos": p, "vel": (p - c).normalized() * rng.randf_range(60, 170) + Vector2(0, -80), "acc": Vector2(0, 520),
									   "life": rng.randf_range(0.6, 1.0), "max": 1.0, "col": [Color(0.5, 0.48, 0.45), Color(0.66, 0.63, 0.58), Color(0.35, 0.33, 0.31)][i % 3], "size": rng.randf_range(3, 7)})
			fx_layer.rings.append({"pos": s.position, "r0": 4.0, "r1": w, "life": 0.5, "max": 0.5, "col": Color(0.7, 0.65, 0.55, 0.7), "w": 3.0})
		"spirit":
			Audio.sfx("hit_spirit", 0.0, 0.9, 0.0)
			fx_layer.cols.append({"pos": s.position, "w": w * 0.9, "h": 200.0, "life": 1.0, "max": 1.0, "col": Color(1, 0.97, 0.8)})
			var tw := create_tween().set_parallel()
			tw.tween_property(s, "position", s.position + Vector2(0, -40), 0.8).set_ease(Tween.EASE_IN)
			tw.tween_property(s, "fade", 0.0, 0.8)
			for i in 16:
				s.mat.set_shader_parameter("flash", minf(1.0, i / 8.0))
				fx_layer.parts.append({"pos": s.position + Vector2(rng.randf_range(-w * 0.4, w * 0.4), -rng.randf_range(0, h)), "vel": Vector2(0, rng.randf_range(-90, -40)),
									   "life": 0.7, "max": 0.7, "col": Color(1, 1, 0.85), "size": 2.0})
				await _wait(0.05)
		"void":
			Audio.sfx("hit_void", 0.0, 0.7, 0.0)
			s.mat.set_shader_parameter("tint", Color(0.2, 0.05, 0.35))
			s.mat.set_shader_parameter("tint_amount", 0.6)
			# pull the body into a point at its middle
			var mid := s.position + Vector2(0, -h * 0.5)
			var tw := create_tween().set_parallel()
			tw.tween_property(s, "scale", Vector2(0.02, 0.02), 0.7).set_ease(Tween.EASE_IN)
			tw.tween_property(s, "position", mid, 0.7).set_ease(Tween.EASE_IN)
			tw.tween_property(s, "rotation", TAU * 1.5, 0.7).set_ease(Tween.EASE_IN)
			for i in 14:
				var a := rng.randf() * TAU
				var p := mid + Vector2(cos(a), sin(a)) * rng.randf_range(30, 60)
				fx_layer.parts.append({"pos": p, "vel": (mid - p) * 2.5, "life": 0.4, "max": 0.4, "col": [Color(0.6, 0.3, 1.0), Color(0.1, 0.02, 0.2)][i % 2], "size": 3.0})
				await _wait(0.05)
			fx_layer.rings.append({"pos": mid, "r0": 2.0, "r1": 40.0, "life": 0.3, "max": 0.3, "col": Color(0.8, 0.6, 1.0), "w": 3.0})
	Audio.sfx("enemy_die", -6.0)
	s.visible = false
	dying -= 1


func _flash_node(b: Battler) -> void:
	var n = b.node
	if b.side == "party":
		n.set_flash(0.8)
		await _wait(0.07)
		if is_instance_valid(n):
			n.set_flash(0.0)
	else:
		n.mat.set_shader_parameter("flash", 0.9)
		await _wait(0.07)
		if is_instance_valid(n):
			n.mat.set_shader_parameter("flash", 0.0)


func _pop(b: Battler, text: String, col: Color, tag := "", tagcol := Color.WHITE, big := false) -> void:
	# above the head, nudged so tall enemies' numbers stay on screen
	var p: Vector2 = b.node.position + Vector2(0, -(48.0 if b.side == "party" else minf(_foe_h(b) * 0.75, 120.0)))
	p.y = maxf(p.y, 26.0)
	var n := {"text": text, "pos": p + Vector2(rng.randf_range(-4, 4), 0), "t": 0.0, "col": col, "big": big}
	if tag != "":
		n.tag = tag
		n.tagcol = tagcol
	fx_layer.nums.append(n)


func _pop_mp(b: Battler, amt: int) -> void:
	await _wait(0.12)
	if is_instance_valid(b.node):
		fx_layer.nums.append({"text": "+%d MP" % amt, "pos": b.node.position + Vector2(rng.randf_range(-3, 3), -16), "t": 0.0, "col": Color(0.45, 0.8, 1.0)})


func _foe_h(b: Battler) -> float:
	var s: EnemySprite = b.node
	return float(s.tex.get_height()) if s.tex else 40.0


func _center(b: Battler) -> Vector2:
	if b.side == "party":
		return b.node.position + Vector2(0, -26)
	return b.node.position + Vector2(0, -_foe_h(b) * 0.45)


func _blessed_intro() -> void:
	await _wait(0.6)
	var lines: Dictionary = DB.d.get("blessed_lines", {})
	var say: Array = []
	if not GS.flag("met_blessed"):
		GS.flags["met_blessed"] = true
		say = lines.get("first", [])
	else:
		var pool: Array = lines.get("appear", [])
		if not pool.is_empty():
			say = [pool[rng.randi() % pool.size()]]
	for ln in say:
		message = str(ln)
		await _wait(2.2)
	message = ""


func _weather_banner() -> void:
	await _wait(1.3)
	if not ended:
		_banner(WeatherFX.describe(str(GS.weather.get("kind", ""))))


func _banner(s: String) -> void:
	banner = s
	banner_t = 1.3


# ---- attacks

## Blessed weapons: what style (blade / rifle / pistol / staff) the attacker carries, or "".
func _blessed_style(b: Battler) -> String:
	if b.side != "party":
		return str(b.e.get("style", "")) if b.e.get("blessed", false) else ""
	var w = b.m.equip.weapon
	if w == null or not DB.is_blessed(w.id):
		return ""
	return str(DB.d.gear[w.id].get("style", "blade"))


func _energy_col(b: Battler) -> Color:
	var el = b.st.get("wel") if b.side == "party" else b.el
	if el != null and DB.d.element_info.has(str(el)):
		return DB.el_color(el).lerp(Color.WHITE, 0.25)
	return Color(0.6, 0.95, 1.0)


## A laser: a white-hot core inside a wide colored glow, a muzzle flash and a splash where it lands.
func _beam(from: Vector2, to: Vector2, col: Color, width: float) -> void:
	fx_layer.lines.append({"a": from, "b": to, "col": Color(col.r, col.g, col.b, 0.55), "w": width * 2.6, "life": 0.2, "max": 0.2})
	fx_layer.lines.append({"a": from, "b": to, "col": col, "w": width * 1.4, "life": 0.18, "max": 0.18})
	fx_layer.lines.append({"a": from, "b": to, "col": Color(1, 1, 1), "w": maxf(1.0, width * 0.5), "life": 0.15, "max": 0.15})
	fx_layer.rings.append({"pos": from, "r0": 2.0, "r1": 10.0 + width * 2.0, "life": 0.16, "max": 0.16, "col": col.lerp(Color.WHITE, 0.5), "w": 2.0})
	for i in 10:
		var a := rng.randf() * TAU
		fx_layer.parts.append({"pos": to, "vel": Vector2(cos(a), sin(a)) * rng.randf_range(40, 140), "life": 0.3, "max": 0.3, "col": col.lerp(Color.WHITE, rng.randf()), "size": 2.0})


## The Blessed step sideways out of the world when an ordinary weapon swings at them.
func _blink(b: Battler, dodge: bool) -> void:
	var s: EnemySprite = b.node
	var c := _center(b)
	Audio.sfx("cast", -4.0, 1.6, 0.0)
	for i in 14:
		fx_layer.parts.append({"pos": c + Vector2(rng.randf_range(-10, 10), rng.randf_range(-18, 18)), "vel": Vector2(rng.randf_range(-30, 30), rng.randf_range(-50, -10)),
							   "life": 0.4, "max": 0.4, "col": Color(0.85, 0.97, 1.0), "size": 2.0})
	for i in 4:
		s.fade = 0.15 if i % 2 == 0 else 0.6
		await _wait(0.04)
	s.fade = 0.0
	var spot := b.home
	if not dodge:
		spot = Vector2(clampf(b.home.x + rng.randf_range(-60, 60), 30, 230), clampf(b.home.y + rng.randf_range(-20, 20), 110, 166))
		b.home = spot
	s.position = spot + (Vector2(rng.randf_range(-24, 24), 0) if dodge else Vector2.ZERO)
	await _wait(0.12)
	s.position = spot
	fx_layer.rings.append({"pos": _center(b), "r0": 18.0, "r1": 2.0, "life": 0.2, "max": 0.2, "col": Color(0.85, 0.97, 1.0), "w": 2.0})
	for i in 4:
		s.fade = 0.6 if i % 2 == 0 else 1.0
		await _wait(0.04)
	s.fade = 1.0


func _do_attack(b: Battler, targets: Array, power := 1.0, el_override = null, label := "") -> void:
	var side := foes if b.side == "party" else party
	targets = _retarget(targets, side)
	if targets.is_empty():
		return
	var tgt: Battler = targets[0]
	var el = el_override
	if el == null and b.side == "party":
		el = b.st.wel
	if label != "":
		_banner(label)
	var bow: bool = b.side == "party" and b.st.wkind == "bow"
	var bst := _blessed_style(b)
	var gun: bool = bst in ["rifle", "pistol"]
	# step forward
	if b.side == "party":
		b.node.set_frame(2)
		if not bow:
			await _move(b.node, b.home + Vector2(-34, 0), 0.12)
		await _play_seq(b, "thrust" if gun else {"bow": "shoot", "staff": "thrust"}.get(str(b.st.wkind), "slash"))
	else:
		await _move(b.node, b.home + Vector2(14, 0), 0.1)
	var ecol := _energy_col(b)
	if gun:
		var muzzle := _center(b) + Vector2(-22 if b.side == "party" else 22, 2)
		Audio.sfx("laser", -2.0, 1.0 if bst == "rifle" else 1.35, 0.05)
		_beam(muzzle, _center(tgt), ecol, 3.0 if bst == "rifle" else 2.0)
		if bst == "pistol":
			await _wait(0.09)
			Audio.sfx("laser", -4.0, 1.5, 0.05)
			_beam(muzzle, _center(tgt) + Vector2(0, -6), ecol, 2.0)
		await _wait(0.08)
	elif bst != "":
		# energy blades and staves: a searing arc of light
		Audio.sfx("laser_swing", -2.0)
		var c := _center(tgt)
		for i in 3:
			var off := Vector2(0, (i - 1) * 6)
			fx_layer.lines.append({"a": c + off + Vector2(-22, -18), "b": c + off + Vector2(22, 18), "col": ecol if i != 1 else Color.WHITE, "w": 3.0 if i == 1 else 2.0, "life": 0.22, "max": 0.22})
		fx_layer.rings.append({"pos": c, "r0": 6.0, "r1": 30.0, "life": 0.25, "max": 0.25, "col": ecol, "w": 3.0})
	else:
		Audio.sfx("bow" if bow else ("swing" if b.side == "party" else "enemy_attack"), -3.0)
		if bow:
			fx_layer.lines.append({"a": _center(b), "b": _center(tgt), "col": DB.el_color(el) if el != null else Color(0.9, 0.9, 0.8), "w": 1.0, "life": 0.18, "max": 0.18})
			await _wait(0.12)
	_slash(_center(tgt), el)
	# hit or miss
	var hit_chance := clampf(0.93 + (float(b.st.dex) - float(tgt.st.dex) * 0.5 - float(tgt.st.spd) * 0.3) * 0.004, 0.72, 0.99)
	if tgt.status.has("elsewhere"):
		_pop(tgt, "Miss", Color.WHITE, "not here", Color(0.7, 0.6, 1.0))
		Audio.sfx("miss")
	elif tgt.side == "foe" and tgt.e.get("blessed", false) and bst == "" and rng.randf() < 0.45:
		# an ordinary weapon can't keep track of them; their own tech can
		_pop(tgt, "Teleported", Color(0.85, 0.97, 1.0))
		await _blink(tgt, true)
	elif rng.randf() > hit_chance:
		_pop(tgt, "Miss", Color.WHITE)
		Audio.sfx("miss")
	elif tgt.side == "party" and rng.randf() < min(0.4, _fx(tgt, "dodge")):
		_pop(tgt, "Evade", Color(0.7, 1.0, 0.9))
		Audio.sfx("miss")
	else:
		var a := _phys_power(b)
		var d := _def_of(tgt, false) * (1.0 - minf(0.8, _fx(b, "pierce")))
		var mult := _el_mult(el, tgt)
		var crit := b.side == "party" and rng.randf() < 0.05 + float(b.st.dex) * 0.0015 + _fx(b, "crit")
		var dmg := _formula(a, d) * power * rng.randf_range(0.9, 1.1) * mult * (1.6 if crit else 1.0)
		# Blessed tech against ordinary flesh: no contest. Against the Blessed themselves: an even fight.
		overload = b.side == "party" and bst != "" and tgt.side == "foe" and not tgt.e.get("blessed", false)
		if overload:
			# ordinary creatures can't resist it at all
			if mult < 1.0:
				dmg /= maxf(0.1, mult)
				mult = 1.0
			dmg *= 3.0
		await _wait(0.05)
		phys_hit = bst == ""
		var dealt := _hurt(tgt, int(dmg), el, mult, crit)
		phys_hit = false
		overload = false
		if b.side == "party" and b.alive():
			var dr := _fx(b, "drain")
			if dr > 0.0 and b.hp < b.maxhp:
				_heal(b, max(1, int(dealt * dr)))
			# physical hits restore a little MP
			if b.maxmp > 0 and b.mp < b.maxmp:
				var gain: int = max(1, int(round(b.maxmp * (0.03 + _fx(b, "mp_hit")))))
				gain = min(gain, b.maxmp - b.mp)
				b.mp += gain
				_pop_mp(b, gain)
	await _wait(0.18)
	if b.side == "party":
		if not bow:
			await _move(b.node, b.home, 0.1)
		b.node.set_frame(0 if b.alive() else 6)
	else:
		await _move(b.node, b.home, 0.1)


## Animation strips in the LPC battle sheet: (first frame, count).
const SEQ := {"slash": [10, 6], "shoot": [16, 8], "thrust": [24, 8], "spellcast": [32, 7]}


func _play_seq(b: Battler, seq_name: String, fps := 18.0) -> void:
	var sq: Array = SEQ[seq_name]
	for i in int(sq[1]):
		if not is_instance_valid(b.node) or not b.alive():
			return
		b.node.set_frame(int(sq[0]) + i)
		await _wait(1.0 / fps)


func _move(n: Node2D, to: Vector2, dur: float) -> void:
	var tw := create_tween()
	tw.tween_property(n, "position", to, dur)
	await tw.finished


func _slash(p: Vector2, el) -> void:
	var col := DB.el_color(el) if el != null else Color(1, 1, 1)
	for i in 3:
		var off := Vector2(rng.randf_range(-6, 6), rng.randf_range(-6, 6))
		fx_layer.lines.append({"a": p + off + Vector2(-10, -10), "b": p + off + Vector2(10, 10), "col": col.lerp(Color.WHITE, 0.5), "w": 1.0, "life": 0.18, "max": 0.18})
	for i in 6:
		fx_layer.parts.append({"pos": p, "vel": Vector2(rng.randf_range(-60, 60), rng.randf_range(-60, 40)), "life": 0.3, "max": 0.3, "col": col, "size": 2.0})


# ---- magic

func _spell_power(b: Battler, el: String) -> float:
	var a := float(b.st.mag)
	if b.side == "party":
		a += float(b.st.get("matk", 0.0)) * 0.5
		var pieces := GS.element_pieces(b.m, el)
		a *= 1.0 + 0.15 * max(0, pieces - 1)
	if b.status.has("mag"):
		a *= 1.3
	return a * (1.0 + _fx(b, "spell"))


func _do_spell(b: Battler, sid: String, targets: Array, pay: bool) -> void:
	var sp: Dictionary = DB.d.spells[sid]
	if pay:
		b.mp -= int(sp.mp)
	await _cast_anim(b, sp.name, sp.el)
	match sp.kind:
		"dmg", "hex", "drain":
			targets = _retarget(targets, foes if b.side == "party" else party)
			for tg in targets:
				_burst(_center(tg), sp.el, 22)
			Audio.sfx("spell_" + sp.el)
			await _wait(0.35)
			for tg in targets:
				if not tg.alive():
					continue
				var mult := _el_mult(sp.el, tg)
				var dmg := _formula(_spell_power(b, sp.el), _def_of(tg, true)) * float(sp.power) * rng.randf_range(0.92, 1.08) * mult
				var dealt := _hurt(tg, int(dmg), sp.el, mult)
				if sp.kind == "hex" and tg.alive():
					tg.status["mdef_down"] = 3
				if sp.kind == "drain":
					_heal(b, int(dealt * 0.5))
		"heal":
			Audio.sfx("heal")
			for tg in targets:
				if tg.alive():
					_burst(_center(tg), "heal", 14)
			await _wait(0.3)
			var amt := DB.spell_heal(_spell_power(b, sp.el), b.level, float(sp.power), GS.element_pieces(b.m, sp.el))
			for tg in targets:
				if tg.alive():
					_heal(tg, amt)
		"revive":
			Audio.sfx("revive")
			for tg in targets:
				_burst(_center(tg), "spirit", 20)
			await _wait(0.35)
			for tg in targets:
				if not tg.alive():
					tg.hp = max(1, int(tg.maxhp * float(sp.power)))
					tg.node.set_frame(0)
					_pop(tg, "Revived", Color(1, 1, 0.7))
				else:
					_pop(tg, "No effect", Color.WHITE)
		"buff":
			Audio.sfx("buff")
			for tg in targets:
				if tg.alive():
					tg.status[sp.stat] = 4
					_burst(_center(tg), "buff", 14)
					_pop(tg, {"str": "STR up", "spd": "Haste", "def": "DEF up", "mag": "MAG up"}.get(sp.stat, "Up"), Color(1, 0.9, 0.5))
			await _wait(0.3)
	await _wait(0.25)
	if b.side == "party" and b.alive():
		b.node.set_frame(0)


func _cast_anim(b: Battler, label: String, el) -> void:
	_banner(label)
	if b.side == "party":
		_play_seq(b, "spellcast")
	else:
		b.node.mat.set_shader_parameter("tint", DB.el_color(el) if el != "heal" else Color.WHITE)
		b.node.mat.set_shader_parameter("tint_amount", 0.6)
	Audio.sfx("cast")
	for i in 10:
		var c := _center(b)
		fx_layer.parts.append({"pos": c + Vector2(rng.randf_range(-14, 14), rng.randf_range(4, 14)), "vel": Vector2(0, rng.randf_range(-50, -20)),
							   "life": 0.4, "max": 0.4, "col": DB.el_color(el) if DB.d.element_info.has(str(el)) else Color(1, 1, 0.8), "size": 2.0})
	await _wait(0.4)
	if b.side == "foe" and is_instance_valid(b.node):
		b.node.mat.set_shader_parameter("tint_amount", 0.0)


func _burst(p: Vector2, el, n: int) -> void:
	var e := str(el)
	for i in n:
		var part := {"pos": p, "vel": Vector2.ZERO, "life": rng.randf_range(0.35, 0.7), "max": 0.7, "col": Color.WHITE, "size": 2.0}
		match e:
			"fire":
				part.pos = p + Vector2(rng.randf_range(-12, 12), rng.randf_range(0, 10))
				part.vel = Vector2(rng.randf_range(-15, 15), rng.randf_range(-80, -30))
				part.col = [Color(1, 0.35, 0.1), Color(1, 0.7, 0.2), Color(1, 0.95, 0.5)][i % 3]
				part.size = 3.0
			"water":
				var a := rng.randf() * TAU
				part.vel = Vector2(cos(a), sin(a) * 0.6) * rng.randf_range(30, 80) + Vector2(0, -30)
				part.acc = Vector2(0, 200)
				part.col = [Color(0.3, 0.6, 1.0), Color(0.7, 0.9, 1.0)][i % 2]
			"wind":
				var a := float(i) / n * TAU
				part.pos = p + Vector2(cos(a), sin(a) * 0.5) * 16
				part.vel = Vector2(-sin(a), cos(a) * 0.5) * 90
				part.col = [Color(0.3, 0.9, 0.8), Color(0.9, 1, 1)][i % 2]
			"stone":
				part.pos = p + Vector2(rng.randf_range(-16, 16), -50 - rng.randf_range(0, 20))
				part.vel = Vector2(0, rng.randf_range(80, 140))
				part.acc = Vector2(0, 220)
				part.col = [Color(0.45, 0.4, 0.35), Color(0.4, 0.75, 0.3)][i % 2]
				part.size = 3.0
				part.life = 0.5
			"spirit":
				part.pos = p + Vector2(rng.randf_range(-10, 10), rng.randf_range(-20, 20))
				part.vel = Vector2(0, rng.randf_range(-40, -10))
				part.col = Color(1, 1, 0.9)
			"void":
				var a := rng.randf() * TAU
				part.pos = p + Vector2(cos(a), sin(a)) * rng.randf_range(16, 26)
				part.vel = (p - part.pos) * 2.2
				part.col = [Color(0.6, 0.3, 1.0), Color(0.15, 0.05, 0.3)][i % 2]
			"heal":
				part.pos = p + Vector2(rng.randf_range(-10, 10), rng.randf_range(0, 14))
				part.vel = Vector2(0, rng.randf_range(-45, -20))
				part.col = [Color(0.5, 1, 0.6), Color(0.9, 1, 0.9)][i % 2]
			"buff":
				part.pos = p + Vector2(rng.randf_range(-10, 10), rng.randf_range(0, 14))
				part.vel = Vector2(0, rng.randf_range(-45, -20))
				part.col = Color(1, 0.85, 0.4)
			_:
				var a := rng.randf() * TAU
				part.vel = Vector2(cos(a), sin(a)) * rng.randf_range(30, 70)
				part.col = Color(1, 1, 1)
		fx_layer.parts.append(part)
	if e == "spirit":
		fx_layer.lines.append({"a": p + Vector2(0, -60), "b": p + Vector2(0, 20), "col": Color(1, 1, 0.9), "w": 6.0, "life": 0.35, "max": 0.35})


# ---- summons

func _do_summon(b: Battler, sid: String) -> void:
	var sd: Dictionary = DB.d.summons[sid]
	b.mp -= int(sd.mp)
	await _cast_anim(b, sd.name, sd.el)
	var tex := Art.tex("res://assets/summons/%s.png" % sid)
	fx_layer.flashes.append({"col": DB.el_color(sd.el), "a": 0.6, "life": 0.5, "max": 0.5})
	Audio.sfx("summon")
	fx_layer.summon = {"tex": tex, "pos": Vector2(-120, 20), "a": 0.0}
	var tw := create_tween()
	tw.tween_property(self, "_summon_pos", Vector2(90, 30), 0.5).from(Vector2(-120, 20))
	tw.parallel().tween_property(self, "_summon_a", 1.0, 0.4).from(0.0)
	await tw.finished
	await _wait(0.4)
	for tg in _living(foes):
		_burst(_center(tg), sd.el, 30)
	fx_layer.flashes.append({"col": Color.WHITE, "a": 0.7, "life": 0.3, "max": 0.3})
	shake = 5.0
	Audio.sfx("spell_" + sd.el)
	await _wait(0.3)
	var power := float(sd.power)
	for tg in _living(foes):
		var mult := _el_mult(sd.el, tg)
		var d := 0.0 if sd.effect == "dmg_pierce" else _def_of(tg, true)
		var dmg := _formula(_spell_power(b, sd.el) * 1.1, d) * power * rng.randf_range(0.95, 1.05) * mult
		_hurt(tg, int(dmg), sd.el, mult)
		if sd.effect == "dmg_hex" and tg.alive():
			tg.status["mdef_down"] = 3
	await _wait(0.3)
	match sd.effect:
		"dmg_heal":
			for p in _living(party):
				_heal(p, int(p.maxhp * 0.3))
		"dmg_haste":
			for p in _living(party):
				p.status["spd"] = 4
				_pop(p, "Haste", Color(1, 0.9, 0.5))
		"dmg_guard":
			for p in _living(party):
				p.status["def"] = 4
				_pop(p, "DEF up", Color(1, 0.9, 0.5))
		"dmg_revive":
			for p in party:
				if not p.alive():
					p.hp = int(p.maxhp * 0.3)
					p.node.set_frame(0)
					_pop(p, "Revived", Color(1, 1, 0.7))
				else:
					_heal(p, int(p.maxhp * 0.2))
		"dmg_fullheal":
			for p in party:
				if not p.alive():
					p.node.set_frame(0)
				p.hp = p.maxhp
				_pop(p, "Restored", Color(0.6, 1, 0.6))
	var tw2 := create_tween()
	tw2.tween_property(self, "_summon_a", 0.0, 0.4)
	await tw2.finished
	fx_layer.summon = {}
	if b.alive():
		b.node.set_frame(0)


var _summon_pos := Vector2.ZERO:
	set(v):
		_summon_pos = v
		if fx_layer and not fx_layer.summon.is_empty():
			fx_layer.summon.pos = v
var _summon_a := 0.0:
	set(v):
		_summon_a = v
		if fx_layer and not fx_layer.summon.is_empty():
			fx_layer.summon.a = v


# ---- limit breaks

func _do_limit(b: Battler, targets: Array) -> void:
	b.limit = 0.0
	var lid: String = DB.d.characters[b.id].limit
	var lim: Dictionary = DB.d.limits[lid]
	_banner(lim.name)
	fx_layer.flashes.append({"col": Color(1, 0.95, 0.7), "a": 0.5, "life": 0.4, "max": 0.4})
	Audio.sfx("limit")
	await _wait(0.4)
	match lid:
		"kindlers_wrath":
			var els := GS.aura_colors(b.m)
			if els.is_empty():
				els = [null]
			for el in els:
				if _living(foes).is_empty():
					break
				var tg := targets if not targets.is_empty() and targets[0].alive() else [_rand_foe()]
				await _do_attack(b, tg, 1.35, el)
		"pit_fury":
			for i in 4:
				if _living(foes).is_empty():
					break
				await _do_attack(b, [_rand_foe()], 0.95, "fire")
		"thousand_feathers":
			for i in 8:
				if _living(foes).is_empty():
					break
				await _do_attack(b, [_rand_foe()], 0.55, "wind")
		"lighthouse_beam":
			b.node.set_frame(4)
			fx_layer.lines.append({"a": _center(b), "b": Vector2(0, 120), "col": Color(1, 1, 0.8), "w": 8.0, "life": 0.6, "max": 0.6})
			for tg in _living(foes):
				_burst(_center(tg), "water", 24)
			await _wait(0.4)
			for tg in _living(foes):
				var mult := _el_mult("water", tg)
				_hurt(tg, int(_formula(_spell_power(b, "water"), _def_of(tg, true)) * 1.15 * mult), "water", mult)
			for p in _living(party):
				_heal(p, int(p.maxhp * 0.3))
		"mountains_embrace":
			b.node.set_frame(4)
			for p in _living(party):
				p.status["bulwark"] = 3
				_heal(p, int(p.maxhp * 0.25))
				_burst(_center(p), "stone", 10)
			for tg in _living(foes):
				var mult := _el_mult("stone", tg)
				_hurt(tg, int(_formula(_phys_power(b), _def_of(tg, false)) * 0.6 * mult), "stone", mult)
			await _wait(0.4)
		"enlightenment":
			b.node.set_frame(4)
			for p in party:
				_burst(_center(p), "spirit", 20)
			await _wait(0.4)
			for p in party:
				p.hp = p.maxhp
				p.node.set_frame(0)
				_pop(p, "Restored", Color(0.6, 1, 0.6))
		"fade":
			var tg: Battler = targets[0] if not targets.is_empty() and targets[0].alive() else _rand_foe()
			if tg:
				b.node.set_fade(0.3)
				await _wait(0.25)
				_burst(_center(tg), "void", 40)
				var a := float(b.st.mag) + float(b.st.dex)
				_hurt(tg, int(1.15 * a * 2.4 * rng.randf_range(0.95, 1.05)), "void", 1.0)
				await _wait(0.2)
				b.node.set_fade(1.0)
	await _wait(0.3)
	if b.alive():
		b.node.set_frame(0)


func _rand_foe():
	var l := _living(foes)
	return l[rng.randi() % l.size()] if l.size() > 0 else null


# ---- items

func _do_item(b: Battler, id: String, targets: Array) -> void:
	var it: Dictionary = DB.d.items[id]
	if not GS.items.has(id):
		_banner("Out of %s." % it.name)
		return
	GS.take_item(id)
	_banner(it.name)
	b.node.set_frame(4)
	await _wait(0.25)
	match it.effect:
		"flee":
			await _do_flee(b, true)
			return
		"heal_pct":
			for tg in targets:
				if tg.alive():
					_burst(_center(tg), "heal", 12)
					_heal(tg, int(tg.maxhp * float(it.v)))
			Audio.sfx("heal")
		"mp_pct":
			for tg in targets:
				if tg.alive():
					var before: int = tg.mp
					tg.mp = min(tg.maxmp, tg.mp + int(tg.maxmp * float(it.v)))
					_pop(tg, "+%d MP" % (tg.mp - before), Color(0.6, 0.75, 1.0))
			Audio.sfx("heal")
		"revive":
			for tg in targets:
				if not tg.alive():
					tg.hp = max(1, int(tg.maxhp * float(it.v)))
					tg.node.set_frame(0)
					_burst(_center(tg), "spirit", 16)
					_pop(tg, "Revived", Color(1, 1, 0.7))
			Audio.sfx("revive")
		"full":
			for tg in targets:
				if not tg.alive():
					tg.node.set_frame(0)
				tg.hp = tg.maxhp
				tg.mp = tg.maxmp
				_pop(tg, "Restored", Color(0.6, 1, 0.6))
			Audio.sfx("heal")
		"boost":
			for tg in targets:
				if tg.alive():
					tg.m.boosts[it.stat] = int(it.get("n", GS.BOOST_BATTLES))
					tg.status[it.stat] = 99
					tg.node.set_glow(true)
					_burst(_center(tg), "buff", 18)
					_pop(tg, "%s up!" % it.stat.to_upper(), Color(1, 0.9, 0.5))
			Audio.sfx("boost")
	await _wait(0.35)
	if b.alive():
		b.node.set_frame(0)


func _do_flee(_b: Battler, sure: bool) -> void:
	if not opts.get("flee", true):
		_banner("Can't escape!")
		Audio.sfx("buzzer")
		await _wait(0.5)
		return
	var ps := 0.0
	for p in _living(party):
		ps += p.spd()
	ps /= max(1, _living(party).size())
	var es := 0.0
	for f in _living(foes):
		es += f.spd()
	es /= max(1, _living(foes).size())
	var chance := clampf(0.55 + (ps - es) * 0.02, 0.25, 0.95)
	if sure or rng.randf() < chance:
		_banner("Escaped!")
		Audio.sfx("flee")
		for p in _living(party):
			p.node.flip_h = true
			p.node.set_frame(2)
			_move(p.node, p.home + Vector2(80, 0), 0.4)
		await _wait(0.5)
		_finish_battle("flee")
	else:
		_banner("Couldn't escape!")
		Audio.sfx("buzzer")
		await _wait(0.5)


# ------------------------------------------------------------------ enemy AI

func _enemy_ai(b: Battler) -> Dictionary:
	var e: Dictionary = b.e
	if e.unique and e.ai.size() > 0:
		var total := 0.0
		for mv in e.ai:
			total += float(mv.w)
		var r := rng.randf() * total
		for mv in e.ai:
			r -= float(mv.w)
			if r <= 0:
				return {"type": "enemy", "move": mv}
		return {"type": "enemy", "move": e.ai[0]}
	var roll := rng.randf()
	if e.caster and roll < 0.35:
		return {"type": "enemy", "move": {"k": "spell", "el": b.el, "power": 0.75 if rng.randf() < 0.3 else 1.0,
										  "target": "all" if rng.randf() < 0.3 else "one", "name": _spell_name(b.el)}}
	if e.skills.size() > 0 and roll < 0.6:
		return {"type": "enemy", "move": {"k": "skill", "s": e.skills[rng.randi() % e.skills.size()]}}
	return {"type": "enemy", "move": {"k": "attack"}}


func _spell_name(el) -> String:
	return {"fire": "Ember", "water": "Splash", "wind": "Gust", "stone": "Shard", "spirit": "Radiance", "void": "Hex"}.get(str(el), "Spell")


func _rand_party() -> Battler:
	var l := _living(party)
	# enemies slightly prefer the front of the line and wounded targets
	var weights := []
	var total := 0.0
	for i in l.size():
		var w: float = 1.0 + (0.3 if i == 0 else 0.0) + (0.4 if float(l[i].hp) / l[i].maxhp < 0.35 else 0.0)
		weights.append(w)
		total += w
	var r := rng.randf() * total
	for i in l.size():
		r -= weights[i]
		if r <= 0:
			return l[i]
	return l[0]


func _do_enemy(b: Battler, act: Dictionary) -> void:
	var mv: Dictionary = act.move
	if _living(party).is_empty():
		return
	if mv.has("say"):
		message = mv.say
		await _wait(1.4)
		message = ""
	var nm: String = mv.get("name", "")
	match mv.k:
		"blink":
			_banner("Blink")
			await _blink(b, false)
		"doze":
			_banner("Zzz...")
			for i in 4:
				fx_layer.nums.append({"text": "z", "pos": _center(b) + Vector2(10 + i * 5, -10 - i * 6), "t": float(i) * -0.2, "col": Color(0.85, 0.9, 1.0)})
			await _wait(0.9)
		"attack":
			await _do_attack(b, [_rand_party()], 1.0, null, nm)
		"skill":
			var sk: Dictionary = DB.d.enemy_skills[mv.s]
			_banner(sk.name)
			var targets := _living(party) if sk.target == "all" else [_rand_party()]
			if sk.kind == "mag":
				await _cast_anim(b, sk.name, b.el)
				for tg in targets:
					_burst(_center(tg), b.el, 14)
				await _wait(0.3)
				for tg in targets:
					var mult := _el_mult(b.el, tg)
					_hurt(tg, int(_formula(float(b.st.mag), _def_of(tg, true)) * float(sk.power) * rng.randf_range(0.9, 1.1) * mult), b.el, mult)
			else:
				await _move(b.node, b.home + Vector2(14, 0), 0.1)
				Audio.sfx("enemy_attack")
				for tg in targets:
					_slash(_center(tg), null)
					phys_hit = true
					_hurt(tg, int(_formula(_phys_power(b), _def_of(tg, false)) * float(sk.power) * rng.randf_range(0.9, 1.1)), null, 1.0)
					phys_hit = false
					if sk.has("stun") and tg.alive() and rng.randf() < 0.35:
						tg.status["stun"] = int(sk.stun)
						_pop(tg, "Stunned", Color(1, 0.9, 0.4))
				await _wait(0.2)
				await _move(b.node, b.home, 0.1)
		"spell":
			var el = b.el if str(mv.get("el", "self")) == "self" else mv.el
			var sname: String = nm if nm != "" else _spell_name(el)
			await _cast_anim(b, sname, el)
			var targets := _living(party) if mv.get("target", "one") == "all" else [_rand_party()]
			for tg in targets:
				_burst(_center(tg), el, 20)
			Audio.sfx("spell_" + str(el))
			await _wait(0.35)
			for tg in targets:
				if tg.alive():
					var mult := _el_mult(el, tg)
					_hurt(tg, int(_formula(float(b.st.mag) * (1.3 if b.status.has("mag") else 1.0), _def_of(tg, true)) * float(mv.power) * rng.randf_range(0.92, 1.08) * mult), el, mult)
		"drain":
			var tg := _rand_party()
			await _cast_anim(b, nm if nm != "" else "Drain", b.el)
			_burst(_center(tg), "void", 20)
			await _wait(0.3)
			var mult := _el_mult(b.el, tg)
			var dealt := _hurt(tg, int(_formula(float(b.st.mag), _def_of(tg, true)) * float(mv.get("power", 1.0)) * mult), b.el, mult)
			_heal(b, int(dealt * 0.6))
		"buff":
			_banner(nm if nm != "" else "Power up")
			b.status[mv.stat] = 4
			_burst(_center(b), "buff", 16)
			Audio.sfx("buff")
			await _wait(0.5)
		"dispel":
			_banner(nm if nm != "" else "Dispel")
			Audio.sfx("dispel")
			for p in _living(party):
				for k in ["str", "def", "mag", "spd", "bulwark"]:
					p.status.erase(k)
				_burst(_center(p), "void", 8)
			b.status["str"] = 3
			await _wait(0.5)
		"heal":
			_banner(nm if nm != "" else "Regenerate")
			_burst(_center(b), "heal", 18)
			Audio.sfx("heal")
			await _wait(0.3)
			_heal(b, int(b.maxhp * 0.1))
		"stun":
			var tg := _rand_party()
			_banner(nm if nm != "" else "Stun")
			_burst(_center(tg), b.el, 14)
			Audio.sfx("stun")
			await _wait(0.3)
			tg.status["stun"] = int(mv.get("turns", 1))
			_pop(tg, "Stunned", Color(1, 0.9, 0.4))
		"silence":
			var tg := _rand_party()
			_banner(nm if nm != "" else "Silence")
			Audio.sfx("silence")
			await _wait(0.3)
			tg.status["silence"] = 3
			_pop(tg, "Silenced", Color(0.8, 0.7, 1.0))
		"summon":
			if _living(foes).size() < 3:
				var spec: String = mv.species
				var e := DB.make_enemy(spec, max(1, b.level - 2), str(b.el))
				var slot := Vector2(b.home.x + 70, b.home.y - 10 + rng.randf_range(-20, 20))
				slot.x = clampf(slot.x, 30, 250)
				slot.y = clampf(slot.y, 90, 166)
				var nb := _add_foe(e, slot)
				nb.node.modulate.a = 0.0
				var tw := create_tween()
				tw.tween_property(nb.node, "modulate:a", 1.0, 0.4)
				_banner("%s appears!" % e.name)
				Audio.sfx("summon_minion")
				await _wait(0.5)
			else:
				await _do_attack(b, [_rand_party()])
		"steal_gold":
			var amt: int = min(GS.gold, 20 + b.level * 6)
			GS.gold -= amt
			_banner(nm if nm != "" else "Steal")
			Audio.sfx("coins")
			message = "%s snatched %d gold!" % [b.name, amt]
			await _wait(1.0)
			message = ""
		"shift":
			var opts_el: Array = b.e.shift
			var i := opts_el.find(b.el)
			b.el = opts_el[(i + 1) % opts_el.size()]
			_banner("Iris becomes %s" % DB.el_name(b.el))
			b.node.mat.set_shader_parameter("tint", DB.el_color(b.el))
			b.node.mat.set_shader_parameter("tint_amount", 0.35 if b.el == "void" else 0.0)
			_burst(_center(b), b.el, 24)
			Audio.sfx("shift")
			await _wait(0.6)
		"elsewhere":
			b.status["elsewhere"] = 3
			b.node.fade = 0.45
			_banner("Elsewhere")
			Audio.sfx("fade")
			await _wait(0.5)
	if b.alive() and not b.status.has("elsewhere") and b.node is EnemySprite and b.node.fade < 1.0:
		b.node.fade = 1.0


func _check_phase(b: Battler) -> void:
	if b.side != "foe" or b.e.phases.is_empty():
		return
	if b.phase_i >= b.e.phases.size():
		return
	var ph: Dictionary = b.e.phases[b.phase_i]
	if float(b.hp) / b.maxhp <= float(ph.at):
		b.phase_i += 1
		message = ph.say
		if ph.has("buff"):
			b.status[ph.buff] = 99
		if ph.has("debuff_self"):
			b.st[ph.debuff_self] = int(b.st[ph.debuff_self] * 0.6)
		_burst(_center(b), b.el, 30)
		Audio.sfx("phase")
		await _wait(2.0)
		message = ""


# ------------------------------------------------------------------ end of battle

func _check_end() -> void:
	if ended:
		return
	if _living(foes).is_empty():
		await _victory()
	elif _living(party).is_empty():
		await _defeat()


func _sync_party() -> void:
	for p in party:
		p.m.hp = p.hp
		p.m.mp = p.mp
		p.m.limit = p.limit


func _victory() -> void:
	ended = true
	phase = "results"
	_close_menu()
	_sync_party()
	var waited := 0.0
	while dying > 0 and waited < 2.5:
		await _wait(0.1)
		waited += 0.1
	await _wait(0.5)
	for p in _living(party):
		p.node.set_frame(7)
	Audio.play_once("victory")
	var xp := 0
	var gold := 0
	var drops := []
	for f in foes:
		xp += int(f.e.xp)
		gold += int(f.e.gold)
		if rng.randf() < (0.15 if not f.e.unique else 1.0):
			var pool := ["potion", "potion", "ether", "hi_potion", "stamina_tonic", "feather"]
			if f.e.unique:
				pool = ["hi_potion", "elixir", "feather", "sage_elixir", "might_elixir"]
			drops.append(pool[rng.randi() % pool.size()])
	var gold_fx := 0.0
	for p in party:
		gold_fx = max(gold_fx, _fx(p, "gold"))
	gold = int(round(gold * (1.0 + gold_fx)))
	GS.gold += gold
	result_lines = ["Victory!", "Gained %d XP and %d gold." % [xp, gold]]
	for d in drops:
		result_lines.append("Found %s." % GS.add_item(d))
	# weapons and armor can drop from any fight; tougher foes drop better gear
	var gear_found := []
	for f in foes:
		var gid := DB.roll_drop(str(f.e.el), str(f.e.tier), rng)
		if gid != "" and gear_found.size() < 2:
			gear_found.append(gid)
	for gid in gear_found:
		GS.add_item("gear:" + gid)
		result_lines.append({"text": "Found %s! (%s)" % [DB.d.gear[gid].name, DB.tier_name(gid)], "gear": gid})
		Audio.sfx("chest")
	# their weapons outlast them
	var blessed_count := 0
	for f in foes:
		if f.e.get("blessed", false):
			blessed_count += 1
	if blessed_count > 0:
		var first := not GS.flag("blessed_salvaged")
		if first or rng.randf() < 0.3 + 0.1 * blessed_count:
			var pool: Array = DB.d.get("blessed_gear", [])
			if not pool.is_empty():
				var gid: String = pool[rng.randi() % pool.size()]
				GS.add_item("gear:" + gid)
				GS.flags["blessed_salvaged"] = true
				var sal: Array = DB.d.blessed_lines.get("salvage", [])
				if not sal.is_empty():
					result_lines.append(str(sal[rng.randi() % sal.size()]))
				result_lines.append({"text": "Salvaged %s! (Blessed)" % DB.d.gear[gid].name, "gear": gid})
				Audio.sfx("chest")
	var ups := []
	for id in GS.roster:
		var m: Dictionary = GS.roster[id]
		var in_party := GS.party.has(id)
		if in_party and m.hp <= 0:
			continue
		var gained := xp if in_party else int(xp * 0.5)
		if in_party:
			for p in party:
				if p.m == m:
					gained = int(round(gained * (1.0 + _fx(p, "xp"))))
		for up in GS.give_xp(m, gained):
			var g: Dictionary = up.gains
			ups.append("%s reached Lv %d!  HP+%d STR+%d DEF+%d MAG+%d SPD+%d DEX+%d" % [DB.d.characters[id].name, up.level,
				g.hp, g.str, g.def, g.mag, g.spd, g.dex])
			var new_spells := DB.spells_for(GS.spell_elements(m), up.level).filter(
				func(s): return int(DB.d.spells[s].lv) == up.level)
			for s in new_spells:
				ups.append("%s learned %s!" % [DB.d.characters[id].name, DB.d.spells[s].name])
	GS.tick_boosts()
	await _show_results(ups)
	_finish_battle("win")


func _show_results(ups: Array) -> void:
	Inp.block(3)
	# wait for the player to read, revealing level-ups one at a time
	while true:
		await get_tree().process_frame
		if Inp.ok() or Inp.back():
			if ups.is_empty():
				break
			var u: String = ups.pop_front()
			result_lines.append(u)
			if result_lines.size() > 7:
				result_lines.remove_at(1)
			Audio.sfx("levelup" if u.contains("reached") else "learn")


func _defeat() -> void:
	ended = true
	_close_menu()
	_sync_party()
	await _wait(0.8)
	Audio.music("gameover", 0.8)
	phase = "gameover"
	gameover_idx = 0
	Inp.block(10)


func _gameover_input() -> void:
	var v := Inp.vert()
	if v:
		gameover_idx = wrapi(gameover_idx + v, 0, 3)
		Audio.sfx("cursor")
	if Inp.ok():
		Audio.sfx("confirm")
		_finish_battle(["retry", "load", "title"][gameover_idx])


func _finish_battle(res: String) -> void:
	ended = true
	_sync_party()
	for p in party:
		p.m.limit = p.limit
	finished.emit(res)


# ------------------------------------------------------------------ drawing

func _draw() -> void:
	if bg_tex:
		draw_texture(bg_tex, Vector2.ZERO)
	for sp in splats:
		var a := clampf(sp.t, 0.0, 1.0)
		var c1 := Color(0.42, 0.0, 0.03) if not sp.get("ash", false) else Color(0.22, 0.2, 0.19)
		var c2 := Color(0.3, 0.0, 0.02) if not sp.get("ash", false) else Color(0.35, 0.32, 0.3)
		draw_circle(sp.p, sp.r, Color(c1.r, c1.g, c1.b, a * 0.85))
		draw_circle(sp.p + Vector2(sp.r, 0.5), sp.r * 0.6, Color(c2.r, c2.g, c2.b, a * 0.8))
	draw_rect(Rect2(0, FIELD_H, 480, 270 - FIELD_H), Color(0.02, 0.02, 0.06))


func _draw_ui(ci: Node2D) -> void:
	# enemy list
	var lr := Rect2(4, 178, 186, 88)
	Art.window(ci, lr)
	var y := lr.position.y + 6
	for f in foes:
		if not f.alive():
			continue
		Art.icon(ci, str(f.el), Vector2(lr.position.x + 8, y + 3))
		var nm: String = f.name
		if Art.width(nm) > 150:
			nm = nm.substr(0, 20) + "."
		Art.text(ci, Vector2(lr.position.x + 22, y), nm, Color(1, 1, 1) if not f.e.unique else Art.YELLOW)
		if f.e.unique:
			Art.bar(ci, Rect2(lr.position.x + 22, y + 15, 150, 4), float(f.hp) / f.maxhp, Color(0.95, 0.35, 0.35))
			y += 6
		y += 16
		if y > lr.end.y - 14:
			break
	# party panel
	var pr := Rect2(194, 178, 282, 88)
	Art.window(ci, pr)
	for i in party.size():
		var p: Battler = party[i]
		var py := pr.position.y + 6 + i * 19
		var col := Art.YELLOW if p == menu_for else (Art.RED if not p.alive() else Art.WHITE)
		Art.text(ci, Vector2(pr.position.x + 8, py), p.name, col)
		var st := ""
		if p.status.has("stun"):
			st = "STN"
		elif p.status.has("silence"):
			st = "SIL"
		elif p.status.has("bulwark") or p.status.has("def"):
			st = "DEF"
		elif p.status.has("spd"):
			st = "HST"
		if st != "":
			Art.text(ci, Vector2(pr.position.x + 62, py + 2), st, Color(0.8, 0.8, 1.0), 8, Art.font_small)
		Art.text_right(ci, Vector2(pr.position.x + 128, py), "%d" % p.hp, Art.RED if p.hp < p.maxhp * 0.25 else Art.WHITE)
		Art.text(ci, Vector2(pr.position.x + 130, py + 2), "/%d" % p.maxhp, Art.GREY, 8, Art.font_small)
		Art.text_right(ci, Vector2(pr.position.x + 192, py), "%d" % p.mp, Art.CYAN)
		# ATB and limit gauges
		var full := p.gauge >= 100.0
		var atb_col := Color(1, 0.9, 0.3) if full and fmod(t, 0.4) < 0.2 else Color(0.35, 0.7, 1.0)
		Art.bar(ci, Rect2(pr.position.x + 198, py + 4, 46, 5), p.gauge / 100.0, atb_col)
		var lim_col := Color(1.0, 0.45, 0.8) if p.limit >= 100.0 and fmod(t, 0.3) < 0.15 else Color(0.85, 0.35, 0.6)
		Art.bar(ci, Rect2(pr.position.x + 248, py + 4, 26, 5), p.limit / 100.0, lim_col)
	Art.text(ci, Vector2(pr.position.x + 198, pr.end.y - 12), "TIME", Art.GREY, 8, Art.font_small)
	Art.text(ci, Vector2(pr.position.x + 248, pr.end.y - 12), "LIMIT", Art.GREY, 8, Art.font_small)
	# spinning marker over the character whose turn it is
	if menu_for != null and phase == "fight" and menu_for.alive():
		_draw_marker(ci, menu_for.node.position + Vector2(0, -58.0 + sin(t * 4.0) * 2.0))
	# command menu
	if menu_for != null and phase == "fight":
		var cmds := _commands(menu_for)
		var cr := Rect2(4, 178, 186, 88)
		Art.window(ci, cr)
		for i in cmds.size():
			var c: String = cmds[i]
			var ccol := Color(1, 0.55, 0.85) if c == "Limit" else Art.WHITE
			var cxp := 22 + floori(i / 3.0) * (86 if cmds.size() <= 6 else 60)
			Art.text(ci, cr.position + Vector2(cxp, 10 + (i % 3) * 22), c, ccol if c != "Combo" else Color(1, 0.85, 0.4))
		if menu_state == "cmd":
			Art.cursor(ci, cr.position + Vector2(22 + floori(cmd_idx / 3.0) * (86 if cmds.size() <= 6 else 60), 10 + (cmd_idx % 3) * 22))
		Art.window(ci, Rect2(cr.position.x, cr.position.y - 20, 98, 19), "dark")
		Art.text(ci, Vector2(cr.position.x + 8, cr.position.y - 18), menu_for.name, Art.YELLOW)
		if menu_state in ["spell", "summon", "item", "combo"]:
			_draw_sub(ci, menu_for)
		if menu_state == "target":
			var lst := _target_list()
			for i in lst.size():
				if pending.get("all", false) or i == target_idx:
					var tb: Battler = lst[i]
					var p := _center(tb)
					if tb.side == "foe":
						Art.cursor(ci, p + Vector2(-_foe_h(tb) * 0.3 - 4, -6))
					else:
						Art.cursor(ci, p + Vector2(-10, -6))
			if not lst.is_empty():
				var tb: Battler = lst[clampi(target_idx, 0, lst.size() - 1)]
				var label: String = tb.name if not pending.get("all", false) else ("All enemies" if target_side == "foe" else "Whole party")
				var w := Art.width(label) + 16
				Art.window(ci, Rect2(240 - w / 2, 4, w, 20), "dark")
				Art.text_center(ci, Vector2(240, 6), label)
	# banner / messages
	if banner_t > 0 and message == "":
		var w := Art.width(banner) + 24
		Art.window(ci, Rect2(240 - w / 2, 6, w, 20), "dark")
		Art.text_center(ci, Vector2(240, 8), banner)
	if message != "":
		var lines := Art.wrap(message, 420)
		var r := Rect2(24, 6, 432, 12 + lines.size() * 15)
		Art.window(ci, r, "dark")
		for i in lines.size():
			Art.text(ci, r.position + Vector2(10, 5 + i * 15), lines[i], Art.YELLOW)
	if phase == "results":
		var r := Rect2(40, 30, 400, 20 + result_lines.size() * 16)
		Art.window(ci, r)
		for i in result_lines.size():
			var ln = result_lines[i]
			if ln is Dictionary:
				Art.text_fit(ci, r.position + Vector2(12, 8 + i * 16), ln.text, DB.tier_color(ln.gear, t), r.size.x - 24)
			else:
				Art.text_fit(ci, r.position + Vector2(12, 8 + i * 16), ln, Art.YELLOW if i == 0 else Art.WHITE, r.size.x - 24)
	if phase == "gameover":
		ci.draw_rect(Rect2(0, 0, 480, 270), Color(0, 0, 0, 0.7))
		Art.text_center(ci, Vector2(240, 80), "Your light fades...", Color(1, 0.6, 0.6), 16, Art.font_title)
		var r := Rect2(170, 120, 140, 60)
		Art.window(ci, r)
		var o := ["Retry battle", "Load a save", "Title screen"]
		for i in 3:
			Art.text(ci, r.position + Vector2(26, 6 + i * 16), o[i])
		Art.cursor(ci, r.position + Vector2(26, 6 + gameover_idx * 16))


## Little yellow upside-down triangle that spins around its vertical axis.
func _draw_marker(ci: Node2D, p: Vector2) -> void:
	var sx := cos(t * 5.0)
	var w := 6.0 * absf(sx)
	var front := sx >= 0.0
	var top := p.round()
	var col := Color(1.0, 0.9, 0.2) if front else Color(0.85, 0.62, 0.1)
	var pts := PackedVector2Array([top + Vector2(-w - 0.5, -6), top + Vector2(w + 0.5, -6), top + Vector2(0, 4)])
	ci.draw_colored_polygon(PackedVector2Array([top + Vector2(-w - 1.5, -7), top + Vector2(w + 1.5, -7), top + Vector2(0, 5.5)]), Color(0.15, 0.08, 0, 0.9))
	ci.draw_colored_polygon(pts, col)
	if front and w > 2.0:
		ci.draw_line(top + Vector2(-w * 0.5, -5), top + Vector2(0, 1), Color(1, 1, 0.8), 1.0)


func _draw_sub(ci: Node2D, b: Battler) -> void:
	var rows := []
	match menu_state:
		"spell":
			for sid in _spells(b):
				var sp: Dictionary = DB.d.spells[sid]
				rows.append([sp.name, "%d" % int(sp.mp), Art.WHITE if b.mp >= int(sp.mp) else Art.GREY, sp.el])
		"summon":
			for sid in GS.summons:
				var sd: Dictionary = DB.d.summons[sid]
				rows.append([sd.name, "%d" % int(sd.mp), Art.WHITE if b.mp >= int(sd.mp) else Art.GREY, sd.el])
		"item":
			for id in _usable_items():
				rows.append([DB.d.items[id].name, "x%d" % GS.items[id], Art.WHITE, DB.icon_for(id)])
		"combo":
			for e in _combos_for(b):
				var cb: Dictionary = e.combo
				rows.append(["%s (+%s)" % [cb.name, e.partner.name], "%d" % int(cb.mp), Art.WHITE if b.mp >= int(cb.mp) and e.partner.mp >= int(cb.mp) else Art.GREY, cb.el])
	var r := Rect2(106, 120, 210, 146)
	Art.window(ci, r)
	var vis := 9
	var top := clampi(sub_idx - vis + 2, 0, max(0, rows.size() - vis))
	for i in range(top, min(rows.size(), top + vis)):
		var y := r.position.y + 6 + (i - top) * 15
		var row: Array = rows[i]
		Art.icon(ci, row[3], Vector2(r.position.x + 24, y + 3))
		Art.text(ci, Vector2(r.position.x + 38, y), row[0], row[2])
		Art.text_right(ci, Vector2(r.end.x - 10, y), row[1], row[2])
	Art.cursor(ci, Vector2(r.position.x + 24, r.position.y + 6 + (sub_idx - top) * 15))
	if menu_state != "item":
		Art.text_right(ci, Vector2(r.end.x - 10, r.position.y - 13), "MP %d/%d" % [b.mp, b.maxmp], Art.CYAN)
