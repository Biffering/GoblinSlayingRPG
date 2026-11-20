extends Node
## Music (crossfading, looping) and sound effects. Missing files are skipped silently.

var _sfx := {}
var _players: Array = []
var _next := 0
var _last := {}
var _a: AudioStreamPlayer
var _b: AudioStreamPlayer
var _active: AudioStreamPlayer
var current := ""
var _tween: Tween
var _duck := 0.0
var _amb_a: AudioStreamPlayer
var _amb_b: AudioStreamPlayer
var _amb_cur := ""
var _amb_tween: Tween

const MUSIC_DB := -8.0
const SFX_DB := -4.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in 16:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)
	_a = AudioStreamPlayer.new()
	_b = AudioStreamPlayer.new()
	add_child(_a)
	add_child(_b)
	_active = _a
	_amb_a = AudioStreamPlayer.new()
	_amb_b = AudioStreamPlayer.new()
	add_child(_amb_a)
	add_child(_amb_b)


func _lin(v: float) -> float:
	return linear_to_db(max(0.0001, v))


func sfx(sfx_name: String, vol := 0.0, pitch := 1.0, var_pitch := 0.04) -> void:
	if GS.settings.sfx <= 0.01:
		return
	if not _sfx.has(sfx_name):
		var path := "res://assets/sounds/%s.wav" % sfx_name
		_sfx[sfx_name] = load(path) if ResourceLoader.exists(path) else null
	if _sfx[sfx_name] == null:
		return
	var now := Time.get_ticks_msec()
	if now - int(_last.get(sfx_name, -1000)) < 35:
		return
	_last[sfx_name] = now
	var p: AudioStreamPlayer = _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _sfx[sfx_name]
	p.volume_db = SFX_DB + vol + _lin(GS.settings.sfx)
	p.pitch_scale = pitch * randf_range(1.0 - var_pitch, 1.0 + var_pitch)
	p.play()


func music(track: String, fade := 0.8) -> void:
	if track == current and _active.playing:
		return
	current = track
	var path := "res://assets/music/%s.ogg" % track
	if not ResourceLoader.exists(path):
		stop_music(fade)
		current = track
		return
	var st = load(path)
	if st is AudioStreamOggVorbis:
		st.loop = true
	var old := _active
	var nxt := _b if _active == _a else _a
	_active = nxt
	nxt.stream = st
	nxt.volume_db = -60.0
	nxt.play()
	_new_tween()
	_tween.tween_property(nxt, "volume_db", _target_db(), fade)
	if old.playing:
		_tween.tween_property(old, "volume_db", -60.0, fade)
		_tween.chain().tween_callback(old.stop)


## Weather ambience (birds, breeze, rain, storm...). Crossfades between loops; "" fades it out.
func ambient(amb_name: String, vol_db := -4.0) -> void:
	var target := vol_db + SFX_DB + _lin(GS.settings.sfx)
	if _amb_tween and _amb_tween.is_valid():
		_amb_tween.kill()
	_amb_tween = create_tween().set_parallel(true)
	if amb_name == _amb_cur and amb_name != "":
		var cur := _amb_a if _amb_a.playing else _amb_b
		_amb_tween.tween_property(cur, "volume_db", target, 1.0)
		return
	_amb_cur = amb_name
	for p in [_amb_a, _amb_b]:
		if p.playing:
			_amb_tween.tween_property(p, "volume_db", -60.0, 2.0)
	_amb_tween.chain().tween_callback(func():
		for p in [_amb_a, _amb_b]:
			if p.volume_db <= -59.0:
				p.stop())
	if amb_name == "":
		return
	var path := "res://assets/sounds/%s.ogg" % amb_name
	if not ResourceLoader.exists(path):
		return
	var st = load(path)
	if st is AudioStreamOggVorbis:
		st.loop = true
	var nxt := _amb_b if _amb_a.playing else _amb_a
	nxt.stream = st
	nxt.volume_db = -60.0
	nxt.play()
	_amb_tween.tween_property(nxt, "volume_db", target, 2.0)


func play_once(track: String) -> void:
	## Jingles (victory, level up fanfare) that don't loop.
	var path := "res://assets/music/%s.ogg" % track
	if not ResourceLoader.exists(path):
		return
	stop_music(0.2)
	current = track
	var st = load(path)
	if st is AudioStreamOggVorbis:
		st.loop = false
	var nxt := _b if _active == _a else _a
	_active = nxt
	nxt.stream = st
	nxt.volume_db = _target_db()
	nxt.play()


func stop_music(fade := 0.6) -> void:
	current = ""
	_new_tween()
	for p in [_a, _b]:
		if p.playing:
			_tween.tween_property(p, "volume_db", -60.0, fade)
	_tween.chain().tween_callback(func():
		if current == "":
			_a.stop()
			_b.stop())


func duck(db: float) -> void:
	_duck = db
	if _active.playing:
		_new_tween()
		_tween.tween_property(_active, "volume_db", _target_db(), 0.25)


func refresh_volume() -> void:
	if _active.playing:
		_active.volume_db = _target_db()


func _target_db() -> float:
	return MUSIC_DB + _duck + _lin(GS.settings.music)


func _new_tween() -> void:
	if _tween and _tween.is_valid():
		_tween.kill()
	_tween = create_tween().set_parallel(true)
