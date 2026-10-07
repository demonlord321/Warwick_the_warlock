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


def finish_dialogue(game):
    """Press Z until the open box closes (finish the line, then advance)."""
    from states import DialogueState
    state = game.states.top()
    assert isinstance(state, DialogueState), type(state)
    guard = 0
    while game.states.top() is state:
        state.advance()
        guard += 1
        assert guard < 50, "dialogue did not close"


def check_dialogue_picking():
    """The first entry whose requires are all met is the one that plays."""
    from dialogue import dialogue_path, load_dialogue, pick_entry

    path = dialogue_path()
    assert path.endswith(os.path.join("data", "chapter1", "dialogue.json")), path
    assert os.path.exists(path), path
    data = load_dialogue()
    before = pick_entry(data["beggar_plea"], {})
    assert before["requires"] == []
    after = pick_entry(data["beggar_plea"], {"slums_gate_open": True})
    assert "slums_gate_open" in after["requires"]
    assert after is not before

    watcher = pick_entry(data["gate_watcher_warning"], {})
    assert "slums_gate_open" in watcher["sets"]
    again = pick_entry(data["gate_watcher_warning"], {"slums_gate_open": True})
    assert "slums_gate_open" not in again["sets"]

    locked = pick_entry(data["slums_gate_locked"], {})
    assert any("locked" in line.lower() for line in locked["lines"])

    assert pick_entry([{"requires": ["nope"], "sets": [], "lines": ["x"]}], {}) is None
    entries = [
        {"requires": ["slums_gate_open"], "sets": [], "lines": ["after"]},
        {"requires": [], "sets": [], "lines": ["before"]},
    ]
    assert pick_entry(entries, {})["lines"] == ["before"]
    assert pick_entry(entries, {"slums_gate_open": True})["lines"] == ["after"]
    print("dialogue picking OK")


def check_gate_lock(game, door_xy, flag):
    """A flag-gated door stays shut (player doesn't move) until its flag is set."""
    assert not game.flags.get(flag)
    steps = path_to(game.current, (game.player.x, game.player.y), door_xy)
    for dx, dy in steps[:-1]:
        game.explore.step(dx, dy)
    before = (game.current.name, game.player.x, game.player.y)
    game.explore.step(*steps[-1])
    assert (game.current.name, game.player.x, game.player.y) == before, "door should be locked"
    from states import DialogueState
    state = game.states.top()
    assert isinstance(state, DialogueState), type(state)
    assert any("locked" in line.lower() for line in state.lines), state.lines
    finish_dialogue(game)
    assert game.states.top() is game.explore
    print(f"  {game.current.name} {door_xy} locked without '{flag}'  OK")


def bump(game, target_xy):
    """Walk beside target_xy and step onto it (an NPC, chest, or door)."""
    src = game.current
    start = (game.player.x, game.player.y)
    for dx, dy in DIRS:
        stand = (target_xy[0] - dx, target_xy[1] - dy)
        if not src.is_walkable(*stand) or src.tile_at(*stand) == "D":
            continue
        try:
            steps = path_to(src, start, stand)
        except AssertionError:
            continue
        for sdx, sdy in steps:
            game.explore.step(sdx, sdy)
        game.explore.step(dx, dy)
        return
    raise AssertionError(f"no path to bump {target_xy} in {src.name}")


def open_gate_by_talking(game, flag):
    """The NPC whose current entry sets `flag` does so when their box closes."""
    from dialogue import pick_entry

    found = None
    for pos, npc in game.current.npcs.items():
        entry = pick_entry(game.dialogue[npc["dialogue_key"]], game.flags)
        if entry and flag in (entry.get("sets") or []):
            found = (pos, npc)
            break
    assert found, f"no NPC on {game.current.name} sets {flag}"
    pos, npc = found
    bump(game, pos)
    assert not game.flags.get(flag), "flag waits until the box closes"
    finish_dialogue(game)
    assert game.flags.get(flag) is True
    print(f"  talked to {npc['id']}; '{flag}' set when the box closed  OK")


def check_flag_key(game):
    """F1 prints the flags dict (and the chapter sitting next to it)."""
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        assert game.states.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F1)])
    text = buf.getvalue()
    assert "flags:" in text and "slums_gate_open" in text and game.chapter in text, text
    print("F1 prints flags OK")


def check_save_round_trip(game):
    """Step on an S tile, then Load Game restores chapter, map, position, and flags."""
    import json

    from save_load import SAVE_PATH, has_save

    if os.path.exists(SAVE_PATH):
        os.remove(SAVE_PATH)
    try:
        game.current = game.get_map("slums1")
        game.player.x, game.player.y = 13, 9
        game.flags["slums_gate_open"] = True
        game.flags["demo_flag"] = True
        game.explore.step(1, 0)
        assert (game.current.name, game.player.x, game.player.y) == ("slums1", 14, 9)
        box = game.states.top()
        assert any("saved" in line.lower() for line in box.lines), box.lines
        finish_dialogue(game)
        assert has_save()
        with open(SAVE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert data == {
            "chapter": "chapter1",
            "map": "slums1",
            "x": 14,
            "y": 9,
            "flags": {"slums_gate_open": True, "demo_flag": True},
        }

        game.flags = {}
        game.player.x, game.player.y = 2, 2
        game.current = game.get_map("slums2")
        game.return_to_menu()
        menu = game.menu
        load_i = menu.OPTIONS.index("Load Game")
        assert menu.enabled(load_i)
        menu.selected = load_i
        assert game.states.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        assert game.states.top() is game.explore
        assert game.chapter == "chapter1"
        assert game.current.name == "slums1"
        assert (game.player.x, game.player.y) == (14, 9)
        assert game.flags == {"slums_gate_open": True, "demo_flag": True}
        print("save/load round trip OK")
    finally:
        if os.path.exists(SAVE_PATH):
            os.remove(SAVE_PATH)


def check_main_menu(game):
    """Boots on the title. New Game starts fresh in slums1. Esc returns to the title."""
    from states import MenuState

    menu = game.states.top()
    assert menu is game.menu and isinstance(menu, MenuState)
    # Always exercise the greyed-out Load Game path, even if a previous run left a file.
    from save_load import SAVE_PATH
    if os.path.exists(SAVE_PATH):
        os.remove(SAVE_PATH)
    game.draw()
    assert menu.OPTIONS[menu.selected] == "New Game"

    load_i = menu.OPTIONS.index("Load Game")
    assert menu.enabled(load_i) is False
    # Down skips Load Game while it is greyed out.
    game.states.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)])
    assert menu.OPTIONS[menu.selected] == "Quit"
    game.states.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)])
    assert menu.OPTIONS[menu.selected] == "New Game"

    menu.selected = menu.OPTIONS.index("Quit")
    assert menu.confirm() is False
    assert game.states.top() is menu

    menu.selected = 0
    assert game.states.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)])
    assert game.states.top() is game.explore
    assert game.flags == {}
    assert game.chapter == settings.CHAPTER
    assert game.current.name == settings.START_MAP
    assert (game.player.x, game.player.y) == game.current.player_start

    assert game.states.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
    assert game.states.top() is menu
    game.new_game()
    assert game.states.top() is game.explore
    assert game.flags == {}
    assert (game.player.x, game.player.y) == game.current.player_start
    print("main menu OK")


def main():
    random.seed(1)
    check_dialogue_picking()
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
    check_main_menu(game)
    print("start:", game.current.name, game.current.player_start)
    assert game.current.name == settings.START_MAP
    assert game.states.top() is game.explore
    assert game.chapter == settings.CHAPTER
    assert game.flags == {}
    check_dialogue_box(game)

    # Chapter 1 route: the alley gate is locked until an NPC's dialogue sets the flag.
    check_gate_lock(game, (39, 15), "slums_gate_open")
    open_gate_by_talking(game, "slums_gate_open")
    check_flag_key(game)
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
    from states import DialogueState
    beggar = game.states.top()
    assert isinstance(beggar, DialogueState)
    assert any("beggar" in line.lower() for line in beggar.lines), beggar.lines
    finish_dialogue(game)
    check_save_round_trip(game)
    pygame.quit()
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
