"""specimen hierarchy for cascading menus

Revision ID: 0007_specimen_hierarchy
Revises: 0006_outputs_integrations
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_specimen_hierarchy"
down_revision = "0006_outputs_integrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("specimen_type", sa.Column("parent_id", sa.String(length=36), nullable=True))
    op.add_column(
        "specimen_type",
        sa.Column("is_selectable", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_foreign_key(
        "fk_specimen_type_parent_id",
        "specimen_type",
        "specimen_type",
        ["parent_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_specimen_type_parent_id", "specimen_type", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_specimen_type_parent_id", table_name="specimen_type")
    op.drop_constraint("fk_specimen_type_parent_id", "specimen_type", type_="foreignkey")
    op.drop_column("specimen_type", "is_selectable")
    op.drop_column("specimen_type", "parent_id")
