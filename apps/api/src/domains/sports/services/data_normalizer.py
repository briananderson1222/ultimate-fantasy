"""
Sports data normalization layer for standardizing data from multiple providers.

Provides comprehensive data normalization including:
- Player data standardization across providers
- Team information normalization
- Game/match data formatting
- Statistics normalization and validation
- Position and sport-specific mappings
- Data quality validation and enhancement
- Provider-agnostic data structures
"""

import re
from datetime import datetime
from typing import Any
from uuid import uuid4

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger

logger = get_logger(__name__)


class DataNormalizationError(Exception):
    """Data normalization errors."""


class ValidationError(DataNormalizationError):
    """Data validation errors."""


class SportsDataNormalizer:
    """Normalize and standardize sports data from multiple providers."""

    def __init__(self) -> None:
        # Position mappings for different sports
        self.position_mappings = {
            "nfl": {
                "quarterback": "QB",
                "qb": "QB",
                "running back": "RB",
                "rb": "RB",
                "fullback": "FB",
                "fb": "FB",
                "wide receiver": "WR",
                "wr": "WR",
                "tight end": "TE",
                "te": "TE",
                "kicker": "K",
                "k": "K",
                "placekicker": "K",
                "defense": "DEF",
                "dst": "DEF",
                "def": "DEF",
                "defense/special teams": "DEF",
            },
            "mlb": {
                "pitcher": "P",
                "p": "P",
                "starting pitcher": "SP",
                "sp": "SP",
                "relief pitcher": "RP",
                "rp": "RP",
                "closer": "CL",
                "cl": "CL",
                "catcher": "C",
                "c": "C",
                "first base": "1B",
                "1b": "1B",
                "second base": "2B",
                "2b": "2B",
                "third base": "3B",
                "3b": "3B",
                "shortstop": "SS",
                "ss": "SS",
                "outfield": "OF",
                "of": "OF",
                "left field": "LF",
                "lf": "LF",
                "center field": "CF",
                "cf": "CF",
                "right field": "RF",
                "rf": "RF",
                "designated hitter": "DH",
                "dh": "DH",
            },
            "wnba": {
                "point guard": "PG",
                "pg": "PG",
                "shooting guard": "SG",
                "sg": "SG",
                "guard": "G",
                "g": "G",
                "small forward": "SF",
                "sf": "SF",
                "power forward": "PF",
                "pf": "PF",
                "forward": "F",
                "f": "F",
                "center": "C",
                "c": "C",
            },
        }

        # Team abbreviation standardization
        self.team_abbreviations = {
            "nfl": {
                "arizona cardinals": "ARI",
                "atlanta falcons": "ATL",
                "baltimore ravens": "BAL",
                "buffalo bills": "BUF",
                "carolina panthers": "CAR",
                "chicago bears": "CHI",
                "cincinnati bengals": "CIN",
                "cleveland browns": "CLE",
                "dallas cowboys": "DAL",
                "denver broncos": "DEN",
                "detroit lions": "DET",
                "green bay packers": "GB",
                "houston texans": "HOU",
                "indianapolis colts": "IND",
                "jacksonville jaguars": "JAX",
                "kansas city chiefs": "KC",
                "las vegas raiders": "LV",
                "los angeles chargers": "LAC",
                "los angeles rams": "LAR",
                "miami dolphins": "MIA",
                "minnesota vikings": "MIN",
                "new england patriots": "NE",
                "new orleans saints": "NO",
                "new york giants": "NYG",
                "new york jets": "NYJ",
                "philadelphia eagles": "PHI",
                "pittsburgh steelers": "PIT",
                "san francisco 49ers": "SF",
                "seattle seahawks": "SEA",
                "tampa bay buccaneers": "TB",
                "tennessee titans": "TEN",
                "washington commanders": "WAS",
            },
        }

        # Injury status mappings
        self.injury_status_mappings = {
            "healthy": "healthy",
            "active": "healthy",
            "out": "out",
            "inactive": "out",
            "injured reserve": "out",
            "ir": "out",
            "questionable": "questionable",
            "q": "questionable",
            "doubtful": "doubtful",
            "d": "doubtful",
            "probable": "questionable",  # Map probable to questionable
            "p": "questionable",
            "day-to-day": "questionable",
            "gtd": "questionable",  # Game time decision
        }

        # Game status mappings
        self.game_status_mappings = {
            "scheduled": "scheduled",
            "pre": "scheduled",
            "pregame": "scheduled",
            "in progress": "in_progress",
            "live": "in_progress",
            "active": "in_progress",
            "halftime": "in_progress",
            "break": "in_progress",
            "final": "final",
            "finished": "final",
            "completed": "final",
            "postponed": "postponed",
            "delayed": "postponed",
            "suspended": "suspended",
            "cancelled": "cancelled",
            "canceled": "cancelled",
        }

        # Standard stat names for different sports
        self.stat_mappings = {
            "nfl": {
                "passing_yards": ["passingYards", "passYds", "pass_yds", "py"],
                "passing_touchdowns": [
                    "passingTouchdowns",
                    "passTds",
                    "pass_tds",
                    "ptd",
                ],
                "interceptions": ["interceptions", "ints", "int"],
                "rushing_yards": ["rushingYards", "rushYds", "rush_yds", "ry"],
                "rushing_touchdowns": [
                    "rushingTouchdowns",
                    "rushTds",
                    "rush_tds",
                    "rtd",
                ],
                "receiving_yards": ["receivingYards", "recYds", "rec_yds", "rey"],
                "receiving_touchdowns": [
                    "receivingTouchdowns",
                    "recTds",
                    "rec_tds",
                    "retd",
                ],
                "receptions": ["receptions", "rec", "catches"],
                "targets": ["targets", "tgt"],
                "fumbles": ["fumbles", "fum"],
                "fumbles_lost": ["fumblesLost", "fumLost", "fl"],
            },
            "mlb": {
                "at_bats": ["atBats", "ab"],
                "hits": ["hits", "h"],
                "home_runs": ["homeRuns", "hr"],
                "runs_batted_in": ["runsBattedIn", "rbi"],
                "runs": ["runs", "r"],
                "stolen_bases": ["stolenBases", "sb"],
                "batting_average": ["battingAverage", "avg", "ba"],
                "on_base_percentage": ["onBasePercentage", "obp"],
                "slugging_percentage": ["sluggingPercentage", "slg"],
                "innings_pitched": ["inningsPitched", "ip"],
                "earned_runs": ["earnedRuns", "er"],
                "earned_run_average": ["earnedRunAverage", "era"],
                "wins": ["wins", "w"],
                "losses": ["losses", "l"],
                "saves": ["saves", "sv"],
                "strikeouts": ["strikeouts", "so", "k"],
                "walks": ["walks", "bb"],
                "hits_allowed": ["hitsAllowed", "ha"],
            },
            "wnba": {
                "points": ["points", "pts"],
                "rebounds": ["rebounds", "reb"],
                "assists": ["assists", "ast"],
                "steals": ["steals", "stl"],
                "blocks": ["blocks", "blk"],
                "turnovers": ["turnovers", "to"],
                "field_goals_made": ["fieldGoalsMade", "fgm"],
                "field_goals_attempted": ["fieldGoalsAttempted", "fga"],
                "field_goal_percentage": ["fieldGoalPercentage", "fg_pct"],
                "three_point_made": ["threePointMade", "3pm"],
                "three_point_attempted": ["threePointAttempted", "3pa"],
                "three_point_percentage": ["threePointPercentage", "3p_pct"],
                "free_throws_made": ["freeThrowsMade", "ftm"],
                "free_throws_attempted": ["freeThrowsAttempted", "fta"],
                "free_throw_percentage": ["freeThrowPercentage", "ft_pct"],
                "minutes": ["minutes", "min"],
            },
        }

    def normalize_player_data(
        self,
        raw_data: dict[str, Any],
        provider: str,
        sport: str,
    ) -> dict[str, Any]:
        """
        Normalize player data from any provider to standard format.

        Args:
            raw_data: Raw player data from provider
            provider: Data provider name (espn, the_athletic, etc.)
            sport: Sport type (nfl, mlb, wnba)

        Returns:
            Normalized player data
        """
        try:
            # Extract basic player information
            player_data = {
                "player_id": self._generate_or_extract_id(raw_data, "player_id"),
                "external_id": str(raw_data.get("external_id", raw_data.get("id", ""))),
                "name": self._normalize_name(raw_data.get("name", "")),
                "position": self._normalize_position(
                    raw_data.get("position", ""), sport
                ),
                "team_id": self._normalize_team_id(raw_data.get("team_id", ""), sport),
                "sport": sport.lower(),
                "injury_status": self._normalize_injury_status(
                    raw_data.get("injury_status", "healthy")
                ),
                "injury_description": raw_data.get("injury_description"),
            }

            # Add optional fields if available
            optional_fields = [
                "jersey_number",
                "height",
                "weight",
                "age",
                "experience",
                "birth_date",
                "college",
                "salary",
                "contract_years",
            ]

            for field in optional_fields:
                if field in raw_data and raw_data[field] is not None:
                    player_data[field] = raw_data[field]

            # Normalize season stats if present
            if raw_data.get("season_stats"):
                player_data["season_stats"] = self._normalize_stats(
                    raw_data["season_stats"], sport
                )

            # Normalize game stats if present
            if raw_data.get("game_stats"):
                player_data["game_stats"] = self._normalize_stats(
                    raw_data["game_stats"], sport
                )

            # Normalize projections if present
            if raw_data.get("projections"):
                player_data["projections"] = self._normalize_projections(
                    raw_data["projections"], sport
                )

            # Add metadata
            player_data["normalized_at"] = datetime.utcnow().isoformat()
            player_data["source_provider"] = provider

            # Validate normalized data
            self._validate_player_data(player_data, sport)

            return player_data

        except Exception as e:
            logger.error(f"Failed to normalize player data: {e}")
            raise DataNormalizationError(f"Player data normalization failed: {e}")

    def normalize_team_data(
        self,
        raw_data: dict[str, Any],
        provider: str,
        sport: str,
    ) -> dict[str, Any]:
        """
        Normalize team data from any provider to standard format.

        Args:
            raw_data: Raw team data from provider
            provider: Data provider name
            sport: Sport type

        Returns:
            Normalized team data
        """
        try:
            team_data = {
                "team_id": self._normalize_team_id(raw_data.get("team_id", ""), sport),
                "name": raw_data.get("name", ""),
                "city": raw_data.get("city", ""),
                "abbreviation": self._normalize_team_id(
                    raw_data.get("abbreviation", ""), sport
                ),
                "sport": sport.lower(),
                "conference": raw_data.get("conference"),
                "division": raw_data.get("division"),
                "logo_url": raw_data.get("logo_url"),
                "colors": raw_data.get("colors", []),
                "founded_year": raw_data.get("founded_year"),
                "stadium": raw_data.get("stadium"),
                "coach": raw_data.get("coach"),
            }

            # Add metadata
            team_data["normalized_at"] = datetime.utcnow().isoformat()
            team_data["source_provider"] = provider

            # Validate normalized data
            self._validate_team_data(team_data, sport)

            return team_data

        except Exception as e:
            logger.error(f"Failed to normalize team data: {e}")
            raise DataNormalizationError(f"Team data normalization failed: {e}")

    def normalize_game_data(
        self,
        raw_data: dict[str, Any],
        provider: str,
        sport: str,
    ) -> dict[str, Any]:
        """
        Normalize game/match data from any provider to standard format.

        Args:
            raw_data: Raw game data from provider
            provider: Data provider name
            sport: Sport type

        Returns:
            Normalized game data
        """
        try:
            game_data = {
                "game_id": self._generate_or_extract_id(raw_data, "game_id"),
                "external_id": str(raw_data.get("external_id", raw_data.get("id", ""))),
                "sport": sport.lower(),
                "home_team": self._normalize_team_id(
                    raw_data.get("home_team", ""), sport
                ),
                "away_team": self._normalize_team_id(
                    raw_data.get("away_team", ""), sport
                ),
                "scheduled_at": self._normalize_datetime(raw_data.get("scheduled_at")),
                "status": self._normalize_game_status(
                    raw_data.get("status", "scheduled")
                ),
                "week": raw_data.get("week"),
                "season": raw_data.get("season"),
            }

            # Add score information if available
            if "home_score" in raw_data:
                game_data["home_score"] = self._safe_int(raw_data["home_score"])
            if "away_score" in raw_data:
                game_data["away_score"] = self._safe_int(raw_data["away_score"])

            # Add game state information
            optional_fields = [
                "period",
                "time_remaining",
                "is_final",
                "attendance",
                "weather",
                "temperature",
                "wind",
                "surface",
            ]

            for field in optional_fields:
                if field in raw_data and raw_data[field] is not None:
                    game_data[field] = raw_data[field]

            # Add metadata
            game_data["normalized_at"] = datetime.utcnow().isoformat()
            game_data["source_provider"] = provider

            # Validate normalized data
            self._validate_game_data(game_data, sport)

            return game_data

        except Exception as e:
            logger.error(f"Failed to normalize game data: {e}")
            raise DataNormalizationError(f"Game data normalization failed: {e}")

    def normalize_stats_data(
        self,
        raw_stats: dict[str, Any],
        player_id: str,
        sport: str,
        game_id: str | None = None,
        week: int | None = None,
        season: str | None = None,
    ) -> dict[str, Any]:
        """
        Normalize player statistics data.

        Args:
            raw_stats: Raw statistics data
            player_id: Player identifier
            sport: Sport type
            game_id: Optional game identifier
            week: Optional week number
            season: Optional season

        Returns:
            Normalized statistics data
        """
        try:
            stats_data = {
                "player_id": player_id,
                "sport": sport.lower(),
                "stats": self._normalize_stats(raw_stats, sport),
                "fantasy_points": self._calculate_fantasy_points(raw_stats, sport),
            }

            # Add context information
            if game_id:
                stats_data["game_id"] = game_id
            if week:
                stats_data["week"] = week
            if season:
                stats_data["season"] = season

            # Add metadata
            stats_data["normalized_at"] = datetime.utcnow().isoformat()

            return stats_data

        except Exception as e:
            logger.error(f"Failed to normalize stats data: {e}")
            raise DataNormalizationError(f"Stats data normalization failed: {e}")

    def batch_normalize_players(
        self,
        raw_players: list[dict[str, Any]],
        provider: str,
        sport: str,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Normalize multiple players efficiently.

        Args:
            raw_players: List of raw player data
            provider: Data provider name
            sport: Sport type

        Returns:
            Tuple of (normalized_players, error_messages)
        """
        normalized_players = []
        error_messages = []

        for i, raw_player in enumerate(raw_players):
            try:
                normalized = self.normalize_player_data(raw_player, provider, sport)
                normalized_players.append(normalized)
            except Exception as e:
                error_msg = f"Failed to normalize player {i}: {e}"
                error_messages.append(error_msg)
                logger.warning(error_msg)

        logger.info(
            f"Batch normalized {len(normalized_players)}/{len(raw_players)} players "
            f"with {len(error_messages)} errors"
        )

        return normalized_players, error_messages

    # Private helper methods

    def _generate_or_extract_id(self, data: dict[str, Any], field: str) -> str:
        """Generate or extract ID from data."""
        if data.get(field):
            return str(data[field])
        elif data.get("id"):
            return str(data["id"])
        else:
            return str(uuid4())

    def _normalize_name(self, name: str) -> str:
        """Normalize player name."""
        if not name:
            return ""

        # Remove extra whitespace and standardize format
        name = re.sub(r"\s+", " ", name.strip())

        # Handle common name formats
        if "," in name:
            # "Last, First" -> "First Last"
            parts = name.split(",", 1)
            if len(parts) == 2:
                name = f"{parts[1].strip()} {parts[0].strip()}"

        return name.title()

    def _normalize_position(self, position: str, sport: str) -> str:
        """Normalize player position."""
        if not position:
            return ""

        position_lower = position.lower().strip()
        sport_mappings = self.position_mappings.get(sport.lower(), {})

        return sport_mappings.get(position_lower, position.upper())

    def _normalize_team_id(self, team_id: str, sport: str) -> str:
        """Normalize team identifier."""
        if not team_id:
            return ""

        team_id = team_id.strip().upper()

        # Check if it's already a valid abbreviation
        if len(team_id) <= 4:
            return team_id

        # Try to find abbreviation from full name
        team_lower = team_id.lower()
        sport_teams = self.team_abbreviations.get(sport.lower(), {})

        return sport_teams.get(team_lower, team_id)

    def _normalize_injury_status(self, status: str) -> str:
        """Normalize injury status."""
        if not status:
            return "healthy"

        status_lower = status.lower().strip()
        return self.injury_status_mappings.get(status_lower, "healthy")

    def _normalize_game_status(self, status: str) -> str:
        """Normalize game status."""
        if not status:
            return "scheduled"

        status_lower = status.lower().strip()
        return self.game_status_mappings.get(status_lower, "scheduled")

    def _normalize_datetime(self, dt_str: str | datetime | None) -> str | None:
        """Normalize datetime string to ISO format."""
        if not dt_str:
            return None

        if isinstance(dt_str, datetime):
            return dt_str.isoformat()

        try:
            # Try to parse various datetime formats
            if isinstance(dt_str, str):
                # Handle common formats
                parsed_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                return parsed_dt.isoformat()
        except Exception:
            logger.warning(f"Could not parse datetime: {dt_str}")

        return str(dt_str)  # Return as-is if parsing fails

    def _normalize_stats(self, stats: dict[str, Any], sport: str) -> dict[str, Any]:
        """Normalize statistics to standard format."""
        if not stats:
            return {}

        sport_mappings = self.stat_mappings.get(sport.lower(), {})
        normalized_stats = {}

        # Map provider-specific stat names to standard names
        for standard_name, provider_names in sport_mappings.items():
            for provider_name in provider_names:
                if provider_name in stats:
                    value = stats[provider_name]
                    if value is not None:
                        normalized_stats[standard_name] = self._safe_numeric(value)
                        break

        # Include any unmapped stats as-is
        for key, value in stats.items():
            if key not in [name for names in sport_mappings.values() for name in names]:
                if value is not None:
                    normalized_stats[key] = self._safe_numeric(value)

        return normalized_stats

    def _normalize_projections(
        self, projections: dict[str, Any], sport: str
    ) -> dict[str, Any]:
        """Normalize projection data."""
        if not projections:
            return {}

        # Apply same normalization as stats
        normalized = self._normalize_stats(projections, sport)

        # Ensure fantasy_points is included
        if "fantasy_points" not in normalized and "fantasy_points" in projections:
            normalized["fantasy_points"] = self._safe_numeric(
                projections["fantasy_points"]
            )

        return normalized

    def _calculate_fantasy_points(self, stats: dict[str, Any], sport: str) -> float:
        """Calculate fantasy points from stats using standard scoring."""
        if not stats:
            return 0.0

        points = 0.0

        if sport.lower() == "nfl":
            # Standard NFL PPR scoring
            points += stats.get("passing_yards", 0) * 0.04  # 1 pt per 25 yards
            points += stats.get("passing_touchdowns", 0) * 4
            points -= stats.get("interceptions", 0) * 2

            points += stats.get("rushing_yards", 0) * 0.1  # 1 pt per 10 yards
            points += stats.get("rushing_touchdowns", 0) * 6

            points += stats.get("receiving_yards", 0) * 0.1
            points += stats.get("receiving_touchdowns", 0) * 6
            points += stats.get("receptions", 0) * 1  # PPR

            points -= stats.get("fumbles_lost", 0) * 2

        elif sport.lower() == "mlb":
            # Standard MLB scoring
            points += stats.get("runs", 0) * 1
            points += stats.get("hits", 0) * 1
            points += stats.get("home_runs", 0) * 4
            points += stats.get("runs_batted_in", 0) * 1
            points += stats.get("stolen_bases", 0) * 2

            # Pitching
            points += stats.get("wins", 0) * 5
            points += stats.get("saves", 0) * 5
            points += stats.get("strikeouts", 0) * 1
            points -= stats.get("earned_runs", 0) * 1
            points -= stats.get("hits_allowed", 0) * 0.5
            points -= stats.get("walks", 0) * 0.5

        elif sport.lower() == "wnba":
            # Standard WNBA scoring
            points += stats.get("points", 0) * 1
            points += stats.get("rebounds", 0) * 1.2
            points += stats.get("assists", 0) * 1.5
            points += stats.get("steals", 0) * 3
            points += stats.get("blocks", 0) * 3
            points -= stats.get("turnovers", 0) * 1

        return round(points, 2)

    def _safe_numeric(self, value: Any) -> int | float:
        """Safely convert value to numeric."""
        if value is None:
            return 0

        try:
            # Try int first, then float
            if isinstance(value, (int, float)):
                return value
            elif isinstance(value, str):
                if "." in value:
                    return float(value)
                else:
                    return int(value)
            else:
                return float(value)
        except (ValueError, TypeError):
            return 0

    def _safe_int(self, value: Any) -> int:
        """Safely convert value to integer."""
        try:
            return int(float(value)) if value is not None else 0
        except (ValueError, TypeError):
            return 0

    # Validation methods

    def _validate_player_data(self, player_data: dict[str, Any], sport: str) -> None:
        """Validate normalized player data."""
        required_fields = ["player_id", "name", "sport"]

        for field in required_fields:
            if not player_data.get(field):
                raise ValidationError(f"Required field '{field}' is missing or empty")

        # Validate sport
        if player_data["sport"] not in ["nfl", "mlb", "wnba", "nba"]:
            raise ValidationError(f"Invalid sport: {player_data['sport']}")

        # Validate position if present
        if player_data.get("position"):
            valid_positions = set(
                self.position_mappings.get(sport.lower(), {}).values()
            )
            if player_data["position"] not in valid_positions:
                logger.warning(
                    f"Unknown position '{player_data['position']}' for sport {sport}"
                )

    def _validate_team_data(self, team_data: dict[str, Any], sport: str) -> None:
        """Validate normalized team data."""
        required_fields = ["team_id", "name", "sport"]

        for field in required_fields:
            if not team_data.get(field):
                raise ValidationError(f"Required field '{field}' is missing or empty")

    def _validate_game_data(self, game_data: dict[str, Any], sport: str) -> None:
        """Validate normalized game data."""
        required_fields = ["game_id", "sport", "home_team", "away_team"]

        for field in required_fields:
            if not game_data.get(field):
                raise ValidationError(f"Required field '{field}' is missing or empty")

        # Validate teams are different
        if game_data["home_team"] == game_data["away_team"]:
            raise ValidationError("Home and away teams cannot be the same")


# Export alias for backward compatibility
DataNormalizer = SportsDataNormalizer

# Global normalizer instance
_normalizer: SportsDataNormalizer | None = None


def get_data_normalizer() -> SportsDataNormalizer:
    """Get the global data normalizer instance."""
    global _normalizer
    if _normalizer is None:
        _normalizer = SportsDataNormalizer()
    return _normalizer


def reset_data_normalizer() -> None:
    """Reset the global normalizer (useful for testing)."""
    global _normalizer
    _normalizer = None
