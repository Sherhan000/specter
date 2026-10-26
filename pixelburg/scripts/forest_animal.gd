class_name ForestAnimal
extends Sprite2D
## A wild (or zoo) animal wandering around a home point. Tap a wild one to try to catch it.

var species := "rabbit"
var home := Vector2.ZERO        ## grid position
var radius := 3.0
var g := Vector2.ZERO           ## current grid position
var target := Vector2.ZERO
var life := -1.0                ## seconds left for wild animals, -1 = forever
var origin := Vector2.ZERO       ## parent position when the animal lives inside a zoo view
var city: Node
var _wait := 0.0
var _t := randf() * 3.0
var _speed := 0.4
var _fading := false
var _back := false


func setup(p_species: String, p_home: Vector2, p_radius: float, p_city: Node) -> void:
	species = p_species
	home = p_home
	radius = p_radius
	city = p_city
	g = home + Vector2(randf_range(-radius, radius), randf_range(-radius, radius)) * 0.5
	target = g
	texture = Assets.tex("units/animal_" + species)
	hframes = 10
	centered = false
	var m: Dictionary = Assets.units().animals[species]
	offset = -Vector2(m.anchor[0], m.anchor[1])
	material = Assets.world_mat
	_speed = {"rabbit": 0.3, "deer": 0.22, "fox": 0.26, "boar": 0.18, "wolf": 0.26, "bear": 0.14}.get(species, 0.2)
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.8)
	_place()


func _place() -> void:
	position = Iso.grid(g) - origin


func hit(wp: Vector2) -> bool:
	var d := wp - global_position
	return absf(d.x) < 30 and d.y < 10 and d.y > -40


func tapped() -> void:
	if life < 0.0:
		Game.sfx("tap")
		city.hud.toast(Loc.t("zoo_animal") % Loc.t("animal_" + species))
		return
	city.hud.animal_popup(self)


func _process(delta: float) -> void:
	_t += delta
	if life > 0.0:
		life -= delta
		if life <= 0.0 and not _fading:
			_fading = true
			var tw := create_tween()
			tw.tween_property(self, "modulate:a", 0.0, 1.0)
			tw.tween_callback(queue_free)
	if _wait > 0.0:
		_wait -= delta
		frame = 4 if not _back else 9
		return
	var d := target - g
	if d.length() < 0.05:
		_wait = randf_range(1.0, 4.0)
		target = home + Vector2(randf_range(-radius, radius), randf_range(-radius, radius))
		return
	var step := minf(d.length(), _speed * delta)
	g += d.normalized() * step
	var sd := Iso.grid_vec(d)
	_back = sd.y < 0
	flip_h = (sd.x > 0) if not _back else (sd.x < 0)
	frame = int(_t * (10.0 if species == "rabbit" else 7.0)) % 4 + (5 if _back else 0)
	_place()
