"""Add is_admin column to users table

Revision ID: 20250921_000003
Revises: 20250921_000002
Create Date: 2025-09-21 00:00:03.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250921_000003'
down_revision = '20250921_000002'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    # Remove is_admin column from users table
    op.drop_column('users', 'is_admin')