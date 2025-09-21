"""SQLAlchemy models package.

Models are added in tasks T009-T021.
"""

# Domain models are now in their respective domains
from domains.leagues.models.league import League
from domains.leagues.models.league_branding import LeagueBranding
from domains.leagues.models.team import Team
from domains.lineups.models.lineup import Lineup
from domains.scoring.models.score import Score
from domains.sports.models.player import Player
from domains.shared.models.achievement import Achievement
from domains.shared.models.base import Base
from domains.trading.models.trade import Trade
from domains.trading.models.transaction import Transaction
from domains.trading.models.waiver import Waiver
from domains.users.models.user import User
from domains.users.models.user_preference import UserPreference
from domains.waitlist.models.waitlist import Waitlist

from .chat_message import ChatMessage
from .draft import Draft
from .notification import Notification
from .preset import Preset
from .roster import Roster
from .rule import Rule
from .schedule import Schedule
from .trade import Trade
from .waiver_bid import WaiverBid

__all__ = [
    "Achievement",
    "Base",
    "ChatMessage",
    "Draft",
    "League",
    "LeagueBranding",
    "Lineup",
    "Notification",
    "Player",
    "Preset",
    "Roster",
    "Rule",
    "Schedule",
    "Score",
    "Team",
    "Trade",
    "Transaction",
    "User",
    "UserPreference",
    "WaiverBid",
    "Waitlist",
    "Waiver",
]
