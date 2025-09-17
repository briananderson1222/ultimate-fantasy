"""read API helper indexes

Revision ID: 20250913_000003
Revises: 20250912_000002
Create Date: 2025-09-13

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250913_000003"
down_revision = "20250912_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # teams: for listing by user and by league
    op.create_index("ix_teams_user_id", "teams", ["user_id"], unique=False)
    op.create_index("ix_teams_league_id", "teams", ["league_id"], unique=False)

    # waivers: filter by league and (optionally) team
    op.create_index(
        "ix_waivers_league_team", "waivers", ["league_id", "team_id"], unique=False
    )


def downgrade() -> None:
    # Drop created indexes (ignore if not present)
    try:
        op.drop_index("ix_waivers_league_team", table_name="waivers")
    except Exception:
        pass
    try:
        op.drop_index("ix_teams_league_id", table_name="teams")
    except Exception:
        pass
    try:
        op.drop_index("ix_teams_user_id", table_name="teams")
    except Exception:
        pass
    # Do not drop ix_lineups_team_id_game_day here; it belongs to prior migration
