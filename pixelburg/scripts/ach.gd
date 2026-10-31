class_name Ach
extends RefCounted
## Achievements (ROADMAP 30): ~50 goals across the game, most with several tiers.
## The state lives in Game.ach: {"got": {id: tiers earned}, "streak", "last", "pending", "logins", "best"}.

## id, counter key, name, text with %s for the target, tier targets, reward weight
const LIST := [
	["builder", "built", ["Строитель", "Builder"], ["Построй зданий: %s", "Build %s buildings"], [10, 40, 120, 300], 1],
	["homes", "homes", ["Домовладелец", "Home maker"], ["Построй жилых домов: %s", "Build %s homes"], [5, 20, 60], 1],
	["shops", "shops", ["Торговец", "Shopkeeper"], ["Построй магазинов и кафе: %s", "Build %s shops and cafes"], [5, 20, 60], 1],
	["services", "services", ["Городские службы", "City services"], ["Построй служб: %s", "Build %s city services"], [5, 15, 40], 1],
	["industry", "ind", ["Промышленник", "Industrialist"], ["Построй производств: %s", "Build %s production buildings"], [3, 10, 25], 1],
	["decor", "decor", ["Дизайнер", "Designer"], ["Поставь украшений: %s", "Place %s decorations"], [5, 25, 80], 1],
	["fun", "fun", ["Весельчак", "Fun maker"], ["Построй мест для отдыха: %s", "Build %s fun places"], [2, 6, 12], 1],
	["upgrader", "upgrades", ["Мастер улучшений", "Upgrader"], ["Улучши здания: %s раз", "Upgrade buildings %s times"], [10, 50, 200], 1],
	["towers", "lvl3", ["Высший уровень", "Top level"], ["Доведи зданий до 3 уровня: %s", "Get %s buildings to level 3"], [1, 8, 25], 2],
	["pop", "pop", ["Население", "Population"], ["Достигни населения: %s", "Reach a population of %s"], [100, 500, 2000, 8000], 1],
	["level", "level", ["Опыт мэра", "Mayor's experience"], ["Достигни уровня: %s", "Reach level %s"], [5, 10, 20, 30], 1],
	["rich", "coins_total", ["Богач", "Tycoon"], ["Заработай монет за всё время: %s", "Earn %s coins in total"], [10000, 100000, 1000000, 10000000], 1],
	["goods", "goods_total", ["Производитель", "Producer"], ["Произведи товаров: %s", "Produce %s goods"], [500, 5000, 50000], 1],
	["savings", "deposit", ["Копилка", "Piggy bank"], ["Держи на вкладе: %s", "Keep %s in the deposit"], [1000, 20000], 1],
	["plots", "plots", ["Землевладелец", "Landowner"], ["Купи участков земли: %s", "Buy %s plots"], [3, 8, 16], 1],
	["roads", "roads", ["Дорожник", "Road builder"], ["Проложи дорог: %s клеток", "Lay %s road tiles"], [50, 200, 600], 1],
	["lights", "lights", ["Светофоры", "Traffic lights"], ["Поставь светофоров: %s", "Place %s traffic lights"], [1, 6, 20], 1],
	["rings", "rings", ["Круговое движение", "Roundabouts"], ["Построй колец: %s", "Build %s roundabouts"], [1, 4, 10], 1],
	["lamps", "lamps", ["Свет в городе", "City lights"], ["Поставь фонарей: %s", "Place %s street lamps"], [10, 50, 200], 1],
	["hlamps", "hlamps", ["Уютные крыльца", "Cosy porches"], ["Повесь фонарей над домами: %s", "Hang %s porch lamps"], [3, 20], 1],
	["paves", "paves", ["Плиточник", "Paver"], ["Выложи плитки: %s клеток", "Lay %s paving tiles"], [20, 100, 400], 1],
	["walls", "walls", ["Стены кварталов", "Quarter walls"], ["Построй стен: %s", "Build %s wall pieces"], [10, 40, 120], 1],
	["quarters", "quarters", ["Единый квартал", "One quarter"], ["Объедини кварталов стенами: %s", "Join %s quarters with walls"], [1, 4], 1],
	["water", "water", ["Речник", "Waterway"], ["Выкопай клеток воды: %s", "Dig %s water tiles"], [10, 60, 250], 1],
	["waterw", "waterw", ["Чистая вода", "Clean water"], ["Построй водоканалов: %s", "Build %s water plants"], [1, 3], 1],
	["power", "power", ["Энергетик", "Power engineer"], ["Построй электростанций и солнечных ферм: %s", "Build %s power plants or solar farms"], [1, 3, 8], 1],
	["beach", "beach", ["Пляжный сезон", "Beach season"], ["Купи участков пляжа: %s", "Buy %s beach segments"], [1, 4, 8], 1],
	["airport", "airport", ["Аэропорт", "Airport"], ["Построй аэропорт", "Build an airport"], [1], 3],
	["flights", "flights", ["Открытое небо", "Open skies"], ["Открой авиарейсов: %s", "Open %s flight routes"], [1, 4, 8], 1],
	["tourists", "arrivals", ["Гостеприимство", "Hospitality"], ["Прими туристов из других стран: %s", "Welcome %s travellers from abroad"], [100, 2000, 20000], 1],
	["bus", "bus", ["Общественный транспорт", "Public transport"], ["Построй остановок и станций: %s", "Build %s stops and stations"], [2, 6, 15], 1],
	["parking", "parking", ["Где припарковаться", "Parking spot"], ["Построй парковок: %s", "Build %s car parks"], [1, 4, 10], 1],
	["edu", "edu", ["Город знаний", "City of knowledge"], ["Построй школ и учебных центров: %s", "Build %s schools"], [1, 3, 6], 1],
	["health", "health", ["Здоровье города", "City health"], ["Построй больниц и клиник: %s", "Build %s hospitals and clinics"], [1, 3], 1],
	["culture", "culture", ["Культурный центр", "Culture hub"], ["Построй культурных зданий: %s", "Build %s cultural buildings"], [1, 2], 1],
	["sport", "sport", ["Спортивный город", "Sports town"], ["Построй спортивных зданий: %s", "Build %s sports buildings"], [1, 3], 1],
	["media", "media", ["Голос города", "Voice of the city"], ["Построй ТВ и газет: %s", "Build %s TV and newspaper buildings"], [1, 4, 8], 1],
	["garbage", "garbage", ["Чистый город", "Clean city"], ["Построй станций вывоза мусора: %s", "Build %s garbage stations"], [1, 3], 1],
	["fire", "fire", ["Пожарная безопасность", "Fire safety"], ["Построй пожарных станций: %s", "Build %s fire stations"], [1, 3], 1],
	["police", "police", ["Порядок", "Law and order"], ["Построй полиции и охраны: %s", "Build %s police and guard posts"], [1, 4], 1],
	["prison", "prison", ["За решётку", "Behind bars"], ["Построй тюрьму", "Build a prison"], [1], 2],
	["robbers", "robbers", ["Ловец грабителей", "Robber catcher"], ["Поймай грабителей банков: %s", "Catch %s bank robbers"], [1, 5, 15], 1],
	["darkside", "mayor_rob", ["Тёмная сторона", "The dark side"], ["Ограбь банк, будучи мэром", "Rob a bank as the mayor"], [1], 1],
	["jailed", "jailed", ["Отсидел своё", "Did your time"], ["Попади в тюрьму как мэр", "Go to prison as the mayor"], [1], 1],
	["protests", "protests", ["Голос народа", "Voice of the people"], ["Переживи митингов: %s", "Live through %s protests"], [1, 5, 12], 1],
	["talks", "talks", ["Умеет слушать", "Good listener"], ["Выслушай митингующих: %s раз", "Hear the protesters out %s times"], [1, 4], 1],
	["brands", "brands", ["Бренды города", "City brands"], ["Дождись брендов жителей: %s", "See %s resident brands founded"], [1, 3, 6], 2],
	["chains", "brand_b", ["Сеть магазинов", "Chain stores"], ["Построй заведений брендов: %s", "Build %s brand outlets"], [3, 12, 30], 1],
	["history", "hist", ["Хранитель истории", "Keeper of history"], ["Построй исторических объектов: %s", "Build %s historic sights"], [1, 3, 6], 2],
	["animals", "animals", ["Зоопарк", "Zookeeper"], ["Поймай видов зверей: %s", "Catch %s animal species"], [1, 5, 15], 1],
	["happy", "happy", ["Счастливый город", "Happy city"], ["Подними счастье до %s%%", "Raise happiness to %s%%"], [70, 85, 95], 1],
	["rep", "rep", ["Репутация", "Reputation"], ["Подними репутацию до %s", "Raise reputation to %s"], [70, 90], 1],
	["days", "day", ["Старожил", "Old-timer"], ["Проживи в городе дней: %s", "Live %s days in the city"], [10, 50, 150, 365], 1],
	["streak", "best", ["Верность городу", "Loyal mayor"], ["Заходи в игру дней подряд: %s", "Visit the game %s days in a row"], [3, 7, 14, 30], 2],
	["logins", "logins", ["Постоянный мэр", "Regular mayor"], ["Заходи в игру всего дней: %s", "Visit the game on %s different days"], [7, 30, 100], 1],
]

const DAILY_COINS := [200, 300, 450, 600, 800, 1000]   ## days 1..6 (× the level factor); day 7 is gems
const DAILY_GEMS := 5


static func target_text(a: Array, tier: int) -> String:
	var t: String = Loc.pick(a[3])
	return t % Loc.num(int(a[4][tier])) if t.contains("%s") else t


static func reward(a: Array, tier: int) -> Dictionary:
	var n: int = (a[4] as Array).size()
	var w: int = int(a[5])
	var gems: int = tier if n > 1 else 1
	return {"coins": 250 * w * (tier + 1) * (tier + 1), "gems": gems * (1 if w < 2 else 2)}


static func daily_reward(day_in_cycle: int) -> Dictionary:
	var f := 1.0 + Game.level * 0.15
	if day_in_cycle >= 6:
		return {"coins": int(1500 * f), "gems": DAILY_GEMS}
	return {"coins": int(DAILY_COINS[day_in_cycle] * f), "gems": 0}


static func _count(pred: Callable) -> int:
	var n := 0
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if b.built and pred.call(b, Data.B[b.id]):
			n += 1
	return n


static func _svc(names: Array) -> int:
	return _count(func(_b, d): return names.has(d.get("svc", "")))


static func value(key: String) -> int:
	var crime: Dictionary = Game.crime
	var pr: Dictionary = Game.protest
	match key:
		"built": return _count(func(_b, _d): return true)
		"homes": return _count(func(_b, d): return d.cat == "home")
		"shops": return _count(func(_b, d): return d.cat == "shop")
		"services": return _count(func(_b, d): return d.cat == "service")
		"ind": return _count(func(_b, d): return d.cat == "ind")
		"decor": return _count(func(_b, d): return d.cat == "decor")
		"fun": return _count(func(_b, d): return d.cat == "fun")
		"lvl3": return _count(func(b, _d): return b.lvl >= 3)
		"upgrades": return int(Game.stats.get("upgrades", 0))
		"pop": return maxi(Game.pop, Game.peak_pop)
		"level": return Game.level
		"coins_total": return int(Game.stats.coins_total)
		"goods_total": return int(Game.stats.goods_total)
		"deposit": return Game.deposit
		"plots": return Game.plots.size()
		"roads": return Game.roads.size()
		"lights": return Game.lights.size()
		"rings": return Game.rings.size()
		"lamps": return Game.lamps.size()
		"hlamps": return Game.house_lamp_count()
		"paves": return Game.paves.size()
		"walls": return Game.walls.size()
		"quarters": return Game.quarter_of.size()
		"water": return Game.water.size()
		"waterw": return _svc(["water"])
		"power": return _svc(["power", "solar"])
		"beach": return Game.beach.size()
		"airport": return 1 if Game.has_airport() else 0
		"flights": return Game.flights.size()
		"arrivals":
			var n := 0
			for c in Game.arrivals:
				n += int(Game.arrivals[c])
			return n
		"bus": return _svc(["bus", "metro"])
		"parking": return _svc(["parking"])
		"edu": return _svc(["edu"])
		"health": return _svc(["health"])
		"culture": return _svc(["culture"])
		"sport": return _svc(["sport"])
		"media": return _svc(["tv", "news"])
		"garbage": return _svc(["garbage"])
		"fire": return _svc(["fire"])
		"police": return _svc(["police", "patrol", "guard"])
		"prison": return _svc(["prison"])
		"robbers": return int(crime.get("caught", 0))
		"mayor_rob": return int(crime.get("mayor", 0))
		"jailed": return int(crime.get("jailed", 0))
		"protests": return int(pr.get("count", 0))
		"talks": return int(pr.get("talks", 0))
		"brands": return Game.brands.size()
		"brand_b": return _count(func(b, _d): return Data.brand_of(b.id) != "")
		"hist": return _count(func(_b, d): return d.get("hist", 0) > 0)
		"animals": return Game.caught.size()
		"happy": return int(Game.happy)
		"rep": return int(Game.rep)
		"day": return Game.day
		"best": return int(Game.ach.get("best", 0))
		"logins": return int(Game.ach.get("logins", 0))
	return 0


static func tier_of(id: String) -> int:
	return int(Game.ach.got.get(id, 0))


static func total() -> int:
	var n := 0
	for a in LIST:
		n += (a[4] as Array).size()
	return n


static func earned() -> int:
	var n := 0
	for a in LIST:
		n += tier_of(a[0])
	return n


## Awards every tier reached since the last check; returns what was earned [[name, tier, reward], ...].
static func check() -> Array:
	var out := []
	for a in LIST:
		var tiers: Array = a[4]
		var t := tier_of(a[0])
		if t >= tiers.size():
			continue
		var v := value(a[1])
		while t < tiers.size() and v >= int(tiers[t]):
			var r := reward(a, t)
			Game.coins += int(r.coins)
			Game.gems += int(r.gems)
			Game.stats.coins_total = int(Game.stats.coins_total) + int(r.coins)
			out.append([a, t, r])
			t += 1
		Game.ach.got[a[0]] = t
	return out
