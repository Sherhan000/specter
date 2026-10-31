class_name Stroller
extends Node2D
## A person out for a stroll on the paving and footpaths (Game.paves): wanders from tile to tile,
## stops now and then to look around, sometimes walks a dog; fades out after a while.

const SPEED := 0.13                ## tiles per second
const JOG_SPEED := 0.34
const KINDS := ["man", "woman", "man", "woman", "grandpa", "grandma", "boy", "girl", "jogger"]
const DIRS := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]
const DOGS := [Color("8a5a32"), Color("2a2624"), Color("e8dcc4"), Color("c89048")]

var sprite: Sprite2D
var kind := "man"
var row := 0
var tile := Vector2i.ZERO
var prev := Vector2i(-9999, -9999)
var g := Vector2.ZERO
var target := Vector2.ZERO
var heading := Vector2(0, 1)
var steps := 0                     ## tiles left before going home
var pause := 0.0
var done := false
var dog := false
var dog_color: Color = DOGS.pick_random()
var _anim := randf()


func start(from: Vector2i) -> void:
	tile = from
	kind = KINDS.pick_random()
	dog = kind in ["man", "woman", "grandpa", "grandma"] and randf() < 0.35
	var meta: Dictionary = Assets.units().people
	var rows: Array = meta.kinds.get(kind, [0])
	row = int(rows.pick_random())
	steps = randi_range(6, 16)
	g = _spot(tile)
	target = g
	sprite = Sprite2D.new()
	sprite.texture = Assets.tex("units/people")
	sprite.hframes = 12
	sprite.vframes = int(sprite.texture.get_height() / meta.cell[1])
	sprite.centered = false
	sprite.offset = -Vector2(meta.anchor[0], meta.anchor[1])
	sprite.material = Assets.world_mat
	add_child(sprite)
	_next()
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.5)
	_visual()


## A point to walk to on a tile: the middle of a footpath, anywhere on wide paving.
func _spot(t: Vector2i) -> Vector2:
	var c := Vector2(t) + Vector2(0.5, 0.5)
	if Game.paves.get(t, "") == "path":
		return c
	return c + Vector2(randf_range(-0.28, 0.28), randf_range(-0.28, 0.28))


## Paved neighbours of a tile, the way back last.
func ways(t: Vector2i) -> Array:
	var out: Array = []
	for d in DIRS:
		var o: Vector2i = t + d
		if Game.paves.has(o) and o != prev:
			out.append(o)
	if out.is_empty() and Game.paves.has(prev):
		out.append(prev)
	return out


func _next() -> void:
	var w := ways(tile)
	if w.is_empty() or steps <= 0:
		finish()
		return
	steps -= 1
	prev = tile
	tile = w.pick_random()
	target = _spot(tile)


func step(delta: float) -> void:
	if done:
		return
	if not Game.paves.has(tile):
		finish()
		return
	if pause > 0.0:
		pause -= delta
		_visual()
		return
	var spd := JOG_SPEED if kind == "jogger" else SPEED
	var to := target - g
	var l := to.length()
	var move := spd * delta
	_anim += delta * (2.0 if kind == "jogger" else 1.2)
	if l <= move:
		g = target
		if kind != "jogger" and randf() < 0.25:
			pause = randf_range(1.0, 3.0)
		_next()
	else:
		heading = to / l
		g += heading * move
	_visual()


func finish() -> void:
	if done:
		return
	done = true
	var tw := create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.5)
	tw.tween_callback(queue_free)


func _visual() -> void:
	position = Iso.grid(g)
	var dir := Iso.grid_vec(heading)
	var back := dir.y < -0.01
	sprite.flip_h = (dir.x > 0) if not back else (dir.x < 0)
	var walking := pause <= 0.0 and not done
	sprite.frame = row * 12 + (4 if back else 0) + (int(_anim * 8.0) % 4 if walking else 0)
	if dog:
		queue_redraw()


func _draw() -> void:
	if not dog:
		return
	# a small dog trotting beside, a little ahead, on a lead
	var h := Iso.grid_vec(heading).normalized()
	var side := Vector2(-h.y, h.x)
	var p := h * 7.0 + side * 6.0
	var bob := absf(sin(_anim * 9.0)) * 1.0 if pause <= 0.0 else 0.0
	var body := p + Vector2(0, -4.0 - bob)
	var dark := dog_color.darkened(0.35)
	for k in [-1.0, 1.0]:
		var leg: Vector2 = body + h * 2.2 * k
		draw_line(leg, leg + Vector2(0, 3.6 + bob), dark, 1.2)
	draw_circle(body - h * 1.6, 2.0, dog_color)
	draw_circle(body + h * 1.6, 2.0, dog_color)
	var head := body + h * 3.8 + Vector2(0, -1.6)
	draw_circle(head, 1.7, dog_color)
	draw_circle(head + h * 1.3 + Vector2(0, 0.4), 0.9, dark)
	draw_line(body - h * 3.2, body - h * 4.6 + Vector2(0, -2.0), dog_color, 1.2)
	draw_line(head + Vector2(0, -0.6), Vector2(side.x * 2.0, -11.0), Color(0.2, 0.18, 0.16, 0.8), 0.6)
