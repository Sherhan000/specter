class_name DisasterFx
extends Node2D
## What a natural event looks like in the city: flood water creeping over the land near rivers and seas, cracks
## in the ground and a shaking camera for an earthquake, deep snow and a thick snowfall in a blizzard.
## (Tourist crowds are people, see Tourist and Life.) Drawn under the buildings; redrawn a few times a second.

const MAX_TILES := 1400

var city: Node
var layer: CanvasLayer
var snow: CPUParticles2D
var _flood: Array = []           ## Vector2i tiles under water, with the radius they were built for
var _flood_r := -1
var _flood_n := -1
var _snow_tiles: Array = []
var _snow_key := -1
var _t := 0.0
var _redraw_t := 0.0


func _ready() -> void:
	z_index = -5
	layer = CanvasLayer.new()
	layer.layer = 6
	add_child(layer)
	snow = CPUParticles2D.new()
	snow.texture = Assets.tex("fx/snow_1")
	snow.amount = 380
	snow.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	snow.direction = Vector2(0.7, 1)
	snow.spread = 18.0
	snow.gravity = Vector2(40, 20)
	snow.initial_velocity_min = 240.0
	snow.initial_velocity_max = 380.0
	snow.scale_amount_min = 1.2
	snow.scale_amount_max = 3.0
	snow.emitting = false
	layer.add_child(snow)
	get_viewport().size_changed.connect(_fit)
	_fit()
	Game.disaster_changed.connect(_on_changed)
	_refresh()


func _fit() -> void:
	var vp := get_viewport().get_visible_rect().size
	snow.position = Vector2(vp.x * 0.4, -10)
	snow.emission_rect_extents = Vector2(vp.x * 0.8, 10)
	snow.lifetime = vp.y / 220.0


func _on_changed(state: String) -> void:
	_refresh()
	if state == "start" and Game.disaster_kind() == "quake":
		shake(2.5, 14.0)
	elif state == "hit" and Game.disaster_kind() == "quake":
		shake(1.5, 10.0)


## The camera trembles for a few seconds.
func shake(secs: float, power: float) -> void:
	if city == null or city.camera == null:
		return
	var cam: Camera2D = city.camera
	var tw := create_tween()
	var steps := int(secs * 20.0)
	for i in steps:
		var k := 1.0 - float(i) / steps
		tw.tween_property(cam, "offset", Vector2(randf_range(-1, 1), randf_range(-1, 1)) * power * k, 0.05)
	tw.tween_property(cam, "offset", Vector2.ZERO, 0.1)


## How far the water has come (tiles from the shore) – it rises while the mayor decides.
func flood_radius() -> int:
	if Game.disaster_kind() != "flood":
		return 0
	var now := Game.abs_hour()
	if str(Game.disaster.phase) == "threat":
		var el := clampf(1.0 - float(int(Game.disaster.ends) - now) / Data.DZ_HOURS, 0.0, 1.0)
		return 1 + int(el * 2.0)
	if str(Game.disaster.phase) == "after":
		if not bool(Game.disaster.hit):
			return 1 if int(Game.disaster.ends) - now > Data.DZ_AFTER / 2 else 0
		return 3 if int(Game.disaster.ends) - now > Data.DZ_AFTER / 2 else 2
	return 0


func snow_amount() -> float:
	if Game.disaster_kind() != "blizzard":
		return 0.0
	if str(Game.disaster.phase) == "threat":
		return 1.0
	return (0.8 if bool(Game.disaster.hit) else 0.45) * clampf(float(int(Game.disaster.ends) - Game.abs_hour()) / Data.DZ_AFTER + 0.3, 0.0, 1.0)


func _refresh() -> void:
	var r := flood_radius()
	if r != _flood_r or Game.water.size() != _flood_n:
		_flood_r = r
		_flood_n = Game.water.size()
		_flood = []
		if r > 0:
			var seen := {}
			for w in Game.water:
				for dy in range(-r, r + 1):
					for dx in range(-r, r + 1):
						var c: Vector2i = w + Vector2i(dx, dy)
						if absi(dx) + absi(dy) <= r + 1 and not Game.water.has(c) and not seen.has(c) \
								and c.x >= 0 and c.y >= 0 and c.x < Data.MAP and c.y < Data.MAP:
							seen[c] = true
							_flood.append(c)
							if _flood.size() >= MAX_TILES:
								break
			_flood.shuffle()
	var sa := snow_amount()
	snow.emitting = sa > 0.05
	snow.modulate.a = clampf(sa, 0.2, 1.0)
	var key := int(sa * 10.0) + Game.buildings.size() * 100 + Game.net.size() * 7
	if key != _snow_key:
		_snow_key = key
		_snow_tiles = []
		if sa > 0.05:
			for c in Game.net:
				_snow_tiles.append(c)
			for uid in Game.buildings:
				var b: Dictionary = Game.buildings[uid]
				var n := int(Data.B[b.id].size)
				for dy in n:
					for dx in n:
						_snow_tiles.append(Vector2i(b.x + dx, b.y + dy))
			_snow_tiles = _snow_tiles.slice(0, MAX_TILES * 2)
	queue_redraw()


func _process(delta: float) -> void:
	_t += delta
	_redraw_t -= delta
	if _redraw_t <= 0.0:
		_redraw_t = 0.25
		if Game.disaster_active() or not _flood.is_empty() or not _snow_tiles.is_empty():
			_refresh()


static func _diamond(c: Vector2i, inset := 0.0) -> PackedVector2Array:
	var x0 := c.x + inset
	var y0 := c.y + inset
	var x1 := c.x + 1.0 - inset
	var y1 := c.y + 1.0 - inset
	return PackedVector2Array([Iso.vertex(x0, y0), Iso.vertex(x1, y0), Iso.vertex(x1, y1), Iso.vertex(x0, y1)])


func _draw() -> void:
	# ---- flood water with moving ripples
	for c in _flood:
		var ph := sin(_t * 2.0 + c.x * 0.9 + c.y * 1.3)
		draw_colored_polygon(_diamond(c, 0.04), Color(0.2, 0.46, 0.74, 0.42 + 0.06 * ph))
		if (c.x * 7 + c.y * 3) % 3 == 0:
			var m := Iso.center(c) + Vector2(ph * 18.0, 0)
			draw_line(m - Vector2(34, 0), m + Vector2(34, 0), Color(0.85, 0.95, 1.0, 0.45), 4.0)
	# ---- earthquake cracks around the buildings in danger / damaged
	if Game.disaster_kind() == "quake" and (str(Game.disaster.phase) == "threat" or bool(Game.disaster.hit)):
		for uid in Game.disaster.uids:
			if not Game.buildings.has(uid):
				continue
			var b: Dictionary = Game.buildings[uid]
			var n := float(Data.B[b.id].size)
			var rng := RandomNumberGenerator.new()
			rng.seed = int(uid) * 7919 + 13
			for k in 3:
				var p := Vector2(b.x + rng.randf_range(-0.3, n + 0.3), b.y + rng.randf_range(-0.3, n + 0.3))
				var pts := PackedVector2Array()
				var dir := Vector2.from_angle(rng.randf() * TAU)
				for s in 7:
					pts.append(Iso.grid(p))
					dir = dir.rotated(rng.randf_range(-0.9, 0.9))
					p += dir * rng.randf_range(0.18, 0.4)
				draw_polyline(pts, Color(0.1, 0.07, 0.06, 0.85), 7.0)
				draw_polyline(pts, Color(0.25, 0.2, 0.17, 0.9), 3.0)
	# ---- snow cover
	var sa := snow_amount()
	if sa > 0.05:
		for c in _snow_tiles:
			draw_colored_polygon(_diamond(c, 0.06), Color(0.93, 0.96, 1.0, 0.5 * sa))
