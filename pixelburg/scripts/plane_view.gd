class_name PlaneView
extends Node2D
## An airliner that glides down over the airport, rolls along the runway and taxis away (fades out).
## Drawn with polygons; the shadow on the ground shrinks towards the plane as it lands.

const APPROACH := 9.0   ## seconds in the air
const ROLL := 4.0       ## seconds on the runway
const ALT := 520.0      ## start height, px
const GX := Vector2(Iso.HX, Iso.HY)    ## one tile along grid x
const GY := Vector2(-Iso.HX, Iso.HY)   ## one tile along grid y

var from := Vector2.ZERO   ## grid point where the approach starts
var touch := Vector2.ZERO  ## touchdown point
var stop := Vector2.ZERO   ## where it slows down
var tail := Color("2a6ab8")
var t := 0.0
var alt := ALT


func setup(center: Vector2, tail_col: Color) -> void:
	touch = center + Vector2(-1.0, 0.6)
	from = touch + Vector2(-16.0, 0.0)
	stop = center + Vector2(1.4, 0.6)
	tail = tail_col
	z_index = 30
	_place()


func _process(delta: float) -> void:
	t += delta
	_place()
	queue_redraw()
	if t > APPROACH + ROLL + 1.0:
		queue_free()


func _place() -> void:
	var g: Vector2
	if t < APPROACH:
		var k := t / APPROACH
		g = from.lerp(touch, k)
		alt = ALT * pow(1.0 - k, 1.6)
	else:
		var k := clampf((t - APPROACH) / ROLL, 0.0, 1.0)
		g = touch.lerp(stop, 1.0 - pow(1.0 - k, 2.0))
		alt = 0.0
	position = Iso.grid(g)
	modulate.a = clampf(t / 0.8, 0.0, 1.0) * clampf(APPROACH + ROLL + 1.0 - t, 0.0, 1.0)


func _p(u: float, v: float, up := 0.0) -> Vector2:
	return GX * u + GY * v + Vector2(0, -alt - up)


func _poly(pts: Array, col: Color) -> void:
	draw_colored_polygon(PackedVector2Array(pts), col)


func _draw() -> void:
	var sh := Color(0, 0, 0, 0.18 * (1.0 - alt / ALT * 0.6))
	var a := alt
	alt = 0.0
	_poly([_p(-0.55, -0.04), _p(0.6, -0.04), _p(0.6, 0.04), _p(-0.55, 0.04)], sh)
	_poly([_p(-0.05, -0.45), _p(0.12, -0.04), _p(0.12, 0.04), _p(-0.05, 0.45), _p(-0.15, 0.45), _p(-0.08, 0.0), _p(-0.15, -0.45)], sh)
	alt = a
	var body := Color("f4f4f2")
	var wing := Color("d4d6d8")
	_poly([_p(-0.05, -0.45, 6), _p(0.12, -0.05, 6), _p(0.12, 0.05, 6), _p(-0.05, 0.45, 6), _p(-0.15, 0.45, 6), _p(-0.08, 0.0, 6), _p(-0.15, -0.45, 6)], wing)
	_poly([_p(-0.5, -0.18, 14), _p(-0.4, -0.03, 14), _p(-0.4, 0.03, 14), _p(-0.5, 0.18, 14), _p(-0.56, 0.18, 14), _p(-0.56, -0.18, 14)], wing)
	for v in [-0.2, 0.2]:
		_poly([_p(0.02, v - 0.03, 0), _p(0.12, v - 0.03, 0), _p(0.12, v + 0.03, 0), _p(0.02, v + 0.03, 0)], Color("a8acb0"))
	_poly([_p(-0.55, -0.05, 4), _p(0.55, -0.05, 4), _p(0.62, 0.0, 8), _p(0.55, 0.05, 4), _p(0.55, 0.05, 16), _p(-0.55, 0.05, 16), _p(-0.55, -0.05, 16)], body)
	_poly([_p(-0.45, 0.05, 10), _p(0.45, 0.05, 10), _p(0.45, 0.05, 12), _p(-0.45, 0.05, 12)], tail)
	_poly([_p(0.5, 0.05, 11), _p(0.56, 0.05, 11), _p(0.56, 0.05, 15), _p(0.5, 0.05, 15)], Color("3a4a5a"))
	_poly([_p(-0.56, 0.0, 14), _p(-0.4, 0.0, 14), _p(-0.5, 0.0, 44), _p(-0.6, 0.0, 44)], tail)
