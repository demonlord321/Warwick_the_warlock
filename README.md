# RPG Maps — Milestone 1 demo

Four connected maps for a top-down, tile-based RPG (turn-based combat comes later),
plus a small Pygame demo: window, game loop, map loading, tile-by-tile movement,
collision, a camera that follows the player and stops at map edges, and doors.
All graphics are coloured shapes — no art files needed.

Settings: 32px tiles, 800x600 window (see `settings.py`).

## Run it

```bash
pip install pygame            # add --break-system-packages on some Linux systems
python game.py                # play: arrows/WASD to move, Esc to quit
python view_map.py dungeon    # look at one map (arrow keys scroll)
python validate_maps.py       # check all maps for mistakes
python smoke_test.py          # headless play-through of every door
python make_screenshots.py    # regenerate screenshots/*.png
```

In the demo: walk into an NPC to see its dialogue key, walk into a chest to open it,
step on a save point / boss tile for a placeholder message, and grass (`g`) may
trigger a placeholder "Encounter!" message. Messages are also printed to the terminal.

## The maps

1. **Willowbrook Village** (`town`) — starting town: houses, a pond, 4 NPCs, a save point, and grass outskirts with encounters. Your house is on the left; the cave mouth is at the top.
2. **Your House** (`house`) — interior with Mom, a bedroom with a save point by the bed, and a chest.
3. **Mossy Caverns** (`dungeon`) — 3 rooms: entrance hall → flooded cavern (cross the river at the single bridge in the top) → switchback vault (zig-zag around two walls) with a chest, a save point and the door to the boss.
4. **Warden's Chamber** (`boss_room`) — pillared hall between two water channels; the boss waits in the throne alcove.

Route: town ↔ house, town ↔ dungeon ↔ boss_room. Every door works both ways.

## Files

| File | What it does |
|------|--------------|
| `maps/` | the map data (`.txt` grids + `.json` metadata) and `maps/README.md` with the legend/format |
| `settings.py` | tile size, window size, start map |
| `tiles.py` | the legend: colour and solid/walkable for each character |
| `map_loader.py` | `GameMap`: reads a `.txt` + `.json` pair |
| `camera.py` | follows the player, clamps at edges, centres small maps |
| `render.py` | draws tiles and the player |
| `player.py` | grid position + collision check |
| `game.py` | the demo game loop (doors, NPCs, chests, encounters) |
| `view_map.py` | standalone viewer (only needs pygame + maps/) |
| `validate_maps.py` | standalone checker (plain Python) |
| `smoke_test.py`, `make_screenshots.py` | headless test + screenshot generator |

## Legend

`#` wall · `.` floor · `P` player start · `N` NPC · `D` door · `g` grass (encounters) ·
`T` tree · `~` water · `S` save point · `C` chest · `B` boss trigger.
Solid (can't walk onto): `# N T ~ C`. Full details in `maps/README.md`.

## Adding a new map

1. Create `maps/cellar.txt` — a rectangle of legend characters (keep every row the same width,
   surround it with `#` or `T`). Put a `D` where the exit goes.
2. Create `maps/cellar.json`:
   ```json
   {
     "display_name": "Old Cellar",
     "doors": [{"x": 5, "y": 9, "target_map": "house", "spawn_x": 3, "spawn_y": 12}],
     "npcs": [],
     "encounters": {"rate": 0.1, "enemy_pool": ["rat"]},
     "boss": null
   }
   ```
   The spawn is where you appear in the *other* map — next to its door, not on it.
3. Add the return trip: put a `D` in the other map (replace a wall/floor tile) and add a matching
   door entry there with `target_map: "cellar"` and a spawn next to the cellar's `D`.
4. Run `python validate_maps.py` — it tells you exactly what's missing or mismatched.
5. Run `python view_map.py cellar` to look at it, then `python game.py` to walk there.
