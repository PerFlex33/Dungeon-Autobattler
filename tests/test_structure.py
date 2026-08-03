import ast
import importlib
import pkgutil
import tomllib
from pathlib import Path

import dungeon_autobattler


def test_alle_module_importierbar() -> None:
    """Stellt sicher, dass jedes Modul im Paket fehlerfrei importiert werden kann."""
    package = dungeon_autobattler
    fehler = []
    for _, name, _ in pkgutil.walk_packages(
        package.__path__, prefix=f"{package.__name__}."
    ):
        try:
            importlib.import_module(name)
        except Exception as e:  # noqa: BLE001
            fehler.append(f"{name}: {e}")
    assert not fehler, f"Import-Fehler: {fehler}"


def test_pyproject_hat_pflichtfelder() -> None:
    """Prüft, dass pyproject.toml existiert und Kernfelder enthält."""
    pfad = Path(__file__).parent.parent / "pyproject.toml"
    with pfad.open("rb") as f:
        daten = tomllib.load(f)

    assert "project" in daten
    assert "name" in daten["project"]
    assert "dependencies" in daten["project"]


def test_keine_nackten_except_blocke() -> None:
    """Verhindert `except:` ohne spezifizierten Exception-Typ im Quellcode."""
    src_dir = Path(__file__).parent.parent / "src"
    verstoesse = []
    for datei in src_dir.rglob("*.py"):
        baum = ast.parse(datei.read_text(encoding="utf-8"))
        for knoten in ast.walk(baum):
            if isinstance(knoten, ast.ExceptHandler) and knoten.type is None:
                verstoesse.append(f"{datei}:{knoten.lineno}")
    assert not verstoesse, f"Nackte except-Blöcke gefunden: {verstoesse}"
