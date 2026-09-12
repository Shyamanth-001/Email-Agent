import os

from collections.abc import Generator
from email.utils import parsedate_to_datetime

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ai.classifier import classify_email
from database import SessionLocal, init_database
from gmail.email_parser import extract_email_content
from gmail.gmail_service import (
    get_gmail_service,
    get_added_message_ids,
    get_message,
)
from gmail.pubsub import parse_pubsub_notification
from models import Email
from repository import save_classified_email
from api.schemas import EmailResponse, StatsResponse


app = FastAPI(
    title="Email Classifier API",
    version="3.0.0",
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# Configuration
# ==================================================

HISTORY_ID_FILE = "gmail_history_id.txt"


# ==================================================
# Startup
# ==================================================

@app.on_event("startup")
def create_tables() -> None:
    init_database()


# ==================================================
# Database dependency
# ==================================================

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ==================================================
# Gmail utility functions
# ==================================================

def get_headers(message: dict) -> dict[str, str]:
    """
    Convert Gmail headers into a dictionary.
    """

    return {
        header["name"].lower(): header["value"]
        for header in message["payload"].get(
            "headers",
            [],
        )
    }


def parse_received_at(value: str | None):
    """
    Convert Gmail Date header into datetime.
    """

    if not value:
        return None

    try:
        return parsedate_to_datetime(value)

    except (
        TypeError,
        ValueError,
        IndexError,
    ):
        return None


# ==================================================
# Gmail history ID storage
# ==================================================

def load_history_id():
    """
    Load the last processed Gmail history ID.
    """

    if not os.path.exists(HISTORY_ID_FILE):
        return None

    with open(
        HISTORY_ID_FILE,
        "r",
    ) as file:

        value = file.read().strip()

    return value if value else None


def save_history_id(history_id):
    """
    Save the latest Gmail history ID.
    """

    with open(
        HISTORY_ID_FILE,
        "w",
    ) as file:

        file.write(str(history_id))


# ==================================================
# Process one Gmail message
# ==================================================

def process_single_message(
    service,
    db,
    message_id: str,
):
    """
    Fetch, parse, classify and save one Gmail message.
    """

    print("\n" + "=" * 60)
    print("PROCESSING MESSAGE")
    print("=" * 60)

    print("Message ID:", message_id)

    # ------------------------------------------------
    # Fetch complete Gmail message
    # ------------------------------------------------

    message = get_message(
        service,
        message_id,
    )

    # ------------------------------------------------
    # Extract headers
    # ------------------------------------------------

    headers = get_headers(message)

    sender = headers.get(
        "from",
        "",
    )

    subject = headers.get(
        "subject",
        "",
    )

    # ------------------------------------------------
    # Extract body
    # ------------------------------------------------

    content = extract_email_content(
        message["payload"],
    )

    body = content["body"]

    print("Thread ID:", message.get("threadId"))
    print("FROM:", sender)
    print("SUBJECT:", subject)

    # ------------------------------------------------
    # Check whether already processed
    # ------------------------------------------------

    existing_email = (
        db.query(Email.id)
        .filter_by(
            gmail_message_id=message_id,
        )
        .first()
    )

    if existing_email:

        print(
            "Skipped already-saved message:",
            message_id,
        )

        return False

    # ------------------------------------------------
    # Classify with Groq
    # ------------------------------------------------

    print("Classifying email with Groq...")

    classification = classify_email(
        subject=subject,
        body=body,
    )

    print("\nAI CLASSIFICATION")
    print("-" * 30)

    print(
        "Category:",
        classification.category,
    )

    print(
        "Priority:",
        classification.priority,
    )

    print(
        "Sentiment:",
        classification.sentiment,
    )

    print(
        "Summary:",
        classification.summary,
    )

    print(
        "Requires response:",
        classification.requires_response,
    )

    # ------------------------------------------------
    # Save to PostgreSQL
    # ------------------------------------------------

    email, created = save_classified_email(
        db,

        gmail_message_id=message_id,

        gmail_thread_id=message.get(
            "threadId",
        ),

        sender=sender,

        subject=subject,

        body=body,

        received_at=parse_received_at(
            headers.get("date"),
        ),

        classification=classification,
    )

    if created:

        print(
            "Saved:",
            email.subject or "(no subject)",
        )

    else:

        print(
            "Skipped:",
            email.subject or "(no subject)",
        )

    return created


# ==================================================
# Process Gmail history
# ==================================================

def process_history(
    service,
    previous_history_id: str,
):
    """
    Find messages added after previous_history_id
    and process them.
    """

    print("\n" + "=" * 60)
    print("PROCESSING GMAIL HISTORY")
    print("=" * 60)

    print(
        "Starting history ID:",
        previous_history_id,
    )

    # ------------------------------------------------
    # Get newly added messages
    # ------------------------------------------------

    message_ids = get_added_message_ids(
        service,
        previous_history_id,
    )

    print(
        "New messages found:",
        len(message_ids),
    )

    if not message_ids:
        return

    # ------------------------------------------------
    # Database
    # ------------------------------------------------

    with SessionLocal() as db:

        for message_id in message_ids:

            process_single_message(
                service,
                db,
                message_id,
            )


# ==================================================
# Root endpoint
# ==================================================

@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Email Classifier API",
    }


# ==================================================
# Gmail Pub/Sub webhook
# ==================================================

@app.post("/gmail/webhook")
async def gmail_webhook(
    request: Request,
):
    """
    Receive Gmail notifications forwarded by
    Google Pub/Sub.
    """

    print("\n" + "=" * 60)
    print("PUB/SUB NOTIFICATION RECEIVED")
    print("=" * 60)

    # ------------------------------------------------
    # Receive Pub/Sub request
    # ------------------------------------------------

    pubsub_data = await request.json()

    print("Pub/Sub payload:")
    print(pubsub_data)

    # ------------------------------------------------
    # Extract Pub/Sub message
    # ------------------------------------------------

    message = pubsub_data.get("message")

    if not message:

        print("No Pub/Sub message found.")

        return {
            "status": "ignored",
        }

    # ------------------------------------------------
    # Extract encoded Gmail notification
    # ------------------------------------------------

    encoded_data = message.get("data")

    if not encoded_data:

        print("No data found in Pub/Sub message.")

        return {
            "status": "ignored",
        }

    # ------------------------------------------------
    # Decode Gmail notification
    # ------------------------------------------------

    notification = parse_pubsub_notification(
        encoded_data,
    )

    if not notification:

        print("Unable to decode Gmail notification.")

        return {
            "status": "ignored",
        }

    email_address = notification.get(
        "emailAddress",
    )

    new_history_id = notification.get(
        "historyId",
    )

    print("\nGMAIL NOTIFICATION")
    print("-" * 30)

    print(
        "Email:",
        email_address,
    )

    print(
        "History ID:",
        new_history_id,
    )

    if not new_history_id:

        print("No history ID found.")

        return {
            "status": "ignored",
        }

    # ------------------------------------------------
    # Load previous history ID
    # ------------------------------------------------

    previous_history_id = load_history_id()

    # ------------------------------------------------
    # First notification
    # ------------------------------------------------

    if not previous_history_id:

        print(
            "No previous history ID exists."
        )

        print(
            "Saving current history ID."
        )

        save_history_id(
            new_history_id,
        )

        return {
            "status": "initialized",
            "history_id": new_history_id,
        }

    # ------------------------------------------------
    # Gmail service
    # ------------------------------------------------

    service = get_gmail_service()

    # ------------------------------------------------
    # Process Gmail history
    # ------------------------------------------------

    try:

        process_history(
            service,
            previous_history_id,
        )

        # --------------------------------------------
        # Only save new history ID after successful
        # processing.
        # --------------------------------------------

        save_history_id(
            new_history_id,
        )

        print(
            "History ID updated:",
            new_history_id,
        )

    except Exception as err:

        print(
            "\nERROR processing Gmail history:"
        )

        print(err)

        # Returning an exception causes FastAPI to
        # return a 500 response. Pub/Sub can then
        # retry the notification.

        raise

    return {
        "status": "ok",
        "history_id": new_history_id,
    }


# ==================================================
# React API — Emails
# ==================================================

@app.get(
    "/emails",
    response_model=list[EmailResponse],
)
def list_emails(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),

    db: Session = Depends(get_db),
) -> list[Email]:

    return list(
        db.scalars(
            select(Email)
            .order_by(
                Email.classified_at.desc(),
                Email.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
    )


# ==================================================
# React API — Single email
# ==================================================

@app.get(
    "/emails/{email_id}",
    response_model=EmailResponse,
)
def get_email(
    email_id: int,
    db: Session = Depends(get_db),
) -> Email:

    email = db.get(
        Email,
        email_id,
    )

    if email is None:

        raise HTTPException(
            status_code=404,
            detail="Email not found",
        )

    return email


# ==================================================
# React API — Statistics
# ==================================================

@app.get(
    "/stats",
    response_model=StatsResponse,
)
def get_stats(
    db: Session = Depends(get_db),
) -> StatsResponse:

    total = (
        db.scalar(
            select(func.count())
            .select_from(Email)
        )
        or 0
    )

    needs_reply = (
        db.scalar(
            select(func.count())
            .select_from(Email)
            .where(
                Email.requires_response.is_(True)
            )
        )
        or 0
    )

    categories = dict(
        db.execute(
            select(
                Email.category,
                func.count(),
            )
            .group_by(
                Email.category,
            )
        ).all()
    )

    priorities = dict(
        db.execute(
            select(
                Email.priority,
                func.count(),
            )
            .group_by(
                Email.priority,
            )
        ).all()
    )

    return StatsResponse(
        total_emails=total,
        requires_response=needs_reply,
        by_category=categories,
        by_priority=priorities,
    )