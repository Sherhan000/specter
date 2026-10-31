extends Node
## City state and rules: buildings, roads, land, time of day, seasons and weather, the economy
## (daily ledger, taxes, bank), happiness, population, reputation, city rules, saving, sound and music.

signal changed
signal building_added(uid: int)
signal building_removed(uid: int)
signal building_updated(uid: int)
signal building_moved(uid: int)
signal roads_changed
signal lights_changed
signal lamps_changed
signal water_changed
signal walls_changed
signal paves_changed
signal land_changed
signal trees_changed
signal level_up(level: int)
signal toast(text: String)
signal gem_found(uid: int)
signal phase_changed(phase: String)
signal hour_passed(hour: int)
signal day_passed(day: int)
signal weather_changed(kind: String)
signal season_changed(season: String)
signal animals_changed
signal game_over
signal plane_landed(country: String, pax: int)
signal heist(uid: int, caught: bool, by_mayor: bool)   ## a bank was robbed (life: people run, police chase)
signal disaster_changed(state: String)   ## "start" (danger), "hit"/"safe" (answered), "end"
signal protest_changed(state: String)   ## "start", "end" (people go home) or "force" (the police disperse them)

const SAVE_PATH := "user://city.json"
const SAVE_VERSION := 4
const GARBAGE_MAX := 100.0
const SEASONS := ["spring", "summer", "autumn", "winter"]

# ------------------------------------------------------------------ saved state
var coins := 0
var gems := 0
var goods := 0
var xp := 0
var level := 1
var rank := 0   ## best mayor rank reached (index in Data.RANKS)
var beach: Array = []        ## owned beach segments (0..7, one per plot row)
var flights: Array = []      ## bought airport routes (Data.COUNTRIES ids)
var arrivals := {}           ## country -> travellers who flew in, all time
var arrivals_day := {}       ## country -> travellers who flew in today
var plots: Array = []        ## owned plots (Vector2i)
var roads := {}              ## Vector2i -> road type (player roads)
var lights := {}             ## Vector2i -> true (traffic lights on intersections)
var rings := {}              ## Vector2i -> true (roundabouts on intersections; cars circle the island)
var lamps := {}              ## Vector2i quarter cell -> style ("classic" / "modern")
var buildings := {}          ## uid -> dictionary, see _add_building
var next_uid := 1
var cleared_trees := {}
var water := {}              ## Vector2i -> true: water the player dug (rivers grow into seas and oceans)
var water_body := {}         ## Vector2i -> 1 river, 2 sea, 3 ocean (by the size of the connected water)
var walls := {}              ## Vector2i -> wall type (Data.WALLS)
var quarter_of := {}         ## home uid -> {"homes", "happy", "tile"}: homes joined by walls into one quarter
var road_deco := {}          ## road tile -> decoration along its sidewalks (Data.ROAD_DECO)
var brands := {}             ## residents' brands: brand id (Data.BRANDS) -> {"owner": name, "day": founded}
var crime := {}              ## bank heists and the mayor's record, see _empty_crime()
var disaster := {}           ## natural event with a choice, see _empty_disaster()
var protest := {}            ## residents' anger and the protest going on, see _empty_protest()
var ach := _empty_ach()      ## achievements and the daily login streak, see Ach
var paves := {}              ## Vector2i -> paving on the grass (Data.PAVES); strollers walk on it
var claimed: Array = []
var stats := {"coins_total": 0, "goods_total": 0, "upgrades": 0}
var settings := {"sound": true, "music": true, "lang": "", "ui_scale": 1.0}
var profile := {"name": "", "age": 0, "gender": "", "privacy": false, "intro": false}
var day := 1
var day_time := 0.29
var tax := Data.TAX_DEFAULT
var rep := 50.0
var happy := 55.0
var power_supply := 0.0      ## kW produced right now (village generator + plants + solar by sun and weather)
var power_demand := 0.0      ## kW used by homes, businesses and street lamps
var power_ratio := 1.0       ## share of the demand that is covered (1 while the batteries last)
var light_power := 1.0       ## power_ratio, eased: how bright the lights of the city are
var power_store := 0.0       ## kWh in the solar batteries
var power_cap := 0.0
var water_supply := 0
var water_demand := 0
var water_ratio := 1.0
var _plant_kw := 0.0
var _solar_kw := 0.0
var _demand_kw := 0.0
var peak_pop := 0
var caught: Array = []       ## species names of animals caught for the zoo
var weather := "clear"
var weather_until := 0       ## absolute hour when the weather changes
var patrol_until := 0        ## absolute hour until which a recent watchtower check keeps crime risk down
var mood: Array = []         ## temporary happiness modifiers [{"v", "until", "why"}]
var ledger: Array = []       ## closed days, newest last
var today := {}              ## running ledger of the current day
var loan := {}               ## {"left": int, "daily": int, "days": int}
var deposit := 0
var tutorial := 0
var lost := false

# ------------------------------------------------------------------ derived (recalc)
var net := {}                ## every drivable tile: player roads + highway -> type
var highway := {}           ## the regional roads outside the land (highway + country roads)
var occ := {}                ## tile -> uid
var road_ok := {}
var connected := {}          ## road tiles connected to the highway
var pop := 0
var capacity := 0
var jobs := 0
var workforce := 0
var workers := 0
var staff := 1.0
var unemployment := 0.0
var happy_target := 55.0
var home_happy := {}         ## uid -> int
var home_reasons := {}       ## uid -> Array of [text key, value]
var garbage := 0.0            ## uncollected waste in the city, 0..GARBAGE_MAX
var rules := {}              ## rule -> true if broken
var laws: Array = []         ## passed laws (Data.LAWS ids)
var jam_tiles := {}          ## traffic-light cluster tiles
var natural_trees := {}
var phase := ""
var offline_note := false
var season := "spring"

var _autosave := 0.0
var _paused_at := 0.0
const SIM_SLICES := 8
var _sim_clock := 0.0
var _sim_keys: Array = []
var _sim_pos := 0
var _sim_seen := {}
var _save_task := -1
var _sfx: Array[AudioStreamPlayer] = []
var _sfx_cache := {}
var _music_a: AudioStreamPlayer
var _music_b: AudioStreamPlayer
var _music_track := ""
var _ambient: AudioStreamPlayer
var _ambient_track := ""
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_rng.randomize()
	for i in 12:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_sfx.append(p)
	_music_a = AudioStreamPlayer.new()
	_music_b = AudioStreamPlayer.new()
	_ambient = AudioStreamPlayer.new()
	for m in [_music_a, _music_b, _ambient]:
		m.volume_db = -60.0
		add_child(m)
	highway = Data.regional_roads()
	_gen_trees()
	if not load_game():
		new_game()
	if settings.lang != "":
		Loc.lang = settings.lang
	phase = phase_name()
	season = season_name()


# ====================================================================== world
func _gen_trees() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 7331
	natural_trees.clear()
	# groves: a few clusters on the land, denser towards the forest around it
	var groves: Array[Vector2] = []
	for i in 26:
		groves.append(Vector2(rng.randf_range(Data.LAND0, Data.LAND1), rng.randf_range(Data.LAND0, Data.LAND1)))
	for y in range(Data.LAND0, Data.LAND1):
		for x in range(Data.LAND0, Data.LAND1):
			var c := Vector2i(x, y)
			if _in_start_layout(c):
				continue
			var start := Data.START_PLOTS.has(Data.plot_of(c))
			var zone := Data.zone_at(c)
			var dens := 0.02 if start else (0.1 if zone == "leisure" else 0.05 if zone == "city" else 0.03)
			var edge := mini(mini(x - Data.LAND0, Data.LAND1 - 1 - x), mini(y - Data.LAND0, Data.LAND1 - 1 - y))
			dens += 0.45 * clampf(1.0 - edge / 6.0, 0.0, 1.0)
			for g in groves:
				var d := g.distance_to(Vector2(c))
				if d < 3.5:
					dens += 0.45 * (1.0 - d / 3.5)
			if start:
				dens = minf(dens, 0.15)
			if rng.randf() < dens:
				natural_trees[c] = "tree_%d" % rng.randi_range(0, Scenery.SINGLES - 1)


func _in_start_layout(c: Vector2i) -> bool:
	return c.x >= Data.CENTER - 6 and c.x <= Data.CENTER + 13 and absi(c.y - Data.CENTER) <= 5


func is_owned(c: Vector2i) -> bool:
	var seg := Data.beach_seg(c)
	if seg >= 0:
		return beach.has(seg)
	return Data.in_land(c) and plots.has(Data.plot_of(c))


func tree_at(c: Vector2i) -> String:
	if cleared_trees.has(c) or occ.has(c) or roads.has(c) or water.has(c) or walls.has(c) or paves.has(c):
		return ""
	return natural_trees.get(c, "")


func plot_buyable(p: Vector2i) -> bool:
	if plots.has(p) or p.x < 0 or p.y < 0 or p.x >= Data.PLOTS or p.y >= Data.PLOTS:
		return false
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		if plots.has(p + d):
			return true
	return false


func beach_buyable(i: int) -> bool:
	if i < 0 or i >= Data.PLOTS or beach.has(i):
		return false
	return plots.has(Vector2i(0, i)) or beach.has(i - 1) or beach.has(i + 1)


func buy_beach(i: int, with_gems: bool) -> bool:
	if not beach_buyable(i):
		return false
	var price := Data.beach_price(beach.size())
	if level < price.level and not with_gems:
		toast.emit(Loc.t("locked_lvl") % price.level)
		sfx("error")
		return false
	if not pay(0 if with_gems else price.coins, price.gems if with_gems else 0, "land"):
		return false
	beach.append(i)
	add_xp(price.coins / 60)
	land_changed.emit()
	changed.emit()
	sfx("done")
	toast.emit(Loc.t("beach_bought"))
	save_game()
	return true


func abs_hour() -> int:
	return day * 24 + int(day_time * 24.0)


func hour() -> int:
	return int(day_time * 24.0)


func season_name() -> String:
	return SEASONS[int((day - 1) / Data.SEASON_DAYS) % 4]


func is_female() -> bool:
	return profile.gender == "f"


func mayor_title() -> String:
	return Loc.t("mayor_f" if is_female() else "mayor_m")


# ====================================================================== new / save / load
func new_game() -> void:
	coins = Data.START_COINS
	gems = Data.START_GEMS
	goods = 40
	xp = 0
	level = 1
	plots = Data.START_PLOTS.duplicate()
	beach = []
	flights = []
	arrivals = {}
	arrivals_day = {}
	roads = {}
	lights = {}
	rings = {}
	lamps = {}
	buildings = {}
	occ = {}
	next_uid = 1
	cleared_trees = {}
	water = {}
	water_body = {}
	walls = {}
	road_deco = {}
	paves = {}
	brands = {}
	crime = _empty_crime()
	protest = _empty_protest()
	ach = _empty_ach()
	disaster = _empty_disaster()
	claimed = []
	laws = []
	stats = {"coins_total": 0, "goods_total": 0, "upgrades": 0}
	day = 1
	day_time = 0.29
	tax = Data.TAX_DEFAULT
	rep = 50.0
	rank = 0
	happy = 60.0
	peak_pop = 0
	caught = []
	weather = "clear"
	weather_until = abs_hour() + 6
	mood = []
	ledger = []
	today = _empty_day()
	loan = {}
	deposit = 0
	tutorial = 0
	lost = false
	var c := Data.CENTER
	# a small neighbourhood on a crossroads, and a dirt road out to the first farm
	for i in range(c - 5, c + 7):
		roads[Vector2i(i, c)] = "asphalt"
	for i in range(c + 7, c + 13):
		roads[Vector2i(i, c)] = "dirt"
	for i in range(c - 4, c + 5):
		roads[Vector2i(c, i)] = "asphalt"
	lights[Vector2i(c, c)] = true
	var homes: Array[int] = []
	for t in [Vector2i(c - 4, c - 1), Vector2i(c - 3, c - 1), Vector2i(c - 2, c - 1), Vector2i(c + 2, c - 1),
			Vector2i(c - 4, c + 1), Vector2i(c - 3, c + 1), Vector2i(c + 2, c + 1), Vector2i(c - 1, c - 3), Vector2i(c + 1, c + 3)]:
		homes.append(_add_building("house_small", t.x, t.y, true))
	_add_building("bakery", c + 1, c + 1, true)
	_add_building("cafe", c + 1, c - 1, true)
	_add_building("tree", c - 2, c + 1, true, 2)
	_add_building("tree", c - 1, c + 3, true, 1)
	_add_building("farm", c + 10, c - 2, true)
	for uid in homes:
		buildings[uid].occ = 3
		buildings[uid].ready = randf() < 0.5
	lamps[Vector2i(2 * (c - 3), 2 * c)] = "classic"
	lamps[Vector2i(2 * (c + 3) + 1, 2 * c + 1)] = "classic"
	lamps[Vector2i(2 * c, 2 * (c - 3))] = "classic"
	_rebuild_net()
	recalc()
	happy = happy_target
	season = season_name()


func _empty_day() -> Dictionary:
	return {"day": day, "in": {}, "out": {}}


func _add_building(id: String, x: int, y: int, built: bool, lvl := 1, rot := -1) -> int:
	var uid := next_uid
	next_uid += 1
	if rot < 0:
		rot = facing_for(x, y, maxi(1, Data.B[id].size), 0)
	buildings[uid] = {"id": id, "x": x, "y": y, "lvl": lvl, "rot": rot, "built": built, "upg": false, "prog": 0.0,
		"ready": false, "stocked": false, "occ": 0, "closed": false, "dmg": false, "priv": "", "link": 0, "fire": 0.0,
		"cd_check": 0, "cd_meet": 0, "hlamp": ""}
	_occupy(uid)
	return uid


func _occupy(uid: int) -> void:
	var b: Dictionary = buildings[uid]
	var n: int = Data.B[b.id].size
	var paved := false
	for dy in n:
		for dx in n:
			occ[Vector2i(b.x + dx, b.y + dy)] = uid
			if paves.erase(Vector2i(b.x + dx, b.y + dy)):
				paved = true
	if paved:
		paves_changed.emit()


func _vacate(uid: int) -> void:
	var b: Dictionary = buildings[uid]
	var n: int = Data.B[b.id].size
	for dy in n:
		for dx in n:
			occ.erase(Vector2i(b.x + dx, b.y + dy))


static func _v2(p) -> Vector2i:
	return Vector2i(int(p[0]), int(p[1]))


func to_dict() -> Dictionary:
	return {
		"v": SAVE_VERSION, "time": Time.get_unix_time_from_system(),
		"coins": coins, "gems": gems, "goods": goods, "xp": xp, "level": level,
		"plots": plots.map(func(p): return [p.x, p.y]),
		"beach": beach.duplicate(),
		"flights": flights.duplicate(), "arrivals": arrivals.duplicate(), "arrivals_day": arrivals_day.duplicate(),
		"roads": roads.keys().map(func(v): return [v.x, v.y, roads[v]]),
		"lights": lights.keys().map(func(v): return [v.x, v.y]),
		"rings": rings.keys().map(func(v): return [v.x, v.y]),
		"lamps": lamps.keys().map(func(v): return [v.x, v.y, lamps[v]]),
		"cleared": cleared_trees.keys().map(func(v): return [v.x, v.y]),
		"water": water.keys().map(func(v): return [v.x, v.y]),
		"walls": walls.keys().map(func(v): return [v.x, v.y, walls[v]]),
		"paves": paves.keys().map(func(v): return [v.x, v.y, paves[v]]),
		"brands": brands.duplicate(true),
		"crime": crime.duplicate(true),
		"protest": protest.duplicate(true), "ach": ach.duplicate(true),
		"disaster": disaster.duplicate(true),
		"road_deco": road_deco.keys().map(func(v): return [v.x, v.y, road_deco[v]]),
		"buildings": buildings.keys().map(func(u): return [u, buildings[u]]),
		"next_uid": next_uid, "claimed": claimed, "laws": laws, "stats": stats, "settings": settings, "profile": profile,
		"day": day, "day_time": day_time, "tax": tax, "rep": rep, "happy": happy, "peak_pop": peak_pop,
		"caught": caught, "weather": weather, "weather_until": weather_until, "patrol_until": patrol_until, "mood": mood,
		"ledger": ledger, "today": today, "loan": loan, "deposit": deposit, "garbage": garbage, "tutorial": tutorial, "lost": lost,
		"events": Events.to_dict(), "power_store": power_store, "rank": rank,
	}


## Saves the city (atomically, keeping the previous save as a backup).
func save_game(now := false) -> void:
	_finish_save()
	var data := to_dict()
	_write_save(data)


func _finish_save() -> void:
	if _save_task >= 0:
		WorkerThreadPool.wait_for_task_completion(_save_task)
		_save_task = -1


static func _write_save(data: Dictionary) -> void:
	var text := JSON.stringify(data)
	# keep the previous good save as a backup, then swap the new one in atomically
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.copy_absolute(ProjectSettings.globalize_path(SAVE_PATH), ProjectSettings.globalize_path(SAVE_PATH + ".bak"))
	var f := FileAccess.open(SAVE_PATH + ".tmp", FileAccess.WRITE)
	if f:
		f.store_string(text)
		f.close()
		DirAccess.rename_absolute(ProjectSettings.globalize_path(SAVE_PATH + ".tmp"), ProjectSettings.globalize_path(SAVE_PATH))


func load_game() -> bool:
	_finish_save()
	for path in [SAVE_PATH, SAVE_PATH + ".bak"]:
		if not FileAccess.file_exists(path):
			continue
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
		if typeof(parsed) == TYPE_DICTIONARY and from_dict(parsed):
			return true
	return false


func from_dict(p: Dictionary) -> bool:
	if int(p.get("v", 0)) != SAVE_VERSION:
		return false
	coins = int(p.coins)
	gems = int(p.gems)
	goods = int(p.goods)
	xp = int(p.xp)
	level = int(p.level)
	plots = p.plots.map(func(v): return _v2(v))
	laws = Array(p.get("laws", [])).filter(func(l): return Data.LAWS.has(str(l))).map(func(l): return str(l))
	roads = {}
	for v in p.roads:
		roads[_v2(v)] = str(v[2]) if Data.ROADS.has(str(v[2])) else "asphalt"
	lights = {}
	for v in p.get("lights", []):
		lights[_v2(v)] = true
	rings = {}
	for v in p.get("rings", []):
		rings[_v2(v)] = true
	lamps = {}
	for v in p.get("lamps", []):
		lamps[_v2(v)] = str(v[2])
	cleared_trees = {}
	for v in p.cleared:
		cleared_trees[_v2(v)] = true
	beach = []
	for v in p.get("beach", []):
		beach.append(int(v))
	flights = []
	for v in p.get("flights", []):
		if Data.COUNTRIES.has(str(v)):
			flights.append(str(v))
	arrivals = {}
	for k in p.get("arrivals", {}):
		arrivals[str(k)] = int(p.arrivals[k])
	arrivals_day = {}
	for k in p.get("arrivals_day", {}):
		arrivals_day[str(k)] = int(p.arrivals_day[k])
	water = {}
	for v in p.get("water", []):
		water[_v2(v)] = true
	walls = {}
	for v in p.get("walls", []):
		if Data.WALLS.has(str(v[2])):
			walls[_v2(v)] = str(v[2])
	brands = {}
	var bd: Dictionary = p.get("brands", {})
	for k in bd:
		if Data.BRANDS.has(str(k)):
			brands[str(k)] = {"owner": str(bd[k].get("owner", "")), "day": int(bd[k].get("day", 1))}
	crime = _empty_crime()
	var cd: Dictionary = p.get("crime", {})
	for k in crime:
		if cd.has(k):
			crime[k] = bool(cd[k]) if crime[k] is bool else int(cd[k])
	protest = _empty_protest()
	ach = _load_ach(p.get("ach", {}))
	var pd: Dictionary = p.get("protest", {})
	for k in protest:
		if not pd.has(k):
			continue
		if protest[k] is Dictionary:
			for c in pd[k]:
				if str(c) in Data.PROTEST_CAUSES:
					protest[k][str(c)] = float(pd[k][c])
		elif protest[k] is float:
			protest[k] = float(pd[k])
		elif protest[k] is String:
			protest[k] = str(pd[k])
		else:
			protest[k] = int(pd[k])
	disaster = _empty_disaster()
	var dzd: Dictionary = p.get("disaster", {})
	for k in disaster:
		if not dzd.has(k):
			continue
		if disaster[k] is Array:
			disaster[k] = (dzd[k] as Array).map(func(v): return int(v))
		elif disaster[k] is bool:
			disaster[k] = bool(dzd[k])
		elif disaster[k] is String:
			disaster[k] = str(dzd[k])
		else:
			disaster[k] = int(dzd[k])
	paves = {}
	for v in p.get("paves", []):
		if Data.PAVES.has(str(v[2])):
			paves[_v2(v)] = str(v[2])
	road_deco = {}
	for v in p.get("road_deco", []):
		if Data.ROAD_DECO.has(str(v[2])):
			road_deco[_v2(v)] = str(v[2])
	_update_water_bodies()
	buildings = {}
	occ = {}
	for pair in p.buildings:
		var b: Dictionary = pair[1]
		if not Data.B.has(b.id):
			continue
		var uid := int(pair[0])
		buildings[uid] = {"id": b.id, "x": int(b.x), "y": int(b.y), "lvl": clampi(int(b.get("lvl", 1)), 1, 3), "rot": int(b.get("rot", 0)),
			"built": bool(b.built), "upg": bool(b.get("upg", false)), "prog": float(b.prog), "ready": bool(b.ready),
			"stocked": bool(b.get("stocked", false)), "occ": int(b.get("occ", 0)), "closed": bool(b.get("closed", false)),
			"dmg": bool(b.get("dmg", false)), "priv": str(b.get("priv", "")), "link": int(b.get("link", 0)), "fire": float(b.get("fire", 0.0)),
			"cd_check": int(b.get("cd_check", 0)), "cd_meet": int(b.get("cd_meet", 0)),
			"hlamp": str(b.get("hlamp", ""))}
		_occupy(uid)
	next_uid = int(p.next_uid)
	claimed = p.claimed.map(func(v): return int(v))
	for k in p.stats:
		stats[k] = p.stats[k]
	for k in p.settings:
		settings[k] = p.settings[k]
	for k in p.get("profile", {}):
		profile[k] = p.profile[k]
	day = int(p.get("day", 1))
	day_time = float(p.get("day_time", 0.3))
	tax = int(p.get("tax", Data.TAX_DEFAULT))
	rep = float(p.get("rep", 50))
	happy = float(p.get("happy", 55))
	peak_pop = int(p.get("peak_pop", 0))
	caught = p.get("caught", []).map(func(v): return str(v))
	weather = str(p.get("weather", "clear"))
	weather_until = int(p.get("weather_until", 0))
	patrol_until = int(p.get("patrol_until", 0))
	power_store = float(p.get("power_store", 0.0))
	rank = int(p.get("rank", Data.rank_for(level, rep)))
	mood = p.get("mood", [])
	ledger = p.get("ledger", [])
	today = p.get("today", _empty_day())
	loan = p.get("loan", {})
	deposit = int(p.get("deposit", 0))
	garbage = clampf(float(p.get("garbage", 0.0)), 0.0, GARBAGE_MAX)
	tutorial = int(p.get("tutorial", 99))
	lost = bool(p.get("lost", false))
	Events.from_dict(p.get("events", {}))
	_rebuild_net()
	recalc()
	var away := clampf(Time.get_unix_time_from_system() - float(p.time), 0.0, Data.OFFLINE_CAP)
	if away > 60.0 and not lost:
		_offline(away)
		offline_note = true
	return true


## Backup code: the whole save compressed into text the player can keep somewhere safe.
func export_code() -> String:
	var raw := JSON.stringify(to_dict()).to_utf8_buffer()
	var packed := raw.compress(FileAccess.COMPRESSION_GZIP)
	return "PXB4:" + str(raw.size()) + ":" + Marshalls.raw_to_base64(packed)


func import_code(code: String) -> bool:
	code = code.strip_edges().replace("\n", "").replace(" ", "")
	var parts := code.split(":")
	if parts.size() != 3 or parts[0] != "PXB4" or not parts[1].is_valid_int():
		return false
	var packed := Marshalls.base64_to_raw(parts[2])
	if packed.is_empty():
		return false
	var raw := packed.decompress(int(parts[1]), FileAccess.COMPRESSION_GZIP)
	var parsed = JSON.parse_string(raw.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY or int(parsed.get("v", 0)) != SAVE_VERSION:
		return false
	var keep_settings := settings.duplicate()
	if not from_dict(parsed):
		return false
	settings = keep_settings
	save_game()
	return true


func reset_game(keep_profile := true) -> void:
	var prof := profile.duplicate()
	var sets := settings.duplicate()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH + ".bak"))
	Events.reset()
	new_game()
	settings = sets
	if keep_profile:
		profile = prof
		tutorial = 99
	save_game()


func delete_personal_data() -> void:
	profile = {"name": "", "age": 0, "gender": "", "privacy": false, "intro": false}
	save_game()


func _notification(what: int) -> void:
	match what:
		NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT:
			save_game(true)
			_paused_at = Time.get_unix_time_from_system()
		NOTIFICATION_APPLICATION_RESUMED:
			if _paused_at > 0.0:
				var away := clampf(Time.get_unix_time_from_system() - _paused_at, 0.0, Data.OFFLINE_CAP)
				if away > 2.0 and not lost and profile.intro:
					_offline(away)
				_paused_at = 0.0
		NOTIFICATION_WM_CLOSE_REQUEST:
			save_game(true)
			get_tree().quit()


## Time away: production runs for the whole time, but the clock moves at most one day
## so the player never comes back to a pile of daily bills.
func _offline(away: float) -> void:
	simulate(away)
	var clock := minf(away, Data.DAY_LENGTH)
	while clock > 0.0:
		var step := minf(clock, 10.0)
		_advance_time(step)
		clock -= step


# ====================================================================== main loop
func _process(delta: float) -> void:
	if not lost and profile.intro:
		_simulate_sliced(delta)
		_advance_time(delta)
		happy = move_toward(happy, happy_target, delta * 0.35)
		_autosave += delta
		if _autosave > 20.0:
			_autosave = 0.0
			save_game()
	_update_music(delta)


func _advance_time(delta: float) -> void:
	var prev_hour := hour()
	_update_power(delta)
	day_time += delta / Data.DAY_LENGTH
	while day_time >= 1.0:
		day_time -= 1.0
		_end_of_day()
	var ph := phase_name()
	if ph != phase:
		phase = ph
		phase_changed.emit(ph)
	if hour() != prev_hour:
		_on_hour()


func _on_hour() -> void:
	var now := abs_hour()
	mood = mood.filter(func(m): return int(m.until) > now)
	_move_population()
	_update_garbage()
	_update_airport()
	_update_probe()
	_update_protest()
	check_ach()
	_update_disaster()
	if now >= weather_until:
		_pick_weather()
	recalc()
	_check_lose()
	if hour() == 9 and water_ratio < 0.85:
		toast.emit(Loc.t("water_low"))
	elif hour() == 20 and light_power < 0.85:
		toast.emit(Loc.t("power_low"))
	hour_passed.emit(hour())
	Events.on_hour(hour())


func _end_of_day() -> void:
	arrivals_day = {}
	# ---- passive income
	var biz_tax := 0
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		if b.priv != "" and b.built and not b.closed and not b.dmg:
			biz_tax += int(Data.stat(b.id, "income", b.lvl) * 3 * tax / 10.0 * (Data.BRAND_TAX if Data.brand_of(b.id) != "" else 1.0))
	biz_tax = int(biz_tax * rank_bonus() * law_mult("biz") * (Data.JAIL_TAX_MULT if in_jail() else 1.0))
	if biz_tax > 0:
		_earn("taxes", biz_tax)
	if is_connected_to_highway():
		var tour := int(pop * 0.08 * (happy / 100.0) * (0.5 + rep / 100.0))
		for uid in buildings:
			var b: Dictionary = buildings[uid]
			if Data.B[b.id].cat == "fun" and _works(uid):
				tour += 60 * b.lvl
			elif Data.B[b.id].get("tab", "") == "hotel" and _works(uid):
				tour += 120 * b.lvl
			elif Data.B[b.id].get("landmark", false) and _works(uid):
				tour += 400 * b.lvl
			tour += hist_tourists(uid)
		tour = int(tour * rank_bonus() * law_mult("tour") * (Data.JAIL_TAX_MULT if in_jail() else 1.0))
		if tour > 0:
			_earn("tourism", tour)
		if goods > 400:
			var sold := (goods - 400) / 4
			goods -= sold
			_earn("export", sold / 2)
	var fares := transit_fares()
	if fares > 0:
		_earn("transit", fares)
	if deposit > 0:
		var interest := maxi(1, int(deposit * 0.015))
		deposit += interest
		_add_ledger("in", "interest", interest)
	# ---- expenses
	_spend("upkeep", daily_upkeep())
	_spend("roads", daily_roads())
	_spend("laws", int(law_sum("daily")))
	add_rep(law_sum("rep"))
	check_rank()
	if not loan.is_empty():
		var pay_now: int = mini(int(loan.daily), int(loan.left))
		_spend("loan", pay_now)
		loan.left = int(loan.left) - pay_now
		loan.days = int(loan.days) - 1
		if int(loan.left) <= 0:
			loan = {}
			toast.emit(Loc.t("loan_paid"))
	# ---- rules and debts
	var broken := 0
	for r in rules:
		if rules[r]:
			broken += 1
	if broken > 0:
		add_rep(-0.7 * broken)
	else:
		add_rep(0.6)
	if coins < 0:
		add_mood(-12, 24, "debt")
		add_rep(-2)
	ledger.append(today)
	while ledger.size() > 14:
		ledger.pop_front()
	day += 1
	today = _empty_day()
	var s := season_name()
	if s != season:
		season = s
		season_changed.emit(s)
		_pick_weather()
	check_ach()
	day_passed.emit(day)
	Events.on_day(day)
	changed.emit()
	save_game()


func daily_upkeep() -> int:
	var total := 0.0
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		if not b.built or b.priv != "":
			continue
		total += Data.stat(b.id, "upkeep", b.lvl) * (0.3 if b.closed else 1.0)
	total += lamps.size() * 0.5 + lights.size() * 2.0 + rings.size() * Data.RING_UPKEEP
	total += house_lamp_count() * Data.HOUSE_LAMP_UPKEEP
	total += paves.size() * Data.PAVE_UPKEEP
	return int(round(total))


func daily_roads() -> int:
	var total := 0.0
	for c in roads:
		total += float(Data.ROADS[roads[c]].upkeep)
	return int(round(total))


func _earn(key: String, n: int) -> void:
	coins += n
	stats.coins_total = int(stats.coins_total) + n
	_add_ledger("in", key, n)


func _spend(key: String, n: int) -> void:
	if n <= 0:
		return
	coins -= n
	_add_ledger("out", key, n)


func _add_ledger(side: String, key: String, n: int) -> void:
	if today.is_empty():
		today = _empty_day()
	var d: Dictionary = today[side]
	d[key] = int(d.get(key, 0)) + n


func earn_event(key: String, n: int) -> void:
	_earn(key, n)
	changed.emit()


func spend_event(key: String, n: int) -> void:
	_spend(key, n)
	changed.emit()


func simulate(dt: float) -> void:
	var dirty := false
	for uid in buildings.keys():
		dirty = _sim_building(uid, dt) or dirty
	if dirty:
		recalc()


## One frame of the running game: each building is advanced once every SIM_SLICES frames by the
## time that passed since, so a big city costs the same per frame as a small one.
func _simulate_sliced(dt: float) -> void:
	_sim_clock += dt
	if _sim_keys.is_empty() or _sim_pos >= _sim_keys.size():
		_sim_keys = buildings.keys()
		_sim_pos = 0
		if _sim_seen.size() > buildings.size() + 64:
			for uid in _sim_seen.keys():
				if not buildings.has(uid):
					_sim_seen.erase(uid)
	var n := maxi(1, ceili(_sim_keys.size() / float(SIM_SLICES)))
	var dirty := false
	var end := mini(_sim_pos + n, _sim_keys.size())
	for i in range(_sim_pos, end):
		var uid: int = _sim_keys[i]
		if not buildings.has(uid):
			continue
		var last: float = _sim_seen.get(uid, _sim_clock - dt)
		_sim_seen[uid] = _sim_clock
		dirty = _sim_building(uid, _sim_clock - last) or dirty
	_sim_pos = end
	if dirty:
		recalc()


func _sim_building(uid: int, dt: float) -> bool:
	var dirty := false
	var b: Dictionary = buildings[uid]
	var d: Dictionary = Data.B[b.id]
	if not b.built:
		b.prog += dt
		if b.prog >= d.time:
			b.built = true
			b.prog = 0.0
			if b.priv == "":
				add_xp(int(d.cost / 10) + 5)
			if b.id == "metro_station":
				toast.emit(Loc.t("metro_ready" if metro_open() else "metro_wait"))
			elif Data.B[b.id].get("svc", "") == "bus" and bus_stops().size() < 2:
				toast.emit(Loc.t("bus_wait"))
			dirty = true
			building_updated.emit(uid)
		return dirty
	if b.upg:
		b.prog += dt
		if b.prog >= Data.upgrade_cost(b.id, b.lvl).time:
			b.lvl += 1
			b.upg = false
			b.prog = 0.0
			b.ready = false
			b.stocked = false
			stats.upgrades = int(stats.get("upgrades", 0)) + 1
			add_xp(int(d.cost / 8) + 10)
			sfx("upgrade")
			dirty = true
			building_updated.emit(uid)
		return dirty
	if b.fire > 0.0:
		b.fire -= dt
		if b.fire <= 0.0:
			b.fire = 0.0
			building_updated.emit(uid)
	if b.ready or b.priv != "" or d.cat in ["decor", "service"] or not _works(uid):
		return dirty
	var speed := 1.0
	match d.cat:
		"home":
			if b.occ <= 0:
				return dirty
		"shop":
			if not b.stocked:
				var use := Data.stat(b.id, "use", b.lvl)
				if goods < use:
					return dirty
				goods -= use
				b.stocked = true
				dirty = true
			speed = staff
		"ind", "fun":
			speed = staff
	b.prog += dt * speed
	if b.prog >= d.cycle:
		b.prog = d.cycle
		b.ready = true
		building_updated.emit(uid)
	return dirty


## Built, open, not burnt and reachable by road.
func _works(uid: int) -> bool:
	var b: Dictionary = buildings[uid]
	return b.built and not b.upg and not b.closed and not b.dmg and road_ok.get(uid, false)


func works(uid: int) -> bool:
	return buildings.has(uid) and _works(uid)


## Tourists a day that a working historic sight (field "hist") brings, × its level.
func hist_tourists(uid: int) -> int:
	if not buildings.has(uid) or not _works(uid):
		return 0
	var b: Dictionary = buildings[uid]
	return int(Data.B[b.id].get("hist", 0)) * int(b.lvl)


# ====================================================================== population & happiness
func _move_population() -> void:
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		if Data.B[b.id].cat != "home":
			continue
		var cap := Data.stat(b.id, "pop", b.lvl)
		if not _works(uid):
			if b.closed or b.dmg:
				b.occ = 0
			continue
		var h: int = home_happy.get(uid, 50)
		if h >= 40 and b.occ < cap:
			b.occ = mini(cap, b.occ + maxi(1, int(ceil(cap * (0.15 + h / 400.0)))))
		elif h < 30 and b.occ > 0:
			b.occ = maxi(0, b.occ - maxi(1, int(ceil(cap * 0.12))))


func add_mood(v: int, hours: int, why: String) -> void:
	mood.append({"v": v, "until": abs_hour() + hours, "why": why})
	recalc()


func add_rep(v: float) -> void:
	rep = clampf(rep + v, 0.0, 100.0)
	changed.emit()


func mood_total() -> int:
	var t := 0
	for m in mood:
		t += int(m.v)
	return t


func weather_mood() -> int:
	match weather:
		"storm":
			return -4
		"rain", "fog":
			return -1
		"snow":
			return 1 if season == "winter" else -1
	return 1 if season == "summer" else 0


func recalc() -> void:
	pop = 0
	capacity = 0
	jobs = 0
	road_ok.clear()
	var homes: Array[int] = []
	var infl: Array[int] = []
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		var d: Dictionary = Data.B[b.id]
		road_ok[uid] = _touches_road(b.x, b.y, d.size)
		if not b.built:
			continue
		match d.cat:
			"home":
				if _works(uid):
					var cap := Data.stat(b.id, "pop", b.lvl)
					b.occ = mini(b.occ, cap)
					pop += b.occ
					capacity += cap
					homes.append(uid)
				elif b.closed or b.dmg:
					b.occ = 0
			"shop", "ind", "service", "fun":
				if _works(uid):
					jobs += Data.stat(b.id, "jobs", b.lvl)
					infl.append(uid)
			"decor":
				infl.append(uid)
	peak_pop = maxi(peak_pop, pop)
	_recalc_utilities()
	workforce = int(pop * Data.WORKFORCE)
	workers = mini(workforce, jobs)
	staff = 1.0 if jobs == 0 else clampf(float(workers) / jobs, 0.15, 1.0)
	unemployment = 0.0 if workforce == 0 else maxf(0.0, float(workforce - jobs) / workforce)
	_check_rules()
	_recalc_quarters()
	home_happy.clear()
	home_reasons.clear()
	var global := 45 - garbage_mood() + mood_total() + int(law_sum("happy")) + weather_mood() - int(round((tax - Data.TAX_DEFAULT) * 2.2)) - int(unemployment * 22.0)
	for r in rules:
		if rules[r]:
			global -= 2
	var has_gov := false
	for uid in infl:
		if Data.B[buildings[uid].id].get("svc", "") == "gov":
			has_gov = true
	var metro_ok := metro_open()
	var landmarks: Array[Vector2] = []
	for uid in buildings:
		var lb: Dictionary = buildings[uid]
		if Data.B[lb.id].get("landmark", false) and lb.built:
			landmarks.append(Vector2(lb.x + Data.B[lb.id].size / 2.0, lb.y + Data.B[lb.id].size / 2.0))
	var total := 0.0
	var weight := 0
	for uid in homes:
		var b: Dictionary = buildings[uid]
		var n: int = Data.B[b.id].size
		var hc := Vector2(b.x + n / 2.0, b.y + n / 2.0)
		var reasons: Array = []
		var decor := 0
		var svc := {}
		var poll := 0
		var shop_near := false
		var fun := 0
		for o in infl:
			var ob: Dictionary = buildings[o]
			var od: Dictionary = Data.B[ob.id]
			var on: int = od.size
			var dist := maxf(absf(ob.x + on / 2.0 - hc.x), absf(ob.y + on / 2.0 - hc.y))
			match od.cat:
				"decor":
					if dist <= od.radius:
						decor += Data.stat(ob.id, "happy", ob.lvl)
				"service":
					if (od.svc != "metro" or metro_ok) and (od.svc == "gov" or dist <= od.radius):
						svc[od.svc] = true
				"fun":
					if dist <= od.radius:
						fun = maxi(fun, Data.stat(ob.id, "happy", ob.lvl))
				"shop":
					if dist <= 9:
						shop_near = true
				"ind":
					var p: int = od.get("poll", 0)
					if p > 0 and dist <= (6 if p >= 5 else 3):
						poll += p
		var h := global
		decor = mini(decor, 25)
		if decor > 0:
			reasons.append(["r_decor", decor])
		h += decor
		for key in ["edu", "fire", "police", "health", "bus", "metro", "sport", "tv", "news"]:
			if svc.has(key):
				var v: int = {"edu": 8, "fire": 5, "police": 7, "health": 9, "bus": 3, "metro": 6, "sport": 5, "tv": 4, "news": 2}[key]
				h += v
				reasons.append(["r_" + key, v])
		if garbage_mood() > 0:
			reasons.append(["r_garbage", -garbage_mood()])
		if water_ratio < 0.9:
			var wp := int(round((1.0 - water_ratio) * 20.0))
			h -= wp
			reasons.append(["r_water", -wp])
		for lm in landmarks:
			if maxf(absf(lm.x - hc.x), absf(lm.y - hc.y)) <= Data.LANDMARK_RADIUS:
				h += 6
				reasons.append(["r_landmark", 6])
				break
		if has_gov:
			h += 6
		if fun > 0:
			h += mini(fun, 12)
			reasons.append(["r_fun", mini(fun, 12)])
		if shop_near:
			h += 5
			reasons.append(["r_shop", 5])
		else:
			h -= 6
			reasons.append(["r_noshop", -6])
		if garbage >= 40.0:
			poll += int(garbage / 25.0)
		if poll > 0:
			h -= mini(poll * 2, 22)
			reasons.append(["r_poll", -mini(poll * 2, 22)])
		var rt := _road_type_near(b.x, b.y, n)
		if rt == "stone":
			h += 2
		elif rt in ["boulevard", "brick"]:
			h += 3
		elif rt == "bus_lane":
			h += 1
		elif rt == "bike":
			h += 2
		elif rt == "red":
			h += 1
		elif rt == "dirt":
			h -= 2
			reasons.append(["r_dirt", -2])
		elif rt == "gravel":
			h -= 1
			reasons.append(["r_dirt", -1])
		if b.link > 0 and buildings.has(b.link):
			h += 3
			reasons.append(["r_link", 3])
		if quarter_of.has(uid):
			h += int(quarter_of[uid].happy)
			reasons.append(["r_quarter", int(quarter_of[uid].happy)])
		var sd := _street_deco_near(b.x, b.y, n)
		if sd > 0:
			h += sd
			reasons.append(["r_street_deco", sd])
		var pv := _pave_near(b.x, b.y, n)
		if pv > 0:
			h += pv
			reasons.append(["r_pave", pv])
		var wv := _water_view(b.x, b.y, n)
		if wv > 0:
			h += wv
			reasons.append(["r_water_view", wv])
		h += mini(_lamps_near(hc, 2.6), 3)
		if str(b.get("hlamp", "")) != "":
			h += Data.HOUSE_LAMP_HAPPY
			reasons.append(["r_house_lamp", Data.HOUSE_LAMP_HAPPY])
		if _jam_near(hc):
			h -= 4
			reasons.append(["r_jam", -4])
		if tax > Data.TAX_DEFAULT:
			reasons.append(["r_tax", -int(round((tax - Data.TAX_DEFAULT) * 2.2))])
		if unemployment > 0.1:
			reasons.append(["r_jobs", -int(unemployment * 22.0)])
		h = clampi(h, 0, 100)
		home_happy[uid] = h
		home_reasons[uid] = reasons
		total += h * maxi(1, b.occ)
		weight += maxi(1, b.occ)
	happy_target = clampf(total / weight, 0.0, 100.0) if weight > 0 else clampf(global + 10, 0.0, 100.0)
	changed.emit()


func _lamps_near(c: Vector2, r: float) -> int:
	var n := 0
	for q in lamps:
		var p := LampView.slot_grid(q)
		if absf(p.x - c.x) <= r and absf(p.y - c.y) <= r:
			n += 1
	return n


func _jam_near(c: Vector2) -> bool:
	for t in jam_tiles:
		if absf(t.x + 0.5 - c.x) <= 4 and absf(t.y + 0.5 - c.y) <= 4:
			return true
	return false


func _touches_road(x: int, y: int, n: int) -> bool:
	for i in n:
		for c in [Vector2i(x + i, y - 1), Vector2i(x + i, y + n), Vector2i(x - 1, y + i), Vector2i(x + n, y + i)]:
			if net.has(c):
				return true
	return false


func _road_type_near(x: int, y: int, n: int) -> String:
	for i in n:
		for c in [Vector2i(x + i, y + n), Vector2i(x + n, y + i), Vector2i(x + i, y - 1), Vector2i(x - 1, y + i)]:
			if roads.has(c):
				return roads[c]
	return ""


const SIDES := [Vector2i(0, 1), Vector2i(1, 0), Vector2i(0, -1), Vector2i(-1, 0)]


## Tiles just outside one side of an n x n footprint: rot 0 = +y, 1 = +x, 2 = -y, 3 = -x.
static func side_tiles(x: int, y: int, n: int, rot: int) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for i in n:
		match rot:
			0: out.append(Vector2i(x + i, y + n))
			1: out.append(Vector2i(x + n, y + i))
			2: out.append(Vector2i(x + i, y - 1))
			_: out.append(Vector2i(x - 1, y + i))
	return out


func _street_at(c: Vector2i) -> bool:
	return net.has(c) and net[c] != "highway"


## Which way a building at (x, y) should face: towards a street, keeping `prefer` when it has one.
func facing_for(x: int, y: int, n: int, prefer := 0) -> int:
	for k in 4:
		var r := (prefer + k) % 4
		for c in side_tiles(x, y, n, r):
			if _street_at(c):
				return r
	return prefer


## Grid point where the lot meets the street (the end of the path to the front door).
func entry_point(uid: int) -> Vector2:
	var b: Dictionary = buildings[uid]
	var n: int = Data.B[b.id].size
	var m := Assets.meta(Assets.building_sprite(b.id, b.lvl, int(b.get("rot", 0))))
	if m.has("entry_g"):
		return Vector2(b.x, b.y) + Vector2(m.entry_g[0], m.entry_g[1])
	var c := Vector2(b.x + n * 0.5, b.y + n * 0.5)
	return c + Vector2(SIDES[int(b.get("rot", 0))]) * n * 0.5


## Road tile in front of the building's entrance, or any street next to it.
func entrance_tile(uid: int) -> Vector2i:
	var b: Dictionary = buildings[uid]
	var n: int = Data.B[b.id].size
	var rot := int(b.get("rot", 0))
	var e := entry_point(uid)
	var out := Vector2(SIDES[rot]) * 0.5
	var t := Vector2i(floori(e.x + out.x), floori(e.y + out.y))
	if _street_at(t):
		return t
	for k in 4:
		for c in side_tiles(b.x, b.y, n, (rot + k) % 4):
			if _street_at(c):
				return c
	return Vector2i(-1, -1)


func _rebuild_net() -> void:
	net = highway.duplicate()
	for c in roads:
		net[c] = roads[c]
	connected.clear()
	var queue: Array[Vector2i] = []
	for c in highway:
		connected[c] = true
		queue.append(c)
	while not queue.is_empty():
		var c: Vector2i = queue.pop_back()
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var nc: Vector2i = c + d
			if net.has(nc) and not connected.has(nc):
				connected[nc] = true
				queue.append(nc)
	# a roundabout needs a crossing: it goes when a road of it is removed
	for c in rings.keys():
		if not roads.has(c) or not is_intersection(c):
			rings.erase(c)


## Built metro stations in the order they were built: the line runs underground from one to the next.
func metro_stations() -> Array[int]:
	var out: Array[int] = []
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		if b.id == "metro_station" and b.built and not b.closed:
			out.append(uid)
	out.sort()
	return out


## The landmark earns more with every district home around it: x2 with all of them.
func landmark_bonus() -> float:
	var n := 0
	for uid in buildings:
		if buildings[uid].id == "dushanbe_home" and buildings[uid].built:
			n += 1
	return 1.0 + minf(n, Data.LANDMARK_HOMES) / float(Data.LANDMARK_HOMES)


## Tickets for a day of buses (once two stops are served) and metro (once two stations are built).
func transit_fares() -> int:
	var n := 0
	var stops := bus_stops().size()
	if stops >= 2 and not laws.has("free_bus"):
		n += 15 * stops
	var st := metro_stations().size()
	if st >= 2:
		n += 80 * st
	return n


## The metro works once there are two stations: one where the line starts and one where it goes.
func metro_open() -> bool:
	return metro_stations().size() >= 2


## Bus stops the city bus serves, in the order they were built.
func bus_stops() -> Array[int]:
	var out: Array[int] = []
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		if Data.B[b.id].get("svc", "") == "bus" and b.built and not b.closed and road_ok.get(uid, false):
			out.append(uid)
	out.sort()
	return out


## Decorated streets in front of a home: the best decoration on the roads around it.
func _street_deco_near(x: int, y: int, n: int) -> int:
	var best := 0
	for i in n:
		for c in [Vector2i(x + i, y - 1), Vector2i(x + i, y + n), Vector2i(x - 1, y + i), Vector2i(x + n, y + i)]:
			if road_deco.has(c):
				best = maxi(best, int(Data.ROAD_DECO[road_deco[c]].happy))
	return best


## Paving right next to a building: the best "happy" of it, up to PAVE_HAPPY_MAX.
func _pave_near(x: int, y: int, n: int) -> int:
	var best := 0
	for i in n:
		for c in [Vector2i(x + i, y - 1), Vector2i(x + i, y + n), Vector2i(x - 1, y + i), Vector2i(x + n, y + i)]:
			if paves.has(c):
				best = maxi(best, int(Data.PAVES[paves[c]].happy))
	return mini(best, Data.PAVE_HAPPY_MAX)


## Homes by the water are happier: +3 by a river, +5 by a sea, +7 by an ocean (within 2 tiles).
func _water_view(x: int, y: int, n: int) -> int:
	var best := 0
	for dy in range(-2, n + 2):
		for dx in range(-2, n + 2):
			best = maxi(best, water_kind(Vector2i(x + dx, y + dy)))
	return [0, 3, 5, 7][best]


func is_connected_to_highway() -> bool:
	for g in Data.gates():
		if roads.has(g):
			return true
	return false


func is_intersection(c: Vector2i) -> bool:
	if not net.has(c):
		return false
	var n := 0
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		if net.has(c + d):
			n += 1
	return n >= 3


# ====================================================================== power & water
func _recalc_utilities() -> void:
	_plant_kw = 0.0
	_solar_kw = 0.0
	_demand_kw = lamps.size() * Data.POWER_LAMP + house_lamp_count() * Data.POWER_HOUSE_LAMP
	power_cap = 0.0
	water_supply = Data.WATER_FREE
	water_demand = 0
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		var d: Dictionary = Data.B[b.id]
		if not b.built or not _works(uid):
			continue
		if d.cat == "home":
			_demand_kw += b.occ * Data.POWER_HOME
			water_demand += b.occ
		elif d.cat != "decor":
			_demand_kw += Data.POWER_BASE + Data.stat(b.id, "jobs", b.lvl) * Data.POWER_JOB
		if d.has("power"):
			if d.get("svc", "") == "solar":
				_solar_kw += Data.stat(b.id, "power", b.lvl)
				power_cap += Data.stat(b.id, "store", b.lvl)
			else:
				_plant_kw += Data.stat(b.id, "power", b.lvl)
		if d.has("water"):
			water_supply += Data.stat(b.id, "water", b.lvl)
	water_demand = int(water_demand * law_mult("water"))
	water_ratio = 1.0 if water_demand <= water_supply else water_supply / float(water_demand)
	power_store = minf(power_store, power_cap)
	_update_power(0.0)


## Solar panels follow the sun and the clouds; the batteries carry the city through the night.
func _update_power(delta: float) -> void:
	var sun := clampf(1.0 - night_amount() * 1.2, 0.0, 1.0)
	sun *= {"cloudy": 0.6, "rain": 0.35, "storm": 0.2, "snow": 0.45, "fog": 0.5, "windy": 0.85, "heat": 1.1}.get(weather, 1.0)
	power_supply = Data.POWER_FREE + _plant_kw + _solar_kw * sun
	power_demand = _demand_kw * law_mult("power")
	power_store = clampf(power_store + (power_supply - power_demand) * delta * 24.0 / Data.DAY_LENGTH, 0.0, power_cap)
	if power_demand <= power_supply or power_store > 0.0:
		power_ratio = 1.0
	else:
		power_ratio = clampf(power_supply / power_demand, 0.0, 1.0)
	light_power = move_toward(light_power, power_ratio, delta * 0.6) if delta > 0.0 else power_ratio


## How brightly the electric light shines: only when it is dark (night, storm) and only with current.
func light_level() -> float:
	return night_amount() * light_power


# ====================================================================== rules
func _check_rules() -> void:
	rules.clear()
	jam_tiles.clear()
	for c in lights:
		var n := 0
		for o in lights:
			if absi(o.x - c.x) <= 3 and absi(o.y - c.y) <= 3:
				n += 1
		if n > 3:
			jam_tiles[c] = true
	rules["lights"] = not jam_tiles.is_empty()
	var have := {}
	var decor_n := lamps.size() / 4
	var homes_no_road := false
	var home_list: Array[int] = []
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		var d: Dictionary = Data.B[b.id]
		if not b.built:
			continue
		if d.cat == "service" and not b.closed and not b.dmg:
			have[d.svc] = true
		if d.cat == "decor":
			decor_n += d.size * d.size
		if d.cat == "home":
			home_list.append(uid)
			if not road_ok.get(uid, false):
				homes_no_road = true
	var poll_bad := false
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		if int(Data.B[b.id].get("poll", 0)) < 5 or not b.built or b.closed:
			continue
		for h in home_list:
			var hb: Dictionary = buildings[h]
			if absi(hb.x - b.x) <= 4 and absi(hb.y - b.y) <= 4:
				poll_bad = true
	rules["pollution"] = poll_bad
	rules["roads"] = homes_no_road
	rules["garbage"] = pop > 100 and garbage >= 60.0
	rules["school"] = pop > 150 and not have.has("edu")
	rules["fire"] = pop > 200 and not have.has("fire")
	rules["police"] = pop > 300 and not have.has("police")
	rules["health"] = pop > 500 and not have.has("health")
	rules["decor"] = pop > 40 and decor_n * 30 < pop
	rules["budget"] = coins < 0


# ====================================================================== laws
func has_law(id: String) -> bool:
	return id in laws


## Sum of an additive law effect over the passed laws.
func law_sum(key: String) -> float:
	var t := 0.0
	for l in laws:
		t += float(Data.LAWS[l].get(key, 0.0))
	return t


## Product of a multiplier law effect over the passed laws.
func law_mult(key: String) -> float:
	var t := 1.0
	for l in laws:
		t *= float(Data.LAWS[l].get(key, 1.0))
	return t


## Pass or repeal a law. Passing costs Data.LAW_COST; repealing is free.
func toggle_law(id: String) -> bool:
	if has_law(id):
		laws.erase(id)
	else:
		if laws.size() >= Data.MAX_LAWS or coins < Data.LAW_COST:
			return false
		_spend("laws", Data.LAW_COST)
		laws.append(id)
	_recalc_utilities()
	recalc()
	return true


# ====================================================================== watchtower
## Multiplier on crime risk while a recent document check is still in effect.
func patrol_mult() -> float:
	return Data.TOWER_PATROL_MULT if abs_hour() < patrol_until else 1.0


## Hours left before a tower's action is off cooldown (0 if ready now).
func tower_cooldown(uid: int, meeting := false) -> int:
	if not buildings.has(uid):
		return 0
	var b: Dictionary = buildings[uid]
	var until := int(b.get("cd_meet" if meeting else "cd_check", 0))
	return maxi(0, until - abs_hour())


## Check residents' papers at a watchtower: a small fine, +reputation, and less crime risk for a while.
## Returns the coins earned, or -1 if still on cooldown.
func check_documents(uid: int) -> int:
	if not buildings.has(uid) or tower_cooldown(uid) > 0:
		return -1
	var b: Dictionary = buildings[uid]
	var reward: int = _rng.randi_range(Data.TOWER_CHECK_MIN, Data.TOWER_CHECK_MAX) * int(b.lvl)
	_earn("patrol", reward)
	add_rep(1.0)
	patrol_until = abs_hour() + Data.TOWER_PATROL_HOURS
	b.cd_check = abs_hour() + Data.TOWER_CHECK_COOLDOWN
	sfx("done")
	changed.emit()
	save_game()
	return reward


## Hold a gathering at a watchtower: costs coins, lifts the city's mood for a while. Returns false if
## it can't be paid for or is still on cooldown.
func hold_meeting(uid: int) -> bool:
	if not buildings.has(uid) or tower_cooldown(uid, true) > 0:
		return false
	if not pay(Data.TOWER_MEETING_COST, 0, "meeting"):
		return false
	var b: Dictionary = buildings[uid]
	add_mood(Data.TOWER_MEETING_HAPPY, Data.TOWER_MEETING_HOURS, "meeting")
	add_rep(1.0)
	b.cd_meet = abs_hour() + Data.TOWER_MEETING_COOLDOWN
	sfx("done")
	save_game()
	return true


# ====================================================================== crime (bank heists, the mayor in prison)
func _empty_crime() -> Dictionary:
	## heists: banks robbed by residents; caught: robbers caught; mayor: robberies by the mayor;
	## probe: hour when the investigation of the mayor's robbery ends (0 = none); found: will they find out;
	## loot: what the mayor took; cd: hour when the mayor may rob again; jail: hour when the mayor is released.
	return {"heists": 0, "caught": 0, "mayor": 0, "probe": 0, "found": false, "loot": 0, "cd": 0, "jail": 0, "jailed": 0}


## Crime risk multiplier: laws, a recent watchtower check and a working prison.
func crime_mult() -> float:
	return law_mult("crime") * patrol_mult() * (Data.PRISON_CRIME_MULT if has_service("prison") else 1.0)


func police_count() -> int:
	var n := 0
	for uid in buildings:
		if Data.B[buildings[uid].id].get("svc", "") == "police" and _works(uid):
			n += 1
	return n


func working_banks() -> Array[int]:
	var out: Array[int] = []
	for uid in buildings:
		if buildings[uid].id == "bank" and _works(uid):
			out.append(uid)
	return out


## A guard agency covers this bank (cameras, guards).
func bank_guarded(uid: int) -> bool:
	if not buildings.has(uid):
		return false
	var b: Dictionary = buildings[uid]
	return covered_by("guard", Vector2i(int(b.x), int(b.y)))


func heist_catch_chance(uid: int) -> float:
	var n := police_count()
	if n == 0:
		return 0.0
	var p := Data.HEIST_CATCH + Data.HEIST_CATCH_EXTRA * (n - 1) + (Data.HEIST_CATCH_GUARD if bank_guarded(uid) else 0.0)
	return minf(p, Data.HEIST_CATCH_MAX)


func heist_loot(uid: int) -> int:
	return Data.HEIST_LOOT * int(buildings[uid].lvl) if buildings.has(uid) else 0


## A resident robs a bank. roll < 0 = random. Returns true if the robber was caught (the money comes back).
func bank_heist(uid: int, roll := -1.0) -> bool:
	if not buildings.has(uid):
		return false
	var r := roll if roll >= 0.0 else _rng.randf()
	var caught := r < heist_catch_chance(uid)
	crime.heists = int(crime.heists) + 1
	if caught:
		crime.caught = int(crime.caught) + 1
		add_rep(2.0)
	else:
		_spend("heist", mini(heist_loot(uid), maxi(coins, 0)))
		add_rep(-3.0)
		add_mood(-4, 24, "crime")
	heist.emit(uid, caught, false)
	changed.emit()
	return caught


func in_jail() -> bool:
	return abs_hour() < int(crime.get("jail", 0))


func jail_hours() -> int:
	return maxi(0, int(crime.get("jail", 0)) - abs_hour())


## Chance the police find out the mayor robbed this bank.
func mayor_suspect_chance(uid: int) -> float:
	var p := Data.MAYOR_SUSPECT + Data.MAYOR_SUSPECT_POLICE * police_count() + Data.MAYOR_SUSPECT_REPEAT * int(crime.mayor)
	if bank_guarded(uid):
		p += Data.MAYOR_SUSPECT_GUARD
	return minf(p, Data.MAYOR_SUSPECT_MAX)


func mayor_rob_loot(uid: int) -> int:
	return Data.MAYOR_ROB_LOOT * int(buildings[uid].lvl) if buildings.has(uid) else 0


## Why the mayor can't rob this bank now ("" = can).
func mayor_rob_problem(uid: int) -> String:
	if not buildings.has(uid) or buildings[uid].id != "bank" or not _works(uid):
		return "rob_closed"
	if in_jail():
		return "in_jail"
	if int(crime.probe) > 0:
		return "rob_probe"
	if abs_hour() < int(crime.cd):
		return "rob_wait"
	return ""


## The mayor robs a bank: coins now, an investigation for MAYOR_PROBE_HOURS. roll < 0 = random.
## Returns the loot (0 if not possible).
func mayor_rob(uid: int, roll := -1.0) -> int:
	if mayor_rob_problem(uid) != "":
		sfx("error")
		return 0
	var loot := mayor_rob_loot(uid)
	var r := roll if roll >= 0.0 else _rng.randf()
	crime.found = r < mayor_suspect_chance(uid)
	crime.mayor = int(crime.mayor) + 1
	crime.loot = loot
	crime.probe = abs_hour() + Data.MAYOR_PROBE_HOURS
	crime.cd = abs_hour() + Data.MAYOR_ROB_COOLDOWN
	_earn("heist", loot)
	add_mood(-3, 24, "crime")
	add_anger("rob", Data.ANGER_ROB)
	heist.emit(uid, false, true)
	sfx("coin")
	changed.emit()
	save_game()
	return loot


## End of the investigation: either the case is closed or the mayor goes to prison.
func _update_probe() -> void:
	if int(crime.get("probe", 0)) <= 0 or abs_hour() < int(crime.probe):
		return
	crime.probe = 0
	if bool(crime.found):
		go_to_jail()
	else:
		Events.probe_closed()


func go_to_jail() -> void:
	var fine := int(crime.loot) * Data.JAIL_FINE_MULT
	crime.jail = abs_hour() + Data.JAIL_HOURS
	crime.jailed = int(crime.jailed) + 1
	crime.found = false
	_spend("fines", fine)
	add_rep(-Data.JAIL_REP)
	add_mood(Data.JAIL_MOOD, Data.JAIL_HOURS, "mayor_jail")
	add_anger("rob", Data.ANGER_JAIL)
	Events.mayor_jailed(fine)
	changed.emit()
	save_game()


## Get out of prison early on bail (gems).
func pay_bail() -> bool:
	if not in_jail() or not pay(0, Data.JAIL_BAIL_GEMS, "bail"):
		return false
	crime.jail = 0
	add_rep(-3.0)
	mood = mood.filter(func(m): return str(m.why) != "mayor_jail")
	toast.emit(Loc.t("bail_done"))
	changed.emit()
	save_game()
	return true


# ====================================================================== protests (ROADMAP 28)
func _empty_protest() -> Dictionary:
	## anger: 0..PROTEST_MAX; why: cause -> share of the anger; until: hour the protest ends (0 = none);
	## cause: what people protest about; site: the building they gather at; cd: no new protest before this hour;
	## count: protests so far; talks/forced: how many were answered by talking / dispersed by the police.
	var why := {}
	for c in Data.PROTEST_CAUSES:
		why[c] = 0.0
	return {"anger": 0.0, "why": why, "until": 0, "cause": "", "site": 0, "cd": 0, "count": 0, "talks": 0, "forced": 0}


## Something unfair happened: the residents get angrier (cause: Data.PROTEST_CAUSES).
func add_anger(cause: String, v: float) -> void:
	if protest.is_empty():
		protest = _empty_protest()
	protest.anger = clampf(float(protest.anger) + v, 0.0, Data.PROTEST_MAX)
	protest.why[cause] = float(protest.why.get(cause, 0.0)) + v


func anger() -> float:
	return float(protest.get("anger", 0.0))


func protest_active() -> bool:
	return int(protest.get("until", 0)) > abs_hour()


## The main grievance: the cause behind most of the anger.
func protest_cause() -> String:
	var best := "mood"
	var top := 0.0
	for c in protest.why:
		if float(protest.why[c]) > top:
			top = float(protest.why[c])
			best = str(c)
	return best


## Where people gather: the town hall, else a square or park, else the busiest public building.
func protest_site() -> int:
	for kinds in [["town_hall"], ["plaza", "park", "fountain", "statue"], ["court", "school", "police", "post_office"]]:
		for uid in buildings:
			if buildings[uid].id in kinds and buildings[uid].built:
				return uid
	for uid in buildings:
		if buildings[uid].built and Data.B[buildings[uid].id].cat == "service":
			return uid
	return 0


func protest_talk_cost() -> int:
	return int(Data.PROTEST_TALK_COST * (1.0 + level / 10.0))


## Hourly: unfair taxes, low happiness and broken rules add anger, time softens it; high anger starts a protest.
func _update_protest() -> void:
	if protest.is_empty():
		protest = _empty_protest()
	var now := abs_hour()
	if tax > Data.ANGER_TAX_FAIR:
		add_anger("tax", (tax - Data.ANGER_TAX_FAIR) * Data.ANGER_TAX)
	if pop > 0 and happy < Data.ANGER_UNHAPPY_AT:
		add_anger("mood", Data.ANGER_UNHAPPY)
	var br := broken_rules()
	if br > 0:
		add_anger("rules", br * Data.ANGER_RULES)
	if int(protest.until) > 0 and now >= int(protest.until):
		_end_protest(false)
		return
	if protest_active():
		return
	protest.anger = maxf(0.0, float(protest.anger) - Data.PROTEST_DECAY)
	var total := 0.0
	for c in protest.why:
		total += float(protest.why[c])
	if total > 0.0:
		var k := float(protest.anger) / total
		for c in protest.why:
			protest.why[c] = float(protest.why[c]) * k
	if float(protest.anger) >= Data.PROTEST_AT and pop >= Data.PROTEST_MIN_POP and now >= int(protest.cd) and not lost and tutorial >= 99:
		start_protest()


## People take to the streets.
func start_protest() -> bool:
	var site := protest_site()
	if site == 0 or protest_active():
		return false
	protest.site = site
	protest.cause = protest_cause()
	protest.until = abs_hour() + Data.PROTEST_HOURS
	protest.count = int(protest.count) + 1
	add_rep(-Data.PROTEST_REP)
	add_mood(Data.PROTEST_MOOD, Data.PROTEST_HOURS, "protest")
	Events.protest_started(str(protest.cause), site)
	protest_changed.emit("start")
	changed.emit()
	return true


## How many people come out: grows with anger and the city.
func protest_crowd() -> int:
	return clampi(int(4 + anger() / 10.0 + pop / 120), 4, Data.PROTEST_CROWD)


## The mayor meets the people: pays for their demand (taxes go back to normal), the anger goes away.
func protest_talk() -> bool:
	if not protest_active():
		return false
	if not pay(protest_talk_cost(), 0, "events"):
		return false
	if str(protest.cause) == "tax" and tax > Data.ANGER_TAX_FAIR:
		set_tax(Data.TAX_DEFAULT)
	protest.talks = int(protest.talks) + 1
	add_rep(Data.PROTEST_TALK_REP)
	mood = mood.filter(func(m): return str(m.why) != "protest")
	add_mood(Data.PROTEST_TALK_MOOD, 24, "protest_heard")
	protest.anger = 0.0
	for c in protest.why:
		protest.why[c] = 0.0
	_end_protest(true)
	toast.emit(Loc.t("pr_talk_done"))
	return true


## The police break up the protest: it ends now, but people get angrier and trust the mayor less.
func protest_force() -> bool:
	if not protest_active():
		return false
	if police_count() == 0:
		toast.emit(Loc.t("pr_no_police"))
		return false
	protest.forced = int(protest.forced) + 1
	add_rep(-Data.PROTEST_FORCE_REP)
	add_mood(Data.PROTEST_FORCE_MOOD, 48, "protest_force")
	protest.until = 0
	protest.cd = abs_hour() + Data.PROTEST_COOLDOWN
	mood = mood.filter(func(m): return str(m.why) != "protest")
	add_anger(str(protest.cause), Data.PROTEST_FORCE_ANGER)
	protest_changed.emit("force")
	changed.emit()
	save_game()
	return true


func _end_protest(heard: bool) -> void:
	protest.until = 0
	protest.cd = abs_hour() + Data.PROTEST_COOLDOWN
	mood = mood.filter(func(m): return str(m.why) != "protest")
	if not heard:
		add_rep(-Data.PROTEST_IGNORE_REP)
		protest.anger = float(protest.anger) * Data.PROTEST_IGNORE_LEFT
		for c in protest.why:
			protest.why[c] = float(protest.why[c]) * Data.PROTEST_IGNORE_LEFT
		Events.protest_over()
	protest_changed.emit("end")
	changed.emit()
	save_game()


# ====================================================================== natural events (flood, quake, blizzard, tourists)
func _empty_disaster() -> Dictionary:
	## phase: "" calm, "threat" (waiting for the mayor's answer), "after" (consequences visible); kind: Data.DZ_KINDS;
	## ends: hour the phase ends; cd: no new event before this hour; opt/hit: the answer and whether it went wrong;
	## uids: buildings in danger (flood: near water; quake: random ones) / damaged ones; count: events so far.
	return {"phase": "", "kind": "", "ends": 0, "cd": 0, "opt": -1, "hit": false, "count": 0, "uids": []}


func disaster_active() -> bool:
	return str(disaster.get("phase", "")) != ""


func disaster_kind() -> String:
	return str(disaster.get("kind", ""))


func disaster_cost(kind: String, opt: int) -> int:
	return int(Data.DZ[kind].cost[opt] * (1.0 + level / 10.0))


## Which events can happen now (floods need water, blizzards need winter).
func disaster_available() -> Array:
	var out: Array = []
	for k in Data.DZ_KINDS:
		match k:
			"flood":
				if not water.is_empty() and season_name() != "winter":
					out.append(k)
			"blizzard":
				if season_name() == "winter":
					out.append(k)
			"tourists":
				if pop >= 100:
					out.append(k)
			_:
				out.append(k)
	return out


## Buildings in danger: near water for a flood, a handful of random ones for a quake.
func disaster_targets(kind: String) -> Array:
	var out: Array = []
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		if not b.built or Data.B[b.id].cat == "decor":
			continue
		if kind == "flood":
			var near := false
			for dy in range(-4, 5):
				for dx in range(-4, 5):
					if water.has(Vector2i(b.x + dx, b.y + dy)):
						near = true
			if near:
				out.append(uid)
		elif kind == "quake":
			out.append(uid)
	out.shuffle()
	return out.slice(0, 12 if kind == "quake" else 30)


func _update_disaster() -> void:
	if disaster.is_empty():
		disaster = _empty_disaster()
	var now := abs_hour()
	match str(disaster.phase):
		"threat":
			if now >= int(disaster.ends):
				disaster_choose(disaster_kind(), 2)
		"after":
			if now >= int(disaster.ends):
				disaster.phase = ""
				disaster.kind = ""
				disaster.uids = []
				disaster.cd = now + Data.DZ_COOLDOWN
				disaster_changed.emit("end")
				changed.emit()
		_:
			if now >= int(disaster.cd) and now >= Data.DZ_FIRST and pop >= Data.DZ_MIN_POP and not lost and tutorial >= 99 \
					and not protest_active() and not in_jail() and randf() < Data.DZ_CHANCE:
				start_disaster()


## The danger appears: a letter with 3 answers, the effect is visible in the city.
func start_disaster(kind := "") -> bool:
	if disaster_active():
		return false
	var av := disaster_available()
	if kind == "" and not av.is_empty():
		kind = str(av.pick_random())
	if kind == "":
		return false
	disaster.phase = "threat"
	disaster.kind = kind
	disaster.ends = abs_hour() + Data.DZ_HOURS
	disaster.opt = -1
	disaster.hit = false
	disaster.uids = disaster_targets(kind)
	disaster.count = int(disaster.count) + 1
	Events.disaster_started(kind)
	disaster_changed.emit("start")
	changed.emit()
	return true


## The mayor answers (opt 0 expensive and safe, 1 cheap and risky, 2 nothing). No money for 0/1 = nothing.
func disaster_choose(kind: String, opt: int) -> bool:
	if str(disaster.get("phase", "")) != "threat" or kind != disaster_kind() or opt < 0 or opt > 2:
		return false
	var d: Dictionary = Data.DZ[kind]
	if opt < 2 and not pay(disaster_cost(kind, opt), 0, "events"):
		opt = 2
	var hit := false
	var n := 0
	var sick := 0.5 if has_service("health") else 1.0
	if kind == "tourists":
		earn_event("tourists", int(d.gain[opt]))
		garbage = clampf(garbage + float(d.garbage[opt]), 0.0, 100.0)
		hit = opt > 0
	else:
		var risk := float(d.risk[opt])
		if risk < 1.0:
			if has_service("fire"):
				risk -= Data.DZ_FIRE_SAVE
			if has_service("health"):
				risk -= Data.DZ_HEALTH_SAVE
		hit = randf() < risk
		if hit:
			var pool: Array = (disaster.uids as Array).filter(func(u): return buildings.has(u))
			n = clampi(ceili(pool.size() * float(d.frac[opt])), 1, 8) if not pool.is_empty() else 0
			var dmged: Array = []
			for i in n:
				var u: int = pool[i]
				buildings[u].dmg = true
				dmged.append(u)
				building_updated.emit(u)
			disaster.uids = dmged
			n = dmged.size()
		else:
			disaster.uids = []
	var mv := int(round(float(d.mood[opt]) * (sick if int(d.mood[opt]) < 0 else 1.0)))
	if mv != 0:
		add_mood(mv, 24, "disaster_" + kind)
	add_rep(float(d.rep[opt]))
	disaster.phase = "after"
	disaster.opt = opt
	disaster.hit = hit
	disaster.ends = abs_hour() + Data.DZ_AFTER
	Events.disaster_result(kind, opt, hit, n)
	disaster_changed.emit("hit" if hit else "safe")
	recalc()
	changed.emit()
	save_game()
	return true


func broken_rules() -> int:
	var n := 0
	for r in rules:
		if rules[r]:
			n += 1
	return n


func has_service(svc: String) -> bool:
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		if Data.B[b.id].get("svc", "") == svc and b.built and not b.closed and not b.dmg:
			return true
	return false


func service_building(svc: String) -> int:
	for uid in buildings:
		if Data.B[buildings[uid].id].get("svc", "") == svc and _works(uid):
			return uid
	return 0


func covered_by(svc: String, c: Vector2i) -> bool:
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		var d: Dictionary = Data.B[b.id]
		if d.get("svc", "") == svc and _works(uid):
			if maxi(absi(b.x + 1 - c.x), absi(b.y + 1 - c.y)) <= int(d.radius):
				return true
	return false


func _check_lose() -> void:
	if lost or peak_pop < 60:
		return
	if happy <= 2.0 and pop <= peak_pop * 0.4:
		lost = true
		save_game()
		game_over.emit()


func status(uid: int) -> String:
	var b: Dictionary = buildings[uid]
	var d: Dictionary = Data.B[b.id]
	if not b.built or b.upg:
		return ""
	if b.fire > 0.0:
		return "fire"
	if b.dmg:
		return "dmg"
	if b.closed:
		return "closed"
	if d.cat == "decor":
		return ""
	if not road_ok.get(uid, false):
		return "road"
	if b.priv != "":
		return ""
	if d.cat == "shop" and not b.stocked and not b.ready and goods < Data.stat(b.id, "use", b.lvl):
		return "goods"
	if d.cat != "home" and staff < 0.6:
		return "staff"
	return ""


# ====================================================================== actions
func add_xp(n: int) -> void:
	xp += n
	while xp >= Data.xp_for_level(level):
		xp -= Data.xp_for_level(level)
		level += 1
		gems += 1
		sfx("levelup")
		level_up.emit(level)
	check_rank()
	changed.emit()


func rank_name() -> String:
	return Loc.pick([Data.RANKS[rank][2], Data.RANKS[rank][3]])


func rank_bonus() -> float:
	return 1.0 + Data.RANKS[rank][4] / 100.0


## Promote the mayor when level and reputation allow it (never demotes); sends a letter.
func check_rank() -> void:
	var r := Data.rank_for(level, rep)
	if r > rank:
		rank = r
		coins += 500 * r
		gems += r
		sfx("levelup")
		Events.rank_up(r)


func can_afford(c: int, g: int) -> bool:
	return coins >= c and gems >= g


func pay(c: int, g: int, key := "build") -> bool:
	if not can_afford(c, g):
		toast.emit(Loc.t("no_money") if coins < c else Loc.t("no_gems"))
		sfx("error")
		return false
	coins -= c
	gems -= g
	if c > 0:
		_add_ledger("out", key, c)
	changed.emit()
	return true


func place_problem(id: String, x: int, y: int, ignore_uid := 0) -> String:
	var n: int = maxi(1, Data.B[id].size) if id != "road" else 1
	if id != "road":
		if Data.B[id].get("unique", false) and ignore_uid == 0 and buildings.values().any(func(b): return b.id == id):
			return "already_built"
		if Data.B[id].has("needs") and not buildings.values().any(func(b): return b.id == Data.B[id].needs):
			return "need_landmark"
	for dy in n:
		for dx in n:
			var c := Vector2i(x + dx, y + dy)
			if not is_owned(c):
				return "bad_place"
			if (occ.has(c) and occ[c] != ignore_uid) or roads.has(c) or tree_at(c) != "" or walls.has(c):
				return "bad_place"
			if id != "road" and water.has(c):
				return "bad_place"
			if id != "road" and not Data.allowed_in(id, Data.zone_at(c)):
				return "wrong_zone"
	if id == "zoo" and ignore_uid == 0 and caught.size() < Data.ZOO_ANIMALS:
		return "need_animals"
	if id != "road" and Data.B[id].get("highway", false) and not is_connected_to_highway():
		return "need_highway"
	return ""


func can_place(id: String, x: int, y: int) -> bool:
	return place_problem(id, x, y) == ""


func place(id: String, x: int, y: int, rot := -1) -> int:
	var d: Dictionary = Data.B[id]
	var why := place_problem(id, x, y)
	if level < d.lvl:
		why = "locked"
	if in_jail():
		why = "in_jail"
	if why != "":
		toast.emit(Loc.t("locked_lvl") % d.lvl if why == "locked" else Loc.t("in_jail") % jail_hours() if why == "in_jail" else Loc.t(why))
		sfx("error")
		return 0
	if not pay(d.cost, d.get("gems", 0)):
		return 0
	var uid := _add_building(id, x, y, false, 1, rot)
	recalc()
	building_added.emit(uid)
	sfx("place")
	sfx("construct", -8.0)
	save_game()
	return uid


## A business opened by residents (accepted proposal): free for the city, pays a daily tax.
func place_private(id: String, x: int, y: int, owner: String) -> int:
	if place_problem(id, x, y) != "":
		return 0
	var uid := _add_building(id, x, y, false)
	buildings[uid].priv = owner
	recalc()
	building_added.emit(uid)
	return uid


# ====================================================================== residents' brands
## A resident founds a brand; from now on the brand itself proposes its kiosks, shops and flagships.
func found_brand(bid: String, owner: String) -> bool:
	if not Data.BRANDS.has(bid) or brands.has(bid):
		return false
	brands[bid] = {"owner": owner, "day": day}
	save_game()
	return true


## Buildings of a brand (any state), oldest first.
func brand_branches(bid: String) -> Array[int]:
	var out: Array[int] = []
	for uid in buildings:
		if Data.brand_of(buildings[uid].id) == bid:
			out.append(uid)
	out.sort()
	return out


## The brand grows with its chain: level 2 from 3 branches, level 3 from 6; every branch shows the brand's level.
func brand_level(bid: String) -> int:
	var n := brand_branches(bid).size()
	return 1 + int(n >= 3) + int(n >= 6)


## What the brand opens next: first a kiosk, then shops and kiosks by turns, a flagship once it has a few branches.
func brand_next_kind(bid: String) -> String:
	var counts := {"kiosk": 0, "shop": 0, "flag": 0}
	for uid in brand_branches(bid):
		counts[str(buildings[uid].id).trim_prefix(bid + "_")] += 1
	var n: int = counts.kiosk + counts.shop + counts.flag
	if n == 0:
		return "kiosk"
	if n >= Data.BRAND_FLAG_BRANCHES and level >= int(Data.B[bid + "_flag"].lvl) and counts.flag <= n / 6:
		return "flag"
	return "shop" if counts.shop <= counts.kiosk else "kiosk"


## The brand opens a branch at x, y (free for the city, pays a higher daily tax). Returns its uid or 0.
func open_branch(bid: String, kind: String, x: int, y: int) -> int:
	if not brands.has(bid) or not kind in Data.BRAND_KINDS:
		return 0
	var uid := place_private(bid + "_" + kind, x, y, str(brands[bid].owner))
	if uid > 0:
		sync_brand(bid)
		save_game()
	return uid


## Every branch shows the brand's current level (a growing chain renovates all its places).
func sync_brand(bid: String) -> void:
	var lv := brand_level(bid)
	var changed: Array[int] = []
	for uid in brand_branches(bid):
		if int(buildings[uid].lvl) != lv:
			buildings[uid].lvl = lv
			changed.append(uid)
	if changed.is_empty():
		return
	recalc()
	for uid in changed:
		building_updated.emit(uid)


## Turn a building to face another side; the door and the lot turn with it.
func rotate_building(uid: int) -> void:
	if not buildings.has(uid):
		return
	var b: Dictionary = buildings[uid]
	b.rot = (int(b.get("rot", 0)) + 1) % 4
	recalc()
	building_updated.emit(uid)
	sfx("place")
	save_game()


func move_building(uid: int, x: int, y: int, rot := -1) -> bool:
	var b: Dictionary = buildings[uid]
	if rot >= 0:
		b.rot = rot
	if place_problem(b.id, x, y, uid) != "":
		toast.emit(Loc.t("bad_place"))
		sfx("error")
		return false
	_vacate(uid)
	b.x = x
	b.y = y
	_occupy(uid)
	recalc()
	building_moved.emit(uid)
	trees_changed.emit()
	sfx("place")
	save_game()
	return true


func can_upgrade(uid: int) -> String:
	var b: Dictionary = buildings[uid]
	if not b.built or b.upg:
		return "busy"
	if b.lvl >= 3:
		return "max"
	if b.priv != "":
		return "private"
	var up := Data.upgrade_cost(b.id, b.lvl)
	if level < up.level:
		return "level"
	return ""


func upgrade(uid: int) -> bool:
	var b: Dictionary = buildings[uid]
	if in_jail():
		toast.emit(Loc.t("in_jail") % jail_hours())
		sfx("error")
		return false
	if can_upgrade(uid) != "":
		sfx("error")
		return false
	var up := Data.upgrade_cost(b.id, b.lvl)
	if not pay(up.coins, up.gems):
		return false
	b.upg = true
	b.prog = 0.0
	b.ready = false
	recalc()
	building_updated.emit(uid)
	sfx("place")
	save_game()
	return true


func remaining(uid: int) -> float:
	var b: Dictionary = buildings[uid]
	if not b.built:
		return Data.B[b.id].time - b.prog
	if b.upg:
		return Data.upgrade_cost(b.id, b.lvl).time - b.prog
	return 0.0


func speedup_cost(uid: int) -> int:
	return maxi(1, int(ceil(remaining(uid) / 120.0)))


func speedup(uid: int) -> void:
	var r := remaining(uid)
	if r <= 0.0:
		return
	if not pay(0, speedup_cost(uid)):
		return
	sfx("gem")
	buildings[uid].prog += r + 0.01
	simulate(0.0)


func set_closed(uid: int, closed: bool) -> void:
	var b: Dictionary = buildings[uid]
	if b.closed == closed:
		return
	b.closed = closed
	b.ready = false
	b.prog = 0.0
	if closed:
		if Data.B[b.id].cat == "home" and b.occ > 0:
			add_mood(-3, 12, "closed_home")
			add_rep(-1)
		b.occ = 0
	recalc()
	building_updated.emit(uid)
	sfx("door")
	save_game()


func evict(uid: int) -> void:
	var b: Dictionary = buildings[uid]
	if b.occ <= 0:
		return
	b.occ = 0
	b.ready = false
	b.prog = 0.0
	add_rep(-3)
	add_mood(-4, 24, "evicted")
	add_anger("demolish", Data.ANGER_EVICT)
	building_updated.emit(uid)
	sfx("door")
	save_game()


func repair_cost(uid: int) -> int:
	return int(Data.B[buildings[uid].id].cost * 0.25) + 20


func repair(uid: int) -> bool:
	var b: Dictionary = buildings[uid]
	if not b.dmg or not pay(repair_cost(uid), 0, "repairs"):
		return false
	b.dmg = false
	recalc()
	building_updated.emit(uid)
	sfx("upgrade")
	save_game()
	return true


func link_cost() -> int:
	return 200


func can_link(a: int, b: int) -> bool:
	if a == b or not buildings.has(a) or not buildings.has(b):
		return false
	var ba: Dictionary = buildings[a]
	var bb: Dictionary = buildings[b]
	if Data.B[ba.id].cat != "home" or Data.B[bb.id].cat != "home" or ba.link > 0 or bb.link > 0:
		return false
	return absi(ba.x - bb.x) <= 5 and absi(ba.y - bb.y) <= 5


func link_homes(a: int, b: int) -> bool:
	if not can_link(a, b):
		toast.emit(Loc.t("link_bad"))
		sfx("error")
		return false
	if not pay(link_cost(), 0):
		return false
	buildings[a].link = b
	buildings[b].link = a
	recalc()
	building_updated.emit(a)
	building_updated.emit(b)
	sfx("done")
	toast.emit(Loc.t("linked"))
	save_game()
	return true


func unlink(uid: int) -> void:
	var o: int = buildings[uid].link
	buildings[uid].link = 0
	if buildings.has(o):
		buildings[o].link = 0
		building_updated.emit(o)
	building_updated.emit(uid)
	recalc()


func road_path(a: Vector2i, b: Vector2i, type: String) -> Array[Vector2i]:
	## L-shaped path, longer axis first. Keeps tiles that can take this road type.
	var out: Array[Vector2i] = []
	var c := a
	out.append(c)
	var x_first := absi(b.x - a.x) >= absi(b.y - a.y)
	for pass_i in 2:
		if (pass_i == 0) == x_first:
			while c.x != b.x:
				c.x += signi(b.x - a.x)
				out.append(c)
		else:
			while c.y != b.y:
				c.y += signi(b.y - a.y)
				out.append(c)
	var res: Array[Vector2i] = []
	for t in out:
		if roads.has(t):
			if roads[t] != type:
				res.append(t)
		elif can_place("road", t.x, t.y):
			res.append(t)
	return res


func road_cost(tiles: Array[Vector2i], type: String) -> int:
	var cost := 0
	for t in tiles:
		var full := int(Data.ROADS[type].cost)
		if roads.has(t):
			full = maxi(1, full - int(Data.ROADS[roads[t]].cost) / 2)
		cost += full
	return cost


func build_roads(tiles: Array[Vector2i], type: String) -> bool:
	if tiles.is_empty():
		return false
	if not pay(road_cost(tiles, type), 0, "roads"):
		return false
	var paved := false
	for t in tiles:
		roads[t] = type
		if paves.erase(t):
			paved = true
	if paved:
		paves_changed.emit()
	add_xp(tiles.size())
	_rebuild_net()
	recalc()
	roads_changed.emit()
	sfx("road")
	save_game()
	return true


func refund_of(uid: int) -> int:
	var b: Dictionary = buildings[uid]
	if b.priv != "":
		return 0
	return int(Data.B[b.id].cost * (0.3 if b.built else 0.6))


func demolish(uid: int) -> void:
	if not buildings.has(uid):
		return
	var b: Dictionary = buildings[uid]
	coins += refund_of(uid)
	if b.link > 0 and buildings.has(b.link):
		buildings[b.link].link = 0
		building_updated.emit(b.link)
	if Data.B[b.id].cat == "home" and b.occ > 0:
		add_rep(-2)
		add_mood(-2, 12, "demolished")
		add_anger("demolish", Data.ANGER_DEMOLISH)
	if b.priv != "":
		add_rep(-4)
	_vacate(uid)
	buildings.erase(uid)
	recalc()
	building_removed.emit(uid)
	if Data.brand_of(b.id) != "":
		sync_brand(Data.brand_of(b.id))
	sfx("demolish")
	save_game()


func remove_road(c: Vector2i) -> void:
	var t: Array[Vector2i] = [c]
	remove_roads(t)


# ====================================================================== water, walls, street decoration
## Tiles a stroke of the water brush can fill: owned land without buildings or walls. Roads stay and become bridges.
func water_tiles(tiles: Array[Vector2i]) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for t in tiles:
		if is_owned(t) and not occ.has(t) and not walls.has(t) and not water.has(t) and not paves.has(t) and not out.has(t):
			out.append(t)
	return out


func dig_water(tiles: Array[Vector2i]) -> bool:
	var ok := water_tiles(tiles)
	if ok.is_empty() or not pay(ok.size() * Data.WATER_COST, 0, "roads"):
		return false
	for t in ok:
		water[t] = true
	add_xp(ok.size())
	_update_water_bodies()
	recalc()
	water_changed.emit()
	trees_changed.emit()
	sfx("road")
	save_game()
	return true


func fill_water(tiles: Array[Vector2i]) -> bool:
	var any := false
	for t in tiles:
		if water.erase(t):
			any = true
	if not any:
		return false
	_update_water_bodies()
	recalc()
	water_changed.emit()
	sfx("demolish")
	save_game()
	return true


## Connected water grows from a river into a sea and then an ocean.
func _update_water_bodies() -> void:
	water_body.clear()
	for start in water:
		if water_body.has(start):
			continue
		var comp: Array[Vector2i] = [start]
		water_body[start] = 0
		var k := 0
		while k < comp.size():
			var c: Vector2i = comp[k]
			k += 1
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var n: Vector2i = c + d
				if water.has(n) and not water_body.has(n):
					water_body[n] = 0
					comp.append(n)
		var kind := 3 if comp.size() >= Data.WATER_OCEAN else 2 if comp.size() >= Data.WATER_SEA else 1
		for c in comp:
			water_body[c] = kind


## Size class of the water a tile belongs to: 0 none, 1 river, 2 sea, 3 ocean.
func water_kind(c: Vector2i) -> int:
	return int(water_body.get(c, 0))


func wall_tiles(tiles: Array[Vector2i], type: String) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for t in tiles:
		if is_owned(t) and not occ.has(t) and not roads.has(t) and not water.has(t) and not paves.has(t) and walls.get(t, "") != type:
			out.append(t)
	return out


func build_walls(tiles: Array[Vector2i], type: String) -> bool:
	var ok := wall_tiles(tiles, type)
	if ok.is_empty() or not pay(ok.size() * int(Data.WALLS[type].cost), 0, "roads"):
		return false
	for t in ok:
		walls[t] = type
	add_xp(ok.size())
	recalc()
	walls_changed.emit()
	trees_changed.emit()
	sfx("place")
	save_game()
	return true


func remove_walls(tiles: Array[Vector2i]) -> bool:
	var any := false
	for t in tiles:
		if walls.erase(t):
			any = true
	if any:
		recalc()
		walls_changed.emit()
		sfx("demolish")
		save_game()
	return any


## Homes joined by walls make one quarter: a wall line touching a home's side links it, and a home
## carries the line on to the walls on its other sides. Quarters of two or more built homes count.
func _recalc_quarters() -> void:
	quarter_of.clear()
	var seen := {}
	var dirs := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]
	for start in walls:
		if seen.has(start):
			continue
		seen[start] = true
		var homes := {}
		var best := 0
		var todo: Array[Vector2i] = [start]
		while not todo.is_empty():
			var t: Vector2i = todo.pop_back()
			best = maxi(best, int(Data.WALLS.get(walls[t], {}).get("block", 0)))
			for dv in dirs:
				var nt: Vector2i = t + dv
				if walls.has(nt):
					if not seen.has(nt):
						seen[nt] = true
						todo.append(nt)
					continue
				var uid: int = occ.get(nt, 0)
				if uid == 0 or homes.has(uid) or not buildings.has(uid):
					continue
				var hb: Dictionary = buildings[uid]
				if not hb.built or Data.B[hb.id].cat != "home":
					continue
				homes[uid] = true
				var n: int = Data.B[hb.id].size
				for i in n:
					for e in [Vector2i(hb.x + i, hb.y - 1), Vector2i(hb.x + i, hb.y + n), Vector2i(hb.x - 1, hb.y + i), Vector2i(hb.x + n, hb.y + i)]:
						if walls.has(e) and not seen.has(e):
							seen[e] = true
							todo.append(e)
		if homes.size() < 2:
			continue
		var q := {"homes": homes.size(), "happy": mini(homes.size(), Data.QUARTER_HAPPY_MAX) + best, "tile": start}
		for uid in homes:
			quarter_of[uid] = q


## Street improvement: railings, flower pots or bollards along the sidewalks of player roads.
func deco_tiles(tiles: Array[Vector2i], type: String) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for t in tiles:
		if roads.has(t) and road_deco.get(t, "") != type:
			out.append(t)
	return out


func decorate_roads(tiles: Array[Vector2i], type: String) -> bool:
	if type == "none":
		var any := false
		for t in tiles:
			if road_deco.erase(t):
				any = true
		if any:
			walls_changed.emit()
			save_game()
		return any
	var ok := deco_tiles(tiles, type)
	if ok.is_empty() or not pay(ok.size() * int(Data.ROAD_DECO[type].cost), 0, "roads"):
		return false
	for t in ok:
		road_deco[t] = type
	add_xp(ok.size())
	recalc()
	walls_changed.emit()
	sfx("place")
	save_game()
	return true


## Tiles a stroke of the paving brush can pave: owned grass without buildings, roads, water or walls.
func pave_tiles(tiles: Array[Vector2i], type: String) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for t in tiles:
		if is_owned(t) and not occ.has(t) and not roads.has(t) and not water.has(t) and not walls.has(t) \
				and paves.get(t, "") != type and not out.has(t):
			out.append(t)
	return out


func build_paves(tiles: Array[Vector2i], type: String) -> bool:
	var ok := pave_tiles(tiles, type)
	if ok.is_empty() or not pay(ok.size() * int(Data.PAVES[type].cost), 0, "roads"):
		return false
	for t in ok:
		paves[t] = type
	add_xp(ok.size())
	recalc()
	paves_changed.emit()
	trees_changed.emit()
	sfx("road")
	save_game()
	return true


func remove_paves(tiles: Array[Vector2i]) -> bool:
	var any := false
	for t in tiles:
		if paves.erase(t):
			any = true
	if any:
		recalc()
		paves_changed.emit()
		trees_changed.emit()
		sfx("demolish")
		save_game()
	return any


## Player roads along the same L-shaped path the road tool uses.
func removable_path(a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for t in _straight_path(a, b):
		if roads.has(t) and not out.has(t):
			out.append(t)
	return out


func _straight_path(a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	var c := a
	out.append(c)
	var x_first := absi(b.x - a.x) >= absi(b.y - a.y)
	for pass_i in 2:
		if (pass_i == 0) == x_first:
			while c.x != b.x:
				c.x += signi(b.x - a.x)
				out.append(c)
		else:
			while c.y != b.y:
				c.y += signi(b.y - a.y)
				out.append(c)
	return out


func road_refund(tiles: Array[Vector2i]) -> int:
	var n := 0
	for t in tiles:
		if roads.has(t):
			n += int(Data.ROADS[roads[t]].cost) / 2
	return n


func remove_roads(tiles: Array[Vector2i]) -> bool:
	var any := false
	var refund := road_refund(tiles)
	for t in tiles:
		if roads.erase(t):
			any = true
			road_deco.erase(t)
			lights.erase(t)
			rings.erase(t)
			for k in [Vector2i(0, 0), Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1)]:
				lamps.erase(t * 2 + k)
	if not any:
		return false
	coins += refund
	_rebuild_net()
	recalc()
	roads_changed.emit()
	lights_changed.emit()
	lamps_changed.emit()
	sfx("demolish")
	save_game()
	return true


func toggle_light(c: Vector2i) -> bool:
	if lights.has(c):
		lights.erase(c)
	else:
		if not is_intersection(c) or not roads.has(c):
			toast.emit(Loc.t("light_bad"))
			sfx("error")
			return false
		if not pay(Data.LIGHT_COST, 0, "roads"):
			return false
		lights[c] = true
		rings.erase(c)
	recalc()
	lights_changed.emit()
	sfx("place")
	save_game()
	if rules.get("lights", false):
		toast.emit(Loc.t("rule_lights_warn"))
	return true


## A roundabout on a crossing: cars circle the island and give way to those already on the ring.
## It replaces a traffic light on the same tile.
func toggle_ring(c: Vector2i) -> bool:
	if rings.has(c):
		rings.erase(c)
	else:
		if not is_intersection(c) or not roads.has(c):
			toast.emit(Loc.t("ring_bad"))
			sfx("error")
			return false
		if not pay(Data.RING_COST, 0, "roads"):
			return false
		rings[c] = true
		lights.erase(c)
	recalc()
	lights_changed.emit()
	sfx("place")
	save_game()
	return true


## Lamps live on a half-tile grid: quarter q covers grid position q / 2 .. q / 2 + 0.5.
## Street lamps stand on the sidewalk corners of player roads: slot q = 2 * tile + corner.
func lamp_problem(q: Vector2i) -> String:
	var tile := Vector2i(floori(q.x / 2.0), floori(q.y / 2.0))
	if not roads.has(tile) or not is_owned(tile) or lamps.has(q):
		return "lamp_road"
	var p := LampView.slot_grid(q)
	for o in lamps:
		if LampView.slot_grid(o).distance_to(p) < 0.7:
			return "lamp_close"
	return ""


func place_lamp(q: Vector2i, style: String) -> bool:
	var why := lamp_problem(q)
	if level < int(Data.B.lamp.lvl):
		why = "locked"
	if why != "":
		toast.emit(Loc.t(why) if why != "locked" else Loc.t("locked_lvl") % Data.B.lamp.lvl)
		sfx("error")
		return false
	if not pay(Data.LAMP_COST, 0):
		return false
	lamps[q] = style
	add_xp(1)
	recalc()
	lamps_changed.emit()
	sfx("place")
	save_game()
	return true


func remove_lamp(q: Vector2i) -> void:
	if lamps.erase(q):
		recalc()
		lamps_changed.emit()
		sfx("demolish")
		save_game()


## A lamp over the front door of a built home; style is one of the street lamp styles.
func house_lamp_problem(uid: int) -> String:
	if not buildings.has(uid) or Data.B[buildings[uid].id].cat != "home":
		return "hlamp_home"
	if not buildings[uid].built:
		return "hlamp_built"
	return ""


func place_house_lamp(uid: int, style: String) -> bool:
	var why := house_lamp_problem(uid)
	if level < int(Data.B.lamp.lvl):
		why = "locked"
	elif why == "" and buildings[uid].hlamp == style:
		why = "hlamp_same"
	if why != "":
		toast.emit(Loc.t(why) if why != "locked" else Loc.t("locked_lvl") % Data.B.lamp.lvl)
		sfx("error")
		return false
	if not pay(Data.HOUSE_LAMP_COST, 0):
		return false
	buildings[uid].hlamp = style
	add_xp(1)
	recalc()
	building_updated.emit(uid)
	sfx("place")
	save_game()
	return true


func remove_house_lamp(uid: int) -> void:
	if buildings.has(uid) and buildings[uid].get("hlamp", "") != "":
		buildings[uid].hlamp = ""
		recalc()
		building_updated.emit(uid)
		sfx("demolish")
		save_game()


func house_lamp_count() -> int:
	var n := 0
	for uid in buildings:
		if buildings[uid].get("hlamp", "") != "":
			n += 1
	return n


func clear_tree(c: Vector2i) -> bool:
	if tree_at(c) == "" or not pay(Data.TREE_CLEAR_COST, 0):
		return false
	cleared_trees[c] = true
	add_xp(1)
	trees_changed.emit()
	sfx("demolish")
	return true


func collect(uid: int) -> Dictionary:
	var b: Dictionary = buildings.get(uid, {})
	if b.is_empty() or not b.ready:
		return {}
	var d: Dictionary = Data.B[b.id]
	var res := {}
	var mf := 0.7 + 0.6 * happy / 100.0
	match d.cat:
		"home":
			var cap := Data.stat(b.id, "pop", b.lvl)
			var fill := clampf(float(b.occ) / maxf(1.0, cap), 0.0, 1.0)
			res = {"coins": maxi(1, int(round(Data.stat(b.id, "rent", b.lvl) * fill * tax / 10.0 * mf)))}
		"shop", "fun":
			if d.get("landmark", false):
				mf *= landmark_bonus()
			res = {"coins": maxi(1, int(round(Data.stat(b.id, "income", b.lvl) * mf)))}
			b.stocked = false
		"ind":
			res = {"goods": Data.stat(b.id, "out", b.lvl)}
	b.ready = false
	b.prog = 0.0
	if res.has("coins"):
		coins += res.coins
		stats.coins_total = int(stats.coins_total) + res.coins
		_add_ledger("in", "rent" if d.cat == "home" else "shops", res.coins)
		sfx("coin")
		add_xp(maxi(1, res.coins / 25))
	else:
		goods += res.goods
		stats.goods_total = int(stats.goods_total) + res.goods
		sfx("goods")
		add_xp(maxi(1, res.goods / 12))
	if _rng.randf() < Data.GEM_CHANCE:
		gems += 1
		res["gems"] = 1
		sfx("gem")
		gem_found.emit(uid)
	building_updated.emit(uid)
	changed.emit()
	return res


func buy_plot(p: Vector2i, with_gems: bool) -> bool:
	if not plot_buyable(p):
		return false
	var price := Data.plot_price(plots.size())
	if level < price.level and not with_gems:
		toast.emit(Loc.t("locked_lvl") % price.level)
		sfx("error")
		return false
	if not pay(0 if with_gems else price.coins, price.gems if with_gems else 0, "land"):
		return false
	plots.append(p)
	add_xp(price.coins / 60)
	land_changed.emit()
	changed.emit()
	sfx("done")
	toast.emit(Loc.t("expanded"))
	save_game()
	return true


func set_tax(v: int) -> void:
	tax = clampi(v, Data.TAX_MIN, Data.TAX_MAX)
	recalc()
	save_game()


# ---------------------------------------------------------------- bank
func loan_offers() -> Array[int]:
	var out: Array[int] = [2000]
	if level >= 8:
		out.append(5000)
	if level >= 12 and rep >= 40:
		out.append(15000)
	if level >= 16 and rep >= 55:
		out.append(40000)
	return out


func loan_rate() -> float:
	return 0.12 if rep >= 70 else 0.2 if rep >= 40 else 0.3


func take_loan(amount: int) -> bool:
	if not loan.is_empty() or not has_service("bank"):
		sfx("error")
		return false
	var total := int(amount * (1.0 + loan_rate()))
	loan = {"left": total, "daily": int(ceil(total / 7.0)), "days": 7, "amount": amount}
	coins += amount
	_add_ledger("in", "loan", amount)
	sfx("coin")
	changed.emit()
	save_game()
	return true


func repay_loan() -> bool:
	if loan.is_empty() or not pay(int(loan.left), 0, "loan"):
		return false
	loan = {}
	add_rep(1)
	save_game()
	return true


func move_deposit(amount: int) -> bool:
	## positive: put coins in, negative: take them out
	if (amount > 0 and coins < amount) or (amount < 0 and deposit < -amount) or amount == 0:
		sfx("error")
		return false
	coins -= amount
	deposit += amount
	sfx("coin")
	changed.emit()
	save_game()
	return true


# ---------------------------------------------------------------- animals
func catch_chance(species: String) -> float:
	return {"rabbit": 0.8, "deer": 0.6, "fox": 0.55, "boar": 0.45, "wolf": 0.35, "bear": 0.25}.get(species, 0.5)


func try_catch(species: String) -> int:
	## 1 caught, 0 escaped, -1 could not pay
	if not pay(Data.CATCH_COST, 0, "zoo"):
		return -1
	if _rng.randf() < catch_chance(species):
		caught.append(species)
		add_xp(15)
		sfx("done")
		animals_changed.emit()
		changed.emit()
		save_game()
		return 1
	sfx("error")
	return 0


# ====================================================================== missions
func mission_value(m: Dictionary) -> int:
	var t: String = m.type
	if t.begins_with("build:"):
		var id := t.substr(6)
		var n := 0
		for uid in buildings:
			if buildings[uid].id == id and buildings[uid].built:
				n += 1
		return n
	match t:
		"roads": return roads.size()
		"pop": return pop
		"level": return level
		"happy": return int(happy)
		"rep": return int(rep)
		"coins_total": return int(stats.coins_total)
		"goods_total": return int(stats.goods_total)
		"plots": return plots.size()
		"upgrades": return int(stats.get("upgrades", 0))
		"lamps": return lamps.size()
		"animals": return caught.size()
		"lvl3":
			var n := 0
			for uid in buildings:
				if buildings[uid].lvl >= 3:
					n += 1
			return n
	return 0


func active_missions() -> Array[int]:
	var out: Array[int] = []
	for i in Data.MISSIONS.size():
		if not claimed.has(i):
			out.append(i)
			if out.size() >= 3:
				break
	return out


func mission_done(i: int) -> bool:
	return mission_value(Data.MISSIONS[i]) >= Data.MISSIONS[i].n


func claim(i: int) -> void:
	if claimed.has(i) or not mission_done(i):
		return
	var m: Dictionary = Data.MISSIONS[i]
	claimed.append(i)
	coins += m.coins
	gems += m.gems
	_add_ledger("in", "missions", m.coins)
	sfx("done")
	toast.emit(Loc.t("mission_done"))
	add_rep(1)
	add_xp(m.xp)
	save_game()


func ready_missions() -> int:
	var n := 0
	for i in active_missions():
		if mission_done(i):
			n += 1
	return n + Events.story_ready()


# ====================================================================== time of day & weather
const TINT_KEYS := [
	[0.00, Color(0.30, 0.35, 0.62)], [0.20, Color(0.30, 0.35, 0.62)], [0.24, Color(0.80, 0.62, 0.74)],
	[0.28, Color(1.00, 0.86, 0.72)], [0.36, Color(1.0, 1.0, 1.0)], [0.70, Color(1.0, 1.0, 1.0)],
	[0.75, Color(1.00, 0.76, 0.54)], [0.80, Color(0.68, 0.50, 0.66)], [0.833, Color(0.30, 0.35, 0.62)],
	[1.00, Color(0.30, 0.35, 0.62)],
]


func world_tint() -> Color:
	var c := Color.WHITE
	for i in TINT_KEYS.size() - 1:
		var a: Array = TINT_KEYS[i]
		var b: Array = TINT_KEYS[i + 1]
		if day_time >= a[0] and day_time <= b[0]:
			c = (a[1] as Color).lerp(b[1], (day_time - a[0]) / maxf(0.0001, b[0] - a[0]))
			break
	match weather:
		"rain":
			c *= Color(0.8, 0.84, 0.92)
		"storm":
			c *= Color(0.62, 0.66, 0.78)
		"fog":
			c = c.lerp(Color(0.85, 0.87, 0.9), 0.25)
		"cloudy":
			c *= Color(0.92, 0.93, 0.96)
		"snow":
			c *= Color(0.94, 0.96, 1.02)
		"windy":
			c *= Color(0.96, 0.98, 0.97)
		"heat":
			c *= Color(1.05, 0.98, 0.86)
	return c


func night_amount() -> float:
	var t := day_time
	var n := 0.0
	if t >= 0.833 or t < 0.2:
		n = 1.0
	elif t >= 0.75:
		n = (t - 0.75) / 0.083
	elif t < 0.27:
		n = 1.0 - (t - 0.2) / 0.07
	if weather == "storm":
		n = maxf(n, 0.55)
	elif weather == "rain":
		n = maxf(n, 0.25)
	return n


func phase_name() -> String:
	var h := day_time * 24.0
	if h >= 5.0 and h < 9.0:
		return "morning"
	if h >= 9.0 and h < 18.0:
		return "day"
	if h >= 18.0 and h < 20.0:
		return "evening"
	return "night"


func clock_text() -> String:
	var minutes := int(day_time * 24.0 * 60.0)
	return "%02d:%02d" % [minutes / 60, minutes % 60]


func _pick_weather() -> void:
	var table: Dictionary = {
		"spring": {"clear": 4, "cloudy": 3, "rain": 3, "storm": 1, "fog": 1, "windy": 2},
		"summer": {"clear": 6, "cloudy": 2, "rain": 1, "storm": 2, "heat": 2, "windy": 1},
		"autumn": {"clear": 2, "cloudy": 3, "rain": 4, "storm": 1, "fog": 2, "windy": 3},
		"winter": {"clear": 2, "cloudy": 3, "snow": 5, "fog": 1, "windy": 2},
	}[season_name()]
	var total := 0
	for k in table:
		total += int(table[k])
	var r := _rng.randi() % total
	var pick := "clear"
	for k in table:
		r -= int(table[k])
		if r < 0:
			pick = k
			break
	set_weather(pick, _rng.randi_range(3, 8))


func set_weather(kind: String, hours: int) -> void:
	weather_until = abs_hour() + hours
	if kind != weather:
		weather = kind
		weather_changed.emit(kind)
		recalc()


# ====================================================================== sound
func sfx(sound: String, vol_db := 0.0, pitch := 1.0) -> void:
	if not settings.sound:
		return
	if not _sfx_cache.has(sound):
		var stream: AudioStream = null
		for ext in ["ogg", "wav"]:
			var path := "res://assets/sfx/%s.%s" % [sound, ext]
			if ResourceLoader.exists(path):
				stream = load(path)
				break
		_sfx_cache[sound] = stream
	if _sfx_cache[sound] == null:
		return
	for p in _sfx:
		if not p.playing:
			p.stream = _sfx_cache[sound]
			p.pitch_scale = pitch * randf_range(0.96, 1.04)
			p.volume_db = vol_db
			p.play()
			return


func set_setting(key: String, value) -> void:
	settings[key] = value
	if key == "lang":
		Loc.set_lang(value)
	save_game()


func _music_for_phase() -> String:
	if not profile.intro:
		return "music_title"
	match phase_name():
		"morning":
			return "music_morning"
		"evening":
			return "music_evening"
		"night":
			return "music_night"
	return "music_day"


func _load_loop(name: String) -> AudioStream:
	for ext in ["ogg", "wav"]:
		var path := "res://assets/sfx/%s.%s" % [name, ext]
		if ResourceLoader.exists(path):
			var s = load(path)
			if s is AudioStreamWAV:
				s.loop_mode = AudioStreamWAV.LOOP_FORWARD
				s.loop_begin = 0
				s.loop_end = int(s.get_length() * s.mix_rate)
			elif s is AudioStreamOggVorbis:
				s.loop = true
			return s
	return null


func _update_music(delta: float) -> void:
	var want := _music_for_phase() if settings.music else ""
	if want != _music_track:
		_music_track = want
		var tmp := _music_a
		_music_a = _music_b
		_music_b = tmp
		if want != "":
			_music_a.stream = _load_loop(want)
			_music_a.volume_db = -50.0
			if _music_a.stream:
				_music_a.play()
	if _music_a.playing:
		_music_a.volume_db = move_toward(_music_a.volume_db, -10.0, delta * 12.0)
	if _music_b.playing:
		_music_b.volume_db = move_toward(_music_b.volume_db, -60.0, delta * 12.0)
		if _music_b.volume_db <= -59.0:
			_music_b.stop()
	# weather / city ambience loop
	var amb := ""
	if settings.sound and profile.intro and not lost:
		match weather:
			"rain":
				amb = "amb_rain"
			"storm":
				amb = "amb_storm"
			_:
				amb = "amb_night" if phase == "night" else "amb_city"
	if amb != _ambient_track:
		_ambient_track = amb
		_ambient.stop()
		if amb != "":
			_ambient.stream = _load_loop(amb)
			_ambient.volume_db = -40.0
			if _ambient.stream:
				_ambient.play()
	if _ambient.playing:
		_ambient.volume_db = move_toward(_ambient.volume_db, -14.0 if weather in ["rain", "storm"] else -20.0, delta * 8.0)


# ====================================================================== garbage
## Waste made per in-game hour by the residents.
func garbage_rate() -> float:
	return pop * 0.04


## Waste the working depots and plants carry away per hour (a truck leaves each one).
func garbage_capacity() -> int:
	var c := 0
	for uid in buildings:
		var d: Dictionary = Data.B[buildings[uid].id]
		if d.get("svc", "") == "garbage" and _works(uid):
			c += int(d.garb) * buildings[uid].lvl
	return c


func garbage_depots() -> Array:
	var r: Array = []
	for uid in buildings:
		if Data.B[buildings[uid].id].get("svc", "") == "garbage" and _works(uid):
			r.append(uid)
	return r


func garbage_mood() -> int:
	return clampi(int((garbage - 40.0) / 6.0), 0, 10)


func garbage_level() -> String:
	return "low" if garbage < 30.0 else "mid" if garbage < 60.0 else "high"


func _update_garbage() -> void:
	var before := garbage
	garbage = clampf(garbage + garbage_rate() - garbage_capacity(), 0.0, GARBAGE_MAX)
	if before < 60.0 and garbage >= 60.0 and pop > 100:
		toast.emit(Loc.t("garbage_warn"))


# ====================================================================== airport
## The working airport, or 0.
func airport_uid() -> int:
	for uid in buildings:
		if Data.B[buildings[uid].id].get("svc", "") == "airport" and _works(uid):
			return uid
	return 0


func has_airport() -> bool:
	return buildings.values().any(func(b): return Data.B[b.id].get("svc", "") == "airport")


func buy_flight(id: String) -> bool:
	if not Data.COUNTRIES.has(id) or flights.has(id):
		return false
	if not has_airport():
		toast.emit(Loc.t("air_need"))
		sfx("error")
		return false
	var c: Dictionary = Data.COUNTRIES[id]
	if level < int(c.lvl):
		toast.emit(Loc.t("locked_lvl") % int(c.lvl))
		sfx("error")
		return false
	if not pay(int(c.cost), 0, "build"):
		return false
	flights.append(id)
	add_xp(int(c.cost) / 80)
	changed.emit()
	sfx("done")
	toast.emit(Loc.t("air_bought") % Data.country_name(id))
	save_game()
	return true


## A plane lands from this route: travellers arrive and spend money (more with hotels in town).
func land_flight(id: String) -> int:
	var uid := airport_uid()
	if uid == 0 or not flights.has(id):
		return 0
	var c: Dictionary = Data.COUNTRIES[id]
	var pax := int(round(int(c.pax) * _rng.randf_range(0.6, 1.2) * (1.0 + 0.25 * (buildings[uid].lvl - 1))))
	var first := not arrivals.has(id)
	arrivals[id] = int(arrivals.get(id, 0)) + pax
	arrivals_day[id] = int(arrivals_day.get(id, 0)) + pax
	var hotels := buildings.values().filter(func(b): return Data.B[b.id].get("tab", "") == "hotel" and b.built).size()
	var spend := int(pax * int(c.spend) * (1.0 + minf(hotels, 5) * 0.1) * law_mult("tour"))
	if spend > 0:
		_earn("flights", spend)
	if first:
		toast.emit(Loc.t("air_first") % Data.country_name(id))
	plane_landed.emit(id, pax)
	return pax


func _update_airport() -> void:
	if flights.is_empty() or hour() < 6 or airport_uid() == 0:
		return
	for id in flights:
		if _rng.randf() < Data.FLIGHT_CHANCE:
			land_flight(id)


func arrivals_total(today_only := false) -> int:
	var n := 0
	var d: Dictionary = arrivals_day if today_only else arrivals
	for k in d:
		n += int(d[k])
	return n


## [country, all time, today] for every country that sent people, most first.
func arrival_stats() -> Array:
	var r: Array = []
	for k in arrivals:
		r.append([k, int(arrivals[k]), int(arrivals_day.get(k, 0))])
	r.sort_custom(func(a, b): return a[1] > b[1])
	return r


# ====================================================================== newspaper
## Loc keys of today's headlines (most important first), chosen by the state of the city.
func paper_headlines() -> Array:
	var h: Array = []
	var burning := 0
	for uid in buildings:
		if buildings[uid].fire > 0.0:
			burning += 1
	if burning > 0:
		h.append("n_fire")
	for m in mood:
		if str(m.why) == "crime":
			h.append("n_crime")
			break
	if protest_active():
		h.append("n_protest")
	if in_jail():
		h.append("n_jail")
	elif int(crime.get("caught", 0)) > 0 and int(crime.get("heists", 0)) > 0:
		h.append("n_heist")
	if power_ratio < 0.85:
		h.append("n_power")
	if water_ratio < 0.9:
		h.append("n_water")
	if weather in ["storm", "heat"]:
		h.append("n_" + weather)
	if unemployment > 0.1:
		h.append("n_jobless")
	elif workers > 0 and unemployment <= 0.03:
		h.append("n_work")
	if pop > 100 and garbage >= 60.0:
		h.append("n_garbage")
	if happy >= 75.0:
		h.append("n_happy")
	elif happy < 35.0:
		h.append("n_sad")
	if coins >= 50000:
		h.append("n_rich")
	elif coins < 500:
		h.append("n_poor")
	if not loan.is_empty():
		h.append("n_loan")
	if pop >= 1000:
		h.append("n_pop3")
	elif pop >= 300:
		h.append("n_pop2")
	elif pop >= 50:
		h.append("n_pop1")
	for r in rules:
		if rules[r]:
			h.append("n_rules")
			break
	if has_service("tv"):
		h.append("n_tv")
	if arrivals_total(true) > 0:
		h.append("n_flights")
	if h.is_empty():
		h.append("n_calm")
	return h


# ====================================================================== achievements + daily reward (ROADMAP 30)
func _empty_ach() -> Dictionary:
	## got: achievement id -> tiers earned; last: day number of the last login; streak/best: days in a row;
	## logins: days visited; pending: today's reward is waiting to be taken; cycle: its place in the 7-day cycle.
	return {"got": {}, "last": 0, "streak": 0, "best": 0, "logins": 0, "pending": false, "cycle": 0}


static func _load_ach(d: Dictionary) -> Dictionary:
	var a := {"got": {}, "last": 0, "streak": 0, "best": 0, "logins": 0, "pending": false, "cycle": 0}
	for k in ["last", "streak", "best", "logins", "cycle"]:
		a[k] = int(d.get(k, 0))
	a.pending = bool(d.get("pending", false))
	for k in d.get("got", {}):
		a.got[str(k)] = int(d.got[k])
	return a


## Number of the real-world day (local time), for the daily reward.
static func real_day() -> int:
	var bias := int(Time.get_time_zone_from_system().get("bias", 0))
	return floori((Time.get_unix_time_from_system() + bias * 60.0) / 86400.0)


## A new real day starts the next step of the 7-day streak (a missed day resets it). Returns true when a reward is waiting.
func daily_roll(today_no := -1) -> bool:
	var n := today_no if today_no >= 0 else real_day()
	var last := int(ach.last)
	if n != last:
		ach.streak = int(ach.streak) + 1 if n == last + 1 else 1
		ach.cycle = (int(ach.streak) - 1) % 7
		ach.last = n
		ach.logins = int(ach.logins) + 1
		ach.best = maxi(int(ach.best), int(ach.streak))
		ach.pending = true
		check_ach()
	return bool(ach.pending)


func daily_claim() -> Dictionary:
	if not bool(ach.pending):
		return {}
	var r := Ach.daily_reward(int(ach.cycle))
	ach.pending = false
	coins += int(r.coins)
	gems += int(r.gems)
	stats.coins_total = int(stats.coins_total) + int(r.coins)
	sfx("levelup")
	changed.emit()
	return r


func check_ach() -> void:
	if lost or not profile.intro:
		return
	var got := Ach.check()
	if got.is_empty():
		return
	var lines := []
	for g in got:
		var a: Array = g[0]
		var tiers: int = (a[4] as Array).size()
		var star: String = "" if tiers == 1 else " " + ["I", "II", "III", "IV"][mini(int(g[1]), 3)]
		var gem_txt := " +%d %s" % [int(g[2].gems), Loc.t("gems")] if int(g[2].gems) > 0 else ""
		lines.append(Loc.t("ach_toast") % [Loc.pick(a[2]) + star, Loc.num(int(g[2].coins)), gem_txt])
	toast.emit("\n".join(lines))
	sfx("levelup")
	changed.emit()
