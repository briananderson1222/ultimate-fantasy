"""scoreboard aggregation indexes

Revision ID: 20250912_000002
Revises: 20250912_000001
Create Date: 2025-09-12

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250912_000002"
down_revision = "20250912_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_scores_player_id_game_day",
        "scores",
        ["player_id", "game_day"],
        unique=False,
    )
    op.create_index(
        "ix_lineups_team_id_game_day", "lineups", ["team_id", "game_day"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_lineups_team_id_game_day", table_name="lineups")
    op.drop_index("ix_scores_player_id_game_day", table_name="scores")
