class_name Actor2D
extends Node2D
## A sprite-sheet character with an elemental aura layer behind it and a flash/glow body shader.
## Position is the character's feet (bottom center of the frame).

var sheet: Texture2D
var aura_tex: Texture2D
var weapon_tex: Texture2D
var frame_size := Vector2(20, 20)
var cols := 3
var frame := 0
var flip_h := false
var offset := Vector2.ZERO
var aura_mat: ShaderMaterial
var body_mat: ShaderMaterial
var _shadow_layer: Layer
var _aura_layer: Layer
var _body_layer: Layer
var _wglow_layer: Layer
var wglow_mat: ShaderMaterial
var weapon_tier := ""
var shadow := true
var shadow_w := 6.0
var shadow_y := 0.0      # the shadow sits at the feet (the node's position), whatever the sprite offset


class Layer extends Node2D:
	var actor
	var mode := 0  # 0 shadow, 1 aura, 2 body, 3 weapon glow

	func _draw() -> void:
		actor._draw_layer(self, mode)


func setup(sheet_path: String, fsize: Vector2, columns: int, aura_path: String = "") -> void:
	sheet = Art.tex(sheet_path)
	frame_size = fsize
	cols = columns
	aura_tex = Art.tex(aura_path) if aura_path != "" else null
	if _aura_layer == null:
		_shadow_layer = Layer.new()
		_shadow_layer.actor = self
		_shadow_layer.mode = 0
		add_child(_shadow_layer)
		_aura_layer = Layer.new()
		_aura_layer.actor = self
		_aura_layer.mode = 1
		aura_mat = Art.aura_material([], 0.0, 1.0, randf() * 6.0)
		_aura_layer.material = aura_mat
		add_child(_aura_layer)
		_wglow_layer = Layer.new()
		_wglow_layer.actor = self
		_wglow_layer.mode = 3
		wglow_mat = ShaderMaterial.new()
		wglow_mat.shader = load("res://shaders/weapon_glow.gdshader")
		_wglow_layer.material = wglow_mat
		add_child(_wglow_layer)
		_body_layer = Layer.new()
		_body_layer.actor = self
		_body_layer.mode = 2
		body_mat = Art.body_material()
		_body_layer.material = body_mat
		add_child(_body_layer)
	redraw()


func set_aura(colors: Array, strength: float, radius: float) -> void:
	if aura_mat:
		Art.set_aura(aura_mat, colors, strength, radius, aura_mat.get_shader_parameter("seed"))


## Rare weapons glow magenta, legendary ones gold, Blessed ones a cold electric cyan.
func set_weapon_tier(t: String) -> void:
	weapon_tier = t
	if wglow_mat:
		var c := Color(1.0, 0.82, 0.25) if t == "legendary" else Color(1.0, 0.3, 0.85)
		if t == "blessed":
			c = Color(0.55, 0.95, 1.0)
		wglow_mat.set_shader_parameter("glow_color", c)
		wglow_mat.set_shader_parameter("strength", 1.0 if t == "blessed" else (0.95 if t == "legendary" else (0.75 if t == "rare" else 0.0)))
	redraw()


func set_flash(v: float) -> void:
	if body_mat:
		body_mat.set_shader_parameter("flash", v)


func set_glow(on: bool) -> void:
	if body_mat:
		body_mat.set_shader_parameter("glow", 1.0 if on else 0.0)


func set_fade(v: float) -> void:
	if body_mat:
		body_mat.set_shader_parameter("fade", v)


func set_tint(c: Color, amount: float) -> void:
	if body_mat:
		body_mat.set_shader_parameter("tint", c)
		body_mat.set_shader_parameter("tint_amount", amount)


func set_frame(f: int) -> void:
	if f != frame:
		frame = f
		redraw()


func redraw() -> void:
	if _aura_layer:
		_shadow_layer.queue_redraw()
		_aura_layer.queue_redraw()
		_wglow_layer.queue_redraw()
		_body_layer.queue_redraw()


func _src(f: int) -> Rect2:
	return Rect2((f % cols) * frame_size.x, floori(float(f) / cols) * frame_size.y, frame_size.x, frame_size.y)


func _dest() -> Rect2:
	var pos := Vector2(-frame_size.x / 2.0, -frame_size.y) + offset
	var size := frame_size
	if flip_h:
		size.x = -size.x
		pos.x += frame_size.x
	return Rect2(pos.round(), size)


func _draw_layer(layer: Node2D, mode: int) -> void:
	if sheet == null:
		return
	if mode == 0:
		if shadow:
			layer.draw_rect(Rect2(Vector2(-shadow_w + offset.x, -2 + shadow_y), Vector2(shadow_w * 2, 3)).abs(), Color(0, 0, 0, 0.28))
		return
	if mode == 3:
		if weapon_tex and weapon_tier in ["rare", "legendary", "blessed"]:
			var d := _dest()
			for o in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1), Vector2(-1, -1), Vector2(1, 1)]:
				layer.draw_texture_rect_region(weapon_tex, Rect2(d.position + o, d.size), _src(frame))
		return
	if mode == 1:
		if aura_tex:
			layer.draw_texture_rect_region(aura_tex, _dest(), _src(frame))
		return
	layer.draw_texture_rect_region(sheet, _dest(), _src(frame))
	if weapon_tex:
		layer.draw_texture_rect_region(weapon_tex, _dest(), _src(frame))
