from __future__ import annotations

import uuid as _uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user_id, get_db
from domains.users.models.user_preference import UserPreference

router = APIRouter()


class PreferencesIn(BaseModel):
    theme: str = Field("light")
    density: str = Field("comfortable")
    locale: str = Field("en-US")
    layouts: dict | None = None


class PreferencesOut(PreferencesIn):
    user_id: _uuid.UUID


@router.get(
    "/me/preferences", status_code=status.HTTP_200_OK, response_model=PreferencesOut
)
def get_my_preferences(
    user_id: _uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> PreferencesOut:
    """
    Get the preferences for the current user.

    This endpoint retrieves the application preferences for the authenticated user,
    including their selected theme, density, locale, and custom layouts.

    If no preferences have been set for the user, it returns a default set of
    preferences.
    """
    row = (
        db.query(UserPreference).filter(UserPreference.user_id == user_id).one_or_none()
    )
    if not row:
        return PreferencesOut(
            user_id=user_id,
            theme="light",
            density="comfortable",
            locale="en-US",
            layouts=None,
        )
    return PreferencesOut(
        user_id=row.user_id,
        theme=row.theme,
        density=row.density,
        locale=row.locale,
        layouts=row.layouts,
    )


@router.put(
    "/me/preferences", status_code=status.HTTP_200_OK, response_model=PreferencesOut
)
def put_my_preferences(
    payload: PreferencesIn,
    user_id: _uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> PreferencesOut:
    """
    Update the preferences for the current user.

    This endpoint allows an authenticated user to set or update their application
    preferences.

    - **theme**: The name of the UI theme (e.g., 'light', 'dark').
    - **density**: The UI density (e.g., 'comfortable', 'compact').
    - **locale**: The user's preferred locale (e.g., 'en-US').
    - **layouts**: A dictionary to store custom UI layout configurations.
    """
    row = (
        db.query(UserPreference).filter(UserPreference.user_id == user_id).one_or_none()
    )
    if not row:
        row = UserPreference(user_id=user_id)
        db.add(row)
    row.theme = payload.theme
    row.density = payload.density
    row.locale = payload.locale
    row.layouts = payload.layouts
    db.flush()
    return PreferencesOut(
        user_id=row.user_id,
        theme=row.theme,
        density=row.density,
        locale=row.locale,
        layouts=row.layouts,
    )
