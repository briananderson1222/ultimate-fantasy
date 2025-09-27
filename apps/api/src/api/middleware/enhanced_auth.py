"""
Enhanced authentication middleware with rate limiting.

Provides comprehensive authentication and authorization features:
- JWT token validation
- Rate limiting per user/IP
- Request throttling
- Token blacklisting
- Multi-tier authentication
- Security headers
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

import jwt
from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from infrastructure.cache.redis_pool import get_redis_pool
except ImportError:
    get_redis_pool = None

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger

logger = get_logger(__name__)


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""

    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 0

    def __post_init__(self):
        if self.burst_limit == 0:
            self.burst_limit = max(self.requests_per_minute // 2, 5)


@dataclass
class AuthConfig:
    """Authentication configuration."""

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    require_https: bool = True
    allow_anonymous_routes: set[str] = None
    rate_limit_enabled: bool = True
    default_rate_limit: RateLimitRule = None

    def __post_init__(self):
        if self.allow_anonymous_routes is None:
            self.allow_anonymous_routes = {
                "/health",
                "/docs",
                "/redoc",
                "/openapi.json",
                "/auth/login",
                "/auth/register",
                "/auth/refresh",
            }

        if self.default_rate_limit is None:
            self.default_rate_limit = RateLimitRule(
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_limit=10,
            )


class TokenBlacklist:
    """Token blacklist management."""

    def __init__(self, redis_pool=None):
        self.redis_pool = redis_pool
        self._memory_blacklist: set[str] = set()

    async def add_token(self, jti: str, exp: datetime):
        """Add token to blacklist."""
        if self.redis_pool:
            # Store in Redis with expiration
            await self.redis_pool.set(
                "auth",
                f"blacklist:{jti}",
                True,
                ttl=int((exp - datetime.utcnow()).total_seconds()),
            )
        else:
            # Fallback to memory (not recommended for production)
            self._memory_blacklist.add(jti)

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        if self.redis_pool:
            result = await self.redis_pool.get("auth", f"blacklist:{jti}")
            return result is not None
        else:
            return jti in self._memory_blacklist

    async def cleanup_expired(self):
        """Clean up expired tokens from memory blacklist."""
        # Redis handles expiration automatically
        if not self.redis_pool:
            # For memory blacklist, we'd need token expiration tracking
            # This is simplified for the example
            pass


class RateLimiter:
    """Rate limiting implementation."""

    def __init__(self, redis_pool=None):
        self.redis_pool = redis_pool
        self._memory_counters: dict[str, dict[str, Any]] = {}

    def _get_rate_limit_key(self, identifier: str, window: str) -> str:
        """Generate rate limit key."""
        return f"rate_limit:{identifier}:{window}"

    async def is_rate_limited(
        self, identifier: str, rule: RateLimitRule
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check if request should be rate limited.

        Returns:
            Tuple of (is_limited, rate_limit_info)
        """
        now = datetime.utcnow()
        windows = {
            "minute": (60, rule.requests_per_minute),
            "hour": (3600, rule.requests_per_hour),
            "day": (86400, rule.requests_per_day),
        }

        rate_info = {
            "limit": rule.requests_per_minute,
            "remaining": rule.requests_per_minute,
            "reset": int((now + timedelta(minutes=1)).timestamp()),
            "retry_after": None,
        }

        for window_name, (window_seconds, limit) in windows.items():
            window_start = int(now.timestamp()) // window_seconds * window_seconds
            key = self._get_rate_limit_key(identifier, f"{window_name}:{window_start}")

            if self.redis_pool:
                current_count = await self._redis_rate_limit_check(key, window_seconds)
            else:
                current_count = self._memory_rate_limit_check(
                    key, window_start, window_seconds
                )

            if current_count > limit:
                rate_info["remaining"] = 0
                rate_info["retry_after"] = window_seconds - (
                    int(now.timestamp()) - window_start
                )
                return True, rate_info

            # Update rate info for minute window (most restrictive for display)
            if window_name == "minute":
                rate_info["remaining"] = max(0, limit - current_count)

        return False, rate_info

    async def _redis_rate_limit_check(self, key: str, ttl: int) -> int:
        """Redis-based rate limit checking."""
        try:
            # Increment counter
            count = await self.redis_pool.redis_client.incr(key)

            # Set expiration on first increment
            if count == 1:
                await self.redis_pool.redis_client.expire(key, ttl)

            return count
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return 0  # Fail open

    def _memory_rate_limit_check(
        self, key: str, window_start: int, window_seconds: int
    ) -> int:
        """Memory-based rate limit checking (fallback)."""
        now = time.time()

        # Clean up old entries
        self._memory_counters = {
            k: v for k, v in self._memory_counters.items() if v["expires"] > now
        }

        if key not in self._memory_counters:
            self._memory_counters[key] = {
                "count": 0,
                "expires": window_start + window_seconds,
            }

        self._memory_counters[key]["count"] += 1
        return self._memory_counters[key]["count"]


class EnhancedAuthMiddleware(BaseHTTPMiddleware):
    """
    Enhanced authentication middleware with comprehensive security features.
    """

    def __init__(self, app, config: AuthConfig):
        super().__init__(app)
        self.config = config
        self.security = HTTPBearer(auto_error=False)
        self.redis_pool = None
        self.token_blacklist = None
        self.rate_limiter = None

        # User-specific rate limits
        self.user_rate_limits: dict[str, RateLimitRule] = {}

        # Initialize async components
        self._initialized = False

    async def _initialize(self):
        """Initialize async components."""
        if self._initialized:
            return

        if get_redis_pool:
            try:
                self.redis_pool = await get_redis_pool()
            except Exception as e:
                logger.warning(f"Redis not available for auth middleware: {e}")

        self.token_blacklist = TokenBlacklist(self.redis_pool)
        self.rate_limiter = RateLimiter(self.redis_pool)
        self._initialized = True

    async def dispatch(self, request: Request, call_next):
        """Process request through auth and rate limiting."""
        await self._initialize()

        # Add security headers
        response = Response()
        self._add_security_headers(response)

        try:
            # Check HTTPS requirement
            if self.config.require_https and request.url.scheme != "https":
                if request.url.hostname not in ["localhost", "127.0.0.1"]:
                    raise HTTPException(
                        status_code=status.HTTP_426_UPGRADE_REQUIRED,
                        detail="HTTPS required",
                    )

            # Skip auth for anonymous routes
            if self._is_anonymous_route(request.url.path):
                response = await call_next(request)
                self._add_security_headers(response)
                return response

            # Rate limiting
            if self.config.rate_limit_enabled:
                await self._check_rate_limits(request, response)

            # Authentication
            user = await self._authenticate_request(request)

            # Add user to request state
            request.state.user = user
            request.state.user_id = user.get("user_id")
            request.state.authenticated = True

            # Process request
            response = await call_next(request)
            self._add_security_headers(response)

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def _is_anonymous_route(self, path: str) -> bool:
        """Check if route allows anonymous access."""
        # Exact match
        if path in self.config.allow_anonymous_routes:
            return True

        # Pattern matching for common routes
        anonymous_patterns = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/",
            "/static/",
            "/favicon.ico",
        ]

        return any(path.startswith(pattern) for pattern in anonymous_patterns)

    async def _check_rate_limits(self, request: Request, response: Response):
        """Check and enforce rate limits."""
        # Get identifier (user ID if authenticated, IP otherwise)
        identifier = self._get_rate_limit_identifier(request)

        # Get rate limit rule for user/IP
        rule = self._get_rate_limit_rule(request, identifier)

        # Check rate limit
        is_limited, rate_info = await self.rate_limiter.is_rate_limited(
            identifier, rule
        )

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

        if is_limited:
            if rate_info["retry_after"]:
                response.headers["Retry-After"] = str(rate_info["retry_after"])

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": rate_info["limit"],
                    "retry_after": rate_info["retry_after"],
                },
            )

    def _get_rate_limit_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting."""
        # Try to get user ID from existing auth
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        return request.client.host if request.client else "unknown"

    def _get_rate_limit_rule(self, request: Request, identifier: str) -> RateLimitRule:
        """Get rate limit rule for identifier."""
        # Check for user-specific rate limits
        if identifier.startswith("user:"):
            user_id = identifier[5:]  # Remove "user:" prefix
            if user_id in self.user_rate_limits:
                return self.user_rate_limits[user_id]

        # Check for premium/admin users (higher limits)
        if hasattr(request.state, "user") and request.state.user:
            user_role = request.state.user.get("role", "user")

            if user_role == "admin":
                return RateLimitRule(
                    requests_per_minute=300,
                    requests_per_hour=5000,
                    requests_per_day=50000,
                    burst_limit=50,
                )
            elif user_role == "premium":
                return RateLimitRule(
                    requests_per_minute=120,
                    requests_per_hour=2000,
                    requests_per_day=20000,
                    burst_limit=20,
                )

        return self.config.default_rate_limit

    async def _authenticate_request(self, request: Request) -> dict[str, Any]:
        """Authenticate request and return user info."""
        # Get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract token
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization[7:]  # Remove "Bearer " prefix

        # Validate token
        try:
            payload = jwt.decode(
                token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check token blacklist
        jti = payload.get("jti")
        if jti and await self.token_blacklist.is_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate required claims
        required_claims = ["user_id", "exp", "iat"]
        for claim in required_claims:
            if claim not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Missing required claim: {claim}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return payload

    def _add_security_headers(self, response: Response):
        """Add security headers to response."""
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Content-Security-Policy": "default-src 'self'",
                "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            }
        )

    async def revoke_token(self, token: str):
        """Revoke a token by adding it to blacklist."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                options={
                    "verify_exp": False
                },  # Don't verify expiration for blacklisting
            )

            jti = payload.get("jti")
            exp = datetime.fromtimestamp(payload.get("exp", 0))

            if jti:
                await self.token_blacklist.add_token(jti, exp)
                logger.info(f"Token {jti} added to blacklist")

        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")

    def set_user_rate_limit(self, user_id: str, rule: RateLimitRule):
        """Set custom rate limit for specific user."""
        self.user_rate_limits[user_id] = rule
        logger.info(f"Custom rate limit set for user {user_id}")

    async def get_rate_limit_status(self, identifier: str) -> dict[str, Any]:
        """Get current rate limit status for identifier."""
        rule = self.config.default_rate_limit
        is_limited, rate_info = await self.rate_limiter.is_rate_limited(
            identifier, rule
        )

        return {
            "identifier": identifier,
            "is_limited": is_limited,
            "rate_info": rate_info,
            "rule": {
                "requests_per_minute": rule.requests_per_minute,
                "requests_per_hour": rule.requests_per_hour,
                "requests_per_day": rule.requests_per_day,
                "burst_limit": rule.burst_limit,
            },
        }


def require_auth(roles: list[str] | None = None):
    """
    Decorator to require authentication and optionally specific roles.

    Args:
        roles: List of required roles (optional)
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not getattr(request.state, "authenticated", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if roles:
                user_role = request.state.user.get("role", "user")
                if user_role not in roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions",
                    )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_scope(scopes: list[str]):
    """
    Decorator to require specific OAuth scopes.

    Args:
        scopes: List of required scopes
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not getattr(request.state, "authenticated", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_scopes = request.state.user.get("scopes", [])
            if not all(scope in user_scopes for scope in scopes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scopes"
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
