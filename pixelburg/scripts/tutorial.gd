class_name Tutorial
extends Control
## First steps with Alina: collect taxes, lay a road, build a house, then a tour of zones,
## money, mail and the rules of the city.

var hud
var _hint: PanelContainer
var _hint_text: Label
var _arrow: TextureRect
var _target: Callable          ## returns a screen position (virtual units) to point at, or Vector2.INF
var _waiting := false
var _check: Callable
var _start_roads := 0
var _start_houses := 0
var _t := 0.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_hint = PanelContainer.new()
	_hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_hint)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	_hint.add_child(h)
	var pic := TextureRect.new()
	pic.texture = Assets.face("alina", "smile")
	pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	pic.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	pic.custom_minimum_size = Vector2(40, 40)
	h.add_child(pic)
	_hint_text = hud.text("", h, 12, Color("2a2030"), 250)
	_arrow = TextureRect.new()
	_arrow.texture = Assets.ui_icon("upgrade")
	_arrow.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_arrow.size = Vector2(32, 32)
	_arrow.rotation = PI
	_arrow.pivot_offset = Vector2(16, 16)
	_arrow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_arrow.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	add_child(_arrow)
	_hint.visible = false
	_arrow.visible = false


func start() -> void:
	match Game.tutorial:
		0:
			hud.dialog.play([
				_l("happy", "Здравствуйте, {title} {name}! Я Алина, ваш заместитель. Добро пожаловать в нашу долину!",
					"Hello, Mayor {name}! I'm Alina, your deputy. Welcome to our valley!"),
				_l("talk", "Город пока маленький: несколько домов, пекарня, кафе и ферма. Но жители уже ждут от вас решений.",
					"The town is small for now: a few houses, a bakery, a café and a farm. But people already expect decisions from you."),
				_l("think", "С чего бы начать… Пожалуй, с самого простого — с денег.", "Where to start… With the simplest thing, I suppose: money."),
				_l("smile", "Давайте я покажу самое главное. Это займёт пару минут.", "Let me show you the essentials. It takes just a couple of minutes."),
			], func(): _step(1))
		_:
			_step(Game.tutorial)


## Only one thing can be done while the tutorial waits for it: the city takes just that action,
## the HUD only the named buttons.
func _lock(action: String, buttons: Array) -> void:
	hud.city.input_lock = action
	hud.gate(buttons)


func _houses() -> int:
	return Game.buildings.values().filter(func(b): return Data.B[b.id].cat == "home").size()


func _l(expr: String, ru: String, en: String) -> Dictionary:
	return {"who": "alina", "expr": expr, "text": [ru, en]}


func _step(n: int) -> void:
	Game.tutorial = n
	_waiting = false
	_hint.visible = false
	_arrow.visible = false
	_lock("", [])
	match n:
		1:
			_lock("collect", ["none"])
			_wait(["Над домиками висят монетки — это налоги жителей. Нажмите на дом, чтобы собрать их.",
				"Coins float above the houses: residents' taxes. Tap a house to collect them."],
				func(): return int(Game.stats.coins_total) > 0, _ready_bubble, 2)
		2:
			_lock("road", ["RoadButton"])
			_start_roads = Game.roads.size()
			_wait(["Без дорог здания не работают. Нажмите кнопку дорог и проведите дорогу пальцем, потом нажмите галочку.",
				"Buildings need roads. Tap the road button, drag a road with your finger, then tap the tick."],
				func(): return Game.roads.size() > _start_roads, func(): return _control_pos("RoadButton"), 3)
		3:
			_lock("build", ["BuildButton"])
			_start_houses = _houses()
			_wait(["Теперь постройте ещё один домик: кнопка «Строить», вкладка «Жильё». Дома — только в зоне города.",
				"Now build another little house: the Build button, Homes tab. Homes go only in the city zone."],
				func(): return _houses() > _start_houses,
				func(): return _control_pos("BuildButton"), 4)
		4:
			hud.dialog.play([
				_l("talk", "Отлично! Долина поделена на зоны: город, фермы, промзона и отдых. Фермы строят только в зоне ферм, заводы — в промзоне.",
					"Great! The valley is split into zones: city, farms, industry and leisure. Farms go in the farm zone, factories in the industrial zone."),
				_l("smile", "Фермы делают товары, а магазины их продают. Нет товаров — магазины стоят.",
					"Farms make goods and shops sell them. No goods, no sales."),
				_l("worried", "И главное — деньги. Каждый день город платит за содержание зданий, дорог и зарплаты. Смотрите отчёт в «Финансах».",
					"And money matters. Every day the city pays for building upkeep, roads and salaries. Check the report in Finance."),
				_l("talk", "В почту приходят письма: нарушения, просьбы жителей, идеи для бизнеса. Ваши решения влияют на репутацию.",
					"Letters arrive in the mailbox: violations, residents' requests, business ideas. Your decisions shape your reputation."),
				_l("worried", "Если счастье упадёт до нуля и больше половины жителей уедет — мэра снимут, и всё начнётся сначала. Берегите людей!",
					"If happiness drops to zero and most residents leave, the mayor is removed and everything starts over. Take care of people!"),
				_l("happy", "Удачи, {title}! Я буду рядом.", "Good luck, Mayor! I'll be around."),
			], func():
				Game.tutorial = 99
				Game.save_game())


func _wait(t: Array, check: Callable, target: Callable, next: int) -> void:
	_hint_text.text = Events.fmt(t)
	_hint.visible = true
	_hint.reset_size()
	_check = check
	_target = target
	_waiting = true
	_hint.set_meta("next", next)


## The collect bubble nearest the middle of the screen, clear of the top bar.
func _ready_bubble() -> Vector2:
	var best := Vector2.INF
	var mid: Vector2 = hud.root.size / 2
	for uid in hud.city.views:
		var v: BuildingView = hud.city.views[uid]
		if not v.bubble.visible:
			continue
		var p: Vector2 = hud.city.world_to_screen(v.global_position + v.bubble.position + Vector2(0, -70)) / hud.S
		if p.y < 70 or p.x < 20 or p.x > hud.root.size.x - 60 or p.y > hud.root.size.y - 40:
			continue
		if best == Vector2.INF or p.distance_to(mid) < best.distance_to(mid):
			best = p
	return best


func _control_pos(name: String) -> Vector2:
	var n: Control = hud.root.find_child(name, true, false)
	if n and n.is_visible_in_tree():
		return (n.global_position + Vector2(n.size.x / 2, -4) * hud.S) / hud.S
	return Vector2.INF


func _process(delta: float) -> void:
	_t += delta
	if not _waiting:
		return
	var p: Vector2 = _target.call() if _target.is_valid() else Vector2.INF
	var low: bool = p != Vector2.INF and p.y < hud.root.size.y * 0.5
	_hint.position = Vector2((hud.root.size.x - _hint.size.x) / 2, hud.root.size.y - _hint.size.y - 70 if low else 40)
	_arrow.visible = p != Vector2.INF and not hud.modal.visible
	if _arrow.visible:
		_arrow.position = p - Vector2(16, 32 + absf(sin(_t * 4.0)) * 8.0)
	if _check.call():
		_waiting = false
		Game.sfx("done")
		_step(int(_hint.get_meta("next")))
