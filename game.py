"""Milestone 1 demo: walk around, bump into things, go through doors.

Run:  python game.py
Keys: arrows / WASD to move, Esc to quit.
"""
import random

import pygame

import settings
from camera import Camera
from map_loader import GameMap
from player import Player
from render import draw_map, draw_player

MESSAGE_TIME_MS = 2000


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption("RPG Maps Demo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)

        self.maps = {}               # cache: name -> GameMap
        self.opened_chests = set()   # (map_name, x, y)
        self.camera = Camera()
        self.message = ""
        self.message_until = 0
        self.last_move = 0

        self.current = self.get_map(settings.START_MAP)
        start_x, start_y = self.current.player_start
        self.player = Player(start_x, start_y)
        self.camera.follow(self.player.x, self.player.y, self.current)

    # ---------- helpers ----------
    def get_map(self, name):
        if name not in self.maps:
            self.maps[name] = GameMap(name)
        return self.maps[name]

    def show(self, text):
        print(text)  # also log to the terminal
        self.message = text
        self.message_until = pygame.time.get_ticks() + MESSAGE_TIME_MS

    def change_map(self, door):
        self.current = self.get_map(door["target_map"])
        self.player.x, self.player.y = door["spawn_x"], door["spawn_y"]
        self.show(f"Entered {self.current.display_name}")

    # ---------- what happens when you move ----------
    def step(self, dx, dy):
        """Try to move one tile and react to whatever is there."""
        target = (self.player.x + dx, self.player.y + dy)
        tile = self.current.tile_at(*target)

        # Bumping into things you can interact with.
        if tile == "N":
            npc = self.current.npcs.get(target, {})
            self.show(f"{npc.get('id', 'NPC')}: [dialogue '{npc.get('dialogue_key', '?')}']")
            return
        if tile == "C":
            key = (self.current.name, *target)
            if key in self.opened_chests:
                self.show("The chest is empty.")
            else:
                self.opened_chests.add(key)
                self.show("You opened the chest! (item placeholder)")
            return

        if not self.player.try_move(dx, dy, self.current):
            return  # blocked by a wall, tree, water...

        here = (self.player.x, self.player.y)
        if tile == "D":
            self.change_map(self.current.doors[here])
        elif tile == "S":
            self.show("Game saved. (placeholder)")
        elif tile == "B" and self.current.boss:
            self.show(f"BOSS BATTLE: {self.current.boss['enemy_id']}! (placeholder)")
        elif tile == "g":
            enc = self.current.encounters
            if enc["enemy_pool"] and random.random() < enc["rate"]:
                self.show(f"Encounter! A wild {random.choice(enc['enemy_pool'])} appears!")

    # ---------- main loop ----------
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

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

    def draw(self):
        self.camera.follow(self.player.x, self.player.y, self.current)
        self.screen.fill((0, 0, 0))
        draw_map(self.screen, self.current, self.camera.x, self.camera.y, self.opened_chests)
        draw_player(self.screen, self.player.x, self.player.y, self.camera.x, self.camera.y)

        # Map name label (top-left)
        label = self.font.render(self.current.display_name, True, (255, 255, 255))
        bg = pygame.Rect(8, 8, label.get_width() + 16, label.get_height() + 10)
        pygame.draw.rect(self.screen, (0, 0, 0), bg)
        pygame.draw.rect(self.screen, (255, 255, 255), bg, 2)
        self.screen.blit(label, (16, 13))

        # Message box (bottom)
        if self.message and pygame.time.get_ticks() < self.message_until:
            box = pygame.Rect(20, settings.SCREEN_HEIGHT - 70, settings.SCREEN_WIDTH - 40, 50)
            pygame.draw.rect(self.screen, (0, 0, 0), box)
            pygame.draw.rect(self.screen, (255, 255, 255), box, 2)
            text = self.font.render(self.message, True, (255, 255, 255))
            self.screen.blit(text, (box.x + 14, box.y + 15))

    def run(self):
        running = True
        while running:
            running = self.handle_input()
            self.draw()
            pygame.display.flip()
            self.clock.tick(settings.FPS)
        pygame.quit()


if __name__ == "__main__":
    Game().run()
