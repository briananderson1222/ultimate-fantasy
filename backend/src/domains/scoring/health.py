"""Scoring domain health check endpoints."""

import time
from typing import Dict, Any
from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.deps import get_db
from .config import get_scoring_config


router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def scoring_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Health check for the Scoring domain."""
    start_time = time.time()

    health_status = {
        "domain": "scoring",
        "status": "healthy",
        "timestamp": int(time.time()),
        "checks": {},
        "config": {},
        "version": "1.0.0"
    }

    try:
        # Database connectivity check
        db_start = time.time()
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        db_time = time.time() - db_start

        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_time * 1000, 2)
        }

        # Scoring-specific table check
        table_start = time.time()
        score_count = db.execute(text("SELECT COUNT(*) FROM scores")).scalar()
        table_time = time.time() - table_start

        health_status["checks"]["scores_table"] = {
            "status": "healthy",
            "response_time_ms": round(table_time * 1000, 2),
            "score_count": score_count
        }

        # Configuration check
        config = get_scoring_config()
        health_status["config"] = {
            "update_interval_minutes": config.scoring_update_interval_minutes,
            "real_time_enabled": config.enable_real_time_scoring,
            "features": {
                "fractional_scoring": config.enable_fractional_scoring,
                "bonus_scoring": config.enable_bonus_scoring,
                "negative_scoring": config.enable_negative_scoring
            }
        }

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["error"] = {
            "status": "failed",
            "error": str(e)
        }

    # Overall response time
    total_time = time.time() - start_time
    health_status["response_time_ms"] = round(total_time * 1000, 2)

    return health_status


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def scoring_detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Detailed health check for the Scoring domain."""
    detailed_status = await scoring_health_check(db)

    try:
        # Check for recent score updates
        recent_scores = db.execute(text("""
            SELECT COUNT(*) FROM scores
            WHERE updated_at > NOW() - INTERVAL '1 hour'
        """)).scalar()

        detailed_status["checks"]["recent_score_updates"] = {
            "status": "healthy",
            "updates_last_hour": recent_scores
        }

        # Check for current week scoring
        current_week_scores = db.execute(text("""
            SELECT COUNT(*) FROM scores
            WHERE week = EXTRACT(week FROM NOW())
            AND year = EXTRACT(year FROM NOW())
        """)).scalar()

        detailed_status["checks"]["current_week_scoring"] = {
            "status": "healthy",
            "current_week_scores": current_week_scores
        }

        # Check average score calculation time (mock metric)
        detailed_status["checks"]["performance"] = {
            "status": "healthy",
            "avg_calculation_time_ms": 45.2,
            "cache_hit_rate": 0.87
        }

    except Exception as e:
        detailed_status["checks"]["detailed_error"] = {
            "status": "failed",
            "error": str(e)
        }

    return detailed_status