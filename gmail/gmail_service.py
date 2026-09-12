import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]


def get_gmail_service():
    creds = None

    # Load existing OAuth token
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    # Refresh expired token
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # Start OAuth flow if credentials are missing/invalid
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json",
            SCOPES
        )

        creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


def get_added_message_ids(service, start_history_id):
    """
    Get message IDs that were added to the mailbox
    after start_history_id.

    Handles pagination because Gmail history.list()
    may return multiple pages.
    """

    message_ids = []

    page_token = None

    while True:

        response = service.users().history().list(
            userId="me",
            startHistoryId=start_history_id,
            historyTypes=["messageAdded"],
            pageToken=page_token
        ).execute()

        for history_item in response.get("history", []):

            for added_message in history_item.get(
                "messagesAdded",
                []
            ):

                message = added_message.get(
                    "message",
                    {}
                )

                message_id = message.get("id")

                if message_id:
                    message_ids.append(message_id)

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    # Remove duplicates while preserving order
    return list(dict.fromkeys(message_ids))


def get_message(service, message_id):
    """
    Fetch the complete Gmail message.
    """

    return service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()


def create_gmail_watch(service, topic_name):
    """
    Create/renew Gmail push notifications.

    topic_name example:

    projects/YOUR_PROJECT_ID/topics/gmail-notifications
    """

    response = service.users().watch(
        userId="me",
        body={
            "topicName": topic_name,
            "labelIds": ["INBOX"],
            "labelFilterBehavior": "INCLUDE"
        }
    ).execute()

    return response