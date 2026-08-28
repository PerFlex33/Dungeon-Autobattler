"""
Haupteinstiegspunkt für das Spiel mit Pygame-GUI.
"""

import random
import sys

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

# Konstanten
TILE_SIZE = 40
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60


def main() -> None:
    """Initialisiert das Spiel und startet die Hauptschleife."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dungeon Autobattler")
    clock = pygame.time.Clock()

    # Initialisierung von Map und Engine
    map_width = SCREEN_WIDTH // TILE_SIZE
    map_height = SCREEN_HEIGHT // TILE_SIZE
    generator = DungeonGenerator(map_width, map_height)
    game_map = generator.generate_random_walk(steps=300)

    player_stats = Stats(hp=100, max_hp=100, ad=10, armor=5)
    player = Character(name="Held", base_stats=player_stats, items=[])

    start_pos = generator.find_free_tile(game_map)
    engine = Engine(player, game_map, start_pos, difficulty=1.2)

    # Mehrere verschiedene Gegner spawnen
    enemy_types = list(EnemyType)
    for _ in range(5):
        enemy_type = random.choice(enemy_types)
        enemy_pos = generator.find_free_tile(game_map)
        engine.spawn_enemy(
            enemy_pos.x,
            enemy_pos.y,
            create_enemy(enemy_type, difficulty_multiplier=engine.difficulty),
        )

    # Shop einrichten und Test-Ausrüstung hinzufügen
    shop_pos = generator.find_free_tile(game_map)
    engine.game_map.set_tile(shop_pos.x, shop_pos.y, TileType.SHOP)

    engine.shop_items.append(
        Item(
            "Brustpanzer der Macht",
            Rarity.RARE,
            Stats(
                hp=20,
                max_hp=20,
                ad=2,
                armor=15,
                evasion_rating=0,
                accuracy=0,
                crit_chance=0.0,
                crit_multiplier=0.0,
            ),
            slot=EquipmentSlot.CHESTPLATE,
        )
    )

    # UI Font
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 18)

    # State speichert jetzt auch die Auswahl im Inventar
    state = {"show_inventory": False, "inv_selection": 0}

    def draw_scene(current_enemy: Character | None = None) -> None:
        """Zeichnet den kompletten aktuellen Frame inklusive Menüs und Combat."""
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

        # Spieler zeichnen
        player_rect = pygame.Rect(
            engine.player_pos.x * TILE_SIZE,
            engine.player_pos.y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(screen, (0, 200, 0), player_rect)

        # UI zeichnen (Gold und HP)
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

        # Inventar/Stats Overlay
        if state["show_inventory"]:
            overlay = pygame.Surface((450, 350))
            overlay.set_alpha(230)
            overlay.fill((50, 50, 50))
            screen.blit(overlay, (175, 125))
            pygame.draw.rect(screen, (200, 200, 200), (175, 125, 450, 350), 2)

            stats = engine.player.current_stats

            title = font.render(
                "Charakter Stats & Inventar", True, (255, 255, 255)
            )
            hp_s = small_font.render(
                f"HP: {stats.hp}/{stats.max_hp}", True, (50, 255, 50)
            )
            offense_s = small_font.render(
                f"Angriff (AD): {stats.ad}  |  Genauigkeit: {stats.accuracy}",
                True,
                (255, 255, 255),
            )
            crit_s = small_font.render(
                f"Krit-Chance: {int(stats.crit_chance * 100)}%  |  Krit-Schaden: {int(stats.crit_multiplier * 100)}%",
                True,
                (255, 200, 50),
            )
            defense_s = small_font.render(
                f"Rüstung: {stats.armor}  |  Ausweichen: {stats.evasion_rating}",
                True,
                (200, 200, 255),
            )

            screen.blit(title, (195, 140))
            screen.blit(hp_s, (195, 180))
            screen.blit(offense_s, (195, 210))
            screen.blit(crit_s, (195, 240))
            screen.blit(defense_s, (195, 270))

            inv_title = small_font.render(
                "Items: (W/S: Navi | E: An-/Ablegen)", True, (0, 255, 255)
            )
            screen.blit(inv_title, (195, 310))

            for i, item in enumerate(engine.player.items):
                is_equipped = item in engine.player.equipment.values()

                prefix = "-> " if i == state["inv_selection"] else "   "
                suffix = " [ANGELEGT]" if is_equipped else ""

                # Farben für Auswahl und Status
                color = (200, 200, 200)
                if i == state["inv_selection"]:
                    color = (255, 255, 0)
                elif is_equipped:
                    color = (100, 255, 100)

                item_text = small_font.render(
                    f"{prefix}{item.name} ({item.rarity.value}){suffix}",
                    True,
                    color,
                )
                screen.blit(item_text, (195, 340 + i * 25))

            if not engine.player.items:
                none_text = small_font.render(
                    "Keine Items", True, (150, 150, 150)
                )
                screen.blit(none_text, (195, 340))

        # Kampfanzeige Overlay
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

        # Combat Log Overlay
        log_surface = pygame.Surface((380, 160))
        log_surface.set_alpha(200)
        log_surface.fill((20, 20, 20))
        screen.blit(log_surface, (10, SCREEN_HEIGHT - 170))
        pygame.draw.rect(
            screen, (100, 100, 100), (10, SCREEN_HEIGHT - 170, 380, 160), 2
        )

        log_title = small_font.render("Kampf-Log:", True, (255, 200, 0))
        screen.blit(log_title, (20, SCREEN_HEIGHT - 160))

        for i, log_entry in enumerate(engine.combat_log[-6:]):
            text_color = (
                (255, 100, 100)
                if "Held trifft" in log_entry
                else (200, 200, 200)
            )
            log_text = small_font.render(log_entry, True, text_color)
            screen.blit(log_text, (20, SCREEN_HEIGHT - 130 + i * 20))

        pygame.display.flip()

    def combat_callback(enemy: Character) -> None:
        """Wird von der Engine nach jedem Schlag aufgerufen."""
        draw_scene(current_enemy=enemy)
        pygame.event.pump()
        pygame.time.delay(800)

    running = True
    while running:
        # 1. Events verarbeiten
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Globale Hotkeys
                if event.key == pygame.K_i:
                    state["show_inventory"] = not state["show_inventory"]
                    state["inv_selection"] = 0
                elif event.key == pygame.K_F5:
                    try:
                        engine.save_game("savegame.json")
                    except DungeonError as e:
                        print(f"Fehler beim Speichern: {e}")
                elif event.key == pygame.K_F9 or event.key == pygame.K_l:
                    try:
                        engine = Engine.load_game("savegame.json")
                        state["show_inventory"] = False
                    except DungeonError as e:
                        print(f"Fehler beim Laden: {e}")

                # Eingaben wenn das Inventar OFFEN ist
                elif state["show_inventory"]:
                    if event.key in (pygame.K_w, pygame.K_UP):
                        state["inv_selection"] = max(
                            0, state["inv_selection"] - 1
                        )
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        if engine.player.items:
                            state["inv_selection"] = min(
                                len(engine.player.items) - 1,
                                state["inv_selection"] + 1,
                            )
                    elif event.key in (pygame.K_e, pygame.K_RETURN):
                        if engine.player.items:
                            selected_item = engine.player.items[
                                state["inv_selection"]
                            ]
                            if selected_item.slot:
                                slot_key = selected_item.slot.value
                                # Fallback für Ringe
                                if slot_key == "ring":
                                    slot_key = "ring_1"

                                # Item toggeln (An-/Ablegen)
                                if (
                                    engine.player.equipment.get(slot_key)
                                    == selected_item
                                ):
                                    engine.player.equipment[slot_key] = None
                                else:
                                    engine.player.equipment[slot_key] = (
                                        selected_item
                                    )

                                # Wenn Item angelegt wird, prüfen, ob es die max_hp erhöht
                                # und sicherstellen, dass die HP nicht über max_hp steigen
                                engine.player.current_stats  # Trigger Stats-Neuberechnung

                # Eingaben wenn das Inventar GESCHLOSSEN ist (Bewegung)
                else:
                    if event.key == pygame.K_w:
                        engine.move_player(0, -1, ui_callback=combat_callback)
                    elif event.key == pygame.K_s:
                        engine.move_player(0, 1, ui_callback=combat_callback)
                    elif event.key == pygame.K_a:
                        engine.move_player(-1, 0, ui_callback=combat_callback)
                    elif event.key == pygame.K_d:
                        engine.move_player(1, 0, ui_callback=combat_callback)

        # 2. Zeichnen
        draw_scene()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
