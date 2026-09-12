import sys
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

from ai.classifier import classify_email
from database import SessionLocal, init_database
from gmail.email_parser import extract_email_content
from gmail.gmail_service import get_gmail_service
from repository import save_classified_email


def get_headers(message: dict) -> dict[str, str]:
    return {
        header["name"].lower(): header["value"]
        for header in message["payload"].get("headers", [])
    }


def get_recent_emails(service, max_results: int = 5) -> list[dict]:
    response = service.users().messages().list(
        userId="me", q="in:inbox is:unread newer_than:7d", maxResults=max_results
    ).execute()
    return response.get("messages", [])


def parse_received_at(value: str | None):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None


def process_emails() -> None:
    init_database()
    service = get_gmail_service()
    messages = get_recent_emails(service)

    with SessionLocal() as db:
        for item in messages:
            message = service.users().messages().get(
                userId="me", id=item["id"], format="full"
            ).execute()
            headers = get_headers(message)
            content = extract_email_content(message["payload"])

            # Skip the LLM call too: reruns should be cheap and idempotent.
            from models import Email
            if db.query(Email.id).filter_by(gmail_message_id=message["id"]).first():
                print(f"Skipped already-saved message: {message['id']}")
                continue

            classification = classify_email(
                subject=headers.get("subject", ""), body=content["body"]
            )
            email, created = save_classified_email(
                db,
                gmail_message_id=message["id"],
                gmail_thread_id=message.get("threadId"),
                sender=headers.get("from", ""),
                subject=headers.get("subject", ""),
                body=content["body"],
                received_at=parse_received_at(headers.get("date")),
                classification=classification,
            )
            print(f"{'Saved' if created else 'Skipped'}: {email.subject or '(no subject)'}")


def run_loop(interval_seconds: int = 180) -> None:
    """Run continuously, checking for new emails every interval_seconds (default 5 min)."""
    minutes = interval_seconds // 60
    print(f"🚀 Starting continuous email monitor (checking every {minutes} min). Press Ctrl+C to stop.\n")
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Checking for unread emails...")
        try:
            process_emails()
        except Exception as err:
            print(f"[{timestamp}] Error during email check: {err}")
        print(f"Sleeping for {minutes} minutes...\n")
        time.sleep(interval_seconds)


def main() -> None:
    if "--loop" in sys.argv:
        run_loop(interval_seconds=180)
    else:
        process_emails()


if __name__ == "__main__":
    main()

