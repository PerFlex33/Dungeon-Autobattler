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

    # Shop einrichten
    shop_pos = generator.find_free_tile(game_map)
    engine.game_map.set_tile(shop_pos.x, shop_pos.y, TileType.SHOP)

    engine.shop_items.append(
        Item(
            "Schwert",
            Rarity.RARE,
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
        )
    )

    # UI Font
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 18)

    show_inventory = False
    running = True
    while running:
        # 1. Events verarbeiten
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    engine.move_player(0, -1)
                elif event.key == pygame.K_s:
                    engine.move_player(0, 1)
                elif event.key == pygame.K_a:
                    engine.move_player(-1, 0)
                elif event.key == pygame.K_d:
                    engine.move_player(1, 0)
                elif event.key == pygame.K_i:
                    show_inventory = not show_inventory
                elif event.key == pygame.K_F5:
                    try:
                        engine.save_game("savegame.json")
                    except DungeonError as e:
                        print(f"Fehler beim Speichern: {e}")
                elif event.key == pygame.K_F9 or event.key == pygame.K_l:
                    try:
                        engine = Engine.load_game("savegame.json")
                        game_map = engine.game_map
                        show_inventory = False
                    except DungeonError as e:
                        print(f"Fehler beim Laden: {e}")

        # 2. Zeichnen
        screen.fill((30, 30, 30))  # Dunkler Hintergrund

        for y, row in enumerate(game_map.tiles):
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
            f"HP: {engine.player.base_stats.hp}/{engine.player.base_stats.max_hp}",
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
        if show_inventory:
            overlay = pygame.Surface((400, 300))
            overlay.set_alpha(230)
            overlay.fill((50, 50, 50))
            screen.blit(overlay, (200, 150))
            pygame.draw.rect(screen, (200, 200, 200), (200, 150, 400, 300), 2)

            stats = engine.player.current_stats
            title = font.render(
                "Charakter Stats & Inventar", True, (255, 255, 255)
            )
            hp_s = small_font.render(
                f"HP: {stats.hp}/{stats.max_hp}", True, (255, 255, 255)
            )
            ad_s = small_font.render(
                f"Angriff (AD): {stats.ad}", True, (255, 255, 255)
            )

            armor_s = small_font.render(
                f"Rüstung: {stats.armor} | Ausweichen: {stats.evasion_rating}",
                True,
                (255, 255, 255),
            )

            screen.blit(title, (220, 170))
            screen.blit(hp_s, (220, 210))
            screen.blit(ad_s, (220, 240))
            screen.blit(armor_s, (220, 270))

            inv_title = small_font.render("Items:", True, (0, 255, 255))
            screen.blit(inv_title, (220, 310))

            for i, item in enumerate(engine.player.items):
                item_text = small_font.render(
                    f"- {item.name} ({item.rarity.value})",
                    True,
                    (200, 200, 200),
                )
                screen.blit(item_text, (220, 340 + i * 25))

            if not engine.player.items:
                none_text = small_font.render(
                    "Keine Items", True, (150, 150, 150)
                )
                screen.blit(none_text, (220, 340))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
