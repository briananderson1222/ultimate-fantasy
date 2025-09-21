from __future__ import annotations

import uuid as _uuid
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ..domains.sports.models.player import Player
from ..domains.scoring.models.score import Score
from ..domains.leagues.models.league import League
from ..services.sports_data_service import SportsDataService, SportType, PlayerData
from ..infrastructure.database.session_factory import get_db_session
from ..infrastructure.logging.domain_logger import get_logger

logger = get_logger(__name__)


class InjuryStatus(Enum):
    """Player injury statuses"""
    HEALTHY = "healthy"
    QUESTIONABLE = "questionable"
    DOUBTFUL = "doubtful"
    OUT = "out"


@dataclass
class PlayerSearchFilters:
    """Player search filter criteria"""
    sport: Optional[str] = None
    position: Optional[str] = None
    team_id: Optional[str] = None
    injury_status: Optional[str] = None
    min_projection: Optional[float] = None
    available_only: bool = False  # Not on any roster


@dataclass
class PlayerProjection:
    """Player fantasy projection"""
    player_id: str
    week: int
    projected_points: float
    confidence: float  # 0.0 to 1.0
    stat_projections: Dict[str, float]
    injury_risk: float  # 0.0 to 1.0


class PlayerServiceError(Exception):
    """Base exception for player service errors"""
    pass


class PlayerNotFoundError(PlayerServiceError):
    """Player not found errors"""
    pass


class PlayerService:
    """
    Player service for stats and status management

    Implements T029 requirements:
    - PlayerService with stats and status management
    - Add search, filtering, and projection calculations
    - Include injury status updates and team affiliations
    """

    def __init__(self, sports_data_service: Optional[SportsDataService] = None):
        self.sports_data_service = sports_data_service or SportsDataService()
        self.projection_confidence_threshold = 0.7
        self.stats_cache_duration_minutes = 15

    # Player Retrieval Methods

    def get_player(self, player_id: str, db: Optional[Session] = None) -> Optional[Player]:
        """Get player by ID"""
        with get_db_session() if db is None else db as session:
            return session.query(Player).filter(Player.player_id == player_id).first()

    def get_player_by_external_id(
        self,
        external_id: str,
        sport: str,
        db: Optional[Session] = None
    ) -> Optional[Player]:
        """Get player by external ID and sport"""
        with get_db_session() if db is None else db as session:
            return session.query(Player).filter(
                and_(Player.external_id == external_id, Player.sport == sport)
            ).first()

    def get_players_by_team(
        self,
        team_id: str,
        sport: str,
        db: Optional[Session] = None
    ) -> List[Player]:
        """Get all players for a team"""
        with get_db_session() if db is None else db as session:
            return session.query(Player).filter(
                and_(Player.team_id == team_id, Player.sport == sport)
            ).order_by(Player.name).all()

    def search_players(
        self,
        query: Optional[str] = None,
        filters: Optional[PlayerSearchFilters] = None,
        limit: int = 50,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[Player]:
        """
        Search players with filtering options

        Args:
            query: Text search for player name
            filters: Additional search filters
            limit: Maximum results to return
            offset: Results offset for pagination
            db: Optional database session

        Returns:
            List of matching Player instances
        """
        with get_db_session() if db is None else db as session:
            query_obj = session.query(Player)

            # Apply text search
            if query:
                search_pattern = f"%{query}%"
                query_obj = query_obj.filter(Player.name.ilike(search_pattern))

            # Apply filters
            if filters:
                if filters.sport:
                    query_obj = query_obj.filter(Player.sport == filters.sport)

                if filters.position:
                    query_obj = query_obj.filter(Player.position == filters.position)

                if filters.team_id:
                    query_obj = query_obj.filter(Player.team_id == filters.team_id)

                if filters.injury_status:
                    query_obj = query_obj.filter(Player.injury_status == filters.injury_status)

                # TODO: Implement available_only filter (requires roster checking)
                # TODO: Implement min_projection filter (requires projections calculation)

            return query_obj.order_by(Player.name).offset(offset).limit(limit).all()

    def get_trending_players(
        self,
        sport: str,
        trend_type: str = "hot",  # hot, cold, rising, falling
        days: int = 7,
        limit: int = 20,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trending players based on recent performance

        Args:
            sport: Sport to analyze
            trend_type: Type of trend to analyze
            days: Number of days to analyze
            limit: Maximum results to return
            db: Optional database session

        Returns:
            List of player trend data
        """
        cutoff_date = date.today() - timedelta(days=days)

        with get_db_session() if db is None else db as session:
            # Get players with recent scores
            recent_scores = session.query(
                Score.player_id,
                func.avg(Score.fantasy_points).label("avg_points"),
                func.count(Score.score_id).label("game_count"),
                func.max(Score.fantasy_points).label("max_points"),
                func.min(Score.fantasy_points).label("min_points")
            ).join(Player).filter(
                and_(
                    Player.sport == sport,
                    Score.game_date >= cutoff_date,
                    Score.is_final == True
                )
            ).group_by(Score.player_id).subquery()

            # Join with player data
            query_obj = session.query(
                Player,
                recent_scores.c.avg_points,
                recent_scores.c.game_count,
                recent_scores.c.max_points,
                recent_scores.c.min_points
            ).join(
                recent_scores,
                Player.player_id == recent_scores.c.player_id
            )

            # Apply trend-specific ordering
            if trend_type == "hot":
                query_obj = query_obj.order_by(desc(recent_scores.c.avg_points))
            elif trend_type == "cold":
                query_obj = query_obj.order_by(recent_scores.c.avg_points)
            elif trend_type == "rising":
                # TODO: Implement rising trend calculation (requires historical comparison)
                query_obj = query_obj.order_by(desc(recent_scores.c.max_points))
            elif trend_type == "falling":
                # TODO: Implement falling trend calculation (requires historical comparison)
                query_obj = query_obj.order_by(recent_scores.c.min_points)

            results = query_obj.limit(limit).all()

            trending_data = []
            for player, avg_points, game_count, max_points, min_points in results:
                trending_data.append({
                    "player": self._get_player_summary(player),
                    "trend_data": {
                        "avg_points": float(avg_points) if avg_points else 0.0,
                        "game_count": int(game_count) if game_count else 0,
                        "max_points": float(max_points) if max_points else 0.0,
                        "min_points": float(min_points) if min_points else 0.0,
                        "trend_type": trend_type,
                        "period_days": days
                    }
                })

            return trending_data

    # Player Statistics Methods

    def get_player_stats(
        self,
        player_id: str,
        stat_type: str = "season",  # season, recent, career
        season: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get player statistics

        Args:
            player_id: Player ID
            stat_type: Type of stats to retrieve
            season: Optional season filter
            db: Optional database session

        Returns:
            Statistics dictionary or None if not found
        """
        with get_db_session() if db is None else db as session:
            player = session.query(Player).filter(Player.player_id == player_id).first()
            if not player:
                return None

            if stat_type == "season":
                return player.season_stats
            elif stat_type == "recent":
                # Get recent game stats (last 7 games)
                recent_scores = session.query(Score).filter(
                    and_(
                        Score.player_id == player_id,
                        Score.is_final == True
                    )
                ).order_by(desc(Score.game_date)).limit(7).all()

                if not recent_scores:
                    return None

                # Aggregate recent stats
                total_points = sum(score.fantasy_points for score in recent_scores)
                game_count = len(recent_scores)

                return {
                    "games_played": game_count,
                    "total_fantasy_points": total_points,
                    "avg_fantasy_points": total_points / game_count if game_count > 0 else 0,
                    "recent_games": [
                        {
                            "date": score.game_date.isoformat(),
                            "points": score.fantasy_points,
                            "stats": score.stat_values
                        }
                        for score in recent_scores
                    ]
                }
            elif stat_type == "career":
                # TODO: Implement career stats aggregation
                return player.season_stats

        return None

    def get_player_projections(
        self,
        player_id: str,
        week: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Optional[PlayerProjection]:
        """
        Get player fantasy projections

        Args:
            player_id: Player ID
            week: Optional specific week (defaults to next week)
            db: Optional database session

        Returns:
            PlayerProjection or None if not available
        """
        with get_db_session() if db is None else db as session:
            player = session.query(Player).filter(Player.player_id == player_id).first()
            if not player:
                return None

            # Use stored projections or calculate basic projection
            if player.projections:
                projected_points = player.projections.get("fantasy_points", 0.0)
                stat_projections = player.projections.get("stats", {})
            else:
                # Calculate basic projection from recent performance
                recent_avg = self._calculate_recent_average(player_id, db=session)
                projected_points = recent_avg
                stat_projections = {}

            # Calculate confidence based on recent consistency
            confidence = self._calculate_projection_confidence(player_id, db=session)

            # Calculate injury risk
            injury_risk = self._calculate_injury_risk(player)

            return PlayerProjection(
                player_id=player_id,
                week=week or self._get_current_week(),
                projected_points=projected_points,
                confidence=confidence,
                stat_projections=stat_projections,
                injury_risk=injury_risk
            )

    def compare_players(
        self,
        player_ids: List[str],
        stat_categories: Optional[List[str]] = None,
        season: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple players across stat categories

        Args:
            player_ids: List of player IDs to compare
            stat_categories: Optional specific stats to compare
            season: Optional season filter
            db: Optional database session

        Returns:
            Player comparison data
        """
        with get_db_session() if db is None else db as session:
            players = session.query(Player).filter(
                Player.player_id.in_(player_ids)
            ).all()

            if not players:
                return {"players": [], "comparison": {}}

            comparison_data = {
                "players": [self._get_player_summary(player) for player in players],
                "comparison": {}
            }

            # Default stat categories by sport
            if not stat_categories:
                sport = players[0].sport
                stat_categories = self._get_default_stat_categories(sport)

            # Compare each stat category
            for category in stat_categories:
                category_data = {}
                for player in players:
                    stats = player.season_stats or {}
                    category_data[str(player.player_id)] = stats.get(category, 0)

                comparison_data["comparison"][category] = category_data

            return comparison_data

    # Player Status Updates

    def update_injury_status(
        self,
        player_id: str,
        injury_status: str,
        injury_description: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Player:
        """
        Update player injury status

        Args:
            player_id: Player ID
            injury_status: New injury status
            injury_description: Optional injury description
            db: Optional database session

        Returns:
            Updated Player instance

        Raises:
            PlayerNotFoundError: Player not found
        """
        with get_db_session() if db is None else db as session:
            player = session.query(Player).filter(Player.player_id == player_id).first()
            if not player:
                raise PlayerNotFoundError("Player not found")

            # Validate injury status
            if injury_status not in [status.value for status in InjuryStatus]:
                raise PlayerServiceError(f"Invalid injury status: {injury_status}")

            old_status = player.injury_status
            player.injury_status = injury_status
            player.injury_description = injury_description

            session.commit()

            logger.info(f"Player {player.name} injury status updated: {old_status} -> {injury_status}")
            return player

    def update_team_affiliation(
        self,
        player_id: str,
        new_team_id: Optional[str],
        db: Optional[Session] = None
    ) -> Player:
        """
        Update player team affiliation

        Args:
            player_id: Player ID
            new_team_id: New team ID (None for free agent)
            db: Optional database session

        Returns:
            Updated Player instance

        Raises:
            PlayerNotFoundError: Player not found
        """
        with get_db_session() if db is None else db as session:
            player = session.query(Player).filter(Player.player_id == player_id).first()
            if not player:
                raise PlayerNotFoundError("Player not found")

            old_team = player.team_id
            player.team_id = new_team_id

            session.commit()

            logger.info(f"Player {player.name} team updated: {old_team} -> {new_team_id}")
            return player

    async def sync_player_from_external(
        self,
        external_id: str,
        sport: str,
        force_update: bool = False,
        db: Optional[Session] = None
    ) -> Player:
        """
        Sync player data from external sports API

        Args:
            external_id: External player ID
            sport: Sport type
            force_update: Force update even if recently synced
            db: Optional database session

        Returns:
            Updated or created Player instance
        """
        with get_db_session() if db is None else db as session:
            # Check if player exists
            player = session.query(Player).filter(
                and_(Player.external_id == external_id, Player.sport == sport)
            ).first()

            # Skip if recently updated (unless forced)
            if player and not force_update:
                time_since_update = datetime.utcnow() - player.updated_at.replace(tzinfo=None)
                if time_since_update.total_seconds() < (self.stats_cache_duration_minutes * 60):
                    return player

            # Get data from external API
            sport_type = SportType(sport)
            player_data = await self.sports_data_service.get_player_data(external_id, sport_type)

            if not player_data:
                if player:
                    return player  # Return existing player if API fails
                else:
                    raise PlayerServiceError(f"Could not retrieve player data for {external_id}")

            if player:
                # Update existing player
                player.name = player_data.name
                player.position = player_data.position
                player.team_id = player_data.team_id
                player.injury_status = player_data.injury_status
                player.injury_description = player_data.injury_description
                player.season_stats = player_data.season_stats
                player.game_stats = player_data.game_stats
                player.projections = player_data.projections
            else:
                # Create new player
                player = Player(
                    external_id=player_data.external_id,
                    name=player_data.name,
                    position=player_data.position,
                    team_id=player_data.team_id,
                    sport=player_data.sport,
                    injury_status=player_data.injury_status,
                    injury_description=player_data.injury_description,
                    season_stats=player_data.season_stats,
                    game_stats=player_data.game_stats,
                    projections=player_data.projections
                )
                session.add(player)

            session.commit()

            logger.info(f"Player synced from external API: {player.name}")
            return player

    # Helper Methods

    def _get_player_summary(self, player: Player) -> Dict[str, Any]:
        """Get player summary for API responses"""
        return {
            "player_id": str(player.player_id),
            "external_id": player.external_id,
            "name": player.name,
            "position": player.position,
            "team_id": player.team_id,
            "sport": player.sport,
            "injury_status": player.injury_status,
            "injury_description": player.injury_description
        }

    def _calculate_recent_average(self, player_id: str, games: int = 5, db: Optional[Session] = None) -> float:
        """Calculate recent average fantasy points"""
        with get_db_session() if db is None else db as session:
            recent_scores = session.query(Score.fantasy_points).filter(
                and_(
                    Score.player_id == player_id,
                    Score.is_final == True
                )
            ).order_by(desc(Score.game_date)).limit(games).all()

            if not recent_scores:
                return 0.0

            total_points = sum(score.fantasy_points for score in recent_scores)
            return total_points / len(recent_scores)

    def _calculate_projection_confidence(self, player_id: str, db: Optional[Session] = None) -> float:
        """Calculate projection confidence based on performance consistency"""
        with get_db_session() if db is None else db as session:
            recent_scores = session.query(Score.fantasy_points).filter(
                and_(
                    Score.player_id == player_id,
                    Score.is_final == True
                )
            ).order_by(desc(Score.game_date)).limit(10).all()

            if len(recent_scores) < 3:
                return 0.5  # Low confidence with insufficient data

            points = [score.fantasy_points for score in recent_scores]
            avg_points = sum(points) / len(points)

            if avg_points == 0:
                return 0.3

            # Calculate coefficient of variation (lower = more consistent = higher confidence)
            variance = sum((p - avg_points) ** 2 for p in points) / len(points)
            std_dev = variance ** 0.5
            cv = std_dev / avg_points if avg_points > 0 else 1.0

            # Convert CV to confidence (inverse relationship)
            confidence = max(0.1, min(1.0, 1.0 - (cv / 2.0)))
            return confidence

    def _calculate_injury_risk(self, player: Player) -> float:
        """Calculate injury risk factor"""
        if player.injury_status == "healthy":
            return 0.1
        elif player.injury_status == "questionable":
            return 0.3
        elif player.injury_status == "doubtful":
            return 0.6
        elif player.injury_status == "out":
            return 1.0
        else:
            return 0.2

    def _get_current_week(self) -> int:
        """Get current week number (simplified implementation)"""
        # TODO: Implement proper week calculation based on sport and season
        return 1

    def _get_default_stat_categories(self, sport: str) -> List[str]:
        """Get default stat categories for sport"""
        categories = {
            "mlb": ["hits", "home_runs", "rbis", "runs", "stolen_bases", "era", "wins", "saves"],
            "nfl": ["passing_yards", "passing_touchdowns", "rushing_yards", "rushing_touchdowns",
                   "receiving_yards", "receptions", "field_goals"],
            "wnba": ["points", "rebounds", "assists", "steals", "blocks", "three_pointers"]
        }
        return categories.get(sport, ["fantasy_points"])

    # League-Specific Methods

    def get_available_players(
        self,
        league_id: str,
        filters: Optional[PlayerSearchFilters] = None,
        limit: int = 50,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[Player]:
        """
        Get players available for waiver/free agency in a league

        Args:
            league_id: League ID
            filters: Optional search filters
            limit: Maximum results to return
            offset: Results offset for pagination
            db: Optional database session

        Returns:
            List of available Player instances
        """
        with get_db_session() if db is None else db as session:
            league = session.query(League).filter(League.league_id == league_id).first()
            if not league:
                raise PlayerServiceError("League not found")

            # TODO: Implement availability check by checking team rosters
            # For now, return all players filtered by sport
            if not filters:
                filters = PlayerSearchFilters()
            filters.sport = league.sport

            return self.search_players(filters=filters, limit=limit, offset=offset, db=session)

    def get_roster_eligible_positions(
        self,
        player_id: str,
        league_id: str,
        db: Optional[Session] = None
    ) -> List[str]:
        """
        Get positions a player is eligible for in a league

        Args:
            player_id: Player ID
            league_id: League ID
            db: Optional database session

        Returns:
            List of eligible position strings
        """
        with get_db_session() if db is None else db as session:
            player = session.query(Player).filter(Player.player_id == player_id).first()
            league = session.query(League).filter(League.league_id == league_id).first()

            if not player or not league:
                return []

            # Get roster settings from league
            roster_settings = league.roster_settings or {}
            eligible_positions = [player.position]

            # Add flex positions if applicable
            if league.sport == "nfl" and player.position in ["RB", "WR", "TE"]:
                eligible_positions.append("FLEX")
            elif league.sport == "wnba":
                eligible_positions.append("FLEX")

            return eligible_positions
