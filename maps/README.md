# maps/ — map format

Each map is two files with the same name:

* `<name>.txt` — the tile grid, one character per tile, every row the same width.
* `<name>.json` — metadata (doors, NPCs, encounters, boss).

Coordinates: `x` = 0-indexed column, `y` = 0-indexed row (top-left is 0,0).

## Tile legend

| Char | Tile          | Walkable? | Notes |
|------|---------------|-----------|-------|
| `#`  | wall          | no  | also used for furniture/pillars |
| `.`  | floor         | yes | |
| `P`  | player start  | yes | exactly one, only in `town.txt` |
| `N`  | NPC           | no  | needs an entry in `npcs`; talk by walking into it |
| `D`  | door / exit   | yes | needs an entry in `doors`; stepping on it changes map |
| `g`  | grass         | yes | random-encounter tile (uses `encounters`) — in the dungeon read it as "moss" |
| `T`  | tree          | no  | |
| `~`  | water         | no  | |
| `S`  | save point    | yes | |
| `C`  | chest         | no  | open by walking into it |
| `B`  | boss trigger  | yes | needs `boss` in JSON; stepping on it starts the boss fight |

No other characters are used.

## JSON fields

```json
{
  "display_name": "Willowbrook Village",
  "doors": [{"x": 9, "y": 11, "target_map": "house", "spawn_x": 10, "spawn_y": 13}],
  "npcs": [{"x": 24, "y": 16, "id": "elder", "dialogue_key": "elder_intro"}],
  "encounters": {"rate": 0.08, "enemy_pool": ["slime", "field_rat"]},
  "boss": null
}
```

* `display_name` is **optional** (extra, not in the original spec): the name shown on screen. Defaults to the file name.
* `doors`: every `D` in the grid has exactly one entry and vice versa. `spawn_x/spawn_y` is where you
  appear in `target_map` — the walkable tile just **inside** that map's return door (never on it).
* Doors must line up spatially. A door's direction is the way you walk through it (a `D` with floor
  below it is walked through going north). If you leave one map going north, you arrive in the next
  map at a door you'd walk through going south to come back (north ↔ south, east ↔ west).
  Each `D` sits in a wall with exactly one open neighbour.
* `encounters.rate` is the chance (0–1) per step on `g`. Use `{"rate": 0.0, "enemy_pool": []}` for safe maps.
* `boss`: `{"x", "y", "enemy_id"}` matching the single `B` tile, or `null`.

## Current maps

| File | Name | Size | Connections |
|------|------|------|-------------|
| `town` | Willowbrook Village | 40x30 | house door (9,11), go north ↔ house; cave mouth (19,1), go north ↔ dungeon |
| `house` | Your House | 20x15 | front door (10,14) on south wall, go south ↔ town |
| `dungeon` | Mossy Caverns (3 rooms) | 40x30 | exit (7,29) on south wall ↔ town; sealed door (38,21) on east wall ↔ boss_room |
| `boss_room` | Warden's Chamber | 30x17 | door (0,8) on west wall ↔ dungeon; throne/boss on the east side |
