from gmail_service import get_gmail_service
from email_parser import extract_email_content


def get_headers(message):
    headers = message["payload"].get(
        "headers",
        []
    )

    result = {}

    for header in headers:
        result[header["name"].lower()] = header["value"]

    return result


def main():
    service = get_gmail_service()

    response = service.users().messages().list(
        userId="me",
        maxResults=5
    ).execute()

    messages = response.get(
        "messages",
        []
    )

    for item in messages:

        message = service.users().messages().get(
            userId="me",
            id=item["id"],
            format="full"
        ).execute()

        headers = get_headers(message)

        content = extract_email_content(
            message["payload"]
        )

        print("=" * 80)

        print("Message ID:")
        print(message["id"])

        print("\nThread ID:")
        print(message["threadId"])

        print("\nFrom:")
        print(headers.get("from"))

        print("\nTo:")
        print(headers.get("to"))

        print("\nSubject:")
        print(headers.get("subject"))

        print("\nBody:")
        print(content["body"])

        print("\nAttachments:")
        for attachment in content["attachments"]:
            print(attachment)


if __name__ == "__main__":
    main()