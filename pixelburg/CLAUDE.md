# Пиксельбург — памятка для Claude

Изометрический градострой для Android. Godot 4.7.2, рендер GL Compatibility. Пакет `com.pixelburg.citybuilder`.
Текущая версия 1.3.1 (code 5), опубликована в Google Play. Языки игры: русский, английский. Отвечай пользователю по-русски, коротко.

## Где что
- `scripts/` — код: `game.gd` (экономика, сохранения), `city.gd` (камера, ввод, режимы), `life.gd` (жители, машины),
  `ground.gd` + `shaders/ground.gdshader` (земля и дороги), `hud.gd`/`panels.gd`/`dialog_box.gd`/`tutorial.gd` (интерфейс),
  `data.gd` (здания, баланс), `loc.gd` (тексты ru/en).
- `tools/gen_assets.py` + `tools/art/` — генерация графики (Python). Иконки: `assets/ui/icons/*.png`.
- `tools/dev/` — тесты: `logic_test.tscn` (должно быть "DONE: 0 failed"), `ui_test`, `view_test`, `showcase` (скриншоты).

## Сборка и тесты (из папки pixelburg/)
- Нужны Godot 4.7.2 + export templates (github.com/godotengine/godot-builds, 4.7.2-stable); для графики — python3, numpy, scipy, pycairo, pillow.
- Проверка: `godot --headless --import` → `python3 tools/fix_imports.py` → `godot --headless --import` →
  `godot --headless res://tools/dev/logic_test.tscn` (ждать «DONE: 0 failed»). Для нового — добавлять проверку в logic_test.
- Графика только для нового: `python3 tools/gen_assets.py buildings only=id1,id2` (модули: tools/art/b_*.py, список MODULES в gen_assets.py).
- Скриншоты: `xvfb-run -a godot --rendering-driver opengl3` БЕЗ `--headless` (вместе рендер зависает).
- Android: JDK 17, Android SDK (platform 36, build-tools 36.0.0), `--install-android-build-template`; подпись через
  GODOT_ANDROID_KEYSTORE_RELEASE_PATH/USER/PASSWORD. Если Maven Central отдаёт 429 — Gradle на зеркало
  maven-central.storage-download.googleapis.com (init-скрипт в ~/.gradle/init.d). APK из AAB: `bundletool build-apks --mode=universal`.
- Windows: пресет «Windows Desktop», `godot --headless --export-release "Windows Desktop" build/pixelburg.exe` (build/ в .gitignore).

## Правила
- Шейдеры: на телефонах мало текстурных юнитов — не больше 5–6 sampler в одном шейдере (земля использует Texture2DArray).
- Ключ подписи и пароль НИКОГДА не коммитить и не показывать.
- Перед сборкой: прогнать `logic_test`. APK/AAB собирать один раз в конце задачи.
- Сохранения: SAVE_VERSION в game.gd; при смене формата старые сохранения сбрасываются.

## Экономия лимитов
- Одна задача — одна сессия. В конце сессии обновить `NEXT.md`, сделать commit + push.
- Не показывать код в чате, сразу менять файлы. Не перерисовывать всю графику без просьбы.

## Шаблон первого сообщения новой сессии
Проект: моя игра Пиксельбург. Прочитай CLAUDE.md и NEXT.md.
Задача: [одна конкретная задача]. Отвечай коротко, код в чат не выводи.
В конце обнови NEXT.md и сделай commit + push.
