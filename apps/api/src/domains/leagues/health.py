"""League domain health check endpoints."""

import time
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.deps import get_db

from .config import get_league_config

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def leagues_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Health check for the League domain."""
    start_time = time.time()

    health_status: dict[str, Any] = {
        "domain": "leagues",
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

        # League-specific table check
        table_start = time.time()
        league_count = db.execute(text("SELECT COUNT(*) FROM leagues")).scalar()
        table_time = time.time() - table_start

        health_status["checks"]["leagues_table"] = {
            "status": "healthy",
            "response_time_ms": round(table_time * 1000, 2),
            "league_count": league_count,
        }

        # Configuration check
        config = get_league_config()
        health_status["config"] = {
            "max_league_size": config.max_league_size,
            "features_enabled": {
                "branding": config.enable_league_branding,
                "custom_rules": config.enable_custom_rules,
                "commissioner_tools": config.enable_commissioner_tools,
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
async def leagues_detailed_health_check(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Detailed health check for the League domain."""
    detailed_status = await leagues_health_check(db)

    try:
        # Additional detailed checks
        detailed_status["checks"]["league_branding_table"] = {"status": "checking"}

        branding_count = db.execute(
            text("SELECT COUNT(*) FROM league_branding")
        ).scalar()
        detailed_status["checks"]["league_branding_table"] = {
            "status": "healthy",
            "branding_count": branding_count,
        }

        # Check for leagues with recent activity
        from infrastructure.database.sql_utils import HEALTH_QUERIES

        recent_leagues = db.execute(text(HEALTH_QUERIES["recent_leagues"]())).scalar()

        detailed_status["checks"]["recent_activity"] = {
            "status": "healthy",
            "active_leagues_24h": recent_leagues,
        }

    except Exception as e:
        detailed_status["checks"]["detailed_error"] = {
            "status": "failed",
            "error": str(e),
        }

    return detailed_status
