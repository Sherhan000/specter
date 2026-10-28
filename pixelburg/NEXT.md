# Что дальше

## Сделано (1.3.0)
- Реальный масштаб, 55 зданий с поворотом, жители с работой и машинами, светофоры, горизонт с горами.
- Новый интерфейс (Inter, иконки пользователя), обучение с блокировкой кнопок, удаление дорог.
- Исправлено для телефонов: белые дороги, прокрутка магазина/настроек, вылет окна животных.
- AAB отправлен в закрытое тестирование Google Play (нужно 12 тестировщиков на 14 дней).

## Windows .exe
- Пресет «Windows Desktop» в export_presets.cfg (x86_64, embed_pck, `build/pixelburg.exe`). `build/` в .gitignore.
- Нужны Godot 4.7.2 и export templates 4.7.2 (github.com/godotengine/godot-builds, релиз 4.7.2-stable).
- Сборка из корня pixelburg/:
  `godot --headless --import`
  `godot --headless res://tools/dev/logic_test.tscn` (должно быть «DONE: 0 failed»)
  `godot --headless --export-release "Windows Desktop" build/pixelburg.exe`
- На Linux иконка/метаданные в .exe не вшиваются (нет rcedit) — на Windows сборка сама их применит; игре это не мешает.
- logic_test впервые запущен: ошибок GDScript (электричество/вода) нет; исправлен порядок в самом тесте (проверка жителей до блока «losing»).
- .exe не запускался на Windows — проверить вручную.

## Сделано после 1.3.0 (не собрано, не проверено в Godot)
- 4 новых здания (59 всего): Хрущёвка, Общежитие, Панельная многоэтажка (у хрущёвки и панельки магазин на 1-м этаже, пока только визуально), Роддом (служба `health`).
- Спрайты: `tools/art/b_homes.py` (`python3 tools/gen_assets.py buildings only=khrushchevka,panel_block,dorm,maternity`; нужны scipy, pycairo). Данные: `data.gd`.
- Сделать: открыть в Godot (создаст `.import`), запустить `tools/fix_imports.py`, `logic_test` (ждёт «DONE: 0 failed»), посмотреть баланс/цены, при желании дать магазину на 1-м этаже доход.

## Идеи на следующие версии
- Таджикский язык, местные здания (чайхана, базар), горы Памира.
- Реклама за изумруды (AdMob) — потребует обновить политику и «Безопасность данных».
