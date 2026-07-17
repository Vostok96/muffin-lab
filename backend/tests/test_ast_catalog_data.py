import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1] / "alembic" / "data"


def test_reviewed_organism_catalog_has_expected_size() -> None:
    organisms = json.loads((DATA_DIR / "organisms_v1.json").read_text(encoding="utf-8"))
    assert len(organisms) == 2452
    assert len({name.casefold() for name in organisms}) == 2452


def test_simcore_ast_panels_preserve_counts_and_orders() -> None:
    panels = json.loads((DATA_DIR / "ast_panels_v1.json").read_text(encoding="utf-8"))
    assert [(panel["display_order"], panel["name"]) for panel in panels] == [
        (1, "PANEL SIN ATB"),
        (10, "PANEL AST-N401"),
        (11, "PANEL AST-N402"),
        (13, "PANEL AST-N403"),
        (15, "PANEL AST-P663"),
        (16, "PANEL AST-ST03"),
        (17, "PANEL AST-YS08"),
    ]
    assert [len(panel["antibiotics"]) for panel in panels] == [0, 15, 12, 13, 17, 17, 5]
    assert sum(len(panel["antibiotics"]) for panel in panels) == 79
    n401_orders = [entry[2] for entry in panels[1]["antibiotics"]]
    assert n401_orders.count(5) == 2
    assert n401_orders.count(10) == 2
    assert n401_orders.count(11) == 2
