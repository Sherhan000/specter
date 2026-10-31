class_name CitizenPanels
extends RefCounted
## Windows about the residents: the analytics panel (money, wages, health, births and deaths), the mayor's prices
## for light, water and fares, the list of residents and a resident's card.

var hud


func _init(p_hud) -> void:
	hud = p_hud


func _vbox(sep := 5) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", sep)
	return v


func _hbox(sep := 5) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", sep)
	return h


func _card(parent: Node) -> VBoxContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", hud._sb("card", 5, 6))
	parent.add_child(p)
	var v := _vbox(2)
	p.add_child(v)
	return v


func _w() -> float:
	return minf(440.0, hud.root.size.x - 60.0)


func _row(parent: Node, label: String, value: String, col := Color("3a2a1e")) -> void:
	var h := _hbox(5)
	parent.add_child(h)
	var l: Label = hud.text(label, h, 12)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var v: Label = hud.text(value, h, 12, col)
	v.add_theme_font_override("font", hud.bold_font)


func _t(ru: String, en: String) -> String:
	return Loc.pick([ru, en])


# ---------------------------------------------------------------- analytics
func analytics() -> void:
	var cz: Citizens = Game.cz
	var s := cz.summary()
	var k := cz.scale
	var v := _vbox(5)
	if s.n == 0:
		hud.text(_t("В городе пока нет жителей.", "There are no residents yet."), v, 12, Color("3a2a1e"), _w())
		hud.popup(_t("Жители", "Residents"), "", [[Loc.t("close"), "blue", Callable()]], v)
		return
	hud.title(_t("Деньги жителей", "Residents' money"), v, 13)
	var c := _card(v)
	_row(c, _t("Всего у жителей", "Total in wallets"), Loc.num(int(s.wallet * k)))
	_row(c, _t("Средний кошелёк", "Average wallet"), Loc.num(int(s.wallet / float(s.n))))
	var wsum := 0.0
	var wn := 0
	for p in s.wages:
		wsum += s.wages[p]
		wn += int(s.wage_n[p])
	_row(c, _t("Средняя зарплата в день", "Average daily wage"), Loc.num(int(wsum / maxf(1.0, wn))))
	_row(c, _t("Без работы", "Unemployed"), "%d / %d" % [int(s.jobless * k), int(s.adults * k)], Color("b83a2a") if s.jobless > s.adults * 0.25 else Color("3a2a1e"))
	_row(c, _t("В бедности", "In poverty"), str(int(s.poor * k)), Color("b83a2a") if s.poor > 0 else Color("3a2a1e"))
	_row(c, _t("Платят городу за свет, воду, проезд", "Paid to the city for power, water, fares"), "+%s/%s" % [Loc.num(cz.last_util), _t("день", "day")], Color("2a7a2a"))
	hud.title(_t("Зарплаты по профессиям", "Wages by profession"), v, 13)
	var c2 := _card(v)
	var profs: Array = s.wages.keys()
	profs.sort_custom(func(a, b): return s.wages[a] / s.wage_n[a] > s.wages[b] / s.wage_n[b])
	if profs.is_empty():
		hud.text(_t("Пока никто не работает.", "Nobody works yet."), c2, 11, Color("8a6a4a"), _w() - 20)
	for p in profs:
		_row(c2, "%s (%d)" % [Citizens.prof_name(p), int(s.wage_n[p] * k)], Loc.num(int(s.wages[p] / s.wage_n[p])))
	hud.title(_t("Образование", "Education"), v, 13)
	var c3 := _card(v)
	for i in 3:
		_row(c3, Loc.pick(Citizens.EDU_NAMES[i]), str(int(s.edu[i] * k)))
	hud.title(_t("Здоровье и население", "Health and population"), v, 13)
	var c4 := _card(v)
	_row(c4, _t("Дети / школьники", "Kids / students"), "%d / %d" % [int(s.kids * k), int(s.students * k)])
	_row(c4, _t("Взрослые / пенсионеры", "Adults / retired"), "%d / %d" % [int(s.adults * k), int(s.retired * k)])
	_row(c4, _t("Больных", "Sick"), str(int(s.sick * k)), Color("b83a2a") if s.sick > s.n * 0.1 else Color("3a2a1e"))
	_row(c4, _t("Родилось всего", "Births in total"), str(int(cz.stats.births)), Color("2a7a2a"))
	_row(c4, _t("Умерло всего", "Deaths in total"), str(int(cz.stats.deaths)))
	for cause in Citizens.CAUSES:
		if int(cz.stats.causes.get(cause, 0)) > 0:
			_row(c4, "   " + Loc.pick(Citizens.CAUSE_NAMES[cause]), str(int(cz.stats.causes[cause])), Color("6a5a4a"))
	if not Game.has_service("health"):
		hud.text(_t("Нет больницы или поликлиники — больные выздоравливают хуже и чаще умирают.", "No hospital or clinic — the sick recover worse and die more often."), v, 11, Color("b83a2a"), _w())
	for e in cz.stats.recent.slice(0, 4):
		hud.text("• " + Loc.pick(e), v, 10, Color("6a5a4a"), _w())
	hud.popup(_t("Жители", "Residents"), "", [[_t("Цены", "Prices"), "green", prices], [_t("Список", "List"), "purple", list],
		[Loc.t("close"), "blue", Callable()]], v, 440)


# ---------------------------------------------------------------- the mayor's prices
func prices() -> void:
	var cz: Citizens = Game.cz
	var v := _vbox(6)
	hud.text(_t("Цены задаёте вы. Дорогие свет, вода и проезд приносят больше монет, но злят жителей и пустят их кошельки; дешёвые радуют людей.",
		"You set the prices. Expensive power, water and fares bring more coins but anger residents and drain their wallets; cheap ones make people happy."), v, 11, Color("8a6a4a"), _w() - 20)
	for key in [["power", "Свет", "Power"], ["water", "Вода", "Water"], ["fare", "Проезд", "Fares"]]:
		var c := _card(v)
		var h := _hbox(6)
		c.add_child(h)
		var l: Label = hud.text(_t(key[1], key[2]), h, 13)
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(hud.button("−", "", "blue", func():
			cz.set_price(key[0], -1)
			prices(), Vector2(40, 28)))
		var pl: Label = hud.text("×%.2f" % float(cz.prices[key[0]]), h, 13)
		pl.custom_minimum_size.x = 56
		pl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		h.add_child(hud.button("+", "", "blue", func():
			cz.set_price(key[0], 1)
			prices(), Vector2(40, 28)))
	var avg := cz.price_avg()
	var note := _t("Цены обычные.", "Prices are normal.")
	if avg >= 1.5:
		note = _t("Слишком дорого: жители недовольны.", "Too expensive: residents are unhappy.")
	elif avg <= 0.75:
		note = _t("Дёшево: жители довольны, но доход города меньше.", "Cheap: residents are glad, but the city earns less.")
	hud.text(note, v, 12, Color("3a2a1e"), _w() - 20)
	hud.popup(_t("Цены города", "City prices"), "", [[Loc.t("back"), "blue", analytics]], v)


# ---------------------------------------------------------------- list and card
func list() -> void:
	var cz: Citizens = Game.cz
	var v := _vbox(3)
	var shown := cz.list.duplicate()
	shown.sort_custom(func(a, b): return int(a.wallet) > int(b.wallet))
	for c in shown.slice(0, 14):
		var cc: Dictionary = c
		var b: Button = hud.button("%s, %d — %s" % [Loc.pick(cc.name), int(cc.age), Citizens.prof_name(cc.job) if cz.is_adult(cc) else _group_name(cz.age_group(cc))],
			"", "blue", func(): card(int(cc.id)), Vector2(0, 24))
		v.add_child(b)
	hud.popup(_t("Жители", "Residents"), "", [[Loc.t("back"), "blue", analytics]], v, 440)


func _group_name(g: String) -> String:
	return {"kid": _t("ребёнок", "child"), "student": _t("школьник", "student"), "retired": _t("пенсионер", "retired"), "adult": _t("взрослый", "adult")}[g]


func card(id: int) -> void:
	var cz: Citizens = Game.cz
	var c := cz.by_id(id)
	if c.is_empty():
		list()
		return
	var v := _vbox(4)
	var cd := _card(v)
	_row(cd, _t("Возраст", "Age"), str(int(c.age)))
	_row(cd, _t("Профессия", "Profession"), Citizens.prof_name(c.job) if cz.is_adult(c) else _group_name(cz.age_group(c)))
	_row(cd, _t("Образование", "Education"), Loc.pick(Citizens.EDU_NAMES[int(c.edu)]))
	if int(c.study) > 0:
		_row(cd, _t("Учится", "Studying"), _t("IT-курсы (ещё %d дн.)", "IT course (%d more days)") % int(c.study), Color("6a3fd0"))
	if c.job != "":
		_row(cd, _t("Зарплата в день", "Daily wage"), Loc.num(cz.wage_of(c)))
		_row(cd, _t("Стаж", "Career"), _t("%d дн., ступень %d", "%d days, step %d") % [int(c.career), int(c.rank) + 1])
	_row(cd, _t("Кошелёк", "Wallet"), Loc.num(int(c.wallet)), Color("b83a2a") if int(c.poor) > 0 else Color("3a2a1e"))
	_row(cd, _t("Здоровье", "Health"), _t("болеет (%d дн.)", "sick (%d days)") % int(c.sick) if int(c.sick) > 0 else _t("здоров", "healthy"),
		Color("b83a2a") if int(c.sick) > 0 else Color("2a7a2a"))
	hud.popup(Loc.pick(c.name), "", [[Loc.t("back"), "blue", list]], v, 360)


## A resident on the street was tapped: show a card of someone from that home who matches the role.
func card_for_person(p) -> void:
	var cz: Citizens = Game.cz
	var pick: Dictionary = {}
	var want: Array = {"child": ["kid", "student"], "retired": ["retired"], "adult": ["adult"]}.get(p.role, ["adult"])
	for c in cz.list:
		if int(c.home) == p.home and cz.age_group(c) in want:
			if not p.get("cid", 0) or int(c.id) == int(p.cid):
				pick = c
				if int(c.id) == int(p.get("cid", 0)):
					break
	if pick.is_empty():
		for c in cz.list:
			if cz.age_group(c) in want:
				pick = c
				break
	if pick.is_empty():
		return
	p.cid = int(pick.id)
	card(int(pick.id))
