import random

from dungeon_autobattler.engine import GameMap, Position, TileType


class DungeonGenerator:
    """
    Klasse zur prozeduralen Generierung von Dungeons.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def generate(self, wall_density: float = 0.3) -> GameMap:
        """
        Generiert eine Map mit zufälligen Wänden.
        Stellt sicher, dass die Ränder Mauern sind.
        """
        game_map = GameMap(self.width, self.height)

        # Zuerst alles mit Boden füllen (ist Standard in GameMap)
        # Dann zufällig Wände setzen
        for y in range(self.height):
            for x in range(self.width):
                # Ränder sind immer Wände
                if (
                    x == 0
                    or y == 0
                    or x == self.width - 1
                    or y == self.height - 1
                    or random.random() < wall_density
                ):
                    game_map.set_tile(x, y, TileType.WALL)

        return game_map

    def generate_random_walk(self, steps: int = 200) -> GameMap:
        """
        Generiert eine Map mittels Random Walk, um sicherzustellen, dass Wege verbunden sind.
        """
        game_map = GameMap(self.width, self.height)
        # Alles als Wand initialisieren
        for y in range(self.height):
            for x in range(self.width):
                game_map.set_tile(x, y, TileType.WALL)

        # Startpunkt
        x, y = self.width // 2, self.height // 2
        game_map.set_tile(x, y, TileType.EMPTY)

        for _ in range(steps):
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            new_x, new_y = x + dx, y + dy

            if 1 <= new_x < self.width - 1 and 1 <= new_y < self.height - 1:
                x, y = new_x, new_y
                game_map.set_tile(x, y, TileType.EMPTY)

        return game_map

    def find_free_tile(self, game_map: GameMap) -> Position:
        """Findet ein zufälliges freies Feld auf der Map."""
        free_tiles = []
        for y in range(1, game_map.height - 1):
            for x in range(1, game_map.width - 1):
                if game_map.tiles[y][x] == TileType.EMPTY:
                    free_tiles.append(Position(x, y))

        if not free_tiles:
            # Fallback: Mitte erzwingen
            mid_x, mid_y = game_map.width // 2, game_map.height // 2
            game_map.set_tile(mid_x, mid_y, TileType.EMPTY)
            return Position(mid_x, mid_y)

        return random.choice(free_tiles)
