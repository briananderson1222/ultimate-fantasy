"""
WebSocket authentication middleware.

Provides secure WebSocket connection management with:
- Token-based authentication
- Connection rate limiting
- Message authorization
- Session management
- Real-time security monitoring
"""

import asyncio
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import jwt
from fastapi import WebSocket, status
from starlette.websockets import WebSocketState

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


class ConnectionState(Enum):
    """WebSocket connection states."""

    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    CLOSING = "closing"
    CLOSED = "closed"


class MessageType(Enum):
    """WebSocket message types."""

    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_ERROR = "auth_error"
    PING = "ping"
    PONG = "pong"
    DATA = "data"
    ERROR = "error"
    RATE_LIMIT = "rate_limit"
    DISCONNECT = "disconnect"


@dataclass
class ConnectionInfo:
    """WebSocket connection information."""

    websocket: WebSocket
    user_id: str | None = None
    connection_id: str = ""
    state: ConnectionState = ConnectionState.CONNECTING
    authenticated_at: datetime | None = None
    last_activity: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    rate_limit_reset: datetime = field(default_factory=datetime.utcnow)
    subscriptions: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSocketConfig:
    """WebSocket authentication configuration."""

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    auth_timeout_seconds: int = 30
    ping_interval_seconds: int = 30
    max_connections_per_user: int = 5
    max_message_rate_per_minute: int = 60
    max_message_size: int = 1024 * 1024  # 1MB
    allowed_origins: list[str] = field(default_factory=list)
    require_auth: bool = True


class WebSocketRateLimiter:
    """Rate limiter for WebSocket messages."""

    def __init__(self, redis_pool=None):
        self.redis_pool = redis_pool
        self._memory_counters: dict[str, dict[str, Any]] = {}

    async def check_rate_limit(
        self, connection_id: str, rate_limit: int, window_seconds: int = 60
    ) -> bool:
        """
        Check if connection is rate limited.

        Args:
            connection_id: Connection identifier
            rate_limit: Messages per window
            window_seconds: Time window in seconds

        Returns:
            True if rate limited
        """
        now = time.time()
        window_start = int(now) // window_seconds * window_seconds
        key = f"ws_rate:{connection_id}:{window_start}"

        if self.redis_pool:
            return await self._redis_rate_check(key, rate_limit, window_seconds)
        else:
            return self._memory_rate_check(key, rate_limit, now, window_seconds)

    async def _redis_rate_check(self, key: str, limit: int, ttl: int) -> bool:
        """Redis-based rate limiting."""
        try:
            count = await self.redis_pool.redis_client.incr(key)
            if count == 1:
                await self.redis_pool.redis_client.expire(key, ttl)
            return count > limit
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return False  # Fail open

    def _memory_rate_check(
        self, key: str, limit: int, now: float, window_seconds: int
    ) -> bool:
        """Memory-based rate limiting."""
        # Clean up old entries
        cutoff = now - window_seconds
        self._memory_counters = {
            k: v for k, v in self._memory_counters.items() if v["window_start"] > cutoff
        }

        if key not in self._memory_counters:
            self._memory_counters[key] = {"count": 0, "window_start": now}

        self._memory_counters[key]["count"] += 1
        return self._memory_counters[key]["count"] > limit


class WebSocketAuthMiddleware:
    """
    WebSocket authentication and authorization middleware.

    Manages secure WebSocket connections with authentication,
    rate limiting, and real-time session management.
    """

    def __init__(self, config: WebSocketConfig):
        self.config = config
        self.connections: dict[str, ConnectionInfo] = {}
        self.user_connections: dict[str, set[str]] = {}
        self.rate_limiter = WebSocketRateLimiter()
        self.redis_pool = None
        self._initialized = False

        # Message handlers
        self.message_handlers: dict[MessageType, Callable] = {
            MessageType.AUTH: self._handle_auth_message,
            MessageType.PING: self._handle_ping_message,
            MessageType.DATA: self._handle_data_message,
        }

    async def _initialize(self):
        """Initialize async components."""
        if self._initialized:
            return

        if get_redis_pool:
            try:
                self.redis_pool = await get_redis_pool()
                self.rate_limiter = WebSocketRateLimiter(self.redis_pool)
            except Exception as e:
                logger.warning(f"Redis not available for WebSocket middleware: {e}")

        self._initialized = True

    async def connect(self, websocket: WebSocket, connection_id: str) -> ConnectionInfo:
        """
        Handle new WebSocket connection.

        Args:
            websocket: WebSocket instance
            connection_id: Unique connection identifier

        Returns:
            ConnectionInfo instance

        Raises:
            Exception: If connection is rejected
        """
        await self._initialize()

        # Check origin if configured
        if self.config.allowed_origins:
            origin = websocket.headers.get("origin")
            if origin not in self.config.allowed_origins:
                logger.warning(
                    f"WebSocket connection rejected: invalid origin {origin}"
                )
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise Exception("Invalid origin")

        # Accept WebSocket connection
        await websocket.accept()

        # Create connection info
        connection = ConnectionInfo(
            websocket=websocket,
            connection_id=connection_id,
            state=ConnectionState.CONNECTING,
        )

        self.connections[connection_id] = connection
        logger.info(f"WebSocket connection {connection_id} established")

        # Start authentication if required
        if self.config.require_auth:
            connection.state = ConnectionState.AUTHENTICATING
            await self._send_auth_required(connection)

            # Set authentication timeout
            asyncio.create_task(self._auth_timeout_handler(connection_id))
        else:
            connection.state = ConnectionState.AUTHENTICATED
            await self._send_auth_success(connection, None)

        return connection

    async def disconnect(self, connection_id: str):
        """
        Handle WebSocket disconnection.

        Args:
            connection_id: Connection identifier
        """
        if connection_id not in self.connections:
            return

        connection = self.connections[connection_id]
        connection.state = ConnectionState.CLOSING

        # Remove from user connections
        if connection.user_id:
            user_connections = self.user_connections.get(connection.user_id, set())
            user_connections.discard(connection_id)
            if not user_connections:
                del self.user_connections[connection.user_id]

        # Clean up connection
        del self.connections[connection_id]
        connection.state = ConnectionState.CLOSED

        logger.info(f"WebSocket connection {connection_id} disconnected")

    async def handle_message(self, connection_id: str, message: str) -> bool:
        """
        Handle incoming WebSocket message.

        Args:
            connection_id: Connection identifier
            message: Raw message string

        Returns:
            True if message was handled successfully
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]

        try:
            # Check message size
            if len(message) > self.config.max_message_size:
                await self._send_error(connection, "Message too large")
                return False

            # Check rate limiting
            if await self.rate_limiter.check_rate_limit(
                connection_id, self.config.max_message_rate_per_minute
            ):
                await self._send_rate_limit_error(connection)
                return False

            # Update activity
            connection.last_activity = datetime.utcnow()
            connection.message_count += 1

            # Parse message
            try:
                message_data = json.loads(message)
            except json.JSONDecodeError:
                await self._send_error(connection, "Invalid JSON")
                return False

            # Validate message structure
            if not isinstance(message_data, dict) or "type" not in message_data:
                await self._send_error(connection, "Invalid message format")
                return False

            # Get message type
            try:
                message_type = MessageType(message_data["type"])
            except ValueError:
                await self._send_error(
                    connection, f"Unknown message type: {message_data['type']}"
                )
                return False

            # Handle message based on type
            handler = self.message_handlers.get(message_type)
            if handler:
                return await handler(connection, message_data)
            else:
                await self._send_error(
                    connection, f"Unhandled message type: {message_type.value}"
                )
                return False

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self._send_error(connection, "Internal server error")
            return False

    async def _handle_auth_message(
        self, connection: ConnectionInfo, message_data: dict[str, Any]
    ) -> bool:
        """Handle authentication message."""
        if connection.state != ConnectionState.AUTHENTICATING:
            await self._send_error(connection, "Authentication not required")
            return False

        token = message_data.get("token")
        if not token:
            await self._send_error(connection, "Missing authentication token")
            return False

        try:
            # Validate JWT token
            payload = jwt.decode(
                token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm]
            )

            user_id = payload.get("user_id")
            if not user_id:
                await self._send_error(connection, "Invalid token: missing user_id")
                return False

            # Check connection limits per user
            if await self._check_user_connection_limit(user_id):
                await self._send_error(connection, "Too many connections for user")
                return False

            # Update connection info
            connection.user_id = user_id
            connection.state = ConnectionState.AUTHENTICATED
            connection.authenticated_at = datetime.utcnow()
            connection.metadata.update(payload)

            # Add to user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection.connection_id)

            await self._send_auth_success(connection, user_id)
            logger.info(
                f"WebSocket connection {connection.connection_id} authenticated for user {user_id}"
            )

            return True

        except jwt.ExpiredSignatureError:
            await self._send_error(connection, "Token has expired")
            return False
        except jwt.InvalidTokenError:
            await self._send_error(connection, "Invalid token")
            return False

    async def _handle_ping_message(
        self, connection: ConnectionInfo, message_data: dict[str, Any]
    ) -> bool:
        """Handle ping message."""
        await self._send_message(
            connection,
            {
                "type": MessageType.PONG.value,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        return True

    async def _handle_data_message(
        self, connection: ConnectionInfo, message_data: dict[str, Any]
    ) -> bool:
        """Handle data message (application-specific)."""
        if connection.state != ConnectionState.AUTHENTICATED:
            await self._send_error(connection, "Authentication required")
            return False

        # This would be handled by application-specific logic
        # For now, just acknowledge receipt
        await self._send_message(
            connection,
            {
                "type": "ack",
                "message_id": message_data.get("id"),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return True

    async def _check_user_connection_limit(self, user_id: str) -> bool:
        """Check if user has exceeded connection limit."""
        current_connections = len(self.user_connections.get(user_id, set()))
        return current_connections >= self.config.max_connections_per_user

    async def _send_auth_required(self, connection: ConnectionInfo):
        """Send authentication required message."""
        await self._send_message(
            connection,
            {
                "type": MessageType.AUTH.value,
                "message": "Authentication required",
                "timeout": self.config.auth_timeout_seconds,
            },
        )

    async def _send_auth_success(self, connection: ConnectionInfo, user_id: str | None):
        """Send authentication success message."""
        await self._send_message(
            connection,
            {
                "type": MessageType.AUTH_SUCCESS.value,
                "user_id": user_id,
                "connection_id": connection.connection_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def _send_error(self, connection: ConnectionInfo, error_message: str):
        """Send error message."""
        await self._send_message(
            connection,
            {
                "type": MessageType.ERROR.value,
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def _send_rate_limit_error(self, connection: ConnectionInfo):
        """Send rate limit error message."""
        await self._send_message(
            connection,
            {
                "type": MessageType.RATE_LIMIT.value,
                "error": "Rate limit exceeded",
                "retry_after": 60,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def _send_message(self, connection: ConnectionInfo, message: dict[str, Any]):
        """Send message to WebSocket connection."""
        if connection.websocket.client_state != WebSocketState.CONNECTED:
            return

        try:
            await connection.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")

    async def _auth_timeout_handler(self, connection_id: str):
        """Handle authentication timeout."""
        await asyncio.sleep(self.config.auth_timeout_seconds)

        if connection_id in self.connections:
            connection = self.connections[connection_id]
            if connection.state == ConnectionState.AUTHENTICATING:
                await self._send_error(connection, "Authentication timeout")
                await connection.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                await self.disconnect(connection_id)

    async def broadcast_to_user(self, user_id: str, message: dict[str, Any]):
        """
        Broadcast message to all connections for a user.

        Args:
            user_id: User identifier
            message: Message to broadcast
        """
        user_connections = self.user_connections.get(user_id, set())

        for connection_id in user_connections.copy():
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                await self._send_message(connection, message)

    async def broadcast_to_subscription(
        self, subscription: str, message: dict[str, Any]
    ):
        """
        Broadcast message to all connections subscribed to a topic.

        Args:
            subscription: Subscription topic
            message: Message to broadcast
        """
        for connection in self.connections.values():
            if subscription in connection.subscriptions:
                await self._send_message(connection, message)

    async def subscribe(self, connection_id: str, subscription: str) -> bool:
        """
        Subscribe connection to a topic.

        Args:
            connection_id: Connection identifier
            subscription: Subscription topic

        Returns:
            True if subscription successful
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        if connection.state != ConnectionState.AUTHENTICATED:
            return False

        connection.subscriptions.add(subscription)
        logger.info(f"Connection {connection_id} subscribed to {subscription}")
        return True

    async def unsubscribe(self, connection_id: str, subscription: str) -> bool:
        """
        Unsubscribe connection from a topic.

        Args:
            connection_id: Connection identifier
            subscription: Subscription topic

        Returns:
            True if unsubscription successful
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        connection.subscriptions.discard(subscription)
        logger.info(f"Connection {connection_id} unsubscribed from {subscription}")
        return True

    def get_connection_stats(self) -> dict[str, Any]:
        """Get WebSocket connection statistics."""
        authenticated_count = sum(
            1
            for conn in self.connections.values()
            if conn.state == ConnectionState.AUTHENTICATED
        )

        return {
            "total_connections": len(self.connections),
            "authenticated_connections": authenticated_count,
            "unique_users": len(self.user_connections),
            "connections_by_state": {
                state.value: sum(
                    1 for conn in self.connections.values() if conn.state == state
                )
                for state in ConnectionState
            },
        }

    async def cleanup_inactive_connections(self, max_idle_minutes: int = 30):
        """Clean up inactive connections."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_idle_minutes)
        inactive_connections = []

        for connection_id, connection in self.connections.items():
            if connection.last_activity < cutoff_time:
                inactive_connections.append(connection_id)

        for connection_id in inactive_connections:
            connection = self.connections[connection_id]
            await self._send_message(
                connection,
                {
                    "type": MessageType.DISCONNECT.value,
                    "reason": "Inactive connection cleanup",
                },
            )
            await connection.websocket.close(code=status.WS_1001_GOING_AWAY)
            await self.disconnect(connection_id)

        if inactive_connections:
            logger.info(
                f"Cleaned up {len(inactive_connections)} inactive WebSocket connections"
            )


# Global middleware instance
_ws_auth_middleware: WebSocketAuthMiddleware | None = None


def get_websocket_auth_middleware(
    config: WebSocketConfig | None = None,
) -> WebSocketAuthMiddleware:
    """Get global WebSocket auth middleware instance."""
    global _ws_auth_middleware

    if _ws_auth_middleware is None:
        if config is None:
            raise ValueError("WebSocket config required for first initialization")
        _ws_auth_middleware = WebSocketAuthMiddleware(config)

    return _ws_auth_middleware


def reset_websocket_auth_middleware():
    """Reset global middleware instance (useful for testing)."""
    global _ws_auth_middleware
    _ws_auth_middleware = None
