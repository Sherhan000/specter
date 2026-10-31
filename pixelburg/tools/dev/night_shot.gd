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
	Game.level = 12
	Game.rep = 60.0
	Game.check_rank()
	await _wait(1.5)
	await _shot("n1_rank_hud")
	city.hud.panels.profile()
	await _wait(0.5)
	await _shot("n1_rank_profile")
	get_tree().quit()


func _wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + name + ".png")
