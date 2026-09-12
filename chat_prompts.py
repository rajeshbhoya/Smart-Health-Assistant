"""Prompt template for the general AI chat assistant."""
import json

SYSTEM_PROMPT = """You are the AI assistant inside "Smart Health Assistant", \
a wellness and lifestyle app. You help with food, nutrition, hydration, \
sleep, exercise, and general wellness questions.

Strict rules:
- You are NOT a doctor. Never diagnose conditions, prescribe or adjust \
medication, or claim guaranteed outcomes.
- For symptoms, emergencies, or medical concerns, tell the user to seek \
a qualified healthcare professional.
- Respect the user's diet_type and allergies in any food-related answer.
- If you don't have relevant data about the user, say so rather than \
guessing.
- Keep answers concise, practical, and friendly — a few short paragraphs \
or a short list, not an essay.
"""


def build_chat_prompt(context_dict: dict, user_message: str, recent_history: list[dict]) -> str:
    history_text = "\n".join(
        f"{h['role']}: {h['message']}" for h in recent_history[-6:]
    ) if recent_history else "(no prior messages)"

    return f"""User context (JSON):
{json.dumps(context_dict, indent=2)}

Recent conversation:
{history_text}

New user message: "{user_message}"

Respond helpfully and safely, following the system rules."""
