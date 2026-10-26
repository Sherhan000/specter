extends Node
## Dev only: starts a fresh city and saves screenshots from several places. SHOT_DIR = output.

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
	Game.day_time = 0.4
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	await _wait(2.0)
	var c := Data.CENTER
	var shots := [["v1_start", Vector2i(c + 1, c), 0.62], ["v2_close", Vector2i(c, c), 1.2], ["v3_far", Vector2i(c, c), 0.3],
		["v4_top", Vector2i(Data.LAND0 + 4, Data.LAND0 + 4), 0.45], ["v5_left", Vector2i(Data.LAND0, Data.LAND1 - 6), 0.4],
		["v7_horizon", Vector2i(70, 72), 0.45], ["v8_hz_west", Vector2i(40, 105), 0.5], ["v9_hz_far", Vector2i(70, 72), 0.3]]
	for s in shots:
		city.camera.position = Iso.center(s[1])
		city.camera.zoom = Vector2(s[2], s[2])
		city._clamp_camera()
		await _wait(1.5)
		await _shot(s[0])
	Game.day_time = 0.92
	city.camera.position = Iso.center(Vector2i(c + 1, c))
	city.camera.zoom = Vector2(0.62, 0.62)
	await _wait(3.0)
	await _shot("v6_night")
	city.camera.position = Iso.center(Vector2i(70, 72))
	city.camera.zoom = Vector2(0.45, 0.45)
	city._clamp_camera()
	await _wait(2.0)
	await _shot("v10_hz_night")
	get_tree().quit()


func _wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + name + ".png")
