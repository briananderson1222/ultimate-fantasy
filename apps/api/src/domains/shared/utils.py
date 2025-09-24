"""
Shared utility functions used across multiple domains.

This module provides common helper functions to avoid duplication and ensure
consistency across the fantasy sports platform.
"""

import hashlib
import uuid as _uuid
from datetime import date, timedelta
from typing import Any


def generate_invite_code(length: int = 6) -> str:
    """
    Generate a random invite code for leagues.

    Args:
        length: Length of the invite code

    Returns:
        Random alphanumeric invite code
    """
    import random
    import string

    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def normalize_team_name(name: str) -> str:
    """
    Normalize team name for consistency.

    Args:
        name: Raw team name

    Returns:
        Normalized team name
    """
    return name.strip().title() if name else "Unnamed Team"


def calculate_week_from_date(game_date: date, season_start: date) -> int:
    """
    Calculate fantasy week number from game date.

    Args:
        game_date: Date of the game
        season_start: Start date of the fantasy season

    Returns:
        Week number (1-based)
    """
    if game_date < season_start:
        return 1

    days_diff = (game_date - season_start).days
    week = (days_diff // 7) + 1
    return max(1, min(week, 17))  # Cap at 17 weeks for NFL


def get_current_season() -> str:
    """
    Get the current fantasy season year.

    Returns:
        Current season as string (e.g., "2024")
    """
    today = date.today()
    # Fantasy seasons typically start in late summer/early fall
    # If it's before July, we're probably still in the previous season
    if today.month < 7:
        return str(today.year - 1)
    return str(today.year)


def sanitize_player_name(name: str) -> str:
    """
    Sanitize player name for database storage and display.

    Args:
        name: Raw player name

    Returns:
        Sanitized player name
    """
    if not name:
        return "Unknown Player"

    # Remove extra whitespace and normalize case
    sanitized = " ".join(name.strip().split())

    # Handle common name patterns
    # Convert "LASTNAME, FIRSTNAME" to "Firstname Lastname"
    if ", " in sanitized:
        parts = sanitized.split(", ")
        if len(parts) == 2:
            sanitized = f"{parts[1]} {parts[0]}"

    return sanitized.title()


def hash_consistent_id(input_string: str) -> str:
    """
    Generate a consistent hash-based ID from input string.
    Useful for creating predictable test data or external ID mapping.

    Args:
        input_string: String to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.md5(input_string.encode()).hexdigest()


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate if a string is a valid UUID.

    Args:
        uuid_string: String to validate

    Returns:
        True if valid UUID, False otherwise
    """
    try:
        _uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float with fallback.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer with fallback.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def merge_player_stats(
    current_stats: dict[str, Any] | None, new_stats: dict[str, Any]
) -> dict[str, Any]:
    """
    Merge player statistics dictionaries, handling nested structures.

    Args:
        current_stats: Existing statistics
        new_stats: New statistics to merge

    Returns:
        Merged statistics dictionary
    """
    if not current_stats:
        return new_stats.copy()

    merged = current_stats.copy()

    for key, value in new_stats.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            # Recursively merge nested dictionaries
            merged[key] = merge_player_stats(merged[key], value)
        else:
            # Override with new value
            merged[key] = value

    return merged


def format_fantasy_points(points: float, precision: int = 2) -> str:
    """
    Format fantasy points for display.

    Args:
        points: Raw fantasy points
        precision: Decimal places to show

    Returns:
        Formatted points string
    """
    return f"{points:.{precision}f}"


def calculate_win_percentage(wins: int, losses: int, ties: int = 0) -> float:
    """
    Calculate win percentage for team records.

    Args:
        wins: Number of wins
        losses: Number of losses
        ties: Number of ties (count as 0.5 wins)

    Returns:
        Win percentage as decimal (0.0 to 1.0)
    """
    total_games = wins + losses + ties
    if total_games == 0:
        return 0.0

    effective_wins = wins + (ties * 0.5)
    return effective_wins / total_games


def is_playoff_eligible(
    wins: int, losses: int, ties: int = 0, min_games: int = 10
) -> bool:
    """
    Determine if a team is eligible for playoffs.

    Args:
        wins: Number of wins
        losses: Number of losses
        ties: Number of ties
        min_games: Minimum games required for eligibility

    Returns:
        True if playoff eligible
    """
    total_games = wins + losses + ties
    return total_games >= min_games


def get_trade_deadline(season_start: date, sport: str = "nfl") -> date:
    """
    Calculate trade deadline based on sport and season start.

    Args:
        season_start: Start of fantasy season
        sport: Sport type

    Returns:
        Trade deadline date
    """
    if sport.lower() == "nfl":
        # NFL trade deadline is typically around week 9
        return season_start + timedelta(weeks=8)
    elif sport.lower() == "mlb":
        # MLB trade deadline is end of July
        year = season_start.year
        return date(year, 7, 31)
    elif sport.lower() == "wnba":
        # WNBA trade deadline varies, use mid-season
        return season_start + timedelta(weeks=6)
    else:
        # Default to mid-season
        return season_start + timedelta(weeks=8)


def validate_roster_construction(
    players: list[dict[str, Any]], sport: str, max_players: int = 15
) -> list[str]:
    """
    Validate roster construction rules for a sport.

    Args:
        players: List of player dictionaries with position info
        sport: Sport type
        max_players: Maximum players allowed

    Returns:
        List of validation error messages
    """
    errors = []

    if len(players) > max_players:
        errors.append(f"Roster exceeds maximum of {max_players} players")

    # Count positions
    position_counts = {}
    for player in players:
        position = player.get("position", "").upper()
        position_counts[position] = position_counts.get(position, 0) + 1

    # Sport-specific validation
    if sport.lower() == "nfl":
        required_positions = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
        for pos, min_count in required_positions.items():
            if position_counts.get(pos, 0) < min_count:
                errors.append(f"Need at least {min_count} {pos}")

    elif sport.lower() == "mlb":
        required_positions = {
            "C": 1,
            "1B": 1,
            "2B": 1,
            "3B": 1,
            "SS": 1,
            "OF": 3,
            "P": 5,
        }
        for pos, min_count in required_positions.items():
            if position_counts.get(pos, 0) < min_count:
                errors.append(f"Need at least {min_count} {pos}")

    return errors


def generate_cache_key(*parts: str, prefix: str = "") -> str:
    """
    Generate a consistent cache key from components.

    Args:
        *parts: Key components
        prefix: Optional prefix

    Returns:
        Cache key string
    """
    key_parts = [prefix] if prefix else []
    key_parts.extend(str(part) for part in parts if part)
    return ":".join(key_parts)
