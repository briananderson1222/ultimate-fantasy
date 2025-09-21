from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..domains.trading.models.trade import Trade
from ..domains.leagues.models.league import League
from ..domains.leagues.models.team import Team
from ..domains.sports.models.player import Player
from ..models.notification import Notification
from ..infrastructure.database.session_factory import get_db_session
from ..infrastructure.logging.domain_logger import get_logger

logger = get_logger(__name__)


class TradeStatus(Enum):
    """Trade status types"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    VETOED = "vetoed"
    COMPLETED = "completed"


@dataclass
class TradeEvaluation:
    """Trade fairness evaluation"""
    fairness_score: float  # 0.0 to 1.0 (1.0 = perfectly fair)
    offering_team_value: float
    receiving_team_value: float
    value_difference: float
    position_analysis: Dict[str, Any]
    injury_risk_analysis: Dict[str, Any]
    recommendation: str  # accept, reject, caution


@dataclass
class TradeOffer:
    """Trade offer data"""
    offering_team_id: str
    receiving_team_id: str
    offered_players: List[str]
    requested_players: List[str]
    trade_message: Optional[str] = None
    expires_hours: int = 72


class TradeServiceError(Exception):
    """Base exception for trade service errors"""
    pass


class TradeNotFoundError(TradeServiceError):
    """Trade not found errors"""
    pass


class InvalidTradeError(TradeServiceError):
    """Invalid trade errors"""
    pass


class TradeDeadlineError(TradeServiceError):
    """Trade deadline errors"""
    pass


class TradeService:
    """
    Trade service for player exchanges

    Implements T031 requirements:
    - TradeService for player exchanges
    - Add trade evaluation, fairness analysis, processing
    - Include deadline enforcement and veto handling
    """

    def __init__(self):
        self.default_expiration_hours = 72
        self.max_expiration_hours = 168  # 1 week
        self.min_expiration_hours = 24
        self.veto_period_hours = 48
        self.fairness_threshold = 0.3  # Minimum fairness score to auto-approve

    # Trade Creation and Management

    def propose_trade(
        self,
        league_id: str,
        trade_offer: TradeOffer,
        proposing_user_id: str,
        db: Optional[Session] = None
    ) -> Trade:
        """
        Propose a new trade

        Args:
            league_id: League ID
            trade_offer: Trade offer details
            proposing_user_id: User proposing the trade
            db: Optional database session

        Returns:
            Created Trade instance

        Raises:
            TradeServiceError: Trade proposal failed
            InvalidTradeError: Invalid trade parameters
        """
        with get_db_session() if db is None else db as session:
            # Validate league exists and is in correct state
            league = session.query(League).filter(League.league_id == league_id).first()
            if not league:
                raise TradeServiceError("League not found")

            if league.status not in ["active", "drafting"]:
                raise TradeServiceError("Trades not allowed in current league state")

            # Check trade deadline
            if self._is_past_trade_deadline(league):
                raise TradeDeadlineError("Trade deadline has passed")

            # Validate teams
            offering_team = session.query(Team).filter(
                and_(Team.team_id == trade_offer.offering_team_id, Team.league_id == league_id)
            ).first()
            receiving_team = session.query(Team).filter(
                and_(Team.team_id == trade_offer.receiving_team_id, Team.league_id == league_id)
            ).first()

            if not offering_team or not receiving_team:
                raise InvalidTradeError("One or both teams not found in league")

            # Validate user owns the offering team
            if str(offering_team.user_id) != str(proposing_user_id):
                raise TradeServiceError("User does not own the offering team")

            # Validate teams are different
            if offering_team.team_id == receiving_team.team_id:
                raise InvalidTradeError("Cannot trade with yourself")

            # Validate players
            self._validate_trade_players(trade_offer, offering_team, receiving_team, session)

            # Calculate expiration time
            expiration_hours = min(max(trade_offer.expires_hours, self.min_expiration_hours), self.max_expiration_hours)
            expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)

            # Create trade
            trade = Trade(
                league_id=league_id,
                offering_team_id=trade_offer.offering_team_id,
                receiving_team_id=trade_offer.receiving_team_id,
                offered_players=trade_offer.offered_players,
                requested_players=trade_offer.requested_players,
                status=TradeStatus.PENDING.value,
                trade_message=trade_offer.trade_message,
                expires_at=expires_at
            )

            session.add(trade)
            session.flush()  # Get trade_id

            # Send notification to receiving team
            notification = Notification.create_trade_notification(
                user_id=str(receiving_team.user_id),
                league_id=league_id,
                team_id=str(receiving_team.team_id),
                trade_id=str(trade.trade_id),
                notification_type="trade_proposal",
                other_team_name=getattr(offering_team, "team_name", getattr(offering_team, "name", ""))
            )
            session.add(notification)

            session.commit()

            logger.info(f"Trade proposed: {offering_team.name} to {receiving_team.name}")
            return trade

    def respond_to_trade(
        self,
        trade_id: str,
        user_id: str,
        response: str,  # accept or reject
        rejection_reason: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Trade:
        """
        Respond to a trade proposal

        Args:
            trade_id: Trade ID
            user_id: User responding to trade
            response: "accept" or "reject"
            rejection_reason: Optional reason for rejection
            db: Optional database session

        Returns:
            Updated Trade instance

        Raises:
            TradeNotFoundError: Trade not found
            TradeServiceError: Invalid response attempt
        """
        with get_db_session() if db is None else db as session:
            trade = session.query(Trade).filter(Trade.trade_id == trade_id).first()
            if not trade:
                raise TradeNotFoundError("Trade not found")

            if trade.status != TradeStatus.PENDING.value:
                raise TradeServiceError(f"Cannot respond to trade with status: {trade.status}")

            # Check if trade has expired
            if trade.is_expired():
                trade.status = TradeStatus.EXPIRED.value
                session.commit()
                raise TradeServiceError("Trade has expired")

            # Validate user owns the receiving team
            receiving_team = session.query(Team).filter(Team.team_id == trade.receiving_team_id).first()
            if str(receiving_team.user_id) != str(user_id):
                raise TradeServiceError("User does not own the receiving team")

            # Process response
            if response.lower() == "accept":
                trade.status = TradeStatus.ACCEPTED.value
                trade.processed_at = datetime.utcnow()

                # Check if trade needs league approval or veto period
                league = session.query(League).filter(League.league_id == trade.league_id).first()
                trade_settings = league.trade_settings or {}

                if trade_settings.get("commissioner_approval_required", False):
                    # Wait for commissioner approval
                    logger.info(f"Trade accepted, waiting for commissioner approval: {trade_id}")
                elif trade_settings.get("league_vote_enabled", False):
                    # Start league voting period
                    logger.info(f"Trade accepted, starting league vote period: {trade_id}")
                else:
                    # Process trade immediately or start veto period
                    veto_period = trade_settings.get("trade_review_period_hours", 48)
                    if veto_period > 0:
                        # Schedule trade processing after veto period
                        logger.info(f"Trade accepted, starting {veto_period}h veto period: {trade_id}")
                    else:
                        # Process immediately
                        self._process_trade(trade, session)

                # Send notification to offering team
                offering_team = session.query(Team).filter(Team.team_id == trade.offering_team_id).first()
                notification = Notification.create_trade_notification(
                    user_id=str(offering_team.user_id),
                    league_id=str(trade.league_id),
                    team_id=str(trade.offering_team_id),
                    trade_id=str(trade.trade_id),
                    notification_type="trade_accepted",
                    other_team_name=getattr(receiving_team, "team_name", getattr(receiving_team, "name", ""))
                )
                session.add(notification)

            elif response.lower() == "reject":
                trade.status = TradeStatus.REJECTED.value
                trade.rejection_reason = rejection_reason
                trade.processed_at = datetime.utcnow()

                # Send notification to offering team
                offering_team = session.query(Team).filter(Team.team_id == trade.offering_team_id).first()
                notification = Notification.create_trade_notification(
                    user_id=str(offering_team.user_id),
                    league_id=str(trade.league_id),
                    team_id=str(trade.offering_team_id),
                    trade_id=str(trade.trade_id),
                    notification_type="trade_rejected",
                    other_team_name=getattr(receiving_team, "team_name", getattr(receiving_team, "name", ""))
                )
                session.add(notification)

                logger.info(f"Trade rejected: {trade_id}")

            else:
                raise TradeServiceError("Invalid response. Must be 'accept' or 'reject'")

            session.commit()
            return trade

    def cancel_trade(
        self,
        trade_id: str,
        user_id: str,
        db: Optional[Session] = None
    ) -> Trade:
        """
        Cancel a pending trade (offering team only)

        Args:
            trade_id: Trade ID
            user_id: User cancelling the trade
            db: Optional database session

        Returns:
            Updated Trade instance

        Raises:
            TradeNotFoundError: Trade not found
            TradeServiceError: Cannot cancel trade
        """
        with get_db_session() if db is None else db as session:
            trade = session.query(Trade).filter(Trade.trade_id == trade_id).first()
            if not trade:
                raise TradeNotFoundError("Trade not found")

            if trade.status != TradeStatus.PENDING.value:
                raise TradeServiceError("Can only cancel pending trades")

            # Validate user owns the offering team
            offering_team = session.query(Team).filter(Team.team_id == trade.offering_team_id).first()
            if str(offering_team.user_id) != str(user_id):
                raise TradeServiceError("Only the offering team can cancel the trade")

            trade.status = TradeStatus.REJECTED.value
            trade.rejection_reason = "Cancelled by offering team"
            trade.processed_at = datetime.utcnow()

            session.commit()

            logger.info(f"Trade cancelled by offering team: {trade_id}")
            return trade

    # Trade Evaluation and Analysis

    def evaluate_trade_fairness(
        self,
        trade_id: str,
        db: Optional[Session] = None
    ) -> TradeEvaluation:
        """
        Evaluate trade fairness and provide analysis

        Args:
            trade_id: Trade ID
            db: Optional database session

        Returns:
            TradeEvaluation with fairness analysis

        Raises:
            TradeNotFoundError: Trade not found
        """
        with get_db_session() if db is None else db as session:
            trade = session.query(Trade).filter(Trade.trade_id == trade_id).first()
            if not trade:
                raise TradeNotFoundError("Trade not found")

            # Get players involved in trade
            offered_players = session.query(Player).filter(
                Player.player_id.in_(trade.offered_players or [])
            ).all()
            requested_players = session.query(Player).filter(
                Player.player_id.in_(trade.requested_players or [])
            ).all()

            # Calculate player values
            offering_value = self._calculate_players_value(offered_players)
            receiving_value = self._calculate_players_value(requested_players)

            # Calculate fairness score
            total_value = offering_value + receiving_value
            if total_value == 0:
                fairness_score = 1.0
            else:
                value_difference = abs(offering_value - receiving_value)
                fairness_score = max(0.0, 1.0 - (value_difference / total_value))

            # Analyze positions
            position_analysis = self._analyze_position_impact(trade, offered_players, requested_players)

            # Analyze injury risks
            injury_analysis = self._analyze_injury_risks(offered_players, requested_players)

            # Generate recommendation
            recommendation = self._generate_trade_recommendation(fairness_score, position_analysis, injury_analysis)

            return TradeEvaluation(
                fairness_score=fairness_score,
                offering_team_value=offering_value,
                receiving_team_value=receiving_value,
                value_difference=abs(offering_value - receiving_value),
                position_analysis=position_analysis,
                injury_risk_analysis=injury_analysis,
                recommendation=recommendation
            )

    def get_trade_history(
        self,
        league_id: str,
        team_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trade history for league or team

        Args:
            league_id: League ID
            team_id: Optional team filter
            limit: Maximum results to return
            offset: Results offset for pagination
            db: Optional database session

        Returns:
            List of trade history data
        """
        with get_db_session() if db is None else db as session:
            query = session.query(Trade).filter(Trade.league_id == league_id)

            if team_id:
                query = query.filter(
                    or_(Trade.offering_team_id == team_id, Trade.receiving_team_id == team_id)
                )

            trades = query.order_by(desc(Trade.created_at)).offset(offset).limit(limit).all()

            trade_history = []
            for trade in trades:
                offering_team = session.query(Team).filter(Team.team_id == trade.offering_team_id).first()
                receiving_team = session.query(Team).filter(Team.team_id == trade.receiving_team_id).first()

                # Get player details
                offered_players = session.query(Player).filter(
                    Player.player_id.in_(trade.offered_players or [])
                ).all()
                requested_players = session.query(Player).filter(
                    Player.player_id.in_(trade.requested_players or [])
                ).all()

                trade_data = {
                    "trade_id": str(trade.trade_id),
                    "status": trade.status,
                    "offering_team": {
                        "team_id": str(offering_team.team_id),
                        "name": offering_team.name
                    } if offering_team else None,
                    "receiving_team": {
                        "team_id": str(receiving_team.team_id),
                        "name": receiving_team.name
                    } if receiving_team else None,
                    "offered_players": [
                        {
                            "player_id": str(p.player_id),
                            "name": p.name,
                            "position": p.position
                        } for p in offered_players
                    ],
                    "requested_players": [
                        {
                            "player_id": str(p.player_id),
                            "name": p.name,
                            "position": p.position
                        } for p in requested_players
                    ],
                    "trade_message": trade.trade_message,
                    "created_at": trade.created_at.isoformat(),
                    "processed_at": trade.processed_at.isoformat() if trade.processed_at else None,
                    "expires_at": trade.expires_at.isoformat() if trade.expires_at else None
                }

                trade_history.append(trade_data)

            return trade_history

    # Veto and Commissioner Actions

    def veto_trade(
        self,
        trade_id: str,
        commissioner_id: str,
        veto_reason: str,
        db: Optional[Session] = None
    ) -> Trade:
        """
        Veto a trade (commissioner only)

        Args:
            trade_id: Trade ID
            commissioner_id: Commissioner user ID
            veto_reason: Reason for veto
            db: Optional database session

        Returns:
            Updated Trade instance

        Raises:
            TradeNotFoundError: Trade not found
            TradeServiceError: Invalid veto attempt
        """
        with get_db_session() if db is None else db as session:
            trade = session.query(Trade).filter(Trade.trade_id == trade_id).first()
            if not trade:
                raise TradeNotFoundError("Trade not found")

            # Validate commissioner
            league = session.query(League).filter(League.league_id == trade.league_id).first()
            if str(league.commissioner_id) != str(commissioner_id):
                raise TradeServiceError("Only commissioner can veto trades")

            if trade.status not in [TradeStatus.ACCEPTED.value, TradeStatus.PENDING.value]:
                raise TradeServiceError(f"Cannot veto trade with status: {trade.status}")

            trade.status = TradeStatus.VETOED.value
            trade.vetoed_reason = veto_reason
            trade.processed_at = datetime.utcnow()

            # Send notifications to both teams
            offering_team = session.query(Team).filter(Team.team_id == trade.offering_team_id).first()
            receiving_team = session.query(Team).filter(Team.team_id == trade.receiving_team_id).first()

            for team in [offering_team, receiving_team]:
                notification = Notification.create_trade_notification(
                    user_id=str(team.user_id),
                    league_id=str(trade.league_id),
                    team_id=str(team.team_id),
                    trade_id=str(trade.trade_id),
                    notification_type="trade_vetoed",
                    other_team_name="Commissioner"
                )
                session.add(notification)

            session.commit()

            logger.info(f"Trade vetoed by commissioner: {trade_id}")
            return trade

    def process_trade(
        self,
        trade_id: str,
        commissioner_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Trade:
        """
        Process (complete) an accepted trade

        Args:
            trade_id: Trade ID
            commissioner_id: Optional commissioner ID for manual processing
            db: Optional database session

        Returns:
            Updated Trade instance

        Raises:
            TradeNotFoundError: Trade not found
            TradeServiceError: Cannot process trade
        """
        with get_db_session() if db is None else db as session:
            trade = session.query(Trade).filter(Trade.trade_id == trade_id).first()
            if not trade:
                raise TradeNotFoundError("Trade not found")

            if trade.status != TradeStatus.ACCEPTED.value:
                raise TradeServiceError(f"Cannot process trade with status: {trade.status}")

            # Validate commissioner if manual processing
            if commissioner_id:
                league = session.query(League).filter(League.league_id == trade.league_id).first()
                if str(league.commissioner_id) != str(commissioner_id):
                    raise TradeServiceError("Only commissioner can manually process trades")

            return self._process_trade(trade, session)

    # Helper Methods

    def _validate_trade_players(
        self,
        trade_offer: TradeOffer,
        offering_team: Team,
        receiving_team: Team,
        session: Session
    ) -> None:
        """Validate players in trade proposal"""
        # Validate offered players belong to offering team
        for player_id in trade_offer.offered_players:
            if player_id not in (offering_team.roster or []):
                player = session.query(Player).filter(Player.player_id == player_id).first()
                player_name = player.name if player else "Unknown"
                raise InvalidTradeError(f"Player {player_name} is not on offering team's roster")

        # Validate requested players belong to receiving team
        for player_id in trade_offer.requested_players:
            if player_id not in (receiving_team.roster or []):
                player = session.query(Player).filter(Player.player_id == player_id).first()
                player_name = player.name if player else "Unknown"
                raise InvalidTradeError(f"Player {player_name} is not on receiving team's roster")

        # Validate trade has players on both sides
        if not trade_offer.offered_players or not trade_offer.requested_players:
            raise InvalidTradeError("Trade must include players from both teams")

    def _is_past_trade_deadline(self, league: League) -> bool:
        """Check if current date is past trade deadline"""
        trade_settings = league.trade_settings or {}
        deadline_week = trade_settings.get("trade_deadline_week", 13)

        # TODO: Implement proper week calculation based on season schedule
        # For now, assume we're always before deadline
        return False

    def _calculate_players_value(self, players: List[Player]) -> float:
        """Calculate total fantasy value of players"""
        total_value = 0.0

        for player in players:
            # Use projections if available, otherwise use recent performance
            if player.projections and "fantasy_points" in player.projections:
                player_value = player.projections["fantasy_points"]
            elif player.season_stats:
                # Simple value calculation based on season stats
                # TODO: Implement more sophisticated valuation algorithm
                player_value = 15.0  # Placeholder value
            else:
                player_value = 10.0  # Default value for unknown players

            # Adjust for injury status
            if player.injury_status == "questionable":
                player_value *= 0.9
            elif player.injury_status == "doubtful":
                player_value *= 0.7
            elif player.injury_status == "out":
                player_value *= 0.3

            total_value += player_value

        return total_value

    def _analyze_position_impact(
        self,
        trade: Trade,
        offered_players: List[Player],
        requested_players: List[Player]
    ) -> Dict[str, Any]:
        """Analyze positional impact of trade"""
        offered_positions = {}
        requested_positions = {}

        for player in offered_players:
            offered_positions[player.position] = offered_positions.get(player.position, 0) + 1

        for player in requested_players:
            requested_positions[player.position] = requested_positions.get(player.position, 0) + 1

        return {
            "offered_positions": offered_positions,
            "requested_positions": requested_positions,
            "position_balance": "balanced" if offered_positions == requested_positions else "unbalanced"
        }

    def _analyze_injury_risks(
        self,
        offered_players: List[Player],
        requested_players: List[Player]
    ) -> Dict[str, Any]:
        """Analyze injury risks in trade"""
        offered_injured = sum(1 for p in offered_players if p.injury_status != "healthy")
        requested_injured = sum(1 for p in requested_players if p.injury_status != "healthy")

        return {
            "offered_injured_count": offered_injured,
            "requested_injured_count": requested_injured,
            "injury_risk_imbalance": abs(offered_injured - requested_injured),
            "high_risk": (offered_injured + requested_injured) > len(offered_players + requested_players) * 0.3
        }

    def _generate_trade_recommendation(
        self,
        fairness_score: float,
        position_analysis: Dict[str, Any],
        injury_analysis: Dict[str, Any]
    ) -> str:
        """Generate trade recommendation based on analysis"""
        if fairness_score >= 0.8:
            if injury_analysis.get("high_risk", False):
                return "caution"
            else:
                return "accept"
        elif fairness_score >= self.fairness_threshold:
            return "caution"
        else:
            return "reject"

    def _process_trade(self, trade: Trade, session: Session) -> Trade:
        """Actually process the trade by swapping players"""
        # Get teams
        offering_team = session.query(Team).filter(Team.team_id == trade.offering_team_id).first()
        receiving_team = session.query(Team).filter(Team.team_id == trade.receiving_team_id).first()

        # Swap players
        for player_id in (trade.offered_players or []):
            offering_team.remove_player_from_roster(player_id)
            receiving_team.add_player_to_roster(player_id)

        for player_id in (trade.requested_players or []):
            receiving_team.remove_player_from_roster(player_id)
            offering_team.add_player_to_roster(player_id)

        # Update trade status
        trade.status = TradeStatus.COMPLETED.value
        trade.processed_at = datetime.utcnow()

        session.commit()

        logger.info(f"Trade completed: {offering_team.name} <-> {receiving_team.name}")
        return trade

    # League Management Methods

    def get_pending_trades(self, league_id: str, db: Optional[Session] = None) -> List[Trade]:
        """Get all pending trades in a league"""
        with get_db_session() if db is None else db as session:
            return session.query(Trade).filter(
                and_(Trade.league_id == league_id, Trade.status == TradeStatus.PENDING.value)
            ).order_by(Trade.created_at).all()

    def expire_old_trades(self, db: Optional[Session] = None) -> int:
        """Expire trades that have passed their expiration time"""
        with get_db_session() if db is None else db as session:
            now = datetime.utcnow()

            expired_trades = session.query(Trade).filter(
                and_(
                    Trade.status == TradeStatus.PENDING.value,
                    Trade.expires_at <= now
                )
            ).all()

            for trade in expired_trades:
                trade.status = TradeStatus.EXPIRED.value
                trade.processed_at = now

            session.commit()

            if expired_trades:
                logger.info(f"Expired {len(expired_trades)} old trades")

            return len(expired_trades)

    def get_trade_statistics(self, league_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Get trade statistics for a league"""
        with get_db_session() if db is None else db as session:
            # Count trades by status
            trade_counts = session.query(
                Trade.status,
                func.count(Trade.trade_id).label("count")
            ).filter(Trade.league_id == league_id).group_by(Trade.status).all()

            status_counts = {status: count for status, count in trade_counts}

            # Get most active traders
            team_activity = session.query(
                Trade.offering_team_id.label("team_id"),
                func.count(Trade.trade_id).label("trade_count")
            ).filter(Trade.league_id == league_id).group_by(Trade.offering_team_id).all()

            # Get recent trade activity
            recent_trades = session.query(Trade).filter(
                and_(
                    Trade.league_id == league_id,
                    Trade.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).count()

            return {
                "total_trades": sum(status_counts.values()),
                "status_breakdown": status_counts,
                "recent_activity": recent_trades,
                "most_active_teams": [
                    {"team_id": str(team_id), "trade_count": count}
                    for team_id, count in team_activity
                ]
            }
