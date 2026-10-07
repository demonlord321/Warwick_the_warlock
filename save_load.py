"""save.json in the project folder: chapter, map, position, and flags.

Stepping on an S tile writes the file. Load Game on the title reads it back.
The file is gitignored; it belongs to whoever is playing.
"""
import json
import os

import settings
from dialogue import load_dialogue

SAVE_PATH = os.path.join(settings.ROOT, "save.json")


def has_save():
    return os.path.exists(SAVE_PATH)


def save_game(game):
    """Write the shared story state and where Warwick is standing."""
    data = {
        "chapter": game.chapter,
        "map": game.current.name,
        "x": game.player.x,
        "y": game.player.y,
        "flags": dict(game.flags),
    }
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"Saved {data['map']} at ({data['x']}, {data['y']}) flags={data['flags']}")


def load_game(game):
    """Replace the live story state with save.json and start exploring there."""
    with open(SAVE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    game.flags = dict(data["flags"])
    game.chapter = data["chapter"]
    game.dialogue = load_dialogue(game.chapter)
    game.maps = {}
    game.opened_chests = set()
    game.message = ""
    game.message_until = 0
    game.current = game.get_map(data["map"])
    game.player.x = data["x"]
    game.player.y = data["y"]
    game.camera.follow(game.player.x, game.player.y, game.current)
    game.return_to_menu()
    game.states.push(game.explore)
