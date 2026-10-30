class_name MetroView
extends Node2D
## The metro line: a tunnel running underground in a straight line from station to station (in the
## order they were built) and a train shuttling along it, seen faintly through the ground.

const SPEED := 1.6       ## tiles per second
const WAIT := 3.0        ## seconds at a station

var points: Array[Vector2] = []   ## station entrances, grid units
var _pos := 0.0                   ## distance along the line, tiles
var _dir := 1.0
var _wait := 0.0
var _len := 0.0


func refresh() -> void:
	points.clear()
	if Game.metro_open():
		for uid in Game.metro_stations():
			var b: Dictionary = Game.buildings[uid]
			points.append(Vector2(b.x + 0.5, b.y + 0.5))
	_len = 0.0
	for i in range(1, points.size()):
		_len += points[i].distance_to(points[i - 1])
	_pos = clampf(_pos, 0.0, _len)
	visible = points.size() >= 2
	queue_redraw()


## Grid position and direction of the train at a distance along the line.
func at(d: float) -> Array:
	for i in range(1, points.size()):
		var seg := points[i].distance_to(points[i - 1])
		if d <= seg or i == points.size() - 1:
			var t := clampf(d / maxf(seg, 0.001), 0.0, 1.0)
			return [points[i - 1].lerp(points[i], t), (points[i] - points[i - 1]).normalized()]
		d -= seg
	return [points[0], Vector2.RIGHT]


func _process(delta: float) -> void:
	if points.size() < 2:
		return
	if _wait > 0.0:
		_wait -= delta
		return
	var before := _pos
	_pos += _dir * SPEED * delta
	if _pos >= _len or _pos <= 0.0:
		_pos = clampf(_pos, 0.0, _len)
		_dir = -_dir
		_wait = WAIT
	else:
		# stop at the stations in between
		var acc := 0.0
		for i in range(1, points.size() - 1):
			acc += points[i].distance_to(points[i - 1])
			if (before - acc) * (_pos - acc) < 0.0:
				_pos = acc
				_wait = WAIT
	queue_redraw()


func _draw() -> void:
	if points.size() < 2:
		return
	var night := Game.night_amount()
	# the tunnel: a dark band with dashed rails, faint, under the ground
	for i in range(1, points.size()):
		var a := Iso.grid(points[i - 1])
		var b := Iso.grid(points[i])
		draw_line(a, b, Color(0.12, 0.1, 0.14, 0.28), 34.0)
		var n := int(a.distance_to(b) / 40.0)
		for k in n:
			var p0 := a.lerp(b, float(k) / n)
			var p1 := a.lerp(b, (k + 0.5) / n)
			draw_line(p0, p1, Color(0.85, 0.8, 0.7, 0.25), 3.0)
	for p in points:
		draw_circle(Iso.grid(p), 22.0, Color(0.85, 0.15, 0.15, 0.55))
		draw_circle(Iso.grid(p), 12.0, Color(1, 1, 1, 0.7))
	# the train: three cars, windows glowing at night
	var r := at(_pos)
	var g: Vector2 = r[0]
	var dir: Vector2 = r[1]
	for k in 3:
		var c0 := Iso.grid(g - dir * (0.32 * k + 0.02))
		var c1 := Iso.grid(g - dir * (0.32 * k + 0.3))
		draw_line(c0, c1, Color(0.82, 0.18, 0.16, 0.6), 22.0)
		draw_line(c0, c1, Color(0.95, 0.9, 0.6, 0.35 + 0.45 * night), 6.0)
