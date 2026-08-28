"""
Kernlogik des Spiels inklusive Map-Verwaltung und Bewegung.
"""

import json
import math
import random
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Callable, Optional

from dungeon_autobattler.models import (
    Character,
    DungeonError,
    InvalidMoveError,
    Item,
    LoadGameError,
    Rarity,
    SaveGameError,
)


class TileType(Enum):
    """Typen von Feldern auf der Map."""

    EMPTY = "."
    WALL = "#"
    ENEMY = "E"
    BOSS = "B"
    EXIT = "X"
    SHOP = "S"


@dataclass
class Position:
    """Repräsentiert eine Koordinate auf der Map."""

    x: int
    y: int

    def __add__(self, other: "Position") -> "Position":
        return Position(self.x + other.x, self.y + other.y)


class GameMap:
    """
    Verwaltet die 2D-Karte des Dungeons.

    Attributes:
        width: Breite der Map
        height: Höhe der Map
        tiles: 2D-Liste der TileTypes
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.tiles = [
            [TileType.EMPTY for _ in range(width)] for _ in range(height)
        ]

    def is_walkable(self, pos: Position) -> bool:
        """Prüft, ob eine Position betreten werden kann."""
        if not (0 <= pos.x < self.width and 0 <= pos.y < self.height):
            return False
        return self.tiles[pos.y][pos.x] != TileType.WALL

    def set_tile(self, x: int, y: int, tile_type: TileType) -> None:
        """Setzt einen TileType an einer bestimmten Position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = tile_type


class Engine:
    """
    Hauptspiel-Engine, die Spieler und Map verbindet.

    Attributes:
        player: Das Character-Objekt des Spielers
        player_pos: Aktuelle Position auf der Map
        game_map: Die aktuelle Map
    """

    def __init__(
        self,
        player: Character,
        game_map: GameMap,
        start_pos: Position,
        difficulty: float = 1.0,
    ) -> None:
        self.player = player
        self.game_map = game_map
        self.player_pos = start_pos
        self.difficulty = difficulty
        self.enemies: dict[tuple[int, int], Character] = {}
        self.shop_items: list[Item] = []
        self.combat_log: list[str] = []

    def spawn_enemy(self, x: int, y: int, enemy: Character) -> None:
        """Platziert einen Gegner auf der Map."""
        self.game_map.set_tile(x, y, TileType.ENEMY)
        self.enemies[(x, y)] = enemy

    def move_player(
        self,
        dx: int,
        dy: int,
        ui_callback: Optional[Callable[[Character], None]] = None,
    ) -> bool:
        """
        Versucht den Spieler zu bewegen.
        """
        if abs(dx) > 1 or abs(dy) > 1:
            raise InvalidMoveError("Spieler kann nur maximal 1 Feld ziehen.")
        if dx == 0 and dy == 0:
            return True

        new_pos = self.player_pos + Position(dx, dy)
        if self.game_map.is_walkable(new_pos):
            tile = self.game_map.tiles[new_pos.y][new_pos.x]
            if tile == TileType.ENEMY:
                enemy = self.enemies.get((new_pos.x, new_pos.y))
                if enemy:
                    won = self.resolve_combat(enemy, ui_callback)
                    if won:
                        # Belohnungen
                        self.player.gold += enemy.gold
                        self.player.gain_xp(25)

                        # Gegner besiegt, Feld wird leer
                        self.game_map.set_tile(
                            new_pos.x, new_pos.y, TileType.EMPTY
                        )
                        del self.enemies[(new_pos.x, new_pos.y)]
                        self.player_pos = new_pos
                        return True
                    return False  # Spieler hat verloren/ist tot
            elif tile == TileType.SHOP:
                if self.shop_items:
                    item = self.shop_items[0]
                    cost = 20
                    if self.player.gold >= cost:
                        self.player.gold -= cost
                        self.player.items.append(item)
                        self.shop_items.pop(0)

                self.player_pos = new_pos
                return True
            elif tile == TileType.EXIT:
                print("Sieg! Du hast den Ausgang erreicht.")
                self.player_pos = new_pos
                return True

            self.player_pos = new_pos
            return True
        return False

    def resolve_combat(
        self,
        enemy: Character,
        ui_callback: Optional[Callable[[Character], None]] = None,
    ) -> bool:
        """
        Führt einen automatisierten Kampf Schritt für Schritt durch.
        """
        if not self.player.is_alive():
            raise DungeonError("Ein toter Spieler kann nicht kämpfen.")
        if not enemy.is_alive():
            raise DungeonError("Gegner ist bereits tot.")

        self.combat_log.append(f"--- Kampf gegen {enemy.name} ---")
        if ui_callback:
            ui_callback(enemy)

        while self.player.is_alive() and enemy.is_alive():
            # Spieler greift an
            self._execute_attack(self.player, enemy)
            if ui_callback:
                ui_callback(enemy)

            if not enemy.is_alive():
                break

            # Gegner greift an
            self._execute_attack(enemy, self.player)
            if ui_callback:
                ui_callback(enemy)

        return self.player.is_alive()

    def _execute_attack(self, attacker: Character, defender: Character) -> None:
        att = attacker.current_stats
        deff = defender.current_stats

        evasion_term = math.pow(deff.evasion_rating / 4.0, 0.8)
        hit_chance = (
            att.accuracy / (att.accuracy + evasion_term)
            if (att.accuracy + evasion_term) > 0
            else 1.0
        )

        hit_chance = max(0.05, min(1.0, hit_chance))

        if random.random() > hit_chance:
            self.combat_log.append(f"{attacker.name} verfehlt {defender.name}!")
            return

        # Kritischer Treffer berechnen
        raw_damage = att.ad
        is_crit = False
        if random.random() < att.crit_chance:
            raw_damage = int(raw_damage * att.crit_multiplier)
            is_crit = True

        damage_reduction = 0.0
        if (deff.armor + 5.0 * raw_damage) > 0:
            damage_reduction = deff.armor / (deff.armor + 5.0 * raw_damage)

        damage_reduction = min(0.90, damage_reduction)

        actual_damage = max(1, int(raw_damage * (1.0 - damage_reduction)))
        defender.take_damage(actual_damage)

        crit_text = " (KRITISCH!)" if is_crit else ""
        self.combat_log.append(
            f"{attacker.name} trifft für {actual_damage} Schaden{crit_text}"
        )

    def save_game(self, filepath: str) -> None:
        """Speichert den aktuellen Spielzustand als JSON."""
        data = {
            "player": asdict(self.player),
            "player_pos": asdict(self.player_pos),
            "difficulty": self.difficulty,
            "map": {
                "width": self.game_map.width,
                "height": self.game_map.height,
                "tiles": [
                    [t.value for t in row] for row in self.game_map.tiles
                ],
            },
            "enemies": [
                {"x": pos[0], "y": pos[1], "data": asdict(enemy)}
                for pos, enemy in self.enemies.items()
            ],
        }
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except OSError as e:
            raise SaveGameError(f"Fehler beim Speichern: {e}") from e

    @classmethod
    def load_game(cls, filepath: str) -> "Engine":
        """Lädt einen Spielzustand aus einer JSON-Datei."""
        from dungeon_autobattler.models import Item, Stats

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Spieler rekonstruieren
            p_data = data["player"]
            p_stats = Stats(**p_data["base_stats"])
            player = Character(
                name=p_data["name"],
                base_stats=p_stats,
                items=[
                    Item(
                        i["name"],
                        Rarity(i["rarity"]),
                        Stats(**i["bonus_stats"]),
                    )
                    for i in p_data["items"]
                ]
                if "items" in p_data
                else [],
                gold=p_data.get("gold", 0),
                xp=p_data.get("xp", 0),
                level=p_data.get("level", 1),
            )

            # Map rekonstruieren
            m_data = data["map"]
            g_map = GameMap(m_data["width"], m_data["height"])
            g_map.tiles = [
                [TileType(t) for t in row] for row in m_data["tiles"]
            ]

            # Engine erstellen
            pos = Position(**data["player_pos"])
            difficulty = data.get("difficulty", 1.0)
            engine = cls(player, g_map, pos, difficulty)

            # Gegner rekonstruieren
            from dungeon_autobattler.models import Enemy, EnemyType

            for e_entry in data["enemies"]:
                e_data = e_entry["data"]
                e_stats = Stats(**e_data["base_stats"])
                enemy = Enemy(
                    name=e_data["name"],
                    base_stats=e_stats,
                    items=[],
                    gold=e_data.get("gold", 0),
                    xp=e_data.get("xp", 0),
                    level=e_data.get("level", 1),
                    enemy_type=EnemyType(
                        e_data.get("enemy_type", EnemyType.GOBLIN.value)
                    )
                    if isinstance(e_data.get("enemy_type"), str)
                    else EnemyType.GOBLIN,
                    loot_value=e_data.get("loot_value", 1.0),
                )
                engine.enemies[(e_entry["x"], e_entry["y"])] = enemy

            return engine
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            raise LoadGameError(f"Fehler beim Laden: {e}") from e
