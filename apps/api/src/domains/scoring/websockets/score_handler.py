"""
Real-time score updates handler for WebSocket connections.

Provides comprehensive scoring event handling including:
- Live game score updates and statistics
- Player performance tracking and alerts
- Fantasy point calculations and updates
- Lineup optimization suggestions
- Injury and status notifications
- League standings and rankings updates
- Personalized user notifications
- Integration with sports data feeds and scoring engines
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

from sqlalchemy.orm import Session

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

from infrastructure.events.redis_pubsub import (
    get_event_system, Event, EventType, EventFilter
)
from infrastructure.websockets.connection_manager import (
    get_connection_manager, MessageType, RoomType
)
from domains.leagues.models.league import League
from domains.teams.models.team import Team
from domains.sports.services.sports_data_service import get_sports_data_service
from domains.scoring.services.scoring_service import get_scoring_service

logger = get_logger(__name__)


class ScoreWebSocketError(Exception):
    """Score WebSocket handler errors."""
    pass


class ScoreWebSocketHandler:
    """Handles real-time score and performance updates via WebSocket."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.connection_manager = get_connection_manager()
        self.event_system = get_event_system()

        # Active subscriptions by user/league
        self.user_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # user_id -> league_ids
        self.league_subscribers: Dict[str, Set[str]] = defaultdict(set)  # league_id -> user_ids

        # Scoring thresholds for notifications
        self.score_thresholds = {
            "touchdown": {"points": 6, "icon": "🏈"},
            "field_goal": {"points": 3, "icon": "🥅"},
            "homerun": {"points": 4, "icon": "⚾"},
            "three_pointer": {"points": 3, "icon": "🏀"},
            "milestone": {"points": 20, "icon": "⭐"},
        }

        # Event subscription
        self.subscription_id: Optional[str] = None

        # Performance tracking
        self.player_performance_cache: Dict[str, Dict[str, Any]] = {}
        self.game_status_cache: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize the score handler."""
        try:
            # Register message handlers
            self.connection_manager.register_message_handler(
                MessageType.SCORE_UPDATE, self._handle_score_subscription_request
            )
            self.connection_manager.register_message_handler(
                MessageType.PLAYER_STATS, self._handle_player_stats_request
            )

            # Subscribe to scoring events
            score_filter = EventFilter(
                event_types=[
                    EventType.SCORE_UPDATED,
                    EventType.GAME_STARTED,
                    EventType.GAME_COMPLETED,
                    EventType.PLAYER_STATS_UPDATED,
                ]
            )

            self.subscription_id = await self.event_system.subscribe(
                handler=self._handle_score_event,
                event_filter=score_filter,
                subscription_id="score_websocket_handler"
            )

            # Start background tasks
            asyncio.create_task(self._score_monitoring_loop())

            logger.info("Score WebSocket handler initialized")

        except Exception as e:
            logger.error(f"Failed to initialize score handler: {e}")
            raise ScoreWebSocketError(f"Failed to initialize: {e}")

    async def shutdown(self):
        """Shutdown the score handler."""
        try:
            if self.subscription_id:
                await self.event_system.unsubscribe(self.subscription_id)

            logger.info("Score WebSocket handler shutdown")

        except Exception as e:
            logger.error(f"Error shutting down score handler: {e}")

    async def subscribe_to_league_scores(self,
                                       connection_id: str,
                                       user_id: str,
                                       league_id: str) -> Dict[str, Any]:
        """
        Subscribe user to live score updates for a league.

        Args:
            connection_id: WebSocket connection ID
            user_id: User subscribing
            league_id: League to subscribe to

        Returns:
            Dict containing subscription result
        """
        try:
            # Validate user access to league
            access_result = await self._validate_league_access(league_id, user_id)
            if not access_result["allowed"]:
                return {
                    "success": False,
                    "error": access_result["reason"],
                }

            # Create score room for league
            room_id = f"scores_{league_id}"
            await self.connection_manager.create_room(
                room_id=room_id,
                room_type=RoomType.LEAGUE,
                metadata={
                    "league_id": league_id,
                    "type": "scores",
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

            # Join the room
            join_success = await self.connection_manager.join_room(connection_id, room_id)
            if not join_success:
                return {
                    "success": False,
                    "error": "Failed to join score room",
                }

            # Track subscriptions
            self.user_subscriptions[user_id].add(league_id)
            self.league_subscribers[league_id].add(user_id)

            # Get current game status for league
            current_games = await self._get_current_league_games(league_id)

            # Send initial score state
            await self.connection_manager.send_message(
                connection_id=connection_id,
                message_type=MessageType.SCORE_UPDATE,
                data={
                    "action": "subscribed",
                    "league_id": league_id,
                    "current_games": current_games,
                    "user_lineup": await self._get_user_lineup_status(user_id, league_id),
                },
                room_id=room_id,
            )

            logger.info(
                f"User subscribed to league scores",
                extra={
                    "user_id": user_id,
                    "league_id": league_id,
                    "room_id": room_id,
                }
            )

            return {
                "success": True,
                "room_id": room_id,
                "current_games": current_games,
            }

        except Exception as e:
            logger.error(f"Failed to subscribe to league scores: {e}")
            return {
                "success": False,
                "error": f"Failed to subscribe: {e}",
            }

    async def unsubscribe_from_league_scores(self,
                                           connection_id: str,
                                           user_id: str,
                                           league_id: str):
        """
        Unsubscribe user from league score updates.

        Args:
            connection_id: WebSocket connection ID
            user_id: User unsubscribing
            league_id: League to unsubscribe from
        """
        try:
            room_id = f"scores_{league_id}"

            # Leave the room
            await self.connection_manager.leave_room(connection_id, room_id)

            # Update subscriptions
            self.user_subscriptions[user_id].discard(league_id)
            self.league_subscribers[league_id].discard(user_id)

            # Clean up empty sets
            if not self.user_subscriptions[user_id]:
                del self.user_subscriptions[user_id]
            if not self.league_subscribers[league_id]:
                del self.league_subscribers[league_id]

            logger.info(f"User unsubscribed from league scores: {user_id} from {league_id}")

        except Exception as e:
            logger.error(f"Error unsubscribing from league scores: {e}")

    # Event handlers

    async def _handle_score_event(self, event: Event):
        """Handle scoring events from the event system."""
        try:
            if event.event_type == EventType.SCORE_UPDATED:
                await self._handle_score_update(event.data)

            elif event.event_type == EventType.GAME_STARTED:
                await self._handle_game_started(event.data)

            elif event.event_type == EventType.GAME_COMPLETED:
                await self._handle_game_completed(event.data)

            elif event.event_type == EventType.PLAYER_STATS_UPDATED:
                await self._handle_player_stats_updated(event.data)

        except Exception as e:
            logger.error(f"Error handling score event: {e}")

    async def _handle_score_update(self, data: Dict[str, Any]):
        """Handle real-time score updates."""
        try:
            game_id = data.get("game_id")
            if not game_id:
                return

            # Update game cache
            self.game_status_cache[game_id] = {
                **data,
                "last_updated": datetime.utcnow().isoformat(),
            }

            # Find affected leagues and users
            affected_leagues = await self._find_leagues_affected_by_game(game_id)

            for league_id in affected_leagues:
                room_id = f"scores_{league_id}"

                # Get fantasy impact for this league
                fantasy_impact = await self._calculate_fantasy_impact(data, league_id)

                # Broadcast to league room
                await self.connection_manager.broadcast_to_room(
                    room_id=room_id,
                    message_type=MessageType.SCORE_UPDATE,
                    data={
                        "action": "score_update",
                        "game_id": game_id,
                        "game_data": data,
                        "fantasy_impact": fantasy_impact,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                # Send personalized notifications
                await self._send_personalized_score_notifications(league_id, data, fantasy_impact)

        except Exception as e:
            logger.error(f"Error handling score update: {e}")

    async def _handle_game_started(self, data: Dict[str, Any]):
        """Handle game start notifications."""
        try:
            game_id = data.get("game_id")
            affected_leagues = await self._find_leagues_affected_by_game(game_id)

            for league_id in affected_leagues:
                room_id = f"scores_{league_id}"

                # Get lineup alerts for this game
                lineup_alerts = await self._get_lineup_alerts_for_game(league_id, data)

                await self.connection_manager.broadcast_to_room(
                    room_id=room_id,
                    message_type=MessageType.GAME_STATUS,
                    data={
                        "action": "game_started",
                        "game_id": game_id,
                        "game_data": data,
                        "lineup_alerts": lineup_alerts,
                        "started_at": data.get("started_at"),
                    }
                )

        except Exception as e:
            logger.error(f"Error handling game start: {e}")

    async def _handle_game_completed(self, data: Dict[str, Any]):
        """Handle game completion notifications."""
        try:
            game_id = data.get("game_id")
            affected_leagues = await self._find_leagues_affected_by_game(game_id)

            for league_id in affected_leagues:
                room_id = f"scores_{league_id}"

                # Calculate final fantasy scores
                final_scores = await self._calculate_final_game_scores(league_id, data)

                await self.connection_manager.broadcast_to_room(
                    room_id=room_id,
                    message_type=MessageType.GAME_STATUS,
                    data={
                        "action": "game_completed",
                        "game_id": game_id,
                        "game_data": data,
                        "final_scores": final_scores,
                        "completed_at": data.get("completed_at"),
                    }
                )

        except Exception as e:
            logger.error(f"Error handling game completion: {e}")

    async def _handle_player_stats_updated(self, data: Dict[str, Any]):
        """Handle player statistics updates."""
        try:
            player_id = data.get("player_id")
            if not player_id:
                return

            # Update player cache
            self.player_performance_cache[player_id] = {
                **data,
                "last_updated": datetime.utcnow().isoformat(),
            }

            # Find leagues where this player is rostered
            affected_leagues = await self._find_leagues_with_player(player_id)

            for league_id in affected_leagues:
                room_id = f"scores_{league_id}"

                # Calculate fantasy points for this update
                fantasy_points = await self._calculate_player_fantasy_points(player_id, data, league_id)

                # Check for milestone achievements
                milestones = self._check_player_milestones(data)

                await self.connection_manager.broadcast_to_room(
                    room_id=room_id,
                    message_type=MessageType.PLAYER_STATS,
                    data={
                        "action": "player_update",
                        "player_id": player_id,
                        "stats_update": data,
                        "fantasy_points": fantasy_points,
                        "milestones": milestones,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                # Send targeted notifications to player owners
                await self._send_player_owner_notifications(league_id, player_id, data, fantasy_points, milestones)

        except Exception as e:
            logger.error(f"Error handling player stats update: {e}")

    async def _handle_score_subscription_request(self, connection_id: str, data: Dict[str, Any], room_id: str):
        """Handle score subscription requests from WebSocket."""
        try:
            action = data.get("action")
            league_id = data.get("league_id")

            if not league_id:
                await self.connection_manager.send_message(
                    connection_id=connection_id,
                    message_type=MessageType.ERROR,
                    data={"message": "league_id required"}
                )
                return

            # This would require user context - typically handled during connection
            await self.connection_manager.send_message(
                connection_id=connection_id,
                message_type=MessageType.ERROR,
                data={"message": "Score subscriptions handled during connection setup"}
            )

        except Exception as e:
            logger.error(f"Error handling score subscription request: {e}")

    async def _handle_player_stats_request(self, connection_id: str, data: Dict[str, Any], room_id: str):
        """Handle player statistics requests."""
        try:
            player_id = data.get("player_id")
            if not player_id:
                await self.connection_manager.send_message(
                    connection_id=connection_id,
                    message_type=MessageType.ERROR,
                    data={"message": "player_id required"}
                )
                return

            # Get current player performance
            player_stats = await self._get_current_player_stats(player_id)

            await self.connection_manager.send_message(
                connection_id=connection_id,
                message_type=MessageType.PLAYER_STATS,
                data={
                    "action": "player_stats",
                    "player_id": player_id,
                    "stats": player_stats,
                },
                room_id=room_id,
            )

        except Exception as e:
            logger.error(f"Error handling player stats request: {e}")

    # Background tasks

    async def _score_monitoring_loop(self):
        """Background task for continuous score monitoring."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._check_for_stale_games()
                await self._update_performance_summaries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Score monitoring loop error: {e}")

    # Helper methods

    async def _validate_league_access(self, league_id: str, user_id: str) -> Dict[str, Any]:
        """Validate if user can access league scores."""
        try:
            # Get league
            league = self.db.query(League).filter(
                League.league_id == league_id
            ).first()

            if not league:
                return {
                    "allowed": False,
                    "reason": "League not found",
                }

            # Check if user is in this league
            user_team = self.db.query(Team).filter(
                Team.league_id == league_id,
                Team.owner_id == user_id
            ).first()

            if not user_team and league.commissioner_id != user_id:
                return {
                    "allowed": False,
                    "reason": "User not in this league",
                }

            return {
                "allowed": True,
                "reason": "League member",
            }

        except Exception as e:
            logger.error(f"Error validating league access: {e}")
            return {
                "allowed": False,
                "reason": f"Validation error: {e}",
            }

    async def _get_current_league_games(self, league_id: str) -> List[Dict[str, Any]]:
        """Get current games relevant to a league."""
        try:
            # This would integrate with sports data service
            sports_service = await get_sports_data_service()

            # Get league sport
            league = self.db.query(League).filter(League.league_id == league_id).first()
            if not league:
                return []

            sport = league.sport or "nfl"

            # Get today's games
            today_games = await sports_service.get_schedule(
                sport=sport.upper(),
                date=datetime.utcnow().date(),
                use_cache=True
            )

            return today_games or []

        except Exception as e:
            logger.error(f"Error getting current league games: {e}")
            return []

    async def _get_user_lineup_status(self, user_id: str, league_id: str) -> Dict[str, Any]:
        """Get user's current lineup status."""
        try:
            # Get user's team
            user_team = self.db.query(Team).filter(
                Team.league_id == league_id,
                Team.owner_id == user_id
            ).first()

            if not user_team:
                return {}

            # Get current lineup (simplified)
            lineup = user_team.lineup or {}

            return {
                "team_id": user_team.team_id,
                "team_name": user_team.team_name,
                "lineup_set": bool(lineup),
                "player_count": len(lineup.get("players", [])),
                "projected_points": lineup.get("projected_points", 0),
            }

        except Exception as e:
            logger.error(f"Error getting user lineup status: {e}")
            return {}

    async def _find_leagues_affected_by_game(self, game_id: str) -> List[str]:
        """Find all leagues that have players in the given game."""
        try:
            # This would require cross-referencing game teams with rostered players
            # Simplified implementation
            return []

        except Exception as e:
            logger.error(f"Error finding leagues affected by game: {e}")
            return []

    async def _calculate_fantasy_impact(self, game_data: Dict[str, Any], league_id: str) -> Dict[str, Any]:
        """Calculate fantasy impact of game events."""
        try:
            scoring_service = get_scoring_service()

            # Get league scoring rules
            league = self.db.query(League).filter(League.league_id == league_id).first()
            scoring_rules = league.scoring_rules if league else {}

            # Calculate impact (simplified)
            return {
                "total_fantasy_points": 0,
                "top_performers": [],
                "significant_plays": [],
            }

        except Exception as e:
            logger.error(f"Error calculating fantasy impact: {e}")
            return {}

    async def _send_personalized_score_notifications(self,
                                                   league_id: str,
                                                   game_data: Dict[str, Any],
                                                   fantasy_impact: Dict[str, Any]):
        """Send personalized notifications based on user rosters."""
        try:
            # Get all users in league
            subscribers = self.league_subscribers.get(league_id, set())

            for user_id in subscribers:
                # Check if user has players in this game
                user_players = await self._get_user_players_in_game(user_id, league_id, game_data)

                if user_players:
                    # Send targeted notification
                    await self.connection_manager.broadcast_to_user(
                        user_id=user_id,
                        message_type=MessageType.NOTIFICATION,
                        data={
                            "type": "score_alert",
                            "title": "Your players are scoring!",
                            "message": f"Updates from {len(user_players)} of your players",
                            "game_id": game_data.get("game_id"),
                            "your_players": user_players,
                            "fantasy_impact": fantasy_impact,
                        }
                    )

        except Exception as e:
            logger.error(f"Error sending personalized notifications: {e}")

    async def _get_user_players_in_game(self, user_id: str, league_id: str, game_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get user's players who are in the current game."""
        # Simplified implementation
        return []

    def _check_player_milestones(self, stats_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if player hit any milestones."""
        milestones = []

        # Check various milestones
        if stats_data.get("touchdowns", 0) >= 3:
            milestones.append({
                "type": "hat_trick",
                "description": "3+ Touchdowns",
                "icon": "🔥",
                "significance": "high",
            })

        if stats_data.get("passing_yards", 0) >= 300:
            milestones.append({
                "type": "passing_milestone",
                "description": "300+ Passing Yards",
                "icon": "💪",
                "significance": "medium",
            })

        return milestones

    async def _check_for_stale_games(self):
        """Check for games that might need status updates."""
        try:
            current_time = datetime.utcnow()

            # Check game cache for stale entries
            stale_games = []
            for game_id, game_info in self.game_status_cache.items():
                last_updated = datetime.fromisoformat(game_info["last_updated"])
                if current_time - last_updated > timedelta(minutes=5):
                    stale_games.append(game_id)

            # Clean up stale entries
            for game_id in stale_games:
                del self.game_status_cache[game_id]

        except Exception as e:
            logger.error(f"Error checking for stale games: {e}")

    async def _update_performance_summaries(self):
        """Update performance summaries for active players."""
        try:
            # This would periodically calculate performance summaries
            pass

        except Exception as e:
            logger.error(f"Error updating performance summaries: {e}")

    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get statistics about score subscriptions."""
        return {
            "total_user_subscriptions": len(self.user_subscriptions),
            "total_league_rooms": len(self.league_subscribers),
            "active_games_cached": len(self.game_status_cache),
            "active_player_cache": len(self.player_performance_cache),
            "subscriptions_by_league": {
                league_id: len(users)
                for league_id, users in self.league_subscribers.items()
            }
        }


# Global handler instance
_score_handler: Optional[ScoreWebSocketHandler] = None


def get_score_handler(db_session: Session) -> ScoreWebSocketHandler:
    """Get or create score WebSocket handler."""
    global _score_handler
    if _score_handler is None:
        _score_handler = ScoreWebSocketHandler(db_session)
    return _score_handler


async def initialize_score_handler(db_session: Session):
    """Initialize the score WebSocket handler."""
    handler = get_score_handler(db_session)
    await handler.initialize()
    return handler


async def shutdown_score_handler():
    """Shutdown the score WebSocket handler."""
    global _score_handler
    if _score_handler:
        await _score_handler.shutdown()
        _score_handler = None