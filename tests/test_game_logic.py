from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dungeon_autobattler.engine import Engine, GameMap, Position, TileType
from dungeon_autobattler.models import Character, Stats


@pytest.fixture
def basic_stats() -> Stats:
    return Stats(
        hp=100, max_hp=100, ad=10, armor=5, evasion_rating=10, accuracy=100
    )


@pytest.fixture
def player(basic_stats: Stats) -> Character:
    return Character(name="Held", base_stats=basic_stats, items=[])


@pytest.fixture
def game_map() -> GameMap:
    return GameMap(width=10, height=10)


@pytest.fixture
def engine(player: Character, game_map: GameMap) -> Engine:
    # 1x1 Chunk-Welt für den Test
    return Engine(player, [[game_map]], 0, 0, Position(1, 1))


def test_character_take_damage(player: Character) -> None:
    player.take_damage(5)
    assert player.base_stats.hp == 95

    player.take_damage(200)
    assert player.base_stats.hp == 0
    assert not player.is_alive()


def test_character_level_up(player: Character) -> None:
    leveled_up = player.gain_xp(50)
    assert leveled_up is True
    assert player.level == 2
    assert player.base_stats.max_hp == 120
    assert player.base_stats.ad == 15


def test_engine_movement(engine: Engine) -> None:
    assert engine.move_player(1, 0) is True
    assert engine.player_pos == Position(2, 1)

    engine.game_map.set_tile(3, 1, TileType.WALL)
    assert engine.move_player(1, 0) is False
    assert engine.player_pos == Position(2, 1)

    # Boundary check (wird in Macro-World behandelt, aber für einzelne Map = False)
    engine.player_pos = Position(0, 0)
    assert engine.move_player(-1, 0) is False


@patch("random.random", return_value=0.5)
def test_resolve_combat(mock_random: MagicMock, engine: Engine) -> None:
    enemy_stats = Stats(hp=20, max_hp=20, ad=8, armor=0)
    enemy = Character("Weak Goblin", enemy_stats, [])

    won = engine.resolve_combat(enemy)
    assert won is True
    assert engine.player.is_alive()
    assert not enemy.is_alive()


@patch("random.random", return_value=0.5)
def test_combat_trigger_on_move(mock_random: MagicMock, engine: Engine) -> None:
    enemy_stats = Stats(hp=10, max_hp=10, ad=5, armor=0)
    enemy = Character("Small Rat", enemy_stats, [], gold=15)
    # Globale Koordinate: Chunk 0, 0 und Position 2, 1
    engine.spawn_enemy(0, 0, 2, 1, enemy)

    success = engine.move_player(1, 0)
    assert success is True
    assert engine.player_pos == Position(2, 1)
    assert engine.player.gold == 15
    assert (0, 0, 2, 1) not in engine.enemies
    assert engine.game_map.tiles[1][2] == TileType.EMPTY


def test_save_load(engine: Engine, tmp_path: Path) -> None:
    save_file = tmp_path / "test_save.json"
    engine.player.gold = 100
    engine.player_pos = Position(3, 3)

    engine.save_game(str(save_file))
    assert save_file.exists()

    new_engine = Engine.load_game(str(save_file))
    assert new_engine.player.name == engine.player.name
    assert new_engine.player.gold == 100
    assert new_engine.player_pos == Position(3, 3)
    assert new_engine.game_map.width == engine.game_map.width
