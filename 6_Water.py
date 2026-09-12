import streamlit as st
import pandas as pd
import plotly.express as px

import config
from core import database as db, auth
from core.water_tracker import log_water, get_today_progress, get_weekly_chart_data
from ui import components as ui
from ui.theme import inject_css

inject_css()
auth.require_login()
user_id = auth.current_user_id()

ui.page_header("Water", "Stay on top of your daily hydration goal.", "water")

profile_row = db.get_profile(user_id)
target_ml = profile_row.get("water_target_ml", 2500) if profile_row else 2500

progress = get_today_progress(user_id, target_ml)
with ui.card_container("water_ring"):
    c1, c2 = st.columns([1, 2])
    with c1:
        ui.ring_progress(progress["percentage"], "of daily target", size="9rem", icon_key="water")
    with c2:
        st.markdown("#### Today's Water Intake")
        ui.progress_bar(progress["percentage"])
        st.caption(f"{progress['consumed_ml']} ml of {progress['target_ml']} ml target — {progress['remaining_ml']} ml remaining")
        if progress["percentage"] >= 100:
            ui.alert("🎉 Great job — you've hit today's water target!", "success")

st.markdown("#### Quick Add")
with st.container(key="qa_wrap_water"):
    cols = st.columns(4)
    amounts = [250, 500, 750, 1000]
    for i, amt in enumerate(amounts):
        with cols[i]:
            st.markdown('<div class="sha-qa-icon">💧</div>', unsafe_allow_html=True)
            if st.button(f"+{amt} ml", width='stretch', key=f"water_quick_{amt}"):
                log_water(user_id, amt)
                st.rerun()

with st.expander("Custom amount"):
    custom = st.number_input("Amount (ml)", min_value=1, max_value=3000, value=200)
    if st.button("➕ Add Custom Amount"):
        log_water(user_id, custom)
        st.rerun()

st.markdown("#### Weekly Trend")
weekly = get_weekly_chart_data(user_id)
if weekly:
    df = pd.DataFrame(weekly)
    fig = px.bar(df, x="day", y="total", title="Water Intake — Last 7 Days")
    fig.add_hline(y=target_ml, line_dash="dash", annotation_text="Target")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
    st.plotly_chart(fig, width='stretch')
else:
    ui.empty_state("No water logged yet this week.", "💧")

ui.disclaimer_footer()
