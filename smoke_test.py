"""Headless test: plays through every door using the real game code.

Usage:  SDL_VIDEODRIVER=dummy python smoke_test.py
"""
import os
import random
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

import settings  # noqa: E402
from game import Game  # noqa: E402
from map_loader import GameMap  # noqa: E402

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def path_to(game_map, start, goal):
    """Breadth-first search; returns a list of (dx, dy) steps, never walking over other doors."""
    prev, q = {start: None}, deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        if cur != start and game_map.tile_at(*cur) == "D":
            continue
        for dx, dy in DIRS:
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt not in prev and game_map.is_walkable(*nxt):
                prev[nxt] = cur
                q.append(nxt)
    assert goal in prev, f"no path to {goal} in {game_map.name}"
    steps, cur = [], goal
    while prev[cur] is not None:
        p = prev[cur]
        steps.append((cur[0] - p[0], cur[1] - p[1]))
        cur = p
    return steps[::-1]


def walk_through_door(game, door_xy):
    src = game.current
    door = src.doors[door_xy]
    for dx, dy in path_to(src, (game.player.x, game.player.y), door_xy):
        game.step(dx, dy)
        game.draw()
    assert game.current.name == door["target_map"], (game.current.name, door)
    assert (game.player.x, game.player.y) == (door["spawn_x"], door["spawn_y"])
    assert game.current.is_walkable(game.player.x, game.player.y)
    print(f"  {src.name} {door_xy} -> {game.current.name} at {(game.player.x, game.player.y)}  OK")


def main():
    random.seed(1)
    names = sorted(f[:-4] for f in os.listdir(settings.MAPS_DIR) if f.endswith(".txt"))
    for n in names:
        m = GameMap(n)
        print(f"loaded {n}: {m.width}x{m.height}, {len(m.doors)} doors, '{m.display_name}'")

    game = Game()
    print("start:", game.current.name, game.current.player_start)
    route = [("town", (9, 11)), ("house", (10, 14)), ("town", (19, 1)),
             ("dungeon", (38, 21)), ("boss_room", (12, 19)), ("dungeon", (7, 29))]
    for map_name, door_xy in route:
        assert game.current.name == map_name, game.current.name
        walk_through_door(game, door_xy)

    # Every door in every map, teleporting next to it first.
    for n in names:
        for door_xy, door in GameMap(n).doors.items():
            game.current = game.get_map(n)
            for dx, dy in DIRS:  # find a walkable neighbour to step from
                nx, ny = door_xy[0] - dx, door_xy[1] - dy
                if game.current.is_walkable(nx, ny) and game.current.tile_at(nx, ny) != "D":
                    game.player.x, game.player.y = nx, ny
                    game.step(dx, dy)
                    break
            assert game.current.name == door["target_map"]
    print("all doors work from a neighbouring tile")

    # Interactions: chest in dungeon, boss trigger.
    game.current = game.get_map("dungeon")
    game.player.x, game.player.y = 36, 17
    game.step(0, -1)
    assert ("dungeon", 36, 16) in game.opened_chests
    game.current = game.get_map("boss_room")
    game.player.x, game.player.y = 12, 4
    game.step(0, -1)
    assert "BOSS" in game.message
    pygame.quit()
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
