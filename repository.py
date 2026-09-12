"""Small persistence boundary; Gmail message ID makes repeated runs safe."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai.schemas import EmailClassification
from models import Email


def save_classified_email(
    db: Session,
    *,
    gmail_message_id: str,
    gmail_thread_id: str | None,
    sender: str,
    subject: str,
    body: str,
    received_at: datetime | None,
    classification: EmailClassification,
) -> tuple[Email, bool]:
    """Return (email, created). Existing Gmail messages are never reclassified/saved."""
    existing = db.scalar(
        select(Email).where(Email.gmail_message_id == gmail_message_id)
    )
    if existing:
        return existing, False

    email = Email(
        gmail_message_id=gmail_message_id,
        gmail_thread_id=gmail_thread_id,
        sender=sender,
        subject=subject,
        body=body,
        received_at=received_at,
        **classification.model_dump(),
    )
    db.add(email)
    try:
        db.commit()
    except IntegrityError:
        # A second worker may have saved this Gmail message after our first lookup.
        db.rollback()
        existing = db.scalar(
            select(Email).where(Email.gmail_message_id == gmail_message_id)
        )
        if existing:
            return existing, False
        raise

    db.refresh(email)
    return email, True
