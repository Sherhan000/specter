extends Node
## Localisation (Russian / English), resident phrases and the privacy policy text.

signal changed

const S := {
	"title": ["Пиксельбург", "Pixelburg"],
	"intro_sub": ["Построй город своей мечты", "Build the town of your dreams"],
	"intro_tap": ["Нажмите, чтобы начать", "Tap to begin"],
	"mayor_m": ["господин мэр", "Mayor"],
	"mayor_f": ["госпожа мэр", "Mayor"],
	"coins": ["Монеты", "Coins"],
	"gems": ["Изумруды", "Emeralds"],
	"goods": ["Товары", "Goods"],
	"pop": ["Жители", "Residents"],
	"happy": ["Счастье", "Happiness"],
	"rep": ["Репутация", "Reputation"],
	"level": ["Уровень", "Level"],
	"lvl_short": ["Ур.", "Lv."],
	"per_day": ["день", "day"],
	"cat_home": ["Жильё", "Homes"],
	"cat_shop": ["Бизнес", "Shops"],
	"cat_ind": ["Производство", "Industry"],
	"cat_service": ["Службы", "Services"],
	"cat_fun": ["Отдых", "Leisure"],
	"cat_decor": ["Декор", "Decor"],
	"cat_hotel": ["Отели", "Hotels"],
	"hotels_title": ["Отели", "Hotels"],
	"hotels_locked": ["Отели откроются, когда ваша дорога дойдёт до края земли и соединится с трассой", "Hotels open once your road reaches the edge of the land and joins the highway"],
	"hotels_open": ["Город соединён с трассой — туристы приедут в ваши отели", "The city is joined to the highway: tourists will come to your hotels"],
	"need_landmark": ["Сначала постройте Башню Душанбе", "Build the Dushanbe Tower first"],
	"already_built": ["Такое здание в городе может быть только одно", "A city can have only one of these"],
	"need_highway": ["Сначала проведите дорогу к краю земли, к трассе", "First build a road to the edge of the land, to the highway"],
	"metro_wait": ["Постройте вторую станцию — туда, куда пойдёт метро", "Build a second station where the metro should go"],
	"metro_ready": ["Метро открыто! Поезд ходит под землёй между станциями", "The metro is open! Trains run underground between the stations"],
	"bus_wait": ["Нужна ещё одна остановка у дороги — тогда пойдёт автобус", "One more stop by a road and the bus will start running"],
	"xray_on": ["Высокие здания прозрачные", "Tall buildings are see-through"],
	"xray_off": ["Высокие здания снова видны", "Tall buildings are solid again"],
	"close": ["Закрыть", "Close"],
	"ok": ["ОК", "OK"],
	"cancel": ["Отмена", "Cancel"],
	"yes": ["Да", "Yes"],
	"no": ["Нет", "No"],
	"claim": ["Забрать", "Claim"],
	"locked_lvl": ["Нужен ур. %d", "Needs Lv. %d"],
	"hint_road_start": ["Проведите пальцем или нажмите начало дороги", "Drag a finger or tap where the road starts"],
	"hint_road_end": ["Нажмите, куда тянуть дорогу", "Tap where the road ends"],
	"hint_road_drag": ["Нажмите на перекрёсток, чтобы поставить светофор", "Tap a crossing to add a traffic light"],
	"hint_demolish": ["Выберите, что снести", "Choose what to demolish"],
	"hint_lamp": ["Нажимайте, куда поставить фонари. Фонарь занимает четверть клетки.", "Tap where to put lamps. A lamp takes a quarter of a tile."],
	"hint_no_road": ["Рядом нет дороги: здание не заработает", "No road nearby: the building won't work"],
	"no_money": ["Не хватает монет!", "Not enough coins!"],
	"no_gems": ["Не хватает изумрудов!", "Not enough emeralds!"],
	"bad_place": ["Здесь строить нельзя", "Can't build here"],
	"wrong_zone": ["Не та зона для этого здания", "Wrong zone for this building"],
	"zone_needed": ["Зона: %s", "Zone: %s"],
	"need_animals": ["Для зоопарка нужно поймать %d животных в лесу", "Catch %d forest animals to open a zoo"],
	"lamp_close": ["Слишком близко к другому фонарю", "Too close to another lamp"],
	"lamp_road": ["Фонари ставят на тротуар вашей улицы", "Street lamps go on the sidewalk of your streets"],
	"land_title": ["Земля долины", "Land of the valley"],
	"land_hint": ["Нажмите на участок с табличкой «Продаётся», чтобы купить его", "Tap a plot with a «For sale» sign to buy it"],
	"road_remove": ["Убрать дорогу", "Remove road"],
	"thinking": ["(думает)", "(thinking)"],
	"hint_road_remove": ["Проведите по дороге, которую нужно убрать", "Drag along the road you want to remove"],
	"road_remove_cost": ["Убрать %d клеток: вернём %s монет", "Remove %d tiles: %s coins back"],
	"lamp_classic": ["Классика", "Classic"],
	"lamp_modern": ["Модерн", "Modern"],
	"lamp_lantern": ["С двумя плафонами", "Twin lantern"],
	"r_water_view": ["Вид на воду", "Water view"],
	"r_street_deco": ["Красивая улица", "Pretty street"],
	"tool_road": ["Дороги", "Roads"],
	"tool_water": ["Вода", "Water"],
	"tool_wall": ["Стены", "Walls"],
	"tool_deco": ["Улучшить улицы", "Improve streets"],
	"water_dig": ["Река", "River"],
	"water_fill": ["Засыпать", "Fill in"],
	"wall_remove": ["Убрать стену", "Remove wall"],
	"deco_remove": ["Убрать украшения", "Remove decoration"],
	"hint_water": ["Ведите пальцем — река потечёт за ним. Соедините реки в море, море — в океан. Над дорогой будет мост, вокруг домов — вода", "Drag to dig a river. Join rivers into a sea and a sea into an ocean. Over a road it becomes a bridge, water flows around houses"],
	"hint_wall": ["Проведите линию, где встанет стена", "Drag a line where the wall should stand"],
	"hint_deco": ["Проведите по дороге, чтобы украсить тротуары", "Drag along a road to decorate its sidewalks"],
	"paint_cost": ["%d клеток — %s монет", "%d tiles: %s coins"],
	"lamp_remove_q": ["Убрать фонарь?", "Remove the lamp?"],
	"light_add_q": ["Поставить светофор за %d монет?", "Put up a traffic light for %d coins?"],
	"light_remove_q": ["Убрать светофор с перекрёстка?", "Remove the traffic light?"],
	"light_bad": ["Светофор ставят только на перекрёстке", "Traffic lights go only on crossings"],
	"rule_lights_warn": ["Слишком много светофоров рядом — будут пробки!", "Too many traffic lights close together — traffic jams!"],
	"constructing": ["Строится... %s", "Building... %s"],
	"upgrading": ["Улучшается... %s", "Upgrading... %s"],
	"working": ["Работает... %s", "Working... %s"],
	"ready_collect": ["Готово! Нажмите, чтобы собрать", "Ready! Tap to collect"],
	"st_road": ["Нет дороги!", "No road!"],
	"st_closed": ["Закрыто", "Closed"],
	"st_fire": ["Пожар!", "On fire!"],
	"st_dmg": ["Повреждено — нужен ремонт", "Damaged — needs repair"],
	"st_goods": ["Нет товаров — стройте фермы", "No goods — build farms"],
	"st_staff": ["Мало работников", "Not enough workers"],
	"private_owner": ["Частный бизнес: %s. Платит налог каждый день.", "Private business of %s. Pays tax every day."],
	"private_note": ["Этот бизнес открыли жители. Город его не содержит, а получает налог. Снос испортит репутацию.",
		"Residents opened this business. The city doesn't pay for it and collects tax. Demolishing it hurts reputation."],
	"desc_home": ["Здесь живут жители. Они платят налог и ходят на работу.", "Residents live here, pay taxes and go to work."],
	"desc_shop": ["Продаёт товары жителям и приносит доход.", "Sells goods to residents and earns money."],
	"desc_ind": ["Производит товары для магазинов.", "Produces goods for shops."],
	"desc_service": ["Городская служба: помогает жителям в радиусе действия.", "City service: helps residents within its range."],
	"desc_fun": ["Место отдыха: продаёт билеты и радует жителей.", "Leisure spot: sells tickets and cheers people up."],
	"desc_decor": ["Украшает город: жители рядом счастливее.", "Decorates the city: residents nearby are happier."],
	"upgrade_need": ["Улучшение с ур. %d", "Upgrade at Lv. %d"],
	"speedup": ["Ускорить", "Speed up"],
	"demolish_q": ["Снести «%s»? Вернётся %d монет.", "Demolish \"%s\"? Refund: %d coins."],
	"demolish_road_q": ["Убрать дорогу?", "Remove road?"],
	"close_q": ["Закрыть «%s»? Работа остановится, содержание снизится. Жители дома уедут.",
		"Close \"%s\"? Work stops and upkeep drops. Residents of a home will move out."],
	"evict_q": ["Выселить жильцов? Это решит проблемы с соседями, но жители будут недовольны.",
		"Evict the tenants? It solves neighbour problems, but people will be upset."],
	"unlink_q": ["Разорвать дружбу домов?", "Unlink these houses?"],
	"link_title": ["Соединить дома", "Link houses"],
	"link_hint": ["Выберите соседний дом. Жильцы подружатся: +счастье. Стоит %d монет.", "Pick a nearby house. Neighbours become friends: +happiness. Costs %d coins."],
	"link_bad": ["Эти дома нельзя соединить", "These houses can't be linked"],
	"linked": ["Соседи подружились!", "The neighbours are friends now!"],
	"move_title": ["Переместить: %s", "Move: %s"],
	"move_hint": ["Перетащите здание и нажмите галочку", "Drag the building and tap the tick"],
	"tree_q": ["Убрать дерево за %d монет?", "Clear this tree for %d coins?"],
	"level_up": ["Новый уровень %d!", "Level %d reached!"],
	"level_up_text": ["+1 изумруд. Так держать!", "+1 emerald. Keep it up!"],
	"unlocked": ["Открыто: %s", "Unlocked: %s"],
	"beach_title": ["Пляж", "Beach"],
	"beach_text": ["Купить этот кусок пляжа у моря? Здесь можно строить пляжные зонты, вышки и бары.", "Buy this stretch of beach by the sea? You can build umbrellas, lifeguard towers and bars here."],
	"beach_far": ["Пляж можно купить рядом с вашим участком или с уже купленным пляжем.", "Beach can be bought next to your plot or to beach you already own."],
	"beach_owned": ["Этот пляж ваш. Стройте пляжные здания из меню.", "This beach is yours. Build beach buildings from the menu."],
	"beach_bought": ["Пляж куплен!", "Beach bought!"],
	"zone_beach": ["Пляж", "Beach"],
	"zone_desc_beach": ["пляжные зонты, спасательные вышки и бары", "beach umbrellas, lifeguard towers and bars"],
	"plot_title": ["Новый участок", "New plot"],
	"plot_text": ["Купить этот участок? Зона: %s.", "Buy this plot? Zone: %s."],
	"plot_far": ["Этот участок пока далеко. Сначала купите соседний.", "This plot is too far. Buy a neighbouring plot first."],
	"plot_lvl": ["За монеты — с ур. %d", "For coins — from Lv. %d"],
	"expanded": ["Город стал больше!", "The city has grown!"],
	"mission_done": ["Задание выполнено!", "Mission complete!"],
	"all_missions": ["Все задания выполнены! Вы великий мэр.", "All missions done! You are a great mayor."],
	"missions": ["Задания", "Missions"],
	"settings": ["Настройки", "Settings"],
	"land": ["Земля и зоны", "Land and zones"],
	"land_info": ["Нажмите на свободный участок с табличкой, чтобы купить его. Долина поделена на зоны:",
		"Tap a free plot with a sign to buy it. The valley is split into zones:"],
	"zone": ["Зона", "Zone"],
	"zone_city": ["Город", "City"],
	"zone_farm": ["Фермы", "Farmland"],
	"zone_industry": ["Промзона", "Industrial"],
	"zone_leisure": ["Отдых", "Leisure"],
	"zone_desc_city": ["дома, магазины и городские службы", "homes, shops and city services"],
	"zone_desc_farm": ["фермы, сады, теплицы и ранчо", "farms, orchards, greenhouses and ranches"],
	"zone_desc_industry": ["лесопилки, мастерские и заводы — подальше от домов", "sawmills, workshops and factories — away from homes"],
	"zone_desc_leisure": ["парки, кафе, зоопарк и аттракционы", "parks, cafes, the zoo and the funfair"],
	"highway_yes": ["Город подключён к трассе: приезжают туристы, товары продаются на экспорт.", "The city is connected to the highway: tourists come and surplus goods are exported."],
	"highway_no": ["Проведите дорогу к трассе (въезды в середине каждого края долины) — будут туристы и экспорт.", "Build a road to the highway (gates in the middle of each valley edge) for tourists and exports."],
	"sound": ["Звуки", "Sounds"],
	"music": ["Музыка", "Music"],
	"language": ["Язык: Русский", "Language: English"],
	"on": ["вкл", "on"],
	"off": ["выкл", "off"],
	"privacy": ["Конфиденциальность", "Privacy"],
	"reset": ["Начать заново", "New city"],
	"reset_q": ["Удалить город и начать заново?", "Delete your city and start over?"],
	"whats_new": ["Что нового в версии %s", "What's new in %s"],
	"quit_game": ["Выйти из игры", "Quit the game"],
	"back_again": ["Нажмите «Назад» ещё раз, чтобы выйти", "Press Back again to quit"],
	"quit_q": ["Выйти из игры? Прогресс сохранён.", "Quit the game? Progress is saved."],
	"offline": ["Пока вас не было, город работал.", "Your city kept working while you were away."],
	"road_cost": ["%d клеток: %s монет", "%d tiles: %s coins"],
	"min": ["%dм %02dс", "%dm %02ds"],
	"sec": ["%dс", "%ds"],
	"happy_line": ["Счастье %d%% (стремится к %d%%)", "Happiness %d%% (heading to %d%%)"],
	"workers_line": ["Работают %d из %d мест · мест в домах: %d", "%d of %d jobs filled · housing: %d"],
	"gem_line": ["Изумруды — редкость: за уровни, сюжет и очень редко при сборе", "Emeralds are rare: from levels, story and very rarely when collecting"],
	"rep_line": ["Репутация мэра: %d из 100", "Mayor's reputation: %d of 100"],
	"date_fmt": ["%s, день %d", "%s, day %d"],
	"morning": ["Утро", "Morning"],
	"day": ["День", "Day"],
	"evening": ["Вечер", "Evening"],
	"night": ["Ночь", "Night"],
	"spring": ["Весна", "Spring"],
	"summer": ["Лето", "Summer"],
	"autumn": ["Осень", "Autumn"],
	"winter": ["Зима", "Winter"],
	"weather_clear": ["Ясно", "Clear"],
	"weather_cloudy": ["Облачно", "Cloudy"],
	"weather_rain": ["Дождь", "Rain"],
	"weather_storm": ["Гроза", "Thunderstorm"],
	"weather_snow": ["Снегопад", "Snow"],
	"weather_fog": ["Туман", "Fog"],
	"weather_windy": ["Ветрено", "Windy"],
	"weather_heat": ["Жара", "Heatwave"],
	"beep": ["Би-бип!", "Beep beep!"],
	# finance
	"finance": ["Финансы", "Finance"],
	"fin_today": ["Сегодня (день %d)", "Today (day %d)"],
	"fin_income": ["Доходы", "Income"],
	"fin_expense": ["Расходы", "Expenses"],
	"fin_bills": ["Счета в полночь", "Bills at midnight"],
	"fin_bills_note": ["В полночь город платит за содержание зданий, зарплаты служб, дороги, фонари и кредит.",
		"At midnight the city pays building upkeep, service salaries, roads, lamps and loans."],
	"fin_chart": ["Доходы и расходы по дням", "Income and expenses by day"],
	"fin_yesterday": ["Вчера", "Yesterday"],
	"fin_tax": ["Налог: %d%%", "Tax: %d%%"],
	"fin_tax_note": ["Выше налог — больше денег с домов, но жители недовольны. 10% — норма.", "Higher tax brings more money from homes, but residents get unhappy. 10% is normal."],
	"led_rent": ["Налоги с домов", "Home taxes"],
	"led_shops": ["Магазины и отдых", "Shops and leisure"],
	"led_taxes": ["Налог с частного бизнеса", "Private business tax"],
	"led_tourism": ["Туристы", "Tourism"],
	"led_transit": ["Автобусы и метро", "Buses and metro"],
	"led_export": ["Экспорт товаров", "Goods export"],
	"led_interest": ["Проценты по вкладу", "Deposit interest"],
	"led_missions": ["Задания", "Missions"],
	"led_fines": ["Штрафы и суды", "Fines and lawsuits"],
	"led_deals": ["Сделки", "Deals"],
	"led_loan": ["Кредит", "Loan"],
	"led_upkeep": ["Содержание и зарплаты", "Upkeep and salaries"],
	"led_roads": ["Дороги и светофоры", "Roads and lights"],
	"led_laws": ["Законы", "Laws"],
	"led_build": ["Строительство", "Construction"],
	"led_land": ["Покупка земли", "Land"],
	"led_repairs": ["Ремонт", "Repairs"],
	"led_events": ["Праздники и события", "Festivals and events"],
	"led_zoo": ["Ловля животных", "Animal catching"],
	"bank_none": ["Постройте банк, чтобы брать кредиты и открывать вклады.", "Build a bank to take loans and open deposits."],
	"bank_loan_info": ["Кредит возвращается за 7 дней. Переплата: %d%% (зависит от репутации).", "A loan is repaid over 7 days. Interest: %d%% (depends on reputation)."],
	"bank_loan_q": ["Взять %s монет? Вернуть нужно %s за 7 дней.", "Borrow %s coins? You'll repay %s over 7 days."],
	"bank_debt": ["Долг по кредиту", "Loan debt"],
	"bank_repay": ["Погасить сразу", "Repay now"],
	"bank_deposit": ["Вклад (1.5% в день)", "Deposit (1.5% a day)"],
	"bank_withdraw": ["Снять всё", "Withdraw all"],
	"loan_paid": ["Кредит погашен!", "Loan repaid!"],
	# inbox & events
	"inbox": ["Почта", "Mail"],
	"inbox_empty": ["Писем пока нет.", "No letters yet."],
	"inbox_done": ["Решение принято", "Decision made"],
	"inbox_expired": ["Вы не ответили вовремя", "You didn't answer in time"],
	"ev_fined": ["Штраф получен: +%d", "Fine collected: +%d"],
	"ev_court_won": ["Суд выигран: +%d", "Lawsuit won: +%d"],
	"ev_biz_open": ["Жители открывают новый бизнес!", "Residents are opening a new business!"],
	"ev_biz_nospot": ["Для бизнеса не нашлось места у дороги", "No free spot by a road for the business"],
	"ev_fire_saved": ["Пожарные потушили «%s»", "Firefighters saved \"%s\""],
	"ev_thief_caught": ["Полиция поймала угонщика!", "Police caught the car thief!"],
	# city & rules
	"city": ["Город и правила", "City and rules"],
	"ci_pop": ["Жители / места", "Residents / housing"],
	"ci_jobs": ["Работники / места", "Workers / jobs"],
	"ci_unemp": ["Безработица", "Unemployment"],
	"ci_power": ["Электричество", "Electricity"],
	"ci_water": ["Вода", "Water"],
	"power_low": ["Не хватает электричества: свет тускнеет. Постройте солнечные панели или электростанцию.", "Not enough electricity: the lights are dimming. Build solar panels or a power plant."],
	"water_low": ["Жителям не хватает воды! Постройте водонапорную станцию.", "Residents are short of water! Build a water station."],
	"r_water": ["Нехватка воды", "Water shortage"],
	"ci_election": ["Выборы в день %d — ваш рейтинг", "Election on day %d — your rating"],
	"ci_lose_note": ["Если счастье упадёт до 0, а жителей станет меньше %s, мэра снимут.", "If happiness hits 0 and residents fall below %s, the mayor is removed."],
	"rules": ["Правила города", "City rules"],
	"laws": ["Законы", "Laws"],
	"back": ["Назад", "Back"],
	"laws_note": ["Принято законов: %d из %d. Принять закон — %d монет, отменить — бесплатно.", "Laws passed: %d of %d. Passing a law costs %d coins, repealing is free."],
	"law_on": ["Принять %d", "Pass %d"],
	"law_off": ["Отменить", "Repeal"],
	"lawfx_happy": ["счастье %s", "happiness %s"],
	"lawfx_rep": ["репутация %s/день", "reputation %s/day"],
	"lawfx_daily": ["расход %s/день", "cost %s/day"],
	"lawfx_biz": ["налог с бизнеса %s", "business tax %s"],
	"lawfx_tour": ["туристы %s", "tourism %s"],
	"lawfx_power": ["расход тока %s", "power use %s"],
	"lawfx_water": ["расход воды %s", "water use %s"],
	"lawfx_fire": ["пожары %s", "fires %s"],
	"lawfx_crime": ["преступность %s", "crime %s"],
	"watchtower_title": ["Дозорная башня", "Watchtower"],
	"check_docs": ["Проверить документы", "Check papers"],
	"check_docs_note": ["Штраф с нарушителей: %d–%d монет, +репутация, меньше риска преступлений на время.",
		"Fines from offenders: %d–%d coins, +reputation, less crime risk for a while."],
	"check_docs_go": ["Проверить", "Check"],
	"meeting": ["Собрание", "Meeting"],
	"meeting_note": ["Собрать жителей на площади: %d монет, +%d к настроению на время.",
		"Gather residents on the square: %d coins, +%d mood for a while."],
	"meeting_go": ["Собрать %d", "Hold for %d"],
	"mood_meeting": ["собрание жителей", "a residents' meeting"],
	"rule_lights": ["Не больше 3 светофоров на участке 7×7", "No more than 3 traffic lights in a 7×7 area"],
	"rule_pollution": ["Заводы и лесопилки — не ближе 4 клеток к домам", "Factories and sawmills at least 4 tiles from homes"],
	"rule_roads": ["У каждого дома должна быть дорога", "Every home needs a road"],
	"rule_school": ["Школа, когда жителей больше 150", "A school once there are 150+ residents"],
	"rule_fire": ["Пожарная часть, когда жителей больше 200", "A fire station once there are 200+ residents"],
	"rule_police": ["Полиция, когда жителей больше 300", "A police station once there are 300+ residents"],
	"rule_health": ["Больница, когда жителей больше 500", "A hospital once there are 500+ residents"],
	"rule_decor": ["1 клетка зелени или декора на 30 жителей", "1 tile of greenery or decor per 30 residents"],
	"rule_budget": ["Бюджет без долгов", "No budget debt"],
	"moods": ["Настроение города", "City mood"],
	"mood_debt": ["Долги: не платят зарплаты", "Debts: unpaid salaries"],
	"mood_closed_home": ["Закрыт жилой дом", "A home was closed"],
	"mood_evicted": ["Выселение жильцов", "Tenants evicted"],
	"mood_demolished": ["Снесён жилой дом", "A home was demolished"],
	"mood_ignored": ["Нарушения без наказания", "Violations went unpunished"],
	"mood_noise": ["Шум по ночам", "Night noise"],
	"mood_festival": ["Праздник!", "Festival!"],
	"mood_no_festival": ["Праздник отменён", "Festival cancelled"],
	"mood_viktor_plant": ["Дым от завода Громова", "Smoke from Grom's plant"],
	"mood_crime": ["Ограбления", "Robberies"],
	"mood_illness": ["Эпидемия гриппа", "Flu outbreak"],
	"why_happy": ["Почему жители довольны или нет", "What residents like and dislike"],
	"radius": ["Радиус действия (клеток)", "Range (tiles)"],
	"r_decor": ["Зелень и декор рядом", "Greenery and decor nearby"],
	"r_edu": ["Школа рядом", "School nearby"],
	"r_fire": ["Пожарная часть рядом", "Fire station nearby"],
	"r_police": ["Полиция рядом", "Police nearby"],
	"r_health": ["Больница рядом", "Hospital nearby"],
	"r_bus": ["Автобусная остановка рядом", "Bus stop nearby"],
	"r_metro": ["Метро рядом", "Metro nearby"],
	"r_news": ["Газеты рядом", "Newspapers nearby"],
	"n_garbage": ["Город тонет в мусоре — вывоз не справляется", "The city is drowning in garbage"],
	"garbage_warn": ["Мусор копится! Постройте станцию вывоза", "Garbage is piling up! Build a garbage depot"],
	"rule_garbage": ["Мусор нужно вывозить: не копите больше 60%", "Collect the garbage: keep the pile under 60%"],
	"gb_title": ["Вывоз мусора", "Garbage collection"],
	"gb_pile": ["Мусор в городе", "Garbage in the city"],
	"gb_made": ["Жители производят в час", "Residents make per hour"],
	"gb_cap": ["Вывозят в час", "Collected per hour"],
	"gb_depots": ["Станций работает", "Depots working"],
	"gb_low": ["Чисто: мусор под контролем", "Clean: garbage is under control"],
	"gb_mid": ["Мусор копится — добавьте станцию", "Garbage is piling up: add a depot"],
	"gb_high": ["Свалка! Падает счастье, растёт загрязнение", "A dump! Happiness falls, pollution grows"],
	"gb_none": ["Нет станции: мусоровозки не ездят", "No depot: no trucks on the road"],
	"r_garbage": ["Мусор в городе", "Garbage in the city"],
	"paper_title": ["Городская газета", "City Gazette"],
	"paper_day": ["Выпуск: день %d", "Issue: day %d"],
	"n_fire": ["ПОЖАР! Горят здания, пожарные в пути", "FIRE! Buildings are burning, firefighters on the way"],
	"n_crime": ["Ограбление: жители требуют больше полиции", "Robbery: residents demand more police"],
	"n_power": ["Перебои со светом: городу не хватает энергии", "Power cuts: the city lacks energy"],
	"n_water": ["Воды не хватает — люди стоят в очередях", "Water shortage: people queue for it"],
	"n_storm": ["Штормовое предупреждение: держитесь дома", "Storm warning: stay indoors"],
	"n_heat": ["Жара! Пожарная опасность выросла", "Heatwave! Fire danger is up"],
	"n_jobless": ["Безработица растёт — нужны новые рабочие места", "Unemployment is rising: more jobs are needed"],
	"n_work": ["Работы хватает всем!", "There is work for everyone!"],
	"n_happy": ["Горожане счастливы: лучший город региона", "Citizens are happy: the best town in the region"],
	"n_sad": ["Недовольство в городе: мэру пора что-то менять", "Discontent in town: the mayor must act"],
	"n_rich": ["Казна полна: мэр может позволить себе всё", "The treasury is full: the mayor can afford anything"],
	"n_poor": ["В казне пусто: город считает каждую монету", "The treasury is empty: every coin counts"],
	"n_loan": ["Город живёт в долг: банк ждёт выплат", "The city lives on credit: the bank awaits payments"],
	"n_pop1": ["Город растёт: в нём уже больше полусотни жителей", "The town grows: over fifty residents now"],
	"n_pop2": ["Больше 300 жителей — Пиксельбург становится известным", "Over 300 residents: Pixelburg is getting famous"],
	"n_pop3": ["Тысяча жителей! Настоящий мегаполис", "A thousand residents! A true metropolis"],
	"n_rules": ["Инспекция: в городе нарушены нормы", "Inspection: city rules are broken"],
	"n_tv": ["Телевидение: в эфире программа о нашем городе", "TV: a show about our city is on air"],
	"n_calm": ["В городе тихо и спокойно", "All is quiet in the city"],
	"r_tv": ["Телевидение рядом", "TV coverage"],
	"r_sport": ["Спорт рядом", "Sports nearby"],
	"r_landmark": ["Рядом Башня Душанбе", "Dushanbe Tower nearby"],
	"r_fun": ["Места отдыха", "Leisure spots"],
	"r_shop": ["Магазин рядом", "Shop nearby"],
	"r_noshop": ["Нет магазина рядом", "No shop nearby"],
	"r_poll": ["Дым от производства", "Industrial smoke"],
	"r_dirt": ["Пыльная грунтовка", "Dusty dirt road"],
	"r_link": ["Дружба с соседями", "Friendly neighbours"],
	"r_jam": ["Пробки у светофоров", "Traffic jams"],
	"r_tax": ["Высокие налоги", "High taxes"],
	"r_jobs": ["Безработица", "Unemployment"],
	# animals & zoo
	"zoo": ["Животные и зоопарк", "Animals and the zoo"],
	"zoo_info": ["В лесу живут звери. Нажмите на зверя, чтобы поймать его (нужно %d для зоопарка, каждая попытка %d монет). Зоопарк строят в зоне отдыха.",
		"Animals live in the forest. Tap one to catch it (%d needed for a zoo, %d coins per try). Zoos go in the leisure zone."],
	"zoo_caught": ["Поймано", "Caught"],
	"zoo_animal": ["%s живёт в нашем зоопарке", "This %s lives in our zoo"],
	"catch": ["Поймать", "Catch"],
	"catch_q": ["Отправить егерей поймать: %s? Стоимость %d монет, шанс %d%%.", "Send rangers to catch the %s? Cost %d coins, chance %d%%."],
	"caught": ["Пойман: %s!", "Caught: %s!"],
	"escaped": ["Зверь убежал...", "The animal got away..."],
	"animal_deer": ["Олень", "deer"],
	"animal_rabbit": ["Заяц", "hare"],
	"animal_fox": ["Лиса", "fox"],
	"animal_boar": ["Кабан", "boar"],
	"animal_wolf": ["Волк", "wolf"],
	"animal_bear": ["Медведь", "bear"],
	# profile & privacy
	"profile": ["Профиль", "Profile"],
	"pf_title": ["Знакомство", "About you"],
	"pf_intro": ["Как к вам обращаться? Эти данные остаются только на вашем устройстве.", "How should we address you? This stays only on your device."],
	"pf_name": ["Имя", "Name"],
	"pf_name_ph": ["Ваше имя", "Your name"],
	"pf_age": ["Возраст", "Age"],
	"pf_gender": ["Пол (для обращения в диалогах)", "Gender (for how characters address you)"],
	"pf_m": ["Мужской", "Male"],
	"pf_f": ["Женский", "Female"],
	"pf_next": ["Дальше", "Next"],
	"pf_kid": ["Вам меньше 13 лет: прочитайте политику конфиденциальности вместе с родителями.", "You are under 13: please read the privacy policy together with a parent."],
	"pf_local": ["Имя, возраст и пол хранятся только на этом устройстве и никуда не отправляются.", "Name, age and gender are stored only on this device and are never sent anywhere."],
	"pf_delete": ["Удалить мои данные", "Delete my data"],
	"pf_delete_q": ["Удалить имя, возраст и пол? Город останется.", "Delete name, age and gender? Your city stays."],
	"pp_accept": ["Я прочитал(а) и принимаю", "I have read and accept"],
	"pp_continue": ["Продолжить", "Continue"],
	"backup": ["Резервная копия", "Backup"],
	"backup_text": ["Прогресс хранится на устройстве. Если на телефоне включено резервное копирование Android, Google сам сохранит игру. Ещё можно скопировать код города и сохранить его в заметках или отправить себе: по коду город восстановится на любом устройстве.",
		"Progress is stored on the device. If Android backup is on, Google saves the game for you. You can also copy your city code and keep it in notes or send it to yourself: the code restores your city on any device."],
	"backup_copy": ["Скопировать код города", "Copy city code"],
	"backup_copied": ["Код скопирован", "Code copied"],
	"backup_paste": ["Вставьте сюда код города", "Paste a city code here"],
	"backup_restore": ["Восстановить из кода", "Restore from code"],
	"backup_bad": ["Код не подошёл", "That code doesn't work"],
	"credits": ["Авторы", "Credits"],
	"credits_text": ["Игра, графика и музыка созданы для «Пиксельбурга».\nШрифт: Inter (The Inter Project Authors) — лицензия SIL Open Font License 1.1.\nВсе звуки и музыка синтезированы специально для игры.",
		"Game, art and music made for Pixelburg.\nFont: Inter (The Inter Project Authors) — SIL Open Font License 1.1.\nAll sounds and music were synthesised for this game."],
	# game over
	"lose_title": ["Мэра сняли с должности", "The mayor was removed"],
	"lose_text": ["Жители потеряли терпение: счастье упало до нуля, и больше половины горожан уехали из долины.",
		"Residents lost patience: happiness fell to zero and most of the townsfolk left the valley."],
	"lose_election": ["Вы проиграли выборы, и Виктор Громов занял ваш кабинет.", "You lost the election and Viktor Grom took over your office."],
	"lose_stats": ["Вы правили %d дней, максимум жителей: %s, уровень %d.", "You governed for %d days, peak population %s, level %d."],
	"lose_restart": ["Начать заново", "Start again"],
	"privacy_full": ["""ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ ИГРЫ «ПИКСЕЛЬБУРГ»

1. Общие положения
Эта политика объясняет, какие данные использует игра «Пиксельбург» (далее — «игра»), зачем и где они хранятся. Игра создана независимым разработчиком. Мы уважаем вашу приватность и устроили игру так, чтобы ваши данные не покидали устройство.

2. Данные, которые вы вводите сами
При первом запуске игра просит указать имя, возраст и пол.
• Имя нужно, чтобы персонажи обращались к вам по имени.
• Пол нужен только для правильного обращения в диалогах («господин мэр» или «госпожа мэр»).
• Возраст нужен, чтобы подсказать младшим игрокам прочитать эту политику вместе с родителями.
Вы можете указать любое имя или псевдоним. Эти данные хранятся только в файле сохранения на вашем устройстве. Мы их не получаем, не передаём третьим лицам и не используем для рекламы или аналитики.

3. Игровой прогресс
Город, деньги, настройки и прогресс сохраняются в памяти приложения на вашем устройстве.
• Резервное копирование Android. Если на вашем телефоне включено резервное копирование, система Android может сохранить файлы игры в вашем аккаунте Google. Этим управляет Google по вашим настройкам; у разработчика нет доступа к этим копиям. Отключить копирование можно в настройках телефона.
• Код города. В настройках можно по вашему желанию скопировать текстовый код с сохранением. Вы сами решаете, где его хранить. Игра никуда его не отправляет.

4. Что игра НЕ делает
• Не подключается к интернету и не требует разрешения на доступ к сети.
• Не показывает рекламу и не содержит покупок.
• Не использует аналитику, трекеры, рекламные идентификаторы и сторонние SDK.
• Не запрашивает доступ к геолокации, контактам, камере, микрофону, файлам и другим разрешениям.
• Не собирает и не продаёт никакие данные.

5. Дети
Игра подходит для игроков любого возраста. Мы не собираем персональные данные детей: всё, что вводится в игре, остаётся на устройстве. Если вам меньше 13 лет, прочитайте эту политику вместе с родителями или опекунами.

6. Удаление данных
• Имя, возраст и пол: Настройки → Профиль → «Удалить мои данные».
• Весь прогресс: Настройки → «Начать заново», очистка данных приложения в настройках Android или удаление игры.
Так как данные хранятся только у вас, после удаления восстановить их можно только из вашей резервной копии или кода города.

7. Безопасность
Данные хранятся в закрытой папке приложения, недоступной другим приложениям. Ничего не передаётся по сети, поэтому данные нельзя перехватить при передаче.

8. Сторонние материалы
В игре используются шрифты под свободной лицензией SIL Open Font License и звуки, созданные для игры. Они не собирают никаких данных.

9. Изменения политики
Если политика изменится (например, появится новая функция), мы обновим этот текст в игре и на странице игры в Google Play до того, как изменения вступят в силу.

10. Контакты
Вопросы о конфиденциальности можно задать разработчику по адресу электронной почты, указанному на странице игры в Google Play.

Дата вступления в силу: 2026 год.""",
	"""PIXELBURG PRIVACY POLICY

1. Overview
This policy explains what data the game Pixelburg (the "game") uses, why, and where it is stored. The game is made by an independent developer. We respect your privacy and built the game so that your data never leaves your device.

2. Data you enter yourself
On first launch the game asks for a name, age and gender.
• The name lets characters address you personally.
• Gender is only used for the right form of address in dialogues.
• Age is used to suggest that younger players read this policy with a parent.
You may use any name or nickname. This data is stored only in the save file on your device. We never receive it, never share it with third parties and never use it for advertising or analytics.

3. Game progress
Your city, money, settings and progress are saved in the app's private storage on your device.
• Android backup. If backup is turned on for your phone, Android may store the game's files in your Google account. Google manages this according to your settings; the developer has no access to these copies. You can turn backup off in your phone settings.
• City code. In the settings you may copy a text code containing your save. You decide where to keep it. The game never sends it anywhere.

4. What the game does NOT do
• It does not connect to the internet and does not request network access.
• It shows no ads and has no purchases.
• It uses no analytics, trackers, advertising IDs or third-party SDKs.
• It does not request location, contacts, camera, microphone, files or any other permissions.
• It does not collect or sell any data.

5. Children
The game is suitable for players of all ages. We do not collect children's personal data: everything entered in the game stays on the device. If you are under 13, please read this policy together with a parent or guardian.

6. Deleting your data
• Name, age and gender: Settings → Profile → "Delete my data".
• All progress: Settings → "New city", clearing the app's data in Android settings, or uninstalling the game.
Because the data is stored only on your side, it can only be restored from your own backup or city code.

7. Security
Data is kept in the app's private folder, which other apps cannot access. Nothing is sent over the network, so nothing can be intercepted in transit.

8. Third-party materials
The game uses fonts under the SIL Open Font License and sounds created for the game. They do not collect any data.

9. Changes
If this policy changes (for example, when a new feature appears), we will update this text in the game and on the game's Google Play page before the changes take effect.

10. Contact
Privacy questions can be sent to the developer at the e-mail address shown on the game's Google Play page.

Effective: 2026."""],
}

## What residents say when tapped. Keys are chosen from their mood, job, weather and time.
const PHRASES := {
	"p_hello": [["Здравствуйте, {title}!", "Привет, {name}!", "Хороший у нас город!", "О, сам мэр! Можно селфи?"],
		["Hello, Mayor!", "Hi, {name}!", "We have a nice town!", "Oh, the mayor! Selfie?"]],
	"p_happy": [["Люблю наш город!", "Спасибо, {title}!", "Жить здесь — одно удовольствие.", "Лучший мэр долины!"],
		["I love our town!", "Thank you, Mayor!", "Living here is a joy.", "Best mayor in the valley!"]],
	"p_sad": [["Что-то мне здесь не нравится...", "Может, переехать?", "Мэр, сделайте что-нибудь!"],
		["I don't like it here...", "Maybe I should move away?", "Mayor, do something!"]],
	"p_r_noshop": [["Хоть бы магазин поближе...", "За хлебом ходить далеко!"], ["I wish there was a shop nearby...", "The bakery is so far away!"]],
	"p_r_poll": [["Дышать нечем от завода!", "Опять дым в окна..."], ["The factory smoke is choking us!", "Smoke in our windows again..."]],
	"p_r_dirt": [["Пыльно на этой дороге.", "Асфальт бы положить..."], ["This road is so dusty.", "Could we get asphalt here?"]],
	"p_r_jam": [["Опять пробки!", "Светофоры на каждом шагу!"], ["Traffic jams again!", "Traffic lights everywhere!"]],
	"p_r_tax": [["Налоги кусаются...", "Снизьте налоги, пожалуйста!"], ["Taxes bite...", "Please lower the taxes!"]],
	"p_r_jobs": [["Никак не найду работу.", "Нужно больше рабочих мест!"], ["I can't find a job.", "We need more jobs!"]],
	"p_kind_police": [["Всё под контролем.", "Нарушителей не видели?"], ["Everything's under control.", "Seen any troublemakers?"]],
	"p_kind_doctor": [["Не болейте!", "Мойте руки!"], ["Stay healthy!", "Wash your hands!"]],
	"p_kind_firefighter": [["Мы на страже!", "Огнетушитель дома есть?"], ["We're on guard!", "Got an extinguisher at home?"]],
	"p_kind_builder": [["Работы много!", "Смена была тяжёлой."], ["Lots of work!", "Tough shift today."]],
	"p_kind_chef": [["Сегодня пицца удалась!", "Заходите на обед!"], ["The pizza turned out great today!", "Come by for lunch!"]],
	"p_kind_farmer": [["Урожай что надо!", "Коровы передают привет."], ["Great harvest!", "The cows say hi."]],
	"p_kind_boy": [["Ура, после школы — гулять!", "А зоопарк будет?"], ["Yay, playtime after school!", "Will there be a zoo?"]],
	"p_kind_girl": [["Хочу на карусель!", "Я нарисовала наш город!"], ["I want to ride the carousel!", "I drew our town!"]],
	"p_kind_grandpa": [["Вот в наше время...", "Хорошо гулять в парке."], ["Back in my day...", "A walk in the park is lovely."]],
	"p_kind_grandma": [["Внучку бы в хорошую школу...", "Скамеек бы побольше!"], ["My grandkid needs a good school...", "We need more benches!"]],
	"p_kind_jogger": [["Пять километров!", "Не отвлекайте, бегу!"], ["Five kilometres!", "Can't stop, running!"]],
	"p_kind_postman": [["Вам письмо!", "Почту принёс!"], ["You've got mail!", "Mail delivery!"]],
	"p_kind_business": [["Время — деньги.", "Опаздываю на встречу!"], ["Time is money.", "Late for a meeting!"]],
	"p_kind_businesswoman": [["У меня совещание.", "Отличный квартал для офиса."], ["I have a meeting.", "Great block for an office."]],
	"p_kind_student": [["Сессия скоро...", "Есть тут библиотека?"], ["Exams soon...", "Is there a library here?"]],
	"p_kind_teen": [["Скучно... Нужен кинотеатр!", "Классный город!"], ["Bored... We need a cinema!", "Cool town!"]],
	"p_w_clear": [["Какое солнце!", "Отличная погода!"], ["What sunshine!", "Lovely weather!"]],
	"p_w_cloudy": [["Пасмурно сегодня.", "Хоть бы не дождь."], ["Cloudy today.", "Hope it won't rain."]],
	"p_w_rain": [["Где мой зонтик?", "Промок до нитки!"], ["Where's my umbrella?", "I'm soaked!"]],
	"p_w_storm": [["Ой, гроза!", "Скорее домой!"], ["Oh, a thunderstorm!", "Let's get home quick!"]],
	"p_w_snow": [["Снег! Красота!", "Слепим снеговика?"], ["Snow! Beautiful!", "Shall we build a snowman?"]],
	"p_w_fog": [["Ничего не видно...", "Туман как молоко."], ["Can't see a thing...", "Fog as thick as milk."]],
	"p_w_windy": [["Держите шляпу!", "Ух, как дует!"], ["Hold your hat!", "Wow, it's gusty!"]],
	"p_w_heat": [["Ну и жара сегодня...", "Пойду куплю мороженое."], ["It's so hot today...", "I'm getting ice cream."]],
	"p_morning": [["Доброе утро!", "Кофе бы..."], ["Good morning!", "I need coffee..."]],
	"p_day": [["Хорошего дня!", "Обеденный перерыв!"], ["Have a nice day!", "Lunch break!"]],
	"p_evening": [["Наконец-то вечер.", "Пойду в кафе."], ["Finally evening.", "Off to a cafe."]],
	"p_night": [["Пора спать...", "Тише, все спят."], ["Time for bed...", "Shh, everyone's asleep."]],
	"p_to_work": [["Спешу на работу!", "Не опоздать бы!"], ["Hurrying to work!", "Mustn't be late!"]],
	"p_to_fun": [["Иду отдыхать!", "Встречаюсь с друзьями."], ["Off to relax!", "Meeting friends."]],
}

var lang := "ru"


func _ready() -> void:
	var sys := OS.get_locale_language()
	lang = "ru" if sys in ["ru", "uk", "be", "kk", "uz", "ky", "tg"] else "en"


func set_lang(l: String) -> void:
	lang = l
	changed.emit()


func t(key: String) -> String:
	if not S.has(key):
		return key
	return S[key][0 if lang == "ru" else 1]


func pick(pair: Array) -> String:
	return pair[0 if lang == "ru" else 1]


func duration(seconds: float) -> String:
	var s := int(ceil(seconds))
	if s >= 60:
		return t("min") % [s / 60, s % 60]
	return t("sec") % s


func num(n: int) -> String:
	var s := str(absi(n))
	var out := ""
	while s.length() > 3:
		out = " " + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return ("-" if n < 0 else "") + s + out
