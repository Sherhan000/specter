extends Node
## Dev only: headless checks of the rules: zones, economy and ledger, bank, rules, events,
## story, losing, saving and backup codes, turning buildings, removing roads, residents. Not exported.

var fails := 0
var city


func check(cond: bool, what: String) -> void:
	print(("OK   " if cond else "FAIL ") + what)
	if not cond:
		fails += 1


func _ready() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json"))
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://city.json.bak"))
	Events.reset()
	Game.new_game()
	Game.profile = {"name": "Тест", "age": 20, "gender": "f", "privacy": true, "intro": true}
	Game.tutorial = 99
	city = load("res://scenes/main.tscn").instantiate()
	add_child(city)
	await get_tree().process_frame
	await get_tree().process_frame
	var c := Data.CENTER

	# ------------------------------------------------ data and sprites
	check(Data.ORDER.size() == Data.B.size() and Data.B.size() >= 55, "%d building types" % Data.B.size())
	var missing := 0
	for id in Data.ORDER:
		if id == "lamp":
			continue
		for L in [1, 2, 3]:
			for r in 4:
				if Assets.tex("buildings/" + Assets.building_sprite(id, L, r)) == null or Assets.meta(Assets.building_sprite(id, L, r)).is_empty():
					missing += 1
					print("     missing sprite ", Assets.building_sprite(id, L, r))
	check(missing == 0, "every building has 3 levels x 4 sides (%d missing)" % missing)
	for who in Events.CHARS:
		check(Assets.portrait(who, "smile") != null and Assets.portrait(who, "think") != null and Assets.face(who, "talk") != null,
			"portraits of " + who)
	var regional := Data.regional_roads()
	check(regional.size() > 250, "regional roads lead out of the valley (%d tiles)" % regional.size())
	check(Data.gates().size() >= 3 and Data.far_ends().size() >= 3, "gates and far ends for through traffic")
	check(Data.zone_of_plot(Vector2i(0, 3)) == "leisure" and Data.zone_of_plot(Vector2i(6, 1)) == "farm"
		and Data.zone_of_plot(Vector2i(6, 6)) == "industry" and Data.zone_of_plot(Vector2i(3, 3)) == "city", "zones laid out")

	# ------------------------------------------------ start state
	check(Game.pop == 27, "start population 27 (got %d)" % Game.pop)
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if Data.B[b.id].cat == "home":
			check(Game.entrance_tile(uid) != Vector2i(-1, -1), "start home %d at %d,%d faces a street" % [uid, b.x, b.y])
	for uid in Game.buildings:
		if Data.B[Game.buildings[uid].id].cat != "decor":
			check(Game.road_ok[uid], "start %s touches a road" % Game.buildings[uid].id)
	check(Game.lights.has(Vector2i(c, c)) and city.light_nodes.size() == 1, "traffic light at the start crossing")
	check(Game.lamps.size() == 3 and city.lamp_nodes.size() == 3, "start lamps placed")

	# ------------------------------------------------ zones
	check(Game.place_problem("farm", c - 4, c + 2) == "wrong_zone", "farm not allowed in the city zone")
	check(Game.place_problem("house_small", c + 10, c - 6) == "wrong_zone", "house not allowed in farmland")
	check(Game.place_problem("farm", c + 10, c - 6) == "", "farm allowed in farmland")
	check(Game.place_problem("house_small", c - 30, c - 30) == "bad_place", "can't build on unowned land")
	var c0 := Game.coins
	var house := Game.place("house_small", c + 3, c - 1)
	check(house > 0 and Game.coins == c0 - 120, "house costs 120")
	Game.simulate(11.0)
	check(Game.buildings[house].built, "construction finished")

	# ------------------------------------------------ roads & lights
	var path := Game.road_path(Vector2i(c - 3, c + 2), Vector2i(c - 3, c + 4), "dirt")
	c0 = Game.coins
	check(Game.build_roads(path, "dirt") and Game.coins == c0 - path.size() * 6, "dirt road %d tiles" % path.size())
	var up := Game.road_path(Vector2i(c - 3, c + 2), Vector2i(c - 3, c + 4), "stone")
	check(up.size() == path.size() and Game.road_cost(up, "stone") < up.size() * 30, "upgrading road is cheaper than new")
	check(not Game.toggle_light(Vector2i(c - 3, c + 3)), "no light on a straight road")
	Game.lights.clear()
	for i in 4:
		Game.lights[Vector2i(c - 2 + i, c)] = true
	Game.recalc()
	check(Game.rules.lights, "4 lights close together break the rule")
	Game.lights = {Vector2i(c, c): true}
	Game.recalc()
	check(not Game.rules.lights, "one light is fine")

	# ------------------------------------------------ roundabouts
	var rx := Vector2i(c, c)
	Game.coins = maxi(Game.coins, 5000)
	check(not Game.toggle_ring(Vector2i(c - 3, c + 3)), "no roundabout on a straight road")
	c0 = Game.coins
	check(Game.toggle_ring(rx) and Game.coins == c0 - Data.RING_COST, "roundabout costs %d" % Data.RING_COST)
	check(Game.rings.has(rx) and not Game.lights.has(rx), "roundabout replaces the traffic light")
	await get_tree().process_frame
	check(city.ring_nodes.has(rx) and city.ring_nodes[rx].size() == 2, "roundabout island and fountain are drawn")
	Game.save_game()
	Game.rings.clear()
	Game.load_game()
	check(Game.rings.has(rx), "roundabout is saved")
	var ctr := Vector2(rx) + Vector2(0.5, 0.5)
	var straight := Life.ring_segment(rx, Vector2(1, 0), Vector2(1, 0), 0.105)
	var plain := Life.segment_for(rx, Vector2(1, 0), Vector2(1, 0), 0.105)
	check(Life.eval_seg(straight, 0.0).distance_to(plain[0]) < 0.001 and Life.eval_seg(straight, 1.0).distance_to(plain[2]) < 0.001,
		"ring path starts and ends in the lanes")
	var inside := 1.0
	var ccw := true
	for i in 41:
		var k := i / 40.0
		inside = minf(inside, Life.eval_seg(straight, k).distance_to(ctr))
		var g0 := Life.eval_seg(straight, k) - ctr
		var tg := Life.tangent_seg(straight, k, Vector2(1, 0))
		if k > 0.3 and k < 0.7 and g0.cross(tg) > 0.0:
			ccw = false
	check(inside > RingView.APRON, "cars drive around the island (%.2f)" % inside)
	check(ccw, "everyone circles the same way, island on the left")
	var ring_near := Life.ring_segment(rx, Vector2(1, 0), Vector2(0, 1), 0.105)
	var ring_far := Life.ring_segment(rx, Vector2(1, 0), Vector2(0, -1), 0.105)
	check(float(ring_near[3]) < float(straight[3]) and float(straight[3]) < float(ring_far[3]), "right turn short, left turn the long way round")
	var ringer := Life.Car.new()
	ringer.p = [rx - Vector2i(0, 1), rx, rx + Vector2i(1, 0)] as Array[Vector2i]
	ringer.idx = 0
	check(city.life._ring_blocks(rx, Vector2i(1, 0), [ringer, Vector2i(0, 1), Vector2i(0, 1)]),
		"entering cars give way to a car coming round the ring")
	check(not city.life._ring_blocks(rx, Vector2i(1, 0), [ringer, Vector2i(0, 1), Vector2i(-1, 0)]),
		"no need to wait for a car leaving before the entry")
	ringer.free()
	Game.coins = maxi(Game.coins, 5000)
	check(Game.toggle_light(rx) and not Game.rings.has(rx), "a traffic light replaces the roundabout")
	check(Game.toggle_ring(rx) and Game.toggle_ring(rx) and not Game.rings.has(rx), "roundabout can be removed")
	Game.lights = {rx: true}
	Game.recalc()

	# ------------------------------------------------ lamps
	var q := Vector2i(2 * (c + 5), 2 * c)
	c0 = Game.coins
	Game.level = 2
	check(Game.lamp_problem(Vector2i(2 * (c + 4), 2 * (c + 3))) == "lamp_road", "lamps stand only on street sidewalks")
	check(Game.place_lamp(q, "modern") and Game.coins == c0 - Data.LAMP_COST, "lamp on a sidewalk corner")
	check(Game.lamp_problem(q + Vector2i(-1, 0)) == "lamp_close", "lamps need space between them")
	await get_tree().process_frame
	check(city.lamp_nodes.has(q), "lamp view created")

	# ------------------------------------------------ economy: ledger, tax, upkeep
	Game.coins = 10000
	Game.today = Game._empty_day()
	var uid0: int = Game.buildings.keys()[0]
	Game.buildings[uid0].ready = true
	var r1 := Game.collect(uid0)
	check(r1.has("coins") and int(Game.today["in"].get("rent", 0)) == r1.coins, "rent goes to the ledger")
	Game.set_tax(20)
	Game.buildings[uid0].ready = true
	var r2 := Game.collect(uid0)
	check(r2.coins > r1.coins, "higher tax brings more rent (%d > %d)" % [r2.coins, r1.coins])
	var h20 := Game.happy_target
	Game.set_tax(10)
	check(Game.happy_target > h20, "lower tax makes people happier")
	var bills := Game.daily_upkeep() + Game.daily_roads()
	var before := Game.coins
	Game.day_time = 0.999
	Game._advance_time(2.0)
	check(Game.day == 2, "a new day started")
	check(Game.ledger.size() == 1 and int(Game.ledger[0]["out"].get("upkeep", 0)) > 0, "upkeep charged at midnight")
	check(Game.coins <= before - bills + 200, "bills reduce coins (%d -> %d, bills %d)" % [before, Game.coins, bills])

	# ------------------------------------------------ turning buildings and removing roads
	var turn: int = Game.buildings.keys()[3]
	var rot0 := int(Game.buildings[turn].get("rot", 0))
	Game.rotate_building(turn)
	await get_tree().process_frame
	check(int(Game.buildings[turn].rot) == (rot0 + 1) % 4, "building turned to the next side")
	check(city.views[turn].sprite.texture == Assets.tex("buildings/" + Assets.building_sprite(Game.buildings[turn].id, Game.buildings[turn].lvl, (rot0 + 1) % 4)),
		"the view shows the turned sprite")
	Game.rotate_building(turn)
	Game.rotate_building(turn)
	Game.rotate_building(turn)
	check(Game.facing_for(c + 3, c - 1, 1, 2) == 0, "a lot north of the street faces it")
	var spur := Game.road_path(Vector2i(c + 4, c + 1), Vector2i(c + 4, c + 3), "asphalt")
	Game.build_roads(spur, "asphalt")
	var gone := Game.removable_path(Vector2i(c + 4, c + 1), Vector2i(c + 4, c + 3))
	c0 = Game.coins
	var refund := Game.road_refund(gone)
	check(gone.size() == 3 and refund > 0, "removable road found (%d tiles, %d back)" % [gone.size(), refund])
	check(Game.remove_roads(gone) and Game.coins == c0 + refund and not Game.roads.has(Vector2i(c + 4, c + 2)), "road removed with a refund")

	# ------------------------------------------------ close, evict, link, move
	var h1: int = Game.buildings.keys()[0]
	Game.buildings[h1].occ = 6
	Game.set_closed(h1, true)
	check(Game.buildings[h1].occ == 0 and not Game.works(h1), "closed home is empty")
	Game.set_closed(h1, false)
	Game.buildings[h1].occ = 6
	var rep0 := Game.rep
	Game.evict(h1)
	check(Game.buildings[h1].occ == 0 and Game.rep < rep0, "eviction empties the house and costs reputation")
	var h2: int = Game.buildings.keys()[1]
	check(Game.can_link(h1, h2), "neighbour houses can be linked")
	check(Game.link_homes(h1, h2) and Game.buildings[h1].link == h2, "houses linked")
	var shop := 0
	for uid in Game.buildings:
		if Game.buildings[uid].id == "bakery":
			shop = uid
	var old_x: int = Game.buildings[shop].x
	check(Game.move_building(shop, c + 3, c + 1), "bakery moved")
	check(not Game.occ.has(Vector2i(old_x, c + 1)) and Game.occ.get(Vector2i(c + 3, c + 1), 0) == shop, "occupancy follows the move")

	# ------------------------------------------------ bank
	check(not Game.take_loan(2000), "no loan without a bank")
	var bank := Game._add_building("bank", c - 6, c - 3, true)
	Game.recalc()
	c0 = Game.coins
	check(Game.take_loan(2000) and Game.coins == c0 + 2000 and int(Game.loan.left) > 2000, "loan taken with interest")
	check(Game.move_deposit(1000) and Game.deposit == 1000, "deposit opened")
	Game.day_time = 0.999
	Game._advance_time(2.0)
	check(Game.deposit > 1000, "deposit earns interest")
	check(int(Game.loan.days) == 6, "loan instalment paid")
	check(Game.repay_loan() and Game.loan.is_empty(), "loan repaid early")
	Game.demolish(bank)

	# ------------------------------------------------ watchtower
	var tower := Game._add_building("watchtower", c - 6, c - 3, true)
	Game.recalc()
	check(Game.tower_cooldown(tower) == 0, "watchtower ready at start")
	c0 = Game.coins
	var reward := Game.check_documents(tower)
	check(reward > 0 and Game.coins == c0 + reward, "checking papers pays a fine")
	check(Game.tower_cooldown(tower) > 0, "checking papers starts a cooldown")
	check(Game.check_documents(tower) == -1, "checking papers again is blocked by the cooldown")
	check(Game.patrol_mult() < 1.0, "a recent check lowers crime risk")
	Game.coins = Data.TOWER_MEETING_COST - 1
	check(not Game.hold_meeting(tower), "meeting needs enough coins")
	Game.coins = Data.TOWER_MEETING_COST + 500
	c0 = Game.coins
	var mood_before := Game.mood.size()
	check(Game.hold_meeting(tower) and Game.coins == c0 - Data.TOWER_MEETING_COST, "meeting costs coins")
	check(Game.mood.size() == mood_before + 1, "meeting lifts the mood")
	check(Game.tower_cooldown(tower, true) > 0, "meeting starts its own cooldown")
	Game.demolish(tower)

	# ------------------------------------------------ new roads, hotels, buses, metro, see-through towers
	for t in Data.ROAD_ORDER:
		check(Data.ROADS.has(t) and Ground.ROAD_IDS.has(t), "road type %s drawn by the ground shader" % t)
	check(Data.ROAD_ORDER.size() >= 7, "three new road types")
	city.hud._set_cat("hotel")
	await get_tree().process_frame
	var cards: int = city.hud.build_cards.get_children().filter(func(n): return not n.is_queued_for_deletion()).size()
	check(cards == 1 + Data.HOTELS.size(), "hotels window: a note and five hotel cards (%d)" % cards)
	# bike lanes bring cyclists out
	var saved_roads := Game.roads.duplicate()
	for rc in Game.roads:
		Game.roads[rc] = "bike"
	Game.phase = "day"
	Game.weather = "clear"
	for k in 5:
		city.life._update_cyclists()
	check(city.life.cyclists.size() > 0, "cyclists ride on bike lanes (%d)" % city.life.cyclists.size())
	if city.life.cyclists.size() > 0:
		var cy: Cyclist = city.life.cyclists[0]
		var p0 := cy.g
		for k in 10:
			cy.step(0.1)
		check(cy.g != p0 or cy.done, "a cyclist moves along the street")
	Game.roads = saved_roads
	check(Data.B.has("sport_tower") and Data.B.sport_tower.svc == "sport", "sports tower is a sports service")
	city.hud._set_cat("home")
	city.start_road()
	check(city.hud.road_types.get_child_count() == Data.ROAD_ORDER.size() + 1, "road bar lists every road type")
	city.set_tool("water")
	check(city.hud.road_types.get_child_count() == 2 and city.hud.tool_tabs.visible, "water tool: dig and fill in")
	city.cancel_mode()
	check(Assets.units().props.has("lamp_lantern"), "third street lamp style")
	for hid in ["house_american", "house_tajik", "house_asian", "dacha", "sky_villa"]:
		check(Data.ORDER.has(hid) and Data.B[hid].cat == "home", "new home type " + hid)
	check(Data.NEWS.size() > 0 and Data.NEWS_VERSION != "", "what's new list for this update")
	Game.settings["news"] = ""
	city.hud.panels.whats_new()
	check(Game.settings.news == Data.NEWS_VERSION and city.hud.modal.visible, "what's new window shows once")
	city.hud.close_modal()
	check(city.has_method("quit_game"), "the game can be quit from the menu")

	# ------------------------------------------------ interface size (settings)
	var csz0 := get_window().content_scale_size
	get_window().content_scale_size = Vector2i(1600, 720)   # a phone-shaped screen (the headless window is square)
	get_window().content_scale_aspect = Window.CONTENT_SCALE_ASPECT_IGNORE
	city.hud._fit()
	print("ui viewport %s, base scale %.2f, max step %.2f" % [get_viewport().get_visible_rect().size, city.hud.S, city.hud.max_ui_scale()])
	var hud_s: float = city.hud.S
	check(is_equal_approx(city.hud.ui_scale(), 1.0), "interface size starts at 100%")
	city.hud.step_ui_scale(1)
	check(Game.settings.ui_scale > 1.0 and city.hud.S > hud_s and city.hud.root.size.y < city.hud.get_viewport().get_visible_rect().size.y / hud_s,
		"bigger interface: buttons and icons grow (%.2f -> %.2f)" % [hud_s, city.hud.S])
	for i in 10:
		city.hud.step_ui_scale(1)
	check(is_equal_approx(city.hud.ui_scale(), city.hud.max_ui_scale()) and city.hud.ui_scale() > 1.0
		and city.hud.root.size.y >= city.hud.MIN_UI_H - 0.5 and city.hud.root.size.x >= city.hud.MIN_UI_W - 0.5,
		"interface size stops at the largest step that fits (%d%%)" % roundi(city.hud.ui_scale() * 100.0))
	for i in 20:
		city.hud.step_ui_scale(-1)
	check(is_equal_approx(city.hud.ui_scale(), city.hud.UI_SCALES[0]) and city.hud.S < hud_s, "interface can be made smaller")
	city.hud.panels.settings()
	check(city.hud.modal.visible, "settings window opens with the size control")
	city.hud.close_modal()
	city.hud.step_ui_scale(3)
	Game.save_game()
	Game.settings.ui_scale = 1.0
	Game.load_game()
	check(is_equal_approx(city.hud.ui_scale(), city.hud.UI_SCALES[3]), "interface size is saved (%.2f)" % city.hud.ui_scale())
	Game.set_setting("ui_scale", 1.0)
	city.hud._fit()
	check(is_equal_approx(city.hud.S, hud_s), "interface back to normal size")
	get_window().content_scale_size = csz0
	get_window().content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
	city.hud._fit()

	# ------------------------------------------------ water, bridges, walls, street decoration
	Game.coins = 999999
	var free_land: Array[Vector2i] = []
	for yy in range(c - 12, c + 12):
		for xx in range(c - 12, c + 12):
			var t := Vector2i(xx, yy)
			if Game.is_owned(t) and not Game.occ.has(t) and not Game.roads.has(t):
				free_land.append(t)
	var line: Array[Vector2i] = []
	var road_tile: Vector2i = Game.roads.keys()[0]
	var house_tile: Vector2i = Game.occ.keys()[0]
	line.append(road_tile)
	line.append(house_tile)
	line.append(free_land[0])
	check(Game.dig_water(line), "water dug")
	check(Game.water.has(road_tile) and Game.roads.has(road_tile), "a river over a road becomes a bridge")
	check(not Game.water.has(house_tile), "water flows around houses, not over them")
	check(Game.water_kind(free_land[0]) == 1, "a little water is a river")
	check(Game.place_problem("bakery", free_land[0].x, free_land[0].y) != "", "no building on the water")
	var lake: Array[Vector2i] = []
	for t in free_land:
		if lake.size() < Data.WATER_OCEAN:
			lake.append(t)
	Game.dig_water(lake)
	var biggest := 0
	for t in Game.water:
		biggest = maxi(biggest, Game.water_kind(t))
	check(biggest >= 2, "joined water grows into a sea or an ocean (%d)" % biggest)
	city.water_life.refresh()
	check(city.water_life.agents.size() > 0, "boats, ducks or gulls on the water (%d)" % city.water_life.agents.size())
	Game.save_game()
	var wn := Game.water.size()
	Game.load_game()
	check(Game.water.size() == wn, "water saved and loaded")
	var all_water: Array[Vector2i] = []
	all_water.assign(Game.water.keys())
	Game.fill_water(all_water)
	check(Game.water.is_empty(), "water filled in")
	var wall_line: Array[Vector2i] = [free_land[0], free_land[1]]
	check(Game.build_walls(wall_line, "stone") and Game.walls.size() == 2, "stone wall built")
	check(Game.place_problem("bakery", free_land[0].x, free_land[0].y) != "", "no building on a wall")
	check(Game.remove_walls(wall_line) and Game.walls.is_empty(), "wall removed")
	# homes joined by walls make one quarter
	check(Data.WALL_ORDER.has("plaster") and Data.WALL_ORDER.has("arch") and int(Data.WALLS.arch.block) > 0, "quarter wall and arch passage in the wall list")
	var qx := Vector2i(-1, -1)
	for t in free_land:
		var ok := true
		for i in 5:
			if not free_land.has(t + Vector2i(i, 0)):
				ok = false
		if ok and Game.place_problem("house_small", t.x, t.y) == "" and Game.place_problem("house_small", t.x + 2, t.y) == "" \
				and Game.place_problem("house_small", t.x + 4, t.y) == "":
			qx = t
			break
	check(qx.x >= 0, "room for three little houses in a row")
	if qx.x >= 0:
		var qh: Array[int] = []
		for i in 3:
			qh.append(Game.place("house_small", qx.x + i * 2, qx.y))
		Game.simulate(11.0)
		check(qh.all(func(u): return u > 0 and Game.buildings[u].built), "three houses built for a quarter")
		check(not Game.quarter_of.has(qh[0]), "houses apart are not a quarter")
		var arch_line: Array[Vector2i] = [qx + Vector2i(1, 0)]
		check(Game.build_walls(arch_line, "arch"), "arch passage built between two houses")
		check(Game.quarter_of.has(qh[0]) and Game.quarter_of.has(qh[1]) and int(Game.quarter_of[qh[0]].homes) == 2, "the wall joins two houses into one quarter")
		check(int(Game.quarter_of[qh[0]].happy) == 2 + int(Data.WALLS.arch.block), "a quarter with an arch is happier (%d)" % int(Game.quarter_of[qh[0]].happy))
		check(not Game.quarter_of.has(qh[2]), "the third house is not in it yet")
		if Game.home_reasons.has(qh[0]):
			check(Game.home_reasons[qh[0]].any(func(r): return r[0] == "r_quarter"), "mood shows the quarter")
		var plaster_line: Array[Vector2i] = [qx + Vector2i(3, 0)]
		check(Game.build_walls(plaster_line, "plaster"), "quarter wall built")
		check(int(Game.quarter_of.get(qh[2], {}).get("homes", 0)) == 3 and int(Game.quarter_of[qh[0]].homes) == 3, "the middle house carries the quarter on to the third")
		city.street_props.refresh()
		var wp = city.street_props.pieces.get("w%s" % (qx + Vector2i(1, 0)))
		check(wp != null and wp.touch == 10 and wp.arms == 10, "the arch runs into the houses on both sides")
		Game.save_game()
		Game.load_game()
		check(int(Game.quarter_of.get(qh[1], {}).get("homes", 0)) == 3, "quarter kept after loading")
		check(Game.remove_walls(arch_line) and not Game.quarter_of.has(qh[0]) and int(Game.quarter_of[qh[1]].homes) == 2, "removing the arch splits the quarter")
		Game.remove_walls(plaster_line)
		check(Game.quarter_of.is_empty(), "no walls, no quarter")
		for u in qh:
			Game.demolish(u)
	var deco_line: Array[Vector2i] = [road_tile]
	check(Game.decorate_roads(deco_line, "planters") and Game.road_deco.has(road_tile), "street decorated with flower pots")
	check(Game.decorate_roads(deco_line, "none") and Game.road_deco.is_empty(), "street decoration removed")
	check(Data.HOTELS.size() == 5 and Data.HOTELS.all(func(h): return Data.tab_of(h) == "hotel" and Data.B[h].get("highway", false)),
		"five hotels in their own tab, opened by the highway")
	Game.level = 30
	Game.coins = 999999
	Game.gems = 9999
	var spots: Array[Vector2i] = []
	for yy in range(c - 12, c + 12):
		for xx in range(c - 12, c + 12):
			if Game.place_problem("bus_stop", xx, yy) == "" and Game._touches_road(xx, yy, 1) and spots.size() < 4:
				var far := true
				for o in spots:
					if absi(o.x - xx) + absi(o.y - yy) < 3:
						far = false
				if far:
					spots.append(Vector2i(xx, yy))
	check(spots.size() == 4, "free spots by the roads for stops and stations (%d)" % spots.size())
	var gate_roads := {}
	for g in Data.gates():
		if Game.roads.has(g):
			gate_roads[g] = Game.roads[g]
			Game.roads.erase(g)
	check(not Game.is_connected_to_highway() and Game.place_problem("hotel_boutique", spots[0].x, spots[0].y) in ["need_highway", "bad_place"],
		"hotels closed without a road to the highway")
	var hotel_spot := ""
	var hx := Vector2i(-1, -1)
	for yy in range(c - 14, c + 14):
		for xx in range(c - 14, c + 14):
			if hx.x < 0 and Game.place_problem("hotel_boutique", xx, yy) == "need_highway":
				hx = Vector2i(xx, yy)
	check(hx.x >= 0, "a spot where only the highway is missing for a hotel")
	Game.roads[Data.gates()[0]] = "asphalt"
	check(Game.is_connected_to_highway() and Game.place_problem("hotel_boutique", hx.x, hx.y) == "", "hotels open once a road reaches the edge")
	Game.roads.erase(Data.gates()[0])
	for g in gate_roads:
		Game.roads[g] = gate_roads[g]
	var stops: Array[int] = []
	for k in 2:
		stops.append(Game._add_building("bus_stop", spots[k].x, spots[k].y, true))
	Game.recalc()
	check(Game.bus_stops().size() == 2 and Game.transit_fares() > 0, "two bus stops start a bus line with fares")
	var kinds := ["bus_stop_simple", "bus_stop_modern", "bus_stop_ad", "bus_stop_village"]
	check(kinds.all(func(k): return Data.B.has(k) and Data.B[k].svc == "bus" and Data.ORDER.has(k)), "four new kinds of bus stops")
	var tvk := ["tv_studio", "tv_center", "tv_tower"]
	check(tvk.all(func(k): return Data.B.has(k) and Data.B[k].svc == "tv" and Data.ORDER.has(k)), "three kinds of TV buildings")
	check(Data.B.tv_tower.radius > Data.B.tv_center.radius and Data.B.tv_center.radius > Data.B.tv_studio.radius, "a taller TV building reaches farther")
	var tvb := Game._add_building("tv_studio", spots[3].x, spots[3].y, true)
	Game.recalc()
	check(Game.has_service("tv") and Game.covered_by("tv", spots[3]), "a TV studio covers its surroundings")
	Game.demolish(tvb)
	Game.recalc()
	var nws := ["newsstand", "newspaper"]
	check(nws.all(func(k): return Data.B.has(k) and Data.B[k].svc == "news" and Data.ORDER.has(k)), "newsstand and newspaper office exist")
	var nb := Game._add_building("newsstand", spots[3].x, spots[3].y, true)
	Game.recalc()
	check(Game.covered_by("news", spots[3]), "a newsstand covers its surroundings")
	Game.demolish(nb)
	var hl: Array = Game.paper_headlines()
	check(not hl.is_empty() and hl.all(func(k): return Loc.t(k) != k), "paper headlines all have texts")
	var old_coins := Game.coins
	Game.coins = 100000
	check(Game.paper_headlines().has("n_rich"), "paper reports a full treasury")
	Game.coins = old_coins
	var fb := Game._add_building("house_small", spots[3].x, spots[3].y, true)
	Game.buildings[fb].fire = 5.0
	check(Game.paper_headlines()[0] == "n_fire", "paper puts a fire on the front page")
	Game.demolish(fb)
	Game.recalc()
	var mixed := Game._add_building("bus_stop_village", spots[3].x, spots[3].y, true)
	Game.recalc()
	check(Game.bus_stops().has(mixed) and Game.bus_stops().size() == 3, "a village stop joins the same bus line")
	Game.demolish(mixed)
	Game.recalc()
	city.life._update_buses()
	check(city.life.cars.any(func(car): return is_instance_valid(car) and car.role == "city_bus"), "a city bus drives between the stops")
	# ---- garbage
	var gpop := Game.pop
	Game.pop = 1000
	Game.garbage = 0.0
	Game._update_garbage()
	check(is_equal_approx(Game.garbage, 40.0), "residents make garbage (%.1f)" % Game.garbage)
	Game.garbage = 90.0
	Game.recalc()
	Game.pop = 1000
	Game._check_rules()
	check(Game.rules.get("garbage", false) and Game.garbage_mood() > 0, "a big pile breaks the garbage rule and costs mood")
	check(Game.paper_headlines().has("n_garbage") and Loc.t("n_garbage") != "n_garbage", "paper reports the garbage")
	var gd := Game._add_building("garbage_depot", spots[3].x, spots[3].y, true)
	Game.recalc()
	if Game.garbage_depots().has(gd):
		check(Game.garbage_capacity() >= 12, "a working depot has capacity")
		Game.garbage = 50.0
		Game.pop = 100
		Game._update_garbage()
		check(Game.garbage < 50.0, "a depot carries garbage away")
		for _try in 6:
			city.life._garb_hour = -1
			city.life._update_garbage_trucks()
		check(city.life.cars.any(func(car): return is_instance_valid(car) and car.kind == "garbage"), "a garbage truck leaves the depot")
	else:
		check(true, "depot has no road here (skipped truck check)")
	Game.demolish(gd)
	Game.pop = gpop
	Game.garbage = 0.0
	Game.recalc()
	check(Data.B.has("recycling_plant") and Data.ORDER.has("recycling_plant"), "recycling plant is in the build list")
	for mid in ["market_stall", "market", "bazaar"]:
		check(Data.B.has(mid) and Data.ORDER.has(mid) and Data.B[mid].cat == "shop" and Data.B[mid].income > 0, "%s is a shop in the list" % mid)
		var mb := Game._add_building(mid, spots[3].x, spots[3].y, true)
		check(mb != 0 and Game.buildings.has(mb), "%s can be placed" % mid)
		if mb != 0:
			Game.demolish(mb)
	Game.recalc()
	# cafes and fast food: each kind is a working shop with its own sprite, residents eat there
	for fid in ["coffee_kiosk", "shawarma", "donut_shop", "burger_bar", "food_trucks", "chaikhana", "drive_thru"]:
		check(Data.B.has(fid) and Data.ORDER.has(fid) and Data.B[fid].cat == "shop" and Data.B[fid].income > 0, "%s is a shop in the list" % fid)
		check(FileAccess.file_exists("res://assets/buildings/%s_1_0.png" % fid) and FileAccess.file_exists("res://assets/buildings/%s_3_3.png" % fid), "%s has its own sprites" % fid)
		var food_b := Game._add_building(fid, spots[3].x, spots[3].y, true)
		check(food_b != 0 and Game.buildings.has(food_b), "%s can be placed" % fid)
		if food_b != 0:
			Game.demolish(food_b)
	# new filling stations: each is a working shop with its own sprite, open around the clock, the old one stays
	check(Data.B.has("gas_station") and Data.ORDER.has("gas_station"), "the old gas station is still there")
	for gid in ["ev_station", "gas_highway"]:
		check(Data.B.has(gid) and Data.ORDER.has(gid) and Data.B[gid].cat == "shop" and Data.B[gid].income > 0, "%s is a shop in the list" % gid)
		check(FileAccess.file_exists("res://assets/buildings/%s_1_0.png" % gid) and FileAccess.file_exists("res://assets/buildings/%s_3_3.png" % gid), "%s has its own sprites" % gid)
		check(Life.SHOPS.has(gid), "residents refuel at %s" % gid)
		var fuel_b := Game._add_building(gid, spots[3].x, spots[3].y, true)
		check(fuel_b != 0 and Game.buildings.has(fuel_b), "%s can be placed" % gid)
		if fuel_b != 0:
			Game.demolish(fuel_b)
	# new farm buildings: each one produces goods in the farm zone and has its own sprite
	for fid in ["apiary", "chicken_farm", "melon_field", "vineyard", "windmill", "fish_farm", "dairy"]:
		check(Data.B.has(fid) and Data.ORDER.has(fid) and Data.B[fid].cat == "ind" and Data.B[fid].out > 0 and Data.B[fid].zones == ["farm"], "%s is a farm building in the list" % fid)
		check(FileAccess.file_exists("res://assets/buildings/%s_1_0.png" % fid) and FileAccess.file_exists("res://assets/buildings/%s_3_3.png" % fid), "%s has its own sprites" % fid)
		check(Game.place_problem(fid, c - 4, c + 2) == "wrong_zone", "%s is not allowed in the city zone" % fid)
		var farm_b := Game._add_building(fid, c + 10, c - 6, true)
		check(farm_b != 0 and Game.buildings.has(farm_b), "%s can be placed in farmland" % fid)
		if farm_b != 0:
			Game.demolish(farm_b)
	# new kinds of trees: decoration with their own sprites, and they grow in the wild too
	for tid in ["tree_birch", "tree_pine", "tree_poplar", "tree_apple", "tree_autumn", "tree_willow", "tree_sakura", "tree_palm", "tree_chinar"]:
		check(Data.B.has(tid) and Data.ORDER.has(tid) and Data.B[tid].cat == "decor" and int(Data.B[tid].size) == 1 and Data.B[tid].happy > 0, "%s is a tree in the decor list" % tid)
		check(FileAccess.file_exists("res://assets/buildings/%s_1_0.png" % tid) and FileAccess.file_exists("res://assets/buildings/%s_3_3.png" % tid), "%s has its own sprites" % tid)
		var tree_b := Game._add_building(tid, c - 4, c + 2, true)
		check(tree_b != 0 and Game.buildings.has(tree_b), "%s can be placed in the city" % tid)
		if tree_b != 0:
			Game.demolish(tree_b)
	check(Data.B.tree_palm.zones.has("beach"), "palms can stand on the beach")
	var wild := {}
	for k in Game.natural_trees.values():
		wild[k] = true
	check(range(Scenery.SINGLES).all(func(i): return not Assets.nature("tree_%d" % i).is_empty() and FileAccess.file_exists("res://assets/nature/tree_%d.png" % i)), "every wild tree kind has a sprite")
	check(wild.has("tree_8") and wild.has("tree_%d" % (Scenery.SINGLES - 1)), "new kinds of trees grow in the wild")
	Game.recalc()
	check(Data.PRIVATE_KINDS.all(func(k): return Data.B.has(k) and int(Data.B[k].size) == 1), "residents propose only small businesses")
	check(Data.beach_seg(Vector2i(75, 100)) == 2 and Data.beach_seg(Vector2i(80, 100)) == -1 and Data.zone_at(Vector2i(75, 100)) == "beach", "beach tiles map to segments")
	Game.beach = []
	check(not Game.is_owned(Vector2i(75, 100)) and Game.beach_buyable(3) == Game.plots.has(Vector2i(0, 3)), "beach is not owned at the start")
	Game.plots.append(Vector2i(0, 2))
	Game.coins = 100000
	Game.level = 20
	check(Game.beach_buyable(2) and Game.buy_beach(2, false) and Game.is_owned(Vector2i(75, 100)), "beach segment can be bought")
	check(Game.beach_buyable(3) and not Game.beach_buyable(5), "beach is bought segment by segment")
	for bid in ["beach_umbrella", "lifeguard_tower", "beach_bar"]:
		check(Data.B.has(bid) and Data.ORDER.has(bid), "%s is in the build list" % bid)
		check(Game.place_problem(bid, 74, 101) == "", "%s can be placed on the bought beach" % bid)
		check(Game.place_problem(bid, 74, 121) != "", "%s cannot be placed on unbought beach" % bid)
	check(Game.place_problem("house_small", 74, 101) == "wrong_zone", "homes cannot be built on the beach")
	var bb := Game._add_building("beach_bar", 74, 101, true)
	check(bb != 0 and Game.buildings.has(bb), "beach bar can be built")
	if bb != 0:
		Game.demolish(bb)
	Game.beach = []
	Game.plots.erase(Vector2i(0, 2))
	# airport: routes are bought in the airport, planes bring travellers, analytics by country
	check(Data.B.has("airport") and Data.ORDER.has("airport") and Data.B.airport.get("unique", false) and Data.B.airport.svc == "airport", "airport is a unique service in the list")
	check(Data.COUNTRY_ORDER.size() == Data.COUNTRIES.size() and Data.COUNTRY_ORDER.size() >= 12, "airport has routes to many countries")
	check(Data.COUNTRY_ORDER.all(func(k): return Data.COUNTRIES[k].flag.size() == 3 and int(Data.COUNTRIES[k].pax) > 0), "every country has a flag and travellers")
	Game.flights = []
	Game.arrivals = {}
	Game.arrivals_day = {}
	Game.coins = 100000
	Game.level = 20
	check(not Game.buy_flight("russia") and Game.flights.is_empty(), "no flights without an airport")
	var ap := Game._add_building("airport", 90, 90, true)
	check(Game.place_problem("airport", spots[3].x, spots[3].y) == "already_built", "only one airport per city")
	var ac0 := Game.coins
	check(Game.buy_flight("russia") and Game.flights.has("russia") and Game.coins == ac0 - int(Data.COUNTRIES.russia.cost), "flight route can be bought")
	check(not Game.buy_flight("russia") and not Game.buy_flight("usa"), "a route is bought once and needs its level")
	Game.road_ok[ap] = true
	check(Game.airport_uid() == ap, "working airport found")
	var c1 := Game.coins
	var pax := Game.land_flight("russia")
	check(pax > 0 and Game.coins > c1, "plane brings %d travellers who spend money" % pax)
	check(Game.land_flight("turkey") == 0, "no planes from routes not bought")
	Game.buy_flight("turkey")
	var pax2 := Game.land_flight("turkey")
	check(Game.arrivals_total() == pax + pax2 and Game.arrivals_total(true) == pax + pax2, "arrivals are counted")
	var stt: Array = Game.arrival_stats()
	check(stt.size() == 2 and stt[0][1] >= stt[1][1] and int(Game.arrivals[stt[0][0]]) == stt[0][1], "analytics by country, most first")
	var sd := Game.to_dict()
	check(sd.flights.has("turkey") and int(sd.arrivals.russia) == pax and int(sd.arrivals_day.turkey) == pax2, "routes and arrivals are saved")
	check(Game.paper_headlines().has("n_flights"), "the paper writes about the airport")
	city.hud.panels.airport()
	check(city.hud.modal.visible and city.hud.modal_box.get_child_count() > 2, "airport window opens with analytics")
	city.hud.close_modal()
	city.life._on_plane_landed("turkey", pax2)
	check(city.world.get_children().any(func(n): return n is PlaneView), "a plane flies in to the airport")
	Game.demolish(ap)
	Game.flights = []
	Game.arrivals = {}
	Game.arrivals_day = {}
	Game.recalc()
	for sid in ["site_small", "site_house", "site_crane"]:
		check(Data.B.has(sid) and Data.ORDER.has(sid) and Data.B[sid].cat == "decor", "%s is a decor building in the list" % sid)
		var sb := Game._add_building(sid, spots[3].x, spots[3].y, true)
		check(sb != 0 and Game.buildings.has(sb), "%s can be placed" % sid)
		if sb != 0:
			Game.demolish(sb)
	Game.recalc()
	var st1 := Game._add_building("metro_station", spots[2].x, spots[2].y, true)
	Game.recalc()
	check(not Game.metro_open(), "one metro station is not a line yet")
	var fares1 := Game.transit_fares()
	var st2 := Game._add_building("metro_station", spots[3].x, spots[3].y, true)
	Game.recalc()
	city.metro.refresh()
	check(Game.metro_open() and Game.transit_fares() > fares1, "two stations open the metro")
	check(city.metro.points.size() == 2 and city.metro.visible, "the train runs underground between the stations")
	var tall := Game._add_building("twin_towers", c + 20, c + 20, true)
	city._add_view(tall)
	var tv: BuildingView = city.views[tall]
	check(tv.is_tall(), "skybridge twins count as a tall building")
	city.set_xray(true)
	check(tv.faded(), "see-through mode fades tall buildings")
	city.set_xray(false)
	check(not tv.faded(), "see-through mode off")
	check(Game.place_problem("dushanbe_home", hx.x, hx.y) == "need_landmark", "district homes need the Dushanbe Tower")
	var landmark := Game._add_building("dushanbe_tower", hx.x + 3, hx.y, true)
	check(Game.place_problem("dushanbe_tower", c + 30, c - 30) == "already_built", "Dushanbe Tower can be built only once")
	check(Game.place_problem("dushanbe_home", hx.x, hx.y) == "", "district homes allowed once the tower stands")
	var b0 := Game.landmark_bonus()
	var hp := hx
	for yy in range(hx.y - 12, hx.y + 12):
		for xx in range(hx.x - 12, hx.x + 12):
			if hp == hx and Game.place_problem("dushanbe_home", xx, yy) == "" and Game._touches_road(xx, yy, 2):
				hp = Vector2i(xx, yy)
	var dh := Game._add_building("dushanbe_home", hp.x, hp.y, true)
	check(Game.landmark_bonus() > b0, "every district home raises the tower's income")
	Game.recalc()
	check(Game.home_reasons.get(dh, []).any(func(r): return r[0] == "r_landmark"), "homes near the tower are happier")
	Game.demolish(dh)
	Game.demolish(landmark)
	for uid in [stops[0], stops[1], st1, st2, tall]:
		Game.demolish(uid)

	# ------------------------------------------------ animals and zoo
	Game.level = 9
	check(Game.place_problem("zoo", Data.LAND0 + 16, Data.LAND0 + 24) != "", "zoo needs animals and owned leisure land")
	Game.caught = ["deer", "fox", "rabbit", "boar", "wolf"]
	Game.plots.append(Vector2i(1, 3))
	var zp := "no free spot"
	for yy in range(Data.LAND0 + 30, Data.LAND0 + 38):
		for xx in range(Data.LAND0 + 10, Data.LAND0 + 18):
			if zp != "":
				zp = Game.place_problem("zoo", xx, yy)
	check(zp == "", "zoo allowed with 5 animals in leisure zone (%s)" % zp)

	# ------------------------------------------------ events
	Game.level = 5
	Events._proposal()
	var prop: Dictionary = Events.inbox[0]
	check(prop.kind == "proposal", "business proposal arrives")
	var n_before := Game.buildings.size()
	Events.resolve(int(prop.id), 0)
	check(Game.buildings.size() == n_before + 1, "accepted proposal opens a private business")
	var priv := 0
	for uid in Game.buildings:
		if Game.buildings[uid].priv != "":
			priv = uid
	Game.simulate(100.0)
	Game.today = Game._empty_day()
	Game.day_time = 0.999
	Game._advance_time(2.0)
	check(int(Game.ledger[-1]["in"].get("taxes", 0)) > 0, "private business pays daily tax")
	Events._violation()
	var v: Dictionary = Events.inbox[0]
	check(v.kind == "violation", "violation letter arrives")
	c0 = Game.coins
	Events.resolve(int(v.id), 0)
	check(Game.coins == c0 + int(v.fine), "fine collected")
	Events._violation()
	v = Events.inbox[0]
	Events.resolve(int(v.id), 1)
	check(Game.buildings[int(v.uid)].closed, "inspection closes the business")
	Game.coins = 50000
	var fire_target: int = Game.buildings.keys()[2]
	Events.start_fire(fire_target)
	check(Game.buildings[fire_target].dmg and Game.buildings[fire_target].fire > 0.0, "fire without a station damages the building")
	check(Game.repair(fire_target) and not Game.buildings[fire_target].dmg, "damaged building repaired")

	# ------------------------------------------------ story & election
	Events.chapter = 0
	Events._check_story()
	check(Events.chapter == 1 and Events.story.size() >= 1, "story begins with Boris")
	Events.chapter = 7
	Game.level = 9
	Game.day = 15
	Events._check_story()
	check(Events.chapter == 8 and Events.election_day == 19, "election announced")
	Game.rep = 80
	Game.happy = 75
	Events.on_day(19)
	check(Events.flags.get("election_done", false) and not Game.lost, "election won with good ratings")

	# ------------------------------------------------ save / load / backup code
	Game.save_game()
	var coins_saved := Game.coins
	var b_saved := Game.buildings.size()
	Game.coins = 1
	check(Game.load_game() and Game.coins == coins_saved and Game.buildings.size() == b_saved, "save and load round trip")
	var code := Game.export_code()
	check(code.begins_with("PXB4:") and code.length() > 100, "backup code exported (%d chars)" % code.length())
	Game.coins = 7
	check(Game.import_code(code) and Game.coins == coins_saved, "backup code restores the city")
	check(not Game.import_code("garbage"), "bad code rejected")

	# ------------------------------------------------ life
	await get_tree().create_timer(1.0).timeout
	check(city.life.persons.size() > 0, "residents created (%d)" % city.life.persons.size())
	check(city.life.cars.size() > 0, "cars in town (%d)" % city.life.cars.size())
	var dv: BuildingView = null
	for uid in city.views:
		if city.views[uid].door.has_opening():
			dv = city.views[uid]
			break
	check(dv != null, "buildings have doors that open")
	if dv:
		var dr: DoorView = dv.door
		dv.open_door(1.4)
		dr.step(0.2, 1.0)
		dr.step(0.2, 1.0)
		check(dr.visible and dr.angle > 1.2 and dr.inward.y < 0.0, "door leaf swings into the house (%.2f rad)" % dr.angle)
		check(dr._clip(PackedVector2Array([dr.a, dr.b, dr.b + dr.up, dr.a + dr.up])).size() == 1, "room is drawn inside the opening")
		dr.step(0.55, 1.0)
		dr.step(0.15, 1.0)
		check(dr.angle > 0.0 and dr.angle < DoorView.MAX_ANGLE * 0.9, "door closes slowly (%.2f rad)" % dr.angle)
		dr.step(0.5, 1.0)
		check(not dr.visible and dr.angle == 0.0, "door shut again")

	# ------------------------------------------------ multi-storey car parks
	for pid in ["parking_deck", "parking_tower", "parking_green", "parking_spiral"]:
		check(Data.B.has(pid) and Data.ORDER.has(pid) and Data.B[pid].svc == "parking" and int(Data.B[pid].park) > 0, "%s is a car park in the list" % pid)
		check(FileAccess.file_exists("res://assets/buildings/%s_1_0.png" % pid) and FileAccess.file_exists("res://assets/buildings/%s_3_3.png" % pid), "%s has its own sprites" % pid)
	check(Data.B.has("parking") and not Data.B.parking.has("park"), "the old open car park stays as it was")
	check(Data.stat("parking_spiral", "park", 3) > Data.stat("parking_spiral", "park", 1), "car park holds more cars at a higher level")
	var lf: Life = city.life
	var gpos := Vector2i(-1, -1)
	for yy in range(c - 14, c + 14):
		for xx in range(c - 14, c + 14):
			if gpos.x < 0 and Game.place_problem("parking_deck", xx, yy) == "" and Game._touches_road(xx, yy, 2):
				var probe := Game._add_building("parking_deck", xx, yy, true)
				Game.recalc()
				if probe != 0 and lf.garage_spots(probe).is_empty():
					Game.demolish(probe)
				elif probe != 0:
					gpos = Vector2i(xx, yy)
					Game.demolish(probe)
	var gar := Game._add_building("parking_deck", gpos.x, gpos.y, true) if gpos.x >= 0 else 0
	check(gar != 0, "car park can be placed by a road")
	if gar != 0:
		Game.recalc()
		lf.buildings_changed()
		var gsp := lf.garage_spots(gar)
		check(gsp.size() == Life.garage_capacity(gar) and gsp.size() == int(Data.B.parking_deck.park), "car park has %d places" % gsp.size())
		check(gsp.size() > 1 and lf._spot_by_key(gsp[1][0]) == gsp[1], "car park places are found by their key")
		var gacc := lf._sidewalk_access(gar)
		check(lf.spot_sidewalk(gsp[0]).tile == gacc.tile, "drivers walk out of the car park gate")
		# a car inside is out of sight and counted in the card
		var gcar := lf._make_car("sedan")
		gcar.park_at(gsp[0])
		lf.spots[gsp[0][0]] = gcar
		check(not gcar.visible and lf.garage_used(gar) == 1, "car parked inside the car park is hidden (%d inside)" % lf.garage_used(gar))
		check(gcar.door_point().distance_to(Game.entry_point(gar)) < 2.5, "driver gets in at the car park door")
		# streets around full: a resident's car goes to the car park
		var blocker := lf._make_car("hatch")
		var blocked: Array = []
		for dy in range(-3, 4):
			for dx in range(-3, 4):
				for sp in lf.spots_of(gacc.tile + Vector2i(dx, dy)):
					if not lf.spots.has(sp[0]):
						lf.spots[sp[0]] = blocker
						blocked.append(sp[0])
		var fsp := lf.find_spot(gar, null)
		check(fsp.size() > 4 and fsp[3] == gar and fsp[0] != gsp[0][0], "with the street full a car gets a free place in the car park")
		for k in blocked:
			lf.spots.erase(k)
		# a car drives in from down the road and disappears inside
		var gtile := lf._spot_tile(gsp[1][0])
		var gbefore: Vector2i = gtile - Vector2i(gsp[1][2])
		var from := Vector2i(-1, -1)
		for t in Game.net:
			var md := absi(t.x - gtile.x) + absi(t.y - gtile.y)
			if from.x < 0 and md >= 3 and md <= 8 and lf.car_path(t, gbefore).size() > 1:
				from = t
		var incar := lf._make_car("suv")
		var started := from.x >= 0 and incar.drive_to_spot(gsp[1], from)
		check(started, "car sets off to the car park")
		if started:
			lf.spots[gsp[1][0]] = incar
			# run the traffic like Life._process does, in 0.05 s steps
			for i in 3600:
				if incar.state == "parked":
					break
				lf._rebuild_bins()
				if i % 10 == 0:
					lf._update_lights()
				for car in lf.cars:
					if is_instance_valid(car) and car.moving():
						car.drive(0.05)
			check(incar.state == "parked" and incar.spot == gsp[1] and not incar.visible, "car drove into the car park and parked inside (%s)" % incar.state)
		# and drives out again
		var out := lf.car_path(gtile, from if from.x >= 0 else gbefore)
		if out.size() > 1:
			gcar.start_route(out, null)
			check(gcar.state == "unparking" and gcar.visible and gcar.modulate.a < 0.1, "car comes out of the car park gate")
			for i in 40:
				gcar.drive(0.05)
			check(gcar.state == "driving" and gcar.modulate.a == 1.0, "car is back on the street")
			lf.spots.erase(gsp[0][0])
		Game.demolish(gar)
		check(lf.garage_used(gar) == 0 and (not is_instance_valid(incar) or incar.state == "gone"), "cars leave a car park that was pulled down")
		blocker.queue_free()

	# ------------------------------------------------ losing
	Game.peak_pop = 200
	for uid in Game.buildings:
		if Data.B[Game.buildings[uid].id].cat == "home":
			Game.buildings[uid].occ = 0
	Game.recalc()
	Game.happy = 0.0
	Game._check_lose()
	check(Game.lost, "losing when happiness is 0 and residents left")

	print("\n%s: %d failed" % ["DONE" if fails == 0 else "FAILURES", fails])
	get_tree().quit(fails)
