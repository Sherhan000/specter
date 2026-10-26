class_name LampView
extends Node2D
## Street lamp on a sidewalk corner: the post, a glowing head and a light pool on the ground
## (drawn under the buildings, so the light never covers houses). The lights fade in and out with
## the night through a shared material, so a lamp costs nothing per frame.

var q := Vector2i.ZERO
var sprite: Sprite2D
var glow: Sprite2D
var head: Sprite2D
var pool: Sprite2D


## Grid position of a lamp slot: quarter q = 2 * tile + corner (0 / 1 on each axis).
static func slot_grid(p_q: Vector2i) -> Vector2:
	var t := Vector2(floori(p_q.x / 2.0), floori(p_q.y / 2.0))
	var c := Vector2(posmod(p_q.x, 2), posmod(p_q.y, 2))
	return t + Vector2(0.1, 0.1) + c * 0.8


func setup(p_q: Vector2i, style: String, pool_layer: Node2D) -> void:
	q = p_q
	position = Iso.grid(slot_grid(q))
	var m: Dictionary = Assets.units().props["lamp_" + style]
	var shift := Vector2(0, Iso.HY)
	sprite = Sprite2D.new()
	sprite.texture = Assets.tex("units/lamp_" + style)
	sprite.centered = false
	sprite.offset = Vector2(m.o[0], m.o[1]) + shift
	sprite.material = Assets.world_mat
	add_child(sprite)
	glow = Sprite2D.new()
	glow.texture = Assets.tex("units/lamp_%s_glow" % style)
	glow.centered = false
	glow.offset = Vector2(m.glow[0], m.glow[1]) + shift
	glow.material = Assets.night_mat
	add_child(glow)
	head = Sprite2D.new()
	head.texture = Assets.tex("fx/lamp_head")
	head.position = Vector2(m.points.light[0], m.points.light[1]) + shift
	head.material = Assets.night_mat
	head.modulate.a = 0.95
	head.z_index = 1
	add_child(head)
	pool = Sprite2D.new()
	pool.texture = Assets.tex("fx/light_pool")
	pool.position = position + Vector2(head.position.x * 0.6, 0)
	pool.scale = Vector2(1.5, 1.5)
	pool.material = Assets.night_mat
	pool.modulate = Color(1.5, 1.3, 1.0, 1.0)
	pool_layer.add_child(pool)


func free_all() -> void:
	if is_instance_valid(pool):
		pool.queue_free()
	queue_free()


func hit(wp: Vector2) -> bool:
	var d := wp - position
	return d.x > -12 and d.x < 14 and d.y < 6 and d.y > -60

