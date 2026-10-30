# Что дальше

## Сейчас
- В Google Play 1.3.1 (code 5). В main готова следующая версия (1.4.0, не собрана): всё ниже + см. Data.NEWS.
- План обновлений по пунктам — ROADMAP.md (один пункт на чат). Сделаны пункты 1–10.

## Что есть в игре (кратко, где искать)
- Здания: scripts/data.gd (B, ORDER, TABS); графика: tools/art/b_*.py (b_towers — башни, отели, транспорт, Душанбе; b_houses2 — дома мира, дачи, башня-виллы).
- Отели (вкладка «Отели», нужна дорога к трассе), Башня Душанбе (4x4, одна) + дома квартала, автобусы/остановки, метро (metro_view.gd).
- Дороги 8 видов (шейдер ground.gdshader, типы 1–11), велосипедисты (cyclist.gd), прозрачные высокие здания (кнопка-глаз).
- Вода: река → море (30) → океан (120), мосты, острова, жизнь на воде (water_life.gd). Стены и украшения улиц (street_props.gd).
- Аэропорт (4x4, один, нужна дорога к трассе), рейсы в 16 стран, аналитика прилётов (panels.airport).
- Фонари: classic, modern, lantern. «Что нового» показывается раз после обновления (Data.NEWS_VERSION).

## Сделано в последней сессии (пункт 10)
- Двери: scripts/door_view.gd (DoorView, вместо чёрного Polygon2D в building_view.door). Створка на дальнем косяке поворачивается внутрь (до ~100°, ложится к скрытой стене),
  широкие проёмы (≥40 px) — две створки, ≥30 px — стеклянные. За створкой комната: задняя стена, пол, боковая стена, коврик, лампа;
  всё обрезано по проёму (Geometry2D.intersect_polygons). Ночью комната ярче, свет на тротуар (glow_mat). Новая графика не нужна —
  берёт метки door_a/door_b/door_t из meta.json. Узел обрабатывается только пока дверь открыта. Проверки в logic_test, Data.NEWS дополнен.
- Проверено скриншотами (xvfb, день/ночь, середина поворота). На телефоне глазами не смотрели.

## Пункт 9 (ранее)
- Аэропорт: Data.B "airport" (service, svc "airport", unique, highway, 4x4, зоны industry/leisure/city, ур. 16). Графика tools/art/b_airport.py (модуль в MODULES): терминал, вышка, полоса, самолёты.
- Рейсы: Data.COUNTRIES/COUNTRY_ORDER (16 стран: цена, уровень, флаг из 3 полос, pax, spend), FLIGHT_CHANCE. Game.flights (купленные), Game.arrivals (всего), Game.arrivals_day (за день, сброс в _end_of_day) — в сохранении (ключи flights/arrivals/arrivals_day, SAVE_VERSION не менялся).
- Game.buy_flight(id), land_flight(id) (пассажиры → доход "flights", больше с отелями, закон tour), _update_airport() в _on_hour (с 6:00, шанс на рейс), arrival_stats(), arrivals_total(today), сигнал plane_landed.
- Окно panels.airport() (кнопка-самолёт в карточке аэропорта): статистика, полосы по странам с %, покупка рейсов. Газета: заголовок n_flights.
- Самолёт садится на аэропорт: scripts/plane_view.gd (рисуется полигонами), life._on_plane_landed (не больше 3 сразу). Проверки в logic_test, Data.NEWS дополнен.
- Не проверено глазами в игре: посадка самолёта (направление по оси x сетки, не по повороту здания) и вид окна на телефоне.

## Пункт 8 (ранее)
- Пляж за западной границей земли: тайлы x 70..79, y 80..159 (Data.BEACH_X0/BEACH_W, beach_seg(c) → сегмент 0..7 по рядам участков), зона "beach", region "beach".
  Покупка по сегментам: Game.beach (в сохранении, ключ "beach", SAVE_VERSION не менялся), beach_buyable/buy_beach, Data.beach_price, panels.beach_plot,
  таблички продажи в city._rebuild_signs, подсветка в ground.update_info. Песок и море рисует ground.gdshader (по константам land0), деревья не растут (Data.beach_area).
- Здания только на пляже (zones ["beach"]): beach_umbrella, lifeguard_tower (decor), beach_bar (shop, доход). Графика tools/art/b_beach.py (модуль в MODULES). Проверки в logic_test, Data.NEWS дополнен.
- Не проверено глазами в игре (скриншоты showcase не снимались): стоит глянуть вид песка/моря на телефоне.

## Пункт 7 (ранее)
- Рынок (cat shop, приносит доход): market_stall (1x1), market (2x2, открытый рынок), bazaar (3x3, крытый базар, 4 гема). data.gd (B, ORDER), в life.gd SHOPS (жители ходят на рынок).
  Графика tools/art/b_market.py (новый модуль в MODULES gen_assets.py). В logic_test добавлены проверки, «DONE: 0 failed». Data.NEWS дополнен.

## Пункт 6 (ранее)
- Недостроенные дома — чисто для красоты (decor, happy +1): site_small (1x1, кладка стены), site_house (2x2, 3 стадии: фундамент → этаж с лесами → крыша-каркас),
  site_crane (2x2, башенный кран, котлован, бытовка). data.gd (B, ORDER), графика b_towers.py, проверка в logic_test.

## Пункт 5 (ранее)
- Мусор: Game.garbage (0..100, в сохранении), +pop*0.04/час (garbage_rate), вывоз garbage_capacity() = сумма «garb»×lvl работающих зданий svc "garbage"
  (garbage_depot 2x2 — 12/ч, recycling_plant 3x3 индустрия — 40/ч). _update_garbage() в _on_hour. Мусор ≥40 добавляет загрязнение домам,
  ≥40 снижает счастье (garbage_mood до −10), ≥60 при pop>100 — нарушено правило "garbage" (RULES), заголовок n_garbage, тост.
- life.gd: _update_garbage_trucks() — каждый час каждая станция шлёт мусоровозку по дорогам и обратно (старый случайный утренний рейс убран).
- Окно panels.garbage() — кнопка в карточке станции (иконка пока demolish). Графика b_towers.py (garbage_depot, recycling_plant). В logic_test добавлены проверки.

## Пункт 4 (ранее)
- Газеты: newsstand (киоск 1x1, r6) и newspaper (редакция 2x2, r14), svc "news", +2 счастья в радиусе (r_news). Графика b_towers.py.
- Кнопка-газета в карточке здания открывает panels.newspaper(): заголовки по состоянию города — Game.paper_headlines() (пожар, ограбление,
  энергия, вода, погода, работа, счастье, казна, кредит, население, нормы, ТВ); тексты n_* в loc.gd. В logic_test добавлены проверки.
- Иконка "newspaper" уже есть (assets/ui/icons).

## Пункт 3 (ранее)
- Телевидение: tv_studio (2x2, r12), tv_center (3x3, r20), tv_tower (2x2, r32) — svc "tv", +4 счастья в радиусе (game.gd список svc, loc r_tv).
  Графика b_towers.py (tv_*), в logic_test добавлена проверка. Иконка "tv" пока alias на info (ждёт иконки Gemini).

## Пункт 2 (ранее)
- Остановки 4 новых вида (data.gd, b_towers.py): bus_stop_simple (навес), bus_stop_modern (стекло), bus_stop_ad (реклама + экран),
  bus_stop_village (деревянная). Все svc "bus": Game.bus_stops() теперь берёт любые здания с svc "bus", автобус ходит между любыми.
- Пункт 1 (ранее): выход из игры, дома американский/таджикский/азиатский, дачи, башня-виллы, окно «Что нового».
- Проверено: logic_test «DONE: 0 failed».

## Перед выпуском 1.4.0
- export_presets.cfg: version/code=6, version/name="1.4.0"; project.godot config/version. Собрать AAB, проверить на телефоне выход.
- Иконки от пользователя (Gemini): лист 4x4 на маджента-фоне → `python3 tools/art/cut_icons.py 5=лист.png` (имена — 5-я строка
  tools/art/icon_sheet_names.json: eye news river wall street exit bus metro hotel bike sport power water tv newspaper plane),
  затем import + fix_imports. Пока файлов нет, assets.gd ui_icon подставляет старые иконки (alias).
