from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from domains.leagues.models.league import League
from domains.leagues.models.team import Team
from domains.shared.events.publisher import DomainEventPublisher
from domains.shared.exceptions import (
    InsufficientPermissionsError,
    InvalidTradeError,
    LeagueNotFoundError,
    PlayerNotFoundError,
    TradeAlreadyProcessedError,
    TradeExpiredError,
    TradeNotFoundError,
)
from domains.shared.interfaces.trading_service import TradingServiceInterface
from domains.shared.models.notification import Notification
from domains.sports.models.player import Player
from domains.trading.models.trade import Trade
from domains.trading.models.waiver import Waiver
from infrastructure.events.dispatcher import get_event_dispatcher

logger = logging.getLogger(__name__)


@dataclass
class TradeEvaluation:
    """Aggregate metrics describing a proposed trade."""

    fairness_score: float
    offering_team_value: float
    receiving_team_value: float
    value_difference: float
    position_analysis: dict[str, Any]
    injury_risk_analysis: dict[str, Any]
    recommendation: str


class TradingService(TradingServiceInterface):
    """Trading domain service providing trade and waiver workflows."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.default_expiration_hours = 72
        self.min_expiration_hours = 24
        self.max_expiration_hours = 168

        try:
            dispatcher = get_event_dispatcher()
            self.event_publisher: DomainEventPublisher | None = DomainEventPublisher(
                dispatcher, "trading"
            )
        except RuntimeError:
            self.event_publisher = None

    # ------------------------------------------------------------------
    # Trade management
    # ------------------------------------------------------------------
    def propose_trade(
        self,
        *,
        league_id: str,
        from_team_id: str,
        to_team_id: str,
        offered_players: list[str],
        requested_players: list[str],
        proposing_user_id: str,
        message: str | None = None,
        expiration_hours: int | None = None,
    ) -> Trade:
        """Create a new trade proposal between two teams."""

        league = self._get_league(league_id)
        offering_team = self._get_team(from_team_id)
        receiving_team = self._get_team(to_team_id)

        if (
            offering_team.league_id != league.league_id
            or receiving_team.league_id != league.league_id
        ):
            raise InvalidTradeError("Both teams must belong to the specified league")
        if offering_team.team_id == receiving_team.team_id:
            raise InvalidTradeError("Cannot trade with the same team")
        if str(offering_team.user_id) != str(proposing_user_id):
            raise InsufficientPermissionsError("You do not own the offering team")

        normalized_offered = [str(pid) for pid in offered_players]
        normalized_requested = [str(pid) for pid in requested_players]
        self._validate_trade_players(normalized_offered, offering_team)
        self._validate_trade_players(normalized_requested, receiving_team)

        expires_at = self._calculate_expiration(
            expiration_hours or self.default_expiration_hours
        )

        trade = Trade(
            league_id=league.league_id,
            offering_team_id=offering_team.team_id,
            receiving_team_id=receiving_team.team_id,
            offered_players=normalized_offered,
            requested_players=normalized_requested,
            status="pending",
            trade_message=message,
            expires_at=expires_at,
        )
        self.session.add(trade)
        self.session.commit()

        self._notify_trade_proposed(trade, offering_team, receiving_team)
        self._publish_event(
            "trade.proposed",
            str(trade.trade_id),
            {
                "trade_id": str(trade.trade_id),
                "league_id": str(league.league_id),
                "offering_team_id": str(offering_team.team_id),
                "receiving_team_id": str(receiving_team.team_id),
                "expiration": expires_at.isoformat() if expires_at else None,
            },
        )
        return trade

    def respond_to_trade(
        self,
        *,
        trade_id: str,
        responding_user_id: str,
        action: str,
        rejection_reason: str | None = None,
    ) -> Trade:
        """Accept or reject a pending trade."""

        trade = self._get_trade(trade_id)
        if trade.status != "pending":
            raise TradeAlreadyProcessedError("Trade is no longer pending")

        if trade.expires_at and datetime.utcnow() > trade.expires_at:
            trade.status = "expired"
            trade.processed_at = datetime.utcnow()
            self.session.commit()
            raise TradeExpiredError("Trade has expired")

        receiving_team = self._get_team(str(trade.receiving_team_id))
        if str(receiving_team.user_id) != str(responding_user_id):
            raise InsufficientPermissionsError("You do not own the receiving team")

        action_lower = action.lower()
        if action_lower == "accept":
            trade.status = "accepted"
            trade.processed_at = datetime.utcnow()
            self.session.commit()
            self._publish_event(
                "trade.accepted",
                str(trade.trade_id),
                {"trade_id": str(trade.trade_id)},
            )
        elif action_lower == "reject":
            trade.status = "rejected"
            trade.rejection_reason = rejection_reason
            trade.processed_at = datetime.utcnow()
            self.session.commit()
            self._publish_event(
                "trade.rejected",
                str(trade.trade_id),
                {"trade_id": str(trade.trade_id), "reason": rejection_reason},
            )
        else:
            raise InvalidTradeError("Action must be 'accept' or 'reject'")

        return trade

    def cancel_trade(self, *, trade_id: str, requesting_user_id: str) -> Trade:
        """Cancel a pending trade as the offering team."""

        trade = self._get_trade(trade_id)
        if trade.status != "pending":
            raise TradeAlreadyProcessedError("Only pending trades can be cancelled")

        offering_team = self._get_team(str(trade.offering_team_id))
        if str(offering_team.user_id) != str(requesting_user_id):
            raise InsufficientPermissionsError("You do not own the offering team")

        trade.status = "rejected"
        trade.rejection_reason = "Cancelled by offering team"
        trade.processed_at = datetime.utcnow()
        self.session.commit()

        self._publish_event(
            "trade.cancelled",
            str(trade.trade_id),
            {"trade_id": str(trade.trade_id)},
        )
        return trade

    def get_trade(self, trade_id: str) -> Trade:
        return self._get_trade(trade_id)

    def list_league_trades(
        self,
        *,
        league_id: str,
        team_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Trade]:
        league_uuid = uuid.UUID(str(league_id))
        query = self.session.query(Trade).filter(Trade.league_id == league_uuid)
        if team_id:
            team_uuid = uuid.UUID(str(team_id))
            query = query.filter(
                (Trade.offering_team_id == team_uuid)
                | (Trade.receiving_team_id == team_uuid)
            )
        if status:
            query = query.filter(Trade.status == status)
        return (
            query.order_by(Trade.created_at.desc())
            .offset(offset)
            .limit(max(1, min(100, limit)))
            .all()
        )

    def evaluate_trade(self, trade_id: str) -> TradeEvaluation:
        trade = self._get_trade(trade_id)
        offered_players = self._fetch_players(trade.offered_players or [])
        requested_players = self._fetch_players(trade.requested_players or [])

        offering_value = self._calculate_players_value(offered_players)
        receiving_value = self._calculate_players_value(requested_players)
        total = offering_value + receiving_value
        value_difference = abs(offering_value - receiving_value)
        fairness_score = (
            1.0 if total == 0 else max(0.0, 1.0 - (value_difference / total))
        )

        position_analysis = self._position_breakdown(offered_players, requested_players)
        injury_analysis = self._injury_breakdown(offered_players, requested_players)
        recommendation = self._recommendation_from_score(
            fairness_score, injury_analysis
        )

        return TradeEvaluation(
            fairness_score=fairness_score,
            offering_team_value=offering_value,
            receiving_team_value=receiving_value,
            value_difference=value_difference,
            position_analysis=position_analysis,
            injury_risk_analysis=injury_analysis,
            recommendation=recommendation,
        )

    # ------------------------------------------------------------------
    # Async interface implementations (waivers & eligibility)
    # ------------------------------------------------------------------
    async def validate_trade_eligibility(self, user_id: str, league_id: str) -> bool:
        team = (
            self.session.query(Team)
            .filter(
                Team.user_id == uuid.UUID(user_id),
                Team.league_id == uuid.UUID(league_id),
            )
            .first()
        )
        return team is not None

    async def process_waiver_claim(self, waiver_id: str, user_id: str) -> dict:
        waiver = (
            self.session.query(Waiver)
            .filter(Waiver.waiver_id == uuid.UUID(waiver_id))
            .first()
        )
        if not waiver:
            raise ValueError(f"Waiver with ID {waiver_id} not found")

        transaction = {
            "transaction_id": str(uuid.uuid4()),
            "waiver_id": waiver_id,
            "user_id": user_id,
            "type": "waiver_claim",
            "status": "processed",
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._publish_event(
            "waiver.claim_processed",
            waiver_id,
            {
                "transaction_id": transaction["transaction_id"],
                "waiver_id": waiver_id,
                "user_id": user_id,
                "player_id": str(waiver.player_id),
                "league_id": str(waiver.league_id),
            },
        )
        return transaction

    async def get_active_waivers(self, league_id: str) -> list[Waiver]:
        return (
            self.session.query(Waiver)
            .filter(Waiver.league_id == uuid.UUID(league_id))
            .order_by(Waiver.bid.desc())
            .all()
        )

    async def get_user_transactions(self, user_id: str, league_id: str) -> list[dict]:
        team = (
            self.session.query(Team)
            .filter(
                Team.user_id == uuid.UUID(user_id),
                Team.league_id == uuid.UUID(league_id),
            )
            .first()
        )
        if not team:
            return []

        waivers = (
            self.session.query(Waiver)
            .filter(Waiver.team_id == team.team_id)
            .order_by(Waiver.created_at.desc())
            .all()
        )
        return [
            {
                "transaction_id": str(waiver.waiver_id),
                "type": "waiver_bid",
                "player_id": str(waiver.player_id),
                "bid": waiver.bid,
                "status": waiver.status,
                "created_at": (
                    waiver.created_at.isoformat() if waiver.created_at else None
                ),
            }
            for waiver in waivers
        ]

    async def validate_waiver_claim(self, waiver_id: str, user_id: str) -> bool:
        waiver = (
            self.session.query(Waiver)
            .filter(Waiver.waiver_id == uuid.UUID(waiver_id))
            .first()
        )
        if not waiver:
            return False
        return await self.validate_trade_eligibility(user_id, str(waiver.league_id))

    async def get_trade_deadline(self, league_id: str) -> datetime:
        league = self._get_league(league_id)
        settings = league.trade_settings or {}
        deadline = settings.get("deadline")
        if deadline:
            try:
                return datetime.fromisoformat(deadline)
            except ValueError:
                logger.debug("Invalid trade deadline format: %s", deadline)
        return datetime(datetime.utcnow().year, 12, 31, 23, 59, 59)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_league(self, league_id: str) -> League:
        league = (
            self.session.query(League)
            .filter(League.league_id == uuid.UUID(str(league_id)))
            .first()
        )
        if not league:
            raise LeagueNotFoundError("League not found")
        return league

    def _get_team(self, team_id: str) -> Team:
        team = (
            self.session.query(Team)
            .filter(Team.team_id == uuid.UUID(str(team_id)))
            .first()
        )
        if not team:
            raise InvalidTradeError("Team not found")
        return team

    def _get_trade(self, trade_id: str) -> Trade:
        trade = (
            self.session.query(Trade)
            .filter(Trade.trade_id == uuid.UUID(str(trade_id)))
            .first()
        )
        if not trade:
            raise TradeNotFoundError("Trade not found")
        return trade

    def _calculate_expiration(self, hours: int) -> datetime:
        clamped = max(self.min_expiration_hours, min(self.max_expiration_hours, hours))
        return datetime.utcnow() + timedelta(hours=clamped)

    def _validate_trade_players(self, player_ids: list[str], team: Team) -> None:
        roster = {str(pid) for pid in team.roster or []}
        missing = [pid for pid in player_ids if pid not in roster]
        if missing:
            raise InvalidTradeError(f"Players not on team roster: {', '.join(missing)}")
        if len(player_ids) != len(set(player_ids)):
            raise InvalidTradeError("Duplicate players in trade payload")

    def _fetch_players(self, player_ids: list[str]) -> list[Player]:
        if not player_ids:
            return []
        players = (
            self.session.query(Player)
            .filter(Player.player_id.in_([uuid.UUID(pid) for pid in player_ids]))
            .all()
        )
        found_ids = {str(player.player_id) for player in players}
        missing = [pid for pid in player_ids if pid not in found_ids]
        if missing:
            raise PlayerNotFoundError(f"Unknown players in trade: {', '.join(missing)}")
        return players

    @staticmethod
    def _calculate_players_value(players: list[Player]) -> float:
        value = 0.0
        for player in players:
            projections = player.projections or {}
            value += float(projections.get("fantasy_points", 0.0))
        return value or float(len(players))

    @staticmethod
    def _position_breakdown(
        offered_players: list[Player], requested_players: list[Player]
    ) -> dict[str, Any]:
        def _counts(players: list[Player]) -> dict[str, int]:
            counts: dict[str, int] = {}
            for player in players:
                counts[player.position] = counts.get(player.position, 0) + 1
            return counts

        return {
            "offered": _counts(offered_players),
            "requested": _counts(requested_players),
        }

    @staticmethod
    def _injury_breakdown(
        offered_players: list[Player], requested_players: list[Player]
    ) -> dict[str, Any]:
        offered_injured = sum(
            1
            for player in offered_players
            if (player.injury_status or "").lower() not in {"", "healthy"}
        )
        requested_injured = sum(
            1
            for player in requested_players
            if (player.injury_status or "").lower() not in {"", "healthy"}
        )
        total = offered_injured + requested_injured
        return {
            "offered_injured": offered_injured,
            "requested_injured": requested_injured,
            "high_risk": total >= max(1, len(offered_players + requested_players) // 2),
        }

    @staticmethod
    def _recommendation_from_score(
        fairness_score: float, injury_analysis: dict[str, Any]
    ) -> str:
        if fairness_score >= 0.8 and not injury_analysis.get("high_risk", False):
            return "accept"
        if fairness_score >= 0.5:
            return "caution"
        return "reject"

    def _notify_trade_proposed(
        self, trade: Trade, offering_team: Team, receiving_team: Team
    ) -> None:
        try:
            notification = Notification.create_trade_notification(
                user_id=str(receiving_team.user_id),
                league_id=str(trade.league_id),
                team_id=str(receiving_team.team_id),
                trade_id=str(trade.trade_id),
                notification_type="trade_proposal",
                other_team_name=getattr(
                    offering_team, "team_name", getattr(offering_team, "name", "")
                ),
            )
            self.session.add(notification)
            self.session.commit()
        except Exception:  # pragma: no cover - notifications are best effort
            logger.debug("Failed to enqueue trade notification", exc_info=True)

    def _publish_event(
        self, event: str, entity_id: str, payload: dict[str, Any]
    ) -> None:
        if not self.event_publisher:
            return
        try:
            import asyncio

            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.debug("No active event loop; skipping event publish for %s", event)
            return

        task = loop.create_task(
            self.event_publisher.publish_event(event, entity_id, payload)
        )
        task.add_done_callback(lambda t: t.exception())
