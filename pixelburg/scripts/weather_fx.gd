class_name WeatherFx
extends Node
## Clouds and their shadows, rain, thunderstorms with lightning, snow, fog,
## and the seasonal look of the world (autumn leaves, snow cover, wet streets).

var city: Node
var layer: CanvasLayer
var rain: CPUParticles2D
var snow: CPUParticles2D
var flash: ColorRect
var fog: ColorRect
var clouds: Array[Sprite2D] = []
var _bolt_t := 5.0
var _splash_t := 0.0
var _snow_amt := 0.0
var _autumn_amt := 0.0
var _wet_amt := 0.0
var _storm := false


func _ready() -> void:
	layer = CanvasLayer.new()
	layer.layer = 5
	add_child(layer)
	rain = CPUParticles2D.new()
	rain.texture = Assets.tex("fx/rain")
	rain.amount = 260
	rain.lifetime = 0.9
	rain.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	rain.direction = Vector2(-0.22, 1)
	rain.spread = 3.0
	rain.gravity = Vector2.ZERO
	rain.initial_velocity_min = 900.0
	rain.initial_velocity_max = 1150.0
	rain.scale_amount_min = 1.4
	rain.scale_amount_max = 2.2
	rain.emitting = false
	layer.add_child(rain)
	snow = CPUParticles2D.new()
	snow.texture = Assets.tex("fx/snow_1")
	snow.amount = 220
	snow.lifetime = 7.0
	snow.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	snow.direction = Vector2(0.15, 1)
	snow.spread = 25.0
	snow.gravity = Vector2(6, 8)
	snow.initial_velocity_min = 60.0
	snow.initial_velocity_max = 110.0
	snow.scale_amount_min = 1.0
	snow.scale_amount_max = 2.6
	snow.emitting = false
	layer.add_child(snow)
	fog = ColorRect.new()
	fog.color = Color(0.85, 0.88, 0.92, 0.0)
	fog.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(fog)
	flash = ColorRect.new()
	flash.color = Color(0.9, 0.93, 1.0, 0.0)
	flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(flash)
	get_viewport().size_changed.connect(_fit)
	_fit()
	_spawn_clouds()
	Game.weather_changed.connect(func(_k): _apply())
	_apply()
	var s := Game.season
	_snow_amt = 1.0 if s == "winter" else 0.0
	_autumn_amt = 1.0 if s == "autumn" else 0.0


func _fit() -> void:
	var vp := get_viewport().get_visible_rect().size
	for p in [rain, snow]:
		p.position = Vector2(vp.x / 2 + 80, -30)
		p.emission_rect_extents = Vector2(vp.x * 0.7, 10)
	snow.lifetime = vp.y / 70.0
	fog.size = vp
	flash.size = vp


func _spawn_clouds() -> void:
	var r: Rect2 = city.view_rect().grow(2500.0)
	for i in 9:
		var s := Sprite2D.new()
		s.position = Vector2(randf_range(r.position.x, r.end.x), randf_range(r.position.y, r.end.y))
		city.sky.add_child(s)
		var c := Sprite2D.new()
		c.position = Vector2(-60, -300)
		c.z_index = 10
		s.add_child(c)
		clouds.append(s)
	_set_cloud_textures()


func _set_cloud_textures() -> void:
	for i in clouds.size():
		var s := clouds[i]
		if _storm:
			s.texture = Assets.tex("nature/storm_shadow_%d" % (i % 2))
			s.get_child(0).texture = Assets.tex("nature/storm_%d" % (i % 2))
		else:
			s.texture = Assets.tex("nature/cloud_shadow_%d" % (i % 4))
			s.get_child(0).texture = Assets.tex("nature/cloud_%d" % (i % 4))
		s.scale = Vector2(3.2, 3.2)


func _apply() -> void:
	var w := Game.weather
	var stormy := w in ["rain", "storm"]
	if stormy != _storm:
		_storm = stormy
		_set_cloud_textures()
	rain.emitting = stormy
	rain.amount = 360 if w == "storm" else 200
	snow.emitting = w == "snow"


func _process(delta: float) -> void:
	var w := Game.weather
	var vis_clouds := 9 if w in ["rain", "storm", "cloudy"] else 4 if w in ["clear", "snow"] else 6
	var bounds: Rect2 = city.view_rect().grow(2500.0)
	var zoomed_out := clampf((0.55 - city.camera.zoom.x) / 0.25, 0.0, 1.0)
	var night := Game.night_amount()
	var tint := Game.world_tint()
	for i in clouds.size():
		var s := clouds[i]
		s.visible = i < vis_clouds
		s.position += Vector2(45, 12) * delta * (2.0 if w == "storm" else 1.0)
		s.modulate.a = (1.0 - night * 0.6) * (1.3 if _storm else 1.0)
		var c: Sprite2D = s.get_child(0)
		c.modulate = Color(tint.r, tint.g, tint.b, (0.05 + 0.55 * zoomed_out) * (1.0 if not _storm else 1.3))
		# clouds drift around the camera: one that leaves the area comes back on the other side
		if not bounds.grow(800.0).has_point(s.position):
			if s.position.x > bounds.end.x:
				s.position = Vector2(bounds.position.x, randf_range(bounds.position.y, bounds.end.y))
			else:
				s.position = Vector2(randf_range(bounds.position.x, bounds.end.x), randf_range(bounds.position.y, bounds.end.y))
	# lightning
	if w == "storm":
		_bolt_t -= delta
		if _bolt_t <= 0.0:
			_bolt_t = randf_range(5.0, 14.0)
			_lightning()
	flash.color.a = move_toward(flash.color.a, 0.0, delta * 2.5)
	# fog
	fog.color.a = move_toward(fog.color.a, 0.32 if w == "fog" else 0.0, delta * 0.2)
	# puddle splashes on the ground around the camera
	if w in ["rain", "storm"]:
		_splash_t -= delta
		if _splash_t <= 0.0:
			_splash_t = 0.05 if w == "storm" else 0.09
			_splash()
	# seasons ease in slowly
	var s_name := Game.season
	_snow_amt = move_toward(_snow_amt, 1.0 if s_name == "winter" else 0.0, delta * 0.05)
	_autumn_amt = move_toward(_autumn_amt, 1.0 if s_name == "autumn" else 0.0, delta * 0.05)
	_wet_amt = move_toward(_wet_amt, 0.18 if w in ["rain", "storm"] else 0.0, delta * 0.1)
	Assets.set_season(_snow_amt, _autumn_amt, _wet_amt)


func _lightning() -> void:
	var view: Rect2 = city.view_rect()
	var bolt := Sprite2D.new()
	bolt.texture = Assets.tex("fx/lightning_%d" % (randi() % 3))
	bolt.centered = false
	bolt.offset = Vector2(-70, -420)
	bolt.scale = Vector2(2.4, 2.4)
	bolt.position = Vector2(randf_range(view.position.x, view.end.x), randf_range(view.position.y + view.size.y * 0.3, view.end.y))
	bolt.material = Assets.glow_mat
	city.top_fx.add_child(bolt)
	var tw := bolt.create_tween()
	tw.tween_property(bolt, "modulate:a", 0.0, 0.35).set_delay(0.12)
	tw.tween_callback(bolt.queue_free)
	flash.color.a = 0.55
	get_tree().create_timer(randf_range(0.3, 1.2)).timeout.connect(func(): Game.sfx("thunder", -2.0))


func _splash() -> void:
	var view: Rect2 = city.view_rect()
	var s := Sprite2D.new()
	s.texture = Assets.tex("fx/splash")
	s.hframes = 3
	s.scale = Vector2(2.5, 2.5)
	s.position = Vector2(randf_range(view.position.x, view.end.x), randf_range(view.position.y, view.end.y))
	s.modulate = Color(1, 1, 1, 0.7)
	city.pools.add_child(s)
	var tw := s.create_tween()
	tw.tween_property(s, "frame", 2, 0.25)
	tw.tween_callback(s.queue_free)
