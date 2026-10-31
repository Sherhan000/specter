class_name Assets
extends RefCounted
## Cached textures, sprite metadata and shared materials.

static var _tex := {}
static var _img := {}
static var _meta := {}
static var _nature := {}
static var _units := {}
static var _icons := {}
static var _icon_names: Array = []
static var _atlas := {}
static var _faces := {}
static var world_mat: ShaderMaterial
static var sway_mat: ShaderMaterial
static var glow_mat: CanvasItemMaterial
static var city_rooms_mat: ShaderMaterial
static var rooms_mat: ShaderMaterial
static var shadow_mat: ShaderMaterial
static var night_mat: ShaderMaterial


static func tex(path: String) -> Texture2D:
	if not _tex.has(path):
		_tex[path] = load("res://assets/%s.png" % path) if ResourceLoader.exists("res://assets/%s.png" % path) else null
	return _tex[path]


static func image(path: String) -> Image:
	if not _img.has(path):
		var t := tex(path)
		_img[path] = t.get_image() if t else Image.create(1, 1, false, Image.FORMAT_RGBA8)
		if _img[path].is_compressed():
			_img[path].decompress()
	return _img[path]


static func _json(path: String) -> Variant:
	return JSON.parse_string(FileAccess.get_file_as_string(path))


## Sprite metadata of a building: "o" body offset from the anchor (bottom vertex of the
## footprint), optional "base", "sh", "glow", "rooms" layers, "points", "door_g", "entry_g".
static func meta(name: String) -> Dictionary:
	if _meta.is_empty():
		_meta = _json("res://assets/buildings/meta.json")
	return _meta.get(name, {})


static func nature(name: String) -> Dictionary:
	if _nature.is_empty():
		_nature = _json("res://assets/nature/meta.json")
	return _nature.get(name, {})


static func units() -> Dictionary:
	if _units.is_empty():
		_units = _json("res://assets/units/meta.json")
	return _units


## Region of one vehicle frame: heading 0..15, layer 0 base, 1 paint, 2 lights, 3/4 siren.
static func car_frame(kind: String, heading: int, layer: int) -> AtlasTexture:
	var key := "car_%s_%d_%d" % [kind, heading, layer]
	if not _icons.has(key):
		var m: Dictionary = units().cars[kind]
		var at := AtlasTexture.new()
		at.atlas = tex("units/car_" + kind)
		at.region = Rect2(heading * m.cell[0], layer * m.cell[1], m.cell[0], m.cell[1])
		_icons[key] = at
	return _icons[key]


## Icon from the generated sheets: size 16, 32 or 64.
static func icon_px(name: String, size: int) -> Texture2D:
	var key := "%s_%d" % [name, size]
	if not _icons.has(key):
		var ai := tex("ui/icons/" + name)
		if ai:
			_icons[key] = ai
		else:
			if _icon_names.is_empty():
				_icon_names = _json("res://assets/ui/icons.json")
			var alias := {"rotate": "move", "home": "pop", "factory": "jobs", "hospital": "heart", "school": "mission",
				"remove": "demolish"}
			var nm: String = alias.get(name, name)
			var at := AtlasTexture.new()
			at.atlas = tex("ui/icons_%d" % size)
			at.region = Rect2(maxi(0, _icon_names.find(nm)) * size, 0, size, size)
			_icons[key] = at
	return _icons[key]


## Interface icon from the 128 px atlas (or a hand-made one in ui/icons/), for any display size.
static func ui_icon(name: String) -> Texture2D:
	var key := "ui_" + name
	if not _icons.has(key):
		var ai := tex("ui/icons/" + name)
		if ai:
			_icons[key] = ai
		else:
			if _atlas.is_empty():
				_atlas = _json("res://assets/ui/icons_atlas.json")
			# icons of the newest sheet fall back to an older one until the hand-made picture is added
			var alias := {"home": "pop", "factory": "jobs", "hospital": "heart", "school": "mission", "remove": "demolish",
				"news": "star", "exit": "door", "river": "rain", "wall": "build", "street": "road", "bus": "road", "metro": "road",
				"hotel": "home", "bike": "speed", "sport": "trophy", "power": "storm", "water": "rain", "tv": "info",
				"newspaper": "mail", "plane": "globe", "eye": "info", "tile": "land"}
			var nm: String = alias.get(name, name)
			var i := maxi(0, (_atlas.names as Array).find(nm))
			var cell: int = _atlas.cell
			var at := AtlasTexture.new()
			at.atlas = tex("ui/icons_128")
			at.region = Rect2((i % int(_atlas.cols)) * cell, (i / int(_atlas.cols)) * cell, cell, cell)
			_icons[key] = at
	return _icons[key]


static func icon(name: String, big := false) -> Texture2D:
	return icon_px(name, 32 if big else 16)


## Half-figure of a character (for dialogues).
static func portrait(who: String, expr: String) -> Texture2D:
	var t := tex("portraits/%s_%s" % [who, expr])
	return t if t else tex("portraits/%s_smile" % who)


## Head and shoulders of a character, for small avatars.
static func face(who: String, expr: String) -> Texture2D:
	var key := "face_%s_%s" % [who, expr]
	if not _icons.has(key):
		if _faces.is_empty():
			_faces = _json("res://assets/portraits/faces.json")
		var name := "%s_%s" % [who, expr] if _faces.has("%s_%s" % [who, expr]) else "%s_smile" % who
		var r: Array = _faces.get(name, [0, 0, 448, 448])
		var at := AtlasTexture.new()
		at.atlas = tex("portraits/" + name)
		at.region = Rect2(r[0], r[1], r[2], r[3])
		_icons[key] = at
	return _icons[key]


## Sprite name of a building at a level facing a side (0 +y, 1 +x, 2 -y, 3 -x).
static func building_sprite(id: String, lvl: int, rot := 0) -> String:
	return "%s_%d_%d" % [id, lvl, rot]


static func init_materials() -> void:
	if world_mat:
		return
	var sh: Shader = load("res://shaders/world.gdshader")
	world_mat = ShaderMaterial.new()
	world_mat.shader = sh
	sway_mat = ShaderMaterial.new()
	sway_mat.shader = sh
	sway_mat.set_shader_parameter("sway", 1.2)
	for m in [world_mat, sway_mat]:
		m.set_shader_parameter("horizon_y", Data.HORIZON * Iso.HY)
	glow_mat = CanvasItemMaterial.new()
	glow_mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	rooms_mat = ShaderMaterial.new()
	rooms_mat.shader = load("res://shaders/rooms.gdshader")
	city_rooms_mat = ShaderMaterial.new()
	city_rooms_mat.shader = rooms_mat.shader
	shadow_mat = ShaderMaterial.new()
	shadow_mat.shader = load("res://shaders/shadow.gdshader")
	night_mat = ShaderMaterial.new()
	night_mat.shader = load("res://shaders/night_glow.gdshader")


## night drives shadows and the far villages; lit is the electric light of the city (needs current).
static func set_daylight(tint: Color, night: float, lit := -1.0) -> void:
	if lit < 0.0:
		lit = night
	for m in [world_mat, sway_mat]:
		m.set_shader_parameter("tint", Vector3(tint.r, tint.g, tint.b))
	rooms_mat.set_shader_parameter("night", night)
	city_rooms_mat.set_shader_parameter("night", lit)
	night_mat.set_shader_parameter("night", lit)
	shadow_mat.set_shader_parameter("strength", clampf(1.0 - night * 1.4, 0.0, 1.0))


static func set_haze(c: Color) -> void:
	for m in [world_mat, sway_mat]:
		m.set_shader_parameter("haze", Vector3(c.r, c.g, c.b))


static func set_season(snow: float, autumn: float, wet: float) -> void:
	for m in [world_mat, sway_mat]:
		m.set_shader_parameter("snow", snow)
		m.set_shader_parameter("autumn", autumn)
		m.set_shader_parameter("wet", wet)
