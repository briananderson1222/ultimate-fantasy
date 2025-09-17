from __future__ import annotations

import os
import uuid as _uuid
from collections.abc import Awaitable, Callable

import jwt
from jwt import PyJWKClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Authentication context extractor.

    Supports two modes controlled by env AUTH_MODE:
    - dev (default): HS256 tokens via AUTH_DEV_SECRET, and legacy x-user-id fallback.
    - jwks: RS256 tokens validated against AUTH_JWKS_URL (+ optional AUD/ISS).
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        mode = os.getenv("AUTH_MODE", "dev").lower()
        authz = request.headers.get("authorization") or request.headers.get(
            "Authorization"
        )

        request.state.user_id = None
        request.state.user_claims = None

        if authz and authz.startswith("Bearer "):
            token = authz.split(" ", 1)[1].strip()
            try:
                if mode == "jwks":
                    jwks_url = os.getenv("AUTH_JWKS_URL")
                    audience = os.getenv("AUTH_AUDIENCE")
                    issuer = os.getenv("AUTH_ISSUER")
                    if jwks_url:
                        jwk_client = PyJWKClient(jwks_url)
                        signing_key = jwk_client.get_signing_key_from_jwt(token)
                        claims = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=["RS256"],
                            audience=audience,
                            issuer=issuer,
                        )
                    else:
                        claims = {}
                else:  # dev
                    secret = os.getenv("AUTH_DEV_SECRET", "dev-secret")
                    claims = jwt.decode(token, secret, algorithms=["HS256"])

                sub = claims.get("sub") if isinstance(claims, dict) else None
                request.state.user_claims = claims if isinstance(claims, dict) else None

                # Persist/update user from claims when available
                if request.state.user_claims and sub:
                    try:
                        from domains.users.services.user_service import UserService
                        from services.db import SessionLocal

                        with SessionLocal() as sess:
                            user = UserService(sess).ensure_user_from_claims(
                                request.state.user_claims
                            )
                            request.state.user_id = user.user_id
                    except Exception:
                        # fallback: set UUID from sub if valid, otherwise None
                        try:
                            request.state.user_id = _uuid.UUID(str(sub))
                        except ValueError:
                            request.state.user_id = None
            except Exception:
                # Leave user unset; downstream deps may raise 401
                request.state.user_id = None
                request.state.user_claims = None
        # Legacy fallback in dev mode only
        elif mode.startswith("dev"):
            user_header = request.headers.get("x-user-id")
            if user_header:
                try:
                    request.state.user_id = _uuid.UUID(user_header)
                except ValueError:
                    request.state.user_id = None

        return await call_next(request)
