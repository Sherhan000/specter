extends Node
## Dev only: frame-time budget of the simulation in a big city (headless: scripts only).
## Headless frames are capped near 145 fps, so a median of ~6.9 ms means the work fits.

var city


func _ready() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json"))
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json.bak"))
	Events.reset()
	Game.new_game()
	Game.profile = {"name": "Test", "age": 30, "gender": "m", "privacy": true, "intro": true}
	Game.tutorial = 99
	Events.chapter = 9
	Events.flags = {"zoo_arc": true, "hall_arc": true, "election_done": true}
	var big := OS.get_environment("PERF_SMALL") == ""
	if big:
		var sc = load("res://tools/dev/showcase.gd").new()
		sc._build_city()
		sc.free()
	Game.day_time = 7.5 / 24.0
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	var c := Data.CENTER
	city.camera.position = Iso.center(Vector2i(c, c))
	city.camera.zoom = Vector2(0.7, 0.7)
	await get_tree().create_timer(3.0).timeout
	var kinds := {}
	for n in get_tree().root.find_children("*", "", true, false):
		var k: String = n.get_class()
		if n is CPUParticles2D:
			k += " emitting" if n.emitting else " idle"
		kinds[k] = kinds.get(k, 0) + 1
	var ks := kinds.keys()
	ks.sort_custom(func(a, b): return kinds[a] > kinds[b])
	for k in ks.slice(0, 12):
		print("perf nodes %-28s %d" % [k, kinds[k]])
	await _measure("all", 8000)
	var L: Life = city.life
	# break the life step down: same order as Life._process, timed part by part
	L.set_process(false)
	var acc := {}
	var frames := 0
	var t_end := Time.get_ticks_msec() + 6000
	while Time.get_ticks_msec() < t_end:
		await get_tree().process_frame
		frames += 1
		var d := get_process_delta_time()
		L._hour = Game.day_time * 24.0
		var t := Time.get_ticks_usec()
		if L._dirty:
			L._rebuild_persons()
		t = _acc(acc, "rebuild_persons", t)
		L._rebuild_bins()
		t = _acc(acc, "bins", t)
		L._tick -= d
		if L._tick <= 0.0:
			L._tick = 0.5
			L._tick_persons(0.5)
			t = _acc(acc, "tick_persons", t)
			L._update_lights()
			t = _acc(acc, "lights", t)
		for car in L.cars:
			if is_instance_valid(car) and car.moving():
				car.drive(d)
		t = _acc(acc, "cars", t)
		for w in L.walkers:
			if is_instance_valid(w):
				w.step(d)
		t = _acc(acc, "walkers", t)
		L._ambient_t -= d
		if L._ambient_t <= 0.0:
			L._ambient_t = 2.0
			L._ambient()
		t = _acc(acc, "ambient", t)
		L._social_t -= d
		if L._social_t <= 0.0:
			L._social_t = 1.3
			L._social()
		t = _acc(acc, "social", t)
		L.cars = L.cars.filter(func(x): return is_instance_valid(x))
		L.walkers = L.walkers.filter(func(w): return is_instance_valid(w) and not w.done)
		t = _acc(acc, "filter", t)
	for k in acc:
		print("perf life %-16s %.3f ms/frame" % [k, acc[k] / 1000.0 / frames])
	var whole := 0
	frames = 0
	t_end = Time.get_ticks_msec() + 4000
	while Time.get_ticks_msec() < t_end:
		await get_tree().process_frame
		frames += 1
		var t9 := Time.get_ticks_usec()
		L._process(get_process_delta_time())
		whole += Time.get_ticks_usec() - t9
	print("perf life whole _process %.3f ms/frame" % (whole / 1000.0 / frames))
	L.set_process(true)
	var parts: Array = get_tree().root.find_children("*", "CPUParticles2D", true, false)
	for pp in parts:
		pp.emitting = false
	await _measure("no particles", 4000)
	for pp in parts:
		pp.emitting = true
	await _measure("again all", 4000)
	Game.process_mode = Node.PROCESS_MODE_DISABLED
	await _measure("game disabled", 4000)
	Game.process_mode = Node.PROCESS_MODE_INHERIT
	Events.process_mode = Node.PROCESS_MODE_DISABLED
	await _measure("events disabled", 4000)
	Events.process_mode = Node.PROCESS_MODE_INHERIT
	city.process_mode = Node.PROCESS_MODE_DISABLED
	await _measure("city tree disabled", 4000)
	city.process_mode = Node.PROCESS_MODE_INHERIT
	city.set_process(false)
	await _measure("city self off", 3000)
	city.set_process(true)
	for ch in city.get_children():
		var cnt: int = ch.find_children("*", "", true, false).size()
		if cnt < 20 and not ch.has_method("_process") and not (ch is Camera2D) and ch != city.ground:
			continue
		ch.process_mode = Node.PROCESS_MODE_DISABLED
		await _measure("off: %s (%d)" % [ch.name, cnt], 3000)
		ch.process_mode = Node.PROCESS_MODE_INHERIT
	city.world.process_mode = Node.PROCESS_MODE_DISABLED
	await _measure("world disabled", 4000)
	city.world.process_mode = Node.PROCESS_MODE_INHERIT
	city.hud.process_mode = Node.PROCESS_MODE_DISABLED
	await _measure("hud disabled", 4000)
	city.hud.process_mode = Node.PROCESS_MODE_INHERIT
	for k in ["backdrop", "weather", "scenery"]:
		city.get(k).process_mode = Node.PROCESS_MODE_DISABLED
	await _measure("bg/weather/scenery off", 4000)
	for k in ["backdrop", "weather", "scenery"]:
		city.get(k).process_mode = Node.PROCESS_MODE_INHERIT
	await _measure("again all", 4000)
	var tt := Time.get_ticks_usec()
	for i in 20:
		city._update_daylight()
	print("perf city daylight %.3fms" % ((Time.get_ticks_usec() - tt) / 20000.0))
	tt = Time.get_ticks_usec()
	city._cull()
	print("perf city cull %.3fms" % ((Time.get_ticks_usec() - tt) / 1000.0))
	tt = Time.get_ticks_usec()
	var nv := 0
	for v in city.views.values():
		if v.is_processing():
			v._process(0.016)
			nv += 1
	print("perf views process %.3fms (%d active)" % [(Time.get_ticks_usec() - tt) / 1000.0, nv])
	tt = Time.get_ticks_usec()
	for i in 10:
		city.backdrop._process(0.016)
	print("perf backdrop %.3fms" % ((Time.get_ticks_usec() - tt) / 10000.0))
	tt = Time.get_ticks_usec()
	for i in 10:
		city.weather._process(0.016)
	print("perf weather %.3fms" % ((Time.get_ticks_usec() - tt) / 10000.0))
	tt = Time.get_ticks_usec()
	for i in 10:
		city.hud._process(0.016)
	print("perf hud %.3fms" % ((Time.get_ticks_usec() - tt) / 10000.0))
	tt = Time.get_ticks_usec()
	var nl := 0
	for n in city.find_children("*", "", true, false):
		if n.is_processing() and n.has_method("_process") and not (n is BuildingView) and n != city and n != city.life:
			nl += 1
	print("perf other processing nodes %d" % nl)
	var t1 := Time.get_ticks_usec()
	Game.simulate(0.016)
	var t2 := Time.get_ticks_usec()
	Game.save_game()
	var t3 := Time.get_ticks_usec()
	var dct := Game.to_dict()
	var t4 := Time.get_ticks_usec()
	JSON.stringify(dct)
	var t5 := Time.get_ticks_usec()
	print("perf simulate %.2fms save %.2fms (to_dict %.2fms, stringify %.2fms)" % [(t2 - t1) / 1000.0, (t3 - t2) / 1000.0, (t4 - t3) / 1000.0, (t5 - t4) / 1000.0])
	print("perf: persons=%d walkers=%d cars=%d views=%d nodes=%d" % [L.persons.size(), L.walkers.size(), L.cars.size(),
		city.views.size(), Performance.get_monitor(Performance.OBJECT_NODE_COUNT)])
	get_tree().quit()


func _acc(acc: Dictionary, key: String, t: int) -> int:
	var now := Time.get_ticks_usec()
	acc[key] = acc.get(key, 0) + now - t
	return now


## Wall time per frame (TIME_PROCESS is only the worst frame of the last second).
func _measure(label: String, ms: int) -> void:
	var samples: Array[float] = []
	var t0 := Time.get_ticks_msec()
	var last := Time.get_ticks_usec()
	while Time.get_ticks_msec() - t0 < ms:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		samples.append((now - last) / 1000.0)
		last = now
	samples.sort()
	print("perf %-22s frames=%d median=%.2fms p95=%.2fms" % [label, samples.size(), samples[samples.size() / 2], samples[int(samples.size() * 0.95)]])
