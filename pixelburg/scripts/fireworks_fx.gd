class_name FireworksFx
extends Node2D
## Weekend fireworks over the main square: on the 6th and 7th day of every week, 20:00-23:00, rockets fly up over
## plazas, fountains and the town hall and burst into coloured sparks (drawn additively above the city).

const COLORS := [Color("ff4060"), Color("ffd040"), Color("40d0ff"), Color("80ff60"), Color("e060ff"), Color("ffffff")]

var city: Node
var _shots: Array = []     ## {pos, t, col, seed, kind}
var _next := 0.0
var _spots: Array = []
var _spots_n := -1


static func is_weekend(day: int) -> bool:
	return day % 7 == 6 or day % 7 == 0


static func active(day: int, hour: int) -> bool:
	return is_weekend(day) and hour >= 20 and hour < 23


func _ready() -> void:
	z_index = 400
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	material = m


func _find_spots() -> void:
	if _spots_n == Game.buildings.size():
		return
	_spots_n = Game.buildings.size()
	_spots.clear()
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if b.id in ["plaza", "fountain", "town_hall"] and b.built:
			var sz: int = Data.B[b.id].size
			_spots.append(Iso.vertex(b.x + sz * 0.5, b.y + sz * 0.5))


func burst(at: Vector2) -> void:
	_shots.append({"pos": at, "t": 0.0, "col": COLORS[randi() % COLORS.size()], "seed": randi(), "kind": randi() % 3})


func _process(delta: float) -> void:
	var on := active(Game.day, Game.hour()) and Game.phase != "day"
	if on:
		_find_spots()
		_next -= delta
		if _next <= 0.0 and not _spots.is_empty():
			var s: Vector2 = _spots[randi() % _spots.size()]
			burst(s + Vector2(randf_range(-70, 70), -randf_range(160, 260)))
			_next = randf_range(0.5, 1.6)
	for s in _shots:
		s.t += delta
	_shots = _shots.filter(func(s): return s.t < 2.0)
	if on or not _shots.is_empty():
		queue_redraw()


func _draw() -> void:
	for s in _shots:
		var t: float = s.t
		var rng := RandomNumberGenerator.new()
		rng.seed = s.seed
		var n := 34 if s.kind != 1 else 22
		var fade := clampf(1.4 - t * 0.7, 0.0, 1.0)
		for i in n:
			var a := TAU * i / n + rng.randf() * 0.2
			var sp := rng.randf_range(0.6, 1.0) * (170.0 if s.kind != 2 else 220.0)
			var d := Vector2(cos(a), sin(a)) * sp * (1.0 - exp(-t * 2.6)) * 1.0
			d.y += 40.0 * t * t
			var col: Color = s.col if (s.kind != 1 or i % 2 == 0) else Color.WHITE
			col.a = fade
			draw_circle(s.pos + d, 3.4 if t < 1.0 else 2.4, col)
			draw_circle(s.pos + d - Vector2(cos(a), sin(a)) * 5.0, 1.2, Color(col.r, col.g, col.b, fade * 0.5))
