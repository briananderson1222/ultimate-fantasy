"""Lineup domain health check endpoints."""

import time
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.deps import get_db

from .config import get_lineup_config

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def lineups_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Health check for the Lineup domain."""
    start_time = time.time()

    health_status: dict[str, Any] = {
        "domain": "lineups",
        "status": "healthy",
        "timestamp": int(time.time()),
        "checks": {},
        "config": {},
        "version": "1.0.0",
    }

    try:
        # Database connectivity check
        db_start = time.time()
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        db_time = time.time() - db_start

        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_time * 1000, 2),
        }

        # Lineup-specific table check
        table_start = time.time()
        lineup_count = db.execute(text("SELECT COUNT(*) FROM lineups")).scalar()
        table_time = time.time() - table_start

        health_status["checks"]["lineups_table"] = {
            "status": "healthy",
            "response_time_ms": round(table_time * 1000, 2),
            "lineup_count": lineup_count,
        }

        # Configuration check
        config = get_lineup_config()
        health_status["config"] = {
            "roster_positions": config.roster_positions,
            "max_players": config.max_players_per_lineup,
            "features": {
                "bench_players": config.enable_bench_players,
                "optimizer": config.enable_lineup_optimizer,
                "injury_notifications": config.enable_injury_notifications,
            },
        }

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["error"] = {"status": "failed", "error": str(e)}

    # Overall response time
    total_time = time.time() - start_time
    health_status["response_time_ms"] = round(total_time * 1000, 2)

    return health_status


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def lineups_detailed_health_check(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Detailed health check for the Lineup domain."""
    detailed_status = await lineups_health_check(db)

    try:
        # Check for lineups set for current week
        from infrastructure.database.sql_utils import HEALTH_QUERIES

        current_week_lineups = db.execute(
            text(HEALTH_QUERIES["current_week_lineups"]())
        ).scalar()

        detailed_status["checks"]["current_week_lineups"] = {
            "status": "healthy",
            "current_week_count": current_week_lineups,
        }

        # Check for recent lineup changes
        recent_changes = db.execute(
            text(HEALTH_QUERIES["recent_lineups"]())
        ).scalar()

        detailed_status["checks"]["recent_activity"] = {
            "status": "healthy",
            "changes_last_hour": recent_changes,
        }

    except Exception as e:
        detailed_status["checks"]["detailed_error"] = {
            "status": "failed",
            "error": str(e),
        }

    return detailed_status
