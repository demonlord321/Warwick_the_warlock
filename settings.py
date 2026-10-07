"""Global settings for the demo. Change numbers here, not all over the code."""
import os

TILE_SIZE = 32                 # pixels per tile
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
MOVE_DELAY_MS = 140            # how often the player steps while a key is held

START_MAP = "town"             # map that contains the single 'P' tile
MAPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")
