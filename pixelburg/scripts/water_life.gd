class_name WaterLife
extends Node
## Life on the water the player dug: trees, stones and reeds on the banks, ducks on rivers,
## sailing boats on seas, ships on oceans and gulls above them. Small details fade in as you zoom in.

const DIRS := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]

var city: Node
var decor: Array[Node] = []      ## bank decoration (trees, stones, reeds)
var details: Array[Node2D] = []  ## the small ones, shown only up close
var agents: Array[Floater] = []
var bodies: Array = []           ## [tiles: Array[Vector2i], kind: int]
var detail := 0.0


static func _h(c: Vector2i, salt: int) -> float:
	var v := (c.x * 73856093) ^ (c.y * 19349663) ^ (salt * 83492791)
	v = (v ^ (v >> 13)) * 1274126177
	return float((v ^ (v >> 16)) & 0xFFFF) / 65536.0


func refresh() -> void:
	for n in decor:
		if is_instance_valid(n):
			n.queue_free()
	decor.clear()
	details.clear()
	for a in agents:
		if is_instance_valid(a):
			a.queue_free()
	agents.clear()
	_find_bodies()
	for c in Game.water:
		_decorate(c)
	for body in bodies:
		_populate(body[0], body[1])
	_apply_detail()


func _find_bodies() -> void:
	bodies.clear()
	var seen := {}
	for start in Game.water:
		if seen.has(start):
			continue
		var comp: Array[Vector2i] = [start]
		seen[start] = true
		var k := 0
		while k < comp.size():
			var c: Vector2i = comp[k]
			k += 1
			for d in DIRS:
				var n: Vector2i = c + d
				if Game.water.has(n) and not seen.has(n):
					seen[n] = true
					comp.append(n)
		bodies.append([comp, Game.water_kind(start)])


## Bank corners: a corner of a water tile whose other three tiles around it are dry.
func _decorate(c: Vector2i) -> void:
	var kind := Game.water_kind(c)
	for k in 4:
		var dx := k % 2
		var dy := k / 2
		var sx := 1 if dx == 1 else -1
		var sy := 1 if dy == 1 else -1
		if Game.water.has(c + Vector2i(sx, 0)) or Game.water.has(c + Vector2i(0, sy)) or Game.water.has(c + Vector2i(sx, sy)):
			continue
		if Game.roads.has(c):
			continue
		var p := Vector2(c) + Vector2(0.18 + 0.64 * dx, 0.18 + 0.64 * dy)
		var h := _h(c, k)
		if h < (0.3 if kind == 1 else 0.15):
			var t: Sprite2D = city.scenery._tree_sprite("tree_%d" % int(_h(c, k + 7) * 8.0), Iso.grid(p), city.world)
			t.scale = Vector2(0.75, 0.75)
			decor.append(t)
		elif h < 0.65:
			var d := BankDetail.new()
			d.kind = "stones" if h < 0.48 or kind > 1 else "reeds"
			d.seed = int(h * 1000.0)
			d.position = Iso.grid(p)
			city.world.add_child(d)
			decor.append(d)
			details.append(d)


func _populate(tiles: Array, kind: int) -> void:
	var n := 0
	match kind:
		1:
			n = mini(4, tiles.size() / 6)
		2:
			n = mini(6, tiles.size() / 10 + 1)
		3:
			n = mini(9, tiles.size() / 14 + 2)
	for i in n:
		var what := "duck" if kind == 1 else ("ship" if kind == 3 and i % 3 == 0 else "boat")
		_spawn(what, tiles, city.world)
	if kind >= 2:
		for i in mini(5, 1 + tiles.size() / 25):
			_spawn("gull", tiles, city.top_fx)


func _spawn(what: String, tiles: Array, parent: Node) -> void:
	var f := Floater.new()
	f.what = what
	f.tiles = tiles
	f.g = Vector2(tiles.pick_random()) + Vector2(0.5, 0.5)
	parent.add_child(f)
	f.pick_target()
	agents.append(f)
	if what in ["duck", "gull"]:
		details.append(f)


func set_zoom(z: float) -> void:
	var d := clampf((z - 0.5) / 0.3, 0.0, 1.0)
	if absf(d - detail) > 0.02:
		detail = d
		_apply_detail()


func _apply_detail() -> void:
	for n in details:
		if is_instance_valid(n):
			n.modulate.a = detail
			n.visible = detail > 0.01


## Stones or reeds on a bank, drawn by hand.
class BankDetail extends Node2D:
	var kind := "stones"
	var seed := 0

	func _draw() -> void:
		var rng := RandomNumberGenerator.new()
		rng.seed = seed
		if kind == "stones":
			for i in 5:
				var p := Vector2(rng.randf_range(-16, 16), rng.randf_range(-7, 7))
				var r := rng.randf_range(2.5, 6.0)
				var col := Color(0.55, 0.55, 0.52).lerp(Color(0.72, 0.7, 0.66), rng.randf())
				draw_set_transform(p, 0.0, Vector2(1.0, 0.6))
				draw_circle(Vector2.ZERO, r, col.darkened(0.25))
				draw_circle(Vector2(-r * 0.2, -r * 0.35), r * 0.75, col)
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		else:
			for i in 14:
				var b := Vector2(rng.randf_range(-14, 14), rng.randf_range(-6, 6))
				var top := b + Vector2(rng.randf_range(-3, 3), -rng.randf_range(10, 18))
				draw_line(b, top, Color(0.36, 0.55, 0.24).lerp(Color(0.55, 0.62, 0.3), rng.randf()), 1.4)
				if rng.randf() < 0.3:
					draw_line(top, top + Vector2(0, 4), Color(0.45, 0.3, 0.18), 2.5)


## Something moving on (or above) the water: a duck, a boat, a ship or a gull.
class Floater extends Node2D:
	var what := "boat"
	var tiles: Array = []
	var g := Vector2.ZERO
	var target := Vector2.ZERO
	var dir := Vector2.RIGHT
	var wait := 0.0
	var _t := randf() * 10.0

	func pick_target() -> void:
		# a nearby tile of the same water, so boats keep off the land
		var best := Vector2.ZERO
		var tries := 0
		while tries < 12:
			var c: Vector2 = Vector2(tiles.pick_random()) + Vector2(randf_range(0.3, 0.7), randf_range(0.3, 0.7))
			tries += 1
			best = c
			if c.distance_to(g) < 5.0:
				break
		target = best
		position = Iso.grid(g)

	func _process(delta: float) -> void:
		_t += delta
		var speed := {"duck": 0.12, "boat": 0.22, "ship": 0.16, "gull": 0.9}[what] as float
		if wait > 0.0:
			wait -= delta
		else:
			var to := target - g
			if to.length() < 0.05:
				wait = randf_range(1.0, 5.0) if what != "gull" else 0.0
				pick_target()
			else:
				dir = dir.lerp(to.normalized(), minf(1.0, delta * 2.0)).normalized()
				g += dir * minf(speed * delta, to.length())
		position = Iso.grid(g) + (Vector2(0, -60) if what == "gull" else Vector2.ZERO)
		queue_redraw()

	func _draw() -> void:
		var h := (Iso.grid(g + dir) - Iso.grid(g)).normalized()
		var bob := sin(_t * 2.0) * 0.8
		match what:
			"duck":
				draw_set_transform(Vector2(0, bob), 0.0, Vector2(1, 0.6))
				draw_circle(Vector2.ZERO, 3.5, Color(0.5, 0.36, 0.22))
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
				draw_circle(h * 3.0 + Vector2(0, -3 + bob), 1.8, Color(0.2, 0.45, 0.25))
				draw_line(h * 4.5 + Vector2(0, -3 + bob), h * 6.0 + Vector2(0, -2.6 + bob), Color(0.95, 0.7, 0.2), 1.2)
			"boat", "ship":
				var big := what == "ship"
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * (3.2 if big else 2.4))
				var L := 22.0 if big else 12.0
				var W := 6.0 if big else 3.5
				var side := Vector2(-h.y, h.x) * W
				var y := Vector2(0, bob)
				var hull := PackedVector2Array([h * L + y, side + y - h * L * 0.7, -h * L + y, -side + y - h * L * 0.7])
				draw_colored_polygon(PackedVector2Array([h * (L + 4) + y * 0.0, -h * L - side * 1.5, -h * L + side * 1.5]),
					Color(1, 1, 1, 0.25))   # wake
				draw_colored_polygon(hull, Color("f4f2ec") if big else Color("8a5a34"))
				var deck := PackedVector2Array([h * L * 0.8 + y - Vector2(0, 3), side * 0.7 + y - h * L * 0.6 - Vector2(0, 3),
					-h * L * 0.9 + y - Vector2(0, 3), -side * 0.7 + y - h * L * 0.6 - Vector2(0, 3)])
				draw_colored_polygon(deck, Color("c8342a") if big else Color("c8a070"))
				if big:
					draw_rect(Rect2(-6, -12 + bob, 12, 8), Color("f8f8f4"))
					draw_rect(Rect2(-2, -18 + bob, 4, 6), Color("2a2a30"))
					draw_line(Vector2(-5, -8 + bob), Vector2(5, -8 + bob), Color("6a9ac0"), 1.5)
				else:
					var mast := Vector2(0, -3 + bob)
					draw_line(mast, mast + Vector2(0, -20), Color("5a3a20"), 1.2)
					var s := 1.0 if h.x >= 0 else -1.0
					draw_colored_polygon(PackedVector2Array([mast + Vector2(s, -19), mast + Vector2(s, -2), mast + Vector2(s * 11, -3)]),
						Color("fbfaf4"))
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
			"gull":
				var flap := sin(_t * 7.0) * 3.0
				draw_polyline(PackedVector2Array([Vector2(-7, -flap), Vector2(-2, 0), Vector2(0, 1), Vector2(2, 0), Vector2(7, -flap)]),
					Color(0.98, 0.98, 0.98), 1.6)
