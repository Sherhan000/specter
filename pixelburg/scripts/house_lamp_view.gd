class_name HouseLampView
extends Node2D
## A lamp at the front door of a home, placed by the player (Game.place_house_lamp). Drawn with
## polygons on the wall next to the painted door, at the height of its top (right above the door
## a porch roof often covers the wall): "classic" is a black lantern hanging from a curled bracket,
## "modern" a box sconce shining up and down, "lantern" two round lights on both sides of the door.
## At night the glass glows and a pool of light lies on the porch (both through the shared night
## material, so the lamp costs nothing per frame).

var style := ""
var lights: Array[Vector2] = []      ## glowing points (node space)
var _walls: Array[Vector2] = []      ## where each lamp is fixed to the wall
var _out := Vector2.ZERO             ## off the wall, towards the street (unit)
var _along := Vector2.ZERO           ## along the facade, a -> b (unit)
var _s := 4.0                        ## size of a lamp in px
var _pool: Sprite2D


## a, b: bottom corners of the door; t: its top-left corner (all in the building node's space).
func setup(p_style: String, a: Vector2, b: Vector2, t: Vector2, pool_layer: Node2D, origin: Vector2) -> void:
	style = p_style
	var up := Vector2(0, t.y - a.y)
	var u := b - a
	_along = u.normalized() if u.length() > 0.01 else Vector2.RIGHT
	var inward := Vector2(u.x, -u.y) if u.y > 0.0 else Vector2(-u.x, u.y)
	if absf(u.y) < 0.01:
		inward = Vector2(0, -1)
	_out = -inward.normalized()
	_s = clampf(-up.y * 0.26, 3.5, 7.0)
	material = Assets.world_mat
	z_index = 1
	lights.clear()
	_walls.clear()
	match style:
		"modern":
			_walls.append(a - _along * _s * 0.9 + up * 0.78)
			lights.append(_walls[0] + _out * _s * 0.45)
		"lantern":
			for side in [-1.0, 1.0]:
				var w: Vector2 = (a if side < 0.0 else b) + _along * side * _s * 0.8 + up * 0.74
				_walls.append(w)
				lights.append(w + _out * _s * 0.75 + Vector2(0, -_s * 0.15))
		_:
			_walls.append(b + _along * _s * 0.9 + up * 0.9)
			lights.append(_walls[0] + _out * _s * 1.3 + Vector2(0, _s * 0.85))
	for p in lights:
		var h := Sprite2D.new()
		h.texture = Assets.tex("fx/lamp_head")
		h.position = p
		h.scale = Vector2.ONE * _s / 3.2
		h.material = Assets.night_mat
		h.modulate = Color(1.4, 1.25, 1.0, 1.0)
		h.z_index = 1
		add_child(h)
	_pool = Sprite2D.new()
	_pool.texture = Assets.tex("fx/light_pool")
	_pool.position = origin + (a + b) * 0.5 + _out * 16.0
	_pool.scale = Vector2(1.1, 1.1) if style != "lantern" else Vector2(1.3, 1.15)
	_pool.material = Assets.night_mat
	_pool.modulate = Color(1.5, 1.3, 1.0, 0.9)
	pool_layer.add_child(_pool)
	queue_redraw()


func free_all() -> void:
	if is_instance_valid(_pool):
		_pool.queue_free()
	queue_free()


func _exit_tree() -> void:
	if is_instance_valid(_pool):
		_pool.queue_free()


func _draw() -> void:
	var iron := Color(0.12, 0.11, 0.12)
	var glass := Color(1.0, 0.86, 0.5)
	var s := _s
	match style:
		"modern":
			# a box on the wall: dark plate, grey body, lit slits on top and bottom
			var w := _walls[0]
			var o := _out * s * 0.9
			var x := _along * s * 0.45
			var h := Vector2(0, s * 0.8)
			draw_colored_polygon(PackedVector2Array([w - x - h, w + x - h, w + x + h, w - x + h]), Color(0.2, 0.21, 0.24))
			draw_colored_polygon(PackedVector2Array([w - x - h + o, w + x - h + o, w + x + h + o, w - x + h + o]), Color(0.5, 0.52, 0.57))
			draw_colored_polygon(PackedVector2Array([w + x - h, w + x - h + o, w + x + h + o, w + x + h]), Color(0.36, 0.37, 0.42))
			draw_colored_polygon(PackedVector2Array([w - x - h, w + x - h, w + x - h + o, w - x - h + o]), Color(0.7, 0.72, 0.76))
			draw_line(w - x * 0.6 + o * 0.5 + h * 1.05, w + x * 0.6 + o * 0.5 + h * 1.05, glass, 1.2)
			draw_line(w - x * 0.6 + o * 0.5 - h * 1.05, w + x * 0.6 + o * 0.5 - h * 1.05, glass, 1.0)
		"lantern":
			for i in lights.size():
				var p := lights[i]
				draw_line(_walls[i], p, iron, 1.2)
				draw_circle(_walls[i], s * 0.25, iron)
				draw_circle(p, s * 0.55, glass)
				draw_arc(p, s * 0.55, 0.0, TAU, 12, Color(0.98, 0.96, 0.9, 0.8), 0.8)
				draw_colored_polygon(PackedVector2Array([p + Vector2(-s * 0.3, -s * 0.48), p + Vector2(s * 0.3, -s * 0.48),
					p + Vector2(0, -s * 0.8)]), iron)
		_:
			# a curled bracket off the wall and a little black lantern hanging from it
			var w := _walls[0]
			var p := lights[0]
			var tip := w + _out * s * 1.3
			draw_line(w + Vector2(0, -s * 0.6), w + Vector2(0, s * 0.6), iron, 1.6)
			draw_line(w, tip, iron, 1.3)
			draw_arc(w.lerp(tip, 0.45) + Vector2(0, s * 0.35), s * 0.3, 0.0, TAU, 8, iron, 0.9)
			draw_line(tip, p + Vector2(0, -s * 0.95), iron, 1.0)
			var hw := s * 0.42
			draw_colored_polygon(PackedVector2Array([p + Vector2(-hw, -s * 0.5), p + Vector2(hw, -s * 0.5),
				p + Vector2(hw * 0.8, s * 0.5), p + Vector2(-hw * 0.8, s * 0.5)]), glass)
			draw_colored_polygon(PackedVector2Array([p + Vector2(-hw * 1.35, -s * 0.5), p + Vector2(hw * 1.35, -s * 0.5),
				p + Vector2(0, -s * 0.95)]), iron)
			draw_colored_polygon(PackedVector2Array([p + Vector2(-hw, s * 0.5), p + Vector2(hw, s * 0.5),
				p + Vector2(hw * 0.5, s * 0.8), p + Vector2(-hw * 0.5, s * 0.8)]), iron)
			draw_line(p + Vector2(0, -s * 0.5), p + Vector2(0, s * 0.5), Color(iron, 0.6), 0.7)
