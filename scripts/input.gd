extends Node
## Input actions (keyboard + gamepad) and menu-friendly helpers with key repeat.

const DIRS := ["up", "down", "left", "right"]
var _held := {}
var _repeat := {}
var block_frames := 0
var _latch := {}   # action -> frames left; a press is held until something consumes it


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_add("up", [KEY_UP, KEY_W], [JOY_BUTTON_DPAD_UP], [JOY_AXIS_LEFT_Y, -1.0])
	_add("down", [KEY_DOWN, KEY_S], [JOY_BUTTON_DPAD_DOWN], [JOY_AXIS_LEFT_Y, 1.0])
	_add("left", [KEY_LEFT, KEY_A], [JOY_BUTTON_DPAD_LEFT], [JOY_AXIS_LEFT_X, -1.0])
	_add("right", [KEY_RIGHT, KEY_D], [JOY_BUTTON_DPAD_RIGHT], [JOY_AXIS_LEFT_X, 1.0])
	_add("ok", [KEY_Z, KEY_SPACE, KEY_ENTER, KEY_KP_ENTER], [JOY_BUTTON_A], [])
	_add("back", [KEY_X, KEY_ESCAPE, KEY_BACKSPACE], [JOY_BUTTON_B, JOY_BUTTON_START], [])
	_add("run", [KEY_SHIFT, KEY_C], [JOY_BUTTON_X, JOY_BUTTON_RIGHT_STICK], [])
	_add("tab", [KEY_TAB, KEY_Q, KEY_E], [JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER], [])
	_add("map", [KEY_M], [JOY_BUTTON_BACK, JOY_BUTTON_Y], [])


func _add(action: String, keys: Array, buttons: Array, axis: Array) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action, 0.4)
	for k in keys:
		var e := InputEventKey.new()
		e.physical_keycode = k
		InputMap.action_add_event(action, e)
	for b in buttons:
		var e := InputEventJoypadButton.new()
		e.button_index = b
		InputMap.action_add_event(action, e)
	if axis.size() == 2:
		var e := InputEventJoypadMotion.new()
		e.axis = axis[0]
		e.axis_value = axis[1]
		InputMap.action_add_event(action, e)


func _process(delta: float) -> void:
	if block_frames > 0:
		block_frames -= 1
	for a in ["ok", "back", "tab", "map", "up", "down", "left", "right"]:
		if Input.is_action_just_pressed(a):
			_latch[a] = 4
		elif _latch.get(a, 0) > 0:
			_latch[a] -= 1
	for d in DIRS:
		if Input.is_action_pressed(d):
			_held[d] = _held.get(d, 0.0) + delta
		else:
			_held[d] = 0.0
			_repeat[d] = 0.0


func _take(a: String) -> bool:
	if block_frames > 0:
		return false
	if _latch.get(a, 0) > 0:
		_latch[a] = 0
		return true
	return false


func ok() -> bool:
	return _take("ok")


func back() -> bool:
	return _take("back")


func tab() -> bool:
	return _take("tab")


func map_key() -> bool:
	return _take("map")


func held(d: String) -> bool:
	return Input.is_action_pressed(d)


## True on first press and then repeatedly while held (for menu cursors).
func pressed(d: String) -> bool:
	if block_frames > 0:
		return false
	if _take(d):
		_repeat[d] = 0.0
		return true
	var h: float = _held.get(d, 0.0)
	if h > 0.32:
		var r: float = _repeat.get(d, 0.0) + get_process_delta_time()
		if r >= 0.07:
			_repeat[d] = 0.0
			return true
		_repeat[d] = r
	return false


func vert() -> int:
	return (1 if pressed("down") else 0) - (1 if pressed("up") else 0)


func horiz() -> int:
	return (1 if pressed("right") else 0) - (1 if pressed("left") else 0)


func block(frames: int = 2) -> void:
	block_frames = frames
	_latch.clear()
