"""
Authentication middleware for Ultimate Fantasy Platform
Provides JWT token validation, role-based access control, rate limiting, and security headers
"""

import logging
import os
import time
import uuid as _uuid
from collections import defaultdict
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any

import jwt
import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from domains.users.services.user_service import UserService
from infrastructure.config import settings
from infrastructure.database.session_factory import (
    get_db_session as get_async_db_session,
)
from infrastructure.database.session_factory import (
    get_session_factory,
)


class AuthenticationError(Exception):
    """Raised when authentication fails or credentials are invalid."""


class AuthorizationError(Exception):
    """Raised when a user is not permitted to perform an action."""


class RateLimitExceededError(Exception):
    """Raised when client exceeds configured rate limits."""


class TokenExpiredError(Exception):
    """Raised when JWT token has expired."""


class InvalidTokenError(Exception):
    """Raised for malformed or unrecognized JWT tokens."""


logger = logging.getLogger(__name__)


# Security scheme for FastAPI
security = HTTPBearer(auto_error=False)


@contextmanager
def sync_db_session():
    """Provide a synchronous database session scope."""

    factory = get_session_factory()
    session = factory.get_sync_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class TokenManager:
    """Manages JWT tokens and validation"""

    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_hours = settings.JWT_EXPIRATION_HOURS

        # Token blacklist (Redis-backed)
        self.redis_client: redis.Redis | None = None
        self.blacklist_prefix = "token_blacklist:"

    async def set_redis_client(self, redis_client: redis.Redis):
        """Set Redis client for token blacklist"""
        self.redis_client = redis_client

    def create_access_token(
        self,
        user_id: str,
        username: str,
        email: str,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a JWT access token

        Args:
            user_id: User ID
            username: Username
            email: User email
            roles: List of user roles
            permissions: List of user permissions
            expires_delta: Optional custom expiration time

        Returns:
            JWT token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)

        payload = {
            "sub": user_id,
            "username": username,
            "email": email,
            "roles": roles or [],
            "permissions": permissions or [],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Created access token for user {username}")
        return token

    def create_refresh_token(self, user_id: str, username: str) -> str:
        """
        Create a JWT refresh token

        Args:
            user_id: User ID
            username: Username

        Returns:
            JWT refresh token string
        """
        expire = datetime.utcnow() + timedelta(days=30)  # Refresh tokens last 30 days

        payload = {
            "sub": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Created refresh token for user {username}")
        return token

    async def validate_token(self, token: str) -> dict[str, Any]:
        """
        Validate a JWT token

        Args:
            token: JWT token string

        Returns:
            Token payload

        Raises:
            InvalidTokenError: If token is invalid
            TokenExpiredError: If token has expired
            AuthenticationError: If token is blacklisted
        """
        try:
            # Check if token is blacklisted
            if await self.is_token_blacklisted(token):
                raise AuthenticationError("Token has been revoked")

            # Decode and validate token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True},
            )

            # Validate token type
            if payload.get("type") not in ["access", "refresh"]:
                raise InvalidTokenError("Invalid token type")

            return payload

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {e!s}")
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise AuthenticationError("Token validation failed")

    async def blacklist_token(self, token: str, expiry_time: int | None = None):
        """
        Add token to blacklist

        Args:
            token: JWT token to blacklist
            expiry_time: Optional expiry time in seconds
        """
        if not self.redis_client:
            logger.warning("Redis client not available for token blacklisting")
            return

        try:
            # Extract token expiry for automatic cleanup
            if not expiry_time:
                payload = jwt.decode(
                    token,
                    self.secret_key,
                    algorithms=[self.algorithm],
                    options={"verify_exp": False},
                )
                exp_timestamp = payload.get("exp")
                if exp_timestamp:
                    expiry_time = max(0, int(exp_timestamp - time.time()))

            # Add to blacklist with expiry
            blacklist_key = f"{self.blacklist_prefix}{token}"
            await self.redis_client.set(
                blacklist_key,
                "blacklisted",
                ex=expiry_time or 86400,  # Default 24 hours
            )

            logger.debug("Token added to blacklist")

        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")

    async def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted

        Args:
            token: JWT token to check

        Returns:
            True if blacklisted, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            blacklist_key = f"{self.blacklist_prefix}{token}"
            result = await self.redis_client.get(blacklist_key)
            return result is not None

        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False


class RateLimiter:
    """Rate limiting functionality"""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis_client = redis_client
        self.rate_limit_prefix = "rate_limit:"

        # Default rate limits per endpoint type
        self.default_limits = {
            "auth": {"requests": 10, "window": 60},  # 10 requests per minute for auth
            "api": {"requests": 100, "window": 60},  # 100 requests per minute for API
            "upload": {"requests": 5, "window": 60},  # 5 uploads per minute
            "websocket": {
                "requests": 20,
                "window": 60,
            },  # 20 WebSocket connections per minute
        }

        # In-memory fallback when Redis unavailable
        self.memory_cache: dict[str, dict[str, Any]] = defaultdict(dict)

    async def check_rate_limit(
        self,
        identifier: str,
        limit_type: str = "api",
        custom_limit: int | None = None,
        custom_window: int | None = None,
    ) -> dict[str, Any]:
        """
        Check if request is within rate limits

        Args:
            identifier: Unique identifier (e.g., user ID, IP address)
            limit_type: Type of rate limit to apply
            custom_limit: Optional custom request limit
            custom_window: Optional custom time window

        Returns:
            Dictionary with rate limit status and metadata

        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        # Get rate limit configuration
        config = self.default_limits.get(limit_type, self.default_limits["api"])
        max_requests = custom_limit or config["requests"]
        window_seconds = custom_window or config["window"]

        current_time = int(time.time())

        try:
            if self.redis_client:
                # Redis-based rate limiting (preferred)
                result = await self._check_redis_rate_limit(
                    identifier, limit_type, max_requests, window_seconds, current_time
                )
            else:
                # Memory-based fallback
                result = self._check_memory_rate_limit(
                    identifier, limit_type, max_requests, window_seconds, current_time
                )

            # Check if limit exceeded
            if result["requests_made"] > max_requests:
                raise RateLimitExceededError(
                    f"Rate limit exceeded: {result['requests_made']}/{max_requests} "
                    f"requests in {window_seconds} seconds"
                )

            return result

        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request on error to avoid blocking legitimate users
            return {
                "allowed": True,
                "requests_made": 0,
                "requests_remaining": max_requests,
                "reset_time": current_time + window_seconds,
                "error": str(e),
            }

    async def _check_redis_rate_limit(
        self,
        identifier: str,
        limit_type: str,
        max_requests: int,
        window_seconds: int,
        current_time: int,
    ) -> dict[str, Any]:
        """Redis-based rate limiting using sliding window"""
        key = f"{self.rate_limit_prefix}{limit_type}:{identifier}"
        window_start = current_time - window_seconds

        # Use Redis pipeline for atomic operations
        if self.redis_client is None:
            raise RuntimeError("Redis client not available for rate limiting")
        pipe = self.redis_client.pipeline()

        # Remove old entries and add current request
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.zcount(key, window_start, current_time)
        pipe.expire(key, window_seconds + 1)

        results = await pipe.execute()
        requests_made = results[2]  # Result from zcount

        return {
            "allowed": requests_made <= max_requests,
            "requests_made": requests_made,
            "requests_remaining": max(0, max_requests - requests_made),
            "reset_time": current_time + window_seconds,
            "window_seconds": window_seconds,
        }

    def _check_memory_rate_limit(
        self,
        identifier: str,
        limit_type: str,
        max_requests: int,
        window_seconds: int,
        current_time: int,
    ) -> dict[str, Any]:
        """Memory-based rate limiting fallback"""
        key = f"{limit_type}:{identifier}"
        window_start = current_time - window_seconds

        # Get or create request history
        if key not in self.memory_cache:
            self.memory_cache[key] = {"requests": [], "last_cleanup": current_time}

        request_history = self.memory_cache[key]["requests"]

        # Clean up old requests
        self.memory_cache[key]["requests"] = [
            req_time for req_time in request_history if req_time > window_start
        ]

        # Add current request
        self.memory_cache[key]["requests"].append(current_time)
        requests_made = len(self.memory_cache[key]["requests"])

        # Cleanup memory cache periodically
        if (
            current_time - self.memory_cache[key]["last_cleanup"] > 300
        ):  # Every 5 minutes
            self._cleanup_memory_cache(current_time)
            self.memory_cache[key]["last_cleanup"] = current_time

        return {
            "allowed": requests_made <= max_requests,
            "requests_made": requests_made,
            "requests_remaining": max(0, max_requests - requests_made),
            "reset_time": current_time + window_seconds,
            "window_seconds": window_seconds,
        }

    def _cleanup_memory_cache(self, current_time: int):
        """Clean up old entries from memory cache"""
        cutoff_time = current_time - 3600  # Remove entries older than 1 hour

        keys_to_remove = []
        for key, data in self.memory_cache.items():
            # Remove old requests
            data["requests"] = [
                req_time for req_time in data["requests"] if req_time > cutoff_time
            ]

            # Remove empty entries
            if not data["requests"] and current_time - data["last_cleanup"] > 600:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.memory_cache[key]


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Enhanced authentication context middleware with rate limiting and security"""

    def __init__(self, app, redis_client: redis.Redis | None = None):
        super().__init__(app)
        self.token_manager = TokenManager()
        self.rate_limiter = RateLimiter(redis_client)

        # Protected endpoints configuration
        self.protected_endpoints = {
            "/api/v1/auth/logout",
            "/api/v1/auth/refresh",
            "/api/v1/auth/profile",
            "/api/v1/leagues",
            "/api/v1/draft",
            "/api/v1/trades",
            "/api/v1/lineups",
            "/api/v1/waivers",
        }

        # Rate limit configuration per endpoint
        self.endpoint_rate_limits = {
            "/api/v1/auth/login": {"type": "auth", "requests": 10, "window": 60},
            "/api/v1/auth/register": {"type": "auth", "requests": 5, "window": 60},
            "/api/v1/draft/*/pick": {"type": "api", "requests": 30, "window": 60},
            "/api/v1/sports/players": {"type": "api", "requests": 200, "window": 60},
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enhanced middleware dispatch with authentication and rate limiting"""
        try:
            # Apply rate limiting first
            await self._apply_rate_limiting(request)

            # Legacy authentication support (preserve existing functionality)
            await self._apply_legacy_auth(request)

            # Enhanced authentication for protected endpoints
            await self._apply_enhanced_auth(request)

            # Process request
            response = await call_next(request)

            # Add security headers
            self._add_security_headers(response)

            return response

        except (RateLimitExceededError, AuthenticationError) as e:
            return self._create_error_response(e)
        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"},
            )

    async def _apply_rate_limiting(self, request: Request):
        """Apply rate limiting based on endpoint"""
        path = request.url.path

        # Skip rate limiting for health checks
        if path in ["/health", "/api/health"]:
            return

        # Get client identifier
        client_id = self._get_client_identifier(request)

        # Get rate limit config
        rate_config = self._get_endpoint_rate_config(path)

        # Check rate limit
        await self.rate_limiter.check_rate_limit(
            identifier=client_id,
            limit_type=rate_config["type"],
            custom_limit=rate_config.get("requests"),
            custom_window=rate_config.get("window"),
        )

    async def _apply_legacy_auth(self, request: Request):
        """Apply legacy authentication (preserve existing functionality)"""
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
                        with sync_db_session() as sess:
                            user_service = UserService(sess)
                            user = user_service.ensure_user_from_claims(
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

    async def _apply_enhanced_auth(self, request: Request):
        """Apply enhanced authentication for protected endpoints"""
        path = request.url.path

        # Check if endpoint requires authentication
        if not self._requires_authentication(path):
            return

        # If already authenticated via legacy method, skip
        if hasattr(request.state, "user_id") and request.state.user_id:
            return

        # Extract token and validate with enhanced token manager
        token = self._extract_token(request)
        if not token:
            raise AuthenticationError("Authentication required")

        # Validate token with enhanced manager
        token_payload = await self.token_manager.validate_token(token)

        # Store enhanced user info
        request.state.enhanced_auth = True
        request.state.token_payload = token_payload

    def _requires_authentication(self, path: str) -> bool:
        """Check if endpoint requires authentication"""
        public_endpoints = {
            "/health",
            "/api/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/docs",
            "/openapi.json",
        }

        if path in public_endpoints:
            return False

        return any(path.startswith(endpoint) for endpoint in self.protected_endpoints)

    def _extract_token(self, request: Request) -> str | None:
        """Extract JWT token from request"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]

        token = request.query_params.get("token")
        if token:
            return token

        return None

    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Use user ID if authenticated
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"

        # Use IP address as fallback
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _get_endpoint_rate_config(self, path: str) -> dict[str, Any]:
        """Get rate limit configuration for endpoint"""
        # Check exact matches first
        if path in self.endpoint_rate_limits:
            return self.endpoint_rate_limits[path]

        # Check pattern matches
        for pattern, config in self.endpoint_rate_limits.items():
            if "*" in pattern:
                pattern_parts = pattern.split("*")
                if all(part in path for part in pattern_parts if part):
                    return config

        # Default configuration
        return {"type": "api", "requests": 100, "window": 60}

    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    def _create_error_response(self, error: Exception) -> JSONResponse:
        """Create error response for authentication/authorization failures"""
        if isinstance(error, RateLimitExceededError):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "rate_limit_exceeded", "message": str(error)},
                headers={"Retry-After": "60"},
            )
        elif isinstance(error, AuthenticationError):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "authentication_failed", "message": str(error)},
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_error",
                    "message": "An unexpected error occurred",
                },
            )


# Global instances
token_manager = TokenManager()


# Dependency functions for FastAPI
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_async_db_session),
) -> dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user

    Returns:
        User information dictionary

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Validate token
        token_payload = await token_manager.validate_token(credentials.credentials)

        # Get user from database
        user_service = UserService()
        user = user_service.get_user_sync(token_payload["sub"], db)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User account inactive"
            )

        return {
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "roles": token_payload.get("roles", []),
            "permissions": token_payload.get("permissions", []),
            "is_admin": user.is_admin,
            "token_payload": token_payload,
        }

    except (AuthenticationError, TokenExpiredError, InvalidTokenError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_async_db_session),
) -> dict[str, Any] | None:
    """
    FastAPI dependency to optionally get current authenticated user

    Returns:
        User information dictionary or None if not authenticated
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def require_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    FastAPI dependency that requires admin access

    Returns:
        User information dictionary

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return current_user
