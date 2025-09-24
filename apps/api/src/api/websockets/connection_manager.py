"""
WebSocket Connection Manager for Ultimate Fantasy Platform
Manages real-time connections for draft updates, live scoring, and chat functionality
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect

from domains.leagues.services.league_service import LeagueService
from domains.shared.exceptions import (
    AuthenticationError,
    LeagueNotFoundError,
)
from domains.users.services.user_service import UserService
from infrastructure.database.session_factory import get_db_session

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Types of WebSocket connections"""

    DRAFT = "draft"
    SCORES = "scores"
    TRADES = "trades"
    WAIVERS = "waivers"
    CHAT = "chat"
    GENERAL = "general"


class MessageType(Enum):
    """Types of real-time messages"""

    # Draft messages
    DRAFT_STARTED = "draft_started"
    DRAFT_PICK = "draft_pick"
    DRAFT_TIMER = "draft_timer"
    DRAFT_COMPLETED = "draft_completed"

    # Score messages
    SCORE_UPDATE = "score_update"
    LINEUP_LOCKED = "lineup_locked"
    GAME_STARTED = "game_started"
    GAME_FINAL = "game_final"

    # Trade messages
    TRADE_PROPOSED = "trade_proposed"
    TRADE_ACCEPTED = "trade_accepted"
    TRADE_REJECTED = "trade_rejected"
    TRADE_EXPIRED = "trade_expired"

    # Waiver messages
    WAIVER_PROCESSED = "waiver_processed"
    WAIVER_WON = "waiver_won"
    WAIVER_LOST = "waiver_lost"

    # Chat messages
    CHAT_MESSAGE = "chat_message"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"

    # System messages
    NOTIFICATION = "notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


@dataclass
class Connection:
    """Represents a WebSocket connection"""

    connection_id: str
    websocket: WebSocket
    user_id: str
    username: str
    league_id: str | None
    connection_types: set[ConnectionType]
    connected_at: datetime
    last_ping: datetime
    metadata: dict[str, Any]


@dataclass
class Message:
    """Real-time message structure"""

    type: MessageType
    data: dict[str, Any]
    league_id: str | None = None
    user_id: str | None = None
    target_users: list[str] | None = None
    timestamp: datetime | None = None
    correlation_id: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""

    def __init__(self, redis_client: redis.Redis | None = None):
        """Initialize connection manager with optional Redis client"""
        self.active_connections: dict[str, Connection] = {}
        self.league_connections: dict[str, set[str]] = defaultdict(set)
        self.user_connections: dict[str, set[str]] = defaultdict(set)
        self.type_connections: dict[ConnectionType, set[str]] = defaultdict(set)

        # Redis for cross-instance communication
        self.redis_client = redis_client
        self.redis_channel = "fantasy_realtime"

        # Services - initialize with session when needed

        # Heartbeat and cleanup
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 300  # 5 minutes
        self._cleanup_task: asyncio.Task | None = None
        self._heartbeat_task: asyncio.Task | None = None

    async def start(self):
        """Start the connection manager and background tasks"""
        logger.info("Starting WebSocket connection manager")

        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_stale_connections())
        self._heartbeat_task = asyncio.create_task(self._send_heartbeats())

        # Subscribe to Redis if available
        if self.redis_client:
            asyncio.create_task(self._redis_subscriber())

    async def stop(self):
        """Stop the connection manager and clean up"""
        logger.info("Stopping WebSocket connection manager")

        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        # Close all connections
        await self._close_all_connections()

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        league_id: str | None = None,
        connection_types: list[str] | None = None,
    ) -> str:
        """
        Establish a new WebSocket connection

        Args:
            websocket: FastAPI WebSocket instance
            user_id: Authenticated user ID
            league_id: Optional league to join
            connection_types: Types of updates to receive

        Returns:
            Connection ID

        Raises:
            AuthenticationError: If user authentication fails
            LeagueNotFoundError: If league doesn't exist or user not member
        """
        try:
            await websocket.accept()

            # Validate user and league
            with get_db_session() as db:
                user_service = UserService(db)
                user = user_service.get_user_sync(user_id)
                if not user or not user.is_active:
                    await websocket.close(
                        code=1008, reason="User not found or inactive"
                    )
                    raise AuthenticationError("Invalid user")

                if league_id:
                    league_service = LeagueService(db)
                    if not league_service.is_user_in_league(league_id, user_id):
                        await websocket.close(code=1008, reason="Not a league member")
                        raise LeagueNotFoundError("User not in league")

            # Create connection
            connection_id = str(uuid.uuid4())
            types = {ConnectionType(t) for t in (connection_types or ["general"])}

            connection = Connection(
                connection_id=connection_id,
                websocket=websocket,
                user_id=user_id,
                username=user.username,
                league_id=league_id,
                connection_types=types,
                connected_at=datetime.utcnow(),
                last_ping=datetime.utcnow(),
                metadata={},
            )

            # Store connection
            self.active_connections[connection_id] = connection
            self.user_connections[user_id].add(connection_id)

            if league_id:
                self.league_connections[league_id].add(connection_id)

            for conn_type in types:
                self.type_connections[conn_type].add(connection_id)

            logger.info(
                f"WebSocket connected: {connection_id} (user: {user.username}, league: {league_id})"
            )

            # Notify league members of user joining
            if league_id:
                await self.broadcast_to_league(
                    league_id,
                    Message(
                        type=MessageType.USER_JOINED,
                        data={
                            "user_id": user_id,
                            "username": user.username,
                            "connection_types": [t.value for t in types],
                        },
                        league_id=league_id,
                    ),
                    exclude_users=[user_id],
                )

            return connection_id

        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            await websocket.close(code=1011, reason="Connection failed")
            raise

    async def disconnect(self, connection_id: str, reason: str = "Client disconnect"):
        """
        Close and clean up a WebSocket connection

        Args:
            connection_id: Connection to close
            reason: Reason for disconnection
        """
        connection = self.active_connections.get(connection_id)
        if not connection:
            return

        try:
            # Close WebSocket if still open
            if connection.websocket.client_state.CONNECTED:
                await connection.websocket.close(code=1000, reason=reason)
        except Exception as e:
            logger.warning(f"Error closing WebSocket: {e}")

        # Remove from all tracking structures
        self.active_connections.pop(connection_id, None)
        self.user_connections[connection.user_id].discard(connection_id)

        if connection.league_id:
            self.league_connections[connection.league_id].discard(connection_id)

        for conn_type in connection.connection_types:
            self.type_connections[conn_type].discard(connection_id)

        logger.info(f"WebSocket disconnected: {connection_id} (reason: {reason})")

        # Notify league members of user leaving
        if connection.league_id and self.league_connections[connection.league_id]:
            await self.broadcast_to_league(
                connection.league_id,
                Message(
                    type=MessageType.USER_LEFT,
                    data={
                        "user_id": connection.user_id,
                        "username": connection.username,
                        "reason": reason,
                    },
                    league_id=connection.league_id,
                ),
                exclude_users=[connection.user_id],
            )

    async def send_to_connection(self, connection_id: str, message: Message) -> bool:
        """
        Send message to a specific connection

        Args:
            connection_id: Target connection
            message: Message to send

        Returns:
            True if sent successfully, False otherwise
        """
        connection = self.active_connections.get(connection_id)
        if not connection:
            return False

        try:
            message_data = {
                "type": message.type.value,
                "data": message.data,
                "timestamp": message.timestamp.isoformat(),
                "correlation_id": message.correlation_id,
            }

            if message.league_id:
                message_data["league_id"] = message.league_id

            await connection.websocket.send_text(json.dumps(message_data))
            return True

        except WebSocketDisconnect:
            # Connection already closed, clean up
            await self.disconnect(connection_id, "Connection lost")
            return False
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            return False

    async def send_to_user(self, user_id: str, message: Message) -> int:
        """
        Send message to all connections for a user

        Args:
            user_id: Target user
            message: Message to send

        Returns:
            Number of connections that received the message
        """
        connection_ids = self.user_connections[user_id].copy()
        sent_count = 0

        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        return sent_count

    async def broadcast_to_league(
        self,
        league_id: str,
        message: Message,
        connection_types: list[ConnectionType] | None = None,
        exclude_users: list[str] | None = None,
    ) -> int:
        """
        Broadcast message to all connections in a league

        Args:
            league_id: Target league
            message: Message to send
            connection_types: Filter by connection types
            exclude_users: Users to exclude from broadcast

        Returns:
            Number of connections that received the message
        """
        connection_ids = self.league_connections[league_id].copy()
        exclude_users = exclude_users or []
        sent_count = 0

        for connection_id in connection_ids:
            connection = self.active_connections.get(connection_id)
            if not connection:
                continue

            # Skip excluded users
            if connection.user_id in exclude_users:
                continue

            # Filter by connection types if specified
            if connection_types:
                if not any(
                    ct in connection.connection_types for ct in connection_types
                ):
                    continue

            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        # Also publish to Redis for other instances
        if self.redis_client:
            await self._publish_to_redis(
                league_id, message, connection_types, exclude_users
            )

        return sent_count

    async def broadcast_to_type(
        self,
        connection_type: ConnectionType,
        message: Message,
        league_id: str | None = None,
    ) -> int:
        """
        Broadcast message to all connections of a specific type

        Args:
            connection_type: Target connection type
            message: Message to send
            league_id: Optional league filter

        Returns:
            Number of connections that received the message
        """
        connection_ids = self.type_connections[connection_type].copy()
        sent_count = 0

        for connection_id in connection_ids:
            connection = self.active_connections.get(connection_id)
            if not connection:
                continue

            # Filter by league if specified
            if league_id and connection.league_id != league_id:
                continue

            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        return sent_count

    async def handle_message(self, connection_id: str, message: str):
        """
        Handle incoming message from WebSocket connection

        Args:
            connection_id: Source connection
            message: Raw message string
        """
        connection = self.active_connections.get(connection_id)
        if not connection:
            return

        try:
            data = json.loads(message)
            message_type = data.get("type")

            # Update last ping time
            connection.last_ping = datetime.utcnow()

            if message_type == "ping":
                # Respond to ping with pong
                await self.send_to_connection(
                    connection_id,
                    Message(
                        type=MessageType.HEARTBEAT,
                        data={
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    ),
                )

            elif message_type == "join_league":
                # Join a new league room
                league_id = data.get("league_id")
                if league_id:
                    await self._join_league(connection_id, league_id)

            elif message_type == "leave_league":
                # Leave current league room
                if connection.league_id:
                    await self._leave_league(connection_id)

            elif message_type == "chat_message":
                # Handle chat message
                await self._handle_chat_message(connection_id, data)

            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from connection {connection_id}: {message}")
            await self.send_to_connection(
                connection_id,
                Message(type=MessageType.ERROR, data={"error": "Invalid JSON format"}),
            )
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")

    async def get_connection_stats(self) -> dict[str, Any]:
        """Get statistics about active connections"""
        return {
            "total_connections": len(self.active_connections),
            "connections_by_league": {
                league_id: len(connections)
                for league_id, connections in self.league_connections.items()
            },
            "connections_by_type": {
                conn_type.value: len(connections)
                for conn_type, connections in self.type_connections.items()
            },
            "unique_users": len(self.user_connections),
            "uptime": datetime.utcnow().isoformat(),
        }

    # Private methods

    async def _join_league(self, connection_id: str, league_id: str):
        """Handle joining a league room"""
        connection = self.active_connections.get(connection_id)
        if not connection:
            return

        try:
            # Verify user can join league
            with get_db_session() as db:
                league_service = LeagueService(db)
                if not league_service.is_user_in_league(
                    league_id, connection.user_id
                ):
                    await self.send_to_connection(
                        connection_id,
                        Message(
                            type=MessageType.ERROR,
                            data={"error": "Not a league member"},
                        ),
                    )
                    return

            # Leave current league if any
            if connection.league_id:
                self.league_connections[connection.league_id].discard(connection_id)

            # Join new league
            connection.league_id = league_id
            self.league_connections[league_id].add(connection_id)

            # Notify league members
            await self.broadcast_to_league(
                league_id,
                Message(
                    type=MessageType.USER_JOINED,
                    data={
                        "user_id": connection.user_id,
                        "username": connection.username,
                    },
                    league_id=league_id,
                ),
                exclude_users=[connection.user_id],
            )

        except Exception as e:
            logger.error(f"Error joining league {league_id}: {e}")

    async def _leave_league(self, connection_id: str):
        """Handle leaving current league room"""
        connection = self.active_connections.get(connection_id)
        if not connection or not connection.league_id:
            return

        league_id = connection.league_id
        self.league_connections[league_id].discard(connection_id)
        connection.league_id = None

        # Notify remaining league members
        await self.broadcast_to_league(
            league_id,
            Message(
                type=MessageType.USER_LEFT,
                data={"user_id": connection.user_id, "username": connection.username},
                league_id=league_id,
            ),
        )

    async def _handle_chat_message(self, connection_id: str, data: dict[str, Any]):
        """Handle incoming chat message"""
        connection = self.active_connections.get(connection_id)
        if not connection or not connection.league_id:
            return

        message_content = data.get("content", "").strip()
        if not message_content:
            return

        # Create chat message
        chat_message = Message(
            type=MessageType.CHAT_MESSAGE,
            data={
                "user_id": connection.user_id,
                "username": connection.username,
                "content": message_content,
                "timestamp": datetime.utcnow().isoformat(),
            },
            league_id=connection.league_id,
        )

        # Broadcast to league
        await self.broadcast_to_league(
            connection.league_id, chat_message, connection_types=[ConnectionType.CHAT]
        )

    async def _cleanup_stale_connections(self):
        """Background task to clean up stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.utcnow()
                timeout_threshold = now - timedelta(seconds=self.connection_timeout)

                stale_connections = [
                    conn_id
                    for conn_id, conn in self.active_connections.items()
                    if conn.last_ping < timeout_threshold
                ]

                for connection_id in stale_connections:
                    await self.disconnect(connection_id, "Connection timeout")

                if stale_connections:
                    logger.info(
                        f"Cleaned up {len(stale_connections)} stale connections"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection cleanup: {e}")

    async def _send_heartbeats(self):
        """Background task to send heartbeat messages"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                heartbeat_message = Message(
                    type=MessageType.HEARTBEAT,
                    data={"type": "ping", "server_time": datetime.utcnow().isoformat()},
                )

                # Send to all connections
                connection_ids = list(self.active_connections.keys())
                for connection_id in connection_ids:
                    await self.send_to_connection(connection_id, heartbeat_message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending heartbeats: {e}")

    async def _close_all_connections(self):
        """Close all active connections"""
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id, "Server shutdown")

    async def _publish_to_redis(
        self,
        league_id: str,
        message: Message,
        connection_types: list[ConnectionType] | None = None,
        exclude_users: list[str] | None = None,
    ):
        """Publish message to Redis for cross-instance communication"""
        if not self.redis_client:
            return

        try:
            redis_message = {
                "league_id": league_id,
                "message": asdict(message),
                "connection_types": [ct.value for ct in (connection_types or [])],
                "exclude_users": exclude_users or [],
            }

            await self.redis_client.publish(
                self.redis_channel, json.dumps(redis_message, default=str)
            )

        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")

    async def _redis_subscriber(self):
        """Subscribe to Redis messages from other instances"""
        if not self.redis_client:
            return

        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(self.redis_channel)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        league_id = data["league_id"]
                        msg_data = data["message"]
                        connection_types = [
                            ConnectionType(ct)
                            for ct in data.get("connection_types", [])
                        ]
                        exclude_users = data.get("exclude_users", [])

                        # Reconstruct message object
                        msg = Message(
                            type=MessageType(msg_data["type"]),
                            data=msg_data["data"],
                            league_id=msg_data.get("league_id"),
                            user_id=msg_data.get("user_id"),
                            target_users=msg_data.get("target_users"),
                            timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                            correlation_id=msg_data.get("correlation_id"),
                        )

                        # Broadcast to local connections
                        await self.broadcast_to_league(
                            league_id, msg, connection_types, exclude_users
                        )

                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis subscriber error: {e}")


# Global connection manager instance
connection_manager = ConnectionManager()
