"""
Recipe Intelligence: "What Can I Cook?", Healthy Recipe Generator, and
"Make My Food Healthier". All results are saved per-user for history.
"""
from core import database as db
from core.models import UserContext
from core.food_ai import filter_ai_food_list
from services import ai_client
from services.prompts import recipe_prompts


def what_can_i_cook(user_id: int, context: UserContext, ingredients: list[str]) -> dict:
    ctx_dict = context.to_prompt_dict()
    prompt = recipe_prompts.build_ingredient_recipe_prompt(ctx_dict, ingredients)
    recipe = ai_client.chat_json(recipe_prompts.SYSTEM_PROMPT, prompt)

    diet_type, allergies = context.profile.diet_type, context.profile.allergies
    recipe["ingredients"] = filter_ai_food_list(
        [{"name": i.get("item", "")} | i for i in recipe.get("ingredients", [])], diet_type, allergies
    )

    db.save_recipe(user_id, "what_can_i_cook", ", ".join(ingredients), recipe)
    return recipe


def generate_healthy_recipe(user_id: int, context: UserContext, food_name: str) -> dict:
    ctx_dict = context.to_prompt_dict()
    prompt = recipe_prompts.build_healthy_recipe_prompt(ctx_dict, food_name)
    recipe = ai_client.chat_json(recipe_prompts.SYSTEM_PROMPT, prompt)
    db.save_recipe(user_id, "healthy_recipe", food_name, recipe)
    return recipe


def make_food_healthier(user_id: int, context: UserContext, food_name: str) -> dict:
    ctx_dict = context.to_prompt_dict()
    prompt = recipe_prompts.build_make_healthier_prompt(ctx_dict, food_name)
    result = ai_client.chat_json(recipe_prompts.SYSTEM_PROMPT, prompt)
    db.save_recipe(user_id, "make_healthier", food_name, result)
    return result
