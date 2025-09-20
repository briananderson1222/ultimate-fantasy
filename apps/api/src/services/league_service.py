from __future__ import annotations

import uuid as _uuid
import secrets
import string
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.league import League
from ..models.team import Team
from ..models.user import User
from ..models.achievement import Achievement
from ..infrastructure.database.session_factory import get_db_session
from ..infrastructure.logging.domain_logger import get_logger

logger = get_logger(__name__)


class LeagueServiceError(Exception):
    """Base exception for league service errors"""
    pass


class LeagueNotFoundError(LeagueServiceError):
    """League not found errors"""
    pass


class LeagueFullError(LeagueServiceError):
    """League at capacity errors"""
    pass


class InviteCodeError(LeagueServiceError):
    """Invalid invite code errors"""
    pass


class PermissionError(LeagueServiceError):
    """Insufficient permissions errors"""
    pass


class LeagueService:
    """
    League service for configuration management

    Implements T028 requirements:
    - LeagueService with configuration management
    - Add league creation, settings, and membership
    - Include invite code generation and validation
    """

    def __init__(self):
        self.invite_code_length = 8
        self.max_leagues_per_user = 10  # As commissioner
        self.max_teams_per_user_per_league = 1

    # League Creation and Management

    def create_league(
        self,
        commissioner_id: str,
        name: str,
        sport: str,
        league_type: str,
        season: str,
        max_teams: int = 12,
        custom_settings: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> League:
        """
        Create a new fantasy league

        Args:
            commissioner_id: User ID of the league commissioner
            name: League name
            sport: Sport type (mlb, nfl, wnba)
            league_type: Type of league (head_to_head, rotisserie)
            season: Season identifier
            max_teams: Maximum number of teams (2-20)
            custom_settings: Optional custom league settings
            db: Optional database session

        Returns:
            Created League instance

        Raises:
            LeagueServiceError: League creation failed
        """
        with get_db_session() if db is None else db as session:
            # Validate commissioner exists
            commissioner = session.query(User).filter(User.user_id == commissioner_id).first()
            if not commissioner:
                raise LeagueServiceError("Commissioner not found")

            # Check commissioner's league limit
            existing_leagues = session.query(League).filter(
                League.commissioner_id == commissioner_id
            ).count()

            if existing_leagues >= self.max_leagues_per_user:
                raise LeagueServiceError(f"Commissioner has reached maximum of {self.max_leagues_per_user} leagues")

            # Generate unique invite code
            invite_code = self._generate_invite_code(session)

            # Create league with default settings
            league = League(
                name=name,
                sport=sport,
                league_type=league_type,
                season=season,
                commissioner_id=commissioner_id,
                max_teams=max_teams,
                invite_code=invite_code,
                scoring_rules=self._get_default_scoring_rules(sport, custom_settings),
                roster_settings=self._get_default_roster_settings(sport, custom_settings),
                draft_settings=self._get_default_draft_settings(custom_settings),
                waiver_settings=self._get_default_waiver_settings(custom_settings),
                trade_settings=self._get_default_trade_settings(custom_settings),
                playoff_settings=self._get_default_playoff_settings(custom_settings)
            )

            session.add(league)
            session.flush()  # Get the league_id

            # Create commissioner's team automatically
            commissioner_team = Team(
                league_id=league.league_id,
                user_id=commissioner_id,
                name=f"{commissioner.display_name or commissioner.username}'s Team",
                wins=0,
                losses=0,
                ties=0,
                points_for=0.0,
                points_against=0.0,
                waiver_priority=1,
                faab_budget=100,
                roster=[]
            )

            session.add(commissioner_team)
            session.flush()

            # Create first league achievement for commissioner
            first_league_achievement = Achievement.create_first_league_achievement(
                commissioner_id, league.league_id
            )
            session.add(first_league_achievement)

            session.commit()

            logger.info(f"League created: {name} by {commissioner.username}")
            return league

    def get_league(self, league_id: str, db: Optional[Session] = None) -> Optional[League]:
        """Get league by ID"""
        with get_db_session() if db is None else db as session:
            return session.query(League).filter(League.league_id == league_id).first()

    def get_league_by_invite_code(self, invite_code: str, db: Optional[Session] = None) -> Optional[League]:
        """Get league by invite code"""
        with get_db_session() if db is None else db as session:
            return session.query(League).filter(League.invite_code == invite_code).first()

    def get_user_leagues(
        self,
        user_id: str,
        as_commissioner: bool = False,
        db: Optional[Session] = None
    ) -> List[League]:
        """
        Get leagues for a user

        Args:
            user_id: User ID
            as_commissioner: If True, return only leagues where user is commissioner
            db: Optional database session

        Returns:
            List of League instances
        """
        with get_db_session() if db is None else db as session:
            if as_commissioner:
                # Get leagues where user is commissioner
                return session.query(League).filter(
                    League.commissioner_id == user_id
                ).order_by(League.created_at.desc()).all()
            else:
                # Get all leagues where user has a team
                leagues = session.query(League).join(Team).filter(
                    Team.user_id == user_id
                ).order_by(League.created_at.desc()).all()

                return leagues

    def update_league_settings(
        self,
        league_id: str,
        user_id: str,
        updates: Dict[str, Any],
        db: Optional[Session] = None
    ) -> League:
        """
        Update league settings (commissioner only)

        Args:
            league_id: League ID
            user_id: User ID (must be commissioner)
            updates: Settings to update
            db: Optional database session

        Returns:
            Updated League instance

        Raises:
            LeagueNotFoundError: League not found
            PermissionError: User is not commissioner
        """
        with get_db_session() if db is None else db as session:
            league = session.query(League).filter(League.league_id == league_id).first()
            if not league:
                raise LeagueNotFoundError("League not found")

            if str(league.commissioner_id) != str(user_id):
                raise PermissionError("Only commissioner can update league settings")

            # Only allow updates if league is in setup status
            if league.status != "setup":
                raise LeagueServiceError("League settings can only be updated during setup phase")

            # Update allowed fields
            allowed_fields = {
                'name', 'max_teams', 'scoring_rules', 'roster_settings',
                'draft_settings', 'waiver_settings', 'trade_settings', 'playoff_settings'
            }

            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(league, field, value)

            session.commit()

            logger.info(f"League settings updated: {league.name}")
            return league

    def transition_league_status(
        self,
        league_id: str,
        user_id: str,
        new_status: str,
        db: Optional[Session] = None
    ) -> League:
        """
        Transition league to new status (commissioner only)

        Args:
            league_id: League ID
            user_id: User ID (must be commissioner)
            new_status: New status to transition to
            db: Optional database session

        Returns:
            Updated League instance

        Raises:
            LeagueNotFoundError: League not found
            PermissionError: User is not commissioner or invalid transition
        """
        with get_db_session() if db is None else db as session:
            league = session.query(League).filter(League.league_id == league_id).first()
            if not league:
                raise LeagueNotFoundError("League not found")

            if str(league.commissioner_id) != str(user_id):
                raise PermissionError("Only commissioner can change league status")

            if not league.can_transition_to(new_status):
                raise PermissionError(f"Cannot transition from {league.status} to {new_status}")

            league.status = new_status
            session.commit()

            logger.info(f"League status changed: {league.name} -> {new_status}")
            return league

    # Team Management

    def join_league(
        self,
        invite_code: str,
        user_id: str,
        team_name: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Team:
        """
        Join a league using invite code

        Args:
            invite_code: League invite code
            user_id: User ID
            team_name: Optional custom team name
            db: Optional database session

        Returns:
            Created Team instance

        Raises:
            InviteCodeError: Invalid invite code
            LeagueFullError: League is full
            LeagueServiceError: User already in league
        """
        with get_db_session() if db is None else db as session:
            # Find league by invite code
            league = session.query(League).filter(League.invite_code == invite_code).first()
            if not league:
                raise InviteCodeError("Invalid invite code")

            # Check if league is joinable
            if league.status not in ["setup", "drafting"]:
                raise LeagueServiceError("League is not accepting new members")

            # Check if user exists
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise LeagueServiceError("User not found")

            # Check if user already has a team in this league
            existing_team = session.query(Team).filter(
                and_(Team.league_id == league.league_id, Team.user_id == user_id)
            ).first()

            if existing_team:
                raise LeagueServiceError("User already has a team in this league")

            # Check if league is full
            current_team_count = session.query(Team).filter(
                Team.league_id == league.league_id
            ).count()

            if league.is_full(current_team_count):
                raise LeagueFullError("League is full")

            # Determine team name
            if not team_name:
                team_name = f"{user.display_name or user.username}'s Team"

            # Check for duplicate team names in league
            existing_name = session.query(Team).filter(
                and_(Team.league_id == league.league_id, Team.name == team_name)
            ).first()

            if existing_name:
                team_name = f"{team_name} ({user.username})"

            # Determine waiver priority (last to join gets highest priority number)
            max_priority = session.query(Team).filter(
                Team.league_id == league.league_id
            ).count() + 1

            # Create team
            team = Team(
                league_id=league.league_id,
                user_id=user_id,
                name=team_name,
                wins=0,
                losses=0,
                ties=0,
                points_for=0.0,
                points_against=0.0,
                waiver_priority=max_priority,
                faab_budget=100,
                roster=[]
            )

            session.add(team)
            session.commit()

            logger.info(f"User {user.username} joined league {league.name}")
            return team

    def leave_league(
        self,
        league_id: str,
        user_id: str,
        db: Optional[Session] = None
    ) -> None:
        """
        Leave a league (remove team)

        Args:
            league_id: League ID
            user_id: User ID
            db: Optional database session

        Raises:
            LeagueServiceError: Cannot leave league or user not in league
        """
        with get_db_session() if db is None else db as session:
            league = session.query(League).filter(League.league_id == league_id).first()
            if not league:
                raise LeagueNotFoundError("League not found")

            # Commissioner cannot leave their own league
            if str(league.commissioner_id) == str(user_id):
                raise LeagueServiceError("Commissioner cannot leave their own league")

            # Only allow leaving during setup phase
            if league.status != "setup":
                raise LeagueServiceError("Cannot leave league after setup phase")

            # Find and remove team
            team = session.query(Team).filter(
                and_(Team.league_id == league_id, Team.user_id == user_id)
            ).first()

            if not team:
                raise LeagueServiceError("User is not in this league")

            # Adjust waiver priorities for remaining teams
            teams_to_adjust = session.query(Team).filter(
                and_(
                    Team.league_id == league_id,
                    Team.waiver_priority > team.waiver_priority
                )
            ).all()

            for team_to_adjust in teams_to_adjust:
                team_to_adjust.waiver_priority -= 1

            session.delete(team)
            session.commit()

            logger.info(f"User {user_id} left league {league.name}")

    def get_league_teams(self, league_id: str, db: Optional[Session] = None) -> List[Team]:
        """Get all teams in a league"""
        with get_db_session() if db is None else db as session:
            return session.query(Team).filter(
                Team.league_id == league_id
            ).order_by(Team.waiver_priority).all()

    def get_user_team_in_league(
        self,
        league_id: str,
        user_id: str,
        db: Optional[Session] = None
    ) -> Optional[Team]:
        """Get user's team in specific league"""
        with get_db_session() if db is None else db as session:
            return session.query(Team).filter(
                and_(Team.league_id == league_id, Team.user_id == user_id)
            ).first()

    # Configuration Helpers

    def _generate_invite_code(self, session: Session) -> str:
        """Generate unique invite code"""
        while True:
            # Generate code with uppercase letters and numbers
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                          for _ in range(self.invite_code_length))

            # Check if code is unique
            existing = session.query(League).filter(League.invite_code == code).first()
            if not existing:
                return code

    def _get_default_scoring_rules(self, sport: str, custom_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get default scoring rules for sport with optional customizations"""
        defaults = {
            "mlb": {
                "hitting": {
                    "hits": 1, "doubles": 2, "triples": 3, "home_runs": 4,
                    "rbis": 1, "runs": 1, "stolen_bases": 2, "walks": 1, "strikeouts": -1
                },
                "pitching": {
                    "wins": 5, "saves": 5, "innings_pitched": 1, "strikeouts": 1,
                    "earned_runs": -1, "hits_allowed": -0.5, "walks_allowed": -0.5
                }
            },
            "nfl": {
                "passing": {
                    "yards": 0.04, "touchdowns": 4, "interceptions": -2, "completions": 0.1
                },
                "rushing": {
                    "yards": 0.1, "touchdowns": 6, "attempts": 0.1
                },
                "receiving": {
                    "yards": 0.1, "touchdowns": 6, "receptions": 1, "targets": 0.1
                },
                "kicking": {
                    "field_goals": 3, "extra_points": 1, "missed_fg": -1
                },
                "defense": {
                    "touchdowns": 6, "sacks": 1, "interceptions": 2, "fumble_recoveries": 2
                }
            },
            "wnba": {
                "scoring": {
                    "points": 1, "field_goals_made": 0.5, "three_pointers": 1
                },
                "rebounding": {
                    "rebounds": 1.2, "offensive_rebounds": 0.5, "defensive_rebounds": 0.7
                },
                "playmaking": {
                    "assists": 1.5, "steals": 2, "blocks": 2
                },
                "turnovers": {
                    "turnovers": -1, "personal_fouls": -0.5
                }
            }
        }

        base_rules = defaults.get(sport, {})

        # Apply custom overrides
        if custom_settings and "scoring_rules" in custom_settings:
            self._deep_merge_dict(base_rules, custom_settings["scoring_rules"])

        return base_rules

    def _get_default_roster_settings(self, sport: str, custom_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get default roster settings for sport with optional customizations"""
        defaults = {
            "mlb": {
                "starting_positions": ["C", "1B", "2B", "3B", "SS", "OF", "OF", "OF", "P", "P"],
                "bench_spots": 5,
                "ir_spots": 2,
                "max_per_position": {"P": 10, "C": 3, "1B": 3, "2B": 3, "3B": 3, "SS": 3, "OF": 8},
                "total_roster_size": 17
            },
            "nfl": {
                "starting_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"],
                "bench_spots": 6,
                "ir_spots": 1,
                "max_per_position": {"QB": 3, "RB": 6, "WR": 6, "TE": 3, "K": 2, "DEF": 2},
                "total_roster_size": 16
            },
            "wnba": {
                "starting_positions": ["PG", "SG", "SF", "PF", "C", "FLEX", "FLEX"],
                "bench_spots": 5,
                "ir_spots": 1,
                "max_per_position": {"PG": 3, "SG": 3, "SF": 3, "PF": 3, "C": 3},
                "total_roster_size": 13
            }
        }

        base_settings = defaults.get(sport, defaults["nfl"])  # Default to NFL if sport not found

        # Apply custom overrides
        if custom_settings and "roster_settings" in custom_settings:
            self._deep_merge_dict(base_settings, custom_settings["roster_settings"])

        return base_settings

    def _get_default_draft_settings(self, custom_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get default draft settings with optional customizations"""
        defaults = {
            "draft_type": "snake",  # snake, auction, linear
            "pick_timer_seconds": 90,
            "auto_draft_enabled": True,
            "draft_order": "random",  # random, commissioner_set, reverse_standings
            "allow_draft_trades": False,
            "pause_on_disconnect": True
        }

        # Apply custom overrides
        if custom_settings and "draft_settings" in custom_settings:
            defaults.update(custom_settings["draft_settings"])

        return defaults

    def _get_default_waiver_settings(self, custom_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get default waiver settings with optional customizations"""
        defaults = {
            "waiver_type": "rolling",  # rolling, reset, faab
            "waiver_period_hours": 24,
            "waiver_budget": 100,  # FAAB budget
            "minimum_bid": 1,
            "waiver_days": ["Wednesday", "Saturday"],  # Days when waivers process
            "allow_same_day_drops": False,
            "waiver_priority_reset": "never"  # never, weekly, playoff
        }

        # Apply custom overrides
        if custom_settings and "waiver_settings" in custom_settings:
            defaults.update(custom_settings["waiver_settings"])

        return defaults

    def _get_default_trade_settings(self, custom_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get default trade settings with optional customizations"""
        defaults = {
            "trade_deadline_week": 13,  # Week of season
            "trade_review_period_hours": 48,
            "commissioner_approval_required": False,
            "league_vote_enabled": False,
            "vote_threshold_percentage": 60,
            "allow_future_picks": True,
            "veto_threshold": 4,  # Number of veto votes needed
            "trade_processing": "immediate"  # immediate, daily, commissioner
        }

        # Apply custom overrides
        if custom_settings and "trade_settings" in custom_settings:
            defaults.update(custom_settings["trade_settings"])

        return defaults

    def _get_default_playoff_settings(self, custom_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get default playoff settings with optional customizations"""
        defaults = {
            "playoff_teams": 6,
            "playoff_start_week": 15,
            "championship_week": 17,
            "playoff_seeding": "record",  # record, points, head_to_head
            "consolation_bracket": True,
            "playoff_matchup_length": 1,  # weeks
            "tiebreaker_rules": ["head_to_head", "points_for", "points_against"]
        }

        # Apply custom overrides
        if custom_settings and "playoff_settings" in custom_settings:
            defaults.update(custom_settings["playoff_settings"])

        return defaults

    def _deep_merge_dict(self, base_dict: Dict[str, Any], override_dict: Dict[str, Any]) -> None:
        """Deep merge override_dict into base_dict"""
        for key, value in override_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge_dict(base_dict[key], value)
            else:
                base_dict[key] = value

    # League Discovery and Search

    def search_leagues(
        self,
        query: Optional[str] = None,
        sport: Optional[str] = None,
        league_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[League]:
        """
        Search for public leagues

        Args:
            query: Search query for league name
            sport: Filter by sport
            league_type: Filter by league type
            status: Filter by status
            limit: Maximum results to return
            offset: Results offset for pagination
            db: Optional database session

        Returns:
            List of matching League instances
        """
        with get_db_session() if db is None else db as session:
            query_obj = session.query(League)

            # Apply filters
            if query:
                query_obj = query_obj.filter(League.name.ilike(f"%{query}%"))

            if sport:
                query_obj = query_obj.filter(League.sport == sport)

            if league_type:
                query_obj = query_obj.filter(League.league_type == league_type)

            if status:
                query_obj = query_obj.filter(League.status == status)

            # Only return leagues that are accepting members
            query_obj = query_obj.filter(League.status.in_(["setup", "drafting"]))

            return query_obj.order_by(League.created_at.desc()).offset(offset).limit(limit).all()

    def get_league_summary(self, league_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Get league summary with team count and basic info

        Args:
            league_id: League ID
            db: Optional database session

        Returns:
            League summary dictionary
        """
        with get_db_session() if db is None else db as session:
            league = session.query(League).filter(League.league_id == league_id).first()
            if not league:
                raise LeagueNotFoundError("League not found")

            team_count = session.query(Team).filter(Team.league_id == league_id).count()
            commissioner = session.query(User).filter(User.user_id == league.commissioner_id).first()

            return {
                "league_id": str(league.league_id),
                "name": league.name,
                "sport": league.sport,
                "league_type": league.league_type,
                "season": league.season,
                "status": league.status,
                "team_count": team_count,
                "max_teams": league.max_teams,
                "is_full": league.is_full(team_count),
                "commissioner": {
                    "user_id": str(commissioner.user_id),
                    "username": commissioner.username,
                    "display_name": commissioner.display_name or commissioner.username
                } if commissioner else None,
                "created_at": league.created_at.isoformat(),
                "invite_code": league.invite_code if league.status == "setup" else None
            }