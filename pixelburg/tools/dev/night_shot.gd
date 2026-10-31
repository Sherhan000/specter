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
	var ids := ["tower_twin", "tower_gold", "tower_sail", "tower_ring", "tower_wind", "tower_crown"]
	for i in ids.size():
		Game._add_building(ids[i], c - 8 + (i % 3) * 4, c + 2 + (i / 3) * 4, true, 2)
	Game.recalc()
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	await _wait(2.0)
	city.camera.position = Iso.center(Vector2i(c - 2, c + 4))
	city.camera.zoom = Vector2(0.45, 0.45)
	await _wait(1.0)
	await _shot("n6_towers")
	Game.day_time = 0.88
	await _wait(1.0)
	await _shot("n6_towers_night")
	get_tree().quit()


func _wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + name + ".png")
