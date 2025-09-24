"""
Enhanced waiver processing service with FAAB (Free Agent Acquisition Budget) support.

Provides comprehensive waiver claim processing including:
- FAAB bidding system with budget management
- Priority-based waiver order processing
- Blind auction mechanics for competitive bidding
- Drop player validation and roster management
- Waiver period timing and batch processing
- Tie-breaking rules and fair allocation
- Real-time notifications and status updates
- Integration with league rules and settings
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.orm import Session

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

from domains.leagues.models.league import League
from domains.notifications.services.notification_service import get_notification_service
from domains.teams.models.team import Team
from domains.trading.models.waiver_bid import WaiverBid
from domains.sports.services.sports_data_service import get_sports_data_service

logger = get_logger(__name__)


class WaiverProcessorError(Exception):
    """Waiver processor service errors."""
    pass


class WaiverType(Enum):
    """Types of waiver systems."""
    PRIORITY = "priority"  # Traditional waiver priority order
    FAAB = "faab"         # Free Agent Acquisition Budget
    BLIND_BID = "blind_bid"  # Blind bidding auction


class ProcessingResult(Enum):
    """Waiver processing results."""
    SUCCESSFUL = "successful"
    INSUFFICIENT_BUDGET = "insufficient_budget"
    ROSTER_FULL = "roster_full"
    PLAYER_UNAVAILABLE = "player_unavailable"
    INVALID_DROP = "invalid_drop"
    OUTBID = "outbid"
    LOWER_PRIORITY = "lower_priority"


@dataclass
class WaiverClaim:
    """Individual waiver claim for processing."""

    bid_id: str
    team_id: str
    player_id: str
    drop_player_id: Optional[str]
    bid_amount: float
    priority: int
    submitted_at: datetime
    waiver_period: int


@dataclass
class ProcessingOutcome:
    """Result of processing a waiver claim."""

    bid_id: str
    team_id: str
    player_id: str
    result: ProcessingResult
    bid_amount: float
    winning_amount: Optional[float]
    drop_player_id: Optional[str]
    reason: str
    processed_at: datetime


@dataclass
class WaiverPeriodResult:
    """Complete results for a waiver processing period."""

    period_id: str
    league_id: str
    processed_at: datetime
    total_claims: int
    successful_claims: int
    failed_claims: int
    total_budget_spent: float
    player_results: Dict[str, List[ProcessingOutcome]]
    team_budget_updates: Dict[str, float]
    roster_updates: Dict[str, List[Dict[str, any]]]
    notifications_sent: int


class WaiverProcessor:
    """Enhanced waiver processing service with FAAB support."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.notification_service = None

    async def process_waiver_period(
        self,
        league_id: str,
        waiver_period: int,
        force_process: bool = False,
    ) -> WaiverPeriodResult:
        """
        Process all waiver claims for a specific period.

        Args:
            league_id: League to process waivers for
            waiver_period: Waiver period number to process
            force_process: Force processing even if not scheduled

        Returns:
            Complete processing results with all outcomes
        """
        try:
            logger.info(
                f"Starting waiver processing",
                extra={
                    "league_id": league_id,
                    "waiver_period": waiver_period,
                    "force_process": force_process,
                }
            )

            # Get league and validate waiver settings
            league = self.db.query(League).filter(
                League.league_id == league_id
            ).first()

            if not league:
                raise WaiverProcessorError(f"League {league_id} not found")

            waiver_settings = league.waiver_settings or {}
            waiver_type = WaiverType(waiver_settings.get("type", "priority"))

            # Validate processing time
            if not force_process and not self._is_processing_time(league, waiver_period):
                raise WaiverProcessorError("Not yet time to process this waiver period")

            # Get all pending claims for this period
            claims = self._get_pending_claims(league_id, waiver_period)

            if not claims:
                logger.info(f"No waiver claims to process for period {waiver_period}")
                return WaiverPeriodResult(
                    period_id=f"{league_id}_{waiver_period}",
                    league_id=league_id,
                    processed_at=datetime.utcnow(),
                    total_claims=0,
                    successful_claims=0,
                    failed_claims=0,
                    total_budget_spent=0.0,
                    player_results={},
                    team_budget_updates={},
                    roster_updates={},
                    notifications_sent=0,
                )

            # Group claims by player for processing
            claims_by_player = self._group_claims_by_player(claims)

            # Initialize results tracking
            all_outcomes = []
            team_budget_updates = {}
            roster_updates = {}
            total_budget_spent = 0.0

            # Process each player's claims
            for player_id, player_claims in claims_by_player.items():
                player_outcomes = await self._process_player_claims(
                    league, player_id, player_claims, waiver_type
                )
                all_outcomes.extend(player_outcomes)

                # Track budget and roster changes
                for outcome in player_outcomes:
                    if outcome.result == ProcessingResult.SUCCESSFUL:
                        if outcome.team_id not in team_budget_updates:
                            team_budget_updates[outcome.team_id] = 0.0

                        spent_amount = outcome.winning_amount or outcome.bid_amount
                        team_budget_updates[outcome.team_id] += spent_amount
                        total_budget_spent += spent_amount

                        # Track roster changes
                        if outcome.team_id not in roster_updates:
                            roster_updates[outcome.team_id] = []

                        roster_updates[outcome.team_id].append({
                            "action": "add",
                            "player_id": outcome.player_id,
                            "drop_player_id": outcome.drop_player_id,
                            "acquired_via": "waiver",
                            "cost": spent_amount,
                        })

            # Apply all roster and budget updates
            await self._apply_processing_results(all_outcomes, team_budget_updates, roster_updates)

            # Send notifications
            notifications_sent = await self._send_processing_notifications(
                league_id, all_outcomes, waiver_period
            )

            # Create period result
            player_results = {}
            for outcome in all_outcomes:
                if outcome.player_id not in player_results:
                    player_results[outcome.player_id] = []
                player_results[outcome.player_id].append(outcome)

            successful_claims = len([o for o in all_outcomes if o.result == ProcessingResult.SUCCESSFUL])
            failed_claims = len(all_outcomes) - successful_claims

            result = WaiverPeriodResult(
                period_id=f"{league_id}_{waiver_period}",
                league_id=league_id,
                processed_at=datetime.utcnow(),
                total_claims=len(claims),
                successful_claims=successful_claims,
                failed_claims=failed_claims,
                total_budget_spent=total_budget_spent,
                player_results=player_results,
                team_budget_updates=team_budget_updates,
                roster_updates=roster_updates,
                notifications_sent=notifications_sent,
            )

            logger.info(
                f"Waiver processing completed",
                extra={
                    "league_id": league_id,
                    "waiver_period": waiver_period,
                    "total_claims": len(claims),
                    "successful": successful_claims,
                    "failed": failed_claims,
                    "budget_spent": total_budget_spent,
                }
            )

            return result

        except Exception as e:
            logger.error(f"Waiver processing failed: {e}")
            raise WaiverProcessorError(f"Failed to process waivers: {e}")

    async def _process_player_claims(
        self,
        league: League,
        player_id: str,
        claims: List[WaiverClaim],
        waiver_type: WaiverType,
    ) -> List[ProcessingOutcome]:
        """Process all claims for a specific player."""
        try:
            # Validate player is available
            sports_service = await get_sports_data_service()
            player_data = await sports_service.get_player_details(player_id)

            if not player_data:
                return [
                    ProcessingOutcome(
                        bid_id=claim.bid_id,
                        team_id=claim.team_id,
                        player_id=player_id,
                        result=ProcessingResult.PLAYER_UNAVAILABLE,
                        bid_amount=claim.bid_amount,
                        winning_amount=None,
                        drop_player_id=claim.drop_player_id,
                        reason="Player not found",
                        processed_at=datetime.utcnow(),
                    )
                    for claim in claims
                ]

            # Check if player is already owned
            owned_by_team = self._check_player_ownership(league.league_id, player_id)
            if owned_by_team:
                return [
                    ProcessingOutcome(
                        bid_id=claim.bid_id,
                        team_id=claim.team_id,
                        player_id=player_id,
                        result=ProcessingResult.PLAYER_UNAVAILABLE,
                        bid_amount=claim.bid_amount,
                        winning_amount=None,
                        drop_player_id=claim.drop_player_id,
                        reason=f"Player already owned by {owned_by_team}",
                        processed_at=datetime.utcnow(),
                    )
                    for claim in claims
                ]

            # Process based on waiver type
            if waiver_type == WaiverType.FAAB:
                return await self._process_faab_claims(league, player_id, claims)
            elif waiver_type == WaiverType.BLIND_BID:
                return await self._process_blind_bid_claims(league, player_id, claims)
            else:  # Priority system
                return await self._process_priority_claims(league, player_id, claims)

        except Exception as e:
            logger.error(f"Failed to process claims for player {player_id}: {e}")
            return [
                ProcessingOutcome(
                    bid_id=claim.bid_id,
                    team_id=claim.team_id,
                    player_id=player_id,
                    result=ProcessingResult.PLAYER_UNAVAILABLE,
                    bid_amount=claim.bid_amount,
                    winning_amount=None,
                    drop_player_id=claim.drop_player_id,
                    reason=f"Processing error: {e}",
                    processed_at=datetime.utcnow(),
                )
                for claim in claims
            ]

    async def _process_faab_claims(
        self,
        league: League,
        player_id: str,
        claims: List[WaiverClaim],
    ) -> List[ProcessingOutcome]:
        """Process FAAB (Free Agent Acquisition Budget) claims."""
        outcomes = []

        # Sort by bid amount (highest first), then by submission time (earliest first)
        claims.sort(key=lambda c: (-c.bid_amount, c.submitted_at))

        winning_claim = None
        winning_amount = 0.0

        # Find the winning claim
        for claim in claims:
            # Validate budget
            team = self.db.query(Team).filter(Team.team_id == claim.team_id).first()
            if not team:
                continue

            current_budget = team.waiver_budget or 0.0
            if current_budget < claim.bid_amount:
                outcomes.append(ProcessingOutcome(
                    bid_id=claim.bid_id,
                    team_id=claim.team_id,
                    player_id=player_id,
                    result=ProcessingResult.INSUFFICIENT_BUDGET,
                    bid_amount=claim.bid_amount,
                    winning_amount=None,
                    drop_player_id=claim.drop_player_id,
                    reason=f"Insufficient budget (have ${current_budget}, need ${claim.bid_amount})",
                    processed_at=datetime.utcnow(),
                ))
                continue

            # Validate roster space and drop player
            roster_valid, roster_error = await self._validate_roster_transaction(
                team, player_id, claim.drop_player_id
            )
            if not roster_valid:
                outcomes.append(ProcessingOutcome(
                    bid_id=claim.bid_id,
                    team_id=claim.team_id,
                    player_id=player_id,
                    result=ProcessingResult.ROSTER_FULL if "roster full" in roster_error.lower() else ProcessingResult.INVALID_DROP,
                    bid_amount=claim.bid_amount,
                    winning_amount=None,
                    drop_player_id=claim.drop_player_id,
                    reason=roster_error,
                    processed_at=datetime.utcnow(),
                ))
                continue

            # This claim wins
            winning_claim = claim
            winning_amount = claim.bid_amount
            break

        # Process all claims
        for claim in claims:
            if claim == winning_claim:
                outcomes.append(ProcessingOutcome(
                    bid_id=claim.bid_id,
                    team_id=claim.team_id,
                    player_id=player_id,
                    result=ProcessingResult.SUCCESSFUL,
                    bid_amount=claim.bid_amount,
                    winning_amount=winning_amount,
                    drop_player_id=claim.drop_player_id,
                    reason="Highest valid bid",
                    processed_at=datetime.utcnow(),
                ))
            else:
                reason = "Outbid" if winning_claim else "No valid bids"
                outcomes.append(ProcessingOutcome(
                    bid_id=claim.bid_id,
                    team_id=claim.team_id,
                    player_id=player_id,
                    result=ProcessingResult.OUTBID,
                    bid_amount=claim.bid_amount,
                    winning_amount=winning_amount if winning_claim else None,
                    drop_player_id=claim.drop_player_id,
                    reason=reason,
                    processed_at=datetime.utcnow(),
                ))

        return outcomes

    async def _process_blind_bid_claims(
        self,
        league: League,
        player_id: str,
        claims: List[WaiverClaim],
    ) -> List[ProcessingOutcome]:
        """Process blind bidding claims (second-price auction)."""
        # In blind bidding, winner pays the second-highest bid amount
        valid_claims = []

        # Validate all claims first
        for claim in claims:
            team = self.db.query(Team).filter(Team.team_id == claim.team_id).first()
            if not team:
                continue

            current_budget = team.waiver_budget or 0.0
            if current_budget < claim.bid_amount:
                continue

            roster_valid, _ = await self._validate_roster_transaction(
                team, player_id, claim.drop_player_id
            )
            if roster_valid:
                valid_claims.append(claim)

        if not valid_claims:
            return [
                ProcessingOutcome(
                    bid_id=claim.bid_id,
                    team_id=claim.team_id,
                    player_id=player_id,
                    result=ProcessingResult.PLAYER_UNAVAILABLE,
                    bid_amount=claim.bid_amount,
                    winning_amount=None,
                    drop_player_id=claim.drop_player_id,
                    reason="No valid bids",
                    processed_at=datetime.utcnow(),
                )
                for claim in claims
            ]

        # Sort by bid amount
        valid_claims.sort(key=lambda c: (-c.bid_amount, c.submitted_at))

        # Winner pays second-highest price (or minimum if only one bid)
        winning_claim = valid_claims[0]
        winning_amount = valid_claims[1].bid_amount if len(valid_claims) > 1 else winning_claim.bid_amount

        outcomes = []
        for claim in claims:
            if claim == winning_claim:
                outcomes.append(ProcessingOutcome(
                    bid_id=claim.bid_id,
                    team_id=claim.team_id,
                    player_id=player_id,
                    result=ProcessingResult.SUCCESSFUL,
                    bid_amount=claim.bid_amount,
                    winning_amount=winning_amount,
                    drop_player_id=claim.drop_player_id,
                    reason="Winning bid in blind auction",
                    processed_at=datetime.utcnow(),
                ))
            else:
                outcomes.append(ProcessingOutcome(
                    bid_id=claim.bid_id,
                    team_id=claim.team_id,
                    player_id=player_id,
                    result=ProcessingResult.OUTBID,
                    bid_amount=claim.bid_amount,
                    winning_amount=winning_amount,
                    drop_player_id=claim.drop_player_id,
                    reason="Outbid in blind auction",
                    processed_at=datetime.utcnow(),
                ))

        return outcomes

    async def _process_priority_claims(
        self,
        league: League,
        player_id: str,
        claims: List[WaiverClaim],
    ) -> List[ProcessingOutcome]:
        """Process traditional priority-based waiver claims."""
        # Sort by priority (lower number = higher priority)
        claims.sort(key=lambda c: (c.priority, c.submitted_at))

        outcomes = []
        winning_claim = None

        for claim in claims:
            team = self.db.query(Team).filter(Team.team_id == claim.team_id).first()
            if not team:
                continue

            # Validate roster transaction
            roster_valid, roster_error = await self._validate_roster_transaction(
                team, player_id, claim.drop_player_id
            )

            if roster_valid and not winning_claim:
                # This claim wins
                winning_claim = claim
                outcomes.append(ProcessingOutcome(
                    bid_id=claim.bid_id,
                    team_id=claim.team_id,
                    player_id=player_id,
                    result=ProcessingResult.SUCCESSFUL,
                    bid_amount=claim.bid_amount,
                    winning_amount=0.0,  # No cost in priority system
                    drop_player_id=claim.drop_player_id,
                    reason=f"Highest priority (#{claim.priority})",
                    processed_at=datetime.utcnow(),
                ))
            else:
                result = ProcessingResult.LOWER_PRIORITY
                reason = "Lower priority"

                if not roster_valid:
                    result = ProcessingResult.ROSTER_FULL if "roster full" in roster_error.lower() else ProcessingResult.INVALID_DROP
                    reason = roster_error

                outcomes.append(ProcessingOutcome(
                    bid_id=claim.bid_id,
                    team_id=claim.team_id,
                    player_id=player_id,
                    result=result,
                    bid_amount=claim.bid_amount,
                    winning_amount=None,
                    drop_player_id=claim.drop_player_id,
                    reason=reason,
                    processed_at=datetime.utcnow(),
                ))

        return outcomes

    # Helper methods

    def _is_processing_time(self, league: League, waiver_period: int) -> bool:
        """Check if it's time to process the waiver period."""
        waiver_settings = league.waiver_settings or {}

        # Default processing schedule: Wednesday mornings
        processing_day = waiver_settings.get("processing_day", 2)  # 0=Monday, 2=Wednesday
        processing_hour = waiver_settings.get("processing_hour", 9)  # 9 AM

        now = datetime.utcnow()

        # Simple check - in production this would be more sophisticated
        return (now.weekday() == processing_day and now.hour >= processing_hour)

    def _get_pending_claims(self, league_id: str, waiver_period: int) -> List[WaiverClaim]:
        """Get all pending waiver claims for a period."""
        try:
            bids = self.db.query(WaiverBid).filter(
                WaiverBid.league_id == league_id,
                WaiverBid.waiver_period == waiver_period,
                WaiverBid.status == "pending"
            ).all()

            return [
                WaiverClaim(
                    bid_id=bid.bid_id,
                    team_id=bid.team_id,
                    player_id=bid.player_id,
                    drop_player_id=bid.drop_player_id,
                    bid_amount=bid.bid_amount,
                    priority=bid.priority,
                    submitted_at=bid.created_at,
                    waiver_period=bid.waiver_period,
                )
                for bid in bids
            ]

        except Exception as e:
            logger.error(f"Failed to get pending claims: {e}")
            return []

    def _group_claims_by_player(self, claims: List[WaiverClaim]) -> Dict[str, List[WaiverClaim]]:
        """Group waiver claims by player ID."""
        groups = {}
        for claim in claims:
            if claim.player_id not in groups:
                groups[claim.player_id] = []
            groups[claim.player_id].append(claim)
        return groups

    def _check_player_ownership(self, league_id: str, player_id: str) -> Optional[str]:
        """Check if player is already owned by a team."""
        teams = self.db.query(Team).filter(Team.league_id == league_id).all()

        for team in teams:
            roster = team.roster or []
            for player in roster:
                if player.get("player_id") == player_id:
                    return team.team_id

        return None

    async def _validate_roster_transaction(
        self, team: Team, add_player_id: str, drop_player_id: Optional[str]
    ) -> Tuple[bool, str]:
        """Validate if roster transaction is valid."""
        try:
            roster = team.roster or []
            roster_size = len(roster)
            max_roster_size = 16  # Would come from league settings

            if drop_player_id:
                # Validate drop player exists on roster
                drop_player_exists = any(
                    p.get("player_id") == drop_player_id for p in roster
                )
                if not drop_player_exists:
                    return False, f"Drop player {drop_player_id} not found on roster"

                # Transaction is valid (1 in, 1 out)
                return True, "Valid drop transaction"
            else:
                # Adding without dropping
                if roster_size >= max_roster_size:
                    return False, f"Roster full ({roster_size}/{max_roster_size})"
                return True, "Valid add transaction"

        except Exception as e:
            return False, f"Validation error: {e}"

    async def _apply_processing_results(
        self,
        outcomes: List[ProcessingOutcome],
        budget_updates: Dict[str, float],
        roster_updates: Dict[str, List[Dict[str, any]]],
    ) -> None:
        """Apply all processing results to the database."""
        try:
            # Update team budgets
            for team_id, spent_amount in budget_updates.items():
                team = self.db.query(Team).filter(Team.team_id == team_id).first()
                if team:
                    current_budget = team.waiver_budget or 0.0
                    team.waiver_budget = current_budget - spent_amount

            # Update rosters
            sports_service = await get_sports_data_service()

            for team_id, updates in roster_updates.items():
                team = self.db.query(Team).filter(Team.team_id == team_id).first()
                if not team:
                    continue

                roster = team.roster or []

                for update in updates:
                    if update["action"] == "add":
                        # Remove dropped player if specified
                        if update["drop_player_id"]:
                            roster = [p for p in roster if p.get("player_id") != update["drop_player_id"]]

                        # Add new player
                        player_data = await sports_service.get_player_details(update["player_id"])
                        if player_data:
                            roster.append({
                                "player_id": update["player_id"],
                                "name": player_data.get("name"),
                                "position": player_data.get("position"),
                                "acquired_via": update["acquired_via"],
                                "acquired_date": datetime.utcnow().isoformat(),
                                "waiver_cost": update["cost"],
                            })

                team.roster = roster

            # Update waiver bid statuses
            for outcome in outcomes:
                bid = self.db.query(WaiverBid).filter(WaiverBid.bid_id == outcome.bid_id).first()
                if bid:
                    bid.status = "successful" if outcome.result == ProcessingResult.SUCCESSFUL else "failed"
                    bid.result_reason = outcome.reason
                    bid.processed_at = outcome.processed_at

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to apply processing results: {e}")
            self.db.rollback()
            raise

    async def _send_processing_notifications(
        self, league_id: str, outcomes: List[ProcessingOutcome], waiver_period: int
    ) -> int:
        """Send notifications for waiver processing results."""
        try:
            if not self.notification_service:
                self.notification_service = get_notification_service()

            notifications_sent = 0

            # Group outcomes by team
            team_outcomes = {}
            for outcome in outcomes:
                if outcome.team_id not in team_outcomes:
                    team_outcomes[outcome.team_id] = []
                team_outcomes[outcome.team_id].append(outcome)

            # Send notification to each team
            for team_id, team_outcomes_list in team_outcomes.items():
                team = self.db.query(Team).filter(Team.team_id == team_id).first()
                if not team or not team.owner_id:
                    continue

                successful_claims = [o for o in team_outcomes_list if o.result == ProcessingResult.SUCCESSFUL]
                failed_claims = [o for o in team_outcomes_list if o.result != ProcessingResult.SUCCESSFUL]

                # Build notification message
                title = f"Waiver Results - Period {waiver_period}"
                message_parts = []

                if successful_claims:
                    message_parts.append(f"✅ {len(successful_claims)} successful claim(s)")
                if failed_claims:
                    message_parts.append(f"❌ {len(failed_claims)} failed claim(s)")

                message = "; ".join(message_parts)

                await self.notification_service.send_notification(
                    user_id=str(team.owner_id),
                    notification_type="waiver_results",
                    title=title,
                    message=message,
                    data={
                        "league_id": league_id,
                        "waiver_period": waiver_period,
                        "successful_claims": len(successful_claims),
                        "failed_claims": len(failed_claims),
                        "outcomes": [
                            {
                                "player_id": o.player_id,
                                "result": o.result.value,
                                "reason": o.reason,
                            }
                            for o in team_outcomes_list
                        ],
                    },
                )
                notifications_sent += 1

            return notifications_sent

        except Exception as e:
            logger.error(f"Failed to send processing notifications: {e}")
            return 0


# Global processor factory
def create_waiver_processor(db_session: Session) -> WaiverProcessor:
    """Create a waiver processor instance with database session."""
    return WaiverProcessor(db_session)