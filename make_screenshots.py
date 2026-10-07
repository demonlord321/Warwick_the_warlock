"""Saves a full-map overview PNG of every map to screenshots/ (works headless).

Usage:  SDL_VIDEODRIVER=dummy python make_screenshots.py
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

import settings  # noqa: E402
from map_loader import GameMap  # noqa: E402
from render import draw_map, draw_player  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
HEADER = 40


def overview(game_map, font, small):
    w, h = game_map.pixel_size
    surf = pygame.Surface((w, h + HEADER))
    surf.fill((20, 20, 30))
    title = f"{game_map.display_name}  ({game_map.name}.txt, {game_map.width}x{game_map.height})"
    surf.blit(font.render(title, True, (255, 255, 255)), (10, 10))

    tiles = pygame.Surface((w, h))
    draw_map(tiles, game_map)
    if game_map.player_start:
        draw_player(tiles, *game_map.player_start, 0, 0)
    # Label each door with where it goes.
    for (x, y), door in game_map.doors.items():
        label = small.render("-> " + door["target_map"], True, (255, 255, 255), (0, 0, 0))
        lx = min(max(0, x * settings.TILE_SIZE - 10), w - label.get_width())
        ly = y * settings.TILE_SIZE - 16 if y > 0 else (y + 1) * settings.TILE_SIZE + 2
        tiles.blit(label, (lx, ly))
    surf.blit(tiles, (0, HEADER))
    return surf


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(OUT_DIR, exist_ok=True)
    font, small = pygame.font.Font(None, 30), pygame.font.Font(None, 18)
    # Current chapter's maps go in screenshots/, other folders in screenshots/<folder>/.
    for folder in sorted(os.listdir(settings.MAPS_ROOT)):
        maps_dir = os.path.join(settings.MAPS_ROOT, folder)
        if not os.path.isdir(maps_dir):
            continue
        out_dir = OUT_DIR if maps_dir == settings.MAPS_DIR else os.path.join(OUT_DIR, folder)
        os.makedirs(out_dir, exist_ok=True)
        for f in sorted(os.listdir(maps_dir)):
            if f.endswith(".txt"):
                m = GameMap(f[:-4], maps_dir)
                path = os.path.join(out_dir, m.name + ".png")
                pygame.image.save(overview(m, font, small), path)
                print("saved", path)

    # One in-game frame to show the camera + map label.
    from game import Game
    game = Game()
    game.player.x, game.player.y = 20, 6
    game.show("Encounter! A wild sewer_rat appears!")
    game.draw()
    path = os.path.join(OUT_DIR, "gameplay_slums1.png")
    pygame.image.save(game.screen, path)
    print("saved", path)
    pygame.quit()


if __name__ == "__main__":
    main()
