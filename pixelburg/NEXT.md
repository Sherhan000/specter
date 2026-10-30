# Что дальше

## Сейчас
- В Google Play 1.3.1 (code 5). В main готова следующая версия (1.4.0, не собрана): всё ниже + см. Data.NEWS.
- План обновлений по пунктам — ROADMAP.md (один пункт на чат). Сделаны пункты 1–3.

## Что есть в игре (кратко, где искать)
- Здания: scripts/data.gd (B, ORDER, TABS); графика: tools/art/b_*.py (b_towers — башни, отели, транспорт, Душанбе; b_houses2 — дома мира, дачи, башня-виллы).
- Отели (вкладка «Отели», нужна дорога к трассе), Башня Душанбе (4x4, одна) + дома квартала, автобусы/остановки, метро (metro_view.gd).
- Дороги 8 видов (шейдер ground.gdshader, типы 1–11), велосипедисты (cyclist.gd), прозрачные высокие здания (кнопка-глаз).
- Вода: река → море (30) → океан (120), мосты, острова, жизнь на воде (water_life.gd). Стены и украшения улиц (street_props.gd).
- Фонари: classic, modern, lantern. «Что нового» показывается раз после обновления (Data.NEWS_VERSION).

## Сделано в последней сессии (пункт 3)
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
