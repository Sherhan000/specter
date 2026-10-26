class_name Intro
extends CanvasLayer
## First launch: an opening animation over the valley, then the player's profile (name, age,
## gender, stored only on this device), then the privacy policy to read and accept.

var hud
var root: Control
var bg: ColorRect
var stage := 0
var _name_edit: LineEdit
var _age := 16
var _age_label: Label
var _gender := ""
var _g_buttons := {}
var _next_btn: Button
var _accept: CheckBox
var _accept_btn: Button
var _kid_note: Label
var _tap_label: Label
var _t := 0.0


func _ready() -> void:
	layer = 30
	root = Control.new()
	root.theme = hud.ui_theme
	root.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	root.scale = Vector2(hud.S, hud.S)
	root.size = hud.root.size
	add_child(root)
	bg = ColorRect.new()
	bg.color = Color(0.08, 0.1, 0.2, 1.0)
	bg.size = root.size
	root.add_child(bg)
	_opening()


# ---------------------------------------------------------------- opening animation
func _opening() -> void:
	var city: Node = hud.city
	city.camera.zoom = Vector2(0.45, 0.45)
	city.camera.position = Iso.center(Vector2i(Data.CENTER - 14, Data.CENTER - 14))
	var tw := create_tween()
	tw.tween_property(bg, "color:a", 0.0, 1.6)
	var cam := city.create_tween().set_parallel()
	cam.tween_property(city.camera, "position", Iso.center(Vector2i(Data.CENTER + 2, Data.CENTER)), 6.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	cam.tween_property(city.camera, "zoom", Vector2(1.0, 1.0), 6.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	var title := Loc.t("title").to_upper()
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 1)
	root.add_child(row)
	var letters: Array[Label] = []
	for ch in title:
		var l: Label = hud._label(ch, row, 24, 8)
		l.add_theme_color_override("font_color", Color("ffe080"))
		l.add_theme_color_override("font_outline_color", Color("2a1a30"))
		l.modulate.a = 0.0
		letters.append(l)
	row.reset_size()
	row.position = Vector2((root.size.x - row.get_combined_minimum_size().x) / 2, root.size.y * 0.24)
	for i in letters.size():
		var l := letters[i]
		var t2 := l.create_tween()
		t2.tween_interval(1.0 + i * 0.12)
		t2.tween_callback(func(): Game.sfx("coin", -12.0, 0.8 + i * 0.05))
		t2.tween_property(l, "modulate:a", 1.0, 0.01)
		t2.tween_property(l, "position:y", -14.0, 0.0)
		t2.tween_property(l, "position:y", 0.0, 0.45).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	var sub: Label = hud.text(Loc.t("intro_sub"), root, 15, Color("ffffff"))
	sub.add_theme_color_override("font_outline_color", Color("2a1a30"))
	sub.add_theme_constant_override("outline_size", 6)
	sub.reset_size()
	sub.position = Vector2((root.size.x - sub.size.x) / 2, root.size.y * 0.24 + 40)
	sub.modulate.a = 0.0
	var t3 := sub.create_tween()
	t3.tween_interval(1.0 + letters.size() * 0.12 + 0.4)
	t3.tween_property(sub, "modulate:a", 1.0, 0.8)
	_tap_label = hud.text(Loc.t("intro_tap"), root, 13, Color("fff4b0"))
	_tap_label.add_theme_color_override("font_outline_color", Color("2a1a30"))
	_tap_label.add_theme_constant_override("outline_size", 6)
	_tap_label.reset_size()
	_tap_label.position = Vector2((root.size.x - _tap_label.size.x) / 2, root.size.y * 0.78)
	_tap_label.modulate.a = 0.0
	var catcher := Control.new()
	catcher.size = root.size
	catcher.mouse_filter = Control.MOUSE_FILTER_STOP
	root.add_child(catcher)
	catcher.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and stage == 0 and _t > 2.0:
			stage = 1
			Game.sfx("done")
			var fade := create_tween()
			fade.tween_property(row, "modulate:a", 0.0, 0.4)
			fade.parallel().tween_property(sub, "modulate:a", 0.0, 0.4)
			fade.parallel().tween_property(_tap_label, "modulate:a", 0.0, 0.3)
			fade.tween_callback(func():
				row.queue_free()
				sub.queue_free()
				catcher.queue_free()
				_profile()))


func _process(delta: float) -> void:
	_t += delta
	if stage == 0 and _t > 3.0 and is_instance_valid(_tap_label):
		_tap_label.modulate.a = 0.6 + 0.4 * sin(_t * 4.0)


# ---------------------------------------------------------------- profile
func _panel(width: float) -> VBoxContainer:
	var dim := ColorRect.new()
	dim.color = Color(0.05, 0.04, 0.1, 0.5)
	dim.size = root.size
	root.add_child(dim)
	var center := CenterContainer.new()
	center.size = root.size
	root.add_child(center)
	var p := PanelContainer.new()
	center.add_child(p)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 7)
	v.custom_minimum_size = Vector2(width, 0)
	p.add_child(v)
	dim.set_meta("center", center)
	return v


func _clear() -> void:
	for c in root.get_children():
		if c != bg:
			c.queue_free()


func _profile() -> void:
	_clear()
	var v := _panel(minf(360.0, root.size.x - 40))
	var t: Label = hud.title(Loc.t("pf_title"), v, 16)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud.text(Loc.t("pf_intro"), v, 11, Color("6a5a4a"), minf(340.0, root.size.x - 60))
	hud.text(Loc.t("pf_name"), v, 12)
	_name_edit = LineEdit.new()
	_name_edit.max_length = 16
	_name_edit.placeholder_text = Loc.t("pf_name_ph")
	_name_edit.custom_minimum_size = Vector2(0, 30)
	_name_edit.text_changed.connect(func(_s): _validate())
	v.add_child(_name_edit)
	var ah := HBoxContainer.new()
	ah.add_theme_constant_override("separation", 6)
	v.add_child(ah)
	var al: Label = hud.text(Loc.t("pf_age"), ah, 12)
	al.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ah.add_child(hud.button("-", "", "red", func(): _set_age(_age - 1), Vector2(30, 26)))
	_age_label = hud.title(str(_age), ah, 15, Color("3a2a1e"))
	_age_label.custom_minimum_size = Vector2(32, 0)
	_age_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ah.add_child(hud.button("+", "", "green", func(): _set_age(_age + 1), Vector2(30, 26)))
	ah.add_child(hud.button("+10", "", "green", func(): _set_age(_age + 10), Vector2(40, 26)))
	_kid_note = hud.text(Loc.t("pf_kid"), v, 11, Color("b83a2a"), minf(340.0, root.size.x - 60))
	_kid_note.visible = false
	hud.text(Loc.t("pf_gender"), v, 12)
	var gh := HBoxContainer.new()
	gh.add_theme_constant_override("separation", 6)
	v.add_child(gh)
	for g in ["m", "f"]:
		var b: Button = hud.button(Loc.t("pf_" + g), "", "blue", func():
			_gender = g
			_validate())
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		gh.add_child(b)
		_g_buttons[g] = b
	_next_btn = hud.button(Loc.t("pf_next"), "ok", "green", func(): _privacy())
	v.add_child(_next_btn)
	_validate()


func _set_age(a: int) -> void:
	_age = clampi(a, 5, 99)
	_age_label.text = str(_age)
	_kid_note.visible = _age < 13


func _validate() -> void:
	for g in _g_buttons:
		_g_buttons[g].modulate = Color.WHITE if g == _gender else Color(0.6, 0.6, 0.72)
	_next_btn.disabled = _name_edit.text.strip_edges() == "" or _gender == ""


# ---------------------------------------------------------------- privacy policy
func _privacy() -> void:
	DisplayServer.virtual_keyboard_hide()
	var name := _name_edit.text.strip_edges()
	_clear()
	var w := minf(460.0, root.size.x - 40)
	var v := _panel(w)
	var t: Label = hud.title(Loc.t("privacy"), v, 16)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var scroll := ScrollContainer.new()
	hud.extra_scrolls.append(scroll)
	scroll.custom_minimum_size = Vector2(w, root.size.y - 150)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(scroll)
	hud.text(Loc.t("privacy_full"), scroll, 13, Color("3a2a1e"), w - 16)
	_accept = CheckBox.new()
	_accept.text = Loc.t("pp_accept")
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
		_accept.add_theme_stylebox_override(st, StyleBoxEmpty.new())
	_accept.add_theme_color_override("font_hover_pressed_color", Color("3a2a1e"))
	_accept.add_theme_font_override("font", hud.body_font)
	_accept.add_theme_font_size_override("font_size", 12)
	_accept.add_theme_color_override("font_color", Color("3a2a1e"))
	_accept.add_theme_color_override("font_pressed_color", Color("3a2a1e"))
	_accept.add_theme_color_override("font_hover_color", Color("3a2a1e"))
	_accept.focus_mode = Control.FOCUS_NONE
	v.add_child(_accept)
	_accept_btn = hud.button(Loc.t("pp_continue"), "ok", "green", func():
		Game.profile = {"name": name, "age": _age, "gender": _gender, "privacy": true, "intro": true}
		Game.tutorial = 0
		Game.save_game()
		Game.sfx("levelup")
		var fade := create_tween()
		fade.tween_property(root, "modulate:a", 0.0, 0.5)
		fade.tween_callback(func():
			hud.safe.visible = true
			queue_free()
			hud.tutorial.start()))
	_accept_btn.disabled = true
	_accept.toggled.connect(func(on): _accept_btn.disabled = not on)
	v.add_child(_accept_btn)
