extends Node2D
## Main scene: the valley (ground shader, backdrop, scenery), the buildings, the camera,
## touch input and the build / road / move / lamp / link / demolish / land modes.

enum Mode { NONE, PLACE, ROAD, DEMOLISH, MOVE, LAMP, LINK, LAND }

const ZOOM_MIN := 0.3
const ZOOM_MAX := 1.6
const ZOOM_START := 0.62
const LIGHT_PERIOD := 16.0
const LONG_PRESS := 0.45

var ground: Ground
var backdrop: Backdrop
var scenery: Scenery
var decals: Node2D
var shadows: Node2D
var pools: Node2D
var cursors: Node2D
var world: Node2D
var top_fx: Node2D
var sky: Node2D
var camera: Camera2D
var hud: CanvasLayer
var life: Life
var weather: WeatherFx

var views := {}          ## uid -> BuildingView
var lamp_nodes := {}     ## quarter Vector2i -> LampView
var sale_signs: Array[Node2D] = []
var light_nodes := {}    ## Vector2i -> [TrafficLight, TrafficLight]
var forest_animals: Array[ForestAnimal] = []
var zoo_animals: Array[ForestAnimal] = []
var input_lock := ""     ## while the tutorial runs: "" = free, otherwise only this action is allowed

var mode := Mode.NONE
var place_id := ""
var place_rot := 0
var rot_auto := true
var road_type := "asphalt"
var lamp_style := "classic"
var ghost: Sprite2D
var ghost_tile := Vector2i.ZERO
var road_start := Vector2i(-1, -1)
var road_tiles: Array[Vector2i] = []
var demolish_target := {}
var move_uid := 0
var link_from := 0
var _last_road_end := Vector2i(-1, -1)

var _touches := {}
var _press_pos := Vector2.ZERO
var _press_time := 0.0
var _pressing := false
var _moved := false
var _drag_ghost := false
var _drawing_road := false
var _velocity := Vector2.ZERO
var _last_drag_time := 0
var _pinch_dist := 0.0
var _mouse_down := false
var _time := 0.0
var _cull_t := 0.0
var _animal_t := 2.0
var _bird_t := 6.0


func _ready() -> void:
	Assets.init_materials()
	get_tree().set_auto_accept_quit(false)
	_build_layers()
	scenery = Scenery.new()
	scenery.city = self
	add_child(scenery)
	ground.extra_roads = scenery.village_roads
	ground.update_roads(Game.net)
	ground.update_info()
	scenery.rebuild_land_trees()
	_rebuild_signs()
	_rebuild_lights()
	_rebuild_lamps()
	for uid in Game.buildings:
		_add_view(uid)
	life = Life.new()
	life.city = self
	add_child(life)
	weather = WeatherFx.new()
	weather.city = self
	add_child(weather)

	hud = preload("res://scripts/hud.gd").new()
	hud.city = self
	add_child(hud)

	camera.position = Iso.center(Vector2i(Data.CENTER + 1, Data.CENTER))
	camera.zoom = Vector2(ZOOM_START, ZOOM_START)
	_clamp_camera()

	Game.building_added.connect(_add_view)
	Game.building_removed.connect(_on_building_removed)
	Game.building_updated.connect(_on_building_updated)
	Game.building_moved.connect(_on_building_moved)
	Game.roads_changed.connect(_on_roads_changed)
	Game.lights_changed.connect(_rebuild_lights)
	Game.lamps_changed.connect(_rebuild_lamps)
	Game.land_changed.connect(_on_land_changed)
	Game.trees_changed.connect(scenery.rebuild_land_trees)
	Game.gem_found.connect(_on_gem_found)
	Game.animals_changed.connect(_rebuild_zoo_animals)
	Events.fire_started.connect(_on_fire)
	Events.crime.connect(func(caught): life.start_chase(caught))
	_rebuild_zoo_animals()
	_update_daylight()
	scenery.update(_view_rect())


func _build_layers() -> void:
	backdrop = Backdrop.new()
	backdrop.city = self
	add_child(backdrop)
	ground = Ground.new()
	ground.z_index = -10
	add_child(ground)
	decals = Node2D.new()
	decals.z_index = -9
	add_child(decals)
	shadows = Node2D.new()
	shadows.z_index = -8
	add_child(shadows)
	pools = Node2D.new()
	pools.z_index = -7
	pools.material = Assets.glow_mat
	add_child(pools)
	cursors = Node2D.new()
	cursors.z_index = -6
	add_child(cursors)
	world = Node2D.new()
	world.y_sort_enabled = true
	add_child(world)
	top_fx = Node2D.new()
	top_fx.z_index = 40
	add_child(top_fx)
	sky = Node2D.new()
	sky.z_index = 50
	add_child(sky)
	camera = Camera2D.new()
	add_child(camera)


func _sprite(tex_path: String, m: Dictionary, pos: Vector2, mat: Material, parent: Node) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = Assets.tex(tex_path)
	s.centered = false
	s.position = pos
	s.offset = Vector2(m.o[0], m.o[1]) + Vector2(0, Iso.HY)
	s.material = mat
	parent.add_child(s)
	return s


func _rebuild_signs() -> void:
	for s in sale_signs:
		s.queue_free()
	sale_signs.clear()
	var m: Dictionary = Assets.units().props.sale_sign
	for py in Data.PLOTS:
		for px in Data.PLOTS:
			var p := Vector2i(px, py)
			if not Game.plot_buyable(p):
				continue
			var c := Vector2i(Data.LAND0 + px * Data.PLOT + Data.PLOT / 2, Data.LAND0 + py * Data.PLOT + Data.PLOT / 2)
			var s := _sprite("units/sale_sign", m, Iso.center(c), Assets.world_mat, world)
			s.set_meta("plot", p)
			var z := Sprite2D.new()
			z.texture = Assets.ui_icon({"city": "home", "farm": "goods", "industry": "factory", "leisure": "zoo"}[Data.zone_of_plot(p)])
			var ts := z.texture.get_size()
			z.scale = Vector2(26.0, 26.0) / maxf(ts.x, 1.0)
			z.position = Vector2(0, -26)
			s.add_child(z)
			sale_signs.append(s)


func _rebuild_lights() -> void:
	for c in light_nodes:
		for l in light_nodes[c]:
			l.queue_free()
	light_nodes.clear()
	for c in Game.lights:
		var pair := []
		for axis in ["x", "y"]:
			var tl := TrafficLight.new()
			world.add_child(tl)
			tl.setup(c, axis, self)
			pair.append(tl)
		light_nodes[c] = pair
	ground.update_roads(Game.net)


func _rebuild_lamps() -> void:
	for q in lamp_nodes.keys():
		if not Game.lamps.has(q):
			lamp_nodes[q].free_all()
			lamp_nodes.erase(q)
	for q in Game.lamps:
		if lamp_nodes.has(q):
			continue
		var l := LampView.new()
		world.add_child(l)
		l.setup(q, Game.lamps[q], pools)
		lamp_nodes[q] = l


func light_state(tile: Vector2i, axis: String) -> int:
	return light_state_at(tile, axis, 0.0)


## Light of one axis `ahead` seconds from now: 0 red, 1 yellow, 2 green.
func light_state_at(tile: Vector2i, axis: String, ahead: float) -> int:
	var off := float(absi(tile.x * 31 + tile.y * 17) % 16)
	var t := fmod(_time + off + ahead, LIGHT_PERIOD)
	# x: green 0-6, yellow 6-7.5, red 7.5-16 ; y: red 0-8, green 8-14, yellow 14-15.5, red
	if axis == "x":
		return 2 if t < 6.0 else 1 if t < 7.5 else 0
	return 2 if t >= 8.0 and t < 14.0 else 1 if t >= 14.0 and t < 15.5 else 0


func light_allows(tile: Vector2i, dir: Vector2i) -> bool:
	if not Game.lights.has(tile):
		return true
	return light_state(tile, "x" if dir.x != 0 else "y") == 2


func _add_view(uid: int) -> void:
	var v := BuildingView.new()
	world.add_child(v)
	v.setup(uid, decals, shadows)
	views[uid] = v
	scenery.rebuild_land_trees()


func _on_building_removed(uid: int) -> void:
	if views.has(uid):
		var v: BuildingView = views[uid]
		puff(v.anchor() - Vector2(0, v.size * 60), v.size)
		v.queue_free()
		views.erase(uid)
	scenery.rebuild_land_trees()
	life.buildings_changed()


func _on_building_updated(uid: int) -> void:
	if views.has(uid):
		views[uid].refresh()


func _on_building_moved(uid: int) -> void:
	if views.has(uid):
		views[uid].queue_free()
		views.erase(uid)
	_add_view(uid)
	views[uid].pop_in()
	life.buildings_changed()


func _on_roads_changed() -> void:
	ground.update_roads(Game.net)
	scenery.rebuild_land_trees()
	_rebuild_lights()
	life.roads_changed()


func _on_land_changed() -> void:
	ground.update_info()
	scenery.rebuild_land_trees()
	_rebuild_signs()


func _on_gem_found(uid: int) -> void:
	if views.has(uid):
		var v: BuildingView = views[uid]
		var top := v.global_position + Vector2(0, v.top_y() - 30)
		hud.fly_reward(world_to_screen(top), {"gems": 1})


func _on_fire(uid: int, covered: bool) -> void:
	if covered:
		life.dispatch("fire", uid)
	if views.has(uid):
		views[uid].refresh()


func _rebuild_zoo_animals() -> void:
	for a in zoo_animals:
		if is_instance_valid(a):
			a.queue_free()
	zoo_animals.clear()
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if b.id != "zoo" or not b.built or not views.has(uid):
			continue
		var m := Assets.meta(views[uid].tex_name)
		var pens: Array = []
		for k in 4:
			if m.get("points", {}).has("pen%d" % k):
				pass
		for i in mini(Game.caught.size(), 4 * b.lvl):
			var pen := Vector2(0.75 + (i % 2) * 1.5, 0.75 + ((i / 2) % 2) * 1.5)
			var a := ForestAnimal.new()
			world.add_child(a)
			a.setup(Game.caught[i], Vector2(b.x, b.y) + pen, 0.45, self)
			zoo_animals.append(a)


# ====================================================================== frame
func _process(delta: float) -> void:
	_time += delta
	_update_daylight()
	if _touches.is_empty() and not _mouse_down and _velocity.length() > 5.0:
		camera.position -= _velocity * delta / camera.zoom.x
		_velocity *= pow(0.02, delta)
		_clamp_camera()
	if _pressing and not _moved and mode == Mode.NONE and _time - _press_time > LONG_PRESS:
		_pressing = false
		_long_press(_press_pos)
	_cull_t -= delta
	if _cull_t <= 0.0:
		_cull_t = 0.25
		_cull()
	_animal_t -= delta
	if _animal_t <= 0.0:
		_animal_t = 3.0
		_update_forest_animals()
	_bird_t -= delta
	if _bird_t <= 0.0:
		_bird_t = randf_range(14.0, 30.0)
		if Game.weather in ["clear", "cloudy"] and Game.night_amount() < 0.5:
			_spawn_birds()


func _cull() -> void:
	var view := _view_rect()
	scenery.update(view)
	# only buildings on screen animate; the others (and their smoke and fountains) sleep
	var near := view.grow(400)
	for uid in views:
		var v: BuildingView = views[uid]
		var on := near.has_point(v.position)
		var mode := Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED
		if v.process_mode != mode:
			v.process_mode = mode


const SKY_DAY := [Color(0.36, 0.58, 0.84), Color(0.78, 0.87, 0.94)]
const SKY_DUSK := [Color(0.3, 0.34, 0.6), Color(0.98, 0.7, 0.5)]
const SKY_NIGHT := [Color(0.03, 0.05, 0.12), Color(0.12, 0.16, 0.28)]


func _update_daylight() -> void:
	var tint := Game.world_tint()
	var night := Game.night_amount()
	Assets.set_daylight(tint, night)
	var h := Game.day_time * 24.0
	var dusk := clampf(1.0 - absf(h - 19.6) / 1.6, 0.0, 1.0) + clampf(1.0 - absf(h - 6.0) / 1.2, 0.0, 1.0) * 0.7
	var zen := SKY_DAY[0].lerp(SKY_DUSK[0], dusk).lerp(SKY_NIGHT[0], night)
	var hor := SKY_DAY[1].lerp(SKY_DUSK[1], dusk).lerp(SKY_NIGHT[1], night)
	if Game.weather in ["rain", "storm", "snow", "fog"]:
		var grey := Color(0.55, 0.58, 0.62) * (1.0 - night * 0.8)
		zen = zen.lerp(grey, 0.6)
		hor = hor.lerp(grey * 1.1, 0.6)
	backdrop.set_colors(zen, hor, night, tint)
	ground.set_daylight(tint, hor)
	Assets.set_haze(hor)
	RenderingServer.set_default_clear_color(hor)


func _update_forest_animals() -> void:
	forest_animals = forest_animals.filter(func(a): return is_instance_valid(a))
	if forest_animals.size() >= 8:
		return
	var view := _view_rect().grow(400)
	for attempt in 40:
		var c := Vector2i(randi_range(Data.LAND0 - Data.FOREST - 6, Data.LAND1 + Data.FOREST + 5),
			randi_range(Data.LAND0 - Data.FOREST - 6, Data.LAND1 + Data.FOREST + 5))
		if Data.region(c) != "forest" or Game.net.has(c):
			continue
		var p := Iso.center(c)
		if not view.has_point(p):
			continue
		var weights := {"rabbit": 5, "deer": 4, "fox": 3, "boar": 2, "wolf": 1, "bear": 1}
		var pick := "rabbit"
		var r := randi() % 16
		for k in weights:
			r -= int(weights[k])
			if r < 0:
				pick = k
				break
		var a := ForestAnimal.new()
		world.add_child(a)
		a.setup(pick, Vector2(c) + Vector2(0.5, 0.5), 3.0, self)
		a.life = randf_range(40.0, 80.0)
		forest_animals.append(a)
		return


func _spawn_birds() -> void:
	var view := _view_rect()
	var from_left := randf() < 0.5
	var start := Vector2(view.position.x - 80 if from_left else view.end.x + 80, randf_range(view.position.y, view.end.y))
	var dir := Vector2(1 if from_left else -1, randf_range(-0.3, 0.3)).normalized()
	for i in randi_range(4, 7):
		var b := Critter.new()
		b.texture = Assets.tex("fx/bird")
		b.hframes = 2
		b.position = start + Vector2(-dir.x * i * 26, (i % 2) * 20 - 10 + i * 4)
		b.velocity = dir * 110.0
		b.life = (view.size.x + 300) / 110.0
		b.z_index = 30
		sky.add_child(b)


func map_rect() -> Rect2:
	var a := Iso.vertex(0, Data.MAP)
	var b := Iso.vertex(Data.MAP, 0)
	return Rect2(a.x, 0.0, b.x - a.x, Iso.vertex(Data.MAP, Data.MAP).y)


func _view_rect() -> Rect2:
	var size := get_viewport().get_visible_rect().size / camera.zoom
	return Rect2(camera.position - size / 2, size)


func view_rect() -> Rect2:
	return _view_rect()


func _clamp_camera() -> void:
	var half := get_viewport().get_visible_rect().size / camera.zoom / 2.0
	var left := Iso.vertex(Data.LAND0, Data.LAND1).x - 1800.0
	var right := Iso.vertex(Data.LAND1, Data.LAND0).x + 1800.0
	var bottom := Iso.vertex(Data.LAND1, Data.LAND1).y + 1400.0
	# the sky beyond the horizon may fill about half of the screen
	var top := Data.HORIZON * Iso.HY - half.y * 0.05
	camera.position = camera.position.clamp(Vector2(left, top), Vector2(right, maxf(top, bottom)))


func focus(world_p: Vector2, zoom := 0.0) -> void:
	var tw := create_tween().set_parallel()
	tw.tween_property(camera, "position", world_p, 0.6).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	if zoom > 0.0:
		tw.tween_property(camera, "zoom", Vector2(zoom, zoom), 0.6).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


# ====================================================================== input
func screen_to_world(p: Vector2) -> Vector2:
	var vp := get_viewport().get_visible_rect().size
	return camera.position + (p - vp / 2) / camera.zoom


func world_to_screen(p: Vector2) -> Vector2:
	var vp := get_viewport().get_visible_rect().size
	return (p - camera.position) * camera.zoom + vp / 2


func _zoom_at(screen_p: Vector2, factor: float) -> void:
	var before := screen_to_world(screen_p)
	var z := clampf(camera.zoom.x * factor, ZOOM_MIN, ZOOM_MAX)
	camera.zoom = Vector2(z, z)
	camera.position += before - screen_to_world(screen_p)
	_clamp_camera()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouse and event.device == InputEvent.DEVICE_ID_EMULATION:
		return  # touch is handled below
	if event is InputEventScreenTouch:
		if event.pressed:
			_touches[event.index] = event.position
			if _touches.size() == 1:
				_begin_press(event.position)
			elif _touches.size() == 2:
				_moved = true
				_pressing = false
				_drawing_road = false
				_pinch_dist = _pinch_distance()
		else:
			var was_single := _touches.size() == 1
			_touches.erase(event.index)
			if was_single:
				_end_press(event.position)
	elif event is InputEventScreenDrag:
		_touches[event.index] = event.position
		if _touches.size() == 1:
			_drag(event.position, event.relative)
		elif _touches.size() == 2:
			var d := _pinch_distance()
			if _pinch_dist > 0.0 and d > 0.0:
				var mid: Vector2 = (_touches.values()[0] + _touches.values()[1]) / 2.0
				_zoom_at(mid, d / _pinch_dist)
				camera.position -= event.relative / 2.0 / camera.zoom.x
			_pinch_dist = d
	elif event is InputEventMouseButton:
		match event.button_index:
			MOUSE_BUTTON_LEFT:
				_mouse_down = event.pressed
				if event.pressed:
					_begin_press(event.position)
				else:
					_end_press(event.position)
			MOUSE_BUTTON_WHEEL_UP:
				if event.pressed:
					_zoom_at(event.position, 1.12)
			MOUSE_BUTTON_WHEEL_DOWN:
				if event.pressed:
					_zoom_at(event.position, 1.0 / 1.12)
			MOUSE_BUTTON_RIGHT:
				if event.pressed and input_lock == "":
					cancel_mode()
	elif event is InputEventMouseMotion and _mouse_down:
		_drag(event.position, event.relative)
	elif event is InputEventMagnifyGesture:
		_zoom_at(event.position, event.factor)
	elif event is InputEventPanGesture:
		camera.position += event.delta * 10.0 / camera.zoom.x
		_clamp_camera()


func _pinch_distance() -> float:
	var v: Array = _touches.values()
	return (v[0] - v[1]).length() if v.size() >= 2 else 0.0


func _begin_press(p: Vector2) -> void:
	_press_pos = p
	_press_time = _time
	_pressing = true
	_moved = false
	_velocity = Vector2.ZERO
	var tile := Iso.to_tile(screen_to_world(p))
	_drag_ghost = (mode == Mode.PLACE or mode == Mode.MOVE) and ghost != null and _ghost_covers(tile)
	_drawing_road = mode == Mode.ROAD


func _drag(p: Vector2, rel: Vector2) -> void:
	if not _moved and (p - _press_pos).length() < 14.0:
		return
	_moved = true
	_pressing = false
	var tile := Iso.to_tile(screen_to_world(p))
	if _drag_ghost:
		_set_ghost_tile(_tile_for_size(tile, _ghost_size()))
		return
	if _drawing_road:
		var start := Iso.to_tile(screen_to_world(_press_pos))
		road_start = start
		_last_road_end = tile
		_set_road_preview(_road_path(start, tile))
		hud.show_road_bar(_road_cost_text(), not road_tiles.is_empty())
		return
	camera.position -= rel / camera.zoom.x
	_clamp_camera()
	var now := Time.get_ticks_msec()
	var dt := maxf(0.001, (now - _last_drag_time) / 1000.0)
	_last_drag_time = now
	_velocity = _velocity.lerp(rel / dt, 0.4) if dt < 0.1 else Vector2.ZERO


func _end_press(p: Vector2) -> void:
	_pressing = false
	if mode == Mode.MOVE and _drag_ghost and _moved:
		_drag_ghost = false
		return
	if not _moved:
		_velocity = Vector2.ZERO
		_tap(p)
	elif Time.get_ticks_msec() - _last_drag_time > 80:
		_velocity = Vector2.ZERO
	_drawing_road = false


func _long_press(p: Vector2) -> void:
	if input_lock != "":
		return
	var v := pick_view(screen_to_world(p))
	if v and Game.buildings[v.uid].priv == "":
		Input.vibrate_handheld(40)
		start_move(v.uid)
		_drag_ghost = true
		_moved = true


func _road_path(a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	if road_type == "remove":
		return Game.removable_path(a, b)
	return Game.road_path(a, b, road_type)


func _tap(screen_p: Vector2) -> void:
	var wp := screen_to_world(screen_p)
	var tile := Iso.to_tile(wp)
	match mode:
		Mode.NONE:
			if input_lock != "" and input_lock != "collect" and input_lock != "info":
				Game.sfx("tap")
				return
			var agent: Variant = life.pick(wp)
			if agent != null and input_lock == "":
				life.tapped(agent)
				return
			for a in forest_animals + zoo_animals:
				if is_instance_valid(a) and a.hit(wp):
					if input_lock == "":
						a.tapped()
					return
			var v := pick_view(wp)
			if v:
				_tap_building(v)
				return
			if input_lock != "":
				Game.sfx("tap")
				return
			var sign := _sign_at(wp)
			if sign != Vector2i(-1, -1):
				hud.open_plot(sign)
			elif Game.tree_at(tile) != "" and Game.is_owned(tile):
				hud.confirm(Loc.t("tree_q") % Data.TREE_CLEAR_COST, func(): Game.clear_tree(tile))
			elif _lamp_at(wp) != Vector2i(-99, -99):
				var q := _lamp_at(wp)
				hud.confirm(Loc.t("lamp_remove_q"), func(): Game.remove_lamp(q))
			elif Game.roads.has(tile) and Game.is_intersection(tile):
				hud.confirm(Loc.t("light_remove_q") if Game.lights.has(tile) else Loc.t("light_add_q") % Data.LIGHT_COST,
					func(): Game.toggle_light(tile))
			else:
				Game.sfx("tap")
		Mode.LAND:
			if Data.in_land(tile) and Game.plot_buyable(Data.plot_of(tile)):
				hud.open_plot(Data.plot_of(tile))
			else:
				Game.sfx("error")
		Mode.PLACE, Mode.MOVE:
			if _ghost_covers(tile):
				confirm_mode()
			else:
				_set_ghost_tile(_tile_for_size(tile, _ghost_size()))
		Mode.ROAD:
			if road_start == Vector2i(-1, -1):
				road_start = tile
				_last_road_end = Vector2i(-1, -1)
				_set_road_preview(_road_path(tile, tile))
			elif tile == _last_road_end and not road_tiles.is_empty():
				confirm_mode()
				return
			else:
				_last_road_end = tile
				_set_road_preview(_road_path(road_start, tile))
			hud.show_road_bar(_road_cost_text(), not road_tiles.is_empty())
		Mode.LAMP:
			var q := _quarter_at(wp)
			if Game.place_lamp(q, lamp_style):
				hud.show_lamp_bar()
		Mode.LINK:
			var v := pick_view(wp)
			if v and v.uid != link_from:
				if Game.link_homes(link_from, v.uid):
					cancel_mode()
			else:
				Game.sfx("error")
		Mode.DEMOLISH:
			var v := pick_view(wp)
			if v:
				demolish_target = {"uid": v.uid}
				_show_cursors(_footprint(v.tile, v.size), "cursor_sel")
				hud.show_mode_bar(Loc.t("demolish_q") % [Data.name_of(v.id), Game.refund_of(v.uid)], "", true)
			elif _lamp_at(wp) != Vector2i(-99, -99):
				demolish_target = {"lamp": _lamp_at(wp)}
				hud.show_mode_bar(Loc.t("lamp_remove_q"), "", true)
			elif Game.roads.has(tile):
				demolish_target = {"road": tile}
				_show_cursors(_tiles([tile]), "cursor_sel")
				hud.show_mode_bar(Loc.t("demolish_road_q"), "", true)
			else:
				Game.sfx("error")


func _sign_at(wp: Vector2) -> Vector2i:
	for s in sale_signs:
		var d := wp - s.position
		if absf(d.x) < 40 and d.y < 20 and d.y > -110:
			return s.get_meta("plot")
	return Vector2i(-1, -1)


## Lamp slot under a point: the nearest sidewalk corner of a road tile.
func _quarter_at(wp: Vector2) -> Vector2i:
	var g := Iso.to_grid(wp)
	var t := Vector2i(floori(g.x), floori(g.y))
	var f := g - Vector2(t)
	return Vector2i(2 * t.x + (1 if f.x > 0.5 else 0), 2 * t.y + (1 if f.y > 0.5 else 0))


func _lamp_at(wp: Vector2) -> Vector2i:
	for q in lamp_nodes:
		if lamp_nodes[q].hit(wp):
			return q
	return Vector2i(-99, -99)


func pick_view(wp: Vector2) -> BuildingView:
	var best: BuildingView = null
	for uid in views:
		var v: BuildingView = views[uid]
		if v.visible and v.contains_point(wp) and (best == null or v.position.y > best.position.y):
			best = v
	return best


func _tap_building(v: BuildingView) -> void:
	v.bounce()
	var res := Game.collect(v.uid)
	if not res.is_empty():
		var top := v.global_position + Vector2(0, v.top_y() - 20)
		hud.fly_reward(world_to_screen(top), res)
		float_text(top, "+%s" % Loc.num(res.get("coins", res.get("goods", 0))))
		hud.tutorial_event("collect")
		return
	if input_lock != "" and input_lock != "info":
		Game.sfx("tap")
		return
	Game.sfx("tap")
	hud.show_info(v.uid)


func float_text(pos: Vector2, text: String, col := Color("fff4b0")) -> void:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", hud.font)
	l.add_theme_font_size_override("font_size", 30)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color("221c28"))
	l.add_theme_constant_override("outline_size", 10)
	l.z_index = 60
	sky.add_child(l)
	l.position = pos - Vector2(l.get_minimum_size().x / 2, 16)
	var tw := l.create_tween().set_parallel()
	tw.tween_property(l, "position:y", l.position.y - 60, 0.9).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tw.tween_property(l, "modulate:a", 0.0, 0.4).set_delay(0.6)
	tw.chain().tween_callback(l.queue_free)


func puff(pos: Vector2, n: int) -> void:
	var dust := CPUParticles2D.new()
	dust.texture = Assets.tex("fx/puff")
	dust.one_shot = true
	dust.explosiveness = 1.0
	dust.amount = 20 * n
	dust.lifetime = 1.1
	dust.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	dust.emission_sphere_radius = n * 70.0
	dust.spread = 180.0
	dust.initial_velocity_min = 40.0
	dust.initial_velocity_max = 90.0
	dust.gravity = Vector2(0, -12)
	dust.scale_amount_min = 2.4
	dust.scale_amount_max = 4.0
	var grad := Gradient.new()
	grad.set_color(0, Color(0.85, 0.8, 0.7, 0.9))
	grad.set_color(1, Color(0.85, 0.8, 0.7, 0.0))
	dust.color_ramp = grad
	dust.position = pos
	dust.z_index = 40
	add_child(dust)
	dust.emitting = true
	dust.finished.connect(dust.queue_free)


# ====================================================================== modes
func _ghost_size() -> int:
	if mode == Mode.MOVE and Game.buildings.has(move_uid):
		return Data.B[Game.buildings[move_uid].id].size
	return Data.B[place_id].size if place_id != "" else 1


func start_place(id: String) -> void:
	cancel_mode()
	if id == "lamp":
		start_lamp()
		return
	mode = Mode.PLACE
	place_id = id
	rot_auto = true
	ghost = Sprite2D.new()
	ghost.centered = false
	ghost.z_index = 30
	world.add_child(ghost)
	ground.set_overlay(1.0)
	_set_ghost_tile(_best_spot(id))
	hud.show_place_bar(id)


## A sensible first position for the ghost: the visible free spot of the right zone next to a road.
func _best_spot(id: String) -> Vector2i:
	var n: int = Data.B[id].size
	var center := Iso.to_tile(camera.position)
	var best := _tile_for_size(center, n)
	var best_d := 1e9
	for c in Game.roads:
		for d in Iso.DIRS:
			var t: Vector2i = c + d
			if d.x < 0 or d.y < 0:
				t = c + d * n
			if Game.can_place(id, t.x, t.y):
				var dist := Vector2(t - center).length()
				if dist < best_d:
					best_d = dist
					best = t
	return best


func rotate_ghost() -> void:
	if ghost == null:
		return
	rot_auto = false
	place_rot = (place_rot + 1) % 4
	_set_ghost_tile(ghost_tile)


func start_move(uid: int) -> void:
	cancel_mode()
	if not Game.buildings.has(uid):
		return
	mode = Mode.MOVE
	move_uid = uid
	var b: Dictionary = Game.buildings[uid]
	place_id = b.id
	place_rot = int(b.get("rot", 0))
	rot_auto = false
	if views.has(uid):
		views[uid].modulate.a = 0.35
	ghost = Sprite2D.new()
	ghost.centered = false
	ghost.z_index = 30
	world.add_child(ghost)
	ground.set_overlay(1.0)
	_set_ghost_tile(Vector2i(b.x, b.y))
	hud.show_mode_bar(Loc.t("move_title") % Data.name_of(b.id), Loc.t("move_hint"), true)


func start_road() -> void:
	cancel_mode()
	mode = Mode.ROAD
	road_start = Vector2i(-1, -1)
	_last_road_end = Vector2i(-1, -1)
	road_tiles.clear()
	ground.set_overlay(0.6)
	hud.show_road_bar(_road_cost_text(), false)


func start_lamp() -> void:
	cancel_mode()
	if Game.level < int(Data.B.lamp.lvl):
		hud.toast(Loc.t("locked_lvl") % Data.B.lamp.lvl)
		return
	mode = Mode.LAMP
	hud.show_lamp_bar()


func start_land() -> void:
	cancel_mode()
	mode = Mode.LAND
	ground.set_overlay(1.0)
	var marks: Array[Vector2i] = []
	hud.show_mode_bar(Loc.t("land_title"), Loc.t("land_hint"), false)


func start_link(uid: int) -> void:
	cancel_mode()
	mode = Mode.LINK
	link_from = uid
	var b: Dictionary = Game.buildings[uid]
	var marks: Array[Vector2i] = []
	for o in Game.buildings:
		if Game.can_link(uid, o):
			var ob: Dictionary = Game.buildings[o]
			marks.append_array(_footprint(Vector2i(ob.x, ob.y), Data.B[ob.id].size))
	_show_cursors(marks, "cursor_road")
	_add_cursors(_footprint(Vector2i(b.x, b.y), Data.B[b.id].size), "cursor_sel")
	hud.show_mode_bar(Loc.t("link_title"), Loc.t("link_hint") % Game.link_cost(), false)


func set_road_type(t: String) -> void:
	road_type = t
	if road_start != Vector2i(-1, -1):
		var end := _last_road_end if _last_road_end != Vector2i(-1, -1) else road_start
		_set_road_preview(_road_path(road_start, end))
	hud.show_road_bar(_road_cost_text(), not road_tiles.is_empty())


func start_demolish() -> void:
	cancel_mode()
	mode = Mode.DEMOLISH
	demolish_target = {}
	hud.show_mode_bar(Loc.t("hint_demolish"), "", false)


func cancel_mode() -> void:
	if ghost:
		ghost.queue_free()
		ghost = null
	if mode == Mode.MOVE and views.has(move_uid):
		views[move_uid].modulate.a = 1.0
	_show_cursors(_tiles([]), "")
	if mode in [Mode.PLACE, Mode.MOVE, Mode.ROAD, Mode.LAND]:
		ground.set_overlay(0.0)
	mode = Mode.NONE
	place_id = ""
	move_uid = 0
	link_from = 0
	road_tiles.clear()
	road_start = Vector2i(-1, -1)
	demolish_target = {}
	if hud:
		hud.hide_mode_bar()


func confirm_mode() -> void:
	match mode:
		Mode.PLACE:
			if Game.place(place_id, ghost_tile.x, ghost_tile.y, place_rot) > 0:
				var id := place_id
				cancel_mode()
				hud.tutorial_event("placed:" + id)
				if Data.B[id].cat == "decor" and Game.coins >= Data.B[id].cost and input_lock == "":
					start_place(id)
		Mode.MOVE:
			if Game.move_building(move_uid, ghost_tile.x, ghost_tile.y, place_rot):
				cancel_mode()
		Mode.ROAD:
			var ok := Game.remove_roads(road_tiles) if road_type == "remove" else Game.build_roads(road_tiles, road_type)
			if ok:
				road_start = Vector2i(-1, -1)
				_last_road_end = Vector2i(-1, -1)
				_set_road_preview(_tiles([]))
				hud.show_road_bar(_road_cost_text(), false)
				hud.tutorial_event("road")
		Mode.DEMOLISH:
			if demolish_target.has("uid"):
				Game.demolish(demolish_target.uid)
			elif demolish_target.has("road"):
				Game.remove_road(demolish_target.road)
			elif demolish_target.has("lamp"):
				Game.remove_lamp(demolish_target.lamp)
			demolish_target = {}
			_show_cursors(_tiles([]), "")
			hud.show_mode_bar(Loc.t("hint_demolish"), "", false)
		Mode.LAMP, Mode.LINK, Mode.LAND:
			cancel_mode()


func _tile_for_size(tile: Vector2i, n: int) -> Vector2i:
	return tile - Vector2i((n - 1) / 2, (n - 1) / 2)


func _tiles(list: Array) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	out.assign(list)
	return out


func _ghost_covers(tile: Vector2i) -> bool:
	if ghost == null:
		return false
	var n := _ghost_size()
	return tile.x >= ghost_tile.x and tile.y >= ghost_tile.y and tile.x < ghost_tile.x + n and tile.y < ghost_tile.y + n


func _set_ghost_tile(t: Vector2i) -> void:
	ghost_tile = t
	var n := _ghost_size()
	if rot_auto:
		place_rot = Game.facing_for(t.x, t.y, n, place_rot)
	var name := Assets.building_sprite(place_id, 1 if mode == Mode.PLACE else Game.buildings[move_uid].lvl, place_rot)
	var m := Assets.meta(name)
	ghost.texture = Assets.tex("buildings/" + name)
	ghost.position = Iso.vertex(t.x + n * 0.5, t.y + n * 0.5)
	ghost.offset = Vector2(m.o[0], m.o[1]) + Vector2(0, n * Iso.HY)
	var why := Game.place_problem(place_id, t.x, t.y, move_uid)
	var ok := why == ""
	ghost.modulate = Color(1, 1, 1, 0.68) if ok else Color(1, 0.45, 0.45, 0.6)
	_show_cursors(_footprint(t, n), "cursor_ok" if ok else "cursor_bad")
	# roads around the footprint glow so you can see the building will be connected
	var around: Array[Vector2i] = []
	for i in n:
		for c in [Vector2i(t.x + i, t.y - 1), Vector2i(t.x + i, t.y + n), Vector2i(t.x - 1, t.y + i), Vector2i(t.x + n, t.y + i)]:
			if Game.net.has(c):
				around.append(c)
	_add_cursors(around, "cursor_road")
	if mode == Mode.PLACE:
		hud.place_hint(why, not around.is_empty())


func _footprint(t: Vector2i, n: int) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for dy in n:
		for dx in n:
			out.append(t + Vector2i(dx, dy))
	return out


func _show_cursors(tiles: Array[Vector2i], tex_name: String) -> void:
	for c in cursors.get_children():
		c.queue_free()
	_add_cursors(tiles, tex_name)


func _add_cursors(tiles: Array[Vector2i], tex_name: String) -> void:
	if tex_name == "":
		return
	for t in tiles:
		var s := Sprite2D.new()
		s.texture = Assets.tex("ui/" + tex_name)
		s.position = Iso.center(t)
		cursors.add_child(s)


func _set_road_preview(tiles: Array[Vector2i]) -> void:
	road_tiles = tiles
	_show_cursors(tiles, "cursor_bad" if road_type == "remove" else "cursor_ok")
	if road_start != Vector2i(-1, -1) and not tiles.has(road_start):
		_add_cursors(_tiles([road_start]), "cursor_sel")


func _road_cost_text() -> String:
	if road_tiles.is_empty():
		if road_type == "remove":
			return Loc.t("hint_road_remove")
		return Loc.t("hint_road_start") if road_start == Vector2i(-1, -1) else Loc.t("hint_road_end")
	if road_type == "remove":
		return Loc.t("road_remove_cost") % [road_tiles.size(), Loc.num(Game.road_refund(road_tiles))]
	return Loc.t("road_cost") % [road_tiles.size(), Loc.num(Game.road_cost(road_tiles, road_type))]


# ====================================================================== android back
func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		if hud and hud.back():
			return
		if mode != Mode.NONE:
			cancel_mode()
			return
		hud.confirm(Loc.t("quit_q"), _quit)


func _quit() -> void:
	Game.save_game()
	get_tree().quit()


class Critter extends Sprite2D:
	var velocity := Vector2.ZERO
	var life := 10.0
	var _t := randf()

	func _process(delta: float) -> void:
		position += velocity * delta
		_t += delta
		frame = int(_t * 5.0) % 2
		flip_h = velocity.x < 0
		life -= delta
		if life <= 0.0:
			queue_free()
