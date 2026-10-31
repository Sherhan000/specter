class_name Citizens
extends RefCounted
## A representative sample of the city's residents (up to CAP people): age, education, profession, wage, wallet,
## health. Drives careers, the residents' economy (wages, food, shopping, the mayor's prices for light, water and
## fares), births, illness and deaths. The sample is scaled up to the real population in the statistics.
## State lives in Game.cz and is saved with the game.

const CAP := 240
const YEAR_DAYS := 6          ## one year of a resident's age passes in this many game days
const PROMO_DAYS := 25        ## days of work between raises
const PRICE_STEPS := [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
const FOOD := 16
const RENT := 10
const BASE_POWER := 2.0
const BASE_WATER := 1.0
const BASE_FARE := 1.0

## profession id: [ru, en, base wage per day, minimal education]
const PROF := {
	"seller": ["Продавец", "Shop assistant", 44, 0], "worker": ["Рабочий", "Factory worker", 50, 0],
	"farmer": ["Фермер", "Farmer", 42, 0], "cook": ["Повар", "Cook", 48, 0], "artist": ["Артист", "Entertainer", 52, 0],
	"clerk": ["Клерк", "Clerk", 58, 1], "teacher": ["Учитель", "Teacher", 70, 1], "police": ["Полицейский", "Police officer", 74, 1],
	"firefighter": ["Пожарный", "Firefighter", 72, 1], "nurse": ["Медсестра", "Nurse", 64, 1],
	"doctor": ["Врач", "Doctor", 112, 2], "banker": ["Банкир", "Banker", 96, 2], "it": ["IT-специалист", "IT specialist", 122, 2],
}
const EDU_NAMES := [["Без образования", "No education"], ["Школа", "School"], ["Высшее / IT", "Higher / IT"]]
const CAUSES := ["age", "illness", "poverty", "no_hospital", "pollution"]
const CAUSE_NAMES := {"age": ["Старость", "Old age"], "illness": ["Болезнь", "Illness"], "poverty": ["Бедность", "Poverty"],
	"no_hospital": ["Нет больницы", "No hospital"], "pollution": ["Загрязнение", "Pollution"]}
const NAMES := [["Азиз", "Aziz"], ["Мадина", "Madina"], ["Руслан", "Ruslan"], ["Лола", "Lola"], ["Фаррух", "Farrukh"],
	["Зарина", "Zarina"], ["Саид", "Said"], ["Нигина", "Nigina"], ["Тимур", "Timur"], ["Дильшод", "Dilshod"], ["Анна", "Anna"],
	["Иван", "Ivan"], ["Мария", "Maria"], ["Олег", "Oleg"], ["Света", "Sveta"], ["Артём", "Artem"], ["Камила", "Kamila"],
	["Рустам", "Rustam"], ["Шахло", "Shakhlo"], ["Умед", "Umed"], ["Дина", "Dina"], ["Егор", "Egor"], ["Алия", "Aliya"], ["Ильяс", "Ilyas"]]

var list: Array = []                       ## citizen dictionaries, see _make()
var prices := {"power": 1.0, "water": 1.0, "fare": 1.0}
var stats := {"births": 0, "deaths": 0, "causes": {}, "recent": []}   ## recent: last events [[ru, en], ...]
var scale := 1.0                           ## real residents per sampled one
var next_id := 1
var pool: Array = []                       ## [[profession, weight], ...] from working buildings
var last_util := 0                         ## what residents paid the city yesterday


func reset() -> void:
	list = []
	prices = {"power": 1.0, "water": 1.0, "fare": 1.0}
	stats = {"births": 0, "deaths": 0, "causes": {}, "recent": []}
	scale = 1.0
	next_id = 1
	pool = []
	last_util = 0


func to_dict() -> Dictionary:
	return {"list": list, "prices": prices, "stats": stats, "next_id": next_id}


func from_dict(d: Dictionary) -> void:
	reset()
	if d.is_empty():
		return
	list = d.get("list", [])
	for c in list:
		c.id = int(c.id)
		c.home = int(c.home)
	for k in d.get("prices", {}):
		prices[k] = float(d.prices[k])
	var st: Dictionary = d.get("stats", {})
	for k in st:
		stats[k] = st[k]
	next_id = int(d.get("next_id", 1))


# ---------------------------------------------------------------- helpers
static func prof_name(id: String) -> String:
	return Loc.pick([PROF[id][0], PROF[id][1]]) if PROF.has(id) else Loc.pick(["Без работы", "Unemployed"])


static func prof_for_building(bid: String) -> String:
	var d: Dictionary = Data.B[bid]
	if bid in ["school", "kindergarten"]:
		return "teacher"
	if bid == "it_run":
		return "it"
	if bid in ["hospital", "maternity"]:
		return "doctor"
	if bid == "clinic":
		return "nurse"
	if bid in ["police", "police_post", "watchtower", "prison", "court", "security_office"]:
		return "police"
	if bid == "fire_station":
		return "firefighter"
	if bid == "bank":
		return "banker"
	if bid in ["farm", "apiary", "orchard", "chicken_farm", "greenhouse", "melon_field", "ranch", "vineyard", "fish_farm", "dairy", "windmill"]:
		return "farmer"
	if bid in ["cafe", "shawarma", "burger_bar", "pizzeria", "restaurant", "chaikhana", "drive_thru", "food_trucks", "bakery", "donut_shop"]:
		return "cook"
	match d.cat:
		"shop":
			return "seller"
		"ind":
			return "worker"
		"fun":
			return "artist"
	return "clerk"


func wage_of(c: Dictionary) -> int:
	if c.job == "":
		return 0
	var base: int = PROF[c.job][2]
	return int(round(base * (1.0 + 0.2 * int(c.edu)) * (1.0 + 0.08 * int(c.rank))))


func _make(age: int, home: int) -> Dictionary:
	var nm: Array = NAMES.pick_random()
	return {"id": next_id, "name": nm, "age": age, "home": home, "edu": 0, "job": "", "rank": 0, "career": 0,
		"wallet": randi_range(60, 300), "sick": 0, "sick_by": "", "poor": 0, "study": 0, "learn": "", "born": Game.day}


func age_group(c: Dictionary) -> String:
	if int(c.age) < 7:
		return "kid"
	if int(c.age) < 18:
		return "student"
	if int(c.age) >= 62:
		return "retired"
	return "adult"


func is_adult(c: Dictionary) -> bool:
	return age_group(c) == "adult"


func price_avg() -> float:
	return (float(prices.power) + float(prices.water) + float(prices.fare)) / 3.0


func set_price(k: String, dir: int) -> void:
	var i := PRICE_STEPS.find(float(prices[k]))
	if i < 0:
		i = 2
	prices[k] = PRICE_STEPS[clampi(i + dir, 0, PRICE_STEPS.size() - 1)]


func by_id(id: int) -> Dictionary:
	for c in list:
		if int(c.id) == id:
			return c
	return {}


# ---------------------------------------------------------------- daily step
func on_day() -> void:
	_sync()
	_pool()
	var polluted := _polluted_homes()
	var hosp := Game.has_service("health")
	var maternity := false
	var school := false
	var itschool := false
	var shops := false
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if not Game.works(uid):
			continue
		if b.id == "maternity":
			maternity = true
		if b.id in ["school", "kindergarten"]:
			school = true
		if b.id == "it_run":
			itschool = true
		if Data.B[b.id].cat == "shop":
			shops = true
	var emp_rate := 1.0 if Game.workforce <= 0 else clampf(float(Game.workers) / Game.workforce, 0.0, 1.0)
	var sick_n := 0
	for c in list:
		if int(c.sick) > 0:
			sick_n += 1
	var sick_share := float(sick_n) / maxf(1.0, list.size())
	var util := 0.0
	var dead: Array = []
	var born: Array = []
	var fares := Game.bus_stops().size() >= 2 or Game.metro_open()
	for c in list:
		_age(c)
		var grp := age_group(c)
		# ---- education and career
		if grp == "student":
			if school and int(c.age) == 17 and int(c.edu) < 1:
				c.edu = 1
		elif grp == "adult":
			if int(c.edu) == 0 and school and randf() < 0.01:
				c.edu = 1
			if int(c.edu) == 1 and itschool and int(c.study) == 0 and randf() < 0.04:
				c.study = 8
				c.learn = "it"
			if int(c.study) > 0:
				c.study = int(c.study) - 1
				if int(c.study) == 0:
					c.edu = 2
					c.learn = ""
					c.job = ""      # looks for a better job now
					c.rank = 0
			elif c.job == "" and randf() < emp_rate * 0.6:
				_hire(c)
			elif c.job != "":
				c.career = int(c.career) + 1
				if int(c.career) % PROMO_DAYS == 0 and int(c.rank) < 5:
					c.rank = int(c.rank) + 1
				if randf() < (1.0 - emp_rate) * 0.03:
					c.job = ""
					c.career = 0
					c.rank = 0
		# ---- money
		var income := 0
		var costs := 0.0
		match grp:
			"adult":
				income = wage_of(c) if int(c.study) == 0 else 12
				if c.job == "" and int(c.study) == 0:
					income = 18
				costs = FOOD + RENT
				if shops:
					costs += income * 0.3
			"retired":
				income = 34
				costs = FOOD * 0.8 + RENT * 0.5
			"student":
				income = 8
				costs = 4
		var ut := 0.0
		if grp != "kid":
			ut = BASE_POWER * float(prices.power) + BASE_WATER * float(prices.water) + (BASE_FARE * float(prices.fare) if fares and grp == "adult" else 0.0)
		util += ut
		c.wallet = int(c.wallet) + income - int(costs) - int(ut)
		if int(c.wallet) < 0:
			c.wallet = 0
			c.poor = int(c.poor) + 1
		else:
			c.poor = maxi(0, int(c.poor) - 1)
		# ---- health
		var home_b: Dictionary = Game.buildings.get(int(c.home), {})
		if int(c.sick) > 0:
			c.sick = int(c.sick) - 1
			if hosp and randf() < 0.3:
				c.sick = 0
			if int(c.sick) == 0:
				c.sick_by = ""
		else:
			var p_sick := 0.004 + sick_share * 0.35 + (0.01 if int(c.poor) > 3 else 0.0)
			var by := "illness"
			if polluted.has(int(c.home)):
				p_sick += 0.03
				by = "pollution"
			if Game.garbage >= 40.0:
				p_sick += 0.01
			if int(c.age) >= 62:
				p_sick += 0.01
			if randf() < p_sick:
				c.sick = randi_range(4, 9)
				c.sick_by = by
		# ---- death
		var cause := ""
		if Game.pop >= 20 and Game.day >= 5 and not home_b.is_empty():
			if int(c.age) >= 62 and randf() < (int(c.age) - 60) * 0.0006:
				cause = "age"
			elif int(c.sick) > 0:
				var pd := 0.004 if hosp else 0.022
				if randf() < pd * (2.0 if int(c.age) >= 62 else 1.0):
					cause = "illness" if hosp else "no_hospital"
					if c.sick_by == "pollution":
						cause = "pollution"
			elif int(c.poor) >= 8 and randf() < 0.012:
				cause = "poverty"
		if cause != "":
			dead.append([c, cause])
			continue
		# ---- birth
		if grp == "adult" and int(c.age) >= 20 and int(c.age) <= 40 and int(c.wallet) > 150 and int(c.sick) == 0 \
				and not home_b.is_empty() and int(Game.home_happy.get(int(c.home), 50)) >= 50:
			if randf() < (0.012 if maternity else 0.005):
				born.append(c)
	for pair in dead:
		_die(pair[0], pair[1])
	for c in born:
		_birth(c)
	# residents pay the city
	last_util = int(util * scale)
	if last_util > 0:
		Game._earn("utilities", last_util)
	# unfair prices make people angry, cheap ones make them happy
	if price_avg() >= 1.5:
		Game.add_mood(-4, 24, "prices")
		Game.add_anger("tax", 4.0)
	elif price_avg() <= 0.75:
		Game.add_mood(3, 24, "prices")


func _age(c: Dictionary) -> void:
	if (Game.day - int(c.born)) % YEAR_DAYS == 0 and Game.day != int(c.born):
		c.age = int(c.age) + 1
		if int(c.age) == 62:
			c.job = ""
			c.career = 0
			c.rank = 0


func _hire(c: Dictionary) -> void:
	var total := 0.0
	for e in pool:
		if int(PROF[e[0]][3]) <= int(c.edu):
			total += float(e[1])
	if total <= 0.0:
		return
	var r := randf() * total
	for e in pool:
		if int(PROF[e[0]][3]) <= int(c.edu):
			r -= float(e[1])
			if r <= 0.0:
				c.job = e[0]
				c.career = 0
				c.rank = 0
				return


func _pool() -> void:
	var w := {}
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if not Game.works(uid) or not Data.B[b.id].has("jobs"):
			continue
		var p := prof_for_building(b.id)
		w[p] = float(w.get(p, 0.0)) + float(Data.stat(b.id, "jobs", b.lvl))
	pool = []
	for p in w:
		pool.append([p, w[p]])


func _polluted_homes() -> Dictionary:
	var out := {}
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if int(Data.B[b.id].get("poll", 0)) < 5 or not b.built or b.closed:
			continue
		for h in Game.buildings:
			var hb: Dictionary = Game.buildings[h]
			if Data.B[hb.id].cat == "home" and absi(hb.x - b.x) <= 4 and absi(hb.y - b.y) <= 4:
				out[h] = true
	return out


## Keep the sample in line with the real population: newcomers arrive, extra people move away.
func _sync() -> void:
	var homes: Array = []
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if Data.B[b.id].cat == "home" and b.occ > 0 and Game.works(uid):
			homes.append(uid)
	for c in list:
		if not homes.has(int(c.home)) and not homes.is_empty():
			c.home = homes.pick_random()
	var target := mini(Game.pop, CAP)
	if homes.is_empty():
		list = []
		scale = 1.0
		return
	while list.size() < target:
		var age := randi_range(1, 17) if randf() < 0.28 else (randi_range(62, 78) if randf() < 0.15 else randi_range(18, 55))
		var c := _make(age, homes.pick_random())
		c.born = Game.day - age * YEAR_DAYS
		c.edu = 1 if age >= 18 and randf() < 0.7 else 0
		next_id += 1
		list.append(c)
	while list.size() > target:
		list.remove_at(randi() % list.size())
	scale = maxf(1.0, float(Game.pop) / maxf(1.0, list.size()))


func _die(c: Dictionary, cause: String) -> void:
	list.erase(c)
	stats.deaths = int(stats.deaths) + 1
	stats.causes[cause] = int(stats.causes.get(cause, 0)) + 1
	var hb: Dictionary = Game.buildings.get(int(c.home), {})
	if not hb.is_empty():
		hb.occ = maxi(0, int(hb.occ) - 1)
	_log([c.name[0] + " (%d): " % int(c.age) + CAUSE_NAMES[cause][0], c.name[1] + " (%d): " % int(c.age) + CAUSE_NAMES[cause][1]])
	if Game.pop > 0 and int(stats.deaths) % 5 == 1:
		Game.toast.emit(Loc.pick(["Умер житель: " + CAUSE_NAMES[cause][0], "A resident died: " + CAUSE_NAMES[cause][1]]))


func _birth(parent: Dictionary) -> void:
	var hb: Dictionary = Game.buildings.get(int(parent.home), {})
	if hb.is_empty():
		return
	var c := _make(0, int(parent.home))
	c.wallet = 0
	next_id += 1
	list.append(c)
	if int(hb.occ) < Data.stat(hb.id, "pop", hb.lvl):
		hb.occ = int(hb.occ) + 1
	stats.births = int(stats.births) + 1
	_log(["Родился " + c.name[0], "Born: " + c.name[1]])


func _log(pair: Array) -> void:
	stats.recent.push_front(pair)
	while stats.recent.size() > 12:
		stats.recent.pop_back()


# ---------------------------------------------------------------- statistics
func summary() -> Dictionary:
	var out := {"n": list.size(), "wallet": 0, "sick": 0, "kids": 0, "students": 0, "adults": 0, "retired": 0, "jobless": 0, "poor": 0,
		"wages": {}, "wage_n": {}, "edu": [0, 0, 0]}
	for c in list:
		out.wallet += int(c.wallet)
		if int(c.sick) > 0:
			out.sick += 1
		if int(c.poor) >= 3:
			out.poor += 1
		out.edu[int(c.edu)] += 1
		match age_group(c):
			"kid":
				out.kids += 1
			"student":
				out.students += 1
			"retired":
				out.retired += 1
			_:
				out.adults += 1
				if c.job == "":
					out.jobless += 1
				else:
					out.wages[c.job] = float(out.wages.get(c.job, 0.0)) + wage_of(c)
					out.wage_n[c.job] = int(out.wage_n.get(c.job, 0)) + 1
	return out
