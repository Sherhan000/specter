extends Node
## Dev only: screenshots of the game in many states. Not exported.
## SHOT_DIR = output folder, SHOT_SET = "intro" | "game" (default game), SHOT_LANG = ru | en

var out := ""
var city


func _ready() -> void:
	out = OS.get_environment("SHOT_DIR") + "/"
	var lang := OS.get_environment("SHOT_LANG")
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json"))
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json.bak"))
	Events.reset()
	Game.new_game()
	if lang != "":
		Game.settings.lang = lang
		Loc.lang = lang
	var set_name := OS.get_environment("SHOT_SET")
	if set_name == "intro":
		Game.profile = {"name": "", "age": 0, "gender": "", "privacy": false, "intro": false}
		city = load("res://scenes/main.tscn").instantiate()
		add_child(city)
		await _wait(1.2)
		await _shot("i0_logo_early")
		await _wait(2.8)
		await _shot("i1_logo")
		var intro: Intro = city.hud.get_children().filter(func(c): return c is Intro)[0]
		intro.stage = 1
		intro._profile()
		await _wait(0.4)
		intro._name_edit.text = "Шерзод" if Loc.lang == "ru" else "Alex"
		intro._gender = "m"
		intro._set_age(24)
		intro._validate()
		await _wait(0.2)
		await _shot("i2_profile")
		intro._privacy()
		await _wait(0.4)
		await _shot("i3_privacy")
		intro._accept.button_pressed = true
		intro._accept_btn.emit_signal("pressed")
		await _wait(1.4)
		await _shot("i4_tutorial")
		city.hud.dialog._next(false)
		city.hud.dialog._next(false)
		city.hud.dialog._next(false)
		await _wait(0.6)
		await _shot("i5_tut_collect")
		get_tree().quit()
		return
	Game.profile = {"name": "Шерзод" if Loc.lang == "ru" else "Alex", "age": 24, "gender": "m", "privacy": true, "intro": true}
	Game.tutorial = 99
	# a richer city for the screenshots
	_grow_city()
	if set_name == "ux":
		await _ux()
		get_tree().quit()
		return
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	await _wait(3.0)
	Game.day_time = 0.42
	await _wait(5.0)
	await _shot("g1_city")
	city.hud.dialog.visible = false
	city.hud.dialog._lines.clear()
	city.camera.zoom = Vector2(2.0, 2.0)
	city.camera.position = Iso.center(Vector2i(Data.CENTER, Data.CENTER))
	await _wait(1.0)
	await _shot("g2_close")
	city.camera.zoom = Vector2(0.4, 0.4)
	city.camera.position = Iso.center(Vector2i(Data.CENTER - 4, Data.CENTER - 4))
	await _wait(1.0)
	await _shot("g3_far")
	city.camera.zoom = Vector2(1.0, 1.0)
	city.camera.position = Iso.center(Vector2i(Data.LAND0 - 6, Data.CENTER))
	await _wait(1.5)
	await _shot("g4_forest")
	city.camera.position = Iso.center(Vector2i(Data.CENTER + 2, Data.CENTER))
	city.camera.zoom = Vector2(1.2, 1.2)
	city.hud.toggle_build_menu()
	await _wait(0.4)
	await _shot("g5_menu")
	city.hud.toggle_build_menu()
	var uid: int = Game.buildings.keys()[0]
	city.hud.show_info(uid)
	await _wait(0.4)
	await _shot("g6_info")
	city.hud.info_panel.visible = false
	city.start_place("cottage")
	await _wait(0.4)
	await _shot("g7_place")
	city.cancel_mode()
	Game.today = {"day": Game.day, "in": {"rent": 320, "shops": 210}, "out": {"build": 450}}
	Game.ledger = [{"day": 1, "in": {"rent": 200, "shops": 100}, "out": {"upkeep": 180, "roads": 20}},
		{"day": 2, "in": {"rent": 260, "shops": 160, "taxes": 90}, "out": {"upkeep": 210, "roads": 22}}]
	city.hud.panels.finance()
	await _wait(0.5)
	await _shot("g8_finance")
	city.hud.close_modal()
	Events._violation()
	Events._proposal()
	city.hud.panels.inbox()
	await _wait(0.5)
	await _shot("g9_inbox")
	city.hud.close_modal()
	city.hud.panels.city_info()
	await _wait(0.5)
	await _shot("g10_rules")
	city.hud.close_modal()
	Events.chapter = 1
	Events.flags["done_boris_houses"] = true
	Game.level = 3
	Events._check_story()
	await _wait(1.5)
	await _shot("g11_dialog")
	city.hud.dialog._next(false)
	await _wait(1.5)
	await _shot("g12_dialog2")
	city.hud.dialog.visible = false
	Game.set_weather("rain", 5)
	Game.day_time = 0.86
	await _wait(3.0)
	await _shot("g13_rain_evening")
	Game.set_weather("storm", 5)
	Game.day_time = 0.95
	await _wait(4.0)
	await _shot("g14_storm_night")
	Game.day = 13
	Game.season = "winter"
	Game.set_weather("snow", 5)
	Game.day_time = 0.45
	await _wait(25.0)
	await _shot("g15_winter")
	get_tree().quit()


func _mouse(pos: Vector2, pressed: bool) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = pressed
	e.position = pos
	e.global_position = pos
	Input.parse_input_event(e)


func _move(pos: Vector2, rel: Vector2) -> void:
	var e := InputEventMouseMotion.new()
	e.position = pos
	e.global_position = pos
	e.relative = rel
	e.button_mask = MOUSE_BUTTON_MASK_LEFT
	Input.parse_input_event(e)


func _drag(a: Vector2, b: Vector2, hold := 0.0) -> void:
	_mouse(a, true)
	await _wait(0.05 + hold)
	var steps := 12
	for i in steps:
		var p := a.lerp(b, (i + 1.0) / steps)
		_move(p, (b - a) / steps)
		await get_tree().process_frame


func _ux() -> void:
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	Events.chapter = 9
	await _wait(2.5)
	city.hud.dialog.visible = false
	Game.day_time = 0.45
	var c := Data.CENTER
	city.camera.zoom = Vector2(1.3, 1.3)
	city.camera.position = Iso.center(Vector2i(c, c))
	await _wait(0.5)
	# long press on a building and drag it somewhere else
	var uid: int = 0
	for u in Game.buildings:
		if Game.buildings[u].id == "cottage":
			uid = u
			break
	var bv: BuildingView = city.views[uid]
	var sp: Vector2 = city.world_to_screen(bv.global_position + Vector2(0, -20))
	_mouse(sp, true)
	await _wait(0.7)
	for i in 10:
		_move(sp + Vector2(-8 * i, 5 * i), Vector2(-8, 5))
		await get_tree().process_frame
	await _wait(0.2)
	await _shot("u1_move_drag")
	_mouse(sp + Vector2(-80, 50), false)
	city.cancel_mode()
	# drag a road with a finger
	city.start_road()
	await _wait(0.2)
	var a: Vector2 = city.world_to_screen(Iso.center(Vector2i(c + 2, c - 3)))
	var b: Vector2 = city.world_to_screen(Iso.center(Vector2i(c + 6, c - 5)))
	await _drag(a, b)
	await _wait(0.2)
	await _shot("u2_road_drag")
	_mouse(b, false)
	city.confirm_mode()
	city.cancel_mode()
	await _wait(0.3)
	# lamp tool
	city.start_lamp()
	for q in [Vector2i(2 * c + 7, 2 * c + 3), Vector2i(2 * c + 11, 2 * c + 3)]:
		Game.place_lamp(q, "classic")
	await _wait(0.2)
	await _shot("u3_lamps")
	city.cancel_mode()
	# link two homes
	var homes: Array = Game.buildings.keys().filter(func(u): return Data.B[Game.buildings[u].id].cat == "home")
	city.start_link(homes[0])
	await _wait(0.3)
	await _shot("u4_link_mode")
	city.cancel_mode()
	Game.link_homes(homes[0], homes[1])
	Game.day_time = 0.92
	await _wait(1.0)
	await _shot("u5_garland_night")
	Game.day_time = 0.45
	# a person speaks and a car honks
	await _wait(1.0)
	var w = null
	for x in city.life.walkers:
		if is_instance_valid(x):
			w = x
			break
	if w:
		city.camera.position = w.position
		w.tapped()
	for x in city.life.cars:
		if is_instance_valid(x) and not x.on_highway:
			x.tapped()
			break
	await _wait(0.4)
	await _shot("u6_speech")
	# fire with a fire station nearby, then a police chase
	var fs := Game._add_building("fire_station", c - 8, c - 3, true)
	var ps := Game._add_building("police", c + 4, c - 4, true)
	Game.recalc()
	city._add_view(fs)
	city._add_view(ps)
	var target: int = homes[2]
	Events.start_fire(target)
	city.camera.position = city.views[target].position
	await _wait(3.0)
	await _shot("u7_fire")
	Events.crime.emit(true)
	await _wait(0.5)
	var thief = null
	for x in city.life.cars:
		if is_instance_valid(x) and x.role == "thief":
			thief = x
	if thief:
		city.camera.zoom = Vector2(1.0, 1.0)
		for k in 30:
			city.camera.position = thief.position
			await get_tree().process_frame
		await _wait(1.8)
		city.camera.position = thief.position
	await _shot("u8_chase")
	# forest animal popup and the zoo
	city.camera.position = Iso.center(Vector2i(Data.LAND0 - 5, c))
	await _wait(5.0)
	if not city.forest_animals.is_empty():
		city.camera.position = city.forest_animals[0].position
		city.hud.animal_popup(city.forest_animals[0])
	await _wait(0.4)
	await _shot("u9_animal")
	city.hud.close_modal()
	Game.caught = ["deer", "fox", "rabbit", "boar", "wolf", "bear"]
	Game.plots.append(Vector2i(1, 3))
	Game.plots.append(Vector2i(2, 3))
	city.refresh_ground()
	var zoo := Game._add_building("zoo", Data.LAND0 + 12, Data.LAND0 + 28, true)
	Game.buildings[zoo].lvl = 3
	Game.roads[Vector2i(Data.LAND0 + 14, Data.LAND0 + 29)] = "asphalt"
	Game._rebuild_net()
	Game.recalc()
	city._add_view(zoo)
	city._rebuild_zoo_animals()
	city.camera.zoom = Vector2(1.6, 1.6)
	city.camera.position = city.views[zoo].position + Vector2(0, -40)
	await _wait(2.0)
	await _shot("u10_zoo")


func _grow_city() -> void:
	var c := Data.CENTER
	Game.level = 8
	Game.coins = 50000
	for i in range(c - 5, c + 1):
		Game.roads[Vector2i(i, c + 5)] = "stone"
	for i in range(c + 1, c + 5):
		Game.roads[Vector2i(c - 5, i)] = "asphalt"
	Game.roads[Vector2i(c, c + 5)] = "stone"
	for spec in [["cottage", c - 4, c - 1], ["bungalow", c + 3, c - 1], ["house_small", c - 4, c + 1], ["cafe", c + 3, c + 1],
			["park", c - 4, c + 3], ["cottage", c + 1, c + 3], ["flowershop", c - 2, c + 3], ["farm", c + 9, c + 1],
			["orchard", c + 11, c - 2], ["school", c - 3, c - 4], ["fountain", c + 1, c - 3]]:
		var uid := Game._add_building(spec[0], spec[1], spec[2], true)
		Game.buildings[uid].occ = 8
	Game.lamps[Vector2i(2 * c + 3, 2 * c - 2)] = "modern"
	Game.lamps[Vector2i(2 * c - 4, 2 * c + 2)] = "classic"
	Game.caught = ["deer", "fox"]
	Game._rebuild_net()
	Game.recalc()


func _wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + name + ".png")
