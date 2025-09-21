"""Common API response wrappers."""

from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Simple envelope used by legacy endpoints."""

    success: bool
    data: T
    message: Optional[str] = None


__all__ = ["APIResponse"]
