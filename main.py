import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

from database import SessionLocal, init_database
from models import User
from gmail.gmail_service import (
    get_gmail_service,
    get_gmail_service_for_user,
    create_gmail_watch,
)

# ==================================================
# Environment & Configuration
# ==================================================

load_dotenv()

GMAIL_PUBSUB_TOPIC = os.getenv("GMAIL_PUBSUB_TOPIC")


# ==================================================
# Multi-User Gmail Watch Setup
# ==================================================

def setup_gmail_watch() -> None:
    if not GMAIL_PUBSUB_TOPIC:
        print("GMAIL_PUBSUB_TOPIC is not set in environment variables.")
        print("Example: GMAIL_PUBSUB_TOPIC=projects/YOUR_PROJECT_ID/topics/gmail-notifications")
        return

    print("Initializing database connection...")
    init_database()
    db = SessionLocal()

    try:
        users = db.query(User).filter(User.is_active == True).all()
        users_with_tokens = [u for u in users if u.gmail_refresh_token]

        if users_with_tokens:
            print(f"\nFound {len(users_with_tokens)} user(s) with stored Gmail refresh tokens.")
            for user in users_with_tokens:
                print(f"\nCreating Gmail Watch for user: {user.email}...")
                try:
                    service = get_gmail_service_for_user(user.gmail_refresh_token)
                    response = create_gmail_watch(service, GMAIL_PUBSUB_TOPIC)
                    history_id = response.get("historyId")
                    expiration = response.get("expiration")

                    if history_id:
                        user.gmail_history_id = str(history_id)
                        if expiration:
                            user.gmail_watch_expiration = datetime.fromtimestamp(
                                int(expiration) / 1000.0, tz=timezone.utc
                            )
                        db.commit()
                        print(f"GMAIL WATCH CREATED for {user.email}")
                        print(f"  History ID: {history_id}")
                        print(f"  Expiration: {user.gmail_watch_expiration}")
                except Exception as error:
                    print(f"Failed to create Gmail Watch for {user.email}: {error}")
        else:
            print("\nNo active users with stored Gmail refresh tokens found in database.")
            print("Users can sign in via the web interface to connect their Gmail account.")
    finally:
        db.close()


def main():
    if "--watch" in sys.argv:
        setup_gmail_watch()
    else:
        print("Usage:")
        print("  python main.py --watch")


if __name__ == "__main__":
    main()