from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from src.whatsapp_bot import send_poll, register_vote, send_confirmation

app = Flask(__name__)

DEFAULT_POLL_ID = "poll_1"
DEFAULT_QUESTION = "Which movie should we watch tonight?"
DEFAULT_OPTIONS = ["Movie A", "Movie B", "Movie C"]

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    from_number = request.form.get("From")
    body = request.form.get("Body", "").strip()
    resp = MessagingResponse()

    if body.lower() == "poll":
        send_poll([from_number], DEFAULT_POLL_ID, DEFAULT_QUESTION, DEFAULT_OPTIONS)
        resp.message("Please reply with the number of your choice.")
        return str(resp)

    if body.isdigit():
        success, msg = register_vote(DEFAULT_POLL_ID, from_number, body)
        if success:
            send_confirmation(from_number, DEFAULT_POLL_ID)
            # resp.message("Thanks, your vote was registered!")
        else:
            resp.message(msg)
        return str(resp)

    resp.message("Send 'poll' to receive a poll, or reply with the poll option number to vote.")
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
