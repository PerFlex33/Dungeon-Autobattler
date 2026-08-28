"""
Hier befinden sich alle Datenmodelle für Charaktere, Items und die Welt.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Rarity(Enum):
    """Seltenheitsstufe eines Items."""

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class EnemyType(Enum):
    """Verschiedene Gegnertypen im Spiel mit individuellen Skalierungen."""

    GOBLIN = "Goblin"
    SKELETON = "Skelett"
    ORC = "Ork"
    MAGE = "Magier"
    KNIGHT = "Ritter"
    DRAGON = "Drache"


class DungeonError(Exception):
    """Basis-Exception für alle spielspezifischen Fehler."""


class LoadGameError(DungeonError):
    """Wird geworfen, wenn beim Laden der Savegame-Datei ein Fehler auftritt."""


class SaveGameError(DungeonError):
    """Wird geworfen, wenn beim Speichern des Spielstands ein Fehler auftritt."""


class InvalidMoveError(DungeonError):
    """Wird geworfen, wenn eine ungültige Bewegung auf der Map versucht wird."""


@dataclass
class Stats:
    """
    Stats von Charakteren, NPCs und Gegnern.

    Attributes:
        hp: Aktuelle Lebenspunkte
        max_hp: Maximale Lebenspunkte
        ad: Angriffskraft (Attack Damage)
        armor: Rüstungswert zur Schadensreduktion
        evasion_rating: Ausweichwert, der die gegnerische Genauigkeit kontert
        accuracy: Treffergenauigkeit
        crit_chance: Wahrscheinlichkeit für einen kritischen Treffer (0.0 bis 1.0)
        crit_multiplier: Multiplikator für den Schaden bei kritischen Treffern
    """

    hp: int
    max_hp: int
    ad: int
    armor: int = 0
    evasion_rating: int = 0
    accuracy: int = 100
    crit_chance: float = 0.05
    crit_multiplier: float = 1.5

    def __post_init__(self) -> None:
        """Validiert die Stats nach der Initialisierung auf korrekte Wertebereiche."""
        if self.max_hp < 0:
            raise ValueError("Maximale HP dürfen nicht negativ sein.")
        self.hp = max(self.hp, 0)
        self.hp = min(self.hp, self.max_hp)
        if (
            self.ad < 0
            or self.armor < 0
            or self.evasion_rating < 0
            or self.accuracy < 0
        ):
            raise ValueError("Basis-Werte dürfen nicht negativ sein.")


class EquipmentSlot(Enum):
    """Verfügbare Ausrüstungs-Slots für Items."""

    HELMET = "helmet"
    CHESTPLATE = "chestplate"
    PANTS = "pants"
    SHOES = "shoes"
    RING = "ring"
    AMULET = "amulet"


@dataclass
class Item:
    """
    Ein Item, das dem Spieler Stats gewährt oder konsumiert werden kann.

    Attributes:
        name: Name des Items.
        rarity: Seltenheitsstufe.
        bonus_stats: Die Stats, die beim Tragen addiert werden.
        slot: Der Ausrüstungsslot (falls es anlegbar ist).
        is_consumable: True, wenn das Item verbraucht werden kann (z.B. Tränke).
        heal_amount: Menge an HP, die beim Konsumieren geheilt wird.
    """

    name: str
    rarity: Rarity
    bonus_stats: Stats
    slot: EquipmentSlot | None = None
    is_consumable: bool = False
    heal_amount: int = 0


def _default_equipment() -> dict[str, Optional["Item"]]:
    """Erzeugt ein leeres Equipment-Dictionary mit allen verfügbaren Slots für neue Charaktere."""
    return {
        "helmet": None,
        "chestplate": None,
        "pants": None,
        "shoes": None,
        "ring_1": None,
        "ring_2": None,
        "ring_3": None,
        "ring_4": None,
        "amulet": None,
    }


@dataclass
class Character:
    """
    Basisklasse für Spieler und NPCs.

    Attributes:
        name: Name der Entität.
        base_stats: Basis-Stats ohne angelegte Items.
        items: Rucksack-Inventar (Liste aller getragenen Items).
        equipment: Aktuell angelegte Ausrüstungsgegenstände.
        gold: Gesammeltes Gold.
        xp: Gesammelte Erfahrungspunkte.
        level: Aktuelles Level.
    """

    name: str
    base_stats: Stats
    items: list[Item]
    equipment: dict[str, Optional["Item"]] = field(
        default_factory=_default_equipment
    )
    gold: int = 0
    xp: int = 0
    level: int = 1

    @property
    def current_stats(self) -> Stats:
        """
        Berechnet die aktuellen Stats dynamisch basierend auf base_stats und angelegter Ausrüstung.

        Returns:
            Ein neues Stats-Objekt mit den aufsummierten Werten.
        """
        total_hp = self.base_stats.hp
        total_max_hp = self.base_stats.max_hp
        total_ad = self.base_stats.ad
        total_armor = self.base_stats.armor
        total_evasion = self.base_stats.evasion_rating
        total_accuracy = self.base_stats.accuracy
        total_crit_chance = self.base_stats.crit_chance
        total_crit_multi = self.base_stats.crit_multiplier

        equipped_items = [
            item for item in self.equipment.values() if item is not None
        ]

        for item in equipped_items:
            total_hp += item.bonus_stats.hp
            total_max_hp += item.bonus_stats.max_hp
            total_ad += item.bonus_stats.ad
            total_armor += item.bonus_stats.armor
            total_evasion += item.bonus_stats.evasion_rating
            total_accuracy += item.bonus_stats.accuracy
            total_crit_chance += item.bonus_stats.crit_chance
            total_crit_multi += item.bonus_stats.crit_multiplier

        total_hp = min(total_hp, total_max_hp)

        return Stats(
            hp=total_hp,
            max_hp=total_max_hp,
            ad=total_ad,
            armor=total_armor,
            evasion_rating=total_evasion,
            accuracy=total_accuracy,
            crit_chance=total_crit_chance,
            crit_multiplier=total_crit_multi,
        )

    def is_alive(self) -> bool:
        """
        Prüft, ob der Charakter noch am Leben ist.

        Returns:
            True, wenn die HP größer als 0 sind.
        """
        return self.current_stats.hp > 0

    def take_damage(self, amount: int) -> None:
        """
        Reduziert die HP um den übergebenen, final berechneten Schaden.

        Args:
            amount: Der abzuziehende Schaden (muss >= 0 sein).
        """
        if amount < 0:
            raise ValueError("Schadenswert darf nicht negativ sein.")
        self.base_stats.hp = max(0, self.base_stats.hp - amount)

    def gain_xp(self, amount: int) -> bool:
        """
        Erhöht die XP des Charakters und führt bei Erreichen der Grenze ein Level-Up durch.

        Args:
            amount: Die Anzahl der zu gewährenden Erfahrungspunkte.

        Returns:
            True, wenn ein Level-Up stattgefunden hat, sonst False.
        """
        self.xp += amount
        xp_needed = self.level * 50
        if self.xp >= xp_needed:
            self.xp -= xp_needed
            self.level += 1
            self.base_stats.max_hp += 20
            self.base_stats.hp = self.base_stats.max_hp
            self.base_stats.ad += 5
            return True
        return False


@dataclass
class Enemy(Character):
    """
    Repräsentiert einen Feind auf der Karte.

    Attributes:
        enemy_type: Die Art des Feindes (z.B. Goblin, Drache).
        loot_value: Multiplikator für Gold- und Item-Drops.
    """

    enemy_type: EnemyType = EnemyType.GOBLIN
    loot_value: float = 1.0


def create_enemy(
    enemy_type: EnemyType, difficulty_multiplier: float = 1.0
) -> Enemy:
    """
    Erstellt einen parametrisierten Gegner basierend auf seinem Typ und dem aktuellen Schwierigkeitsgrad.

    Args:
        enemy_type: Die Art des Gegners aus der EnemyType-Enum.
        difficulty_multiplier: Skalar, mit dem alle Basis-Stats multipliziert werden.

    Returns:
        Ein vollständig initialisiertes Enemy-Objekt.
    """
    base_data = {
        EnemyType.GOBLIN: {
            "hp": 30,
            "ad": 5,
            "armor": 0,
            "evasion": 50,
            "accuracy": 80,
            "crit_c": 0.05,
            "crit_m": 1.5,
            "gold": 10,
            "xp": 20,
            "loot": 1.0,
        },
        EnemyType.SKELETON: {
            "hp": 40,
            "ad": 8,
            "armor": 15,
            "evasion": 10,
            "accuracy": 90,
            "crit_c": 0.05,
            "crit_m": 1.5,
            "gold": 15,
            "xp": 30,
            "loot": 1.2,
        },
        EnemyType.ORC: {
            "hp": 60,
            "ad": 12,
            "armor": 40,
            "evasion": 5,
            "accuracy": 90,
            "crit_c": 0.05,
            "crit_m": 1.5,
            "gold": 25,
            "xp": 50,
            "loot": 1.5,
        },
        EnemyType.MAGE: {
            "hp": 35,
            "ad": 20,
            "armor": 0,
            "evasion": 25,
            "accuracy": 120,
            "crit_c": 0.10,
            "crit_m": 2.0,
            "gold": 30,
            "xp": 60,
            "loot": 2.0,
        },
        EnemyType.KNIGHT: {
            "hp": 80,
            "ad": 15,
            "armor": 80,
            "evasion": 0,
            "accuracy": 100,
            "crit_c": 0.05,
            "crit_m": 1.5,
            "gold": 40,
            "xp": 80,
            "loot": 2.5,
        },
        EnemyType.DRAGON: {
            "hp": 200,
            "ad": 40,
            "armor": 150,
            "evasion": 100,
            "accuracy": 150,
            "crit_c": 0.15,
            "crit_m": 2.0,
            "gold": 200,
            "xp": 500,
            "loot": 10.0,
        },
    }

    data = base_data[enemy_type]

    scaled_hp = int(data["hp"] * difficulty_multiplier)
    scaled_ad = int(data["ad"] * difficulty_multiplier)
    scaled_armor = int(data["armor"] * difficulty_multiplier)
    scaled_evasion = int(data["evasion"] * difficulty_multiplier)
    scaled_accuracy = int(data["accuracy"] * difficulty_multiplier)

    stats = Stats(
        hp=scaled_hp,
        max_hp=scaled_hp,
        ad=scaled_ad,
        armor=scaled_armor,
        evasion_rating=scaled_evasion,
        accuracy=scaled_accuracy,
        crit_chance=data["crit_c"],
        crit_multiplier=data["crit_m"],
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
