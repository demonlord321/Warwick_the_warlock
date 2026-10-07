# Warwick the Warlock — maps and engine demo

Chapter 1 ("The Master") is set in the slums: `maps/chapter1/slums1` (back alleys) and
`maps/chapter1/slums2` (the main road). The original four prototype maps live in `maps/parked/`.
Each sub-folder of `maps/` is one set of maps; `settings.py` picks which one the game plays
(`CHAPTER`, `START_MAP`).

Below: the map format, plus a small Pygame demo (turn-based combat comes later),
plus a small Pygame demo: window, game loop, map loading, tile-by-tile movement,
collision, a camera that follows the player and stops at map edges, and doors.
All graphics are coloured shapes — no art files needed.

Settings: 32px tiles, 800x600 window (see `settings.py`).

## Run it

```bash
pip install pygame            # add --break-system-packages on some Linux systems
python game.py                # play: arrows/WASD to move, Z advances dialogue, F1 prints flags, Esc to quit
python view_map.py slums1     # look at one map (arrow keys scroll); parked/town for parked maps
python validate_maps.py       # check all maps for mistakes
python smoke_test.py          # headless play-through of every door
python make_screenshots.py    # regenerate screenshots/*.png
```

In the demo: walk into an NPC to talk. Z finishes the current line or advances to
the next, and the box closes after the last one. That NPC's `sets` flags turn on
when the box closes (the gate watcher sets `slums_gate_open`, which unlocks the
east gate). Bump the locked gate to read `slums_gate_locked` in the same box.
F1 prints the flags dict. Walk into a chest to open it,
step on a save point / boss tile for a placeholder message, and grass (`g`) may
trigger a placeholder "Encounter!" message. Messages are also printed to the terminal.

## Chapter 1 maps (`maps/chapter1/`, dark "slums" palette)

1. **The Slums: Back Alleys** (`slums1`, 40x30) — a maze of narrow alleys with dead ends. Warwick starts in a
   hovel in the top-left. A beggar, an urchin, a drunk in a small yard and a gate-watcher; a save point in a
   little courtyard; two chests tucked in dead ends; rubble heaps (`g`) are encounter tiles (sewer_rat,
   alley_cutpurse); puddles (`~`) block. The gate on the east wall leads to the main road and stays
   **locked until `slums_gate_open`** (placeholder flag name until the story beats are set).
2. **The Slums: Main Road** (`slums2`, 50x22) — a 4-tile-wide road running west to east with sidewalks and
   buildings on both sides, narrow dead-end alleys between them, a back yard with a chest, a save point,
   four NPCs (fruit seller, street guard, old woman, thug), puddles and rubble (sewer_rat, street_thug).
   You arrive from the alleys at the west end; the east end is walled off for now (future exit).

Route: slums1 east gate ↔ slums2 west end (you leave going east and arrive walking east).

## Parked prototype maps (`maps/parked/`)

1. **Willowbrook Village** (`town`) — starting town: houses, a pond, 4 NPCs, a save point, and grass outskirts with encounters. Your house is on the left; the cave mouth is at the top.
2. **Your House** (`house`) — interior with Mom, a bedroom with a save point by the bed, and a chest.
3. **Mossy Caverns** (`dungeon`) — 3 rooms: entrance hall → flooded cavern (cross the river at the single bridge in the top) → switchback vault (zig-zag around two walls) with a chest, a save point and the door to the boss.
4. **Warden's Chamber** (`boss_room`) — long east–west hall: you enter from the west door, walk between two water channels and rows of pillars, and the boss waits in the throne alcove in the east wall.

Route: town ↔ house, town ↔ dungeon ↔ boss_room. Every door works both ways, and doors line up
spatially: leave town northwards through the cave mouth → arrive at the dungeon's south entrance;
leave the dungeon through its east door → arrive at the boss room's west door; the house's front
door (north from the street) opens onto the house's south wall. `validate_maps.py` enforces this.

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
| `game.py` | window, shared story state (`flags`, `chapter`), and the main loop |
| `states.py` | state stack; exploring, plus a dialogue box pushed on top of it |
| `dialogue.py` | loads `data/<chapter>/dialogue.json` and picks the entry for the current flags |
| `data/chapter1/dialogue.json` | placeholder lines for the slums NPCs and the locked gate |
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
   The spawn is where you appear in the *other* map — the tile just inside its door, not on it.
3. Add the return trip: put a `D` in the other map (replace a wall/floor tile) and add a matching
   door entry there with `target_map: "cellar"` and a spawn just inside the cellar's `D`.
   Directions must match: if you walk north into the house's door, the cellar's exit must be on
   its south wall (so you walk south to go back).
4. Run `python validate_maps.py` — it tells you exactly what's missing or mismatched.
5. Run `python view_map.py cellar` to look at it, then `python game.py` to walk there.
