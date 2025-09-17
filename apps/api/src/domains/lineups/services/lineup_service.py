from __future__ import annotations

import builtins
import uuid
from collections.abc import Iterable
from datetime import date

from sqlalchemy.orm import Session

from domains.lineups.models.lineup import Lineup
from domains.shared.events.publisher import DomainEventPublisher
from domains.shared.interfaces.lineup_service import LineupServiceInterface
from infrastructure.events.dispatcher import get_event_dispatcher


class LineupService(LineupServiceInterface):
    def __init__(self, session: Session) -> None:
        self.session = session

        # Initialize event publishing
        try:
            dispatcher = get_event_dispatcher()
            self.event_publisher = DomainEventPublisher(dispatcher, "lineups")
        except RuntimeError:
            # Event dispatcher not initialized, disable events
            self.event_publisher = None

    def set_lineup(
        self, *, team_id: str | uuid.UUID, game_day: date, players: Iterable[dict]
    ) -> Lineup:
        # TODO: enforce league rules and roster checks (positions, duplicates, etc.)
        team_uuid = uuid.UUID(team_id) if isinstance(team_id, str) else team_id

        # Convert UUIDs to strings for JSON serialization
        serializable_players = []
        for player in players:
            player_copy = player.copy()
            if "player_id" in player_copy and hasattr(player_copy["player_id"], "hex"):
                player_copy["player_id"] = str(player_copy["player_id"])
            serializable_players.append(player_copy)

        lineup = Lineup(
            team_id=team_uuid,
            game_day=game_day,
            players=serializable_players,
            version=1,
        )
        self.session.add(lineup)
        self.session.flush()

        # Publish lineup set event
        if self.event_publisher:
            try:
                import asyncio
                asyncio.create_task(self.event_publisher.publish_event(
                    "lineup_set",
                    str(lineup.lineup_id),
                    {
                        "lineup_id": str(lineup.lineup_id),
                        "team_id": str(team_uuid),
                        "game_day": game_day.isoformat(),
                        "player_count": len(serializable_players),
                        "version": 1,
                    }
                ))

                # Publish integration event for scoring domain
                asyncio.create_task(self.event_publisher.publish_integration_event(
                    "lineup_updated",
                    str(lineup.lineup_id),
                    {
                        "lineup_id": str(lineup.lineup_id),
                        "team_id": str(team_uuid),
                        "game_day": game_day.isoformat(),
                        "players": serializable_players,
                    },
                    target_domains=["scoring"]
                ))
            except Exception as e:
                pass

        return lineup

    def list(
        self,
        *,
        team_id: str | uuid.UUID,
        game_day: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Lineup]:
        team_uuid = uuid.UUID(team_id) if isinstance(team_id, str) else team_id
        q = self.session.query(Lineup).filter(Lineup.team_id == team_uuid)
        if game_day is not None:
            q = q.filter(Lineup.game_day == game_day)
        q = q.offset(max(0, offset)).limit(max(1, min(100, limit)))
        return q.all()

    # Interface implementation methods
    async def get_lineup(self, lineup_id: str) -> Lineup:
        """Get lineup by ID."""
        lineup_uuid = uuid.UUID(lineup_id)
        lineup = self.session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            raise ValueError(f"Lineup with ID {lineup_id} not found")
        return lineup

    async def validate_lineup_ownership(self, lineup_id: str, user_id: str) -> bool:
        """Validate if a user owns a specific lineup."""
        from domains.leagues.models.team import Team

        lineup_uuid = uuid.UUID(lineup_id)
        user_uuid = uuid.UUID(user_id)

        # Get the lineup
        lineup = self.session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            return False

        # Check if the user owns the team that owns this lineup
        team = self.session.query(Team).filter(Team.team_id == lineup.team_id).first()
        if not team:
            return False

        return team.user_id == user_uuid

    async def get_lineup_by_user_league(self, user_id: str, league_id: str) -> Lineup:
        """Get user's lineup for a specific league."""
        from domains.leagues.models.team import Team

        user_uuid = uuid.UUID(user_id)
        league_uuid = uuid.UUID(league_id)

        # Find the user's team in the league
        team = (
            self.session.query(Team)
            .filter(Team.user_id == user_uuid, Team.league_id == league_uuid)
            .first()
        )
        if not team:
            raise ValueError(f"User {user_id} has no team in league {league_id}")

        # Find the most recent lineup for this team
        lineup = (
            self.session.query(Lineup)
            .filter(Lineup.team_id == team.team_id)
            .order_by(Lineup.game_day.desc())
            .first()
        )
        if not lineup:
            raise ValueError(f"No lineup found for user {user_id} in league {league_id}")

        return lineup

    async def get_lineups_by_league(self, league_id: str) -> builtins.list[Lineup]:
        """Get all lineups for a specific league."""
        from domains.leagues.models.team import Team

        league_uuid = uuid.UUID(league_id)

        # Get all teams in the league
        teams = self.session.query(Team).filter(Team.league_id == league_uuid).all()
        team_ids = [team.team_id for team in teams]

        # Get all lineups for these teams
        lineups = self.session.query(Lineup).filter(Lineup.team_id.in_(team_ids)).all()
        return lineups

    async def is_lineup_active(self, lineup_id: str) -> bool:
        """Check if a lineup is active for the current period."""
        lineup_uuid = uuid.UUID(lineup_id)
        lineup = self.session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            return False

        # For now, all lineups are considered active
        # In the future, this could check against current game week/day
        return True

    async def get_lineup_slots(self, lineup_id: str) -> builtins.list[dict]:
        """Get all slots for a specific lineup."""
        lineup_uuid = uuid.UUID(lineup_id)
        lineup = self.session.query(Lineup).filter(Lineup.lineup_id == lineup_uuid).first()
        if not lineup:
            raise ValueError(f"Lineup with ID {lineup_id} not found")

        # Return the players list as slots
        # This could be enhanced to return actual LineupSlot objects in the future
        return lineup.players or []
