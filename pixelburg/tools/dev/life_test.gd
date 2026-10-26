extends Node
## Dev only: watches the morning rush in the starting town and prints what the residents do.

var out := ""
var city


func _ready() -> void:
	out = OS.get_environment("SHOT_DIR") + "/"
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json"))
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json.bak"))
	Events.reset()
	Game.new_game()
	Game.profile = {"name": "Test", "age": 30, "gender": "m", "privacy": true, "intro": true}
	Game.tutorial = 99
	Events.chapter = 9
	Events.flags = {"zoo_arc": true, "hall_arc": true, "election_done": true}
	Game.day_time = float(OS.get_environment("LT_START") if OS.get_environment("LT_START") != "" else "6.4") / 24.0
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	Engine.time_scale = float(OS.get_environment("LT_SCALE") if OS.get_environment("LT_SCALE") != "" else "4")
	var c := Data.CENTER
	city.camera.position = Iso.center(Vector2i(c, c))
	city.camera.zoom = Vector2(0.9, 0.9)
	for i in 16:
		await get_tree().create_timer(5.0 * Engine.time_scale / 4.0).timeout
		var L: Life = city.life
		var moving := L.cars.filter(func(x): return is_instance_valid(x) and x.moving()).size()
		var parked := L.cars.filter(func(x): return is_instance_valid(x) and x.state == "parked").size()
		var waiting := L.walkers.filter(func(w): return is_instance_valid(w) and w._wait > 0.5).size()
		var at_home := L.persons.filter(func(p): return p.where == p.home).size()
		var at_work := L.persons.filter(func(p): return p.work > 0 and p.where == p.work).size()
		print("t=%s persons=%d home=%d work=%d walkers=%d waiting=%d cars moving=%d parked=%d reserved=%d fps=%d" % [
			Game.clock_text(), L.persons.size(), at_home, at_work, L.walkers.size(), waiting, moving, parked, L.reserve.size(),
			Engine.get_frames_per_second()])
		if i % 4 == 3:
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(out + "life_%02d.png" % i)
	get_tree().quit()
