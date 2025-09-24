"""Add username column to users table

Revision ID: 20250921_000002
Revises: 20250921_000001
Create Date: 2025-09-21 21:00:00.000000

This migration adds the missing username column to the users table
that is expected by the JWT generation code but was not included
in the original schema.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250921_000002"
down_revision = "20250913_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Recreate users table with complete schema including username column."""
    connection = op.get_bind()

    # Since there are no users in the table, we can safely recreate it with the complete schema
    # This is simpler than trying to add all the missing columns one by one

    # Create the complete users table with all required columns
    connection.execute(sa.text("""
        CREATE TABLE users_new (
            user_id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            cognito_sub VARCHAR(128),
            password_hash VARCHAR(255) NOT NULL,
            is_email_verified BOOLEAN NOT NULL DEFAULT 0,
            email_verification_token VARCHAR(255),
            password_reset_token VARCHAR(255),
            password_reset_expires DATETIME,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            display_name VARCHAR(100),
            bio VARCHAR(500),
            avatar_url VARCHAR(500),
            phone_number VARCHAR(20),
            timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
            country VARCHAR(2),
            is_active BOOLEAN NOT NULL DEFAULT 1,
            is_premium BOOLEAN NOT NULL DEFAULT 0,
            premium_expires_at DATETIME,
            preferences TEXT,
            notification_settings TEXT,
            privacy_settings TEXT,
            last_login_at DATETIME,
            last_active_at DATETIME,
            login_count INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """))

    # Copy any existing data from old table to new table (though there should be none)
    # We'll create a default user if the old table had any data
    old_users = connection.execute(sa.text("SELECT * FROM users")).fetchall()
    if old_users:
        for old_user in old_users:
            # Create a username from email if it doesn't exist
            username = old_user[6] if len(old_user) > 6 and old_user[6] else None
            if not username and len(old_user) > 1:
                username = old_user[1].split('@')[0].lower()  # Use email prefix

            connection.execute(sa.text("""
                INSERT INTO users_new (
                    user_id, username, email, cognito_sub, display_name,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """), {
                'user_id': old_user[0],
                'username': username,
                'email': old_user[1],
                'cognito_sub': old_user[3],
                'display_name': old_user[2],
                'created_at': old_user[4],
                'updated_at': old_user[5]
            })

    # Drop old table and rename new table
    connection.execute(sa.text("DROP TABLE users"))
    connection.execute(sa.text("ALTER TABLE users_new RENAME TO users"))

    # Create indexes
    op.create_index('idx_user_username', 'users', ['username'], unique=True)
    op.create_index('idx_user_email', 'users', ['email'], unique=True)
    op.create_index('idx_user_cognito_sub', 'users', ['cognito_sub'], unique=True)


def downgrade() -> None:
    """Remove username column from users table."""
    op.drop_index('idx_user_username', table_name='users')
    op.drop_column('users', 'username')