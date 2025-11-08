from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load local .env file
load_dotenv(dotenv_path="config/.env", override=True)

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
    return client.messages.create(
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

    results = []
    for number in to:
        msg = send_message(number, poll_text)
        results.append(msg.sid)
    return results

def register_vote(poll_id: str, user_number: str, reply: str):
    """
    Record a user's vote for a poll.
    Returns a tuple: (success: bool, message: str)
    """
    if poll_id not in votes:
        print(f"No poll with id {poll_id} found.")
        return False, "Poll not found."

    try:
        choice_index = int(reply.strip()) - 1
        if choice_index < 0:
            raise ValueError()
    except ValueError:
        return False, "Invalid response. Please reply with the number of your choice."

    votes[poll_id][user_number] = choice_index
    return True, f"Vote registered for option {choice_index + 1}."

def send_confirmation(user_number: str, poll_id: int):
    """
    Sends a confirmation message to a user after voting.
    :param user_number: WhatsApp number of voter
    :param poll_id:
    """
    if poll_id not in votes:
        return send_message(user_number, "No poll found.")

    choice_index = votes[poll_id].get(user_number)
    if choice_index is None:
        return send_message(user_number, "You haven't voted yet.")
    # send confirmation
    choice_display = choice_index + 1
    return send_message(user_number, f"Thanks, your vote for option {choice_display} has been recorded!")
