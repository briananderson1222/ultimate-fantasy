"""Waitlist domain health check endpoints."""

import time
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.deps import get_db

from .config import get_waitlist_config

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def waitlist_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Health check for the Waitlist domain."""
    start_time = time.time()

    health_status: dict[str, Any] = {
        "domain": "waitlist",
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

        # Waitlist-specific table check
        table_start = time.time()
        waitlist_count = db.execute(text("SELECT COUNT(*) FROM waitlists")).scalar()
        table_time = time.time() - table_start

        health_status["checks"]["waitlists_table"] = {
            "status": "healthy",
            "response_time_ms": round(table_time * 1000, 2),
            "waitlist_count": waitlist_count,
        }

        # Configuration check
        config = get_waitlist_config()
        health_status["config"] = {
            "max_waitlist_size": config.max_waitlist_size,
            "auto_invite_enabled": config.auto_invite_enabled,
            "features": {
                "position_visible": config.waitlist_position_visible,
                "priority_enabled": config.enable_waitlist_priority,
                "referral_bonus": config.enable_referral_bonus,
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
async def waitlist_detailed_health_check(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Detailed health check for the Waitlist domain."""
    detailed_status = await waitlist_health_check(db)

    try:
        # Check for active waitlists
        active_waitlists = db.execute(
            text(
                """
            SELECT COUNT(DISTINCT league_id) FROM waitlists
            WHERE status = 'active'
        """
            )
        ).scalar()

        detailed_status["checks"]["active_waitlists"] = {
            "status": "healthy",
            "active_count": active_waitlists,
        }

        # Check for recent waitlist activity
        recent_joins = db.execute(
            text(
                """
            SELECT COUNT(*) FROM waitlists
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """
            )
        ).scalar()

        detailed_status["checks"]["recent_activity"] = {
            "status": "healthy",
            "joins_24h": recent_joins,
        }

        # Check for expired invitations
        expired_invitations = db.execute(
            text(
                """
            SELECT COUNT(*) FROM waitlists
            WHERE status = 'invited'
            AND created_at < NOW() - INTERVAL '72 hours'
        """
            )
        ).scalar()

        detailed_status["checks"]["expired_invitations"] = {
            "status": "healthy" if (expired_invitations or 0) < 10 else "warning",
            "expired_count": expired_invitations,
        }

    except Exception as e:
        detailed_status["checks"]["detailed_error"] = {
            "status": "failed",
            "error": str(e),
        }

    return detailed_status
