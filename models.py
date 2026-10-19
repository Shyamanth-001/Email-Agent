from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    google_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    picture: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    gmail_refresh_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    gmail_history_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    gmail_watch_expiration: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    emails: Mapped[list["Email"]] = relationship(
        back_populates="user"
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    replaced_by_token_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("refresh_tokens.id"),
        nullable=True,
    )

    token_family_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="refresh_tokens",
    )


class Email(Base):
    __tablename__ = "emails"

    __table_args__ = (
        UniqueConstraint("user_id", "gmail_message_id", name="uq_user_gmail_message"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    gmail_message_id: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )

    gmail_thread_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    sender: Mapped[str] = mapped_column(
        String(512)
    )

    subject: Mapped[str] = mapped_column(
        String(998),
        default=""
    )

    body: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    category: Mapped[str] = mapped_column(
        String(64)
    )

    priority: Mapped[str] = mapped_column(
        String(16)
    )

    sentiment: Mapped[str] = mapped_column(
        String(32)
    )

    summary: Mapped[str] = mapped_column(
        Text
    )

    requires_response: Mapped[bool] = mapped_column(
        Boolean
    )

    classified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped["User | None"] = relationship(
        back_populates="emails"
    )