"""Checks every map in maps/ for mistakes. Needs only plain Python.

Usage:  python validate_maps.py          (exit code 0 = all good)

Checks:
  * grid is rectangular and only uses legend characters
  * every 'D' has a JSON door entry and every door entry sits on a 'D'
  * door targets exist; spawns are in bounds, walkable and not a door
  * every door has a reverse door, and the spawn is right next to it
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

MAPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")
START_MAP = "town"
LEGEND = set("#.PNDgT~SCB")
SOLID = set("#NTC~")


def load_all():
    maps = {}
    for txt in sorted(glob.glob(os.path.join(MAPS_DIR, "*.txt"))):
        name = os.path.splitext(os.path.basename(txt))[0]
        with open(txt, encoding="utf-8") as f:
            rows = [line.rstrip("\r\n") for line in f if line.strip()]
        json_path = os.path.join(MAPS_DIR, name + ".json")
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


def adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def validate():
    errors, warnings = [], []
    maps = load_all()
    if START_MAP not in maps:
        return [f"start map '{START_MAP}' not found"], warnings

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
            back = [b for b in tmeta.get("doors", []) if b["target_map"] == name
                    and adjacent((b["x"], b["y"]), spawn)]
            if not back:
                err(f"door {(d['x'], d['y'])} -> '{tgt}': no return door next to spawn {spawn}")
            elif not any(adjacent((b["spawn_x"], b["spawn_y"]), (d["x"], d["y"])) for b in back):
                err(f"door {(d['x'], d['y'])} -> '{tgt}': return door does not spawn next to this door")

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
    errors, warnings = validate()
    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)
    if errors:
        print(f"\n{len(errors)} error(s) found.")
        sys.exit(1)
    names = sorted(load_all())
    print(f"All {len(names)} maps OK: {', '.join(names)}")


if __name__ == "__main__":
    main()
