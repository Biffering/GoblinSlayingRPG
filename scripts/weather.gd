extends Node2D
## Changing weather outdoors: sunshine and birdsong, breezes, rain, thunderstorms, ashfall, snow and void motes.
## Drawn in screen space above the map (or the battle). Weather also nudges elemental damage in battle.

const KINDS := {
	"sunny":  {"name": "Sunny", "amb": "amb_birds", "tint": Color(1.0, 0.92, 0.7, 0.07), "mods": {"fire": 0.15},
			   "msg": "The sun breaks through. Birds are singing."},
	"breeze": {"name": "Breezy", "amb": "amb_breeze", "tint": Color(1, 1, 1, 0.0), "mods": {"wind": 0.15},
			   "msg": "A cool breeze picks up."},
	"gale":   {"name": "Gale", "amb": "amb_gale", "tint": Color(0.7, 0.75, 0.8, 0.08), "mods": {"wind": 0.25, "fire": -0.1},
			   "msg": "The wind howls into a gale."},
	"cloudy": {"name": "Overcast", "amb": "amb_breeze", "tint": Color(0.35, 0.38, 0.45, 0.16), "mods": {},
			   "msg": "Clouds roll over the sky."},
	"rain":   {"name": "Rain", "amb": "amb_rain", "tint": Color(0.2, 0.25, 0.4, 0.22), "mods": {"water": 0.2, "fire": -0.2},
			   "msg": "It starts to rain."},
	"storm":  {"name": "Thunderstorm", "amb": "amb_storm", "tint": Color(0.08, 0.1, 0.22, 0.38),
			   "mods": {"water": 0.15, "wind": 0.2, "fire": -0.2}, "msg": "Thunder rumbles. A storm is coming!"},
	"ash":    {"name": "Ashfall", "amb": "amb_ash", "tint": Color(0.35, 0.25, 0.22, 0.2), "mods": {"fire": 0.2, "water": -0.1},
			   "msg": "Grey ash drifts down from the mountain."},
	"ember":  {"name": "Ember Storm", "amb": "amb_ash", "tint": Color(0.4, 0.08, 0.04, 0.3), "mods": {"fire": 0.25, "water": -0.15},
			   "msg": "The sky turns red. Embers rain down!"},
	"snow":   {"name": "Snowfall", "amb": "amb_hum", "tint": Color(0.85, 0.88, 1.0, 0.12), "mods": {"spirit": 0.2, "fire": -0.1},
			   "msg": "Soft snow begins to fall."},
	"motes":  {"name": "Void Motes", "amb": "amb_hum", "tint": Color(0.2, 0.08, 0.3, 0.22), "mods": {"void": 0.2, "spirit": -0.1},
			   "msg": "Specks of nothing drift up from the ground."},
}
const BY_WORLD := {
	"fire":   {"sunny": 3, "breeze": 1, "ash": 3, "ember": 1},
	"water":  {"sunny": 3, "breeze": 2, "rain": 3, "storm": 2},
	"wind":   {"sunny": 2, "breeze": 4, "gale": 2, "rain": 1, "storm": 1},
	"stone":  {"sunny": 2, "cloudy": 2, "breeze": 2, "rain": 2, "storm": 1},
	"spirit": {"sunny": 3, "snow": 3, "breeze": 2},
	"void":   {"cloudy": 2, "motes": 3, "storm": 1},
}

var in_battle := false
var t := 0.0
var drops: Array = []
var clouds: Array = []
var flash := 0.0
var next_bolt := 6.0
var msg := ""
var msg_t := 0.0
var fade := 1.0         # 0..1 strength while a new weather fades in
var rng := RandomNumberGenerator.new()


static func pick(world: String, r: RandomNumberGenerator, avoid := "") -> String:
	var table: Dictionary = BY_WORLD.get(world, {"sunny": 1})
	var total := 0.0
	for k in table:
		if k != avoid:
			total += float(table[k])
	var x := r.randf() * total
	for k in table:
		if k == avoid:
			continue
		x -= float(table[k])
		if x <= 0:
			return k
	return table.keys()[0]


static func mult(el) -> float:
	## Battle damage multiplier for an element under the current weather.
	if not GS.weather_on or el == null:
		return 1.0
	var k: Dictionary = KINDS.get(GS.weather.kind, {})
	return 1.0 + float(k.get("mods", {}).get(str(el), 0.0))


static func describe(kind: String) -> String:
	var k: Dictionary = KINDS.get(kind, {})
	if k.is_empty():
		return ""
	var parts := []
	var mods: Dictionary = k.mods
	for el in mods:
		parts.append("%s %s%d%%" % [DB.el_name(el), "+" if mods[el] > 0 else "", int(round(mods[el] * 100))])
	return k.name + ("" if parts.is_empty() else ": " + ", ".join(parts))


func _ready() -> void:
	rng.randomize()
	z_index = 50
	for i in 160:
		drops.append(Vector3(rng.randf() * 480, rng.randf() * 270, rng.randf_range(0.6, 1.0)))
	for i in 5:
		clouds.append(Vector3(rng.randf() * 600 - 60, rng.randf() * 270, rng.randf_range(40, 90)))
	if not in_battle:
		_ensure_weather(true)
	_apply_audio()


func _ensure_weather(announce: bool) -> void:
	var world: String = GS.weather.get("world", "")
	if world != GS.weather_world or not KINDS.has(GS.weather.get("kind", "")):
		_change(pick(GS.weather_world, rng), announce)


func _change(kind: String, announce: bool) -> void:
	GS.weather = {"kind": kind, "t": 0.0, "dur": rng.randf_range(70.0, 140.0), "world": GS.weather_world}
	fade = 0.0
	next_bolt = rng.randf_range(3.0, 8.0)
	if announce:
		msg = KINDS[kind].msg
		msg_t = 4.0
	_apply_audio()


func _apply_audio() -> void:
	if not GS.weather_on:
		Audio.ambient("")
		return
	Audio.ambient(str(KINDS[GS.weather.kind].amb), -10.0 if in_battle else -4.0)


func _process(delta: float) -> void:
	t += delta
	fade = min(1.0, fade + delta / 4.0)
	if msg_t > 0:
		msg_t -= delta
	if flash > 0:
		flash = max(0.0, flash - delta * 2.5)
	if GS.weather_on and not in_battle:
		GS.weather.t = float(GS.weather.t) + delta
		if GS.weather.t > float(GS.weather.dur):
			_change(pick(GS.weather_world, rng, GS.weather.kind), true)
	var kind: String = GS.weather.get("kind", "")
	if GS.weather_on and kind in ["storm", "ember"]:
		next_bolt -= delta
		if next_bolt <= 0:
			next_bolt = rng.randf_range(6.0, 14.0)
			flash = 1.0
			_thunder()
	queue_redraw()


func _thunder() -> void:
	await get_tree().create_timer(rng.randf_range(0.2, 1.0)).timeout
	if is_instance_valid(self):
		Audio.sfx("thunder%d" % (1 + rng.randi() % 2), -2.0, 1.0, 0.1)


func _draw() -> void:
	if not GS.weather_on:
		return
	var kind: String = GS.weather.kind
	var k: Dictionary = KINDS[kind]
	var tint: Color = k.tint
	tint.a *= fade
	if tint.a > 0.0:
		draw_rect(Rect2(0, 0, 480, 270), tint)
	# drifting cloud shadows on sunny / cloudy days
	if kind in ["sunny", "cloudy", "breeze"] and not in_battle:
		for c in clouds:
			var x := fposmod(c.x + t * 6.0, 640.0) - 80.0
			var a := (0.06 if kind != "cloudy" else 0.1) * fade
			draw_circle(Vector2(x, c.y), c.z, Color(0.05, 0.05, 0.12, a))
			draw_circle(Vector2(x + c.z * 0.7, c.y + 6), c.z * 0.7, Color(0.05, 0.05, 0.12, a))
	var n := int(drops.size() * fade)
	match kind:
		"rain", "storm":
			var slant := 3.0 if kind == "rain" else 6.0
			var cnt := n if kind == "storm" else floori(n * 2 / 3.0)
			for i in cnt:
				var d: Vector3 = drops[i]
				var y := fposmod(d.y + t * 320.0 * d.z, 290.0) - 10.0
				var x := fposmod(d.x - y * slant / 12.0, 480.0)
				draw_line(Vector2(x, y), Vector2(x - slant, y + 9), Color(0.75, 0.82, 1.0, 0.45 * d.z), 1.0)
		"ash", "ember":
			for i in floori(n / 2.0):
				var d: Vector3 = drops[i]
				var y := fposmod(d.y + t * 22.0 * d.z, 280.0) - 5.0
				var x := fposmod(d.x + sin(t * 0.8 + d.y) * 10.0, 480.0)
				var col := Color(0.72, 0.68, 0.66, 0.6) if kind == "ash" or i % 3 else Color(1.0, 0.5, 0.15, 0.85)
				draw_rect(Rect2(int(x), int(y), 2 if d.z > 0.85 else 1, 1), col)
		"snow":
			for i in floori(n / 2.0):
				var d: Vector3 = drops[i]
				var y := fposmod(d.y + t * 26.0 * d.z, 280.0) - 5.0
				var x := fposmod(d.x + sin(t * 1.1 + d.y * 0.1) * 8.0, 480.0)
				draw_rect(Rect2(int(x), int(y), 2 if d.z > 0.8 else 1, 2 if d.z > 0.8 else 1), Color(1, 1, 1, 0.85))
		"motes":
			for i in floori(n / 3.0):
				var d: Vector3 = drops[i]
				var y := fposmod(d.y - t * 12.0 * d.z, 280.0) - 5.0
				var x := fposmod(d.x + sin(t * 0.6 + d.y) * 6.0, 480.0)
				var pulse := 0.5 + 0.5 * sin(t * 3.0 + d.x)
				draw_rect(Rect2(int(x), int(y), 1, 1), Color(0.75, 0.5, 1.0, 0.3 + 0.5 * pulse))
		"breeze", "gale":
			var cnt := floori(n / 8.0) if kind == "breeze" else floori(n / 3.0)
			for i in cnt:
				var d: Vector3 = drops[i]
				var sp := 60.0 if kind == "breeze" else 170.0
				var x := fposmod(d.x + t * sp * d.z, 500.0) - 10.0
				var y := fposmod(d.y + sin(t * 2.0 + d.x) * 8.0, 270.0)
				if kind == "gale" and i % 2 == 0:
					draw_line(Vector2(x, y), Vector2(x - 14, y), Color(1, 1, 1, 0.25), 1.0)
				else:
					var leaf := Color(0.55, 0.75, 0.3, 0.9) if GS.weather_world != "fire" else Color(0.85, 0.45, 0.2, 0.9)
					draw_rect(Rect2(int(x), int(y), 2, 1), leaf)
		"sunny":
			# a few motes of light in the sunbeams
			for i in 14:
				var d: Vector3 = drops[i]
				var y := fposmod(d.y + sin(t * 0.5 + d.x) * 20.0, 270.0)
				draw_rect(Rect2(int(d.x), int(y), 1, 1), Color(1, 0.95, 0.7, 0.35 + 0.3 * sin(t * 2.0 + d.y)))
	if flash > 0.0:
		var fc := Color(1, 1, 1) if kind == "storm" else Color(1, 0.5, 0.3)
		draw_rect(Rect2(0, 0, 480, 270), Color(fc.r, fc.g, fc.b, 0.55 * flash * flash))
	if msg_t > 0.0 and not in_battle:
		var a := clampf(msg_t, 0.0, 1.0)
		var line := msg
		var sub := describe(kind)
		var w: float = max(Art.width(line), Art.width(sub, 9)) + 20
		draw_rect(Rect2(6, 238, w, 28), Color(0.02, 0.02, 0.06, 0.6 * a))
		Art.text(self, Vector2(16, 240), line, Color(1, 1, 1, a))
		Art.text(self, Vector2(16, 253), sub, Color(0.8, 0.9, 1.0, a), 9)
