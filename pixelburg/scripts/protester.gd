class_name Protester
extends Node2D
## One person at a protest (ROADMAP 28): walks up to the gathering place, stands there raising a placard
## and chanting now and then; goes home when the protest ends or runs when the police break it up.

const SPEED := 0.22                ## tiles per second
const PLACARD_FRAMES := 7
const BY_CAUSE := {"rob": [5, 6], "tax": [2, 0], "demolish": [3, 0], "mood": [4, 1], "rules": [6, 5]}
const GENERIC := [0, 1]
const KINDS := ["man", "woman", "man", "woman", "teen", "student", "grandpa", "grandma", "business", "builder"]

var life: Life
var sprite: Sprite2D
var placard: Sprite2D
var kind := "man"
var row := 0
var cause := "mood"
var g := Vector2.ZERO
var spot := Vector2.ZERO           ## where to stand
var face := Vector2.ZERO           ## what to face (the building)
var heading := Vector2(0, 1)
var state := "come"                ## come, stand, leave, run
var away := Vector2.ZERO
var done := false
var _anim := randf() * 4.0
var _chant := randf_range(2.0, 9.0)


func start(from: Vector2, at: Vector2, look: Vector2, why: String) -> void:
	cause = why
	g = from
	spot = at
	face = look
	kind = KINDS.pick_random()
	var meta: Dictionary = Assets.units().people
	var rows: Array = meta.kinds.get(kind, [0])
	row = int(rows.pick_random())
	sprite = Sprite2D.new()
	sprite.texture = Assets.tex("units/people")
	sprite.hframes = 12
	sprite.vframes = int(sprite.texture.get_height() / meta.cell[1])
	sprite.centered = false
	sprite.offset = -Vector2(meta.anchor[0], meta.anchor[1])
	sprite.material = Assets.world_mat
	add_child(sprite)
	var pt := Assets.tex("units/placards")
	if pt:
		placard = Sprite2D.new()
		placard.texture = pt
		placard.hframes = PLACARD_FRAMES
		var pool: Array = BY_CAUSE.get(cause, GENERIC) + GENERIC
		placard.frame = int(pool.pick_random())
		placard.scale = Vector2(0.5, 0.5)
		placard.centered = false
		placard.offset = Vector2(-16, -44)
		placard.material = Assets.world_mat
		add_child(placard)
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.5)
	_visual()


func tapped() -> void:
	Game.sfx("tap")
	_shout()


func _shout() -> void:
	var key := "pr_cause_" + cause
	if life and life.city:
		life.speech(self, Loc.t(key), 2.4)


## The protest is over: go home calmly.
func leave(to: Vector2) -> void:
	if state in ["leave", "run"]:
		return
	state = "leave"
	away = to


## The police break it up: a "!" over the head and running away fast.
func run_away(to: Vector2) -> void:
	state = "run"
	away = to
	var b := Sprite2D.new()
	b.texture = Assets.ui_icon("warn")
	var ts := b.texture.get_size()
	b.scale = Vector2(20.0, 20.0) / maxf(ts.x, 1.0)
	b.position = Vector2(0, -56)
	b.z_index = 30
	add_child(b)
	var tw := b.create_tween()
	tw.tween_property(b, "position:y", -70.0, 2.0)
	tw.parallel().tween_property(b, "modulate:a", 0.0, 2.0)
	tw.tween_callback(b.queue_free)


func step(delta: float) -> void:
	if done:
		return
	_anim += delta
	match state:
		"come":
			if _walk_to(spot, SPEED * 1.6, delta):
				state = "stand"
		"stand":
			heading = (face - g).normalized() if (face - g).length() > 0.01 else heading
			_chant -= delta
			if _chant <= 0.0:
				_chant = randf_range(6.0, 14.0)
				if randf() < 0.35:
					_shout()
		"leave", "run":
			if _walk_to(away, SPEED * (2.6 if state == "run" else 1.0), delta):
				_finish()
				return
			if modulate.a > 0.0 and g.distance_to(away) < 1.2:
				modulate.a = maxf(0.0, g.distance_to(away) / 1.2)
	_visual()


func _walk_to(to: Vector2, speed: float, delta: float) -> bool:
	var d := to - g
	var len := d.length()
	var stp := speed * delta
	if len <= stp:
		g = to
		return true
	g += d / len * stp
	heading = d / len
	return false


func _finish() -> void:
	done = true
	var tw := create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.3)
	tw.tween_callback(queue_free)


func _visual() -> void:
	position = Iso.grid(g)
	var dir := Iso.grid_vec(heading)
	var back := dir.y < -0.01
	sprite.flip_h = (dir.x > 0) if not back else (dir.x < 0)
	if state == "stand":
		# arms up with the placard, raised higher on every chant beat
		var up := int(_anim * 1.6) % 2
		sprite.frame = row * 12 + 10 + up
		sprite.flip_h = false
		if placard:
			placard.position = Vector2(0, -15.0 - 2.0 * up)
	else:
		sprite.frame = row * 12 + (4 if back else 0) + int(_anim * 8.0) % 4
		if placard:
			placard.position = Vector2(3, -11)
	if placard:
		placard.visible = state != "run"
