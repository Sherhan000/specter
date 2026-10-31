class_name PhotoMode
extends CanvasLayer
## Photo mode: hides the whole HUD, the camera stays free (drag / pinch / wheel), colour filters
## (day, sunset, night, black and white) and a shutter button that saves a PNG – to the Android gallery
## (Pictures/Pixelburg) or to user://photos on a computer.

const FILTERS := ["none", "day", "sunset", "night", "bw"]
const NAMES := {"none": ["Как есть", "As is"], "day": ["День", "Day"], "sunset": ["Закат", "Sunset"],
	"night": ["Ночь", "Night"], "bw": ["Ч/б", "B&W"]}
const SHADER := """
shader_type canvas_item;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform int mode = 0;
void fragment() {
	vec3 c = texture(screen_tex, SCREEN_UV).rgb;
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	vec2 q = SCREEN_UV - 0.5;
	float vig = 1.0 - dot(q, q) * 0.9;
	if (mode == 1) { c = pow(c, vec3(0.85)) * vec3(1.06, 1.03, 0.97) + 0.04; }
	else if (mode == 2) { c = mix(c, vec3(l) * vec3(1.25, 0.8, 0.55), 0.45) * vec3(1.12, 0.88, 0.75) * vig; }
	else if (mode == 3) { c = mix(c, vec3(l) * vec3(0.45, 0.6, 1.0), 0.55) * vec3(0.55, 0.65, 0.95) * vig; }
	else if (mode == 4) { c = vec3(clamp((l - 0.5) * 1.15 + 0.5, 0.0, 1.0)) * vig; }
	COLOR = vec4(c, 1.0);
}
"""

var city: Node
var hud: CanvasLayer
var active := false
var filter := "none"
var last_path := ""
var filter_layer: CanvasLayer
var filter_rect: ColorRect
var mat: ShaderMaterial
var ui: Control
var row: HBoxContainer
var buttons := {}
var flash: ColorRect
var note: Label


func _ready() -> void:
	layer = 30
	visible = false
	filter_layer = CanvasLayer.new()
	filter_layer.layer = 29
	filter_layer.visible = false
	add_child(filter_layer)
	filter_rect = ColorRect.new()
	filter_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	filter_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = SHADER
	mat = ShaderMaterial.new()
	mat.shader = sh
	filter_rect.material = mat
	filter_layer.add_child(filter_rect)
	ui = Control.new()
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(ui)
	flash = ColorRect.new()
	flash.color = Color.WHITE
	flash.modulate.a = 0.0
	flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(flash)


func _build_ui() -> void:
	for c in ui.get_children():
		c.queue_free()
	buttons = {}
	var s: float = hud.S
	var vp := get_viewport().get_visible_rect().size
	var root := Control.new()
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = hud.ui_theme
	root.scale = Vector2(s, s)
	root.size = vp / s
	ui.add_child(root)
	var close: TextureButton = hud.round_btn("cancel", "red", func(): leave(), 40)
	close.position = Vector2(8, 8)
	root.add_child(close)
	row = HBoxContainer.new()
	row.add_theme_constant_override("separation", 4)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(row)
	for f in FILTERS:
		var b: Button = hud.button(Loc.pick(NAMES[f]), "", "blue", func(): set_filter(f), Vector2(0, 26))
		row.add_child(b)
		buttons[f] = b
	row.size = Vector2(0, 0)
	row.position = Vector2(8, root.size.y - 36)
	var shutter: TextureButton = hud.round_btn("camera", "orange", func(): snap(), 60)
	shutter.position = Vector2(root.size.x - 70, root.size.y / 2.0 - 30)
	root.add_child(shutter)
	note = Label.new()
	note.add_theme_font_size_override("font_size", 11)
	note.add_theme_color_override("font_color", Color.WHITE)
	note.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	note.add_theme_constant_override("outline_size", 4)
	note.position = Vector2(60, 16)
	note.modulate.a = 0.0
	root.add_child(note)
	set_filter(filter)


func enter() -> void:
	if active or city == null:
		return
	active = true
	city.photo_mode = true
	hud.visible = false
	visible = true
	filter_layer.visible = true
	city.cancel_mode()
	_build_ui()
	if OS.get_name() == "Android":
		OS.request_permissions()


func leave() -> void:
	if not active:
		return
	active = false
	city.photo_mode = false
	hud.visible = true
	visible = false
	filter_layer.visible = false
	Game.sfx("tap")


func set_filter(f: String) -> void:
	filter = f
	mat.set_shader_parameter("mode", FILTERS.find(f))
	for k in buttons:
		(buttons[k] as Button).modulate = Color.WHITE if k == f else Color(1, 1, 1, 0.6)
	Game.sfx("tap")


## Where photos go: the gallery folder on Android, user://photos elsewhere.
static func photo_dir() -> String:
	if OS.get_name() == "Android":
		var pics := OS.get_system_dir(OS.SYSTEM_DIR_PICTURES)
		if pics != "":
			var d := pics.path_join("Pixelburg")
			if DirAccess.make_dir_recursive_absolute(d) == OK or DirAccess.dir_exists_absolute(d):
				return d
	DirAccess.make_dir_recursive_absolute("user://photos")
	return "user://photos"


static func save_image(img: Image) -> String:
	var stamp := Time.get_datetime_string_from_system().replace(":", "-").replace("T", "_")
	for dir in [photo_dir(), "user://photos"]:
		DirAccess.make_dir_recursive_absolute(dir)
		var path: String = dir.path_join("pixelburg_%s.png" % stamp)
		if img.save_png(path) == OK:
			return path
	return ""


## Takes the picture: the interface is hidden, the view with the filter is saved as PNG.
func snap() -> void:
	if not active:
		return
	ui.visible = false
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	ui.visible = true
	last_path = save_image(img)
	Game.sfx("upgrade")
	flash.modulate.a = 0.8
	create_tween().tween_property(flash, "modulate:a", 0.0, 0.35)
	if note:
		note.text = Loc.t("photo_saved") if last_path != "" else Loc.t("photo_failed")
		note.modulate.a = 1.0
		var tw := create_tween()
		tw.tween_interval(2.0)
		tw.tween_property(note, "modulate:a", 0.0, 0.6)
