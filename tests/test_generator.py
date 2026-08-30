import unittest

from dungeon_autobattler.engine import Position, TileType
from dungeon_autobattler.generator import DungeonGenerator


class TestDungeonGenerator(unittest.TestCase):
    def test_random_walk_connected(self) -> None:
        width, height = 20, 20
        generator = DungeonGenerator(width, height)
        # Ruft generiere Chunk auf, öffnet alle Himmelsrichtungen (N, S, W, O)
        game_map = generator.generate_chunk(True, True, True, True, steps=100)

        # Sicherstellen, dass Ränder (mit Ausnahme der Ausgänge in der Mitte) Mauern sind
        self.assertEqual(game_map.tiles[0][0], TileType.WALL)
        self.assertEqual(game_map.tiles[height - 1][width - 1], TileType.WALL)

        # Sicherstellen, dass es freie Felder gibt
        free_tiles = []
        for y in range(height):
            for x in range(width):
                if game_map.tiles[y][x] == TileType.EMPTY:
                    free_tiles.append((x, y))

        self.assertGreater(len(free_tiles), 0)

    def test_find_free_tile(self) -> None:
        width, height = 10, 10
        generator = DungeonGenerator(width, height)
        # Erstellt geschlossenen Raum ohne Ausgänge
        game_map = generator.generate_chunk(
            False, False, False, False, steps=20
        )

        pos = generator.find_free_tile(game_map)
        self.assertIsInstance(pos, Position)
        self.assertEqual(game_map.tiles[pos.y][pos.x], TileType.EMPTY)


if __name__ == "__main__":
    unittest.main()
