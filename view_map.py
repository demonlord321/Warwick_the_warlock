"""Tiny standalone map viewer: draws one map as coloured squares.

Usage:
    python view_map.py slums1                 # open a window (arrow keys scroll)
    python view_map.py slums1 --save out.png  # save the whole map as a PNG
    python view_map.py parked/town            # maps in other folders: <folder>/<name>

Only needs pygame and the maps/ folder - it does not import the game code.
"""
import json
import os
import sys

import pygame

TILE = 32
MAPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")
COLOURS = {
    "#": (90, 90, 100), ".": (200, 185, 150), "P": (60, 200, 255),
    "N": (230, 120, 60), "D": (140, 90, 40), "g": (90, 170, 80),
    "T": (35, 100, 40), "~": (50, 110, 200), "S": (255, 230, 70),
    "C": (150, 95, 35), "B": (170, 30, 40),
}
# Darker palette for maps whose JSON says "theme": "slums".
THEME_COLOURS = {
    "slums": {"#": (40, 37, 44), ".": (78, 74, 72), "D": (70, 48, 30),
              "g": (72, 60, 48), "~": (52, 66, 58)},
}


def find(name):
    """'slums1' searches every folder in maps/ (chapter1 first); 'parked/town' is exact."""
    if os.path.exists(os.path.join(MAPS_DIR, name + ".txt")):
        return os.path.join(MAPS_DIR, name)
    for folder in sorted(os.listdir(MAPS_DIR)):
        path = os.path.join(MAPS_DIR, folder, name)
        if os.path.exists(path + ".txt"):
            return path
    sys.exit(f"map '{name}' not found under {MAPS_DIR}")


def load(name):
    base = find(name)
    with open(base + ".txt", encoding="utf-8") as f:
        rows = [line.rstrip("\r\n") for line in f if line.strip()]
    with open(base + ".json", encoding="utf-8") as f:
        meta = json.load(f)
    return rows, meta


def draw(rows, theme=None):
    colours = {**COLOURS, **THEME_COLOURS.get(theme, {})}
    surf = pygame.Surface((len(rows[0]) * TILE, len(rows) * TILE))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            rect = (x * TILE, y * TILE, TILE, TILE)
            pygame.draw.rect(surf, colours.get(ch, (255, 0, 255)), rect)
            pygame.draw.rect(surf, (0, 0, 0), rect, 1)
    return surf


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    name = sys.argv[1]
    rows, meta = load(name)
    pygame.init()
    print(f"{name}: {len(rows[0])}x{len(rows)} tiles, {len(meta.get('doors', []))} doors")

    if "--save" in sys.argv:
        out = sys.argv[sys.argv.index("--save") + 1]
        pygame.image.save(draw(rows, meta.get("theme")), out)
        print("saved", out)
        return

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption(f"view_map: {name}")
    image = draw(rows, meta.get("theme"))
    cam_x = cam_y = 0
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return
        keys = pygame.key.get_pressed()
        cam_x += (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 8
        cam_y += (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 8
        cam_x = max(0, min(cam_x, max(0, image.get_width() - 800)))
        cam_y = max(0, min(cam_y, max(0, image.get_height() - 600)))
        screen.fill((0, 0, 0))
        screen.blit(image, (-cam_x, -cam_y))
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
