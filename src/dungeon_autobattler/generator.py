"""Prozedurale Generierung der Makro-Welt und der einzelnen Dungeon-Chunks."""

import random

from dungeon_autobattler.engine import GameMap, Position, TileType


class DungeonGenerator:
    """
    Klasse zur prozeduralen Generierung von Dungeons und Makro-Welten.

    Attributes:
        width: Breite (in Feldern) eines einzelnen Chunks.
        height: Höhe (in Feldern) eines einzelnen Chunks.
    """

    def __init__(self, width: int, height: int):
        """Legt die Größe fest, in der spätere Chunks generiert werden.

        Args:
            width: Breite eines Chunks in Feldern.
            height: Höhe eines Chunks in Feldern.
        """
        self.width = width
        self.height = height

    def generate_macro_grid(
        self, width_chunks: int = 8, height_chunks: int = 8
    ) -> list[list[dict[str, bool]]]:
        """
        Generiert einen Spanning-Tree über das Grid, um sicherzustellen,
        dass alle Chunks lückenlos miteinander verbunden und erreichbar sind.

        Der Algorithmus ist ein randomisierter, iterativer Depth-First-Search
        (Backtracking), der für jeden Chunk speichert, in welche
        Himmelsrichtungen ("N", "S", "E", "W") eine Verbindung zum
        Nachbar-Chunk existiert.

        Args:
            width_chunks: Anzahl der Chunks in horizontaler Richtung.
            height_chunks: Anzahl der Chunks in vertikaler Richtung.

        Returns:
            Ein zweidimensionales Grid (Zeile für Zeile), in dem jedes
            Feld ein Dictionary mit den Schlüsseln ``"N"``, ``"S"``,
            ``"E"``, ``"W"`` (offene Verbindungen) sowie ``"visited"``
            enthält.

        Examples:
            Mit einem festen Seed ist das Ergebnis deterministisch, jeder
            Chunk eines 2x2-Grids wird besucht und jeder Chunk hat
            mindestens eine offene Verbindung zu einem Nachbarn:

            >>> random.seed(42)
            >>> generator = DungeonGenerator(10, 10)
            >>> grid = generator.generate_macro_grid(2, 2)
            >>> len(grid), len(grid[0])
            (2, 2)
            >>> all(cell["visited"] for row in grid for cell in row)
            True
            >>> any(any(cell[d] for d in "NSEW") for row in grid for cell in row)
            True
        """
        grid = [
            {"N": False, "S": False, "E": False, "W": False, "visited": False}
            for _ in range(width_chunks * height_chunks)
        ]

        def get_idx(x: int, y: int) -> int:
            return y * width_chunks + x

        stack = [(0, 0)]
        grid[get_idx(0, 0)]["visited"] = True

        while stack:
            cx, cy = stack[-1]
            unvisited_neighbors = []
            directions = [
                ("N", 0, -1, "S"),
                ("S", 0, 1, "N"),
                ("W", -1, 0, "E"),
                ("E", 1, 0, "W"),
            ]

            for d, dx, dy, op in directions:
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < width_chunks
                    and 0 <= ny < height_chunks
                    and not grid[get_idx(nx, ny)]["visited"]
                ):
                    unvisited_neighbors.append((d, nx, ny, op))

            if unvisited_neighbors:
                d, nx, ny, op = random.choice(unvisited_neighbors)
                grid[get_idx(cx, cy)][d] = True
                grid[get_idx(nx, ny)][op] = True
                grid[get_idx(nx, ny)]["visited"] = True
                stack.append((nx, ny))
            else:
                stack.pop()

        return [
            [grid[get_idx(x, y)] for x in range(width_chunks)]
            for y in range(height_chunks)
        ]

    def generate_chunk(
        self,
        open_n: bool,
        open_s: bool,
        open_w: bool,
        open_e: bool,
        steps: int = 200,
    ) -> GameMap:
        """
        Generiert einen einzelnen Chunk und bricht Wege zu den offenen Himmelsrichtungen durch.

        Zunächst wird die gesamte Karte mit Wänden gefüllt. Anschließend
        gräbt ein "Random Walk", ausgehend vom Zentrum, begehbare Felder
        frei. Zuletzt werden für jede als offen markierte Himmelsrichtung
        gerade Gänge bis zum Kartenrand freigeräumt, damit benachbarte
        Chunks stets erreichbar sind.

        Args:
            open_n: Ob eine Verbindung nach Norden freigeschaltet wird.
            open_s: Ob eine Verbindung nach Süden freigeschaltet wird.
            open_w: Ob eine Verbindung nach Westen freigeschaltet wird.
            open_e: Ob eine Verbindung nach Osten freigeschaltet wird.
            steps: Anzahl der Schritte des Random Walk.

        Returns:
            Die generierte ``GameMap`` des Chunks.

        Examples:
            Das Zentrum eines Chunks ist nach der Generierung immer begehbar:

            >>> random.seed(1)
            >>> generator = DungeonGenerator(9, 9)
            >>> chunk = generator.generate_chunk(True, False, False, False, steps=50)
            >>> chunk.tiles[4][4]
            <TileType.EMPTY: '.'>

            Bei geöffneter Nordverbindung ist das obere Randfeld über der
            Mitte ebenfalls begehbar:

            >>> chunk.tiles[0][4]
            <TileType.EMPTY: '.'>
        """
        game_map = GameMap(self.width, self.height)

        for y in range(self.height):
            for x in range(self.width):
                game_map.set_tile(x, y, TileType.WALL)

        x, y = self.width // 2, self.height // 2
        game_map.set_tile(x, y, TileType.EMPTY)

        for _ in range(steps):
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            new_x, new_y = x + dx, y + dy

            if 1 <= new_x < self.width - 1 and 1 <= new_y < self.height - 1:
                x, y = new_x, new_y
                game_map.set_tile(x, y, TileType.EMPTY)

        mid_x, mid_y = self.width // 2, self.height // 2

        if open_n:
            for ty in range(mid_y, -1, -1):
                game_map.set_tile(mid_x, ty, TileType.EMPTY)
        if open_s:
            for ty in range(mid_y, self.height):
                game_map.set_tile(mid_x, ty, TileType.EMPTY)
        if open_w:
            for tx in range(mid_x, -1, -1):
                game_map.set_tile(tx, mid_y, TileType.EMPTY)
        if open_e:
            for tx in range(mid_x, self.width):
                game_map.set_tile(tx, mid_y, TileType.EMPTY)

        return game_map

    def find_free_tile(self, game_map: GameMap) -> Position:
        """Findet ein zufälliges freies Feld auf der Map.

        Sucht unter allen inneren (nicht am Rand liegenden) Feldern nach
        begehbaren (``TileType.EMPTY``) Feldern und wählt eines davon
        zufällig aus. Existiert kein freies Feld, wird das Zentrum der
        Karte freigeräumt und zurückgegeben, damit stets eine gültige
        Position geliefert wird.

        Args:
            game_map: Die Karte, auf der gesucht werden soll.

        Returns:
            Eine begehbare ``Position`` innerhalb der Karte.

        Examples:
            >>> random.seed(7)
            >>> game_map = GameMap(5, 5)
            >>> for x in range(5):
            ...     for y in range(5):
            ...         game_map.set_tile(x, y, TileType.WALL)
            >>> game_map.set_tile(2, 2, TileType.EMPTY)
            >>> pos = DungeonGenerator(5, 5).find_free_tile(game_map)
            >>> pos
            Position(x=2, y=2)

            Gibt es kein freies Feld, wird eines im Zentrum erzeugt:

            >>> voll_belegt = GameMap(5, 5)
            >>> for x in range(5):
            ...     for y in range(5):
            ...         voll_belegt.set_tile(x, y, TileType.WALL)
            >>> pos = DungeonGenerator(5, 5).find_free_tile(voll_belegt)
            >>> pos
            Position(x=2, y=2)
            >>> voll_belegt.tiles[2][2]
            <TileType.EMPTY: '.'>
        """
        free_tiles = []
        for y in range(1, game_map.height - 1):
            for x in range(1, game_map.width - 1):
                if game_map.tiles[y][x] == TileType.EMPTY:
                    free_tiles.append(Position(x, y))

        if not free_tiles:
            mid_x, mid_y = game_map.width // 2, game_map.height // 2
            game_map.set_tile(mid_x, mid_y, TileType.EMPTY)
            return Position(mid_x, mid_y)

        return random.choice(free_tiles)
