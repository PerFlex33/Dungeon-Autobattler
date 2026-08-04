from pathlib import Path

import pytest

from dungeon_autobattler.engine import Engine, GameMap, Position, TileType
from dungeon_autobattler.models import Character, Stats


@pytest.fixture
def basic_stats() -> Stats:
    return Stats(hp=100, max_hp=100, ad=10, defense=5)


@pytest.fixture
def player(basic_stats: Stats) -> Character:
    return Character(name="Held", base_stats=basic_stats, items=[])


@pytest.fixture
def game_map() -> GameMap:
    return GameMap(width=10, height=10)


@pytest.fixture
def engine(player: Character, game_map: GameMap) -> Engine:
    return Engine(player, game_map, Position(1, 1))


def test_character_take_damage(player: Character) -> None:
    # ad=10 vs defense=5 -> 5 damage
    player.take_damage(10)
    assert player.base_stats.hp == 95

    # ad=2 vs defense=5 -> min 1 damage
    player.take_damage(2)
    assert player.base_stats.hp == 94

    # massive damage
    player.take_damage(200)
    assert player.base_stats.hp == 0
    assert not player.is_alive()


def test_character_level_up(player: Character) -> None:
    # xp_needed = level * 50 = 50
    leveled_up = player.gain_xp(50)
    assert leveled_up is True
    assert player.level == 2
    assert player.base_stats.max_hp == 120
    assert player.base_stats.ad == 15
    assert player.base_stats.defense == 7


def test_engine_movement(engine: Engine) -> None:
    # Normal move
    assert engine.move_player(1, 0) is True
    assert engine.player_pos == Position(2, 1)

    # Wall collision
    engine.game_map.set_tile(3, 1, TileType.WALL)
    assert engine.move_player(1, 0) is False
    assert engine.player_pos == Position(2, 1)

    # Boundary check
    engine.player_pos = Position(0, 0)
    assert engine.move_player(-1, 0) is False


def test_resolve_combat(engine: Engine) -> None:
    enemy_stats = Stats(hp=20, max_hp=20, ad=8, defense=0)
    enemy = Character("Weak Goblin", enemy_stats, [])

    # Player: 100 HP, 10 AD, 5 DEF
    # Enemy: 20 HP, 8 AD, 0 DEF
    # Round 1: Player hits Enemy for 10 -> Enemy has 10. Enemy hits Player for (8-5)=3 -> Player has 97.
    # Round 2: Player hits Enemy for 10 -> Enemy has 0. Player wins.

    won = engine.resolve_combat(enemy)
    assert won is True
    assert engine.player.is_alive()
    assert not enemy.is_alive()


def test_combat_trigger_on_move(engine: Engine) -> None:
    enemy_stats = Stats(hp=10, max_hp=10, ad=5, defense=0)
    enemy = Character("Small Rat", enemy_stats, [], gold=15)
    engine.spawn_enemy(2, 1, enemy)

    # Move onto enemy tile
    success = engine.move_player(1, 0)
    assert success is True
    assert engine.player_pos == Position(2, 1)
    assert engine.player.gold == 15
    assert (2, 1) not in engine.enemies
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
