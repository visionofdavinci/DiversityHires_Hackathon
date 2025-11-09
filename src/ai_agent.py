# src/ai_agent.py
from src.orchestrator import get_group_recommendations

class AIAgent:
    def __init__(self):
        pass

    def respond(self, message, usernames):
        message = message.lower()

        if "movie" in message or "recommend" in message:
            data = get_group_recommendations(usernames)
            top = data["recommendations"][:3]
            response = "Here are a few good picks:\n" + "\n".join(f"- {m['title']}" for m in top)
            return response

        elif "free" in message or "available" in message:
            data = get_group_recommendations(usernames)
            free_slots = data["common_free_slots"][:2]
            response = "You’re all free at:\n" + "\n".join(str(slot) for slot in free_slots)
            return response

        else:
            return "I can help you find movies or check when you’re all free!"
