# Pixelburg / Пиксельбург

Isometric city builder for Android, made with **Godot 4.7.2** (GL Compatibility renderer). Version 1.3.0.

- Real scale: one cell is 16 m, streets have lanes, parking, sidewalks, crosswalks and stop lines
- 55 building types in 6 categories, each with 3 upgrade levels and 4 sides (buildings can be turned)
- Residents with homes, jobs, cars and daily plans; pedestrians wait at crosswalks, cars follow each other,
  reserve intersections, obey traffic lights and park on the street
- A valley with zones (city, farms, industry, leisure), regional roads to neighbouring towns, forests,
  villages and a horizon with mountain ranges and distant town lights
- Day and night, weather and seasons; story characters, letters, rules, bank and elections

Layout:
- `scripts/` — game code: `game.gd` (economy, rules, save), `city.gd` (camera, input, modes, world layers),
  `life.gd` (residents, walkers, cars, traffic), `ground.gd` + `shaders/ground.gdshader` (terrain and roads),
  `scenery.gd` (forests, villages), `backdrop.gd` (horizon), `hud.gd` / `panels.gd` / `dialog_box.gd` /
  `tutorial.gd` (interface), `data.gd` (balance and world layout)
- `tools/gen_assets.py` + `tools/art/` — generates the art: `python3 tools/gen_assets.py [ground] [buildings]
  [nature] [units] [ui] [sky] [only=id,id]` (needs Pillow, numpy, scipy and pycairo), then
  `python3 tools/fix_imports.py` and a Godot import
- `tools/dev/` — dev-only test and screenshot scenes (excluded from export): `logic_test`, `life_test`,
  `view_test`, `ui_test`, `showcase`
- `export_presets.cfg` — Android preset (AAB, target SDK 36, arm64 + armv7). The keystore is supplied via the
  `GODOT_ANDROID_KEYSTORE_RELEASE_PATH/USER/PASSWORD` environment variables or the editor's export dialog.

Interface icons can be replaced by hand-made ones: put `assets/ui/icons/<name>.png` (for example `coin.png`,
`shop.png`) and the game uses it instead of the generated icon.

Fonts: Inter (SIL Open Font License 1.1, see `assets/fonts/OFL_Inter.txt`).
