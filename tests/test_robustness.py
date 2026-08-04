import json
from pathlib import Path

import pytest

from dungeon_autobattler.engine import Engine, GameMap, Position
from dungeon_autobattler.models import (
    Character,
    Item,
    LoadGameError,
    Rarity,
    Stats,
)


@pytest.fixture
def engine() -> Engine:
    stats = Stats(hp=100, max_hp=100, ad=10, defense=5)
    player = Character(name="Held", base_stats=stats, items=[])
    game_map = GameMap(width=10, height=10)
    return Engine(player, game_map, Position(1, 1))


def test_stats_validation() -> None:
    # Negative max_hp
    with pytest.raises(
        ValueError, match="Maximale HP dürfen nicht negativ sein"
    ):
        Stats(hp=10, max_hp=-1, ad=1, defense=0)

    # Negative ad
    with pytest.raises(ValueError, match="Angriffskraft"):
        Stats(hp=10, max_hp=10, ad=-5, defense=0)

    # HP capping
    s = Stats(hp=200, max_hp=100, ad=10, defense=5)
    assert s.hp == 100


def test_item_bonus_consistency() -> None:
    base = Stats(hp=50, max_hp=50, ad=10, defense=5)
    item_stats = Stats(hp=20, max_hp=20, ad=5, defense=5)
    item = Item("Test Item", Rarity.COMMON, item_stats)
    char = Character("Hero", base, [item])

    curr = char.current_stats
    assert curr.hp == 70
    assert curr.max_hp == 70
    assert curr.ad == 15
    assert curr.defense == 10

    # take_damage should use current defense (10)
    # Damage 20 - 10 Def = 10 damage to base hp
    char.take_damage(20)
    assert char.base_stats.hp == 40
    assert char.current_stats.hp == 60


def test_negative_damage() -> None:
    char = Character("Hero", Stats(50, 50, 10, 5), [])
    with pytest.raises(
        ValueError, match="Schadenswert darf nicht negativ sein"
    ):
        char.take_damage(-10)


def test_load_game_corrupt_json(tmp_path: Path) -> None:
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("invalid json")
    from dungeon_autobattler.engine import Engine

    with pytest.raises(LoadGameError, match="Fehler beim Laden"):
        Engine.load_game(str(corrupt_file))


def test_load_game_missing_keys(tmp_path: Path) -> None:
    missing_key_file = tmp_path / "missing.json"
    missing_key_file.write_text(json.dumps({"player": {}}))
    from dungeon_autobattler.engine import Engine

    with pytest.raises(LoadGameError, match="Fehler beim Laden"):
        Engine.load_game(str(missing_key_file))


def test_invalid_move(engine: Engine) -> None:
    from dungeon_autobattler.models import InvalidMoveError

    with pytest.raises(InvalidMoveError, match="maximal 1 Feld"):
        engine.move_player(2, 0)


def test_combat_preconditions(engine: Engine) -> None:
    from dungeon_autobattler.models import Character, DungeonError, Stats

    enemy = Character("Dead Goblin", Stats(0, 30, 5, 2), [])
    with pytest.raises(DungeonError, match="Gegner ist bereits tot"):
        engine.resolve_combat(enemy)

    engine.player.base_stats.hp = 0
    with pytest.raises(DungeonError, match="toter Spieler"):
        engine.resolve_combat(enemy)
