from twilio.rest import Client
import os

ACCOUNT_SID = os.getenv(
    "TWILIO_ACCOUNT_SID"
)

AUTH_TOKEN = os.getenv(
    "TWILIO_AUTH_TOKEN"
)

TWILIO_PHONE = os.getenv(
    "TWILIO_PHONE_NUMBER"
)

client = Client(
    ACCOUNT_SID,
    AUTH_TOKEN
)

def send_sms(to_number, message_text):

    try:

        message = client.messages.create(

            body=message_text,

            from_=TWILIO_PHONE,

            to=to_number
        )

        print(
            "SMS SENT:",
            message.sid
        )

        return True

    except Exception as e:

        print(
            "SMS ERROR:",
            e
        )

        return False