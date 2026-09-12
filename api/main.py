from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import SessionLocal, init_database
from models import Email
from api.schemas import EmailResponse, StatsResponse

app = FastAPI(title="Email Classifier API", version="3.0.0")


@app.on_event("startup")
def create_tables() -> None:
    init_database()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/emails", response_model=list[EmailResponse])
def list_emails(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Email]:
    return list(
        db.scalars(
            select(Email)
            .order_by(Email.classified_at.desc(), Email.id.desc())
            .offset(offset)
            .limit(limit)
        )
    )


@app.get("/emails/{email_id}", response_model=EmailResponse)
def get_email(email_id: int, db: Session = Depends(get_db)) -> Email:
    email = db.get(Email, email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@app.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    total = db.scalar(select(func.count()).select_from(Email)) or 0
    needs_reply = (
        db.scalar(
            select(func.count()).select_from(Email).where(Email.requires_response.is_(True))
        )
        or 0
    )
    categories = dict(
        db.execute(select(Email.category, func.count()).group_by(Email.category)).all()
    )
    priorities = dict(
        db.execute(select(Email.priority, func.count()).group_by(Email.priority)).all()
    )
    return StatsResponse(
        total_emails=total,
        requires_response=needs_reply,
        by_category=categories,
        by_priority=priorities,
    )
