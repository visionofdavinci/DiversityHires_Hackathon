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

# --- In-memory storage for votes ---
votes = {}  # {poll_id: {user_number: choice_index}}

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

def send_poll(to: list[str], poll_id: str, question: str, options: list[str]):
    """
    Sends a poll to a list of WhatsApp numbers.
    Users reply with a number to vote.
    """
    votes[poll_id] = {}

    poll_text = question + "\n"
    for i, opt in enumerate(options, start=1):
        poll_text += f"{i}. {opt}\n"
    
    for number in to:
        send_message(number, poll_text)

def register_vote(poll_id: str, user_number: str, reply: str):
    """
    Record a user's vote for a poll.
    :param poll_id: Identifier of the poll
    :param user_number: WhatsApp number of the user
    :param reply: User's reply as a string (e.g., '1', '2', '3')
    """
    if poll_id not in votes:
        print(f"No poll with id {poll_id} found.")
        return "Poll not found."

    try:
        choice_index = int(reply.strip()) - 1
        if choice_index < 0:
            raise ValueError()
    except ValueError:
        return "Invalid response. Please reply with the number of your choice."

    votes[poll_id][user_number] = choice_index
    return f"Vote registered for option {choice_index + 1}."

def send_confirmation(user_number: str, choice_index: int):
    """
    Sends a confirmation message to a user after voting.
    :param user_number: WhatsApp number of voter
    :param choice_index: The option index they selected
    """
    message = f"Thanks! Your vote for option {choice_index} has been recorded ✅"
    send_message(user_number, message)
