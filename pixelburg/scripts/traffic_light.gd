class_name TrafficLight
extends Node2D
## Pole with three lamps on an intersection corner; the lit lamp follows the cycle of one axis.

const COLORS := [Color(1.0, 0.22, 0.18), Color(1.0, 0.78, 0.2), Color(0.3, 1.0, 0.45)]
const KEYS := ["red", "yellow", "green"]

var tile := Vector2i.ZERO
var axis := "x"   ## traffic moving along this grid axis is controlled by this light
var city: Node
var lamps: Array[Sprite2D] = []


func setup(p_tile: Vector2i, p_axis: String, p_city: Node) -> void:
	tile = p_tile
	axis = p_axis
	city = p_city
	var corner := Vector2(0.84, 0.16) if axis == "x" else Vector2(0.16, 0.84)
	position = Iso.vertex(tile.x + corner.x, tile.y + corner.y)
	var name := "tlight_" + axis
	var m: Dictionary = Assets.units().props[name]
	var shift := Vector2(0, Iso.HY)
	var s := Sprite2D.new()
	s.texture = Assets.tex("units/" + name)
	s.centered = false
	s.offset = Vector2(m.o[0], m.o[1]) + shift
	s.material = Assets.world_mat
	add_child(s)
	for i in 3:
		var p: Array = m.points[KEYS[i]]
		var l := Sprite2D.new()
		l.texture = Assets.tex("fx/lamp_head")
		l.scale = Vector2(0.18, 0.18)
		l.position = Vector2(p[0], p[1]) + shift
		l.modulate = COLORS[i]
		l.material = Assets.glow_mat
		add_child(l)
		lamps.append(l)


func _process(_delta: float) -> void:
	var state: int = city.light_state(tile, axis)  # 0 red, 1 yellow, 2 green
	for i in 3:
		lamps[i].visible = i == state
