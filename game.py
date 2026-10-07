"""Warwick the Warlock — overworld demo.

Run:  python game.py
Keys: the title screen uses up/down (or W/S) and Z/Enter.
      In the slums, arrows / WASD move, Z advances dialogue, F1 prints flags.
      Esc returns to the title. Quit on the title exits.

Game owns the window and the shared story state (flags and chapter — the
bits a save file will hold later). Input, update, and draw go through the
state stack. The game boots on the title screen (see states.py).
"""
import os

import pygame

import settings
from camera import Camera
from dialogue import load_dialogue
from map_loader import GameMap
from player import Player
from states import ExploreState, MenuState, StateStack

MESSAGE_TIME_MS = 2000


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption("RPG Maps Demo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)

        # Shared by every state. Save/load will write these out later.
        # flags: story switches, e.g. {"slums_gate_open": True}. Missing = false.
        # chapter: which maps/<folder> and data/<folder> we are playing.
        self.flags = {}
        self.chapter = settings.CHAPTER
        self.dialogue = load_dialogue(self.chapter)

        self.maps = {}               # cache: name -> GameMap
        self.opened_chests = set()   # (map_name, x, y)
        self.camera = Camera()
        self.message = ""
        self.message_until = 0

        self.player = Player(0, 0)
        self.current = self.get_map(settings.START_MAP)

        self.states = StateStack()
        self.explore = ExploreState(self)
        self.menu = MenuState(self)
        self.states.push(self.menu)

    # ---------- helpers ----------
    def maps_dir(self):
        return os.path.join(settings.MAPS_ROOT, self.chapter)

    def get_map(self, name):
        if name not in self.maps:
            self.maps[name] = GameMap(name, self.maps_dir())
        return self.maps[name]

    def new_game(self):
        """Start fresh: empty flags, chapter 1, standing on the slums1 start tile.

        The chapter intro screen (PLAN M1.6) will play before this later.
        Load Game will skip it. For now New Game drops you straight into the map.
        """
        self.flags = {}
        self.chapter = settings.CHAPTER
        self.dialogue = load_dialogue(self.chapter)
        self.maps = {}
        self.opened_chests = set()
        self.message = ""
        self.message_until = 0
        self.current = self.get_map(settings.START_MAP)
        self.player.x, self.player.y = self.current.player_start
        self.camera.follow(self.player.x, self.player.y, self.current)
        self.return_to_menu()
        self.states.push(self.explore)

    def return_to_menu(self):
        """Pop back to the title. Does not save, and does not ask."""
        while not isinstance(self.states.top(), MenuState):
            self.states.pop()

    def show(self, text):
        """A short banner (chests, encounters, "entered ..."). Also prints it."""
        print(text)
        self.message = text
        self.message_until = pygame.time.get_ticks() + MESSAGE_TIME_MS

    # ---------- main loop ----------
    def draw(self):
        self.screen.fill((0, 0, 0))
        self.states.draw(self.screen)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(settings.FPS)
            events = pygame.event.get()
            running = self.states.handle_input(events)
            if running:
                self.states.update(dt)
                self.draw()
                pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
