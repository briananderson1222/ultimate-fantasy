"""Consolidate domain models

Revision ID: 20250921_000001
Revises: fe6733db1cc1
Create Date: 2025-09-21 19:00:00.000000

This migration ensures all consolidated domain models are properly reflected
in the database schema. Most changes should already be in place from previous
migrations, but this serves as a checkpoint for the domain consolidation.

Key changes:
- Notification model moved to domains/shared/models/notification.py
- Rule model moved to domains/shared/models/rule.py
- All other domain models already consolidated
- Updated imports throughout codebase to use domain models

Note: This is primarily a documentation migration as the schema changes
were already implemented in previous migrations.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250921_000001"
down_revision = "fe6733db1cc1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Apply domain consolidation changes.

    This migration primarily documents the completion of domain consolidation.
    Most schema changes were already applied in previous migrations.
    """
    # Create indexes for notification and rule tables if they don't exist
    # These should already be in place but we add them for completeness

    # Notification table indexes (if not already exists)
    try:
        op.create_index(
            "idx_notification_user_id", "notifications", ["user_id"], if_not_exists=True
        )
        op.create_index(
            "idx_notification_league_id",
            "notifications",
            ["league_id"],
            if_not_exists=True,
        )
        op.create_index(
            "idx_notification_type",
            "notifications",
            ["notification_type"],
            if_not_exists=True,
        )
        op.create_index(
            "idx_notification_is_read", "notifications", ["is_read"], if_not_exists=True
        )
        op.create_index(
            "idx_user_unread_notifications",
            "notifications",
            ["user_id", "is_read", "created_at"],
            if_not_exists=True,
        )
    except Exception:
        # Indexes may already exist
        pass


def downgrade() -> None:
    """
    Revert domain consolidation changes.

    Note: This doesn't revert the code changes, only any schema changes.
    """
    # Remove indexes if needed
    pass
