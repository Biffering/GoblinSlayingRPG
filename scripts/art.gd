extends Node
## Textures, fonts, shaders and the small UI drawing kit every screen uses.

var font: FontFile
var font_title: FontFile
var font_small: FontFile
var tiles_index: Dictionary = {}
var icons_index: Dictionary = {}
var tex_cache: Dictionary = {}
var aura_shader: Shader
var body_shader: Shader
var window_box: StyleBoxTexture
var window_dark: StyleBoxTexture
var window_gold: StyleBoxTexture
var enemy_sizes: Dictionary = {}
var hands: Dictionary = {}

const FS := 11          # body text size
const LINE := 15        # body line height
const WHITE := Color(0.96, 0.93, 0.88)
const GREY := Color(0.66, 0.62, 0.6)
const YELLOW := Color(1.0, 0.84, 0.46)
const RED := Color(1.0, 0.4, 0.4)
const GREEN := Color(0.5, 1.0, 0.55)
const CYAN := Color(0.55, 0.9, 1.0)


func _ready() -> void:
	font = _clean_font("res://assets/fonts/Inter-Bold.otf")
	font_title = _pixel_font("res://assets/fonts/PressStart2P.ttf")
	font_small = font
	tiles_index = JSON.parse_string(FileAccess.open("res://assets/tiles/index.json", FileAccess.READ).get_as_text())
	var icons: Array = JSON.parse_string(FileAccess.open("res://assets/ui/icons.json", FileAccess.READ).get_as_text())
	for i in icons.size():
		icons_index[icons[i]] = i
	enemy_sizes = JSON.parse_string(FileAccess.open("res://assets/enemies/sizes.json", FileAccess.READ).get_as_text())
	hands = JSON.parse_string(FileAccess.open("res://assets/battle/hands.json", FileAccess.READ).get_as_text())
	aura_shader = load("res://shaders/aura.gdshader")
	body_shader = load("res://shaders/body.gdshader")
	window_box = _box("res://assets/ui/window.png")
	window_dark = _box("res://assets/ui/window_dark.png")
	window_gold = _box("res://assets/ui/window_gold.png")


func _pixel_font(path: String) -> FontFile:
	var f: FontFile = load(path)
	f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	f.hinting = TextServer.HINTING_NONE
	f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	f.generate_mipmaps = false
	return f


## Plain, bold, easy-to-read text. Rendered at full window resolution (stretch mode canvas_items).
func _clean_font(path: String) -> FontFile:
	var f: FontFile = load(path)
	f.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
	f.hinting = TextServer.HINTING_LIGHT
	f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	f.generate_mipmaps = false
	return f


func _box(path: String) -> StyleBoxTexture:
	var sb := StyleBoxTexture.new()
	sb.texture = load(path)
	sb.texture_margin_left = 6
	sb.texture_margin_right = 6
	sb.texture_margin_top = 6
	sb.texture_margin_bottom = 6
	# riveted iron frame over leather: tile it so the grain and the hammered band never smear
	sb.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	sb.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	return sb


func tex(path: String) -> Texture2D:
	if not tex_cache.has(path):
		if ResourceLoader.exists(path):
			tex_cache[path] = load(path)
		else:
			tex_cache[path] = null
	return tex_cache[path]


func tileset(world: String) -> Texture2D:
	return tex("res://assets/tiles/%s.png" % world)


func tile_rect(tile_name: String) -> Rect2:
	var i: int = int(tiles_index.get(tile_name, 0))
	return Rect2((i % 16) * 32, floori(i / 16.0) * 32, 32, 32)


# ------------------------------------------------------------------ drawing kit

func window(ci: CanvasItem, r: Rect2, style: String = "blue") -> void:
	var sb := window_box
	if style == "dark":
		sb = window_dark
	elif style == "gold":
		sb = window_gold
	ci.draw_style_box(sb, r)


func text(ci: CanvasItem, pos: Vector2, s: String, col: Color = WHITE, size: int = FS, f: Font = null, shadow := true) -> void:
	if f == null:
		f = font
	var p := Vector2(round(pos.x), round(pos.y + size * 0.95))
	if shadow:
		var sh := Color(0.04, 0.02, 0.02, col.a * 0.9)
		ci.draw_string(f, p + Vector2(0.67, 0.67), s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, sh)
		ci.draw_string(f, p + Vector2(0.34, 0.67), s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, sh)
	ci.draw_string(f, p, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


func text_right(ci: CanvasItem, pos: Vector2, s: String, col: Color = WHITE, size: int = FS, f: Font = null) -> void:
	text(ci, pos - Vector2(width(s, size, f), 0), s, col, size, f)


func text_center(ci: CanvasItem, pos: Vector2, s: String, col: Color = WHITE, size: int = FS, f: Font = null, shadow := true) -> void:
	text(ci, pos - Vector2(roundf(width(s, size, f) / 2.0), 0), s, col, size, f, shadow)


## Draws text that never spills past `max_w`: it shrinks (down to `min_size`), and if it still won't fit
## it's cut short with a trailing dot. Returns the width it used.
func text_fit(ci: CanvasItem, pos: Vector2, s: String, col: Color, max_w: float, size: int = FS, min_size: int = 8, f: Font = null) -> float:
	var fs := fit_size(s, max_w, size, min_size, f)
	var t := s
	if width(t, fs, f) > max_w:
		while t.length() > 1 and width(t + ".", fs, f) > max_w:
			t = t.substr(0, t.length() - 1)
		t = t.strip_edges() + "."
	# keep shrunk text on the same baseline as full-size text beside it
	text(ci, pos + Vector2(0, (size - fs) * 0.8), t, col, fs, f)
	return width(t, fs, f)


func text_fit_right(ci: CanvasItem, pos: Vector2, s: String, col: Color, max_w: float, size: int = FS, min_size: int = 8) -> void:
	var fs := fit_size(s, max_w, size, min_size)
	var w := minf(width(s, fs), max_w)
	text_fit(ci, pos - Vector2(w, 0), s, col, max_w, size, min_size)


func fit_size(s: String, max_w: float, size: int = FS, min_size: int = 8, f: Font = null) -> int:
	var fs := size
	while fs > min_size and width(s, fs, f) > max_w:
		fs -= 1
	return fs


func width(s: String, size: int = FS, f: Font = null) -> float:
	if f == null:
		f = font
	return f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x


func wrap(s: String, max_w: float, size: int = FS) -> Array:
	var lines := []
	for para in s.split("\n"):
		var cur := ""
		for word in para.split(" "):
			var t := word if cur == "" else cur + " " + word
			if width(t, size) > max_w and cur != "":
				lines.append(cur)
				cur = word
			else:
				cur = t
		lines.append(cur)
	return lines


func cursor(ci: CanvasItem, pos: Vector2) -> void:
	var t := tex("res://assets/ui/cursor.png")
	var bob := 1.0 if fmod(Time.get_ticks_msec() / 1000.0, 0.6) < 0.3 else 0.0
	ci.draw_texture(t, Vector2(round(pos.x - 17 + bob), round(pos.y + 3)))


func icon(ci: CanvasItem, icon_name: String, pos: Vector2, mod: Color = WHITE) -> void:
	var i: int = icons_index.get(icon_name, 0)
	ci.draw_texture_rect_region(tex("res://assets/ui/icons.png"), Rect2(pos.round(), Vector2(10, 10)), Rect2(i * 10, 0, 10, 10), mod)


func bar(ci: CanvasItem, r: Rect2, frac: float, col: Color, back: Color = Color(0.07, 0.04, 0.04, 0.95)) -> void:
	# iron-rimmed gauge
	ci.draw_rect(r.grow(1), Color(0.04, 0.03, 0.03))
	ci.draw_rect(Rect2(r.position.x - 1, r.end.y, r.size.x + 2, 1), Color(0.42, 0.39, 0.43))
	ci.draw_rect(r, back)
	var w := floorf((r.size.x - 2) * clampf(frac, 0.0, 1.0))
	if w > 0:
		ci.draw_rect(Rect2(r.position + Vector2(1, 1), Vector2(w, r.size.y - 2)), col)
		ci.draw_rect(Rect2(r.position + Vector2(1, 1), Vector2(w, 1)), col.lightened(0.35))
		if r.size.y > 3:
			ci.draw_rect(Rect2(r.position + Vector2(1, r.size.y - 2), Vector2(w, 1)), col.darkened(0.35))


func element_icons(ci: CanvasItem, els: Array, pos: Vector2) -> void:
	var x := pos.x
	for e in els:
		icon(ci, e, Vector2(x, pos.y))
		x += 11


func fmt_time(t: float) -> String:
	var s := int(t)
	return "%d:%02d" % [floori(s / 3600.0), floori(s / 60.0) % 60]


# ------------------------------------------------------------------ materials

func aura_material(colors: Array, strength: float, radius: float, seed_v: float = 0.0) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = aura_shader
	set_aura(m, colors, strength, radius, seed_v)
	return m


func set_aura(m: ShaderMaterial, colors: Array, strength: float, radius: float, seed_v: float = 0.0) -> void:
	var cols := []
	for e in colors:
		cols.append(DB.el_color(e))
	if cols.is_empty():
		strength = 0.0
		cols.append(Color.WHITE)
	while cols.size() < 3:
		cols.append(cols[cols.size() % max(1, colors.size())] if colors.size() > 0 else Color.WHITE)
	m.set_shader_parameter("col0", cols[0])
	m.set_shader_parameter("col1", cols[1])
	m.set_shader_parameter("col2", cols[2])
	m.set_shader_parameter("ncol", max(1, colors.size()))
	m.set_shader_parameter("strength", strength)
	m.set_shader_parameter("radius", radius)
	m.set_shader_parameter("seed", seed_v)


func body_material() -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = body_shader
	return m
