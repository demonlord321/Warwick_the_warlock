"""The tile legend: one character per tile.

Each entry: char -> (name, colour, solid)
  solid=True means the player cannot walk onto that tile.
"""

TILES = {
    "#": ("wall",         (90, 90, 100),   True),
    ".": ("floor",        (200, 185, 150), False),
    "P": ("player_start", (200, 185, 150), False),  # drawn as floor
    "N": ("npc",          (200, 185, 150), True),   # talk by walking into them
    "D": ("door",         (140, 90, 40),   False),  # step on it to change map
    "g": ("grass",        (90, 170, 80),   False),  # random-encounter tile
    "T": ("tree",         (60, 130, 60),   True),
    "~": ("water",        (50, 110, 200),  True),
    "S": ("save_point",   (200, 185, 150), False),  # step on it to save
    "C": ("chest",        (200, 185, 150), True),   # open by walking into it
    "B": ("boss_trigger", (200, 185, 150), False),  # step on it to start the boss
}


# Optional per-map colour palettes, picked with "theme" in a map's JSON.
# Only the base colours change; walkability never does.
_SLUMS_FLOOR = (78, 74, 72)        # wet cobbles
THEMES = {
    "slums": {
        "#": (40, 37, 44),         # soot-black brick
        ".": _SLUMS_FLOOR,
        "P": _SLUMS_FLOOR, "N": _SLUMS_FLOOR, "S": _SLUMS_FLOOR,
        "C": _SLUMS_FLOOR, "B": _SLUMS_FLOOR,
        "D": (70, 48, 30),         # rotten timber gate
        "g": (72, 60, 48),         # rubble and refuse (still the encounter tile)
        "~": (52, 66, 58),         # stagnant puddles / open sewer
        "T": (55, 50, 45),
    },
}


def is_solid(char):
    """Unknown characters are treated as solid so mistakes are easy to spot."""
    return TILES.get(char, ("unknown", (255, 0, 255), True))[2]


def tile_color(char, theme=None):
    palette = THEMES.get(theme, {})
    if char in palette:
        return palette[char]
    return TILES.get(char, ("unknown", (255, 0, 255), True))[1]
