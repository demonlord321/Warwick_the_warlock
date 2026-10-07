"""Checks every map in maps/ for mistakes. Needs only plain Python.

Usage:  python validate_maps.py          (exit code 0 = all good)

Every sub-folder of maps/ (chapter1, parked, ...) is its own set of maps and is
checked on its own: doors only lead to maps in the same folder, and the start
map is the one map in that folder holding the single 'P'.

Checks:
  * grid is rectangular and only uses legend characters
  * every 'D' has a JSON door entry and every door entry sits on a 'D'
  * door targets exist; spawns are in bounds, walkable and not a door
  * every door has a reverse door, and the spawn is right next to it (inward side)
  * doors line up spatially: a door on the north side of one map leads to a
    door on the south side of the next (east <-> west, etc.)
  * locked doors: "requires_flag" / "locked_key" are non-empty strings, a
    locked_key only appears with a requires_flag, and (once dialogue.json exists)
    the locked_key is a real dialogue key and some dialogue entry sets the flag
  * NPC / boss coordinates match 'N' / 'B' tiles (and vice versa)
  * exactly one 'P', and it is in the start map
  * every door, save point, boss, chest and NPC can actually be reached
  * every map can be reached from the start map
"""
import glob
import json
import os
import sys
from collections import deque

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_ROOT = os.path.join(ROOT_DIR, "maps")
LEGEND = set("#.PNDgT~SCB")
SOLID = set("#NTC~")


def map_folders():
    """Every sub-folder of maps/ that holds at least one .txt map."""
    return sorted(d for d in glob.glob(os.path.join(MAPS_ROOT, "*"))
                  if os.path.isdir(d) and glob.glob(os.path.join(d, "*.txt")))


def load_dialogue(maps_dir):
    """Return (path, data) for the first dialogue.json found, else (None, None).

    Looks next to the maps first (maps/<chapter>/dialogue.json), then data/<chapter>/,
    then data/, then the project root.
    """
    chapter = os.path.basename(os.path.normpath(maps_dir))
    for path in (os.path.join(maps_dir, "dialogue.json"),
                 os.path.join(ROOT_DIR, "data", chapter, "dialogue.json"),
                 os.path.join(ROOT_DIR, "data", "dialogue.json"),
                 os.path.join(ROOT_DIR, "dialogue.json")):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return path, json.load(f)
    return None, None


def flags_set_by(dialogue):
    """Every flag that some dialogue entry can set."""
    out = set()
    for entries in (dialogue or {}).values():
        for entry in entries if isinstance(entries, list) else [entries]:
            sets = entry.get("sets", []) if isinstance(entry, dict) else []
            out |= set(sets.keys() if isinstance(sets, dict) else sets)
    return out


def load_all(maps_dir):
    maps = {}
    for txt in sorted(glob.glob(os.path.join(maps_dir, "*.txt"))):
        name = os.path.splitext(os.path.basename(txt))[0]
        with open(txt, encoding="utf-8") as f:
            rows = [line.rstrip("\r\n") for line in f if line.strip()]
        json_path = os.path.join(maps_dir, name + ".json")
        meta = None
        if os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                meta = json.load(f)
        maps[name] = (rows, meta)
    return maps


def tiles_of(rows, char):
    return {(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == char}


def walkable(rows, x, y):
    return 0 <= y < len(rows) and 0 <= x < len(rows[0]) and rows[y][x] not in SOLID


# Direction you walk to go THROUGH a door on that side, as (dx, dy).
SIDES = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
OPPOSITE = {"north": "south", "south": "north", "west": "east", "east": "west"}


def door_side(rows, x, y):
    """Which wall a door is on, judged by its single open (walkable) neighbour.

    A door with floor below it is on the north wall (you walk north to leave),
    floor to its left means the east wall, and so on. Returns None if the door
    does not have exactly one open neighbour (i.e. it isn't set into a wall).
    """
    open_sides = [side for side, (dx, dy) in SIDES.items()
                  if walkable(rows, x - dx, y - dy) and rows[y - dy][x - dx] != "D"]
    return open_sides[0] if len(open_sides) == 1 else None


def inward_tile(rows, x, y):
    """The walkable tile just inside a door (where players should arrive)."""
    dx, dy = SIDES[door_side(rows, x, y)]
    return (x - dx, y - dy)


def adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def validate(maps_dir):
    errors, warnings = [], []
    maps = load_all(maps_dir)
    starts_with_p = [n for n, (rows, _) in maps.items() if tiles_of(rows, "P")]
    if len(starts_with_p) != 1:
        return [f"exactly one map needs a 'P' start tile (found: {starts_with_p or 'none'})"], warnings
    START_MAP = starts_with_p[0]

    dialogue_path, dialogue = load_dialogue(maps_dir)
    settable = flags_set_by(dialogue)

    p_count = 0
    for name, (rows, meta) in maps.items():
        err = lambda msg: errors.append(f"[{name}] {msg}")
        if meta is None:
            err("missing .json file")
            continue
        widths = {len(r) for r in rows}
        if len(widths) != 1:
            err(f"rows have different widths: {sorted(widths)}")
            continue
        for y, row in enumerate(rows):
            for x, c in enumerate(row):
                if c not in LEGEND:
                    err(f"unknown tile {c!r} at ({x},{y})")

        # P
        ps = tiles_of(rows, "P")
        p_count += len(ps)
        if ps and name != START_MAP:
            err(f"'P' found outside the start map at {sorted(ps)}")
        if name == START_MAP and len(ps) != 1:
            err(f"start map must have exactly one 'P' (found {len(ps)})")

        # Doors
        d_tiles = tiles_of(rows, "D")
        door_pos = {(d["x"], d["y"]) for d in meta.get("doors", [])}
        for pos in d_tiles - door_pos:
            err(f"'D' at {pos} has no JSON door entry")
        for pos in door_pos - d_tiles:
            err(f"JSON door at {pos} is not on a 'D' tile")
        for d in meta.get("doors", []):
            # Locked doors (optional fields)
            flag, lkey = d.get("requires_flag"), d.get("locked_key")
            where = f"door {(d['x'], d['y'])}"
            if flag is not None and (not isinstance(flag, str) or not flag):
                err(f"{where}: requires_flag must be a non-empty string")
            if lkey is not None and (not isinstance(lkey, str) or not lkey):
                err(f"{where}: locked_key must be a non-empty string")
            if lkey and not flag:
                err(f"{where}: has a locked_key but no requires_flag, so it can never be locked")
            if flag and not lkey:
                warnings.append(f"[{name}] {where}: requires_flag without locked_key "
                                f"(players get no message when it's locked)")
            if flag and dialogue is not None:
                if lkey and lkey not in dialogue:
                    err(f"{where}: locked_key '{lkey}' is not in {os.path.basename(dialogue_path)}")
                if flag not in settable:
                    err(f"{where}: needs flag '{flag}' but no dialogue entry sets it "
                        f"(the door could never open)")
            tgt = d["target_map"]
            spawn = (d["spawn_x"], d["spawn_y"])
            if tgt not in maps or maps[tgt][1] is None:
                err(f"door {(d['x'], d['y'])} targets missing map '{tgt}'")
                continue
            trows, tmeta = maps[tgt]
            if not walkable(trows, *spawn):
                err(f"door {(d['x'], d['y'])} spawn {spawn} in '{tgt}' is out of bounds or solid")
                continue
            if trows[spawn[1]][spawn[0]] == "D":
                err(f"door {(d['x'], d['y'])} spawn {spawn} in '{tgt}' is ON a door (player would bounce)")
            side = door_side(rows, d["x"], d["y"])
            if side is None:
                err(f"door {(d['x'], d['y'])} must sit in a wall with exactly one open side")
                continue
            back = [b for b in tmeta.get("doors", []) if b["target_map"] == name
                    and trows[b["y"]][b["x"]] == "D" and door_side(trows, b["x"], b["y"])
                    and inward_tile(trows, b["x"], b["y"]) == spawn]
            if not back:
                err(f"door {(d['x'], d['y'])} -> '{tgt}': spawn {spawn} is not the tile just "
                    f"inside a door that leads back to '{name}'")
                continue
            b = back[0]
            if (b["spawn_x"], b["spawn_y"]) != inward_tile(rows, d["x"], d["y"]):
                err(f"door {(d['x'], d['y'])} -> '{tgt}': return door {(b['x'], b['y'])} should "
                    f"spawn at {inward_tile(rows, d['x'], d['y'])} (just inside this door)")
            b_side = door_side(trows, b["x"], b["y"])
            if b_side != OPPOSITE[side]:
                err(f"door {(d['x'], d['y'])} is on the {side} side, so its return door in "
                    f"'{tgt}' {(b['x'], b['y'])} must be on the {OPPOSITE[side]} side "
                    f"(it is on the {b_side} side)")

        # NPCs and boss
        n_tiles = tiles_of(rows, "N")
        npc_pos = {(n["x"], n["y"]) for n in meta.get("npcs", [])}
        for pos in n_tiles - npc_pos:
            err(f"'N' at {pos} has no JSON npc entry")
        for pos in npc_pos - n_tiles:
            err(f"JSON npc at {pos} is not on an 'N' tile")
        b_tiles = tiles_of(rows, "B")
        boss = meta.get("boss")
        boss_pos = {(boss["x"], boss["y"])} if boss else set()
        if b_tiles != boss_pos:
            err(f"'B' tiles {sorted(b_tiles)} do not match JSON boss {sorted(boss_pos)}")

        # Encounters
        enc = meta.get("encounters") or {}
        rate, pool = enc.get("rate", 0), enc.get("enemy_pool", [])
        if not 0 <= rate <= 1:
            err(f"encounter rate {rate} must be between 0 and 1")
        if rate > 0 and not pool:
            err("encounter rate > 0 but enemy_pool is empty")
        if tiles_of(rows, "g") and rate == 0:
            warnings.append(f"[{name}] has grass but encounter rate is 0")

    if p_count != 1:
        errors.append(f"expected exactly one 'P' across all maps, found {p_count}")
    if errors:
        return errors, warnings

    # ---------- Reachability (walk the maps like a player would) ----------
    starts = {name: set() for name in maps}
    starts[START_MAP] |= tiles_of(maps[START_MAP][0], "P")
    reached_maps, queue = {START_MAP}, deque([START_MAP])
    reach = {}
    while queue:
        name = queue.popleft()
        rows, meta = maps[name]
        seen, q = set(starts[name]), deque(starts[name])
        while q:
            x, y = q.popleft()
            if rows[y][x] == "D":
                continue  # stepping on a door takes you away
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in seen and walkable(rows, nx, ny):
                    seen.add((nx, ny))
                    q.append((nx, ny))
        reach[name] = seen
        for d in meta["doors"]:
            if (d["x"], d["y"]) in seen:
                tgt, spawn = d["target_map"], (d["spawn_x"], d["spawn_y"])
                if spawn not in starts[tgt]:
                    starts[tgt].add(spawn)
                    if tgt in reached_maps:
                        queue.append(tgt)  # re-walk with the new entry point
                if tgt not in reached_maps:
                    reached_maps.add(tgt)
                    queue.append(tgt)

    for name, (rows, meta) in maps.items():
        if name not in reached_maps:
            errors.append(f"[{name}] cannot be reached from '{START_MAP}'")
            continue
        seen = reach[name]
        for c in "DSB":
            for pos in tiles_of(rows, c):
                if pos not in seen:
                    errors.append(f"[{name}] '{c}' at {pos} cannot be reached")
        for c in "NC":
            for (x, y) in tiles_of(rows, c):
                if not any(p in seen for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                    errors.append(f"[{name}] '{c}' at {(x, y)} cannot be reached (no walkable neighbour)")
    return errors, warnings


def main():
    total_errors = 0
    for folder in map_folders():
        label = os.path.relpath(folder, ROOT_DIR)
        print(f"== {label} ==")
        total_errors += report(folder)
        print()
    if total_errors:
        print(f"{total_errors} error(s) found.")
        sys.exit(1)
    print("All map folders OK.")


def report(maps_dir):
    errors, warnings = validate(maps_dir)
    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)
    if errors:
        return len(errors)
    maps = load_all(maps_dir)
    print(f"All {len(maps)} maps OK: {', '.join(sorted(maps))}")
    print("Door directions (the way you walk through each door):")
    for name, (rows, meta) in sorted(maps.items()):
        for d in meta["doors"]:
            t_rows = maps[d["target_map"]][0]
            back = [b for b in maps[d["target_map"]][1]["doors"]
                    if inward_tile(t_rows, b["x"], b["y"]) == (d["spawn_x"], d["spawn_y"])][0]
            lock = f"  [locked until '{d['requires_flag']}']" if d.get("requires_flag") else ""
            print(f"  {name} {d['x'], d['y']} go {door_side(rows, d['x'], d['y'])} -> "
                  f"arrive at {d['target_map']} {back['x'], back['y']} (its return door goes {door_side(t_rows, back['x'], back['y'])}){lock}")
    if load_dialogue(maps_dir)[0] is None:
        print("Note: no dialogue.json yet, so locked_key / flag checks against dialogue were skipped.")
    return 0


if __name__ == "__main__":
    main()
