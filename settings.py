"""Global settings for the demo. Change numbers here, not all over the code."""
import os

TILE_SIZE = 32                 # pixels per tile
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
MOVE_DELAY_MS = 140            # how often the player steps while a key is held

ROOT = os.path.dirname(os.path.abspath(__file__))
MAPS_ROOT = os.path.join(ROOT, "maps")
DATA_ROOT = os.path.join(ROOT, "data")   # data/<chapter>/dialogue.json, intro.json, ...
CHAPTER = "chapter1"           # which maps/<folder> and data/<folder> the game plays
MAPS_DIR = os.path.join(MAPS_ROOT, CHAPTER)
START_MAP = "slums1"           # map in that folder with the single 'P' tile

# Dialogue box, drawn along the bottom of the window.
DIALOGUE_BOX_MARGIN = 16
DIALOGUE_BOX_HEIGHT = 140
DIALOGUE_BORDER = 3
DIALOGUE_PAD = 18
DIALOGUE_LINE_GAP = 6
DIALOGUE_CHAR_MS = 32          # typewriter: one new character per this many ms
DIALOGUE_BG = (0, 0, 0)
DIALOGUE_BORDER_COLOR = (255, 255, 255)
DIALOGUE_TEXT_COLOR = (255, 255, 255)

# Title screen. Dark, like the slums, with the options drawn on top.
MENU_BG = (18, 14, 16)
MENU_BAND = (32, 26, 28)          # alley walls along the sides
MENU_TITLE_COLOR = (232, 220, 200)
MENU_SELECTED = (255, 255, 255)
MENU_NORMAL = (190, 180, 170)
MENU_DISABLED = (96, 90, 88)
MENU_TITLE_SIZE = 64
MENU_OPTION_SIZE = 36
INTRO_TITLE_SIZE = 48          # chapter card, a bit smaller than the game title
