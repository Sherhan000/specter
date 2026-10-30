class_name DoorView
extends Node2D
## The front door of a building when someone walks in or out: the leaf (or two leaves of a wide
## door) swings into the house on its hinge, and the lit room behind it shows through the opening:
## floor, side wall, back wall and a ceiling lamp. At night the light spills onto the sidewalk.
## Everything is clipped to the opening painted on the facade, so the wall above hides the leaf.

const OPEN_TIME := 0.28
const CLOSE_TIME := 0.4
const MAX_ANGLE := 1.75              ## ~100 degrees: flat against the inner wall
const DOUBLE_W := 40.0               ## openings this wide (screen px) get two leaves
const GLASS_W := 30.0                ## ... and wide ones are glass doors

var a := Vector2.ZERO                ## bottom corners of the opening on the facade
var b := Vector2.ZERO
var up := Vector2.ZERO               ## bottom -> top of the opening
var inward := Vector2.ZERO           ## screen direction into the house, as long as the opening is wide
var double := false
var glass := false
var open_k := 0.0                    ## 0 closed .. 1 wide open
var angle := 0.0
var night := 0.0
var _left := 0.0
var _hole := PackedVector2Array()
var _spill: Polygon2D


func _init() -> void:
	_spill = Polygon2D.new()
	_spill.material = Assets.glow_mat
	_spill.visible = false
	add_child(_spill)
	set_process(false)
	visible = false


func has_opening() -> bool:
	return _hole.size() == 4


## Corners of the painted door: bottom-left, bottom-right and top-left (screen px, node space).
func setup(p_a: Vector2, p_b: Vector2, p_t: Vector2) -> void:
	a = p_a
	b = p_b
	up = Vector2(0, p_t.y - p_a.y)
	var u := b - a
	# into the house is the iso direction across the facade that goes up the screen
	inward = Vector2(u.x, -u.y) if u.y > 0.0 else Vector2(-u.x, u.y)
	if u.y == 0.0:
		inward = Vector2(0, -u.length() * 0.5)
	double = u.length() >= DOUBLE_W
	glass = u.length() >= GLASS_W
	_hole = PackedVector2Array([a, b, b + up, a + up])
	var out := -inward.normalized() * minf(u.length() * 0.6, 18.0)
	_spill.polygon = PackedVector2Array([a, b, b + out * 1.4 + (b - a) * 0.15, a + out * 1.4 - (b - a) * 0.15])
	_reset()


func clear() -> void:
	_hole = PackedVector2Array()
	_spill.polygon = PackedVector2Array()
	_reset()


func _reset() -> void:
	_left = 0.0
	open_k = 0.0
	angle = 0.0
	visible = false
	set_process(false)


## Keep the door open for this many seconds (a person passing through); repeated calls extend it.
func open(seconds := 1.4) -> void:
	if not has_opening():
		return
	_left = maxf(_left, seconds)
	visible = true
	set_process(true)


func _process(delta: float) -> void:
	step(delta, Game.light_level())


func step(delta: float, p_night: float) -> void:
	night = p_night
	_left = maxf(0.0, _left - delta)
	if _left > CLOSE_TIME:
		open_k = minf(1.0, open_k + delta / OPEN_TIME)
	else:
		open_k = maxf(0.0, open_k - delta / CLOSE_TIME)
	angle = MAX_ANGLE * smoothstep(0.0, 1.0, open_k)
	if open_k <= 0.0 and _left <= 0.0:
		_reset()
		return
	var s := sin(angle) / sin(MAX_ANGLE)
	_spill.visible = night > 0.05
	_spill.vertex_colors = PackedColorArray([Color(1, 0.8, 0.5, 0.42 * night * s), Color(1, 0.8, 0.5, 0.42 * night * s),
		Color(1, 0.8, 0.5, 0.0), Color(1, 0.8, 0.5, 0.0)])
	queue_redraw()


## Parts of a polygon that are seen through the opening.
func _clip(poly: PackedVector2Array) -> Array[PackedVector2Array]:
	return Geometry2D.intersect_polygons(poly, _hole)


func _fill(poly: PackedVector2Array, col: Color) -> void:
	for p in _clip(poly):
		if p.size() >= 3:
			draw_colored_polygon(p, col)


func _draw() -> void:
	if not has_opening() or open_k <= 0.0:
		return
	var u := b - a
	var depth := inward.normalized() * minf(u.length() * 0.75, 22.0)
	var lit := clampf(0.35 + night, 0.0, 1.0)
	# the room: back wall, the floor going in, the side wall that faces us
	var back := Color(0.4, 0.31, 0.26).lerp(Color(0.98, 0.74, 0.44), lit * 0.8)
	var floor_c := Color(0.62, 0.46, 0.3).lerp(Color(1.0, 0.86, 0.56), lit * 0.8)
	var side := Color(0.28, 0.22, 0.19).lerp(Color(0.72, 0.5, 0.3), lit * 0.8)
	draw_colored_polygon(_hole, back)
	_fill(PackedVector2Array([a, b, b + depth, a + depth]), floor_c)
	var e := a if u.y > 0.0 else b
	_fill(PackedVector2Array([e, e + depth, e + depth + up, e + up]), side)
	# a picture on the back wall, a rug, a ceiling lamp and its glow
	var mid := (a + b) * 0.5
	var pic := mid + depth + up * 0.5
	_fill(PackedVector2Array([pic - u * 0.16, pic + u * 0.16, pic + u * 0.16 + up * 0.22, pic - u * 0.16 + up * 0.22]),
		Color(0.36, 0.5, 0.42).lerp(Color(0.6, 0.66, 0.42), lit * 0.6))
	_fill(PackedVector2Array([mid - u * 0.22 + depth * 0.2, mid + u * 0.22 + depth * 0.2,
		mid + u * 0.22 + depth * 0.7, mid - u * 0.22 + depth * 0.7]), Color(0.62, 0.28, 0.22).lerp(Color(0.9, 0.42, 0.3), lit * 0.6))
	var lamp := mid + depth * 0.6 + up * 0.86
	_fill(_disc(lamp, maxf(2.5, u.length() * 0.18)), Color(1.0, 0.92, 0.7, 0.25 + 0.4 * lit))
	_fill(_disc(lamp, 1.2), Color(1.0, 0.97, 0.85))
	# the leaf (two halves for a wide door) swinging in on its hinge
	if double:
		_leaf(a, u * 0.5)
		_leaf(b, -u * 0.5)
	else:
		# hinged on the far jamb, so the open leaf lies against the wall we cannot see
		var f := b if e == a else a
		_leaf(f, a - b if f == b else u)


func _leaf(hinge: Vector2, w: Vector2) -> void:
	var d := inward.normalized() * w.length()
	var p := hinge + w * cos(angle) + d * sin(angle)
	var shade := 1.0 - 0.3 * sin(angle) - 0.55 * night
	var col := Color(0.62, 0.74, 0.82, 0.5) if glass else Color(0.46, 0.3, 0.19)
	col = Color(col.r * shade, col.g * shade, col.b * shade, col.a)
	var frame := Color(col.r * 0.6, col.g * 0.6, col.b * 0.6, 1.0)
	var leaf := PackedVector2Array([hinge, p, p + up, hinge + up])
	for part in _clip(leaf):
		if part.size() < 3:
			continue
		draw_colored_polygon(part, col)
		part.append(part[0])
		draw_polyline(part, frame, 1.0)
	# the handle, if it is still inside the opening
	var knob := hinge + (p - hinge) * 0.85 + up * 0.45
	if Geometry2D.is_point_in_polygon(knob, _hole):
		draw_circle(knob, 1.1, Color(0.85, 0.75, 0.45) * (1.0 - 0.5 * night))


func _disc(c: Vector2, r: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in 10:
		var t := TAU * i / 10.0
		pts.append(c + Vector2(cos(t) * r, sin(t) * r * 0.6))
	return pts
