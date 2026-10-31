extends CanvasLayer
## Touch-friendly interface laid out in a 360 px tall virtual space and scaled to the screen;
## fonts are distance fields and icons vector renders, so they stay sharp at any scale.
## Modal windows live in panels.gd, dialogues in dialog_box.gd.

var city: Node
var font: FontFile           ## Inter Bold: numbers, titles
var body_font: FontFile      ## Inter Regular: running text
var bold_font: Font          ## Inter SemiBold: buttons
var ui_theme: Theme
var S := 2.0
## Interface size steps the player picks in the settings (multiplies the automatic scale).
const UI_SCALES := [0.8, 0.9, 1.0, 1.1, 1.2, 1.35, 1.5]
const MIN_UI_H := 240.0               ## bigger steps are skipped once fewer units than this fit on the screen
const MIN_UI_W := 540.0

var root: Control
var safe: Control
var level_label: Label
var rank_label: Label
var xp_bar: ColorRect
var pill_labels := {}
var pills := {}
var happy_icon: TextureRect
var date_label: Label
var clock_label: Label
var weather_icon: TextureRect
var main_buttons: Control
var badges := {}
var side_buttons: VFlowContainer
var mode_bar: PanelContainer
var mode_title: Label
var mode_sub: Label
var mode_hint: Label
var mode_price: HBoxContainer
var mode_ok: TextureButton
var mode_rot: TextureButton
var mode_land: TextureButton
var _ok_enabled := false
var road_types: HFlowContainer
var tool_tabs: HBoxContainer
var _types_tool := ""
var lamp_types: HBoxContainer
var build_menu: PanelContainer
var build_cards: HBoxContainer
var build_tabs := {}
var build_cat := "home"
var info_panel: PanelContainer
var info_uid := 0
var info_title: Label
var info_stars: HBoxContainer
var info_line: HBoxContainer
var info_note: Label
var info_bar: ColorRect
var info_bar_bg: ColorRect
var info_actions: HBoxContainer
var _info_key := ""
var modal: Control
var modal_panel: PanelContainer
var modal_box: VBoxContainer
var modal_scroll: ScrollContainer
var toast_label: Label
var toast_box: PanelContainer
var panels: Panels
var dialog: DialogBox
var tutorial: Tutorial
var _toast_tw: Tween
var holiday_btn: TextureButton
var _gated: Array[Control] = []    ## main buttons the tutorial may switch off
var _bar_t := 0.0
var _drag_sc: ScrollContainer
var _drag_dist := 0.0
var drag_block := false            ## a finger drag scrolled a list: the button under it must not fire
var build_scroll: ScrollContainer
var extra_scrolls: Array = []


func _ready() -> void:
	layer = 10
	_build_theme()
	root = Control.new()
	root.theme = ui_theme
	root.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	safe = Control.new()
	safe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(safe)
	get_viewport().size_changed.connect(_fit)
	_fit()

	_build_top()
	_build_side()
	_build_bottom()
	_build_mode_bar()
	_build_build_menu()
	_build_info()
	_build_modal()
	toast_box = PanelContainer.new()
	toast_box.add_theme_stylebox_override("panel", _sb("panel_dark", 0, 7))
	toast_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	toast_box.modulate.a = 0.0
	toast_box.z_index = 20
	root.add_child(toast_box)
	toast_label = text("", toast_box, 13, Color.WHITE)
	toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

	panels = Panels.new(self)
	dialog = DialogBox.new()
	dialog.hud = self
	root.add_child(dialog)
	tutorial = Tutorial.new()
	tutorial.hud = self
	root.add_child(tutorial)

	Game.changed.connect(_update)
	Game.toast.connect(toast)
	Game.level_up.connect(_on_level_up)
	Game.game_over.connect(func(): panels.game_over())
	Events.dialog.connect(func(lines):
		_close_panels()
		close_modal()
		dialog.play(lines))
	Events.inbox_changed.connect(_update_badges)
	Loc.changed.connect(_rebuild_texts)
	_update()
	if not Game.profile.intro:
		safe.visible = false
		var intro := Intro.new()
		intro.hud = self
		add_child(intro)
		Game.settings["news"] = Data.NEWS_VERSION   # a new player has nothing to catch up on
	elif Game.lost:
		panels.game_over.call_deferred()
	elif Game.visiting != "":
		_show_visit_bar()
	else:
		_show_splash()
		if Game.offline_note:
			Game.offline_note = false
			toast(Loc.t("offline"))
		if Game.tutorial < 99:
			tutorial.start.call_deferred()
		else:
			var news_due: bool = Game.settings.get("news", "") != Data.NEWS_VERSION
			if Game.daily_roll():
				get_tree().create_timer(2.6).timeout.connect(func(): panels.daily(panels.whats_new if news_due else Callable()))
			elif news_due:
				get_tree().create_timer(2.6).timeout.connect(panels.whats_new)


func _fit() -> void:
	var vp := get_viewport().get_visible_rect().size
	S = _base_scale() * ui_scale()
	root.scale = Vector2(S, S)
	root.size = vp / S
	var win := Vector2(DisplayServer.window_get_size())
	var sa := Rect2(DisplayServer.get_display_safe_area())
	var k := vp / win if win.x > 0 else Vector2.ONE
	var left := maxf(0.0, sa.position.x) * k.x / S
	var top := maxf(0.0, sa.position.y) * k.y / S
	var right := maxf(0.0, win.x - sa.end.x) * k.x / S if sa.size.x > 0 else 0.0
	var bottom := maxf(0.0, win.y - sa.end.y) * k.y / S if sa.size.y > 0 else 0.0
	if OS.get_name() not in ["Android", "iOS"]:
		left = 0.0
		top = 0.0
		right = 0.0
		bottom = 0.0
	safe.position = Vector2(left + 6, top + 5)
	safe.size = root.size - Vector2(left + right + 12, top + bottom + 10)
	if modal:
		modal.size = root.size
	_place_side()


func _base_scale() -> float:
	return maxf(1.0, roundf(get_viewport().get_visible_rect().size.y / 360.0 * 2.0) / 2.0)


## The biggest step that still leaves room for the whole interface on this screen.
func max_ui_scale() -> float:
	var vp := get_viewport().get_visible_rect().size
	var best := 1.0
	for k in UI_SCALES:
		if k > best and _base_scale() * k <= minf(vp.y / MIN_UI_H, vp.x / MIN_UI_W) + 0.001:
			best = k
	return best


## The player's interface size (Game.settings.ui_scale), one of UI_SCALES.
func ui_scale() -> float:
	return clampf(float(Game.settings.get("ui_scale", 1.0)), UI_SCALES[0], max_ui_scale())


## Steps the interface size up or down and lays everything out again.
func step_ui_scale(dir: int) -> void:
	var i := 0
	for k in UI_SCALES.size():
		if absf(UI_SCALES[k] - ui_scale()) < absf(UI_SCALES[i] - ui_scale()):
			i = k
	i = clampi(i + dir, 0, UI_SCALES.find(max_ui_scale()))
	Game.set_setting("ui_scale", UI_SCALES[i])
	_fit()


# ====================================================================== theme + widgets
const INK := Color("2b2f3a")          ## body text on light panels
const PAPER := Color("fbf8f2")
const LINE := Color("ddd5c6")
const BTN := {"blue": ["3d86e8", "2a66c0"], "green": ["2fae62", "1f8a4c"], "red": ["e2544a", "b83a32"],
	"orange": ["f39a22", "c87412"], "purple": ["8a5ce0", "6a40b8"], "grey": ["8a92a2", "666e7e"]}


func _font(path: String) -> FontFile:
	var f: FontFile = load(path)
	f.multichannel_signed_distance_field = true
	f.msdf_pixel_range = 14
	f.generate_mipmaps = true
	return f


func _build_theme() -> void:
	font = _font("res://assets/fonts/Inter-Bold.otf")
	body_font = _font("res://assets/fonts/Inter-Regular.otf")
	bold_font = _font("res://assets/fonts/Inter-SemiBold.otf")
	ui_theme = Theme.new()
	ui_theme.default_font = font
	ui_theme.default_font_size = 11
	ui_theme.set_color("font_color", "Label", Color("ffffff"))
	ui_theme.set_color("font_outline_color", "Label", Color(0.08, 0.09, 0.12, 0.85))
	ui_theme.set_constant("outline_size", "Label", 0)
	ui_theme.set_constant("line_spacing", "Label", 2)
	ui_theme.set_stylebox("panel", "PanelContainer", _sb("panel", 7, 10))
	for st in ["normal", "hover", "pressed", "focus", "disabled"]:
		ui_theme.set_stylebox(st, "Button", _btn_sb("blue", st))
	ui_theme.set_color("font_color", "Button", Color("ffffff"))
	ui_theme.set_color("font_hover_color", "Button", Color("ffffff"))
	ui_theme.set_color("font_pressed_color", "Button", Color("eef2ff"))
	ui_theme.set_color("font_focus_color", "Button", Color("ffffff"))
	ui_theme.set_color("font_disabled_color", "Button", Color("eceef2"))
	ui_theme.set_constant("outline_size", "Button", 0)
	ui_theme.set_constant("h_separation", "Button", 5)
	ui_theme.set_constant("icon_max_width", "Button", 16)
	ui_theme.set_font("font", "LineEdit", body_font)
	ui_theme.set_font_size("font_size", "LineEdit", 13)
	ui_theme.set_color("font_color", "LineEdit", INK)
	ui_theme.set_stylebox("normal", "LineEdit", _sb("card", 5, 6))
	ui_theme.set_stylebox("focus", "LineEdit", _sb("card_sel", 5, 6))
	ui_theme.set_font("font", "TextEdit", body_font)
	ui_theme.set_font_size("font_size", "TextEdit", 10)
	ui_theme.set_color("font_color", "TextEdit", INK)
	ui_theme.set_stylebox("normal", "TextEdit", _sb("card", 5, 6))
	ui_theme.set_stylebox("focus", "TextEdit", _sb("card_sel", 5, 6))
	var grab := StyleBoxFlat.new()
	grab.bg_color = Color("b8b0a0")
	grab.set_corner_radius_all(3)
	var track := StyleBoxFlat.new()
	track.bg_color = Color(0.4, 0.38, 0.34, 0.12)
	track.set_corner_radius_all(3)
	track.content_margin_left = 4
	track.content_margin_right = 4
	ui_theme.set_stylebox("grabber", "VScrollBar", grab)
	ui_theme.set_stylebox("grabber_highlight", "VScrollBar", grab)
	ui_theme.set_stylebox("grabber_pressed", "VScrollBar", grab)
	ui_theme.set_stylebox("scroll", "VScrollBar", track)


## Rounded panel styles: "panel" (light window), "panel_dark", "pill" (dark chip on the map),
## "card" and "card_sel" (light tiles inside windows).
func _sb(kind: String, _margin: int, content: int) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.anti_aliasing = true
	sb.set_content_margin_all(content)
	match kind:
		"panel":
			sb.bg_color = PAPER
			sb.set_corner_radius_all(12)
			sb.set_border_width_all(1)
			sb.border_color = LINE
			sb.shadow_color = Color(0, 0, 0, 0.28)
			sb.shadow_size = 8
			sb.shadow_offset = Vector2(0, 3)
		"panel_dark":
			sb.bg_color = Color(0.11, 0.12, 0.16, 0.92)
			sb.set_corner_radius_all(12)
			sb.shadow_color = Color(0, 0, 0, 0.3)
			sb.shadow_size = 6
		"pill":
			sb.bg_color = Color(0.1, 0.11, 0.15, 0.78)
			sb.set_corner_radius_all(11)
			sb.set_border_width_all(1)
			sb.border_color = Color(1, 1, 1, 0.12)
			sb.content_margin_left = content + 3
			sb.content_margin_right = content + 4
		"card", "card_sel":
			sb.bg_color = Color("ffffff") if kind == "card" else Color("fff6e2")
			sb.set_corner_radius_all(9)
			sb.set_border_width_all(1 if kind == "card" else 2)
			sb.border_color = Color("e2dbcd") if kind == "card" else Color("f0a030")
			sb.shadow_color = Color(0, 0, 0, 0.08)
			sb.shadow_size = 2
			sb.shadow_offset = Vector2(0, 1)
		_:
			sb.bg_color = PAPER
			sb.set_corner_radius_all(8)
	return sb


func _btn_sb(color: String, state: String) -> StyleBox:
	if state == "focus":
		return StyleBoxEmpty.new()
	var c: Array = BTN.get("grey" if state == "disabled" else color, BTN.blue)
	var sb := StyleBoxFlat.new()
	sb.anti_aliasing = true
	sb.bg_color = Color(c[0])
	if state == "hover":
		sb.bg_color = sb.bg_color.lightened(0.08)
	elif state == "pressed":
		sb.bg_color = Color(c[1])
	sb.set_corner_radius_all(8)
	sb.border_width_bottom = 0 if state == "pressed" else 2
	sb.border_color = Color(c[1]).darkened(0.1)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 5 if state != "pressed" else 6
	sb.content_margin_bottom = 5 if state != "pressed" else 4
	return sb


## Numbers and short captions in the bold font. Sizes are given in the old pixel-font scale.
func _label(text: String, parent: Node, size := 8, outline := 0) -> Label:
	var l := Label.new()
	l.text = text
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if size != 8:
		l.add_theme_font_size_override("font_size", int(roundf(size * 1.25)))
	if outline > 0:
		l.add_theme_constant_override("outline_size", maxi(2, outline / 2))
	if parent:
		parent.add_child(l)
	return l


## Body text in the readable font, dark on light panels.
func text(t: String, parent: Node, size := 12, col := INK, width := 0.0) -> Label:
	var l := _label(t, parent)
	l.add_theme_font_override("font", body_font)
	l.add_theme_font_size_override("font_size", maxi(9, size - 1))
	l.add_theme_color_override("font_color", _ink(col))
	l.add_theme_constant_override("line_spacing", 2)
	if width > 0.0:
		l.custom_minimum_size = Vector2(width, 0)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


func title(t: String, parent: Node, size := 15, col := Color("7a2a1a")) -> Label:
	var l := text(t, parent, size, col)
	l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", maxi(10, size - 2))
	return l


## The old warm browns become neutral modern inks; other colours stay as they are.
func _ink(c: Color) -> Color:
	match c.to_html(false):
		"3a2a1e":
			return INK
		"7a2a1a":
			return Color("1f2633")
		"8a5a2a", "8a4a2a":
			return Color("6b5a44")
	return c


func icon_rect(name: String, parent: Node, px := 16) -> TextureRect:
	var r := TextureRect.new()
	r.texture = Assets.ui_icon(name)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	r.custom_minimum_size = Vector2(px, px)
	if parent:
		parent.add_child(r)
	return r


func button(t: String, icon_name: String, color: String, cb: Callable, min_size := Vector2(0, 26)) -> Button:
	var b := Button.new()
	b.text = t
	b.focus_mode = Control.FOCUS_NONE
	if icon_name != "":
		b.icon = Assets.ui_icon(icon_name)
		b.add_theme_constant_override("icon_max_width", 18)
	b.custom_minimum_size = min_size
	b.add_theme_font_override("font", bold_font)
	b.add_theme_font_size_override("font_size", 12)
	if color != "blue":
		for st in ["normal", "hover", "pressed", "disabled"]:
			b.add_theme_stylebox_override(st, _btn_sb(color, st))
	b.pressed.connect(func():
		if drag_block:
			return
		Game.sfx("tap")
		cb.call())
	return b


## Lists scroll by dragging anywhere on them, even over buttons (phones have no wheel).
func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			drag_block = false
			_drag_dist = 0.0
			_drag_sc = null
			for sc in [build_scroll, modal_scroll] + extra_scrolls:
				if is_instance_valid(sc) and sc.is_visible_in_tree() and sc.get_global_rect().has_point(event.position):
					_drag_sc = sc
		else:
			_drag_sc = null
	elif event is InputEventMouseMotion and _drag_sc and (event.button_mask & MOUSE_BUTTON_MASK_LEFT):
		var rel: Vector2 = event.relative / S
		_drag_sc.scroll_horizontal -= int(rel.x)
		_drag_sc.scroll_vertical -= int(rel.y)
		_drag_dist += rel.length()
		if _drag_dist > 8.0:
			drag_block = true
		get_viewport().set_input_as_handled()


func round_btn(icon_name: String, color: String, cb: Callable, size := 44) -> TextureButton:
	var b := TextureButton.new()
	b.texture_normal = Assets.tex("ui/round_" + color)
	b.texture_pressed = Assets.tex("ui/round_%s_p" % color)
	b.ignore_texture_size = true
	b.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	b.custom_minimum_size = Vector2(size, size)
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	b.focus_mode = Control.FOCUS_NONE
	var ic := TextureRect.new()
	ic.texture = Assets.ui_icon(icon_name)
	ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	var inner := size * 0.56
	ic.size = Vector2(inner, inner)
	ic.position = Vector2((size - inner) / 2, (size - inner) / 2 - size * 0.03)
	b.add_child(ic)
	b.pressed.connect(func():
		if drag_block:
			return
		Game.sfx("tap")
		cb.call())
	b.button_down.connect(func(): ic.position.y += size * 0.03)
	b.button_up.connect(func(): ic.position.y -= size * 0.03)
	return b


func price_row(coins: int, gems: int, dark := true, parent: Node = null) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 3)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if coins > 0 or gems == 0:
		icon_rect("coin", h)
		var l := _label(Loc.num(coins), h)
		l.add_theme_color_override("font_color", (Color("3a2a1e") if dark else Color.WHITE) if Game.coins >= coins else Color("d83a2a"))
	if gems > 0:
		icon_rect("gem", h)
		var l := _label(str(gems), h)
		l.add_theme_color_override("font_color", (Color("1e6a3a") if dark else Color.WHITE) if Game.gems >= gems else Color("d83a2a"))
	if parent:
		parent.add_child(h)
	return h


func _pill(icon_name: String, key: String, min_w := 44) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", _sb("pill", 6, 4))
	p.mouse_filter = Control.MOUSE_FILTER_STOP
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 4)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(h)
	var ic := icon_rect(icon_name, h)
	if key == "happy":
		happy_icon = ic
	var l := _label("0", h)
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.custom_minimum_size = Vector2(min_w, 0)
	pill_labels[key] = l
	pills[key] = p
	p.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed:
			_pill_info(key))
	return p


# ====================================================================== top / side / bottom
func _build_top() -> void:
	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", 3)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	safe.add_child(bar)
	var lv := PanelContainer.new()
	lv.add_theme_stylebox_override("panel", _sb("pill", 6, 4))
	bar.add_child(lv)
	var lvbox := VBoxContainer.new()
	lvbox.add_theme_constant_override("separation", 2)
	lv.add_child(lvbox)
	var lvrow := HBoxContainer.new()
	lvbox.add_child(lvrow)
	icon_rect("star", lvrow)
	level_label = _label("1", lvrow)
	level_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var xp_bg := ColorRect.new()
	xp_bg.color = Color("1a1622")
	xp_bg.custom_minimum_size = Vector2(36, 3)
	lvbox.add_child(xp_bg)
	rank_label = text("", lvbox, 9, Color("f8c840"))
	xp_bar = ColorRect.new()
	xp_bar.color = Color("f8c840")
	xp_bar.size = Vector2(0, 3)
	xp_bg.add_child(xp_bar)
	bar.add_child(_pill("coin", "coins", 50))
	bar.add_child(_pill("gem", "gems", 16))
	bar.add_child(_pill("goods", "goods", 30))
	bar.add_child(_pill("pop", "pop", 30))
	bar.add_child(_pill("happy", "happy", 26))
	bar.add_child(_pill("reputation", "rep", 18))

	var right := HBoxContainer.new()
	right.add_theme_constant_override("separation", 3)
	safe.add_child(right)
	var ph := PanelContainer.new()
	ph.add_theme_stylebox_override("panel", _sb("pill", 6, 3))
	ph.mouse_filter = Control.MOUSE_FILTER_STOP
	ph.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed:
			toast(Loc.t("weather_" + Game.weather) + " · " + Loc.t(Game.season)))
	right.add_child(ph)
	var phh := HBoxContainer.new()
	phh.add_theme_constant_override("separation", 3)
	ph.add_child(phh)
	weather_icon = icon_rect("sun", phh)
	var dv := VBoxContainer.new()
	dv.add_theme_constant_override("separation", 1)
	phh.add_child(dv)
	clock_label = _label("", dv)
	date_label = text("", dv, 11, Color("d8d0e8"))
	var gear := round_btn("gear", "grey", func(): panels.settings(), 28)
	gear.name = "SettingsButton"
	right.add_child(gear)
	_gated.append(gear)
	right.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	right.grow_horizontal = Control.GROW_DIRECTION_BEGIN


func _build_side() -> void:
	side_buttons = VFlowContainer.new()
	side_buttons.add_theme_constant_override("v_separation", 4)
	side_buttons.add_theme_constant_override("h_separation", 4)
	safe.add_child(side_buttons)
	for spec in [["mail", "orange", func(): panels.inbox()], ["finance", "green", func(): panels.finance()],
			["mission", "blue", func(): panels.missions()], ["law", "purple", func(): panels.city_info()],
			["trophy", "orange", func(): panels.achievements()]]:
		var b := round_btn(spec[0], spec[1], spec[2], 34)
		b.name = (spec[0] as String).capitalize() + "Button"
		side_buttons.add_child(b)
		_gated.append(b)
		var badge := _label("", b, 16, 5)
		badge.add_theme_color_override("font_color", Color("ffe060"))
		badge.position = Vector2(24, -4)
		badges[spec[0]] = badge
	# see-through tall buildings, to look at what stands behind them
	var xray_cb := func():
		city.set_xray(not city.xray)
		Game.sfx("tap")
		toast(Loc.t("xray_on" if city.xray else "xray_off"))
	holiday_btn = round_btn("calendar", "purple", func(): panels.holiday(), 34)
	holiday_btn.name = "HolidayButton"
	side_buttons.add_child(holiday_btn)
	holiday_btn.visible = Game.holiday() != ""
	Game.day_passed.connect(func(_d): holiday_btn.visible = Game.holiday() != "")
	var xb := round_btn("eye", "blue", xray_cb, 34)
	xb.name = "XrayButton"
	side_buttons.add_child(xb)
	var pb := round_btn("camera", "orange", func(): city.photo.enter(), 34)
	pb.name = "PhotoButton"
	side_buttons.add_child(pb)
	side_buttons.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	side_buttons.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_place_side()


## In a friend's city: whose city it is and the way back home (nothing done here is kept).
func _show_visit_bar() -> void:
	var box := HBoxContainer.new()
	box.name = "VisitBar"
	box.add_theme_constant_override("separation", 6)
	var pc := PanelContainer.new()
	pc.add_child(box)
	var lab := _label(Loc.t("visit_bar") % Game.visiting, box, 11)
	lab.add_theme_color_override("font_color", Color("3a2a1e"))
	lab.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	box.add_child(button(Loc.t("visit_home"), "home", "green", func():
		Game.go_home()
		get_tree().reload_current_scene()))
	var holder := CenterContainer.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(pc)
	safe.add_child(holder)
	holder.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	holder.offset_top = 40.0
	holder.offset_bottom = 40.0
	toast(Loc.t("visit_hint"))


## The side column sits mid-right between the top bar and the build button; with big buttons
## on a short screen it wraps into a second column instead of covering them.
func _place_side() -> void:
	if side_buttons == null:
		return
	var col := -4.0
	for b in side_buttons.get_children():
		col += (b as Control).get_combined_minimum_size().y + 4.0
	var top := 40.0
	var bottom := safe.size.y - 60.0
	var h := minf(col, bottom - top)
	side_buttons.offset_top = clampf(safe.size.y / 2.0 - col / 2.0, top, maxf(top, bottom - h))
	side_buttons.offset_bottom = side_buttons.offset_top + h
	side_buttons.offset_right = 0.0
	side_buttons.offset_left = 0.0


func _build_bottom() -> void:
	main_buttons = Control.new()
	main_buttons.mouse_filter = Control.MOUSE_FILTER_IGNORE
	main_buttons.set_anchors_preset(Control.PRESET_FULL_RECT)
	safe.add_child(main_buttons)
	var right := HBoxContainer.new()
	right.add_theme_constant_override("separation", 6)
	right.alignment = BoxContainer.ALIGNMENT_END
	main_buttons.add_child(right)
	var dem := round_btn("demolish", "red", func(): city.start_demolish(), 38)
	var road := round_btn("road", "grey", func(): city.start_road(), 38)
	var build := round_btn("shop", "orange", toggle_build_menu, 54)
	build.name = "BuildButton"
	road.name = "RoadButton"
	for b in [dem, road]:
		b.size_flags_vertical = Control.SIZE_SHRINK_END
	right.add_child(dem)
	right.add_child(road)
	right.add_child(build)
	right.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	right.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	right.grow_vertical = Control.GROW_DIRECTION_BEGIN

	var left := HBoxContainer.new()
	left.add_theme_constant_override("separation", 6)
	main_buttons.add_child(left)
	var land := round_btn("land", "green", func(): city.start_land(), 38)
	land.name = "LandButton"
	dem.name = "DemolishButton"
	left.add_child(land)
	var paw := round_btn("paw", "orange", func(): panels.animals(), 38)
	paw.name = "AnimalsButton"
	left.add_child(paw)
	for b in [dem, road, build, land, paw]:
		_gated.append(b)
	left.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	left.grow_vertical = Control.GROW_DIRECTION_BEGIN


func _build_mode_bar() -> void:
	mode_bar = PanelContainer.new()
	safe.add_child(mode_bar)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	mode_bar.add_child(h)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", 3)
	h.add_child(v)
	tool_tabs = HBoxContainer.new()
	tool_tabs.add_theme_constant_override("separation", 4)
	v.add_child(tool_tabs)
	for tl in ["road", "water", "wall", "deco", "pave"]:
		var tb := button(Loc.t("tool_" + tl), {"road": "road", "water": "river", "wall": "wall", "deco": "street", "pave": "tile"}[tl], "orange",
			func(): city.set_tool(tl))
		tb.set_meta("tool", tl)
		tb.add_theme_font_size_override("font_size", 11)
		tool_tabs.add_child(tb)
	road_types = HFlowContainer.new()
	road_types.add_theme_constant_override("h_separation", 4)
	road_types.add_theme_constant_override("v_separation", 3)
	v.add_child(road_types)
	lamp_types = HBoxContainer.new()
	lamp_types.add_theme_constant_override("separation", 4)
	v.add_child(lamp_types)
	for st in ["classic", "modern", "lantern"]:
		var b := button(Loc.t("lamp_" + st), "", "blue", func():
			city.lamp_style = st
			show_lamp_bar())
		b.set_meta("style", st)
		lamp_types.add_child(b)
	mode_title = title("", v, 13)
	mode_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	mode_title.custom_minimum_size = Vector2(230, 0)
	mode_sub = text("", v, 11, Color("8a5a2a"), 230)
	mode_hint = text("", v, 11, Color("c83a2a"), 230)
	mode_price = HBoxContainer.new()
	v.add_child(mode_price)
	mode_rot = round_btn("rotate", "blue", func(): city.rotate_ghost(), 34)
	h.add_child(mode_rot)
	mode_land = round_btn("info", "blue", func(): panels.land_info(), 34)
	h.add_child(mode_land)
	h.add_child(round_btn("cancel", "red", func(): city.cancel_mode(), 34))
	mode_ok = round_btn("ok", "green", _on_ok, 34)
	h.add_child(mode_ok)
	mode_bar.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	mode_bar.grow_horizontal = Control.GROW_DIRECTION_BOTH
	mode_bar.grow_vertical = Control.GROW_DIRECTION_BEGIN
	mode_bar.visible = false


func _set_ok(enabled: bool) -> void:
	_ok_enabled = enabled
	mode_ok.modulate = Color.WHITE if enabled else Color(0.55, 0.55, 0.6)


func _on_ok() -> void:
	if _ok_enabled:
		city.confirm_mode()


func _show_bar() -> void:
	_close_panels()
	mode_bar.visible = true
	main_buttons.visible = false
	side_buttons.visible = false
	mode_bar.reset_size()


func show_mode_bar(t: String, sub: String, can_confirm: bool) -> void:
	road_types.visible = false
	tool_tabs.visible = false
	lamp_types.visible = false
	mode_rot.visible = city.mode in [city.Mode.PLACE, city.Mode.MOVE]
	mode_land.visible = city.mode == city.Mode.LAND
	mode_title.text = t
	mode_title.visible = true
	mode_sub.text = sub
	mode_sub.visible = sub != ""
	mode_hint.visible = false
	for c in mode_price.get_children():
		c.queue_free()
	_set_ok(can_confirm)
	_show_bar()


func show_place_bar(id: String) -> void:
	var d: Dictionary = Data.B[id]
	show_mode_bar(Data.name_of(id), Loc.t("zone_needed") % ", ".join(d.zones.map(func(z): return Data.zone_name(z))), true)
	price_row(d.cost, d.get("gems", 0), true, mode_price)


func place_hint(why: String, has_road: bool) -> void:
	var t := ""
	if why == "wrong_zone":
		t = Loc.t("wrong_zone")
	elif why == "need_animals":
		t = Loc.t("need_animals") % Data.ZOO_ANIMALS
	elif why != "":
		t = Loc.t("bad_place")
	elif not has_road:
		t = Loc.t("hint_no_road")
	mode_hint.text = t
	mode_hint.visible = t != ""
	mode_bar.reset_size()


func show_road_bar(sub: String, can_confirm: bool) -> void:
	mode_rot.visible = false
	mode_land.visible = false
	road_types.visible = true
	tool_tabs.visible = true
	lamp_types.visible = false
	mode_title.visible = false
	mode_hint.visible = false
	for tb in tool_tabs.get_children():
		tb.modulate = Color.WHITE if tb.get_meta("tool") == city.tool else Color(0.7, 0.7, 0.78)
	if _types_tool != city.tool:
		_types_tool = city.tool
		for b in road_types.get_children():
			road_types.remove_child(b)
			b.queue_free()
		for t in _tool_options(city.tool):
			var rm: bool = t in ["remove", "fill", "none"]
			var b := button("", "remove" if rm else "", "red" if rm else "blue", func(): city.set_road_type(t))
			b.set_meta("road", t)
			road_types.add_child(b)
	for b in road_types.get_children():
		var t: String = b.get_meta("road")
		b.modulate = Color.WHITE if t == city.road_type else Color(0.6, 0.6, 0.72)
		b.text = _tool_label(city.tool, t)
	mode_sub.text = sub + ("\n" + Loc.t("hint_road_drag") if city.tool == "road" else "")
	mode_sub.visible = true
	for c in mode_price.get_children():
		c.queue_free()
	_set_ok(can_confirm)
	_show_bar()


func _tool_options(tl: String) -> Array:
	match tl:
		"water":
			return ["dig", "fill"]
		"wall":
			return Data.WALL_ORDER + ["remove"]
		"deco":
			return Data.ROAD_DECO_ORDER + ["none"]
		"pave":
			return Data.PAVE_ORDER + ["remove"]
	return Data.ROAD_ORDER + ["remove"]


func _tool_label(tl: String, t: String) -> String:
	match tl:
		"water":
			return "%s %d" % [Loc.t("water_dig"), Data.WATER_COST] if t == "dig" else Loc.t("water_fill")
		"wall":
			return "%s %d" % [Loc.pick(Data.WALLS[t].name), Data.WALLS[t].cost] if t != "remove" else Loc.t("wall_remove")
		"deco":
			return "%s %d" % [Loc.pick(Data.ROAD_DECO[t].name), Data.ROAD_DECO[t].cost] if t != "none" else Loc.t("deco_remove")
		"pave":
			return "%s %d" % [Loc.pick(Data.PAVES[t].name), Data.PAVES[t].cost] if t != "remove" else Loc.t("pave_remove")
	return "%s %d" % [Loc.pick(Data.ROADS[t].name), Data.ROADS[t].cost] if t != "remove" else Loc.t("road_remove")


func show_lamp_bar() -> void:
	mode_rot.visible = false
	mode_land.visible = false
	road_types.visible = false
	tool_tabs.visible = false
	lamp_types.visible = true
	mode_title.text = Data.name_of("lamp")
	mode_title.visible = true
	mode_hint.visible = false
	for b in lamp_types.get_children():
		b.modulate = Color.WHITE if b.get_meta("style") == city.lamp_style else Color(0.6, 0.6, 0.72)
	mode_sub.text = Loc.t("hint_lamp") % Data.HOUSE_LAMP_COST
	mode_sub.visible = true
	for c in mode_price.get_children():
		c.queue_free()
	price_row(Data.LAMP_COST, 0, true, mode_price)
	_set_ok(true)
	_show_bar()


func hide_mode_bar() -> void:
	mode_bar.visible = false
	main_buttons.visible = true
	side_buttons.visible = true


# ====================================================================== build menu
func _build_build_menu() -> void:
	build_menu = PanelContainer.new()
	safe.add_child(build_menu)
	build_menu.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	build_menu.grow_vertical = Control.GROW_DIRECTION_BEGIN
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 5)
	build_menu.add_child(v)
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 3)
	v.add_child(tabs)
	for cat in Data.TABS:
		var b := button(Loc.t("cat_" + cat), "", "blue", func(): _set_cat(cat))
		b.add_theme_font_size_override("font_size", 11)
		tabs.add_child(b)
		build_tabs[cat] = b
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tabs.add_child(spacer)
	tabs.add_child(round_btn("cancel", "red", toggle_build_menu, 26))
	var scroll := ScrollContainer.new()
	build_scroll = scroll
	scroll.custom_minimum_size = Vector2(0, 124)
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	v.add_child(scroll)
	build_cards = HBoxContainer.new()
	build_cards.add_theme_constant_override("separation", 5)
	scroll.add_child(build_cards)
	build_menu.visible = false


func toggle_build_menu() -> void:
	if build_menu.visible:
		build_menu.visible = false
		main_buttons.visible = true
		side_buttons.visible = true
		return
	city.cancel_mode()
	_close_panels()
	build_menu.visible = true
	main_buttons.visible = false
	side_buttons.visible = false
	_set_cat(build_cat)


func _set_cat(cat: String) -> void:
	build_cat = cat
	for c in build_tabs:
		var b: Button = build_tabs[c]
		for st in ["normal", "hover", "pressed"]:
			if c == cat:
				b.add_theme_stylebox_override(st, _btn_sb("blue", st))
			else:
				var sb := _btn_sb("blue", st) as StyleBoxFlat
				sb.bg_color = Color("ebe6dc") if st != "hover" else Color("e2dccf")
				sb.border_color = Color("d4ccbc")
				b.add_theme_stylebox_override(st, sb)
		b.add_theme_color_override("font_color", Color.WHITE if c == cat else INK)
		b.add_theme_color_override("font_hover_color", Color.WHITE if c == cat else INK)
	for c in build_cards.get_children():
		c.queue_free()
	if cat == "hotel":
		build_cards.add_child(_hotel_banner())
	for id in Data.ORDER:
		if Data.tab_of(id) == cat:
			build_cards.add_child(_card(id))


## The hotels window opens with a note: hotels need a road out to the highway.
func _hotel_banner() -> Control:
	var open := Game.is_connected_to_highway()
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(150, 122)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("3a2a4a") if open else Color("5a4a3a")
	sb.border_color = Color("e8c060")
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 6
	sb.content_margin_right = 6
	p.add_theme_stylebox_override("panel", sb)
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	p.add_child(v)
	var title := text(Loc.t("hotels_title"), v, 15, Color("f4d070"))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var l := text(Loc.t("hotels_open" if open else "hotels_locked"), v, 10, Color("f4eee0"), 138)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return p


func _card(id: String) -> Button:
	var d: Dictionary = Data.B[id]
	var locked: bool = Game.level < d.lvl
	var no_road: bool = d.get("highway", false) and not Game.is_connected_to_highway()
	var card := Button.new()
	card.focus_mode = Control.FOCUS_NONE
	card.custom_minimum_size = Vector2(100, 122)
	for st in ["normal", "hover", "pressed", "disabled"]:
		card.add_theme_stylebox_override(st, _sb("card_sel" if st == "hover" else "card", 5, 4))
	var v := VBoxContainer.new()
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	v.offset_left = 4
	v.offset_right = -4
	v.offset_top = 3
	v.offset_bottom = -3
	v.add_theme_constant_override("separation", 2)
	card.add_child(v)
	var pic := TextureRect.new()
	pic.texture = Assets.tex("buildings/" + Assets.building_sprite(id, 1)) if id != "lamp" else Assets.tex("units/lamp_classic")
	pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	pic.custom_minimum_size = Vector2(92, 56)
	pic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(pic)
	var name := text(Data.name_of(id), v, 11, Color("3a2a1e"))
	name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name.clip_text = true
	name.custom_minimum_size = Vector2(90, 0)
	# zone badges in the corner of the picture
	var zones := HBoxContainer.new()
	zones.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zones.position = Vector2(4, 4)
	zones.add_theme_constant_override("separation", 0)
	card.add_child(zones)
	if d.zones.size() < 4:
		for z in d.zones:
			icon_rect({"city": "build", "farm": "goods", "industry": "jobs", "leisure": "zoo"}[z], zones, 12)
	if locked:
		var row := HBoxContainer.new()
		row.alignment = BoxContainer.ALIGNMENT_CENTER
		v.add_child(row)
		icon_rect("lock", row)
		var l := _label(Loc.t("lvl_short") + " " + str(d.lvl), row)
		l.add_theme_color_override("font_color", Color("a83a2a"))
		pic.modulate = Color(0.2, 0.2, 0.25, 0.8)
	elif no_road:
		var row := HBoxContainer.new()
		row.alignment = BoxContainer.ALIGNMENT_CENTER
		v.add_child(row)
		icon_rect("lock", row)
		var l := _label(Loc.t("cat_hotel"), row)
		l.add_theme_color_override("font_color", Color("a83a2a"))
		pic.modulate = Color(0.45, 0.45, 0.5, 0.85)
	else:
		var pr := price_row(d.cost, d.get("gems", 0))
		pr.alignment = BoxContainer.ALIGNMENT_CENTER
		v.add_child(pr)
		var stat := HBoxContainer.new()
		stat.alignment = BoxContainer.ALIGNMENT_CENTER
		stat.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(stat)
		var txt := ""
		var ic := "happy"
		match d.cat:
			"home":
				ic = "pop"
				txt = "+%d" % d.pop
			"shop", "fun":
				ic = "coin"
				txt = "%d/%s" % [d.income, Loc.duration(d.cycle)]
			"ind":
				ic = "goods"
				txt = "%d/%s" % [d.out, Loc.duration(d.cycle)]
			"service":
				ic = "jobs"
				txt = "+%d" % d.jobs
			_:
				txt = "+%d" % d.happy
		icon_rect(ic, stat)
		var sl := text(txt, stat, 11, Color("4a7a2a"))
		sl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	card.pressed.connect(func():
		if drag_block:
			return
		if Game.level < d.lvl:
			Game.sfx("error")
			toast(Loc.t("locked_lvl") % d.lvl)
			return
		if id == "zoo" and Game.caught.size() < Data.ZOO_ANIMALS:
			Game.sfx("error")
			toast(Loc.t("need_animals") % Data.ZOO_ANIMALS)
			return
		if d.get("highway", false) and not Game.is_connected_to_highway():
			Game.sfx("error")
			toast(Loc.t("need_highway"))
			return
		Game.sfx("tap")
		build_menu.visible = false
		city.start_place(id))
	return card


# ====================================================================== info card
func _build_info() -> void:
	info_panel = PanelContainer.new()
	info_panel.add_theme_stylebox_override("panel", _sb("panel", 7, 7))
	safe.add_child(info_panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	info_panel.add_child(v)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 6)
	v.add_child(head)
	info_title = title("", head, 14)
	info_stars = HBoxContainer.new()
	info_stars.add_theme_constant_override("separation", 0)
	head.add_child(info_stars)
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(sp)
	head.add_child(round_btn("cancel", "red", func(): info_panel.visible = false, 22))
	info_line = HBoxContainer.new()
	info_line.add_theme_constant_override("separation", 4)
	v.add_child(info_line)
	info_note = text("", v, 11, Color("8a4a2a"), 280)
	info_bar_bg = ColorRect.new()
	info_bar_bg.color = Color("5a5468")
	info_bar_bg.custom_minimum_size = Vector2(280, 4)
	v.add_child(info_bar_bg)
	info_bar = ColorRect.new()
	info_bar.color = Color("5ab84a")
	info_bar.size = Vector2(0, 4)
	info_bar_bg.add_child(info_bar)
	info_actions = HBoxContainer.new()
	info_actions.add_theme_constant_override("separation", 4)
	v.add_child(info_actions)
	info_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	info_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	info_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	info_panel.offset_bottom = -2
	info_panel.visible = false


func show_info(uid: int) -> void:
	_close_panels()
	info_uid = uid
	_info_key = ""
	info_panel.visible = true
	_refresh_info()
	info_panel.reset_size()


func _stat(icon: String, t: String, col := Color("3a2a1e")) -> void:
	icon_rect(icon, info_line)
	var l := text(t, info_line, 12, col)
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER


func _refresh_info() -> void:
	if not Game.buildings.has(info_uid):
		info_panel.visible = false
		return
	var b: Dictionary = Game.buildings[info_uid]
	var d: Dictionary = Data.B[b.id]
	var lv: int = b.lvl
	var ratio := 0.0
	var busy: bool = not b.built or b.upg
	var note := ""
	if not b.built:
		note = Loc.t("constructing") % Loc.duration(Game.remaining(info_uid))
		ratio = b.prog / d.time
	elif b.upg:
		note = Loc.t("upgrading") % Loc.duration(Game.remaining(info_uid))
		ratio = b.prog / Data.upgrade_cost(b.id, lv).time
	else:
		var st := Game.status(info_uid)
		if st != "":
			note = Loc.t("st_" + st)
		elif b.ready:
			note = Loc.t("ready_collect")
		elif d.cat in ["home", "shop", "ind", "fun"] and b.priv == "":
			var spd := Game.staff if d.cat != "home" else 1.0
			note = Loc.t("working") % Loc.duration((d.cycle - b.prog) / maxf(0.15, spd))
		if b.priv != "":
			note = Loc.t("private_owner") % b.priv
			if Data.brand_of(b.id) != "":
				note = Loc.t("brand_owner") % [Data.brand_name(Data.brand_of(b.id)), b.priv]
		if d.cat in ["home", "shop", "ind", "fun"]:
			ratio = b.prog / d.cycle
	info_note.text = note
	info_note.visible = note != ""
	info_bar_bg.visible = busy or (d.cat in ["home", "shop", "ind", "fun"] and b.priv == "")
	info_bar.size.x = roundf(280.0 * clampf(ratio, 0.0, 1.0))
	var key := "%d|%s|%s|%s|%s|%d|%d|%d|%d|%d|%s" % [lv, b.built, b.upg, b.closed, b.dmg, b.occ, Game.coins / 50, Game.gems,
		Game.level, int(Game.happy), b.ready]
	if key == _info_key:
		return
	_info_key = key
	info_title.text = Data.name_of(b.id)
	for c in info_stars.get_children():
		c.queue_free()
	for i in 3:
		var s := icon_rect("star", info_stars, 12)
		s.modulate = Color.WHITE if i < lv else Color(0.25, 0.25, 0.3, 0.6)
	for c in info_line.get_children():
		c.queue_free()
	match d.cat:
		"home":
			_stat("pop", "%d/%d" % [b.occ, Data.stat(b.id, "pop", lv)])
			var h: int = Game.home_happy.get(info_uid, int(Game.happy))
			_stat("happy" if h >= 45 else "unhappy", "%d%%" % h, Color("3a7a2a") if h >= 45 else Color("c83a2a"))
			_stat("coin", "%d/%s" % [int(Data.stat(b.id, "rent", lv) * Game.tax / 10.0), Loc.duration(d.cycle)])
		"shop", "fun":
			_stat("jobs", str(Data.stat(b.id, "jobs", lv)))
			if b.priv != "":
				_stat("tax", "%d/%s" % [int(Data.stat(b.id, "income", lv) * 3 * Game.tax / 10.0), Loc.t("per_day")])
			else:
				_stat("coin", "%d/%s" % [Data.stat(b.id, "income", lv), Loc.duration(d.cycle)])
			if d.cat == "shop":
				_stat("goods", "-%d" % Data.stat(b.id, "use", lv))
		"ind":
			_stat("jobs", str(Data.stat(b.id, "jobs", lv)))
			_stat("goods", "%d/%s" % [Data.stat(b.id, "out", lv), Loc.duration(d.cycle)])
		"service":
			_stat("jobs", str(Data.stat(b.id, "jobs", lv)))
			if d.has("power"):
				_stat("power", "+%d kW" % Data.stat(b.id, "power", lv))
			elif d.has("water"):
				_stat("water", "+%d" % Data.stat(b.id, "water", lv))
			else:
				_stat("happy", "+%d" % Data.stat(b.id, "happy", lv))
		"decor":
			_stat("happy", "+%d" % Data.stat(b.id, "happy", lv))
	if b.priv == "" and d.cat != "decor":
		_stat("finance", "-%d/%s" % [Data.stat(b.id, "upkeep", lv), Loc.t("per_day")], Color("a85a2a"))
	for c in info_actions.get_children():
		c.queue_free()
	var uid := info_uid
	if busy:
		var sp := button("%s %d" % [Loc.t("speedup"), Game.speedup_cost(uid)], "gem", "purple", func():
			Game.speedup(uid)
			_info_key = "")
		info_actions.add_child(sp)
	else:
		if b.dmg:
			info_actions.add_child(button(str(Game.repair_cost(uid)), "upgrade", "green", func():
				Game.repair(uid)
				_info_key = ""))
		elif lv < 3 and b.priv == "":
			var up := Data.upgrade_cost(b.id, lv)
			if Game.level >= up.level:
				var ub := button(Loc.num(up.coins) + (" +%d" % up.gems if up.gems > 0 else ""), "upgrade", "green", func():
					Game.upgrade(uid)
					_info_key = "")
				info_actions.add_child(ub)
			else:
				var l := text(Loc.t("upgrade_need") % up.level, info_actions, 11, Color("8a5a2a"))
				l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		if b.priv == "":
			info_actions.add_child(round_btn("move", "blue", func(): city.start_move(uid), 26))
			info_actions.add_child(round_btn("rotate", "blue", func():
				Game.rotate_building(uid)
				_info_key = "", 26))
		if d.cat != "decor":
			info_actions.add_child(round_btn("door" if b.closed else "closed", "orange", func():
				if b.closed:
					Game.set_closed(uid, false)
				else:
					confirm(Loc.t("close_q") % Data.name_of(b.id), func(): Game.set_closed(uid, true))
				_info_key = "", 26))
		if d.cat == "home":
			if b.occ > 0:
				info_actions.add_child(round_btn("evict", "red", func():
					confirm(Loc.t("evict_q"), func():
						Game.evict(uid)
						_info_key = ""), 26))
			if b.link > 0:
				info_actions.add_child(round_btn("link", "purple", func():
					confirm(Loc.t("unlink_q"), func():
						Game.unlink(uid)
						_info_key = ""), 26))
			else:
				info_actions.add_child(round_btn("link", "green", func(): city.start_link(uid), 26))
		if d.get("svc", "") == "patrol":
			info_actions.add_child(round_btn("police", "purple", func(): panels.watchtower(uid), 26))
		if d.get("svc", "") == "garbage":
			info_actions.add_child(round_btn("demolish", "purple", func(): panels.garbage(), 26))
		if d.get("svc", "") == "news":
			info_actions.add_child(round_btn("newspaper", "purple", func(): panels.newspaper(), 26))
		if b.id == "bank" and b.built:
			info_actions.add_child(round_btn("warn", "red", func(): rob_bank(uid), 26))
		if d.get("svc", "") == "airport":
			info_actions.add_child(round_btn("plane", "purple", func(): panels.airport(), 26))
		info_actions.add_child(round_btn("info", "blue", func(): panels.building_details(uid), 26))
	var sp2 := Control.new()
	sp2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info_actions.add_child(sp2)
	info_actions.add_child(round_btn("demolish", "red", func():
		confirm(Loc.t("demolish_q") % [Data.name_of(Game.buildings[uid].id), Game.refund_of(uid)], func(): Game.demolish(uid)), 26))
	info_panel.reset_size.call_deferred()


# ====================================================================== modal
func _build_modal() -> void:
	modal = Control.new()
	modal.mouse_filter = Control.MOUSE_FILTER_STOP
	root.add_child(modal)
	var dim := ColorRect.new()
	dim.color = Color(0.05, 0.04, 0.1, 0.55)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	modal.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	modal.add_child(center)
	modal_panel = PanelContainer.new()
	center.add_child(modal_panel)
	modal_scroll = ScrollContainer.new()
	modal_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	modal_panel.add_child(modal_scroll)
	modal_box = VBoxContainer.new()
	modal_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	modal_box.add_theme_constant_override("separation", 7)
	modal_scroll.add_child(modal_box)
	modal.visible = false


## buttons: Array of [text, color, Callable, (optional) icon]
func popup(t: String, body: String, buttons: Array, extra: Control = null, width := 0.0) -> void:
	for c in modal_box.get_children():
		modal_box.remove_child(c)
		c.queue_free()
	var w := width if width > 0.0 else minf(420.0, root.size.x - 60.0)
	if t != "":
		var tl := title(t, modal_box, 16)
		tl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if body != "":
		text(body, modal_box, 12, Color("3a2a1e"), w)
	if extra:
		modal_box.add_child(extra)
		# narrow content (a column of buttons) sits in the middle of the window
		if extra.get_combined_minimum_size().x < w * 0.7:
			extra.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	if not buttons.is_empty():
		var h := HBoxContainer.new()
		h.alignment = BoxContainer.ALIGNMENT_CENTER
		h.add_theme_constant_override("separation", 10)
		modal_box.add_child(h)
		for b in buttons:
			var cb: Callable = b[2]
			var btn := button(b[0], b[3] if b.size() > 3 else "", b[1], func():
				close_modal()
				if cb.is_valid():
					cb.call())
			btn.custom_minimum_size = Vector2(90, 28)
			h.add_child(btn)
	modal.size = root.size
	modal.visible = true
	_size_modal.call_deferred(w)


func _size_modal(w: float) -> void:
	var max_h := root.size.y - 40.0
	var need := modal_box.get_combined_minimum_size()
	modal_scroll.custom_minimum_size = Vector2(maxf(w, need.x) + (8 if need.y > max_h else 0), minf(need.y, max_h))
	modal_scroll.scroll_vertical = 0


func close_modal() -> void:
	modal.visible = false


## The mayor robs a bank (ROADMAP 25): shows the loot and the risk first; in prison offers bail instead.
func rob_bank(uid: int) -> void:
	if Game.in_jail():
		popup(Loc.t("title"), Loc.t("in_jail") % Game.jail_hours(), [[Loc.t("cancel"), "red", Callable()],
			[Loc.t("bail_btn") % Data.JAIL_BAIL_GEMS, "green", func(): Game.pay_bail()]])
		return
	var why := Game.mayor_rob_problem(uid)
	if why != "":
		Game.toast.emit(Loc.t(why))
		Game.sfx("error")
		return
	var pct := int(round(Game.mayor_suspect_chance(uid) * 100.0))
	confirm(Loc.t("rob_q") % [Loc.num(Game.mayor_rob_loot(uid)), pct, Data.JAIL_HOURS, int(Data.JAIL_REP)], func():
		var loot := Game.mayor_rob(uid)
		if loot > 0:
			Game.toast.emit(Loc.t("rob_done") % Loc.num(loot))
		_info_key = "")


func confirm(t: String, on_yes: Callable) -> void:
	popup(Loc.t("title"), t, [[Loc.t("no"), "red", Callable()], [Loc.t("yes"), "green", on_yes]])


## Tap on a crossing: a traffic light or a roundabout (one replaces the other), or take it away.
func crossing(tile: Vector2i) -> void:
	var b := [[Loc.t("cancel"), "red", Callable()]]
	if Game.lights.has(tile):
		b.append([Loc.t("light_remove"), "orange", func(): Game.toggle_light(tile)])
	else:
		b.append([Loc.t("crossing_light") % Data.LIGHT_COST, "green", func(): Game.toggle_light(tile)])
	if Game.rings.has(tile):
		b.append([Loc.t("ring_remove"), "orange", func(): Game.toggle_ring(tile)])
	else:
		b.append([Loc.t("crossing_ring") % Data.RING_COST, "green", func(): Game.toggle_ring(tile)])
	popup(Loc.t("crossing_t"), Loc.t("crossing_body"), b)


func back() -> bool:
	if dialog.visible:
		dialog.skip()
		return true
	if modal.visible:
		close_modal()
		return true
	if build_menu.visible:
		toggle_build_menu()
		return true
	if info_panel.visible:
		info_panel.visible = false
		return true
	return false


func _close_panels() -> void:
	info_panel.visible = false
	if build_menu.visible:
		build_menu.visible = false
		main_buttons.visible = true
		side_buttons.visible = true


## While the tutorial waits for one action, only the named buttons work; [] frees them all.
func gate(allowed: Array) -> void:
	for c in _gated:
		var on := allowed.is_empty() or c.name in allowed
		if c is TextureButton:
			c.disabled = not on
		c.modulate = Color.WHITE if on else Color(0.55, 0.57, 0.62, 0.75)
	for k in pills:
		pills[k].mouse_filter = Control.MOUSE_FILTER_STOP if allowed.is_empty() else Control.MOUSE_FILTER_IGNORE


## Something happened that the tutorial may be waiting for (collect, road, placed:<id> ...).
func tutorial_event(evt: String) -> void:
	if tutorial and tutorial.has_method("on_event"):
		tutorial.on_event(evt)


func open_plot(p: Vector2i) -> void:
	panels.plot(p)


func animal_popup(a: ForestAnimal) -> void:
	panels.catch_animal(a)


func _on_level_up(lvl: int) -> void:
	var names: Array[String] = []
	for id in Data.ORDER:
		if Data.B[id].lvl == lvl:
			names.append(Data.name_of(id))
	var t := Loc.t("level_up_text")
	if not names.is_empty():
		t += "\n\n" + Loc.t("unlocked") % ", ".join(names)
	popup(Loc.t("level_up") % lvl, t, [[Loc.t("ok"), "green", Callable()]])
	if build_menu.visible:
		_set_cat(build_cat)


func _pill_info(key: String) -> void:
	match key:
		"happy":
			toast(Loc.t("happy_line") % [int(Game.happy), int(Game.happy_target)])
		"pop":
			toast(Loc.t("workers_line") % [Game.workers, Game.jobs, Game.capacity])
		"gems":
			toast(Loc.t("gem_line"))
		"goods":
			toast(Loc.t("goods") + ": " + Loc.num(Game.goods))
		"coins":
			panels.finance()
		"rep":
			toast(Loc.t("rep_line") % int(Game.rep))


# ====================================================================== updates & fx
## Keep a panel centred at the bottom of the safe area whatever its current size.
func _dock_bottom(c: Control, lift := 0.0) -> void:
	c.reset_size()
	c.position = Vector2(roundf((safe.size.x - c.size.x) / 2), safe.size.y - c.size.y - lift)


func _process(delta: float) -> void:
	if info_panel.visible:
		_refresh_info()
		_dock_bottom(info_panel)
	if mode_bar.visible:
		_dock_bottom(mode_bar)
	# the top bar only changes with the game clock: a few updates a second are plenty
	_bar_t -= delta
	if _bar_t > 0.0:
		return
	_bar_t = 0.25
	clock_label.text = Game.clock_text()
	date_label.text = Loc.t("date_fmt") % [Loc.t(Game.season), Game.day]
	var wi: String = {"clear": "sun", "cloudy": "cloud", "rain": "rain", "storm": "storm", "snow": "snow", "fog": "fog",
		"windy": "windy", "heat": "heat"}[Game.weather]
	if Game.phase == "night" and Game.weather == "clear":
		wi = "moon"
	weather_icon.texture = Assets.ui_icon(wi)
	pill_labels.happy.text = "%d%%" % int(Game.happy)
	happy_icon.texture = Assets.ui_icon("happy" if Game.happy >= 45 else "unhappy")
	var n := Game.ready_missions()
	badges.mission.text = str(n) if n > 0 else ""


func _update() -> void:
	level_label.text = str(Game.level)
	rank_label.text = Game.rank_name()
	xp_bar.size.x = roundf(36.0 * Game.xp / Data.xp_for_level(Game.level))
	pill_labels.coins.text = Loc.num(Game.coins)
	pill_labels.coins.add_theme_color_override("font_color", Color("ff7a6a") if Game.coins < 0 else Color("fff8e8"))
	pill_labels.gems.text = str(Game.gems)
	pill_labels.goods.text = Loc.num(Game.goods)
	pill_labels.pop.text = Loc.num(Game.pop)
	pill_labels.rep.text = str(int(Game.rep))
	_update_badges()


func _update_badges() -> void:
	var u := Events.unread()
	badges.mail.text = str(u) if u > 0 else ""
	var br := Game.broken_rules()
	badges.law.text = "!" if br > 0 else ""


func _rebuild_texts() -> void:
	for cat in build_tabs:
		build_tabs[cat].text = Loc.t("cat_" + cat)
	if build_menu.visible:
		_set_cat(build_cat)
	_info_key = ""


func toast(t: String) -> void:
	toast_label.text = t
	toast_label.autowrap_mode = TextServer.AUTOWRAP_OFF
	toast_label.custom_minimum_size = Vector2.ZERO
	if toast_label.get_minimum_size().x > root.size.x * 0.7:
		toast_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		toast_label.custom_minimum_size = Vector2(root.size.x * 0.7, 0)
	toast_box.reset_size()
	toast_box.position = Vector2(roundf((root.size.x - toast_box.size.x) / 2), roundf(root.size.y * 0.16))
	toast_box.modulate.a = 1.0
	if _toast_tw:
		_toast_tw.kill()
	_toast_tw = toast_box.create_tween()
	_toast_tw.tween_interval(2.2)
	_toast_tw.tween_property(toast_box, "modulate:a", 0.0, 0.5)


func fly_reward(screen_pos: Vector2, res: Dictionary) -> void:
	for kind in ["coins", "goods", "gems"]:
		if not res.has(kind):
			continue
		var target: Control = pills[kind]
		var icon: String = {"coins": "coin", "goods": "goods", "gems": "gem"}[kind]
		var dest := target.global_position / S + Vector2(6, 2)
		for i in (5 if kind != "gems" else 3):
			var ic := TextureRect.new()
			ic.texture = Assets.ui_icon(icon)
			ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			ic.size = Vector2(16, 16)
			ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
			root.add_child(ic)
			var start := screen_pos / S - Vector2(8, 8) + Vector2(randf_range(-12, 12), randf_range(-8, 8))
			ic.position = start
			var tw := ic.create_tween()
			tw.tween_interval(i * 0.06)
			tw.tween_property(ic, "position", start + Vector2(0, -12), 0.15).set_ease(Tween.EASE_OUT)
			tw.tween_property(ic, "position", dest, 0.5).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
			tw.tween_callback(ic.queue_free)
		var pulse := target.create_tween()
		pulse.tween_interval(0.65)
		pulse.tween_property(target, "scale", Vector2(1.12, 1.12), 0.08)
		pulse.tween_property(target, "scale", Vector2.ONE, 0.12)


## Short logo animation on every launch after the first one.
func _show_splash() -> void:
	var c := ColorRect.new()
	c.color = Color("1e2a44")
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(c)
	c.size = root.size
	var l := title(Loc.t("title"), c, 30, Color("ffe080"))
	l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", 24)
	l.add_theme_color_override("font_outline_color", Color("221c28"))
	l.add_theme_constant_override("outline_size", 8)
	l.reset_size()
	l.position = (root.size - l.size) / 2
	l.pivot_offset = l.size / 2
	l.scale = Vector2(0.6, 0.6)
	var tw := c.create_tween()
	tw.tween_property(l, "scale", Vector2.ONE, 0.5).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_interval(0.5)
	tw.tween_property(c, "modulate:a", 0.0, 0.6)
	tw.tween_callback(c.queue_free)
