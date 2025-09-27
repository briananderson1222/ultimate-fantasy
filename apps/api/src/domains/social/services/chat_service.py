"""
League chat system service.

Provides comprehensive chat functionality for fantasy leagues including:
- Real-time messaging with WebSocket support
- Message threading and replies
- Rich media support (images, GIFs, reactions)
- Message moderation and filtering
- Chat history and search
- Presence indicators and typing status
"""

import contextlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from infrastructure.websockets.auth_middleware import get_websocket_auth_middleware
except ImportError:
    get_websocket_auth_middleware = None

try:
    from infrastructure.cache.redis_pool import get_redis_pool
except ImportError:
    get_redis_pool = None

try:
    from domains.social.services.moderation_service import ModerationService
except ImportError:
    ModerationService = None

try:
    from models.chat_message import ChatMessage
    from models.league import League
    from models.user import User
except ImportError:
    # Mock classes for when models aren't available
    class ChatMessage:
        pass

    class League:
        pass

    class User:
        pass


try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger

logger = get_logger(__name__)


class MessageType(Enum):
    """Chat message types."""

    TEXT = "text"
    IMAGE = "image"
    GIF = "gif"
    SYSTEM = "system"
    TRADE_PROPOSAL = "trade_proposal"
    DRAFT_UPDATE = "draft_update"
    LINEUP_REMINDER = "lineup_reminder"


class MessageStatus(Enum):
    """Message status types."""

    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    DELETED = "deleted"
    MODERATED = "moderated"


@dataclass
class ChatParticipant:
    """Chat participant information."""

    user_id: str
    username: str
    avatar_url: str | None = None
    is_online: bool = False
    is_typing: bool = False
    last_seen: datetime | None = None
    role: str = "member"  # member, admin, owner


@dataclass
class MessageReaction:
    """Message reaction data."""

    reaction_id: str
    emoji: str
    user_id: str
    username: str
    created_at: datetime


@dataclass
class ChatMessage:
    """Chat message data structure."""

    message_id: str
    league_id: str
    user_id: str
    username: str
    content: str
    message_type: MessageType
    status: MessageStatus
    created_at: datetime
    updated_at: datetime | None = None
    thread_id: str | None = None
    parent_message_id: str | None = None
    reactions: list[MessageReaction] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TypingIndicator:
    """Typing indicator data."""

    user_id: str
    username: str
    league_id: str
    started_at: datetime


class ChatService:
    """
    Comprehensive chat service for fantasy league communication.

    Features:
    - Real-time messaging with WebSocket integration
    - Message threading and conversations
    - Rich media support and file attachments
    - Content moderation and spam prevention
    - Presence tracking and typing indicators
    - Chat history with search and pagination
    """

    def __init__(self, db_session: AsyncSession, redis_pool=None):
        self.db_session = db_session
        self.redis_pool = redis_pool
        self.moderation_service = None
        self.ws_middleware = None

        # Chat state management
        self.active_participants: dict[str, set[ChatParticipant]] = {}
        self.typing_indicators: dict[str, list[TypingIndicator]] = {}

        # Rate limiting
        self.message_rate_limits = {"per_minute": 30, "per_hour": 500, "burst": 5}

        # Initialize async components
        self._initialized = False

    async def initialize(self):
        """Initialize async components."""
        if self._initialized:
            return

        # Initialize Redis connection
        if get_redis_pool and not self.redis_pool:
            try:
                self.redis_pool = await get_redis_pool()
            except Exception as e:
                logger.warning(f"Redis not available for chat service: {e}")

        # Initialize moderation service
        if ModerationService:
            self.moderation_service = ModerationService(
                self.db_session, self.redis_pool
            )
            await self.moderation_service.initialize()

        # Initialize WebSocket middleware
        if get_websocket_auth_middleware:
            try:
                self.ws_middleware = get_websocket_auth_middleware()
            except Exception as e:
                logger.warning(f"WebSocket middleware not available: {e}")

        self._initialized = True

    async def send_message(
        self,
        league_id: str,
        user_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        thread_id: str | None = None,
        parent_message_id: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> ChatMessage:
        """
        Send a chat message to a league.

        Args:
            league_id: League identifier
            user_id: Sender user ID
            content: Message content
            message_type: Type of message
            thread_id: Optional thread ID for threaded conversations
            parent_message_id: Optional parent message for replies
            attachments: Optional file attachments

        Returns:
            ChatMessage: The created message

        Raises:
            ValueError: If validation fails
            PermissionError: If user cannot send messages
        """
        await self.initialize()

        # Validate league membership
        if not await self._is_league_member(league_id, user_id):
            raise PermissionError("User is not a member of this league")

        # Check rate limits
        if not await self._check_rate_limits(user_id, league_id):
            raise ValueError("Message rate limit exceeded")

        # Validate and moderate content
        if self.moderation_service:
            moderation_result = await self.moderation_service.moderate_content(content)
            if moderation_result.action == "block":
                raise ValueError("Message content violates community guidelines")
            elif moderation_result.action == "flag":
                # Message will be sent but flagged for review
                pass

        # Get user information
        user = await self._get_user_info(user_id)
        if not user:
            raise ValueError("User not found")

        # Create message
        message_id = str(uuid4())
        message = ChatMessage(
            message_id=message_id,
            league_id=league_id,
            user_id=user_id,
            username=user.get("username", "Unknown"),
            content=content,
            message_type=message_type,
            status=MessageStatus.SENT,
            created_at=datetime.utcnow(),
            thread_id=thread_id,
            parent_message_id=parent_message_id,
            attachments=attachments or [],
        )

        # Store message in database
        await self._store_message(message)

        # Broadcast to league members
        await self._broadcast_message(message)

        # Update typing indicators
        await self._clear_typing_indicator(user_id, league_id)

        logger.info(f"Message sent in league {league_id} by user {user_id}")
        return message

    async def get_chat_history(
        self,
        league_id: str,
        user_id: str,
        limit: int = 50,
        before_message_id: str | None = None,
        thread_id: str | None = None,
    ) -> list[ChatMessage]:
        """
        Get chat history for a league.

        Args:
            league_id: League identifier
            user_id: Requesting user ID
            limit: Maximum number of messages to return
            before_message_id: Get messages before this message ID
            thread_id: Optional thread filter

        Returns:
            List of chat messages in reverse chronological order
        """
        await self.initialize()

        # Validate league membership
        if not await self._is_league_member(league_id, user_id):
            raise PermissionError("User is not a member of this league")

        # Build query
        query = select(ChatMessage).where(
            and_(
                ChatMessage.league_id == league_id,
                ChatMessage.status != MessageStatus.DELETED,
            )
        )

        if thread_id:
            query = query.where(ChatMessage.thread_id == thread_id)

        if before_message_id:
            # Get timestamp of the before_message_id
            before_message = await self.db_session.execute(
                select(ChatMessage.created_at).where(
                    ChatMessage.message_id == before_message_id
                )
            )
            before_timestamp = before_message.scalar_one_or_none()
            if before_timestamp:
                query = query.where(ChatMessage.created_at < before_timestamp)

        query = query.order_by(desc(ChatMessage.created_at)).limit(limit)

        # Execute query
        result = await self.db_session.execute(query)
        messages = result.scalars().all()

        # Convert to ChatMessage dataclass
        chat_messages = []
        for msg in messages:
            chat_messages.append(await self._convert_db_message(msg))

        return chat_messages

    async def search_messages(
        self, league_id: str, user_id: str, query: str, limit: int = 20
    ) -> list[ChatMessage]:
        """
        Search chat messages in a league.

        Args:
            league_id: League identifier
            user_id: Requesting user ID
            query: Search query
            limit: Maximum results

        Returns:
            List of matching messages
        """
        await self.initialize()

        # Validate league membership
        if not await self._is_league_member(league_id, user_id):
            raise PermissionError("User is not a member of this league")

        # Search in database
        search_query = (
            select(ChatMessage)
            .where(
                and_(
                    ChatMessage.league_id == league_id,
                    ChatMessage.status != MessageStatus.DELETED,
                    ChatMessage.content.ilike(f"%{query}%"),
                )
            )
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )

        result = await self.db_session.execute(search_query)
        messages = result.scalars().all()

        # Convert to ChatMessage dataclass
        chat_messages = []
        for msg in messages:
            chat_messages.append(await self._convert_db_message(msg))

        return chat_messages

    async def add_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """
        Add reaction to a message.

        Args:
            message_id: Message identifier
            user_id: User adding reaction
            emoji: Emoji reaction

        Returns:
            True if reaction was added successfully
        """
        await self.initialize()

        # Get message
        message = await self._get_message(message_id)
        if not message:
            return False

        # Validate league membership
        if not await self._is_league_member(message.league_id, user_id):
            return False

        # Add reaction to Redis
        if self.redis_pool:
            reaction_key = f"chat:reactions:{message_id}"
            reaction_data = {
                "reaction_id": str(uuid4()),
                "emoji": emoji,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
            }

            await self.redis_pool.redis_client.hset(
                reaction_key, f"{user_id}:{emoji}", json.dumps(reaction_data)
            )

            # Broadcast reaction update
            await self._broadcast_reaction_update(message_id, message.league_id)

        return True

    async def remove_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """
        Remove reaction from a message.

        Args:
            message_id: Message identifier
            user_id: User removing reaction
            emoji: Emoji reaction to remove

        Returns:
            True if reaction was removed successfully
        """
        await self.initialize()

        if self.redis_pool:
            reaction_key = f"chat:reactions:{message_id}"
            await self.redis_pool.redis_client.hdel(reaction_key, f"{user_id}:{emoji}")

            # Get message for league_id
            message = await self._get_message(message_id)
            if message:
                await self._broadcast_reaction_update(message_id, message.league_id)

        return True

    async def set_typing_indicator(self, league_id: str, user_id: str, is_typing: bool):
        """
        Set typing indicator for a user in a league.

        Args:
            league_id: League identifier
            user_id: User ID
            is_typing: Whether user is typing
        """
        await self.initialize()

        if self.redis_pool:
            typing_key = f"chat:typing:{league_id}"

            if is_typing:
                user_info = await self._get_user_info(user_id)
                typing_data = {
                    "user_id": user_id,
                    "username": user_info.get("username", "Unknown"),
                    "started_at": datetime.utcnow().isoformat(),
                }

                await self.redis_pool.redis_client.hset(
                    typing_key, user_id, json.dumps(typing_data)
                )

                # Set expiration
                await self.redis_pool.redis_client.expire(typing_key, 10)
            else:
                await self.redis_pool.redis_client.hdel(typing_key, user_id)

            # Broadcast typing update
            await self._broadcast_typing_update(league_id)

    async def get_league_participants(self, league_id: str) -> list[ChatParticipant]:
        """
        Get list of league chat participants.

        Args:
            league_id: League identifier

        Returns:
            List of chat participants
        """
        await self.initialize()

        # Get league members from database
        query = select(User).join(League.members).where(League.league_id == league_id)
        result = await self.db_session.execute(query)
        users = result.scalars().all()

        participants = []
        for user in users:
            # Check online status from Redis
            is_online = False
            if self.redis_pool:
                online_key = f"user:online:{user.user_id}"
                is_online = await self.redis_pool.redis_client.exists(online_key)

            participant = ChatParticipant(
                user_id=user.user_id,
                username=user.username,
                avatar_url=getattr(user, "avatar_url", None),
                is_online=bool(is_online),
                role=getattr(user, "role", "member"),
            )
            participants.append(participant)

        return participants

    async def delete_message(
        self, message_id: str, user_id: str, is_admin: bool = False
    ) -> bool:
        """
        Delete a chat message.

        Args:
            message_id: Message identifier
            user_id: User attempting deletion
            is_admin: Whether user is admin

        Returns:
            True if message was deleted successfully
        """
        await self.initialize()

        # Get message
        message = await self._get_message(message_id)
        if not message:
            return False

        # Check permissions
        if not is_admin and message.user_id != user_id:
            return False

        # Mark as deleted
        await self.db_session.execute(
            ChatMessage.__table__.update()
            .where(ChatMessage.message_id == message_id)
            .values(status=MessageStatus.DELETED, updated_at=datetime.utcnow())
        )
        await self.db_session.commit()

        # Broadcast deletion
        await self._broadcast_message_deletion(message_id, message.league_id)

        return True

    async def _is_league_member(self, league_id: str, user_id: str) -> bool:
        """Check if user is a member of the league."""
        query = (
            select(func.count())
            .select_from(League.__table__.join(League.members))
            .where(and_(League.league_id == league_id, User.user_id == user_id))
        )

        result = await self.db_session.execute(query)
        count = result.scalar()
        return count > 0

    async def _check_rate_limits(self, user_id: str, league_id: str) -> bool:
        """Check if user is within rate limits."""
        if not self.redis_pool:
            return True  # No rate limiting without Redis

        current_time = datetime.utcnow()
        rate_key = f"chat:rate:{user_id}:{league_id}"

        # Check minute limit
        minute_key = f"{rate_key}:minute:{current_time.minute}"
        minute_count = await self.redis_pool.redis_client.incr(minute_key)
        await self.redis_pool.redis_client.expire(minute_key, 60)

        if minute_count > self.message_rate_limits["per_minute"]:
            return False

        # Check hour limit
        hour_key = f"{rate_key}:hour:{current_time.hour}"
        hour_count = await self.redis_pool.redis_client.incr(hour_key)
        await self.redis_pool.redis_client.expire(hour_key, 3600)

        return not hour_count > self.message_rate_limits["per_hour"]

    async def _get_user_info(self, user_id: str) -> dict[str, Any] | None:
        """Get user information."""
        query = select(User).where(User.user_id == user_id)
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()

        if user:
            return {
                "user_id": user.user_id,
                "username": user.username,
                "avatar_url": getattr(user, "avatar_url", None),
            }

        return None

    async def _store_message(self, message: ChatMessage):
        """Store message in database."""
        db_message = ChatMessage(
            message_id=message.message_id,
            league_id=message.league_id,
            user_id=message.user_id,
            content=message.content,
            message_type=message.message_type.value,
            status=message.status.value,
            created_at=message.created_at,
            thread_id=message.thread_id,
            parent_message_id=message.parent_message_id,
            attachments=json.dumps(message.attachments),
            metadata=json.dumps(message.metadata),
        )

        self.db_session.add(db_message)
        await self.db_session.commit()

    async def _get_message(self, message_id: str) -> ChatMessage | None:
        """Get message from database."""
        query = select(ChatMessage).where(ChatMessage.message_id == message_id)
        result = await self.db_session.execute(query)
        db_message = result.scalar_one_or_none()

        if db_message:
            return await self._convert_db_message(db_message)

        return None

    async def _convert_db_message(self, db_message) -> ChatMessage:
        """Convert database message to ChatMessage dataclass."""
        reactions = []
        if self.redis_pool:
            reaction_key = f"chat:reactions:{db_message.message_id}"
            reaction_data = await self.redis_pool.redis_client.hgetall(reaction_key)

            for _key, value in reaction_data.items():
                reaction_info = json.loads(value)
                reaction = MessageReaction(
                    reaction_id=reaction_info["reaction_id"],
                    emoji=reaction_info["emoji"],
                    user_id=reaction_info["user_id"],
                    username=reaction_info.get("username", "Unknown"),
                    created_at=datetime.fromisoformat(reaction_info["created_at"]),
                )
                reactions.append(reaction)

        return ChatMessage(
            message_id=db_message.message_id,
            league_id=db_message.league_id,
            user_id=db_message.user_id,
            username=getattr(db_message, "username", "Unknown"),
            content=db_message.content,
            message_type=MessageType(db_message.message_type),
            status=MessageStatus(db_message.status),
            created_at=db_message.created_at,
            updated_at=db_message.updated_at,
            thread_id=db_message.thread_id,
            parent_message_id=db_message.parent_message_id,
            reactions=reactions,
            attachments=json.loads(db_message.attachments or "[]"),
            metadata=json.loads(db_message.metadata or "{}"),
        )

    async def _broadcast_message(self, message: ChatMessage):
        """Broadcast message to league members via WebSocket."""
        if not self.ws_middleware:
            return

        broadcast_data = {
            "type": "new_message",
            "data": {
                "message_id": message.message_id,
                "league_id": message.league_id,
                "user_id": message.user_id,
                "username": message.username,
                "content": message.content,
                "message_type": message.message_type.value,
                "created_at": message.created_at.isoformat(),
                "thread_id": message.thread_id,
                "parent_message_id": message.parent_message_id,
                "attachments": message.attachments,
            },
        }

        subscription = f"league_chat:{message.league_id}"
        await self.ws_middleware.broadcast_to_subscription(subscription, broadcast_data)

    async def _broadcast_reaction_update(self, message_id: str, league_id: str):
        """Broadcast reaction update to league members."""
        if not self.ws_middleware:
            return

        broadcast_data = {
            "type": "reaction_update",
            "data": {"message_id": message_id, "league_id": league_id},
        }

        subscription = f"league_chat:{league_id}"
        await self.ws_middleware.broadcast_to_subscription(subscription, broadcast_data)

    async def _broadcast_typing_update(self, league_id: str):
        """Broadcast typing indicator update."""
        if not self.ws_middleware:
            return

        typing_users = []
        if self.redis_pool:
            typing_key = f"chat:typing:{league_id}"
            typing_data = await self.redis_pool.redis_client.hgetall(typing_key)

            for _user_id, data in typing_data.items():
                typing_info = json.loads(data)
                typing_users.append(
                    {
                        "user_id": typing_info["user_id"],
                        "username": typing_info["username"],
                    }
                )

        broadcast_data = {
            "type": "typing_update",
            "data": {"league_id": league_id, "typing_users": typing_users},
        }

        subscription = f"league_chat:{league_id}"
        await self.ws_middleware.broadcast_to_subscription(subscription, broadcast_data)

    async def _broadcast_message_deletion(self, message_id: str, league_id: str):
        """Broadcast message deletion to league members."""
        if not self.ws_middleware:
            return

        broadcast_data = {
            "type": "message_deleted",
            "data": {"message_id": message_id, "league_id": league_id},
        }

        subscription = f"league_chat:{league_id}"
        await self.ws_middleware.broadcast_to_subscription(subscription, broadcast_data)

    async def _clear_typing_indicator(self, user_id: str, league_id: str):
        """Clear typing indicator for user."""
        if self.redis_pool:
            typing_key = f"chat:typing:{league_id}"
            await self.redis_pool.redis_client.hdel(typing_key, user_id)


# Global service instance
_chat_service: ChatService | None = None


async def get_chat_service(db_session: AsyncSession) -> ChatService:
    """Get chat service instance."""
    global _chat_service

    if _chat_service is None:
        redis_pool = None
        if get_redis_pool:
            with contextlib.suppress(Exception):
                redis_pool = await get_redis_pool()

        _chat_service = ChatService(db_session, redis_pool)
        await _chat_service.initialize()

    return _chat_service
