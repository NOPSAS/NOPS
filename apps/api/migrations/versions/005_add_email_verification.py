"""add email_verified to users

Revision ID: 005
Revises: 004
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('users', sa.Column('email_verification_token', sa.String(128), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(128), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
