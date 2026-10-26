# Портреты персонажей «Пиксельбурга»: промпты для ИИ

В игре 6 персонажей, у каждого 7 эмоций. Сейчас в игре стоят нарисованные генератором портреты.
Вы можете заменить их своими картинками из любой нейросети: игра подхватит их без изменения кода.

## Как заменить портрет

1. Сгенерируйте картинку по промпту ниже.
2. Сохраните её как **PNG, 512 × 512**, квадрат, персонаж по грудь, лицо в центре и чуть выше середины.
3. Назовите файл строго так: `имя_эмоция.png`, например `alina_happy.png`.
4. Положите в папку `assets/portraits/` вместо старого файла.
5. Откройте проект в Godot (он сам импортирует картинку) и соберите AAB заново.

Если какой-то эмоции нет, игра покажет `имя_smile.png`. Поэтому начните с файлов `*_smile.png`.

| Персонаж | Файлы | Роль |
|---|---|---|
| Алина | `alina_*.png` | заместитель мэра, ведёт обучение |
| Борис Петрович | `boris_*.png` | старый архитектор, друг мэра |
| Виктор Громов | `viktor_*.png` | бизнесмен-соперник, хочет стать мэром |
| Марина Светлова | `marina_*.png` | журналистка «Вестника долины» |
| Олег Смирнов | `oleg_*.png` | начальник полиции, друг |
| Баба Зина | `zina_*.png` | пожилая активистка с внуком |

Эмоции (часть имени файла): `smile`, `talk`, `happy`, `surprised`, `worried`, `angry`, `smug`.

## Как получить одинаковый стиль

- Сначала сделайте один удачный портрет `smile`. Остальные эмоции этого персонажа делайте из него
  (режим «изображение → изображение», «вариации» или «reference image» / «character reference»),
  меняя только описание эмоции.
- Держите один и тот же «общий стиль» (ниже) во всех промптах.
- Фон простой и светлый, без текста, без логотипов, без водяных знаков.

## Общий стиль (вставляйте в начало каждого промпта)

```
Cozy cartoon visual-novel character portrait, bust shot, front-facing, soft cel shading, clean dark outlines,
warm friendly colors, big expressive eyes, simple soft pastel background with a blurred little town,
square 1:1, centered, high detail face, no text, no watermark, no logo
```

## Персонажи

### Алина (alina)
```
young woman about 25, long straight chestnut-brown hair with soft bangs, green eyes, light skin with a gentle blush,
light-blue blazer over a white shirt, small turquoise pendant necklace, kind and smart look, city deputy mayor
```

### Борис Петрович (boris)
```
kind elderly man about 68, neat grey hair, short grey beard, round glasses, brown tweed suit with a green tie,
holds a rolled blueprint, wise grandfatherly architect
```

### Виктор Громов (viktor)
```
man about 45, slicked-back black hair, thin moustache, sharp eyebrows, expensive dark suit with a red tie and gold tie pin,
confident cunning businessman, slightly villainous but not scary, family-friendly
```

### Марина Светлова (marina)
```
woman about 30, short blonde bob haircut, bright red jacket, notebook and pen, press badge,
curious energetic journalist
```

### Олег Смирнов (oleg)
```
man about 40, short brown hair, clean-shaven, navy police uniform with a peaked cap and a golden badge,
calm reliable police chief, friendly face
```

### Баба Зина (zina)
```
grandmother about 75, white hair in a bun, round glasses, warm knitted shawl over a floral dress,
lively and stubborn but loving
```

## Эмоции (добавляйте в конец промпта)

| Файл | Добавка к промпту |
|---|---|
| `_smile` | `gentle closed-mouth smile` |
| `_talk` | `talking, mouth slightly open, friendly explaining gesture` |
| `_happy` | `very happy, big smile, eyes squinting with joy` |
| `_surprised` | `surprised, raised eyebrows, round open mouth` |
| `_worried` | `worried, eyebrows raised in the middle, small frown` |
| `_angry` | `angry, frowning eyebrows, clenched mouth (cartoon, not scary)` |
| `_smug` | `smug smirk, one eyebrow raised, half-closed eyes` |

## Пример полного промпта

```
Cozy cartoon visual-novel character portrait, bust shot, front-facing, soft cel shading, clean dark outlines,
warm friendly colors, big expressive eyes, simple soft pastel background with a blurred little town,
square 1:1, centered, high detail face, no text, no watermark, no logo,
young woman about 25, long straight chestnut-brown hair with soft bangs, green eyes, light skin with a gentle blush,
light-blue blazer over a white shirt, small turquoise pendant necklace, kind and smart look, city deputy mayor,
very happy, big smile, eyes squinting with joy
```

## Важно для Google Play

- Используйте только картинки, которые нейросеть разрешает применять в коммерческих/опубликованных проектах
  (проверьте условия сервиса).
- Не просите сходства с реальными людьми, актёрами или персонажами чужих игр и мультфильмов.
- Не добавляйте на портреты чужие логотипы и бренды.
