extends Node2D
## Title screen: a dark battlefield, drifting embers, a sword in the ground and the battle-worn logo.

var idx := 0
var mode := "main"   # main | load
var slot_idx := 0
var t := 0.0
var open_load := false
var stars: Array = []
var embers: Array = []
var ridge: PackedVector2Array
var logo: Texture2D
var clouds: Array = []
var fog: Array = []
var flash := 0.0
var next_bolt := 3.5
var bolt: PackedVector2Array
var rng2 := RandomNumberGenerator.new()
var busy := false
var flash_in := 0.0
const ELS := ["fire", "water", "wind", "stone", "spirit", "void"]


func _ready() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in 40:
		stars.append(Vector3(rng.randf() * 480, rng.randf() * 120, rng.randf()))
	for i in 70:
		embers.append(Vector3(rng.randf() * 480, rng.randf() * 270, rng.randf_range(0.4, 1.0)))
	# a ragged ridge line of the battlefield
	ridge = PackedVector2Array([Vector2(0, 270)])
	var x := 0.0
	while x <= 480.0:
		ridge.append(Vector2(x, 196 + rng.randf_range(-10, 8) + 10.0 * sin(x * 0.02)))
		x += rng.randf_range(6, 16)
	ridge.append(Vector2(480, 196))
	ridge.append(Vector2(480, 270))
	logo = Art.tex("res://assets/ui/title_logo.png")
	for i in 14:
		clouds.append(Vector4(rng.randf() * 560, rng.randf_range(4, 120), rng.randf_range(30, 70), rng.randf_range(0.3, 1.0)))
	for i in 10:
		fog.append(Vector3(rng.randf() * 560, rng.randf_range(196, 262), rng.randf_range(30, 60)))
	rng2.randomize()
	Audio.ambient("amb_storm", -14.0)
	Audio.music("title", 1.0)
	Inp.block(10)
	if open_load:
		mode = "load"


func _thunder() -> void:
	await get_tree().create_timer(rng2.randf_range(0.25, 0.9)).timeout
	if is_instance_valid(self) and is_inside_tree():
		Audio.sfx("thunder%d" % (1 + rng2.randi() % 2), -6.0, 1.0, 0.1)


func _options() -> Array:
	if GS.has_clear():
		return ["New Game", "New Game+", "Continue", "Quit"]
	return ["New Game", "Continue", "Quit"]


func _has_save() -> bool:
	for i in 4:
		if not GS.slot_summary(i).is_empty():
			return true
	return false


func _process(delta: float) -> void:
	t += delta
	flash_in = max(0.0, flash_in - delta * 1.2)
	queue_redraw()
	# lightning over the battlefield, then the thunder rolls in
	flash = max(0.0, flash - delta * 2.2)
	next_bolt -= delta
	if next_bolt <= 0.0:
		next_bolt = rng2.randf_range(5.0, 11.0)
		flash = 1.0
		bolt = PackedVector2Array()
		var bx := rng2.randf_range(40, 440)
		var by := 0.0
		while by < 190.0:
			bolt.append(Vector2(bx, by))
			bx += rng2.randf_range(-14, 14)
			by += rng2.randf_range(10, 24)
		_thunder()
	if open_load and mode != "load":
		mode = "load"
		open_load = false
	if busy or Main.inst.busy:
		return
	if mode == "main":
		var opts := _options()
		var v := Inp.vert()
		if v:
			idx = wrapi(idx + v, 0, opts.size())
			Audio.sfx("cursor")
		if Inp.ok():
			Audio.sfx("confirm")
			match opts[idx]:
				"New Game":
					busy = true
					Main.inst.start_new_game()
				"New Game+":
					busy = true
					Main.inst.start_new_game_plus()
				"Continue":
					if _has_save():
						mode = "load"
						slot_idx = 0
					else:
						Audio.sfx("buzzer")
				"Quit":
					get_tree().quit()
	else:
		var v := Inp.vert()
		if v:
			slot_idx = wrapi(slot_idx + v, 0, 4)
			Audio.sfx("cursor")
		if Inp.back():
			mode = "main"
			Audio.sfx("cancel")
		elif Inp.ok():
			if GS.slot_summary(slot_idx).is_empty():
				Audio.sfx("buzzer")
			else:
				Audio.sfx("confirm")
				busy = true
				Main.inst.continue_game(slot_idx)


func _draw() -> void:
	# ash-black sky bleeding into a dull red horizon
	for y in 270:
		var k := y / 270.0
		var c := Color(0.02, 0.015, 0.02).lerp(Color(0.22, 0.04, 0.03), pow(k, 1.6))
		draw_rect(Rect2(0, y, 480, 1), c)
	for st in stars:
		var tw := 0.5 + 0.5 * sin(t * 1.5 + st.z * 20.0)
		draw_rect(Rect2(int(st.x), int(st.y), 1, 1), Color(1, 0.8, 0.7, 0.12 + 0.25 * tw * st.z))
	# a blood moon low in the sky
	var moon := Vector2(392, 74)
	draw_circle(moon, 30, Color(0.5, 0.06, 0.05, 0.25))
	draw_circle(moon, 22, Color(0.62, 0.1, 0.07))
	draw_circle(moon + Vector2(6, -5), 6, Color(0.5, 0.07, 0.05))
	# storm clouds rolling across, lit from below by the lightning
	for c in clouds:
		var cx := fposmod(c.x - t * 9.0 * c.w, 560.0) - 40.0
		var cc := Color(0.07, 0.05, 0.07).lerp(Color(0.16, 0.12, 0.15), c.w)
		if flash > 0.0:
			cc = cc.lerp(Color(0.55, 0.5, 0.6), flash * 0.5 * c.w)
		draw_circle(Vector2(cx, c.y), c.z, cc)
		draw_circle(Vector2(cx + c.z * 0.8, c.y + 8), c.z * 0.75, cc)
		draw_circle(Vector2(cx - c.z * 0.7, c.y + 10), c.z * 0.6, cc)
	if flash > 0.6 and bolt.size() > 1:
		draw_polyline(bolt, Color(1, 0.95, 1, flash), 2.0)
		draw_polyline(bolt, Color(0.8, 0.7, 1, flash * 0.5), 5.0)
	# the great sword planted in the ground behind the logo
	var sx := 240.0
	draw_colored_polygon(PackedVector2Array([Vector2(sx - 5, 60), Vector2(sx + 5, 60), Vector2(sx + 5, 196), Vector2(sx, 206), Vector2(sx - 5, 196)]), Color(0.1, 0.08, 0.09))
	draw_rect(Rect2(sx - 1, 64, 2, 128), Color(0.28, 0.24, 0.26))
	draw_rect(Rect2(sx - 22, 52, 44, 7), Color(0.08, 0.06, 0.07))
	draw_rect(Rect2(sx - 3, 32, 6, 20), Color(0.08, 0.06, 0.07))
	draw_circle(Vector2(sx, 30), 5, Color(0.08, 0.06, 0.07))
	# broken blades and spears jutting from the field
	for i in 7:
		var bx := 30.0 + i * 70.0 + (11.0 if i % 2 else -9.0)
		var lean := -0.25 + 0.08 * i
		var h := 18.0 + (i * 7) % 16
		draw_line(Vector2(bx, 204), Vector2(bx + lean * h, 204 - h), Color(0.09, 0.07, 0.08), 2.0)
		draw_line(Vector2(bx - 4 + lean * 4, 204 - 4), Vector2(bx + 4 + lean * 4, 204 - 4), Color(0.09, 0.07, 0.08), 1.0)
	draw_colored_polygon(ridge, Color(0.05, 0.03, 0.035))
	# the hooded slayer stands on the ridge, cape snapping in the wind
	var hx := 92.0
	var hy := 196.0
	var wave := sin(t * 3.0) * 4.0 + sin(t * 7.0) * 1.5
	var dark := Color(0.03, 0.02, 0.025)
	draw_colored_polygon(PackedVector2Array([Vector2(hx - 4, hy - 30), Vector2(hx + 6, hy - 30), Vector2(hx + 26 + wave, hy - 22),
		Vector2(hx + 30 + wave * 1.4, hy - 6), Vector2(hx + 12, hy - 2), Vector2(hx + 4, hy)]), dark)
	draw_colored_polygon(PackedVector2Array([Vector2(hx - 7, hy), Vector2(hx - 5, hy - 30), Vector2(hx + 5, hy - 30), Vector2(hx + 7, hy)]), dark)
	draw_circle(Vector2(hx, hy - 35), 7, dark)
	draw_colored_polygon(PackedVector2Array([Vector2(hx - 7, hy - 36), Vector2(hx, hy - 47), Vector2(hx + 7, hy - 36)]), dark)
	draw_line(Vector2(hx - 6, hy - 24), Vector2(hx - 18, hy - 54), Color(0.18, 0.16, 0.18), 2.0)   # raised blade
	draw_line(Vector2(hx - 10, hy - 28), Vector2(hx - 3, hy - 24), Color(0.12, 0.1, 0.12), 2.0)
	var eye := 0.6 + 0.4 * sin(t * 2.0)
	draw_rect(Rect2(hx - 3, hy - 36, 2, 1), Color(1.0, 0.2, 0.1, eye))
	draw_rect(Rect2(hx + 1, hy - 36, 2, 1), Color(1.0, 0.2, 0.1, eye))
	# low fog rolling over the field
	for f in fog:
		var fx := fposmod(f.x + t * 7.0, 560.0) - 40.0
		draw_circle(Vector2(fx, f.y), f.z, Color(0.35, 0.3, 0.33, 0.07))
	if flash > 0.0:
		draw_rect(Rect2(0, 0, 480, 270), Color(0.85, 0.8, 1.0, 0.35 * flash * flash))
	# embers drifting up from the fires below
	for e in embers:
		var y := fposmod(e.y - t * 18.0 * e.z, 290.0) - 10.0
		var xx: float = e.x + sin(t * 1.3 + e.y) * 6.0
		var life := clampf(y / 270.0, 0.0, 1.0)
		var col := Color(1.0, 0.45 + 0.35 * e.z, 0.15, 0.25 + 0.6 * life)
		draw_rect(Rect2(int(xx), int(y), 1 if e.z < 0.75 else 2, 1 if e.z < 0.75 else 2), col)
	# the logo, with a faint hot glow that flickers like firelight behind it
	if logo:
		var flick := 0.55 + 0.25 * sin(t * 7.0) + 0.15 * sin(t * 13.0 + 1.0)
		var lp := Vector2(240 - logo.get_width() * 0.5, 22).round()
		draw_rect(Rect2(lp.x - 6, lp.y + 8, logo.get_width() + 12, logo.get_height() - 12), Color(0.5, 0.08, 0.04, 0.12 * flick))
		draw_texture(logo, lp)
	# six dim hearth embers under the title, waiting to be relit
	for i in 6:
		var col := DB.el_color(ELS[i])
		var p := Vector2(240 - 75 + i * 30, 104)
		var pulse := 0.4 + 0.3 * sin(t * 1.1 + i * 0.9)
		draw_circle(p, 6, Color(col.r, col.g, col.b, 0.1 * pulse))
		draw_circle(p, 2.5, Color(col.r * 0.6, col.g * 0.6, col.b * 0.6, 0.5 + 0.4 * pulse))
	if mode == "main":
		var opts := _options()
		var r := Rect2(186, 152, 108, 12 + opts.size() * 16)
		Art.window(self, r)
		for i in opts.size():
			var col := Art.WHITE if opts[i] != "Continue" or _has_save() else Art.GREY
			if opts[i] == "New Game+":
				col = Color(1, 0.8, 0.35)
			Art.text(self, r.position + Vector2(26, 6 + i * 16), opts[i], col)
		Art.cursor(self, r.position + Vector2(26, 6 + idx * 16))
	else:
		var r := Rect2(110, 130, 260, 130)
		Art.window(self, r)
		for i in 4:
			var s := GS.slot_summary(i)
			var y := r.position.y + 8 + i * 30
			Art.text(self, Vector2(r.position.x + 30, y), "Autosave" if i == 0 else "Slot %d" % i)
			if s.is_empty():
				Art.text(self, Vector2(r.position.x + 110, y), "(empty)", Art.GREY)
			else:
				Art.text(self, Vector2(r.position.x + 110, y), "Lv %d  %s" % [s.level, s.place])
				Art.text(self, Vector2(r.position.x + 110, y + 13), "Hearts %d/6  %s" % [s.hearts, Art.fmt_time(s.time)], Art.GREY)
		Art.cursor(self, Vector2(r.position.x + 30, r.position.y + 8 + slot_idx * 30))
	Art.text(self, Vector2(6, 256), "Z / Enter: select   X / Esc: back", Color(0.6, 0.6, 0.75), 8, Art.font_small)
	if flash_in > 0.0:
		draw_rect(Rect2(0, 0, 480, 270), Color(1, 1, 1, flash_in))
