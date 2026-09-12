import streamlit as st
import config
from core import database as db, auth
from core.models import UserProfile
from core.utils import validate_positive_number
from ui import components as ui
from ui.theme import inject_css

inject_css()
auth.require_login()

ui.page_header("Profile", "Your personal health profile — this information personalizes every recommendation across the app.", "profile")

user_id = auth.current_user_id()
existing = db.get_profile(user_id) or {}
profile = UserProfile.from_db_row(existing) if existing else UserProfile(user_id=user_id)

user_row = db.get_user_by_id(user_id)
with st.container(key="profile_avatar_strip"):
    pa1, pa2 = st.columns([1, 6])
    with pa1:
        ui.avatar(profile.full_name or user_row["username"], size="3.4rem")
    with pa2:
        st.markdown(f"**{profile.full_name or user_row['username']}**")
        st.caption(user_row["email"])

with st.form("profile_form"):
    with ui.card_container("profile_personal"):
        st.markdown("#### 🧑 Personal Information")
        c1, c2, c3 = st.columns(3)
        with c1:
            full_name = st.text_input("Full Name", value=profile.full_name)
        with c2:
            age = st.number_input("Age", min_value=10, max_value=100, value=profile.age or 25)
        with c3:
            gender = st.selectbox("Gender", config.GENDER_OPTIONS,
                                   index=config.GENDER_OPTIONS.index(profile.gender) if profile.gender in config.GENDER_OPTIONS else 0)

        c4, c5 = st.columns(2)
        with c4:
            height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=float(profile.height_cm or 165.0))
        with c5:
            weight_kg = st.number_input("Weight (kg)", min_value=25.0, max_value=250.0, value=float(profile.weight_kg or 65.0))

    with ui.card_container("profile_lifestyle"):
        st.markdown("#### 🎯 Lifestyle & Goals")
        c6, c7, c8 = st.columns(3)
        with c6:
            activity_level = st.selectbox("Activity Level", config.ACTIVITY_LEVELS,
                                           index=config.ACTIVITY_LEVELS.index(profile.activity_level) if profile.activity_level in config.ACTIVITY_LEVELS else 0)
        with c7:
            fitness_level = st.selectbox("Fitness Level", config.FITNESS_LEVELS,
                                          index=config.FITNESS_LEVELS.index(profile.fitness_level) if profile.fitness_level in config.FITNESS_LEVELS else 0)
        with c8:
            health_goal = st.selectbox("Health Goal", config.HEALTH_GOALS,
                                        index=config.HEALTH_GOALS.index(profile.health_goal) if profile.health_goal in config.HEALTH_GOALS else 0)

    with ui.card_container("profile_food"):
        st.markdown("#### 🥗 Food & Diet Preferences")
        c9, c10 = st.columns(2)
        with c9:
            diet_type = st.selectbox("Diet Type", config.DIET_TYPES,
                                      index=config.DIET_TYPES.index(profile.diet_type) if profile.diet_type in config.DIET_TYPES else 0)
        with c10:
            preferred_meal_style = st.selectbox("Preferred Meal Style", config.MEAL_STYLES,
                                                 index=config.MEAL_STYLES.index(profile.preferred_meal_style) if profile.preferred_meal_style in config.MEAL_STYLES else 0)

        food_preferences = st.text_input("Food Preferences (comma-separated)", value=", ".join(profile.food_preferences))

    with ui.card_container("profile_allergies"):
        st.markdown("#### ⚠️ Allergies & Restrictions")
        allergies = st.multiselect("Allergies / Intolerances", config.COMMON_ALLERGENS, default=[a for a in profile.allergies if a in config.COMMON_ALLERGENS])

    with ui.card_container("profile_budget"):
        st.markdown("#### 💰 Budget & Meal Preferences")
        available_ingredients = st.text_input("Ingredients you usually have at home (optional, comma-separated)",
                                               value=", ".join(profile.available_ingredients))
        daily_food_budget = st.number_input("Daily Food Budget (₹, optional)", min_value=0.0, value=float(profile.daily_food_budget or 0))

    with ui.card_container("profile_targets"):
        st.markdown("#### 🎯 Daily Targets")
        c11, c12 = st.columns(2)
        with c11:
            sleep_target = st.number_input("Sleep Target (hours)", min_value=4.0, max_value=12.0, value=float(profile.sleep_target_hours or 8.0))
        with c12:
            water_target = st.number_input("Water Target (ml)", min_value=1000, max_value=6000, value=int(profile.water_target_ml or 2500))

    submitted = st.form_submit_button("💾 Save Profile", width='stretch')

if submitted:
    ok, msg = validate_positive_number(height_cm, "Height", min_val=100, max_val=250)
    if not ok:
        ui.error_state(msg)
    else:
        ok2, msg2 = validate_positive_number(weight_kg, "Weight", min_val=25, max_val=250)
        if not ok2:
            ui.error_state(msg2)
        else:
            data = dict(
                full_name=full_name.strip(), age=int(age), gender=gender,
                height_cm=height_cm, weight_kg=weight_kg,
                activity_level=activity_level, fitness_level=fitness_level, health_goal=health_goal,
                diet_type=diet_type, food_preferences=[f.strip() for f in food_preferences.split(",") if f.strip()],
                allergies=allergies or ["None"],
                daily_food_budget=daily_food_budget or None,
                preferred_meal_style=preferred_meal_style,
                available_ingredients=[i.strip() for i in available_ingredients.split(",") if i.strip()],
                sleep_target_hours=sleep_target, water_target_ml=int(water_target),
            )
            try:
                db.upsert_profile(user_id, data)
                db.add_weight(user_id, weight_kg)
                st.success("Profile saved successfully!")
                st.rerun()
            except db.DatabaseError:
                ui.error_state("Could not save your profile due to a database error. Please try again.")

ui.disclaimer_footer()
