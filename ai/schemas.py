from pydantic import BaseModel, Field
from typing import Literal


class EmailClassification(BaseModel):
    category: Literal[
        "technical_support",
        "billing",
        "sales",
        "order",
        "complaint",
        "general",
        "spam",
        "other"
    ]

    priority: Literal[
        "low",
        "medium",
        "high"
    ]

    sentiment: Literal[
        "positive",
        "neutral",
        "negative",
        "frustrated"
    ]

    summary: str = Field(
        description="A concise summary of the customer's email."
    )

    requires_response: bool