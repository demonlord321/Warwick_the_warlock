"""Draws maps with simple coloured shapes. No image files needed."""
import pygame

from settings import TILE_SIZE
from tiles import tile_color

GRID_LINE = (0, 0, 0, 40)


def draw_tile(surface, char, px, py, opened=False):
    """Draw one tile with its top-left corner at pixel (px, py)."""
    s = TILE_SIZE
    rect = pygame.Rect(px, py, s, s)
    pygame.draw.rect(surface, tile_color(char), rect)
    cx, cy = px + s // 2, py + s // 2

    if char == "#":
        pygame.draw.rect(surface, (70, 70, 80), rect, 2)
    elif char == "g":
        for dx in (6, 16, 25):  # little grass tufts
            pygame.draw.line(surface, (50, 120, 45), (px + dx, py + 22), (px + dx + 3, py + 14), 2)
    elif char == "T":
        pygame.draw.rect(surface, (110, 75, 40), (cx - 3, py + 20, 6, 10))
        pygame.draw.circle(surface, (35, 100, 40), (cx, py + 14), 12)
    elif char == "~":
        pygame.draw.line(surface, (120, 170, 240), (px + 5, cy), (px + 13, cy - 3), 2)
        pygame.draw.line(surface, (120, 170, 240), (px + 17, cy + 5), (px + 26, cy + 2), 2)
    elif char == "D":
        pygame.draw.rect(surface, (90, 55, 25), rect.inflate(-6, -2), 0)
        pygame.draw.circle(surface, (230, 200, 60), (px + s - 9, cy), 3)
    elif char == "N":
        pygame.draw.circle(surface, (230, 120, 60), (cx, cy - 6), 7)   # head
        pygame.draw.rect(surface, (180, 60, 60), (cx - 7, cy + 1, 14, 12))  # body
    elif char == "C":
        colour = (90, 60, 30) if opened else (150, 95, 35)
        pygame.draw.rect(surface, colour, (px + 5, py + 9, s - 10, s - 15))
        if not opened:
            pygame.draw.rect(surface, (230, 200, 60), (px + 5, cy - 1, s - 10, 3))
    elif char == "S":
        points = [(cx, py + 5), (px + s - 6, cy), (cx, py + s - 5), (px + 6, cy)]
        pygame.draw.polygon(surface, (255, 230, 70), points)
        pygame.draw.polygon(surface, (200, 160, 20), points, 2)
    elif char == "B":
        pygame.draw.circle(surface, (170, 30, 40), (cx, cy), 13)
        pygame.draw.circle(surface, (255, 255, 255), (cx - 5, cy - 3), 3)
        pygame.draw.circle(surface, (255, 255, 255), (cx + 5, cy - 3), 3)


def draw_map(surface, game_map, cam_x=0, cam_y=0, opened_chests=()):
    """Draw only the tiles that are visible through the camera."""
    view_w, view_h = surface.get_size()
    first_x = max(0, cam_x // TILE_SIZE)
    first_y = max(0, cam_y // TILE_SIZE)
    last_x = min(game_map.width, (cam_x + view_w) // TILE_SIZE + 1)
    last_y = min(game_map.height, (cam_y + view_h) // TILE_SIZE + 1)

    for y in range(first_y, last_y):
        for x in range(first_x, last_x):
            char = game_map.tile_at(x, y)
            opened = (game_map.name, x, y) in opened_chests
            draw_tile(surface, char, x * TILE_SIZE - cam_x, y * TILE_SIZE - cam_y, opened)


def draw_player(surface, tile_x, tile_y, cam_x, cam_y):
    cx = tile_x * TILE_SIZE - cam_x + TILE_SIZE // 2
    cy = tile_y * TILE_SIZE - cam_y + TILE_SIZE // 2
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 12)
    pygame.draw.circle(surface, (40, 80, 220), (cx, cy), 9)
