class_name Holidays
extends RefCounted
## Seasonal holidays (ROADMAP 31). The year has 4 seasons of Data.SEASON_DAYS days; a holiday lasts a few days of its season.
## Decorations are drawn by HolidayView, the mood bonus and the special tasks live in Game (hol_*).

const MOOD := 6              ## happiness bonus on every holiday day
const TREAT_COST := 120      ## coins per level for treating the residents
const BUILD_GOAL := 2
## id -> season, first and last day of the season (0-based), name, what happens, decorations [sprite, count]
const LIST := {
	"newyear": {"season": "winter", "from": 2, "to": 3, "name": ["Новый год", "New Year"],
		"text": ["На площади ёлка, дома в гирляндах, во дворах снеговики. Жители радуются празднику!", "A fir tree stands on the square, homes wear garlands and snowmen guard the yards. Everyone is celebrating!"],
		"deco": [["fir_tree", 1], ["snowman", 4], ["garland", 8]]},
	"navruz": {"season": "spring", "from": 0, "to": 1, "name": ["Навруз", "Navruz"],
		"text": ["Во дворе варят сумалак, дети качаются на качелях, повсюду цветы — праздник весны!", "Sumalak simmers in a cauldron, children ride the swings and flowers are everywhere - the spring festival!"],
		"deco": [["sumalak", 1], ["swing", 2], ["flowers", 6]]},
	"halloween": {"season": "autumn", "from": 2, "to": 3, "name": ["Хэллоуин", "Halloween"],
		"text": ["Тыквы с огоньком, оранжевые фонари и добрые привидения на улицах.", "Glowing pumpkins, orange lanterns and friendly ghosts in the streets."],
		"deco": [["pumpkin", 6], ["lantern", 4], ["ghost", 3]]},
	"cityday": {"season": "summer", "from": 1, "to": 2, "name": ["День города", "City Day"],
		"text": ["Флажки на домах, флаги на площади, а вечером в небе — фейерверки!", "Bunting on the houses, flags on the square and fireworks in the evening sky!"],
		"deco": [["flag", 4], ["bunting", 8]]},
}
const ORDER := ["newyear", "navruz", "halloween", "cityday"]


## Holiday going on in the given game day, or "".
static func at(day: int) -> String:
	var season: String = Game.SEASONS[int((day - 1) / Data.SEASON_DAYS) % 4]
	var d := (day - 1) % Data.SEASON_DAYS
	for id in ORDER:
		var h: Dictionary = LIST[id]
		if h.season == season and d >= int(h.from) and d <= int(h.to):
			return id
	return ""


## Unique key of this year's holiday (rewards are taken once per year).
static func key(day: int) -> String:
	var id := at(day)
	return "" if id == "" else "%s:%d" % [id, (day - 1) / (Data.SEASON_DAYS * 4)]


static func days_left(day: int) -> int:
	var id := at(day)
	if id == "":
		return 0
	return int(LIST[id].to) - (day - 1) % Data.SEASON_DAYS + 1


static func reward() -> Dictionary:
	return {"coins": int(700 * (1.0 + Game.level * 0.12)), "gems": 3}
