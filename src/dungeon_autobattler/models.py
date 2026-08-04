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
    Basisklasse für Spieler und Gegner.

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

        return Stats(
            hp=total_hp, max_hp=total_max_hp, ad=total_ad, defense=total_def
        )

    def is_alive(self) -> bool:
        """Prüft, ob der Charakter noch HP hat."""
        return self.base_stats.hp > 0

    def take_damage(self, amount: int) -> None:
        """Reduziert die HP unter Berücksichtigung der Verteidigung."""
        damage = max(1, amount - self.base_stats.defense)
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
