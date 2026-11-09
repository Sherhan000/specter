# «Call your mother today» — раскадровка и промпты

60 секунд, 9 шотов из ИИ-видео + финальный титр (его собирает скрипт).
Звук уже готов (`audio/master_mix.wav`) и сведён точно под этот тайминг,
поэтому **звук из видеогенератора не нужен**: в промпты добавлено `no music, no speech`.

## Как работать

1. Сначала сгенерируй **2 референса персонажей** (Nano Banana / Midjourney / любая картинка-модель),
   потом каждый шот делай как **image-to-video** с этим референсом — иначе мать будет в каждом кадре другой.
2. Видеомодель: Veo 3.x (Google Flow / Gemini), Kling, Sora или Runway. Формат 16:9, лучше 4K или 1080p.
   Делай по 3–4 дубля на шот и бери лучший.
3. Сохраняй клипы как `clips/S01.mp4` … `clips/S09.mp4`.
4. Запусти `./build_video.sh 4k` — выйдет `final_4k.mp4`: монтаж, грейд, зерно, кашé 2.39:1, вспышки молний, звук, титр.
   Если клип короче шота, скрипт плавно его замедлит; если длиннее — обрежет.

## Референсы персонажей (картинки)

**REF_MOTHER (молодая):**
> Cinematic portrait of a young Muslim mother, late 20s, olive skin, tired kind dark-brown eyes, soft features, a loose cream linen headscarf with a dark braid visible, simple modest home dress, warm tungsten light, 35mm film still, Kodak Vision3 500T, shallow depth of field, hyper-realistic skin texture, film grain

**REF_MOTHER_OLD:** то же лицо, 70+ лет:
> Same woman aged 75, deep wrinkles, white hair braid under the same cream headscarf, trembling thin hands, the same kind dark-brown eyes, warm soft light, 35mm film still, hyper-realistic, film grain

**REF_SON (взрослый):**
> Man in his early 30s, olive skin, short dark beard, the same dark-brown eyes as his mother, simple dark clothes, emotional, 35mm film still, hyper-realistic

## Шоты

Общий хвост для каждого промпта (добавляй в конец):
`hyper-realistic, shot on ARRI Alexa, anamorphic lens, 35mm film grain, shallow depth of field, cinematic color grading, 4K, no text, no music, no speech`

| # | Время | Длит. | Что в кадре | Звук (уже в миксе) |
|---|---|---|---|---|
| S01 | 0:00–0:09 | 9 c | Тьма, глина становится человеком | сердцебиение-гром, глина |
| S02 | 0:09–0:13 | 4 c | Молния, первый крик, дрожат горы | раскат грома, крик новорождённого |
| S03 | 0:13–0:20 | 7 c | 3 часа ночи, зубки, мать не спит | плач, шёпот, часы |
| S04 | 0:20–0:25 | 5 c | Ребёнок падает | падение, плач |
| S05 | 0:25–0:31 | 6 c | Мать стареет за секунды | часы, ветер времени |
| S06 | 0:31–0:36 | 5 c | Сын смотрит на ноги матери, золотой свет | ливень начинается |
| S07 | 0:36–0:43 | 7 c | Небо плачет: дождь по миру, горы, молния | ливень, землетрясение, гром |
| S08 | 0:43–0:44 | 1 c | Тишина | абсолютная тишина |
| S09 | 0:44–0:56 | 12 c | Рассвет, свет на лице, она улыбается | пианино, птицы, **закадровый шёпот** |
| S10 | 0:56–1:00 | 4 c | Чёрный экран, капля, титр | капля (делает скрипт) |

### S01 — Глина (9 c)
> Total darkness. A faint beam of warm light reveals wet red-brown clay slowly shaping itself, as if by an invisible force, into a curled human infant in fetal position. Extreme macro, clay surface cracking and smoothing, dust particles floating in the light beam, a slow pulse of light in rhythm with a heartbeat. Extremely slow push-in. Dark, sacred, awe-inspiring.

⚠️ Рук «творца» в кадре не показываем: глина формируется сама. Это и деликатнее с религиозной точки зрения, и выглядит мощнее.

### S02 — Молния и первый крик (4 c)
> A colossal lightning bolt strikes behind a dark mountain range at night, white flash lighting up the entire sky; cut to the clay-colored newborn's face crying its very first cry, tiny fists clenched; rocks and dust tremble and fall from the mountain slope. Fast, violent, epic scale.

(Если модель не тянет 2 действия в одном клипе, сделай S02a «молния над горами» 2 c и S02b «лицо младенца» 2 c, склей в один `S02.mp4`.)

### S03 — 3 часа ночи (7 c), по референсу REF_MOTHER
> 3 AM, dark small bedroom lit only by a dim bedside lamp, a digital clock showing 3:07. The young mother sits on the edge of the bed holding her crying teething baby tightly to her chest, gently rocking. Her eyes are red and swollen from no sleep, she whispers a prayer with her lips barely moving, tears on her cheek, she kisses the baby's head. Handheld close-up, intimate, soft warm light and deep shadows.

💡 Сура Аш-Шарх: ИИ-голосом Коран генерировать не стал — это некорректно и он почти наверняка исказит произношение. В кадре мать шепчет одними губами. Если хочешь, чтобы сура звучала, подложи под S03 (0:13–0:20) отрывок настоящего чтеца, у которого есть разрешение на использование (например, своя запись), и скажи мне — сведу.

### S04 — Падение (5 c)
> Bright afternoon, a 3-year-old boy runs across a dusty courtyard and falls hard; in slow motion the mother, a few meters away, lunges forward, her face breaking in fear, she drops to her knees and scoops him into her arms. Slow motion 120fps feel, dust in golden sunlight, shallow focus on her face.

### S05 — Старение (6 c), REF_MOTHER → REF_MOTHER_OLD
> Time-lapse transformation: the same mother carrying her growing son on her back along the same road; with each step seasons flash by, her face ages decades in seconds, wrinkles deepen, her braid turns white, her hands begin to shake, yet she keeps carrying him. Seamless continuous morph, single take, melancholic golden-hour light.

💡 Лучше всего работает режим «first frame + last frame» (Veo / Kling): первый кадр — молодая мать с ребёнком, последний — старая, держащая подростка за руку.

### S06 — Под её ногами (5 c), REF_SON + REF_MOTHER_OLD
> The grown son stands before his elderly mother in a simple courtyard; slow tilt down from his tear-filled eyes to her bare, cracked, worn feet on the earth. Under her feet a soft golden light begins to glow, then explodes outward in rays of divine golden light through the dust, illuminating the son's face from below. The first raindrops start to fall. Slow motion, reverent.

### S07 — Небо плачет (7 c)
> Epic aerial montage: torrential rain falling over the whole world, over deserts, cities and green valleys; dark storm clouds; a giant mountain range trembles, rocks crumble; a massive lightning bolt cracks the entire sky in half. Sweeping drone shot, overwhelming scale, IMAX feel.

(Молния в миксе на 0:37.4, это 1.4 c от начала шота. Скрипт ставит туда вспышку сам, но если молния в клипе совпадёт, будет ещё сильнее.)

### S08 — Тишина (1 c)
> Static wide shot of the wet courtyard at dawn, completely still, the rain has stopped, the last drops hang in the air, blue pre-dawn light.

(Или просто последний кадр S07 / первый кадр S09 в стоп-кадре.)

### S09 — Рассвет (12 c), REF_MOTHER_OLD
> Close-up of the elderly mother's face at sunrise after the storm. The first warm golden sunlight slowly crosses her wet wrinkled face, droplets on her skin glow. She slowly opens her eyes, looks up at her son off-camera and smiles softly, peacefully, eyes glistening. Very slow push-in, golden hour, birds in the soft background.

Закадровый шёпот идёт с 0:44.8 до ~0:56:
*"You were created in pain. You were raised in pain. And Paradise was placed under the feet of the one who suffered for you."*

### S10 — Титр (4 c)
Делает `build_video.sh` сам: чёрный экран, капля на 0:56.4, текст «Call your mother today.» проявляется на 0:56.9.

## Голос

Готовы 3 варианта шёпота (ElevenLabs v3):
- `vo_brian` — глубокий мужской (стоит по умолчанию)
- `vo_george` — тёплый мужской рассказчик
- `vo_lily` — женский, бархатный (13 c, чуть длиннее)

Переключить: `./mix_audio.sh lily` → `./build_video.sh 4k`.
