class_name Iso
extends RefCounted
## Isometric helpers. A tile is 16 x 16 m and 320 x 160 px; vertex (i, j) of the grid sits at
## ((i - j) * 160, (i + j) * 80) in world space. 10 px of height = 1 m.

const TW := 320
const TH := 160
const HX := 160.0
const HY := 80.0
const DIRS := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]


static func vertex(i: float, j: float) -> Vector2:
	return Vector2((i - j) * HX, (i + j) * HY)


## World position of a point given in grid units.
static func grid(g: Vector2) -> Vector2:
	return Vector2((g.x - g.y) * HX, (g.x + g.y) * HY)


static func center(c: Vector2i) -> Vector2:
	return vertex(c.x + 0.5, c.y + 0.5)


static func to_grid(p: Vector2) -> Vector2:
	return Vector2((p.x / HX + p.y / HY) / 2.0, (p.y / HY - p.x / HX) / 2.0)


static func to_tile(p: Vector2) -> Vector2i:
	var g := to_grid(p)
	return Vector2i(floori(g.x), floori(g.y))


## Depth key of an n x n footprint whose top-left tile is (x, y): the screen y of its centre.
## Everything standing on the ground (people, cars, trees) uses the screen y of its own
## position, so whatever is in front of a building's footprint is drawn over it.
static func sort_y(x: int, y: int, n: int) -> float:
	return (x + y + n) * HY


## Grid-space offset (in tiles) converted to a world-space vector.
static func grid_vec(g: Vector2) -> Vector2:
	return Vector2((g.x - g.y) * HX, (g.x + g.y) * HY)


## Right-hand side of a grid direction (traffic drives on the right).
static func right_of(d: Vector2) -> Vector2:
	return Vector2(-d.y, d.x)


static func dir_name(d: Vector2) -> String:
	if absf(d.x) >= absf(d.y):
		return "px" if d.x > 0 else "nx"
	return "py" if d.y > 0 else "ny"


## Index 0..15 of the nearest of 16 headings; 0 = +x, counting towards +y.
static func dir16(d: Vector2) -> int:
	return posmod(roundi(atan2(d.y, d.x) / (TAU / 16.0)), 16)
