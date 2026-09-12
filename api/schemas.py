from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gmail_message_id: str
    gmail_thread_id: str | None
    sender: str
    subject: str
    body: str
    received_at: datetime | None
    category: str
    priority: str
    sentiment: str
    summary: str
    requires_response: bool
    classified_at: datetime


class StatsResponse(BaseModel):
    total_emails: int
    requires_response: int
    by_category: dict[str, int]
    by_priority: dict[str, int]
