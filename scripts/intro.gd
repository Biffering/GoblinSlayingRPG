extends Node2D
## Opening cutscene: a storm, the goblin horde on the ridge, the hooded slayer, a charge... and a sword's CHINK
## that flashes straight into the title screen. Any button skips.

signal finished

var t := 0.0
var done := false
var rng := RandomNumberGenerator.new()
var rain: Array = []
var flash := 0.0
var next_bolt := 1.2
var shake := 0.0
var hero_tex: Texture2D
var king_tex: Texture2D
var goblin_tex: Texture2D
var clashed := false

const LINES := [
	[1.6, 5.4, "Six worlds. Six Hearths."],
	[3.2, 5.4, "Cursed, one by one, by a king of goblins."],
	[5.9, 9.6, "Their sorrow made him rich."],
	[7.4, 9.6, "Their fear made him king."],
	[10.0, 12.6, "But out of the storm came one who would not kneel."],
]
const CLASH_T := 14.2


func _ready() -> void:
	rng.randomize()
	for i in 220:
		rain.append(Vector3(rng.randf() * 520, rng.randf() * 270, rng.randf_range(0.6, 1.0)))
	hero_tex = Art.tex("res://assets/battle/hero_t0.png")
	king_tex = Art.tex("res://assets/enemies/u_king_goblin.png")
	goblin_tex = Art.tex("res://assets/enemies/goblin_void.png")
	Audio.stop_music(0.5)
	Audio.ambient("amb_storm", -6.0)
	Inp.block(10)


func _process(delta: float) -> void:
	if done:
		return
	t += delta
	flash = max(0.0, flash - delta * 2.4)
	shake = max(0.0, shake - delta * 18.0)
	next_bolt -= delta
	if next_bolt <= 0.0 and t < CLASH_T - 1.5:
		next_bolt = rng.randf_range(1.8, 3.4)
		flash = 1.0
		_thunder()
	if t >= CLASH_T and not clashed:
		clashed = true
		Audio.sfx("sword_clash", 4.0, 1.0, 0.0)
		Audio.sfx("thunder1", 0.0, 0.8, 0.0)
		flash = 1.6
		shake = 8.0
	if t >= CLASH_T + 0.35 or (t > 0.6 and (Inp.ok() or Inp.back())):
		if not clashed:
			Audio.sfx("sword_clash", 2.0, 1.0, 0.0)
		done = true
		finished.emit()
	queue_redraw()


func _thunder() -> void:
	await get_tree().create_timer(rng.randf_range(0.2, 0.7)).timeout
	if is_instance_valid(self) and not done:
		Audio.sfx("thunder%d" % (1 + rng.randi() % 2), -1.0, 1.0, 0.1)


func _sil(tex: Texture2D, src: Rect2, dst: Rect2, lit: float, flip := false) -> void:
	## Pitch-black silhouette that the lightning picks out for an instant.
	if tex == null:
		return
	var c := Color(0.04, 0.02, 0.035).lerp(Color(0.55, 0.5, 0.62), clampf(lit, 0.0, 1.0))
	if flip:
		dst = Rect2(dst.position.x + dst.size.x, dst.position.y, -dst.size.x, dst.size.y)
	draw_texture_rect_region(tex, dst, src, c)


func _draw() -> void:
	var off := Vector2(rng.randf_range(-shake, shake), rng.randf_range(-shake, shake))
	draw_set_transform(off)
	var lit := flash
	# sky
	for y in 270:
		var k := y / 270.0
		var c := Color(0.02, 0.015, 0.025).lerp(Color(0.14, 0.03, 0.04), pow(k, 1.8))
		draw_rect(Rect2(-10, y, 500, 1), c.lerp(Color(0.5, 0.48, 0.6), lit * 0.35))
	if t < 1.4:
		draw_rect(Rect2(-10, -10, 500, 290), Color(0, 0, 0, 1.0 - t / 1.4))
	# --- shot 1: the horde on the ridge
	if t < 5.6:
		var ridge := PackedVector2Array([Vector2(-10, 270), Vector2(-10, 190)])
		for i in 26:
			ridge.append(Vector2(i * 20 - 10, 186 + sin(i * 1.7) * 8 + (i % 3) * 3))
		ridge.append(Vector2(510, 270))
		draw_colored_polygon(ridge, Color(0.03, 0.02, 0.025).lerp(Color(0.3, 0.28, 0.34), lit * 0.5))
		for i in 14:
			var gx := 20.0 + i * 33.0 + sin(i * 3.1) * 8.0
			var gy := 190.0 + sin(i * 1.7) * 6.0
			if goblin_tex:
				var w := goblin_tex.get_width()
				var h := goblin_tex.get_height()
				_sil(goblin_tex, Rect2(0, 0, w, h), Rect2(gx - w * 0.4, gy - h * 0.8, w * 0.8, h * 0.8), lit, i % 2 == 0)
			var blink := 0.6 + 0.4 * sin(t * 3.0 + i)
			draw_rect(Rect2(gx - 3, gy - 30, 2, 1), Color(1, 0.85, 0.1, blink))
			draw_rect(Rect2(gx + 1, gy - 30, 2, 1), Color(1, 0.85, 0.1, blink))
		if king_tex:
			var kw := king_tex.get_width()
			var kh := king_tex.get_height()
			var rise := clampf((t - 0.5) / 3.0, 0.0, 1.0)
			_sil(king_tex, Rect2(0, 0, kw, kh), Rect2(240 - kw * 0.5, 196 - kh * rise, kw, kh * rise), lit)
			draw_rect(Rect2(240 - 8, 196 - kh * rise + kh * 0.22, 4, 2), Color(1, 0.2, 0.05, rise))
			draw_rect(Rect2(240 + 4, 196 - kh * rise + kh * 0.22, 4, 2), Color(1, 0.2, 0.05, rise))
	# --- shots 2-3: the slayer in the rain, then the sword comes out
	elif t < CLASH_T - 1.6:
		draw_colored_polygon(PackedVector2Array([Vector2(-10, 270), Vector2(-10, 218), Vector2(500, 226), Vector2(500, 270)]),
			Color(0.04, 0.025, 0.03))
		if hero_tex:
			var s := 3.0
			var frame := 0
			if t > 10.6:
				frame = 10 + mini(5, int((t - 10.6) * 6.0))     # the slash
			var src := Rect2(frame * 96, 0, 96, 96)
			var push := clampf((t - 5.6) / 6.0, 0.0, 1.0) * 30.0
			var dst := Rect2(240 - 48 * s + 40 - push, 230 - 96 * s + 8 * s, 96 * s, 96 * s)
			_sil(hero_tex, src, dst, lit * 0.9)
			# the eyes burn under the hood
			var eye := 0.7 + 0.3 * sin(t * 2.3)
			var ex := dst.position.x + 44 * s
			var ey := dst.position.y + 52 * s
			draw_rect(Rect2(ex, ey, 2 * s, 2 * s), Color(1, 0.15, 0.05, eye))
			draw_circle(Vector2(ex + s, ey + s), 10, Color(1, 0.1, 0.05, 0.15 * eye))
	# --- shot 4: the charge
	else:
		var k := clampf((t - (CLASH_T - 1.6)) / 1.6, 0.0, 1.0)
		for i in 30:
			var y := 30.0 + i * 8.0
			var x := fposmod(i * 97.0 - t * 900.0, 560.0) - 40.0
			draw_line(Vector2(x, y), Vector2(x + 60, y), Color(0.8, 0.75, 0.85, 0.12), 1.0)
		if king_tex:
			var kw := king_tex.get_width()
			var kh := king_tex.get_height()
			_sil(king_tex, Rect2(0, 0, kw, kh), Rect2(-kw + (240 - 10 + kw * 0.2) * k, 230 - kh, kw, kh), 0.15)
		if hero_tex:
			var s := 2.0
			var src := Rect2((10 + mini(5, int(k * 6.0))) * 96, 0, 96, 96)
			var hx := 480 - (240 + 10) * k
			_sil(hero_tex, src, Rect2(hx - 48 * s, 230 - 88 * s, 96 * s, 96 * s), 0.15)
	# rain over everything
	for d in rain:
		var y := fposmod(d.y + t * 380.0 * d.z, 290.0) - 10.0
		var x := fposmod(d.x - y * 0.5, 520.0) - 20.0
		draw_line(Vector2(x, y), Vector2(x - 5, y + 11), Color(0.7, 0.72, 0.85, 0.35 * d.z), 1.0)
	# words
	for ln in LINES:
		if t >= ln[0] and t <= ln[1]:
			var a := clampf(min(t - ln[0], ln[1] - t) * 2.0, 0.0, 1.0)
			var row := 0 if ln[0] in [1.6, 5.9, 10.0] else 1
			Art.text_center(self, Vector2(240, 214 + row * 18) if t >= 5.6 else Vector2(240, 30 + row * 18), ln[2], Color(0.92, 0.88, 0.9, a), 13)
	draw_set_transform(Vector2.ZERO)
	if flash > 0.0:
		draw_rect(Rect2(0, 0, 480, 270), Color(1, 1, 1, clampf(flash, 0.0, 1.0) * (0.45 if not clashed else 1.0)))
	if t < 1.0:
		Art.text(self, Vector2(6, 256), "Z: skip", Color(0.6, 0.6, 0.7, 0.5), 8)
