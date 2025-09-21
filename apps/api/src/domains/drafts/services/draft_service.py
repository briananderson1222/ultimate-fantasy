"""
DraftService with real-time coordination.

Implements T036 requirements:
- Real-time draft coordination
- Snake draft algorithm
- Pick validation and timer management
- WebSocket integration for live updates
- Auto-draft functionality
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from domains.drafts.models.draft import Draft
from domains.leagues.models.team import Team
from domains.sports.models.player import Player
from infrastructure.cache.redis_pool import FantasyRedisPool, get_redis_pool
from infrastructure.observability.tracing import get_tracer, trace_draft_operation


logger = logging.getLogger(__name__)
tracer = get_tracer()


class DraftStatus(Enum):
    """Draft status enumeration."""
    SETUP = "setup"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class DraftPick:
    """Draft pick information."""
    pick_number: int
    round_number: int
    team_id: str
    player_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    is_auto_pick: bool = False
    time_taken: Optional[int] = None


@dataclass
class DraftState:
    """Current draft state."""
    draft_id: str
    league_id: str
    status: DraftStatus
    current_pick: int
    current_round: int
    current_team_id: str
    time_remaining: Optional[int]
    pick_history: List[DraftPick]
    available_players: List[str]
    draft_order: List[str]


@dataclass
class DraftConfig:
    """Draft configuration."""
    draft_type: str = "snake"
    rounds: int = 16
    pick_time_limit: int = 120  # seconds
    auto_draft_enabled: bool = True
    pause_on_disconnect: bool = True
    allow_trades_during_draft: bool = False


class DraftTimer:
    """Manages draft pick timers."""

    def __init__(self, draft_service: 'DraftService'):
        self.draft_service = draft_service
        self._timers: Dict[str, asyncio.Task] = {}

    async def start_pick_timer(
        self,
        draft_id: str,
        team_id: str,
        seconds: int
    ) -> None:
        """Start timer for current pick."""
        # Cancel existing timer
        await self.cancel_timer(draft_id)

        # Start new timer
        timer_task = asyncio.create_task(
            self._pick_timer_task(draft_id, team_id, seconds)
        )
        self._timers[draft_id] = timer_task

    async def cancel_timer(self, draft_id: str) -> None:
        """Cancel active timer for draft."""
        if draft_id in self._timers:
            self._timers[draft_id].cancel()
            del self._timers[draft_id]

    async def _pick_timer_task(
        self,
        draft_id: str,
        team_id: str,
        seconds: int
    ) -> None:
        """Timer task that handles auto-pick on timeout."""
        try:
            await asyncio.sleep(seconds)
            # Time expired - trigger auto pick
            await self.draft_service.auto_pick(draft_id, team_id)
        except asyncio.CancelledError:
            # Timer was cancelled (pick was made)
            pass


class DraftService:
    """
    Service for managing fantasy drafts with real-time coordination.

    Features:
    - Snake draft algorithm with proper turn order
    - Real-time WebSocket updates
    - Pick timers with auto-draft
    - Draft state persistence and caching
    - Player availability tracking
    - Draft pause/resume functionality
    """

    def __init__(
        self,
        redis_pool: Optional[FantasyRedisPool] = None,
        websocket_manager: Optional[Any] = None  # WebSocket manager will be injected
    ):
        """
        Initialize draft service.

        Args:
            redis_pool: Redis connection for caching draft state
            websocket_manager: WebSocket manager for real-time updates
        """
        self.redis_pool = redis_pool
        self.websocket_manager = websocket_manager
        self.timer = DraftTimer(self)

        # Cache TTL settings
        self.cache_ttl = {
            "draft_state": 60,      # 1 minute
            "pick_history": 300,    # 5 minutes
            "available_players": 60  # 1 minute
        }

    async def create_draft(
        self,
        league_id: str,
        config: DraftConfig,
        db: Session
    ) -> str:
        """
        Create a new draft.

        Args:
            league_id: League identifier
            config: Draft configuration
            db: Database session

        Returns:
            Draft ID
        """
        with trace_draft_operation(
            tracer, "create_draft",
            draft_id="", league_id=league_id
        ) as span:
            # Get teams in league
            teams = db.query(Team).filter(Team.league_id == league_id).all()
            if not teams:
                raise ValueError("No teams found in league")

            # Create draft record
            draft = Draft(
                league_id=league_id,
                draft_type=config.draft_type,
                status=DraftStatus.SETUP.value,
                rounds=config.rounds,
                pick_time_limit=config.pick_time_limit,
                auto_draft_enabled=config.auto_draft_enabled,
                current_pick=0,
                current_round=1
            )

            db.add(draft)
            db.commit()
            db.refresh(draft)

            draft_id = str(draft.draft_id)
            span.set_attribute("draft_id", draft_id)

            # Generate draft order
            draft_order = self._generate_draft_order(teams, config)

            # Initialize draft state
            draft_state = DraftState(
                draft_id=draft_id,
                league_id=league_id,
                status=DraftStatus.SETUP,
                current_pick=0,
                current_round=1,
                current_team_id="",
                time_remaining=None,
                pick_history=[],
                available_players=[],  # Will be populated when draft starts
                draft_order=draft_order
            )

            # Cache draft state
            await self._cache_draft_state(draft_state)

            span.set_attribute("teams_count", len(teams))
            span.set_attribute("draft_order_generated", True)

            return draft_id

    async def start_draft(
        self,
        draft_id: str,
        db: Session
    ) -> DraftState:
        """
        Start the draft process.

        Args:
            draft_id: Draft identifier
            db: Database session

        Returns:
            Updated draft state
        """
        with trace_draft_operation(
            tracer, "start_draft",
            draft_id=draft_id
        ) as span:
            # Get draft state
            draft_state = await self._get_draft_state(draft_id, db)
            if not draft_state:
                raise ValueError("Draft not found")

            if draft_state.status != DraftStatus.SETUP:
                raise ValueError("Draft not in setup state")

            # Update status
            draft_state.status = DraftStatus.ACTIVE
            draft_state.current_pick = 1
            draft_state.current_team_id = draft_state.draft_order[0]

            # Initialize available players
            draft_state.available_players = await self._get_available_players(db)

            # Update database
            draft = db.query(Draft).filter(Draft.draft_id == draft_id).first()
            if draft:
                draft.status = DraftStatus.ACTIVE.value
                draft.started_at = datetime.utcnow()
                draft.current_pick = 1
                db.commit()

            # Cache updated state
            await self._cache_draft_state(draft_state)

            # Start pick timer
            await self.timer.start_pick_timer(
                draft_id,
                draft_state.current_team_id,
                draft.pick_time_limit if draft else 120
            )

            # Broadcast start event
            await self._broadcast_draft_event(
                draft_id, "draft_started", {"draft_state": draft_state.__dict__}
            )

            span.set_attribute("draft_started", True)
            span.set_attribute("available_players_count", len(draft_state.available_players))

            return draft_state

    async def make_pick(
        self,
        draft_id: str,
        team_id: str,
        player_id: str,
        db: Session,
        is_auto_pick: bool = False
    ) -> DraftPick:
        """
        Make a draft pick.

        Args:
            draft_id: Draft identifier
            team_id: Team making the pick
            player_id: Player being picked
            db: Database session
            is_auto_pick: Whether this is an auto pick

        Returns:
            Draft pick information
        """
        with trace_draft_operation(
            tracer, "make_pick",
            draft_id=draft_id, team_id=team_id, player_id=player_id
        ) as span:
            span.set_attribute("is_auto_pick", is_auto_pick)

            # Get and validate draft state
            draft_state = await self._get_draft_state(draft_id, db)
            if not draft_state:
                raise ValueError("Draft not found")

            if draft_state.status != DraftStatus.ACTIVE:
                raise ValueError("Draft is not active")

            if draft_state.current_team_id != team_id:
                raise ValueError("Not your turn to pick")

            if player_id not in draft_state.available_players:
                raise ValueError("Player not available or already drafted")

            # Cancel pick timer
            await self.timer.cancel_timer(draft_id)

            # Create pick
            pick = DraftPick(
                pick_number=draft_state.current_pick,
                round_number=draft_state.current_round,
                team_id=team_id,
                player_id=player_id,
                timestamp=datetime.utcnow(),
                is_auto_pick=is_auto_pick
            )

            # Update draft state
            draft_state.pick_history.append(pick)
            draft_state.available_players.remove(player_id)

            # Calculate next pick
            await self._advance_to_next_pick(draft_state, db)

            # Cache updated state
            await self._cache_draft_state(draft_state)

            # Broadcast pick event
            await self._broadcast_draft_event(
                draft_id, "pick_made", {
                    "pick": pick.__dict__,
                    "next_pick": {
                        "team_id": draft_state.current_team_id,
                        "pick_number": draft_state.current_pick,
                        "time_remaining": draft_state.time_remaining
                    }
                }
            )

            span.set_attribute("pick_successful", True)
            span.set_attribute("next_team_id", draft_state.current_team_id)

            return pick

    async def auto_pick(
        self,
        draft_id: str,
        team_id: str
    ) -> Optional[DraftPick]:
        """
        Automatically make a pick when timer expires.

        Args:
            draft_id: Draft identifier
            team_id: Team that should pick

        Returns:
            Auto pick information or None if failed
        """
        with trace_draft_operation(
            tracer, "auto_pick",
            draft_id=draft_id, team_id=team_id
        ) as span:
            try:
                # Get available players
                from sqlalchemy.orm import sessionmaker
                from infrastructure.database.session_factory import get_session_factory

                session_factory = get_session_factory()
                with session_factory.get_sync_session() as db:
                    draft_state = await self._get_draft_state(draft_id, db)
                    if not draft_state or draft_state.current_team_id != team_id:
                        span.set_attribute("auto_pick_invalid", True)
                        return None

                    # Pick highest ranked available player
                    best_player = await self._get_best_available_player(
                        draft_state.available_players, db
                    )

                    if best_player:
                        pick = await self.make_pick(
                            draft_id, team_id, best_player, db, is_auto_pick=True
                        )
                        span.set_attribute("auto_pick_successful", True)
                        return pick

            except Exception as e:
                logger.error(f"Auto pick failed for {draft_id}/{team_id}: {e}")
                span.set_attribute("auto_pick_error", str(e))

            return None

    async def get_draft_state(
        self,
        draft_id: str,
        db: Session
    ) -> Optional[DraftState]:
        """Get current draft state."""
        return await self._get_draft_state(draft_id, db)

    async def pause_draft(
        self,
        draft_id: str,
        db: Session
    ) -> bool:
        """Pause an active draft."""
        draft_state = await self._get_draft_state(draft_id, db)
        if not draft_state or draft_state.status != DraftStatus.ACTIVE:
            return False

        draft_state.status = DraftStatus.PAUSED
        await self.timer.cancel_timer(draft_id)
        await self._cache_draft_state(draft_state)

        # Update database
        draft = db.query(Draft).filter(Draft.draft_id == draft_id).first()
        if draft:
            draft.status = DraftStatus.PAUSED.value
            db.commit()

        await self._broadcast_draft_event(draft_id, "draft_paused", {})
        return True

    async def resume_draft(
        self,
        draft_id: str,
        db: Session
    ) -> bool:
        """Resume a paused draft."""
        draft_state = await self._get_draft_state(draft_id, db)
        if not draft_state or draft_state.status != DraftStatus.PAUSED:
            return False

        draft_state.status = DraftStatus.ACTIVE
        await self._cache_draft_state(draft_state)

        # Update database
        draft = db.query(Draft).filter(Draft.draft_id == draft_id).first()
        if draft:
            draft.status = DraftStatus.ACTIVE.value
            db.commit()

            # Restart timer
            await self.timer.start_pick_timer(
                draft_id, draft_state.current_team_id, draft.pick_time_limit
            )

        await self._broadcast_draft_event(draft_id, "draft_resumed", {})
        return True

    def _generate_draft_order(
        self,
        teams: List[Team],
        config: DraftConfig
    ) -> List[str]:
        """Generate draft order for snake draft."""
        if config.draft_type != "snake":
            raise ValueError("Only snake draft supported currently")

        # Sort teams by draft order (or random if not set)
        sorted_teams = sorted(teams, key=lambda t: t.draft_order or 999)
        team_ids = [str(t.team_id) for t in sorted_teams]

        return team_ids

    async def _advance_to_next_pick(
        self,
        draft_state: DraftState,
        db: Session
    ) -> None:
        """Advance draft to next pick."""
        total_teams = len(draft_state.draft_order)
        total_picks = total_teams * draft_state.current_round

        if draft_state.current_pick >= total_picks:
            # Round complete - check if draft is done
            if draft_state.current_round >= db.query(Draft).filter(
                Draft.draft_id == draft_state.draft_id
            ).first().rounds:
                # Draft complete
                draft_state.status = DraftStatus.COMPLETED
                await self._broadcast_draft_event(
                    draft_state.draft_id, "draft_completed", {}
                )
                return
            else:
                # Next round
                draft_state.current_round += 1
                draft_state.current_pick += 1
        else:
            draft_state.current_pick += 1

        # Calculate team for this pick (snake order)
        pick_in_round = draft_state.current_pick - (
            (draft_state.current_round - 1) * total_teams
        )

        if draft_state.current_round % 2 == 1:
            # Odd round - normal order
            team_index = pick_in_round - 1
        else:
            # Even round - reverse order
            team_index = total_teams - pick_in_round

        draft_state.current_team_id = draft_state.draft_order[team_index]

        # Start timer for next pick
        draft = db.query(Draft).filter(Draft.draft_id == draft_state.draft_id).first()
        if draft and draft_state.status == DraftStatus.ACTIVE:
            await self.timer.start_pick_timer(
                draft_state.draft_id,
                draft_state.current_team_id,
                draft.pick_time_limit
            )

    async def _get_draft_state(
        self,
        draft_id: str,
        db: Session
    ) -> Optional[DraftState]:
        """Get draft state from cache or database."""
        # Try cache first
        if self.redis_pool:
            cached_state = await self.redis_pool.get("draft", draft_id, "state")
            if cached_state:
                return DraftState(**cached_state)

        # Fallback to database
        draft = db.query(Draft).filter(Draft.draft_id == draft_id).first()
        if not draft:
            return None

        # Build state from database
        teams = db.query(Team).filter(Team.league_id == draft.league_id).all()
        draft_order = [str(t.team_id) for t in sorted(teams, key=lambda t: t.draft_order or 999)]

        # For now, return basic state (in real implementation, would reconstruct from picks)
        return DraftState(
            draft_id=draft_id,
            league_id=str(draft.league_id),
            status=DraftStatus(draft.status),
            current_pick=draft.current_pick,
            current_round=draft.current_round,
            current_team_id=draft_order[0] if draft_order else "",
            time_remaining=None,
            pick_history=[],
            available_players=[],
            draft_order=draft_order
        )

    async def _cache_draft_state(self, draft_state: DraftState) -> None:
        """Cache draft state."""
        if self.redis_pool:
            await self.redis_pool.set(
                "draft", draft_state.draft_id, draft_state.__dict__,
                ttl=self.cache_ttl["draft_state"], suffix="state"
            )

    async def _get_available_players(self, db: Session) -> List[str]:
        """Get list of available player IDs."""
        # In real implementation, would query available players
        # For now, return mock data
        players = db.query(Player).filter(Player.status == "active").limit(200).all()
        return [str(p.player_id) for p in players]

    async def _get_best_available_player(
        self,
        available_players: List[str],
        db: Session
    ) -> Optional[str]:
        """Get best available player for auto pick."""
        if not available_players:
            return None

        # Simple implementation - return first available
        # In real implementation, would use ranking algorithm
        return available_players[0]

    async def _broadcast_draft_event(
        self,
        draft_id: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Broadcast draft event via WebSocket."""
        if self.websocket_manager:
            event = {
                "type": event_type,
                "draft_id": draft_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            await self.websocket_manager.broadcast_to_draft(draft_id, event)


# Global service instance
_draft_service: Optional[DraftService] = None


async def get_draft_service() -> DraftService:
    """Get the global draft service instance."""
    global _draft_service
    if _draft_service is None:
        redis_pool = await get_redis_pool()
        _draft_service = DraftService(redis_pool=redis_pool)
    return _draft_service


def reset_draft_service():
    """Reset the global service (useful for testing)."""
    global _draft_service
    _draft_service = None
