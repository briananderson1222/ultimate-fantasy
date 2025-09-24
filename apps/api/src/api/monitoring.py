"""
Monitoring and metrics endpoints for Ultimate Fantasy Platform API
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from api.middleware.logging import RequestLoggingMiddleware

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


def get_logging_middleware(request: Request) -> RequestLoggingMiddleware:
    """Extract logging middleware from request for metrics access"""

    # Find the logging middleware in the app's middleware stack
    app = request.app
    for middleware in app.middleware_stack:
        if isinstance(middleware, RequestLoggingMiddleware):
            return middleware

    raise HTTPException(status_code=503, detail="Logging middleware not available")


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "ultimate-fantasy-api",
    }


@router.get("/metrics")
async def get_metrics(
    middleware: RequestLoggingMiddleware = Depends(get_logging_middleware),
) -> dict[str, Any]:
    """Get current application metrics"""

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "metrics": middleware.get_metrics(),
    }


@router.get("/metrics/summary")
async def get_metrics_summary(
    middleware: RequestLoggingMiddleware = Depends(get_logging_middleware),
) -> dict[str, Any]:
    """Get summarized metrics for dashboard display"""

    metrics = middleware.get_metrics()

    # Calculate summary statistics
    total_requests = metrics["requests_total"]
    error_rate = (
        (metrics["errors_total"] / total_requests * 100) if total_requests > 0 else 0
    )
    slow_request_rate = (
        (metrics["slow_requests"] / total_requests * 100) if total_requests > 0 else 0
    )

    # Get top endpoints by request count
    top_endpoints = sorted(
        metrics["requests_by_endpoint"].items(), key=lambda x: x[1], reverse=True
    )[:10]

    # Get status code distribution
    status_codes = metrics["requests_by_status"]
    success_requests = sum(
        count for status, count in status_codes.items() if 200 <= status < 300
    )
    client_error_requests = sum(
        count for status, count in status_codes.items() if 400 <= status < 500
    )
    server_error_requests = sum(
        count for status, count in status_codes.items() if status >= 500
    )

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "summary": {
            "total_requests": total_requests,
            "error_rate_percent": round(error_rate, 2),
            "slow_request_rate_percent": round(slow_request_rate, 2),
            "average_response_time_ms": round(
                metrics["response_time_stats"]["average"] * 1000, 2
            ),
            "p95_response_time_ms": round(
                metrics["response_time_stats"]["p95"] * 1000, 2
            ),
            "status_distribution": {
                "success": success_requests,
                "client_errors": client_error_requests,
                "server_errors": server_error_requests,
            },
            "top_endpoints": [
                {"endpoint": endpoint, "requests": count}
                for endpoint, count in top_endpoints
            ],
        },
    }


@router.post("/metrics/reset")
async def reset_metrics(
    middleware: RequestLoggingMiddleware = Depends(get_logging_middleware),
):
    """Reset all metrics (for development/testing)"""

    middleware.metrics = {
        "requests_total": 0,
        "requests_by_status": {},
        "requests_by_method": {},
        "requests_by_endpoint": {},
        "response_times": [],
        "errors_total": 0,
        "slow_requests": 0,
    }

    return {
        "status": "metrics_reset",
        "timestamp": datetime.now(UTC).isoformat(),
    }
