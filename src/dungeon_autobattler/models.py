"""Hier befinden sich alle Datenmodelle"""

from dataclasses import dataclass
from enum import Enum


class Rarity(Enum):
    """
    Seltenheitsstufe eines Items.

    TODO: Dazugehörige drop chancen später
    """

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class EnemyType(Enum):
    """
    Verschiedene Gegnertypen im Spiel.
    """

    GOBLIN = "Goblin"
    SKELETON = "Skelett"
    ORC = "Ork"
    MAGE = "Magier"
    KNIGHT = "Ritter"
    DRAGON = "Drache"


class DungeonError(Exception):
    """Basis-Exception für das Spiel."""


class LoadGameError(DungeonError):
    """Wird geworfen, wenn beim Laden ein Fehler auftritt."""


class SaveGameError(DungeonError):
    """Wird geworfen, wenn beim Speichern ein Fehler auftritt."""


class InvalidMoveError(DungeonError):
    """Wird geworfen, wenn eine Bewegung ungültig ist."""


@dataclass
class Stats:
    """
    Stats von Charakteren, NPCs und Gegnern.

    Attributes:
        hp: Aktuelle HP
        max_hp: Maximale HP
        ad: Angriffskraft
        defense: Verteilung

    Examples:
        >>> stats = Stats(hp=100, max_hp=100, ad=10, defense=5)
        >>> stats.hp
        100
    """

    hp: int
    max_hp: int
    ad: int
    defense: int

    def __post_init__(self) -> None:
        """Validierung der Stats nach Initialisierung."""
        if self.max_hp < 0:
            raise ValueError("Maximale HP dürfen nicht negativ sein.")
        self.hp = max(self.hp, 0)
        self.hp = min(self.hp, self.max_hp)
        if self.ad < 0:
            raise ValueError("Angriffskraft (ad) darf nicht negativ sein.")
        if self.defense < 0:
            raise ValueError("Verteidigung darf nicht negativ sein.")


@dataclass
class Item:
    """
    Ein Item, das Stats verbessern kann.

    Attributes:
        name: Name des Items
        rarity: Seltenheit
        bonus_stats: Die Stats, die das Item verleiht
    """

    name: str
    rarity: Rarity
    bonus_stats: Stats


@dataclass
class Character:
    """
    Basisklasse für Spieler und NPCs.

    Attributes:
        name: Name der Entität
        base_stats: Basis-Stats ohne Items
        items: Liste der getragenen Items
    """

    name: str
    base_stats: Stats
    items: list[Item]
    gold: int = 0
    xp: int = 0
    level: int = 1

    @property
    def current_stats(self) -> Stats:
        """
        Berechnet die aktuellen Stats inklusive Item-Boni.

        Returns:
            Stats Objekt mit summierten Werten.
        """
        total_hp = self.base_stats.hp
        total_max_hp = self.base_stats.max_hp
        total_ad = self.base_stats.ad
        total_def = self.base_stats.defense

        for item in self.items:
            total_hp += item.bonus_stats.hp
            total_max_hp += item.bonus_stats.max_hp
            total_ad += item.bonus_stats.ad
            total_def += item.bonus_stats.defense

        # HP kann nicht höher als max_hp sein (durch Items)
        total_hp = min(total_hp, total_max_hp)

        return Stats(
            hp=total_hp, max_hp=total_max_hp, ad=total_ad, defense=total_def
        )

    def is_alive(self) -> bool:
        """Prüft, ob der Charakter noch HP hat."""
        return self.current_stats.hp > 0

    def take_damage(self, amount: int) -> None:
        """Reduziert die HP unter Berücksichtigung der Verteidigung."""
        if amount < 0:
            raise ValueError("Schadenswert darf nicht negativ sein.")

        stats = self.current_stats
        damage = max(1, amount - stats.defense)
        self.base_stats.hp = max(0, self.base_stats.hp - damage)

    def gain_xp(self, amount: int) -> bool:
        """
        Erhöht XP und prüft auf Level-Up.

        Returns:
            True wenn ein Level-Up stattgefunden hat.
        """
        self.xp += amount
        xp_needed = self.level * 50
        if self.xp >= xp_needed:
            self.xp -= xp_needed
            self.level += 1
            # Stats verbessern bei Level Up
            self.base_stats.max_hp += 20
            self.base_stats.hp = self.base_stats.max_hp
            self.base_stats.ad += 5
            self.base_stats.defense += 2
            return True
        return False


@dataclass
class Enemy(Character):
    """
    Repräsentiert einen Gegner im Spiel.

    Attributes:
        enemy_type: Der Typ des Gegners
        loot_value: Bestimmt die Qualität der Drops
    """

    enemy_type: EnemyType = EnemyType.GOBLIN
    loot_value: float = 1.0


def create_enemy(
    enemy_type: EnemyType, difficulty_multiplier: float = 1.0
) -> Enemy:
    """
    Erstellt einen Gegner basierend auf Typ und Schwierigkeit.

    Args:
        enemy_type: Der gewünschte Gegnertyp.
        difficulty_multiplier: Multiplikator für die Stats.

    Returns:
        Ein konfiguriertes Enemy-Objekt.
    """
    # Basis-Werte für die verschiedenen Typen
    base_data = {
        EnemyType.GOBLIN: {
            "hp": 30,
            "ad": 5,
            "def": 2,
            "gold": 10,
            "xp": 20,
            "loot": 1.0,
        },
        EnemyType.SKELETON: {
            "hp": 40,
            "ad": 8,
            "def": 1,
            "gold": 15,
            "xp": 30,
            "loot": 1.2,
        },
        EnemyType.ORC: {
            "hp": 60,
            "ad": 12,
            "def": 5,
            "gold": 25,
            "xp": 50,
            "loot": 1.5,
        },
        EnemyType.MAGE: {
            "hp": 35,
            "ad": 20,
            "def": 0,
            "gold": 30,
            "xp": 60,
            "loot": 2.0,
        },
        EnemyType.KNIGHT: {
            "hp": 80,
            "ad": 15,
            "def": 10,
            "gold": 40,
            "xp": 80,
            "loot": 2.5,
        },
        EnemyType.DRAGON: {
            "hp": 200,
            "ad": 40,
            "def": 20,
            "gold": 200,
            "xp": 500,
            "loot": 10.0,
        },
    }

    data = base_data[enemy_type]

    # Stats mit Schwierigkeit skalieren
    scaled_hp = int(data["hp"] * difficulty_multiplier)
    scaled_ad = int(data["ad"] * difficulty_multiplier)
    scaled_def = int(data["def"] * difficulty_multiplier)

    stats = Stats(
        hp=scaled_hp, max_hp=scaled_hp, ad=scaled_ad, defense=scaled_def
    )

    return Enemy(
        name=enemy_type.value,
        base_stats=stats,
        items=[],
        gold=int(data["gold"] * difficulty_multiplier),
        xp=int(data["xp"] * difficulty_multiplier),
        enemy_type=enemy_type,
        loot_value=data["loot"] * difficulty_multiplier,
    )
