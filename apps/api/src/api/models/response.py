"""Common API response wrappers."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Simple envelope used by legacy endpoints."""

    success: bool
    data: T
    message: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response format."""

    success: bool = False
    error: str
    message: str
    details: dict | None = None


__all__ = ["APIResponse", "ErrorResponse"]
