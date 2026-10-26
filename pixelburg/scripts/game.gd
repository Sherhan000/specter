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

const SAVE_PATH := "user://city.json"
const SAVE_VERSION := 4
const SEASONS := ["spring", "summer", "autumn", "winter"]

# ------------------------------------------------------------------ saved state
var coins := 0
var gems := 0
var goods := 0
var xp := 0
var level := 1
var plots: Array = []        ## owned plots (Vector2i)
var roads := {}              ## Vector2i -> road type (player roads)
var lights := {}             ## Vector2i -> true (traffic lights on intersections)
var lamps := {}              ## Vector2i quarter cell -> style ("classic" / "modern")
var buildings := {}          ## uid -> dictionary, see _add_building
var next_uid := 1
var cleared_trees := {}
var claimed: Array = []
var stats := {"coins_total": 0, "goods_total": 0, "upgrades": 0}
var settings := {"sound": true, "music": true, "lang": ""}
var profile := {"name": "", "age": 0, "gender": "", "privacy": false, "intro": false}
var day := 1
var day_time := 0.29
var tax := Data.TAX_DEFAULT
var rep := 50.0
var happy := 55.0
var peak_pop := 0
var caught: Array = []       ## species names of animals caught for the zoo
var weather := "clear"
var weather_until := 0       ## absolute hour when the weather changes
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
var rules := {}              ## rule -> true if broken
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
				natural_trees[c] = "tree_%d" % rng.randi_range(0, 7)


func _in_start_layout(c: Vector2i) -> bool:
	return c.x >= Data.CENTER - 6 and c.x <= Data.CENTER + 13 and absi(c.y - Data.CENTER) <= 5


func is_owned(c: Vector2i) -> bool:
	return Data.in_land(c) and plots.has(Data.plot_of(c))


func tree_at(c: Vector2i) -> String:
	if cleared_trees.has(c) or occ.has(c) or roads.has(c):
		return ""
	return natural_trees.get(c, "")


func plot_buyable(p: Vector2i) -> bool:
	if plots.has(p) or p.x < 0 or p.y < 0 or p.x >= Data.PLOTS or p.y >= Data.PLOTS:
		return false
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		if plots.has(p + d):
			return true
	return false


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
	roads = {}
	lights = {}
	lamps = {}
	buildings = {}
	occ = {}
	next_uid = 1
	cleared_trees = {}
	claimed = []
	stats = {"coins_total": 0, "goods_total": 0, "upgrades": 0}
	day = 1
	day_time = 0.29
	tax = Data.TAX_DEFAULT
	rep = 50.0
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
		"ready": false, "stocked": false, "occ": 0, "closed": false, "dmg": false, "priv": "", "link": 0, "fire": 0.0}
	_occupy(uid)
	return uid


func _occupy(uid: int) -> void:
	var b: Dictionary = buildings[uid]
	var n: int = Data.B[b.id].size
	for dy in n:
		for dx in n:
			occ[Vector2i(b.x + dx, b.y + dy)] = uid


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
		"roads": roads.keys().map(func(v): return [v.x, v.y, roads[v]]),
		"lights": lights.keys().map(func(v): return [v.x, v.y]),
		"lamps": lamps.keys().map(func(v): return [v.x, v.y, lamps[v]]),
		"cleared": cleared_trees.keys().map(func(v): return [v.x, v.y]),
		"buildings": buildings.keys().map(func(u): return [u, buildings[u]]),
		"next_uid": next_uid, "claimed": claimed, "stats": stats, "settings": settings, "profile": profile,
		"day": day, "day_time": day_time, "tax": tax, "rep": rep, "happy": happy, "peak_pop": peak_pop,
		"caught": caught, "weather": weather, "weather_until": weather_until, "mood": mood,
		"ledger": ledger, "today": today, "loan": loan, "deposit": deposit, "tutorial": tutorial, "lost": lost,
		"events": Events.to_dict(),
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
	roads = {}
	for v in p.roads:
		roads[_v2(v)] = str(v[2]) if Data.ROADS.has(str(v[2])) else "asphalt"
	lights = {}
	for v in p.get("lights", []):
		lights[_v2(v)] = true
	lamps = {}
	for v in p.get("lamps", []):
		lamps[_v2(v)] = str(v[2])
	cleared_trees = {}
	for v in p.cleared:
		cleared_trees[_v2(v)] = true
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
			"dmg": bool(b.get("dmg", false)), "priv": str(b.get("priv", "")), "link": int(b.get("link", 0)), "fire": float(b.get("fire", 0.0))}
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
	mood = p.get("mood", [])
	ledger = p.get("ledger", [])
	today = p.get("today", _empty_day())
	loan = p.get("loan", {})
	deposit = int(p.get("deposit", 0))
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
	day_time += delta / Data.DAY_LENGTH
	if day_time >= 1.0:
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
	if now >= weather_until:
		_pick_weather()
	recalc()
	_check_lose()
	hour_passed.emit(hour())
	Events.on_hour(hour())


func _end_of_day() -> void:
	# ---- passive income
	var biz_tax := 0
	for uid in buildings:
		var b: Dictionary = buildings[uid]
		if b.priv != "" and b.built and not b.closed and not b.dmg:
			biz_tax += int(Data.stat(b.id, "income", b.lvl) * 3 * tax / 10.0)
	if biz_tax > 0:
		_earn("taxes", biz_tax)
	if is_connected_to_highway():
		var tour := int(pop * 0.08 * (happy / 100.0) * (0.5 + rep / 100.0))
		for uid in buildings:
			var b: Dictionary = buildings[uid]
			if Data.B[b.id].cat == "fun" and _works(uid):
				tour += 60 * b.lvl
		if tour > 0:
			_earn("tourism", tour)
		if goods > 400:
			var sold := (goods - 400) / 4
			goods -= sold
			_earn("export", sold / 2)
	if deposit > 0:
		var interest := maxi(1, int(deposit * 0.015))
		deposit += interest
		_add_ledger("in", "interest", interest)
	# ---- expenses
	_spend("upkeep", daily_upkeep())
	_spend("roads", daily_roads())
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
	total += lamps.size() * 0.5 + lights.size() * 2.0
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
	workforce = int(pop * Data.WORKFORCE)
	workers = mini(workforce, jobs)
	staff = 1.0 if jobs == 0 else clampf(float(workers) / jobs, 0.15, 1.0)
	unemployment = 0.0 if workforce == 0 else maxf(0.0, float(workforce - jobs) / workforce)
	_check_rules()
	home_happy.clear()
	home_reasons.clear()
	var global := 45 + mood_total() + weather_mood() - int(round((tax - Data.TAX_DEFAULT) * 2.2)) - int(unemployment * 22.0)
	for r in rules:
		if rules[r]:
			global -= 2
	var has_gov := false
	for uid in infl:
		if Data.B[buildings[uid].id].get("svc", "") == "gov":
			has_gov = true
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
					if od.svc == "gov" or dist <= od.radius:
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
		for key in ["edu", "fire", "police", "health"]:
			if svc.has(key):
				var v: int = {"edu": 8, "fire": 5, "police": 7, "health": 9}[key]
				h += v
				reasons.append(["r_" + key, v])
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
		if poll > 0:
			h -= mini(poll * 2, 22)
			reasons.append(["r_poll", -mini(poll * 2, 22)])
		var rt := _road_type_near(b.x, b.y, n)
		if rt == "stone":
			h += 2
		elif rt == "dirt":
			h -= 2
			reasons.append(["r_dirt", -2])
		if b.link > 0 and buildings.has(b.link):
			h += 3
			reasons.append(["r_link", 3])
		h += mini(_lamps_near(hc, 2.6), 3)
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
	rules["school"] = pop > 150 and not have.has("edu")
	rules["fire"] = pop > 200 and not have.has("fire")
	rules["police"] = pop > 300 and not have.has("police")
	rules["health"] = pop > 500 and not have.has("health")
	rules["decor"] = pop > 40 and decor_n * 30 < pop
	rules["budget"] = coins < 0


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
	changed.emit()


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
	for dy in n:
		for dx in n:
			var c := Vector2i(x + dx, y + dy)
			if not is_owned(c):
				return "bad_place"
			if (occ.has(c) and occ[c] != ignore_uid) or roads.has(c) or tree_at(c) != "":
				return "bad_place"
			if id != "road" and not Data.allowed_in(id, Data.zone_at(c)):
				return "wrong_zone"
	if id == "zoo" and ignore_uid == 0 and caught.size() < Data.ZOO_ANIMALS:
		return "need_animals"
	return ""


func can_place(id: String, x: int, y: int) -> bool:
	return place_problem(id, x, y) == ""


func place(id: String, x: int, y: int, rot := -1) -> int:
	var d: Dictionary = Data.B[id]
	var why := place_problem(id, x, y)
	if level < d.lvl:
		why = "locked"
	if why != "":
		toast.emit(Loc.t(why) if why != "locked" else Loc.t("locked_lvl") % d.lvl)
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
	for t in tiles:
		roads[t] = type
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
	if b.priv != "":
		add_rep(-4)
	_vacate(uid)
	buildings.erase(uid)
	recalc()
	building_removed.emit(uid)
	sfx("demolish")
	save_game()


func remove_road(c: Vector2i) -> void:
	var t: Array[Vector2i] = [c]
	remove_roads(t)


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
			lights.erase(t)
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
	recalc()
	lights_changed.emit()
	sfx("place")
	save_game()
	if rules.get("lights", false):
		toast.emit(Loc.t("rule_lights_warn"))
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
	[0.28, Color(1.00, 0.86, 0.72)], [0.36, Color(1.0, 1.0, 1.0)], [0.72, Color(1.0, 1.0, 1.0)],
	[0.78, Color(1.00, 0.76, 0.54)], [0.84, Color(0.68, 0.50, 0.66)], [0.89, Color(0.30, 0.35, 0.62)],
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
	return c


func night_amount() -> float:
	var t := day_time
	var n := 0.0
	if t >= 0.89 or t < 0.2:
		n = 1.0
	elif t >= 0.8:
		n = (t - 0.8) / 0.09
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
	if h >= 18.0 and h < 22.0:
		return "evening"
	return "night"


func clock_text() -> String:
	var minutes := int(day_time * 24.0 * 60.0)
	return "%02d:%02d" % [minutes / 60, minutes % 60]


func _pick_weather() -> void:
	var table: Dictionary = {
		"spring": {"clear": 4, "cloudy": 3, "rain": 3, "storm": 1, "fog": 1},
		"summer": {"clear": 7, "cloudy": 2, "rain": 1, "storm": 2},
		"autumn": {"clear": 2, "cloudy": 3, "rain": 4, "storm": 1, "fog": 2},
		"winter": {"clear": 2, "cloudy": 3, "snow": 5, "fog": 1},
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
