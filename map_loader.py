"""Loads a map from maps/<name>.txt (the grid) and maps/<name>.json (metadata)."""
import json
import os

from settings import MAPS_DIR, TILE_SIZE
from tiles import is_solid


class GameMap:
    def __init__(self, name, maps_dir=MAPS_DIR):
        self.name = name
        txt_path = os.path.join(maps_dir, name + ".txt")
        json_path = os.path.join(maps_dir, name + ".json")

        with open(txt_path, encoding="utf-8") as f:
            # rstrip("\n") keeps spaces but removes line endings; skip blank lines
            self.rows = [line.rstrip("\r\n") for line in f if line.strip()]
        with open(json_path, encoding="utf-8") as f:
            meta = json.load(f)

        self.width = len(self.rows[0])
        self.height = len(self.rows)
        self.display_name = meta.get("display_name", name.replace("_", " ").title())

        # Look-ups keyed by (x, y) so we can ask "what door is here?" quickly.
        self.doors = {(d["x"], d["y"]): d for d in meta.get("doors", [])}
        self.npcs = {(n["x"], n["y"]): n for n in meta.get("npcs", [])}
        self.encounters = meta.get("encounters") or {"rate": 0.0, "enemy_pool": []}
        self.boss = meta.get("boss")

        # Find the player start tile, if this map has one.
        self.player_start = None
        for y, row in enumerate(self.rows):
            x = row.find("P")
            if x != -1:
                self.player_start = (x, y)

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def tile_at(self, x, y):
        """Return the tile character, or '#' when outside the map."""
        if not self.in_bounds(x, y):
            return "#"
        return self.rows[y][x]

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and not is_solid(self.tile_at(x, y))

    @property
    def pixel_size(self):
        return self.width * TILE_SIZE, self.height * TILE_SIZE
