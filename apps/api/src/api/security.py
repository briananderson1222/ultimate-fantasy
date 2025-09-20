from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable, Iterable

from fastapi import FastAPI, Request, Response
from starlette.middleware.cors import CORSMiddleware


def configure_security(app: FastAPI) -> None:
    def _parse_origins(raw: str | None) -> list[str]:
        if not raw or not raw.strip():
            # Sensible defaults for local web/Expo dev
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8081",
                "http://127.0.0.1:8081",
                "http://localhost:19006",
                "http://127.0.0.1:19006",
                "http://localhost:19000",
                "http://127.0.0.1:19000",
            ]

        raw = raw.strip()

        if raw == "*":
            return ["*"]

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, Iterable) and not isinstance(parsed, (str, bytes)):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
        except json.JSONDecodeError:
            pass

        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    cors_allow_origins = _parse_origins(os.getenv("CORS_ALLOW_ORIGINS"))
    cors_allow_origin_regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX")
    allow_credentials = (
        os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() in {"1", "true", "t", "yes", "y"}
    )

    if "*" in cors_allow_origins:
        cors_allow_origins = ["*"]
        # Starlette forbids wildcard origins with credentials enabled
        allow_credentials = False
        cors_allow_origin_regex = None

    if cors_allow_origin_regex is None:
        cors_allow_origin_regex = (
            r"https?://(localhost|127\.0\.0\.1|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|"
            r"10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|"
            r"172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})(:[0-9]{2,5})?$"
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins,
        allow_origin_regex=cors_allow_origin_regex,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Domain", "X-Response-Time", "X-Metrics-Domain", "X-Metrics-Duration"],
        max_age=600,
    )

    # Basic security headers via a simple middleware
    @app.middleware("http")
    async def _security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-XSS-Protection", "0")
        return response
