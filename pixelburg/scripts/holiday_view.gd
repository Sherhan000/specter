class_name HolidayView
extends Node2D
## Temporary decorations of the holiday going on (ROADMAP 31): sprites on free tiles by the streets, garlands and
## bunting on houses, and evening fireworks on City Day. Rebuilt when the day or the buildings change.

var city: Node
var _holiday := ""
var _queued := false
var _bursts: Array = []     ## {"p": Vector2, "t": float, "col": Color}
var _next_burst := 0.0
var _center := Vector2.ZERO


func _ready() -> void:
	z_index = 30
	Game.day_passed.connect(func(_d): refresh_soon())
	for sig in [Game.building_added, Game.building_removed, Game.building_moved]:
		sig.connect(func(_u): refresh_soon())
	refresh()


func refresh_soon() -> void:
	if not _queued:
		_queued = true
		refresh.call_deferred()


func _clear() -> void:
	for c in get_children():
		c.queue_free()
	_bursts.clear()


func refresh() -> void:
	_queued = false
	_clear()
	_holiday = Game.holiday()
	if _holiday == "":
		return
	var spots := _free_spots()
	var homes := _facades()
	var used := 0
	for d in Holidays.LIST[_holiday].deco:
		var sprite: String = d[0]
		if sprite in ["garland", "bunting"]:
			for i in mini(int(d[1]), homes.size()):
				_add(sprite, homes[i].pos, homes[i].scale, 62.0)
		else:
			for i in int(d[1]):
				if used >= spots.size():
					break
				_add(sprite, Iso.center(spots[used]), 1.0 if sprite != "fir_tree" else 1.3, 0.0)
				used += 1
	_center = Iso.center(_city_center())


func _add(sprite: String, pos: Vector2, sc: float, lift: float) -> void:
	var tex := Assets.tex("holidays/" + sprite)
	if tex == null:
		return
	var s := Sprite2D.new()
	s.texture = tex
	s.scale = Vector2(sc, sc)
	s.offset = Vector2(0, -tex.get_height() / 2.0 + 14.0)
	s.position = pos - Vector2(0, lift)
	s.z_index = 0
	s.top_level = false
	# lives in the world so it sorts with the buildings and the people
	city.world.add_child(s)
	s.set_meta("holiday", true)
	add_child(_Mark.new(s))


## Keeps track of a world sprite so it goes away with the holiday.
class _Mark extends Node:
	var target: Node

	func _init(t: Node) -> void:
		target = t

	func _exit_tree() -> void:
		if is_instance_valid(target):
			target.queue_free()


func _city_center() -> Vector2i:
	var n := 0
	var sum := Vector2.ZERO
	for uid in Game.buildings:
		if Data.B[Game.buildings[uid].id].get("svc", "") == "gov":
			return Vector2i(Game.buildings[uid].x, Game.buildings[uid].y)
		sum += Vector2(Game.buildings[uid].x, Game.buildings[uid].y)
		n += 1
	if n == 0:
		return Game.plots[0] * Data.PLOT + Vector2i(Data.PLOT / 2, Data.PLOT / 2) if not Game.plots.is_empty() else Vector2i(40, 40)
	return Vector2i(sum / n)


## Free owned tiles next to a street, nearest to the centre of the city first.
func _free_spots() -> Array:
	var c := _city_center()
	var out := []
	for r in Game.roads:
		for d in Iso.DIRS:
			var t: Vector2i = r + d
			if Game.occ.has(t) or Game.net.has(t) or Game.water.has(t) or Game.walls.has(t) or not Game.is_owned(t):
				continue
			if not out.has(t):
				out.append(t)
	out.sort_custom(func(a, b): return (a - c).length_squared() < (b - c).length_squared() or ((a - c).length_squared() == (b - c).length_squared() and (a.x < b.x or (a.x == b.x and a.y < b.y))))
	# spread them out a little: skip tiles right next to one already taken
	var spread := []
	for t in out:
		if spread.all(func(o): return (o - t).abs().x + (o - t).abs().y > 1):
			spread.append(t)
	return spread


## Buildings to hang garlands / bunting on: built ones near the centre.
func _facades() -> Array:
	var c := _city_center()
	var list := []
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		var d: Dictionary = Data.B[b.id]
		if not b.built or d.cat == "decor":
			continue
		list.append({"d": (Vector2i(b.x, b.y) - c).length_squared(), "x": b.x, "y": b.y, "n": int(d.get("size", 1))})
	list.sort_custom(func(a, b): return a.d < b.d)
	var out := []
	for e in list:
		out.append({"pos": Iso.vertex(e.x + e.n, e.y + e.n), "scale": 0.5 + 0.3 * e.n})
	return out


func _process(delta: float) -> void:
	if _holiday != "cityday":
		if not _bursts.is_empty():
			_bursts.clear()
			queue_redraw()
		return
	var h := Game.hour()
	var dark := h >= 19 or h < 5
	_next_burst -= delta
	if dark and _next_burst <= 0.0:
		_next_burst = randf_range(0.6, 1.8)
		var cols := [Color("ff5a5a"), Color("ffd84a"), Color("5ac8ff"), Color("8aff8a"), Color("ff8ae0")]
		_bursts.append({"p": _center + Vector2(randf_range(-420, 420), randf_range(-900, -560)), "t": 0.0, "col": cols[randi() % cols.size()]})
	for b in _bursts:
		b.t += delta
	_bursts = _bursts.filter(func(b): return b.t < 1.6)
	queue_redraw()


func _draw() -> void:
	for b in _bursts:
		var t: float = b.t
		var a := clampf(1.0 - t / 1.6, 0.0, 1.0)
		var col: Color = b.col
		for i in 18:
			var ang := i * TAU / 18.0
			var dist := 150.0 * (1.0 - pow(1.0 - minf(t / 1.2, 1.0), 2.0))
			var p: Vector2 = b.p + Vector2(cos(ang), sin(ang)) * dist + Vector2(0, 40.0 * t * t)
			draw_circle(p, 7.0 * a + 1.5, Color(col.r, col.g, col.b, a))
			draw_circle(p - Vector2(cos(ang), sin(ang)) * 14.0, 4.0 * a, Color(1, 1, 1, a * 0.6))
		draw_circle(b.p, 12.0 * a, Color(1, 1, 0.9, a * 0.7))
