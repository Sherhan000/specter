class_name RingView
extends Node2D
## Roundabout on a crossing. The flat part (cobbled apron, red-and-white curb, the grass island
## with flowers and the give-way teeth at each entry) lies on the decal layer under the traffic;
## the fountain in the middle stands in the sorted world, so cars behind it pass behind it.
## Drawn with polygons, no textures; cars follow Life.ring_segment around it.

const APRON := 0.215    ## island sizes in tiles, from the tile centre
const CURB := 0.175
const GRASS := 0.16
const TEETH := 0.37     ## give-way line: distance of the entry from the centre

var tile := Vector2i.ZERO
var part := "base"


static func make(p_tile: Vector2i, decal_layer: Node2D, world_layer: Node2D) -> Array:
	var out := []
	for k in ["base", "top"]:
		var v := RingView.new()
		v.tile = p_tile
		v.part = k
		v.position = Iso.center(p_tile)
		v.material = Assets.world_mat
		(decal_layer if k == "base" else world_layer).add_child(v)
		out.append(v)
	return out


func _draw() -> void:
	if part == "base":
		_draw_base()
	else:
		_draw_top()


static func _e(r: float, a: float, lift := 0.0) -> Vector2:
	return Iso.grid_vec(Vector2(cos(a), sin(a)) * r) - Vector2(0, lift)


static func _ellipse(r: float, lift := 0.0, n := 32) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in n:
		pts.append(_e(r, TAU * i / n, lift))
	return pts


func _draw_base() -> void:
	# cobbled apron the long trucks may roll over
	draw_colored_polygon(_ellipse(APRON), Color("8e8a82"))
	for i in 28:
		var a := TAU * i / 28.0
		draw_circle(_e(APRON - 0.022, a + 0.05), 3.0, Color("7a766e"))
	# the island stands a little higher: a dark side, then red-and-white curb stones
	draw_colored_polygon(_ellipse(CURB), Color("5e5a54"))
	for i in 16:
		var a0 := TAU * i / 16.0
		var a1 := TAU * (i + 1) / 16.0
		var seg := PackedVector2Array([_e(CURB, a0, 2.0), _e(CURB, a1, 2.0), _e(CURB, a1), _e(CURB, a0)])
		draw_colored_polygon(seg, Color("d8473a") if i % 2 == 0 else Color("f0eee8"))
	draw_colored_polygon(_ellipse(CURB, 3.0), Color("e6e2da"))
	draw_colored_polygon(_ellipse(GRASS, 3.0), Color("5f9a3e"))
	draw_colored_polygon(_ellipse(GRASS * 0.75, 3.0), Color("6cab47"))
	var flowers := [Color("f2d24a"), Color("e8607a"), Color("f4f0f4"), Color("c86ad8")]
	for i in 14:
		var a := TAU * i / 14.0 + 0.2
		draw_circle(_e(GRASS * (0.62 + 0.22 * (i % 2)), a, 3.0), 2.6, flowers[i % flowers.size()])
	# give-way teeth across each incoming lane, pointing at the waiting driver
	for d in Life.ARM_DIRS:
		if not Game.net.has(tile + d):
			continue
		var arm := Vector2(d)
		var din := -arm
		var side := Vector2(-din.y, din.x)
		for k in 4:
			var w := 0.035 + k * 0.05
			var b0 := arm * TEETH + side * (w - 0.017)
			var b1 := arm * TEETH + side * (w + 0.017)
			var tip := arm * (TEETH + 0.04) + side * w
			draw_colored_polygon(PackedVector2Array([Iso.grid_vec(b0), Iso.grid_vec(b1), Iso.grid_vec(tip)]), Color("f4f2ea"))


func _draw_top() -> void:
	# a small stone fountain on the island
	var lift := 3.0
	var r := 0.085
	var basin_h := 7.0
	# the front half of the basin wall faces the camera (grid direction +x +y)
	var side := PackedVector2Array()
	for i in 17:
		side.append(_e(r, -PI / 4.0 + PI * i / 16.0, lift))
	for i in 17:
		side.append(_e(r, 3.0 * PI / 4.0 - PI * i / 16.0, lift + basin_h))
	draw_colored_polygon(_ellipse(r, lift), Color("8a8478"))
	draw_colored_polygon(side, Color("a49c8e"))
	draw_colored_polygon(_ellipse(r, lift + basin_h), Color("c8c0b0"))
	draw_colored_polygon(_ellipse(r * 0.8, lift + basin_h), Color("4f9ac8"))
	draw_colored_polygon(_ellipse(r * 0.45, lift + basin_h, 16), Color("7cc0e6"))
	# the column with a bowl and a jet of water
	var top := lift + basin_h
	draw_rect(Rect2(-2.5, -top - 16.0, 5.0, 16.0), Color("b4ac9c"))
	draw_rect(Rect2(-2.5, -top - 16.0, 2.0, 16.0), Color("cdc6b8"))
	var bowl := PackedVector2Array([Vector2(-9, -top - 16), Vector2(9, -top - 16), Vector2(5, -top - 12), Vector2(-5, -top - 12)])
	draw_colored_polygon(bowl, Color("c8c0b0"))
	draw_line(Vector2(0, -top - 17), Vector2(0, -top - 25), Color(0.75, 0.9, 1.0, 0.9), 2.0)
	draw_circle(Vector2(0, -top - 26), 2.4, Color(0.85, 0.95, 1.0, 0.85))
	for sx in [-1.0, 1.0]:
		draw_line(Vector2(sx * 8, -top - 16), Vector2(sx * 12, -top - 4), Color(0.7, 0.88, 1.0, 0.7), 1.5)
