class_name Ground
extends Node2D
## The valley floor: one big polygon drawn by shaders/ground.gdshader, fed with small data
## textures: terrain weights (static), road tiles and zones / ownership (rebuilt on change).

const ROAD_IDS := {"dirt": 1, "asphalt": 2, "stone": 3, "highway": 4, "country": 5, "town": 6, "boulevard": 7,
	"avenue": 8, "brick": 9, "bus_lane": 10, "bike": 11}
## paving on the grass (Game.paves), drawn by the same shader after the roads
const PAVE_IDS := {"slabs": 12, "terracotta": 13, "mosaic": 14, "path": 15}
const STREETS := ["asphalt", "stone", "town", "boulevard", "avenue", "brick", "bus_lane", "bike"]
## arm bits: north (-y) 1, east (+x) 2, south (+y) 4, west (-x) 8
const ARM_DIRS := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]

var mat: ShaderMaterial
var poly: Polygon2D
var terrain_img: Image
var road_img: Image
var road_tex: ImageTexture
var info_img: Image
var info_tex: ImageTexture
var extra_roads := {}    ## decorative streets of the villages: tile -> "town"
var crosswalks := {}     ## tile -> arm bits with a zebra (used by pedestrians)
var midblock := {}       ## straight tiles with a crossing in the middle
var parking := {}        ## tile -> axis "x" | "y" for street parking


func _ready() -> void:
	mat = ShaderMaterial.new()
	mat.shader = load("res://shaders/ground.gdshader")
	var layers: Array[Image] = []
	for k in ["grass", "forest", "soil", "dirt", "asphalt", "paving", "cobble"]:
		var img: Image = (load("res://assets/ground/%s.png" % k) as Texture2D).get_image()
		if img.is_compressed():
			img.decompress()
		img.clear_mipmaps()
		img.convert(Image.FORMAT_RGBA8)
		img.resize(256, 256)
		img.generate_mipmaps()
		layers.append(img)
	var arr := Texture2DArray.new()
	arr.create_from_images(layers)
	mat.set_shader_parameter("ground_tex", arr)
	mat.set_shader_parameter("noise_tex", load("res://assets/ground/noise.png"))
	var tt: Texture2D = load("res://assets/world/terrain.png")
	terrain_img = tt.get_image()
	mat.set_shader_parameter("terrain_tex", tt)
	mat.set_shader_parameter("map_size", float(Data.MAP))
	mat.set_shader_parameter("horizon", float(Data.HORIZON))
	mat.set_shader_parameter("land0", Vector2(Data.LAND0, Data.LAND0))
	mat.set_shader_parameter("land_size", float(Data.PLOT * Data.PLOTS))
	mat.set_shader_parameter("plot", float(Data.PLOT))
	road_img = Image.create(Data.MAP, Data.MAP, false, Image.FORMAT_RGBA8)
	road_tex = ImageTexture.create_from_image(road_img)
	info_img = Image.create(Data.MAP, Data.MAP, false, Image.FORMAT_RGBA8)
	info_tex = ImageTexture.create_from_image(info_img)
	mat.set_shader_parameter("road_tex", road_tex)
	mat.set_shader_parameter("info_tex", info_tex)
	poly = Polygon2D.new()
	var top := Data.HORIZON * Iso.HY - 200.0
	var w := Data.MAP * Iso.HX * 2.0 + 30000.0
	var bottom := Data.MAP * 2.0 * Iso.HY + 20000.0
	poly.polygon = PackedVector2Array([Vector2(-w, top), Vector2(w, top), Vector2(w, bottom), Vector2(-w, bottom)])
	poly.material = mat
	add_child(poly)


## Terrain weights at a tile: x forest, y farmland, z water, w dry meadow (0..1).
func terrain_at(c: Vector2i) -> Color:
	if c.x < 0 or c.y < 0 or c.x >= Data.MAP or c.y >= Data.MAP:
		return Color(0.6, 0, 0, 0)
	return terrain_img.get_pixel(c.x, c.y)


func _arms(net: Dictionary, c: Vector2i) -> int:
	var t: String = net[c]
	var bits := 0
	for k in 4:
		var o: Vector2i = c + ARM_DIRS[k]
		if not net.has(o):
			continue
		var ot: String = net[o]
		# the highway only joins its own spur, nothing runs onto it from the side
		if (t == "highway") != (ot == "highway") and not (t == "country" or ot == "country"):
			continue
		bits |= 1 << k
	return bits


## Rebuild the road texture from every drivable tile.
func update_roads(net: Dictionary) -> void:
	var all := net.duplicate()
	for c in extra_roads:
		if not all.has(c):
			all[c] = extra_roads[c]
	road_img.fill(Color(0, 0, 0, 0))
	crosswalks.clear()
	midblock.clear()
	parking.clear()
	var arms := {}
	for c in all:
		arms[c] = _arms(all, c)
	# street parking along straight stretches, a mid-block crossing on long ones
	for c in all:
		var t: String = all[c]
		var a: int = arms[c]
		if not t in STREETS or t in ["boulevard", "avenue", "bus_lane", "bike"] or (a != 10 and a != 5):
			continue
		parking[c] = "x" if a == 10 else "y"
		var step := Vector2i(1, 0) if a == 10 else Vector2i(0, 1)
		var along: int = c.x if a == 10 else c.y
		if posmod(along, 6) == 3:
			var quiet := true
			for k in range(-2, 3):
				var o: Vector2i = c + step * k
				if not all.has(o) or arms.get(o, 0) != a:
					quiet = false
			if quiet:
				midblock[c] = true
	for c in all:
		var t: String = all[c]
		var a: int = arms[c]
		var g := a
		var b := 0
		if parking.has(c):
			g |= 16
			var axis: String = parking[c]
			var neg: Vector2i = c + (Vector2i(-1, 0) if axis == "x" else Vector2i(0, -1))
			var pos: Vector2i = c + (Vector2i(1, 0) if axis == "x" else Vector2i(0, 1))
			if parking.get(neg, "") != axis or midblock.has(neg):
				g |= 32
			if parking.get(pos, "") != axis or midblock.has(pos):
				g |= 64
		if t in STREETS and not (a == 10 or a == 5):
			var n := 0
			for k in 4:
				if a & (1 << k):
					n += 1
			if n >= 2:
				for k in 4:
					if a & (1 << k) and all.get(c + ARM_DIRS[k], "") in STREETS:
						b |= 1 << k
				if b != 0:
					crosswalks[c] = b
		if midblock.has(c):
			b |= 32
		if Game.lights.has(c):
			b |= 16
		road_img.set_pixel(c.x, c.y, Color8(ROAD_IDS[t], g, b, 128 + Game.water_kind(c) if Game.water.has(c) else 255))
	# paving: arms join a tile to the same paving next to it; a footpath also runs onto roads, other paving and buildings
	for c in Game.paves:
		if all.has(c) or Game.water.has(c):
			continue
		var t: String = Game.paves[c]
		var bits := 0
		for k in 4:
			var o: Vector2i = c + ARM_DIRS[k]
			var ot: String = Game.paves.get(o, "")
			if ot == t or (t == "path" and (ot != "" or all.has(o) or Game.occ.has(o))) or (t != "path" and all.has(o)):
				bits |= 1 << k
		road_img.set_pixel(c.x, c.y, Color8(PAVE_IDS[t], bits, 0, 255))
	# water dug by the player: alpha 129 river, 130 sea, 131 ocean
	for c in Game.water:
		if not all.has(c):
			road_img.set_pixel(c.x, c.y, Color8(0, 0, 0, 128 + Game.water_kind(c)))
	road_tex.update(road_img)


## Zones, ownership and plots for sale, shown while building.
func update_info() -> void:
	info_img.fill(Color(0, 0, 0, 0))
	var zid := {"city": 1, "farm": 2, "industry": 3, "leisure": 4}
	for y in range(Data.LAND0, Data.LAND1):
		for x in range(Data.LAND0, Data.LAND1):
			var c := Vector2i(x, y)
			var p := Data.plot_of(c)
			info_img.set_pixel(x, y, Color8(zid[Data.zone_of_plot(p)], 255 if Game.plots.has(p) else 0,
				255 if Game.plot_buyable(p) else 0, 255))
	for y in range(Data.LAND0, Data.LAND1):
		for x in range(Data.BEACH_X0, Data.LAND0):
			var seg := Data.beach_seg(Vector2i(x, y))
			info_img.set_pixel(x, y, Color8(4, 255 if Game.beach.has(seg) else 0, 255 if Game.beach_buyable(seg) else 0, 255))
	info_tex.update(info_img)


func set_overlay(v: float) -> void:
	var tw := create_tween()
	tw.tween_method(func(x): mat.set_shader_parameter("overlay", x), float(mat.get_shader_parameter("overlay") if mat.get_shader_parameter("overlay") != null else 0.0), v, 0.25)


func set_daylight(tint: Color, haze: Color) -> void:
	mat.set_shader_parameter("tint", Vector3(tint.r, tint.g, tint.b))
	mat.set_shader_parameter("haze", Vector3(haze.r, haze.g, haze.b))


func set_season(snow: float, autumn: float, wet: float) -> void:
	mat.set_shader_parameter("snow", snow)
	mat.set_shader_parameter("autumn", autumn)
	mat.set_shader_parameter("wet", wet)
