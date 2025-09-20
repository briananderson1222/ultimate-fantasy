from __future__ import annotations

import uuid as _uuid
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..models.draft import Draft
from ..models.league import League
from ..models.team import Team
from ..models.player import Player
from ..models.notification import Notification
from ..infrastructure.database.session_factory import get_db_session
from ..infrastructure.logging.domain_logger import get_logger

logger = get_logger(__name__)


class DraftStatus(Enum):
    """Draft status types"""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class DraftType(Enum):
    """Draft types"""
    SNAKE = "snake"
    AUCTION = "auction"
    LINEAR = "linear"


@dataclass
class DraftPick:
    """Draft pick information"""
    pick_number: int
    round_number: int
    team_id: str
    player_id: Optional[str] = None
    pick_time: Optional[datetime] = None
    is_autopick: bool = False


@dataclass
class DraftSettings:
    """Draft configuration settings"""
    draft_type: str = "snake"
    pick_timer_seconds: int = 90
    auto_draft_enabled: bool = True
    draft_order: List[str] = None  # List of team_ids in order
    pause_between_rounds: bool = False
    allow_pick_trading: bool = False


class DraftServiceError(Exception):
    """Base exception for draft service errors"""
    pass


class DraftNotFoundError(DraftServiceError):
    """Draft not found errors"""
    pass


class InvalidDraftStateError(DraftServiceError):
    """Invalid draft state errors"""
    pass


class PickTimerExpiredError(DraftServiceError):
    """Pick timer expired errors"""
    pass


class DraftService:
    """
    Draft service for player selection process

    Implements T030 requirements:
    - DraftService for player selection process
    - Add draft management, pick validation, timer handling
    - Include snake order calculation and auto-draft
    """

    def __init__(self):
        self.default_pick_timer = 90  # seconds
        self.max_pick_timer = 300  # 5 minutes
        self.min_pick_timer = 30  # 30 seconds
        self.auto_draft_delay = 5  # seconds before auto-pick

        # Timer callbacks for real-time updates
        self.timer_callbacks: Dict[str, List[Callable]] = {}
        self.active_timers: Dict[str, asyncio.Task] = {}

    # Draft Creation and Management

    def create_draft(
        self,
        league_id: str,
        commissioner_id: str,
        draft_settings: Optional[DraftSettings] = None,
        db: Optional[Session] = None
    ) -> Draft:
        """
        Create a new draft for a league

        Args:
            league_id: League ID
            commissioner_id: Commissioner user ID
            draft_settings: Optional draft configuration
            db: Optional database session

        Returns:
            Created Draft instance

        Raises:
            DraftServiceError: Draft creation failed
        """
        with get_db_session() if db is None else db as session:
            # Validate league and commissioner
            league = session.query(League).filter(League.league_id == league_id).first()
            if not league:
                raise DraftServiceError("League not found")

            if str(league.commissioner_id) != str(commissioner_id):
                raise DraftServiceError("Only commissioner can create draft")

            if league.status != "setup":
                raise DraftServiceError("League must be in setup phase to create draft")

            # Check if draft already exists
            existing_draft = session.query(Draft).filter(Draft.league_id == league_id).first()
            if existing_draft:
                raise DraftServiceError("Draft already exists for this league")

            # Get teams in the league
            teams = session.query(Team).filter(Team.league_id == league_id).all()
            if len(teams) < 2:
                raise DraftServiceError("Need at least 2 teams to create a draft")

            # Use provided settings or defaults
            if not draft_settings:
                draft_settings = DraftSettings()

            # Generate draft order if not provided
            if not draft_settings.draft_order:
                draft_settings.draft_order = self._generate_draft_order(teams)

            # Create draft
            draft = Draft(
                league_id=league_id,
                draft_type=draft_settings.draft_type,
                status=DraftStatus.SCHEDULED.value,
                pick_timer=min(max(draft_settings.pick_timer_seconds, self.min_pick_timer), self.max_pick_timer),
                current_pick=1,
                current_team_id=draft_settings.draft_order[0] if draft_settings.draft_order else None,
                picks=[]
            )

            session.add(draft)
            session.commit()

            logger.info(f"Draft created for league {league.name}")
            return draft

    def start_draft(
        self,
        draft_id: str,
        commissioner_id: str,
        db: Optional[Session] = None
    ) -> Draft:
        """
        Start the draft

        Args:
            draft_id: Draft ID
            commissioner_id: Commissioner user ID
            db: Optional database session

        Returns:
            Updated Draft instance

        Raises:
            DraftNotFoundError: Draft not found
            InvalidDraftStateError: Cannot start draft in current state
        """
        with get_db_session() if db is None else db as session:
            draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
            if not draft:
                raise DraftNotFoundError("Draft not found")

            # Validate commissioner
            league = session.query(League).filter(League.league_id == draft.league_id).first()
            if str(league.commissioner_id) != str(commissioner_id):
                raise DraftServiceError("Only commissioner can start draft")

            if draft.status != DraftStatus.SCHEDULED.value:
                raise InvalidDraftStateError(f"Cannot start draft with status: {draft.status}")

            # Update draft and league status
            draft.status = DraftStatus.ACTIVE.value
            draft.started_at = datetime.utcnow()

            # Transition league to drafting
            if league.can_transition_to("drafting"):
                league.status = "drafting"

            session.commit()

            # Start the pick timer
            asyncio.create_task(self._start_pick_timer(str(draft.draft_id)))

            # Notify current team that it's their turn
            self._notify_current_pick(draft, session)

            logger.info(f"Draft started for league {league.name}")
            return draft

    def pause_draft(
        self,
        draft_id: str,
        commissioner_id: str,
        db: Optional[Session] = None
    ) -> Draft:
        """Pause the draft"""
        with get_db_session() if db is None else db as session:
            draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
            if not draft:
                raise DraftNotFoundError("Draft not found")

            league = session.query(League).filter(League.league_id == draft.league_id).first()
            if str(league.commissioner_id) != str(commissioner_id):
                raise DraftServiceError("Only commissioner can pause draft")

            if draft.status != DraftStatus.ACTIVE.value:
                raise InvalidDraftStateError("Draft is not active")

            draft.status = DraftStatus.PAUSED.value
            session.commit()

            # Cancel active timer
            self._cancel_pick_timer(str(draft.draft_id))

            logger.info(f"Draft paused for league {league.name}")
            return draft

    def resume_draft(
        self,
        draft_id: str,
        commissioner_id: str,
        db: Optional[Session] = None
    ) -> Draft:
        """Resume a paused draft"""
        with get_db_session() if db is None else db as session:
            draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
            if not draft:
                raise DraftNotFoundError("Draft not found")

            league = session.query(League).filter(League.league_id == draft.league_id).first()
            if str(league.commissioner_id) != str(commissioner_id):
                raise DraftServiceError("Only commissioner can resume draft")

            if draft.status != DraftStatus.PAUSED.value:
                raise InvalidDraftStateError("Draft is not paused")

            draft.status = DraftStatus.ACTIVE.value
            session.commit()

            # Restart the pick timer
            asyncio.create_task(self._start_pick_timer(str(draft.draft_id)))

            logger.info(f"Draft resumed for league {league.name}")
            return draft

    def get_draft(self, draft_id: str, db: Optional[Session] = None) -> Optional[Draft]:
        """Get draft by ID"""
        with get_db_session() if db is None else db as session:
            return session.query(Draft).filter(Draft.draft_id == draft_id).first()

    def get_draft_by_league(self, league_id: str, db: Optional[Session] = None) -> Optional[Draft]:
        """Get draft by league ID"""
        with get_db_session() if db is None else db as session:
            return session.query(Draft).filter(Draft.league_id == league_id).first()

    # Pick Management

    def make_pick(
        self,
        draft_id: str,
        team_id: str,
        player_id: str,
        user_id: str,
        is_autopick: bool = False,
        db: Optional[Session] = None
    ) -> DraftPick:
        """
        Make a draft pick

        Args:
            draft_id: Draft ID
            team_id: Team making the pick
            player_id: Player being selected
            user_id: User making the pick
            is_autopick: Whether this is an automatic pick
            db: Optional database session

        Returns:
            DraftPick instance

        Raises:
            DraftNotFoundError: Draft not found
            InvalidDraftStateError: Invalid draft state for picking
            DraftServiceError: Invalid pick attempt
        """
        with get_db_session() if db is None else db as session:
            draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
            if not draft:
                raise DraftNotFoundError("Draft not found")

            if draft.status != DraftStatus.ACTIVE.value:
                raise InvalidDraftStateError("Draft is not active")

            # Validate it's the correct team's turn
            if str(draft.current_team_id) != str(team_id):
                raise DraftServiceError("It's not your turn to pick")

            # Validate user has permission to pick for this team
            team = session.query(Team).filter(Team.team_id == team_id).first()
            if not team:
                raise DraftServiceError("Team not found")

            if not is_autopick and str(team.user_id) != str(user_id):
                raise DraftServiceError("User doesn't own this team")

            # Validate player exists and is available
            player = session.query(Player).filter(Player.player_id == player_id).first()
            if not player:
                raise DraftServiceError("Player not found")

            # Check if player is already drafted
            if self._is_player_drafted(draft_id, player_id, session):
                raise DraftServiceError("Player already drafted")

            # Validate roster limits (if applicable)
            self._validate_roster_limits(team_id, player, session)

            # Create pick record
            pick_data = {
                "pick_number": draft.current_pick,
                "round_number": self._calculate_round_number(draft.current_pick, draft),
                "team_id": team_id,
                "player_id": player_id,
                "pick_time": datetime.utcnow().isoformat(),
                "is_autopick": is_autopick
            }

            # Add pick to draft picks array
            current_picks = draft.picks or []
            current_picks.append(pick_data)
            draft.picks = current_picks

            # Add player to team roster
            team.add_player_to_roster(player_id)

            # Advance to next pick
            self._advance_to_next_pick(draft, session)

            session.commit()

            # Cancel current timer and start next if draft continues
            self._cancel_pick_timer(str(draft.draft_id))
            if draft.status == DraftStatus.ACTIVE.value:
                asyncio.create_task(self._start_pick_timer(str(draft.draft_id)))
                # Notify next team
                self._notify_current_pick(draft, session)

            pick = DraftPick(
                pick_number=pick_data["pick_number"],
                round_number=pick_data["round_number"],
                team_id=team_id,
                player_id=player_id,
                pick_time=datetime.fromisoformat(pick_data["pick_time"]),
                is_autopick=is_autopick
            )

            logger.info(f"Pick made: {player.name} to {team.name} (Pick #{pick.pick_number})")
            return pick

    def get_draft_board(
        self,
        draft_id: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get complete draft board with picks and current state

        Args:
            draft_id: Draft ID
            db: Optional database session

        Returns:
            Draft board data
        """
        with get_db_session() if db is None else db as session:
            draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
            if not draft:
                raise DraftNotFoundError("Draft not found")

            league = session.query(League).filter(League.league_id == draft.league_id).first()
            teams = session.query(Team).filter(Team.league_id == draft.league_id).order_by(Team.created_at).all()

            # Get draft order
            draft_order = self._get_draft_order(draft, teams)

            # Calculate total picks and rounds
            total_rounds = self._calculate_total_rounds(league, teams)
            total_picks = len(teams) * total_rounds

            # Get pick information with player details
            picks_with_players = []
            for pick_data in (draft.picks or []):
                player = session.query(Player).filter(Player.player_id == pick_data["player_id"]).first()
                team = session.query(Team).filter(Team.team_id == pick_data["team_id"]).first()

                picks_with_players.append({
                    "pick_number": pick_data["pick_number"],
                    "round_number": pick_data["round_number"],
                    "team": {
                        "team_id": str(team.team_id),
                        "name": team.name,
                        "user_id": str(team.user_id)
                    } if team else None,
                    "player": {
                        "player_id": str(player.player_id),
                        "name": player.name,
                        "position": player.position,
                        "team_id": player.team_id
                    } if player else None,
                    "pick_time": pick_data.get("pick_time"),
                    "is_autopick": pick_data.get("is_autopick", False)
                })

            # Get current pick information
            current_pick_info = None
            if draft.status == DraftStatus.ACTIVE.value and draft.current_pick <= total_picks:
                current_team = session.query(Team).filter(Team.team_id == draft.current_team_id).first()
                if current_team:
                    current_pick_info = {
                        "pick_number": draft.current_pick,
                        "round_number": self._calculate_round_number(draft.current_pick, draft),
                        "team": {
                            "team_id": str(current_team.team_id),
                            "name": current_team.name,
                            "user_id": str(current_team.user_id)
                        },
                        "time_remaining": self._get_time_remaining(str(draft.draft_id))
                    }

            return {
                "draft": {
                    "draft_id": str(draft.draft_id),
                    "league_id": str(draft.league_id),
                    "status": draft.status,
                    "draft_type": draft.draft_type,
                    "current_pick": draft.current_pick,
                    "total_picks": total_picks,
                    "total_rounds": total_rounds,
                    "started_at": draft.started_at.isoformat() if draft.started_at else None
                },
                "teams": [
                    {
                        "team_id": str(team.team_id),
                        "name": team.name,
                        "user_id": str(team.user_id),
                        "draft_position": draft_order.index(str(team.team_id)) + 1
                    }
                    for team in teams
                ],
                "picks": picks_with_players,
                "current_pick": current_pick_info,
                "draft_order": draft_order
            }

    def get_available_players(
        self,
        draft_id: str,
        position: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Get players available for drafting

        Args:
            draft_id: Draft ID
            position: Optional position filter
            limit: Maximum results to return
            offset: Results offset for pagination
            db: Optional database session

        Returns:
            List of available player data
        """
        with get_db_session() if db is None else db as session:
            draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
            if not draft:
                raise DraftNotFoundError("Draft not found")

            league = session.query(League).filter(League.league_id == draft.league_id).first()

            # Get drafted player IDs
            drafted_player_ids = set()
            for pick in (draft.picks or []):
                if pick.get("player_id"):
                    drafted_player_ids.add(pick["player_id"])

            # Query available players
            query = session.query(Player).filter(
                and_(
                    Player.sport == league.sport,
                    ~Player.player_id.in_(drafted_player_ids)
                )
            )

            if position:
                query = query.filter(Player.position == position)

            players = query.order_by(Player.name).offset(offset).limit(limit).all()

            return [
                {
                    "player_id": str(player.player_id),
                    "external_id": player.external_id,
                    "name": player.name,
                    "position": player.position,
                    "team_id": player.team_id,
                    "injury_status": player.injury_status,
                    "projections": player.projections
                }
                for player in players
            ]

    # Auto-Draft Methods

    def enable_autodraft_for_team(
        self,
        draft_id: str,
        team_id: str,
        user_id: str,
        db: Optional[Session] = None
    ) -> None:
        """Enable auto-draft for a team"""
        # TODO: Implement auto-draft queue management
        logger.info(f"Auto-draft enabled for team {team_id} in draft {draft_id}")

    def make_autopick(
        self,
        draft_id: str,
        team_id: str,
        db: Optional[Session] = None
    ) -> DraftPick:
        """
        Make an automatic pick for a team

        Args:
            draft_id: Draft ID
            team_id: Team ID
            db: Optional database session

        Returns:
            DraftPick instance
        """
        with get_db_session() if db is None else db as session:
            # Get best available player based on simple logic
            available_players = self.get_available_players(draft_id, limit=50, db=session)

            if not available_players:
                raise DraftServiceError("No players available for auto-pick")

            # Simple auto-pick logic: select first available player
            # TODO: Implement more sophisticated auto-pick algorithm
            selected_player = available_players[0]

            return self.make_pick(
                draft_id=draft_id,
                team_id=team_id,
                player_id=selected_player["player_id"],
                user_id="system",  # System user for auto-picks
                is_autopick=True,
                db=session
            )

    # Timer Management

    async def _start_pick_timer(self, draft_id: str) -> None:
        """Start pick timer for current pick"""
        try:
            # Cancel existing timer
            self._cancel_pick_timer(draft_id)

            # Create new timer task
            timer_task = asyncio.create_task(self._pick_timer_countdown(draft_id))
            self.active_timers[draft_id] = timer_task

            await timer_task
        except asyncio.CancelledError:
            logger.info(f"Pick timer cancelled for draft {draft_id}")
        except Exception as e:
            logger.error(f"Pick timer error for draft {draft_id}: {e}")

    async def _pick_timer_countdown(self, draft_id: str) -> None:
        """Countdown timer for pick"""
        with get_db_session() as session:
            draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
            if not draft or draft.status != DraftStatus.ACTIVE.value:
                return

            time_remaining = draft.pick_timer

            while time_remaining > 0:
                await asyncio.sleep(1)
                time_remaining -= 1

                # Notify callbacks about timer update
                self._notify_timer_callbacks(draft_id, time_remaining)

                # Check if draft is still active
                session.refresh(draft)
                if draft.status != DraftStatus.ACTIVE.value:
                    return

            # Timer expired - make auto-pick
            try:
                self.make_autopick(draft_id, str(draft.current_team_id), db=session)
                logger.info(f"Auto-pick made due to timer expiration in draft {draft_id}")
            except Exception as e:
                logger.error(f"Failed to make auto-pick for draft {draft_id}: {e}")

    def _cancel_pick_timer(self, draft_id: str) -> None:
        """Cancel active pick timer"""
        if draft_id in self.active_timers:
            self.active_timers[draft_id].cancel()
            del self.active_timers[draft_id]

    def _get_time_remaining(self, draft_id: str) -> int:
        """Get remaining time for current pick"""
        # TODO: Implement actual timer tracking
        return 60  # Placeholder

    def register_timer_callback(self, draft_id: str, callback: Callable[[int], None]) -> None:
        """Register callback for timer updates"""
        if draft_id not in self.timer_callbacks:
            self.timer_callbacks[draft_id] = []
        self.timer_callbacks[draft_id].append(callback)

    def _notify_timer_callbacks(self, draft_id: str, time_remaining: int) -> None:
        """Notify registered callbacks about timer update"""
        if draft_id in self.timer_callbacks:
            for callback in self.timer_callbacks[draft_id]:
                try:
                    callback(time_remaining)
                except Exception as e:
                    logger.error(f"Timer callback error: {e}")

    # Helper Methods

    def _generate_draft_order(self, teams: List[Team]) -> List[str]:
        """Generate random draft order"""
        import random
        team_ids = [str(team.team_id) for team in teams]
        random.shuffle(team_ids)
        return team_ids

    def _get_draft_order(self, draft: Draft, teams: List[Team]) -> List[str]:
        """Get draft order from draft settings or generate default"""
        # TODO: Extract from draft settings stored in league
        return [str(team.team_id) for team in teams]

    def _calculate_round_number(self, pick_number: int, draft: Draft) -> int:
        """Calculate round number from pick number"""
        with get_db_session() as session:
            team_count = session.query(Team).filter(Team.league_id == draft.league_id).count()
            return ((pick_number - 1) // team_count) + 1

    def _calculate_total_rounds(self, league: League, teams: List[Team]) -> int:
        """Calculate total draft rounds based on league settings"""
        roster_settings = league.roster_settings or {}
        starting_positions = roster_settings.get("starting_positions", [])
        bench_spots = roster_settings.get("bench_spots", 5)
        return len(starting_positions) + bench_spots

    def _advance_to_next_pick(self, draft: Draft, session: Session) -> None:
        """Advance draft to next pick"""
        teams = session.query(Team).filter(Team.league_id == draft.league_id).order_by(Team.created_at).all()
        team_count = len(teams)
        total_rounds = self._calculate_total_rounds(
            session.query(League).filter(League.league_id == draft.league_id).first(),
            teams
        )
        total_picks = team_count * total_rounds

        if draft.current_pick >= total_picks:
            # Draft is complete
            draft.status = DraftStatus.COMPLETED.value
            draft.completed_at = datetime.utcnow()
            draft.current_team_id = None

            # Transition league to active
            league = session.query(League).filter(League.league_id == draft.league_id).first()
            if league.can_transition_to("active"):
                league.status = "active"

            logger.info(f"Draft completed for league {league.name}")
            return

        # Calculate next pick
        draft.current_pick += 1
        current_round = self._calculate_round_number(draft.current_pick, draft)

        # Get draft order
        draft_order = self._get_draft_order(draft, teams)

        if draft.draft_type == DraftType.SNAKE.value:
            # Snake draft: reverse order every round
            if current_round % 2 == 0:  # Even rounds are reversed
                pick_in_round = (draft.current_pick - 1) % team_count
                team_index = team_count - 1 - pick_in_round
            else:  # Odd rounds are normal order
                team_index = (draft.current_pick - 1) % team_count
        else:
            # Linear draft: same order every round
            team_index = (draft.current_pick - 1) % team_count

        draft.current_team_id = draft_order[team_index]

    def _is_player_drafted(self, draft_id: str, player_id: str, session: Session) -> bool:
        """Check if player is already drafted"""
        draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
        if not draft or not draft.picks:
            return False

        for pick in draft.picks:
            if pick.get("player_id") == player_id:
                return True

        return False

    def _validate_roster_limits(self, team_id: str, player: Player, session: Session) -> None:
        """Validate roster limits for the pick"""
        team = session.query(Team).filter(Team.team_id == team_id).first()
        league = session.query(League).filter(League.league_id == team.league_id).first()

        roster_settings = league.roster_settings or {}
        max_per_position = roster_settings.get("max_per_position", {})

        if player.position in max_per_position:
            current_count = sum(1 for p_id in (team.roster or [])
                              if session.query(Player).filter(
                                  and_(Player.player_id == p_id, Player.position == player.position)
                              ).first())

            if current_count >= max_per_position[player.position]:
                raise DraftServiceError(f"Team has reached maximum {player.position} players")

    def _notify_current_pick(self, draft: Draft, session: Session) -> None:
        """Send notification to team that it's their turn to pick"""
        if not draft.current_team_id:
            return

        team = session.query(Team).filter(Team.team_id == draft.current_team_id).first()
        if not team:
            return

        # Create notification
        notification = Notification.create_draft_notification(
            user_id=str(team.user_id),
            league_id=str(draft.league_id),
            team_id=str(team.team_id),
            pick_number=draft.current_pick,
            time_remaining=draft.pick_timer
        )

        session.add(notification)
        session.commit()

        logger.info(f"Pick notification sent to team {team.name}")

    # Statistics and Analysis

    def get_draft_summary(
        self,
        draft_id: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get draft summary and statistics"""
        with get_db_session() if db is None else db as session:
            draft = session.query(Draft).filter(Draft.draft_id == draft_id).first()
            if not draft:
                raise DraftNotFoundError("Draft not found")

            league = session.query(League).filter(League.league_id == draft.league_id).first()
            teams = session.query(Team).filter(Team.league_id == draft.league_id).all()

            total_picks = len(draft.picks) if draft.picks else 0
            autopick_count = sum(1 for pick in (draft.picks or []) if pick.get("is_autopick", False))

            # Calculate draft duration if completed
            duration_minutes = None
            if draft.started_at and draft.completed_at:
                duration = draft.completed_at - draft.started_at
                duration_minutes = duration.total_seconds() / 60

            return {
                "draft_id": str(draft.draft_id),
                "league_name": league.name,
                "status": draft.status,
                "total_teams": len(teams),
                "total_picks": total_picks,
                "autopick_count": autopick_count,
                "manual_pick_count": total_picks - autopick_count,
                "started_at": draft.started_at.isoformat() if draft.started_at else None,
                "completed_at": draft.completed_at.isoformat() if draft.completed_at else None,
                "duration_minutes": duration_minutes,
                "current_pick": draft.current_pick if draft.status == DraftStatus.ACTIVE.value else None
            }