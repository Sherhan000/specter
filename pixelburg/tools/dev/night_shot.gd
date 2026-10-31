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
	for i in 12:
		var uid := Game._add_building(["house_small", "house_brick", "cottage"][i % 3], c - 8 + i * 2, c - 3, true, 2)
		Game.buildings[uid].occ = 10
	for id in ["hospital", "school", "it_run", "farm"]:
		Game._add_building(id, c + randi_range(-6, 6), c + 4, true, 2)
	Game.recalc()
	for d in 90:
		Game.day += 1
		Game._move_population()
		Game.recalc()
		Game.cz.on_day()
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	await _wait(2.0)
	var pn = city.hud.panels
	pn.cit.analytics()
	await _wait(0.6)
	await _shot("n3_analytics")
	pn.cit.prices()
	await _wait(0.5)
	await _shot("n3_prices")
	pn.cit.list()
	await _wait(0.5)
	await _shot("n3_list")
	pn.cit.card(int(Game.cz.list[3].id))
	await _wait(0.5)
	await _shot("n3_card")
	get_tree().quit()


func _wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + name + ".png")
