import streamlit as st
import config
from core import database as db, auth
from ui import components as ui
from ui.theme import inject_css

inject_css()
auth.require_login()
user_id = auth.current_user_id()

ui.page_header("Settings", "Manage your appearance, account, and data preferences.", "settings")

tab_display, tab_account, tab_prefs, tab_data = st.tabs(
    ["🎨 Appearance", "👤 Account", "🔔 Preferences", "🗂️ Data"]
)

with tab_display:
    st.markdown("#### Theme")
    current_dark = st.session_state.get("dark_mode", False)
    dark_mode = st.toggle("🌙 Dark Mode", value=current_dark, help="Applies across the whole app for this session.")
    if dark_mode != current_dark:
        st.session_state["dark_mode"] = dark_mode
        st.rerun()
    st.caption("Dark mode is applied instantly and stays consistent across every page.")

with tab_account:
    st.markdown("#### Account")
    user = db.get_user_by_id(user_id)
    with st.container(key="settings_avatar_strip"):
        sa1, sa2 = st.columns([1, 6])
        with sa1:
            ui.avatar(user["username"], size="3.4rem")
        with sa2:
            st.markdown(f"**{user['username']}**")
            st.caption(user["email"])
    st.write("")
    ui.info_panel([
        ("Username", user["username"]),
        ("Email", user["email"]),
        ("Member since", str(user["created_at"]).split("T")[0]),
    ])
    st.write("")
    if st.button("🚪  Logout", width='stretch', key="settings_logout"):
        auth.logout_user()
        st.rerun()

with tab_prefs:
    st.markdown("#### Preferences")
    st.caption("These preferences personalize your experience and don't affect your saved health data.")
    st.toggle("🔔 Medicine reminder notifications", value=True, key="pref_notifications",
              help="Visual reminder badges on the Medicine Reminder page.")
    st.selectbox("📏 Measurement units", ["Metric (kg / cm)", "Imperial (lb / in)"], key="pref_units",
                 help="Display preference only — your stored data remains in metric units.")

with tab_data:
    st.markdown("#### Your Data")
    st.caption("All your tracked data is private to your account and never shared with other users.")

    profile = db.get_profile(user_id)
    if profile:
        def _fmt(v):
            if isinstance(v, list):
                return ", ".join(str(x) for x in v) if v else "None specified"
            return v

        st.markdown("**Personal Information**")
        ui.info_panel([
            ("Name", _fmt(profile.get("full_name"))),
            ("Age", _fmt(profile.get("age"))),
            ("Gender", _fmt(profile.get("gender"))),
            ("Height", f"{profile['height_cm']} cm" if profile.get("height_cm") else None),
            ("Weight", f"{profile['weight_kg']} kg" if profile.get("weight_kg") else None),
        ])
        st.write("")
        st.markdown("**Lifestyle & Goals**")
        ui.info_panel([
            ("Activity Level", _fmt(profile.get("activity_level"))),
            ("Fitness Level", _fmt(profile.get("fitness_level"))),
            ("Health Goal", _fmt(profile.get("health_goal"))),
            ("Sleep Target", f"{profile['sleep_target_hours']} hrs" if profile.get("sleep_target_hours") else None),
            ("Water Target", f"{profile['water_target_ml']} ml" if profile.get("water_target_ml") else None),
        ])
        st.write("")
        st.markdown("**Food & Diet**")
        ui.info_panel([
            ("Diet Type", _fmt(profile.get("diet_type"))),
            ("Food Preferences", _fmt(profile.get("food_preferences"))),
            ("Allergies / Intolerances", _fmt(profile.get("allergies"))),
            ("Daily Food Budget", f"₹{profile['daily_food_budget']}" if profile.get("daily_food_budget") else None),
            ("Preferred Meal Style", _fmt(profile.get("preferred_meal_style"))),
        ])
    else:
        ui.empty_state("No profile data yet.", "🗂️", action_label="Complete Your Profile", action_key="settings_go_profile")

ui.disclaimer_footer()
