import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# ==================================================
# Gmail OAuth & Configuration
# ==================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

BASE_DIR = os.getenv(
    "GMAIL_CREDENTIALS_DIR",
    ".",
)

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json",
)


# ==================================================
# Gmail Service
# ==================================================

def get_client_credentials() -> tuple[str | None, str | None]:
    """
    Load OAuth client ID and secret from environment variables or credentials.json.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    config = data.get("installed") or data.get("web") or {}
                    client_id = client_id or config.get("client_id")
                    client_secret = client_secret or config.get("client_secret")
            except Exception as error:
                print("Could not parse credentials.json:", error)

    return client_id, client_secret


def get_gmail_service_for_user(refresh_token: str):
    """
    Create an authenticated Gmail API service for a specific user given their refresh token.
    """
    if not refresh_token:
        raise ValueError("Refresh token cannot be empty")

    client_id, client_secret = get_client_credentials()

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    if creds.expired or not creds.valid:
        creds.refresh(Request())

    return build(
        "gmail",
        "v1",
        credentials=creds,
    )


# ==================================================
# Gmail History
# ==================================================

def get_added_message_ids(
    service,
    start_history_id: str,
) -> list[str]:
    """
    Get Gmail message IDs that were added after
    start_history_id.

    Handles pagination.

    Important:
        If Gmail returns 404 because the history ID
        is stale, the HttpError is intentionally
        allowed to propagate to api/main.py.
    """

    message_ids = []

    page_token = None

    while True:

        request = (
            service.users()
            .history()
            .list(
                userId="me",
                startHistoryId=str(
                    start_history_id
                ),
                historyTypes=[
                    "messageAdded"
                ],
                pageToken=page_token,
            )
        )

        response = request.execute()

        # ------------------------------------------------
        # Read history entries
        # ------------------------------------------------

        for history_item in response.get(
            "history",
            [],
        ):

            for added_message in history_item.get(
                "messagesAdded",
                [],
            ):

                message = added_message.get(
                    "message",
                    {},
                )

                message_id = message.get(
                    "id"
                )

                if message_id:

                    message_ids.append(
                        message_id
                    )

        # ------------------------------------------------
        # Pagination
        # ------------------------------------------------

        page_token = response.get(
            "nextPageToken"
        )

        if not page_token:
            break

    # ------------------------------------------------
    # Remove duplicates while preserving order
    # ------------------------------------------------

    return list(
        dict.fromkeys(
            message_ids
        )
    )


# ==================================================
# Gmail Message
# ==================================================

def get_message(
    service,
    message_id: str,
):
    """
    Fetch a complete Gmail message.
    """

    return (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full",
        )
        .execute()
    )


# ==================================================
# Gmail Watch
# ==================================================

def create_gmail_watch(
    service,
    topic_name: str,
):
    """
    Create or renew Gmail push notifications.

    Example topic:

        projects/YOUR_PROJECT_ID/topics/
        gmail-notifications
    """

    if not topic_name:

        raise ValueError(
            "Gmail Pub/Sub topic name cannot be empty."
        )

    response = (
        service.users()
        .watch(
            userId="me",
            body={
                "topicName": topic_name,
                "labelIds": [
                    "INBOX"
                ],
                "labelFilterBehavior": "INCLUDE",
            },
        )
        .execute()
    )

    return response




def get_gmail_service(interactive: bool = True):
    """
    Create an authenticated Gmail API service using local token.json file or local OAuth server.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    token_path = os.path.join(BASE_DIR, "token.json")
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as error:
            print("Could not read token.json:", error)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as error:
            print("Could not refresh token.json:", error)
            creds = None

    if not creds or not creds.valid:
        if not interactive:
            raise FileNotFoundError("No valid token.json found for fallback Gmail service")
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(f"{CREDENTIALS_FILE} not found for interactive Gmail OAuth")
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build(
        "gmail",
        "v1",
        credentials=creds,
    )