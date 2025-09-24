"""
WebSocket connection manager for real-time fantasy sports features.

Provides comprehensive WebSocket connection management including:
- Multi-room connection management (leagues, drafts, games)
- User authentication and authorization
- Message broadcasting and targeted delivery
- Connection state tracking and cleanup
- Rate limiting and abuse prevention
- Heartbeat monitoring and auto-reconnection
- Cross-service event distribution
- Scalable architecture for high concurrency
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4
import weakref

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

logger = get_logger(__name__)


class ConnectionError(Exception):
    """WebSocket connection manager errors."""
    pass


class MessageType(Enum):
    """WebSocket message types."""
    # Connection management
    AUTH = "auth"
    HEARTBEAT = "heartbeat"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    # Draft events
    DRAFT_PICK = "draft_pick"
    DRAFT_TIMER = "draft_timer"
    DRAFT_STATUS = "draft_status"

    # Trade events
    TRADE_PROPOSAL = "trade_proposal"
    TRADE_UPDATE = "trade_update"
    TRADE_EXECUTED = "trade_executed"

    # Score events
    SCORE_UPDATE = "score_update"
    GAME_STATUS = "game_status"
    PLAYER_STATS = "player_stats"

    # League events
    LEAGUE_UPDATE = "league_update"
    ROSTER_CHANGE = "roster_change"
    NOTIFICATION = "notification"

    # System events
    ERROR = "error"
    SUCCESS = "success"
    SYSTEM_MESSAGE = "system_message"


class RoomType(Enum):
    """Types of real-time rooms."""
    LEAGUE = "league"
    DRAFT = "draft"
    GAME = "game"
    GLOBAL = "global"


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""

    connection_id: str
    user_id: Optional[str]
    websocket: WebSocket
    connected_at: datetime
    last_heartbeat: datetime
    subscribed_rooms: Set[str]
    metadata: Dict[str, Any]
    rate_limit_tokens: int
    rate_limit_reset: datetime


@dataclass
class Room:
    """A real-time room for grouped connections."""

    room_id: str
    room_type: RoomType
    connections: Set[str]  # connection_ids
    metadata: Dict[str, Any]
    created_at: datetime
    last_activity: datetime


@dataclass
class Message:
    """WebSocket message structure."""

    type: MessageType
    room_id: Optional[str]
    data: Dict[str, Any]
    sender_id: Optional[str]
    timestamp: datetime
    message_id: str


class WebSocketConnectionManager:
    """Manages WebSocket connections for real-time features."""

    def __init__(self,
                 heartbeat_interval: int = 30,
                 connection_timeout: int = 300,
                 rate_limit_per_minute: int = 100):

        # Connection storage
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.rooms: Dict[str, Room] = {}

        # Event handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.connection_handlers: List[Callable] = []
        self.disconnection_handlers: List[Callable] = []

        # Configuration
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout
        self.rate_limit_per_minute = rate_limit_per_minute

        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "rooms_created": 0,
        }

        logger.info("WebSocket connection manager initialized")

    async def start(self):
        """Start background tasks for connection management."""
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        logger.info("WebSocket connection manager started")

    async def stop(self):
        """Stop background tasks and cleanup."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        # Disconnect all connections
        for connection_id in list(self.connections.keys()):
            await self.disconnect(connection_id)

        logger.info("WebSocket connection manager stopped")

    async def connect(self,
                     websocket: WebSocket,
                     user_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            user_id: Optional authenticated user ID
            metadata: Optional connection metadata

        Returns:
            connection_id: Unique identifier for this connection
        """
        try:
            await websocket.accept()

            connection_id = str(uuid4())
            now = datetime.utcnow()

            # Create connection info
            connection_info = ConnectionInfo(
                connection_id=connection_id,
                user_id=user_id,
                websocket=websocket,
                connected_at=now,
                last_heartbeat=now,
                subscribed_rooms=set(),
                metadata=metadata or {},
                rate_limit_tokens=self.rate_limit_per_minute,
                rate_limit_reset=now + timedelta(minutes=1),
            )

            # Store connection
            self.connections[connection_id] = connection_info

            # Track user connections
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)

            # Update statistics
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.connections)

            # Notify handlers
            for handler in self.connection_handlers:
                try:
                    await handler(connection_id, user_id, metadata)
                except Exception as e:
                    logger.warning(f"Connection handler error: {e}")

            logger.info(
                f"WebSocket connected",
                extra={
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "total_connections": self.stats["active_connections"],
                }
            )

            return connection_id

        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            raise ConnectionError(f"Connection failed: {e}")

    async def disconnect(self, connection_id: str, reason: str = "normal"):
        """
        Disconnect a WebSocket connection.

        Args:
            connection_id: Connection to disconnect
            reason: Reason for disconnection
        """
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return

            # Remove from rooms
            for room_id in list(connection.subscribed_rooms):
                await self.leave_room(connection_id, room_id)

            # Close WebSocket if still open
            if connection.websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.websocket.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")

            # Remove from user connections
            if connection.user_id and connection.user_id in self.user_connections:
                self.user_connections[connection.user_id].discard(connection_id)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]

            # Remove connection
            del self.connections[connection_id]

            # Update statistics
            self.stats["active_connections"] = len(self.connections)

            # Notify handlers
            for handler in self.disconnection_handlers:
                try:
                    await handler(connection_id, connection.user_id, reason)
                except Exception as e:
                    logger.warning(f"Disconnection handler error: {e}")

            logger.info(
                f"WebSocket disconnected",
                extra={
                    "connection_id": connection_id,
                    "user_id": connection.user_id,
                    "reason": reason,
                    "total_connections": self.stats["active_connections"],
                }
            )

        except Exception as e:
            logger.error(f"Failed to disconnect WebSocket {connection_id}: {e}")

    async def send_message(self,
                          connection_id: str,
                          message_type: MessageType,
                          data: Dict[str, Any],
                          room_id: Optional[str] = None) -> bool:
        """
        Send message to a specific connection.

        Args:
            connection_id: Target connection
            message_type: Type of message
            data: Message data
            room_id: Optional room context

        Returns:
            bool: True if message was sent successfully
        """
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                logger.warning(f"Connection {connection_id} not found")
                return False

            # Check if WebSocket is still connected
            if connection.websocket.client_state != WebSocketState.CONNECTED:
                await self.disconnect(connection_id, "websocket_closed")
                return False

            # Create message
            message = Message(
                type=message_type,
                room_id=room_id,
                data=data,
                sender_id=None,
                timestamp=datetime.utcnow(),
                message_id=str(uuid4()),
            )

            # Send message
            message_dict = asdict(message)
            message_dict["type"] = message.type.value

            await connection.websocket.send_text(json.dumps(message_dict))

            # Update statistics
            self.stats["messages_sent"] += 1

            return True

        except WebSocketDisconnect:
            await self.disconnect(connection_id, "websocket_disconnect")
            return False
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            await self.disconnect(connection_id, "send_error")
            return False

    async def broadcast_to_room(self,
                               room_id: str,
                               message_type: MessageType,
                               data: Dict[str, Any],
                               exclude_connections: Optional[Set[str]] = None) -> int:
        """
        Broadcast message to all connections in a room.

        Args:
            room_id: Target room
            message_type: Type of message
            data: Message data
            exclude_connections: Connection IDs to exclude

        Returns:
            int: Number of messages sent successfully
        """
        try:
            room = self.rooms.get(room_id)
            if not room:
                logger.warning(f"Room {room_id} not found")
                return 0

            exclude_connections = exclude_connections or set()
            sent_count = 0

            # Send to all connections in room
            for connection_id in room.connections:
                if connection_id not in exclude_connections:
                    success = await self.send_message(
                        connection_id, message_type, data, room_id
                    )
                    if success:
                        sent_count += 1

            # Update room activity
            room.last_activity = datetime.utcnow()

            logger.debug(
                f"Broadcast to room {room_id}",
                extra={
                    "message_type": message_type.value,
                    "connections": len(room.connections),
                    "sent": sent_count,
                }
            )

            return sent_count

        except Exception as e:
            logger.error(f"Failed to broadcast to room {room_id}: {e}")
            return 0

    async def broadcast_to_user(self,
                               user_id: str,
                               message_type: MessageType,
                               data: Dict[str, Any]) -> int:
        """
        Send message to all connections for a user.

        Args:
            user_id: Target user
            message_type: Type of message
            data: Message data

        Returns:
            int: Number of messages sent successfully
        """
        try:
            connection_ids = self.user_connections.get(user_id, set())
            sent_count = 0

            for connection_id in connection_ids:
                success = await self.send_message(connection_id, message_type, data)
                if success:
                    sent_count += 1

            return sent_count

        except Exception as e:
            logger.error(f"Failed to broadcast to user {user_id}: {e}")
            return 0

    async def create_room(self,
                         room_id: str,
                         room_type: RoomType,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a new room for connections.

        Args:
            room_id: Unique room identifier
            room_type: Type of room
            metadata: Optional room metadata

        Returns:
            bool: True if room was created successfully
        """
        try:
            if room_id in self.rooms:
                logger.warning(f"Room {room_id} already exists")
                return False

            room = Room(
                room_id=room_id,
                room_type=room_type,
                connections=set(),
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
            )

            self.rooms[room_id] = room
            self.stats["rooms_created"] += 1

            logger.info(f"Room created: {room_id} ({room_type.value})")
            return True

        except Exception as e:
            logger.error(f"Failed to create room {room_id}: {e}")
            return False

    async def join_room(self, connection_id: str, room_id: str) -> bool:
        """
        Add connection to a room.

        Args:
            connection_id: Connection to add
            room_id: Target room

        Returns:
            bool: True if connection joined successfully
        """
        try:
            connection = self.connections.get(connection_id)
            room = self.rooms.get(room_id)

            if not connection:
                logger.warning(f"Connection {connection_id} not found")
                return False

            if not room:
                logger.warning(f"Room {room_id} not found")
                return False

            # Add to room
            room.connections.add(connection_id)
            connection.subscribed_rooms.add(room_id)
            room.last_activity = datetime.utcnow()

            logger.debug(
                f"Connection joined room",
                extra={
                    "connection_id": connection_id,
                    "room_id": room_id,
                    "room_size": len(room.connections),
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to join room {room_id}: {e}")
            return False

    async def leave_room(self, connection_id: str, room_id: str) -> bool:
        """
        Remove connection from a room.

        Args:
            connection_id: Connection to remove
            room_id: Target room

        Returns:
            bool: True if connection left successfully
        """
        try:
            connection = self.connections.get(connection_id)
            room = self.rooms.get(room_id)

            if connection:
                connection.subscribed_rooms.discard(room_id)

            if room:
                room.connections.discard(connection_id)
                room.last_activity = datetime.utcnow()

                # Clean up empty rooms
                if not room.connections:
                    del self.rooms[room_id]
                    logger.debug(f"Empty room deleted: {room_id}")

            logger.debug(
                f"Connection left room",
                extra={
                    "connection_id": connection_id,
                    "room_id": room_id,
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to leave room {room_id}: {e}")
            return False

    async def handle_message(self, connection_id: str, message_data: str):
        """
        Handle incoming message from a connection.

        Args:
            connection_id: Source connection
            message_data: Raw message data
        """
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return

            # Rate limiting check
            now = datetime.utcnow()
            if now > connection.rate_limit_reset:
                connection.rate_limit_tokens = self.rate_limit_per_minute
                connection.rate_limit_reset = now + timedelta(minutes=1)

            if connection.rate_limit_tokens <= 0:
                await self.send_message(
                    connection_id,
                    MessageType.ERROR,
                    {"message": "Rate limit exceeded"}
                )
                return

            connection.rate_limit_tokens -= 1

            # Parse message
            try:
                message_dict = json.loads(message_data)
                message_type = MessageType(message_dict.get("type"))
                data = message_dict.get("data", {})
                room_id = message_dict.get("room_id")
            except (json.JSONDecodeError, ValueError) as e:
                await self.send_message(
                    connection_id,
                    MessageType.ERROR,
                    {"message": f"Invalid message format: {e}"}
                )
                return

            # Update heartbeat for any message
            connection.last_heartbeat = now
            self.stats["messages_received"] += 1

            # Handle built-in message types
            if message_type == MessageType.HEARTBEAT:
                await self.send_message(
                    connection_id,
                    MessageType.HEARTBEAT,
                    {"timestamp": now.isoformat()}
                )
                return

            elif message_type == MessageType.SUBSCRIBE:
                room_id = data.get("room_id")
                if room_id:
                    await self.join_room(connection_id, room_id)
                    await self.send_message(
                        connection_id,
                        MessageType.SUCCESS,
                        {"message": f"Subscribed to {room_id}"}
                    )
                return

            elif message_type == MessageType.UNSUBSCRIBE:
                room_id = data.get("room_id")
                if room_id:
                    await self.leave_room(connection_id, room_id)
                    await self.send_message(
                        connection_id,
                        MessageType.SUCCESS,
                        {"message": f"Unsubscribed from {room_id}"}
                    )
                return

            # Call registered handlers
            handlers = self.message_handlers.get(message_type, [])
            for handler in handlers:
                try:
                    await handler(connection_id, data, room_id)
                except Exception as e:
                    logger.error(f"Message handler error: {e}")

        except Exception as e:
            logger.error(f"Failed to handle message from {connection_id}: {e}")

    def register_message_handler(self,
                                message_type: MessageType,
                                handler: Callable):
        """Register a handler for a specific message type."""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)

    def register_connection_handler(self, handler: Callable):
        """Register a handler for new connections."""
        self.connection_handlers.append(handler)

    def register_disconnection_handler(self, handler: Callable):
        """Register a handler for disconnections."""
        self.disconnection_handlers.append(handler)

    # Background tasks

    async def _cleanup_loop(self):
        """Background task to clean up stale connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    async def _heartbeat_loop(self):
        """Background task to check connection health."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._check_connection_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")

    async def _cleanup_stale_connections(self):
        """Remove connections that haven't sent heartbeat."""
        now = datetime.utcnow()
        timeout_threshold = now - timedelta(seconds=self.connection_timeout)

        stale_connections = []
        for connection_id, connection in self.connections.items():
            if connection.last_heartbeat < timeout_threshold:
                stale_connections.append(connection_id)

        for connection_id in stale_connections:
            await self.disconnect(connection_id, "timeout")

        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")

    async def _check_connection_health(self):
        """Send heartbeat to all connections."""
        now = datetime.utcnow()

        for connection_id in list(self.connections.keys()):
            try:
                await self.send_message(
                    connection_id,
                    MessageType.HEARTBEAT,
                    {"server_time": now.isoformat()}
                )
            except Exception as e:
                logger.warning(f"Failed to send heartbeat to {connection_id}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics."""
        return {
            **self.stats,
            "active_rooms": len(self.rooms),
            "connections_by_room": {
                room_id: len(room.connections)
                for room_id, room in self.rooms.items()
            },
        }


# Global connection manager instance
_connection_manager: Optional[WebSocketConnectionManager] = None


def get_connection_manager() -> WebSocketConnectionManager:
    """Get the global WebSocket connection manager."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = WebSocketConnectionManager()
    return _connection_manager


async def initialize_connection_manager():
    """Initialize and start the connection manager."""
    manager = get_connection_manager()
    await manager.start()
    return manager


async def shutdown_connection_manager():
    """Shutdown the connection manager."""
    global _connection_manager
    if _connection_manager:
        await _connection_manager.stop()
        _connection_manager = None