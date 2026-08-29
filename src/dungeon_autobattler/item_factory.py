import copy
import random

from dungeon_autobattler.models import (
    EquipmentSlot,
    Item,
    Rarity,
    Stats,
)

# Multiplikatoren für die Skalierung der Stats anhand der Rarität
RARITY_MULTIPLIERS = {
    Rarity.COMMON: 1.0,
    Rarity.UNCOMMON: 1.3,
    Rarity.RARE: 1.6,
    Rarity.EPIC: 2.2,
    Rarity.LEGENDARY: 3.0,
}

# Wahrscheinlichkeiten für die Generierung
RARITY_WEIGHTS = {
    Rarity.COMMON: 50,
    Rarity.UNCOMMON: 30,
    Rarity.RARE: 12,
    Rarity.EPIC: 6,
    Rarity.LEGENDARY: 2,
}

# Zentrale Datenbank der "Base Types" (Grund-Items)
BASE_ITEMS = [
    Item(
        "Rapier",
        Rarity.COMMON,
        Stats(hp=0, max_hp=0, ad=6, armor=0, accuracy=120, crit_chance=0.15),
        EquipmentSlot.WEAPON,
        price=18,
    ),
    Item(
        "Kriegshammer",
        Rarity.COMMON,
        Stats(
            hp=0,
            max_hp=0,
            ad=12,
            armor=0,
            accuracy=85,
            crit_chance=0.05,
            crit_multiplier=2.0,
        ),
        EquipmentSlot.WEAPON,
        price=22,
    ),
    Item(
        "Zauberstab",
        Rarity.COMMON,
        Stats(hp=0, max_hp=0, ad=8, armor=0, evasion_rating=10),
        EquipmentSlot.WEAPON,
        price=20,
    ),
    Item(
        "Kettenhemd",
        Rarity.COMMON,
        Stats(hp=15, max_hp=15, ad=0, armor=10),
        EquipmentSlot.CHESTPLATE,
        price=20,
    ),
    Item(
        "Magierrobe",
        Rarity.COMMON,
        Stats(hp=5, max_hp=5, ad=0, armor=2, evasion_rating=15),
        EquipmentSlot.CHESTPLATE,
        price=18,
    ),
    Item(
        "Lederhose",
        Rarity.COMMON,
        Stats(hp=5, max_hp=5, ad=0, armor=4, evasion_rating=5),
        EquipmentSlot.PANTS,
        price=12,
    ),
    Item(
        "Plattenbeinschienen",
        Rarity.COMMON,
        Stats(hp=10, max_hp=10, ad=0, armor=10),
        EquipmentSlot.PANTS,
        price=25,
    ),
    Item(
        "Lederstiefel",
        Rarity.COMMON,
        Stats(hp=0, max_hp=0, ad=0, armor=2, evasion_rating=10),
        EquipmentSlot.SHOES,
        price=10,
    ),
    Item(
        "Eisenstiefel",
        Rarity.COMMON,
        Stats(hp=5, max_hp=5, ad=0, armor=6),
        EquipmentSlot.SHOES,
        price=15,
    ),
    Item(
        "Ring des Berserkers",
        Rarity.COMMON,
        Stats(hp=0, max_hp=0, ad=5, armor=2, crit_chance=0.10),
        EquipmentSlot.RING,
        price=25,
    ),
    Item(
        "Amulett der Vitalität",
        Rarity.COMMON,
        Stats(hp=30, max_hp=30, ad=0, armor=0),
        EquipmentSlot.AMULET,
        price=30,
    ),
    # Waffen
    Item(
        "Kurzschwert",
        Rarity.COMMON,
        Stats(hp=0, max_hp=0, ad=5, armor=0),
        EquipmentSlot.WEAPON,
        price=10,
    ),
    Item(
        "Kriegsaxt",
        Rarity.COMMON,
        Stats(
            hp=0, max_hp=0, ad=7, armor=0, crit_chance=0.1, crit_multiplier=0.2
        ),
        EquipmentSlot.WEAPON,
        price=15,
    ),
    Item(
        "Dolch",
        Rarity.COMMON,
        Stats(hp=0, max_hp=0, ad=3, armor=0, accuracy=10, crit_chance=0.15),
        EquipmentSlot.WEAPON,
        price=12,
    ),
    # Rüstungen
    Item(
        "Lederbrustpanzer",
        Rarity.COMMON,
        Stats(hp=10, max_hp=10, ad=0, armor=5),
        EquipmentSlot.CHESTPLATE,
        price=15,
    ),
    Item(
        "Plattenpanzer",
        Rarity.COMMON,
        Stats(hp=20, max_hp=20, ad=0, armor=15, evasion_rating=0),
        EquipmentSlot.CHESTPLATE,
        price=30,
    ),
    Item(
        "Eisenhelm",
        Rarity.COMMON,
        Stats(hp=5, max_hp=5, ad=0, armor=8),
        EquipmentSlot.HELMET,
        price=12,
    ),
    # Accessoires
    Item(
        "Ring des Lebens",
        Rarity.COMMON,
        Stats(hp=15, max_hp=15, ad=0, armor=0),
        EquipmentSlot.RING,
        price=20,
    ),
    Item(
        "Amulett der Präzision",
        Rarity.COMMON,
        Stats(hp=0, max_hp=0, ad=0, armor=0, accuracy=25),
        EquipmentSlot.AMULET,
        price=25,
    ),
]

BASE_CONSUMABLES = [
    Item(
        "Kleiner Heiltrank",
        Rarity.COMMON,
        Stats(hp=0, max_hp=0, ad=0, armor=0),
        is_consumable=True,
        heal_amount=30,
        price=10,
    ),
    Item(
        "Großer Heiltrank",
        Rarity.RARE,
        Stats(hp=0, max_hp=0, ad=0, armor=0),
        is_consumable=True,
        heal_amount=80,
        price=30,
    ),
    Item(
        "Riesiger Heiltrank",
        Rarity.EPIC,
        Stats(hp=0, max_hp=0, ad=0, armor=0),
        is_consumable=True,
        heal_amount=150,
        price=60,
    ),
    Item(
        "Göttertrank",
        Rarity.LEGENDARY,
        Stats(hp=0, max_hp=0, ad=0, armor=0),
        is_consumable=True,
        heal_amount=500,
        price=150,
    ),
]


def _scale_stats(base_stats: Stats, multiplier: float) -> Stats:
    """Skaliert alle ganzzahligen Stats mit dem Multiplikator."""
    return Stats(
        hp=int(base_stats.hp * multiplier),
        max_hp=int(base_stats.max_hp * multiplier),
        ad=int(base_stats.ad * multiplier),
        armor=int(base_stats.armor * multiplier),
        evasion_rating=int(base_stats.evasion_rating * multiplier),
        accuracy=int(base_stats.accuracy * multiplier),
        crit_chance=base_stats.crit_chance,
        crit_multiplier=base_stats.crit_multiplier,
    )


def generate_random_equipment(forced_rarity: Rarity | None = None) -> Item:
    """Zieht ein zufälliges Base-Item, weist ihm eine Seltenheit zu und skaliert die Werte."""
    base_item = random.choice(BASE_ITEMS)

    if forced_rarity:
        rarity = forced_rarity
    else:
        rarities = list(RARITY_WEIGHTS.keys())
        weights = list(RARITY_WEIGHTS.values())
        rarity = random.choices(rarities, weights=weights, k=1)[0]

    multiplier = RARITY_MULTIPLIERS[rarity]

    rarity_prefixes = {
        Rarity.COMMON: "",
        Rarity.UNCOMMON: "Gutes ",
        Rarity.RARE: "Mächtiges ",
        Rarity.EPIC: "Episches ",
        Rarity.LEGENDARY: "Legendäres ",
    }

    new_name = f"{rarity_prefixes[rarity]}{base_item.name}".strip()
    scaled_stats = _scale_stats(base_item.bonus_stats, multiplier)
    scaled_price = int(base_item.price * multiplier * 1.2)

    return Item(
        name=new_name,
        rarity=rarity,
        bonus_stats=scaled_stats,
        slot=base_item.slot,
        is_consumable=False,
        price=scaled_price,
    )


def generate_shop_inventory(count: int = 5) -> list[Item]:
    """Generiert ein zufälliges Inventar für den Shop."""
    inventory = []
    for _ in range(count):
        if random.random() < 0.3:
            inventory.append(copy.deepcopy(random.choice(BASE_CONSUMABLES)))
        else:
            inventory.append(generate_random_equipment())
    return inventory
