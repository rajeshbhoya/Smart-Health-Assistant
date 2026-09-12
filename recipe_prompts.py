"""Prompt templates for recipe generation features."""
import json

SYSTEM_PROMPT = """You are a practical home-cooking assistant inside \
"Smart Health Assistant". You create healthy, realistic recipes.

Rules:
- Strictly respect diet_type and allergies — never include restricted ingredients.
- Never claim exact/lab-precise nutrition figures; label them as approximate.
- Keep steps clear and numbered, suitable for a home cook.
- Respond ONLY with valid JSON matching the requested schema.
"""


def build_ingredient_recipe_prompt(context_dict: dict, ingredients: list[str]) -> str:
    return f"""User context (JSON):
{json.dumps(context_dict, indent=2)}

Available ingredients: {', '.join(ingredients)}

Task: Suggest one healthy recipe primarily using these ingredients, \
respecting diet_type and allergies. It's fine to assume common pantry \
staples (salt, oil, water, basic spices) are available.

Return JSON with this schema:
{{
  "recipe_name": "...",
  "ingredients": [{{"item": "...", "quantity": "..."}}],
  "steps": ["step 1", "step 2", "..."],
  "approx_nutrition": {{"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}},
  "healthy_modifications": ["..."],
  "serving_suggestions": "..."
}}
"""


def build_healthy_recipe_prompt(context_dict: dict, food_name: str) -> str:
    return f"""User context (JSON):
{json.dumps(context_dict, indent=2)}

Requested dish: "{food_name}"

Task: Provide a healthier, personalized version of this dish respecting \
diet_type and allergies.

Return JSON with this schema:
{{
  "recipe_name": "...",
  "ingredients": [{{"item": "...", "quantity": "..."}}],
  "steps": ["step 1", "step 2", "..."],
  "approx_nutrition": {{"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}},
  "healthier_substitutions": ["..."],
  "portion_guidance": "..."
}}
"""


def build_make_healthier_prompt(context_dict: dict, food_name: str) -> str:
    return f"""User context (JSON):
{json.dumps(context_dict, indent=2)}

Food the user currently eats: "{food_name}"

Task: Do NOT just say "don't eat it". Explain how to make this specific \
food healthier while keeping it recognizable and enjoyable, respecting \
diet_type and allergies.

Return JSON with this schema:
{{
  "food_name": "{food_name}",
  "whats_improvable": ["..."],
  "healthier_preparation": ["..."],
  "ingredient_substitutions": ["..."],
  "cooking_method_improvements": ["..."],
  "portion_guidance": "...",
  "better_side_options": ["..."]
}}
"""
