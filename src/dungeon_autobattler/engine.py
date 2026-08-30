"""
Kernlogik des Spiels inklusive Map-Verwaltung, Kampfabwicklung und Spielstandsverwaltung.
"""

import json
import math
import random
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import Enum

from dungeon_autobattler.models import (
    Character,
    DungeonError,
    EquipmentSlot,
    InvalidMoveError,
    Item,
    LoadGameError,
    Rarity,
    SaveGameError,
    Stats,
)


class TileType(Enum):
    """Typen von Feldern auf der Map."""

    EMPTY = "."
    WALL = "#"
    ENEMY = "E"
    BOSS = "B"
    EXIT = "X"
    SHOP = "S"
    CHEST = "C"
    LOCKED_CHEST = "L"


@dataclass
class Position:
    """Repräsentiert eine zweidimensionale Koordinate auf der Map."""

    x: int
    y: int

    def __add__(self, other: "Position") -> "Position":
        return Position(self.x + other.x, self.y + other.y)


class GameMap:
    """
    Verwaltet das Grid und die Kollisionen eines Dungeons (Chunk).
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.tiles = [
            [TileType.EMPTY for _ in range(width)] for _ in range(height)
        ]

    def is_walkable(self, pos: Position) -> bool:
        if not (0 <= pos.x < self.width and 0 <= pos.y < self.height):
            return False
        return self.tiles[pos.y][pos.x] != TileType.WALL

    def set_tile(self, x: int, y: int, tile_type: TileType) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = tile_type


class Engine:
    """
    Hauptspiel-Engine, die nun mit einer Macro-Welt (Grid aus Chunks) arbeitet.
    """

    def __init__(
        self,
        player: Character,
        world_chunks: list[list[GameMap]],
        start_chunk_x: int,
        start_chunk_y: int,
        start_pos: Position,
        difficulty: float = 1.0,
    ) -> None:
        self.player = player
        self.world_chunks = world_chunks
        self.chunk_x = start_chunk_x
        self.chunk_y = start_chunk_y
        self.game_map = world_chunks[start_chunk_y][start_chunk_x]
        self.player_pos = start_pos
        self.difficulty = difficulty
        self.enemies: dict[tuple[int, int, int, int], Character] = {}
        self.shop_items: list[Item] = []
        self.combat_log: list[str] = []

    def spawn_enemy(
        self, cx: int, cy: int, x: int, y: int, enemy: Character
    ) -> None:
        """Platziert einen Gegner im globalen Grid."""
        self.world_chunks[cy][cx].set_tile(x, y, TileType.ENEMY)
        self.enemies[(cx, cy, x, y)] = enemy

    def move_player(
        self,
        dx: int,
        dy: int,
        ui_callback: Callable[[Character], None] | None = None,
    ) -> bool:
        """
        Verarbeitet die Fortbewegung und wechselt die Chunks an den Rändern der Map.
        """
        if abs(dx) > 1 or abs(dy) > 1:
            raise InvalidMoveError("Spieler kann nur maximal 1 Feld ziehen.")
        if dx == 0 and dy == 0:
            return True

        new_pos = self.player_pos + Position(dx, dy)
        chunk_dx, chunk_dy = 0, 0

        # Out-of-bounds Check für Chunk-Transition
        if new_pos.x < 0:
            chunk_dx = -1
            new_pos.x = self.game_map.width - 1
        elif new_pos.x >= self.game_map.width:
            chunk_dx = 1
            new_pos.x = 0
        elif new_pos.y < 0:
            chunk_dy = -1
            new_pos.y = self.game_map.height - 1
        elif new_pos.y >= self.game_map.height:
            chunk_dy = 1
            new_pos.y = 0

        if chunk_dx != 0 or chunk_dy != 0:
            new_cx = self.chunk_x + chunk_dx
            new_cy = self.chunk_y + chunk_dy

            if not (
                0 <= new_cx < len(self.world_chunks[0])
                and 0 <= new_cy < len(self.world_chunks)
            ):
                return False

            if not self.world_chunks[new_cy][new_cx].is_walkable(new_pos):
                return False

            self.chunk_x = new_cx
            self.chunk_y = new_cy
            self.game_map = self.world_chunks[new_cy][new_cx]
            self.player_pos = new_pos
            return True

        if self.game_map.is_walkable(new_pos):
            tile = self.game_map.tiles[new_pos.y][new_pos.x]

            if tile in (TileType.ENEMY, TileType.BOSS):
                enemy = self.enemies.get(
                    (self.chunk_x, self.chunk_y, new_pos.x, new_pos.y)
                )
                if enemy:
                    won = self.resolve_combat(enemy, ui_callback)
                    if won:
                        self.player.gold += enemy.gold
                        self.player.gain_xp(25)

                        if tile == TileType.BOSS:
                            boss_key = Item(
                                name="Boss-Schlüssel",
                                rarity=Rarity.EPIC,
                                bonus_stats=Stats(
                                    hp=0,
                                    max_hp=0,
                                    ad=0,
                                    armor=0,
                                    evasion_rating=0,
                                    accuracy=0,
                                ),
                                price=0,
                            )
                            self.player.items.append(boss_key)
                            self.combat_log.append(
                                "Boss besiegt! Boss-Schlüssel erbeutet."
                            )

                        self.game_map.set_tile(
                            new_pos.x, new_pos.y, TileType.EMPTY
                        )
                        del self.enemies[
                            (self.chunk_x, self.chunk_y, new_pos.x, new_pos.y)
                        ]
                        self.player_pos = new_pos
                        return True
                    return False

            elif tile == TileType.CHEST:
                if random.random() > 0.5:
                    gold_amount = random.randint(15, 40)
                    self.player.gold += gold_amount
                    self.combat_log.append(
                        f"Schatztruhe geöffnet! {gold_amount} Gold erhalten."
                    )
                else:
                    from dungeon_autobattler.item_factory import (
                        generate_random_equipment,
                    )

                    loot_item = generate_random_equipment()
                    self.player.items.append(loot_item)
                    self.combat_log.append(
                        f"Schatztruhe geöffnet! {loot_item.name} gefunden."
                    )

                self.game_map.set_tile(new_pos.x, new_pos.y, TileType.EMPTY)
                self.player_pos = new_pos
                return True

            elif tile == TileType.LOCKED_CHEST:
                key_item = next(
                    (
                        i
                        for i in self.player.items
                        if i.name == "Boss-Schlüssel"
                    ),
                    None,
                )
                if key_item:
                    self.player.items.remove(key_item)
                    from dungeon_autobattler.item_factory import (
                        generate_random_equipment,
                    )

                    epic_loot = generate_random_equipment(
                        forced_rarity=Rarity.EPIC
                    )
                    self.player.items.append(epic_loot)
                    self.player.gold += 150
                    self.combat_log.append(
                        f"Boss-Schlüssel benutzt! 150 Gold & {epic_loot.name} erbeutet."
                    )
                    self.game_map.set_tile(new_pos.x, new_pos.y, TileType.EMPTY)
                    self.player_pos = new_pos
                    return True
                else:
                    self.combat_log.append(
                        "Truhe verschlossen! Ein Boss-Schlüssel wird benötigt."
                    )
                    return False

            elif tile == TileType.SHOP:
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
        ui_callback: Callable[[Character], None] | None = None,
    ) -> bool:
        if not self.player.is_alive():
            raise DungeonError("Ein toter Spieler kann nicht kämpfen.")
        if not enemy.is_alive():
            raise DungeonError("Gegner ist bereits tot.")

        self.combat_log.append(f"--- Kampf gegen {enemy.name} ---")
        if ui_callback:
            ui_callback(enemy)

        while self.player.is_alive() and enemy.is_alive():
            self._execute_attack(self.player, enemy)
            if ui_callback:
                ui_callback(enemy)
            if not enemy.is_alive():
                break
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
        chunks_data = []
        for cy, row in enumerate(self.world_chunks):
            row_data = []
            for cx, chunk in enumerate(row):
                row_data.append(
                    {
                        "width": chunk.width,
                        "height": chunk.height,
                        "tiles": [[t.value for t in r] for r in chunk.tiles],
                    }
                )
            chunks_data.append(row_data)

        data = {
            "player": asdict(self.player),
            "chunk_x": self.chunk_x,
            "chunk_y": self.chunk_y,
            "player_pos": asdict(self.player_pos),
            "difficulty": self.difficulty,
            "world_chunks": chunks_data,
            "enemies": [
                {
                    "cx": pos[0],
                    "cy": pos[1],
                    "x": pos[2],
                    "y": pos[3],
                    "data": asdict(enemy),
                }
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
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            p_data = data["player"]
            p_stats = Stats(**p_data["base_stats"])
            player = Character(
                name=p_data["name"],
                base_stats=p_stats,
                items=[
                    Item(
                        name=i["name"],
                        rarity=Rarity(i["rarity"]),
                        bonus_stats=Stats(**i["bonus_stats"]),
                        slot=EquipmentSlot(i["slot"])
                        if i.get("slot")
                        else None,
                        is_consumable=i.get("is_consumable", False),
                        heal_amount=i.get("heal_amount", 0),
                        price=i.get("price", 20),
                    )
                    for i in p_data.get("items", [])
                ],
                gold=p_data.get("gold", 0),
                xp=p_data.get("xp", 0),
                level=p_data.get("level", 1),
            )

            if "equipment" in p_data:
                for slot_key, i_data in p_data["equipment"].items():
                    if i_data:
                        player.equipment[slot_key] = Item(
                            name=i_data["name"],
                            rarity=Rarity(i_data["rarity"]),
                            bonus_stats=Stats(**i_data["bonus_stats"]),
                            slot=EquipmentSlot(i_data["slot"])
                            if i_data.get("slot")
                            else None,
                            is_consumable=i_data.get("is_consumable", False),
                            heal_amount=i_data.get("heal_amount", 0),
                            price=i_data.get("price", 20),
                        )

            m_data = data["world_chunks"]
            world_chunks = []
            for row_data in m_data:
                row_chunks = []
                for c_data in row_data:
                    g_map = GameMap(c_data["width"], c_data["height"])
                    g_map.tiles = [
                        [TileType(t) for t in r] for r in c_data["tiles"]
                    ]
                    row_chunks.append(g_map)
                world_chunks.append(row_chunks)

            pos = Position(**data["player_pos"])
            c_x = data["chunk_x"]
            c_y = data["chunk_y"]
            difficulty = data.get("difficulty", 1.0)
            engine = cls(player, world_chunks, c_x, c_y, pos, difficulty)

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
                engine.enemies[
                    (e_entry["cx"], e_entry["cy"], e_entry["x"], e_entry["y"])
                ] = enemy

            return engine
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            raise LoadGameError(f"Fehler beim Laden: {e}") from e
