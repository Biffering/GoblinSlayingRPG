extends Node2D
## Dialogue box with typewriter text, speaker tags and yes/no choices. Use with await.

var active := false
var speaker := ""
var lines: Array = []
var shown := 0
var total := 0
var choice_opts: Array = []
var choice_idx := 0
var choosing := false
var _re := RegEx.new()

const BOX := Rect2(8, 190, 464, 72)
const TEXT_W := 440.0


func _ready() -> void:
	_re.compile("^([A-Z][A-Z .'\\-]{1,24}): (.*)$")
	visible = false


func _process(_d: float) -> void:
	if active:
		queue_redraw()


func _prepare(page: String, who: String) -> Array:
	## Returns chunks of up to 4 wrapped lines and sets the speaker.
	var m := _re.search(page)
	speaker = who
	var body := page
	if m:
		speaker = m.get_string(1).capitalize()
		body = m.get_string(2)
	body = body.replace("{hero}", DB.d.characters.hero.name)
	var all := Art.wrap(body, TEXT_W)
	var chunks := []
	for i in range(0, all.size(), 4):
		chunks.append(all.slice(i, i + 4))
	return chunks


func _set_lines(l: Array) -> void:
	lines = l
	total = 0
	for x in lines:
		total += x.length()
	shown = 0


func say(pages: Array, who: String = "") -> void:
	if pages.is_empty():
		return
	active = true
	visible = true
	Inp.block(1)
	var chunks := []
	for page in pages:
		for ch in _prepare(str(page), who):
			chunks.append([speaker, ch])
	for chunk in chunks:
		speaker = chunk[0]
		_set_lines(chunk[1])
		var speed: float = [1.2, 2.2, 6.0][int(GS.settings.get("text_speed", 1))]
		var acc := 0.0
		while shown < total:
			await get_tree().process_frame
			acc += speed
			var add := int(acc)
			acc -= add
			var before := shown
			shown = min(total, shown + max(1, add))
			if floori(shown / 3.0) != floori(before / 3.0):
				Audio.sfx("text", -14.0, 1.0, 0.1)
			if Inp.ok() or Inp.back():
				shown = total
		while true:
			await get_tree().process_frame
			if Inp.ok() or Inp.back():
				Audio.sfx("cursor", -6.0)
				break
	active = false
	visible = false
	Inp.block(2)


func ask(question: String, opts: Array = ["Yes", "No"], who: String = "") -> int:
	active = true
	visible = true
	var ch := _prepare(question, who)
	_set_lines(ch[0] if ch.size() > 0 else [])
	shown = total
	choice_opts = opts
	choice_idx = 0
	choosing = true
	Inp.block(2)
	var result := -1
	while result < 0:
		await get_tree().process_frame
		var v := Inp.vert()
		if v != 0:
			choice_idx = wrapi(choice_idx + v, 0, opts.size())
			Audio.sfx("cursor", -6.0)
		if Inp.ok():
			result = choice_idx
			Audio.sfx("confirm")
		elif Inp.back():
			result = opts.size() - 1
			Audio.sfx("cancel")
	choosing = false
	active = false
	visible = false
	Inp.block(2)
	return result


func _draw() -> void:
	if not active:
		return
	Art.window(self, BOX)
	if speaker != "":
		var w := Art.width(speaker) + 14
		Art.window(self, Rect2(BOX.position.x + 6, BOX.position.y - 16, w, 19), "dark")
		Art.text(self, Vector2(BOX.position.x + 13, BOX.position.y - 14), speaker, Art.YELLOW)
	var left := shown
	for i in lines.size():
		var l: String = lines[i]
		var part := l.substr(0, max(0, min(l.length(), left)))
		left -= l.length()
		Art.text(self, Vector2(BOX.position.x + 12, BOX.position.y + 7 + i * Art.LINE), part)
	if shown >= total and not choosing:
		if fmod(Time.get_ticks_msec() / 1000.0, 0.8) < 0.5:
			draw_rect(Rect2(BOX.end.x - 16, BOX.end.y - 10, 6, 3), Color.WHITE)
			draw_rect(Rect2(BOX.end.x - 15, BOX.end.y - 7, 4, 1), Color.WHITE)
	if choosing:
		var h := choice_opts.size() * Art.LINE + 12
		var r := Rect2(BOX.end.x - 100, BOX.position.y - h - 2, 100, h)
		Art.window(self, r)
		for i in choice_opts.size():
			Art.text(self, r.position + Vector2(24, 6 + i * Art.LINE), choice_opts[i])
		Art.cursor(self, r.position + Vector2(24, 6 + choice_idx * Art.LINE))
