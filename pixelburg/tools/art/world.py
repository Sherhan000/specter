"""World layout shared with scripts/data.gd, and the generated terrain map."""
import os

import ground

PLOT, PLOTS, MARGIN, FOREST = 10, 8, 80, 8
LAND0 = MARGIN
LAND1 = LAND0 + PLOT * PLOTS
MAP = LAND1 + MARGIN
CENTER = LAND0 + PLOT * PLOTS // 2
HORIZON = 2 * LAND0 - 18
HIGHWAY_Y = LAND1 + 6
LAKES = [(56, 196, 7.0), (200, 70, 6.0), (190, 186, 5.0)]


def regional_roads():
    out = {}
    for x in range(MAP):
        out[(x, HIGHWAY_Y)] = "highway"
    for y in range(LAND1, HIGHWAY_Y):
        out[(CENTER, y)] = "country"
    for x in range(LAND0):
        out[(x, CENTER)] = "country"
    for y in range(LAND0):
        out[(CENTER, y)] = "country"
    for x in range(LAND1, MAP):
        out[(x, CENTER)] = "country"
    return out


def gen_world(out):
    os.makedirs(out, exist_ok=True)
    W = dict(MAP=MAP, LAND0=LAND0, LAND1=LAND1, FOREST=FOREST, HORIZON=HORIZON, LAKES=LAKES, CLEAR=list(regional_roads().keys()))
    return ground.gen_terrain(out, W)


if __name__ == "__main__":
    import sys
    gen_world(sys.argv[1])
