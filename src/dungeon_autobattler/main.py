"""
Haupteinstiegspunkt für das Spiel mit Pygame-GUI.
Beinhaltet die Render-Logik für die Dungeon-Map, das interaktive Inventar-Overlay,
die schrittweise visuelle Abwicklung von Kämpfen sowie den Händler-Shop (Kaufen/Verkaufen).
"""

import random
import sys
from dataclasses import dataclass

import pygame

from dungeon_autobattler.engine import Engine, TileType
from dungeon_autobattler.generator import DungeonGenerator
from dungeon_autobattler.models import (
    Character,
    DungeonError,
    EnemyType,
    EquipmentSlot,
    Item,
    Rarity,
    Stats,
    create_enemy,
)

TILE_SIZE = 40
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60


@dataclass
class UIState:
    """Speichert den aktuellen Status der Benutzeroberfläche streng typisiert."""

    show_inventory: bool = False
    inv_selection: int = 0
    show_shop: bool = False
    shop_selection: int = 0
    shop_mode: str = "buy"


def main() -> None:
    """
    Initialisiert Pygame, generiert die Startwelt samt Spieler, Items und Gegnern,
    und startet den Main-Loop.
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dungeon Autobattler")
    clock = pygame.time.Clock()

    map_width = SCREEN_WIDTH // TILE_SIZE
    map_height = SCREEN_HEIGHT // TILE_SIZE
    generator = DungeonGenerator(map_width, map_height)
    game_map = generator.generate_random_walk(steps=300)

    player_stats = Stats(hp=80, max_hp=100, ad=10, armor=5)

    start_items = [
        Item(
            "Rostiges Schwert",
            Rarity.COMMON,
            Stats(
                hp=0,
                max_hp=0,
                ad=5,
                armor=0,
                evasion_rating=0,
                accuracy=0,
                crit_chance=0.0,
                crit_multiplier=0.0,
            ),
            slot=EquipmentSlot.WEAPON,
            price=10,
        ),
        Item(
            "Kleiner Heiltrank",
            Rarity.COMMON,
            Stats(
                hp=0,
                max_hp=0,
                ad=0,
                armor=0,
                evasion_rating=0,
                accuracy=0,
                crit_chance=0.0,
                crit_multiplier=0.0,
            ),
            is_consumable=True,
            heal_amount=30,
            price=10,
        ),
        Item(
            "Großer Heiltrank",
            Rarity.RARE,
            Stats(
                hp=0,
                max_hp=0,
                ad=0,
                armor=0,
                evasion_rating=0,
                accuracy=0,
                crit_chance=0.0,
                crit_multiplier=0.0,
            ),
            is_consumable=True,
            heal_amount=80,
            price=30,
        ),
        Item(
            "Ring des Ausweichens",
            Rarity.UNCOMMON,
            Stats(
                hp=0,
                max_hp=0,
                ad=0,
                armor=0,
                evasion_rating=40,
                accuracy=0,
                crit_chance=0.0,
                crit_multiplier=0.0,
            ),
            slot=EquipmentSlot.RING,
            price=20,
        ),
        Item(
            "Ring der Brutalität",
            Rarity.RARE,
            Stats(
                hp=0,
                max_hp=0,
                ad=8,
                armor=0,
                evasion_rating=0,
                accuracy=0,
                crit_chance=0.10,
                crit_multiplier=0.5,
            ),
            slot=EquipmentSlot.RING,
            price=40,
        ),
        Item(
            "Meuchelmörder-Amulett",
            Rarity.EPIC,
            Stats(
                hp=0,
                max_hp=0,
                ad=2,
                armor=0,
                evasion_rating=0,
                accuracy=20,
                crit_chance=0.15,
                crit_multiplier=1.0,
            ),
            slot=EquipmentSlot.AMULET,
            price=60,
        ),
    ]

    player = Character(name="Held", base_stats=player_stats, items=start_items)
    player.gold = 50

    start_pos = generator.find_free_tile(game_map)
    engine = Engine(player, game_map, start_pos, difficulty=1.2)

    enemy_types = list(EnemyType)
    for _ in range(7):
        enemy_type = random.choice(enemy_types)
        enemy_pos = generator.find_free_tile(game_map)
        engine.spawn_enemy(
            enemy_pos.x,
            enemy_pos.y,
            create_enemy(enemy_type, difficulty_multiplier=engine.difficulty),
        )

    engine.shop_items = [
        Item(
            "Schwert des Feuers",
            Rarity.RARE,
            Stats(
                hp=0,
                max_hp=0,
                ad=15,
                armor=0,
                evasion_rating=0,
                accuracy=0,
                crit_chance=0.10,
                crit_multiplier=0.2,
            ),
            slot=EquipmentSlot.WEAPON,
            price=60,
        ),
        Item(
            "Bärenpanzer",
            Rarity.UNCOMMON,
            Stats(
                hp=30,
                max_hp=30,
                ad=0,
                armor=15,
                evasion_rating=0,
                accuracy=0,
                crit_chance=0.0,
                crit_multiplier=0.0,
            ),
            slot=EquipmentSlot.CHESTPLATE,
            price=45,
        ),
        Item(
            "Mittlerer Heiltrank",
            Rarity.COMMON,
            Stats(
                hp=0,
                max_hp=0,
                ad=0,
                armor=0,
                evasion_rating=0,
                accuracy=0,
                crit_chance=0.0,
                crit_multiplier=0.0,
            ),
            is_consumable=True,
            heal_amount=50,
            price=20,
        ),
    ]

    shop_pos = generator.find_free_tile(game_map)
    engine.game_map.set_tile(shop_pos.x, shop_pos.y, TileType.SHOP)

    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 18)

    state = UIState()

    display_slots = {
        "weapon": "Waffe",
        "helmet": "Kopf",
        "chestplate": "Brust",
        "pants": "Beine",
        "shoes": "Schuhe",
        "amulet": "Amulett",
        "ring_1": "Ring 1",
        "ring_2": "Ring 2",
        "ring_3": "Ring 3",
        "ring_4": "Ring 4",
    }
    slot_order = list(display_slots.keys())

    def draw_scene(current_enemy: Character | None = None) -> None:
        """Rendert in jedem Frame die Karte, UI-Overlays, Shops und das dynamische Inventar."""
        screen.fill((30, 30, 30))

        for y, row in enumerate(engine.game_map.tiles):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE
                )
                if tile == TileType.WALL:
                    pygame.draw.rect(screen, (100, 100, 100), rect)
                elif tile == TileType.EMPTY:
                    pygame.draw.rect(screen, (50, 50, 50), rect, 1)
                elif tile == TileType.ENEMY:
                    pygame.draw.rect(screen, (200, 0, 0), rect)
                elif tile == TileType.SHOP:
                    pygame.draw.rect(screen, (0, 0, 200), rect)

        player_rect = pygame.Rect(
            engine.player_pos.x * TILE_SIZE,
            engine.player_pos.y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(screen, (0, 200, 0), player_rect)

        gold_text = font.render(
            f"Gold: {engine.player.gold}", True, (255, 215, 0)
        )
        hp_text = font.render(
            f"HP: {engine.player.current_stats.hp}/{engine.player.current_stats.max_hp}",
            True,
            (255, 255, 255),
        )
        lvl_text = font.render(
            f"Lvl: {engine.player.level} (XP: {engine.player.xp})",
            True,
            (0, 255, 255),
        )
        screen.blit(gold_text, (10, 10))
        screen.blit(hp_text, (10, 40))
        screen.blit(lvl_text, (10, 70))

        if (
            not state.show_shop
            and not state.show_inventory
            and engine.game_map.tiles[engine.player_pos.y][engine.player_pos.x]
            == TileType.SHOP
        ):
            hint_bg = pygame.Surface((300, 40))
            hint_bg.set_alpha(180)
            hint_bg.fill((0, 0, 0))
            screen.blit(hint_bg, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 60))
            hint_text = font.render(
                "[E] Händler ansprechen", True, (255, 255, 255)
            )
            screen.blit(
                hint_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 55)
            )

        if state.show_inventory:
            overlay = pygame.Surface((760, 480))
            overlay.set_alpha(245)
            overlay.fill((40, 40, 40))
            screen.blit(overlay, (20, 60))
            pygame.draw.rect(screen, (200, 200, 200), (20, 60, 760, 480), 2)

            stats = engine.player.current_stats

            title = font.render("Charakter Stats", True, (255, 255, 255))
            hp_s = small_font.render(
                f"HP: {stats.hp}/{stats.max_hp}", True, (50, 255, 50)
            )
            offense_s = small_font.render(
                f"Angriff: {stats.ad} | Genauigkeit: {stats.accuracy}",
                True,
                (255, 255, 255),
            )
            crit_s = small_font.render(
                f"Krit-Chance: {int(stats.crit_chance * 100)}% | Krit-Dmg: {int(stats.crit_multiplier * 100)}%",
                True,
                (255, 200, 50),
            )
            defense_s = small_font.render(
                f"Rüstung: {stats.armor} | Ausweichen: {stats.evasion_rating}",
                True,
                (200, 200, 255),
            )

            screen.blit(title, (40, 75))
            screen.blit(hp_s, (40, 115))
            screen.blit(offense_s, (40, 145))
            screen.blit(crit_s, (40, 175))
            screen.blit(defense_s, (40, 205))

            equip_title = small_font.render("Ausrüstung:", True, (0, 255, 255))
            screen.blit(equip_title, (40, 245))

            for i, slot_key in enumerate(slot_order):
                item = engine.player.equipment.get(slot_key)
                item_name = item.name if item else "<Leer>"
                color = (100, 255, 100) if item else (120, 120, 120)
                screen.blit(
                    small_font.render(
                        f"{display_slots[slot_key]}: {item_name}", True, color
                    ),
                    (40, 275 + i * 21),
                )

            inv_title = small_font.render(
                "Rucksack: (W/S: Navi | E: Anlegen/Benutzen)",
                True,
                (0, 255, 255),
            )
            screen.blit(inv_title, (420, 75))
            pygame.draw.line(screen, (100, 100, 100), (400, 60), (400, 540), 2)

            for i, item in enumerate(engine.player.items):
                is_equipped = item in engine.player.equipment.values()
                prefix = "-> " if i == state.inv_selection else "   "
                suffix = " [ANGELEGT]" if is_equipped else ""

                if getattr(item, "is_consumable", False):
                    slot_info = " [Trank]"
                elif item.slot:
                    slot_info = (
                        f" [{display_slots.get(item.slot.value, 'N/A')}]"
                    )
                else:
                    slot_info = ""

                color = (200, 200, 200)
                if i == state.inv_selection:
                    color = (255, 255, 0)
                elif is_equipped:
                    color = (100, 255, 100)

                item_text = small_font.render(
                    f"{prefix}{item.name}{slot_info} ({item.rarity.value}){suffix}",
                    True,
                    color,
                )
                screen.blit(item_text, (420, 115 + i * 25))

            if not engine.player.items:
                screen.blit(
                    small_font.render("Keine Items", True, (150, 150, 150)),
                    (420, 115),
                )
            else:
                pygame.draw.line(
                    screen, (100, 100, 100), (420, 360), (740, 360), 2
                )
                selected = engine.player.items[state.inv_selection]
                detail_title = small_font.render(
                    f"Info: {selected.name}", True, (255, 200, 50)
                )
                screen.blit(detail_title, (420, 375))

                if getattr(selected, "is_consumable", False):
                    desc = small_font.render(
                        f"Effekt: Heilt sofort {selected.heal_amount} HP",
                        True,
                        (50, 255, 50),
                    )
                    screen.blit(desc, (420, 405))
                else:
                    item_stats = selected.bonus_stats
                    stat_texts = []
                    if item_stats.max_hp > 0:
                        stat_texts.append(f"+{item_stats.max_hp} Max HP")
                    if item_stats.hp > 0 and item_stats.max_hp == 0:
                        stat_texts.append(f"+{item_stats.hp} HP")
                    if item_stats.ad > 0:
                        stat_texts.append(f"+{item_stats.ad} Angriff")
                    if item_stats.armor > 0:
                        stat_texts.append(f"+{item_stats.armor} Rüstung")
                    if item_stats.evasion_rating > 0:
                        stat_texts.append(
                            f"+{item_stats.evasion_rating} Ausweichen"
                        )
                    if item_stats.accuracy > 0:
                        stat_texts.append(f"+{item_stats.accuracy} Genauigkeit")
                    if item_stats.crit_chance > 0:
                        stat_texts.append(
                            f"+{int(item_stats.crit_chance * 100)}% Krit"
                        )
                    if item_stats.crit_multiplier > 0:
                        stat_texts.append(
                            f"+{int(item_stats.crit_multiplier * 100)}% Krit-Dmg"
                        )

                    if not stat_texts:
                        stat_texts.append("Keine zusätzlichen Bonus-Werte")

                    for idx, text in enumerate(stat_texts):
                        stat_col = idx % 2
                        stat_row = idx // 2
                        screen.blit(
                            small_font.render(text, True, (200, 255, 200)),
                            (420 + stat_col * 150, 405 + stat_row * 22),
                        )

        if state.show_shop:
            # Vergrößertes Shop-Overlay (Größe auf 600x480 erhöht, damit mehr Platz ist)
            overlay = pygame.Surface((600, 480))
            overlay.set_alpha(245)
            overlay.fill((20, 20, 50))
            screen.blit(overlay, (100, 60))
            pygame.draw.rect(screen, (100, 100, 255), (100, 60, 600, 480), 3)

            mode_text = "KAUFEN" if state.shop_mode == "buy" else "VERKAUFEN"
            shop_title = font.render(
                f"Wanderhändler - {mode_text}", True, (255, 215, 0)
            )
            screen.blit(shop_title, (130, 80))

            nav_info = small_font.render(
                "W/S: Wählen | E: Aktion | TAB: Modus | Q: Verlassen",
                True,
                (0, 255, 255),
            )
            screen.blit(nav_info, (130, 115))

            pygame.draw.line(screen, (100, 100, 255), (130, 145), (670, 145), 2)

            active_list = (
                engine.shop_items
                if state.shop_mode == "buy"
                else engine.player.items
            )

            if not active_list:
                msg = (
                    "Ausverkauft!"
                    if state.shop_mode == "buy"
                    else "Dein Rucksack ist leer."
                )
                sold_out = font.render(msg, True, (150, 150, 150))
                screen.blit(sold_out, (130, 170))
            else:
                for i, item in enumerate(active_list):
                    prefix = "-> " if i == state.shop_selection else "   "
                    color = (
                        (255, 255, 0)
                        if i == state.shop_selection
                        else (200, 200, 200)
                    )

                    if state.shop_mode == "buy":
                        can_afford = engine.player.gold >= item.price
                        price_color = (
                            (100, 255, 100) if can_afford else (255, 100, 100)
                        )
                        price_val = item.price
                        suffix = ""
                    else:
                        price_color = (100, 255, 100)
                        price_val = item.price // 2
                        is_equipped = item in engine.player.equipment.values()
                        if is_equipped:
                            color = (
                                (100, 255, 100)
                                if i != state.shop_selection
                                else (255, 255, 150)
                            )
                            suffix = " [ANGELEGT]"
                        else:
                            suffix = ""

                    item_text = small_font.render(
                        f"{prefix}{item.name} ({item.rarity.value}){suffix}",
                        True,
                        color,
                    )
                    price_text = small_font.render(
                        f"Preis: {price_val} G", True, price_color
                    )

                    # Kompakterer Abstand (30 Pixel statt 35), damit viele Items reinpassen
                    screen.blit(item_text, (130, 165 + i * 30))
                    screen.blit(price_text, (530, 165 + i * 30))

                # Die Detail-Box weiter nach unten verschoben (Y=370), damit sich nichts überschneidet
                pygame.draw.line(
                    screen, (100, 100, 255), (130, 360), (670, 360), 2
                )
                selected = active_list[state.shop_selection]
                if getattr(selected, "is_consumable", False):
                    desc = small_font.render(
                        f"Effekt: Heilt {selected.heal_amount} HP",
                        True,
                        (50, 255, 50),
                    )
                    screen.blit(desc, (130, 380))
                else:
                    item_stats = selected.bonus_stats
                    stat_texts = []
                    if item_stats.max_hp > 0:
                        stat_texts.append(f"+{item_stats.max_hp} Max HP")
                    if item_stats.hp > 0 and item_stats.max_hp == 0:
                        stat_texts.append(f"+{item_stats.hp} HP")
                    if item_stats.ad > 0:
                        stat_texts.append(f"+{item_stats.ad} AD")
                    if item_stats.armor > 0:
                        stat_texts.append(f"+{item_stats.armor} Rüstung")
                    if item_stats.evasion_rating > 0:
                        stat_texts.append(
                            f"+{item_stats.evasion_rating} Ausweichen"
                        )
                    if item_stats.accuracy > 0:
                        stat_texts.append(f"+{item_stats.accuracy} Genauigkeit")
                    if item_stats.crit_chance > 0:
                        stat_texts.append(
                            f"+{int(item_stats.crit_chance * 100)}% Krit"
                        )
                    if item_stats.crit_multiplier > 0:
                        stat_texts.append(
                            f"+{int(item_stats.crit_multiplier * 100)}% K-Dmg"
                        )

                    if not stat_texts:
                        stat_texts.append("Keine zusätzlichen Werte")

                    for idx, text in enumerate(stat_texts):
                        stat_col = idx % 3
                        stat_row = idx // 3
                        screen.blit(
                            small_font.render(text, True, (200, 255, 200)),
                            (130 + stat_col * 180, 380 + stat_row * 22),
                        )

        if current_enemy:
            overlay = pygame.Surface((340, 120))
            overlay.set_alpha(230)
            overlay.fill((40, 10, 10))
            screen.blit(overlay, (SCREEN_WIDTH // 2 - 170, 50))
            pygame.draw.rect(
                screen,
                (200, 50, 50),
                (SCREEN_WIDTH // 2 - 170, 50, 340, 120),
                3,
            )

            vs_text = font.render(
                f"Kampf! vs {current_enemy.name}", True, (255, 255, 255)
            )
            p_text = font.render(
                f"Held HP: {engine.player.current_stats.hp}/{engine.player.current_stats.max_hp}",
                True,
                (50, 255, 50),
            )
            e_text = font.render(
                f"Gegner HP: {current_enemy.current_stats.hp}/{current_enemy.current_stats.max_hp}",
                True,
                (255, 50, 50),
            )

            screen.blit(vs_text, (SCREEN_WIDTH // 2 - 150, 60))
            screen.blit(p_text, (SCREEN_WIDTH // 2 - 150, 95))
            screen.blit(e_text, (SCREEN_WIDTH // 2 - 150, 130))

        if not state.show_inventory and not state.show_shop:
            log_surface = pygame.Surface((380, 160))
            log_surface.set_alpha(200)
            log_surface.fill((20, 20, 20))
            screen.blit(log_surface, (10, SCREEN_HEIGHT - 170))
            pygame.draw.rect(
                screen, (100, 100, 100), (10, SCREEN_HEIGHT - 170, 380, 160), 2
            )
            screen.blit(
                small_font.render("Kampf-Log:", True, (255, 200, 0)),
                (20, SCREEN_HEIGHT - 160),
            )

            for i, log_entry in enumerate(engine.combat_log[-6:]):
                text_color = (
                    (255, 100, 100)
                    if "Held trifft" in log_entry
                    else (200, 200, 200)
                )
                screen.blit(
                    small_font.render(log_entry, True, text_color),
                    (20, SCREEN_HEIGHT - 130 + i * 20),
                )

        pygame.display.flip()

    def combat_callback(enemy: Character) -> None:
        """Rückruffunktion für die Spiel-Engine. Pausiert das Spiel künstlich während Kämpfen."""
        draw_scene(current_enemy=enemy)
        pygame.event.pump()
        pygame.time.delay(800)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i and not state.show_shop:
                    state.show_inventory = not state.show_inventory
                    state.inv_selection = 0
                elif event.key == pygame.K_F5:
                    try:
                        engine.save_game("savegame.json")
                    except DungeonError as e:
                        print(f"Fehler beim Speichern: {e}")
                elif event.key == pygame.K_F9 or event.key == pygame.K_l:
                    try:
                        engine = Engine.load_game("savegame.json")
                        state.show_inventory = False
                        state.show_shop = False
                    except DungeonError as e:
                        print(f"Fehler beim Laden: {e}")

                elif state.show_shop:
                    active_list = (
                        engine.shop_items
                        if state.shop_mode == "buy"
                        else engine.player.items
                    )

                    if event.key == pygame.K_TAB:
                        state.shop_mode = (
                            "sell" if state.shop_mode == "buy" else "buy"
                        )
                        state.shop_selection = 0
                    elif event.key in (pygame.K_w, pygame.K_UP):
                        state.shop_selection = max(0, state.shop_selection - 1)
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        if active_list:
                            state.shop_selection = min(
                                len(active_list) - 1, state.shop_selection + 1
                            )
                    elif event.key in (pygame.K_e, pygame.K_RETURN):
                        if active_list:
                            selected_item = active_list[state.shop_selection]

                            if state.shop_mode == "buy":
                                if engine.player.gold >= selected_item.price:
                                    engine.player.gold -= selected_item.price
                                    engine.player.items.append(selected_item)
                                    engine.shop_items.pop(state.shop_selection)

                                    if (
                                        state.shop_selection
                                        >= len(engine.shop_items)
                                        and state.shop_selection > 0
                                    ):
                                        state.shop_selection -= 1

                            elif state.shop_mode == "sell":
                                equipped_keys = [
                                    k
                                    for k, v in engine.player.equipment.items()
                                    if v == selected_item
                                ]
                                for k in equipped_keys:
                                    engine.player.equipment[k] = None

                                engine.player.gold += selected_item.price // 2
                                engine.player.items.pop(state.shop_selection)

                                if (
                                    state.shop_selection
                                    >= len(engine.player.items)
                                    and state.shop_selection > 0
                                ):
                                    state.shop_selection -= 1

                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        state.show_shop = False

                elif state.show_inventory:
                    if event.key in (pygame.K_w, pygame.K_UP):
                        state.inv_selection = max(0, state.inv_selection - 1)
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        if engine.player.items:
                            state.inv_selection = min(
                                len(engine.player.items) - 1,
                                state.inv_selection + 1,
                            )
                    elif (
                        event.key in (pygame.K_e, pygame.K_RETURN)
                        and engine.player.items
                    ):
                        selected_item = engine.player.items[state.inv_selection]

                        if getattr(selected_item, "is_consumable", False):
                            max_hp = engine.player.current_stats.max_hp
                            current_hp = engine.player.base_stats.hp
                            if current_hp < max_hp:
                                engine.player.base_stats.hp = min(
                                    current_hp + selected_item.heal_amount,
                                    max_hp,
                                )
                                engine.player.items.pop(state.inv_selection)

                                if (
                                    state.inv_selection
                                    >= len(engine.player.items)
                                    and state.inv_selection > 0
                                ):
                                    state.inv_selection -= 1

                        elif selected_item.slot:
                            equipped_keys = [
                                k
                                for k, v in engine.player.equipment.items()
                                if v == selected_item
                            ]
                            if equipped_keys:
                                for k in equipped_keys:
                                    engine.player.equipment[k] = None
                            else:
                                slot_key = selected_item.slot.value
                                if slot_key == "ring":
                                    free_slot = next(
                                        (
                                            r
                                            for r in [
                                                "ring_1",
                                                "ring_2",
                                                "ring_3",
                                                "ring_4",
                                            ]
                                            if engine.player.equipment[r]
                                            is None
                                        ),
                                        None,
                                    )
                                    if free_slot:
                                        engine.player.equipment[free_slot] = (
                                            selected_item
                                        )
                                    else:
                                        engine.player.equipment["ring_1"] = (
                                            selected_item
                                        )
                                else:
                                    engine.player.equipment[slot_key] = (
                                        selected_item
                                    )

                else:
                    if event.key == pygame.K_w:
                        engine.move_player(0, -1, ui_callback=combat_callback)
                    elif event.key == pygame.K_s:
                        engine.move_player(0, 1, ui_callback=combat_callback)
                    elif event.key == pygame.K_a:
                        engine.move_player(-1, 0, ui_callback=combat_callback)
                    elif event.key == pygame.K_d:
                        engine.move_player(1, 0, ui_callback=combat_callback)
                    elif (
                        event.key == pygame.K_e
                        and engine.game_map.tiles[engine.player_pos.y][
                            engine.player_pos.x
                        ]
                        == TileType.SHOP
                    ):
                        state.show_shop = True
                        state.shop_selection = 0
                        state.shop_mode = "buy"

        draw_scene()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
