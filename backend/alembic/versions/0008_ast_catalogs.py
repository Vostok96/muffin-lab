"""load SIMCORE AST panels and reviewed organism catalog

Revision ID: 0008_ast_catalogs
Revises: 0007_specimen_hierarchy
Create Date: 2026-07-16
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

from alembic import op
import sqlalchemy as sa


revision = "0008_ast_catalogs"
down_revision = "0007_specimen_hierarchy"
branch_labels = None
depends_on = None

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def stable_id(entity: str, code: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"muffin:{entity}:{code}"))


def organism_code(name: str) -> str:
    digest = hashlib.sha1(name.casefold().encode("utf-8")).hexdigest()[:20].upper()
    return f"ORG_{digest}"


def upgrade() -> None:
    op.add_column(
        "ast_panel",
        sa.Column("display_order", sa.Integer(), nullable=True, server_default="999"),
    )
    op.execute("UPDATE ast_panel SET display_order = 999 WHERE display_order IS NULL")
    op.alter_column("ast_panel", "display_order", nullable=False)

    op.drop_constraint(
        "uq_ast_panel_antibiotic_display_order",
        "ast_panel_antibiotic",
        type_="unique",
    )
    op.create_index(
        "ix_ast_panel_antibiotic_display_order",
        "ast_panel_antibiotic",
        ["ast_panel_id", "display_order"],
    )
    op.add_column(
        "ast_panel_antibiotic",
        sa.Column(
            "default_interpretation",
            sa.String(length=10),
            nullable=True,
            server_default="S",
        ),
    )
    op.execute(
        "UPDATE ast_panel_antibiotic "
        "SET default_interpretation = 'S' WHERE default_interpretation IS NULL"
    )
    op.alter_column("ast_panel_antibiotic", "default_interpretation", nullable=False)

    bind = op.get_bind()
    organisms = json.loads((DATA_DIR / "organisms_v1.json").read_text(encoding="utf-8"))
    for name in organisms:
        existing_id = bind.execute(
            sa.text("SELECT id FROM organism WHERE lower(name) = lower(:name) LIMIT 1"),
            {"name": name},
        ).scalar()
        if existing_id:
            bind.execute(
                sa.text("UPDATE organism SET name = :name, is_active = true WHERE id = :id"),
                {"id": existing_id, "name": name},
            )
        else:
            bind.execute(
                sa.text(
                    "INSERT INTO organism (id, code, name, is_active) "
                    "VALUES (:id, :code, :name, true)"
                ),
                {
                    "id": stable_id("organism", name.casefold()),
                    "code": organism_code(name),
                    "name": name,
                },
            )
    op.execute("CREATE UNIQUE INDEX uq_organism_name_lower ON organism (lower(name))")

    panels = json.loads((DATA_DIR / "ast_panels_v1.json").read_text(encoding="utf-8"))
    if len(panels) != 7 or sum(len(panel["antibiotics"]) for panel in panels) != 79:
        raise ValueError("AST panel data must contain 7 panels and 79 relations")

    bind.execute(
        sa.text("UPDATE ast_panel SET is_active = false WHERE code = 'GN_URINE'")
    )

    for panel_data in panels:
        panel_id = bind.execute(
            sa.text(
                "INSERT INTO ast_panel (id, code, name, display_order, is_active) "
                "VALUES (:id, :code, :name, :display_order, true) "
                "ON CONFLICT (code) DO UPDATE SET "
                "name = EXCLUDED.name, display_order = EXCLUDED.display_order, is_active = true "
                "RETURNING id"
            ),
            {
                "id": stable_id("ast_panel", panel_data["code"]),
                "code": panel_data["code"],
                "name": panel_data["name"],
                "display_order": panel_data["display_order"],
            },
        ).scalar_one()
        for antibiotic_code, antibiotic_name, display_order in panel_data["antibiotics"]:
            antibiotic_id = bind.execute(
                sa.text(
                    "INSERT INTO antibiotic (id, code, name, is_active) "
                    "VALUES (:id, :code, :name, true) "
                    "ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, is_active = true "
                    "RETURNING id"
                ),
                {
                    "id": stable_id("antibiotic", antibiotic_code),
                    "code": antibiotic_code,
                    "name": antibiotic_name,
                },
            ).scalar_one()
            bind.execute(
                sa.text(
                    "INSERT INTO ast_panel_antibiotic "
                    "(ast_panel_id, antibiotic_id, display_order, default_method, default_interpretation) "
                    "VALUES (:panel_id, :antibiotic_id, :display_order, 'CMI', 'S') "
                    "ON CONFLICT (ast_panel_id, antibiotic_id) DO UPDATE SET "
                    "display_order = EXCLUDED.display_order, "
                    "default_method = EXCLUDED.default_method, "
                    "default_interpretation = EXCLUDED.default_interpretation"
                ),
                {
                    "panel_id": panel_id,
                    "antibiotic_id": antibiotic_id,
                    "display_order": display_order,
                },
            )


def downgrade() -> None:
    op.drop_index("uq_organism_name_lower", table_name="organism")
    op.drop_column("ast_panel_antibiotic", "default_interpretation")
    op.execute(
        "WITH ranked AS ("
        "SELECT ast_panel_id, antibiotic_id, "
        "row_number() OVER (PARTITION BY ast_panel_id ORDER BY display_order, antibiotic_id) AS new_order "
        "FROM ast_panel_antibiotic"
        ") UPDATE ast_panel_antibiotic target SET display_order = ranked.new_order "
        "FROM ranked WHERE target.ast_panel_id = ranked.ast_panel_id "
        "AND target.antibiotic_id = ranked.antibiotic_id"
    )
    op.drop_index(
        "ix_ast_panel_antibiotic_display_order",
        table_name="ast_panel_antibiotic",
    )
    op.create_unique_constraint(
        "uq_ast_panel_antibiotic_display_order",
        "ast_panel_antibiotic",
        ["ast_panel_id", "display_order"],
    )
    op.drop_column("ast_panel", "display_order")
