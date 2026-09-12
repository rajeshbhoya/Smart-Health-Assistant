"""Prompt templates for the exercise planner."""
import json

SYSTEM_PROMPT = """You are an exercise-planning assistant inside \
"Smart Health Assistant". You provide general fitness suggestions, not \
personal training or medical clearance.

Rules:
- Include a caution encouraging professional guidance for anyone with \
health conditions, injuries, or who is new to exercise.
- Keep it realistic for the stated fitness_level and available time.
- Respond ONLY with valid JSON matching the schema.
"""


def build_exercise_plan_prompt(context_dict: dict, available_minutes: int) -> str:
    return f"""User context (JSON):
{json.dumps(context_dict, indent=2)}

Available time today: {available_minutes} minutes.

Task: Suggest a suitable exercise session for this user's fitness_level, \
health_goal, and activity_level, fitting in the available time.

Return JSON with this schema:
{{
  "session_title": "...",
  "warm_up": ["..."],
  "main_exercises": [{{"name": "...", "sets_or_duration": "...", "notes": "..."}}],
  "cool_down": ["..."],
  "total_duration_min": {available_minutes},
  "caution": "one short safety note about consulting a professional if needed"
}}
"""
