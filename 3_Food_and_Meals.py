import streamlit as st
import config
from core import database as db, auth
from core.models import build_user_context
from core import food_ai, recipe_ai, meal_analyzer
from core.health_calculations import calculate_food_score
from services import ai_client
from ui import components as ui
from ui.theme import inject_css

inject_css()
auth.require_login()

user_id = auth.current_user_id()
profile_row = db.get_profile(user_id)

ui.page_header("Food & Meals", "Personalized recommendations, recipes, and meal analysis — tailored to your diet and allergies.", "meals")

if not profile_row:
    ui.empty_state("Complete your profile first so recommendations respect your diet and allergies.", "👤")
    st.stop()

context = build_user_context(user_id)
profile = context.profile

food_score_today = calculate_food_score(user_id, days=1)
with ui.card_container("food_score_strip"):
    fc1, fc2 = st.columns([1, 4])
    with fc1:
        ui.ring_progress(food_score_today.get("score", 0), "Food Score", size="5.5rem", icon_key="food")
    with fc2:
        st.markdown("**Today's Food Score**")
        st.caption("Based on what you've logged so far today. Log a meal below to improve it.")

def handle_ai_error(e: Exception):
    if isinstance(e, ai_client.AIKeyMissingError):
        ui.error_state(str(e))
    elif isinstance(e, ai_client.AIInvalidResponseError):
        ui.error_state("The AI response couldn't be understood. Please try again.")
    elif isinstance(e, ai_client.AIError):
        ui.error_state(str(e))
    else:
        ui.error_state("Something unexpected happened. Please try again.")

tabs = st.tabs([
    "🍎 Recommendations", "📋 Diet Plan", "💰 Budget Planner",
    "🥘 What Can I Cook?", "📖 Recipe Generator", "✨ Make It Healthier", "📷 Meal Analyzer",
])

# ---------------- Recommendations (deterministic + AI) ----------------
with tabs[0]:
    st.markdown("#### Personalized Food Recommendations")
    st.caption(f"Filtered for: **{profile.diet_type or 'not set'}** | Allergies: **{', '.join(profile.allergies) or 'none'}**")

    meal_type = st.selectbox("Meal type", ["breakfast", "lunch", "dinner", "snack", "general"], key="rec_meal_type")

    catalog = food_ai.get_filtered_catalog(profile.diet_type, profile.allergies)
    with st.expander("Browse safe food categories", expanded=False):
        cols = st.columns(3)
        for i, (cat, items) in enumerate(catalog.items()):
            with cols[i % 3]:
                st.markdown(f"**{cat}**")
                for item in items:
                    st.markdown(f"- {item}")

    if st.button("✨ Get AI-Personalized Recommendations", key="get_rec"):
        with st.spinner("Personalizing recommendations..."):
            try:
                data = food_ai.get_ai_recommendations(context, meal_type)
                recs = data.get("recommendations", [])
                rec_cols = st.columns(2)
                for i, rec in enumerate(recs):
                    with rec_cols[i % 2]:
                        ui.food_card(rec.get("name", ""), rec.get("category", ""), rec.get("why", ""))
                    db.add_food_log(user_id, rec.get("name", ""), meal_type, source="AI_recommended")
                if data.get("notes"):
                    ui.alert(data["notes"], "info")
            except Exception as e:
                handle_ai_error(e)

# ---------------- Diet Plan ----------------
with tabs[1]:
    st.markdown("#### Personalized Diet Plan")
    if st.button("📋 Generate Today's Diet Plan"):
        with st.spinner("Building your personalized diet plan..."):
            try:
                plan = food_ai.get_ai_diet_plan(context)
                meal_labels = {
                    "breakfast": "🌅 Breakfast", "mid_morning_snack": "🍵 Mid-Morning Snack",
                    "lunch": "🍛 Lunch", "evening_snack": "🍪 Evening Snack", "dinner": "🌙 Dinner",
                }
                for key, label in meal_labels.items():
                    meal = plan.get(key, {})
                    if meal.get("items"):
                        st.markdown(f"**{label}** ({meal.get('approx_calories', '?')} kcal est.)")
                        for item in meal["items"]:
                            st.markdown(f"- {item}")
                if plan.get("total_approx_calories"):
                    ui.metric_card("Total Estimated Calories", f"{plan['total_approx_calories']} kcal", "calories")
                ui.alert(plan.get("note", "Estimates only — not medical advice."), "warning")
            except Exception as e:
                handle_ai_error(e)

# ---------------- Budget Planner ----------------
with tabs[2]:
    st.markdown("#### Budget-Aware Food Planner")
    budget = st.number_input("Daily food budget (₹)", min_value=0.0, value=float(profile.daily_food_budget or 150.0))
    if st.button("💰 Generate Budget Plan"):
        with st.spinner("Planning meals within your budget..."):
            try:
                plan = food_ai.get_ai_budget_plan(context, budget)
                total = 0
                for item in plan.get("items", []):
                    st.markdown(f"**{item.get('meal','')}**: {item.get('description','')} — ₹{item.get('approx_cost',0)}")
                    total += item.get("approx_cost", 0) or 0
                ui.metric_card("Total Estimated Cost", f"₹{plan.get('total_approx_cost', total)}", "food")
                ui.alert(plan.get("note", "Prices are approximate and vary by location and time."), "info")
            except Exception as e:
                handle_ai_error(e)

# ---------------- What Can I Cook? ----------------
with tabs[3]:
    st.markdown("#### What Can I Cook?")
    default_ing = ", ".join(profile.available_ingredients) if profile.available_ingredients else ""
    ingredients_text = st.text_area("Ingredients you have (comma-separated)", value=default_ing,
                                     placeholder="rice, moong dal, carrot, tomato, peas")
    if st.button("🥘 Generate Recipe"):
        ingredients = [i.strip() for i in ingredients_text.split(",") if i.strip()]
        if not ingredients:
            ui.error_state("Please enter at least one ingredient.")
        else:
            with st.spinner("Cooking up a recipe idea..."):
                try:
                    recipe = recipe_ai.what_can_i_cook(user_id, context, ingredients)
                    ui.recipe_card(recipe)
                except Exception as e:
                    handle_ai_error(e)

    past = db.get_recipes(user_id, source_type="what_can_i_cook", limit=5)
    if past:
        with st.expander("Recent 'What Can I Cook' recipes"):
            for r in past:
                st.markdown(f"**{r['recipe'].get('recipe_name','Recipe')}** — from: {r['input_text']}")

# ---------------- Healthy Recipe Generator ----------------
with tabs[4]:
    st.markdown("#### Healthy Recipe Generator")
    food_name = st.text_input("What do you want to eat?", placeholder="e.g. khichdi, dal, salad")
    if st.button("📖 Generate Healthy Recipe"):
        if not food_name.strip():
            ui.error_state("Please enter a food name.")
        else:
            with st.spinner("Generating your personalized recipe..."):
                try:
                    recipe = recipe_ai.generate_healthy_recipe(user_id, context, food_name.strip())
                    ui.recipe_card(recipe)
                except Exception as e:
                    handle_ai_error(e)

# ---------------- Make It Healthier ----------------
with tabs[5]:
    st.markdown("#### Make My Food Healthier")
    food_input = st.text_input("Food you currently eat", placeholder="e.g. pizza, burger, fried rice")
    if st.button("✨ Improve This Food"):
        if not food_input.strip():
            ui.error_state("Please enter a food name.")
        else:
            with st.spinner("Finding healthier ways to enjoy this..."):
                try:
                    result = recipe_ai.make_food_healthier(user_id, context, food_input.strip())
                    st.markdown(f"### {result.get('food_name', food_input)}")
                    for key, label in (
                        ("whats_improvable", "What Can Be Improved"),
                        ("healthier_preparation", "Healthier Preparation"),
                        ("ingredient_substitutions", "Ingredient Substitutions"),
                        ("cooking_method_improvements", "Cooking Method Improvements"),
                        ("better_side_options", "Better Side Options"),
                    ):
                        vals = result.get(key) or []
                        if vals:
                            st.markdown(f"**{label}:**")
                            for v in vals:
                                st.markdown(f"- {v}")
                    if result.get("portion_guidance"):
                        st.markdown(f"**Portion Guidance:** {result['portion_guidance']}")
                except Exception as e:
                    handle_ai_error(e)

# ---------------- Meal Analyzer ----------------
with tabs[6]:
    st.markdown("#### AI Meal Analyzer")
    ui.alert("Image-based nutrition analysis is only an estimate and may be inaccurate.", "warning")
    uploaded = st.file_uploader("Upload a photo of your meal", type=config.ALLOWED_IMAGE_TYPES)
    meal_type_img = st.selectbox("Meal type", ["breakfast", "lunch", "dinner", "snack"], key="img_meal_type")
    if uploaded and st.button("📷 Analyze Meal"):
        with st.spinner("Analyzing your meal photo..."):
            try:
                analysis = meal_analyzer.analyze_meal_image(user_id, context, uploaded, meal_type_img)
                st.image(uploaded, width=320)
                st.markdown(f"### {analysis.get('identified_food', 'Unknown food')}")
                st.caption(f"Confidence: {analysis.get('confidence', 'unknown')}")
                nutrition = analysis.get("approx_nutrition", {})
                if nutrition:
                    cols = st.columns(len(nutrition))
                    for i, (k, v) in enumerate(nutrition.items()):
                        with cols[i]:
                            ui.metric_card(k.replace("_g", " (g)").replace("_", " ").title(), str(v), "food")
                if analysis.get("feedback"):
                    st.markdown(f"**Feedback:** {analysis['feedback']}")
                if analysis.get("healthier_alternatives"):
                    st.markdown("**Healthier Alternatives:**")
                    for alt in analysis["healthier_alternatives"]:
                        st.markdown(f"- {alt}")
                ui.alert(analysis.get("disclaimer", ""), "warning")
            except ValueError as ve:
                ui.error_state(str(ve))
            except Exception as e:
                handle_ai_error(e)

    recent_meals = db.get_meal_history(user_id, limit=5)
    if recent_meals:
        with st.expander("Recent analyzed meals"):
            for m in recent_meals:
                st.markdown(f"- **{m['description']}** ({m['meal_type']}) — {m['logged_at']}")

ui.disclaimer_footer()
