class_name Panels
extends RefCounted
## Modal windows: finance and bank, inbox, missions, city rules, settings, land, animals and the zoo,
## building details, game over.

var hud


func _init(p_hud) -> void:
	hud = p_hud


func _vbox(sep := 6) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", sep)
	return v


func _hbox(sep := 6) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", sep)
	return h


func _card(parent: Node, pad := 6) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", hud._sb("card", 5, pad))
	parent.add_child(p)
	return p


func _w() -> float:
	return minf(440.0, hud.root.size.x - 60.0)


func _row(parent: Node, icon: String, label: String, value: String, col := Color("3a2a1e")) -> void:
	var h := _hbox(5)
	parent.add_child(h)
	if icon != "":
		hud.icon_rect(icon, h)
	var l: Label = hud.text(label, h, 12)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var v: Label = hud.text(value, h, 12, col)
	v.add_theme_font_override("font", hud.bold_font)


# ====================================================================== finance
func finance() -> void:
	var v := _vbox(6)
	var today: Dictionary = Game.today
	var inc := 0
	var out := 0
	for k in today.get("in", {}):
		inc += int(today["in"][k])
	for k in today.get("out", {}):
		out += int(today["out"][k])
	# summary
	var c := _card(v)
	var cv := _vbox(3)
	c.add_child(cv)
	hud.title(Loc.t("fin_today") % Game.day, cv, 13, Color("3a2a1e"))
	_row(cv, "coin", Loc.t("fin_income"), "+" + Loc.num(inc), Color("2a7a2a"))
	_row(cv, "finance", Loc.t("fin_expense"), "-" + Loc.num(out), Color("b83a2a"))
	var up := Game.daily_upkeep() + Game.daily_roads() + (int(Game.loan.daily) if not Game.loan.is_empty() else 0)
	_row(cv, "clock", Loc.t("fin_bills"), "-" + Loc.num(up), Color("b83a2a"))
	hud.text(Loc.t("fin_bills_note"), cv, 10, Color("8a6a4a"), _w() - 20)
	# chart of the last days
	var days: Array = Game.ledger.slice(maxi(0, Game.ledger.size() - 6)) + [today]
	var mx := 1
	for d in days:
		var a := 0
		var b := 0
		for k in d.get("in", {}):
			a += int(d["in"][k])
		for k in d.get("out", {}):
			b += int(d["out"][k])
		mx = maxi(mx, maxi(a, b))
	var cc := _card(v)
	var chart_v := _vbox(2)
	cc.add_child(chart_v)
	hud.title(Loc.t("fin_chart"), chart_v, 12, Color("3a2a1e"))
	var chart := _hbox(8)
	chart.alignment = BoxContainer.ALIGNMENT_CENTER
	chart_v.add_child(chart)
	for d in days:
		var a := 0
		var b := 0
		for k in d.get("in", {}):
			a += int(d["in"][k])
		for k in d.get("out", {}):
			b += int(d["out"][k])
		var col := _vbox(1)
		chart.add_child(col)
		var bars := _hbox(1)
		bars.custom_minimum_size = Vector2(0, 60)
		bars.alignment = BoxContainer.ALIGNMENT_CENTER
		col.add_child(bars)
		for pair in [[a, Color("4ab04a")], [b, Color("d85a4a")]]:
			var holder := VBoxContainer.new()
			holder.alignment = BoxContainer.ALIGNMENT_END
			holder.custom_minimum_size = Vector2(10, 60)
			bars.add_child(holder)
			var r := ColorRect.new()
			r.color = pair[1]
			r.custom_minimum_size = Vector2(10, maxf(1.0, 58.0 * pair[0] / mx))
			holder.add_child(r)
		var dl: Label = hud.text(str(int(d.get("day", 0))), col, 10, Color("6a5a4a"))
		dl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	# breakdown of yesterday
	if not Game.ledger.is_empty():
		var last: Dictionary = Game.ledger[-1]
		var bc := _card(v)
		var bv := _vbox(2)
		bc.add_child(bv)
		hud.title(Loc.t("fin_yesterday"), bv, 12, Color("3a2a1e"))
		for k in last.get("in", {}):
			_row(bv, "", Loc.t("led_" + str(k)), "+" + Loc.num(int(last["in"][k])), Color("2a7a2a"))
		for k in last.get("out", {}):
			_row(bv, "", Loc.t("led_" + str(k)), "-" + Loc.num(int(last["out"][k])), Color("b83a2a"))
	# taxes
	var tc := _card(v)
	var tv := _vbox(3)
	tc.add_child(tv)
	var th := _hbox(6)
	tv.add_child(th)
	hud.icon_rect("tax", th)
	var tl: Label = hud.title(Loc.t("fin_tax") % Game.tax, th, 13, Color("3a2a1e"))
	tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	th.add_child(hud.button("-", "", "red", func():
		Game.set_tax(Game.tax - 1)
		finance(), Vector2(30, 24)))
	th.add_child(hud.button("+", "", "green", func():
		Game.set_tax(Game.tax + 1)
		finance(), Vector2(30, 24)))
	hud.text(Loc.t("fin_tax_note"), tv, 10, Color("8a6a4a"), _w() - 20)
	# bank
	var bk := _card(v)
	var bkv := _vbox(4)
	bk.add_child(bkv)
	var bh := _hbox(6)
	bkv.add_child(bh)
	hud.icon_rect("bank", bh)
	hud.title(Data.name_of("bank"), bh, 13, Color("3a2a1e"))
	if not Game.has_service("bank"):
		hud.text(Loc.t("bank_none"), bkv, 11, Color("8a6a4a"), _w() - 20)
	else:
		if Game.loan.is_empty():
			hud.text(Loc.t("bank_loan_info") % int(Game.loan_rate() * 100), bkv, 11, Color("3a2a1e"), _w() - 20)
			var lh := _hbox(4)
			bkv.add_child(lh)
			for amount in Game.loan_offers():
				lh.add_child(hud.button(Loc.num(amount), "coin", "blue", func():
					hud.confirm(Loc.t("bank_loan_q") % [Loc.num(amount), Loc.num(int(amount * (1.0 + Game.loan_rate())))], func():
						Game.take_loan(amount)
						finance())))
		else:
			_row(bkv, "finance", Loc.t("bank_debt"), Loc.num(int(Game.loan.left)), Color("b83a2a"))
			bkv.add_child(hud.button(Loc.t("bank_repay"), "ok", "green", func():
				Game.repay_loan()
				finance()))
		_row(bkv, "coin", Loc.t("bank_deposit"), Loc.num(Game.deposit), Color("2a7a2a"))
		var dh := _hbox(4)
		bkv.add_child(dh)
		for amount in [500, 2000]:
			dh.add_child(hud.button("+" + Loc.num(amount), "", "green", func():
				Game.move_deposit(amount)
				finance()))
		dh.add_child(hud.button(Loc.t("bank_withdraw"), "", "orange", func():
			Game.move_deposit(-Game.deposit)
			finance()))
	hud.popup(Loc.t("finance"), "", [[Loc.t("close"), "blue", Callable()]], v)


# ====================================================================== inbox
func inbox() -> void:
	var v := _vbox(6)
	if Events.inbox.is_empty():
		hud.text(Loc.t("inbox_empty"), v, 12, Color("6a5a4a"), _w())
	for m in Events.inbox:
		var c := _card(v)
		var h := _hbox(8)
		c.add_child(h)
		var pic := TextureRect.new()
		pic.texture = Assets.face(m.get("from", "alina"), "worried" if m.kind in ["violation", "fire", "crime", "illness", "complaint"] else "smile")
		pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		pic.custom_minimum_size = Vector2(44, 44)
		pic.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		pic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		h.add_child(pic)
		var mv := _vbox(3)
		mv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(mv)
		hud.title(Loc.pick(m.title), mv, 12, Color("7a2a1a") if not m.done else Color("8a7a6a"))
		hud.text(Events.fmt(m.text), mv, 11, Color("3a2a1e") if not m.done else Color("8a7a6a"), _w() - 80)
		if not m.done:
			var bh := _hbox(4)
			mv.add_child(bh)
			for i in m.opts.size():
				var opt: Array = m.opts[i]
				var id := int(m.id)
				var color := "green" if i == 0 else "blue" if i < m.opts.size() - 1 else "grey"
				var b: Button = hud.button(Loc.pick(opt[0]), "", color, func():
					Events.resolve(id, i)
					inbox())
				b.add_theme_font_size_override("font_size", 11)
				bh.add_child(b)
		else:
			var chosen := int(m.get("chosen", -1))
			hud.text(Loc.t("inbox_done") if chosen >= 0 else Loc.t("inbox_expired"), mv, 10, Color("8a7a6a"))
	hud.popup(Loc.t("inbox"), "", [[Loc.t("close"), "blue", Callable()]], v)


# ====================================================================== missions
func missions() -> void:
	var v := _vbox(6)
	var story_open: Array = Events.story.filter(func(s): return not s.claimed)
	for s in story_open:
		var c := _card(v)
		var h := _hbox(8)
		c.add_child(h)
		var pic := TextureRect.new()
		pic.texture = Assets.face(s.who, "smile")
		pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		pic.custom_minimum_size = Vector2(40, 40)
		pic.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		h.add_child(pic)
		var mv := _vbox(2)
		mv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(mv)
		hud.title(Loc.pick(s.text), mv, 12, Color("7a2a1a"))
		var pr := _hbox(6)
		mv.add_child(pr)
		hud.text("%s / %s" % [Loc.num(mini(Events.story_value(s), int(s.n))), Loc.num(int(s.n))], pr, 11, Color("4a7a2a"))
		hud.price_row(int(s.coins), int(s.gems), true, pr)
		var done := Events.story_value(s) >= int(s.n)
		var id: String = s.id
		var b: Button = hud.button(Loc.t("claim"), "", "green" if done else "grey", func():
			Events.claim_story(id)
			missions())
		b.disabled = not done
		h.add_child(b)
	for i in Game.active_missions():
		var m: Dictionary = Data.MISSIONS[i]
		var c := _card(v)
		var h := _hbox(8)
		c.add_child(h)
		hud.icon_rect("mission", h, 24)
		var mv := _vbox(2)
		mv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(mv)
		hud.text(Loc.pick(m.text), mv, 12, Color("3a2a1e"), _w() - 150)
		var pr := _hbox(6)
		mv.add_child(pr)
		hud.text("%s / %s" % [Loc.num(mini(Game.mission_value(m), m.n)), Loc.num(m.n)], pr, 11, Color("4a7a2a"))
		hud.price_row(m.coins, m.gems, true, pr)
		var done := Game.mission_done(i)
		var b: Button = hud.button(Loc.t("claim"), "", "green" if done else "grey", func():
			Game.claim(i)
			missions())
		b.disabled = not done
		h.add_child(b)
	if v.get_child_count() == 0:
		hud.text(Loc.t("all_missions"), v, 12, Color("3a2a1e"), _w())
	hud.popup(Loc.t("missions"), "", [[Loc.t("close"), "blue", Callable()]], v)


# ====================================================================== city overview + rules
func city_info() -> void:
	var v := _vbox(5)
	var c := _card(v)
	var cv := _vbox(2)
	c.add_child(cv)
	_row(cv, "pop", Loc.t("ci_pop"), "%s / %s" % [Loc.num(Game.pop), Loc.num(Game.capacity)])
	_row(cv, "jobs", Loc.t("ci_jobs"), "%s / %s" % [Loc.num(Game.workers), Loc.num(Game.jobs)])
	_row(cv, "unhappy", Loc.t("ci_unemp"), "%d%%" % int(Game.unemployment * 100), Color("b83a2a") if Game.unemployment > 0.1 else Color("3a2a1e"))
	_row(cv, "power", Loc.t("ci_power"), "%d / %d kW" % [int(Game.power_supply), int(Game.power_demand)],
		Color("b83a2a") if Game.power_ratio < 0.85 else Color("3a2a1e"))
	_row(cv, "water", Loc.t("ci_water"), "%s / %s" % [Loc.num(Game.water_supply), Loc.num(Game.water_demand)],
		Color("b83a2a") if Game.water_ratio < 0.9 else Color("3a2a1e"))
	_row(cv, "happy", Loc.t("happy"), "%d%% → %d%%" % [int(Game.happy), int(Game.happy_target)])
	_row(cv, "reputation", Loc.t("rep"), str(int(Game.rep)))
	if Events.election_day > 0 and not Events.flags.get("election_done", false):
		_row(cv, "calendar", Loc.t("ci_election") % Events.election_day, "%d%%" % int(Events.election_score()),
			Color("2a7a2a") if Events.election_score() >= 50 else Color("b83a2a"))
	if Game.peak_pop >= 60:
		hud.text(Loc.t("ci_lose_note") % Loc.num(int(Game.peak_pop * 0.4)), cv, 10, Color("8a6a4a"), _w() - 20)
	hud.title(Loc.t("rules"), v, 13)
	for r in Data.RULES:
		var rc := _card(v, 4)
		var h := _hbox(6)
		rc.add_child(h)
		var broken: bool = Game.rules.get(r, false)
		hud.icon_rect("warn" if broken else "ok", h)
		hud.text(Loc.t("rule_" + r), h, 11, Color("b83a2a") if broken else Color("3a5a2a"), _w() - 40)
	if not Game.mood.is_empty():
		hud.title(Loc.t("moods"), v, 13)
		for m in Game.mood:
			_row(v, "", Loc.t("mood_" + str(m.why)), ("+" if int(m.v) > 0 else "") + str(int(m.v)),
				Color("2a7a2a") if int(m.v) > 0 else Color("b83a2a"))
	hud.popup(Loc.t("city"), "", [[Loc.t("laws"), "purple", laws], [Loc.t("close"), "blue", Callable()]], v)


## Laws: pass one from the ready list or repeal a passed one.
func laws() -> void:
	var v := _vbox(5)
	hud.text(Loc.t("laws_note") % [Game.laws.size(), Data.MAX_LAWS, Data.LAW_COST], v, 11, Color("8a6a4a"), _w() - 20)
	for id in Data.LAW_ORDER:
		var l: Dictionary = Data.LAWS[id]
		var on := Game.has_law(id)
		var c := _card(v, 4)
		var h := _hbox(6)
		c.add_child(h)
		hud.icon_rect("ok" if on else "law", h)
		var lv := _vbox(1)
		lv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(lv)
		hud.title(Loc.pick(l.name), lv, 12, Color("2a5a2a") if on else Color("7a2a1a"))
		hud.text(_law_effects(l), lv, 10, Color("3a2a1e"), _w() - 150)
		var can := on or (Game.laws.size() < Data.MAX_LAWS and Game.coins >= Data.LAW_COST)
		var b: Button = hud.button(Loc.t("law_off") if on else Loc.t("law_on") % Data.LAW_COST, "", "red" if on else ("green" if can else "grey"), func():
			Game.toggle_law(id)
			laws())
		b.disabled = not can
		h.add_child(b)
	hud.popup(Loc.t("laws"), "", [[Loc.t("back"), "blue", city_info]], v)


func _law_effects(l: Dictionary) -> String:
	var out: PackedStringArray = []
	for k in ["happy", "rep", "daily"]:
		if l.has(k):
			var n: float = l[k]
			out.append(Loc.t("lawfx_" + k) % [("+" if n > 0 and k != "daily" else "") + str(n if k == "rep" else int(n))])
	for k in ["biz", "tour", "power", "water", "fire", "crime"]:
		if l.has(k):
			var pc := int(round((float(l[k]) - 1.0) * 100.0))
			out.append(Loc.t("lawfx_" + k) % [("+" if pc > 0 else "") + str(pc) + "%"])
	return ", ".join(out)


## Watchtower: check residents' papers (a fine, +reputation, less crime risk for a while),
## or hold a gathering (coins, more happiness for a while). Each action has its own cooldown.
func watchtower(uid: int) -> void:
	if not Game.buildings.has(uid):
		return
	var v := _vbox(6)
	var cd_doc := Game.tower_cooldown(uid)
	var c1 := _card(v, 4)
	var h1 := _hbox(6)
	c1.add_child(h1)
	hud.icon_rect("police", h1)
	var lv1 := _vbox(1)
	lv1.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h1.add_child(lv1)
	hud.title(Loc.t("check_docs"), lv1, 12, Color("2a5a2a"))
	hud.text(Loc.t("check_docs_note") % [Data.TOWER_CHECK_MIN, Data.TOWER_CHECK_MAX], lv1, 10, Color("3a2a1e"), _w() - 150)
	var b1: Button = hud.button(Loc.t("check_docs_go") if cd_doc <= 0 else Loc.duration(cd_doc * Data.DAY_LENGTH / 24.0), "", "green" if cd_doc <= 0 else "grey", func():
		Game.check_documents(uid)
		watchtower(uid))
	b1.disabled = cd_doc > 0
	h1.add_child(b1)
	var cd_meet := Game.tower_cooldown(uid, true)
	var can_meet := cd_meet <= 0 and Game.coins >= Data.TOWER_MEETING_COST
	var c2 := _card(v, 4)
	var h2 := _hbox(6)
	c2.add_child(h2)
	hud.icon_rect("chat", h2)
	var lv2 := _vbox(1)
	lv2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h2.add_child(lv2)
	hud.title(Loc.t("meeting"), lv2, 12, Color("2a5a2a"))
	hud.text(Loc.t("meeting_note") % [Data.TOWER_MEETING_COST, Data.TOWER_MEETING_HAPPY], lv2, 10, Color("3a2a1e"), _w() - 150)
	var b2: Button = hud.button(Loc.t("meeting_go") % Data.TOWER_MEETING_COST if cd_meet <= 0 else Loc.duration(cd_meet * Data.DAY_LENGTH / 24.0), "", "green" if can_meet else "grey", func():
		Game.hold_meeting(uid)
		watchtower(uid))
	b2.disabled = not can_meet
	h2.add_child(b2)
	hud.popup(Loc.t("watchtower_title"), "", [[Loc.t("close"), "blue", Callable()]], v)


## The city paper: headlines picked by the state of the city (Game.paper_headlines).
func newspaper() -> void:
	var v := _vbox(5)
	hud.text(Loc.t("paper_day") % Game.day, v, 11, Color("8a6a4a"), _w())
	var list: Array = Game.paper_headlines()
	for k in list.slice(0, 5):
		var c := _card(v, 5)
		var h := _hbox(6)
		c.add_child(h)
		hud.icon_rect("newspaper", h)
		hud.text(Loc.t(k), h, 12, Color("3a2a1e"), _w() - 50)
	hud.popup(Loc.t("paper_title"), "", [[Loc.t("close"), "blue", Callable()]], v)


func garbage() -> void:
	var v := _vbox(5)
	var lvl: String = Game.garbage_level()
	hud.text(Loc.t("gb_none") if Game.garbage_depots().is_empty() else Loc.t("gb_" + lvl), v, 12, Color("3a2a1e"), _w())
	_row(v, "demolish", Loc.t("gb_pile"), "%d%%" % int(Game.garbage), Color("c03a2a") if lvl == "high" else Color("3a2a1e"))
	_row(v, "pop", Loc.t("gb_made"), "%.1f" % Game.garbage_rate())
	_row(v, "jobs", Loc.t("gb_cap"), str(Game.garbage_capacity()))
	_row(v, "build", Loc.t("gb_depots"), str(Game.garbage_depots().size()))
	hud.popup(Loc.t("gb_title"), "", [[Loc.t("close"), "blue", Callable()]], v)


## The airport: flight routes to buy and where the travellers come from.
func airport() -> void:
	var v := _vbox(5)
	hud.text(Loc.t("air_text") if Game.airport_uid() != 0 else Loc.t("air_closed"), v, 12,
		Color("3a2a1e") if Game.airport_uid() != 0 else Color("b83a2a"), _w())
	var stats: Array = Game.arrival_stats()
	var total := Game.arrivals_total()
	_row(v, "plane", Loc.t("air_routes"), "%d / %d" % [Game.flights.size(), Data.COUNTRY_ORDER.size()])
	_row(v, "pop", Loc.t("air_today"), Loc.num(Game.arrivals_total(true)))
	_row(v, "pop", Loc.t("air_all"), Loc.num(total))
	if not stats.is_empty():
		_row(v, "happy", Loc.t("air_top"), Data.country_name(stats[0][0]), Color("2a7a2a"))
	hud.title(Loc.t("air_stats"), v, 13)
	if stats.is_empty():
		hud.text(Loc.t("air_none"), v, 11, Color("6a5a4a"), _w())
	var bar_w := _w() - 190.0
	for st in stats:
		var c := _card(v, 4)
		var h := _hbox(6)
		c.add_child(h)
		_flag(st[0], h)
		var l: Label = hud.text(Data.country_name(st[0]), h, 11, Color("3a2a1e"))
		l.custom_minimum_size.x = 96
		var bar := Control.new()
		bar.custom_minimum_size = Vector2(bar_w, 10)
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(bar)
		var back := ColorRect.new()
		back.color = Color("e8dcc4")
		back.size = Vector2(bar_w, 10)
		bar.add_child(back)
		var fill := ColorRect.new()
		fill.color = Color(Data.COUNTRIES[st[0]].flag[1]).darkened(0.1) if Data.COUNTRIES[st[0]].flag[1] != "ffffff" else Color("4a8ac8")
		fill.size = Vector2(maxf(2.0, bar_w * float(st[1]) / maxf(1.0, float(stats[0][1]))), 10)
		bar.add_child(fill)
		hud.text("%s · %d%%" % [Loc.num(st[1]), int(round(100.0 * st[1] / maxf(1.0, total)))], h, 11, Color("4a7a2a"))
	hud.title(Loc.t("air_buy"), v, 13)
	for id in Data.COUNTRY_ORDER:
		var co: Dictionary = Data.COUNTRIES[id]
		var c := _card(v, 4)
		var h := _hbox(6)
		c.add_child(h)
		_flag(id, h)
		var l: Label = hud.text(Data.country_name(id), h, 12, Color("3a2a1e"))
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		if Game.flights.has(id):
			hud.text(Loc.t("air_owned"), h, 11, Color("2a7a2a"))
			continue
		if Game.level < int(co.lvl):
			hud.text(Loc.t("air_lvl") % int(co.lvl), h, 11, Color("8a6a4a"))
			continue
		var ok: bool = Game.has_airport() and Game.can_afford(int(co.cost), 0)
		var b: Button = hud.button(Loc.num(int(co.cost)), "coin", "green" if ok else "grey", func():
			Game.buy_flight(id)
			airport())
		b.disabled = not ok
		h.add_child(b)
	hud.popup(Loc.t("air_title"), "", [[Loc.t("close"), "blue", Callable()]], v)


func _flag(id: String, parent: Node) -> void:
	var f := VBoxContainer.new()
	f.add_theme_constant_override("separation", 0)
	f.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	for col in Data.COUNTRIES[id].flag:
		var r := ColorRect.new()
		r.color = Color(col)
		r.custom_minimum_size = Vector2(20, 4)
		f.add_child(r)
	parent.add_child(f)


func building_details(uid: int) -> void:
	if not Game.buildings.has(uid):
		return
	var b: Dictionary = Game.buildings[uid]
	var d: Dictionary = Data.B[b.id]
	var v := _vbox(4)
	hud.text(Loc.t("desc_" + d.cat), v, 12, Color("3a2a1e"), _w())
	_row(v, "land", Loc.t("zone"), ", ".join(d.zones.map(func(z): return Data.zone_name(z))))
	if d.has("radius") and int(d.radius) > 0 and int(d.radius) < 900:
		_row(v, "info", Loc.t("radius"), str(d.radius))
	if d.has("hist"):
		_row(v, "info", Loc.t("hist_tour"), "+%d" % Game.hist_tourists(uid))
	if d.has("park") and hud.city.life:
		_row(v, "info", Loc.t("park_places"), "%d / %d" % [hud.city.life.garage_used(uid), Life.garage_capacity(uid)])
	if Game.quarter_of.has(uid):
		_row(v, "wall", Loc.t("quarter"), Loc.t("quarter_homes") % int(Game.quarter_of[uid].homes))
	if str(Game.buildings[uid].get("hlamp", "")) != "":
		_row(v, "moon", Loc.t("house_lamp"), Loc.t("lamp_" + Game.buildings[uid].hlamp))
	if d.cat == "home" and Game.home_reasons.has(uid):
		hud.title(Loc.t("why_happy"), v, 12)
		for r in Game.home_reasons[uid]:
			_row(v, "happy" if int(r[1]) > 0 else "unhappy", Loc.t(str(r[0])), ("+" if int(r[1]) > 0 else "") + str(r[1]),
				Color("2a7a2a") if int(r[1]) > 0 else Color("b83a2a"))
	var bid := Data.brand_of(b.id)
	if bid != "":
		_row(v, "star", Loc.t("brand"), "«%s»" % Data.brand_name(bid))
		_row(v, "shop", Loc.t("brand_chain"), Loc.t("brand_chain_v") % [Game.brand_branches(bid).size(), Game.brand_level(bid)])
		hud.text(Loc.t("brand_note") % Loc.pick(Data.BRANDS[bid].sells), v, 11, Color("6a5a4a"), _w())
	elif b.priv != "":
		hud.text(Loc.t("private_note"), v, 11, Color("6a5a4a"), _w())
	hud.popup(Data.name_of(b.id), "", [[Loc.t("close"), "blue", Callable()]], v)


# ====================================================================== land / plots
func land_info() -> void:
	var v := _vbox(4)
	hud.text(Loc.t("land_info"), v, 12, Color("3a2a1e"), _w())
	for z in Data.ZONES:
		var h := _hbox(6)
		v.add_child(h)
		hud.icon_rect({"city": "build", "farm": "goods", "industry": "jobs", "leisure": "zoo"}[z], h)
		hud.text(Data.zone_name(z) + " — " + Loc.t("zone_desc_" + z), h, 11, Color("3a2a1e"), _w() - 30)
	var conn := Game.is_connected_to_highway()
	hud.text(Loc.t("highway_yes") if conn else Loc.t("highway_no"), v, 11, Color("2a7a2a") if conn else Color("8a5a2a"), _w())
	hud.popup(Loc.t("land"), "", [[Loc.t("ok"), "blue", Callable()]], v)


func beach_plot(i: int) -> void:
	if Game.beach.has(i):
		hud.popup(Loc.t("beach_title"), Loc.t("beach_owned"), [[Loc.t("ok"), "blue", Callable()]])
		return
	if not Game.beach_buyable(i):
		hud.popup(Loc.t("beach_title"), Loc.t("beach_far"), [[Loc.t("ok"), "blue", Callable()]])
		return
	var price := Data.beach_price(Game.beach.size())
	var buttons := [[Loc.t("cancel"), "red", Callable()]]
	if Game.level >= price.level:
		buttons.append([Loc.num(price.coins), "green", func(): Game.buy_beach(i, false), "coin"])
	buttons.append([str(price.gems), "purple", func(): Game.buy_beach(i, true), "gem"])
	var t := Loc.t("beach_text")
	if Game.level < price.level:
		t += "\n" + Loc.t("plot_lvl") % price.level
	hud.popup(Loc.t("beach_title"), t, buttons)


func plot(p: Vector2i) -> void:
	if p.x < 0:
		beach_plot(p.y)
		return
	var z := Data.zone_of_plot(p)
	if not Game.plot_buyable(p):
		hud.popup(Loc.t("plot_title"), Loc.t("plot_far") + "\n" + Loc.t("zone") + ": " + Data.zone_name(z), [[Loc.t("ok"), "blue", Callable()]])
		return
	var price := Data.plot_price(Game.plots.size())
	var buttons := [[Loc.t("cancel"), "red", Callable()]]
	if Game.level >= price.level:
		buttons.append([Loc.num(price.coins), "green", func(): Game.buy_plot(p, false), "coin"])
	buttons.append([str(price.gems), "purple", func(): Game.buy_plot(p, true), "gem"])
	var t := Loc.t("plot_text") % Data.zone_name(z) + "\n" + Loc.t("zone_desc_" + z)
	if Game.level < price.level:
		t += "\n" + Loc.t("plot_lvl") % price.level
	hud.popup(Loc.t("plot_title"), t, buttons)


# ====================================================================== animals & zoo
func animals() -> void:
	var v := _vbox(5)
	hud.text(Loc.t("zoo_info") % [Data.ZOO_ANIMALS, Data.CATCH_COST], v, 12, Color("3a2a1e"), _w())
	var h := _hbox(4)
	v.add_child(h)
	var counts := {}
	for s in Game.caught:
		counts[s] = int(counts.get(s, 0)) + 1
	for s in Data.ANIMALS:
		var c := _card(h, 4)
		var cv := _vbox(1)
		c.add_child(cv)
		var at := AtlasTexture.new()
		at.atlas = Assets.tex("units/animal_" + s)
		var size: Array = Assets.units().animals[s].cell
		at.region = Rect2(0, 0, size[0], size[1])
		var pic := TextureRect.new()
		pic.texture = at
		pic.custom_minimum_size = Vector2(48, 36)
		pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		pic.modulate = Color.WHITE if counts.has(s) else Color(0.2, 0.2, 0.25, 0.6)
		cv.add_child(pic)
		var l: Label = hud.text("%s ×%d" % [Loc.t("animal_" + s), int(counts.get(s, 0))], cv, 10)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_row(v, "paw", Loc.t("zoo_caught"), "%d / %d" % [Game.caught.size(), Data.ZOO_ANIMALS],
		Color("2a7a2a") if Game.caught.size() >= Data.ZOO_ANIMALS else Color("3a2a1e"))
	hud.popup(Loc.t("zoo"), "", [[Loc.t("close"), "blue", Callable()]], v)


func catch_animal(a: ForestAnimal) -> void:
	var sp := a.species
	var chance := int(Game.catch_chance(sp) * 100)
	hud.popup(Loc.t("animal_" + sp), Loc.t("catch_q") % [Loc.t("animal_" + sp), Data.CATCH_COST, chance],
		[[Loc.t("cancel"), "red", Callable()], [Loc.t("catch"), "green", func():
			var r := Game.try_catch(sp)
			if r == 1:
				hud.toast(Loc.t("caught") % Loc.t("animal_" + sp))
				if is_instance_valid(a):
					a.queue_free()
			elif r == 0:
				hud.toast(Loc.t("escaped"))
				if is_instance_valid(a):
					a.life = 0.5, "paw"]])


# ====================================================================== settings
## "What's new" after an update, shown once per version (and from the settings).
func whats_new() -> void:
	Game.set_setting("news", Data.NEWS_VERSION)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	for item in Data.NEWS:
		hud.text("• " + Loc.pick(item), v, 12, Color("3a2a1e"), _w())
	hud.popup(Loc.t("whats_new") % Data.NEWS_VERSION, "", [[Loc.t("ok"), "green", Callable()]], v, 300)


func settings() -> void:
	var v := _vbox(5)
	v.add_child(hud.button("%s: %s" % [Loc.t("sound"), Loc.t("on" if Game.settings.sound else "off")], "sound", "blue", func():
		Game.set_setting("sound", not Game.settings.sound)
		settings()))
	v.add_child(hud.button("%s: %s" % [Loc.t("music"), Loc.t("on" if Game.settings.music else "off")], "music", "blue", func():
		Game.set_setting("music", not Game.settings.music)
		settings()))
	var sz := _hbox(6)
	sz.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(sz)
	var minus: Button = hud.button("−", "", "blue", func():
		hud.step_ui_scale(-1)
		settings(), Vector2(34, 26))
	minus.disabled = hud.ui_scale() <= hud.UI_SCALES[0]
	sz.add_child(minus)
	var sl: Label = hud.text("%s: %d%%" % [Loc.t("ui_scale"), roundi(hud.ui_scale() * 100.0)], sz, 12, Color("3a2a1e"))
	sl.custom_minimum_size.x = 130
	sl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var plus: Button = hud.button("+", "", "blue", func():
		hud.step_ui_scale(1)
		settings(), Vector2(34, 26))
	plus.disabled = hud.ui_scale() >= hud.max_ui_scale()
	sz.add_child(plus)
	v.add_child(hud.button(Loc.t("language"), "globe", "blue", func():
		Game.set_setting("lang", "en" if Loc.lang == "ru" else "ru")
		settings()))
	v.add_child(hud.button(Loc.t("profile"), "pop", "blue", profile))
	v.add_child(hud.button(Loc.t("backup"), "backup", "green", backup))
	v.add_child(hud.button(Loc.t("privacy"), "info", "blue", privacy))
	v.add_child(hud.button(Loc.t("whats_new") % Data.NEWS_VERSION, "news", "blue", whats_new))
	v.add_child(hud.button(Loc.t("credits"), "heart", "blue", func():
		hud.popup(Loc.t("credits"), Loc.t("credits_text"), [[Loc.t("ok"), "blue", settings]])))
	if OS.get_name() != "Web":
		v.add_child(hud.button(Loc.t("quit_game"), "exit", "orange", func(): hud.city.quit_game()))
	v.add_child(hud.button(Loc.t("reset"), "", "red", func():
		hud.confirm(Loc.t("reset_q"), func():
			Game.reset_game()
			hud.get_tree().reload_current_scene())))
	hud.popup(Loc.t("settings"), "", [[Loc.t("close"), "blue", Callable()]], v, 260)


func profile() -> void:
	var p: Dictionary = Game.profile
	var t := "%s: %s\n%s: %s\n%s: %s" % [Loc.t("pf_name"), p.name, Loc.t("pf_age"), str(p.age),
		Loc.t("pf_gender"), Loc.t("pf_f") if p.gender == "f" else Loc.t("pf_m") if p.gender == "m" else "-"]
	hud.popup(Loc.t("profile"), t + "\n\n" + Loc.t("pf_local"), [[Loc.t("pf_delete"), "red", func():
		hud.confirm(Loc.t("pf_delete_q"), func():
			Game.delete_personal_data()
			hud.get_tree().reload_current_scene())], [Loc.t("ok"), "blue", settings]])


func privacy() -> void:
	var v := _vbox(4)
	hud.text(Loc.t("privacy_full"), v, 13, Color("3a2a1e"), _w())
	hud.popup(Loc.t("privacy"), "", [[Loc.t("ok"), "blue", settings]], v)


func backup() -> void:
	var v := _vbox(5)
	hud.text(Loc.t("backup_text"), v, 11, Color("3a2a1e"), _w())
	var code := Game.export_code()
	v.add_child(hud.button(Loc.t("backup_copy"), "backup", "green", func():
		DisplayServer.clipboard_set(code)
		hud.toast(Loc.t("backup_copied"))))
	var edit := TextEdit.new()
	edit.placeholder_text = Loc.t("backup_paste")
	edit.custom_minimum_size = Vector2(_w(), 60)
	edit.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	v.add_child(edit)
	v.add_child(hud.button(Loc.t("backup_restore"), "upgrade", "orange", func():
		var c := edit.text if edit.text.strip_edges() != "" else DisplayServer.clipboard_get()
		if Game.import_code(c):
			hud.close_modal()
			hud.get_tree().reload_current_scene()
		else:
			hud.toast(Loc.t("backup_bad"))))
	hud.popup(Loc.t("backup"), "", [[Loc.t("close"), "blue", settings]], v)


# ====================================================================== game over
func game_over() -> void:
	var election: bool = Events.flags.get("election_done", false) and Events.chapter == 9 and Game.lost and Events.election_score() < 50
	var t := Loc.t("lose_election") if election else Loc.t("lose_text")
	t += "\n\n" + Loc.t("lose_stats") % [Game.day, Loc.num(Game.peak_pop), Game.level]
	hud.popup(Loc.t("lose_title"), t, [[Loc.t("lose_restart"), "green", func():
		Game.reset_game()
		hud.get_tree().reload_current_scene()]])
