class_name Backdrop
extends Node2D
## What lies beyond the horizon: the sky, mountain ranges, distant towns that light up at night
## and a treeline where the valley floor ends. Layers drift slower than the camera (parallax).

## texture, parallax (0 = fixed to the sky, 1 = moves with the world), offset of the strip
## bottom below the horizon, haze, valley mist
const LAYERS := [["mtn_far", 0.12, -40.0, 0.5, 0.6], ["mtn_mid", 0.22, -30.0, 0.36, 0.55], ["hills", 0.34, -20.0, 0.28, 0.4],
	["skyline", 0.4, -34.0, 0.36, 0.3], ["treeline", 0.55, 12.0, 0.2, 0.2]]

var city: Node
var sky: Polygon2D
var sky_mat: ShaderMaterial
var layers: Array[Sprite2D] = []
var mats: Array[ShaderMaterial] = []
var glow: Sprite2D
var horizon_y := 0.0


func _ready() -> void:
	z_index = -20
	horizon_y = Data.HORIZON * Iso.HY + 30.0
	sky_mat = ShaderMaterial.new()
	sky_mat.shader = load("res://shaders/sky.gdshader")
	sky_mat.set_shader_parameter("horizon_y", horizon_y)
	sky = Polygon2D.new()
	sky.polygon = PackedVector2Array([Vector2(-80000, horizon_y - 30000), Vector2(80000, horizon_y - 30000),
		Vector2(80000, horizon_y + 2000), Vector2(-80000, horizon_y + 2000)])
	sky.material = sky_mat
	add_child(sky)
	var far: Shader = load("res://shaders/far.gdshader")
	for l in LAYERS:
		var s := Sprite2D.new()
		s.texture = Assets.tex("sky/" + l[0])
		s.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
		s.region_enabled = true
		s.centered = false
		var m := ShaderMaterial.new()
		m.shader = far
		m.set_shader_parameter("amount", l[3])
		m.set_shader_parameter("mist", l[4])
		s.material = m
		mats.append(m)
		add_child(s)
		layers.append(s)
		if l[0] == "skyline":
			glow = Sprite2D.new()
			glow.texture = Assets.tex("sky/skyline_glow")
			glow.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
			glow.region_enabled = true
			glow.centered = false
			glow.material = Assets.glow_mat
			add_child(glow)


func _process(_delta: float) -> void:
	var cam: Camera2D = city.camera
	var z := cam.zoom.x
	var k := 1.5 / sqrt(maxf(z, 0.2))     # far things shrink less than the world when zooming out
	var view: Rect2 = city.view_rect()
	for i in layers.size():
		var s := layers[i]
		var tex_h := s.texture.get_height()
		var p: float = LAYERS[i][1]
		var w := view.size.x / k + 400.0
		s.scale = Vector2(k, k)
		var x0 := view.position.x - 200.0
		# the layer follows the camera by (1 - p): far ranges barely move on screen
		s.region_rect = Rect2((x0 - cam.position.x * (1.0 - p)) / k, 0, w, tex_h)
		s.position = Vector2(x0, horizon_y + LAYERS[i][2] * k - tex_h * k)
		if s.texture.resource_path.ends_with("skyline.png"):
			glow.scale = s.scale
			glow.region_rect = s.region_rect
			glow.position = s.position
	glow.modulate.a = Game.night_amount()


func set_colors(zenith: Color, hor: Color, night: float, tint: Color) -> void:
	sky_mat.set_shader_parameter("zenith", Vector3(zenith.r, zenith.g, zenith.b))
	sky_mat.set_shader_parameter("horizon_col", Vector3(hor.r, hor.g, hor.b))
	sky_mat.set_shader_parameter("stars", night)
	for m in mats:
		m.set_shader_parameter("haze", Vector3(hor.r, hor.g, hor.b))
		m.set_shader_parameter("tint", Vector3(tint.r, tint.g, tint.b))
