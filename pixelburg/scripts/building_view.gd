class_name BuildingView
extends Node2D
## Visual for one building: the body (y-sorted by the centre of its footprint), its ground layer
## and cast shadow (drawn under everything), lit windows per room group, signs and lamps at
## night, the door that opens when someone walks in, scaffolding, bubbles, smoke and fire.

var uid := 0
var id := ""
var size := 1
var rot := 0
var tile := Vector2i.ZERO
var sprite: Sprite2D
var glow: Sprite2D
var rooms: Sprite2D
var base: Sprite2D
var shadow: Sprite2D
var bubble: Node2D
var bubble_icon: Sprite2D
var status_icon: Sprite2D
var progress: ProgressBarNode
var door: Polygon2D
var garland: Node2D
var fire_fx: Array[Node2D] = []
var heads: Array[Sprite2D] = []
var smoke: Array[CPUParticles2D] = []
var fountains: Array[CPUParticles2D] = []
var _fountain_t := 0.0
var tex_name := ""
var room_levels := Vector4.ZERO      ## wanted light of each room group (set by the residents)
var openness := 1.0                  ## work places: share of the building that is lit at night
var _room_now := Vector4.ZERO
var _lvl := 0
var _busy := false
var _anim_t := 0.0
var _state_t := 0.0
var _door_t := 0.0
var _phase := randf() * TAU
var _decals: Node2D
var _shadows: Node2D
var _shift := Vector2.ZERO


func setup(p_uid: int, decal_layer: Node2D, shadow_layer: Node2D) -> void:
	uid = p_uid
	_decals = decal_layer
	_shadows = shadow_layer
	var b: Dictionary = Game.buildings[uid]
	id = b.id
	size = Data.B[id].size
	rot = int(b.get("rot", 0))
	tile = Vector2i(b.x, b.y)
	position = Iso.vertex(tile.x + size * 0.5, tile.y + size * 0.5)
	_shift = Vector2(0, size * Iso.HY)

	base = Sprite2D.new()
	base.centered = false
	base.material = Assets.world_mat
	decal_layer.add_child(base)
	shadow = Sprite2D.new()
	shadow.centered = false
	shadow.material = Assets.shadow_mat
	shadow_layer.add_child(shadow)

	sprite = Sprite2D.new()
	sprite.centered = false
	sprite.material = Assets.world_mat
	add_child(sprite)
	rooms = Sprite2D.new()
	rooms.centered = false
	rooms.material = Assets.city_rooms_mat
	add_child(rooms)
	glow = Sprite2D.new()
	glow.centered = false
	glow.material = Assets.glow_mat
	add_child(glow)
	door = Polygon2D.new()
	door.visible = false
	add_child(door)

	progress = ProgressBarNode.new()
	add_child(progress)
	bubble = Node2D.new()
	bubble.z_index = 20
	add_child(bubble)
	var bg := Sprite2D.new()
	bg.texture = Assets.tex("ui/bubble")
	bg.offset = Vector2(0, -60)
	bg.scale = Vector2(0.62, 0.62)
	bubble.add_child(bg)
	bubble_icon = Sprite2D.new()
	bubble_icon.position = Vector2(0, -43)
	bubble.add_child(bubble_icon)
	bubble.visible = false
	status_icon = Sprite2D.new()
	status_icon.z_index = 20
	add_child(status_icon)
	status_icon.visible = false
	refresh(false)


func _exit_tree() -> void:
	for n in [base, shadow]:
		if is_instance_valid(n):
			n.queue_free()


func anchor() -> Vector2:
	return position + _shift


func _set_texture(name: String) -> void:
	tex_name = name
	var m := Assets.meta(name)
	if m.is_empty():
		return
	sprite.texture = Assets.tex("buildings/" + name)
	sprite.offset = Vector2(m.o[0], m.o[1]) + _shift
	glow.texture = Assets.tex("buildings/%s_glow" % name) if m.has("glow") else null
	if m.has("glow"):
		glow.offset = Vector2(m.glow[0], m.glow[1]) + _shift
	rooms.texture = Assets.tex("buildings/%s_rooms" % name) if m.has("rooms") else null
	if m.has("rooms"):
		rooms.position = Vector2(m.rooms[0], m.rooms[1]) + _shift
		rooms.scale = Vector2(m.rooms[2], m.rooms[2])
	var a := anchor()
	base.texture = Assets.tex("buildings/%s_base" % name) if m.has("base") else null
	if m.has("base"):
		base.position = a + Vector2(m.base[0], m.base[1])
	shadow.texture = Assets.tex("buildings/%s_sh" % name) if m.has("sh") else null
	if m.has("sh"):
		shadow.position = a + Vector2(m.sh[0], m.sh[1])
		shadow.scale = Vector2(m.sh[2], m.sh[2])


func top_y() -> float:
	return sprite.offset.y


func refresh(animate := true) -> void:
	var b: Dictionary = Game.buildings.get(uid, {})
	if b.is_empty():
		return
	rot = int(b.get("rot", 0))
	var busy: bool = not b.built or b.upg
	var name := "scaffold_%d" % size if busy else Assets.building_sprite(id, b.lvl, rot)
	if name != tex_name:
		_set_texture(name)
		_setup_extras(Assets.meta(name) if not busy else {})
	progress.visible = busy
	if not busy and (_busy or (_lvl != 0 and _lvl != b.lvl)) and animate:
		pop_in()
	_busy = busy
	_lvl = b.lvl
	bubble.visible = not busy and b.ready
	if bubble.visible:
		bubble_icon.texture = Assets.ui_icon("goods" if Data.B[id].cat == "ind" else "coin")
		var ts := bubble_icon.texture.get_size()
		bubble_icon.scale = Vector2(40.0, 40.0) / maxf(ts.x, 1.0)
	bubble.position = Vector2(0, top_y() + 6)
	status_icon.position = Vector2(0, top_y())
	sprite.modulate = Color(0.55, 0.5, 0.5) if b.dmg else Color.WHITE
	_update_fire(b.fire > 0.0 or b.dmg)
	_update_garland(b)


func _setup_extras(m: Dictionary) -> void:
	for s in smoke:
		s.queue_free()
	smoke.clear()
	fountains.clear()
	for h in heads:
		h.queue_free()
	heads.clear()
	door.visible = false
	door.polygon = PackedVector2Array()
	if m.is_empty():
		return
	for key in m.points:
		var p: Array = m.points[key]
		var pos := Vector2(p[0], p[1]) + _shift
		if key.begins_with("smoke") or key.begins_with("chimney"):
			var ps := CPUParticles2D.new()
			ps.texture = Assets.tex("fx/puff")
			ps.position = pos
			ps.amount = 6 if key.begins_with("chimney") else 14
			ps.lifetime = 4.0
			ps.direction = Vector2(0.35, -1)
			ps.spread = 12.0
			ps.gravity = Vector2(6, -6)
			ps.initial_velocity_min = 10.0
			ps.initial_velocity_max = 18.0
			ps.scale_amount_min = 0.9 if key.begins_with("chimney") else 1.6
			ps.scale_amount_max = 1.4 if key.begins_with("chimney") else 2.4
			var curve := Curve.new()
			curve.add_point(Vector2(0, 0.5))
			curve.add_point(Vector2(1, 2.2))
			ps.scale_amount_curve = curve
			var grad := Gradient.new()
			grad.set_color(0, Color(1, 1, 1, 0.7))
			grad.set_color(1, Color(1, 1, 1, 0.0))
			ps.color_ramp = grad
			ps.z_index = 15
			add_child(ps)
			smoke.append(ps)
		elif key.begins_with("light"):
			var h := Sprite2D.new()
			h.texture = Assets.tex("fx/lamp_head")
			h.material = Assets.glow_mat
			h.position = pos
			h.scale = Vector2(1.6, 1.6)
			add_child(h)
			heads.append(h)
		elif key == "fountain":
			var ps := CPUParticles2D.new()
			ps.texture = Assets.tex("fx/drop")
			ps.position = pos
			ps.amount = 44
			ps.lifetime = 1.1
			ps.direction = Vector2(0, -1)
			ps.spread = 16.0
			ps.gravity = Vector2(0, 90)
			ps.initial_velocity_min = 40.0
			ps.initial_velocity_max = 58.0
			ps.scale_amount_min = 0.85
			ps.scale_amount_max = 1.3
			ps.color = Color(0.85, 0.95, 1.0, 0.8)
			ps.z_index = 2
			add_child(ps)
			smoke.append(ps)
			fountains.append(ps)
			# a soft mist drifting off the jet, for a fuller, more alive spray
			var mist := CPUParticles2D.new()
			mist.texture = Assets.tex("fx/drop")
			mist.position = pos + Vector2(0, -8)
			mist.amount = 24
			mist.lifetime = 1.6
			mist.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
			mist.emission_sphere_radius = 5.0
			mist.direction = Vector2(0, -1)
			mist.spread = 65.0
			mist.gravity = Vector2(0, 26)
			mist.initial_velocity_min = 6.0
			mist.initial_velocity_max = 16.0
			mist.scale_amount_min = 0.45
			mist.scale_amount_max = 0.85
			mist.color = Color(0.92, 0.97, 1.0, 0.3)
			mist.z_index = 2
			add_child(mist)
			smoke.append(mist)
	if m.points.has("door_a") and m.points.has("door_t"):
		var a := Vector2(m.points.door_a[0], m.points.door_a[1]) + _shift
		var b2 := Vector2(m.points.door_b[0], m.points.door_b[1]) + _shift
		var t := Vector2(m.points.door_t[0], m.points.door_t[1]) + _shift
		var hgt := a.y - t.y
		door.polygon = PackedVector2Array([a, b2, b2 - Vector2(0, hgt), a - Vector2(0, hgt)])


## Grid position of the door (a point on the facade) and of the lot entrance on the street side.
func door_grid() -> Vector2:
	var m := Assets.meta(tex_name)
	if m.has("door_g"):
		return Vector2(tile) + Vector2(m.door_g[0], m.door_g[1])
	return Vector2(tile) + Vector2(size * 0.5, size * 0.5)


func entry_grid() -> Vector2:
	var m := Assets.meta(tex_name)
	if m.has("entry_g"):
		return Vector2(tile) + Vector2(m.entry_g[0], m.entry_g[1])
	return Game.entry_point(uid)


func open_door(seconds := 1.4) -> void:
	_door_t = seconds
	door.visible = door.polygon.size() > 0


func _update_fire(on: bool) -> void:
	if on and fire_fx.is_empty():
		var b: Dictionary = Game.buildings[uid]
		var burning: bool = b.fire > 0.0
		for i in (4 if size == 1 else 8):
			var f := Sprite2D.new()
			f.texture = Assets.tex("fx/fire") if burning else Assets.tex("fx/smoke_dark")
			f.hframes = 4 if burning else 1
			f.scale = Vector2(2.2, 2.2)
			f.position = Vector2(randf_range(-70, 70) * size, top_y() * randf_range(0.15, 0.55) + _shift.y * 0.5)
			f.z_index = 16
			add_child(f)
			fire_fx.append(f)
	elif not on:
		for f in fire_fx:
			f.queue_free()
		fire_fx.clear()


func _update_garland(b: Dictionary) -> void:
	if garland:
		garland.queue_free()
		garland = null
	var other: int = b.link
	if other <= 0 or other < uid or not Game.buildings.has(other):
		return
	var ob: Dictionary = Game.buildings[other]
	var on: int = Data.B[ob.id].size
	var my_top := Vector2(0, top_y() * 0.45)
	var their := Iso.vertex(ob.x + on * 0.5, ob.y + on * 0.5) - position + Vector2(0, -60)
	garland = Node2D.new()
	garland.z_index = 18
	add_child(garland)
	var line := Line2D.new()
	line.width = 1.5
	line.default_color = Color(0.2, 0.18, 0.22)
	var pts := PackedVector2Array()
	for i in 17:
		var t := i / 16.0
		pts.append(my_top.lerp(their, t) + Vector2(0, sin(t * PI) * 26.0))
	line.points = pts
	garland.add_child(line)
	var cols := [Color(1, 0.4, 0.4), Color(1, 0.85, 0.3), Color(0.4, 0.8, 1), Color(0.5, 1, 0.5)]
	for i in range(1, 16):
		var bulb := Sprite2D.new()
		bulb.texture = Assets.tex("units/lamp_dot")
		bulb.modulate = cols[i % 4]
		bulb.position = pts[i]
		bulb.material = Assets.glow_mat
		garland.add_child(bulb)


func _process(delta: float) -> void:
	_anim_t += delta
	var night := Game.light_level()
	glow.modulate.a = night * openness
	_room_now = _room_now.lerp(room_levels, minf(1.0, delta * 3.0))
	rooms.modulate = Color(_room_now.x, _room_now.y, _room_now.z, _room_now.w)
	rooms.visible = night > 0.02
	for h in heads:
		h.modulate.a = night * (0.85 + sin(_anim_t * 6.0) * 0.06)
	if garland:
		for i in range(1, garland.get_child_count()):
			garland.get_child(i).modulate.a = 0.35 + night * 0.65 * (0.7 + 0.3 * sin(_anim_t * 3.0 + i))
	if _door_t > 0.0:
		_door_t -= delta
		door.color = Color(0.1, 0.07, 0.06).lerp(Color(1.0, 0.85, 0.5), night * 0.9)
		if _door_t <= 0.0:
			door.visible = false
	if bubble.visible:
		bubble.position.y = top_y() + 6 + sin(_anim_t * 3.0 + _phase) * 4.0
	for f in fire_fx:
		if f.hframes > 1:
			f.frame = posmod(int(_anim_t * 10.0 + f.position.x), 4)
		else:
			f.position.y -= delta * 10.0
			if f.position.y < top_y() - 30:
				f.position.y = top_y() * 0.3
	if status_icon.visible:
		status_icon.position.y = top_y() + sin(_anim_t * 4.0) * 3.0
	if not fountains.is_empty():
		var jet := 1.0 + sin(_anim_t * 2.2 + _phase) * 0.18
		for ps in fountains:
			ps.speed_scale = jet
		if fountains[0].emitting:
			_fountain_t -= delta
			if _fountain_t <= 0.0:
				_fountain_t = randf_range(0.5, 0.9)
				_fountain_splash(fountains[randi() % fountains.size()].position)
	# the state of the building changes slowly: look at it a few times a second
	_state_t -= delta
	if _state_t > 0.0:
		return
	_state_t = 0.2 + randf() * 0.1
	var b: Dictionary = Game.buildings.get(uid, {})
	if b.is_empty():
		return
	if fire_fx.size() > 0 and b.fire <= 0.0 and not b.dmg:
		_update_fire(false)
	if not b.built or b.upg:
		var total: float = Data.B[id].time if not b.built else Data.upgrade_cost(id, b.lvl).time
		progress.ratio = b.prog / total
		progress.position = Vector2(0, top_y() + 24)
		progress.queue_redraw()
	var st := Game.status(uid) if b.built and not b.ready else ""
	status_icon.visible = st != ""
	if st != "":
		var ic: String = {"road": "noroad", "closed": "closed", "fire": "fire", "dmg": "fire", "goods": "goods", "staff": "jobs"}.get(st, "warn")
		status_icon.texture = Assets.ui_icon(ic)
		var ts := status_icon.texture.get_size()
		status_icon.scale = Vector2(40.0, 40.0) / maxf(ts.x, 1.0)
	var works := Game.works(uid)
	for s in smoke:
		s.emitting = works


func contains_point(world_p: Vector2) -> bool:
	if bubble.visible and (world_p - (global_position + bubble.position + Vector2(0, -25))).length() < 26.0:
		return true
	var local := world_p - global_position - sprite.offset
	var img := Assets.image("buildings/" + tex_name)
	if local.x < 0 or local.y < 0 or local.x >= img.get_width() or local.y >= img.get_height():
		return false
	return img.get_pixel(int(local.x), int(local.y)).a > 0.5


## Tall enough to hide what stands behind it (towers, skyscrapers).
func is_tall() -> bool:
	return sprite.texture != null and sprite.texture.get_height() > 460


## Whether a world point falls inside the picture of the building (its bounding box).
func covers(world_p: Vector2) -> bool:
	if sprite.texture == null:
		return false
	var local := world_p - global_position - sprite.offset
	var sz := sprite.texture.get_size()
	return local.x >= 0 and local.y >= 0 and local.x < sz.x and local.y < sz.y - size * Iso.HY


var _fade := 1.0
func set_fade(a: float) -> void:
	if is_equal_approx(a, _fade):
		return
	_fade = a
	create_tween().tween_property(self, "modulate:a", a, 0.25)


func faded() -> bool:
	return _fade < 0.99


func bounce() -> void:
	var tw := create_tween()
	sprite.scale = Vector2.ONE
	tw.tween_property(sprite, "scale", Vector2(1.03, 0.97), 0.07)
	tw.tween_property(sprite, "scale", Vector2(0.99, 1.01), 0.08)
	tw.tween_property(sprite, "scale", Vector2.ONE, 0.1)


func pop_in() -> void:
	sprite.scale = Vector2(1.08, 0.7)
	var tw := create_tween()
	tw.tween_property(sprite, "scale", Vector2.ONE, 0.6).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	Game.sfx("done")
	var dust := CPUParticles2D.new()
	dust.texture = Assets.tex("fx/puff")
	dust.one_shot = true
	dust.explosiveness = 1.0
	dust.amount = 26
	dust.lifetime = 1.0
	dust.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	dust.emission_sphere_radius = size * 70.0
	dust.direction = Vector2(0, -1)
	dust.spread = 180.0
	dust.initial_velocity_min = 40.0
	dust.initial_velocity_max = 80.0
	dust.gravity = Vector2(0, 40)
	dust.scale_amount_min = 2.0
	dust.scale_amount_max = 3.2
	var grad := Gradient.new()
	grad.set_color(0, Color(0.95, 0.9, 0.8, 0.9))
	grad.set_color(1, Color(0.95, 0.9, 0.8, 0.0))
	dust.color_ramp = grad
	dust.position = Vector2(0, _shift.y * 0.5)
	dust.z_index = 16
	add_child(dust)
	dust.emitting = true
	dust.finished.connect(dust.queue_free)


## A droplet from the spray landing back in the basin, for the fountain's periodic ripple.
func _fountain_splash(at: Vector2) -> void:
	var s := Sprite2D.new()
	s.texture = Assets.tex("fx/splash")
	s.hframes = 3
	s.scale = Vector2(0.9, 0.9)
	s.position = at + Vector2(randf_range(-10.0, 10.0), randf_range(6.0, 14.0))
	s.modulate = Color(0.9, 0.97, 1.0, 0.6)
	s.z_index = 2
	add_child(s)
	var tw := s.create_tween()
	tw.tween_property(s, "frame", 2, 0.3)
	tw.tween_callback(s.queue_free)


class ProgressBarNode extends Node2D:
	var ratio := 0.0

	func _ready() -> void:
		z_index = 20

	func _draw() -> void:
		var w := 80.0
		draw_rect(Rect2(-w / 2 - 3, -3, w + 6, 14), Color(0.13, 0.1, 0.16))
		draw_rect(Rect2(-w / 2, 0, w, 8), Color(0.32, 0.3, 0.38))
		var fw := roundf(w * clampf(ratio, 0, 1))
		draw_rect(Rect2(-w / 2, 0, fw, 8), Color(0.33, 0.78, 0.36))
		draw_rect(Rect2(-w / 2, 0, fw, 3), Color(0.6, 0.95, 0.55))
