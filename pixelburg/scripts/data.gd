class_name Data
extends RefCounted
## Static game data: world layout and zones, buildings, roads, balance, city rules and missions.

# ---------------------------------------------------------------- world
## One tile is 16 x 16 metres. The player's land sits in the middle of a much bigger valley:
## forest right around it, then fields, lakes and villages, and far to the north the horizon.
const PLOT := 10           ## plot size in tiles (160 m)
const PLOTS := 8           ## plots per side (8 x 8 plots = 80 x 80 tiles = 1.28 km)
const MARGIN := 80         ## countryside around the land, in tiles
const FOREST := 8          ## thick forest band right around the land
const LAND0 := MARGIN                ## first tile of the land (80)
const LAND1 := LAND0 + PLOT * PLOTS  ## first tile after the land (160)
const MAP := LAND1 + MARGIN          ## whole valley (240 x 240)
const CENTER := LAND0 + PLOT * PLOTS / 2  ## 120
const HORIZON := 2 * LAND0 - 18      ## tiles with x + y below this are beyond the horizon
const BEACH_W := 10          ## width of the beach strip west of the land, in tiles (one segment per plot row)
const BEACH_X0 := LAND0 - BEACH_W
const HIGHWAY_Y := LAND1 + 6         ## the highway runs along x on this row
const START_PLOTS := [Vector2i(3, 3), Vector2i(4, 3), Vector2i(3, 4), Vector2i(4, 4), Vector2i(5, 3)]
const ZONES := ["city", "farm", "industry", "leisure"]  ## (the "beach" zone is only the bought beach strip)
const LAKES := [[56, 196, 7.0], [200, 70, 6.0], [190, 186, 5.0]]

# ---------------------------------------------------------------- balance
const START_COINS := 1500
const START_GEMS := 5
const TREE_CLEAR_COST := 20
const OFFLINE_CAP := 6 * 3600.0
const DAY_LENGTH := 1080.0  ## real seconds per in-game day (1 hour = 45 s)
const SEASON_DAYS := 4
const MULT := [1.0, 1.6, 2.5]
const POP_MULT := [1.0, 1.3, 1.6]
const JOBS_MULT := [1.0, 1.3, 1.6]
const UPKEEP_MULT := [1.0, 1.4, 1.9]
const GEM_CHANCE := 0.008  ## chance of an emerald when collecting
const TAX_DEFAULT := 10
const TAX_MIN := 0
const TAX_MAX := 25
const LAMP_COST := 40
const LIGHT_COST := 150
const RING_COST := 220     ## a roundabout on a crossing (no power needed)
const RING_UPKEEP := 0.8
const MOVE_COST := 0       ## moving a building is free, only its old spot must be left clean
const CATCH_COST := 80
const ZOO_ANIMALS := 5
const WORKFORCE := 0.6     ## share of residents who work
const POWER_FREE := 3.0    ## kW from the village's old generator: enough for the first houses and lamps
const WATER_FREE := 40     ## residents served by the village wells
const POWER_HOME := 0.1    ## kW per resident
const POWER_JOB := 0.3     ## kW per worker (plus POWER_BASE per business)
const POWER_BASE := 1.0
const POWER_LAMP := 0.25   ## kW per street lamp
## A lamp over the front door of a home (placed with the lamp tool by tapping a house). Its look follows
## the chosen street lamp style; the home gets a little happier.
const HOUSE_LAMP_COST := 30
const HOUSE_LAMP_HAPPY := 2
const HOUSE_LAMP_UPKEEP := 0.25
const POWER_HOUSE_LAMP := 0.1

const ROADS := {
	"dirt": {"name": ["Грунтовка", "Dirt road"], "cost": 6, "upkeep": 0.2, "row": 2, "speed": 0.75},
	"asphalt": {"name": ["Асфальт", "Asphalt"], "cost": 18, "upkeep": 0.5, "row": 3, "speed": 1.0},
	"stone": {"name": ["Брусчатка", "Cobblestone"], "cost": 30, "upkeep": 0.8, "row": 4, "speed": 0.9},
	"boulevard": {"name": ["Бульвар", "Boulevard"], "cost": 45, "upkeep": 1.2, "row": 7, "speed": 1.1},
	"avenue": {"name": ["Проспект", "Avenue"], "cost": 60, "upkeep": 1.5, "row": 8, "speed": 1.3},
	"brick": {"name": ["Кирпичная улица", "Brick street"], "cost": 35, "upkeep": 0.9, "row": 9, "speed": 0.85},
	"bus_lane": {"name": ["Улица с автобусной полосой", "Bus lane street"], "cost": 40, "upkeep": 0.8, "row": 10, "speed": 1.05},
	"bike": {"name": ["Улица с велодорожкой", "Bike lane street"], "cost": 38, "upkeep": 0.7, "row": 11, "speed": 0.95},
	"gravel": {"name": ["Щебёнка", "Gravel road"], "cost": 9, "upkeep": 0.3, "row": 12, "speed": 0.8},
	"concrete": {"name": ["Бетонка из плит", "Concrete plates"], "cost": 22, "upkeep": 0.4, "row": 13, "speed": 0.95},
	"red": {"name": ["Красная улица", "Red street"], "cost": 32, "upkeep": 0.6, "row": 14, "speed": 1.0},
	"highway": {"name": ["Трасса", "Highway"], "cost": 0, "upkeep": 0.0, "row": 5, "speed": 1.6},
	"country": {"name": ["Загородная дорога", "Country road"], "cost": 0, "upkeep": 0.0, "row": 6, "speed": 1.25},
}
## Water the player digs: a river joins into a sea at WATER_SEA tiles and an ocean at WATER_OCEAN.
const WATER_COST := 12
const WATER_SEA := 30
const WATER_OCEAN := 120
## Walls touch the buildings next to them; homes joined by one wall line make a quarter (Game.quarters).
## block: extra mood a quarter gets for having a wall of that kind (the quarter walls made for it).
const WALLS := {
	"stone": {"name": ["Каменная стена", "Stone wall"], "cost": 14, "block": 0},
	"brick": {"name": ["Кирпичная стена", "Brick wall"], "cost": 18, "block": 0},
	"plaster": {"name": ["Стена квартала", "Quarter wall"], "cost": 24, "block": 1},
	"arch": {"name": ["Арка-переход", "Arch passage"], "cost": 45, "block": 2},
}
const WALL_ORDER := ["stone", "brick", "plaster", "arch"]
## Quarter mood: +1 per home in it (from 2 homes), up to QUARTER_HAPPY_MAX, plus the best wall's "block".
const QUARTER_HAPPY_MAX := 6
## Paving on the grass in front of the houses (Game.paves): whole tiles of tiles or a narrow footpath.
## happy: mood of a home with such paving next to it; strollers walk along the paved tiles.
const PAVES := {
	"slabs": {"name": ["Серая плитка", "Grey paving"], "cost": 8, "happy": 1},
	"terracotta": {"name": ["Красная плитка", "Terracotta tiles"], "cost": 12, "happy": 1},
	"mosaic": {"name": ["Узорный кафель", "Patterned tiles"], "cost": 20, "happy": 2},
	"path": {"name": ["Пешеходная дорожка", "Footpath"], "cost": 5, "happy": 1},
}
const PAVE_ORDER := ["slabs", "terracotta", "mosaic", "path"]
const PAVE_UPKEEP := 0.05
const PAVE_HAPPY_MAX := 2
## Street improvements along the sidewalks.
const ROAD_DECO := {
	"railing": {"name": ["Кованая решётка", "Iron railing"], "cost": 10, "happy": 1},
	"planters": {"name": ["Вазоны с цветами", "Flower pots"], "cost": 14, "happy": 2},
	"bollards": {"name": ["Столбики", "Bollards"], "cost": 6, "happy": 0},
}
const ROAD_DECO_ORDER := ["railing", "planters", "bollards"]
const ROAD_ORDER := ["dirt", "gravel", "asphalt", "concrete", "stone", "red", "boulevard", "avenue", "brick", "bus_lane", "bike"]

## Mayor ranks: [min level, min reputation, ru, en, income bonus %]. Rank only goes up (the best one reached is kept).
const RANKS := [
	[1, 0, "Староста деревни", "Village Elder", 0],
	[3, 30, "Глава посёлка", "Town Head", 2],
	[6, 40, "Городской голова", "City Head", 4],
	[10, 45, "Градоначальник", "Governor", 6],
	[15, 50, "Мэр города", "City Mayor", 8],
	[20, 55, "Мэр большого города", "Big City Mayor", 10],
	[28, 60, "Мэр-реформатор", "Reform Mayor", 12],
	[36, 65, "Мэр столицы", "Capital Mayor", 15],
	[45, 70, "Мэр мегаполиса", "Metropolis Mayor", 20],
]


static func rank_for(lvl: int, rep: float) -> int:
	var r := 0
	for i in RANKS.size():
		if lvl >= RANKS[i][0] and rep >= RANKS[i][1]:
			r = i
	return r


## "What's new" shown once after an update. Bump NEWS_VERSION and rewrite NEWS with every release.
const NEWS_VERSION := "1.4.0"
const NEWS := [
	["Звания мэра: от «Старосты деревни» до «Мэра мегаполиса» — звание растёт с уровнем и репутацией и никогда не пропадает. За каждое новое звание — награда и прибавка к доходу города (до +20%), приходит письмо. Звание видно в панели сверху, в профиле и в сведениях о городе.",
	 "Mayor ranks: from «Village Elder» to «Metropolis Mayor» — the rank grows with your level and reputation and is never lost. Every new rank brings a reward and a bonus to the city's income (up to +20%), plus a letter. The rank is shown in the top bar, in the profile and in the city info."],
	["Режим фото: кнопка с фотоаппаратом справа убирает весь интерфейс — остаётся только город. Камеру можно двигать и приближать пальцами, а фильтры «День», «Закат», «Ночь» и «Ч/б» меняют настроение кадра. Кнопка-затвор сохраняет снимок в галерею телефона (папка Pictures/Pixelburg), на компьютере — в папку user://photos. Крестик слева сверху возвращает в игру",
	 "Photo mode: the camera button on the right hides the whole interface so only the city is left. Move and zoom the camera with your fingers, and the Day, Sunset, Night and B&W filters set the mood of the shot. The shutter button saves the picture to the phone's gallery (Pictures/Pixelburg folder), on a computer to user://photos. The cross at the top left takes you back to the game"],
	["Стихийные события с выбором: иногда на город обрушивается наводнение (у реки и моря), землетрясение, снежная буря зимой или нашествие туристов. Приходит письмо с тремя вариантами: дорого и надёжно, дёшево и рискованно или ничего не делать. Пожарные и больница снижают ущерб. Вода заливает берег, по земле идут трещины и трясётся экран, снег заметает улицы, а у достопримечательностей собираются толпы туристов. Повреждённые дома чинятся в их карточке",
	 "Natural events with a choice: now and then the city is hit by a flood (by a river or sea), an earthquake, a winter blizzard or a tourist rush. A letter offers three answers: costly and safe, cheap and risky, or do nothing. Fire stations and a hospital reduce the damage. Water floods the shore, cracks run across the ground and the screen shakes, snow buries the streets, and crowds of tourists gather at the sights. Damaged homes are repaired from their card"],
	["Митинги: если мэр поступает нечестно — грабит банк, держит высокие налоги, сносит дома с жильцами, нарушает правила города — жители злятся. Когда терпение кончается, люди выходят к ратуше с плакатами и требуют своих прав. Можно выслушать их (это стоит денег, налоги вернутся к честным), разогнать полицией (быстро, но доверие упадёт, а злость вырастет) или ждать, пока разойдутся. Недовольство видно в карточке ратуши",
	 "Protests: when the mayor is unfair — robs a bank, keeps taxes high, tears down homes with people inside, breaks the city's rules — residents get angry. When they've had enough, they gather at the town hall with placards and demand their rights. You can hear them (it costs coins, taxes go back to fair), send the police (quick, but trust falls and anger grows) or wait until they go home. The town hall card shows how angry people are"],
	["Офис «it-run» — IT-школа (2x2): тёмный кампус с фиолетовой подсветкой, стеклянным атриумом, светящимся значком </> и спутниковой тарелкой на крыше. Студенты ходят сюда на занятия, как в обычную школу, а город получает пользу: образование, радость жителей и рабочие места для преподавателей.",
	 "The «it-run» office — an IT school (2x2): a dark campus with violet lighting, a glass atrium, a glowing </> logo and a satellite dish on the roof. Students attend classes here just like at a regular school, and the city benefits: education, happier residents and jobs for teachers."],
	["Три супермаркета: «Амид» (сине-белый стеклянный зал с круглым логотипом), «Анис» (кирпичный рынок-зал с полосатыми тентами и звездой-анисом) и «Ёвар» (жёлто-бирюзовый склад-дискаунтер с пилообразной крышей и шестигранным логотипом). Жители ходят туда за покупками, а магазины дают доход и рабочие места.",
	 "Three supermarkets: Amid (a blue-white glass hall with a round logo), Anis (a brick market hall with striped awnings and a star-anise logo) and Yovar (a yellow-teal discount warehouse with a saw-tooth roof and a hexagon logo). Residents go shopping there, and the stores bring income and jobs."],
	["Преступность и ограбления банков: иногда житель грабит банк — люди вокруг разбегаются, полиция мчится с мигалками и может поймать грабителя (тогда деньги вернутся). Новые здания: охрана «Щит» (банки под её защитой грабят реже, а грабителей чаще ловят) и тюрьма (меньше преступлений). Мэр тоже может ограбить банк (кнопка в карточке банка) — но если следствие узнает, мэра посадят: 3 дня нельзя строить, налоги и туристы вдвое меньше, штраф и падение репутации; можно выйти под залог",
	 "Crime and bank heists: now and then a resident robs a bank — people around run away, the police race in with sirens and may catch the robber (then the money comes back). New buildings: Shield Guards (guarded banks are robbed less often and robbers are caught more often) and a prison (less crime). The mayor can rob a bank too (button in the bank's card) — but if the investigation finds out, the mayor goes to prison: no building for 3 days, taxes and tourism halved, a fine and a reputation hit; bail gets you out early"],
	["Бренды жителей: с 6-го уровня жители основывают свои бренды — «Сладкий Ёж» (кондитерские), «Бодрый Кот» (кофейни), «Листик» (продукты), «Зарядик» (электроника), «Нитка» (одежда) и «Пиксельбургер» (бургерные). У каждого свои цвета, вывеска и эмблема. Бренд сам предлагает открыть киоск, магазин, а потом и большой флагман с парковкой; чем больше мест, тем выше уровень всей сети, а налог с них больше обычного", "Residents' brands: from level 6 residents found brands of their own - Sweet Hedgehog (sweet shops), Perky Cat (coffee houses), Leafy (groceries), Zaryadik (electronics), Nitka (clothes) and Pixelburger (burger bars). Each has its own colours, sign and emblem. The brand itself asks to open a kiosk, a shop and later a big flagship with a car park; the more places, the higher the whole chain's level, and they pay more tax than usual"],
	["30 новых объектов, у каждого свой вид. Дороги: щебёнка, бетонка из плит и красная улица. Машины: малолитражка, минивэн, кабриолет, ретро-седан, лимузин, фургон с мороженым и бетономешалка. Здания: книжный, парикмахерская, кафе-мороженое, автомойка, автосервис, автосалон, пост полиции, поликлиника, боулинг, мини-гольф, летняя сцена, скейт-парк, беседка, часовая башня, флагшток, арт-объект, прокат велосипедов, место для пикника, текстильная фабрика и автозавод", "30 new objects, each with its own look. Roads: gravel, concrete plates and a red street. Cars: a city mini, a minivan, a convertible, a retro sedan, a limousine, an ice-cream van and a concrete mixer. Buildings: a bookshop, a barber shop, an ice-cream parlour, a car wash, an auto repair shop, a car dealership, a police post, a clinic, a bowling alley, mini golf, an open-air stage, a skate park, a gazebo, a clock tower, a flagpole, an art sculpture, a bike rental, a picnic spot, a textile mill and a car plant"],
	["Новые недорогие дома для начала игры, у каждого свой вид: бревенчатая изба с резными наличниками и поленницей, глинобитный дом с тандыром, кирпичный домик с живой изгородью, домик-шалаш со стеклянным фасадом и костровищем, дом из морских контейнеров, белый средиземноморский дом с террасой на крыше и дом на две семьи", "New cheap homes for the early game, each with its own look: a log cabin with carved window frames and a woodpile, an adobe house with a tandoor oven, a brick house behind a hedge, an A-frame cabin with a glass front and a fire pit, a shipping-container house, a whitewashed Mediterranean house with a roof terrace and a duplex for two families"],
	["Крепость Худжанда — одна на город (4x4): кирпичные стены с круглыми зубцами, башни, высокий портал ворот со стрельчатой аркой, музей во дворе, а перед ней парк Камоли Худжанди с фонтаном, чинарами и памятником поэту. Привлекает больше всего туристов", "The Khujand Fortress, one per city (4x4): brick walls with rounded battlements, towers, a tall gate portal with a pointed arch, a museum in the courtyard and in front the Kamoli Khujandi park with a fountain, plane trees and the poet's statue. Draws the most tourists of all"],
	["Замок и исторические объекты, у каждого свой вид: каменный замок со рвом, башнями и донжоном, мавзолей с бирюзовым куполом, пятиярусная пагода, руины античного храма (с уровнем его восстанавливают), кирпичный минарет и триумфальная арка. Они радуют жителей и привлекают туристов", "A castle and historic sights, each with its own look: a stone castle with a moat, towers and a keep, a mausoleum with a turquoise dome, a five-tier pagoda, ruins of an ancient temple (restored as it levels up), a brick minaret and a triumphal arch. They cheer residents up and draw tourists"],
	["Плитка вместо травы: в режиме дорог выберите «Плитка» и проведите пальцем перед домами — серая, красная или узорная плитка и пешеходные дорожки. По ним гуляют пешеходы, иногда с собакой, а жителям рядом приятнее", "Paving instead of grass: in road mode pick «Paving» and drag in front of the houses - grey, terracotta or patterned tiles and footpaths. People stroll along them, sometimes with a dog, and the homes beside them are happier"],
	["Фонарь над входом: в режиме фонаря нажмите на дом — над дверью появится фонарь (классика, модерн или два плафона по бокам), ночью он светит на крыльцо, а жителям уютнее", "A lamp over the door: in lamp mode tap a house and a lamp appears above its entrance (classic, modern or twin lights on both sides); at night it lights the porch and the residents feel cosier"],
	["Дома можно связать в единый квартал: проведите стену от дома к дому — стена примыкает к домам. Новые стены: штукатурная стена квартала с черепицей и арка-переход с крышей. Дома одного квартала счастливее", "Join homes into one quarter: draw a wall from house to house and it joins onto them. New walls: a plastered quarter wall with a tiled top and a roofed arch passage. Homes of one quarter are happier"],
	["Многоэтажные парковки, у каждой свой вид: бетонная с открытыми этажами, автоматическая башня со стеллажами, зелёная с растениями и солнечной крышей и круглая со спиральным пандусом — машины жителей заезжают внутрь и паркуются, в карточке видно, сколько мест занято", "Multi-storey car parks, each with its own look: an open concrete deck garage, an automated tower with car racks, a green garage with plants and a solar roof and a round one with a spiral ramp - residents' cars drive in and park there, and the card shows how many places are taken"],
	["Кольцо на перекрёстке: нажмите на перекрёсток и выберите «Кольцо» — машины объезжают островок с фонтаном по кругу и уступают тем, кто уже на кольце, светофор и электричество не нужны", "Roundabouts: tap a crossing and choose Roundabout - cars circle an island with a fountain and give way to those already on the ring, no traffic light or power needed"],
	["В настройках можно увеличить или уменьшить кнопки и иконки (от 80% до 150%) — подстройте интерфейс под свой телефон, выбор сохраняется", "In the settings you can make the buttons and icons bigger or smaller (80% to 150%) - fit the interface to your phone, the choice is saved"],
	["Два новых вида заправки, у каждой свой вид: электрозаправка с солнечными панелями на навесе и электромобилями на зарядке и большая заправка у трассы с колонками, магазином, кафе, автомойкой и стелой с ценами", "Two new kinds of filling stations, each with its own look: an EV charging station with a solar roof and electric cars plugged in, and a big highway fuel stop with pumps, a shop, a cafe, a car wash and a price pylon"],
	["Новые деревья, у каждого свой вид: берёзы, сосны и ели, тополя, яблоня с яблоками, осенний клён, плакучая ива, сакура, пальмы и чинара — ставятся как украшение и растут в природе", "New trees, each with its own look: birches, pines and spruces, poplars, an apple tree, an autumn maple, a weeping willow, sakura, palms and a chinar - place them as decoration, and they also grow in the wild"],
	["Новые здания для ферм, у каждого свой вид: пасека с ульями, птичник с курами, бахча с дынями и навесом на сваях, виноградник со шпалерами, мельница с крыльями, рыбное хозяйство с садками и большая молочная ферма", "New farm buildings, each with its own look: an apiary with beehives, a poultry farm with chickens, a melon field with a shelter on stilts, a vineyard with trellises, a windmill with sails, a fish farm with net cages and a big dairy"],
	["Кафе и фастфуд, каждый со своим видом: кофейня-киоск с огромной чашкой, шаурма, пончиковая, бургерная, дворик фудтраков, чайхана с топчанами и фастфуд с автоокном", "Cafes and fast food, each with its own look: a coffee kiosk with a giant cup, a shawarma grill, a donut shop, a burger bar, a food truck court, a chaikhana teahouse and a drive-thru"],
	["Двери открываются по-настоящему: створка поворачивается внутрь, видно освещённую комнату, а ночью свет падает на тротуар", "Doors open for real: the leaf swings inside, you can see the lit room, and at night light spills onto the sidewalk"],
	["Аэропорт: купите рейсы в 16 стран — самолёты привозят путешественников со всего мира, а аналитика покажет, из какой страны пришло больше всего людей", "Airport: buy flights to 16 countries; planes bring travellers from all over the world, and the analytics show which country sends the most people"],
	["Пляж за границей карты: купите участки пляжа у моря и стройте зонты, спасательную вышку и пляжный бар", "Beach beyond the map border: buy beach plots by the sea and build umbrellas, a lifeguard tower and a beach bar"],
	["Река, море и океан: копайте воду пальцем, над дорогой будет мост, у домов — берег", "Rivers, seas and oceans: dig water with your finger, roads become bridges"],
	["Лодки, корабли, утки, чайки, камни и камыши у воды", "Boats, ships, ducks, gulls, stones and reeds by the water"],
	["Башня Душанбе и квартал жёлтых домов вокруг неё", "Dushanbe Tower and its quarter of yellow homes"],
	["Отели в отдельной вкладке — откроются, когда дорога дойдёт до трассы", "Hotels in their own tab: they open once a road reaches the highway"],
	["Автобусы, остановки и метро под землёй", "Buses, bus stops and an underground metro"],
	["Новые дороги: проспект, кирпичная, автобусная полоса, велодорожка — и велосипедисты", "New roads: avenue, brick, bus lane, bike lane, and cyclists"],
	["Красивые башни, спортивная башня, башня-виллы", "Signature towers, a sports tower and a sky-villa tower"],
	["Новые дома: американский, азиатский, таджикский и дачи с большими участками", "New homes: American, Asian and Tajik houses, and dachas with big plots"],
	["Стены, украшения улиц и новый фонарь", "Walls, street decoration and a new street lamp"],
	["Кнопка-глаз делает высокие здания прозрачными", "The eye button makes tall buildings see-through"],
	["Выход из игры: кнопка в настройках и двойное «Назад»", "Quitting: a button in settings, or press Back twice"],
	["Остановки разного вида: навес, стеклянная, с рекламой и экраном, деревенская", "Bus stops of every kind: simple, glass, with ads and a screen, village"],
	["Телевидение: маленькая студия, телецентр и высокая телебашня — жители счастливее", "Television: a small studio, a TV centre and a tall TV tower make residents happier"],
	["Газеты: киоск и редакция — новости о городе: население, счастье, деньги, пожары", "Newspapers: a newsstand and an office with news about your city: people, mood, money, fires"],
	["Недостроенные дома и стройки с краном — для красоты, как будто идёт стройка", "Unfinished houses and building sites with a crane, for looks, as if a construction is going on"],
	["Рынок: рыночный прилавок, открытый рынок и крытый базар — торговля свежими продуктами", "Markets: a market stall, an open-air market and a covered bazaar selling fresh goods"],
	["Мусор: жители производят отходы, станция вывоза и завод отправляют мусоровозки по дорогам — иначе падает счастье и растёт загрязнение", "Garbage: residents make waste; depots and recycling plants send trucks along the roads, or mood drops and pollution rises"],
]

## Category: home | shop | ind | service | fun (leisure businesses) | decor.
## zones: where it may be built. upkeep: coins per in-game day (salaries for services).
## pop is the number of residents (a little house is one family), jobs the workers needed.
const B := {
	# ------------------------------------------------ homes (pop, rent per cycle)
	"house_small": {"name": ["Домик", "Little House"], "cat": "home", "zones": ["city"], "size": 1, "cost": 120, "lvl": 1, "time": 10,
		"pop": 4, "rent": 10, "cycle": 90, "upkeep": 6},
	"house_american": {"name": ["Американский дом", "American House"], "cat": "home", "zones": ["city"], "size": 1, "cost": 300, "lvl": 2,
		"time": 18, "pop": 5, "rent": 18, "cycle": 110, "upkeep": 9},
	"house_tajik": {"name": ["Таджикский дом", "Tajik House"], "cat": "home", "zones": ["city", "farm"], "size": 1, "cost": 260, "lvl": 2,
		"time": 16, "pop": 6, "rent": 16, "cycle": 110, "upkeep": 8},
	"house_log": {"name": ["Изба", "Log Cabin"], "cat": "home", "zones": ["city", "farm"], "size": 1, "cost": 140, "lvl": 1,
		"time": 12, "pop": 4, "rent": 11, "cycle": 90, "upkeep": 6},
	"house_adobe": {"name": ["Глинобитный дом", "Adobe House"], "cat": "home", "zones": ["city", "farm"], "size": 1, "cost": 110, "lvl": 1,
		"time": 10, "pop": 5, "rent": 10, "cycle": 90, "upkeep": 5},
	"house_brick": {"name": ["Кирпичный домик", "Brick House"], "cat": "home", "zones": ["city"], "size": 1, "cost": 180, "lvl": 1,
		"time": 14, "pop": 4, "rent": 13, "cycle": 100, "upkeep": 7},
	"house_aframe": {"name": ["Домик-шалаш", "A-Frame Cabin"], "cat": "home", "zones": ["city", "leisure"], "size": 1, "cost": 220, "lvl": 2,
		"time": 15, "pop": 3, "rent": 14, "cycle": 100, "upkeep": 7},
	"house_container": {"name": ["Дом из контейнеров", "Container House"], "cat": "home", "zones": ["city"], "size": 1, "cost": 240, "lvl": 2,
		"time": 14, "pop": 4, "rent": 16, "cycle": 100, "upkeep": 8},
	"house_med": {"name": ["Средиземноморский дом", "Mediterranean House"], "cat": "home", "zones": ["city"], "size": 1, "cost": 280, "lvl": 2,
		"time": 18, "pop": 5, "rent": 18, "cycle": 110, "upkeep": 9},
	"house_duplex": {"name": ["Дом на две семьи", "Duplex"], "cat": "home", "zones": ["city"], "size": 1, "cost": 380, "lvl": 3,
		"time": 22, "pop": 8, "rent": 24, "cycle": 120, "upkeep": 12},
	"house_asian": {"name": ["Азиатский дом", "Asian House"], "cat": "home", "zones": ["city"], "size": 1, "cost": 520, "lvl": 3,
		"time": 25, "pop": 4, "rent": 24, "cycle": 120, "upkeep": 12},
	"dacha": {"name": ["Дача", "Dacha"], "cat": "home", "zones": ["farm", "city", "leisure"], "size": 2, "cost": 700, "lvl": 3, "time": 30,
		"pop": 4, "rent": 26, "cycle": 140, "upkeep": 10},
	"cottage": {"name": ["Коттедж", "Cottage"], "cat": "home", "zones": ["city"], "size": 1, "cost": 450, "lvl": 3, "time": 25,
		"pop": 5, "rent": 22, "cycle": 120, "upkeep": 12},
	"bungalow": {"name": ["Современный дом", "Modern House"], "cat": "home", "zones": ["city"], "size": 1, "cost": 900, "lvl": 5, "time": 40,
		"pop": 4, "rent": 34, "cycle": 150, "upkeep": 18},
	"townhouse": {"name": ["Таунхаусы", "Townhouses"], "cat": "home", "zones": ["city"], "size": 2, "cost": 1800, "lvl": 6, "time": 80,
		"pop": 12, "rent": 70, "cycle": 180, "upkeep": 35},
	"khrushchevka": {"name": ["Хрущёвка", "Panel Block"], "cat": "home", "zones": ["city"], "size": 2, "cost": 3200, "lvl": 8, "time": 120,
		"pop": 30, "rent": 110, "cycle": 200, "upkeep": 50},
	"dorm": {"name": ["Общежитие", "Dormitory"], "cat": "home", "zones": ["city"], "size": 2, "cost": 4200, "lvl": 9, "time": 140,
		"pop": 40, "rent": 125, "cycle": 200, "upkeep": 60},
	"villa": {"name": ["Вилла", "Villa"], "cat": "home", "zones": ["city"], "size": 2, "cost": 4500, "lvl": 9, "time": 120,
		"pop": 6, "rent": 140, "cycle": 240, "upkeep": 60},
	"apartments": {"name": ["Многоэтажка", "Apartments"], "cat": "home", "zones": ["city"], "size": 2, "cost": 6000, "lvl": 11, "time": 180,
		"pop": 50, "rent": 180, "cycle": 240, "upkeep": 80},
	"panel_block": {"name": ["Панельная многоэтажка", "High-rise Block"], "cat": "home", "zones": ["city"], "size": 2, "cost": 8500, "lvl": 12, "time": 200,
		"pop": 70, "rent": 220, "cycle": 260, "upkeep": 100},
	"condo": {"name": ["Жилой комплекс", "Condo"], "cat": "home", "zones": ["city"], "size": 2, "cost": 13000, "gems": 5, "lvl": 15, "time": 240,
		"pop": 100, "rent": 300, "cycle": 300, "upkeep": 140},
	"tower": {"name": ["Небоскрёб", "Skyscraper"], "cat": "home", "zones": ["city"], "size": 2, "cost": 26000, "gems": 10, "lvl": 19, "time": 300,
		"pop": 200, "rent": 480, "cycle": 300, "upkeep": 220},
	"highrise": {"name": ["Жилая башня", "Residential Tower"], "cat": "home", "zones": ["city"], "size": 2, "cost": 9500, "lvl": 13, "time": 210,
		"pop": 75, "rent": 240, "cycle": 270, "upkeep": 100},
	"sky_home": {"name": ["Жилой небоскрёб", "Residential Skyscraper"], "cat": "home", "zones": ["city"], "size": 3, "cost": 48000, "gems": 20, "lvl": 24, "time": 420,
		"pop": 420, "rent": 900, "cycle": 360, "upkeep": 420},
	# the sand-yellow homes of the Dushanbe Tower quarter (42 in the project): built once the tower stands, happier close to it
	"dushanbe_home": {"name": ["Дом квартала «Душанбе»", "Dushanbe Quarter Home"], "cat": "home", "zones": ["city"], "size": 2, "cost": 14000,
		"gems": 3, "lvl": 27, "time": 220, "needs": "dushanbe_tower", "pop": 140, "rent": 360, "cycle": 300, "upkeep": 130},
	# towers with a signature design
	"sky_villa": {"name": ["Башня-виллы", "Sky Villas"], "cat": "home", "zones": ["city"], "size": 2, "cost": 34000, "gems": 12, "lvl": 21,
		"time": 340, "pop": 60, "rent": 620, "cycle": 300, "upkeep": 200},
	"round_tower": {"name": ["Круглая башня", "Round Tower"], "cat": "home", "zones": ["city"], "size": 2, "cost": 12000, "gems": 3, "lvl": 14, "time": 240,
		"pop": 90, "rent": 280, "cycle": 270, "upkeep": 110},
	"deco_tower": {"name": ["Башня ар-деко", "Art Deco Tower"], "cat": "home", "zones": ["city"], "size": 2, "cost": 22000, "gems": 8, "lvl": 17, "time": 300,
		"pop": 150, "rent": 420, "cycle": 300, "upkeep": 170},
	"stack_tower": {"name": ["Башня-каскад", "Cascade Tower"], "cat": "home", "zones": ["city"], "size": 2, "cost": 30000, "gems": 12, "lvl": 20, "time": 330,
		"pop": 210, "rent": 520, "cycle": 300, "upkeep": 230},
	"twin_towers": {"name": ["Башни-близнецы", "Skybridge Twins"], "cat": "home", "zones": ["city"], "size": 3, "cost": 42000, "gems": 16, "lvl": 22, "time": 400,
		"pop": 360, "rent": 800, "cycle": 360, "upkeep": 360},
	# the landmark: one per city (77-floor tower and four more high-rises, offices, mall, hotel); brings tourists
	"dushanbe_tower": {"name": ["Башня Душанбе", "Dushanbe Tower"], "cat": "shop", "unique": true, "landmark": true, "zones": ["city"], "size": 4,
		"cost": 120000, "gems": 40, "lvl": 27, "time": 600, "jobs": 300, "use": 0, "income": 3200, "cycle": 400, "upkeep": 600},
	# ------------------------------------------------ hotels (own tab; open only with a road to the highway)
	"hotel_boutique": {"name": ["Бутик-отель", "Boutique Hotel"], "cat": "shop", "tab": "hotel", "highway": true, "zones": ["city", "leisure"], "size": 2,
		"cost": 9000, "gems": 2, "lvl": 10, "time": 200, "jobs": 12, "use": 0, "income": 300, "cycle": 240, "upkeep": 70},
	"hotel_resort": {"name": ["Курортный отель", "Resort Hotel"], "cat": "shop", "tab": "hotel", "highway": true, "zones": ["leisure", "city"], "size": 3,
		"cost": 18000, "gems": 5, "lvl": 14, "time": 260, "jobs": 24, "use": 0, "income": 520, "cycle": 260, "upkeep": 120},
	"hotel_palace": {"name": ["Отель-дворец", "Palace Hotel"], "cat": "shop", "tab": "hotel", "highway": true, "zones": ["city", "leisure"], "size": 3,
		"cost": 30000, "gems": 10, "lvl": 18, "time": 320, "jobs": 36, "use": 0, "income": 820, "cycle": 300, "upkeep": 180},
	"hotel_sail": {"name": ["Отель «Парус»", "Sail Hotel"], "cat": "shop", "tab": "hotel", "highway": true, "zones": ["leisure", "city"], "size": 3,
		"cost": 45000, "gems": 16, "lvl": 22, "time": 380, "jobs": 50, "use": 0, "income": 1200, "cycle": 330, "upkeep": 260},
	"hotel_grand": {"name": ["Гранд-отель", "Grand Hotel"], "cat": "shop", "tab": "hotel", "highway": true, "zones": ["city"], "size": 3,
		"cost": 65000, "gems": 24, "lvl": 26, "time": 450, "jobs": 70, "use": 0, "income": 1700, "cycle": 360, "upkeep": 360},
	# ------------------------------------------------ shops and offices (jobs, goods used, income per cycle)
	"bakery": {"name": ["Пекарня", "Bakery"], "cat": "shop", "zones": ["city"], "size": 1, "cost": 250, "lvl": 1, "time": 15,
		"jobs": 2, "use": 6, "income": 30, "cycle": 90, "upkeep": 8},
	"cafe": {"name": ["Кафе", "Cafe"], "cat": "shop", "zones": ["city", "leisure"], "size": 1, "cost": 700, "lvl": 2, "time": 30,
		"jobs": 3, "use": 8, "income": 48, "cycle": 100, "upkeep": 12},
	# cafes and fast food, each with its own look (tools/art/b_food.py)
	"coffee_kiosk": {"name": ["Кофейня-киоск", "Coffee Kiosk"], "cat": "shop", "zones": ["city", "leisure"], "size": 1, "cost": 500, "lvl": 2, "time": 20,
		"jobs": 2, "use": 5, "income": 38, "cycle": 90, "upkeep": 7},
	"shawarma": {"name": ["Шаурма", "Shawarma Grill"], "cat": "shop", "zones": ["city", "leisure"], "size": 1, "cost": 900, "lvl": 3, "time": 25,
		"jobs": 2, "use": 7, "income": 50, "cycle": 95, "upkeep": 9},
	"donut_shop": {"name": ["Пончиковая", "Donut Shop"], "cat": "shop", "zones": ["city", "leisure"], "size": 1, "cost": 1300, "lvl": 4, "time": 35,
		"jobs": 3, "use": 9, "income": 62, "cycle": 105, "upkeep": 13},
	"burger_bar": {"name": ["Бургерная", "Burger Bar"], "cat": "shop", "zones": ["city", "leisure"], "size": 1, "cost": 1500, "lvl": 5, "time": 40,
		"jobs": 4, "use": 10, "income": 72, "cycle": 110, "upkeep": 16},
	"food_trucks": {"name": ["Дворик фудтраков", "Food Truck Court"], "cat": "shop", "zones": ["city", "leisure"], "size": 2, "cost": 3400, "lvl": 7, "time": 70,
		"jobs": 9, "use": 18, "income": 140, "cycle": 140, "upkeep": 36},
	"chaikhana": {"name": ["Чайхана", "Teahouse (Chaikhana)"], "cat": "shop", "zones": ["city", "leisure"], "size": 2, "cost": 5200, "lvl": 9, "time": 110,
		"jobs": 10, "use": 22, "income": 175, "cycle": 150, "upkeep": 44},
	"drive_thru": {"name": ["Фастфуд с автоокном", "Drive-Thru"], "cat": "shop", "zones": ["city", "industry"], "size": 2, "cost": 6500, "lvl": 11, "time": 130,
		"jobs": 12, "use": 28, "income": 205, "cycle": 160, "upkeep": 55},
	"flowershop": {"name": ["Цветочный", "Flower Shop"], "cat": "shop", "zones": ["city"], "size": 1, "cost": 1100, "lvl": 4, "time": 40,
		"jobs": 3, "use": 10, "income": 62, "cycle": 110, "upkeep": 15},
	"pharmacy": {"name": ["Аптека", "Pharmacy"], "cat": "shop", "zones": ["city"], "size": 1, "cost": 1400, "lvl": 5, "time": 45,
		"jobs": 3, "use": 9, "income": 72, "cycle": 110, "upkeep": 16},
	"bookshop": {"name": ["Книжный магазин", "Bookshop"], "cat": "shop", "zones": ["city"], "size": 1, "cost": 900, "lvl": 4, "time": 35,
		"jobs": 2, "use": 8, "income": 50, "cycle": 110, "upkeep": 12},
	"barber": {"name": ["Парикмахерская", "Barber Shop"], "cat": "shop", "zones": ["city"], "size": 1, "cost": 600, "lvl": 3, "time": 25,
		"jobs": 2, "use": 6, "income": 38, "cycle": 100, "upkeep": 9},
	"ice_cream": {"name": ["Кафе-мороженое", "Ice Cream Parlour"], "cat": "shop", "zones": ["city", "leisure"], "size": 1, "cost": 700, "lvl": 3, "time": 25,
		"jobs": 2, "use": 8, "income": 44, "cycle": 100, "upkeep": 10},
	"car_wash": {"name": ["Автомойка", "Car Wash"], "cat": "shop", "zones": ["city"], "size": 1, "cost": 1300, "lvl": 5, "time": 40,
		"jobs": 2, "use": 10, "income": 66, "cycle": 110, "upkeep": 14},
	"auto_repair": {"name": ["Автосервис", "Auto Repair"], "cat": "shop", "zones": ["city", "industry"], "size": 1, "cost": 1600, "lvl": 6, "time": 45,
		"jobs": 4, "use": 10, "income": 80, "cycle": 120, "upkeep": 18},
	"car_dealer": {"name": ["Автосалон", "Car Dealership"], "cat": "shop", "zones": ["city"], "size": 2, "cost": 6500, "lvl": 10, "time": 140,
		"jobs": 8, "use": 20, "income": 260, "cycle": 180, "upkeep": 60},
	"pizzeria": {"name": ["Пиццерия", "Pizzeria"], "cat": "shop", "zones": ["city", "leisure"], "size": 1, "cost": 1800, "lvl": 6, "time": 50,
		"jobs": 4, "use": 12, "income": 85, "cycle": 120, "upkeep": 20},
	"gas_station": {"name": ["Заправка", "Gas Station"], "cat": "shop", "zones": ["city", "industry", "farm"], "size": 1, "cost": 2200, "lvl": 7, "time": 55,
		"jobs": 3, "use": 10, "income": 95, "cycle": 110, "upkeep": 20},
	"ev_station": {"name": ["Электрозаправка", "EV Charging Station"], "cat": "shop", "zones": ["city", "industry", "leisure"], "size": 1, "cost": 3200, "lvl": 9, "time": 60,
		"jobs": 2, "use": 10, "income": 115, "cycle": 120, "upkeep": 18},
	"gas_highway": {"name": ["Заправка у трассы", "Highway Fuel Stop"], "cat": "shop", "zones": ["city", "industry", "farm"], "size": 2, "cost": 7800, "lvl": 12, "time": 150,
		"jobs": 14, "use": 32, "income": 240, "cycle": 170, "upkeep": 60},
	"boutique": {"name": ["Бутик", "Boutique"], "cat": "shop", "zones": ["city"], "size": 1, "cost": 2600, "lvl": 8, "time": 60,
		"jobs": 4, "use": 14, "income": 110, "cycle": 130, "upkeep": 26},
	"supermarket": {"name": ["Супермаркет", "Supermarket"], "cat": "shop", "zones": ["city"], "size": 2, "cost": 4200, "lvl": 10, "time": 120,
		"jobs": 12, "use": 30, "income": 170, "cycle": 160, "upkeep": 50},
	"amid": {"name": ["Супермаркет «Амид»", "Amid Supermarket"], "cat": "shop", "zones": ["city"], "size": 2, "cost": 5200, "lvl": 11, "time": 130,
		"jobs": 14, "use": 34, "income": 200, "cycle": 160, "upkeep": 56},
	"anis": {"name": ["Супермаркет «Анис»", "Anis Supermarket"], "cat": "shop", "zones": ["city"], "size": 2, "cost": 4600, "lvl": 10, "time": 120,
		"jobs": 13, "use": 32, "income": 182, "cycle": 155, "upkeep": 52},
	"yovar": {"name": ["Супермаркет «Ёвар»", "Yovar Supermarket"], "cat": "shop", "zones": ["city", "industry"], "size": 2, "cost": 3800, "lvl": 9, "time": 110,
		"jobs": 12, "use": 36, "income": 160, "cycle": 140, "upkeep": 44},
	"market_stall": {"name": ["Рыночный прилавок", "Market Stall"], "cat": "shop", "zones": ["city", "farm", "leisure"], "size": 1, "cost": 600, "lvl": 3, "time": 20,
		"jobs": 2, "use": 6, "income": 40, "cycle": 90, "upkeep": 6},
	"market": {"name": ["Рынок", "Market"], "cat": "shop", "zones": ["city", "farm", "leisure"], "size": 2, "cost": 3800, "lvl": 8, "time": 90,
		"jobs": 10, "use": 20, "income": 150, "cycle": 140, "upkeep": 40},
	"bazaar": {"name": ["Крытый базар", "Covered Bazaar"], "cat": "shop", "zones": ["city"], "size": 3, "cost": 16000, "gems": 4, "lvl": 14, "time": 220,
		"jobs": 32, "use": 60, "income": 430, "cycle": 220, "upkeep": 120},
	"office": {"name": ["Бизнес-центр", "Office Block"], "cat": "shop", "zones": ["city"], "size": 2, "cost": 8000, "lvl": 11, "time": 160,
		"jobs": 30, "use": 0, "income": 190, "cycle": 200, "upkeep": 60},
	"restaurant": {"name": ["Ресторан", "Restaurant"], "cat": "shop", "zones": ["city", "leisure"], "size": 2, "cost": 7000, "lvl": 12, "time": 150,
		"jobs": 14, "use": 36, "income": 230, "cycle": 170, "upkeep": 65},
	"cinema": {"name": ["Кинотеатр", "Cinema"], "cat": "shop", "zones": ["city", "leisure"], "size": 2, "cost": 10000, "lvl": 14, "time": 200,
		"jobs": 16, "use": 40, "income": 320, "cycle": 200, "upkeep": 90},
	"hotel": {"name": ["Отель", "Hotel"], "cat": "shop", "zones": ["city", "leisure"], "size": 2, "cost": 14000, "gems": 4, "lvl": 15, "time": 240,
		"jobs": 20, "use": 30, "income": 400, "cycle": 240, "upkeep": 110},
	"sky_office": {"name": ["Офисный небоскрёб", "Office Skyscraper"], "cat": "shop", "zones": ["city"], "size": 3, "cost": 52000, "gems": 20, "lvl": 25, "time": 420,
		"jobs": 160, "use": 0, "income": 1500, "cycle": 360, "upkeep": 380},
	"sky_heli": {"name": ["Небоскрёб с вертолётной площадкой", "Helipad Skyscraper"], "cat": "shop", "zones": ["city"], "size": 3, "cost": 62000, "gems": 24, "lvl": 26, "time": 480,
		"jobs": 180, "use": 0, "income": 1800, "cycle": 360, "upkeep": 420},
	"mall": {"name": ["Торговый центр", "Mall"], "cat": "shop", "zones": ["city"], "size": 3, "cost": 20000, "gems": 8, "lvl": 18, "time": 300,
		"jobs": 40, "use": 80, "income": 560, "cycle": 240, "upkeep": 160},
	# ------------------------------------------------ production (jobs, goods out per cycle)
	"farm": {"name": ["Ферма", "Farm"], "cat": "ind", "zones": ["farm"], "size": 2, "cost": 150, "lvl": 1, "time": 12,
		"jobs": 3, "out": 16, "cycle": 60, "upkeep": 6, "poll": 1},
	"orchard": {"name": ["Сад", "Orchard"], "cat": "ind", "zones": ["farm"], "size": 2, "cost": 900, "lvl": 3, "time": 40,
		"jobs": 5, "out": 30, "cycle": 90, "upkeep": 12, "poll": 0},
	"greenhouse": {"name": ["Теплица", "Greenhouse"], "cat": "ind", "zones": ["farm"], "size": 2, "cost": 1600, "lvl": 4, "time": 50,
		"jobs": 6, "out": 45, "cycle": 100, "upkeep": 18, "poll": 0},
	"warehouse": {"name": ["Склад", "Warehouse"], "cat": "ind", "zones": ["industry", "farm"], "size": 2, "cost": 2000, "lvl": 5, "time": 55,
		"jobs": 5, "out": 40, "cycle": 100, "upkeep": 16, "poll": 2},
	"ranch": {"name": ["Ранчо", "Ranch"], "cat": "ind", "zones": ["farm"], "size": 2, "cost": 2400, "lvl": 6, "time": 70,
		"jobs": 7, "out": 60, "cycle": 120, "upkeep": 24, "poll": 2},
	# new farm buildings, each with its own look (tools/art/b_farm.py)
	"apiary": {"name": ["Пасека", "Apiary"], "cat": "ind", "zones": ["farm"], "size": 1, "cost": 450, "lvl": 2, "time": 20,
		"jobs": 2, "out": 12, "cycle": 50, "upkeep": 4, "poll": 0},
	"chicken_farm": {"name": ["Птичник", "Poultry Farm"], "cat": "ind", "zones": ["farm"], "size": 2, "cost": 1200, "lvl": 3, "time": 40,
		"jobs": 4, "out": 34, "cycle": 80, "upkeep": 12, "poll": 2},
	"melon_field": {"name": ["Бахча", "Melon Field"], "cat": "ind", "zones": ["farm"], "size": 2, "cost": 1400, "lvl": 4, "time": 45,
		"jobs": 5, "out": 40, "cycle": 90, "upkeep": 14, "poll": 0},
	"vineyard": {"name": ["Виноградник", "Vineyard"], "cat": "ind", "zones": ["farm"], "size": 2, "cost": 2200, "lvl": 5, "time": 60,
		"jobs": 6, "out": 52, "cycle": 100, "upkeep": 20, "poll": 0},
	"windmill": {"name": ["Мельница", "Windmill"], "cat": "ind", "zones": ["farm"], "size": 2, "cost": 2800, "lvl": 6, "time": 75,
		"jobs": 5, "out": 62, "cycle": 110, "upkeep": 22, "poll": 0},
	"fish_farm": {"name": ["Рыбное хозяйство", "Fish Farm"], "cat": "ind", "zones": ["farm"], "size": 2, "cost": 3400, "lvl": 7, "time": 90,
		"jobs": 7, "out": 80, "cycle": 120, "upkeep": 30, "poll": 1},
	"dairy": {"name": ["Молочная ферма", "Dairy"], "cat": "ind", "zones": ["farm"], "size": 3, "cost": 6000, "gems": 2, "lvl": 9, "time": 140,
		"jobs": 12, "out": 150, "cycle": 160, "upkeep": 50, "poll": 3},
	"sawmill": {"name": ["Лесопилка", "Sawmill"], "cat": "ind", "zones": ["industry"], "size": 2, "cost": 1800, "lvl": 5, "time": 60,
		"jobs": 8, "out": 50, "cycle": 100, "upkeep": 20, "poll": 6},
	"workshop": {"name": ["Мастерская", "Workshop"], "cat": "ind", "zones": ["industry"], "size": 2, "cost": 3000, "lvl": 7, "time": 90,
		"jobs": 10, "out": 75, "cycle": 120, "upkeep": 30, "poll": 6},
	"textile_mill": {"name": ["Текстильная фабрика", "Textile Mill"], "cat": "ind", "zones": ["industry"], "size": 2, "cost": 5000, "lvl": 9, "time": 130,
		"jobs": 14, "out": 120, "cycle": 160, "upkeep": 50, "poll": 7},
	"factory": {"name": ["Фабрика", "Factory"], "cat": "ind", "zones": ["industry"], "size": 2, "cost": 7000, "lvl": 10, "time": 150,
		"jobs": 20, "out": 160, "cycle": 180, "upkeep": 70, "poll": 10},
	"car_plant": {"name": ["Автозавод", "Car Plant"], "cat": "ind", "zones": ["industry"], "size": 3, "cost": 16000, "gems": 4, "lvl": 15, "time": 260,
		"jobs": 30, "out": 380, "cycle": 220, "upkeep": 120, "poll": 12},
	"logistics": {"name": ["Логистический центр", "Logistics Hub"], "cat": "ind", "zones": ["industry"], "size": 3, "cost": 15000, "gems": 5, "lvl": 16, "time": 240,
		"jobs": 25, "out": 280, "cycle": 220, "upkeep": 110, "poll": 6},
	# ------------------------------------------------ services (jobs, coverage radius, happiness, salaries)
	"kindergarten": {"name": ["Детский сад", "Kindergarten"], "cat": "service", "zones": ["city"], "size": 1, "cost": 1200, "lvl": 3, "time": 50,
		"jobs": 3, "upkeep": 15, "svc": "edu", "radius": 9, "happy": 5},
	"school": {"name": ["Школа", "School"], "cat": "service", "zones": ["city"], "size": 2, "cost": 2500, "lvl": 4, "time": 90,
		"jobs": 6, "upkeep": 40, "svc": "edu", "radius": 16, "happy": 8},
	"it_run": {"name": ["IT-школа «it-run»", "IT School «it-run»"], "cat": "service", "zones": ["city"], "size": 2, "cost": 6800, "lvl": 12, "time": 140,
		"jobs": 9, "upkeep": 70, "svc": "edu", "radius": 18, "happy": 9},
	"post_office": {"name": ["Почта", "Post Office"], "cat": "service", "zones": ["city"], "size": 1, "cost": 1800, "lvl": 5, "time": 60,
		"jobs": 3, "upkeep": 18, "svc": "post", "radius": 18, "happy": 3},
	"fire_station": {"name": ["Пожарная часть", "Fire Station"], "cat": "service", "zones": ["city", "industry"], "size": 2, "cost": 3500, "lvl": 5, "time": 100,
		"jobs": 5, "upkeep": 45, "svc": "fire", "radius": 20, "happy": 5},
	"police": {"name": ["Полиция", "Police"], "cat": "service", "zones": ["city", "industry"], "size": 2, "cost": 4500, "lvl": 6, "time": 110,
		"jobs": 6, "upkeep": 50, "svc": "police", "radius": 20, "happy": 7},
	"police_post": {"name": ["Пост полиции", "Police Post"], "cat": "service", "zones": ["city", "industry"], "size": 1, "cost": 1500, "lvl": 4, "time": 50,
		"jobs": 2, "upkeep": 18, "svc": "police", "radius": 10, "happy": 3},
	"watchtower": {"name": ["Дозорная башня", "Watchtower"], "cat": "service", "zones": ["city", "industry"], "size": 1, "cost": 2200, "lvl": 5, "time": 70,
		"jobs": 2, "upkeep": 20, "svc": "patrol", "radius": 10, "happy": 2},
	"gym": {"name": ["Спорткомплекс", "Sports Centre"], "cat": "service", "zones": ["city"], "size": 2, "cost": 3000, "lvl": 7, "time": 90,
		"jobs": 4, "upkeep": 25, "svc": "sport", "radius": 14, "happy": 6},
	"bank": {"name": ["Банк", "Bank"], "cat": "service", "zones": ["city"], "size": 2, "cost": 5000, "lvl": 7, "time": 120,
		"jobs": 7, "upkeep": 40, "svc": "bank", "radius": 0, "happy": 2},
	"security_office": {"name": ["Охрана «Щит»", "Shield Guards"], "cat": "service", "zones": ["city", "industry"], "size": 1, "cost": 2400, "lvl": 7, "time": 70,
		"jobs": 4, "upkeep": 25, "svc": "guard", "radius": 12, "happy": 2},
	"prison": {"name": ["Тюрьма", "Prison"], "cat": "service", "zones": ["city", "industry"], "size": 2, "cost": 6500, "gems": 1, "lvl": 9, "time": 150,
		"jobs": 8, "upkeep": 60, "svc": "prison", "radius": 0, "happy": 0},
	"library": {"name": ["Библиотека", "Library"], "cat": "service", "zones": ["city"], "size": 2, "cost": 3500, "lvl": 8, "time": 100,
		"jobs": 4, "upkeep": 30, "svc": "culture", "radius": 18, "happy": 6},
	"court": {"name": ["Суд", "Courthouse"], "cat": "service", "zones": ["city"], "size": 2, "cost": 6000, "lvl": 8, "time": 130,
		"jobs": 5, "upkeep": 45, "svc": "law", "radius": 0, "happy": 3},
	"hospital": {"name": ["Больница", "Hospital"], "cat": "service", "zones": ["city"], "size": 2, "cost": 8000, "lvl": 9, "time": 180,
		"jobs": 12, "upkeep": 90, "svc": "health", "radius": 24, "happy": 9},
	"clinic": {"name": ["Поликлиника", "Clinic"], "cat": "service", "zones": ["city"], "size": 1, "cost": 1800, "lvl": 4, "time": 55,
		"jobs": 3, "upkeep": 22, "svc": "health", "radius": 12, "happy": 4},
	"maternity": {"name": ["Роддом", "Maternity Hospital"], "cat": "service", "zones": ["city"], "size": 2, "cost": 6500, "lvl": 8, "time": 150,
		"jobs": 8, "upkeep": 60, "svc": "health", "radius": 18, "happy": 8},
	"town_hall": {"name": ["Ратуша", "Town Hall"], "cat": "service", "zones": ["city"], "size": 3, "cost": 15000, "gems": 10, "lvl": 13, "time": 240,
		"jobs": 8, "upkeep": 70, "svc": "gov", "radius": 999, "happy": 6},
	"water_station": {"name": ["Водонапорная станция", "Water Station"], "cat": "service", "zones": ["city", "industry", "farm"], "size": 2, "cost": 2200, "lvl": 4, "time": 80,
		"jobs": 3, "upkeep": 28, "svc": "water", "radius": 0, "happy": 2, "water": 160},
	"power_plant": {"name": ["Электростанция", "Power Plant"], "cat": "service", "zones": ["industry", "city"], "size": 2, "cost": 5200, "lvl": 6, "time": 120,
		"jobs": 8, "upkeep": 48, "svc": "power", "radius": 0, "happy": 0, "power": 120},
	"solar_panel": {"name": ["Солнечные панели", "Solar Panels"], "cat": "service", "zones": ["city", "industry", "farm", "leisure"], "size": 1, "cost": 650, "lvl": 2, "time": 20,
		"jobs": 1, "upkeep": 3, "svc": "solar", "radius": 0, "happy": 1, "power": 8, "store": 48},
	"sport_tower": {"name": ["Спортивная башня", "Sports Tower"], "cat": "service", "zones": ["city", "leisure"], "size": 2, "cost": 16000, "gems": 4,
		"lvl": 15, "time": 260, "jobs": 14, "upkeep": 90, "svc": "sport", "radius": 18, "happy": 7},
	"bus_stop": {"name": ["Автобусная остановка", "Bus Stop"], "cat": "service", "zones": ["city", "industry", "farm", "leisure"], "size": 1, "cost": 300, "lvl": 3, "time": 10,
		"jobs": 1, "upkeep": 4, "svc": "bus", "radius": 7, "happy": 3},
	"bus_stop_simple": {"name": ["Остановка-навес", "Simple Bus Shelter"], "cat": "service", "zones": ["city", "industry", "farm", "leisure"], "size": 1, "cost": 200, "lvl": 3, "time": 8,
		"jobs": 1, "upkeep": 3, "svc": "bus", "radius": 6, "happy": 2},
	"bus_stop_modern": {"name": ["Стеклянная остановка", "Glass Bus Stop"], "cat": "service", "zones": ["city", "industry", "leisure"], "size": 1, "cost": 600, "lvl": 6, "time": 15,
		"jobs": 1, "upkeep": 5, "svc": "bus", "radius": 8, "happy": 4},
	"bus_stop_ad": {"name": ["Остановка с рекламой", "Bus Stop with Ads"], "cat": "service", "zones": ["city", "leisure"], "size": 1, "cost": 900, "lvl": 8, "time": 18,
		"jobs": 1, "upkeep": 2, "svc": "bus", "radius": 8, "happy": 4},
	"bus_stop_village": {"name": ["Деревенская остановка", "Village Bus Stop"], "cat": "service", "zones": ["farm", "city", "leisure"], "size": 1, "cost": 250, "lvl": 3, "time": 10,
		"jobs": 1, "upkeep": 3, "svc": "bus", "radius": 7, "happy": 3},
	"tv_studio": {"name": ["Маленькая телестудия", "Small TV Studio"], "cat": "service", "zones": ["city", "leisure"], "size": 2, "cost": 4000, "lvl": 6, "time": 60,
		"jobs": 5, "upkeep": 30, "svc": "tv", "radius": 12, "happy": 4},
	"tv_center": {"name": ["Телецентр", "TV Centre"], "cat": "service", "zones": ["city", "leisure"], "size": 3, "cost": 14000, "gems": 2, "lvl": 11, "time": 150,
		"jobs": 14, "upkeep": 80, "svc": "tv", "radius": 20, "happy": 6},
	"tv_tower": {"name": ["Телебашня", "TV Tower"], "cat": "service", "zones": ["city", "leisure"], "size": 2, "cost": 30000, "gems": 5, "lvl": 15, "time": 240,
		"jobs": 8, "upkeep": 100, "svc": "tv", "radius": 32, "happy": 8},
	"newsstand": {"name": ["Газетный киоск", "Newsstand"], "cat": "service", "zones": ["city", "leisure"], "size": 1, "cost": 500, "lvl": 4, "time": 15,
		"jobs": 1, "upkeep": 3, "svc": "news", "radius": 6, "happy": 2},
	"newspaper": {"name": ["Редакция газеты", "Newspaper Office"], "cat": "service", "zones": ["city", "leisure"], "size": 2, "cost": 5000, "lvl": 7, "time": 70,
		"jobs": 6, "upkeep": 35, "svc": "news", "radius": 14, "happy": 3},
	"garbage_depot": {"name": ["Станция вывоза мусора", "Garbage Depot"], "cat": "service", "zones": ["city", "industry"], "size": 2, "cost": 2800, "lvl": 5, "time": 70,
		"jobs": 4, "upkeep": 30, "svc": "garbage", "radius": 999, "happy": 0, "garb": 12},
	"recycling_plant": {"name": ["Мусороперерабатывающий завод", "Recycling Plant"], "cat": "service", "zones": ["industry"], "size": 3, "cost": 12000, "gems": 2, "lvl": 11, "time": 140,
		"jobs": 12, "upkeep": 90, "svc": "garbage", "radius": 999, "happy": 0, "garb": 40},
	"metro_station": {"name": ["Станция метро", "Metro Station"], "cat": "service", "zones": ["city", "industry", "leisure"], "size": 1, "cost": 6000, "gems": 2, "lvl": 10, "time": 120,
		"jobs": 3, "upkeep": 40, "svc": "metro", "radius": 14, "happy": 6},
	"parking": {"name": ["Парковка", "Car Park"], "cat": "service", "zones": ["city", "industry", "leisure"], "size": 2, "cost": 900, "lvl": 4, "time": 30,
		"jobs": 1, "upkeep": 6, "svc": "parking", "radius": 6, "happy": 2},
	# multi-storey car parks: "park" = cars that fit inside (× level multiplier); residents' cars drive in and park there
	"parking_deck": {"name": ["Многоэтажная парковка", "Multi-Storey Car Park"], "cat": "service", "zones": ["city", "industry", "leisure"], "size": 2, "cost": 4500, "lvl": 7, "time": 80,
		"jobs": 3, "upkeep": 18, "svc": "parking", "radius": 8, "happy": 2, "park": 10},
	"parking_tower": {"name": ["Автоматическая башня-парковка", "Automated Parking Tower"], "cat": "service", "zones": ["city", "leisure"], "size": 1, "cost": 5200, "lvl": 10, "time": 90,
		"jobs": 2, "upkeep": 22, "svc": "parking", "radius": 6, "happy": 2, "park": 6},
	"parking_green": {"name": ["Зелёная парковка", "Green Car Park"], "cat": "service", "zones": ["city", "leisure"], "size": 2, "cost": 8500, "lvl": 9, "time": 100,
		"jobs": 4, "upkeep": 24, "svc": "parking", "radius": 9, "happy": 4, "park": 9},
	"parking_spiral": {"name": ["Круглая парковка-спираль", "Spiral Car Park"], "cat": "service", "zones": ["city", "industry", "leisure"], "size": 2, "cost": 12000, "gems": 2, "lvl": 13, "time": 140,
		"jobs": 4, "upkeep": 34, "svc": "parking", "radius": 10, "happy": 3, "park": 14},
	# ------------------------------------------------ leisure businesses (tickets)
	"museum": {"name": ["Музей", "Museum"], "cat": "fun", "zones": ["city", "leisure"], "size": 2, "cost": 8000, "lvl": 12, "time": 180,
		"jobs": 6, "income": 140, "cycle": 200, "upkeep": 50, "radius": 22, "happy": 8},
	"zoo": {"name": ["Зоопарк", "Zoo"], "cat": "fun", "zones": ["leisure"], "size": 3, "cost": 6000, "lvl": 8, "time": 150,
		"jobs": 7, "income": 120, "cycle": 180, "upkeep": 60, "radius": 28, "happy": 10},
	"funfair": {"name": ["Парк аттракционов", "Funfair"], "cat": "fun", "zones": ["leisure"], "size": 3, "cost": 12000, "gems": 4, "lvl": 12, "time": 200,
		"jobs": 10, "income": 200, "cycle": 200, "upkeep": 90, "radius": 28, "happy": 12},
	"bowling": {"name": ["Боулинг", "Bowling Alley"], "cat": "fun", "zones": ["city", "leisure"], "size": 2, "cost": 5500, "lvl": 9, "time": 120,
		"jobs": 6, "income": 150, "cycle": 180, "upkeep": 45, "radius": 16, "happy": 7},
	"mini_golf": {"name": ["Мини-гольф", "Mini Golf"], "cat": "fun", "zones": ["leisure", "city"], "size": 2, "cost": 3000, "lvl": 7, "time": 80,
		"jobs": 3, "income": 90, "cycle": 160, "upkeep": 25, "radius": 14, "happy": 6},
	"open_stage": {"name": ["Летняя сцена", "Open-Air Stage"], "cat": "fun", "zones": ["leisure", "city"], "size": 2, "cost": 4500, "lvl": 8, "time": 100,
		"jobs": 5, "income": 120, "cycle": 180, "upkeep": 40, "radius": 20, "happy": 8},
	"skate_park": {"name": ["Скейт-парк", "Skate Park"], "cat": "fun", "zones": ["city", "leisure"], "size": 2, "cost": 1800, "lvl": 5, "time": 60,
		"jobs": 1, "income": 30, "cycle": 160, "upkeep": 12, "radius": 12, "happy": 5},
	"stadium": {"name": ["Стадион", "Stadium"], "cat": "fun", "zones": ["leisure", "city"], "size": 3, "cost": 18000, "gems": 6, "lvl": 16, "time": 260,
		"jobs": 12, "income": 320, "cycle": 260, "upkeep": 120, "radius": 32, "happy": 14},
	# historic sights: tickets like a museum, and "hist" = extra tourists a day (× level) once a road reaches them
	"ancient_temple": {"name": ["Античный храм", "Ancient Temple"], "cat": "fun", "zones": ["city", "leisure"], "size": 2, "cost": 7000, "lvl": 9, "time": 160,
		"jobs": 4, "income": 120, "cycle": 200, "upkeep": 40, "radius": 20, "happy": 8, "hist": 110},
	"mausoleum": {"name": ["Мавзолей с куполом", "Domed Mausoleum"], "cat": "fun", "zones": ["city", "leisure"], "size": 2, "cost": 9000, "gems": 2, "lvl": 11, "time": 180,
		"jobs": 5, "income": 150, "cycle": 200, "upkeep": 50, "radius": 22, "happy": 9, "hist": 140},
	"pagoda": {"name": ["Пагода", "Pagoda"], "cat": "fun", "zones": ["city", "leisure"], "size": 2, "cost": 11000, "gems": 3, "lvl": 13, "time": 200,
		"jobs": 5, "income": 170, "cycle": 200, "upkeep": 55, "radius": 22, "happy": 10, "hist": 160},
	"castle": {"name": ["Замок", "Castle"], "cat": "fun", "zones": ["city", "leisure"], "size": 3, "cost": 24000, "gems": 6, "lvl": 15, "time": 300,
		"jobs": 10, "income": 260, "cycle": 240, "upkeep": 110, "radius": 30, "happy": 14, "hist": 300},
	# Khujand's own landmark: the fortress by the Kamoli Khujandi park, one per city
	"khujand_fortress": {"name": ["Крепость Худжанда", "Khujand Fortress"], "cat": "fun", "unique": true, "zones": ["city", "leisure"], "size": 4,
		"cost": 32000, "gems": 8, "lvl": 17, "time": 320, "jobs": 12, "income": 300, "cycle": 240, "upkeep": 120, "radius": 32, "happy": 16, "hist": 380},
	# ------------------------------------------------ decor (happiness in a radius)
	"tree": {"name": ["Деревья", "Trees"], "cat": "decor", "zones": ["city", "farm", "industry", "leisure"], "size": 1, "cost": 30, "lvl": 1, "time": 2,
		"happy": 2, "radius": 4, "upkeep": 0},
	# new kinds of trees, each with its own look (they also grow wild on the land)
	"tree_birch": {"name": ["Берёзы", "Birches"], "cat": "decor", "zones": ["city", "farm", "industry", "leisure"], "size": 1, "cost": 40, "lvl": 1, "time": 2,
		"happy": 2, "radius": 4, "upkeep": 0},
	"tree_pine": {"name": ["Сосны и ели", "Pines and Spruces"], "cat": "decor", "zones": ["city", "farm", "industry", "leisure"], "size": 1, "cost": 50, "lvl": 2, "time": 3,
		"happy": 2, "radius": 5, "upkeep": 0},
	"tree_poplar": {"name": ["Тополя", "Poplars"], "cat": "decor", "zones": ["city", "farm", "industry", "leisure"], "size": 1, "cost": 50, "lvl": 2, "time": 3,
		"happy": 2, "radius": 5, "upkeep": 0},
	"tree_apple": {"name": ["Яблоня", "Apple Tree"], "cat": "decor", "zones": ["city", "farm", "leisure"], "size": 1, "cost": 70, "lvl": 3, "time": 4,
		"happy": 3, "radius": 4, "upkeep": 0},
	"tree_autumn": {"name": ["Осенний клён", "Autumn Maple"], "cat": "decor", "zones": ["city", "farm", "industry", "leisure"], "size": 1, "cost": 80, "lvl": 4, "time": 4,
		"happy": 3, "radius": 5, "upkeep": 0},
	"tree_willow": {"name": ["Плакучая ива", "Weeping Willow"], "cat": "decor", "zones": ["city", "farm", "leisure"], "size": 1, "cost": 100, "lvl": 5, "time": 5,
		"happy": 3, "radius": 5, "upkeep": 1},
	"tree_sakura": {"name": ["Сакура", "Sakura"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 150, "lvl": 6, "time": 6,
		"happy": 4, "radius": 5, "upkeep": 1},
	"tree_palm": {"name": ["Пальмы", "Palms"], "cat": "decor", "zones": ["city", "leisure", "beach"], "size": 1, "cost": 180, "lvl": 7, "time": 6,
		"happy": 4, "radius": 5, "upkeep": 1},
	"tree_chinar": {"name": ["Чинара", "Chinar Tree"], "cat": "decor", "zones": ["city", "farm", "leisure"], "size": 1, "cost": 250, "lvl": 8, "time": 8,
		"happy": 5, "radius": 6, "upkeep": 1},
	"flowerbed": {"name": ["Цветник", "Flower Garden"], "cat": "decor", "zones": ["city", "farm", "industry", "leisure"], "size": 1, "cost": 80, "lvl": 1, "time": 4,
		"happy": 3, "radius": 4, "upkeep": 1},
	"bench": {"name": ["Скверик", "Small Square"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 150, "lvl": 2, "time": 5,
		"happy": 3, "radius": 5, "upkeep": 1},
	"gazebo": {"name": ["Беседка", "Gazebo"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 600, "lvl": 3, "time": 15,
		"happy": 5, "radius": 6, "upkeep": 2},
	"picnic": {"name": ["Место для пикника", "Picnic Spot"], "cat": "decor", "zones": ["city", "leisure", "farm"], "size": 1, "cost": 300, "lvl": 2, "time": 8,
		"happy": 4, "radius": 6, "upkeep": 1},
	"flag_pole": {"name": ["Флагшток", "Flagpole"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 400, "lvl": 2, "time": 8,
		"happy": 3, "radius": 6, "upkeep": 1},
	"bike_rental": {"name": ["Прокат велосипедов", "Bike Rental"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 800, "lvl": 4, "time": 15,
		"happy": 4, "radius": 8, "upkeep": 3},
	"art_sculpture": {"name": ["Арт-объект", "Art Sculpture"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 2500, "lvl": 7, "time": 40,
		"happy": 9, "radius": 8, "upkeep": 3},
	"clock_tower": {"name": ["Часовая башня", "Clock Tower"], "cat": "decor", "zones": ["city"], "size": 1, "cost": 3500, "lvl": 8, "time": 60,
		"happy": 12, "radius": 10, "upkeep": 5},
	"playground": {"name": ["Детская площадка", "Playground"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 400, "lvl": 3, "time": 10,
		"happy": 5, "radius": 5, "upkeep": 2},
	"fountain": {"name": ["Фонтан", "Fountain"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 1200, "lvl": 5, "time": 30,
		"happy": 8, "radius": 7, "upkeep": 4},
	"park": {"name": ["Парк", "Park"], "cat": "decor", "zones": ["city", "leisure"], "size": 2, "cost": 2000, "lvl": 6, "time": 45,
		"happy": 12, "radius": 8, "upkeep": 6},
	"pond": {"name": ["Пруд", "Pond"], "cat": "decor", "zones": ["city", "leisure"], "size": 2, "cost": 1800, "lvl": 7, "time": 40,
		"happy": 9, "radius": 8, "upkeep": 4},
	"plaza": {"name": ["Площадь", "Plaza"], "cat": "decor", "zones": ["city", "leisure"], "size": 2, "cost": 2500, "lvl": 8, "time": 50,
		"happy": 10, "radius": 8, "upkeep": 5},
	"statue": {"name": ["Статуя", "Statue"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 5000, "gems": 3, "lvl": 10, "time": 60,
		"happy": 20, "radius": 10, "upkeep": 8},
	# historic monuments (decor): happiness around and tourists ("hist")
	"triumph_arch": {"name": ["Триумфальная арка", "Triumphal Arch"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 3000, "gems": 1, "lvl": 8, "time": 50,
		"happy": 12, "radius": 8, "upkeep": 5, "hist": 50},
	"minaret": {"name": ["Минарет", "Minaret"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 4000, "gems": 2, "lvl": 10, "time": 60,
		"happy": 14, "radius": 9, "upkeep": 6, "hist": 70},
	# unfinished houses and building yards: pure decoration, "as if a construction is going on"
	"site_small": {"name": ["Стройка: кладка стены", "Building: laying a wall"], "cat": "decor", "zones": ["city", "farm", "leisure"], "size": 1, "cost": 120, "lvl": 2, "time": 5,
		"happy": 1, "radius": 3, "upkeep": 0},
	"site_house": {"name": ["Недостроенный дом", "Unfinished House"], "cat": "decor", "zones": ["city", "farm", "leisure"], "size": 2, "cost": 400, "lvl": 3, "time": 10,
		"happy": 1, "radius": 4, "upkeep": 0},
	"site_crane": {"name": ["Стройка с краном", "Building Site with Crane"], "cat": "decor", "zones": ["city", "industry", "leisure"], "size": 2, "cost": 900, "lvl": 4, "time": 15,
		"happy": 1, "radius": 5, "upkeep": 0},
	# beach buildings: only on the bought beach
	"beach_umbrella": {"name": ["Пляжный зонт", "Beach Umbrella"], "cat": "decor", "zones": ["beach"], "size": 1, "cost": 500, "lvl": 7, "time": 8,
		"happy": 4, "radius": 6, "upkeep": 1},
	"lifeguard_tower": {"name": ["Спасательная вышка", "Lifeguard Tower"], "cat": "decor", "zones": ["beach"], "size": 1, "cost": 1500, "lvl": 8, "time": 20,
		"happy": 7, "radius": 9, "upkeep": 3},
	"beach_bar": {"name": ["Пляжный бар", "Beach Bar"], "cat": "shop", "zones": ["beach"], "size": 2, "cost": 4500, "lvl": 8, "time": 80,
		"jobs": 8, "use": 14, "income": 190, "cycle": 120, "upkeep": 35},
	# the airport: one per city, needs a road to the highway; flights from the bought routes bring travellers (Game.flights)
	"airport": {"name": ["Аэропорт", "Airport"], "cat": "service", "unique": true, "highway": true, "zones": ["industry", "leisure", "city"], "size": 4,
		"cost": 60000, "gems": 12, "lvl": 16, "time": 420, "jobs": 60, "upkeep": 280, "svc": "airport", "radius": 999, "happy": 0},
	# residents' brands (item 24): opened only by brands (not in ORDER), see BRANDS; graphics tools/art/b_brands.py
	"ezhik_kiosk": {"name": ["Киоск «Сладкий Ёж»", "Sweet Hedgehog Kiosk"], "cat": "shop", "brand": "ezhik", "zones": ["city"], "size": 1, "cost": 600, "lvl": 5, "time": 20,
		"jobs": 2, "use": 6, "income": 42, "cycle": 100, "upkeep": 8},
	"ezhik_shop": {"name": ["Магазин «Сладкий Ёж»", "Sweet Hedgehog Shop"], "cat": "shop", "brand": "ezhik", "zones": ["city"], "size": 1, "cost": 1200, "lvl": 5, "time": 35,
		"jobs": 3, "use": 10, "income": 74, "cycle": 110, "upkeep": 14},
	"ezhik_flag": {"name": ["Флагман «Сладкий Ёж»", "Sweet Hedgehog Flagship"], "cat": "shop", "brand": "ezhik", "zones": ["city"], "size": 2, "cost": 4200, "lvl": 8, "time": 60,
		"jobs": 8, "use": 24, "income": 170, "cycle": 130, "upkeep": 30},
	"kot_kiosk": {"name": ["Киоск «Бодрый Кот»", "Perky Cat Kiosk"], "cat": "shop", "brand": "kot", "zones": ["city"], "size": 1, "cost": 600, "lvl": 5, "time": 20,
		"jobs": 2, "use": 6, "income": 42, "cycle": 100, "upkeep": 8},
	"kot_shop": {"name": ["Магазин «Бодрый Кот»", "Perky Cat Shop"], "cat": "shop", "brand": "kot", "zones": ["city"], "size": 1, "cost": 1200, "lvl": 5, "time": 35,
		"jobs": 3, "use": 10, "income": 74, "cycle": 110, "upkeep": 14},
	"kot_flag": {"name": ["Флагман «Бодрый Кот»", "Perky Cat Flagship"], "cat": "shop", "brand": "kot", "zones": ["city"], "size": 2, "cost": 4200, "lvl": 8, "time": 60,
		"jobs": 8, "use": 24, "income": 170, "cycle": 130, "upkeep": 30},
	"listik_kiosk": {"name": ["Киоск «Листик»", "Leafy Kiosk"], "cat": "shop", "brand": "listik", "zones": ["city"], "size": 1, "cost": 600, "lvl": 5, "time": 20,
		"jobs": 2, "use": 6, "income": 42, "cycle": 100, "upkeep": 8},
	"listik_shop": {"name": ["Магазин «Листик»", "Leafy Shop"], "cat": "shop", "brand": "listik", "zones": ["city"], "size": 1, "cost": 1200, "lvl": 5, "time": 35,
		"jobs": 3, "use": 10, "income": 74, "cycle": 110, "upkeep": 14},
	"listik_flag": {"name": ["Флагман «Листик»", "Leafy Flagship"], "cat": "shop", "brand": "listik", "zones": ["city"], "size": 2, "cost": 4200, "lvl": 8, "time": 60,
		"jobs": 8, "use": 24, "income": 170, "cycle": 130, "upkeep": 30},
	"zaryadik_kiosk": {"name": ["Киоск «Зарядик»", "Zaryadik Kiosk"], "cat": "shop", "brand": "zaryadik", "zones": ["city"], "size": 1, "cost": 600, "lvl": 5, "time": 20,
		"jobs": 2, "use": 6, "income": 42, "cycle": 100, "upkeep": 8},
	"zaryadik_shop": {"name": ["Магазин «Зарядик»", "Zaryadik Shop"], "cat": "shop", "brand": "zaryadik", "zones": ["city"], "size": 1, "cost": 1200, "lvl": 5, "time": 35,
		"jobs": 3, "use": 10, "income": 74, "cycle": 110, "upkeep": 14},
	"zaryadik_flag": {"name": ["Флагман «Зарядик»", "Zaryadik Flagship"], "cat": "shop", "brand": "zaryadik", "zones": ["city"], "size": 2, "cost": 4200, "lvl": 8, "time": 60,
		"jobs": 8, "use": 24, "income": 170, "cycle": 130, "upkeep": 30},
	"nitka_kiosk": {"name": ["Киоск «Нитка»", "Nitka Kiosk"], "cat": "shop", "brand": "nitka", "zones": ["city"], "size": 1, "cost": 600, "lvl": 5, "time": 20,
		"jobs": 2, "use": 6, "income": 42, "cycle": 100, "upkeep": 8},
	"nitka_shop": {"name": ["Магазин «Нитка»", "Nitka Shop"], "cat": "shop", "brand": "nitka", "zones": ["city"], "size": 1, "cost": 1200, "lvl": 5, "time": 35,
		"jobs": 3, "use": 10, "income": 74, "cycle": 110, "upkeep": 14},
	"nitka_flag": {"name": ["Флагман «Нитка»", "Nitka Flagship"], "cat": "shop", "brand": "nitka", "zones": ["city"], "size": 2, "cost": 4200, "lvl": 8, "time": 60,
		"jobs": 8, "use": 24, "income": 170, "cycle": 130, "upkeep": 30},
	"pixelburger_kiosk": {"name": ["Киоск «Пиксельбургер»", "Pixelburger Kiosk"], "cat": "shop", "brand": "pixelburger", "zones": ["city"], "size": 1, "cost": 600, "lvl": 5, "time": 20,
		"jobs": 2, "use": 6, "income": 42, "cycle": 100, "upkeep": 8},
	"pixelburger_shop": {"name": ["Магазин «Пиксельбургер»", "Pixelburger Shop"], "cat": "shop", "brand": "pixelburger", "zones": ["city"], "size": 1, "cost": 1200, "lvl": 5, "time": 35,
		"jobs": 3, "use": 10, "income": 74, "cycle": 110, "upkeep": 14},
	"pixelburger_flag": {"name": ["Флагман «Пиксельбургер»", "Pixelburger Flagship"], "cat": "shop", "brand": "pixelburger", "zones": ["city"], "size": 2, "cost": 4200, "lvl": 8, "time": 60,
		"jobs": 8, "use": 24, "income": 170, "cycle": 130, "upkeep": 30},
	# street lamps stand on the sidewalks and are placed with their own tool (see Game.place_lamp)
	"lamp": {"name": ["Фонарь", "Street Lamp"], "cat": "decor", "zones": ["city", "farm", "industry", "leisure"], "size": 0, "cost": LAMP_COST, "lvl": 2, "time": 0,
		"happy": 1, "radius": 2, "upkeep": 0},
}
const ORDER := ["house_small", "house_adobe", "house_log", "house_brick", "house_american", "house_tajik", "house_aframe", "house_container", "house_med", "cottage", "house_duplex", "house_asian", "dacha", "bungalow", "townhouse", "khrushchevka", "villa", "dorm", "apartments", "panel_block", "condo", "highrise", "round_tower", "tower", "deco_tower", "stack_tower", "sky_villa", "twin_towers", "sky_home", "dushanbe_home",
	"bakery", "cafe", "coffee_kiosk", "shawarma", "donut_shop", "burger_bar", "ice_cream", "food_trucks", "chaikhana", "drive_thru", "flowershop", "pharmacy", "bookshop", "barber", "pizzeria", "gas_station", "ev_station", "gas_highway", "car_wash", "auto_repair", "car_dealer", "boutique", "supermarket", "amid", "anis", "yovar", "market_stall", "market", "bazaar", "office", "restaurant",
	"cinema", "hotel", "mall", "sky_office", "sky_heli", "dushanbe_tower",
	"hotel_boutique", "hotel_resort", "hotel_palace", "hotel_sail", "hotel_grand",
	"farm", "apiary", "orchard", "chicken_farm", "greenhouse", "melon_field", "warehouse", "ranch", "vineyard", "windmill", "fish_farm", "dairy", "sawmill", "workshop", "textile_mill", "factory", "car_plant", "logistics",
	"solar_panel", "power_plant", "water_station",
	"kindergarten", "school", "it_run", "post_office", "fire_station", "police", "police_post", "watchtower", "gym", "sport_tower", "bank", "security_office", "prison", "library", "court", "hospital", "clinic", "maternity", "town_hall", "bus_stop", "bus_stop_simple", "bus_stop_modern", "bus_stop_ad", "bus_stop_village", "tv_studio", "tv_center", "tv_tower", "newsstand", "newspaper", "garbage_depot", "recycling_plant", "metro_station", "parking", "parking_deck", "parking_tower", "parking_green", "parking_spiral", "airport",
	"museum", "ancient_temple", "mausoleum", "pagoda", "castle", "khujand_fortress", "zoo", "funfair", "bowling", "mini_golf", "open_stage", "skate_park", "stadium",
	"tree", "tree_birch", "tree_pine", "tree_poplar", "tree_apple", "tree_autumn", "tree_willow", "tree_sakura", "tree_palm", "tree_chinar", "flowerbed", "lamp", "bench", "gazebo", "picnic", "flag_pole", "bike_rental", "playground", "fountain", "park", "pond", "plaza", "statue", "art_sculpture", "clock_tower", "triumph_arch", "minaret", "site_small", "site_house", "site_crane", "beach_umbrella", "lifeguard_tower", "beach_bar"]
## Flight routes bought in the airport. pax: travellers per flight, spend: coins each one leaves in the city,
## flag: stripes (top to bottom), cost/lvl: price of the route.
const COUNTRIES := {
	"russia": {"name": ["Россия", "Russia"], "flag": ["ffffff", "1c3fa8", "d52b1e"], "cost": 8000, "lvl": 16, "pax": 60, "spend": 14},
	"uzbekistan": {"name": ["Узбекистан", "Uzbekistan"], "flag": ["1eb2e8", "ffffff", "1eb53a"], "cost": 8000, "lvl": 16, "pax": 50, "spend": 12},
	"kazakhstan": {"name": ["Казахстан", "Kazakhstan"], "flag": ["00afca", "fec50c", "00afca"], "cost": 10000, "lvl": 16, "pax": 50, "spend": 14},
	"kyrgyzstan": {"name": ["Кыргызстан", "Kyrgyzstan"], "flag": ["e8112d", "ffef00", "e8112d"], "cost": 10000, "lvl": 17, "pax": 40, "spend": 12},
	"turkey": {"name": ["Турция", "Turkey"], "flag": ["e30a17", "ffffff", "e30a17"], "cost": 14000, "lvl": 17, "pax": 70, "spend": 16},
	"uae": {"name": ["ОАЭ", "UAE"], "flag": ["00732f", "ffffff", "000000"], "cost": 18000, "lvl": 18, "pax": 80, "spend": 24},
	"iran": {"name": ["Иран", "Iran"], "flag": ["239f40", "ffffff", "da0000"], "cost": 14000, "lvl": 18, "pax": 50, "spend": 14},
	"china": {"name": ["Китай", "China"], "flag": ["de2910", "de2910", "ffde00"], "cost": 22000, "lvl": 19, "pax": 90, "spend": 18},
	"india": {"name": ["Индия", "India"], "flag": ["ff9933", "ffffff", "138808"], "cost": 20000, "lvl": 19, "pax": 80, "spend": 14},
	"germany": {"name": ["Германия", "Germany"], "flag": ["000000", "dd0000", "ffce00"], "cost": 26000, "lvl": 20, "pax": 60, "spend": 28},
	"france": {"name": ["Франция", "France"], "flag": ["0055a4", "ffffff", "ef4135"], "cost": 26000, "lvl": 20, "pax": 60, "spend": 28},
	"uk": {"name": ["Великобритания", "United Kingdom"], "flag": ["012169", "c8102e", "012169"], "cost": 28000, "lvl": 21, "pax": 60, "spend": 30},
	"korea": {"name": ["Южная Корея", "South Korea"], "flag": ["ffffff", "cd2e3a", "0047a0"], "cost": 30000, "lvl": 22, "pax": 70, "spend": 26},
	"japan": {"name": ["Япония", "Japan"], "flag": ["ffffff", "bc002d", "ffffff"], "cost": 32000, "lvl": 22, "pax": 70, "spend": 30},
	"usa": {"name": ["США", "USA"], "flag": ["b22234", "ffffff", "3c3b6e"], "cost": 40000, "lvl": 24, "pax": 90, "spend": 34},
	"brazil": {"name": ["Бразилия", "Brazil"], "flag": ["009c3b", "ffdf00", "002776"], "cost": 36000, "lvl": 24, "pax": 60, "spend": 24},
}
const COUNTRY_ORDER := ["russia", "uzbekistan", "kazakhstan", "kyrgyzstan", "turkey", "uae", "iran", "china", "india", "germany", "france", "uk", "korea", "japan", "usa", "brazil"]
const FLIGHT_CHANCE := 0.5   ## chance per daytime hour that a route's plane lands

const CATS := ["home", "shop", "ind", "service", "fun", "decor"]
## build menu tabs: the categories plus the hotels, which have a window of their own
const TABS := ["home", "shop", "hotel", "ind", "service", "fun", "decor"]
const LANDMARK_HOMES := 42   ## homes of the quarter (as in the project) that bring the tower to full income
const LANDMARK_RADIUS := 16  ## homes this close to the tower are happier
const HOTELS := ["hotel_boutique", "hotel_resort", "hotel_palace", "hotel_sail", "hotel_grand"]
## shop types residents may open on their own (business proposals)
const PRIVATE_KINDS := ["bakery", "cafe", "flowershop", "pizzeria", "boutique", "pharmacy", "coffee_kiosk", "shawarma", "donut_shop", "burger_bar", "bookshop", "barber", "ice_cream"]
## Residents' own brands (all names invented): a founded brand opens its kiosks, shops and flagships itself.
## name, what it sells (genitive plural, for "a chain of ..."), sector (food: residents eat there, shop: they shop), colour for the UI.
const BRANDS := {
	"ezhik": {"name": ["Сладкий Ёж", "Sweet Hedgehog"], "sells": ["кондитерских", "sweet shops"], "sector": "food", "color": "e87aa8"},
	"kot": {"name": ["Бодрый Кот", "Perky Cat"], "sells": ["кофеен", "coffee houses"], "sector": "food", "color": "2a7a6a"},
	"listik": {"name": ["Листик", "Leafy"], "sells": ["продуктовых", "grocery stores"], "sector": "shop", "color": "3a9a4a"},
	"zaryadik": {"name": ["Зарядик", "Zaryadik"], "sells": ["магазинов электроники", "electronics stores"], "sector": "shop", "color": "2a5ad8"},
	"nitka": {"name": ["Нитка", "Nitka"], "sells": ["магазинов одежды", "clothing stores"], "sector": "shop", "color": "7a3a9a"},
	"pixelburger": {"name": ["Пиксельбургер", "Pixelburger"], "sells": ["бургерных", "burger bars"], "sector": "food", "color": "d83a2a"},
}
const BRAND_ORDER := ["ezhik", "kot", "listik", "zaryadik", "nitka", "pixelburger"]
const BRAND_KINDS := ["kiosk", "shop", "flag"]   ## building id = brand + "_" + kind
const BRAND_MIN_LEVEL := 6     ## city level when residents start founding brands
const BRAND_TAX := 1.3         ## brand branches pay this much more tax than other private businesses
const BRAND_FLAG_BRANCHES := 3 ## branches a brand needs before it opens a flagship
const ANIMALS := ["deer", "rabbit", "fox", "boar", "wolf", "bear"]
## lots people walk through (their props are drawn as part of the building)
const WALKABLE := ["park", "plaza", "bench", "fountain", "statue", "playground", "pond", "flowerbed", "zoo", "funfair"]

## Laws the mayor can pass and repeal from a fixed list. Effects: happy (city mood), daily (coins a day),
## rep (reputation a day), biz/tour (business tax and tourism ×), power/water (demand ×), fire/crime (risk ×).
const LAW_COST := 150   ## one-off cost to pass a law
const MAX_LAWS := 4
const LAW_ORDER := ["free_bus", "eco_fee", "fire_code", "curfew", "save_power", "save_water", "city_ads", "short_week"]
const LAWS := {
	"free_bus": {"name": ["Бесплатный автобус", "Free buses"], "happy": 4, "daily": 120},
	"eco_fee": {"name": ["Экологический сбор", "Eco fee"], "biz": 1.1, "happy": -2, "rep": 0.3},
	"fire_code": {"name": ["Пожарные нормы", "Fire code"], "fire": 0.5, "daily": 80},
	"curfew": {"name": ["Комендантский час", "Curfew"], "crime": 0.4, "happy": -4, "tour": 0.8},
	"save_power": {"name": ["Экономия электричества", "Power saving"], "power": 0.85, "happy": -2},
	"save_water": {"name": ["Экономия воды", "Water saving"], "water": 0.8, "happy": -1},
	"city_ads": {"name": ["Реклама города", "City ads"], "tour": 1.3, "rep": 0.2, "daily": 100},
	"short_week": {"name": ["Четырёхдневка", "Four-day week"], "happy": 6, "biz": 0.85},
}

## Watchtower actions: checking papers catches petty crime (a fine, +rep, cuts crime risk for a while);
## holding a gathering costs coins and lifts mood. Both run on a per-building cooldown (in-game hours).
const TOWER_CHECK_COOLDOWN := 12
const TOWER_CHECK_MIN := 60
const TOWER_CHECK_MAX := 140
const TOWER_PATROL_HOURS := 12   ## how long crime risk stays reduced after a check
const TOWER_PATROL_MULT := 0.5
const TOWER_MEETING_COST := 300
const TOWER_MEETING_COOLDOWN := 24
const TOWER_MEETING_HAPPY := 10
const TOWER_MEETING_HOURS := 24

## Crime (ROADMAP 25). Residents rob banks now and then: people run away, the police chase the robber.
## The mayor may rob a bank too: an investigation follows, and if the police find out, the mayor goes to prison.
const HEIST_MIN_POP := 150
const HEIST_CHANCE := 0.012        ## per hour, × crime multiplier (laws, watchtower check, prison)
const HEIST_LOOT := 500            ## coins taken × bank level (a caught robber gives them back)
const HEIST_CATCH := 0.55          ## chance to catch a robber with one police building
const HEIST_CATCH_EXTRA := 0.1     ## + per extra police building
const HEIST_CATCH_GUARD := 0.2     ## + if a guard agency covers the bank
const HEIST_CATCH_MAX := 0.95
const HEIST_GUARD_MULT := 0.5      ## guarded banks are robbed half as often
const PRISON_CRIME_MULT := 0.6     ## a working prison cuts crime risk
const MAYOR_ROB_LOOT := 1800       ## coins × bank level
const MAYOR_ROB_COOLDOWN := 48     ## hours between the mayor's robberies
const MAYOR_PROBE_HOURS := 6       ## the investigation takes this long
const MAYOR_SUSPECT := 0.25        ## base chance the police find out it was the mayor
const MAYOR_SUSPECT_POLICE := 0.12 ## + per working police building
const MAYOR_SUSPECT_GUARD := 0.2   ## + if guards (cameras) cover the bank
const MAYOR_SUSPECT_REPEAT := 0.1  ## + per earlier robbery by the mayor
const MAYOR_SUSPECT_MAX := 0.95
const JAIL_HOURS := 72             ## time the mayor spends in prison
const JAIL_FINE_MULT := 2          ## fine = loot × this
const JAIL_REP := 25.0
const JAIL_MOOD := -8
const JAIL_BAIL_GEMS := 5          ## get out early on bail
const JAIL_TAX_MULT := 0.5         ## daily business tax and tourism while the mayor is in prison

## Protests (ROADMAP 28). Unfair acts of the mayor build up the residents' anger (0..100). When it gets high,
## people gather in front of the town hall (or the main square) with placards and demand their rights.
const PROTEST_CAUSES := ["rob", "tax", "demolish", "mood", "rules"]
const PROTEST_MIN_POP := 80
const PROTEST_AT := 60.0           ## anger at which a protest starts
const PROTEST_MAX := 100.0
const PROTEST_DECAY := 1.0         ## anger fades by this per hour
const PROTEST_HOURS := 8           ## how long a protest goes on if nobody talks to the people
const PROTEST_COOLDOWN := 36       ## hours after a protest before the next one
const PROTEST_MOOD := -5           ## city mood while people protest
const PROTEST_REP := 3.0           ## reputation lost when a protest starts
const PROTEST_CROWD := 14          ## most protesters shown
## Anger for each kind of unfairness (cause ids are the keys of Loc "pr_cause_*").
const ANGER_ROB := 35.0            ## the mayor robbed a bank
const ANGER_JAIL := 25.0           ## the mayor was caught and jailed
const ANGER_DEMOLISH := 10.0       ## a home with residents was demolished
const ANGER_EVICT := 8.0           ## tenants evicted
const ANGER_TAX_FAIR := 15         ## tax above this angers people…
const ANGER_TAX := 0.5             ## …by this per hour per point above it
const ANGER_UNHAPPY_AT := 35.0     ## happiness below this angers people…
const ANGER_UNHAPPY := 1.5         ## …by this per hour
const ANGER_RULES := 0.3           ## per broken city rule per hour
## Answers to a protest.
const PROTEST_TALK_COST := 400     ## meet the people: coins × (1 + city level / 10)
const PROTEST_TALK_REP := 5.0
const PROTEST_TALK_MOOD := 4
const PROTEST_FORCE_REP := 8.0     ## disperse with the police
const PROTEST_FORCE_MOOD := -6
const PROTEST_FORCE_ANGER := 25.0  ## anger left after dispersing (it only grows)
const PROTEST_IGNORE_REP := 4.0    ## the protest ended on its own
const PROTEST_IGNORE_LEFT := 0.5   ## share of the anger left after an ignored protest

## Natural events with a choice (ROADMAP 32 in the user's list): flood, earthquake, blizzard, tourist rush.
## Each has 3 answers: 0 = expensive and safe, 1 = cheap and risky, 2 = do nothing. Costs are coins × (1 + level / 10).
const DZ_KINDS := ["flood", "quake", "blizzard", "tourists"]
const DZ_MIN_POP := 60
const DZ_CHANCE := 0.012           ## per hour while nothing is going on (about one event every 3–4 days)
const DZ_COOLDOWN := 120           ## hours of peace after an event
const DZ_FIRST := 96               ## no events during the first 4 days
const DZ_HOURS := 10               ## hours the mayor has to answer (the danger is visible meanwhile)
const DZ_AFTER := 8                ## hours the consequences stay visible
const DZ_FIRE_SAVE := 0.15         ## a working fire station lowers the risk of damage by this
const DZ_HEALTH_SAVE := 0.10       ## a working hospital lowers it by this and halves the bad mood
const DZ := {
	"flood": {"cost": [900, 200, 0], "risk": [0.0, 0.45, 1.0], "frac": [0.0, 0.15, 0.3], "mood": [0, -2, -5], "rep": [2, 0, -3]},
	"quake": {"cost": [1200, 250, 0], "risk": [0.1, 0.5, 1.0], "frac": [0.05, 0.15, 0.3], "mood": [0, -3, -6], "rep": [2, 0, -3]},
	"blizzard": {"cost": [700, 150, 0], "risk": [0.0, 0.4, 1.0], "frac": [0.0, 0.1, 0.2], "mood": [0, -3, -6], "rep": [2, 0, -2]},
	"tourists": {"cost": [700, 120, 0], "gain": [2200, 1100, 300], "garbage": [0, 12, 25], "mood": [2, -1, -3], "rep": [3, 1, 0]},
}

## Simple city rules, checked every in-game hour. Breaking one costs reputation.
const RULES := ["lights", "pollution", "roads", "school", "fire", "police", "health", "decor", "budget", "garbage"]

## Task missions. type: build:<id> | roads | pop | level | happy | coins_total | goods_total | plots | upgrades | lvl3 | rep | animals
const MISSIONS := [
	{"type": "roads", "n": 6, "coins": 60, "gems": 0, "xp": 10, "text": ["Постройте 6 клеток дороги", "Build 6 road tiles"]},
	{"type": "build:house_small", "n": 4, "coins": 100, "gems": 0, "xp": 20, "text": ["Постройте 4 домика", "Build 4 little houses"]},
	{"type": "build:farm", "n": 2, "coins": 100, "gems": 0, "xp": 20, "text": ["Постройте 2 фермы в зоне ферм", "Build 2 farms in the farm zone"]},
	{"type": "coins_total", "n": 600, "coins": 80, "gems": 0, "xp": 15, "text": ["Соберите 600 монет", "Collect 600 coins"]},
	{"type": "build:cafe", "n": 1, "coins": 150, "gems": 1, "xp": 30, "text": ["Откройте кафе", "Open a cafe"]},
	{"type": "lamps", "n": 4, "coins": 80, "gems": 0, "xp": 20, "text": ["Поставьте 4 фонаря", "Place 4 street lamps"]},
	{"type": "upgrades", "n": 1, "coins": 150, "gems": 0, "xp": 25, "text": ["Улучшите любое здание", "Upgrade any building"]},
	{"type": "pop", "n": 40, "coins": 200, "gems": 1, "xp": 30, "text": ["Население 40 жителей", "Reach 40 residents"]},
	{"type": "plots", "n": 6, "coins": 250, "gems": 0, "xp": 40, "text": ["Купите новый участок земли", "Buy a new plot of land"]},
	{"type": "build:school", "n": 1, "coins": 300, "gems": 1, "xp": 50, "text": ["Постройте школу", "Build a school"]},
	{"type": "happy", "n": 70, "coins": 300, "gems": 1, "xp": 50, "text": ["Счастье жителей 70%", "Reach 70% happiness"]},
	{"type": "goods_total", "n": 1500, "coins": 300, "gems": 0, "xp": 50, "text": ["Произведите 1 500 товаров", "Produce 1,500 goods"]},
	{"type": "animals", "n": 3, "coins": 250, "gems": 1, "xp": 50, "text": ["Поймайте 3 животных в лесу", "Catch 3 forest animals"]},
	{"type": "lvl3", "n": 1, "coins": 500, "gems": 1, "xp": 60, "text": ["Улучшите здание до 3 уровня", "Upgrade a building to level 3"]},
	{"type": "build:police", "n": 1, "coins": 600, "gems": 1, "xp": 80, "text": ["Постройте полицию", "Build a police station"]},
	{"type": "rep", "n": 65, "coins": 600, "gems": 1, "xp": 80, "text": ["Репутация 65", "Reach reputation 65"]},
	{"type": "pop", "n": 250, "coins": 1500, "gems": 2, "xp": 120, "text": ["Население 250 жителей", "Reach 250 residents"]},
	{"type": "build:zoo", "n": 1, "coins": 1500, "gems": 2, "xp": 150, "text": ["Откройте зоопарк", "Open the zoo"]},
	{"type": "build:factory", "n": 1, "coins": 2000, "gems": 1, "xp": 160, "text": ["Постройте фабрику в промзоне", "Build a factory in the industrial zone"]},
	{"type": "plots", "n": 14, "coins": 2500, "gems": 2, "xp": 200, "text": ["Владейте 14 участками", "Own 14 plots"]},
	{"type": "build:hospital", "n": 1, "coins": 3000, "gems": 2, "xp": 220, "text": ["Постройте больницу", "Build a hospital"]},
	{"type": "level", "n": 12, "coins": 3500, "gems": 2, "xp": 0, "text": ["Достигните 12 уровня", "Reach level 12"]},
	{"type": "build:town_hall", "n": 1, "coins": 6000, "gems": 3, "xp": 320, "text": ["Постройте ратушу", "Build the town hall"]},
	{"type": "pop", "n": 1000, "coins": 10000, "gems": 4, "xp": 500, "text": ["Население 1 000 жителей", "Reach 1,000 residents"]},
	{"type": "build:tower", "n": 1, "coins": 12000, "gems": 5, "xp": 600, "text": ["Постройте небоскрёб", "Build a skyscraper"]},
	{"type": "plots", "n": 64, "coins": 30000, "gems": 10, "xp": 1000, "text": ["Владейте всей долиной", "Own the whole valley"]},
]


static func xp_for_level(level: int) -> int:
	return int(80.0 * pow(level, 1.6))


static func tab_of(id: String) -> String:
	return B[id].get("tab", B[id].cat)


## Brand that owns this building kind ("" for ordinary buildings).
static func brand_of(id: String) -> String:
	return str(B[id].get("brand", "")) if B.has(id) else ""


static func brand_name(bid: String) -> String:
	return Loc.pick(BRANDS[bid].name) if BRANDS.has(bid) else ""


static func name_of(id: String) -> String:
	return Loc.pick(B[id].name)


static func country_name(id: String) -> String:
	return Loc.pick(COUNTRIES[id].name)


static func stat(id: String, key: String, lvl: int) -> int:
	var v: float = B[id].get(key, 0)
	match key:
		"cycle", "radius", "poll":
			return int(v)
		"jobs":
			return int(round(v * JOBS_MULT[lvl - 1]))
		"pop":
			return int(round(v * POP_MULT[lvl - 1]))
		"upkeep":
			return int(round(v * UPKEEP_MULT[lvl - 1]))
	return int(round(v * MULT[lvl - 1]))


static func upgrade_cost(id: String, lvl: int) -> Dictionary:
	## Price to go from `lvl` to `lvl + 1`.
	var d: Dictionary = B[id]
	var coins := int(d.cost * (1.6 if lvl == 1 else 3.2))
	var gems := 0 if lvl == 1 else maxi(1, int(d.cost / 3000) + int(d.get("gems", 0)) / 2)
	var time := int(d.time * (1.2 if lvl == 1 else 2.0)) + 10
	var need := int(d.lvl) + (2 if lvl == 1 else 5)
	return {"coins": coins, "gems": gems, "time": time, "level": need}


static func plot_price(owned: int) -> Dictionary:
	var k := owned - START_PLOTS.size()
	return {"coins": int(1200.0 * pow(1.45, mini(k, 18))) + k * 400, "gems": 8 + 3 * k, "level": 2 + k}


static func plot_of(c: Vector2i) -> Vector2i:
	return Vector2i(floori(float(c.x - LAND0) / PLOT), floori(float(c.y - LAND0) / PLOT))


static func in_land(c: Vector2i) -> bool:
	return c.x >= LAND0 and c.y >= LAND0 and c.x < LAND1 and c.y < LAND1


## The beach beyond the land border: tiles x 70..79, split into one segment per plot row (-1 if not a beach tile)
static func beach_seg(c: Vector2i) -> int:
	if c.x < BEACH_X0 or c.x >= LAND0 or c.y < LAND0 or c.y >= LAND1:
		return -1
	return (c.y - LAND0) / PLOT


## Tiles of the beach and the sea in front of it (kept free of trees)
static func beach_area(c: Vector2i) -> bool:
	return c.x >= LAND0 - 28 and c.x < LAND0 and c.y >= LAND0 - 6 and c.y < LAND1 + 6


static func beach_price(owned: int) -> Dictionary:
	return {"coins": 9000 + owned * 3500, "gems": 25 + owned * 6, "level": 7 + owned}


static func zone_of_plot(p: Vector2i) -> String:
	if p.x <= 1:
		return "leisure"
	if p.x >= 5 and p.y <= 4:
		return "farm"
	if p.y >= 5 and p.x >= 4:
		return "industry"
	return "city"


static func zone_at(c: Vector2i) -> String:
	if beach_seg(c) >= 0:
		return "beach"
	return zone_of_plot(plot_of(c)) if in_land(c) else ""


static func zone_name(z: String) -> String:
	return Loc.t("zone_" + z)


static func allowed_in(id: String, zone: String) -> bool:
	return zone in B[id].zones


## "land" | "forest" | "country" | "beyond" (past the horizon) | "outside" (off the map)
static func region(c: Vector2i) -> String:
	if c.x < 0 or c.y < 0 or c.x >= MAP or c.y >= MAP:
		return "outside"
	if c.x + c.y < HORIZON:
		return "beyond"
	if beach_seg(c) >= 0:
		return "beach"
	if in_land(c):
		return "land"
	var dx: int = maxi(LAND0 - c.x, c.x - (LAND1 - 1))
	var dy: int = maxi(LAND0 - c.y, c.y - (LAND1 - 1))
	return "forest" if maxi(dx, dy) <= FOREST else "country"


## The roads outside the land, owned by the region: the highway to other cities and
## country roads to the villages. tile -> road type
static func regional_roads() -> Dictionary:
	var out := {}
	for x in MAP:
		out[Vector2i(x, HIGHWAY_Y)] = "highway"
	for y in range(LAND1, HIGHWAY_Y):
		out[Vector2i(CENTER, y)] = "country"
	for x in LAND0:
		out[Vector2i(x, CENTER)] = "country"
	for y in LAND0:
		out[Vector2i(CENTER, y)] = "country"
	for x in range(LAND1, MAP):
		out[Vector2i(x, CENTER)] = "country"
	return out


## Land tiles at the end of each regional road: a player road here joins the region.
static func gates() -> Array[Vector2i]:
	return [Vector2i(CENTER, LAND0), Vector2i(CENTER, LAND1 - 1), Vector2i(LAND0, CENTER), Vector2i(LAND1 - 1, CENTER)]


## Where cars from other cities appear and leave: the far ends of the regional roads.
static func far_ends() -> Array[Vector2i]:
	return [Vector2i(0, HIGHWAY_Y), Vector2i(MAP - 1, HIGHWAY_Y), Vector2i(0, CENTER), Vector2i(CENTER, 0), Vector2i(MAP - 1, CENTER)]
