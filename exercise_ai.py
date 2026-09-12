"""AI-assisted exercise planning, layered on deterministic beginner-safe defaults."""
from core import database as db
from core.models import UserContext
from services import ai_client
from services.prompts import exercise_prompts

# Deterministic fallback library (used if AI is unavailable, or for quick suggestions)
FALLBACK_PLANS = {
    "Beginner": {
        "session_title": "Beginner Full-Body Basics",
        "warm_up": ["5 min brisk walk", "Arm circles", "Bodyweight squats x10"],
        "main_exercises": [
            {"name": "Wall Push-ups", "sets_or_duration": "2 sets x 10", "notes": "Keep core engaged"},
            {"name": "Chair Squats", "sets_or_duration": "2 sets x 12", "notes": "Slow controlled movement"},
            {"name": "Standing March", "sets_or_duration": "2 min", "notes": "Light cardio"},
        ],
        "cool_down": ["Standing quad stretch", "Shoulder stretch", "Deep breathing"],
        "total_duration_min": 20,
        "caution": "New to exercise? Start slow and consult a professional if you have any health conditions.",
    },
    "Intermediate": {
        "session_title": "Intermediate Strength & Cardio Mix",
        "warm_up": ["5 min jog in place", "Dynamic stretches"],
        "main_exercises": [
            {"name": "Push-ups", "sets_or_duration": "3 sets x 12", "notes": ""},
            {"name": "Bodyweight Squats", "sets_or_duration": "3 sets x 15", "notes": ""},
            {"name": "Plank", "sets_or_duration": "3 x 30 sec", "notes": ""},
            {"name": "Jumping Jacks", "sets_or_duration": "3 min", "notes": ""},
        ],
        "cool_down": ["Full body stretch", "Deep breathing"],
        "total_duration_min": 30,
        "caution": "Maintain proper form; stop if you feel sharp pain.",
    },
    "Advanced": {
        "session_title": "Advanced Strength & Conditioning",
        "warm_up": ["8 min dynamic warm-up", "Mobility drills"],
        "main_exercises": [
            {"name": "Burpees", "sets_or_duration": "4 sets x 15", "notes": ""},
            {"name": "Jump Squats", "sets_or_duration": "4 sets x 15", "notes": ""},
            {"name": "Push-up Variations", "sets_or_duration": "4 sets x 15", "notes": ""},
            {"name": "Plank to Push-up", "sets_or_duration": "3 sets x 10", "notes": ""},
        ],
        "cool_down": ["Full body stretch", "Foam rolling if available"],
        "total_duration_min": 40,
        "caution": "Advanced routine — ensure adequate recovery and hydration.",
    },
}


def get_fallback_plan(fitness_level: str) -> dict:
    return FALLBACK_PLANS.get(fitness_level, FALLBACK_PLANS["Beginner"])


def get_ai_exercise_plan(context: UserContext, available_minutes: int) -> dict:
    ctx_dict = context.to_prompt_dict()
    prompt = exercise_prompts.build_exercise_plan_prompt(ctx_dict, available_minutes)
    try:
        return ai_client.chat_json(exercise_prompts.SYSTEM_PROMPT, prompt)
    except ai_client.AIError:
        plan = dict(get_fallback_plan(context.profile.fitness_level))
        plan["total_duration_min"] = available_minutes
        return plan
