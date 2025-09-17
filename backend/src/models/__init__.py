"""SQLAlchemy models package.

Models are added in tasks T009-T021.
"""

from .base import Base
from .notification import Notification
from .player import Player
from .preset import Preset
from .roster import Roster
from .rule import Rule
from .schedule import Schedule

# Domain models are now in their respective domains
from domains.leagues.models.league import League
from domains.leagues.models.league_branding import LeagueBranding
from domains.leagues.models.team import Team
from domains.lineups.models.lineup import Lineup
from domains.scoring.models.score import Score
from domains.trading.models.transaction import Transaction
from domains.trading.models.waiver import Waiver
from domains.users.models.user import User
from domains.users.models.user_preference import UserPreference
from domains.waitlist.models.waitlist import Waitlist

__all__ = [
    "Base",
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
    "Transaction",
    "User",
    "UserPreference",
    "Waitlist",
    "Waiver",
]
