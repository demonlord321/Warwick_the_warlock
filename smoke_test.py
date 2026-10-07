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
        game.explore.step(dx, dy)
        game.draw()
    assert game.current.name == door["target_map"], (game.current.name, door)
    assert (game.player.x, game.player.y) == (door["spawn_x"], door["spawn_y"])
    assert game.current.is_walkable(game.player.x, game.player.y)
    print(f"  {src.name} {door_xy} -> {game.current.name} at {(game.player.x, game.player.y)}  OK")


def check_dialogue_box(game):
    """Z finishes a typing line, then advances; the box blocks movement until it closes."""
    from states import DialogueState

    start = (game.player.x, game.player.y)
    closed = []
    game.states.push(DialogueState(game, ["Hello there.", "Second line."],
                                   on_close=lambda: closed.append(True)))
    box = game.states.top()
    game.draw()

    # Still typing: Z reveals the rest of the line and stays on it.
    assert box.chars_shown == 0
    game.states.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)])
    assert box.chars_shown == len("Hello there.")
    assert box.index == 0
    assert game.states.top() is box

    # Line complete: Z moves to the next line.
    game.states.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)])
    assert box.index == 1
    assert box.chars_shown == 0

    # The typewriter only reveals characters; it does not advance on its own.
    box.update(settings.DIALOGUE_CHAR_MS * 3)
    assert box.chars_shown == 3
    box.update(10_000)
    assert box.chars_shown == len("Second line.")
    assert box.index == 1
    game.draw()

    game.states.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)])
    assert closed == [True]
    assert game.states.top() is game.explore

    # A held move key is handled by exploring only. With the box on top it does nothing,
    # and the same key walks once the box is gone. (The dummy video driver never
    # updates get_pressed from posted events, so the test supplies the key state.)
    class Held:
        def __getitem__(self, key):
            return key == pygame.K_d

    real_pressed = pygame.key.get_pressed
    pygame.key.get_pressed = lambda: Held()
    try:
        ready = pygame.time.get_ticks() - settings.MOVE_DELAY_MS
        game.explore.last_move = ready
        game.states.push(DialogueState(game, ["Wait."]))
        assert game.states.handle_input([])
        assert (game.player.x, game.player.y) == start
        game.states.pop()
        game.explore.last_move = ready
        assert game.states.handle_input([])
        assert (game.player.x, game.player.y) == (start[0] + 1, start[1])
    finally:
        pygame.key.get_pressed = real_pressed
    game.player.x, game.player.y = start
    print("dialogue box OK")


def check_gate_lock(game, door_xy, flag):
    """A flag-gated door stays shut (player doesn't move) until its flag is set."""
    assert not game.flags.get(flag)
    steps = path_to(game.current, (game.player.x, game.player.y), door_xy)
    for dx, dy in steps[:-1]:
        game.explore.step(dx, dy)
    before = (game.current.name, game.player.x, game.player.y)
    game.explore.step(*steps[-1])
    assert (game.current.name, game.player.x, game.player.y) == before, "door should be locked"
    assert "locked" in game.message.lower(), game.message
    print(f"  {game.current.name} {door_xy} locked without '{flag}'  OK")
    game.flags[flag] = True  # stand-in for the story beat that sets it


def main():
    random.seed(1)
    # Every map in every folder must load.
    for folder in sorted(os.listdir(settings.MAPS_ROOT)):
        maps_dir = os.path.join(settings.MAPS_ROOT, folder)
        if not os.path.isdir(maps_dir):
            continue
        for f in sorted(os.listdir(maps_dir)):
            if f.endswith(".txt"):
                m = GameMap(f[:-4], maps_dir)
                print(f"loaded {folder}/{m.name}: {m.width}x{m.height}, {len(m.doors)} doors, '{m.display_name}'")

    names = sorted(f[:-4] for f in os.listdir(settings.MAPS_DIR) if f.endswith(".txt"))
    game = Game()
    print("start:", game.current.name, game.current.player_start)
    assert game.current.name == settings.START_MAP
    assert game.states.top() is game.explore
    assert game.chapter == settings.CHAPTER
    assert game.flags == {}
    check_dialogue_box(game)

    # Chapter 1 route: the alley gate is locked until its flag is set.
    check_gate_lock(game, (39, 15), "slums_gate_open")
    route = [("slums1", (39, 15)), ("slums2", (0, 10))]
    for map_name, door_xy in route:
        assert game.current.name == map_name, game.current.name
        walk_through_door(game, door_xy)

    # Every door in the current chapter, teleporting next to it first.
    for n in names:
        for door_xy, door in GameMap(n).doors.items():
            game.current = game.get_map(n)
            for dx, dy in DIRS:  # find a walkable neighbour to step from
                nx, ny = door_xy[0] - dx, door_xy[1] - dy
                if game.current.is_walkable(nx, ny) and game.current.tile_at(nx, ny) != "D":
                    game.player.x, game.player.y = nx, ny
                    game.explore.step(dx, dy)
                    break
            assert game.current.name == door["target_map"]
    print("all doors work from a neighbouring tile")

    # Interactions: a chest in each slums map, and talking to an NPC.
    for map_name, stand, step in (("slums1", (11, 28), (-1, 0)), ("slums2", (16, 2), (1, 0))):
        game.current = game.get_map(map_name)
        game.player.x, game.player.y = stand
        game.explore.step(*step)
        chest = (map_name, stand[0] + step[0], stand[1] + step[1])
        assert chest in game.opened_chests, chest
    game.current = game.get_map("slums1")
    game.player.x, game.player.y = 17, 2
    game.explore.step(0, 1)
    assert "beggar" in game.message, game.message
    pygame.quit()
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
