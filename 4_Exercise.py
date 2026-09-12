import streamlit as st
import pandas as pd
import plotly.express as px

import config
from core import database as db, auth
from core.models import build_user_context
from core import exercise_ai
from services import ai_client
from ui import components as ui
from ui.theme import inject_css

inject_css()
auth.require_login()
user_id = auth.current_user_id()

ui.page_header("Exercise", "AI-assisted workout plans tailored to your fitness level and goal.", "exercise")

profile_row = db.get_profile(user_id)
if not profile_row:
    ui.empty_state("Complete your profile first for a tailored exercise plan.", "👤")
    st.stop()

context = build_user_context(user_id)
profile = context.profile

exercise_hist_7d = db.get_exercise_history(user_id, limit=50)
from datetime import datetime, timedelta
week_ago = (datetime.now() - timedelta(days=7)).isoformat()
sessions_7d = [e for e in exercise_hist_7d if str(e.get("logged_at", "")) >= week_ago]
total_minutes_7d = sum(e.get("duration_min", 0) for e in sessions_7d)

m1, m2, m3 = st.columns(3)
with m1:
    ui.metric_card("Sessions (7d)", str(len(sessions_7d)), "exercise")
with m2:
    ui.metric_card("Active Minutes (7d)", f"{total_minutes_7d} min", "exercise")
with m3:
    ui.metric_card("Fitness Level", profile.fitness_level or "—", "exercise")

tab_plan, tab_log, tab_history = st.tabs(["🧠 AI Plan", "➕ Log Exercise", "📈 History"])

def _render_exercise_plan(plan: dict):
    st.markdown(f"### {plan.get('session_title', 'Your Session')}")
    for section, label in (("warm_up", "🔥 Warm-Up"), ("cool_down", "🧘 Cool-Down")):
        items = plan.get(section) or []
        if items:
            st.markdown(f"**{label}**")
            for i in items:
                st.markdown(f"- {i}")
    main = plan.get("main_exercises") or []
    if main:
        st.markdown("**💪 Main Exercises**")
        for ex in main:
            st.markdown(f"- **{ex.get('name','')}** — {ex.get('sets_or_duration','')} _{ex.get('notes','')}_")
    ui.alert(plan.get("caution", "Consult a professional if you have any health conditions."), "warning")


with tab_plan:
    minutes = st.slider("Minutes available today", 10, 90, 30, step=5)
    if st.button("🏃 Generate Exercise Plan"):
        with st.spinner("Building your session..."):
            try:
                plan = exercise_ai.get_ai_exercise_plan(context, minutes)
                _render_exercise_plan(plan)
            except ai_client.AIError as e:
                ui.error_state(str(e))
                fallback = exercise_ai.get_fallback_plan(profile.fitness_level)
                st.info("Showing a general fallback plan instead:")
                _render_exercise_plan(fallback)

with tab_log:
    with st.form("exercise_log_form"):
        activity = st.text_input("Activity", placeholder="e.g. Running, Yoga, Strength Training")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=300, value=30)
        intensity = st.selectbox("Intensity", ["Light", "Moderate", "Intense"])
        submitted = st.form_submit_button("➕ Log Session")
    if submitted:
        if not activity.strip():
            ui.error_state("Please enter an activity name.")
        else:
            db.add_exercise(user_id, activity.strip(), int(duration), intensity)
            st.success("Exercise logged!")
            st.rerun()

with tab_history:
    history = db.get_exercise_history(user_id, limit=30)
    if history:
        df = pd.DataFrame(history)
        st.dataframe(df[["activity", "duration_min", "intensity", "logged_at"]], width='stretch', hide_index=True)
        fig = px.bar(df.sort_values("logged_at"), x="logged_at", y="duration_min", color="intensity", title="Exercise Duration Over Time")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
        st.plotly_chart(fig, width='stretch')
    else:
        ui.empty_state("No exercise logged yet.", "🏃")

ui.disclaimer_footer()
