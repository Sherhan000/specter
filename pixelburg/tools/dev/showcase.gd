extends Node
## Dev only: builds a big zoned showcase city and saves the store screenshots. Not exported.
## SHOT_DIR = output folder, SHOT_LANG = ru | en

var out := ""
var city


func _ready() -> void:
	out = OS.get_environment("SHOT_DIR") + "/"
	var lang := OS.get_environment("SHOT_LANG") if OS.get_environment("SHOT_LANG") != "" else "ru"
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json"))
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json.bak"))
	Events.reset()
	Game.new_game()
	Game.settings.lang = lang
	Loc.lang = lang
	Game.profile = {"name": "Шерзод" if lang == "ru" else "Alex", "age": 25, "gender": "m", "privacy": true, "intro": true}
	Game.tutorial = 99
	Events.chapter = 9
	Events.flags = {"zoo_arc": true, "hall_arc": true, "election_done": true}
	Game.level = 22
	Game.coins = 48250
	Game.gems = 27
	Game.goods = 900
	Game.rep = 74
	Game.caught = ["deer", "fox", "rabbit", "boar", "wolf", "bear", "deer", "fox"]
	_build_city()
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	await _wait(1.0)
	Game.happy = 81
	Game.happy_target = 81
	Game.day_time = 0.43
	await _wait(6.0)
	var c := Data.CENTER
	# 1 downtown overview
	_cam(Vector2i(c - 2, c - 2), 0.55)
	await _wait(3.0)
	await _shot("01_city")
	# 2 street life close up
	_cam(Vector2i(c + 3, c), 1.2)
	await _wait(2.0)
	await _shot("02_street")
	# 3 Alina talks
	_cam(Vector2i(c - 6, c - 4), 0.8)
	Events.say([{"who": "alina", "expr": "happy", "text": ["{Title}, жители предлагают открыть новое кафе у парка. Разрешим?",
		"Mayor, residents want to open a new cafe by the park. Shall we allow it?"]}])
	await _wait(3.0)
	await _shot("03_story")
	city.hud.dialog.visible = false
	city.hud.dialog._lines.clear()
	# 4 farms, the highway and the forest
	_cam(Vector2i(c + 20, c - 14), 0.6)
	await _wait(2.5)
	await _shot("04_farms")
	# 5 the leisure zone: zoo and funfair
	for u in Game.buildings:
		if Game.buildings[u].id == "zoo":
			city.camera.position = city.views[u].position + Vector2(90, -60)
			city.camera.zoom = Vector2(0.9, 0.9)
	await _wait(2.0)
	await _shot("05_zoo")
	# 6 the city at night
	Game.day_time = 0.93
	_cam(Vector2i(c - 1, c - 1), 0.7)
	await _wait(5.0)
	await _shot("06_night")
	# 7 a rainy evening
	Game.set_weather("rain", 500)
	Game.day_time = 0.83
	_cam(Vector2i(c + 1, c - 1), 0.9)
	await _wait(4.0)
	await _shot("07_rain")
	# 8 winter
	Game.day = 13
	Game.season = "winter"
	Game.set_weather("snow", 500)
	Game.day_time = 0.47
	_cam(Vector2i(c - 4, c + 2), 0.8)
	await _wait(26.0)
	await _shot("08_winter")
	# the valley and the mountains beyond it
	Game.season = "summer"
	Game.day = 6
	Game.set_weather("clear", 500)
	Game.day_time = 0.72
	city.weather._snow_amt = 0.0
	city.weather.snow.emitting = false
	city.hud.root.visible = false
	_cam(Vector2i(c - 48, c - 48), 0.42)
	city._clamp_camera()
	await _wait(14.0)
	await _shot("09_valley")
	# feature graphic source: night overview without the interface
	Game.season = "summer"
	Game.day = 6
	Game.set_weather("clear", 500)
	Game.day_time = 0.9
	city.hud.root.visible = false
	_cam(Vector2i(c - 3, c - 3), 0.6)
	await _wait(28.0)
	await _shot("fg_night")
	Game.day_time = 0.44
	await _wait(1.0)
	await _shot("fg_day")
	get_tree().quit()


func _place(id: String, x: int, y: int, rng: RandomNumberGenerator) -> void:
	if not Data.B.has(id) or Game.place_problem(id, x, y) != "":
		return
	var uid := Game._add_building(id, x, y, true, rng.randi_range(2, 3) if Data.B[id].cat != "decor" else rng.randi_range(1, 3))
	if Data.B[id].cat == "home":
		Game.buildings[uid].occ = Data.stat(id, "pop", Game.buildings[uid].lvl)
	if rng.randf() < 0.12 and Data.B[id].cat in ["home", "shop", "ind", "fun"]:
		Game.buildings[uid].ready = true


func _pick(list: Array, size: int, rng: RandomNumberGenerator) -> String:
	var ok := list.filter(func(id): return Data.B.has(id) and maxi(1, Data.B[id].size) == size)
	return "" if ok.is_empty() else ok[rng.randi() % ok.size()]


## A street grid every 7 tiles around the centre; every block is four 3x3 lots facing the streets.
func _build_city() -> void:
	Game.plots = []
	for py in Data.PLOTS:
		for px in Data.PLOTS:
			Game.plots.append(Vector2i(px, py))
	Game.roads.clear()
	Game.buildings.clear()
	Game.occ.clear()
	Game.lamps.clear()
	Game.lights.clear()
	var c := Data.CENTER
	var lines := [c - 28, c - 21, c - 14, c - 7, c, c + 7, c + 14, c + 21, c + 28]
	for k in range(c - 28, c + 29):
		for l in lines:
			for t in [Vector2i(k, l), Vector2i(l, k)]:
				var z := Data.zone_at(t)
				var tp := "dirt" if z == "farm" else "stone" if (absi(t.x - c) <= 7 and absi(t.y - c) <= 7) else "asphalt"
				if not Game.roads.has(t) or tp == "stone":
					Game.roads[t] = tp
	# avenues out to the regional roads
	for k in range(Data.LAND0, Data.LAND1):
		for t in [Vector2i(k, c), Vector2i(c, k)]:
			if not Game.roads.has(t):
				Game.roads[t] = "asphalt"
	for t in Game.natural_trees:
		if Data.zone_at(t) != "leisure" or Game.roads.has(t):
			Game.cleared_trees[t] = true
	Game._rebuild_net()
	var rng := RandomNumberGenerator.new()
	rng.seed = 21
	for bi in lines.size() - 1:
		for bj in lines.size() - 1:
			var x0: int = lines[bi] + 1
			var y0: int = lines[bj] + 1
			var z := Data.zone_at(Vector2i(x0 + 2, y0 + 2))
			var ring := maxi(absi(x0 + 3 - c), absi(y0 + 3 - c)) / 7
			var big: Array
			var small: Array
			var decor := ["tree", "flowerbed", "tree"]
			match z:
				"farm":
					big = ["farm", "orchard", "greenhouse", "ranch", "farm", "orchard"]
					small = ["tree", "tree", "tree", "gas_station"]
					decor = ["tree"]
				"industry":
					big = ["sawmill", "workshop", "factory", "logistics", "warehouse", "fire_station", "parking"]
					small = ["tree", "tree", "gas_station"]
					decor = ["tree"]
				"leisure":
					big = ["park", "zoo", "funfair", "stadium", "museum", "pond", "plaza", "restaurant", "hotel"]
					small = ["cafe", "fountain", "bench", "pizzeria", "statue", "playground"]
					decor = ["tree", "fountain", "bench"]
				_:
					if ring <= 1:
						big = ["mall", "town_hall", "tower", "condo", "tower", "condo", "apartments", "tower", "office", "cinema", "restaurant", "bank", "hospital", "hotel", "plaza"]
						small = ["boutique", "cafe", "flowershop", "pharmacy", "bakery", "pizzeria"]
						decor = ["fountain", "statue", "tree", "flowerbed"]
					elif ring <= 2:
						big = ["townhouse", "apartments", "condo", "apartments", "school", "police", "townhouse", "library", "park", "supermarket", "condo", "apartments"]
						small = ["bakery", "cafe", "cottage", "bungalow", "cottage", "house_small", "kindergarten", "pharmacy"]
					else:
						big = ["townhouse", "villa", "park", "villa"]
						small = ["house_small", "cottage", "bungalow", "house_small", "playground"]
			for q in 4:
				var west := q % 2 == 0
				var north := q < 2
				var qx := x0 + (0 if west else 3)
				var qy := y0 + (0 if north else 3)
				var roll := rng.randf()
				var id3 := _pick(big, 3, rng)
				if id3 != "" and roll < 0.3:
					_place(id3, qx, qy, rng)
					continue
				var id2 := _pick(big, 2, rng)
				if id2 != "" and roll < 0.8:
					_place(id2, qx if west else qx + 1, qy if north else qy + 1, rng)
				# the rest of the lot: small buildings along the streets, greenery inside
				for dy in 3:
					for dx in 3:
						var on_street := (dx == 0 and west) or (dx == 2 and not west) or (dy == 0 and north) or (dy == 2 and not north)
						var id: String = _pick(small, 1, rng) if on_street else decor[rng.randi() % decor.size()]
						_place(id, qx + dx, qy + dy, rng)
	# traffic lights on the avenues, lamps along the streets
	for d in [-14, 0, 14]:
		Game.lights[Vector2i(c + d, c)] = true
		Game.lights[Vector2i(c, c + d)] = true
	for t in Game.roads:
		if (t.x + t.y) % 3 == 0 and Data.zone_at(t) != "farm" and Game.lamp_problem(t * 2) == "":
			Game.lamps[t * 2] = "classic" if absi(t.x - c) <= 7 and absi(t.y - c) <= 7 else "modern"
	Game._rebuild_net()
	Game.recalc()
	print("showcase: pop %d, workers %d, jobs %d, staff %.2f" % [Game.pop, Game.workers, Game.jobs, Game.staff])


func _process(_delta: float) -> void:
	# keep the shops stocked so the screenshots are not covered with "no goods" signs
	Game.goods = maxi(Game.goods, 900)


func _cam(c: Vector2i, z: float) -> void:
	city.camera.position = Iso.center(c)
	city.camera.zoom = Vector2(z, z)


func _wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + name + ".png")
