# Ролик «Call your mother today»: состояние и план для новой сессии

## Готово
- `audio/master_mix.m4a`: финальный звук на 60 с. Исходники в `audio/raw/`: 3 варианта шёпота (ElevenLabs v3), 11 SFX, 2 музыкальных трека. Пересобрать: `./mix_audio.sh [brian|george|lily]`.
- `SHOTS.md`: раскадровка на 9 шотов с таймингом и промптами.
- `build_video.sh`: монтаж клипов из `clips/S01..S09.mp4`, грейд, зерно, кашé 2.39:1, вспышки молний, титр.

## Следующий этап: 3D в Blender (бесплатно, CPU)
Пользователь выбрал 3D, качество важнее времени (готов ждать 10+ часов), рендер должен идти без его участия.
- Blender ставится через `pip install bpy` (5.2.3 LTS, Python 3.13). GPU нет: 4 ядра CPU, 15 ГБ RAM, значит Cycles на CPU с денойзом.
- Доступные бесплатные ресурсы:
  - Poly Haven: `api.polyhaven.com` и `dl.polyhaven.org/file/...` (HDRI, текстуры, модели, CC0).
  - MakeHuman с raw.githubusercontent.com (`makehumancommunity/makehuman/master/makehuman/data/`): `3dobjs/base.obj`, `rigs/default.mhskel` + `default_weights.mhw`, `eyes/high-poly`, targets (height, expression). Файлы macrodetails весят по 604 байта, скорее всего это заглушки, надо проверить.
  - Недоступны: Sketchfab, Fab, Hugging Face, extensions.blender.org, download.blender.org, ambientcg.
- Предложенный стиль: «ожившая глина / скульптура». Фигуры из глины с SSS, объёмный свет, дождь частицами, горы из displacement и Poly Haven, без детальных лиц. Стиль совпадает с темой «создан из глины» и надёжно получается кодом.
- Рендер вести посегментно, кадры сохранять на диск (резюмируемо). Готовые шоты в mp4 периодически пушить в эту ветку, сессию держать живой проверками по расписанию.
