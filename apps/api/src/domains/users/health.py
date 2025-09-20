"""User domain health check endpoints."""

import time
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.deps import get_db

from .config import get_user_config

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def users_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Health check for the User domain."""
    start_time = time.time()

    health_status: dict[str, Any] = {
        "domain": "users",
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

        # User-specific table check
        table_start = time.time()
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        table_time = time.time() - table_start

        health_status["checks"]["users_table"] = {
            "status": "healthy",
            "response_time_ms": round(table_time * 1000, 2),
            "user_count": user_count,
        }

        # Configuration check
        config = get_user_config()
        health_status["config"] = {
            "jwt_algorithm": config.jwt_algorithm,
            "token_expiry_minutes": config.access_token_expire_minutes,
            "security": {
                "password_min_length": config.password_min_length,
                "max_login_attempts": config.max_login_attempts,
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
async def users_detailed_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Detailed health check for the User domain."""
    detailed_status = await users_health_check(db)

    try:
        # Additional detailed checks
        preferences_count = db.execute(
            text("SELECT COUNT(*) FROM user_preferences")
        ).scalar()
        detailed_status["checks"]["user_preferences_table"] = {
            "status": "healthy",
            "preferences_count": preferences_count,
        }

        # Check for users with recent activity
        recent_users = db.execute(
            text(
                """
            SELECT COUNT(*) FROM users
            WHERE last_login > NOW() - INTERVAL '24 hours'
        """
            )
        ).scalar()

        detailed_status["checks"]["recent_activity"] = {
            "status": "healthy",
            "active_users_24h": recent_users,
        }

    except Exception as e:
        detailed_status["checks"]["detailed_error"] = {
            "status": "failed",
            "error": str(e),
        }

    return detailed_status
