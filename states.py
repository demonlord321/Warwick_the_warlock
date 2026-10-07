"""State stack: input, update, and draw go to whichever state is on top.

The title screen is the bottom state. Exploring is pushed on top of it.
Dialogue (and later battle) get pushed above exploring, so the map stays
up underneath and the player can't walk while another state is active.
Smooth movement is parked; see PLAN.md.
"""
import random

import pygame

import settings
from dialogue import flags_to_set, pick_entry
from render import draw_map, draw_player
from save_load import has_save, load_game, save_game


class State:
    """One mode of play. Subclasses fill in handle_input, update, and draw."""

    def __init__(self, game):
        self.game = game

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def on_escape(self):
        """Esc. Return False to quit the program. Exploring overrides this."""
        return False

    def handle_input(self, events):
        """Handle this frame's events. Return False to quit the game."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                print(f"flags: {self.game.flags}  chapter: {self.game.chapter}")
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return self.on_escape()
        return True

    def update(self, dt):
        pass

    def draw(self, screen):
        pass


class StateStack:
    """The states currently in play. The last one pushed is the active state."""

    def __init__(self):
        self.states = []

    def push(self, state):
        self.states.append(state)
        state.on_enter()

    def pop(self):
        # The menu sits at the bottom for the whole session. Popping it would
        # leave the game with nothing to draw or take input.
        if len(self.states) <= 1:
            raise RuntimeError("can't pop the last state")
        state = self.states.pop()
        state.on_exit()
        return state

    def top(self):
        return self.states[-1]

    def handle_input(self, events):
        return self.top().handle_input(events)

    def update(self, dt):
        self.top().update(dt)

    def draw(self, screen):
        # Bottom to top, so a state pushed later (the dialogue box) paints
        # over the map without having to know how the map is drawn.
        for state in self.states:
            state.draw(screen)


def wrap_text(font, text, max_width):
    """Split text into rows that fit max_width. Always returns at least one row."""
    if text == "":
        return [""]
    rows = []
    current = ""
    for word in text.split(" "):
        trial = word if current == "" else current + " " + word
        if current == "" or font.size(trial)[0] <= max_width:
            current = trial
        else:
            rows.append(current)
            current = word
    if current:
        rows.append(current)
    return rows


class DialogueState(State):
    """A bottom panel of typewriter text. Push one to talk.

    Z while the line is still appearing finishes it. Z once it's fully shown
    advances to the next line, and closes the box after the last one.
    Exploring keeps drawing the map underneath, but it doesn't get input
    until this state is popped, so the player can't walk with the box open.
    """

    def __init__(self, game, lines, on_close=None):
        super().__init__(game)
        self.lines = list(lines) if lines else [""]
        self.index = 0
        self.chars_shown = 0
        self.acc_ms = 0
        self.on_close = on_close

    def on_enter(self):
        for line in self.lines:
            print(line)

    def on_escape(self):
        self.game.return_to_menu()
        return True

    def handle_input(self, events):
        if not super().handle_input(events):
            return False
        # Esc may have closed this box and gone back to the menu.
        if self.game.states.top() is not self:
            return True
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
                self.advance()
                if self.game.states.top() is not self:
                    return True
        return True

    def update(self, dt):
        line = self.lines[self.index]
        if self.chars_shown >= len(line):
            return
        self.acc_ms += dt
        while self.acc_ms >= settings.DIALOGUE_CHAR_MS and self.chars_shown < len(line):
            self.acc_ms -= settings.DIALOGUE_CHAR_MS
            self.chars_shown += 1

    def advance(self):
        """What Z does: finish the current line, or move on if it's already done."""
        line = self.lines[self.index]
        if self.chars_shown < len(line):
            self.chars_shown = len(line)
            self.acc_ms = 0
            return
        self.index += 1
        self.chars_shown = 0
        self.acc_ms = 0
        if self.index >= len(self.lines):
            callback = self.on_close
            self.game.states.pop()
            if callback:
                callback()

    def draw(self, screen):
        margin = settings.DIALOGUE_BOX_MARGIN
        box = pygame.Rect(
            margin,
            settings.SCREEN_HEIGHT - margin - settings.DIALOGUE_BOX_HEIGHT,
            settings.SCREEN_WIDTH - 2 * margin,
            settings.DIALOGUE_BOX_HEIGHT,
        )
        pygame.draw.rect(screen, settings.DIALOGUE_BG, box)
        pygame.draw.rect(screen, settings.DIALOGUE_BORDER_COLOR, box, settings.DIALOGUE_BORDER)

        font = self.game.font
        pad = settings.DIALOGUE_PAD
        shown = self.lines[self.index][:self.chars_shown]
        y = box.y + pad
        line_h = font.get_linesize()
        for row in wrap_text(font, shown, box.width - 2 * pad):
            if y + line_h > box.bottom - pad:
                break
            img = font.render(row, True, settings.DIALOGUE_TEXT_COLOR)
            screen.blit(img, (box.x + pad, y))
            y += line_h + settings.DIALOGUE_LINE_GAP

        if self.chars_shown >= len(self.lines[self.index]):
            prompt = font.render("Z", True, settings.DIALOGUE_TEXT_COLOR)
            screen.blit(
                prompt,
                (box.right - pad - prompt.get_width(), box.bottom - pad - prompt.get_height() + 6),
            )


class ExploreState(State):
    """Walking the map: tile steps, doors, and the placeholder interactions."""

    def __init__(self, game):
        super().__init__(game)
        self.last_move = 0

    def on_escape(self):
        self.game.return_to_menu()
        return True

    def handle_input(self, events):
        if not super().handle_input(events):
            return False
        # Esc goes back to the title. Don't also take a step that frame.
        if self.game.states.top() is not self:
            return True

        now = pygame.time.get_ticks()
        if now - self.last_move < settings.MOVE_DELAY_MS:
            return True
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
        if dx or dy:
            self.step(dx, dy)
            self.last_move = now
        return True

    def step(self, dx, dy):
        """Try to move one tile and react to whatever is there."""
        game = self.game
        target = (game.player.x + dx, game.player.y + dy)
        tile = game.current.tile_at(*target)

        # Bumping into things you can interact with.
        if tile == "N":
            npc = game.current.npcs.get(target, {})
            key = npc.get("dialogue_key")
            if key:
                self.start_dialogue(key)
            else:
                game.show(f"{npc.get('id', 'NPC')}: (no dialogue_key)")
            return
        if tile == "C":
            key = (game.current.name, *target)
            if key in game.opened_chests:
                game.show("The chest is empty.")
            else:
                game.opened_chests.add(key)
                game.show("You opened the chest! (item placeholder)")
            return

        # Locked doors (need a story flag) block you like a wall.
        if tile == "D":
            door = game.current.doors[target]
            if game.current.door_locked(door, game.flags):
                locked_key = door.get("locked_key")
                if locked_key:
                    self.start_dialogue(locked_key)
                else:
                    game.show("It's locked.")
                return

        if not game.player.try_move(dx, dy, game.current):
            return  # blocked by a wall, tree, water...

        here = (game.player.x, game.player.y)
        if tile == "D":
            self.change_map(game.current.doors[here])
        elif tile == "S":
            save_game(game)
            self.say(["Game saved."])
        elif tile == "B" and game.current.boss:
            game.show(f"BOSS BATTLE: {game.current.boss['enemy_id']}! (placeholder)")
        elif tile == "g":
            enc = game.current.encounters
            if enc["enemy_pool"] and random.random() < enc["rate"]:
                game.show(f"Encounter! A wild {random.choice(enc['enemy_pool'])} appears!")

    def start_dialogue(self, key):
        """Open the box for this key, using the first entry our flags allow."""
        entries = self.game.dialogue.get(key)
        if not entries:
            self.game.show(f"[no dialogue '{key}']")
            return
        entry = pick_entry(entries, self.game.flags)
        if entry is None:
            self.game.show(f"[no matching dialogue '{key}']")
            return
        # Remember the flags now; they flip when the box closes, not when it opens.
        to_set = flags_to_set(entry)

        def apply_sets():
            for flag in to_set:
                self.game.flags[flag] = True

        self.say(entry["lines"], on_close=apply_sets)

    def say(self, lines, on_close=None):
        """Open the dialogue box on these lines. Walking waits until it closes."""
        self.game.message = ""
        self.game.states.push(DialogueState(self.game, lines, on_close=on_close))

    def change_map(self, door):
        game = self.game
        game.current = game.get_map(door["target_map"])
        game.player.x, game.player.y = door["spawn_x"], door["spawn_y"]
        game.show(f"Entered {game.current.display_name}")

    def draw(self, screen):
        game = self.game
        game.camera.follow(game.player.x, game.player.y, game.current)
        draw_map(screen, game.current, game.camera.x, game.camera.y, game.opened_chests)
        draw_player(screen, game.player.x, game.player.y, game.camera.x, game.camera.y)

        # Map name label (top-left)
        label = game.font.render(game.current.display_name, True, (255, 255, 255))
        bg = pygame.Rect(8, 8, label.get_width() + 16, label.get_height() + 10)
        pygame.draw.rect(screen, (0, 0, 0), bg)
        pygame.draw.rect(screen, (255, 255, 255), bg, 2)
        screen.blit(label, (16, 13))

        # Short banner (bottom) for chests, locked doors, and other one-liners.
        if game.message and pygame.time.get_ticks() < game.message_until:
            box = pygame.Rect(20, settings.SCREEN_HEIGHT - 70, settings.SCREEN_WIDTH - 40, 50)
            pygame.draw.rect(screen, (0, 0, 0), box)
            pygame.draw.rect(screen, (255, 255, 255), box, 2)
            text = game.font.render(game.message, True, (255, 255, 255))
            screen.blit(text, (box.x + 14, box.y + 15))


class MenuState(State):
    """Title screen: New Game, Load Game, Quit.

    Up/down (or W/S) moves the cursor. Z or Enter confirms.
    Load Game is drawn grey and skipped while save.json is missing.
    Esc here quits, same as choosing Quit.
    """

    OPTIONS = ("New Game", "Load Game", "Quit")

    def __init__(self, game):
        super().__init__(game)
        self.selected = 0
        self.title_font = pygame.font.Font(None, settings.MENU_TITLE_SIZE)
        self.option_font = pygame.font.Font(None, settings.MENU_OPTION_SIZE)

    def enabled(self, index):
        if self.OPTIONS[index] == "Load Game":
            return has_save()
        return True

    def move(self, direction):
        """Step the cursor, skipping options that can't be chosen."""
        count = len(self.OPTIONS)
        i = self.selected
        for _ in range(count):
            i = (i + direction) % count
            if self.enabled(i):
                self.selected = i
                return

    def confirm(self):
        """Carry out the highlighted option. Return False to quit the program."""
        if not self.enabled(self.selected):
            return True
        choice = self.OPTIONS[self.selected]
        if choice == "New Game":
            self.game.new_game()
        elif choice == "Load Game":
            load_game(self.game)
        elif choice == "Quit":
            return False
        return True

    def handle_input(self, events):
        if not super().handle_input(events):
            return False
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_UP, pygame.K_w):
                self.move(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.move(1)
            elif event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_KP_ENTER):
                return self.confirm()
        return True

    def draw(self, screen):
        # Full-screen state. Don't paint the title over the map once we've left it.
        if self.game.states.top() is not self:
            return
        screen.fill(settings.MENU_BG)
        band = pygame.Rect(0, 0, 64, settings.SCREEN_HEIGHT)
        pygame.draw.rect(screen, settings.MENU_BAND, band)
        pygame.draw.rect(screen, settings.MENU_BAND,
                         band.move(settings.SCREEN_WIDTH - 64, 0))

        title = self.title_font.render("Warwick the Warlock", True, settings.MENU_TITLE_COLOR)
        screen.blit(title, title.get_rect(center=(settings.SCREEN_WIDTH // 2, 180)))

        y = 340
        for i, label in enumerate(self.OPTIONS):
            if i == self.selected:
                color = settings.MENU_SELECTED
                text = "> " + label
            elif not self.enabled(i):
                color = settings.MENU_DISABLED
                text = "  " + label
            else:
                color = settings.MENU_NORMAL
                text = "  " + label
            img = self.option_font.render(text, True, color)
            screen.blit(img, img.get_rect(center=(settings.SCREEN_WIDTH // 2, y)))
            y += 52
