"""Backward-compatible import for League-related models."""

from domains.leagues.models.league import League
from domains.leagues.models.league_branding import LeagueBranding

__all__ = ["League", "LeagueBranding"]
