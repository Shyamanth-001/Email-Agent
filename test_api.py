from fastapi import FastAPI, Request
from gmail.gmail_service import get_gmail_service
from gmail.pubsub import parse_pubsub_notification

app = FastAPI()


@app.post("/gmail/webhook")
async def gmail_webhook(request: Request):

    data = await request.json()

    message = data.get("message")

    if not message:
        return {"status": "ignored"}

    encoded_data = message.get("data")

    if not encoded_data:
        return {"status": "ignored"}

    notification = parse_pubsub_notification(encoded_data)

    email_address = notification["emailAddress"]
    history_id = notification["historyId"]

    print("GMAIL NOTIFICATION")
    print("Email:", email_address)
    print("History ID:", history_id)

    return {"status": "ok"}