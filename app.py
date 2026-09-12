"""
Smart Health Assistant — main entry point.

Owns the single st.set_page_config() call and the app-wide navigation
(st.navigation / st.Page), so the sidebar shows friendly page titles
("Dashboard", "Profile", ...) instead of raw filenames. Also renders
the authentication screen and the Dashboard itself.
"""
import os
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import config
from core import database as db
from core import auth
from core.health_calculations import (
    calculate_bmi, bmi_category, calculate_health_score, calculate_food_score,
    full_calorie_estimate, get_weight_trend,
)
from core.models import UserProfile
from core.water_tracker import get_today_progress
from ui import components as ui
from ui.theme import inject_css, icon_html, initials_avatar_html

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon=config.APP_ICON if os.path.exists(config.APP_ICON) else "❤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()
inject_css()


# ---------------------------------------------------------------------------
# Auth screen (shown only when logged out — no navigation/sidebar at all)
# ---------------------------------------------------------------------------

AUTH_FEATURES = [
    ("❤️", "Track health score, BMI, and calories in one place"),
    ("🥗", "AI-personalized meals that respect your diet & allergies"),
    ("🤖", "A wellness chat assistant available whenever you need it"),
]


def render_auth_screen():
    with st.container(key="auth_shell"):
        hero_col, form_col = st.columns([1.05, 1], gap="small")

        with hero_col:
            with st.container(key="auth_hero"):
                features_html = "".join(
                    f'<div class="sha-auth-feature"><span class="dot">{emoji}</span><span>{text}</span></div>'
                    for emoji, text in AUTH_FEATURES
                )
                hero_html = (
                    f'<div class="sha-auth-icon">❤️</div>'
                    f'<h1>{config.APP_NAME}</h1>'
                    f'<div class="sha-auth-tagline">Your personal wellness companion — track, understand, and '
                    f'improve your everyday health, every single day.</div>'
                    f'{features_html}'
                )
                st.markdown(hero_html, unsafe_allow_html=True)

        with form_col:
            with st.container(key="auth_card"):
                tab_login, tab_register = st.tabs(["🔐  Login", "📝  Register"])

                with tab_login:
                    st.markdown('<h2>Welcome back</h2><div class="sha-auth-sub">Please log in to continue your health journey.</div>', unsafe_allow_html=True)
                    with st.form("login_form"):
                        identifier = st.text_input("Username or Email", placeholder="you@example.com")
                        password = st.text_input("Password", type="password", placeholder="••••••••")
                        submitted = st.form_submit_button("Log In", width='stretch', type="primary")
                    if submitted:
                        success, message = auth.login_user(identifier, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            ui.error_state(message)

                with tab_register:
                    st.markdown('<h2>Create your account</h2><div class="sha-auth-sub">Takes less than a minute to get started.</div>', unsafe_allow_html=True)
                    with st.form("register_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            username = st.text_input("Username", help="3-20 characters, letters/numbers/underscore")
                        with col2:
                            email = st.text_input("Email")
                        col3, col4 = st.columns(2)
                        with col3:
                            password = st.text_input("Password", type="password", help="At least 8 characters, 1 letter, 1 number")
                        with col4:
                            confirm_password = st.text_input("Confirm Password", type="password")
                        submitted = st.form_submit_button("Create Account", width='stretch', type="primary")
                    if submitted:
                        success, message = auth.register_user(username, email, password, confirm_password)
                        if success:
                            st.success(message)
                        else:
                            ui.error_state(message)

    ui.disclaimer_footer()


# ---------------------------------------------------------------------------
# Dashboard (registered as the default page in st.navigation, below)
# ---------------------------------------------------------------------------

def _greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good Morning"
    if hour < 17:
        return "Good Afternoon"
    return "Good Evening"


def render_dashboard_page():
    user_id = auth.current_user_id()
    user = db.get_user_by_id(user_id)
    profile_row = db.get_profile(user_id)

    if not profile_row:
        ui.page_header("Dashboard", "Here's your health overview for today.", "dashboard")
        ui.alert("Your profile is incomplete. Please visit the <b>Profile</b> page to get personalized recommendations.", kind="warning")
        ui.disclaimer_footer()
        return

    profile = UserProfile.from_db_row(profile_row)
    first_name = (profile.full_name or user["username"]).split(" ")[0]

    greeting_date = date.today().strftime('%A, %d %B %Y')
    greeting_html = (
        f'<div class="sha-hero-banner"><h1>{_greeting()}, {first_name} 👋</h1>'
        f'<div class="sha-subtitle">Here\'s your health overview for {greeting_date}.</div></div>'
    )
    st.markdown(greeting_html, unsafe_allow_html=True)

    if not profile.is_complete:
        ui.alert("Some profile fields are missing. Complete your profile for more accurate insights.", kind="warning")

    # --- Compute live metrics from real data ---
    bmi = calculate_bmi(profile.weight_kg, profile.height_cm) if profile.weight_kg and profile.height_cm else 0
    health_result = calculate_health_score(user_id, profile) if profile.is_complete else None
    food_result = calculate_food_score(user_id, days=1)
    calorie_est = full_calorie_estimate(profile) if profile.is_complete else None
    water_progress = get_today_progress(user_id, profile.water_target_ml)
    trend, latest_weight, change = get_weight_trend(user_id)

    trend_kind = "down" if (change is not None and change < 0) else ("up" if (change is not None and change > 0) else "neutral")

    row1 = st.columns(4)
    with row1[0]:
        ui.metric_card("Health Score", f"{health_result['score']}/100" if health_result else "—",
                        "health_score", health_result["category"] if health_result else "Complete profile")
    with row1[1]:
        ui.metric_card("BMI", f"{bmi}" if bmi else "—", "bmi", bmi_category(bmi) if bmi else "")
    with row1[2]:
        ui.metric_card("Current Weight", f"{latest_weight} kg" if latest_weight else "—", "weight",
                        f"{'+' if change and change > 0 else ''}{change} kg recent" if change is not None else "No logs yet",
                        trend=(f"{change:+.1f} kg" if change is not None else ""), trend_kind=trend_kind)
    with row1[3]:
        ui.metric_card("Daily Calories", f"{int(calorie_est['goal_calories'])} kcal" if calorie_est else "—",
                        "calories", "Goal estimate" if calorie_est else "")

    row2 = st.columns(4)
    with row2[0]:
        ui.metric_card("Water", f"{water_progress['percentage']}%", "water",
                        f"{water_progress['consumed_ml']}/{water_progress['target_ml']} ml")
    with row2[1]:
        sleep_hist = db.get_sleep_history(user_id, limit=1)
        sleep_val = f"{sleep_hist[0]['duration_hours']} hrs" if sleep_hist else "—"
        ui.metric_card("Sleep (last log)", sleep_val, "sleep", f"Target {profile.sleep_target_hours} hrs")
    with row2[2]:
        exercise_hist = db.get_exercise_history(user_id, limit=7)
        ui.metric_card("Exercise (7d)", f"{len(exercise_hist)} sessions", "exercise")
    with row2[3]:
        ui.metric_card("Food Score", f"{food_result.get('score', 0)}/100", "food", "Today")

    # --- Today's progress rings ---
    st.write("")
    ui.section_header("Today's Progress", "analytics")
    with ui.card_container("progress_rings"):
        pr = st.columns(4)
        with pr[0]:
            ring_val = health_result["score"] if health_result else 0
            ui.ring_progress(ring_val, "Health Score", icon_key="health_score")
        with pr[1]:
            ui.ring_progress(water_progress["percentage"], "Water Intake", icon_key="water")
        with pr[2]:
            sleep_pct = min(100, round((sleep_hist[0]["duration_hours"] / profile.sleep_target_hours) * 100)) if sleep_hist and profile.sleep_target_hours else 0
            ui.ring_progress(sleep_pct, "Sleep Target", icon_key="sleep")
        with pr[3]:
            ui.ring_progress(food_result.get("score", 0) if food_result else 0, "Food Score", icon_key="food")

    # --- Quick actions ---
    st.write("")
    ui.section_header("Quick Actions", "dashboard")
    with st.container(key="qa_wrap_dashboard"):
        qa = st.columns(4)
        with qa[0]:
            if ui.quick_action("Log Water", "water", key="qa_water"):
                st.switch_page("pages/6_Water.py")
        with qa[1]:
            if ui.quick_action("Log Sleep", "sleep", key="qa_sleep"):
                st.switch_page("pages/5_Sleep.py")
        with qa[2]:
            if ui.quick_action("Food & Meals", "meals", key="qa_food"):
                st.switch_page("pages/3_Food_and_Meals.py")
        with qa[3]:
            if ui.quick_action("Ask AI Assistant", "ai", key="qa_ai"):
                st.switch_page("pages/7_AI_Assistant.py")

    # --- Analytics grid (real data only, empty states where absent) ---
    st.write("")
    ui.section_header("Your Trends", "analytics")

    weight_hist = db.get_weight_history(user_id, limit=30)
    water_hist = db.get_water_history(user_id, days=14)
    health_hist = db.get_health_score_history(user_id, limit=30)

    c1, c2 = st.columns(2)
    with c1:
        with ui.card_container("weight_trend"):
            st.markdown("**⚖️ Weight Trend**")
            if weight_hist:
                df = pd.DataFrame(weight_hist).sort_values("logged_at")
                fig = px.line(df, x="logged_at", y="weight_kg", markers=True)
                fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260,
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, width='stretch')
            else:
                ui.empty_state("No weight history yet.<br>Add your first entry on the Health page.", "⚖️")
    with c2:
        with ui.card_container("water_intake"):
            st.markdown("**💧 Water Intake (14d)**")
            if water_hist:
                df = pd.DataFrame(water_hist)
                fig = px.bar(df, x="day", y="total")
                fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260,
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, width='stretch')
            else:
                ui.empty_state("No water history yet.<br>Log your first glass on the Water page.", "💧")

    c3, c4 = st.columns(2)
    with c3:
        with ui.card_container("health_score_trend"):
            st.markdown("**❤️ Health Score Trend**")
            if health_hist:
                df = pd.DataFrame(health_hist).sort_values("score_date")
                fig = px.line(df, x="score_date", y="score", markers=True)
                fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260,
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, width='stretch')
            else:
                ui.empty_state("No health score history yet.<br>Visit the Health page to generate one.", "❤️")
    with c4:
        with ui.card_container("food_score_today"):
            st.markdown("**🥗 Food Score (Today)**")
            breakdown = food_result.get("breakdown") if food_result else None
            if breakdown:
                df = pd.DataFrame({"Category": list(breakdown.keys()), "Points": list(breakdown.values())})
                fig = px.bar(df, x="Category", y="Points")
                fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260,
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, width='stretch')
            else:
                ui.empty_state("No food logged yet today.<br>Log a meal on the Food & Meals page.", "🥗")

    ui.disclaimer_footer()


# ---------------------------------------------------------------------------
# Sidebar (rendered once per authenticated session — brand, nav, mini profile)
# ---------------------------------------------------------------------------

def render_sidebar_and_get_nav():
    user_id = auth.current_user_id()
    user = db.get_user_by_id(user_id)
    profile_row = db.get_profile(user_id)
    profile_name = (profile_row.get("full_name") if profile_row else None) or user["username"]
    profile_goal = (profile_row.get("health_goal") if profile_row else None) or "Set your goal"

    dashboard_page = st.Page(render_dashboard_page, title="Dashboard", icon="🏠", default=True, url_path="dashboard")
    profile_page = st.Page("pages/1_Profile.py", title="Profile", icon="👤", url_path="profile")
    health_page = st.Page("pages/2_Health.py", title="Health", icon="❤️", url_path="health")
    food_page = st.Page("pages/3_Food_and_Meals.py", title="Food & Meals", icon="🥗", url_path="food-meals")
    exercise_page = st.Page("pages/4_Exercise.py", title="Exercise", icon="🏃", url_path="exercise")
    sleep_page = st.Page("pages/5_Sleep.py", title="Sleep", icon="😴", url_path="sleep")
    water_page = st.Page("pages/6_Water.py", title="Water", icon="💧", url_path="water")
    ai_page = st.Page("pages/7_AI_Assistant.py", title="AI Assistant", icon="🤖", url_path="ai-assistant")
    med_page = st.Page("pages/8_Medicine_Reminder.py", title="Medicine Reminder", icon="💊", url_path="medicine")
    reports_page = st.Page("pages/9_Reports.py", title="Reports", icon="📊", url_path="reports")
    settings_page = st.Page("pages/10_Settings.py", title="Settings", icon="⚙️", url_path="settings")

    with st.sidebar:
        if os.path.exists(config.APP_ICON):
            st.logo(config.APP_ICON, size="large")
        else:
            brand_html = (
                f'<div class="sha-sidebar-brand">{icon_html("health_score", size="1.5rem")}'
                f'<span class="sha-sidebar-brand-name">{config.APP_NAME}</span></div>'
            )
            st.markdown(brand_html, unsafe_allow_html=True)

        pg = st.navigation([
            dashboard_page, profile_page, health_page, food_page, exercise_page,
            sleep_page, water_page, ai_page, med_page, reports_page, settings_page,
        ])

        user_card_html = (
            f'<div class="sha-sidebar-user">{initials_avatar_html(profile_name, size="2.4rem")}'
            f'<div><div class="sha-sidebar-user-name">{profile_name}</div>'
            f'<div class="sha-sidebar-user-goal">{profile_goal}</div></div></div>'
        )
        st.markdown(user_card_html, unsafe_allow_html=True)
        if st.button("🚪  Logout", width='stretch', key="sidebar_logout"):
            auth.logout_user()
            st.rerun()

    return pg


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
# IMPORTANT: st.navigation() must be called on every run (even logged out).
# If it is never called, Streamlit falls back to auto-discovering everything
# under pages/ and shows raw filenames (e.g. "app") in the sidebar. Calling
# it unconditionally — with the nav hidden pre-login — suppresses that
# automatic behavior completely.
if not auth.is_authenticated():
    auth_nav = st.navigation([st.Page(render_auth_screen, title=config.APP_NAME)], position="hidden")
    auth_nav.run()
else:
    navigation = render_sidebar_and_get_nav()
    navigation.run()
