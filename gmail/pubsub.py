import base64
import json


def parse_pubsub_notification(data):
    """
    Decode the Base64URL encoded Gmail notification
    sent inside the Pub/Sub message.
    """

    if not data:
        return None

    decoded_bytes = base64.urlsafe_b64decode(
        data + "=" * (-len(data) % 4)
    )

    decoded_text = decoded_bytes.decode(
        "utf-8"
    )

    return json.loads(decoded_text)