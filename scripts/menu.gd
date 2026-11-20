extends Node2D
## The pause menu: Items, Magic, Equip, Status, Formation, Quests, Summons, Config, Save, Title.


const CMDS := ["Items", "Magic", "Equip", "Status", "Formation", "Quests", "Summons", "Config", "Save", "Quit"]

var map
var active := false
var mode := "main"
var cmd := 0
var member_idx := 0
var list_idx := 0
var list_scroll := 0
var sub_idx := 0
var picked := -1
var message := ""
var message_t := 0.0
var list_cache: Array = []


func _ready() -> void:
	visible = false


func _process(delta: float) -> void:
	if active:
		if message_t > 0:
			message_t -= delta
		queue_redraw()


func open() -> void:
	active = true
	visible = true
	mode = "main"
	Inp.block(2)
	while active:
		await get_tree().process_frame
		_step()
	visible = false
	Inp.block(3)


func _close() -> void:
	active = false


func _flash(msg: String) -> void:
	message = msg
	message_t = 1.8


func _members() -> Array:
	return GS.active_members()


# ------------------------------------------------------------------ input per mode

func _step() -> void:
	match mode:
		"main":
			var v := Inp.vert()
			if v:
				cmd = wrapi(cmd + v, 0, CMDS.size())
				Audio.sfx("cursor")
			if Inp.back():
				Audio.sfx("cancel")
				_close()
			elif Inp.ok():
				Audio.sfx("confirm")
				match CMDS[cmd]:
					"Items":
						mode = "items"
						list_idx = 0
						list_scroll = 0
					"Magic", "Equip", "Status":
						mode = "pick_member"
						member_idx = 0
					"Formation":
						mode = "formation"
						list_idx = 0
						picked = -1
					"Quests":
						mode = "quests"
						list_idx = 0
					"Summons":
						mode = "summons"
						list_idx = 0
					"Config":
						mode = "config"
						list_idx = 0
					"Save":
						mode = "save"
						list_idx = 0
					"Quit":
						mode = "quit"
						list_idx = 1
		"pick_member":
			var v := Inp.vert()
			if v:
				member_idx = wrapi(member_idx + v, 0, _members().size())
				Audio.sfx("cursor")
			if Inp.back():
				mode = "main"
				Audio.sfx("cancel")
			elif Inp.ok():
				Audio.sfx("confirm")
				list_idx = 0
				list_scroll = 0
				match CMDS[cmd]:
					"Magic":
						mode = "magic"
					"Equip":
						mode = "equip"
						sub_idx = 0
					"Status":
						mode = "status"
		"items":
			_items_step()
		"item_target":
			_target_step("item")
		"magic":
			_magic_step()
		"magic_target":
			_target_step("magic")
		"equip":
			_equip_step()
		"equip_list":
			_equip_list_step()
		"status":
			var h := Inp.horiz()
			if h:
				member_idx = wrapi(member_idx + h, 0, _members().size())
				Audio.sfx("cursor")
			if Inp.back() or Inp.ok():
				mode = "pick_member"
				Audio.sfx("cancel")
		"formation":
			_formation_step()
		"quests", "summons":
			var n := _quest_list().size() if mode == "quests" else GS.summons.size()
			var v := Inp.vert()
			if v and n > 0:
				list_idx = wrapi(list_idx + v, 0, n)
				Audio.sfx("cursor")
			if Inp.back():
				mode = "main"
				Audio.sfx("cancel")
		"config":
			_config_step()
		"save":
			var v := Inp.vert()
			if v:
				list_idx = wrapi(list_idx + v, 0, 3)
				Audio.sfx("cursor")
			if Inp.back():
				mode = "main"
				Audio.sfx("cancel")
			elif Inp.ok():
				if GS.save_game(list_idx + 1):
					Audio.sfx("save")
					_flash("Saved to slot %d." % (list_idx + 1))
				else:
					_flash("Could not save.")
		"quit":
			var v := Inp.vert()
			if v:
				list_idx = wrapi(list_idx + v, 0, 2)
				Audio.sfx("cursor")
			if Inp.back():
				mode = "main"
			elif Inp.ok():
				if list_idx == 0:
					_close()
					Main.inst.goto_title()
				else:
					mode = "main"


# ------------------------------------------------------------------ items

func _item_list() -> Array:
	var use := []
	var keys := []
	for id in GS.items:
		if DB.d.items.has(id):
			use.append(id)
		else:
			keys.append(id)
	use.sort_custom(func(a, b): return DB.d.items.keys().find(a) < DB.d.items.keys().find(b))
	return use + keys


func _items_step() -> void:
	var lst := _item_list()
	var v := Inp.vert()
	if v and lst.size() > 0:
		list_idx = wrapi(list_idx + v, 0, lst.size())
		Audio.sfx("cursor")
	if Inp.back():
		mode = "main"
		Audio.sfx("cancel")
	elif Inp.ok() and lst.size() > 0:
		var id: String = lst[list_idx]
		if DB.d.items.has(id) and DB.d.items[id].effect != "flee":
			mode = "item_target"
			member_idx = 0
			Audio.sfx("confirm")
		else:
			Audio.sfx("buzzer")


func _target_step(kind: String) -> void:
	var v := Inp.vert()
	if v:
		member_idx = wrapi(member_idx + v, 0, _members().size())
		Audio.sfx("cursor")
	if Inp.back():
		mode = "items" if kind == "item" else "magic"
		Audio.sfx("cancel")
		return
	if not Inp.ok():
		return
	var tgt: Dictionary = _members()[member_idx]
	if kind == "item":
		var id: String = _item_list()[list_idx]
		if _use_item(id, tgt):
			GS.take_item(id)
			Audio.sfx("heal" if DB.d.items[id].effect != "boost" else "boost")
			if not GS.items.has(id):
				mode = "items"
				list_idx = clampi(list_idx, 0, max(0, _item_list().size() - 1))
		else:
			Audio.sfx("buzzer")
	else:
		var caster: Dictionary = _members()[sub_idx]
		var sid: String = _castable(caster)[list_idx]
		var sp: Dictionary = DB.d.spells[sid]
		if caster.mp < int(sp.mp):
			Audio.sfx("buzzer")
			_flash("Not enough MP.")
			return
		if _cast_out(caster, sid, tgt):
			caster.mp -= int(sp.mp)
			Audio.sfx("heal")
		else:
			Audio.sfx("buzzer")
	GS.changed.emit()


func _use_item(id: String, m: Dictionary) -> bool:
	var it: Dictionary = DB.d.items[id]
	var s := GS.stats(m)
	match it.effect:
		"heal_pct":
			if m.hp <= 0 or m.hp >= s.maxhp:
				return false
			m.hp = min(s.maxhp, m.hp + int(s.maxhp * float(it.v)))
		"mp_pct":
			if m.mp >= s.maxmp or m.hp <= 0:
				return false
			m.mp = min(s.maxmp, m.mp + int(s.maxmp * float(it.v)))
		"revive":
			if m.hp > 0:
				return false
			m.hp = int(s.maxhp * float(it.v))
		"full":
			if m.hp <= 0:
				m.hp = 1
			m.hp = s.maxhp
			m.mp = s.maxmp
		"boost":
			m.boosts[it.stat] = int(it.get("n", GS.BOOST_BATTLES))
			_flash("%s glows with power!" % DB.d.characters[m.id].name)
		_:
			return false
	return true


# ------------------------------------------------------------------ magic

func _castable(m: Dictionary) -> Array:
	return DB.spells_for(GS.spell_elements(m), m.level)


func _magic_step() -> void:
	var caster: Dictionary = _members()[member_idx]
	var lst := _castable(caster)
	var v := Inp.vert()
	if v and lst.size() > 0:
		list_idx = wrapi(list_idx + v, 0, lst.size())
		Audio.sfx("cursor")
	if Inp.back():
		mode = "pick_member"
		Audio.sfx("cancel")
	elif Inp.ok() and lst.size() > 0:
		var sp: Dictionary = DB.d.spells[lst[list_idx]]
		if sp.kind in ["heal", "revive"]:
			sub_idx = member_idx
			member_idx = 0
			mode = "magic_target"
			Audio.sfx("confirm")
		else:
			Audio.sfx("buzzer")
			_flash("Can only be cast in battle.")


func _cast_out(caster: Dictionary, sid: String, tgt: Dictionary) -> bool:
	var sp: Dictionary = DB.d.spells[sid]
	var cs := GS.stats(caster)
	var amt := DB.spell_heal(cs.mag, caster.level, float(sp.power), GS.element_pieces(caster, sp.el))
	var targets := [tgt]
	if sp.target == "allies":
		targets = _members()
	var any := false
	for t in targets:
		var st := GS.stats(t)
		if sp.kind == "revive":
			if t.hp <= 0:
				t.hp = int(st.maxhp * float(sp.power))
				any = true
		elif t.hp > 0 and t.hp < st.maxhp:
			t.hp = min(st.maxhp, t.hp + amt)
			any = true
	return any


# ------------------------------------------------------------------ equip

const SLOTS := ["weapon", "armor", "acc"]
const SLOT_NAMES := {"weapon": "Weapon", "armor": "Armor", "acc": "Accessory"}


func _equip_step() -> void:
	var v := Inp.vert()
	if v:
		sub_idx = wrapi(sub_idx + v, 0, 3)
		Audio.sfx("cursor")
	var h := Inp.horiz()
	if h:
		member_idx = wrapi(member_idx + h, 0, _members().size())
		Audio.sfx("cursor")
	if Inp.back():
		mode = "pick_member"
		Audio.sfx("cancel")
	elif Inp.ok():
		mode = "equip_list"
		list_idx = 0
		list_scroll = 0
		Audio.sfx("confirm")


func _candidates(slot: String) -> Array:
	var out := [null]
	for g in GS.gear:
		if DB.gear_slot(DB.d.gear[g.id].kind) == slot:
			out.append(g)
	return out


func _equip_list_step() -> void:
	var slot: String = SLOTS[sub_idx]
	var lst := _candidates(slot)
	var v := Inp.vert()
	if v:
		list_idx = wrapi(list_idx + v, 0, lst.size())
		Audio.sfx("cursor")
	if Inp.back():
		mode = "equip"
		Audio.sfx("cancel")
	elif Inp.ok():
		var m: Dictionary = _members()[member_idx]
		if slot == "weapon" and lst[list_idx] == null and m.id == "hero" and false:
			return
		GS.equip(m, slot, lst[list_idx])
		Audio.sfx("equip")
		mode = "equip"


func _preview(m: Dictionary, slot: String, inst) -> Dictionary:
	var copy := m.duplicate(true)
	copy.equip[slot] = inst
	return GS.stats(copy)


# ------------------------------------------------------------------ formation

func _formation_step() -> void:
	var ids := _roster_order()
	var v := Inp.vert()
	if v:
		list_idx = wrapi(list_idx + v, 0, ids.size())
		Audio.sfx("cursor")
	if Inp.back():
		if picked >= 0:
			picked = -1
		else:
			mode = "main"
		Audio.sfx("cancel")
	elif Inp.ok():
		if picked < 0:
			picked = list_idx
			Audio.sfx("confirm")
			return
		var a: String = ids[picked]
		var b: String = ids[list_idx]
		picked = -1
		if a == b:
			# toggle in/out of the active party
			if GS.party.has(a):
				if a == "hero":
					_flash("Wren always leads.")
					Audio.sfx("buzzer")
					return
				GS.party.erase(a)
			elif GS.party.size() < GS.MAX_PARTY:
				GS.party.append(a)
			else:
				_flash("The party is full (4).")
				Audio.sfx("buzzer")
				return
		else:
			var ia := GS.party.find(a)
			var ib := GS.party.find(b)
			if ia >= 0 and ib >= 0:
				GS.party[ia] = b
				GS.party[ib] = a
			elif ia >= 0 and ib < 0:
				if a == "hero":
					_flash("Wren always leads.")
					Audio.sfx("buzzer")
					return
				GS.party[ia] = b
			elif ib >= 0 and ia < 0:
				if b == "hero":
					_flash("Wren always leads.")
					Audio.sfx("buzzer")
					return
				GS.party[ib] = a
		# hero stays first
		if GS.party.has("hero") and GS.party[0] != "hero":
			GS.party.erase("hero")
			GS.party.insert(0, "hero")
		Audio.sfx("equip")
		GS.changed.emit()


func _roster_order() -> Array:
	var ids := GS.party.duplicate()
	for id in GS.roster:
		if not ids.has(id):
			ids.append(id)
	return ids


# ------------------------------------------------------------------ quests & config

func _quest_list() -> Array:
	var act := []
	var fin := []
	for q in GS.quests:
		if GS.quests[q] == "done":
			fin.append(q)
		else:
			act.append(q)
	return act + fin


const CFG := ["Battle Mode", "Text Speed", "Music", "Sound FX", "Minimap", "Always Run", "Practice Stash"]


func _config_step() -> void:
	var v := Inp.vert()
	if v:
		list_idx = wrapi(list_idx + v, 0, CFG.size())
		Audio.sfx("cursor")
	var h := Inp.horiz()
	if Inp.ok():
		h = 1
	if h:
		Audio.sfx("cursor")
		match list_idx:
			0:
				GS.settings.battle_mode = "active" if GS.settings.battle_mode == "wait" else "wait"
			1:
				GS.settings.text_speed = wrapi(int(GS.settings.text_speed) + h, 0, 3)
			2:
				GS.settings.music = clampf(snappedf(GS.settings.music + h * 0.1, 0.1), 0.0, 1.0)
				Audio.refresh_volume()
			3:
				GS.settings.sfx = clampf(snappedf(GS.settings.sfx + h * 0.1, 0.1), 0.0, 1.0)
			4:
				GS.settings.minimap = not GS.settings.get("minimap", true)
			5:
				GS.settings.auto_run = not GS.settings.get("auto_run", false)
			6:
				if not GS.flag("blessed_stash"):
					GS.grant_blessed_stash()
					message = "Twelve Blessed weapons added to your bag."
					message_t = 2.5
					Audio.sfx("chest")
		GS.save_settings()
	if Inp.back():
		mode = "main"
		Audio.sfx("cancel")


# ------------------------------------------------------------------ drawing

func _draw() -> void:
	if not active:
		return
	draw_rect(Rect2(0, 0, 480, 270), Color(0, 0, 0.05, 0.45))
	match mode:
		"main", "pick_member", "formation_x":
			_draw_party(Rect2(8, 8, 330, 254))
			_draw_cmds()
		"items", "item_target":
			_draw_items()
		"magic", "magic_target":
			_draw_magic()
		"equip", "equip_list":
			_draw_equip()
		"status":
			_draw_status()
		"formation":
			_draw_formation()
		"quests":
			_draw_quests()
		"summons":
			_draw_summons()
		"config":
			_draw_config()
		"save":
			_draw_save()
		"quit":
			_draw_party(Rect2(8, 8, 330, 254))
			_draw_cmds()
			var r := Rect2(150, 100, 180, 70)
			Art.window(self, r)
			Art.text_center(self, Vector2(240, 108), "Return to the title?")
			Art.text(self, Vector2(220, 128), "Yes")
			Art.text(self, Vector2(220, 143), "No")
			Art.cursor(self, Vector2(220, 128 + list_idx * 15))
	if message_t > 0:
		var w := Art.width(message) + 20
		Art.window(self, Rect2(240 - w / 2, 230, w, 24), "dark")
		Art.text_center(self, Vector2(240, 234), message, Art.YELLOW)


func _draw_cmds() -> void:
	var r := Rect2(346, 8, 126, CMDS.size() * 16 + 12)
	Art.window(self, r)
	for i in CMDS.size():
		Art.text(self, Vector2(r.position.x + 26, r.position.y + 6 + i * 16), CMDS[i])
	if mode == "main" or mode == "quit":
		Art.cursor(self, Vector2(r.position.x + 26, r.position.y + 6 + cmd * 16))
	var r2 := Rect2(346, r.end.y + 4, 126, 64)
	Art.window(self, r2)
	Art.icon(self, "gold", r2.position + Vector2(10, 9))
	Art.text_right(self, Vector2(r2.end.x - 10, r2.position.y + 6), "%d G" % GS.gold, Art.YELLOW)
	Art.text(self, Vector2(r2.position.x + 10, r2.position.y + 22), "Time")
	Art.text_right(self, Vector2(r2.end.x - 10, r2.position.y + 22), Art.fmt_time(GS.play_time))
	Art.text(self, Vector2(r2.position.x + 10, r2.position.y + 38), "Hearts")
	Art.text_right(self, Vector2(r2.end.x - 10, r2.position.y + 38), "%d / 6" % GS.hearts(), Art.CYAN)


func _draw_member_card(m: Dictionary, r: Rect2, selected: bool) -> void:
	var s := GS.stats(m)
	var c: Dictionary = DB.d.characters[m.id]
	var sheet := "res://assets/battle/%s.png" % (m.id if m.id != "hero" else "hero_t%d" % GS.hero_tier())
	var t := Art.tex(sheet)
	# aura colours as a soft backdrop glow
	var cols := GS.aura_colors(m)
	var pulse := 0.5 + 0.5 * sin(Time.get_ticks_msec() / 800.0)
	for i in cols.size():
		var col := DB.el_color(cols[i])
		var rad: float = 10.0 + GS.aura_radius(m) * 2.0 + pulse * 2.0
		draw_circle(r.position + Vector2(26 + i * 3, 30), rad, Color(col.r, col.g, col.b, 0.13 * GS.aura_strength(m) + 0.04))
	draw_texture_rect_region(t, Rect2(r.position + Vector2(2, 2), Vector2(48, 48)), Rect2(24, 22, 48, 48),
		Color(1, 1, 0.8) if not m.boosts.is_empty() and pulse > 0.5 else Color.WHITE)
	Art.text(self, r.position + Vector2(52, 4), "%s %s" % [c.name, c.title], Art.YELLOW if selected else Art.WHITE)
	Art.text(self, r.position + Vector2(52, 19), "Lv %d" % m.level)
	Art.element_icons(self, cols, r.position + Vector2(100, 23))
	if not m.boosts.is_empty():
		Art.text(self, r.position + Vector2(150, 19), "Boosted", Art.YELLOW)
	Art.text(self, r.position + Vector2(52, 34), "HP")
	Art.text_right(self, r.position + Vector2(190, 34), "%d/%d" % [m.hp, s.maxhp], Art.RED if m.hp <= 0 else Art.WHITE)
	Art.bar(self, Rect2(r.position + Vector2(196, 39), Vector2(70, 5)), float(m.hp) / s.maxhp, Color(0.4, 0.9, 0.45))
	Art.text(self, r.position + Vector2(52, 48), "MP")
	Art.text_right(self, r.position + Vector2(190, 48), "%d/%d" % [m.mp, s.maxmp])
	Art.bar(self, Rect2(r.position + Vector2(196, 53), Vector2(70, 5)), float(m.mp) / max(1, s.maxmp), Color(0.45, 0.6, 1.0))
	var nx := DB.xp_to_next(m.level)
	Art.text(self, r.position + Vector2(200, 4), "Next %d" % (nx - m.xp), Art.GREY, 13)
	Art.bar(self, Rect2(r.position + Vector2(200, 21), Vector2(66, 4)), float(m.xp) / nx, Color(0.95, 0.8, 0.35))


func _draw_party(r: Rect2) -> void:
	Art.window(self, r)
	var mem := _members()
	for i in mem.size():
		var cr := Rect2(r.position + Vector2(8, 6 + i * 61), Vector2(r.size.x - 16, 60))
		var sel: bool = (mode in ["pick_member", "item_target", "magic_target"]) and i == member_idx
		_draw_member_card(mem[i], cr, sel)
		if sel:
			Art.cursor(self, cr.position + Vector2(4, 20))


func _list_window(r: Rect2, rows: Array, sel: int, show_cursor: bool, row_h := 15) -> void:
	## rows: [[text, right_text, color, icon]]
	Art.window(self, r)
	var visible_rows := int((r.size.y - 12) / row_h)
	var top := clampi(sel - visible_rows + 2, 0, max(0, rows.size() - visible_rows))
	for i in range(top, min(rows.size(), top + visible_rows)):
		var y := r.position.y + 6 + (i - top) * row_h
		var row: Array = rows[i]
		var x := r.position.x + 24
		if row.size() > 3 and row[3] != "":
			Art.icon(self, row[3], Vector2(x, y + 3))
			x += 13
		var right_w := 0.0
		if row.size() > 1 and row[1] != "":
			right_w = Art.width(row[1]) + 6
			Art.text_right(self, Vector2(r.end.x - 10, y), row[1], row[2] if row.size() > 2 else Art.WHITE)
		Art.text_fit(self, Vector2(x, y), row[0], row[2] if row.size() > 2 else Art.WHITE, r.end.x - 12 - right_w - x)
	if show_cursor and rows.size() > 0:
		Art.cursor(self, Vector2(r.position.x + 24, r.position.y + 6 + (sel - top) * row_h))
	if top > 0:
		draw_rect(Rect2(r.end.x - 14, r.position.y + 4, 5, 2), Color.WHITE)
	if top + visible_rows < rows.size():
		draw_rect(Rect2(r.end.x - 14, r.end.y - 6, 5, 2), Color.WHITE)


func _draw_items() -> void:
	var lst := _item_list()
	var rows := []
	for id in lst:
		var key: bool = not DB.d.items.has(id)
		rows.append([DB.info(id).name, "" if key else "x%d" % GS.items[id], Art.CYAN if key else Art.WHITE, DB.icon_for(id)])
	if rows.is_empty():
		rows.append(["(nothing)", "", Art.GREY, ""])
	_list_window(Rect2(8, 30, 230, 232), rows, list_idx, mode == "items")
	Art.window(self, Rect2(8, 4, 230, 24), "dark")
	Art.text(self, Vector2(18, 8), "Items")
	if lst.size() > 0:
		var info := DB.info(lst[list_idx])
		Art.window(self, Rect2(246, 4, 226, 44), "dark")
		var lines := Art.wrap(info.get("desc", ""), 206)
		for i in min(2, lines.size()):
			Art.text(self, Vector2(256, 8 + i * 15), lines[i])
	_draw_party_small(Rect2(246, 52, 226, 210), mode == "item_target")


func _draw_party_small(r: Rect2, cursor_on: bool) -> void:
	Art.window(self, r)
	var mem := _members()
	for i in mem.size():
		var m: Dictionary = mem[i]
		var s := GS.stats(m)
		var y := r.position.y + 8 + i * 50
		Art.text(self, Vector2(r.position.x + 24, y), DB.d.characters[m.id].name, Art.YELLOW if cursor_on and i == member_idx else Art.WHITE)
		Art.text_right(self, Vector2(r.end.x - 10, y), "Lv %d" % m.level, Art.GREY)
		Art.text(self, Vector2(r.position.x + 24, y + 15), "HP %d/%d" % [m.hp, s.maxhp], Art.RED if m.hp <= 0 else Art.WHITE)
		Art.text(self, Vector2(r.position.x + 24, y + 29), "MP %d/%d" % [m.mp, s.maxmp])
		Art.bar(self, Rect2(r.position.x + 130, y + 20, 80, 5), float(m.hp) / s.maxhp, Color(0.4, 0.9, 0.45))
		Art.bar(self, Rect2(r.position.x + 130, y + 34, 80, 5), float(m.mp) / max(1, s.maxmp), Color(0.45, 0.6, 1.0))
		if not m.boosts.is_empty():
			Art.text_right(self, Vector2(r.end.x - 10, y + 15), "Boost", Art.YELLOW)
	if cursor_on:
		Art.cursor(self, Vector2(r.position.x + 24, r.position.y + 8 + member_idx * 50))


func _draw_magic() -> void:
	var ci := member_idx if mode == "magic" else sub_idx
	var caster: Dictionary = _members()[ci]
	var lst := _castable(caster)
	var rows := []
	for sid in lst:
		var sp: Dictionary = DB.d.spells[sid]
		var usable: bool = sp.kind in ["heal", "revive"]
		rows.append([sp.name, "%d MP" % int(sp.mp), Art.WHITE if usable else Art.GREY, sp.el])
	if rows.is_empty():
		rows.append(["(equip elemental gear to learn spells)", "", Art.GREY, ""])
	Art.window(self, Rect2(8, 4, 230, 24), "dark")
	Art.text(self, Vector2(18, 8), "%s's Magic   MP %d" % [DB.d.characters[caster.id].name, caster.mp])
	_list_window(Rect2(8, 30, 230, 232), rows, list_idx, mode == "magic")
	if lst.size() > 0:
		var sp: Dictionary = DB.d.spells[lst[list_idx]]
		Art.window(self, Rect2(246, 4, 226, 44), "dark")
		var d: String = sp.get("desc", "")
		if d == "":
			d = {"dmg": "%s damage to %s." % [DB.el_name(sp.el), "all foes" if sp.target == "all" else "one foe"],
				 "heal": "Restores HP to %s." % ("the party" if sp.target == "allies" else "one ally"),
				 "revive": "Revives a fallen ally."}.get(sp.kind, "")
		Art.text(self, Vector2(256, 8), d)
		Art.text(self, Vector2(256, 23), "Element: %s" % DB.el_name(sp.el), DB.el_color(sp.el))
	_draw_party_small(Rect2(246, 52, 226, 210), mode == "magic_target")


func _draw_equip() -> void:
	var m: Dictionary = _members()[member_idx]
	var s := GS.stats(m)
	var c: Dictionary = DB.d.characters[m.id]
	Art.window(self, Rect2(8, 4, 464, 24), "dark")
	Art.text(self, Vector2(18, 8), "Equip: %s   (Left/Right: switch member)" % c.name)
	var r := Rect2(8, 30, 230, 70)
	Art.window(self, r)
	for i in 3:
		var slot: String = SLOTS[i]
		var inst = m.equip[slot]
		var y := r.position.y + 6 + i * 19
		Art.text(self, Vector2(r.position.x + 24, y), SLOT_NAMES[slot], Art.GREY)
		if inst != null:
			var g: Dictionary = DB.d.gear[inst.id]
			Art.icon(self, g.kind, Vector2(r.position.x + 92, y + 3))
			Art.text_fit(self, Vector2(r.position.x + 106, y), DB.gear_label(inst), DB.tier_color(inst.id), r.size.x - 114)
		else:
			Art.text(self, Vector2(r.position.x + 106, y), "-", Art.GREY)
	if mode == "equip":
		Art.cursor(self, Vector2(r.position.x + 24, r.position.y + 6 + sub_idx * 19))
	# stats with preview
	var prev := s
	var cand = null
	if mode == "equip_list":
		var lst := _candidates(SLOTS[sub_idx])
		cand = lst[list_idx]
		prev = _preview(m, SLOTS[sub_idx], cand)
	var sr := Rect2(8, 104, 230, 158)
	Art.window(self, sr)
	var keys := [["Attack", "atk"], ["Strength", "str"], ["Defense", "def"], ["Armor", "wdef"], ["Magic", "mag"],
				 ["Magic Def", "mdef"], ["Speed", "spd"], ["Dexterity", "dex"], ["Max HP", "maxhp"]]
	for i in keys.size():
		var k: String = keys[i][1]
		var y := sr.position.y + 6 + i * 16
		Art.text(self, Vector2(sr.position.x + 12, y), keys[i][0], Art.GREY)
		Art.text_right(self, Vector2(sr.position.x + 150, y), str(int(s[k])))
		if mode == "equip_list":
			var nv := int(prev[k])
			var col := Art.GREEN if nv > int(s[k]) else (Art.RED if nv < int(s[k]) else Art.WHITE)
			Art.text(self, Vector2(sr.position.x + 160, y), ">")
			Art.text_right(self, Vector2(sr.end.x - 12, y), str(nv), col)
	if mode == "equip_list":
		var lst := _candidates(SLOTS[sub_idx])
		var rows := []
		for g in lst:
			if g == null:
				rows.append(["(remove)", "", Art.GREY, ""])
			else:
				var gd: Dictionary = DB.d.gear[g.id]
				rows.append([DB.gear_label(g), "", DB.tier_color(g.id), gd.kind])
		_list_window(Rect2(246, 30, 226, 128), rows, list_idx, true)
		Art.window(self, Rect2(246, 162, 226, 100), "dark")
		if cand != null:
			_draw_gear_info(cand.id, Rect2(246, 162, 226, 100))
	else:
		_draw_aura_panel(m, Rect2(246, 30, 226, 232))


## Tier, element, bonuses and flavor text of a piece of gear.
func _draw_gear_info(id: String, r: Rect2) -> void:
	var gd: Dictionary = DB.d.gear[id]
	var x := r.position.x + 10
	var y := r.position.y + 4
	Art.text(self, Vector2(x, y), DB.tier_name(id), DB.tier_color(id))
	var en := DB.el_name(gd.el) if gd.el != null else "No element"
	if gd.el != null:
		Art.icon(self, gd.el, Vector2(r.end.x - 24 - Art.width(en), y + 3))
	Art.text_right(self, Vector2(r.end.x - 10, y), en, DB.el_color(gd.el) if gd.el != null else Art.GREY)
	y += 15
	# shorthand, two to a row, each squeezed into its own column
	var bl := DB.gear_bonus_short(id)
	if gd.kind == "bow":
		bl.append("Uses DEX")
	elif gd.kind == "staff":
		bl.append("+MAG power")
	var col_w := (r.size.x - 20) / 2.0
	for i in bl.size():
		if i >= 6:
			break
		Art.text_fit(self, Vector2(x + (i % 2) * col_w, y + floori(i / 2.0) * 13), bl[i], Art.GREEN, col_w - 6, 11, 8)
	y += int(ceil(min(6, bl.size()) / 2.0)) * 13 + 2
	# flavor text: smaller, and only as much as fits
	var lines := Art.wrap(str(gd.get("desc", "")), int(r.size.x) - 20, 9)
	for i in lines.size():
		if y + 11 > r.end.y - 2:
			break
		Art.text(self, Vector2(x, y), lines[i], Art.GREY, 9)
		y += 11


func _draw_aura_panel(m: Dictionary, r: Rect2) -> void:
	Art.window(self, r)
	var cols := GS.aura_colors(m)
	Art.text(self, r.position + Vector2(12, 6), "Aura", Art.YELLOW)
	var x := r.position.x + 60
	for e in cols:
		Art.text(self, Vector2(x, r.position.y + 6), DB.el_name(e), DB.el_color(e))
		x += Art.width(DB.el_name(e)) + 8
	if cols.is_empty():
		Art.text(self, Vector2(x, r.position.y + 6), "none", Art.GREY)
	Art.text(self, r.position + Vector2(12, 24), "Strength grows with level (%d)." % m.level, Art.GREY)
	var s := GS.stats(m)
	Art.text(self, r.position + Vector2(12, 46), "Resistances", Art.YELLOW)
	var y := r.position.y + 62
	var any := false
	for e in DB.d.elements:
		var v: float = s.res.get(e, 0.0)
		if abs(v) > 0.001:
			any = true
			Art.icon(self, e, Vector2(r.position.x + 14, y + 3))
			Art.text(self, Vector2(r.position.x + 28, y), DB.el_name(e))
			Art.text_right(self, Vector2(r.end.x - 12, y), ("+" if v > 0 else "") + "%d%%" % int(round(v * 100)), Art.GREEN if v > 0 else Art.RED)
			y += 15
	if not any:
		Art.text(self, Vector2(r.position.x + 14, y), "none (wear elemental armor)", Art.GREY)
		y += 15
	y += 8
	Art.text(self, Vector2(r.position.x + 12, y), "Spell elements", Art.YELLOW)
	Art.element_icons(self, GS.spell_elements(m), Vector2(r.position.x + 120, y + 3))


func _draw_status() -> void:
	var m: Dictionary = _members()[member_idx]
	var c: Dictionary = DB.d.characters[m.id]
	var s := GS.stats(m)
	var r := Rect2(8, 4, 464, 262)
	Art.window(self, r)
	var sheet := "res://assets/battle/%s.png" % (m.id if m.id != "hero" else "hero_t%d" % GS.hero_tier())
	var cols := GS.aura_colors(m)
	var pulse := 0.5 + 0.5 * sin(Time.get_ticks_msec() / 800.0)
	for i in cols.size():
		var col := DB.el_color(cols[i])
		draw_circle(Vector2(52 + (i - (cols.size() - 1) / 2.0) * 6, 52), 18.0 + GS.aura_radius(m) * 3.0 + pulse * 3.0,
			Color(col.r, col.g, col.b, 0.12 * GS.aura_strength(m) + 0.05))
	draw_texture_rect_region(Art.tex(sheet), Rect2(16, 4, 72, 72), Rect2(7 * 96 + 12, 4, 72, 72))
	Art.text(self, Vector2(90, 12), "%s %s" % [c.name, c.title], Art.YELLOW, 16)
	Art.text(self, Vector2(90, 32), "Level %d    Next level in %d XP" % [m.level, DB.xp_to_next(m.level) - m.xp])
	var lim: Dictionary = DB.d.limits[c.limit]
	Art.text(self, Vector2(90, 47), "Limit: %s" % lim.name, Art.CYAN)
	var bio := Art.wrap(c.bio, 360)
	for i in min(2, bio.size()):
		Art.text(self, Vector2(90, 64 + i * 14), bio[i], Art.GREY)
	var keys := [["HP", "%d / %d" % [m.hp, s.maxhp]], ["MP", "%d / %d" % [m.mp, s.maxmp]], ["Strength", s.str], ["Defense", s.def],
				 ["Magic", s.mag], ["Magic Def", s.mdef], ["Speed", s.spd], ["Dexterity", s.dex], ["Weapon Atk", int(s.atk)],
				 ["Armor", int(s.wdef + s.wmdef)]]
	for i in keys.size():
		var y := 102 + (i % 5) * 16
		var x := 24 + floori(i / 5.0) * 150
		Art.text(self, Vector2(x, y), keys[i][0], Art.GREY)
		Art.text_right(self, Vector2(x + 130, y), str(keys[i][1]))
	Art.text(self, Vector2(330, 102), "Spells", Art.YELLOW)
	var sp := _castable(m)
	for i in min(9, sp.size()):
		var spd: Dictionary = DB.d.spells[sp[i]]
		Art.icon(self, spd.el, Vector2(330, 120 + i * 14 + 3))
		Art.text(self, Vector2(344, 120 + i * 14), spd.name, Art.WHITE, 13)
	if sp.size() > 9:
		Art.text(self, Vector2(344, 120 + 9 * 14), "+%d more" % (sp.size() - 9), Art.GREY)
	if not m.boosts.is_empty():
		var bt := []
		for k in m.boosts:
			bt.append("%s +30%% (%d battles)" % [k.to_upper(), m.boosts[k]])
		Art.text(self, Vector2(24, 190), "Boosted: " + ", ".join(bt), Art.YELLOW)
	Art.text(self, Vector2(24, 245), "Left/Right: other members", Art.GREY)


func _draw_formation() -> void:
	var ids := _roster_order()
	var rows := []
	for i in ids.size():
		var rid: String = ids[i]
		var m: Dictionary = GS.roster[rid]
		var act := GS.party.has(rid)
		rows.append(["%s%s" % ["> " if picked == i else "", DB.d.characters[rid].name], "Lv %d  %s" % [m.level, "ACTIVE" if act else "resting"],
					 Art.YELLOW if picked == i else (Art.WHITE if act else Art.GREY), ""])
	Art.window(self, Rect2(8, 4, 464, 24), "dark")
	Art.text(self, Vector2(18, 8), "Formation: pick two to swap. Pick one twice to move in/out. (max 4)")
	_list_window(Rect2(8, 30, 230, 232), rows, list_idx, true, 18)
	var id: String = ids[list_idx]
	var c: Dictionary = DB.d.characters[id]
	var r := Rect2(246, 30, 226, 232)
	Art.window(self, r)
	var sheet := "res://assets/battle/%s.png" % (id if id != "hero" else "hero_t%d" % GS.hero_tier())
	draw_texture_rect_region(Art.tex(sheet), Rect2(r.position + Vector2(86, 4), Vector2(48, 48)), Rect2(24, 22, 48, 48))
	Art.text_center(self, r.position + Vector2(113, 56), "%s %s" % [c.name, c.title], Art.YELLOW)
	var bio := Art.wrap(c.bio, 200)
	for i in bio.size():
		Art.text(self, r.position + Vector2(12, 78 + i * 15), bio[i])
	var inn = c.innate
	Art.text(self, r.position + Vector2(12, 160), "Innate element: %s" % (DB.el_name(inn) if inn != null else "none (Kindler)"),
		DB.el_color(inn) if inn != null else Art.GREY)
	Art.text(self, r.position + Vector2(12, 176), "Limit: %s" % DB.d.limits[c.limit].name, Art.CYAN)
	var lim := Art.wrap(DB.d.limits[c.limit].desc, 200)
	for i in lim.size():
		Art.text(self, r.position + Vector2(12, 192 + i * 15), lim[i], Art.GREY)


func _draw_quests() -> void:
	var lst := _quest_list()
	var rows := []
	for q in lst:
		var qd: Dictionary = DB.d.quests[q]
		var st := GS.quest_state(q)
		var col := Art.GREY if st == "done" else (Art.GREEN if st == "ready" else Art.WHITE)
		var tag: String = {"main": "Main", "side": "Side", "companion": "Ally", "key": "Key", "omni": "???"}[qd.kind]
		rows.append([qd.title, tag, col, qd.world if qd.world in DB.d.elements else ""])
	if rows.is_empty():
		rows.append(["No quests yet. Talk to people!", "", Art.GREY, ""])
	Art.window(self, Rect2(8, 4, 464, 24), "dark")
	Art.text(self, Vector2(18, 8), "Quests   (green: ready to turn in)")
	_list_window(Rect2(8, 30, 260, 232), rows, list_idx, lst.size() > 0)
	if lst.size() > 0:
		var qd: Dictionary = DB.d.quests[lst[list_idx]]
		var r := Rect2(276, 30, 196, 232)
		Art.window(self, r)
		Art.text(self, r.position + Vector2(10, 6), qd.title, Art.YELLOW)
		Art.text(self, r.position + Vector2(10, 22), "From: %s" % qd.giver, Art.GREY)
		var st := GS.quest_state(lst[list_idx])
		Art.text(self, r.position + Vector2(10, 38), {"active": "In progress", "ready": "Return to %s!" % qd.giver, "done": "Complete"}.get(st, ""),
			Art.GREEN if st == "ready" else Art.WHITE)
		var lines := Art.wrap(qd.desc, 176)
		for i in lines.size():
			Art.text(self, r.position + Vector2(10, 60 + i * 15), lines[i])


func _draw_summons() -> void:
	var rows := []
	for sid in GS.summons:
		var sd: Dictionary = DB.d.summons[sid]
		rows.append([sd.name, "%d MP" % int(sd.mp), DB.el_color(sd.el), sd.el])
	if rows.is_empty():
		rows.append(["None yet. Summon stones hide in caves.", "", Art.GREY, ""])
	Art.window(self, Rect2(8, 4, 464, 24), "dark")
	Art.text(self, Vector2(18, 8), "Summons (%d / 8)" % GS.summons.size())
	_list_window(Rect2(8, 30, 230, 232), rows, list_idx, GS.summons.size() > 0)
	if GS.summons.size() > 0:
		var sid: String = GS.summons[list_idx]
		var sd: Dictionary = DB.d.summons[sid]
		var r := Rect2(246, 30, 226, 232)
		Art.window(self, r)
		var t := Art.tex("res://assets/summons/%s.png" % sid)
		draw_texture(t, r.position + Vector2(57, 8))
		var lines := Art.wrap(sd.desc, 206)
		for i in lines.size():
			Art.text(self, r.position + Vector2(10, 128 + i * 15), lines[i])


func _draw_config() -> void:
	var r := Rect2(100, 42, 280, 158)
	Art.window(self, r)
	var vals := [GS.settings.battle_mode.capitalize(), ["Slow", "Normal", "Fast"][int(GS.settings.text_speed)],
				 "%d%%" % int(round(GS.settings.music * 100)), "%d%%" % int(round(GS.settings.sfx * 100)),
				 "On" if GS.settings.get("minimap", true) else "Off",
				 "On" if GS.settings.get("auto_run", false) else "Off",
				 "Claimed" if GS.flag("blessed_stash") else "Claim"]
	for i in CFG.size():
		Art.text(self, r.position + Vector2(28, 8 + i * 20), CFG[i])
		Art.text_right(self, r.position + Vector2(r.size.x - 14, 8 + i * 20), "< %s >" % vals[i], Art.YELLOW)
	Art.cursor(self, r.position + Vector2(28, 8 + list_idx * 20))
	var hint := "Wait: time pauses while you choose. Active: enemies keep acting (like FF7)." if list_idx == 0 else ("On: you always run; hold Shift to walk." if list_idx == 5 else ("Twelve laser weapons to practice with. Makes the game much easier." if list_idx == 6 else "Left/Right to change."))
	var lines := Art.wrap(hint, 260)
	Art.window(self, Rect2(100, 204, 280, 16 + lines.size() * 15), "dark")
	for i in lines.size():
		Art.text(self, Vector2(110, 210 + i * 15), lines[i], Art.GREY)


func _draw_save() -> void:
	var r := Rect2(90, 40, 300, 170)
	Art.window(self, r)
	Art.text(self, r.position + Vector2(14, 6), "Save to which slot?", Art.YELLOW)
	for i in 3:
		var s := GS.slot_summary(i + 1)
		var y := r.position.y + 28 + i * 44
		Art.text(self, Vector2(r.position.x + 30, y), "Slot %d" % (i + 1))
		if s.is_empty():
			Art.text(self, Vector2(r.position.x + 100, y), "(empty)", Art.GREY)
		else:
			Art.text(self, Vector2(r.position.x + 100, y), "Lv %d  %s" % [s.level, s.place])
			Art.text(self, Vector2(r.position.x + 100, y + 15), "Hearts %d/6   %s" % [s.hearts, Art.fmt_time(s.time)], Art.GREY)
	Art.cursor(self, Vector2(r.position.x + 30, r.position.y + 28 + list_idx * 44))
