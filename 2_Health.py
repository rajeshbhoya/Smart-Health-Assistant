import streamlit as st
import pandas as pd
import plotly.express as px

import config
from core import database as db, auth
from core.models import UserProfile
from core.health_calculations import (
    calculate_bmi, bmi_category, full_calorie_estimate, calculate_health_score,
)
from ui import components as ui
from ui.theme import inject_css

inject_css()
auth.require_login()

user_id = auth.current_user_id()
profile_row = db.get_profile(user_id)

ui.page_header("Health", "Track your key health metrics and understand your progress.", "health_score")

if not profile_row:
    ui.empty_state("Complete your profile first to unlock BMI, calorie, and health score insights.", "👤")
    st.stop()

profile = UserProfile.from_db_row(profile_row)

tab_overview, tab_weight, tab_calories, tab_score = st.tabs(["📏 BMI & Overview", "⚖️ Weight Tracker", "🔥 Calorie Calculator", "❤️ Health Score"])

with tab_overview:
    bmi = calculate_bmi(profile.weight_kg, profile.height_cm)
    # BMI 15-35 mapped onto a 0-100 ring so the healthy range (~18.5-25) sits
    # in the middle of the gauge rather than clipping at either end.
    bmi_ring_pct = max(0, min(100, round((bmi - 15) / (35 - 15) * 100))) if bmi else 0
    r1, r2 = st.columns([1, 2])
    with r1:
        with ui.card_container("bmi_ring"):
            ui.ring_progress(bmi_ring_pct, "Body Mass Index", value_text=f"{bmi}", size="8.5rem", icon_key="bmi")
            st.markdown(f'<div style="text-align:center;">{ui.badge_html(bmi_category(bmi), "info")}</div>', unsafe_allow_html=True)
    with r2:
        c2, c3 = st.columns(2)
        with c2:
            ui.metric_card("Height", f"{profile.height_cm} cm", "bmi")
        with c3:
            ui.metric_card("Weight", f"{profile.weight_kg} kg", "weight")
        ui.alert("BMI is a general screening indicator, not a diagnosis of body composition or health.", "info")

with tab_weight:
    st.markdown("#### Log Today's Weight")
    with st.form("weight_form"):
        new_weight = st.number_input("Weight (kg)", min_value=25.0, max_value=250.0, value=float(profile.weight_kg or 65.0))
        submitted = st.form_submit_button("Add Entry")
    if submitted:
        db.add_weight(user_id, new_weight)
        db.upsert_profile(user_id, {"weight_kg": new_weight})
        st.success("Weight logged.")
        st.rerun()

    history = db.get_weight_history(user_id, limit=60)
    if history:
        df = pd.DataFrame(history).sort_values("logged_at")
        df["bmi"] = df["weight_kg"].apply(lambda w: calculate_bmi(w, profile.height_cm))
        fig_w = px.line(df, x="logged_at", y="weight_kg", markers=True, title="Weight Trend")
        fig_w.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
        st.plotly_chart(fig_w, width='stretch')

        fig_b = px.line(df, x="logged_at", y="bmi", markers=True, title="BMI Trend")
        fig_b.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
        st.plotly_chart(fig_b, width='stretch')
    else:
        ui.empty_state("No weight entries yet. Log your first one above.", "⚖️")

with tab_calories:
    if profile.is_complete:
        est = full_calorie_estimate(profile)
        c1, c2, c3 = st.columns(3)
        with c1:
            ui.metric_card("BMR (est.)", f"{int(est['bmr'])} kcal", "calories")
        with c2:
            ui.metric_card("TDEE (est.)", f"{int(est['tdee'])} kcal", "calories")
        with c3:
            ui.metric_card("Goal Calories", f"{int(est['goal_calories'])} kcal", "calories")
        st.info(est["explanation"])
        from datetime import date
        db.upsert_calorie_log(user_id, date.today().isoformat(), est["bmr"], est["tdee"], est["goal_calories"])
    else:
        ui.empty_state("Complete your profile (age, height, weight, gender) for a calorie estimate.", "🔥")

with tab_score:
    result = calculate_health_score(user_id, profile)
    c1, c2 = st.columns([1, 2])
    with c1:
        with ui.card_container("health_score_ring"):
            ui.ring_progress(result["score"], "Overall Health Score", value_text=f"{result['score']}", size="8.5rem", icon_key="health_score")
            st.markdown(f'<div style="text-align:center;">{ui.badge_html(result["category"], "info")}</div>', unsafe_allow_html=True)
    with c2:
        if result["positives"]:
            st.markdown("**✅ Doing well:** " + ", ".join(p.replace("_", " ").title() for p in result["positives"]))
        if result["improvements"]:
            st.markdown("**🎯 Room to improve:** " + ", ".join(p.replace("_", " ").title() for p in result["improvements"]))
    ui.alert("This wellness score is educational and motivational — it is not a clinical or medically validated diagnosis.", "warning")

    score_hist = db.get_health_score_history(user_id, limit=30)
    if len(score_hist) > 1:
        df = pd.DataFrame(score_hist).sort_values("score_date")
        fig = px.line(df, x="score_date", y="score", markers=True, title="Health Score Trend")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
        st.plotly_chart(fig, width='stretch')

ui.disclaimer_footer()
