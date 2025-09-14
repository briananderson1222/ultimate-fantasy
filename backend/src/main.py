from __future__ import annotations

import os

from fastapi import FastAPI

from api.leagues_branding import router as leagues_branding_router
from api.leagues_create import router as leagues_create_router
from api.leagues_join import router as leagues_join_router
from api.leagues_me import router as leagues_me_router
from api.leagues_members import router as leagues_members_router
from api.leagues_public import router as leagues_public_router
from api.leagues_settings import router as leagues_settings_router
from api.lineups import router as lineups_router
from api.me_preferences import router as me_preferences_router
from api.middleware.auth import AuthContextMiddleware
from api.middleware.logging import RequestLoggingMiddleware
from api.scoreboard import router as scoreboard_router
from api.security import configure_security
from api.waivers import router as waivers_router

# from api.waitlist import router as waitlist_router
from models.base import Base
from services.db import get_engine

app = FastAPI(title="Ultimate Fantasy Platform API", version="0.1.0")


# Routers (incrementally added across tasks T028-T034)
app.include_router(leagues_create_router)
app.include_router(leagues_join_router)
app.include_router(lineups_router)
app.include_router(waivers_router)
app.include_router(scoreboard_router)
app.include_router(leagues_public_router)
app.include_router(leagues_settings_router)
app.include_router(leagues_me_router)
app.include_router(leagues_members_router)
app.include_router(leagues_branding_router)
app.include_router(me_preferences_router)
# app.include_router(waitlist_router)

# Middleware
app.add_middleware(AuthContextMiddleware)
app.add_middleware(RequestLoggingMiddleware)
configure_security(app)


@app.on_event("startup")
def _startup_create_tables_if_needed() -> None:
    # For local/dev tests, create tables when using the in-memory SQLite fallback
    url = os.getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    if url.startswith("sqlite"):
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
