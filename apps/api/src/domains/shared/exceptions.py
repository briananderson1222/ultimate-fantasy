"""Shared domain-level exception definitions."""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for domain-layer errors."""


# Authentication / User related
class AuthenticationError(DomainError):
    """Authentication failure."""


class TokenExpiredError(AuthenticationError):
    """Token has expired."""


class InvalidTokenError(AuthenticationError):
    """Token is invalid or malformed."""


class AccountDisabledError(AuthenticationError):
    """Account is disabled."""


class TooManyAttemptsError(AuthenticationError):
    """Too many failed attempts."""


class WeakPasswordError(DomainError):
    """Password strength requirements not met."""


class EmailAlreadyExistsError(DomainError):
    """Email already registered."""


class UsernameAlreadyExistsError(DomainError):
    """Username already registered."""


class UserNotFoundError(DomainError):
    """User entity not found."""


# League / Team related
class LeagueError(DomainError):
    """Base league error."""


class LeagueNotFoundError(LeagueError):
    """League not found."""


class LeagueFullError(LeagueError):
    """League at capacity."""


class LeagueValidationError(LeagueError):
    """Invalid league configuration."""


class InvalidInviteCodeError(LeagueError):
    """Invite code invalid."""


class AlreadyInLeagueError(LeagueError):
    """User already a league member."""


class CommissionerOnlyError(LeagueError):
    """Action restricted to commissioner."""


class InsufficientPermissionsError(LeagueError):
    """User lacks permissions."""


class DeadlinePassedError(LeagueError):
    """Action attempted past deadline."""


# Lineup
class LineupNotFoundError(DomainError):
    """Lineup not found."""


class LineupValidationError(DomainError):
    """Invalid lineup configuration."""


class OptimisticLockError(DomainError):
    """Version conflict occurred."""


class InvalidRosterError(DomainError):
    """Roster violates configuration."""


class LineupLockedError(DomainError):
    """Lineup is locked."""


# Player / Sports
class PlayerNotFoundError(DomainError):
    """Player not found."""


class ProviderError(DomainError):
    """External provider failure."""


class ValidationError(DomainError):
    """Generic validation failure."""


# Trading / Waivers
class TradeNotFoundError(DomainError):
    """Trade not found."""


class InvalidTradeError(DomainError):
    """Trade request is invalid."""


class TradeExpiredError(DomainError):
    """Trade can no longer be acted on due to expiration."""


class TradeAlreadyProcessedError(DomainError):
    """Trade has already been processed."""


class WaiverNotFoundError(DomainError):
    """Waiver not found."""


class InvalidWaiverError(DomainError):
    """Invalid waiver request."""


class RateLimitExceededError(DomainError):
    """Operation exceeds configured rate limit."""


__all__ = [
    "DomainError",
    "AuthenticationError",
    "TokenExpiredError",
    "InvalidTokenError",
    "AccountDisabledError",
    "TooManyAttemptsError",
    "WeakPasswordError",
    "EmailAlreadyExistsError",
    "UsernameAlreadyExistsError",
    "UserNotFoundError",
    "LeagueError",
    "LeagueNotFoundError",
    "LeagueFullError",
    "LeagueValidationError",
    "InvalidInviteCodeError",
    "AlreadyInLeagueError",
    "CommissionerOnlyError",
    "InsufficientPermissionsError",
    "DeadlinePassedError",
    "LineupNotFoundError",
    "LineupValidationError",
    "OptimisticLockError",
    "InvalidRosterError",
    "PlayerNotFoundError",
    "ProviderError",
    "ValidationError",
    "TradeNotFoundError",
    "InvalidTradeError",
    "TradeExpiredError",
    "TradeAlreadyProcessedError",
    "WaiverNotFoundError",
    "InvalidWaiverError",
    "RateLimitExceededError",
]
