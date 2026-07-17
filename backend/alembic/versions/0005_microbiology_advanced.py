"""microbiology advanced: organisms, isolates, AST

Revision ID: 0005_microbiology_advanced
Revises: 0004_results_validation
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_microbiology_advanced"
down_revision = "0004_results_validation"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    op.create_table(
        "organism",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index("ix_organism_code", "organism", ["code"], unique=True)

    op.create_table(
        "colony_count_option",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index("ix_colony_count_option_code", "colony_count_option", ["code"], unique=True)

    op.create_table(
        "defined_comment",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("text", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index("ix_defined_comment_code", "defined_comment", ["code"], unique=True)

    op.create_table(
        "antibiotic",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index("ix_antibiotic_code", "antibiotic", ["code"], unique=True)

    op.create_table(
        "ast_panel",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index("ix_ast_panel_code", "ast_panel", ["code"], unique=True)

    op.create_table(
        "ast_panel_antibiotic",
        sa.Column("ast_panel_id", sa.String(length=36), sa.ForeignKey("ast_panel.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("antibiotic_id", sa.String(length=36), sa.ForeignKey("antibiotic.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("default_method", sa.String(length=80), nullable=True),
        sa.UniqueConstraint("ast_panel_id", "display_order", name="uq_ast_panel_antibiotic_display_order"),
    )

    op.create_table(
        "isolate",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("result_id", sa.String(length=36), sa.ForeignKey("result.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organism_id", sa.String(length=36), sa.ForeignKey("organism.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("colony_count_option_id", sa.String(length=36), sa.ForeignKey("colony_count_option.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("phenotype", sa.String(length=500), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("ast_panel_id", sa.String(length=36), sa.ForeignKey("ast_panel.id", ondelete="RESTRICT"), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_isolate_result_id", "isolate", ["result_id"])

    op.create_table(
        "antimicrobial_result",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("isolate_id", sa.String(length=36), sa.ForeignKey("isolate.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("antibiotic_id", sa.String(length=36), sa.ForeignKey("antibiotic.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mic_value", sa.String(length=80), nullable=True),
        sa.Column("interpretation", sa.String(length=10), nullable=False),
        sa.Column("method", sa.String(length=80), nullable=True),
        sa.Column("is_reportable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("isolate_id", "antibiotic_id", name="uq_antimicrobial_result_isolate_antibiotic"),
        sa.CheckConstraint(
            "interpretation IN ('S', 'SDD', 'I', 'R', 'POS', 'NEG', 'NA')",
            name="ck_antimicrobial_result_interpretation",
        ),
        *timestamps(),
    )
    op.create_index("ix_antimicrobial_result_isolate_id", "antimicrobial_result", ["isolate_id"])


def downgrade() -> None:
    op.drop_table("antimicrobial_result")
    op.drop_table("isolate")
    op.drop_table("ast_panel_antibiotic")
    op.drop_table("ast_panel")
    op.drop_table("antibiotic")
    op.drop_table("defined_comment")
    op.drop_table("colony_count_option")
    op.drop_table("organism")
