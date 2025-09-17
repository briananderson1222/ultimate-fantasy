"""Trading domain health check endpoints."""

import time
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.deps import get_db

from .config import get_trading_config

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def trading_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Health check for the Trading domain."""
    start_time = time.time()

    health_status = {
        "domain": "trading",
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

        # Trading-specific table checks
        transaction_count = db.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
        waiver_count = db.execute(text("SELECT COUNT(*) FROM waivers")).scalar()

        health_status["checks"]["trading_tables"] = {
            "status": "healthy",
            "transaction_count": transaction_count,
            "waiver_count": waiver_count
        }

        # Configuration check
        config = get_trading_config()
        health_status["config"] = {
            "waiver_period_hours": config.waiver_period_hours,
            "trade_review_hours": config.trade_review_period_hours,
            "features": {
                "waiver_bidding": config.enable_waiver_bidding,
                "trade_analyzer": config.enable_trade_analyzer,
                "trade_vetoing": config.enable_trade_vetoing
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
async def trading_detailed_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Detailed health check for the Trading domain."""
    detailed_status = await trading_health_check(db)

    try:
        # Check for pending waivers
        pending_waivers = db.execute(text("""
            SELECT COUNT(*) FROM waivers
            WHERE status = 'pending'
            AND process_date <= NOW()
        """)).scalar()

        detailed_status["checks"]["pending_waivers"] = {
            "status": "healthy",
            "pending_count": pending_waivers
        }

        # Check for recent trading activity
        recent_transactions = db.execute(text("""
            SELECT COUNT(*) FROM transactions
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)).scalar()

        detailed_status["checks"]["recent_activity"] = {
            "status": "healthy",
            "transactions_24h": recent_transactions
        }

    except Exception as e:
        detailed_status["checks"]["detailed_error"] = {
            "status": "failed",
            "error": str(e)
        }

    return detailed_status
