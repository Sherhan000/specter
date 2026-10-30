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
const HIGHWAY_Y := LAND1 + 6         ## the highway runs along x on this row
const START_PLOTS := [Vector2i(3, 3), Vector2i(4, 3), Vector2i(3, 4), Vector2i(4, 4), Vector2i(5, 3)]
const ZONES := ["city", "farm", "industry", "leisure"]
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

const ROADS := {
	"dirt": {"name": ["Грунтовка", "Dirt road"], "cost": 6, "upkeep": 0.2, "row": 2, "speed": 0.75},
	"asphalt": {"name": ["Асфальт", "Asphalt"], "cost": 18, "upkeep": 0.5, "row": 3, "speed": 1.0},
	"stone": {"name": ["Брусчатка", "Cobblestone"], "cost": 30, "upkeep": 0.8, "row": 4, "speed": 0.9},
	"boulevard": {"name": ["Бульвар", "Boulevard"], "cost": 45, "upkeep": 1.2, "row": 7, "speed": 1.1},
	"avenue": {"name": ["Проспект", "Avenue"], "cost": 60, "upkeep": 1.5, "row": 8, "speed": 1.3},
	"brick": {"name": ["Кирпичная улица", "Brick street"], "cost": 35, "upkeep": 0.9, "row": 9, "speed": 0.85},
	"bus_lane": {"name": ["Улица с автобусной полосой", "Bus lane street"], "cost": 40, "upkeep": 0.8, "row": 10, "speed": 1.05},
	"highway": {"name": ["Трасса", "Highway"], "cost": 0, "upkeep": 0.0, "row": 5, "speed": 1.6},
	"country": {"name": ["Загородная дорога", "Country road"], "cost": 0, "upkeep": 0.0, "row": 6, "speed": 1.25},
}
const ROAD_ORDER := ["dirt", "asphalt", "stone", "boulevard", "avenue", "brick", "bus_lane"]

## Category: home | shop | ind | service | fun (leisure businesses) | decor.
## zones: where it may be built. upkeep: coins per in-game day (salaries for services).
## pop is the number of residents (a little house is one family), jobs the workers needed.
const B := {
	# ------------------------------------------------ homes (pop, rent per cycle)
	"house_small": {"name": ["Домик", "Little House"], "cat": "home", "zones": ["city"], "size": 1, "cost": 120, "lvl": 1, "time": 10,
		"pop": 4, "rent": 10, "cycle": 90, "upkeep": 6},
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
	"flowershop": {"name": ["Цветочный", "Flower Shop"], "cat": "shop", "zones": ["city"], "size": 1, "cost": 1100, "lvl": 4, "time": 40,
		"jobs": 3, "use": 10, "income": 62, "cycle": 110, "upkeep": 15},
	"pharmacy": {"name": ["Аптека", "Pharmacy"], "cat": "shop", "zones": ["city"], "size": 1, "cost": 1400, "lvl": 5, "time": 45,
		"jobs": 3, "use": 9, "income": 72, "cycle": 110, "upkeep": 16},
	"pizzeria": {"name": ["Пиццерия", "Pizzeria"], "cat": "shop", "zones": ["city", "leisure"], "size": 1, "cost": 1800, "lvl": 6, "time": 50,
		"jobs": 4, "use": 12, "income": 85, "cycle": 120, "upkeep": 20},
	"gas_station": {"name": ["Заправка", "Gas Station"], "cat": "shop", "zones": ["city", "industry", "farm"], "size": 1, "cost": 2200, "lvl": 7, "time": 55,
		"jobs": 3, "use": 10, "income": 95, "cycle": 110, "upkeep": 20},
	"boutique": {"name": ["Бутик", "Boutique"], "cat": "shop", "zones": ["city"], "size": 1, "cost": 2600, "lvl": 8, "time": 60,
		"jobs": 4, "use": 14, "income": 110, "cycle": 130, "upkeep": 26},
	"supermarket": {"name": ["Супермаркет", "Supermarket"], "cat": "shop", "zones": ["city"], "size": 2, "cost": 4200, "lvl": 10, "time": 120,
		"jobs": 12, "use": 30, "income": 170, "cycle": 160, "upkeep": 50},
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
	"sawmill": {"name": ["Лесопилка", "Sawmill"], "cat": "ind", "zones": ["industry"], "size": 2, "cost": 1800, "lvl": 5, "time": 60,
		"jobs": 8, "out": 50, "cycle": 100, "upkeep": 20, "poll": 6},
	"workshop": {"name": ["Мастерская", "Workshop"], "cat": "ind", "zones": ["industry"], "size": 2, "cost": 3000, "lvl": 7, "time": 90,
		"jobs": 10, "out": 75, "cycle": 120, "upkeep": 30, "poll": 6},
	"factory": {"name": ["Фабрика", "Factory"], "cat": "ind", "zones": ["industry"], "size": 2, "cost": 7000, "lvl": 10, "time": 150,
		"jobs": 20, "out": 160, "cycle": 180, "upkeep": 70, "poll": 10},
	"logistics": {"name": ["Логистический центр", "Logistics Hub"], "cat": "ind", "zones": ["industry"], "size": 3, "cost": 15000, "gems": 5, "lvl": 16, "time": 240,
		"jobs": 25, "out": 280, "cycle": 220, "upkeep": 110, "poll": 6},
	# ------------------------------------------------ services (jobs, coverage radius, happiness, salaries)
	"kindergarten": {"name": ["Детский сад", "Kindergarten"], "cat": "service", "zones": ["city"], "size": 1, "cost": 1200, "lvl": 3, "time": 50,
		"jobs": 3, "upkeep": 15, "svc": "edu", "radius": 9, "happy": 5},
	"school": {"name": ["Школа", "School"], "cat": "service", "zones": ["city"], "size": 2, "cost": 2500, "lvl": 4, "time": 90,
		"jobs": 6, "upkeep": 40, "svc": "edu", "radius": 16, "happy": 8},
	"post_office": {"name": ["Почта", "Post Office"], "cat": "service", "zones": ["city"], "size": 1, "cost": 1800, "lvl": 5, "time": 60,
		"jobs": 3, "upkeep": 18, "svc": "post", "radius": 18, "happy": 3},
	"fire_station": {"name": ["Пожарная часть", "Fire Station"], "cat": "service", "zones": ["city", "industry"], "size": 2, "cost": 3500, "lvl": 5, "time": 100,
		"jobs": 5, "upkeep": 45, "svc": "fire", "radius": 20, "happy": 5},
	"police": {"name": ["Полиция", "Police"], "cat": "service", "zones": ["city", "industry"], "size": 2, "cost": 4500, "lvl": 6, "time": 110,
		"jobs": 6, "upkeep": 50, "svc": "police", "radius": 20, "happy": 7},
	"watchtower": {"name": ["Дозорная башня", "Watchtower"], "cat": "service", "zones": ["city", "industry"], "size": 1, "cost": 2200, "lvl": 5, "time": 70,
		"jobs": 2, "upkeep": 20, "svc": "patrol", "radius": 10, "happy": 2},
	"gym": {"name": ["Спорткомплекс", "Sports Centre"], "cat": "service", "zones": ["city"], "size": 2, "cost": 3000, "lvl": 7, "time": 90,
		"jobs": 4, "upkeep": 25, "svc": "sport", "radius": 14, "happy": 6},
	"bank": {"name": ["Банк", "Bank"], "cat": "service", "zones": ["city"], "size": 2, "cost": 5000, "lvl": 7, "time": 120,
		"jobs": 7, "upkeep": 40, "svc": "bank", "radius": 0, "happy": 2},
	"library": {"name": ["Библиотека", "Library"], "cat": "service", "zones": ["city"], "size": 2, "cost": 3500, "lvl": 8, "time": 100,
		"jobs": 4, "upkeep": 30, "svc": "culture", "radius": 18, "happy": 6},
	"court": {"name": ["Суд", "Courthouse"], "cat": "service", "zones": ["city"], "size": 2, "cost": 6000, "lvl": 8, "time": 130,
		"jobs": 5, "upkeep": 45, "svc": "law", "radius": 0, "happy": 3},
	"hospital": {"name": ["Больница", "Hospital"], "cat": "service", "zones": ["city"], "size": 2, "cost": 8000, "lvl": 9, "time": 180,
		"jobs": 12, "upkeep": 90, "svc": "health", "radius": 24, "happy": 9},
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
	"bus_stop": {"name": ["Автобусная остановка", "Bus Stop"], "cat": "service", "zones": ["city", "industry", "farm", "leisure"], "size": 1, "cost": 300, "lvl": 3, "time": 10,
		"jobs": 1, "upkeep": 4, "svc": "bus", "radius": 7, "happy": 3},
	"metro_station": {"name": ["Станция метро", "Metro Station"], "cat": "service", "zones": ["city", "industry", "leisure"], "size": 1, "cost": 6000, "gems": 2, "lvl": 10, "time": 120,
		"jobs": 3, "upkeep": 40, "svc": "metro", "radius": 14, "happy": 6},
	"parking": {"name": ["Парковка", "Car Park"], "cat": "service", "zones": ["city", "industry", "leisure"], "size": 2, "cost": 900, "lvl": 4, "time": 30,
		"jobs": 1, "upkeep": 6, "svc": "parking", "radius": 6, "happy": 2},
	# ------------------------------------------------ leisure businesses (tickets)
	"museum": {"name": ["Музей", "Museum"], "cat": "fun", "zones": ["city", "leisure"], "size": 2, "cost": 8000, "lvl": 12, "time": 180,
		"jobs": 6, "income": 140, "cycle": 200, "upkeep": 50, "radius": 22, "happy": 8},
	"zoo": {"name": ["Зоопарк", "Zoo"], "cat": "fun", "zones": ["leisure"], "size": 3, "cost": 6000, "lvl": 8, "time": 150,
		"jobs": 7, "income": 120, "cycle": 180, "upkeep": 60, "radius": 28, "happy": 10},
	"funfair": {"name": ["Парк аттракционов", "Funfair"], "cat": "fun", "zones": ["leisure"], "size": 3, "cost": 12000, "gems": 4, "lvl": 12, "time": 200,
		"jobs": 10, "income": 200, "cycle": 200, "upkeep": 90, "radius": 28, "happy": 12},
	"stadium": {"name": ["Стадион", "Stadium"], "cat": "fun", "zones": ["leisure", "city"], "size": 3, "cost": 18000, "gems": 6, "lvl": 16, "time": 260,
		"jobs": 12, "income": 320, "cycle": 260, "upkeep": 120, "radius": 32, "happy": 14},
	# ------------------------------------------------ decor (happiness in a radius)
	"tree": {"name": ["Деревья", "Trees"], "cat": "decor", "zones": ["city", "farm", "industry", "leisure"], "size": 1, "cost": 30, "lvl": 1, "time": 2,
		"happy": 2, "radius": 4, "upkeep": 0},
	"flowerbed": {"name": ["Цветник", "Flower Garden"], "cat": "decor", "zones": ["city", "farm", "industry", "leisure"], "size": 1, "cost": 80, "lvl": 1, "time": 4,
		"happy": 3, "radius": 4, "upkeep": 1},
	"bench": {"name": ["Скверик", "Small Square"], "cat": "decor", "zones": ["city", "leisure"], "size": 1, "cost": 150, "lvl": 2, "time": 5,
		"happy": 3, "radius": 5, "upkeep": 1},
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
	# street lamps stand on the sidewalks and are placed with their own tool (see Game.place_lamp)
	"lamp": {"name": ["Фонарь", "Street Lamp"], "cat": "decor", "zones": ["city", "farm", "industry", "leisure"], "size": 0, "cost": LAMP_COST, "lvl": 2, "time": 0,
		"happy": 1, "radius": 2, "upkeep": 0},
}
const ORDER := ["house_small", "cottage", "bungalow", "townhouse", "khrushchevka", "villa", "dorm", "apartments", "panel_block", "condo", "highrise", "round_tower", "tower", "deco_tower", "stack_tower", "twin_towers", "sky_home", "dushanbe_home",
	"bakery", "cafe", "flowershop", "pharmacy", "pizzeria", "gas_station", "boutique", "supermarket", "office", "restaurant",
	"cinema", "hotel", "mall", "sky_office", "sky_heli", "dushanbe_tower",
	"hotel_boutique", "hotel_resort", "hotel_palace", "hotel_sail", "hotel_grand",
	"farm", "orchard", "greenhouse", "warehouse", "ranch", "sawmill", "workshop", "factory", "logistics",
	"solar_panel", "power_plant", "water_station",
	"kindergarten", "school", "post_office", "fire_station", "police", "watchtower", "gym", "bank", "library", "court", "hospital", "maternity", "town_hall", "bus_stop", "metro_station", "parking",
	"museum", "zoo", "funfair", "stadium",
	"tree", "flowerbed", "lamp", "bench", "playground", "fountain", "park", "pond", "plaza", "statue"]
const CATS := ["home", "shop", "ind", "service", "fun", "decor"]
## build menu tabs: the categories plus the hotels, which have a window of their own
const TABS := ["home", "shop", "hotel", "ind", "service", "fun", "decor"]
const LANDMARK_HOMES := 42   ## homes of the quarter (as in the project) that bring the tower to full income
const LANDMARK_RADIUS := 16  ## homes this close to the tower are happier
const HOTELS := ["hotel_boutique", "hotel_resort", "hotel_palace", "hotel_sail", "hotel_grand"]
## shop types residents may open on their own (business proposals)
const PRIVATE_KINDS := ["bakery", "cafe", "flowershop", "pizzeria", "boutique", "pharmacy"]
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

## Simple city rules, checked every in-game hour. Breaking one costs reputation.
const RULES := ["lights", "pollution", "roads", "school", "fire", "police", "health", "decor", "budget"]

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


static func name_of(id: String) -> String:
	return Loc.pick(B[id].name)


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


static func zone_of_plot(p: Vector2i) -> String:
	if p.x <= 1:
		return "leisure"
	if p.x >= 5 and p.y <= 4:
		return "farm"
	if p.y >= 5 and p.x >= 4:
		return "industry"
	return "city"


static func zone_at(c: Vector2i) -> String:
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
