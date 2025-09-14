"""add user_preferences and league_branding

Revision ID: 20250913_000004
Revises: 20250913_000003
Create Date: 2025-09-13

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250913_000004"
down_revision = "20250913_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # user_preferences
    op.create_table(
        "user_preferences",
        sa.Column(
            "user_id",
            psql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "theme", sa.String(length=20), nullable=False, server_default="light"
        ),
        sa.Column(
            "density",
            sa.String(length=20),
            nullable=False,
            server_default="comfortable",
        ),
        sa.Column(
            "locale", sa.String(length=20), nullable=False, server_default="en-US"
        ),
        sa.Column("layouts", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )

    # league_branding
    op.create_table(
        "league_branding",
        sa.Column(
            "league_id",
            psql.UUID(as_uuid=True),
            sa.ForeignKey("leagues.league_id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("theme", sa.JSON(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )


def downgrade() -> None:
    op.drop_table("league_branding")
    op.drop_table("user_preferences")
