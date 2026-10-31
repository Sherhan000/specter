class_name Social
extends RefCounted
## "Pixelchat": residents write posts about what the mayor does. Posts come from game events (a new hospital, a bank
## robbery, a protest, a disaster, taxes and prices, happiness...), collect likes over the next days, and the mayor
## can like them. State lives in Game.soc and is saved with the game.

const MAX_POSTS := 40
const MAX_PER_DAY := 4

## topic: [mood (+1/-1/0), [[ru, en], ...]]   (%s is filled with a building name when there is one)
const TOPICS := {
	"built_good": [1, [["Наконец-то в городе появилось: %s! Спасибо мэру", "At last the city has a %s! Thanks, mayor"],
		["Смотрите, у нас построили %s. Красота!", "Look, they built a %s. Beautiful!"]]],
	"built": [0, [["Рядом со мной строят %s. Посмотрим, что получится.", "They are building a %s near me. Let's see how it goes."],
		["Новая стройка: %s. Шум, но город растёт.", "New construction: %s. Noisy, but the city grows."]]],
	"tower": [1, [["Новая башня — %s! Город растёт ввысь", "A new tower — the %s! The city grows upward"]]],
	"night": [1, [["Теперь и ночью есть куда пойти: %s", "Now there's somewhere to go at night: %s"]]],
	"level": [1, [["Наш город поднялся на уровень %s! Так держать, мэр!", "Our city reached level %s! Keep it up, mayor!"]]],
	"rank": [1, [["Мэр получил звание «%s». Заслуженно!", "The mayor became «%s». Well deserved!"]]],
	"rob": [-1, [["Вы слышали? Мэр ограбил банк! Позор!!!", "Did you hear? The mayor robbed a bank! Shame!!!"],
		["Наш мэр — грабитель. Куда мы катимся?", "Our mayor is a robber. Where are we heading?"]]],
	"heist": [-1, [["Ограбили банк! Полиция, где вы?", "A bank was robbed! Police, where are you?"]]],
	"protest": [-1, [["Идём на площадь к ратуше! Пусть мэр нас услышит", "Let's go to the town hall square! Make the mayor hear us"]]],
	"protest_end": [0, [["Митинг закончился. Посмотрим, изменится ли что-то.", "The protest is over. Let's see whether anything changes."]]],
	"disaster": [-1, [["Беда в городе! Держитесь, соседи", "Trouble in the city! Hang in there, neighbours"]]],
	"disaster_ok": [1, [["Мэр справился с бедой — город спасён!", "The mayor handled the disaster — the city is saved!"]]],
	"disaster_bad": [-1, [["Помощи не было, дома пострадали. Спасибо, мэр...", "No help came and homes were damaged. Thanks, mayor..."]]],
	"tax_high": [-1, [["Налоги просто грабительские! Пора что-то менять.", "Taxes are simply robbery! Time for a change."]]],
	"tax_low": [1, [["Налоги низкие — дышится легче. Респект мэру!", "Taxes are low — easier to breathe. Respect to the mayor!"]]],
	"debt": [-1, [["Город в долгах, а зарплаты когда?", "The city is in debt — and when do we get paid?"]]],
	"happy": [1, [["Живу в лучшем городе! Всё нравится", "I live in the best city! I love it"]]],
	"sad": [-1, [["Мне тут плохо. Мэр, сделайте что-нибудь!", "I feel bad here. Mayor, do something!"]]],
	"garbage": [-1, [["Мусор не вывозят, на улицах грязно", "Nobody collects the garbage, the streets are dirty"]]],
	"power": [-1, [["Опять свет моргает… электростанций мало!", "The lights are flickering again… not enough power plants!"]]],
	"jobs": [-1, [["Работы нет, а счета есть. Мэр, дайте рабочие места!", "No jobs but plenty of bills. Mayor, give us jobs!"]]],
	"prices": [-1, [["Свет, вода и проезд стали золотыми!", "Power, water and fares have become golden!"]]],
	"cheap": [1, [["Дешёвые свет и проезд — спасибо мэру!", "Cheap power and fares — thanks, mayor!"]]],
	"no_hospital": [-1, [["В городе нет больницы, а люди болеют. Это нормально?", "There's no hospital and people are getting sick. Is that normal?"]]],
	"fireworks": [1, [["Салют над площадью! Красота", "Fireworks over the square! Beautiful"]]],
	"born": [1, [["У нас родился малыш! Город растёт", "A baby was born in our family! The city is growing"]]],
}
const BIG_GOOD := ["hospital", "clinic", "school", "kindergarten", "it_run", "park", "plaza", "fountain", "library", "fire_station", "police", "museum",
	"stadium", "zoo", "funfair", "cinema", "maternity", "garbage_depot", "bank"]

var posts: Array = []
var next_id := 1
var today_n := 0
var _day := -1


func reset() -> void:
	posts = []
	next_id = 1
	today_n = 0
	_day = -1


func to_dict() -> Dictionary:
	return {"posts": posts, "next_id": next_id}


func from_dict(d: Dictionary) -> void:
	reset()
	posts = d.get("posts", [])
	for p in posts:
		p.id = int(p.id)
		p.likes = int(p.likes)
	next_id = int(d.get("next_id", 1))


func setup() -> void:
	Game.building_added.connect(_on_building)
	Game.level_up.connect(func(l): post("level", [str(l), str(l)]))
	Game.heist.connect(func(_u, _c, by_mayor): post("rob" if by_mayor else "heist"))
	Game.protest_changed.connect(func(s): post("protest" if s == "start" else "protest_end" if s == "end" else "", []))
	Game.disaster_changed.connect(func(s): post({"start": "disaster", "safe": "disaster_ok", "hit": "disaster_bad"}.get(s, "")))
	Game.day_passed.connect(_on_day)


func _on_building(uid: int) -> void:
	var b: Dictionary = Game.buildings.get(uid, {})
	if b.is_empty() or b.priv != "":
		return
	var nm: Array = Data.B[b.id].name
	if b.id.begins_with("tower_") or b.id in ["sky_office", "sky_heli", "dushanbe_tower"]:
		post("tower", nm)
	elif Data.B[b.id].get("night", false):
		post("night", nm)
	elif b.id in BIG_GOOD:
		post("built_good", nm)
	elif randf() < 0.25:
		post("built", nm)


func _on_day(day: int) -> void:
	_day = day
	today_n = 0
	for p in posts:   # likes keep coming for a few days
		var age: int = day - int(p.day)
		if age <= 3:
			p.likes = int(p.likes) + randi_range(0, maxi(1, Game.pop / 10)) * (1 if int(p.mood) >= 0 else 2)
	if randf() < 0.5:
		return
	var t := ""
	if Game.tax >= 16:
		t = "tax_high"
	elif Game.tax <= 5 and Game.day > 3:
		t = "tax_low"
	elif Game.coins < 0:
		t = "debt"
	elif Game.garbage >= 60.0:
		t = "garbage"
	elif Game.power_ratio < 0.85 and Game.pop > 20:
		t = "power"
	elif Game.unemployment > 0.25 and Game.pop > 20:
		t = "jobs"
	elif Game.cz.price_avg() >= 1.5:
		t = "prices"
	elif Game.cz.price_avg() <= 0.75:
		t = "cheap"
	elif Game.pop > 40 and not Game.has_service("health") and Game.cz.summary().sick > 0:
		t = "no_hospital"
	elif Game.happy >= 75.0:
		t = "happy"
	elif Game.happy <= 35.0:
		t = "sad"
	elif FireworksFx.is_weekend(day) and randf() < 0.5:
		t = "fireworks"
	if t != "":
		post(t)


## Add a post on a topic; arg is a name pair [ru, en] (or [ru, en] strings) for the %s.
func post(topic: String, arg := []) -> void:
	if topic == "" or not TOPICS.has(topic) or Game.pop < 5:
		return
	if today_n >= MAX_PER_DAY:
		return
	today_n += 1
	var tpl: Array = TOPICS[topic][1].pick_random()
	var ru: String = tpl[0]
	var en: String = tpl[1]
	if arg.size() >= 2:
		ru = ru % str(arg[0]).to_lower() if topic in ["built_good", "built", "night"] else ru % str(arg[0])
		en = en % str(arg[1]).to_lower() if topic in ["built_good", "built", "night"] else en % str(arg[1])
	var who: Array = []
	if not Game.cz.list.is_empty():
		who = Game.cz.list.pick_random().name
	else:
		who = Citizens.NAMES.pick_random()
	var base := maxi(1, Game.pop / 12)
	posts.push_front({"id": next_id, "who": who, "ru": ru, "en": en, "day": Game.day, "mood": TOPICS[topic][0],
		"likes": randi_range(0, base * 2), "mine": false})
	next_id += 1
	while posts.size() > MAX_POSTS:
		posts.pop_back()


## The mayor likes a post: one more like, and the author is glad.
func like(id: int) -> void:
	for p in posts:
		if int(p.id) == id and not p.mine:
			p.mine = true
			p.likes = int(p.likes) + 1
			if int(p.mood) < 0:
				Game.add_rep(0.2)
			return


func total_likes() -> int:
	var n := 0
	for p in posts:
		n += int(p.likes)
	return n


## Mood of the feed: share of positive posts among the latest ones, 0..1.
func sentiment() -> float:
	var pos := 0
	var neg := 0
	for p in posts.slice(0, 12):
		if int(p.mood) > 0:
			pos += 1
		elif int(p.mood) < 0:
			neg += 1
	return 0.5 if pos + neg == 0 else float(pos) / (pos + neg)
