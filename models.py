from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gmail_message_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    gmail_thread_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sender: Mapped[str] = mapped_column(String(512))
    subject: Mapped[str] = mapped_column(String(998), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    category: Mapped[str] = mapped_column(String(64))
    priority: Mapped[str] = mapped_column(String(16))
    sentiment: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(Text)
    requires_response: Mapped[bool] = mapped_column(Boolean)
    classified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
