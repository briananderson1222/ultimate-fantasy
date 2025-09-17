"""initial schema

Revision ID: 20250912_000001
Revises:
Create Date: 2025-09-12

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250912_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("user_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("cognito_sub", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("cognito_sub", name="uq_users_cognito_sub"),
    )

    # leagues
    op.create_table(
        "leagues",
        sa.Column(
            "league_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("league_type", sa.String(length=50), nullable=False),
        sa.Column("season", sa.String(length=16), nullable=False),
        sa.Column("commissioner_id", psql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["commissioner_id"], ["users.user_id"]),
    )

    # teams
    op.create_table(
        "teams",
        sa.Column("team_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("league_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.league_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
    )

    # players
    op.create_table(
        "players",
        sa.Column(
            "player_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("position", sa.String(length=20), nullable=False),
    )

    # rosters
    op.create_table(
        "rosters",
        sa.Column(
            "roster_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("team_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("acquisition_date", sa.DateTime(), nullable=False),
        sa.Column("acquisition_method", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.player_id"]),
    )

    # lineups
    op.create_table(
        "lineups",
        sa.Column(
            "lineup_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("team_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_day", sa.Date(), nullable=False),
        sa.Column("players", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"]),
    )

    # schedules
    op.create_table(
        "schedules",
        sa.Column(
            "schedule_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("league_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_day", sa.Date(), nullable=False),
        sa.Column("home_team_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("away_team_id", psql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.league_id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.team_id"]),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.team_id"]),
    )

    # scores
    op.create_table(
        "scores",
        sa.Column(
            "score_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("player_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_day", sa.Date(), nullable=False),
        sa.Column("stats", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.player_id"]),
    )

    # waivers
    op.create_table(
        "waivers",
        sa.Column(
            "waiver_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("league_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("bid", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.league_id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.player_id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"]),
    )

    # transactions
    op.create_table(
        "transactions",
        sa.Column(
            "transaction_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("league_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_type", sa.String(length=16), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.league_id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.player_id"]),
    )

    # notifications
    op.create_table(
        "notifications",
        sa.Column(
            "notification_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("user_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column(
            "is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
    )

    # rules
    op.create_table(
        "rules",
        sa.Column("rule_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("league_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.league_id"]),
    )

    # presets
    op.create_table(
        "presets",
        sa.Column(
            "preset_id", psql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("league_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("presets")
    op.drop_table("rules")
    op.drop_table("notifications")
    op.drop_table("transactions")
    op.drop_table("waivers")
    op.drop_table("scores")
    op.drop_table("schedules")
    op.drop_table("lineups")
    op.drop_table("rosters")
    op.drop_table("players")
    op.drop_table("teams")
    op.drop_table("leagues")
    op.drop_table("users")
