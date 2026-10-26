class_name DialogBox
extends Control
## Visual-novel style dialogue: the speaker stands at the left edge, a name plate, typewriter text
## and choices. Lines with the "think" expression are shown as thoughts.

const CHAR_COLORS := {"alina": Color("2f74d6"), "boris": Color("8a5a2a"), "marina": Color("c0407a"),
	"oleg": Color("3a8a4a"), "viktor": Color("5a4ab0"), "zina": Color("c87412")}

var hud
var _lines: Array = []
var _idx := 0
var _shown := 0.0
var _full := ""
var _on_done: Callable
var _portrait: TextureRect
var _name: Label
var _text: Label
var _more: TextureRect
var _choices: HBoxContainer
var _box: PanelContainer
var _plate: PanelContainer
var _think: Label
var _t := 0.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var dim := ColorRect.new()
	dim.color = Color(0.04, 0.05, 0.08, 0.32)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)
	_portrait = TextureRect.new()
	_portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_portrait.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_portrait)
	_box = PanelContainer.new()
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_box)
	var sb: StyleBoxFlat = hud._sb("panel", 0, 12)
	sb.content_margin_top = 16
	_box.add_theme_stylebox_override("panel", sb)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	_box.add_child(v)
	_think = hud.text("", v, 11, Color("7a8090"))
	_text = hud.text("", v, 14, Color("2b2f3a"), 300)
	_text.custom_minimum_size = Vector2(300, 44)
	_choices = HBoxContainer.new()
	_choices.add_theme_constant_override("separation", 6)
	v.add_child(_choices)
	# the name plate sits on the top edge of the box
	_plate = PanelContainer.new()
	var psb := StyleBoxFlat.new()
	psb.bg_color = Color("2f74d6")
	psb.set_corner_radius_all(9)
	psb.content_margin_left = 10
	psb.content_margin_right = 10
	psb.content_margin_top = 2
	psb.content_margin_bottom = 3
	_plate.add_theme_stylebox_override("panel", psb)
	_plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_plate)
	_name = hud.title("", _plate, 13, Color.WHITE)
	_more = hud.icon_rect("upgrade", self, 12)
	_more.rotation = PI
	visible = false


func play(lines: Array, on_done := Callable()) -> void:
	if visible and not _lines.is_empty():
		_lines.append_array(lines)
		return
	_lines = lines.duplicate()
	_idx = 0
	_on_done = on_done
	visible = true
	_layout()
	_show_line()


func _layout() -> void:
	var rs: Vector2 = hud.root.size
	# a half-figure standing on the bottom edge of the screen
	var ph := minf(rs.y * 0.82, 320.0)
	_portrait.size = Vector2(ph, ph)
	_portrait.position = Vector2(-ph * 0.06, rs.y - ph)
	var left := ph * 0.74
	var bw := minf(rs.x - left - 16, 500.0)
	_text.custom_minimum_size = Vector2(bw - 28, 48)
	_box.position = Vector2(left, rs.y - 10)
	_box.size = Vector2(bw, 0)


func _show_line() -> void:
	var line: Dictionary = _lines[_idx]
	var expr: String = line.get("expr", "smile")
	_portrait.texture = Assets.portrait(line.who, expr)
	_name.text = Events.char_name(line.who)
	_plate.get_theme_stylebox("panel").bg_color = CHAR_COLORS.get(line.who, Color("2f74d6"))
	_think.text = Loc.t("thinking") if expr == "think" else ""
	_think.visible = expr == "think"
	_text.add_theme_color_override("font_color", Color("4a5060") if expr == "think" else Color("2b2f3a"))
	_full = Events.fmt(line.text)
	_shown = 0.0
	_text.text = ""
	for c in _choices.get_children():
		c.queue_free()
	_choices.visible = false
	_portrait.scale = Vector2(0.96, 0.96)
	_portrait.pivot_offset = _portrait.size / 2
	create_tween().tween_property(_portrait, "scale", Vector2.ONE, 0.15)
	Game.sfx("tap", -8.0, 1.3)


func _process(delta: float) -> void:
	if not visible:
		return
	_t += delta
	if _shown < _full.length():
		_shown = minf(_full.length(), _shown + delta * 45.0)
		_text.text = _full.substr(0, int(_shown))
		if _shown >= _full.length():
			_finish_line()
	_box.reset_size()
	_box.position.y = hud.root.size.y - _box.size.y - 10
	_plate.reset_size()
	_plate.position = _box.position + Vector2(14, -_plate.size.y * 0.55)
	_more.visible = _shown >= _full.length() and not _choices.visible
	_more.position = _box.position + _box.size - Vector2(20, 16 + sin(_t * 6.0) * 2.0)


func _finish_line() -> void:
	_text.text = _full
	var line: Dictionary = _lines[_idx]
	var choices: Array = line.get("choices", [])
	if choices.is_empty():
		return
	_choices.visible = true
	for i in choices.size():
		var ch: Array = choices[i]
		var act: String = ch[1]
		var b: Button = hud.button(Loc.pick(ch[0]), "", "green" if i == 0 else "blue", func():
			Events.choose(act)
			_next(true))
		b.add_theme_font_size_override("font_size", 11)
		_choices.add_child(b)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		accept_event()
		if _shown < _full.length():
			_shown = _full.length()
			_finish_line()
		elif not _choices.visible:
			_next(false)


func _next(_chosen: bool) -> void:
	_idx += 1
	if _idx >= _lines.size():
		visible = false
		_lines.clear()
		if _on_done.is_valid():
			var cb := _on_done
			_on_done = Callable()
			cb.call()
		return
	_show_line()


func skip() -> void:
	if _choices.visible:
		return
	_next(false)
