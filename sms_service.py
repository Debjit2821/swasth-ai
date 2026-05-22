from twilio.rest import Client
import os

ACCOUNT_SID = os.getenv(
    "TWILIO_ACCOUNT_SID"
)

AUTH_TOKEN = os.getenv(
    "TWILIO_AUTH_TOKEN"
)

client = Client(
    ACCOUNT_SID,
    AUTH_TOKEN
)

def send_whatsapp(
    to_number,
    message_text
):

    try:

        message = client.messages.create(

            body=message_text,

            from_="whatsapp:+14155238886",

            to=f"whatsapp:{to_number}"
        )

        print(
            "WHATSAPP SENT:",
            message.sid
        )

    except Exception as e:

        print(
            "WHATSAPP ERROR:",
            e
        )