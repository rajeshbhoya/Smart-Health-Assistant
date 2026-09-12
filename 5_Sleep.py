import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import time

import config
from core import database as db, auth
from core.sleep_analyzer import log_sleep, get_weekly_summary
from ui import components as ui
from ui.theme import inject_css

inject_css()
auth.require_login()
user_id = auth.current_user_id()

ui.page_header("Sleep", "Log your sleep and track your weekly rest trends.", "sleep")

profile_row = db.get_profile(user_id)
sleep_target = profile_row.get("sleep_target_hours", 8.0) if profile_row else 8.0

tab_log, tab_summary = st.tabs(["➕ Log Sleep", "📊 Weekly Summary"])

with tab_log:
    with st.form("sleep_form"):
        c1, c2 = st.columns(2)
        with c1:
            sleep_time_val = st.time_input("Sleep Time", value=time(23, 0))
        with c2:
            wake_time_val = st.time_input("Wake Time", value=time(7, 0))
        quality = st.slider("Sleep Quality (optional)", 1, 5, 3)
        submitted = st.form_submit_button("😴 Log Sleep")
    if submitted:
        duration = log_sleep(user_id, sleep_time_val, wake_time_val, quality)
        st.success(f"Logged {duration} hours of sleep.")
        st.rerun()

with tab_summary:
    summary = get_weekly_summary(user_id, sleep_target)
    ring_pct = min(100, round((summary["avg_hours"] / sleep_target) * 100)) if sleep_target and summary["avg_hours"] else 0
    r1, r2 = st.columns([1, 2])
    with r1:
        with ui.card_container("sleep_ring"):
            ui.ring_progress(ring_pct, "of sleep target", value_text=f"{summary['avg_hours']}h", size="8.5rem", icon_key="sleep")
    with r2:
        c2, c3 = st.columns(2)
        with c2:
            ui.metric_card("Avg Quality (7d)", f"{summary['avg_quality']}/5" if summary["avg_quality"] else "—", "sleep")
        with c3:
            ui.metric_card("Entries Logged", str(summary["entries"]), "sleep")

    for s in summary["suggestions"]:
        ui.alert(s, "info")

    history = db.get_sleep_history(user_id, limit=14)
    if history:
        df = pd.DataFrame(history).sort_values("logged_at")
        fig = px.bar(df, x="logged_at", y="duration_hours", title="Sleep Duration Trend")
        fig.add_hline(y=sleep_target, line_dash="dash", annotation_text="Target")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
        st.plotly_chart(fig, width='stretch')
    else:
        ui.empty_state("No sleep logged yet.", "😴")

ui.disclaimer_footer()
