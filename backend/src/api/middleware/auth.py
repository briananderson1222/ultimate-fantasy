from __future__ import annotations

import uuid as _uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Very simple auth context extractor.

    Reads `x-user-id` header and stores a parsed UUID (if valid) on `request.state.user_id`.
    Endpoints may still enforce presence/format explicitly.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        user_header = request.headers.get("x-user-id")
        user_id = None
        if user_header:
            try:
                user_id = _uuid.UUID(user_header)
            except ValueError:
                user_id = None
        request.state.user_id = user_id
        return await call_next(request)
