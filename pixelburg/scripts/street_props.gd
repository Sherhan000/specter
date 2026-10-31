class_name StreetProps
extends Node
## Walls the player builds (stone, brick, plastered quarter walls and roofed arch passages, joining up with
## their neighbours and running into the buildings beside them) and the decoration along improved streets
## (iron railings, flower pots, bollards). One small drawn node per tile.

const DIRS := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]

var city: Node
var pieces := {}    ## "w" / "d" + tile -> node
var _queued := false


## Buildings moved next to walls: rebuild once at the end of the frame.
func refresh_soon(_uid := 0) -> void:
	if not _queued and not Game.walls.is_empty():
		_queued = true
		refresh.call_deferred()


func refresh() -> void:
	_queued = false
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
			elif Game.occ.has(c + DIRS[k]):
				w.arms |= 1 << k   # runs on into the building's side
				w.touch |= 1 << k
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
	const LOOK := {   ## wall colour, height, half thickness, cap colour, cap height
		"stone": [Color("a8a294"), 22.0, 0.07, Color("d8d2c4"), 2.0],
		"brick": [Color("b0583a"), 18.0, 0.07, Color("c8c0b0"), 2.0],
		"plaster": [Color("e6d8bc"), 24.0, 0.08, Color("b4583a"), 3.5],
		"arch": [Color("dcc8a0"), 34.0, 0.17, Color("a84e34"), 0.0],
	}
	var type := "stone"
	var arms := 0
	var touch := 0   ## arms that end at a building rather than at another wall
	const INTO := 0.14

	func _draw() -> void:
		var look: Array = LOOK.get(type, LOOK.stone)
		var col: Color = look[0]
		var h: float = look[1]
		var t: float = look[2]
		if type == "arch" and (arms == 5 or arms == 10):
			_arch(arms == 10, col, h, t)
			return
		if type == "arch":
			h = 26.0   # corners and ends of an arch line are plain plastered walls
			t = 0.09
		var segs: Array = []
		if arms & 1:
			segs.append([-t, -0.5 - _into(1), t, 0.0])
		if arms & 8:
			segs.append([-0.5 - _into(8), -t, 0.0, t])
		if arms & 2:
			segs.append([0.0, -t, 0.5 + _into(2), t])
		if arms & 4:
			segs.append([-t, 0.0, t, 0.5 + _into(4)])
		if segs.is_empty():
			segs.append([-0.35, -t, 0.35, t])
		# segments behind the post first, then the post where the wall turns or ends, then the ones in front
		for pass_front in [false, true]:
			for s in segs:
				if (s[2] > 0.01 or s[3] > 0.01) == pass_front:
					StreetProps.box(self, s[0], s[1], s[2], s[3], h, col)
					_joints(s, h)
					_cap(s, h, look)
			if not pass_front and (type in ["stone", "brick"] or arms not in [5, 10]):
				StreetProps.box(self, -t * 1.5, -t * 1.5, t * 1.5, t * 1.5, h + 5.0, col.lightened(0.05))

	## How far an arm reaches on into the plot of the building it meets, so it joins the house itself.
	func _into(bit: int) -> float:
		return INTO if touch & bit else 0.0

	func _cap(s: Array, h: float, look: Array) -> void:
		if type in ["stone", "brick"]:
			StreetProps.box(self, s[0] - 0.01, s[1] - 0.01, s[2] + 0.01, s[3] + 0.01, look[4], look[3], h)
			return
		# plinth at the foot and a tiled top a little wider than the wall
		StreetProps.box(self, s[0] - 0.005, s[1] - 0.005, s[2] + 0.005, s[3] + 0.005, 4.0, Color("9a8a70"))
		StreetProps.box(self, s[0] - 0.03, s[1] - 0.03, s[2] + 0.03, s[3] + 0.03, 3.5, look[3] if type == "plaster" else Color("b4583a"), h)

	func _joints(s: Array, h: float) -> void:
		if type not in ["stone", "brick"]:
			return
		var line := Color(0, 0, 0, 0.18) if type == "stone" else Color(0.92, 0.88, 0.8, 0.5)
		var step := 6.0 if type == "stone" else 4.0
		var z := step
		while z < h - 1.0:
			var a := Iso.grid(Vector2(s[0], s[3])) - Vector2(0, z)
			var b := Iso.grid(Vector2(s[2], s[3])) - Vector2(0, z)
			draw_line(a, b, line, 1.0)
			z += step

	## A roofed passage through the wall, its archway facing the viewer, on a straight run.
	func _arch(axis_x: bool, col: Color, h: float, t: float) -> void:
		# u runs along the wall, v across it (front face at v = +t)
		var p := func(u: float, v: float, z: float) -> Vector2:
			return Iso.grid(Vector2(u, v) if axis_x else Vector2(v, u)) - Vector2(0, z)
		var lo := -0.5 - _into(8 if axis_x else 1)
		var hi := 0.5 + _into(2 if axis_x else 4)
		if axis_x:
			StreetProps.box(self, lo, -t, hi, t, h, col)
		else:
			StreetProps.box(self, -t, lo, t, hi, h, col)
		# archway: straight sides then a round top, dark inside with the far opening and the floor lit
		var r := 0.2
		var zs := 14.0
		var hole := PackedVector2Array([p.call(-r, t, 0.0)])
		var far := PackedVector2Array([p.call(-r * 0.7, -t, 0.0)])
		for i in 13:
			var a := PI - PI * i / 12.0
			hole.append(p.call(r * cos(a), t, zs + 10.0 * sin(a)))
			far.append(p.call(r * 0.7 * cos(a), -t, zs * 0.8 + 7.0 * sin(a)))
		hole.append(p.call(r, t, 0.0))
		far.append(p.call(r * 0.7, -t, 0.0))
		draw_colored_polygon(hole, Color("3a2e26"))
		var lit := Geometry2D.intersect_polygons(far, hole)
		for q in lit:
			draw_colored_polygon(q, Color("cfc6a8"))
		draw_colored_polygon(PackedVector2Array([p.call(-r, t, 0.0), p.call(r, t, 0.0), p.call(r * 0.7, -t, 0.0), p.call(-r * 0.7, -t, 0.0)]),
			Color("8a7a62"))
		# stone frame and keystone
		for i in 12:
			var a0 := PI - PI * i / 12.0
			var a1 := PI - PI * (i + 1) / 12.0
			draw_line(p.call(r * cos(a0), t, zs + 10.0 * sin(a0)), p.call(r * cos(a1), t, zs + 10.0 * sin(a1)), Color("f2ead6"), 2.0)
		draw_line(p.call(-r, t, 0.0), p.call(-r, t, zs), Color("f2ead6"), 2.0)
		draw_line(p.call(r, t, 0.0), p.call(r, t, zs), Color("f2ead6"), 2.0)
		draw_colored_polygon(PackedVector2Array([p.call(-0.035, t, zs + 8.0), p.call(0.035, t, zs + 8.0), p.call(0.025, t, zs + 13.0), p.call(-0.025, t, zs + 13.0)]),
			Color("bfb08e"))
		# little windows above, one either side of the arch
		for u in [-0.36, 0.36]:
			draw_colored_polygon(PackedVector2Array([p.call(u - 0.05, t, 18.0), p.call(u + 0.05, t, 18.0), p.call(u + 0.05, t, 27.0), p.call(u - 0.05, t, 27.0)]),
				Color("4a6a86"))
			draw_line(p.call(u - 0.06, t, 17.5), p.call(u + 0.06, t, 17.5), Color("f2ead6"), 1.5)
		# pitched tiled roof along the wall: back slope, front slope, then the gable end in view
		var e := t + 0.05
		var ridge := h + 9.0
		var tile := Color("b4583a")
		var r0 := lo - 0.02
		var r1 := hi + 0.02
		draw_colored_polygon(PackedVector2Array([p.call(r0, -e, h - 1.0), p.call(r1, -e, h - 1.0), p.call(r1, 0.0, ridge), p.call(r0, 0.0, ridge)]),
			tile.darkened(0.2))
		draw_colored_polygon(PackedVector2Array([p.call(r0, e, h - 1.0), p.call(r1, e, h - 1.0), p.call(r1, 0.0, ridge), p.call(r0, 0.0, ridge)]),
			tile)
		for i in 6:
			var u := r0 + (r1 - r0) * (i + 0.5) / 6.0
			draw_line(p.call(u, e, h - 1.0), p.call(u, 0.0, ridge), tile.darkened(0.15), 1.0)
		draw_colored_polygon(PackedVector2Array([p.call(r1, -t, h), p.call(r1, t, h), p.call(r1, 0.0, ridge - 1.0)]), col.darkened(0.2))
		draw_line(p.call(r0, 0.0, ridge), p.call(r1, 0.0, ridge), tile.darkened(0.35), 1.5)


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
