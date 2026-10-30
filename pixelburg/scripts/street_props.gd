class_name StreetProps
extends Node
## Walls the player builds (stone or brick, joining up with their neighbours) and the decoration
## along improved streets (iron railings, flower pots, bollards). One small drawn node per tile.

const DIRS := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]

var city: Node
var pieces := {}    ## "w" / "d" + tile -> node


func refresh() -> void:
	for k in pieces:
		if is_instance_valid(pieces[k]):
			pieces[k].queue_free()
	pieces.clear()
	for c in Game.walls:
		var w := WallPiece.new()
		w.type = Game.walls[c]
		for k in 4:
			if Game.walls.has(c + DIRS[k]):
				w.arms |= 1 << k
		w.position = Iso.center(c)
		city.world.add_child(w)
		pieces["w%s" % c] = w
	for c in Game.road_deco:
		if not Game.roads.has(c):
			continue
		var a := 0
		for k in 4:
			if Game.net.has(c + DIRS[k]):
				a |= 1 << k
		if a != 5 and a != 10:
			continue   # decoration only along straight stretches, so crossings stay open
		var d := DecoPiece.new()
		d.type = Game.road_deco[c]
		d.axis_x = a == 10
		d.position = Iso.center(c)
		city.world.add_child(d)
		pieces["d%s" % c] = d


## Draws an axis-aligned box given in grid units around the tile centre (z in pixels).
static func box(n: CanvasItem, x0: float, y0: float, x1: float, y1: float, h: float, col: Color, z0 := 0.0) -> void:
	var p := func(x: float, y: float, z: float) -> Vector2: return Iso.grid(Vector2(x, y)) - Vector2(0, z)
	# the two faces turned to the viewer, then the top
	n.draw_colored_polygon(PackedVector2Array([p.call(x0, y1, z0), p.call(x1, y1, z0), p.call(x1, y1, z0 + h), p.call(x0, y1, z0 + h)]),
		col.darkened(0.12))
	n.draw_colored_polygon(PackedVector2Array([p.call(x1, y0, z0), p.call(x1, y1, z0), p.call(x1, y1, z0 + h), p.call(x1, y0, z0 + h)]),
		col.darkened(0.28))
	n.draw_colored_polygon(PackedVector2Array([p.call(x0, y0, z0 + h), p.call(x1, y0, z0 + h), p.call(x1, y1, z0 + h), p.call(x0, y1, z0 + h)]),
		col.lightened(0.12))


class WallPiece extends Node2D:
	var type := "stone"
	var arms := 0

	func _draw() -> void:
		var stone := type == "stone"
		var col := Color("a8a294") if stone else Color("b0583a")
		var h := 22.0 if stone else 18.0
		var t := 0.07
		var segs: Array = []
		if arms & 1:
			segs.append([-t, -0.5, t, 0.0])
		if arms & 8:
			segs.append([-0.5, -t, 0.0, t])
		if arms & 2:
			segs.append([0.0, -t, 0.5, t])
		if arms & 4:
			segs.append([-t, 0.0, t, 0.5])
		if segs.is_empty():
			segs.append([-0.35, -t, 0.35, t])
		# segments behind the post first, then the post where the wall turns or ends, then the ones in front
		for pass_front in [false, true]:
			for s in segs:
				if (s[2] > 0.01 or s[3] > 0.01) == pass_front:
					StreetProps.box(self, s[0], s[1], s[2], s[3], h, col)
					_joints(s, h)
					StreetProps.box(self, s[0] - 0.01, s[1] - 0.01, s[2] + 0.01, s[3] + 0.01, 2.0, Color("d8d2c4") if stone else Color("c8c0b0"), h)
			if not pass_front:
				StreetProps.box(self, -t * 1.5, -t * 1.5, t * 1.5, t * 1.5, h + 5.0, col.lightened(0.05))

	func _joints(s: Array, h: float) -> void:
		var line := Color(0, 0, 0, 0.18) if type == "stone" else Color(0.92, 0.88, 0.8, 0.5)
		var step := 6.0 if type == "stone" else 4.0
		var z := step
		while z < h - 1.0:
			var a := Iso.grid(Vector2(s[0], s[3])) - Vector2(0, z)
			var b := Iso.grid(Vector2(s[2], s[3])) - Vector2(0, z)
			draw_line(a, b, line, 1.0)
			z += step


class DecoPiece extends Node2D:
	var type := "railing"
	var axis_x := true

	func _draw() -> void:
		# along both outer edges of the sidewalks
		for side in [-0.46, 0.46]:
			var a := Vector2(-0.5, side) if axis_x else Vector2(side, -0.5)
			var b := Vector2(0.5, side) if axis_x else Vector2(side, 0.5)
			match type:
				"railing":
					var n := 10
					for i in n + 1:
						var p := Iso.grid(a.lerp(b, float(i) / n))
						draw_line(p, p - Vector2(0, 10), Color("2a2c34"), 1.4)
						if i % 2 == 0:
							draw_circle(p - Vector2(0, 11), 1.2, Color("c8a040"))
					draw_line(Iso.grid(a) - Vector2(0, 10), Iso.grid(b) - Vector2(0, 10), Color("2a2c34"), 1.8)
					draw_line(Iso.grid(a) - Vector2(0, 3), Iso.grid(b) - Vector2(0, 3), Color("2a2c34"), 1.2)
				"planters":
					for i in 3:
						var m: Vector2 = a.lerp(b, 0.2 + 0.3 * i)
						var d := (b - a).normalized() * 0.06
						var w := Vector2(-d.y, d.x) * 0.6
						StreetProps.box(self, minf(m.x - d.x - w.x, m.x + d.x + w.x), minf(m.y - d.y - w.y, m.y + d.y + w.y),
							maxf(m.x - d.x - w.x, m.x + d.x + w.x), maxf(m.y - d.y - w.y, m.y + d.y + w.y), 6.0, Color("8a6a4a"))
						var top := Iso.grid(m) - Vector2(0, 8)
						draw_circle(top, 5.0, Color("4a8a3a"))
						var cols := [Color("e84a5a"), Color("f4c040"), Color("f6f0f4"), Color("b45ad8")]
						for j in 4:
							draw_circle(top + Vector2(cos(j * 1.7) * 3.0, sin(j * 1.7) * 2.0 - 1.0), 1.4, cols[(i + j) % 4])
				"bollards":
					for i in 4:
						var p := Iso.grid(a.lerp(b, 0.125 + 0.25 * i))
						draw_line(p, p - Vector2(0, 7), Color("5a5c62"), 3.0)
						draw_line(p - Vector2(0, 5), p - Vector2(0, 6), Color("f4f4f4"), 3.0)
						draw_circle(p - Vector2(0, 7), 1.5, Color("6a6c72"))
