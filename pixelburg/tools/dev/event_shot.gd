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
	Game.tutorial = 99
	Events.chapter = 9
	Events.flags = {"zoo_arc": true, "hall_arc": true, "election_done": true}
	Game.day_time = 0.4
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	await _wait(2.0)
	var c := Data.CENTER
	city.camera.position = Iso.center(Vector2i(c + 1, c))
	city.camera.zoom = Vector2(0.9, 0.9)
	Game.start_disaster("quake")
	await _wait(4.0)
	await _shot("e1_quake")
	Game.disaster = Game._empty_disaster()
	Game.season = "winter"
	Game.start_disaster("blizzard")
	await _wait(2.0)
	await _shot("e2_blizzard")
	Game.disaster = Game._empty_disaster()
	city.photo.enter()
	city.photo.set_filter("sunset")
	await _wait(1.0)
	await _shot("e3_photo_ui")
	await city.photo.snap()
	print("PHOTO ", city.photo.last_path)
	get_tree().quit()


func _wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + name + ".png")
