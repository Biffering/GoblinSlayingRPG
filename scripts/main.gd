class_name Main
extends Node
## Screen router: title, exploration map, battles, ending. Owns fades and the battle transition.

static var inst

const IntroScene := preload("res://scripts/intro.gd")
const TitleScreen := preload("res://scripts/title.gd")
const MapScreen := preload("res://scripts/map.gd")
const BattleScreen := preload("res://scripts/battle.gd")
const EndingScreen := preload("res://scripts/ending.gd")

var screen: Node = null
var map_node: Node = null
var battle_node: Node = null
var overlay: CanvasLayer
var fader: Fader
var busy := false


class Fader extends Node2D:
	var alpha := 0.0
	var color := Color.BLACK
	var shatter := 0.0     # battle transition progress 0..1
	var flash := 0.0

	func _process(_d: float) -> void:
		queue_redraw()

	func _draw() -> void:
		var vp := Vector2(480, 270)
		if shatter > 0.0:
			# blinds closing from both sides, in pixel steps
			var n := 18
			for i in n:
				var h := vp.y / n
				var w := vp.x * clampf(shatter * 1.6 - float(i % 3) * 0.15, 0.0, 1.0) / 2.0
				w = floorf(w / 8.0) * 8.0
				draw_rect(Rect2(0, i * h, w, h + 1), Color.BLACK)
				draw_rect(Rect2(vp.x - w, i * h, w, h + 1), Color.BLACK)
		if alpha > 0.0:
			draw_rect(Rect2(Vector2.ZERO, vp), Color(color.r, color.g, color.b, alpha))
		if flash > 0.0:
			draw_rect(Rect2(Vector2.ZERO, vp), Color(1, 1, 1, flash))


func _ready() -> void:
	inst = self
	randomize()
	GS.load_settings()
	overlay = CanvasLayer.new()
	overlay.layer = 100
	add_child(overlay)
	fader = Fader.new()
	overlay.add_child(fader)
	play_intro()


func play_intro() -> void:
	var intro = IntroScene.new()
	fader.alpha = 0.0
	_set_screen(intro)
	await intro.finished
	# the sword's CHINK flashes straight into the title
	var ts = TitleScreen.new()
	ts.flash_in = 1.0
	_set_screen(ts)


func _set_screen(n: Node) -> void:
	if screen and is_instance_valid(screen):
		screen.queue_free()
	screen = n
	add_child(n)
	move_child(n, 0)


func fade_out(t := 0.25) -> void:
	var tw := create_tween()
	tw.tween_property(fader, "alpha", 1.0, t)
	await tw.finished


func fade_in(t := 0.25) -> void:
	var tw := create_tween()
	tw.tween_property(fader, "alpha", 0.0, t)
	await tw.finished


func goto_title() -> void:
	fader.alpha = 1.0
	GS.weather_on = false
	Audio.ambient("")
	if map_node:
		map_node.queue_free()
		map_node = null
	_set_screen(TitleScreen.new())
	await fade_in(0.5)


func start_new_game() -> void:
	await fade_out(0.4)
	GS.new_game()
	_open_map(GS.location.map, GS.location.x, GS.location.y, GS.location.face)
	await fade_in(0.5)


func start_new_game_plus() -> void:
	await fade_out(0.4)
	GS.new_game_plus()
	_open_map(GS.location.map, GS.location.x, GS.location.y, GS.location.face)
	await fade_in(0.5)


func continue_game(slot: int) -> void:
	await fade_out(0.4)
	if GS.load_game(slot):
		_open_map(GS.location.map, GS.location.x, GS.location.y, GS.location.face)
	await fade_in(0.5)


func _open_map(mid: String, x: int, y: int, face: int) -> void:
	if map_node and is_instance_valid(map_node):
		map_node.queue_free()
	map_node = MapScreen.new()
	map_node.setup(mid, x, y, face)
	if screen and is_instance_valid(screen) and screen != map_node:
		screen.queue_free()
	screen = map_node
	add_child(map_node)
	move_child(map_node, 0)


func change_map(mid: String, x: int, y: int, face: int) -> void:
	busy = true
	await fade_out(0.22)
	_open_map(mid, x, y, face)
	await fade_in(0.22)
	busy = false


## Runs a battle on top of the map. Returns "win", "flee" or "lose" (after the game-over screen chose retry/load/title).
var in_battle := false


func battle(enemies: Array, opts: Dictionary = {}) -> String:
	if in_battle or battle_node != null:
		return "busy"
	in_battle = true
	busy = true
	GS.snapshot()
	Audio.sfx("encounter")
	var prev_music: String = Audio.current
	# transition
	for i in 2:
		fader.flash = 0.8
		var tw := create_tween()
		tw.tween_property(fader, "flash", 0.0, 0.12)
		await tw.finished
	var tw2 := create_tween()
	tw2.tween_property(fader, "shatter", 1.0, 0.45)
	await tw2.finished
	_map_visible(false)
	battle_node = BattleScreen.new()
	battle_node.setup(enemies, opts)
	add_child(battle_node)
	fader.shatter = 0.0
	fader.alpha = 1.0
	await fade_in(0.3)
	var result: String = await battle_node.finished
	await fade_out(0.35)
	battle_node.queue_free()
	battle_node = null
	in_battle = false
	if result == "retry":
		GS.restore_snapshot()
		busy = false
		fader.alpha = 0.0
		_map_visible(true)
		return await battle(enemies, opts)
	if result == "title":
		busy = false
		goto_title()
		return "lose"
	if result == "load":
		busy = false
		map_node.queue_free()
		map_node = null
		_set_screen(TitleScreen.new())
		screen.open_load = true
		await fade_in(0.3)
		return "lose"
	_map_visible(true)
	if prev_music != "":
		Audio.music(prev_music, 0.6)
	await fade_in(0.3)
	busy = false
	return result


func _map_visible(on: bool) -> void:
	if map_node == null or not is_instance_valid(map_node):
		return
	map_node.visible = on
	map_node.ui.visible = on
	if map_node.weather_layer:
		map_node.weather_layer.visible = on
		if on and map_node.weather:
			map_node.weather._apply_audio()
	map_node.process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED


func show_ending() -> void:
	busy = true
	await fade_out(0.8)
	_map_visible(false)
	Audio.ambient("")
	var e := EndingScreen.new()
	add_child(e)
	await fade_in(0.8)
	await e.finished
	GS.save_clear()
	await fade_out(0.8)
	e.queue_free()
	_map_visible(true)
	Audio.music(DB.map(GS.location.map).music)
	await fade_in(0.8)
	busy = false
