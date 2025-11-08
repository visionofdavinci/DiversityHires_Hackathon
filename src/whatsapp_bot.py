from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load local .env file
load_dotenv(dotenv_path="config/.env")

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_message(to: str, message: str):
    """
    Send a WhatsApp message to a user.
    :param to: Recipient number in format 'whatsapp:+1234567890'
    :param message: Text to send
    """
    client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        body=message,
        to=to
    )

def send_poll(to: list[str], question: str, options: list[str]):
    """
    Sends a poll to a list of WhatsApp numbers.
    Users reply with a number to vote.
    """
    poll_text = question + "\n"
    for i, opt in enumerate(options, start=1):
        poll_text += f"{i}. {opt}\n"
    
    for number in to:
        send_message(number, poll_text)