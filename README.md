# Dungeon Autobattler

2D-Dungeon-Crawler mit Autobattler-Kampfmechanik (Python, Pygame CE).

## Installation

```bash
uv sync
```

## Starten

```bash
uv run python -m dungeon_autobattler.main
```

## Steuerung

| Taste(n)        | Aktion                                              |
|------------------|------------------------------------------------------|
| `W` `A` `S` `D`  | Bewegen (löst Kampf bei Gegnerfeldern aus)            |
| `E`              | Interagieren (Shop) / im Menü auswählen & bestätigen  |
| `I`              | Inventar öffnen/schließen                             |
| `K`              | Skill-Menü öffnen/schließen                           |
| `F5`             | Spielstand speichern                                  |
| `F9` / `L`       | Spielstand laden                                      |
| `Entf`           | Spielstand löschen                                    |
| `ESC`            | Menü schließen                                        |

**Inventar:** `W`/`S` navigieren, `E` anlegen/benutzen.
**Shop:** `Tab` Kaufen/Verkaufen, `W`/`S` navigieren, `E` bestätigen, `Q`/`ESC` verlassen.
**Skills:** `W`/`S` wählen, `E` bestätigen, `K` schließen.
