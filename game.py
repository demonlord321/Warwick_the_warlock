"""Warwick the Warlock — overworld demo.

Run:  python game.py
Keys: arrows / WASD to move, Z to advance dialogue, Esc to quit.

Game owns the window and the shared story state (flags and chapter — the
bits a save file will hold later). Input, update, and draw go through the
state stack; exploring is the state on it right now (see states.py).
"""
import os

import pygame

import settings
from camera import Camera
from dialogue import load_dialogue
from map_loader import GameMap
from player import Player
from states import ExploreState, StateStack

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
        # chapter: which maps/<folder> we are playing.
        self.flags = {}
        self.chapter = settings.CHAPTER
        self.dialogue = load_dialogue(self.chapter)

        self.maps = {}               # cache: name -> GameMap
        self.opened_chests = set()   # (map_name, x, y)
        self.camera = Camera()
        self.message = ""
        self.message_until = 0

        self.current = self.get_map(settings.START_MAP)
        start_x, start_y = self.current.player_start
        self.player = Player(start_x, start_y)
        self.camera.follow(self.player.x, self.player.y, self.current)

        self.states = StateStack()
        self.explore = ExploreState(self)
        self.states.push(self.explore)

    # ---------- helpers ----------
    def maps_dir(self):
        return os.path.join(settings.MAPS_ROOT, self.chapter)

    def get_map(self, name):
        if name not in self.maps:
            self.maps[name] = GameMap(name, self.maps_dir())
        return self.maps[name]

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
