extends Node2D
## Dev only: renders the ground shader with a sample street layout. SHOT_DIR = output folder,
## SHOT_ROADS = optional swaps of the sample road types, e.g. "asphalt=concrete,stone=red,dirt=gravel".

var cam: Camera2D
var ground: Ground


func _ready() -> void:
	var out := OS.get_environment("SHOT_DIR") + "/"
	ground = Ground.new()
	add_child(ground)
	var net: Dictionary = Data.regional_roads()
	var c := Data.CENTER
	for i in range(c - 8, c + 9):
		net[Vector2i(i, c)] = "asphalt"
	for i in range(c - 6, c + 7):
		net[Vector2i(c, i)] = "asphalt"
	for i in range(c - 8, c + 1):
		net[Vector2i(i, c - 6)] = "stone"
	for i in range(c + 1, c + 5):
		net[Vector2i(c + 4, i)] = "asphalt"
	for i in range(c + 4, c + 9):
		net[Vector2i(i, c + 4)] = "asphalt"
	for i in range(c - 8, c):
		net[Vector2i(i, c + 5)] = "dirt"
	for i in range(c + 1, c + 5):
		net[Vector2i(c - 8, i)] = "dirt"
	net[Vector2i(c - 8, c + 5)] = "dirt"
	for i in range(Data.LAND1 - 6, Data.LAND1):
		net[Vector2i(c, i)] = "asphalt"
	for sw in OS.get_environment("SHOT_ROADS").split(",", false):
		var ab: PackedStringArray = sw.split("=")
		for k in net:
			if net[k] == ab[0] and k.y < Data.HIGHWAY_Y - 2:
				net[k] = ab[1]
	ground.update_roads(net)
	ground.update_info()
	cam = Camera2D.new()
	add_child(cam)
	var shots := [["g_center", Vector2i(c, c), 1.0], ["g_close", Vector2i(c, c), 2.0], ["g_far", Vector2i(c, c), 0.35],
		["g_corner", Vector2i(c + 4, c + 4), 1.2], ["g_dirt", Vector2i(c - 6, c + 4), 1.0],
		["g_highway", Vector2i(c, Data.HIGHWAY_Y - 1), 0.8], ["g_horizon", Vector2i(Data.LAND0 + 2, Data.LAND0 + 2), 0.35],
		["g_overlay", Vector2i(c, c), 0.35]]
	for s in shots:
		cam.position = Iso.center(s[1])
		cam.zoom = Vector2(s[2], s[2])
		if s[0] == "g_overlay":
			ground.mat.set_shader_parameter("overlay", 1.0)
		await get_tree().create_timer(0.3).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(out + s[0] + ".png")
	get_tree().quit()
