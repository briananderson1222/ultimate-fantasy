"""Database-specific SQL utilities for cross-compatibility."""

import os


def get_database_type() -> str:
    """Get the database type from the DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL", "sqlite+pysqlite:///ultimate_fantasy.db")
    if database_url.startswith("postgresql"):
        return "postgresql"
    elif database_url.startswith("sqlite"):
        return "sqlite"
    else:
        # Default to postgresql for other cases
        return "postgresql"


def get_interval_sql(interval: str) -> str:
    """Get database-specific interval SQL."""
    db_type = get_database_type()

    if db_type == "sqlite":
        # SQLite uses datetime() functions
        if "hour" in interval:
            hours = interval.split()[0]
            return f"datetime('now', '-{hours} hours')"
        elif "day" in interval or "hours" in interval:
            if "24 hours" in interval:
                return "datetime('now', '-1 day')"
            elif "72 hours" in interval:
                return "datetime('now', '-3 days')"
            else:
                # Parse number and unit
                parts = interval.split()
                if len(parts) >= 2:
                    number = parts[0]
                    unit = parts[1].rstrip("s")  # Remove plural 's'
                    return f"datetime('now', '-{number} {unit}')"
        return "datetime('now', '-1 day')"  # fallback
    else:
        # PostgreSQL uses INTERVAL
        return f"NOW() - INTERVAL '{interval}'"


def get_now_sql() -> str:
    """Get database-specific NOW() function."""
    db_type = get_database_type()

    if db_type == "sqlite":
        return "datetime('now')"
    else:
        return "NOW()"


def get_extract_sql(field: str, from_expr: str | None = None) -> str:
    """Get database-specific EXTRACT function."""
    db_type = get_database_type()

    if db_type == "sqlite":
        from_expr = from_expr or "datetime('now')"
        if field == "week":
            return f"strftime('%W', {from_expr})"
        elif field == "year":
            return f"strftime('%Y', {from_expr})"
        elif field == "month":
            return f"strftime('%m', {from_expr})"
        elif field == "day":
            return f"strftime('%d', {from_expr})"
        else:
            return f"strftime('%{field[0]}', {from_expr})"
    else:
        from_expr = from_expr or "NOW()"
        return f"EXTRACT({field} FROM {from_expr})"


def get_datetime_comparison_sql(column: str, operator: str, interval: str) -> str:
    """Get database-specific datetime comparison SQL."""
    if operator == ">":
        return f"{column} > {get_interval_sql(interval)}"
    elif operator == "<":
        return f"{column} < {get_interval_sql(interval)}"
    elif operator == ">=":
        return f"{column} >= {get_interval_sql(interval)}"
    elif operator == "<=":
        return f"{column} <= {get_interval_sql(interval)}"
    else:
        return f"{column} {operator} {get_interval_sql(interval)}"


def build_health_query(
    table: str,
    count_field: str = "*",
    where_conditions: list | None = None,
    time_conditions: list | None = None,
) -> str:
    """Build a health check query that works across database types."""
    where_conditions = where_conditions or []
    time_conditions = time_conditions or []

    query = f"SELECT COUNT({count_field}) FROM {table}"

    all_conditions = []

    # Add regular WHERE conditions
    all_conditions.extend(where_conditions)

    # Add time-based conditions
    for time_condition in time_conditions:
        column = time_condition.get("column")
        operator = time_condition.get("operator", ">")
        interval = time_condition.get("interval")

        if column and interval:
            all_conditions.append(
                get_datetime_comparison_sql(column, operator, interval)
            )

    if all_conditions:
        query += " WHERE " + " AND ".join(all_conditions)

    return query


# Common health check queries
HEALTH_QUERIES = {
    "recent_leagues": lambda: build_health_query(
        "leagues",
        time_conditions=[
            {"column": "updated_at", "operator": ">", "interval": "24 hours"}
        ],
    ),
    "recent_users": lambda: build_health_query(
        "users",
        time_conditions=[
            {"column": "last_login_at", "operator": ">", "interval": "24 hours"}
        ],
    ),
    "recent_waivers": lambda: build_health_query(
        "waiver_claims",
        time_conditions=[
            {"column": "created_at", "operator": ">", "interval": "24 hours"}
        ],
    ),
    "recent_lineups": lambda: build_health_query(
        "lineups",
        time_conditions=[
            {"column": "updated_at", "operator": ">", "interval": "1 hour"}
        ],
    ),
    "recent_scores": lambda: build_health_query(
        "player_scores",
        time_conditions=[
            {"column": "updated_at", "operator": ">", "interval": "1 hour"}
        ],
    ),
    "current_week_lineups": lambda: build_health_query(
        "lineups",
        where_conditions=[
            f"week = {get_extract_sql('week')}",
            f"year = {get_extract_sql('year')}",
        ],
    ),
    "current_week_scores": lambda: build_health_query(
        "player_scores",
        where_conditions=[
            f"week = {get_extract_sql('week')}",
            f"year = {get_extract_sql('year')}",
        ],
    ),
    "pending_waivers": lambda: build_health_query(
        "waiver_claims",
        where_conditions=["status = 'pending'", f"process_date <= {get_now_sql()}"],
    ),
    "stale_waitlist": lambda: build_health_query(
        "waitlist_entries",
        where_conditions=["status = 'pending'"],
        time_conditions=[
            {"column": "created_at", "operator": "<", "interval": "72 hours"}
        ],
    ),
}
