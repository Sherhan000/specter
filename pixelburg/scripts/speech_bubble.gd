class_name SpeechBubble
extends Node2D
## A short line of text above a resident or a car.

var font: Font
var _panel: NinePatchRect
var _label: Label


func show_text(text: String, seconds: float) -> void:
	z_index = 45
	_panel = NinePatchRect.new()
	_panel.texture = Assets.tex("fx/speech")
	_panel.patch_margin_left = 6
	_panel.patch_margin_right = 6
	_panel.patch_margin_top = 6
	_panel.patch_margin_bottom = 6
	add_child(_panel)
	_label = Label.new()
	_label.text = text
	if font:
		_label.add_theme_font_override("font", font)
	_label.add_theme_font_size_override("font_size", 11)
	_label.add_theme_color_override("font_color", Color("2a2030"))
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var w := clampf(font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x + 2 if font else 90.0, 24.0, 130.0)
	_label.custom_minimum_size = Vector2(w, 0)
	_label.size = Vector2(w, 0)
	add_child(_label)
	_label.reset_size()
	var sz := _label.size + Vector2(10, 6)
	_panel.size = sz
	_panel.position = Vector2(-sz.x / 2, -36 - sz.y)
	_label.position = _panel.position + Vector2(5, 2)
	var tail := Sprite2D.new()
	tail.texture = Assets.tex("fx/speech_tail")
	tail.centered = false
	tail.position = Vector2(-3, -37)
	add_child(tail)
	scale = Vector2(0.0, 0.0)
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_interval(seconds)
	tw.tween_property(self, "modulate:a", 0.0, 0.3)
	tw.tween_callback(queue_free)
