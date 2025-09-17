from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Middleware and security
from api.middleware.auth import AuthContextMiddleware
from api.middleware.logging import RequestLoggingMiddleware
from api.security import configure_security

# Domain API routers
from domains.leagues.api.leagues_branding import router as leagues_branding_router
from domains.leagues.api.leagues_create import router as leagues_create_router
from domains.leagues.api.leagues_join import router as leagues_join_router
from domains.leagues.api.leagues_me import router as leagues_me_router
from domains.leagues.api.leagues_members import router as leagues_members_router
from domains.leagues.api.leagues_public import router as leagues_public_router
from domains.leagues.api.leagues_settings import router as leagues_settings_router

# Domain health check routers
from domains.leagues.health import router as leagues_health_router
from domains.lineups.api.lineups import router as lineups_router
from domains.lineups.health import router as lineups_health_router
from domains.scoring.api.scoreboard import router as scoreboard_router
from domains.scoring.health import router as scoring_health_router
from domains.trading.api.waivers import router as waivers_router
from domains.trading.health import router as trading_health_router

# User and preferences
from domains.users.api.me_preferences import router as me_preferences_router
from domains.users.health import router as users_health_router
from domains.waitlist.api.waitlist import router as waitlist_router
from domains.waitlist.health import router as waitlist_health_router

# Infrastructure
from infrastructure.container import (
    cleanup_container,
    get_container,
    initialize_container,
)
from infrastructure.database.session_factory import get_session_factory
from infrastructure.middleware.domain_router import (
    DomainMetricsMiddleware,
    DomainRouterMiddleware,
    DomainSecurityMiddleware,
    get_domain_metrics,
    set_metrics_middleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    # Startup
    database_url = os.getenv("DATABASE_URL", "sqlite:///./ultimate_fantasy.db")

    # Initialize dependency injection container
    await initialize_container(database_url)

    # Create tables if needed (for SQLite development)
    if database_url.startswith("sqlite"):
        session_factory = get_session_factory()
        await session_factory.create_tables()

    yield

    # Shutdown
    await cleanup_container()


app = FastAPI(
    title="Ultimate Fantasy Platform API",
    version="0.1.0",
    lifespan=lifespan
)


# Domain-based routers with /api prefix
app.include_router(leagues_create_router, prefix="/api", tags=["leagues"])
app.include_router(leagues_join_router, prefix="/api", tags=["leagues"])
app.include_router(leagues_public_router, prefix="/api", tags=["leagues"])
app.include_router(leagues_settings_router, prefix="/api", tags=["leagues"])
app.include_router(leagues_me_router, prefix="/api", tags=["leagues"])
app.include_router(leagues_members_router, prefix="/api", tags=["leagues"])
app.include_router(leagues_branding_router, prefix="/api", tags=["leagues"])

# Legacy routes without prefix for backward compatibility
app.include_router(leagues_create_router, tags=["leagues-legacy"])
app.include_router(leagues_join_router, tags=["leagues-legacy"])
app.include_router(leagues_public_router, tags=["leagues-legacy"])
app.include_router(leagues_settings_router, tags=["leagues-legacy"])
app.include_router(leagues_me_router, tags=["leagues-legacy"])
app.include_router(leagues_members_router, tags=["leagues-legacy"])
app.include_router(leagues_branding_router, tags=["leagues-legacy"])

app.include_router(lineups_router, prefix="/api", tags=["lineups"])
app.include_router(scoreboard_router, prefix="/api", tags=["scoring"])
app.include_router(waivers_router, prefix="/api", tags=["trading"])
app.include_router(waitlist_router, prefix="/api", tags=["waitlist"])
app.include_router(me_preferences_router, prefix="/api", tags=["users"])

# Legacy routes without prefix for backward compatibility
app.include_router(lineups_router, tags=["lineups-legacy"])
app.include_router(scoreboard_router, tags=["scoring-legacy"])
app.include_router(waivers_router, tags=["trading-legacy"])
app.include_router(waitlist_router, tags=["waitlist-legacy"])
app.include_router(me_preferences_router, tags=["users-legacy"])

# Domain health check endpoints
app.include_router(leagues_health_router, prefix="/api/domains/leagues", tags=["health", "leagues"])
app.include_router(users_health_router, prefix="/api/domains/users", tags=["health", "users"])
app.include_router(lineups_health_router, prefix="/api/domains/lineups", tags=["health", "lineups"])
app.include_router(trading_health_router, prefix="/api/domains/trading", tags=["health", "trading"])
app.include_router(scoring_health_router, prefix="/api/domains/scoring", tags=["health", "scoring"])
app.include_router(waitlist_health_router, prefix="/api/domains/waitlist", tags=["health", "waitlist"])

# Domain-specific middleware (order matters!)
metrics_middleware = DomainMetricsMiddleware(app)
set_metrics_middleware(metrics_middleware)

app.add_middleware(DomainSecurityMiddleware)
app.add_middleware(DomainMetricsMiddleware)
app.add_middleware(DomainRouterMiddleware)

# Core middleware
app.add_middleware(AuthContextMiddleware)
app.add_middleware(RequestLoggingMiddleware)
configure_security(app)


@app.get("/health", tags=["system"])
async def health_check():
    """Application health check endpoint."""
    try:
        container = await get_container()
        health = await container.health_check()
        return {"status": "healthy", "details": health}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/health/services", tags=["system"])
async def services_health_check():
    """Services health check endpoint."""
    try:
        container = await get_container()
        registry = container.get_service_registry()
        return registry.health_check()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/system/info", tags=["system"])
async def system_info():
    """System configuration information."""
    try:
        container = await get_container()
        config = container.get_configuration()
        session_factory = get_session_factory()

        return {
            "container": config,
            "database": session_factory.get_engine_info(),
            "environment": {
                "database_url_provided": bool(os.getenv("DATABASE_URL")),
                "async_mode": os.getenv("DATABASE_ASYNC", "false").lower() == "true",
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/metrics/domains", tags=["metrics"])
async def domain_metrics():
    """Get domain-specific metrics."""
    return get_domain_metrics()


@app.post("/metrics/reset", tags=["metrics"])
async def reset_metrics():
    """Reset domain metrics."""
    from infrastructure.middleware.domain_router import reset_domain_metrics
    reset_domain_metrics()
    return {"status": "metrics_reset"}
