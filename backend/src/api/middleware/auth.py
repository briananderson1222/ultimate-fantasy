from __future__ import annotations

import uuid as _uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Very simple auth context extractor.

    Reads `x-user-id` header and stores a parsed UUID (if valid) on `request.state.user_id`.
    Endpoints may still enforce presence/format explicitly.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        user_header = request.headers.get("x-user-id")
        user_id = None
        if user_header:
            try:
                user_id = _uuid.UUID(user_header)
            except ValueError:
                user_id = None
        request.state.user_id = user_id
        return await call_next(request)

