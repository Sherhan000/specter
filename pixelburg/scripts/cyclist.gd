class_name Cyclist
extends Node2D
## A cyclist riding along the streets, on the bike lane by the curb. Drawn by hand: bicycle and rider.

const SPEED := 0.8                 ## tiles per second
const LANE := 0.19                 ## distance from the middle of the street
const SHIRTS := [Color("e84a3a"), Color("2a8ad8"), Color("f4c040"), Color("3aa858"), Color("9a5ad8"), Color("f08a30")]
const SKIN := [Color("f2c8a0"), Color("d8a478"), Color("a8744a")]

var pts: Array[Vector2] = []       ## lane points, grid units
var tiles: Array[Vector2i] = []
var i := 1
var g := Vector2.ZERO
var dir := Vector2.RIGHT
var done := false
var shirt: Color = SHIRTS.pick_random()
var skin: Color = SKIN.pick_random()
var helmet: Color = SHIRTS.pick_random()
var _t := randf() * 10.0


func start(path: Array[Vector2i]) -> void:
	tiles = path
	var n := path.size()
	for k in n:
		var d := (Vector2(path[mini(k + 1, n - 1)]) - Vector2(path[maxi(k - 1, 0)])).normalized()
		pts.append(Vector2(path[k]) + Vector2(0.5, 0.5) + Vector2(-d.y, d.x) * LANE)
	g = pts[0]
	position = Iso.grid(g)
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.4)


func step(delta: float) -> void:
	if done:
		return
	_t += delta
	var left := SPEED * delta
	while left > 0.0 and i < pts.size():
		var to := pts[i] - g
		var l := to.length()
		if l <= left:
			g = pts[i]
			left -= l
			i += 1
			if i < tiles.size() and not Game.net.has(tiles[i]):
				finish()
				return
		else:
			dir = to / l
			g += dir * left
			left = 0.0
	if i >= pts.size():
		finish()
		return
	position = Iso.grid(g)
	queue_redraw()


func finish() -> void:
	done = true
	var tw := create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.4)
	tw.tween_callback(queue_free)


func _draw() -> void:
	var h := (Iso.grid(g + dir) - Iso.grid(g)).normalized()
	var night := Game.night_amount()
	var dark := Color(0.15, 0.15, 0.18)
	var rear := -h * 7.0 + Vector2(0, -3.5)
	var front := h * 7.0 + Vector2(0, -3.5)
	for wc in [rear, front]:
		draw_arc(wc, 3.6, 0.0, TAU, 14, dark, 1.3)
	var seat := -h * 2.5 + Vector2(0, -9.0)
	var bar := h * 5.0 + Vector2(0, -11.0)
	var crank := Vector2(0, -4.0)
	draw_polyline(PackedVector2Array([rear, seat, crank, rear]), helmet.darkened(0.2), 1.2)
	draw_line(seat, bar, helmet.darkened(0.2), 1.2)
	draw_line(bar, front, helmet.darkened(0.2), 1.2)
	# pedalling legs
	var ph := _t * 9.0
	var p1 := crank + Vector2(cos(ph), sin(ph)) * 2.2
	var p2 := crank - Vector2(cos(ph), sin(ph)) * 2.2
	var hip := seat + Vector2(0, -1.0)
	for p in [p2, p1]:
		var knee: Vector2 = (hip + p) * 0.5 + h * 2.5 + Vector2(0, -1.5)
		draw_polyline(PackedVector2Array([hip, knee, p]), Color("2a3a5a"), 2.0)
	# body leaning to the handlebar, head with a helmet
	var shoulder := hip + h * 4.0 + Vector2(0, -7.0)
	draw_line(hip, shoulder, shirt, 3.6)
	draw_line(shoulder, bar + Vector2(0, -0.5), skin, 1.4)
	var head := shoulder + h * 1.5 + Vector2(0, -3.5)
	draw_circle(head, 2.6, skin)
	draw_arc(head + Vector2(0, -0.6), 2.8, PI, TAU, 8, helmet, 2.0)
	if night > 0.3:
		draw_circle(front + Vector2(0, -3.0), 1.6, Color(1, 0.95, 0.7, night))
