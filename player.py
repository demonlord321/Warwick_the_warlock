"""The player: a position on the tile grid."""


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def try_move(self, dx, dy, game_map):
        """Move one tile if the target is walkable. Returns True if we moved."""
        new_x, new_y = self.x + dx, self.y + dy
        if game_map.is_walkable(new_x, new_y):
            self.x, self.y = new_x, new_y
            return True
        return False
