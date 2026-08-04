"""
Haupteinstiegspunkt für das Spiel mit Pygame-GUI.
"""

import sys

import pygame

from dungeon_autobattler.engine import Engine, GameMap, Position, TileType
from dungeon_autobattler.models import (
    Character,
    DungeonError,
    Item,
    Rarity,
    Stats,
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
    game_map = GameMap(SCREEN_WIDTH // TILE_SIZE, SCREEN_HEIGHT // TILE_SIZE)
    # Einfache Mauern am Rand
    for x in range(game_map.width):
        game_map.set_tile(x, 0, TileType.WALL)
        game_map.set_tile(x, game_map.height - 1, TileType.WALL)
    for y in range(game_map.height):
        game_map.set_tile(0, y, TileType.WALL)
        game_map.set_tile(game_map.width - 1, y, TileType.WALL)

    player_stats = Stats(hp=100, max_hp=100, ad=10, defense=5)
    player = Character(name="Held", base_stats=player_stats, items=[])
    engine = Engine(player, game_map, Position(1, 1))

    # Gegner spawnen
    enemy_stats = Stats(hp=30, max_hp=30, ad=5, defense=2)
    engine.spawn_enemy(5, 5, Character("Goblin", enemy_stats, [], gold=10))

    # Shop einrichten
    engine.game_map.set_tile(3, 3, TileType.SHOP)
    engine.shop_items.append(
        Item("Schwert", Rarity.RARE, Stats(hp=0, max_hp=0, ad=5, defense=0))
    )

    # UI Font
    font = pygame.font.SysFont("Arial", 24)

    running = True
    while running:
        # 1. Events verarbeiten
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    engine.move_player(0, -1)
                elif event.key == pygame.K_DOWN:
                    engine.move_player(0, 1)
                elif event.key == pygame.K_LEFT:
                    engine.move_player(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    engine.move_player(1, 0)
                elif event.key == pygame.K_s:
                    try:
                        engine.save_game("savegame.json")
                    except DungeonError as e:
                        print(f"Fehler beim Speichern: {e}")
                elif event.key == pygame.K_l:
                    try:
                        engine = Engine.load_game("savegame.json")
                        game_map = engine.game_map
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

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
