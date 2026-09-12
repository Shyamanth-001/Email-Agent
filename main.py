import os
import sys

from dotenv import load_dotenv

from gmail.gmail_service import (
    get_gmail_service,
    create_gmail_watch,
)

load_dotenv()


GMAIL_PUBSUB_TOPIC = os.getenv("GMAIL_PUBSUB_TOPIC")


def setup_gmail_watch():
    if not GMAIL_PUBSUB_TOPIC:
        print("GMAIL_PUBSUB_TOPIC is not set.")
        print(
            "Example:"
            " GMAIL_PUBSUB_TOPIC="
            "projects/YOUR_PROJECT_ID/"
            "topics/gmail-notifications"
        )
        return

    print("Creating Gmail Watch...")

    service = get_gmail_service()

    response = create_gmail_watch(
        service,
        GMAIL_PUBSUB_TOPIC,
    )

    print("\nGMAIL WATCH CREATED")
    print("-" * 30)

    print(
        "History ID:",
        response.get("historyId"),
    )

    print(
        "Expiration:",
        response.get("expiration"),
    )

    print("\nGmail is now watching for changes.")


def main():
    if "--watch" in sys.argv:
        setup_gmail_watch()
    else:
        print("Usage:")
        print("  python main.py --watch")


if __name__ == "__main__":
    main()