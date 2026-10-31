extends Node
## Dev only: opens the main windows of the interface and saves screenshots. SHOT_DIR = output.

var out := ""
var city


func _ready() -> void:
	out = OS.get_environment("SHOT_DIR") + "/"
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json"))
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json.bak"))
	Events.reset()
	Game.new_game()
	Game.profile = {"name": "Test", "age": 30, "gender": "m", "privacy": true, "intro": OS.get_environment("UI_INTRO") == ""}
	Game.tutorial = int(OS.get_environment("UI_TUT")) if OS.get_environment("UI_TUT") != "" else 99
	Events.chapter = 9
	Game.day_time = 0.4
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	var hud = city.hud
	await _wait(2.5)
	if not Game.profile.intro:
		await _wait(4.0)
		await _shot("i0_title")
		var intro: Node = hud.get_children().filter(func(c): return c is Intro)[0]
		intro._profile()
		await _wait(0.5)
		await _shot("i1_profile")
		intro._name_edit.text = "Test"
		intro._gender = "m"
		intro._privacy()
		await _wait(0.5)
		await _shot("i2_privacy")
		get_tree().quit()
		return
	if Game.tutorial < 99:
		await _shot("u0_tutorial")
		for i in 4:
			hud.dialog.skip()
			await _wait(0.6)
		await _shot("u0_tutorial_hint")
		get_tree().quit()
		return
	await _wait(1.0)
	hud.close_modal()
	for hd in [[1, "navruz"], [7, "cityday"], [11, "halloween"], [15, "newyear"]]:
		Game.day = hd[0]
		Game.day_time = 0.85 if hd[1] == "cityday" else 0.45
		city.holiday_view.refresh()
		await _wait(0.8)
		await _shot("h_" + hd[1])
	hud.panels.holiday()
	await _wait(0.5)
	await _shot("h_panel")
	hud.close_modal()
	Game.day = 1
	Game.day_time = 0.4
	city.holiday_view.refresh()
	hud.toggle_build_menu()
	await _wait(0.6)
	await _shot("u1_build")
	hud.toggle_build_menu()
	var uid := -1
	for u in Game.buildings:
		if Game.buildings[u].id == "house_small":
			uid = u
			break
	hud.show_info(uid)
	await _wait(0.6)
	await _shot("u2_info")
	hud.panels.finance()
	await _wait(0.6)
	await _shot("u3_finance")
	hud.close_modal()
	hud.panels.settings()
	await _wait(0.6)
	await _shot("u4_settings")
	hud.close_modal()
	hud.panels.animals()
	await _wait(0.6)
	await _shot("u8_animals")
	hud.close_modal()
	hud.panels.land_info()
	await _wait(0.6)
	hud.close_modal()
	hud.panels.missions()
	await _wait(0.6)
	hud.close_modal()
	hud.panels.city_info()
	await _wait(0.6)
	hud.close_modal()
	hud.panels.finance()
	await _wait(0.3)
	hud.close_modal()
	hud.panels.achievements()
	await _wait(0.6)
	await _shot("u9_ach")
	hud.close_modal()
	Game.ach.pending = true
	hud.panels.daily()
	await _wait(0.6)
	await _shot("u10_daily")
	hud.close_modal()
	hud.panels.inbox()
	await _wait(0.6)
	await _shot("u5_inbox")
	hud.close_modal()
	hud.dialog.play([{"who": "boris", "expr": "think", "text": ["Хм… А если построить здесь парк? Жителям нужен отдых.", "Hmm… What if we built a park here?"]},
		{"who": "alina", "expr": "talk", "text": ["Отличная идея! Но сначала проверим бюджет.", "Great idea! But let's check the budget first."],
		"choices": [[["Согласен", "Agreed"], ""], [["Позже", "Later"], ""]]}])
	await _wait(2.0)
	await _shot("u6_dialog")
	hud.dialog.skip()
	await _wait(2.0)
	await _shot("u7_dialog2")
	get_tree().quit()


func _wait(t: float) -> void:
	await get_tree().create_timer(t).timeout


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out + name + ".png")
