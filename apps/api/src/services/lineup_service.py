from __future__ import annotations

import uuid as _uuid
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.exc import IntegrityError

from ..models.lineup import Lineup
from ..models.league import League
from ..models.team import Team
from ..models.player import Player
from ..models.notification import Notification
from ..infrastructure.database.session_factory import get_db_session
from ..infrastructure.logging.domain_logger import get_logger

logger = get_logger(__name__)


class LineupValidationError(Exception):
    """Lineup validation errors"""
    pass


class OptimisticLockError(Exception):
    """Optimistic locking conflict"""
    pass


class LineupLockedError(Exception):
    """Lineup is locked and cannot be modified"""
    pass


@dataclass
class LineupPlayer:
    """Player in lineup with position"""
    player_id: str
    position: str  # Position in lineup (QB, RB, FLEX, etc.)


@dataclass
class LineupValidation:
    """Lineup validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_positions: List[str]
    invalid_players: List[str]


@dataclass
class LineupOptimization:
    """Lineup optimization suggestion"""
    current_projected_points: float
    optimized_projected_points: float
    suggested_changes: List[Dict[str, str]]  # [{"out": player_id, "in": player_id, "position": pos}]
    improvement_percentage: float


class LineupService:
    """
    Lineup service for roster management

    Implements T032 requirements:
    - LineupService for roster management
    - Add position validation, optimistic locking, constraints
    - Include scoring period and lock time management
    """

    def __init__(self):
        self.default_lock_time_hours = 1  # Lock lineups 1 hour before games
        self.max_retries = 3  # For optimistic locking

    # Lineup Creation and Management

    def create_lineup(
        self,
        team_id: str,
        week: int,
        game_day: Optional[date] = None,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Lineup:
        """
        Create a new lineup for a team

        Args:
            team_id: Team ID
            week: Week number
            game_day: Optional specific game day
            user_id: Optional user ID for validation
            db: Optional database session

        Returns:
            Created Lineup instance

        Raises:
            LineupValidationError: Invalid lineup parameters
        """
        with get_db_session() if db is None else db as session:
            # Validate team exists and user owns it
            team = session.query(Team).filter(Team.team_id == team_id).first()
            if not team:
                raise LineupValidationError("Team not found")

            if user_id and str(team.user_id) != str(user_id):
                raise LineupValidationError("User does not own this team")

            # Check if lineup already exists
            existing_lineup = session.query(Lineup).filter(
                and_(
                    Lineup.team_id == team_id,
                    Lineup.week == week,
                    Lineup.game_day == game_day
                )
            ).first()

            if existing_lineup:
                return existing_lineup

            # Create new lineup
            lineup = Lineup(
                team_id=team_id,
                week=week,
                game_day=game_day,
                players=[],
                points_scored=0.0,
                is_locked=False,
                version=1
            )

            session.add(lineup)
            session.commit()

            logger.info(f"Lineup created for team {getattr(team, 'team_name', getattr(team, 'name', ''))}, week {week}")
            return lineup

    def get_lineup(
        self,
        lineup_id: str,
        db: Optional[Session] = None
    ) -> Optional[Lineup]:
        """Get lineup by ID"""
        with get_db_session() if db is None else db as session:
            return session.query(Lineup).filter(Lineup.lineup_id == lineup_id).first()

    def get_team_lineup(
        self,
        team_id: str,
        week: int,
        game_day: Optional[date] = None,
        db: Optional[Session] = None
    ) -> Optional[Lineup]:
        """Get team's lineup for specific week/day"""
        with get_db_session() if db is None else db as session:
            return session.query(Lineup).filter(
                and_(
                    Lineup.team_id == team_id,
                    Lineup.week == week,
                    Lineup.game_day == game_day
                )
            ).first()

    def update_lineup(
        self,
        lineup_id: str,
        lineup_players: List[LineupPlayer],
        user_id: str,
        expected_version: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Lineup:
        """
        Update lineup with optimistic locking

        Args:
            lineup_id: Lineup ID
            lineup_players: List of players with positions
            user_id: User making the update
            expected_version: Expected version for optimistic locking
            db: Optional database session

        Returns:
            Updated Lineup instance

        Raises:
            LineupValidationError: Invalid lineup
            OptimisticLockError: Version conflict
            LineupLockedError: Lineup is locked
        """
        with get_db_session() if db is None else db as session:
            lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_id).first()
            if not lineup:
                raise LineupValidationError("Lineup not found")

            # Validate ownership
            team = session.query(Team).filter(Team.team_id == lineup.team_id).first()
            if str(team.user_id) != str(user_id):
                raise LineupValidationError("User does not own this team")

            # Check if lineup is locked
            if lineup.is_locked:
                raise LineupLockedError("Lineup is locked and cannot be modified")

            # Check optimistic locking
            if expected_version is not None and lineup.version != expected_version:
                raise OptimisticLockError(f"Version conflict. Expected {expected_version}, got {lineup.version}")

            # Validate lineup
            validation = self.validate_lineup(lineup.team_id, lineup_players, session)
            if not validation.is_valid:
                raise LineupValidationError(f"Invalid lineup: {', '.join(validation.errors)}")

            # Update lineup
            lineup.players = [
                {"player_id": lp.player_id, "position": lp.position}
                for lp in lineup_players
            ]
            lineup.version += 1

            try:
                session.commit()
                logger.info(
                    "Lineup updated for team %s, week %s",
                    getattr(team, "team_name", getattr(team, "name", "")),
                    lineup.week,
                )
                return lineup
            except IntegrityError:
                session.rollback()
                raise OptimisticLockError("Lineup was modified by another request")

    def set_starting_player(
        self,
        lineup_id: str,
        player_id: str,
        position: str,
        user_id: str,
        db: Optional[Session] = None
    ) -> Lineup:
        """
        Set a specific player at a specific position

        Args:
            lineup_id: Lineup ID
            player_id: Player ID
            position: Position to set player at
            user_id: User making the change
            db: Optional database session

        Returns:
            Updated Lineup instance
        """
        with get_db_session() if db is None else db as session:
            lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_id).first()
            if not lineup:
                raise LineupValidationError("Lineup not found")

            # Get current lineup players
            current_players = []
            lineup_dict = {}

            for player_data in (lineup.players or []):
                current_players.append(LineupPlayer(
                    player_id=player_data["player_id"],
                    position=player_data["position"]
                ))
                lineup_dict[player_data["position"]] = player_data["player_id"]

            # Update specific position
            lineup_dict[position] = player_id

            # Convert back to LineupPlayer list
            updated_players = [
                LineupPlayer(player_id=pid, position=pos)
                for pos, pid in lineup_dict.items()
            ]

            return self.update_lineup(
                lineup_id=lineup_id,
                lineup_players=updated_players,
                user_id=user_id,
                expected_version=lineup.version,
                db=session
            )

    def swap_players(
        self,
        lineup_id: str,
        player1_id: str,
        player2_id: str,
        user_id: str,
        db: Optional[Session] = None
    ) -> Lineup:
        """
        Swap two players in lineup

        Args:
            lineup_id: Lineup ID
            player1_id: First player ID
            player2_id: Second player ID
            user_id: User making the swap
            db: Optional database session

        Returns:
            Updated Lineup instance
        """
        with get_db_session() if db is None else db as session:
            lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_id).first()
            if not lineup:
                raise LineupValidationError("Lineup not found")

            # Find positions of both players
            player1_pos = None
            player2_pos = None

            for player_data in (lineup.players or []):
                if player_data["player_id"] == player1_id:
                    player1_pos = player_data["position"]
                elif player_data["player_id"] == player2_id:
                    player2_pos = player_data["position"]

            if not player1_pos or not player2_pos:
                raise LineupValidationError("One or both players not found in lineup")

            # Create swapped lineup
            updated_players = []
            for player_data in (lineup.players or []):
                if player_data["player_id"] == player1_id:
                    updated_players.append(LineupPlayer(player_id=player1_id, position=player2_pos))
                elif player_data["player_id"] == player2_id:
                    updated_players.append(LineupPlayer(player_id=player2_id, position=player1_pos))
                else:
                    updated_players.append(LineupPlayer(
                        player_id=player_data["player_id"],
                        position=player_data["position"]
                    ))

            return self.update_lineup(
                lineup_id=lineup_id,
                lineup_players=updated_players,
                user_id=user_id,
                expected_version=lineup.version,
                db=session
            )

    # Lineup Validation

    def validate_lineup(
        self,
        team_id: str,
        lineup_players: List[LineupPlayer],
        session: Optional[Session] = None
    ) -> LineupValidation:
        """
        Validate lineup against league rules

        Args:
            team_id: Team ID
            lineup_players: List of players with positions
            session: Optional database session

        Returns:
            LineupValidation result
        """
        with get_db_session() if session is None else session as db_session:
            errors = []
            warnings = []
            missing_positions = []
            invalid_players = []

            # Get team and league info
            team = db_session.query(Team).filter(Team.team_id == team_id).first()
            league = db_session.query(League).filter(League.league_id == team.league_id).first()

            if not team or not league:
                errors.append("Team or league not found")
                return LineupValidation(False, errors, warnings, missing_positions, invalid_players)

            # Get league roster settings
            roster_settings = league.roster_settings or {}
            required_positions = roster_settings.get("starting_positions", [])

            # Track positions filled
            positions_filled = {}
            player_ids_used = set()

            for lineup_player in lineup_players:
                # Check for duplicate players
                if lineup_player.player_id in player_ids_used:
                    errors.append(f"Player {lineup_player.player_id} used multiple times")
                player_ids_used.add(lineup_player.player_id)

                # Validate player exists and is on team roster
                player = db_session.query(Player).filter(Player.player_id == lineup_player.player_id).first()
                if not player:
                    invalid_players.append(lineup_player.player_id)
                    errors.append(f"Player {lineup_player.player_id} not found")
                    continue

                if lineup_player.player_id not in (team.roster or []):
                    invalid_players.append(lineup_player.player_id)
                    errors.append(f"Player {player.name} not on team roster")
                    continue

                # Validate position eligibility
                eligible_positions = self._get_player_eligible_positions(player, league)
                if lineup_player.position not in eligible_positions:
                    errors.append(f"Player {player.name} not eligible for position {lineup_player.position}")

                # Track position usage
                positions_filled[lineup_player.position] = positions_filled.get(lineup_player.position, 0) + 1

            # Check required positions
            for required_pos in required_positions:
                if required_pos not in positions_filled:
                    missing_positions.append(required_pos)

            # Check for position limits
            for position, count in positions_filled.items():
                if position in required_positions:
                    required_count = required_positions.count(position)
                    if count > required_count:
                        errors.append(f"Too many players at position {position}")

            # Add missing position errors
            if missing_positions:
                errors.extend([f"Missing required position: {pos}" for pos in missing_positions])

            is_valid = len(errors) == 0

            return LineupValidation(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                missing_positions=missing_positions,
                invalid_players=invalid_players
            )

    def _get_player_eligible_positions(self, player: Player, league: League) -> List[str]:
        """Get positions a player is eligible for in the league"""
        eligible_positions = [player.position]

        # Add flex positions based on sport
        if league.sport == "nfl":
            if player.position in ["RB", "WR", "TE"]:
                eligible_positions.append("FLEX")
            if player.position in ["RB", "WR", "TE", "QB"]:
                eligible_positions.append("SUPERFLEX")
        elif league.sport == "wnba":
            eligible_positions.append("FLEX")

        return eligible_positions

    # Lineup Locking

    def lock_lineup(
        self,
        lineup_id: str,
        db: Optional[Session] = None
    ) -> Lineup:
        """Lock lineup to prevent further changes"""
        with get_db_session() if db is None else db as session:
            lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_id).first()
            if not lineup:
                raise LineupValidationError("Lineup not found")

            lineup.is_locked = True
            session.commit()

            logger.info(f"Lineup locked: {lineup_id}")
            return lineup

    def unlock_lineup(
        self,
        lineup_id: str,
        commissioner_id: str,
        db: Optional[Session] = None
    ) -> Lineup:
        """Unlock lineup (commissioner only)"""
        with get_db_session() if db is None else db as session:
            lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_id).first()
            if not lineup:
                raise LineupValidationError("Lineup not found")

            # Validate commissioner
            team = session.query(Team).filter(Team.team_id == lineup.team_id).first()
            league = session.query(League).filter(League.league_id == team.league_id).first()

            if str(league.commissioner_id) != str(commissioner_id):
                raise LineupValidationError("Only commissioner can unlock lineups")

            lineup.is_locked = False
            session.commit()

            logger.info(f"Lineup unlocked by commissioner: {lineup_id}")
            return lineup

    def auto_lock_lineups(
        self,
        league_id: str,
        lock_time: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> int:
        """
        Automatically lock lineups for games starting soon

        Args:
            league_id: League ID
            lock_time: Optional custom lock time
            db: Optional database session

        Returns:
            Number of lineups locked
        """
        if not lock_time:
            lock_time = datetime.utcnow() + timedelta(hours=self.default_lock_time_hours)

        with get_db_session() if db is None else db as session:
            # Get unlocked lineups for the league
            teams = session.query(Team).filter(Team.league_id == league_id).all()
            team_ids = [str(team.team_id) for team in teams]

            lineups_to_lock = session.query(Lineup).filter(
                and_(
                    Lineup.team_id.in_(team_ids),
                    Lineup.is_locked == False,
                    # TODO: Add game time comparison logic
                )
            ).all()

            locked_count = 0
            for lineup in lineups_to_lock:
                lineup.is_locked = True
                locked_count += 1

            session.commit()

            if locked_count > 0:
                logger.info(f"Auto-locked {locked_count} lineups in league {league_id}")

            return locked_count

    # Lineup Analysis and Optimization

    def get_lineup_analysis(
        self,
        lineup_id: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get detailed lineup analysis

        Args:
            lineup_id: Lineup ID
            db: Optional database session

        Returns:
            Lineup analysis data
        """
        with get_db_session() if db is None else db as session:
            lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_id).first()
            if not lineup:
                raise LineupValidationError("Lineup not found")

            team = session.query(Team).filter(Team.team_id == lineup.team_id).first()
            league = session.query(League).filter(League.league_id == team.league_id).first()

            # Get player details
            player_details = []
            total_projected_points = 0.0

            for player_data in (lineup.players or []):
                player = session.query(Player).filter(Player.player_id == player_data["player_id"]).first()
                if player:
                    projected_points = 0.0
                    if player.projections and "fantasy_points" in player.projections:
                        projected_points = player.projections["fantasy_points"]

                    total_projected_points += projected_points

                    player_details.append({
                        "player_id": str(player.player_id),
                        "name": player.name,
                        "position": player.position,
                        "lineup_position": player_data["position"],
                        "team_id": player.team_id,
                        "injury_status": player.injury_status,
                        "projected_points": projected_points,
                        "season_stats": player.season_stats
                    })

            # Analyze position distribution
            position_distribution = {}
            for player_data in (lineup.players or []):
                pos = player_data["position"]
                position_distribution[pos] = position_distribution.get(pos, 0) + 1

            return {
                "lineup_id": str(lineup.lineup_id),
                "team_name": getattr(team, "team_name", getattr(team, "name", "")),
                "week": lineup.week,
                "is_locked": lineup.is_locked,
                "version": lineup.version,
                "total_projected_points": total_projected_points,
                "player_count": len(player_details),
                "players": player_details,
                "position_distribution": position_distribution,
                "validation": self.validate_lineup(lineup.team_id, [
                    LineupPlayer(player_id=p["player_id"], position=p["lineup_position"])
                    for p in player_details
                ], session)
            }

    def suggest_lineup_optimization(
        self,
        lineup_id: str,
        db: Optional[Session] = None
    ) -> LineupOptimization:
        """
        Suggest lineup optimizations for better projected performance

        Args:
            lineup_id: Lineup ID
            db: Optional database session

        Returns:
            LineupOptimization with suggestions
        """
        with get_db_session() if db is None else db as session:
            lineup = session.query(Lineup).filter(Lineup.lineup_id == lineup_id).first()
            if not lineup:
                raise LineupValidationError("Lineup not found")

            # Get current lineup analysis
            current_analysis = self.get_lineup_analysis(lineup_id, session)
            current_projected = current_analysis["total_projected_points"]

            # Get team roster
            team = session.query(Team).filter(Team.team_id == lineup.team_id).first()
            roster_player_ids = team.roster or []

            # Get all roster players
            roster_players = session.query(Player).filter(
                Player.player_id.in_(roster_player_ids)
            ).all()

            # Simple optimization: find best available players for each position
            suggested_changes = []
            optimized_projected = current_projected

            # TODO: Implement more sophisticated optimization algorithm
            # For now, just check if there are obviously better players on bench

            return LineupOptimization(
                current_projected_points=current_projected,
                optimized_projected_points=optimized_projected,
                suggested_changes=suggested_changes,
                improvement_percentage=0.0
            )

    # Lineup History and Statistics

    def get_lineup_history(
        self,
        team_id: str,
        limit: int = 10,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """Get lineup history for a team"""
        with get_db_session() if db is None else db as session:
            lineups = session.query(Lineup).filter(
                Lineup.team_id == team_id
            ).order_by(desc(Lineup.week)).offset(offset).limit(limit).all()

            history = []
            for lineup in lineups:
                history.append({
                    "lineup_id": str(lineup.lineup_id),
                    "week": lineup.week,
                    "game_day": lineup.game_day.isoformat() if lineup.game_day else None,
                    "points_scored": lineup.points_scored,
                    "is_locked": lineup.is_locked,
                    "player_count": len(lineup.players) if lineup.players else 0,
                    "created_at": lineup.created_at.isoformat()
                })

            return history

    def get_lineup_reminders(
        self,
        league_id: str,
        reminder_hours: int = 24,
        db: Optional[Session] = None
    ) -> List[str]:
        """
        Get teams that need lineup reminders

        Args:
            league_id: League ID
            reminder_hours: Hours before games to send reminder
            db: Optional database session

        Returns:
            List of team IDs that need reminders
        """
        with get_db_session() if db is None else db as session:
            # TODO: Implement game schedule checking and reminder logic
            # For now, return empty list
            return []

    def send_lineup_reminders(
        self,
        league_id: str,
        week: int,
        db: Optional[Session] = None
    ) -> int:
        """Send lineup reminder notifications"""
        with get_db_session() if db is None else db as session:
            teams_needing_reminders = self.get_lineup_reminders(league_id, db=session)

            notifications_sent = 0
            for team_id in teams_needing_reminders:
                team = session.query(Team).filter(Team.team_id == team_id).first()
                if team:
                    notification = Notification(
                        user_id=team.user_id,
                        league_id=league_id,
                        team_id=team_id,
                        notification_type="lineup_reminder",
                        title="Lineup Reminder",
                        message=f"Don't forget to set your lineup for Week {week}!",
                        action_url=f"/leagues/{league_id}/lineup",
                        priority="normal"
                    )
                    session.add(notification)
                    notifications_sent += 1

            session.commit()

            if notifications_sent > 0:
                logger.info(f"Sent {notifications_sent} lineup reminders for league {league_id}")

            return notifications_sent

    # Bulk Operations

    def copy_lineup(
        self,
        source_lineup_id: str,
        target_week: int,
        target_game_day: Optional[date] = None,
        user_id: str,
        db: Optional[Session] = None
    ) -> Lineup:
        """
        Copy lineup to another week/day

        Args:
            source_lineup_id: Source lineup ID
            target_week: Target week
            target_game_day: Optional target game day
            user_id: User making the copy
            db: Optional database session

        Returns:
            New Lineup instance
        """
        with get_db_session() if db is None else db as session:
            source_lineup = session.query(Lineup).filter(Lineup.lineup_id == source_lineup_id).first()
            if not source_lineup:
                raise LineupValidationError("Source lineup not found")

            # Validate ownership
            team = session.query(Team).filter(Team.team_id == source_lineup.team_id).first()
            if str(team.user_id) != str(user_id):
                raise LineupValidationError("User does not own this team")

            # Create or update target lineup
            target_lineup = self.get_team_lineup(
                source_lineup.team_id, target_week, target_game_day, session
            )

            if not target_lineup:
                target_lineup = self.create_lineup(
                    source_lineup.team_id, target_week, target_game_day, user_id, session
                )

            # Copy players if target is not locked
            if not target_lineup.is_locked:
                lineup_players = [
                    LineupPlayer(player_id=p["player_id"], position=p["position"])
                    for p in (source_lineup.players or [])
                ]

                target_lineup = self.update_lineup(
                    str(target_lineup.lineup_id),
                    lineup_players,
                    user_id,
                    target_lineup.version,
                    session
                )

                logger.info(f"Lineup copied from week {source_lineup.week} to week {target_week}")

            return target_lineup
