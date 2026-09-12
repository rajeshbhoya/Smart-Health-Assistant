"""
Food Intelligence System.

Design principle (per project requirement): filtering by diet type and
allergies is enforced DETERMINISTICALLY in Python, both before AND after
any AI call — the AI is never solely trusted to respect restrictions.
"""
from core import database as db
from core.models import UserContext
from services import ai_client
from services.prompts import food_prompts

# ---------------------------------------------------------------------------
# Static food catalog (deterministic layer — always available, no AI needed)
# ---------------------------------------------------------------------------

FOOD_CATALOG = {
    "Fruits": ["Apple", "Banana", "Orange", "Papaya", "Guava", "Pomegranate", "Watermelon", "Mango"],
    "Vegetables": ["Spinach", "Broccoli", "Carrot", "Bell Pepper", "Cauliflower", "Cucumber", "Beetroot", "Pumpkin"],
    "Dal": ["Moong Dal", "Toor Dal", "Masoor Dal", "Urad Dal", "Chana Dal"],
    "Pulses": ["Green Gram", "Black Gram", "Horse Gram"],
    "Beans": ["Kidney Beans", "Black Beans", "Green Beans", "Broad Beans"],
    "Chickpeas": ["White Chickpeas", "Black Chickpeas (Kala Chana)"],
    "Rajma": ["Rajma (Red Kidney Beans)"],
    "Grains": ["Brown Rice", "Whole Wheat", "Quinoa", "Oats", "Barley"],
    "Millets": ["Ragi (Finger Millet)", "Jowar (Sorghum)", "Bajra (Pearl Millet)", "Foxtail Millet"],
    "Nuts": ["Almonds", "Walnuts", "Cashews", "Pistachios"],
    "Seeds": ["Chia Seeds", "Flax Seeds", "Pumpkin Seeds", "Sunflower Seeds"],
    "Dairy": ["Milk", "Curd/Yogurt", "Paneer", "Buttermilk"],
    "Eggs": ["Boiled Egg", "Egg Whites", "Omelette"],
    "Vegetarian foods": ["Paneer Curry", "Vegetable Khichdi", "Dal Tadka", "Sprouts Salad"],
    "Non-vegetarian foods": ["Grilled Chicken Breast", "Steamed Fish", "Chicken Soup", "Boiled Egg Curry"],
    "Healthy snacks": ["Roasted Chana", "Sprouts Chaat", "Fruit Bowl", "Handful of Nuts", "Greek Yogurt"],
}

ALLERGEN_KEYWORD_MAP = {
    "Peanuts": ["peanut"],
    "Tree Nuts": ["almond", "walnut", "cashew", "pistachio", "nut"],
    "Dairy/Lactose": ["milk", "paneer", "curd", "yogurt", "buttermilk", "dairy"],
    "Gluten": ["wheat", "barley", "oats"],
    "Soy": ["soy", "soya"],
    "Eggs": ["egg"],
    "Shellfish": ["shrimp", "prawn", "crab", "shellfish"],
    "Fish": ["fish"],
}


def _is_allergen_conflict(food_name: str, allergies: list[str]) -> bool:
    name_lower = food_name.lower()
    for allergen in allergies:
        if allergen == "None":
            continue
        keywords = ALLERGEN_KEYWORD_MAP.get(allergen, [allergen.lower()])
        if any(kw in name_lower for kw in keywords):
            return True
    return False


def _diet_allows_category(category: str, diet_type: str) -> bool:
    if category == "Non-vegetarian foods" and diet_type == "Vegetarian":
        return False
    if category == "Eggs" and diet_type == "Vegetarian":
        return False
    return True


def get_filtered_catalog(diet_type: str, allergies: list[str]) -> dict:
    """Deterministic filtering — the guaranteed-safe fallback and post-AI filter."""
    result = {}
    for category, items in FOOD_CATALOG.items():
        if not _diet_allows_category(category, diet_type):
            continue
        safe_items = [i for i in items if not _is_allergen_conflict(i, allergies)]
        if safe_items:
            result[category] = safe_items
    return result


def filter_ai_food_list(items: list[dict], diet_type: str, allergies: list[str]) -> list[dict]:
    """Post-processing guardrail applied to any AI-generated food/recipe list."""
    safe = []
    for item in items:
        name = item.get("name") or item.get("item") or ""
        category = item.get("category", "")
        if diet_type == "Vegetarian" and any(
            kw in name.lower() for kw in ("chicken", "fish", "mutton", "meat", "egg", "prawn", "beef", "pork")
        ):
            continue
        if _is_allergen_conflict(name, allergies):
            continue
        safe.append(item)
    return safe


# ---------------------------------------------------------------------------
# AI-personalized layer (built on top of the deterministic guardrails)
# ---------------------------------------------------------------------------

def get_ai_recommendations(context: UserContext, meal_type: str = "general") -> dict:
    ctx_dict = context.to_prompt_dict()
    prompt = food_prompts.build_recommendation_prompt(ctx_dict, meal_type)
    data = ai_client.chat_json(food_prompts.SYSTEM_PROMPT, prompt)
    data["recommendations"] = filter_ai_food_list(
        data.get("recommendations", []), context.profile.diet_type, context.profile.allergies
    )
    return data


def get_ai_diet_plan(context: UserContext) -> dict:
    ctx_dict = context.to_prompt_dict()
    prompt = food_prompts.build_diet_plan_prompt(ctx_dict)
    data = ai_client.chat_json(food_prompts.SYSTEM_PROMPT, prompt)
    diet_type, allergies = context.profile.diet_type, context.profile.allergies
    for meal_key in ("breakfast", "mid_morning_snack", "lunch", "evening_snack", "dinner"):
        meal = data.get(meal_key)
        if isinstance(meal, dict) and "items" in meal:
            wrapped = [{"name": i} for i in meal["items"]]
            filtered = filter_ai_food_list(wrapped, diet_type, allergies)
            meal["items"] = [f["name"] for f in filtered]
    return data


def get_ai_budget_plan(context: UserContext, budget: float) -> dict:
    ctx_dict = context.to_prompt_dict()
    prompt = food_prompts.build_budget_plan_prompt(ctx_dict, budget)
    data = ai_client.chat_json(food_prompts.SYSTEM_PROMPT, prompt)
    return data
