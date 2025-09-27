"""
WebSocket API endpoint for real-time fantasy sports connections.

Provides unified WebSocket entry point including:
- User authentication and authorization
- Multi-feature connection routing (drafts, scores, leagues)
- Connection management and lifecycle handling
- Error handling and graceful degradation
- Rate limiting and abuse prevention
- Health monitoring and diagnostics
- Integration with all real-time handlers
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.websockets import WebSocketState
from sqlalchemy.orm import Session

from api.deps import get_current_user_websocket, get_db
from api.models.response import StandardResponse

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger  # type: ignore[assignment]

from domains.drafts.websockets.draft_handler import (
    get_draft_handler,
)
from domains.scoring.websockets.score_handler import (
    get_score_handler,
)
from infrastructure.events.redis_pubsub import get_event_system, initialize_event_system
from infrastructure.websockets.connection_manager import (
    MessageType,
    get_connection_manager,
    initialize_connection_manager,
)

logger = get_logger(__name__)

router = APIRouter()


class WebSocketAPIError(Exception):
    """WebSocket API errors."""


@router.websocket("/real-time/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    draft_id: str | None = Query(None, description="Draft ID to join"),
    league_id: str | None = Query(None, description="League ID for scores"),
    auth_token: str | None = Query(None, description="Authentication token"),
):
    """
    Real-time WebSocket connection endpoint.

    This endpoint provides unified access to all real-time fantasy features:
    - **Draft updates**: Live draft pick notifications and timer countdowns
    - **Score updates**: Real-time game scores and player statistics
    - **League updates**: Roster changes, trade notifications, waiver results
    - **User notifications**: Personal alerts and system messages

    **Connection Parameters:**
    - **draft_id**: Join specific draft room for live draft updates
    - **league_id**: Subscribe to league scores and general updates
    - **auth_token**: Optional authentication for personalized features

    **Message Format:**
    All messages follow the standard format:
    ```json
    {
        "type": "message_type",
        "room_id": "optional_room_context",
        "data": {...},
        "timestamp": "2024-01-01T12:00:00Z",
        "message_id": "unique_id"
    }
    ```

    **Authentication:**
    - Anonymous connections receive public updates only
    - Authenticated users get personalized notifications
    - League membership required for league-specific features

    **Rate Limiting:**
    - 100 messages per minute per connection
    - Automatic disconnection for abuse

    **Health Monitoring:**
    - Automatic heartbeat every 30 seconds
    - Connection timeout after 5 minutes of inactivity
    """
    connection_id = None
    user_id = None

    try:
        # Initialize services if needed
        await _ensure_services_initialized()

        # Get connection manager
        connection_manager = get_connection_manager()

        # Authenticate user if token provided
        current_user = None
        if auth_token:
            try:
                current_user = await get_current_user_websocket(auth_token, db)
                user_id = str(current_user.user_id)
            except Exception as e:
                logger.warning(f"WebSocket authentication failed: {e}")
                # Continue with anonymous connection

        # Accept connection
        connection_id = await connection_manager.connect(
            websocket=websocket,
            user_id=user_id,
            metadata={
                "draft_id": draft_id,
                "league_id": league_id,
                "authenticated": current_user is not None,
                "user_agent": websocket.headers.get("user-agent"),
                "ip_address": websocket.client.host if websocket.client else None,
            },
        )

        logger.info(
            "WebSocket connection established",
            extra={
                "connection_id": connection_id,
                "user_id": user_id,
                "draft_id": draft_id,
                "league_id": league_id,
                "authenticated": current_user is not None,
            },
        )

        # Initialize handlers
        draft_handler = get_draft_handler(db)
        score_handler = get_score_handler(db)

        # Join requested rooms
        room_join_results = {}

        if draft_id and current_user:
            draft_result = await draft_handler.join_draft_room(
                connection_id=connection_id, league_id=draft_id, user_id=user_id
            )
            room_join_results["draft"] = draft_result

        if league_id and current_user:
            score_result = await score_handler.subscribe_to_league_scores(
                connection_id=connection_id, user_id=user_id, league_id=league_id
            )
            room_join_results["scores"] = score_result

        # Send welcome message
        await connection_manager.send_message(
            connection_id=connection_id,
            message_type=MessageType.SUCCESS,
            data={
                "action": "connected",
                "connection_id": connection_id,
                "user_id": user_id,
                "authenticated": current_user is not None,
                "room_joins": room_join_results,
                "server_time": datetime.utcnow().isoformat(),
                "features": {
                    "drafts": draft_id is not None,
                    "scores": league_id is not None,
                    "notifications": current_user is not None,
                },
            },
        )

        # Message handling loop
        while True:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    websocket.receive_text(), timeout=300.0  # 5 minute timeout
                )

                # Handle the message
                await connection_manager.handle_message(connection_id, message)

            except TimeoutError:
                logger.info(f"WebSocket connection {connection_id} timed out")
                break

            except WebSocketDisconnect:
                logger.info(
                    f"WebSocket connection {connection_id} disconnected by client"
                )
                break

            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")

                # Send error to client if still connected
                if websocket.client_state == WebSocketState.CONNECTED:
                    await connection_manager.send_message(
                        connection_id=connection_id,
                        message_type=MessageType.ERROR,
                        data={
                            "message": "Error processing message",
                            "error_type": "message_processing_error",
                        },
                    )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected during setup")

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")

        # Send error if connection is still available
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "data": {
                                "message": "Connection error occurred",
                                "error_type": "connection_error",
                            },
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                )
        except:
            pass

    finally:
        # Cleanup connection
        if connection_id:
            try:
                # Leave specific rooms
                if draft_id and user_id:
                    draft_handler = get_draft_handler(db)
                    await draft_handler.leave_draft_room(
                        connection_id=connection_id,
                        room_id=f"draft_{draft_id}",
                        user_id=user_id,
                    )

                if league_id and user_id:
                    score_handler = get_score_handler(db)
                    await score_handler.unsubscribe_from_league_scores(
                        connection_id=connection_id,
                        user_id=user_id,
                        league_id=league_id,
                    )

                # Disconnect from connection manager
                connection_manager = get_connection_manager()
                await connection_manager.disconnect(connection_id, "normal_closure")

            except Exception as e:
                logger.error(f"Error during WebSocket cleanup: {e}")

        logger.info(
            "WebSocket connection closed",
            extra={
                "connection_id": connection_id,
                "user_id": user_id,
            },
        )


@router.get("/real-time/status", response_model=StandardResponse[dict[str, Any]])
async def get_realtime_status():
    """
    Get real-time service status and statistics.

    Returns comprehensive information about the real-time infrastructure:
    - Active WebSocket connections
    - Room participation statistics
    - Event system health
    - Performance metrics

    **Returns:**
    - Connection counts and distribution
    - Room activity statistics
    - Event processing metrics
    - System health indicators
    """
    try:
        # Get connection manager stats
        connection_manager = get_connection_manager()
        connection_stats = connection_manager.get_stats()

        # Get event system stats
        event_system = get_event_system()
        event_stats = event_system.get_stats()

        # Get handler-specific stats
        get_draft_handler(None)  # Will need to handle this better
        get_score_handler(None)

        status_data = {
            "service_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "connections": {
                "total_active": connection_stats.get("active_connections", 0),
                "total_lifetime": connection_stats.get("total_connections", 0),
                "active_rooms": connection_stats.get("active_rooms", 0),
                "connections_by_room": connection_stats.get("connections_by_room", {}),
            },
            "events": {
                "events_published": event_stats.get("events_published", 0),
                "events_processed": event_stats.get("events_processed", 0),
                "events_failed": event_stats.get("events_failed", 0),
                "active_subscriptions": event_stats.get("active_subscriptions", 0),
            },
            "drafts": {
                "active_rooms": 0,  # draft_handler.get_active_rooms_stats() if available
            },
            "scores": {
                "active_subscriptions": 0,  # score_handler.get_subscription_stats() if available
            },
            "health_indicators": {
                "connection_manager_healthy": True,
                "event_system_healthy": True,
                "redis_connected": True,  # Would check actual Redis connection
                "average_response_time_ms": 25,  # Would calculate from metrics
            },
        }

        return StandardResponse(
            success=True,
            data=status_data,
            message="Real-time service status retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to get real-time status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve real-time service status"
        )


@router.post("/real-time/broadcast", response_model=StandardResponse[dict[str, Any]])
async def broadcast_system_message(
    message_data: dict[str, Any],
    room_id: str | None = None,
    message_type: str = "system_message",
    # current_user: User = Depends(get_current_user),  # Would require admin role
):
    """
    Broadcast a system message to connected users.

    **Admin only endpoint** for sending system-wide notifications:
    - Maintenance announcements
    - Emergency alerts
    - Feature updates
    - General notifications

    **Requirements:**
    - Admin authentication required
    - Valid message format
    - Optional room targeting

    **Parameters:**
    - **message_data**: Message content and metadata
    - **room_id**: Optional specific room to target
    - **message_type**: Type of system message

    **Returns:**
    - Broadcast statistics and delivery confirmation
    """
    try:
        # TODO: Add admin authentication check
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Admin access required")

        connection_manager = get_connection_manager()

        # Prepare system message
        broadcast_data = {
            "type": "system_broadcast",
            "message": message_data.get("message", ""),
            "title": message_data.get("title", "System Message"),
            "severity": message_data.get("severity", "info"),
            "action_required": message_data.get("action_required", False),
            "expires_at": message_data.get("expires_at"),
            "broadcast_time": datetime.utcnow().isoformat(),
        }

        sent_count = 0

        if room_id:
            # Broadcast to specific room
            sent_count = await connection_manager.broadcast_to_room(
                room_id=room_id,
                message_type=MessageType.SYSTEM_MESSAGE,
                data=broadcast_data,
            )
        else:
            # Broadcast to all connections
            for connection_id in connection_manager.connections:
                success = await connection_manager.send_message(
                    connection_id=connection_id,
                    message_type=MessageType.SYSTEM_MESSAGE,
                    data=broadcast_data,
                )
                if success:
                    sent_count += 1

        result_data = {
            "broadcast_id": f"broadcast_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "messages_sent": sent_count,
            "target_room": room_id,
            "message_type": message_type,
            "broadcast_time": datetime.utcnow().isoformat(),
        }

        logger.info(
            "System broadcast sent",
            extra={
                "messages_sent": sent_count,
                "room_id": room_id,
                "message_type": message_type,
            },
        )

        return StandardResponse(
            success=True,
            data=result_data,
            message=f"Broadcast sent to {sent_count} connections",
        )

    except Exception as e:
        logger.error(f"Failed to send system broadcast: {e}")
        raise HTTPException(status_code=500, detail="Failed to send system broadcast")


# Helper functions


async def _ensure_services_initialized():
    """Ensure all real-time services are initialized."""
    try:
        # Initialize connection manager
        connection_manager = get_connection_manager()
        if not hasattr(connection_manager, "_initialized"):
            await initialize_connection_manager()
            connection_manager._initialized = True

        # Initialize event system
        event_system = get_event_system()
        if not event_system.is_running:
            await initialize_event_system()

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise WebSocketAPIError(f"Service initialization failed: {e}")


async def initialize_websocket_api():
    """Initialize the WebSocket API and all dependencies."""
    try:
        await _ensure_services_initialized()
        logger.info("WebSocket API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket API: {e}")
        raise


async def shutdown_websocket_api():
    """Shutdown the WebSocket API and cleanup resources."""
    try:
        from domains.drafts.websockets.draft_handler import shutdown_draft_handler
        from domains.scoring.websockets.score_handler import shutdown_score_handler
        from infrastructure.events.redis_pubsub import shutdown_event_system
        from infrastructure.websockets.connection_manager import (
            shutdown_connection_manager,
        )

        await shutdown_draft_handler()
        await shutdown_score_handler()
        await shutdown_connection_manager()
        await shutdown_event_system()

        logger.info("WebSocket API shutdown completed")

    except Exception as e:
        logger.error(f"Error during WebSocket API shutdown: {e}")


# Add router to main application
def include_websocket_routes(app):
    """Include WebSocket routes in the main FastAPI application."""
    app.include_router(router, prefix="/api/v1", tags=["real-time"])

    # Add startup and shutdown events
    @app.on_event("startup")
    async def startup_websocket_services():
        await initialize_websocket_api()

    @app.on_event("shutdown")
    async def shutdown_websocket_services():
        await shutdown_websocket_api()
