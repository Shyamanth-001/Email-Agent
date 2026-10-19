from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gmail_message_id: str
    gmail_thread_id: str | None = None
    user_id: int | None = None
    sender: str
    subject: str
    body: str
    received_at: datetime | None = None
    category: str
    priority: str
    sentiment: str
    summary: str
    requires_response: bool
    classified_at: datetime


class StatsResponse(BaseModel):
    total: int
    total_emails: int
    requires_response: int
    by_category: dict[str, int]
    by_priority: dict[str, int]
    categories: dict[str, int]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str | None = None
    id_token: str | None = None
    google_token: str | None = None
    gmail_refresh_token: str | None = None

    def get_token(self) -> str | None:
        return self.credential or self.id_token or self.google_token


class GoogleCodeRequest(BaseModel):
    code: str


class ConnectGmailTokenRequest(BaseModel):
    gmail_refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str = ""
    picture: str | None = None
    is_active: bool = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
