extends Node
## Dev only: screenshots of natural events and photo mode. SHOT_DIR = output.

var out := ""
var city


func _ready() -> void:
	out = OS.get_environment("SHOT_DIR") + "/"
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json"))
	Events.reset()
	Game.new_game()
	Game.profile = {"name": "Test", "age": 30, "gender": "m", "privacy": true, "intro": true}
	var c := Data.CENTER
	Game.tutorial = 99
	Game.ach.last = Game.real_day()
	Events.chapter = 9
	Events.flags = {"zoo_arc": true, "hall_arc": true, "election_done": true}
	Game.day_time = 0.4
	var p := [["nightclub", c + 1, c + 1], ["night_market", c + 4, c + 1], ["karaoke", c - 3, c + 1], ["plaza", c + 1, c + 4], ["fountain", c + 4, c + 4]]
	for q in p:
		Game._add_building(q[0], q[1], q[2], true, 2)
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	await _wait(2.0)
	Game.day = 6
	Game.day_time = 0.88
	city.camera.position = Iso.center(Vector2i(c + 2, c + 2))
	city.camera.zoom = Vector2(0.7, 0.7)
	await _wait(1.0)
	for i in 5:
		city.fireworks.burst(Iso.center(Vector2i(c + 2, c + 4)) + Vector2(randf_range(-120, 120), -randf_range(150, 250)))
	await _wait(0.8)
	await _shot("n2_night")
	Game.day_time = 0.4
	await _wait(1.0)
	await _shot("n2_day")
	get_tree().quit()


func _wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + name + ".png")
