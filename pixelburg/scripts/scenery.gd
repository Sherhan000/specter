class_name Scenery
extends Node
## Everything that grows or stands outside the player's buildings: the trees left on the land,
## the forests, meadows and villages of the valley. Outside the land, sprites are made per
## chunk only when the camera comes near, so the whole valley costs little.

const CHUNK := 8
const CLUMPS := 20
const SINGLES := 8

var city: Node
var land_trees := {}        ## tile -> Sprite2D
var chunks := {}            ## Vector2i chunk -> Node2D
var villages: Array = []    ## [{id, tile, rot, lvl}]
var village_roads := {}     ## tile -> "town"
var _village_at := {}       ## chunk -> Array of village entries
var _t := 0.0


func _ready() -> void:
	_gen_villages()


static func _hash(c: Vector2i, salt := 0) -> int:
	var v := (c.x * 73856093) ^ (c.y * 19349663) ^ (salt * 83492791)
	v = (v ^ (v >> 13)) * 1274126177
	return absi(v ^ (v >> 16))


# ====================================================================== villages
func _gen_villages() -> void:
	var roads: Dictionary = Data.regional_roads()
	var lines := []   # [start tile, step, length]
	lines.append([Vector2i(Data.LAND0 - 1, Data.CENTER), Vector2i(-1, 0), Data.LAND0])
	lines.append([Vector2i(Data.CENTER, Data.LAND0 - 1), Vector2i(0, -1), Data.LAND0])
	lines.append([Vector2i(Data.LAND1, Data.CENTER), Vector2i(1, 0), Data.MAP - Data.LAND1])
	lines.append([Vector2i(Data.LAND1 + 30, Data.HIGHWAY_Y - 1), Vector2i(1, 0), 60])
	lines.append([Vector2i(Data.LAND0 - 30, Data.HIGHWAY_Y - 1), Vector2i(-1, 0), 50])
	var kinds := ["house_small", "cottage", "house_small", "bungalow", "cottage", "house_small"]
	for li in lines.size():
		var start: Vector2i = lines[li][0]
		var step: Vector2i = lines[li][1]
		var length: int = lines[li][2]
		var k := Data.FOREST + 6
		while k < length - 4:
			var c: Vector2i = start + step * k
			k += 18 + _hash(c, 3) % 10
			if c.x + c.y < Data.HORIZON + 6:
				continue
			var side := Vector2i(-step.y, step.x)
			if _hash(c, 5) % 2 == 0:
				side = -side
			# a side street with houses on both sides, and a few houses on the main road
			var street: Array[Vector2i] = []
			for j in range(1, 6 + _hash(c, 7) % 3):
				var t: Vector2i = c + side * j
				if not _free_for_village(t, roads):
					break
				street.append(t)
			if street.size() < 3:
				continue
			for t in street:
				village_roads[t] = "town"
			for j in street.size():
				var t: Vector2i = street[j]
				for sgn in [-1, 1]:
					var h: Vector2i = t + step * sgn
					if j < street.size() - 1 and _free_for_village(h, roads) and _hash(h, 11) % 5 != 0:
						_add_house(kinds[_hash(h, 13) % kinds.size()], h, -step * sgn, li)
			for off in [-3, -2, 2, 3]:
				var h: Vector2i = c + step * off + side
				if _free_for_village(h, roads) and _hash(h, 17) % 3 != 0:
					_add_house(kinds[_hash(h, 19) % kinds.size()], h, -side, li)


func _free_for_village(t: Vector2i, roads: Dictionary) -> bool:
	if t.x < 1 or t.y < 1 or t.x >= Data.MAP - 1 or t.y >= Data.MAP - 1 or roads.has(t) or village_roads.has(t):
		return false
	if t.x + t.y < Data.HORIZON + 3 or Data.region(t) != "country":
		return false
	var w: Color = city.ground.terrain_at(t) if city and city.ground else Color()
	return w.b < 0.2


func _add_house(id: String, t: Vector2i, face: Vector2i, salt: int) -> void:
	for v in villages:
		if v.tile == t:
			return
	var rot := 0
	match face:
		Vector2i(0, 1): rot = 0
		Vector2i(1, 0): rot = 1
		Vector2i(0, -1): rot = 2
		_: rot = 3
	var entry := {"id": id, "tile": t, "rot": rot, "lvl": 1 + _hash(t, salt) % 3}
	villages.append(entry)
	var ch := Vector2i(floori(float(t.x) / CHUNK), floori(float(t.y) / CHUNK))
	if not _village_at.has(ch):
		_village_at[ch] = []
	_village_at[ch].append(entry)


# ====================================================================== land trees
func rebuild_land_trees() -> void:
	for c in land_trees.keys():
		if Game.tree_at(c) == "":
			land_trees[c].queue_free()
			land_trees.erase(c)
	for c in Game.natural_trees:
		if land_trees.has(c):
			continue
		var kind := Game.tree_at(c)
		if kind == "":
			continue
		land_trees[c] = _tree_sprite(kind, Iso.center(c), city.world)


func _tree_sprite(name: String, pos: Vector2, parent: Node) -> Sprite2D:
	var m: Dictionary = Assets.nature(name)
	var s := Sprite2D.new()
	s.texture = Assets.tex("nature/" + name)
	s.centered = false
	s.position = pos
	s.offset = Vector2(m.o[0], m.o[1]) + Vector2(0, Iso.HY)
	s.material = Assets.sway_mat
	parent.add_child(s)
	return s


# ====================================================================== chunks
func update(view: Rect2) -> void:
	var r := view.grow(700.0)
	var corners := [Iso.to_grid(r.position), Iso.to_grid(r.end), Iso.to_grid(Vector2(r.position.x, r.end.y)), Iso.to_grid(Vector2(r.end.x, r.position.y))]
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for g in corners:
		lo = lo.min(g)
		hi = hi.max(g)
	var c0 := Vector2i(floori(lo.x / CHUNK), floori(lo.y / CHUNK))
	var c1 := Vector2i(floori(hi.x / CHUNK), floori(hi.y / CHUNK))
	var wanted := {}
	for cy in range(c0.y, c1.y + 1):
		for cx in range(c0.x, c1.x + 1):
			var ch := Vector2i(cx, cy)
			if (cx + cy + 2) * CHUNK < Data.HORIZON - 4:
				continue
			if not _chunk_rect(ch).intersects(r):
				continue
			wanted[ch] = true
			if not chunks.has(ch):
				chunks[ch] = _make_chunk(ch)
			chunks[ch].visible = true
	for ch in chunks.keys():
		if not wanted.has(ch):
			chunks[ch].visible = false
	# keep memory bounded: drop hidden chunks once there are many
	if chunks.size() > 140:
		for ch in chunks.keys():
			if not wanted.has(ch):
				chunks[ch].queue_free()
				chunks.erase(ch)
				if chunks.size() <= 100:
					break


func _chunk_rect(ch: Vector2i) -> Rect2:
	var x0 := ch.x * CHUNK
	var y0 := ch.y * CHUNK
	var left := Iso.vertex(x0, y0 + CHUNK).x
	var right := Iso.vertex(x0 + CHUNK, y0).x
	var top := Iso.vertex(x0, y0).y - 380.0
	var bottom := Iso.vertex(x0 + CHUNK, y0 + CHUNK).y + 40.0
	return Rect2(left, top, right - left, bottom - top)


func _make_chunk(ch: Vector2i) -> Node2D:
	var n := Node2D.new()
	n.y_sort_enabled = true
	city.world.add_child(n)
	for dy in CHUNK:
		for dx in CHUNK:
			var c := Vector2i(ch.x * CHUNK + dx, ch.y * CHUNK + dy)
			_decorate(c, n)
	for v in _village_at.get(ch, []):
		_village_house(v, n)
	return n


func _decorate(c: Vector2i, parent: Node2D) -> void:
	if c.x + c.y < Data.HORIZON + 1:
		return
	if Data.in_land(c):
		return
	if Game.net.has(c) or village_roads.has(c):
		return
	for v in _village_at.get(Vector2i(floori(float(c.x) / CHUNK), floori(float(c.y) / CHUNK)), []):
		if v.tile == c:
			return
	var h := _hash(c, 1)
	var w: Color = city.ground.terrain_at(c)
	# keep a verge along the regional roads
	var verge := false
	for d in Iso.DIRS:
		if Game.highway.has(c + d) or village_roads.has(c + d):
			verge = true
	var pos := Iso.center(c) + Iso.grid_vec(Vector2((h % 17) / 17.0 - 0.5, (h % 13) / 13.0 - 0.5) * 0.12)
	if w.b > 0.25:
		return
	if w.r > 0.55 and not verge:
		var north := c.x + c.y < Data.LAND0 * 2 + 4
		var v := h % CLUMPS
		if north and h % 3 == 0:
			v = 14 + h % 6          # more spruce towards the mountains
		_tree_sprite("clump_%d" % v, pos, parent)
	elif w.r > 0.38:
		if h % 2 == 0:
			_tree_sprite("tree_%d" % (h % SINGLES), pos, parent)
		elif h % 5 == 1:
			_tree_sprite("under_%d" % (h % 4), pos, parent)
	elif w.g > 0.5:
		if h % 41 == 0:
			_tree_sprite("tree_%d" % (h % SINGLES), pos, parent)
	else:
		if verge:
			if h % 23 == 0:
				_tree_sprite("under_%d" % (h % 2), pos, parent)
		elif h % 19 == 0:
			_tree_sprite("tree_%d" % (h % SINGLES), pos, parent)
		elif h % 29 == 0:
			_tree_sprite("under_%d" % (h % 4), pos, parent)


func _village_house(v: Dictionary, parent: Node2D) -> void:
	var name := Assets.building_sprite(v.id, v.lvl, v.rot)
	var m := Assets.meta(name)
	if m.is_empty():
		return
	var t: Vector2i = v.tile
	var node := Node2D.new()
	node.position = Iso.vertex(t.x + 0.5, t.y + 0.5)
	parent.add_child(node)
	var shift := Vector2(0, Iso.HY)
	var body := Sprite2D.new()
	body.texture = Assets.tex("buildings/" + name)
	body.centered = false
	body.offset = Vector2(m.o[0], m.o[1]) + shift
	body.material = Assets.world_mat
	node.add_child(body)
	var anchor := node.position + shift
	if m.has("base"):
		var b := Sprite2D.new()
		b.texture = Assets.tex("buildings/%s_base" % name)
		b.centered = false
		b.position = anchor + Vector2(m.base[0], m.base[1])
		b.material = Assets.world_mat
		city.decals.add_child(b)
		node.tree_exiting.connect(b.queue_free)
	if m.has("sh"):
		var s := Sprite2D.new()
		s.texture = Assets.tex("buildings/%s_sh" % name)
		s.centered = false
		s.position = anchor + Vector2(m.sh[0], m.sh[1])
		s.scale = Vector2(m.sh[2], m.sh[2])
		s.material = Assets.shadow_mat
		city.shadows.add_child(s)
		node.tree_exiting.connect(s.queue_free)
	if m.has("rooms"):
		var r := Sprite2D.new()
		r.texture = Assets.tex("buildings/%s_rooms" % name)
		r.centered = false
		r.position = Vector2(m.rooms[0], m.rooms[1]) + shift
		r.scale = Vector2(m.rooms[2], m.rooms[2])
		r.material = Assets.rooms_mat
		var h := _hash(t, 23)
		r.modulate = Color(1.0 if h % 3 else 0.0, 1.0 if h % 4 == 0 else 0.0, 1.0 if h % 5 == 0 else 0.0, 0.0)
		node.add_child(r)
