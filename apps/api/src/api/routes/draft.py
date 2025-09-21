from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json

from ...domains.drafts.models.draft import Draft
from ...domains.leagues.models.league import League
from ...domains.leagues.models.team import Team
from ...domains.sports.models.player import Player
from ...services.draft_service import DraftService, DraftServiceError, DraftNotFoundError, InvalidDraftStateError, OptimisticLockError
from ...services.league_service import LeagueService
from ...infrastructure.database.session_factory import get_db_session
from ...infrastructure.auth.dependencies import get_current_user
from ...infrastructure.logging.domain_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/draft", tags=["draft"])

# Initialize services
draft_service = DraftService()
league_service = LeagueService()


# Pydantic models for request/response
from pydantic import BaseModel, Field

class DraftCreateRequest(BaseModel):
    draft_type: str = Field(default="snake", description="Type of draft (snake, auction, linear)")
    pick_timer_seconds: int = Field(default=90, ge=30, le=300, description="Time limit per pick in seconds")
    auto_draft_enabled: bool = Field(default=True, description="Enable auto-draft for inactive users")

class DraftPickRequest(BaseModel):
    player_id: str = Field(description="ID of player to draft")

class DraftResponse(BaseModel):
    draft_id: str
    league_id: str
    status: str
    draft_type: str
    current_pick: int
    total_picks: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class DraftBoardResponse(BaseModel):
    draft: DraftResponse
    teams: List[Dict[str, Any]]
    picks: List[Dict[str, Any]]
    current_pick: Optional[Dict[str, Any]]
    draft_order: List[str]

class AvailablePlayersResponse(BaseModel):
    players: List[Dict[str, Any]]
    total_count: int
    has_more: bool


# Draft Management Endpoints

@router.get("/{league_id}", response_model=DraftBoardResponse)
async def get_draft_status(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get draft status and board for a league

    Returns complete draft information including:
    - Draft configuration and status
    - Team draft order
    - All completed picks
    - Current pick information
    - Available players
    """
    try:
        # Get draft by league
        draft = draft_service.get_draft_by_league(league_id, db)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found for this league")

        # Verify user is in the league
        user_team = league_service.get_user_team_in_league(league_id, current_user["user_id"], db)
        if not user_team:
            raise HTTPException(status_code=403, detail="User is not in this league")

        # Get complete draft board
        draft_board = draft_service.get_draft_board(str(draft.draft_id), db)

        return DraftBoardResponse(**draft_board)

    except DraftServiceError as e:
        logger.error(f"Draft service error in get_draft_status: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_draft_status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{league_id}", response_model=DraftResponse)
async def create_draft(
    league_id: str,
    request: DraftCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create a new draft for a league (commissioner only)

    Creates a draft with the specified configuration:
    - Draft type (snake, auction, linear)
    - Pick timer settings
    - Auto-draft configuration
    """
    try:
        # Verify user is commissioner of the league
        league = league_service.get_league(league_id, db)
        if not league:
            raise HTTPException(status_code=404, detail="League not found")

        if str(league.commissioner_id) != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Only league commissioner can create draft")

        # Create draft settings
        from ...services.draft_service import DraftSettings
        draft_settings = DraftSettings(
            draft_type=request.draft_type,
            pick_timer_seconds=request.pick_timer_seconds,
            auto_draft_enabled=request.auto_draft_enabled
        )

        # Create the draft
        draft = draft_service.create_draft(
            league_id=league_id,
            commissioner_id=current_user["user_id"],
            draft_settings=draft_settings,
            db=db
        )

        return DraftResponse(
            draft_id=str(draft.draft_id),
            league_id=str(draft.league_id),
            status=draft.status,
            draft_type=draft.draft_type,
            current_pick=draft.current_pick,
            total_picks=0,  # Will be calculated in get_draft_board
            started_at=draft.started_at,
            completed_at=draft.completed_at
        )

    except DraftServiceError as e:
        logger.error(f"Draft service error in create_draft: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in create_draft: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{league_id}/start")
async def start_draft(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Start the draft (commissioner only)

    Transitions the draft from scheduled to active state and
    begins the pick timer for the first team.
    """
    try:
        # Get draft
        draft = draft_service.get_draft_by_league(league_id, db)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found for this league")

        # Start the draft
        updated_draft = draft_service.start_draft(
            str(draft.draft_id),
            current_user["user_id"],
            db
        )

        return {
            "message": "Draft started successfully",
            "draft_id": str(updated_draft.draft_id),
            "status": updated_draft.status,
            "current_pick": updated_draft.current_pick
        }

    except DraftServiceError as e:
        logger.error(f"Draft service error in start_draft: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in start_draft: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{league_id}/pause")
async def pause_draft(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Pause the draft (commissioner only)

    Pauses an active draft and stops the pick timer.
    """
    try:
        draft = draft_service.get_draft_by_league(league_id, db)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found for this league")

        updated_draft = draft_service.pause_draft(
            str(draft.draft_id),
            current_user["user_id"],
            db
        )

        return {
            "message": "Draft paused successfully",
            "draft_id": str(updated_draft.draft_id),
            "status": updated_draft.status
        }

    except DraftServiceError as e:
        logger.error(f"Draft service error in pause_draft: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in pause_draft: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{league_id}/resume")
async def resume_draft(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Resume a paused draft (commissioner only)

    Resumes a paused draft and restarts the pick timer.
    """
    try:
        draft = draft_service.get_draft_by_league(league_id, db)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found for this league")

        updated_draft = draft_service.resume_draft(
            str(draft.draft_id),
            current_user["user_id"],
            db
        )

        return {
            "message": "Draft resumed successfully",
            "draft_id": str(updated_draft.draft_id),
            "status": updated_draft.status
        }

    except DraftServiceError as e:
        logger.error(f"Draft service error in resume_draft: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in resume_draft: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Draft Pick Endpoints

@router.post("/{league_id}/pick")
async def make_draft_pick(
    league_id: str,
    request: DraftPickRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Make a draft pick

    Allows a team to select a player during their turn in the draft.
    Validates that it's the user's turn and the player is available.
    """
    try:
        # Get draft
        draft = draft_service.get_draft_by_league(league_id, db)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found for this league")

        # Get user's team in this league
        user_team = league_service.get_user_team_in_league(league_id, current_user["user_id"], db)
        if not user_team:
            raise HTTPException(status_code=403, detail="User is not in this league")

        # Make the pick
        pick = draft_service.make_pick(
            draft_id=str(draft.draft_id),
            team_id=str(user_team.team_id),
            player_id=request.player_id,
            user_id=current_user["user_id"],
            is_autopick=False,
            db=db
        )

        return {
            "message": "Pick made successfully",
            "pick_number": pick.pick_number,
            "round_number": pick.round_number,
            "player_id": pick.player_id,
            "team_id": pick.team_id,
            "pick_time": pick.pick_time.isoformat() if pick.pick_time else None
        }

    except DraftServiceError as e:
        logger.error(f"Draft service error in make_draft_pick: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in make_draft_pick: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{league_id}/available-players", response_model=AvailablePlayersResponse)
async def get_available_players(
    league_id: str,
    position: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get players available for drafting

    Returns list of players that haven't been drafted yet,
    with optional filtering by position and search query.
    """
    try:
        # Verify user is in the league
        user_team = league_service.get_user_team_in_league(league_id, current_user["user_id"], db)
        if not user_team:
            raise HTTPException(status_code=403, detail="User is not in this league")

        # Get draft
        draft = draft_service.get_draft_by_league(league_id, db)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found for this league")

        # Get available players
        available_players = draft_service.get_available_players(
            str(draft.draft_id),
            position=position,
            limit=limit + 1,  # Get one extra to check if there are more
            offset=offset,
            db=db
        )

        # Filter by search if provided
        if search:
            search_lower = search.lower()
            available_players = [
                p for p in available_players
                if search_lower in p["name"].lower()
            ]

        has_more = len(available_players) > limit
        if has_more:
            available_players = available_players[:limit]

        return AvailablePlayersResponse(
            players=available_players,
            total_count=len(available_players),
            has_more=has_more
        )

    except DraftServiceError as e:
        logger.error(f"Draft service error in get_available_players: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_available_players: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{league_id}/autopick")
async def enable_autopick(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Enable auto-draft for user's team

    Enables automatic picking when it's the user's turn,
    useful for users who can't actively participate.
    """
    try:
        # Get user's team
        user_team = league_service.get_user_team_in_league(league_id, current_user["user_id"], db)
        if not user_team:
            raise HTTPException(status_code=403, detail="User is not in this league")

        # Get draft
        draft = draft_service.get_draft_by_league(league_id, db)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found for this league")

        # Enable auto-draft
        draft_service.enable_autodraft_for_team(
            str(draft.draft_id),
            str(user_team.team_id),
            current_user["user_id"],
            db
        )

        return {"message": "Auto-draft enabled successfully"}

    except DraftServiceError as e:
        logger.error(f"Draft service error in enable_autopick: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in enable_autopick: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Draft Statistics and Analysis

@router.get("/{league_id}/summary")
async def get_draft_summary(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get draft summary and statistics

    Returns overall draft statistics including:
    - Draft duration and completion status
    - Pick statistics (manual vs auto)
    - Team participation metrics
    """
    try:
        # Verify user is in the league
        user_team = league_service.get_user_team_in_league(league_id, current_user["user_id"], db)
        if not user_team:
            raise HTTPException(status_code=403, detail="User is not in this league")

        # Get draft
        draft = draft_service.get_draft_by_league(league_id, db)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found for this league")

        # Get summary
        summary = draft_service.get_draft_summary(str(draft.draft_id), db)

        return summary

    except DraftServiceError as e:
        logger.error(f"Draft service error in get_draft_summary: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_draft_summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# WebSocket for Real-time Draft Updates

class DraftConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, draft_id: str):
        await websocket.accept()
        if draft_id not in self.active_connections:
            self.active_connections[draft_id] = []
        self.active_connections[draft_id].append(websocket)

    def disconnect(self, websocket: WebSocket, draft_id: str):
        if draft_id in self.active_connections:
            if websocket in self.active_connections[draft_id]:
                self.active_connections[draft_id].remove(websocket)

    async def broadcast_to_draft(self, draft_id: str, message: dict):
        if draft_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[draft_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)

            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections[draft_id].remove(conn)

# Global connection manager
connection_manager = DraftConnectionManager()

@router.websocket("/{league_id}/ws")
async def draft_websocket_endpoint(
    websocket: WebSocket,
    league_id: str,
    token: str,  # JWT token passed as query parameter
    db: Session = Depends(get_db_session)
):
    """
    WebSocket endpoint for real-time draft updates

    Provides real-time notifications for:
    - Pick timer updates
    - New picks made
    - Draft status changes
    - Turn notifications
    """
    try:
        # TODO: Validate JWT token from query parameter
        # For now, accept all connections

        # Get draft
        draft = draft_service.get_draft_by_league(league_id, db)
        if not draft:
            await websocket.close(code=4004, reason="Draft not found")
            return

        draft_id = str(draft.draft_id)

        # Connect to draft room
        await connection_manager.connect(websocket, draft_id)

        try:
            # Send initial draft state
            draft_board = draft_service.get_draft_board(draft_id, db)
            await websocket.send_text(json.dumps({
                "type": "draft_state",
                "data": draft_board
            }))

            # Register timer callback for this draft
            def timer_callback(time_remaining: int):
                import asyncio
                asyncio.create_task(connection_manager.broadcast_to_draft(draft_id, {
                    "type": "timer_update",
                    "time_remaining": time_remaining
                }))

            draft_service.register_timer_callback(draft_id, timer_callback)

            # Keep connection alive and handle incoming messages
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "request_draft_state":
                    # Send updated draft state
                    draft_board = draft_service.get_draft_board(draft_id, db)
                    await websocket.send_text(json.dumps({
                        "type": "draft_state",
                        "data": draft_board
                    }))

        except WebSocketDisconnect:
            connection_manager.disconnect(websocket, draft_id)
            logger.info(f"WebSocket disconnected from draft {draft_id}")

    except Exception as e:
        logger.error(f"WebSocket error in draft endpoint: {e}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass


# Utility function to broadcast draft updates
async def broadcast_draft_update(draft_id: str, update_type: str, data: dict):
    """Broadcast draft updates to all connected clients"""
    message = {
        "type": update_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await connection_manager.broadcast_to_draft(draft_id, message)
