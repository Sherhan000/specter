class_name Life
extends Node
## Residents and traffic.
##
## Every resident lives in one home and follows a day plan: work or school, lunch, errands,
## a walk in the park, visiting a friend, and bed. People walk on the sidewalks and cross only
## at crosswalks, waiting for the light or a gap in the traffic; they open the door and go
## inside. Families own cars that are parked on the street in front of the house at night and
## near the work place during the day. Cars keep their lane and a safe distance, ask for room
## before entering an intersection, stop at red lights and for pedestrians on the crosswalk.
## Visitors and trucks come from other towns along the highway and leave the same way.

const MAX_PERSONS := 260
const MAX_MOVING_CARS := 70
const WALK_SPEED := 0.2         ## tiles per second
const CAR_SPEED := 0.75
const ACCEL := 0.9
const BRAKE := 2.6
const ARM_DIRS := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]
## sidewalk corners of a road tile: NW, NE, SW, SE
const CORNERS := [Vector2(0.075, 0.075), Vector2(0.925, 0.075), Vector2(0.075, 0.925), Vector2(0.925, 0.925)]
const COLORS := [Color("c8342a"), Color("2a5aa8"), Color("e8e8ea"), Color("a8acb0"), Color("2a2c30"), Color("3a7a4a"),
	Color("e8c040"), Color("1e3060"), Color("7a4a2a"), Color("d8d0c0"), Color("8a2a4a")]
const CIVIL := ["man", "woman", "man", "woman", "teen", "student"]
const JOB_KINDS := {
	"police": "police", "hospital": "doctor", "fire_station": "firefighter", "school": "business",
	"farm": "farmer", "orchard": "farmer", "greenhouse": "farmer", "ranch": "farmer", "warehouse": "builder",
	"sawmill": "builder", "workshop": "builder", "power_plant": "builder", "water_station": "builder", "solar_panel": "builder", "factory": "builder", "logistics": "builder",
	"bakery": "chef", "cafe": "chef", "pizzeria": "chef", "restaurant": "chef", "post_office": "postman",
	"bank": "business", "court": "businesswoman", "town_hall": "business", "office": "business", "mall": "businesswoman",
}
const FOOD := ["bakery", "cafe", "pizzeria", "restaurant", "mall"]
const SHOPS := ["supermarket", "market", "market_stall", "bazaar", "bakery", "boutique", "flowershop", "pharmacy", "mall", "gas_station"]
const OUTINGS := ["park", "plaza", "pond", "fountain", "bench", "playground", "statue", "zoo", "funfair", "museum",
	"stadium", "cinema", "restaurant", "library", "gym", "cafe"]

var city: Node
var car_grid := AStarGrid2D.new()
var walk := AStar2D.new()
var crossings := {}      ## "a:b" sidewalk edge -> [tile, arm (0..3) or 4 for mid-block]
var persons: Array = []
var walkers: Array = []  ## Walker nodes outside
var cyclists: Array = [] ## Cyclist nodes riding around
var cars: Array = []     ## every Car node (parked or driving)
var spots := {}          ## parking spot key -> Car (or a reservation)
var reserve := {}        ## intersection tile -> Array of [car, din, dout]
var waiting := {}        ## intersection tile -> {car: seconds waited}
var cross_busy := {}     ## Vector3i(tile.x, tile.y, arm) -> pedestrians on the crosswalk
var bins := {}           ## tile -> cars in it
var _tick := 0.0
var _ambient_t := 2.0
var _social_t := 1.0
var _hour := 0.0
var _garb_hour := -1
var _last_day := -1
var _dirty := true
var _conflict := {}


func _ready() -> void:
	car_grid.region = Rect2i(0, 0, Data.MAP, Data.MAP)
	car_grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
	car_grid.default_compute_heuristic = AStarGrid2D.HEURISTIC_MANHATTAN
	car_grid.update()
	_build_conflicts()
	roads_changed()
	Game.hour_passed.connect(func(_h): _dirty = true)


# ====================================================================== networks
func roads_changed() -> void:
	car_grid.fill_solid_region(Rect2i(0, 0, Data.MAP, Data.MAP), true)
	for c in Game.net:
		car_grid.set_point_solid(c, false)
	_build_walk()
	# spots on roads that are gone
	for k in spots.keys():
		if not Game.net.has(_spot_tile(k)):
			var c: Variant = spots[k]
			spots.erase(k)
			if c is Car and is_instance_valid(c) and c.state == "parked":
				c.lose_spot()
	for c in cars:
		if is_instance_valid(c):
			c.check_path()
	for w in walkers:
		if is_instance_valid(w):
			w.check_path()
	_dirty = true


func buildings_changed() -> void:
	_dirty = true


## A building was picked up and put down elsewhere: routes, car spots and doors that
## pointed at the old place must follow it, or people walk into an empty lot.
func building_moved(uid: int) -> void:
	_dirty = true
	var acc := _sidewalk_access(uid)
	for w in walkers.duplicate():
		if not is_instance_valid(w) or w.done or w.person == null or w.pts.is_empty():
			continue
		var p: Person = w.person
		var last: Dictionary = w.pts.back()
		if w.pts[0].get("door", 0) == uid and w.i <= 2:
			# just stepped out of the old door: start the trip again from the new one
			_drop_walker(w)
			p.where = uid
			_start_trip(p, p.dest, p.dest_stay)
		elif last.get("enter", 0) == uid:
			_reroute_walker(w, uid, acc)
	# the family car follows the home it belongs to
	for car in cars:
		if not is_instance_valid(car) or car.owner_home != uid or car.state != "parked":
			continue
		var headed := false
		for w in walkers:
			if is_instance_valid(w) and not w.pts.is_empty() and w.pts.back().get("car", null) == car:
				headed = true
		if headed:
			continue
		var sp := find_spot(uid, car)
		if sp.is_empty():
			continue
		if spots.get(car.home_spot) == car:
			spots.erase(car.home_spot)
		if spots.get(car.spot[0]) == car:
			spots.erase(car.spot[0])
		car.home_spot = sp[0]
		car.park_at(sp)
		spots[sp[0]] = car
	for car in cars:
		if is_instance_valid(car) and car.owner_home == uid and car.state != "parked":
			car.home_spot = ""


func _drop_walker(w: Walker) -> void:
	if w.crossing != Vector3i(-1, -1, -1):
		crossing_done(w.crossing)
		w.crossing = Vector3i(-1, -1, -1)
	walkers.erase(w)
	w.person.walker = null
	w.done = true
	w.queue_free()


## Send a walker that is already on its way to the new entrance of building `uid`.
func _reroute_walker(w: Walker, uid: int, acc: Dictionary) -> void:
	var p: Person = w.person
	var route := []
	if not acc.is_empty() and walk.get_point_count() > 0:
		var id := walk.get_closest_point(w.g)
		var tile := Vector2i((id / 4) % Data.MAP, (id / 4) / Data.MAP)
		route = walk_route({"tile": tile, "side": -1, "point": w.g, "corners": [id % 4]}, acc)
	if route.is_empty():
		# no sidewalk to the new place: they still get home, unseen
		_drop_walker(w)
		p.where = uid
		p.stay = p.dest_stay
		return
	if w.crossing != Vector3i(-1, -1, -1):
		crossing_done(w.crossing)
		w.crossing = Vector3i(-1, -1, -1)
	var door_to: Vector2 = city.views[uid].door_grid() if city.views.has(uid) else acc.entry
	route.append({"p": acc.entry})
	route.append({"p": door_to, "enter": uid})
	w.pts = route
	w.i = 1


static func _street(t: String) -> bool:
	return t != "highway" and t != "country"


func _arms(c: Vector2i) -> int:
	var a := 0
	for k in 4:
		if Game.net.has(c + ARM_DIRS[k]) and _street(Game.net[c + ARM_DIRS[k]]):
			a |= 1 << k
	return a


func _wid(c: Vector2i, corner: int) -> int:
	return (c.y * Data.MAP + c.x) * 4 + corner


func _build_walk() -> void:
	walk.clear()
	crossings.clear()
	var tiles := []
	for c in Game.net:
		if _street(Game.net[c]):
			tiles.append(c)
	for c in tiles:
		for k in 4:
			walk.add_point(_wid(c, k), Vector2(c) + CORNERS[k])
	var xw: Dictionary = city.ground.crosswalks
	var mid: Dictionary = city.ground.midblock
	for c in tiles:
		var a := _arms(c)
		var x: int = xw.get(c, 0)
		# edges of the tile: north NW-NE, east NE-SE, south SW-SE, west NW-SW
		var edges := [[0, 1, 0], [1, 3, 1], [2, 3, 2], [0, 2, 3]]
		for e in edges:
			var arm: int = e[2]
			if a & (1 << arm) == 0:
				walk.connect_points(_wid(c, e[0]), _wid(c, e[1]))
			elif x & (1 << arm):
				walk.connect_points(_wid(c, e[0]), _wid(c, e[1]))
				crossings[_ekey(_wid(c, e[0]), _wid(c, e[1]))] = [c, arm]
		if mid.has(c):
			var pairs := [[0, 2], [1, 3]] if a == 10 else [[0, 1], [2, 3]]
			for p in pairs:
				walk.connect_points(_wid(c, p[0]), _wid(c, p[1]))
				crossings[_ekey(_wid(c, p[0]), _wid(c, p[1]))] = [c, 4]
		# along the street to the next tile
		var e2: Vector2i = c + Vector2i(1, 0)
		if Game.net.has(e2) and _street(Game.net[e2]):
			walk.connect_points(_wid(c, 1), _wid(e2, 0))
			walk.connect_points(_wid(c, 3), _wid(e2, 2))
		var s2: Vector2i = c + Vector2i(0, 1)
		if Game.net.has(s2) and _street(Game.net[s2]):
			walk.connect_points(_wid(c, 2), _wid(s2, 0))
			walk.connect_points(_wid(c, 3), _wid(s2, 1))


static func _ekey(a: int, b: int) -> String:
	return "%d:%d" % [mini(a, b), maxi(a, b)]


## Where a building's lot meets the sidewalk: [road tile, side (arm index towards the building),
## the sidewalk point, the two corners on that side].
func _sidewalk_access(uid: int) -> Dictionary:
	if not Game.buildings.has(uid):
		return {}
	var r := Game.entrance_tile(uid)
	if r == Vector2i(-1, -1) or not _street(Game.net[r]):
		return {}
	var e: Vector2 = Game.entry_point(uid)
	var b: Dictionary = Game.buildings[uid]
	var n: int = Data.B[b.id].size
	var centre := Vector2(b.x + n * 0.5, b.y + n * 0.5)
	var d := centre - (Vector2(r) + Vector2(0.5, 0.5))
	var side := 0
	if absf(d.x) > absf(d.y):
		side = 1 if d.x > 0 else 3
	else:
		side = 2 if d.y > 0 else 0
	var corner_pairs := [[0, 1], [1, 3], [2, 3], [0, 2]]
	var p := Vector2(r)
	match side:
		0: p += Vector2(clampf(e.x - r.x, 0.1, 0.9), 0.075)
		1: p += Vector2(0.925, clampf(e.y - r.y, 0.1, 0.9))
		2: p += Vector2(clampf(e.x - r.x, 0.1, 0.9), 0.925)
		3: p += Vector2(0.075, clampf(e.y - r.y, 0.1, 0.9))
	return {"tile": r, "side": side, "point": p, "corners": corner_pairs[side], "entry": e}


## A walking route between two sidewalk points given as access dictionaries.
func walk_route(a: Dictionary, b: Dictionary) -> Array:
	if a.is_empty() or b.is_empty():
		return []
	var best: PackedInt64Array = PackedInt64Array()
	var best_cost := INF
	var best_pair := [0, 0]
	for ca in a.corners:
		for cb in b.corners:
			var ia := _wid(a.tile, ca)
			var ib := _wid(b.tile, cb)
			if not walk.has_point(ia) or not walk.has_point(ib):
				continue
			var ids := walk.get_id_path(ia, ib)
			if ids.is_empty():
				continue
			var cost: float = a.point.distance_to(walk.get_point_position(ia)) + b.point.distance_to(walk.get_point_position(ib))
			for i in range(1, ids.size()):
				cost += walk.get_point_position(ids[i - 1]).distance_to(walk.get_point_position(ids[i]))
			if cost < best_cost:
				best_cost = cost
				best = ids
				best_pair = [ca, cb]
	if best.is_empty():
		return []
	# both points on the same stretch of sidewalk: walk straight
	if a.tile == b.tile and a.side == b.side:
		return [{"p": a.point}, {"p": b.point}]
	var out := [{"p": a.point}]
	for i in best.size():
		var pos := walk.get_point_position(best[i])
		if i > 0:
			var key := _ekey(best[i - 1], best[i])
			if crossings.has(key):
				var cr: Array = crossings[key]
				var from := walk.get_point_position(best[i - 1])
				for q in _crossing_points(cr[0], cr[1], from, pos):
					out.append(q)
		out.append({"p": pos})
	out.append({"p": b.point})
	return out


## Waypoints over a crosswalk; the first one carries the crossing to ask for.
func _crossing_points(t: Vector2i, arm: int, from: Vector2, to: Vector2) -> Array:
	var o := Vector2(t)
	var p1: Vector2
	var p2: Vector2
	match arm:
		0:
			p1 = o + Vector2(0.27, 0.195)
			p2 = o + Vector2(0.73, 0.195)
		1:
			p1 = o + Vector2(0.805, 0.27)
			p2 = o + Vector2(0.805, 0.73)
		2:
			p1 = o + Vector2(0.27, 0.805)
			p2 = o + Vector2(0.73, 0.805)
		3:
			p1 = o + Vector2(0.195, 0.27)
			p2 = o + Vector2(0.195, 0.73)
		_:
			var horizontal := absf(to.y - from.y) > absf(to.x - from.x)
			if horizontal:
				p1 = Vector2(o.x + 0.5, from.y + signf(to.y - from.y) * 0.05)
				p2 = Vector2(o.x + 0.5, to.y - signf(to.y - from.y) * 0.05)
			else:
				p1 = Vector2(from.x + signf(to.x - from.x) * 0.05, o.y + 0.5)
				p2 = Vector2(to.x - signf(to.x - from.x) * 0.05, o.y + 0.5)
	if from.distance_to(p2) < from.distance_to(p1):
		var tmp := p1
		p1 = p2
		p2 = tmp
	return [{"p": p1}, {"p": p2, "cross": Vector3i(t.x, t.y, arm)}]


# ====================================================================== crossings and intersections
func controlled(t: Vector2i) -> bool:
	return Game.lights.has(t) or city.ground.crosswalks.has(t) or _arm_count(t) >= 3


func _arm_count(t: Vector2i) -> int:
	var n := 0
	for d in ARM_DIRS:
		if Game.net.has(t + d):
			n += 1
	return n


## May a pedestrian step onto this crosswalk now?
func can_cross(c: Vector3i) -> bool:
	var t := Vector2i(c.x, c.y)
	var arm := c.z
	if arm == 4:
		for car in bins.get(t, []):
			if car.moving() and car.s > 0.15 and car.s < 0.75:
				return false
		for d in ARM_DIRS:
			for car in bins.get(t + d, []):
				if car.moving() and car.next_tile() == t and car.s > 0.55 and car.v > 0.15:
					return false
		return true
	var axis := "y" if arm == 0 or arm == 2 else "x"   # the cars on this arm move along this axis
	if Game.lights.has(t):
		return city.light_state(t, axis) == 0 and _red_left(t, axis) > 3.0
	for r in reserve.get(t, []):
		var din: Vector2i = r[1]
		var dout: Vector2i = r[2]
		if -din == ARM_DIRS[arm] or dout == ARM_DIRS[arm]:
			return false
	for car in bins.get(t + ARM_DIRS[arm], []):
		if car.moving() and car.next_tile() == t and car.v > 0.1:
			return false
	return true


func _red_left(t: Vector2i, axis: String) -> float:
	var left := 0.0
	var probe := 0.0
	while probe < 10.0 and city.light_state_at(t, axis, probe) == 0:
		probe += 0.5
		left = probe
	return left


func crossing_started(c: Vector3i) -> void:
	cross_busy[c] = int(cross_busy.get(c, 0)) + 1


func crossing_done(c: Vector3i) -> void:
	var n: int = int(cross_busy.get(c, 0)) - 1
	if n <= 0:
		cross_busy.erase(c)
	else:
		cross_busy[c] = n


func _crosswalk_busy(t: Vector2i, arm: int) -> bool:
	return cross_busy.has(Vector3i(t.x, t.y, arm))


## Movement conflicts inside one intersection tile, by sampling the lane curves.
func _build_conflicts() -> void:
	var dirs := ARM_DIRS
	var curves := {}
	for din in dirs:
		for dout in dirs:
			curves[[din, dout]] = _curve_points(din, dout, 0.105)
	for a in curves:
		for b in curves:
			var hit := false
			if a[0] == b[0]:
				hit = false
			elif a[1] == b[1]:
				hit = true
			else:
				for p in curves[a]:
					for q in curves[b]:
						if p.distance_to(q) < 0.13:
							hit = true
							break
					if hit:
						break
			_conflict["%s%s%s%s" % [a[0], a[1], b[0], b[1]]] = hit


static func _curve_points(din: Vector2i, dout: Vector2i, lane: float) -> Array:
	var seg := segment_for(Vector2i.ZERO, Vector2(din), Vector2(dout), lane)
	var pts := []
	for i in 9:
		pts.append(eval_seg(seg, (i + 0.5) / 9.0))
	return pts


func _conflicts(din: Vector2i, dout: Vector2i, din2: Vector2i, dout2: Vector2i) -> bool:
	return _conflict.get("%s%s%s%s" % [din, dout, din2, dout2], true)


## A car asks to drive into tile t making the move din -> dout.
func request_enter(car: Car, t: Vector2i, din: Vector2i, dout: Vector2i) -> bool:
	if not car.siren:
		if Game.lights.has(t) and city.light_state(t, "x" if din.x != 0 else "y") != 2:
			return false
		# people on the crosswalks we drive over
		for k in 4:
			if ARM_DIRS[k] == -din or ARM_DIRS[k] == dout:
				if _crosswalk_busy(t, k):
					return false
		# leave the box free: there must be room behind it
		var nxt := t + dout
		for o in bins.get(nxt, []):
			if o != car and o.moving() and o.s < 0.45 and o.heading.dot(Vector2(dout)) > 0.5 and o.v < 0.2:
				return false
	var list: Array = reserve.get(t, [])
	for r in list:
		if r[0] == car:
			return true
		if is_instance_valid(r[0]) and _conflicts(din, dout, r[1], r[2]) and not car.siren:
			return false
	# give way to whoever has waited much longer for a conflicting move
	var w: Dictionary = waiting.get(t, {})
	var mine: float = w.get(car, 0.0)
	for o in w:
		if o != car and is_instance_valid(o) and w[o] > mine + 2.5 and _conflicts(din, dout, o.want_in, o.want_out):
			return false
	list.append([car, din, dout])
	reserve[t] = list
	w.erase(car)
	return true


func note_waiting(car: Car, t: Vector2i, delta: float) -> void:
	if not waiting.has(t):
		waiting[t] = {}
	waiting[t][car] = float(waiting[t].get(car, 0.0)) + delta


func release(car: Car, t: Vector2i) -> void:
	if reserve.has(t):
		reserve[t] = reserve[t].filter(func(r): return r[0] != car and is_instance_valid(r[0]))
		if reserve[t].is_empty():
			reserve.erase(t)
	if waiting.has(t):
		waiting[t].erase(car)


# ====================================================================== lane geometry
static func segment_for(t: Vector2i, din: Vector2, dout: Vector2, lane: float) -> Array:
	var c := Vector2(t) + Vector2(0.5, 0.5)
	var e := c - din * 0.5 + Vector2(-din.y, din.x) * lane
	var x := c + dout * 0.5 + Vector2(-dout.y, dout.x) * lane
	var q: Vector2
	if din == dout:
		q = (e + x) / 2.0
	elif din == -dout:
		q = c + din * 0.3
	else:
		q = c + (Vector2(-din.y, din.x) + Vector2(-dout.y, dout.x)) * lane
	return [e, q, x, maxf(0.2, e.distance_to(q) + q.distance_to(x))]


static func eval_seg(seg: Array, t: float) -> Vector2:
	var a: Vector2 = seg[0]
	var b: Vector2 = seg[1]
	var c: Vector2 = seg[2]
	return a * (1 - t) * (1 - t) + b * 2 * (1 - t) * t + c * t * t


static func tangent_seg(seg: Array, t: float, fallback: Vector2) -> Vector2:
	var a: Vector2 = seg[0]
	var b: Vector2 = seg[1]
	var c: Vector2 = seg[2]
	var v := (b - a) * 2 * (1 - t) + (c - b) * 2 * t
	return v.normalized() if v.length() > 0.0001 else fallback


static func lane_for(type: String, kind: String) -> float:
	match type:
		"highway":
			return 0.35 if kind in ["truck", "bus", "garbage", "delivery"] else 0.12
		"dirt":
			return 0.09
		"boulevard":
			return 0.125
		"avenue":
			return 0.15
		"bus_lane":
			return 0.16 if kind == "bus" else 0.07
		"bike":
			return 0.075
	return 0.105


func car_path(a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	if not car_grid.is_in_boundsv(a) or not car_grid.is_in_boundsv(b) or car_grid.is_point_solid(a) or car_grid.is_point_solid(b):
		return out
	out.assign(car_grid.get_id_path(a, b))
	return out


# ====================================================================== parking
## Spot key: "x,y,side,k". side is the arm index the car is parked against, k = 0 or 1.
func _spot_tile(key: String) -> Vector2i:
	var p := key.split(",")
	return Vector2i(int(p[0]), int(p[1]))


## Spots on a street tile: [key, grid position, heading].
func spots_of(t: Vector2i) -> Array:
	var out := []
	var axis: String = city.ground.parking.get(t, "")
	if axis == "" or city.ground.midblock.has(t):
		return out
	for k in 2:
		var a := 0.3 + k * 0.4
		if axis == "x":
			out.append(["%d,%d,2,%d" % [t.x, t.y, k], Vector2(t) + Vector2(a, 0.78), Vector2(1, 0)])
			out.append(["%d,%d,0,%d" % [t.x, t.y, k], Vector2(t) + Vector2(1.0 - a, 0.22), Vector2(-1, 0)])
		else:
			out.append(["%d,%d,3,%d" % [t.x, t.y, k], Vector2(t) + Vector2(0.22, a), Vector2(0, 1)])
			out.append(["%d,%d,1,%d" % [t.x, t.y, k], Vector2(t) + Vector2(0.78, 1.0 - a), Vector2(0, -1)])
	return out


## The nearest free spot around a building, preferring its own side of the street.
func find_spot(uid: int, for_car: Car) -> Array:
	var acc := _sidewalk_access(uid)
	if acc.is_empty():
		return []
	var r: Vector2i = acc.tile
	var best := []
	var best_d := INF
	for dy in range(-3, 4):
		for dx in range(-3, 4):
			var t := r + Vector2i(dx, dy)
			for sp in spots_of(t):
				var holder: Variant = spots.get(sp[0], null)
				if holder != null and holder != for_car and is_instance_valid(holder):
					continue
				var dist: float = sp[1].distance_to(acc.point)
				# the arrival tile behind the spot must be a road to come in the right way
				var behind := t - Vector2i(sp[2])
				if not Game.net.has(behind):
					dist += 5.0
				if dist < best_d:
					best_d = dist
					best = sp
	return best


## Sidewalk point next to a parked car (where the driver gets in and out).
func spot_sidewalk(sp: Array) -> Dictionary:
	var t := _spot_tile(sp[0])
	var side := int(sp[0].split(",")[2])
	var p: Vector2 = sp[1]
	var d := Vector2(ARM_DIRS[side])
	var q := p + d * 0.15
	var corner_pairs := [[0, 1], [1, 3], [2, 3], [0, 2]]
	return {"tile": t, "side": side, "point": q, "corners": corner_pairs[side]}


# ====================================================================== residents
func _rebuild_persons() -> void:
	_dirty = false
	var homes: Array[int] = []
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if Data.B[b.id].cat == "home" and Game.works(uid) and b.occ > 0 and city.views.has(uid):
			homes.append(uid)
	# people whose home disappeared move away
	for p in persons:
		if not homes.has(p.home):
			p.gone = true
	persons = persons.filter(func(p): return not p.gone or p.walker != null)
	var per_home := {}
	for p in persons:
		per_home[p.home] = int(per_home.get(p.home, 0)) + 1
	var total_pop := maxi(1, Game.pop)
	for uid in homes:
		var occ: int = Game.buildings[uid].occ
		var want := occ if occ <= 6 else mini(occ, 6 + int((occ - 6) * 0.08))
		want = mini(want, maxi(1, int(MAX_PERSONS * occ / float(total_pop)) + 1))
		while int(per_home.get(uid, 0)) < want and persons.size() < MAX_PERSONS:
			persons.append(_new_person(uid, int(per_home.get(uid, 0))))
			per_home[uid] = int(per_home.get(uid, 0)) + 1
	_assign_jobs()
	_assign_cars()
	# plan the rest of today for newcomers now that they know where they work
	for p in persons:
		if p.fresh:
			p.fresh = false
			_plan_day(p)
			# skip what already lies in the past, except going home
			while p.step < p.plan.size() and p.plan[p.step][0] >= 0.0 and p.plan[p.step][0] + 1.0 < _hour and p.plan[p.step][1] != 0:
				p.step += 1


func _new_person(home: int, nth: int) -> Person:
	var p := Person.new()
	p.home = home
	p.where = home
	var roll := randf()
	if nth >= 2 and roll < 0.5:
		p.role = "child"
		p.kind = ["boy", "girl"].pick_random()
	elif roll < 0.18:
		p.role = "retired"
		p.kind = ["grandpa", "grandma"].pick_random()
	else:
		p.role = "adult"
		p.kind = CIVIL.pick_random()
	p.row = _variant_row(p.kind)
	p.speed = WALK_SPEED * randf_range(0.9, 1.1) * (0.8 if p.role == "retired" else 1.0)
	p.wake = randf_range(6.0, 7.3)
	p.bed = randf_range(21.5, 23.8) if p.role != "child" else randf_range(20.5, 21.5)
	p.fresh = true
	return p


func _variant_row(kind: String) -> int:
	var rows: Array = Assets.units().people.kinds.get(kind, [0])
	return int(rows.pick_random())


func _assign_jobs() -> void:
	var places := {}
	var schools: Array[int] = []
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		var cat: String = Data.B[b.id].cat
		if not Game.works(uid):
			continue
		if cat in ["shop", "ind", "service", "fun"]:
			places[uid] = Data.stat(b.id, "jobs", b.lvl)
		if b.id in ["school", "kindergarten"]:
			schools.append(uid)
	for p in persons:
		if p.work > 0 and places.has(p.work):
			places[p.work] -= 1
	for p in persons:
		if p.role == "child":
			if (p.work == 0 or not Game.works(p.work)) and not schools.is_empty():
				p.work = _nearest(p.home, schools)
			continue
		if p.role != "adult":
			continue
		if p.work > 0 and Game.works(p.work):
			continue
		p.work = 0
		var cands: Array[int] = []
		for uid in places:
			if places[uid] > 0:
				cands.append(uid)
		if cands.is_empty() or randf() < 0.12:
			continue
		p.work = _nearest(p.home, cands, 8)
		places[p.work] -= 1
		p.kind = JOB_KINDS.get(Game.buildings[p.work].id, p.kind)
		if p.kind == "business" and randf() < 0.5:
			p.kind = "businesswoman"
		p.row = _variant_row(p.kind)


func _assign_cars() -> void:
	var households := {}
	for p in persons:
		if p.role == "adult":
			if not households.has(p.home):
				households[p.home] = []
			households[p.home].append(p)
	for home in households:
		var list: Array = households[home]
		var has := false
		for p in list:
			if p.car != null and is_instance_valid(p.car):
				has = true
		if has:
			continue
		var id: String = Game.buildings[home].id
		var chance: float = {"house_small": 0.65, "cottage": 0.8, "bungalow": 0.95, "villa": 1.0, "townhouse": 0.7}.get(id, 0.3)
		if randf() > chance:
			continue
		var sp := find_spot(home, null)
		if sp.is_empty():
			continue
		var car := _make_car(["sedan", "hatch", "sedan", "suv", "hatch", "pickup", "sedan", "van", "sports"].pick_random())
		car.owner_home = home
		car.home_spot = sp[0]
		car.park_at(sp)
		spots[sp[0]] = car
		list[0].car = car


func _nearest(from: int, list: Array, top := 1) -> int:
	if list.is_empty():
		return 0
	var a := Game.entry_point(from)
	var scored := []
	for u in list:
		scored.append([a.distance_squared_to(Game.entry_point(u)) + randf() * 4.0, u])
	scored.sort_custom(func(x, y): return x[0] < y[0])
	return scored[randi() % mini(top, scored.size())][1]


func _pick_place(p: Person, kinds: Array, max_dist := 14.0) -> int:
	var cands: Array[int] = []
	var a := Game.entry_point(p.home)
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if b.id in kinds and Game.works(uid) and Game.entry_point(uid).distance_to(a) < max_dist:
			cands.append(uid)
	return _nearest(p.home, cands, 3) if not cands.is_empty() else 0


func _friend_home(p: Person) -> int:
	var homes := []
	for o in persons:
		if o.home != p.home and not homes.has(o.home):
			homes.append(o.home)
	return homes.pick_random() if not homes.is_empty() else 0


## A day: list of [hour, place uid (0 = home), minimum stay in hours].
func _plan_day(p: Person) -> void:
	var plan := []
	match p.role:
		"adult":
			if p.work > 0:
				var leave := randf_range(6.6, 8.6)
				plan.append([leave, p.work, 3.0])
				if randf() < 0.35:
					plan.append([randf_range(12.0, 13.0), -1, 0.8])   # lunch out, then back to work
					plan.append([-1, p.work, 2.5])
				var back := randf_range(16.5, 18.5)
				if randf() < 0.35:
					plan.append([back, -2, 0.6])                      # shopping on the way home
				plan.append([back if plan.back()[1] != -2 else -1, 0, 1.0])
			else:
				plan.append([randf_range(9.0, 11.0), -2, 1.0])
				plan.append([-1, 0, 2.0])
			if randf() < 0.3:
				plan.append([randf_range(19.0, 20.5), -3, 1.6])     # evening out
				plan.append([-1, 0, 1.0])
		"child":
			if p.work > 0:
				plan.append([randf_range(7.4, 8.0), p.work, 5.0])
				plan.append([randf_range(14.0, 15.5), 0, 0.5])
			if randf() < 0.4:
				plan.append([randf_range(16.0, 17.5), -4, 1.2])     # playground or park
				plan.append([-1, 0, 1.0])
		"retired":
			plan.append([randf_range(9.0, 10.5), -3 if randf() < 0.6 else -2, 1.5])
			plan.append([-1, 0, 2.0])
			if randf() < 0.6:
				plan.append([randf_range(14.5, 16.5), -5, 1.5])     # see a friend
				plan.append([-1, 0, 1.0])
	p.plan = plan
	p.step = 0


func _resolve(p: Person, target: int) -> int:
	match target:
		0:
			return p.home
		-1:
			return _pick_place(p, FOOD, 7.0)
		-2:
			return _pick_place(p, SHOPS, 12.0)
		-3:
			return _pick_place(p, OUTINGS, 14.0)
		-4:
			return _pick_place(p, ["playground", "park", "plaza", "pond"], 8.0)
		-5:
			return _friend_home(p)
	return target if Game.works(target) else p.home


func _tick_persons(delta: float) -> void:
	var h := _hour
	for p in persons:
		if p.walker != null or p.driving:
			continue
		if p.gone:
			continue
		p.stay -= delta * 24.0 / Data.DAY_LENGTH
		if p.stay > 0.0 or p.step >= p.plan.size():
			continue
		var item: Array = p.plan[p.step]
		var at: float = item[0]
		if at >= 0.0 and h < at:
			continue
		if h > p.bed + 0.5 and item[1] != 0:
			p.step = p.plan.size()
			if p.where != p.home:
				_start_trip(p, p.home, 0.5)
			continue
		p.step += 1
		var dest := _resolve(p, item[1])
		if dest == 0 or dest == p.where:
			p.stay = item[2]
			continue
		_start_trip(p, dest, item[2])
	# night: anyone still out goes home
	if h > 23.5 or h < 4.0:
		for p in persons:
			if p.walker == null and not p.driving and p.where != p.home and not p.gone:
				_start_trip(p, p.home, 6.0)


## Leave the building the person is in and go to `dest`, on foot or by the family car.
func _start_trip(p: Person, dest: int, stay: float) -> void:
	if not Game.buildings.has(p.where) or not Game.buildings.has(dest):
		p.where = dest
		p.stay = stay
		return
	var from_acc := _sidewalk_access(p.where)
	var to_acc := _sidewalk_access(dest)
	if from_acc.is_empty() or to_acc.is_empty():
		p.where = dest
		p.stay = stay
		return
	var dist: float = from_acc.point.distance_to(to_acc.point)
	var car: Car = p.car if p.car != null and is_instance_valid(p.car) and p.car.state == "parked" else null
	var drive := car != null and dist > 5.0 and cars.filter(func(c): return c.moving()).size() < MAX_MOVING_CARS
	var route: Array
	if drive:
		var sp_acc := spot_sidewalk(car.spot)
		route = walk_route(from_acc, sp_acc)
		if route.is_empty():
			drive = false
	if not drive:
		route = walk_route(from_acc, to_acc)
	if route.is_empty():
		# no sidewalk connection: they still get there, unseen
		p.where = dest
		p.stay = stay
		return
	var w := _make_walker(p)
	var door_from: Vector2 = city.views[p.where].door_grid() if city.views.has(p.where) else from_acc.entry
	var lead := [{"p": door_from, "door": p.where}, {"p": from_acc.entry}]
	route = lead + route
	if drive:
		route.append({"p": car.door_point(), "car": car})
	else:
		var door_to: Vector2 = city.views[dest].door_grid() if city.views.has(dest) else to_acc.entry
		route.append({"p": to_acc.entry})
		route.append({"p": door_to, "enter": dest})
	w.start(route)
	p.dest = dest
	p.dest_stay = stay
	p.where = 0
	if city.views.has(p.home):
		pass


func walker_arrived(w: Walker, enter_uid: int) -> void:
	var p: Person = w.person
	walkers.erase(w)
	if p:
		p.walker = null
		p.where = enter_uid
		p.stay = p.dest_stay
	if city.views.has(enter_uid):
		city.views[enter_uid].open_door()
		if Game.phase == "night" and Data.B[Game.buildings[enter_uid].id].cat == "home":
			Game.sfx("door", -16.0)


func walker_in_car(w: Walker, car: Car) -> void:
	var p: Person = w.person
	walkers.erase(w)
	p.walker = null
	p.driving = true
	car.driver = p
	var dest: int = p.dest
	var sp := find_spot(dest, car) if dest != p.home or car.home_spot == "" else _spot_by_key(car.home_spot)
	if sp.is_empty():
		sp = find_spot(dest, car)
	if sp.is_empty() or not car.drive_to_spot(sp):
		# nowhere to park: walk instead
		p.driving = false
		car.driver = null
		var from := spot_sidewalk(car.spot)
		var route := walk_route(from, _sidewalk_access(dest))
		var w2 := _make_walker(p)
		var door_to: Vector2 = city.views[dest].door_grid() if city.views.has(dest) else Vector2.ZERO
		var acc := _sidewalk_access(dest)
		if route.is_empty() or acc.is_empty():
			walkers.erase(w2)
			w2.queue_free()
			p.walker = null
			p.where = dest
			p.stay = p.dest_stay
			return
		route = [{"p": car.door_point()}] + route + [{"p": acc.entry}, {"p": door_to, "enter": dest}]
		w2.start(route)
		return
	if sp[0] != car.home_spot:
		spots[sp[0]] = car


func _spot_by_key(key: String) -> Array:
	var t := _spot_tile(key)
	for sp in spots_of(t):
		if sp[0] == key:
			return sp
	return []


## The car of a resident is parked; the driver gets out and walks to the door.
func car_parked(car: Car) -> void:
	var p: Person = car.driver
	car.driver = null
	if p == null:
		return
	p.driving = false
	var dest: int = p.dest
	var acc := _sidewalk_access(dest)
	if acc.is_empty():
		p.where = dest
		p.stay = p.dest_stay
		return
	var route := walk_route(spot_sidewalk(car.spot), acc)
	var w := _make_walker(p)
	if route.is_empty():
		route = [{"p": car.door_point()}, {"p": acc.point}]
	var door_to: Vector2 = city.views[dest].door_grid() if city.views.has(dest) else acc.entry
	route = [{"p": car.door_point()}] + route + [{"p": acc.entry}, {"p": door_to, "enter": dest}]
	w.start(route)


func _make_walker(p: Person) -> Walker:
	var w := Walker.new()
	w.life = self
	w.person = p
	w.row = p.row if p else 0
	w.kind = p.kind if p else "man"
	w.speed = p.speed if p else WALK_SPEED
	city.world.add_child(w)
	walkers.append(w)
	if p:
		p.walker = w
	return w


func _make_car(kind: String) -> Car:
	var c := Car.new()
	c.life = self
	c.kind = kind
	city.world.add_child(c)
	c.build()
	if not Assets.units().cars[kind].fixed:
		c.paint_color = COLORS.pick_random()
	cars.append(c)
	return c


# ====================================================================== home lights
func _update_lights() -> void:
	var awake := {}
	var home_n := {}
	for p in persons:
		home_n[p.home] = int(home_n.get(p.home, 0)) + 1
		if p.where == p.home and not _asleep(p):
			awake[p.home] = int(awake.get(p.home, 0)) + 1
	var h := _hour
	for uid in city.views:
		var v: BuildingView = city.views[uid]
		var b: Dictionary = Game.buildings.get(uid, {})
		if b.is_empty():
			continue
		var cat: String = Data.B[b.id].cat
		if cat == "home":
			var n: int = awake.get(uid, 0)
			var total: int = maxi(1, home_n.get(uid, 1))
			var share := n / float(total)
			var hsh := absi(uid * 7919 + int(h) * 31) % 100
			if total <= 6:
				v.room_levels = Vector4(1.0 if n > 0 and (h >= 16.5 or h < 9.0) else 0.0,
					1.0 if n > 0 and (h >= 20.5 or h < 7.5) else 0.0,
					1.0 if n > 0 and (h < 8.5 or (h > 18.0 and h < 20.0)) else 0.0,
					1.0 if n > 0 and hsh < 30 else 0.0)
			else:
				v.room_levels = Vector4(1.0 if share > 0.1 else 0.0, 1.0 if share > 0.35 else 0.0,
					1.0 if share > 0.6 else 0.0, 1.0 if share > 0.2 and hsh < 50 else 0.0)
		else:
			var open := 7.0 <= h and h < 20.0
			if b.id in ["hospital", "police", "fire_station", "hotel", "gas_station"]:
				open = true
			elif cat == "fun" or b.id in ["restaurant", "cinema", "cafe", "pizzeria"]:
				open = 10.0 <= h and h < 23.5
			v.openness = (1.0 if open else 0.12) if Game.works(uid) else 0.0
			var w := 1.0 if open and Game.works(uid) else 0.0
			v.room_levels = Vector4(w, w, w * 0.6, w * 0.3)


func _asleep(p: Person) -> bool:
	return _hour >= p.bed or _hour < p.wake


# ====================================================================== the frame
func _process(delta: float) -> void:
	if not Game.profile.intro:
		return
	_hour = Game.day_time * 24.0
	if Game.day != _last_day:
		_last_day = Game.day
		for p in persons:
			_plan_day(p)
	if _dirty:
		_rebuild_persons()
	_rebuild_bins()
	_tick -= delta
	if _tick <= 0.0:
		_tick = 0.5
		_tick_persons(0.5)
		_update_lights()
	for c in cars:
		if is_instance_valid(c) and c.moving():
			c.drive(delta)
	for w in walkers:
		if is_instance_valid(w):
			w.step(delta)
	for cy in cyclists:
		if is_instance_valid(cy):
			cy.step(delta)
	_ambient_t -= delta
	if _ambient_t <= 0.0:
		_ambient_t = 2.0
		_ambient()
	_social_t -= delta
	if _social_t <= 0.0:
		_social_t = 0.9
		_social()
	cars = cars.filter(func(c): return is_instance_valid(c))
	walkers = walkers.filter(func(w): return is_instance_valid(w) and not w.done)
	cyclists = cyclists.filter(func(cy): return is_instance_valid(cy) and not cy.done)


func _rebuild_bins() -> void:
	bins.clear()
	for c in cars:
		if is_instance_valid(c) and c.moving():
			var t := Vector2i(floori(c.g.x), floori(c.g.y))
			if not bins.has(t):
				bins[t] = []
			bins[t].append(c)


func cars_near(g: Vector2) -> Array:
	var out: Array = []
	var t := Vector2i(floori(g.x), floori(g.y))
	for dy in [-1, 0, 1]:
		for dx in [-1, 0, 1]:
			var k := t + Vector2i(dx, dy)
			if bins.has(k):
				out.append_array(bins[k])
	return out


# ====================================================================== visitors, trucks, services
func _ambient() -> void:
	var moving := cars.filter(func(c): return c.moving()).size()
	var night := Game.phase == "night"
	var through := cars.filter(func(c): return c.role == "through").size()
	if through < (3 if night else 7) and moving < MAX_MOVING_CARS:
		var ends := Data.far_ends()
		var a: Vector2i = ends.pick_random()
		var b: Vector2i = ends.pick_random()
		if a != b:
			var path := car_path(a, b)
			if path.size() > 10:
				var kind: String = ["sedan", "truck", "bus", "suv", "van", "hatch", "sedan", "delivery"].pick_random()
				var c := _make_car(kind)
				c.role = "through"
				c.start_route(path, null)
	# visitors from other towns come to shops and leisure, park, walk in, and later drive home
	var visitors := cars.filter(func(c): return c.role == "visitor").size()
	if not night and visitors < 2 + Game.pop / 120 and moving < MAX_MOVING_CARS and Game.is_connected_to_highway():
		var places: Array[int] = []
		for uid in Game.buildings:
			if Data.B[Game.buildings[uid].id].cat in ["fun", "shop"] and Game.works(uid):
				places.append(uid)
		if not places.is_empty():
			var dest: int = places.pick_random()
			var c := _make_car(["sedan", "suv", "hatch", "van"].pick_random())
			c.role = "visitor"
			c.visit = dest
			var sp := find_spot(dest, c)
			var start: Vector2i = Data.far_ends().pick_random()
			if sp.is_empty() or not c.drive_to_spot(sp, start):
				c.queue_free()
			else:
				spots[sp[0]] = c
	# delivery van to shops in the morning
	if _hour > 7.0 and _hour < 11.0 and randf() < 0.15 and moving < MAX_MOVING_CARS and Game.is_connected_to_highway():
		var shops: Array[int] = []
		for uid in Game.buildings:
			if Data.B[Game.buildings[uid].id].cat in ["shop", "ind"] and Game.works(uid):
				shops.append(uid)
		if not shops.is_empty():
			var dest: int = shops.pick_random()
			var c := _make_car(["delivery", "truck"].pick_random())
			c.role = "delivery"
			c.visit = dest
			var sp := find_spot(dest, c)
			if sp.is_empty() or not c.drive_to_spot(sp, Data.far_ends().pick_random()):
				c.queue_free()
			else:
				spots[sp[0]] = c
	_update_buses()
	_update_cyclists()
	_update_garbage_trucks()


## Every hour each working depot sends a truck along the roads and back (the waste itself is counted in Game).
func _update_garbage_trucks() -> void:
	if int(_hour) == _garb_hour:
		return
	_garb_hour = int(_hour)
	if cars.filter(func(c): return c.moving()).size() >= MAX_MOVING_CARS:
		return
	var tiles: Array = Game.roads.keys()
	for st in Game.garbage_depots():
		if cars.any(func(c): return is_instance_valid(c) and c.kind == "garbage" and c.station == st):
			continue
		var home := Game.entrance_tile(st)
		var path := car_path(home, tiles.pick_random())
		if path.size() < 2:
			continue
		var back := car_path(path.back(), home)
		if back.size() > 1:
			path.append_array(back.slice(1))
		var c := _make_car("garbage")
		c.role = "service"
		c.station = st
		c.start_route(path, null)


## City buses: one per two stops (up to three) once two stops stand by connected roads.
func _update_buses() -> void:
	var stops := Game.bus_stops()
	var want := 0 if stops.size() < 2 else mini(3, (stops.size() + 1) / 2)
	var buses := cars.filter(func(c): return is_instance_valid(c) and c.role == "city_bus" and c.state != "gone")
	if buses.size() > want:
		buses[0].vanish()
	elif buses.size() < want and cars.filter(func(c): return c.moving()).size() < MAX_MOVING_CARS:
		var k := randi() % stops.size()
		var path := car_path(Game.entrance_tile(stops[k]), Game.entrance_tile(stops[(k + 1) % stops.size()]))
		if path.size() > 1:
			var c := _make_car("bus")
			c.role = "city_bus"
			c.stop_idx = (k + 1) % stops.size()
			c.start_route(path, null)


## Cyclists ride where there are bike lanes and sports towers, by day and in dry weather.
func _update_cyclists() -> void:
	var bike: Array = []
	for c in Game.roads:
		if Game.roads[c] == "bike":
			bike.append(c)
	var sport := 0
	for uid in Game.buildings:
		if Game.buildings[uid].id == "sport_tower" and Game.works(uid):
			sport += 1
	var want := mini(16, bike.size() / 3 + sport * 3)
	if Game.phase == "night" or Game.weather in ["rain", "storm", "snow"]:
		want = 0
	if cyclists.size() >= want or (bike.is_empty() and Game.roads.is_empty()):
		return
	var from_list: Array = bike if not bike.is_empty() else Game.roads.keys()
	var a: Vector2i = from_list.pick_random()
	var b: Vector2i = from_list.pick_random() if randf() < 0.6 else Game.roads.keys().pick_random()
	var path := car_path(a, b)
	if path.size() < 4:
		return
	var cy := Cyclist.new()
	city.world.add_child(cy)
	cy.start(path)
	cyclists.append(cy)


## A city bus reached its stop: wait a little, then drive on to the next stop.
func bus_at_stop(car: Car) -> void:
	car.state = "idle"
	var tw := car.create_tween()
	tw.tween_interval(4.0)
	tw.tween_callback(func():
		if not is_instance_valid(car) or car.state != "idle":
			return
		var stops := Game.bus_stops()
		if stops.size() < 2:
			car.vanish()
			return
		for _k in stops.size():
			car.stop_idx = (car.stop_idx + 1) % stops.size()
			var path := car_path(car.p.back(), Game.entrance_tile(stops[car.stop_idx]))
			if path.size() > 1:
				car.start_route(path, null)
				return
		car.vanish())


## A visitor or delivery car finished its stop: leave towards another town.
func visit_done(car: Car) -> void:
	car.leave_spot()
	var path := car_path(_spot_tile(car.spot[0]) if car.spot.size() > 0 else Vector2i(floori(car.g.x), floori(car.g.y)), Data.far_ends().pick_random())
	if path.size() < 2:
		car.vanish()
		return
	car.role = "through"
	car.start_route(path, null)


## Emergency services drive from their station to the building with lights on.
func dispatch(kind: String, target: int) -> void:
	var svc := "fire" if kind == "fire" else "health" if kind == "ambulance" else "police"
	var st := Game.service_building(svc)
	if st == 0 or not Game.buildings.has(target):
		return
	var path := car_path(Game.entrance_tile(st), Game.entrance_tile(target))
	if path.size() < 2:
		return
	var c := _make_car(kind)
	c.siren = true
	c.role = "service"
	c.station = st
	c.start_route(path, null)


func start_chase(caught: bool) -> void:
	var a := Vector2i(0, Data.HIGHWAY_Y)
	var b := Vector2i(Data.MAP - 1, Data.HIGHWAY_Y)
	if randf() < 0.5:
		var tmp := a
		a = b
		b = tmp
	var path := car_path(a, b)
	if path.size() < 20:
		return
	var thief := _make_car("sports")
	thief.paint_color = Color("e8e8ea")
	thief.role = "through"
	thief.vmax_k = 1.5
	thief.start_route(path, null)
	if caught:
		var cop := _make_car("police")
		cop.siren = true
		cop.role = "through"
		cop.vmax_k = 1.5
		cop.delay = 1.4
		cop.start_route(path, null)


# ====================================================================== interactions
func _social() -> void:
	var view: Rect2 = city.view_rect()
	for w in walkers:
		if not is_instance_valid(w) or w.done or w.busy > 0.0 or not view.has_point(w.position) or w.crossing != Vector3i(-1, -1, -1):
			continue
		if randf() < 0.03 and city.camera.zoom.x > 0.8:
			w.wave()
			continue
		for o in walkers:
			if o != w and is_instance_valid(o) and o.busy <= 0.0 and o.crossing == Vector3i(-1, -1, -1) \
					and (o.g - w.g).length() < 0.22:
				# neighbours from the same home (family) are much more likely to stop and talk
				var family: bool = w.person and o.person and w.person.home != 0 and w.person.home == o.person.home
				if randf() < (0.8 if family else 0.45):
					w.chat(o)
					o.chat(w)
					break


func pick(wp: Vector2) -> Variant:
	var best: Variant = null
	var best_d := 26.0
	for list in [walkers, cars]:
		for m in list:
			if not is_instance_valid(m) or not m.visible:
				continue
			var d: float = (m.position + Vector2(0, -12) - wp).length()
			if d < best_d:
				best_d = d
				best = m
	return best


func tapped(agent: Variant) -> void:
	agent.tapped()


func phrase_for(w: Walker) -> String:
	var p: Person = w.person
	var keys: Array[String] = []
	if p and Game.home_reasons.has(p.home):
		for reason in Game.home_reasons[p.home]:
			if int(reason[1]) < 0:
				keys.append("p_" + str(reason[0]))
		var h: int = Game.home_happy.get(p.home, 50)
		if h >= 70:
			keys.append("p_happy")
		elif h < 35:
			keys.append("p_sad")
	if Loc.PHRASES.has("p_kind_" + w.kind):
		keys.append("p_kind_" + w.kind)
	keys.append("p_w_" + Game.weather)
	keys.append("p_" + Game.phase)
	if p and p.dest == p.work and p.work > 0:
		keys.append("p_to_work")
	elif p and p.dest != p.home:
		keys.append("p_to_fun")
	keys.append("p_hello")
	var key: String = keys.pick_random()
	if not Loc.PHRASES.has(key):
		key = "p_hello"
	var list: Array = Loc.PHRASES[key][0 if Loc.lang == "ru" else 1]
	return Events.fmt(str(list.pick_random()))


func speech(owner: Node2D, text: String, seconds := 2.6) -> void:
	for c in owner.get_children():
		if c is SpeechBubble:
			c.queue_free()
	var b := SpeechBubble.new()
	b.font = city.hud.body_font
	owner.add_child(b)
	b.show_text(text, seconds)


# ====================================================================== people
class Person extends RefCounted:
	var home := 0
	var work := 0
	var role := "adult"
	var kind := "man"
	var row := 0
	var speed := 0.2
	var where := 0          ## building the person is in, 0 while outside
	var dest := 0
	var dest_stay := 0.0
	var stay := 0.0
	var plan := []
	var step := 0
	var wake := 6.5
	var bed := 22.5
	var car: Car = null
	var walker: Walker = null
	var driving := false
	var gone := false
	var fresh := false


class Walker extends Node2D:
	## A person on the sidewalk, following waypoints; waits at the curb until it may cross.
	var life: Life
	var person: Person
	var sprite: Sprite2D
	var row := 0
	var kind := "man"
	var speed := 0.2
	var g := Vector2.ZERO
	var heading := Vector2(0, 1)
	var pts: Array = []
	var i := 0
	var busy := 0.0
	var waving := false
	var crossing := Vector3i(-1, -1, -1)
	var side := 0.0
	var done := false
	var _wait := 0.0
	var _anim := randf()

	func _init() -> void:
		side = randf_range(-0.025, 0.025)

	func start(route: Array) -> void:
		pts = route
		i = 1
		g = pts[0].p
		var meta: Dictionary = Assets.units().people
		sprite = Sprite2D.new()
		sprite.texture = Assets.tex("units/people")
		sprite.hframes = 12
		sprite.vframes = int(sprite.texture.get_height() / meta.cell[1])
		sprite.centered = false
		sprite.offset = -Vector2(meta.anchor[0], meta.anchor[1])
		sprite.material = Assets.world_mat
		add_child(sprite)
		if pts[0].has("door") and life.city.views.has(pts[0].door):
			life.city.views[pts[0].door].open_door()
		modulate.a = 0.0
		create_tween().tween_property(self, "modulate:a", 1.0, 0.4)
		_visual()

	func check_path() -> void:
		pass

	func tapped() -> void:
		Game.sfx("tap")
		busy = 2.4
		sprite.frame = row * 12 + 8
		life.speech(self, life.phrase_for(self))

	func wave() -> void:
		busy = 1.6
		waving = true

	func chat(other: Walker) -> void:
		busy = 2.2
		var b := Sprite2D.new()
		b.texture = Assets.ui_icon(["chat", "heart", "chat", "happy"].pick_random())
		var ts := b.texture.get_size()
		b.scale = Vector2(22.0, 22.0) / maxf(ts.x, 1.0)
		b.position = Vector2(0, -44)
		b.z_index = 30
		add_child(b)
		var tw := b.create_tween()
		tw.tween_property(b, "position:y", -58.0, 1.8)
		tw.parallel().tween_property(b, "modulate:a", 0.0, 1.8)
		tw.tween_callback(b.queue_free)
		heading = (other.g - g).normalized() if (other.g - g).length() > 0.01 else heading

	func step(delta: float) -> void:
		if done:
			return
		_anim += delta
		if busy > 0.0:
			busy -= delta
			if waving:
				sprite.frame = row * 12 + 10 + int(_anim * 5.0) % 2
				sprite.flip_h = false
			else:
				var dir := Iso.grid_vec(heading)
				sprite.frame = row * 12 + (8 if dir.y >= 0 else 9)
			if busy <= 0.0:
				waving = false
			return
		if i >= pts.size():
			_arrive()
			return
		var target: Vector2 = pts[i].p
		var pt: Dictionary = pts[i]
		# about to walk over a crosswalk: wait for the light or a gap
		if pt.has("cross") and crossing == Vector3i(-1, -1, -1):
			if not life.can_cross(pt.cross):
				_wait += delta
				var dir := Iso.grid_vec(target - g)
				sprite.frame = row * 12 + (8 if dir.y >= 0 else 9)
				sprite.flip_h = (dir.x > 0) if dir.y >= 0 else (dir.x < 0)
				return
			crossing = pt.cross
			life.crossing_started(crossing)
			_wait = 0.0
		var d := target - g
		var len := d.length()
		var k := 1.25 if crossing != Vector3i(-1, -1, -1) else 1.0
		var stp := speed * k * delta
		if len <= stp:
			g = target
			i += 1
			if crossing != Vector3i(-1, -1, -1) and pt.has("cross"):
				life.crossing_done(crossing)
				crossing = Vector3i(-1, -1, -1)
		else:
			g += d / len * stp
			heading = d / len
		_visual()

	func _arrive() -> void:
		done = true
		if pts.is_empty():
			queue_free()
			return
		var last: Dictionary = pts.back()
		if last.has("car"):
			var car: Car = last.car
			var tw := create_tween()
			tw.tween_property(self, "modulate:a", 0.0, 0.3)
			tw.tween_callback(func():
				life.walker_in_car(self, car)
				queue_free())
			pts = []
			return
		if last.has("enter"):
			var uid: int = last.enter
			var tw := create_tween()
			tw.tween_property(self, "modulate:a", 0.0, 0.45)
			tw.tween_callback(func():
				life.walker_arrived(self, uid)
				queue_free())
			if life.city.views.has(uid):
				life.city.views[uid].open_door()
			pts = []
			return
		if person:
			person.walker = null
		queue_free()

	func _visual() -> void:
		var n := Vector2(-heading.y, heading.x)
		position = Iso.grid(g + n * side)
		var dir := Iso.grid_vec(heading)
		var back := dir.y < -0.01
		sprite.flip_h = (dir.x > 0) if not back else (dir.x < 0)
		sprite.frame = row * 12 + (4 if back else 0) + int(_anim * 8.0) % 4


# ====================================================================== vehicles
class Car extends Node2D:
	## A vehicle: parked (in a spot) or driving along a tile path, lane by lane.
	var life: Life
	var kind := "sedan"
	var role := "resident"     ## resident | through | visitor | delivery | service | city_bus
	var state := "idle"        ## idle | parked | driving | parking | unparking
	var paint_color := Color.WHITE
	var siren := false
	var vmax_k := 1.0
	var delay := 0.0
	var driver: Person = null
	var owner_home := 0
	var home_spot := ""
	var spot: Array = []       ## [key, grid position, heading] while parked or heading to it
	var target_spot: Array = []
	var visit := 0
	var station := 0
	var stop_idx := 0
	var g := Vector2.ZERO
	var heading := Vector2(1, 0)
	var v := 0.0
	var s := 0.0
	var p: Array[Vector2i] = []
	var idx := 0
	var seg := []
	var lane := 0.105
	var want_in := Vector2i.ZERO
	var want_out := Vector2i.ZERO
	var _reserved := Vector2i(-99, -99)
	var _stuck := 0.0
	var _stop_t := 0.0
	var _glide := 0.0
	var _glide_from := Vector2.ZERO
	var _glide_to := Vector2.ZERO
	var _t := randf()
	var base: Sprite2D
	var paint: Sprite2D
	var lights: Sprite2D
	var sir: Sprite2D
	var beam: Sprite2D
	var _frame := -1

	func build() -> void:
		var m: Dictionary = Assets.units().cars[kind]
		for layer in 3:
			var sp := Sprite2D.new()
			sp.centered = false
			sp.offset = -Vector2(m.anchor[0], m.anchor[1])
			sp.material = Assets.world_mat if layer < 2 else Assets.glow_mat
			add_child(sp)
			match layer:
				0: base = sp
				1: paint = sp
				2: lights = sp
		if m.siren:
			sir = Sprite2D.new()
			sir.centered = false
			sir.offset = -Vector2(m.anchor[0], m.anchor[1])
			sir.material = Assets.glow_mat
			add_child(sir)
		beam = Sprite2D.new()
		beam.texture = Assets.tex("fx/beam")
		beam.centered = false
		beam.offset = Vector2(0, -32)
		beam.material = Assets.glow_mat
		beam.z_index = -1
		add_child(beam)

	func moving() -> bool:
		return state in ["driving", "parking", "unparking"]

	func half_len() -> float:
		return float(Assets.units().cars[kind].len) / 160.0 / 2.0

	func next_tile() -> Vector2i:
		return p[idx + 1] if idx + 1 < p.size() else Vector2i(-99, -99)

	func door_point() -> Vector2:
		if spot.is_empty():
			return g
		var side := int(spot[0].split(",")[2])
		return Vector2(spot[1]) + Vector2(ARM_DIRS[side]) * 0.12

	func park_at(sp: Array) -> void:
		spot = sp
		state = "parked"
		g = sp[1]
		heading = sp[2]
		v = 0.0
		_visual()

	func lose_spot() -> void:
		# the street under the car was removed: it drives off to another town
		if state == "parked":
			vanish()

	func leave_spot() -> void:
		if not spot.is_empty() and life.spots.get(spot[0]) == self and spot[0] != home_spot:
			life.spots.erase(spot[0])

	## Start from the parked spot (or a far end) and drive to the spot `sp`.
	func drive_to_spot(sp: Array, from_end := Vector2i(-1, -1)) -> bool:
		var start: Vector2i
		var dir: Vector2i
		if from_end != Vector2i(-1, -1):
			start = from_end
		else:
			start = Vector2i(floori(g.x), floori(g.y))
		var goal := life._spot_tile(sp[0])
		var gdir := Vector2i(sp[2])
		var before := goal - gdir
		var path: Array[Vector2i]
		if from_end == Vector2i(-1, -1):
			dir = Vector2i(heading.round())
			var ahead := start + dir
			if not Game.net.has(ahead):
				ahead = start - dir
			if not Game.net.has(before):
				return false
			var rest := life.car_path(ahead, before)
			if rest.is_empty() and ahead != before:
				return false
			path = [start]
			path.append_array(rest if not rest.is_empty() else [ahead])
		else:
			if not Game.net.has(before):
				return false
			path = life.car_path(start, before)
			if path.is_empty():
				return false
		path.append(goal)
		target_spot = sp
		leave_spot()
		start_route(path, sp)
		return true

	func start_route(path: Array[Vector2i], to_spot: Variant) -> void:
		p = path
		idx = 0
		target_spot = to_spot if to_spot != null else []
		lane = Life.lane_for(Game.net.get(p[0], "asphalt"), kind)
		if state == "parked":
			state = "unparking"
			_glide = 0.0
			_glide_from = g
			_make_first_segment()
			_glide_to = Life.eval_seg(seg, s)
		else:
			state = "driving"
			seg = _segment(0)
			s = 0.0 if role != "through" else 0.5
			g = Life.eval_seg(seg, s)
			v = CAR_SPEED * 0.6
			if role != "city_bus" or modulate.a < 0.99:
				modulate.a = 0.0
				create_tween().tween_property(self, "modulate:a", 1.0, 0.6)
		visible = delay <= 0.0
		_visual()

	func _make_first_segment() -> void:
		var dout := Vector2(p[1] - p[0]) if p.size() > 1 else heading
		var t0 := p[0]
		var c := Vector2(t0) + Vector2(0.5, 0.5)
		var right := Vector2(-heading.y, heading.x)
		var along := (g - c).dot(heading)
		var p0 := c + heading * along + right * lane
		var x := c + dout * 0.5 + Vector2(-dout.y, dout.x) * lane
		var q: Vector2
		if dout.is_equal_approx(heading):
			q = (p0 + x) / 2.0
		elif dout.is_equal_approx(-heading):
			q = c + heading * 0.32
		else:
			q = p0 + heading * (x - p0).dot(heading)
		seg = [p0, q, x, maxf(0.15, p0.distance_to(q) + q.distance_to(x))]
		s = 0.0

	func _segment(k: int) -> Array:
		var din: Vector2 = Vector2(p[k] - p[k - 1]) if k > 0 else (Vector2(p[1] - p[0]) if p.size() > 1 else heading)
		var dout: Vector2 = Vector2(p[k + 1] - p[k]) if k + 1 < p.size() else din
		lane = Life.lane_for(Game.net.get(p[k], "asphalt"), kind)
		return Life.segment_for(p[k], din, dout, lane)

	func check_path() -> void:
		if not moving():
			return
		for k in range(idx, p.size()):
			if not Game.net.has(p[k]):
				vanish()
				return

	func vanish() -> void:
		if life:
			life.release(self, _reserved)
			if not spot.is_empty() and life.spots.get(spot[0]) == self:
				life.spots.erase(spot[0])
			if driver:
				driver.driving = false
				driver.where = driver.dest
				driver.stay = driver.dest_stay
				driver = null
		state = "gone"
		var tw := create_tween()
		tw.tween_property(self, "modulate:a", 0.0, 0.6)
		tw.tween_callback(queue_free)

	func tapped() -> void:
		Game.sfx("horn_" + ("truck" if kind in ["bus", "truck", "garbage", "fire", "delivery"] else "car"), -6.0)
		life.speech(self, Loc.t("beep"), 1.2)

	## Distance to the closest car ahead in our lane, in tiles (INF if none).
	func _gap_ahead() -> float:
		var best := INF
		var right := Vector2(-heading.y, heading.x)
		for o in life.cars_near(g):
			if o == self or not is_instance_valid(o) or o.state == "parked":
				continue
			var d: Vector2 = o.g - g
			var along := d.dot(heading)
			if along <= 0.0 or along > 1.6:
				continue
			if absf(d.dot(right)) > 0.09:
				continue
			if o.heading.dot(heading) < 0.2:
				continue
			var gap: float = along - half_len() - o.half_len()
			best = minf(best, gap)
		return best

	func drive(delta: float) -> void:
		_t += delta
		if delay > 0.0:
			delay -= delta
			visible = delay <= 0.0
			return
		if state == "unparking":
			_glide += delta * 1.1
			var k := smoothstep(0.0, 1.0, _glide)
			g = _glide_from.lerp(_glide_to, k)
			if _glide >= 1.0:
				state = "driving"
				v = 0.2
			_visual()
			return
		if state == "parking":
			_glide += delta * 0.9
			var k2 := smoothstep(0.0, 1.0, _glide)
			g = _glide_from.lerp(_glide_to, k2)
			heading = heading.lerp(Vector2(target_spot[2]), k2).normalized()
			if _glide >= 1.0:
				_parked()
			_visual()
			return
		var t := p[idx]
		var type: String = Game.net.get(t, "asphalt")
		var vmax := CAR_SPEED * float(Data.ROADS.get(type, Data.ROADS.asphalt).speed) * vmax_k
		if kind in ["bus", "truck", "garbage", "fire", "delivery"]:
			vmax *= 0.85
		if siren:
			vmax *= 1.3
		var turning: bool = (seg[1] as Vector2).distance_to(((seg[0] as Vector2) + (seg[2] as Vector2)) / 2.0) > 0.05
		if turning:
			vmax *= 0.55
		var target := vmax
		# keep distance to the car in front
		var gap := _gap_ahead()
		if gap < INF:
			target = minf(target, maxf(0.0, (gap - 0.12) * 1.6))
		# ask to enter the next controlled tile; wait at the stop line otherwise
		var seg_len: float = seg[3]
		var left := (1.0 - s) * seg_len
		var nxt := next_tile()
		if nxt != Vector2i(-99, -99) and left < 0.5:
			var din := nxt - t
			var dout := (p[idx + 2] - nxt) if idx + 2 < p.size() else din
			want_in = din
			want_out = dout
			if (life.controlled(nxt) or siren) and _reserved != nxt:
				if life.request_enter(self, nxt, din, dout):
					_reserved = nxt
				else:
					life.note_waiting(self, nxt, delta)
					var stop := maxf(0.0, left - 0.06)
					target = minf(target, sqrt(2.0 * BRAKE * stop) * 0.9)
		# arriving at our parking spot
		if not target_spot.is_empty() and idx == p.size() - 1:
			var along: float = (Vector2(target_spot[1]) - g).dot(heading)
			target = minf(target, maxf(0.12, along * 1.5))
			if along < 0.3:
				_begin_parking()
				return
		if v < target:
			v = minf(target, v + ACCEL * delta)
		else:
			v = maxf(target, v - BRAKE * delta)
		if v < 0.02:
			_stuck += delta
			if _stuck > 14.0:
				# a rare jam: squeeze through slowly instead of waiting forever
				v = 0.15
				_stuck = 9.0
		else:
			_stuck = 0.0
		s += v * delta / seg_len
		while s >= 1.0:
			s -= 1.0
			idx += 1
			if _reserved != Vector2i(-99, -99) and _reserved != p[mini(idx, p.size() - 1)]:
				life.release(self, _reserved)
				_reserved = Vector2i(-99, -99)
			if idx >= p.size():
				_end_of_route()
				return
			if not Game.net.has(p[idx]):
				vanish()
				return
			seg = _segment(idx)
		g = Life.eval_seg(seg, s)
		heading = Life.tangent_seg(seg, s, heading)
		# fade out when driving past the horizon
		if g.x + g.y < Data.HORIZON + 2.0:
			modulate.a = clampf((g.x + g.y - Data.HORIZON + 1.0) / 3.0, 0.0, 1.0)
		_visual()

	func _begin_parking() -> void:
		state = "parking"
		_glide = 0.0
		_glide_from = g
		_glide_to = target_spot[1]
		if _reserved != Vector2i(-99, -99):
			life.release(self, _reserved)
			_reserved = Vector2i(-99, -99)

	func _parked() -> void:
		spot = target_spot
		target_spot = []
		state = "parked"
		g = spot[1]
		heading = spot[2]
		v = 0.0
		_visual()
		if role in ["visitor", "delivery"]:
			var wait := 25.0 if role == "delivery" else randf_range(60.0, 140.0)
			var tw := create_tween()
			tw.tween_interval(wait)
			tw.tween_callback(func():
				if is_instance_valid(self) and state == "parked":
					life.visit_done(self))
		else:
			life.car_parked(self)

	func _end_of_route() -> void:
		if _reserved != Vector2i(-99, -99):
			life.release(self, _reserved)
			_reserved = Vector2i(-99, -99)
		if role == "city_bus":
			v = 0.0
			life.bus_at_stop(self)
			return
		if role == "service" and station > 0 and siren:
			# at the scene: lights on for a while, then back to the station
			state = "idle"
			var tw := create_tween()
			tw.tween_interval(8.0)
			tw.tween_callback(func():
				if not is_instance_valid(self):
					return
				siren = false
				var back := life.car_path(p.back(), Game.entrance_tile(station)) if Game.buildings.has(station) else []
				if back.size() > 1:
					station = 0
					start_route(back, null)
				else:
					vanish())
			return
		vanish()

	func _visual() -> void:
		position = Iso.grid(g)
		var f := Iso.dir16(heading)
		if f != _frame:
			_frame = f
			base.texture = Assets.car_frame(kind, f, 0)
			paint.texture = Assets.car_frame(kind, f, 1)
			lights.texture = Assets.car_frame(kind, f, 2)
			var sd := Iso.grid_vec(heading)
			beam.rotation = sd.angle()
		paint.modulate = paint_color
		var n := Game.night_amount()
		var lit := n > 0.05 and state != "parked"
		lights.visible = lit or state == "parking"
		lights.modulate.a = maxf(n, 0.35 if state in ["parking", "unparking"] else 0.0)
		beam.visible = lit and n > 0.3
		beam.modulate.a = n * 0.8
		if sir:
			sir.visible = siren
			if siren:
				sir.texture = Assets.car_frame(kind, f, 3 if int(_t * 5.0) % 2 == 0 else 4)
