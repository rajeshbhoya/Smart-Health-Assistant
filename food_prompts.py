"""Prompt templates for personalized food recommendations and diet plans."""
import json

SYSTEM_PROMPT = """You are a wellness-focused nutrition assistant inside the \
"Smart Health Assistant" app. You give general, educational food guidance only.

Rules you must always follow:
- Never diagnose conditions or prescribe treatment.
- Never claim guaranteed health outcomes.
- Strictly respect the user's diet type and allergies — if diet_type is \
Vegetarian, suggest ZERO meat/fish/poultry. If an allergen is listed, suggest \
ZERO foods containing it.
- If a field is "unknown", do not invent a value for it — work around the gap.
- Respond ONLY with valid JSON matching the requested schema. No extra text.
- Keep guidance practical and budget-aware when a budget is given.
"""


def build_recommendation_prompt(context_dict: dict, meal_type: str = "general") -> str:
    return f"""User context (JSON):
{json.dumps(context_dict, indent=2)}

Task: Suggest 6-10 specific food items appropriate for meal_type="{meal_type}" \
that respect this user's diet_type and allergies exactly.

Return JSON with this schema:
{{
  "meal_type": "{meal_type}",
  "recommendations": [
    {{"name": "...", "category": "...", "why": "one short reason tied to their goal/preferences"}}
  ],
  "notes": "one short sentence, e.g. budget or ingredient-availability caveat"
}}
"""


def build_diet_plan_prompt(context_dict: dict) -> str:
    return f"""User context (JSON):
{json.dumps(context_dict, indent=2)}

Task: Build one day's personalized diet plan strictly respecting diet_type \
and allergies. Consider health_goal, preferred_meal_style, and \
daily_food_budget if known.

Return JSON with this schema:
{{
  "breakfast": {{"items": ["..."], "approx_calories": 0}},
  "mid_morning_snack": {{"items": ["..."], "approx_calories": 0}},
  "lunch": {{"items": ["..."], "approx_calories": 0}},
  "evening_snack": {{"items": ["..."], "approx_calories": 0}},
  "dinner": {{"items": ["..."], "approx_calories": 0}},
  "total_approx_calories": 0,
  "note": "one short sentence noting these are estimates, not medical advice"
}}
"""


def build_budget_plan_prompt(context_dict: dict, budget: float) -> str:
    return f"""User context (JSON):
{json.dumps(context_dict, indent=2)}

Daily food budget: {budget} (local currency)

Task: Build a practical one-day meal plan that fits within this budget, \
respecting diet_type and allergies. Prices are approximate and vary by \
location — say so explicitly.

Return JSON with this schema:
{{
  "items": [
    {{"meal": "Breakfast|Lunch|Snack|Dinner", "description": "...", "approx_cost": 0}}
  ],
  "total_approx_cost": 0,
  "budget": {budget},
  "note": "prices are approximate estimates and vary by location and time"
}}
"""
