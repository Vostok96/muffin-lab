"""security foundation

Revision ID: 0001_security_foundation
Revises:
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_security_foundation"
down_revision = None
branch_labels = None
depends_on = None


def utc_now() -> sa.text:
    return sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "role",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
    )
    op.create_index("ix_role_code", "role", ["code"], unique=True)
    op.create_table(
        "user",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("given_name", sa.String(length=120), nullable=False),
        sa.Column("family_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now()),
    )
    op.create_index("ix_user_username", "user", ["username"], unique=True)
    op.create_table(
        "user_role",
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.String(length=36), sa.ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "laboratory_area",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("section", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now()),
    )
    op.create_index("ix_laboratory_area_code", "laboratory_area", ["code"], unique=True)
    op.create_table(
        "user_area_permission",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("laboratory_area_id", sa.String(length=36), sa.ForeignKey("laboratory_area.id", ondelete="CASCADE"), nullable=False),
        sa.Column("can_preliminary_validate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_final_validate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now()),
        sa.UniqueConstraint("user_id", "laboratory_area_id", name="uq_user_area_permission"),
    )
    op.create_table(
        "audit_event",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_user_id", sa.String(length=36), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now()),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_audit_event_entity_type", "audit_event", ["entity_type"])
    op.create_index("ix_audit_event_entity_id", "audit_event", ["entity_id"])
    op.create_index("ix_audit_event_action", "audit_event", ["action"])
    op.create_index("ix_audit_event_occurred_at", "audit_event", ["occurred_at"])


def downgrade() -> None:
    op.drop_table("audit_event")
    op.drop_table("user_area_permission")
    op.drop_table("laboratory_area")
    op.drop_table("user_role")
    op.drop_table("user")
    op.drop_table("role")
