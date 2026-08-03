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
