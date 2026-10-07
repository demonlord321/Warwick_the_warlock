"""A camera that follows the player and stops at the map edges."""
from settings import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    def __init__(self, view_w=SCREEN_WIDTH, view_h=SCREEN_HEIGHT):
        self.view_w = view_w
        self.view_h = view_h
        self.x = 0  # top-left corner of the view, in map pixels
        self.y = 0

    def _axis(self, target, map_size, view_size):
        if map_size <= view_size:
            # Map is smaller than the window: centre it (negative offset).
            return -(view_size - map_size) // 2
        # Keep the target in the middle, but clamp to the map edges.
        return max(0, min(target - view_size // 2, map_size - view_size))

    def follow(self, tile_x, tile_y, game_map):
        map_w, map_h = game_map.pixel_size
        centre_x = tile_x * TILE_SIZE + TILE_SIZE // 2
        centre_y = tile_y * TILE_SIZE + TILE_SIZE // 2
        self.x = self._axis(centre_x, map_w, self.view_w)
        self.y = self._axis(centre_y, map_h, self.view_h)
