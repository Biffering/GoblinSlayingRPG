extends Node2D
## Shops: pawn shops sell gear at the party's level; item shops sell consumables. Buy and sell.

signal closed

var shop_id := ""
var shop: Dictionary
var mode := "top"   # top | buy | sell | qty
var top_idx := 0
var idx := 0
var qty := 1
var message := ""
var message_t := 0.0
var stock: Array = []   # [{"kind": "item"/"gear", "id", "inst", "price"}]


func _ready() -> void:
	shop = DB.d.shops[shop_id]
	var lv := GS.avg_level()
	for gid in shop.gear:
		var inst := {"id": gid, "lv": lv}
		stock.append({"kind": "gear", "id": gid, "inst": inst, "price": DB.gear_price(inst)})
	for iid in shop.items:
		stock.append({"kind": "item", "id": iid, "price": int(DB.d.items[iid].price)})
	Inp.block(2)
	_run()


func _run() -> void:
	while true:
		await get_tree().process_frame
		queue_redraw()
		if message_t > 0:
			message_t -= get_process_delta_time()
		match mode:
			"top":
				var v := Inp.vert()
				if v:
					top_idx = wrapi(top_idx + v, 0, 3)
					Audio.sfx("cursor")
				var pressed_ok := Inp.ok()
				if Inp.back() or (pressed_ok and top_idx == 2):
					Audio.sfx("cancel")
					Inp.block(3)
					closed.emit()
					return
				if pressed_ok:
					Audio.sfx("confirm")
					mode = "buy" if top_idx == 0 else "sell"
					idx = 0
			"buy":
				var v := Inp.vert()
				if v and stock.size() > 0:
					idx = wrapi(idx + v, 0, stock.size())
					Audio.sfx("cursor")
				if Inp.back():
					mode = "top"
					Audio.sfx("cancel")
				elif Inp.ok() and stock.size() > 0:
					var s: Dictionary = stock[idx]
					if s.kind == "item":
						mode = "qty"
						qty = 1
						Audio.sfx("confirm")
					else:
						_buy(s, 1)
			"qty":
				var s: Dictionary = stock[idx]
				var h := Inp.horiz() + Inp.vert() * -1
				if h:
					qty = clampi(qty + h, 1, 99)
					Audio.sfx("cursor")
				if Inp.back():
					mode = "buy"
					Audio.sfx("cancel")
				elif Inp.ok():
					_buy(s, qty)
					mode = "buy"
			"sell":
				var lst := _sellable()
				var v := Inp.vert()
				if v and lst.size() > 0:
					idx = wrapi(idx + v, 0, lst.size())
					Audio.sfx("cursor")
				if Inp.back():
					mode = "top"
					Audio.sfx("cancel")
				elif Inp.ok() and lst.size() > 0:
					var e: Dictionary = lst[idx]
					GS.gold += e.price
					if e.kind == "gear":
						GS.gear.erase(e.inst)
					else:
						GS.take_item(e.id)
					Audio.sfx("coins")
					_flash("Sold for %d G." % e.price)
					idx = clampi(idx, 0, max(0, _sellable().size() - 1))


func _flash(s: String) -> void:
	message = s
	message_t = 1.6


func _buy(s: Dictionary, n: int) -> void:
	var cost: int = s.price * n
	if GS.gold < cost:
		Audio.sfx("buzzer")
		_flash("Not enough gold.")
		return
	GS.gold -= cost
	if s.kind == "gear":
		GS.gear.append(s.inst.duplicate())
	else:
		GS.items[s.id] = GS.items.get(s.id, 0) + n
	Audio.sfx("coins")
	_flash("Bought %s%s." % [DB.info(s.id).name, "" if n == 1 else " x%d" % n])
	GS.changed.emit()


func _sellable() -> Array:
	var out := []
	for g in GS.gear:
		out.append({"kind": "gear", "id": g.id, "inst": g, "price": floori(DB.gear_price(g) / 2.0)})
	for id in GS.items:
		if DB.d.items.has(id):
			out.append({"kind": "item", "id": id, "price": floori(int(DB.d.items[id].price) / 2.0)})
	return out


func _owned(id: String) -> int:
	if DB.is_gear(id):
		var n := 0
		for g in GS.gear:
			if g.id == id:
				n += 1
		for m in GS.roster.values():
			for slot in m.equip:
				if m.equip[slot] != null and m.equip[slot].id == id:
					n += 1
		return n
	return GS.items.get(id, 0)


func _draw() -> void:
	draw_rect(Rect2(0, 0, 480, 270), Color(0, 0, 0.05, 0.5))
	Art.window(self, Rect2(8, 4, 464, 24), "dark")
	Art.text(self, Vector2(18, 8), shop.name)
	Art.icon(self, "gold", Vector2(380, 11))
	Art.text_right(self, Vector2(462, 8), "%d G" % GS.gold, Art.YELLOW)
	if mode == "top":
		var top_r := Rect2(8, 30, 120, 60)
		Art.window(self, top_r)
		for i in 3:
			Art.text(self, top_r.position + Vector2(26, 6 + i * 16), ["Buy", "Sell", "Leave"][i])
		Art.cursor(self, top_r.position + Vector2(26, 6 + top_idx * 16))
		return
	var rows := []
	var sel_entry: Dictionary = {}
	if mode in ["buy", "qty"]:
		for s in stock:
			var nm: String = DB.info(s.id).name
			var col := Art.WHITE if GS.gold >= s.price else Art.GREY
			if s.kind == "gear":
				nm = DB.gear_label(s.inst)
				col = DB.tier_color(s.id) if GS.gold >= s.price else DB.tier_color(s.id).darkened(0.45)
			rows.append([nm, "%d G" % s.price, col, DB.icon_for(s.id)])
		if stock.size() > 0:
			sel_entry = stock[idx]
	else:
		var lst := _sellable()
		for e in lst:
			var nm: String = DB.info(e.id).name
			var col := Art.WHITE
			if e.kind == "gear":
				nm = DB.gear_label(e.inst)
				col = DB.tier_color(e.id)
			elif GS.items.get(e.id, 0) > 1:
				nm += " x%d" % GS.items[e.id]
			rows.append([nm, "%d G" % e.price, col, DB.icon_for(e.id)])
		if lst.size() > 0:
			sel_entry = lst[idx]
		if rows.is_empty():
			rows.append(["(nothing to sell)", "", Art.GREY, ""])
	_list(Rect2(8, 30, 250, 232), rows, idx)
	if sel_entry.is_empty():
		return
	var info := DB.info(sel_entry.id)
	var r := Rect2(266, 30, 206, 232)
	Art.window(self, r)
	var own := "Own %d" % _owned(sel_entry.id)
	Art.text_right(self, r.position + Vector2(196, 6), own, Art.GREY)
	Art.text_fit(self, r.position + Vector2(10, 6), info.name, DB.tier_color(sel_entry.id) if sel_entry.kind == "gear" else Art.YELLOW,
		186 - Art.width(own) - 8)
	var y := r.position.y + 24
	if sel_entry.kind == "gear":
		var gs := DB.gear_stats(sel_entry.inst, GS.avg_level())
		var gd: Dictionary = DB.d.gear[sel_entry.id]
		var el_txt := DB.el_name(gd.el) if gd.el != null else "No element"
		var kind_txt: String = gd.kind.capitalize() if gd.kind != "acc" else "Accessory"
		if DB.is_blessed(sel_entry.id):
			kind_txt = {"blade": "Arc Blade", "rifle": "Assault Laser", "pistol": "Ray Pistol", "staff": "Coil Staff"}.get(str(gd.get("style", "")), kind_txt)
		Art.text_fit(self, Vector2(r.position.x + 10, y), "%s  %s" % [kind_txt, el_txt],
			DB.el_color(gd.el) if gd.el != null else Art.WHITE, 186)
		y += 16
		var parts := []
		for k in gs:
			parts.append("%s %d" % [{"atk": "ATK", "matk": "MATK", "wdef": "DEF", "wmdef": "MDF"}[k], gs[k]])
		Art.text_fit(self, Vector2(r.position.x + 10, y), DB.tier_name(sel_entry.id) + "  " + "  ".join(parts), DB.tier_color(sel_entry.id), 186)
		y += 15
		# bonuses in shorthand, two to a row
		var bl := DB.gear_bonus_short(sel_entry.id)
		for i in bl.size():
			Art.text_fit(self, Vector2(r.position.x + 10 + (i % 2) * 94, y + floori(i / 2.0) * 13), bl[i], Art.GREEN, 88, 11, 8)
		y += int(ceil(bl.size() / 2.0)) * 13 + 5
		# compare with each party member's current gear
		var slot := DB.gear_slot(gd.kind)
		for m in GS.active_members():
			var cur := GS.stats(m)
			var copy: Dictionary = m.duplicate(true)
			copy.equip[slot] = sel_entry.inst
			var nw := GS.stats(copy)
			var key := "atk" if slot == "weapon" else "wdef"
			var score_old: float = cur[key] + (cur.mag if gd.kind == "staff" else 0.0)
			var score_new: float = nw[key] + (nw.mag if gd.kind == "staff" else 0.0)
			var tag := "="
			var col := Art.WHITE
			if score_new > score_old:
				tag = "up"
				col = Art.GREEN
			elif score_new < score_old:
				tag = "down"
				col = Art.RED
			Art.text(self, Vector2(r.position.x + 10, y), DB.d.characters[m.id].name)
			Art.text_right(self, Vector2(r.end.x - 10, y), tag, col)
			y += 14
		y += 6
	var lines := Art.wrap(info.get("desc", ""), 186)
	for l in lines:
		Art.text(self, Vector2(r.position.x + 10, y), l, Art.GREY)
		y += 15
	if mode == "qty":
		var qr := Rect2(80, 110, 180, 50)
		Art.window(self, qr, "gold")
		Art.text(self, qr.position + Vector2(12, 6), "How many?  < %d >" % qty)
		Art.text(self, qr.position + Vector2(12, 24), "Total: %d G" % (sel_entry.price * qty), Art.YELLOW)
	if message_t > 0:
		var w := Art.width(message) + 20
		Art.window(self, Rect2(240 - w / 2, 236, w, 24), "dark")
		Art.text_center(self, Vector2(240, 240), message, Art.YELLOW)


func _list(r: Rect2, rows: Array, sel: int) -> void:
	Art.window(self, r)
	var vis := int((r.size.y - 12) / 15)
	var top := clampi(sel - vis + 2, 0, max(0, rows.size() - vis))
	for i in range(top, min(rows.size(), top + vis)):
		var y := r.position.y + 6 + (i - top) * 15
		var row: Array = rows[i]
		if row[3] != "":
			Art.icon(self, row[3], Vector2(r.position.x + 24, y + 3))
		var right_w := Art.width(row[1]) + 6 if row[1] != "" else 0.0
		Art.text_right(self, Vector2(r.end.x - 10, y), row[1], row[2])
		Art.text_fit(self, Vector2(r.position.x + 37, y), row[0], row[2], r.end.x - 12 - right_w - (r.position.x + 37))
	if mode in ["buy", "sell"]:
		Art.cursor(self, Vector2(r.position.x + 24, r.position.y + 6 + (sel - top) * 15))
