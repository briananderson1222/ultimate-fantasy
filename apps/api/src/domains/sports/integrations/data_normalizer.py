"""
Data normalization utilities for sports API integrations.

Provides functions to normalize data from different providers into
consistent formats for the application.
"""

import logging
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)


def normalize_player_data(
    provider_data: dict[str, Any], provider: str
) -> dict[str, Any]:
    """
    Normalize player data from any provider to standard format.

    Args:
        provider_data: Raw player data from provider
        provider: Provider name (espn, athletic, etc.)

    Returns:
        Normalized player data dictionary
    """
    base_fields = {
        "player_id": "",
        "external_id": "",
        "name": "",
        "position": "",
        "team": "",
        "sport": "",
        "status": "active",
        "injury_status": "healthy",
        "height": None,
        "weight": None,
        "age": None,
        "experience": None,
        "jersey_number": None,
    }

    if provider.lower() == "espn":
        return _normalize_espn_player(provider_data)
    elif provider.lower() == "athletic":
        return _normalize_athletic_player(provider_data)
    else:
        # Generic normalization
        normalized = base_fields.copy()
        normalized.update(
            {
                "player_id": str(
                    provider_data.get("id", provider_data.get("player_id", ""))
                ),
                "external_id": str(
                    provider_data.get("external_id", provider_data.get("id", ""))
                ),
                "name": provider_data.get(
                    "name", provider_data.get("display_name", "")
                ),
                "position": provider_data.get("position", ""),
                "team": provider_data.get("team", ""),
                "sport": provider_data.get("sport", ""),
            }
        )
        return normalized


def _normalize_espn_player(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize ESPN player data."""
    return {
        "player_id": str(data.get("id", "")),
        "external_id": str(data.get("id", "")),
        "name": data.get("displayName", ""),
        "position": data.get("position", {}).get("abbreviation", ""),
        "team": data.get("team", {}).get("abbreviation", ""),
        "sport": "NFL",  # ESPN endpoint specific
        "status": "active",
        "injury_status": "healthy",
        "height": data.get("height"),
        "weight": data.get("weight"),
        "age": data.get("age"),
        "experience": data.get("experience"),
        "jersey_number": data.get("jersey"),
        "headshot_url": data.get("headshot", {}).get("href"),
        "bio": data.get("displayName", ""),
        "college": data.get("college", {}).get("name"),
        "birthplace": data.get("birthPlace"),
        "debut_year": data.get("debutYear"),
    }


def _normalize_athletic_player(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize The Athletic player data."""
    return {
        "player_id": str(data.get("id", "")),
        "external_id": str(data.get("id", "")),
        "name": data.get("display_name", ""),
        "position": data.get("position", ""),
        "team": data.get("team", {}).get("abbreviation", ""),
        "sport": data.get("sport", ""),
        "status": "active" if data.get("active", True) else "inactive",
        "injury_status": data.get("injury_status", "healthy"),
        "height": data.get("height"),
        "weight": data.get("weight"),
        "age": data.get("age"),
        "experience": data.get("years_pro"),
        "jersey_number": data.get("jersey_number"),
        "headshot_url": data.get("headshot_url"),
        "salary": data.get("salary"),
        "contract_years": data.get("contract_years"),
        "draft_year": data.get("draft_year"),
        "draft_round": data.get("draft_round"),
        "draft_pick": data.get("draft_pick"),
        "fantasy_rating": data.get("fantasy_rating"),
        "analyst_notes": data.get("analyst_notes"),
    }


def normalize_game_data(
    provider_data: dict[str, Any], provider: str = "generic"
) -> dict[str, Any]:
    """
    Normalize game/schedule data from any provider to standard format.

    Args:
        provider_data: Raw game data from provider
        provider: Provider name

    Returns:
        Normalized game data dictionary
     """
    base_fields: dict[str, Any] = {
        "game_id": "",
        "home_team": "",
        "away_team": "",
        "game_date": None,
        "game_time": None,
        "status": "scheduled",
        "week": None,
        "season": None,
        "sport": "",
        "venue": None,
        "scores": {},
    }

    if provider.lower() == "espn":
        return _normalize_espn_game(provider_data)
    elif provider.lower() == "athletic":
        return _normalize_athletic_game(provider_data)
    else:
        # Generic normalization
        normalized: dict[str, Any] = base_fields.copy()
        normalized.update(
            {
                "game_id": str(
                    provider_data.get("id", provider_data.get("game_id", ""))
                ),
                "home_team": provider_data.get("home_team", ""),
                "away_team": provider_data.get("away_team", ""),
                "status": provider_data.get("status", "scheduled"),
                "sport": provider_data.get("sport", ""),
            }
        )

        # Handle date parsing
        if "game_date" in provider_data:
            normalized["game_date"] = _parse_date(provider_data["game_date"])

        return normalized


def _normalize_espn_game(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize ESPN game data."""
    competition = data.get("competitions", [{}])[0]
    competitors = competition.get("competitors", [])

    home_team: dict[str, Any] = next((c for c in competitors if c.get("homeAway") == "home"), {})
    away_team: dict[str, Any] = next((c for c in competitors if c.get("homeAway") == "away"), {})

    return {
        "game_id": str(data.get("id", "")),
        "home_team": home_team.get("team", {}).get("abbreviation", ""),
        "away_team": away_team.get("team", {}).get("abbreviation", ""),
        "game_date": _parse_date(data.get("date")),
        "game_time": data.get("date"),  # Full datetime
        "status": data.get("status", {}).get("type", {}).get("name", "scheduled"),
        "week": competition.get("week", {}).get("number"),
        "season": data.get("season", {}).get("year"),
        "sport": "NFL",
        "venue": competition.get("venue", {}).get("fullName"),
        "scores": {
            "home": home_team.get("score", 0),
            "away": away_team.get("score", 0),
        },
        "attendance": competition.get("attendance"),
        "neutral_site": competition.get("neutralSite", False),
        "playoff": data.get("season", {}).get("type") != 2,  # 2 = regular season
        "tv_coverage": competition.get("broadcasts", [{}])[0].get("names", []),
    }


def _normalize_athletic_game(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize The Athletic game data."""
    return {
        "game_id": str(data.get("id", "")),
        "home_team": data.get("home_team", {}).get("abbreviation", ""),
        "away_team": data.get("away_team", {}).get("abbreviation", ""),
        "game_date": _parse_date(data.get("scheduled_date")),
        "game_time": data.get("scheduled_date"),
        "status": data.get("status", "scheduled"),
        "week": data.get("week"),
        "season": data.get("season"),
        "sport": data.get("sport", ""),
        "venue": data.get("venue", {}).get("name"),
        "scores": {
            "home": data.get("home_score", 0),
            "away": data.get("away_score", 0),
        },
        "betting_line": data.get("betting_line"),
        "over_under": data.get("over_under"),
        "weather": data.get("weather"),
        "attendance": data.get("attendance"),
        "tv_coverage": data.get("tv_coverage"),
        "referee": data.get("officials", {}).get("referee"),
    }


def normalize_stats_data(
    provider_data: dict[str, Any], position: str = "", provider: str = "generic"
) -> dict[str, Any]:
    """
    Normalize player statistics data from any provider.

    Args:
        provider_data: Raw stats data from provider
        position: Player position for context
        provider: Provider name

    Returns:
        Normalized stats dictionary
    """
    if provider.lower() == "espn":
        return _normalize_espn_stats(provider_data, position)
    elif provider.lower() == "athletic":
        return _normalize_athletic_stats(provider_data, position)
    else:
        # Generic normalization - return as-is with type conversion
        normalized: dict[str, Any] = {}
        for key, value in provider_data.items():
            if isinstance(value, (int, float)):
                normalized[key] = value
            elif (
                isinstance(value, str)
                and value.replace(".", "").replace("-", "").isdigit()
            ):
                try:
                    normalized[key] = float(value) if "." in value else int(value)
                except ValueError:
                    normalized[key] = value
            else:
                normalized[key] = value

        return normalized


def _normalize_espn_stats(data: dict[str, Any], position: str) -> dict[str, Any]:
    """Normalize ESPN statistics data."""
    normalized = {}

    # ESPN has nested structure with categories and stats
    categories = data.get("splits", {}).get("categories", [])

    for category in categories:
        category.get("name", "").lower()
        stats = category.get("stats", [])

        for stat in stats:
            stat_name = stat.get("name", "").lower().replace(" ", "_")
            stat_value = stat.get("value", 0)

            # Convert to appropriate type
            try:
                if isinstance(stat_value, str) and "." in stat_value:
                    normalized[stat_name] = float(stat_value)
                elif isinstance(stat_value, str):
                    normalized[stat_name] = int(stat_value)
                else:
                    normalized[stat_name] = stat_value
            except (ValueError, TypeError):
                normalized[stat_name] = stat_value

    # Add position-specific calculations
    if position == "QB":
        normalized["passer_rating"] = _calculate_passer_rating(normalized)
    elif position in ["RB", "WR", "TE"]:
        normalized["yards_per_touch"] = _calculate_yards_per_touch(normalized)

    return normalized


def _normalize_athletic_stats(data: dict[str, Any], position: str) -> dict[str, Any]:
    """Normalize The Athletic statistics data."""
    normalized = {}

    # The Athletic provides both traditional and advanced stats
    traditional = data.get("traditional_stats", {})
    advanced = data.get("advanced_metrics", {})

    # Merge traditional stats
    for key, value in traditional.items():
        normalized[key] = value

    # Merge advanced stats with prefix
    for key, value in advanced.items():
        normalized[f"adv_{key}"] = value

    return normalized


def _parse_date(date_str: str | None) -> date | None:
    """Parse date string from various formats."""
    if not date_str:
        return None

    try:
        # Try common formats
        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # Try ISO format
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()

    except (ValueError, TypeError):
        logger.warning(f"Failed to parse date: {date_str}")
        return None


def _calculate_passer_rating(stats: dict[str, Any]) -> float:
    """Calculate NFL passer rating."""
    try:
        attempts = float(stats.get("passing_attempts", 0))
        if attempts == 0:
            return 0.0

        completions = float(stats.get("passing_completions", 0))
        yards = float(stats.get("passing_yards", 0))
        touchdowns = float(stats.get("passing_touchdowns", 0))
        interceptions = float(stats.get("interceptions", 0))

        # NFL passer rating formula
        comp_pct = (completions / attempts - 0.3) * 5
        yards_per_att = (yards / attempts - 3) * 0.25
        td_pct = (touchdowns / attempts) * 20
        int_pct = 2.375 - (interceptions / attempts * 25)

        # Clamp values between 0 and 2.375
        comp_pct = max(0, min(2.375, comp_pct))
        yards_per_att = max(0, min(2.375, yards_per_att))
        td_pct = max(0, min(2.375, td_pct))
        int_pct = max(0, min(2.375, int_pct))

        rating = ((comp_pct + yards_per_att + td_pct + int_pct) / 6) * 100
        return round(rating, 1)

    except (TypeError, ZeroDivisionError):
        return 0.0


def _calculate_yards_per_touch(stats: dict[str, Any]) -> float:
    """Calculate yards per touch for skill position players."""
    try:
        rushing_yards = float(stats.get("rushing_yards", 0))
        receiving_yards = float(stats.get("receiving_yards", 0))
        rushing_attempts = float(stats.get("rushing_attempts", 0))
        receptions = float(stats.get("receptions", 0))

        total_yards = rushing_yards + receiving_yards
        total_touches = rushing_attempts + receptions

        if total_touches == 0:
            return 0.0

        return round(total_yards / total_touches, 2)

    except (TypeError, ZeroDivisionError):
        return 0.0


def sanitize_player_name(name: str) -> str:
    """Sanitize and normalize player names."""
    if not name:
        return ""

    # Remove extra whitespace
    name = " ".join(name.split())

    # Handle common suffixes
    suffixes = ["Jr.", "Sr.", "III", "IV", "V"]
    for suffix in suffixes:
        if name.endswith(f" {suffix}"):
            name = name.replace(f" {suffix}", f", {suffix}")

    return name.title()


def normalize_team_abbreviation(team: str, sport: str = "NFL") -> str:
    """Normalize team abbreviations across providers."""
    if not team:
        return ""

    team = team.upper().strip()

    # Common variations mapping
    mappings = {
        "NFL": {"NWE": "NE", "NOR": "NO", "TAM": "TB", "LVR": "LV", "SFO": "SF"},
        "NBA": {"BRK": "BKN", "PHO": "PHX", "NOP": "NO"},
        "MLB": {"ANA": "LAA", "CWS": "CHW", "FLA": "MIA", "MON": "WSH"},
    }

    sport_mappings = mappings.get(sport.upper(), {})
    return sport_mappings.get(team, team)


def calculate_fantasy_points(
    stats: dict[str, Any], position: str, scoring_system: str = "ppr"
) -> float:
    """
    Calculate fantasy points based on stats, position, and scoring system.

    Args:
        stats: Player statistics
        position: Player position
        scoring_system: Scoring system (ppr, half_ppr, standard)

    Returns:
        Total fantasy points
    """
    points = 0.0

    if position == "QB":
        points += stats.get("passing_yards", 0) * 0.04  # 1 pt per 25 yards
        points += stats.get("passing_touchdowns", 0) * 4  # 4 pts per TD
        points -= stats.get("interceptions", 0) * 2  # -2 pts per INT
        points += stats.get("rushing_yards", 0) * 0.1  # 1 pt per 10 yards
        points += stats.get("rushing_touchdowns", 0) * 6  # 6 pts per TD
        points -= stats.get("fumbles", 0) * 2  # -2 pts per fumble

    elif position in ["RB", "WR", "TE"]:
        points += stats.get("rushing_yards", 0) * 0.1  # 1 pt per 10 yards
        points += stats.get("rushing_touchdowns", 0) * 6  # 6 pts per TD
        points += stats.get("receiving_yards", 0) * 0.1  # 1 pt per 10 yards
        points += stats.get("receiving_touchdowns", 0) * 6  # 6 pts per TD
        points -= stats.get("fumbles", 0) * 2  # -2 pts per fumble

        # Reception points based on scoring system
        receptions = stats.get("receptions", 0)
        if scoring_system == "ppr":
            points += receptions * 1  # 1 pt per reception
        elif scoring_system == "half_ppr":
            points += receptions * 0.5  # 0.5 pts per reception

    elif position == "K":
        points += stats.get("field_goals_made", 0) * 3  # 3 pts per FG
        points += stats.get("extra_points_made", 0) * 1  # 1 pt per XP
        points -= stats.get("field_goals_missed", 0) * 1  # -1 pt per missed FG

    elif position == "DEF":
        points += stats.get("defensive_touchdowns", 0) * 6
        points += stats.get("interceptions", 0) * 2
        points += stats.get("fumble_recoveries", 0) * 2
        points += stats.get("sacks", 0) * 1
        points += stats.get("safeties", 0) * 2

        # Points allowed
        points_allowed = stats.get("points_allowed", 0)
        if points_allowed == 0:
            points += 10
        elif points_allowed <= 6:
            points += 7
        elif points_allowed <= 13:
            points += 4
        elif points_allowed <= 20:
            points += 1
        elif points_allowed >= 35:
            points -= 4

    return round(points, 2)
