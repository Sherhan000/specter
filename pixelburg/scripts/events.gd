extends Node
## Inbox with decisions (violations, business proposals, festivals, complaints), disasters
## (fires, crime, illness) and the story: friends, the rival and the mayoral election.

signal inbox_changed
signal dialog(lines: Array)                   ## [{who, expr, text: [ru, en], choices: [[label, act]]}]
signal fire_started(uid: int, covered: bool)
signal crime(caught: bool)
signal story_changed

const CHARS := {
	"alina": ["Алина", "Alina"],
	"boris": ["Борис Петрович", "Boris"],
	"viktor": ["Виктор Громов", "Viktor Grom"],
	"marina": ["Марина Светлова", "Marina Bright"],
	"oleg": ["Олег Смирнов", "Chief Oleg"],
	"zina": ["Баба Зина", "Granny Zina"],
}
const FIRST_NAMES := [["Иван", "Ivan"], ["Анна", "Anna"], ["Пётр", "Peter"], ["Ольга", "Olga"], ["Дмитрий", "Dmitry"],
	["Елена", "Elena"], ["Сергей", "Sergey"], ["Мария", "Maria"], ["Артём", "Artem"], ["Софья", "Sofia"],
	["Никита", "Nikita"], ["Вера", "Vera"], ["Тимур", "Timur"], ["Лиза", "Liza"], ["Павел", "Pavel"]]

var inbox: Array = []        ## newest first
var next_id := 1
var chapter := 0
var flags := {}
var story: Array = []        ## story missions
var election_day := 0
var _rng := RandomNumberGenerator.new()
var _next_violation := 30
var _next_proposal := 40
var _next_festival := 60


func _ready() -> void:
	_rng.randomize()


func reset() -> void:
	inbox = []
	next_id = 1
	chapter = 0
	flags = {}
	story = []
	election_day = 0
	_next_violation = 30
	_next_proposal = 40
	_next_festival = 60
	inbox_changed.emit()


func to_dict() -> Dictionary:
	return {"inbox": inbox, "next_id": next_id, "chapter": chapter, "flags": flags, "story": story,
		"election_day": election_day, "nv": _next_violation, "np": _next_proposal, "nf": _next_festival}


func from_dict(d: Dictionary) -> void:
	reset()
	inbox = d.get("inbox", [])
	next_id = int(d.get("next_id", 1))
	chapter = int(d.get("chapter", 0))
	flags = d.get("flags", {})
	story = d.get("story", [])
	election_day = int(d.get("election_day", 0))
	_next_violation = int(d.get("nv", 30))
	_next_proposal = int(d.get("np", 40))
	_next_festival = int(d.get("nf", 60))


static func fmt(pair) -> String:
	var s: String = Loc.pick(pair) if pair is Array else str(pair)
	var t := Game.mayor_title()
	return s.replace("{name}", Game.profile.get("name", "")).replace("{Title}", t.substr(0, 1).to_upper() + t.substr(1)).replace("{title}", t)


func char_name(who: String) -> String:
	return Loc.pick(CHARS[who]) if CHARS.has(who) else ""


func unread() -> int:
	var n := 0
	for m in inbox:
		if not m.get("done", false):
			n += 1
	return n


# ====================================================================== inbox
## options: [[label pair, act], ...]; the first act "ok" just closes.
func post(kind: String, who: String, title: Array, text: Array, options: Array, extra := {}) -> Dictionary:
	var m := {"id": next_id, "kind": kind, "from": who, "title": title, "text": text, "opts": options,
		"day": Game.day, "done": false, "expires": Game.abs_hour() + 48}
	for k in extra:
		m[k] = extra[k]
	next_id += 1
	inbox.push_front(m)
	while inbox.size() > 30:
		inbox.pop_back()
	inbox_changed.emit()
	Game.sfx("mail")
	return m


func resolve(id: int, opt: int) -> void:
	for m in inbox:
		if int(m.id) == id and not m.done:
			m.done = true
			var act: String = m.opts[opt][1]
			m["chosen"] = opt
			_apply(act, m)
			inbox_changed.emit()
			Game.save_game()
			return


## A choice made inside a dialogue.
func choose(act: String) -> void:
	_apply(act, {})
	Game.save_game()


func _expire() -> void:
	var now := Game.abs_hour()
	for m in inbox:
		if not m.done and int(m.get("expires", 1 << 30)) < now:
			m.done = true
			m["chosen"] = -1
			if m.kind == "violation":
				Game.add_rep(-3)
			elif m.kind == "proposal":
				Game.add_rep(-1)
	inbox_changed.emit()


func _apply(act: String, m: Dictionary) -> void:
	var uid := int(m.get("uid", 0))
	if act.begins_with("dz:"):
		var parts := act.split(":")
		Game.disaster_choose(parts[1], int(parts[2]))
		return
	match act:
		"ok":
			pass
		"bail":
			Game.pay_bail()
		"pr_talk":
			Game.protest_talk()
		"pr_force":
			Game.protest_force()
		"pr_wait":
			Game.add_rep(-1)
		# ---------------- violations
		"fine":
			Game.earn_event("fines", int(m.fine))
			Game.add_rep(2)
			Game.toast.emit(Loc.t("ev_fined") % int(m.fine))
		"inspect":
			if Game.buildings.has(uid):
				Game.set_closed(uid, true)
				flags["reopen_%d" % uid] = Game.abs_hour() + 24
			Game.add_rep(3)
		"ignore":
			Game.add_rep(-4)
			Game.add_mood(-2, 24, "ignored")
		"court":
			if Game.has_service("law"):
				Game.earn_event("fines", int(m.fine) * 2)
				Game.add_rep(5)
				Game.toast.emit(Loc.t("ev_court_won") % (int(m.fine) * 2))
		"evict_bad":
			if Game.buildings.has(uid):
				Game.evict(uid)
				Game.add_rep(4)
		"warn":
			Game.add_rep(1)
			if _rng.randf() < 0.5:
				Game.add_mood(-2, 24, "noise")
		# ---------------- proposals
		"accept_biz":
			var spot: Vector2i = Vector2i(int(m.spot[0]), int(m.spot[1]))
			var placed := Game.place_private(m.biz, spot.x, spot.y, fmt(m.owner))
			if placed == 0:
				var s := find_business_spot(Data.B[m.biz].size)
				if s != Vector2i(-1, -1):
					placed = Game.place_private(m.biz, s.x, s.y, fmt(m.owner))
			if placed > 0:
				Game.add_rep(2)
				Game.toast.emit(Loc.t("ev_biz_open"))
			else:
				Game.toast.emit(Loc.t("ev_biz_nospot"))
		"decline_biz":
			Game.add_rep(-1)
		# ---------------- residents' brands
		"accept_brand":
			if Game.found_brand(str(m.brand), fmt(m.owner)):
				Game.add_rep(2)
				Game.toast.emit(Loc.t("ev_brand_founded") % Data.brand_name(m.brand))
		"accept_branch":
			var bid := str(m.brand)
			var kind := str(m.kind)
			var at: Vector2i = Vector2i(int(m.spot[0]), int(m.spot[1]))
			var got := Game.open_branch(bid, kind, at.x, at.y)
			if got == 0:
				var s2 := find_business_spot(Data.B[bid + "_" + kind].size)
				if s2 != Vector2i(-1, -1):
					got = Game.open_branch(bid, kind, s2.x, s2.y)
			if got > 0:
				Game.add_rep(1)
				Game.toast.emit(Loc.t("ev_branch_open") % Data.brand_name(bid))
			else:
				Game.toast.emit(Loc.t("ev_biz_nospot"))
		# ---------------- festival
		"festival":
			if Game.pay(600, 0, "events"):
				Game.add_mood(10, 24, "festival")
				Game.add_rep(3)
				flags["festival_until"] = Game.abs_hour() + 24
		"no_festival":
			Game.add_mood(-2, 12, "no_festival")
		"repair":
			if Game.buildings.has(uid):
				Game.repair(uid)
		"show":
			pass
		_:
			_story_act(act, m)


# ====================================================================== hourly / daily
func on_hour(h: int) -> void:
	if Game.lost or Game.tutorial < 99:
		return
	_expire()
	var now := Game.abs_hour()
	for k in flags.keys():
		if str(k).begins_with("reopen_") and int(flags[k]) <= now:
			var uid := int(str(k).substr(7))
			flags.erase(k)
			if Game.buildings.has(uid):
				Game.set_closed(uid, false)
	_check_story()
	if Game.level >= 3 and now >= _next_violation:
		_next_violation = now + _rng.randi_range(26, 44)
		_violation()
	if Game.level >= 3 and now >= _next_proposal:
		_next_proposal = now + _rng.randi_range(30, 50)
		_proposal()
	if Game.pop >= 60 and now >= _next_festival:
		_next_festival = now + _rng.randi_range(60, 90)
		post("festival", "alina", ["Праздник", "Festival"],
			["Жители просят устроить праздник на главной площади. Это стоит 600 монет, но поднимет настроение города.",
			 "Residents ask for a festival on the main square. It costs 600 coins but lifts the city's mood."],
			[[["Устроить (600)", "Hold it (600)"], "festival"], [["Не сейчас", "Not now"], "no_festival"]])
	_disasters(h)


func on_day(d: int) -> void:
	if Game.lost:
		return
	if (Game.rules.get("pollution", false) or Game.rules.get("garbage", false)) and _rng.randf() < 0.6:
		post("complaint", "zina", ["Жалоба", "Complaint"],
			["Дым от заводов идёт прямо в окна! Уберите промышленность подальше от домов, {title}.",
			 "Smoke from the factories goes right into our windows! Move industry away from homes, {title}."],
			[[["Понятно", "Understood"], "ok"]])
	if Game.rules.get("lights", false):
		post("complaint", "oleg", ["Пробки", "Traffic jams"],
			["Слишком много светофоров рядом: машины стоят. Правило города: не больше 3 светофоров на участке 7×7.",
			 "Too many traffic lights close together: cars are stuck. City rule: no more than 3 lights in a 7×7 area."],
			[[["Исправлю", "Will fix"], "ok"]])
	if election_day > 0 and d >= election_day and not flags.get("election_done", false):
		_election()


# ====================================================================== violations
const VIOLATIONS := [
	[["Санитарная проверка", "Health inspection"], ["В «%s» нашли грязную кухню и просроченные продукты.", "\"%s\" has a dirty kitchen and expired food."]],
	[["Работа без лицензии", "No licence"], ["«%s» работает без нужной лицензии.", "\"%s\" operates without the required licence."]],
	[["Шум ночью", "Night noise"], ["Соседи жалуются: «%s» шумит по ночам.", "Neighbours complain that \"%s\" is noisy at night."]],
	[["Нарушение пожарной безопасности", "Fire safety breach"], ["В «%s» загромождены пожарные выходы.", "\"%s\" has blocked fire exits."]],
	[["Неуплата налогов", "Unpaid taxes"], ["«%s» скрывает часть доходов от налоговой.", "\"%s\" hides part of its income from the tax office."]],
]


func _violation() -> void:
	var cands: Array[int] = []
	for uid in Game.buildings:
		var b: Dictionary = Game.buildings[uid]
		if Data.B[b.id].cat in ["shop", "ind", "fun"] and b.built and not b.closed:
			cands.append(uid)
	if cands.is_empty():
		return
	var uid: int = cands.pick_random()
	var b: Dictionary = Game.buildings[uid]
	var v: Array = VIOLATIONS.pick_random()
	var n := Data.name_of(b.id)
	var fine := int(clampf(Data.B[b.id].cost * 0.08, 60, 1500))
	var text := [v[1][0] % Data.B[b.id].name[0], v[1][1] % Data.B[b.id].name[1]]
	if b.priv != "":
		text = [text[0] + " Владелец: " + b.priv + ".", text[1] + " Owner: " + b.priv + "."]
	var opts := [[["Штраф +%d" % fine, "Fine +%d" % fine], "fine"], [["Закрыть на проверку", "Close for inspection"], "inspect"],
		[["Не трогать", "Let it go"], "ignore"]]
	if Game.has_service("law"):
		opts.insert(1, [["В суд +%d" % (fine * 2), "Sue +%d" % (fine * 2)], "court"])
	post("violation", "oleg", v[0], text, opts, {"uid": uid, "fine": fine, "name": n})


# ====================================================================== proposals
func find_business_spot(size: int) -> Vector2i:
	var spots: Array[Vector2i] = []
	for c in Game.roads:
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var t: Vector2i = c + d
			if Data.zone_at(t) == "city" and Game.place_problem("bakery" if size == 1 else "supermarket", t.x, t.y) == "":
				spots.append(t)
	if spots.is_empty():
		return Vector2i(-1, -1)
	return spots.pick_random()


func _proposal() -> void:
	if Game.level >= Data.BRAND_MIN_LEVEL:
		if not Game.brands.is_empty() and _rng.randf() < 0.5 and brand_branch_proposal():
			return
		if Game.brands.size() < Data.BRANDS.size() and _rng.randf() < 0.35 and brand_found_proposal():
			return
	var biz: String = Data.PRIVATE_KINDS.pick_random()
	if Game.level < int(Data.B[biz].lvl):
		biz = "bakery"
	var spot := find_business_spot(1)
	if spot == Vector2i(-1, -1):
		return
	var who: Array = FIRST_NAMES.pick_random()
	var tax := int(Data.stat(biz, "income", 1) * 3 * Game.tax / 10.0)
	post("proposal", "alina", ["Новый бизнес", "New business"],
		["Жител%s %s хочет открыть «%s» на свободном месте у дороги. Город ничего не платит, а налог составит около %d монет в день." % [
			"ьница" if who[0].ends_with("а") or who[0].ends_with("я") else "ь", who[0], Data.B[biz].name[0], tax],
		 "Resident %s wants to open a %s on a free spot by the road. The city pays nothing and the tax is about %d coins a day." % [
			who[1], Data.B[biz].name[1].to_lower(), tax]],
		[[["Разрешить", "Allow"], "accept_biz"], [["Отказать", "Refuse"], "decline_biz"]],
		{"biz": biz, "spot": [spot.x, spot.y], "owner": who})


# ====================================================================== residents' brands
## A resident wants to found a brand of their own (one of Data.BRANDS not founded yet).
func brand_found_proposal() -> bool:
	var free: Array = Data.BRAND_ORDER.filter(func(k): return not Game.brands.has(k))
	if free.is_empty():
		return false
	var bid: String = free.pick_random()
	var br: Dictionary = Data.BRANDS[bid]
	var who: Array = FIRST_NAMES.pick_random()
	post("proposal", "alina", ["Новый бренд", "A new brand"],
		["Жител%s %s хочет основать свой бренд «%s» — сеть %s. Бренд сам будет открывать киоски, магазины, а потом и флагманы, и платить налог больше обычного." % [
			"ьница" if who[0].ends_with("а") or who[0].ends_with("я") else "ь", who[0], br.name[0], br.sells[0]],
		 "Resident %s wants to found a brand of their own, «%s» — a chain of %s. The brand will open its kiosks, shops and later flagships itself and pay more tax than usual." % [
			who[1], br.name[1], br.sells[1]]],
		[[["Поддержать", "Support"], "accept_brand"], [["Отказать", "Refuse"], "decline_biz"]],
		{"brand": bid, "owner": who})
	return true


## A founded brand wants to open its next place.
func brand_branch_proposal() -> bool:
	var bid: String = Game.brands.keys().pick_random()
	var kind := Game.brand_next_kind(bid)
	var id := bid + "_" + kind
	var spot := find_business_spot(Data.B[id].size)
	if spot == Vector2i(-1, -1) and kind == "flag":
		kind = "shop"
		id = bid + "_" + kind
		spot = find_business_spot(1)
	if spot == Vector2i(-1, -1):
		return false
	var br: Dictionary = Data.BRANDS[bid]
	var tax := int(Data.stat(id, "income", Game.brand_level(bid)) * 3 * Game.tax / 10.0 * Data.BRAND_TAX)
	post("proposal", "alina", [br.name[0], br.name[1]],
		["Бренд «%s» (владелец: %s) хочет открыть новое место: %s. Город ничего не платит, налог около %d монет в день." % [
			br.name[0], str(Game.brands[bid].owner), Data.B[id].name[0].to_lower(), tax],
		 "The «%s» brand (owner: %s) wants to open a new place: %s. The city pays nothing, the tax is about %d coins a day." % [
			br.name[1], str(Game.brands[bid].owner), Data.B[id].name[1].to_lower(), tax]],
		[[["Разрешить", "Allow"], "accept_branch"], [["Отказать", "Refuse"], "decline_biz"]],
		{"brand": bid, "kind": kind, "spot": [spot.x, spot.y]})
	return true


# ====================================================================== disasters
func _disasters(_h: int) -> void:
	if Game.pop < 30:
		return
	var fire_p := 0.012 * (2.0 if Game.rules.get("fire", false) else 1.0) * Game.law_mult("fire")
	if Game.weather == "storm":
		fire_p *= 2.0
	elif Game.weather == "heat":
		fire_p *= 1.6
	elif Game.weather == "windy":
		fire_p *= 1.25
	if _rng.randf() < fire_p:
		start_fire()
	if Game.pop >= Data.HEIST_MIN_POP:
		var banks := Game.working_banks()
		if not banks.is_empty():
			var bank: int = banks[_rng.randi() % banks.size()]
			var hp := Data.HEIST_CHANCE * Game.crime_mult() * (Data.HEIST_GUARD_MULT if Game.bank_guarded(bank) else 1.0)
			if _rng.randf() < hp:
				resident_heist(bank)
	if Game.pop >= 100 and _rng.randf() < 0.02 * Game.crime_mult():
		var caught := Game.has_service("police")
		if caught:
			Game.add_rep(2)
			post("crime", "oleg", ["Погоня!", "Car chase!"],
				["Грабитель угнал машину! Наши патрули уже гонятся за ним по трассе.",
				 "A robber stole a car! Our patrols are already chasing him along the highway."],
				[[["Отлично", "Great"], "ok"]])
		else:
			Game.add_rep(-2)
			Game.add_mood(-3, 24, "crime")
			post("crime", "oleg", ["Ограбление", "Robbery"],
				["В городе ограбили магазин, а полиции у нас нет. Жители напуганы.",
				 "A shop was robbed and the city has no police. Residents are scared."],
				[[["Понятно", "Understood"], "ok"]])
		crime.emit(caught)
	if Game.rules.get("health", false) and _rng.randf() < 0.03:
		Game.add_mood(-6, 24, "illness")
		post("illness", "zina", ["Эпидемия гриппа", "Flu outbreak"],
			["Половина района слегла с гриппом, а больницы нет!", "Half the district has the flu and there is no hospital!"],
			[[["Понятно", "Understood"], "ok"]])


## A resident robs a bank: people run, the police chase; a message from the police chief.
func resident_heist(bank: int) -> bool:
	var loot := Game.heist_loot(bank)
	var caught := Game.bank_heist(bank)
	if caught:
		post("crime", "oleg", ["Грабитель пойман!", "Robber caught!"],
			["Житель ограбил банк, люди разбежались, но наши патрульные догнали его. Деньги (%d) вернули в банк." % loot,
			 "A resident robbed the bank and people ran, but our patrol caught him. The money (%d) is back in the bank." % loot],
			[[["Отлично", "Great"], "ok"]], {"uid": bank})
	elif Game.police_count() == 0:
		post("crime", "oleg", ["Ограбление банка", "Bank robbery"],
			["Банк ограбили и унесли %d монет из казны. Полиции нет — ловить некому. Постройте полицию или охрану «Щит»." % loot,
			 "The bank was robbed: %d coins from the treasury are gone. There is no police to chase them. Build a police station or Shield Guards." % loot],
			[[["Понятно", "Understood"], "ok"]], {"uid": bank})
	else:
		post("crime", "oleg", ["Грабитель ушёл", "The robber got away"],
			["Банк ограбили (%d монет), погоня не удалась. Больше полиции и охрана у банка помогут ловить грабителей." % loot,
			 "The bank was robbed (%d coins) and the chase failed. More police and guards at the bank will help catch robbers." % loot],
			[[["Понятно", "Understood"], "ok"]], {"uid": bank})
	return caught


## The investigation of the mayor's robbery found nothing.
func probe_closed() -> void:
	post("crime", "oleg", ["Дело закрыто", "Case closed"],
		["Грабителя банка так и не нашли. Следствие закрыто… но в следующий раз мы будем внимательнее.",
		 "The bank robber was never found. The case is closed… but next time we'll be more careful."],
		[[["Хорошо", "OK"], "ok"]])


## The police found out the mayor robbed the bank.
func mayor_jailed(fine: int) -> void:
	var m := post("crime", "oleg", ["Мэр арестован!", "The mayor is arrested!"],
		["{Title}, камеры и свидетели всё показали: банк ограбили вы. Суд: %d ч. тюрьмы и штраф %d монет. Пока вы сидите, строить нельзя, налоги и туристы — вдвое меньше, город возмущён." % [Data.JAIL_HOURS, fine],
		 "{Title}, the cameras and witnesses show it was you who robbed the bank. Court: %d h of prison and a %d coin fine. While you're inside you can't build, taxes and tourism are halved and the city is outraged." % [Data.JAIL_HOURS, fine]],
		[[["Отсидеть", "Serve the time"], "ok"], [["Залог (%d гемов)" % Data.JAIL_BAIL_GEMS, "Bail (%d gems)" % Data.JAIL_BAIL_GEMS], "bail"]])
	m.expires = Game.abs_hour() + Data.JAIL_HOURS


## Residents protest in front of the town hall: what they want and how the mayor can answer.
const PROTEST_DEMANDS := {
	"rob": ["«Мэр-вор — в отставку!» Люди требуют честности: мэр грабил банк, а платит город.",
		"\"Thief mayor, resign!\" People demand honesty: the mayor robbed a bank and the city pays for it."],
	"tax": ["«Налоги грабят семьи!» Жители требуют снизить налог до честного (сейчас %d%%).",
		"\"Taxes rob our families!\" Residents demand a fair tax (it's %d%% now)."],
	"demolish": ["«Не трогайте наши дома!» Людей выселяют и сносят их дома без спроса.",
		"\"Hands off our homes!\" People are evicted and their homes torn down without asking."],
	"mood": ["«Нам плохо живётся!» Жители недовольны жизнью в городе и хотят, чтобы их услышали.",
		"\"Life here is hard!\" Residents are unhappy with the city and want to be heard."],
	"rules": ["«Мэр нарушает правила города!» Нет нужных служб, мусор, дым — люди требуют порядка.",
		"\"The mayor breaks the city's rules!\" Missing services, garbage, smoke: people demand order."],
}


func protest_started(cause: String, site: int) -> void:
	var dem: Array = PROTEST_DEMANDS.get(cause, PROTEST_DEMANDS.mood)
	var ru := str(dem[0])
	var en := str(dem[1])
	if cause == "tax":
		ru = ru % Game.tax
		en = en % Game.tax
	var cost := Game.protest_talk_cost()
	var place: Array = Data.B[Game.buildings[site].id].name if Game.buildings.has(site) else ["ратуша", "town hall"]
	var opts := [[["Выслушать (%d)" % cost, "Hear them (%d)" % cost], "pr_talk"]]
	if Game.police_count() > 0:
		opts.append([["Разогнать полицией", "Send the police"], "pr_force"])
	opts.append([["Пусть стоят", "Let them be"], "pr_wait"])
	var m := post("protest", "alina", ["Митинг!", "Protest!"],
		["{Title}, у здания «%s» собрались жители с плакатами. %s Выслушать людей — дорого, но они успокоятся. Разогнать — быстро, но доверие упадёт и злость вырастет." % [place[0], ru],
		 "{Title}, residents with placards have gathered at the %s. %s Hearing them costs money but calms them down. Breaking it up is quick, but trust falls and anger grows." % [place[1], en]],
		opts, {"uid": site})
	m.expires = Game.abs_hour() + Data.PROTEST_HOURS


func rank_up(r: int) -> void:
	var k: Array = Data.RANKS[r]
	post("rank", "alina", ["Новое звание: %s" % k[2], "New rank: %s" % k[3]],
		["{Title}, город вас ценит! Теперь вы — «%s». Награда: %d монет и %d изумрудов; доходы города выросли на %d%%." % [k[2], 500 * r, r, k[4]],
		 "{Title}, the city values you! You are now «%s». Reward: %d coins and %d emeralds; the city's income grows by %d%%." % [k[3], 500 * r, r, k[4]]],
		[[["Спасибо!", "Thank you!"], "ok"]])


func protest_over() -> void:
	post("protest", "alina", ["Митинг закончился", "The protest is over"],
		["Люди разошлись, так ничего и не добившись. Злость осталась — если ничего не менять, они выйдут снова.",
		 "People went home with nothing. The anger is still there: if nothing changes, they will be back."],
		[[["Понятно", "Understood"], "ok"]])


# ---------------------------------------------------------------- natural events with a choice
const DZ_TEXT := {
	"flood": [["Наводнение!", "Flood!"],
		["{Title}, вода в реке поднимается и подступает к домам у берега. Дамбы и насосы стоят дорого, но город не пострадает; мешки с песком дешевле, но вода может прорваться; если ничего не делать — дома у воды зальёт.",
		 "{Title}, the water is rising and creeps up to the homes by the shore. Dikes and pumps cost a lot, but the city stays safe; sandbags are cheaper, but the water may break through; do nothing and the homes by the water will be flooded."],
		["Дамбы и насосы (%d)", "Dikes and pumps (%d)"], ["Мешки с песком (%d)", "Sandbags (%d)"], ["Ничего не делать", "Do nothing"]],
	"quake": [["Землетрясение!", "Earthquake!"],
		["{Title}, под городом дрожит земля, по улицам идут трещины. Можно вызвать инженеров и укрепить здания (дорого и надёжно), только подпереть самые опасные (дёшево, но риск обрушений) или надеяться на лучшее.",
		 "{Title}, the ground shakes under the city and cracks run across the streets. Call engineers and reinforce the buildings (costly and safe), prop up only the worst ones (cheap, but some may collapse) or hope for the best."],
		["Инженеры и укрепление (%d)", "Engineers and reinforcing (%d)"], ["Подпереть опасные дома (%d)", "Prop up the worst homes (%d)"], ["Надеяться на лучшее", "Hope for the best"]],
	"blizzard": [["Снежная буря!", "Blizzard!"],
		["{Title}, на город обрушилась снежная буря: дороги заметает, крыши трещат под снегом. Снегоуборочная техника справится надёжно (дорого); дворники с лопатами дешевле, но не везде успеют; без помощи город встанет, а крыши могут обрушиться.",
		 "{Title}, a blizzard hit the city: roads are buried and roofs creak under the snow. Snow ploughs are reliable (costly); janitors with shovels are cheaper but won't get everywhere; with no help the city grinds to a halt and roofs may fall in."],
		["Снегоуборочная техника (%d)", "Snow ploughs (%d)"], ["Дворники с лопатами (%d)", "Janitors with shovels (%d)"], ["Само растает", "It will melt"]],
	"tourists": [["Нашествие туристов!", "Tourist rush!"],
		["{Title}, в город хлынули туристы — толпы с фотоаппаратами у достопримечательностей. Можно нанять гидов и охрану (дорого, зато много дохода и порядок), просто открыть город (дёшево, будет мусор и шум) или не обращать внимания.",
		 "{Title}, tourists flood the city: crowds with cameras at the sights. Hire guides and guards (costly, but big income and order), simply open up the city (cheap, with litter and noise) or ignore it."],
		["Гиды и охрана (%d)", "Guides and guards (%d)"], ["Открыть город (%d)", "Open the city (%d)"], ["Не обращать внимания", "Ignore it"]],
}


func disaster_started(kind: String) -> void:
	var t: Array = DZ_TEXT[kind]
	var opts: Array = []
	for i in 3:
		var lab: Array = t[2 + i]
		if i < 2:
			var c := Game.disaster_cost(kind, i)
			lab = [str(lab[0]) % c, str(lab[1]) % c]
		opts.append([lab, "dz:%s:%d" % [kind, i]])
	var who := "marina" if kind == "tourists" else "oleg"
	var m := post("disaster", who, t[0], t[1], opts, {"dz": kind})
	m.expires = Game.abs_hour() + Data.DZ_HOURS


func disaster_result(kind: String, opt: int, hit: bool, n: int) -> void:
	var ru: String
	var en: String
	if kind == "tourists":
		ru = ["Гости довольны, казна пополнилась, в городе порядок.", "Туристы принесли доход, но оставили мусор и шум.", "Туристы побродили и уехали, оставив немного денег и мусора."][opt]
		en = ["The guests are happy, the treasury grew, the city is orderly.", "Tourists brought income but left litter and noise.", "Tourists wandered about and left, leaving a little money and litter."][opt]
	elif hit:
		ru = "Стихия нанесла ущерб: повреждено зданий — %d. Починить их можно в карточке здания." % n
		en = "The disaster did damage: %d buildings were damaged. Repair them from the building card." % n
	else:
		ru = ["Всё обошлось — меры сработали, город цел.", "Повезло: стихия прошла мимо, потерь нет.", "Повезло: стихия прошла мимо, потерь нет."][opt]
		en = ["All is well - the measures worked and the city is intact.", "Lucky: the disaster passed with no losses.", "Lucky: the disaster passed with no losses."][opt]
	Game.toast.emit(Loc.pick([ru, en]))


func start_fire(uid := 0) -> void:
	if uid == 0:
		var cands: Array[int] = []
		for u in Game.buildings:
			var b: Dictionary = Game.buildings[u]
			if b.built and not b.dmg and b.fire <= 0.0 and Data.B[b.id].cat not in ["decor"]:
				cands.append(u)
		if cands.is_empty():
			return
		uid = cands.pick_random()
	var b: Dictionary = Game.buildings[uid]
	var covered := Game.covered_by("fire", Vector2i(b.x, b.y))
	b.fire = 22.0 if covered else 30.0
	if not covered:
		b.dmg = true
		Game.add_rep(-2)
		post("fire", "oleg", ["Пожар!", "Fire!"],
			["Сгорело здание «%s». Пожарной части рядом нет. Ремонт стоит %d монет." % [Data.B[b.id].name[0], Game.repair_cost(uid)],
			 "\"%s\" burned down. There is no fire station nearby. Repairs cost %d coins." % [Data.B[b.id].name[1], Game.repair_cost(uid)]],
			[[["Отремонтировать", "Repair"], "repair"], [["Позже", "Later"], "ok"]], {"uid": uid})
	else:
		Game.spend_event("repairs", 40)
		Game.toast.emit(Loc.t("ev_fire_saved") % Data.name_of(b.id))
	Game.recalc()
	Game.building_updated.emit(uid)
	Game.sfx("siren")
	fire_started.emit(uid, covered)


# ====================================================================== story
func story_ready() -> int:
	var n := 0
	for s in story:
		if not s.claimed and story_value(s) >= int(s.n):
			n += 1
	return n


func story_value(s: Dictionary) -> int:
	return Game.mission_value({"type": s.type})


func add_story_mission(id: String, who: String, text: Array, type: String, n: int, coins: int, gems: int, rep: int) -> void:
	for s in story:
		if s.id == id:
			return
	story.append({"id": id, "who": who, "text": text, "type": type, "n": n, "coins": coins, "gems": gems, "rep": rep, "claimed": false})
	story_changed.emit()


func claim_story(id: String) -> void:
	for s in story:
		if s.id == id and not s.claimed and story_value(s) >= int(s.n):
			s.claimed = true
			Game.coins += int(s.coins)
			Game.gems += int(s.gems)
			Game.add_rep(float(s.rep))
			Game.sfx("done")
			Game.toast.emit(Loc.t("mission_done"))
			flags["done_" + id] = true
			story_changed.emit()
			_check_story()
			Game.save_game()
			return


func say(lines: Array) -> void:
	dialog.emit(lines)


func _line(who: String, expr: String, ru: String, en: String, choices := []) -> Dictionary:
	return {"who": who, "expr": expr, "text": [ru, en], "choices": choices}


func _check_story() -> void:
	if Game.tutorial < 99:
		return
	var lv := Game.level
	match chapter:
		0:
			chapter = 1
			say([_line("boris", "smile", "{Title} {name}! Я Борис Петрович, архитектор. Строил этот город ещё молодым. Рад, что у долины снова есть хозяин.",
					"Mayor {name}! I'm Boris, an architect. I built this town when I was young. Glad the valley has a mayor again."),
				_line("boris", "talk", "Людям нужны дома. Постройте пять домиков — и я пришлю вам свои старые чертежи.",
					"People need homes. Build five little houses and I'll send you my old blueprints.")])
			add_story_mission("boris_houses", "boris", ["Борис: 5 домиков", "Boris: 5 little houses"], "build:house_small", 5, 400, 1, 2)
		1:
			if lv >= 3 and flags.get("done_boris_houses", false):
				chapter = 2
				say([_line("viktor", "smug", "Добрый день, {title}. Виктор Громов, «Громов Индастриз». Продайте мне землю у реки под завод. Плачу 3 000 сразу.",
						"Good day, Mayor. Viktor Grom, Grom Industries. Sell me the land by the river for a plant. 3,000 coins right now."),
					_line("viktor", "talk", "Жители? Привыкнут к дыму. Деньги не пахнут.", "The residents? They'll get used to the smoke. Money doesn't smell.",
						[[["Продать (+3000, репутация −8)", "Sell (+3000, reputation −8)"], "viktor_sell"], [["Отказать", "Refuse"], "viktor_refuse"]])])
		2:
			if lv >= 4:
				chapter = 3
				say([_line("marina", "smile", "Марина Светлова, «Вестник долины». Можно вопрос для газеты? Жители спрашивают, будут ли расти налоги.",
						"Marina Bright, Valley Herald. A question for the paper? People ask whether taxes will go up."),
					_line("marina", "talk", "Что ответите?", "What do you say?",
						[[["Налоги не поднимем", "Taxes won't go up"], "marina_promise"], [["Если нужно для города — поднимем", "If the city needs it, yes"], "marina_honest"]])])
				add_story_mission("marina_happy", "marina", ["Марина: счастье 65%", "Marina: 65% happiness"], "happy", 65, 600, 1, 3)
		3:
			if Game.pop >= 120:
				chapter = 4
				say([_line("zina", "angry", "Милок, я сорок лет в этом городе живу. Где гулять внукам? Ни парка, ни скамейки!",
						"Dear, I've lived here forty years. Where do my grandkids play? No park, not a single bench!"),
					_line("zina", "talk", "Построй парк — и я за тебя на выборах всю улицу соберу.", "Build a park and I'll bring the whole street to vote for you.")])
				add_story_mission("zina_park", "zina", ["Баба Зина: парк", "Granny Zina: a park"], "build:park", 1, 500, 1, 5)
		4:
			if lv >= 6:
				chapter = 5
				say([_line("oleg", "worried", "Олег Смирнов, начальник полиции. Город растёт, а с ним и кражи. Мне нужен участок и машины.",
						"Oleg, police chief. The city is growing and so is theft. I need a station and patrol cars."),
					_line("oleg", "talk", "Постройте полицию — и мы будем ловить воров прямо на трассе.", "Build a police station and we'll catch thieves right on the highway.")])
				add_story_mission("oleg_police", "oleg", ["Олег: полиция", "Oleg: police station"], "build:police", 1, 800, 1, 4)
		5:
			if lv >= 7 or Game.day >= 9:
				chapter = 6
				var choices := [[["Опровергнуть (300)", "Deny it (300)"], "scandal_deny"], [["Промолчать", "Stay silent"], "scandal_silent"]]
				if Game.has_service("law"):
					choices.insert(0, [["Подать в суд", "Sue him"], "scandal_sue"])
				say([_line("marina", "worried", "{Title}, беда! Газеты Громова пишут, что вы берёте взятки. Это неправда, но люди читают.",
						"Mayor, trouble! Grom's papers say you take bribes. It's a lie, but people read it."),
					_line("viktor", "smug", "Ничего личного, {title}. Просто бизнес. Скоро выборы.", "Nothing personal, Mayor. Just business. Elections are coming.", choices)])
		6:
			if lv >= 9:
				chapter = 7
				say([_line("boris", "happy", "Вот и мои чертежи! Городу нужна больница. Это будет лучшее здание долины.",
						"Here are my blueprints! The city needs a hospital. It will be the finest building in the valley.")])
				add_story_mission("boris_hospital", "boris", ["Борис: больница", "Boris: a hospital"], "build:hospital", 1, 2500, 2, 5)
		7:
			if Game.day >= 14 and lv >= 8:
				chapter = 8
				election_day = Game.day + 4
				say([_line("marina", "surprised", "Срочные новости! Виктор Громов выдвигается в мэры. Выборы через 4 дня.",
						"Breaking news! Viktor Grom is running for mayor. The election is in 4 days."),
					_line("viktor", "smug", "Готовьте кабинет, {title}. Скоро он будет моим.", "Pack your office, Mayor. It will be mine soon."),
					_line("alina", "worried", "Голосуют за репутацию и счастье жителей. Поднимите оба показателя выше 55 — и победа наша!",
						"People vote on reputation and happiness. Get both above 55 and we'll win!")])
				add_story_mission("election_rep", "alina", ["Алина: репутация 60", "Alina: reputation 60"], "rep", 60, 1000, 1, 0)
		_:
			pass
	if chapter >= 2 and Game.caught.size() >= 1 and not flags.get("zoo_arc", false):
		flags["zoo_arc"] = true
		say([_line("zina", "happy", "Внучок увидел, как вы поймали зверька, и теперь мечтает о зоопарке! Поймайте пятерых — и стройте.",
				"My grandson saw you catch an animal and now dreams of a zoo! Catch five and build one.")])
		add_story_mission("zina_zoo", "zina", ["Баба Зина: зоопарк", "Granny Zina: the zoo"], "build:zoo", 1, 1500, 2, 5)
	elif chapter >= 7 and lv >= 13 and not flags.get("hall_arc", false):
		flags["hall_arc"] = true
		say([_line("boris", "smile", "Последний мой проект — ратуша. Пусть все видят, что у долины есть сердце.",
				"My last project is a town hall. Let everyone see the valley has a heart.")])
		add_story_mission("boris_hall", "boris", ["Борис: ратуша", "Boris: town hall"], "build:town_hall", 1, 5000, 3, 6)


func _story_act(act: String, _m: Dictionary) -> void:
	match act:
		"viktor_sell":
			flags["viktor_deal"] = true
			Game.earn_event("deals", 3000)
			Game.add_rep(-8)
			Game.add_mood(-5, 48, "viktor_plant")
		"viktor_refuse":
			flags["viktor_angry"] = true
			Game.add_rep(3)
			say([_line("viktor", "angry", "Вы ещё пожалеете, {title}.", "You'll regret this, Mayor.")])
		"marina_promise":
			flags["promise_tax"] = true
			Game.add_rep(4)
		"marina_honest":
			Game.add_rep(2)
		"scandal_sue":
			Game.earn_event("fines", 1000)
			Game.add_rep(6)
			say([_line("marina", "happy", "Суд на вашей стороне! Громову пришлось извиниться и заплатить.",
				"The court sided with you! Grom had to apologise and pay.")])
		"scandal_deny":
			if Game.pay(300, 0, "events"):
				Game.add_rep(-1)
			else:
				Game.add_rep(-5)
		"scandal_silent":
			Game.add_rep(-6)
	story_changed.emit()


func election_score() -> float:
	return Game.rep * 0.55 + Game.happy * 0.45


func _election() -> void:
	flags["election_done"] = true
	chapter = 9
	var score := election_score()
	if score >= 50.0:
		Game.coins += 5000
		Game.gems += 3
		Game.add_rep(10)
		say([_line("marina", "happy", "Итоги выборов: %d%% за вас! Вы остаётесь мэром!" % int(round(50 + (score - 50) * 1.5)),
				"Election results: %d%% for you! You remain mayor!" % int(round(50 + (score - 50) * 1.5))),
			_line("viktor", "angry", "Это ещё не конец...", "This isn't over..."),
			_line("alina", "happy", "Мы победили, {title}! Город верит в вас.", "We won, Mayor! The city believes in you.")])
	else:
		say([_line("marina", "worried", "Итоги выборов: победил Виктор Громов...", "Election results: Viktor Grom has won..."),
			_line("viktor", "smug", "Освобождайте кабинет. Долина теперь моя.", "Clear your desk. The valley is mine now.")])
		Game.lost = true
		Game.save_game()
		Game.game_over.emit()
	story_changed.emit()
