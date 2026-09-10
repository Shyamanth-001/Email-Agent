import base64
from bs4 import BeautifulSoup


def decode_body(data):
    if not data:
        return ""

    decoded_bytes = base64.urlsafe_b64decode(
        data + "=" * (-len(data) % 4)
    )

    return decoded_bytes.decode(
        "utf-8",
        errors="replace"
    )


def html_to_text(html):
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    return soup.get_text(
        separator="\n",
        strip=True
    )


def extract_parts(payload):
    plain_text = []
    html_text = []
    attachments = []

    def walk(part):
        mime_type = part.get("mimeType", "")
        filename = part.get("filename", "")
        body = part.get("body", {})

        if filename:
            attachments.append({
                "filename": filename,
                "mime_type": mime_type,
                "attachment_id": body.get("attachmentId")
            })

        data = body.get("data")

        if data:
            decoded = decode_body(data)

            if mime_type == "text/plain":
                plain_text.append(decoded)

            elif mime_type == "text/html":
                html_text.append(decoded)

        for child in part.get("parts", []):
            walk(child)

    walk(payload)

    return {
        "plain_text": "\n".join(plain_text),
        "html_text": "\n".join(html_text),
        "attachments": attachments
    }


def extract_email_content(payload):
    result = extract_parts(payload)

    if result["plain_text"].strip():
        body = result["plain_text"]

    elif result["html_text"].strip():
        body = html_to_text(
            result["html_text"]
        )

    else:
        body = ""

    return {
        "body": body,
        "attachments": result["attachments"]
    }