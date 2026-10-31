extends Node
## Dev only: runs the residents simulation for many days on a bare city and prints the numbers (balance check).

func _ready() -> void:
	Events.reset()
	Game.new_game()
	var c := Data.CENTER
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	for i in 12:
		var uid := Game._add_building(["house_small", "house_brick", "cottage"][i % 3], c - 8 + i * 2, c - 3, true, 2)
		Game.buildings[uid].occ = 10
	for id in ["hospital", "school", "it_run", "farm"]:
		Game._add_building(id, c + rng.randi_range(-6, 6), c + 4, true, 2)
	for i in 14:
		Game.roads[Vector2i(c - 10 + i * 2, c - 1)] = 3
	Game.recalc()
	print("pop ", Game.pop, " jobs ", Game.jobs)
	var cz: Citizens = Game.cz
	Game.coins = 100000
	for d in 5:
		Game._end_of_day()
	print("LEDGER ", Game.ledger[-1])
	for d in 160:
		Game.day += 1
		Game._move_population()
		Game.recalc()
		cz.on_day()
		if d % 20 == 19:
			var s := cz.summary()
			print("day ", Game.day, " pop ", Game.pop, " n ", s.n, " wallet/avg ", int(s.wallet / maxf(1, s.n)), " jobless ", s.jobless, "/", s.adults,
				" sick ", s.sick, " births ", cz.stats.births, " deaths ", cz.stats.deaths, " ", cz.stats.causes, " util ", cz.last_util, " edu ", s.edu)
	get_tree().quit()
