"""Initial schema

Revision ID: da38e983d495
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "da38e983d495"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("google_id", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("picture", sa.String(length=1000), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("gmail_refresh_token", sa.Text(), nullable=True),
        sa.Column("gmail_history_id", sa.String(length=64), nullable=True),
        sa.Column(
            "gmail_watch_expiration",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_users_google_id",
        "users",
        ["google_id"],
        unique=True,
    )
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    # 2. Refresh tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("replaced_by_token_id", sa.Integer(), nullable=True),
        sa.Column("token_family_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["replaced_by_token_id"],
            ["refresh_tokens.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_tokens_token_hash",
        "refresh_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_refresh_tokens_token_family_id",
        "refresh_tokens",
        ["token_family_id"],
        unique=False,
    )

    # 3. Emails
    op.create_table(
        "emails",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("gmail_message_id", sa.String(length=128), nullable=False),
        sa.Column("gmail_thread_id", sa.String(length=128), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("sender", sa.String(length=512), nullable=False),
        sa.Column("subject", sa.String(length=998), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("sentiment", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("requires_response", sa.Boolean(), nullable=False),
        sa.Column(
            "classified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "gmail_message_id",
            name="uq_user_gmail_message",
        ),
    )

    op.create_index(
        "ix_emails_gmail_message_id",
        "emails",
        ["gmail_message_id"],
        unique=False,
    )
    op.create_index(
        "ix_emails_user_id",
        "emails",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_emails_user_id", table_name="emails")
    op.drop_index("ix_emails_gmail_message_id", table_name="emails")
    op.drop_table("emails")

    op.drop_index(
        "ix_refresh_tokens_token_family_id",
        table_name="refresh_tokens",
    )
    op.drop_index(
        "ix_refresh_tokens_token_hash",
        table_name="refresh_tokens",
    )
    op.drop_index(
        "ix_refresh_tokens_user_id",
        table_name="refresh_tokens",
    )
    op.drop_table("refresh_tokens")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_table("users")