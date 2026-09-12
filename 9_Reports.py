import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

import config
from core import database as db, auth
from core.models import build_user_context
from core.report_generator import generate_weekly_report
from services import ai_client
from ui import components as ui
from ui.theme import inject_css

inject_css()
auth.require_login()
user_id = auth.current_user_id()

ui.page_header("Reports", "Analytics across your tracked data, plus a downloadable weekly AI report.", "reports")

profile_row = db.get_profile(user_id)
if not profile_row:
    ui.empty_state("Complete your profile to unlock analytics and reports.", "👤")
    st.stop()

tab_analytics, tab_weekly = st.tabs(["📈 Analytics", "📄 Weekly AI Report"])

with tab_analytics:
    st.markdown("#### Trends Across Your Tracked Data")

    weight_hist = db.get_weight_history(user_id, limit=60)
    water_hist = db.get_water_history(user_id, days=30)
    sleep_hist = db.get_sleep_history(user_id, limit=30)
    exercise_hist = db.get_exercise_history(user_id, limit=30)
    health_hist = db.get_health_score_history(user_id, limit=30)

    if weight_hist:
        df = pd.DataFrame(weight_hist).sort_values("logged_at")
        fig = px.line(df, x="logged_at", y="weight_kg", markers=True, title="Weight")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=300)
        with ui.card_container("report_weight"):
            st.plotly_chart(fig, width='stretch')
    else:
        ui.empty_state("No weight data yet.", "⚖️")

    c1, c2 = st.columns(2)
    with c1:
        if water_hist:
            df = pd.DataFrame(water_hist)
            fig = px.bar(df, x="day", y="total", title="Water (30d)")
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=280)
            with ui.card_container("report_water"):
                st.plotly_chart(fig, width='stretch')
        else:
            ui.empty_state("No water data yet.", "💧")
    with c2:
        if sleep_hist:
            df = pd.DataFrame(sleep_hist).sort_values("logged_at")
            fig = px.bar(df, x="logged_at", y="duration_hours", title="Sleep (30d)")
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=280)
            with ui.card_container("report_sleep"):
                st.plotly_chart(fig, width='stretch')
        else:
            ui.empty_state("No sleep data yet.", "😴")

    c3, c4 = st.columns(2)
    with c3:
        if exercise_hist:
            df = pd.DataFrame(exercise_hist).sort_values("logged_at")
            fig = px.bar(df, x="logged_at", y="duration_min", color="intensity", title="Exercise (30d)")
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=280)
            with ui.card_container("report_exercise"):
                st.plotly_chart(fig, width='stretch')
        else:
            ui.empty_state("No exercise data yet.", "🏃")
    with c4:
        if health_hist:
            df = pd.DataFrame(health_hist).sort_values("score_date")
            fig = px.line(df, x="score_date", y="score", markers=True, title="Health Score (30d)")
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=280)
            with ui.card_container("report_health"):
                st.plotly_chart(fig, width='stretch')
        else:
            ui.empty_state("No health score history yet.", "❤️")

with tab_weekly:
    st.markdown("#### Weekly AI Health Report")
    st.caption("Generated from your actual tracked data for the last 7 days.")

    if st.button("📄 Generate This Week's Report", width='stretch'):
        with st.spinner("Analyzing your week and building the PDF..."):
            try:
                context = build_user_context(user_id)
                user = db.get_user_by_id(user_id)
                result = generate_weekly_report(user_id, user["username"], context)
                st.success("Report generated!")

                wd = result["weekly_data"]
                ai_sum = result["ai_summary"]

                rc1, rc2 = st.columns([1, 3])
                with rc1:
                    ui.ring_progress(wd["health_score"], "Health Score", value_text=str(wd["health_score"]), size="7.5rem", icon_key="health_score")
                with rc2:
                    st.markdown(f"### {ai_sum.get('headline', 'Weekly Summary')}")
                    st.markdown(ai_sum.get("summary_paragraph", ""))

                cols = st.columns(4)
                with cols[0]:
                    ui.metric_card("Health Score", str(wd["health_score"]), "health_score")
                with cols[1]:
                    ui.metric_card("Food Score", str(wd["food_score"]), "food")
                with cols[2]:
                    ui.metric_card("Avg Sleep", f"{wd['avg_sleep_hours']} hrs", "sleep")
                with cols[3]:
                    ui.metric_card("Avg Water", f"{wd['avg_daily_water_ml']} ml", "water")

                with open(result["pdf_path"], "rb") as f:
                    st.download_button("⬇️ Download PDF Report", f, file_name=Path(result["pdf_path"]).name, mime="application/pdf")
            except ai_client.AIError as e:
                ui.error_state(str(e))
            except Exception:
                ui.error_state("Could not generate the report right now. Please try again.")

    st.markdown("---")
    st.markdown("#### Report History")
    past_reports = db.get_weekly_reports(user_id, limit=12)
    if not past_reports:
        ui.empty_state("No reports generated yet.", "📄")
    else:
        for r in past_reports:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{r['week_start']} → {r['week_end']}**")
            with c2:
                p = Path(r["pdf_path"])
                if p.exists():
                    with open(p, "rb") as f:
                        st.download_button("⬇️ Download", f, file_name=p.name, key=f"dl_{r['id']}")

ui.disclaimer_footer()
