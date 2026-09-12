import streamlit as st
from datetime import time

import config
from core import database as db, auth
from ui import components as ui
from ui.theme import inject_css

inject_css()
auth.require_login()
user_id = auth.current_user_id()

ui.page_header("Medicine Reminder", "Simple scheduling reminders — not a prescribing or diagnostic tool.", "medicine")
ui.alert("This is a reminder tool only. It does not recommend, prescribe, or advise changes to any medication.", "warning")

with ui.card_container("reminder_form"):
    st.markdown("#### ➕ Add a Reminder")
    with st.form("reminder_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            med_name = st.text_input("Medicine Name", placeholder="e.g. Vitamin D")
        with c2:
            reminder_time = st.time_input("Reminder Time", value=time(9, 0))
        with c3:
            frequency = st.selectbox("Frequency", ["Once Daily", "Twice Daily", "Three Times Daily", "Weekly", "As Needed"])
        notes = st.text_area("Notes (optional)", placeholder="e.g. take after breakfast")
        submitted = st.form_submit_button("💊 Add Reminder", width='stretch', type="primary")

if submitted:
    if not med_name.strip():
        ui.error_state("Please enter a medicine name.")
    else:
        db.add_reminder(user_id, med_name.strip(), reminder_time.strftime("%H:%M"), frequency, notes.strip())
        st.success("Reminder added.")
        st.rerun()

st.write("")
ui.section_header("Your Reminders", "medicine")
reminders = db.get_reminders(user_id)
if not reminders:
    ui.empty_state("No reminders set yet. Add your first one above.", "💊")
else:
    for r in reminders:
        with ui.card_container(f"reminder_{r['id']}"):
            c1, c2, c3, c4, c5 = st.columns([3, 1.6, 1.8, 1, 1])
            with c1:
                st.markdown(f"**💊 {r['medicine_name']}**")
                if r["notes"]:
                    st.caption(r["notes"])
            with c2:
                st.markdown(f"🕐 {r['reminder_time']}")
            with c3:
                ui.badge(r["frequency"], "info")
            with c4:
                enabled = st.toggle("On", value=bool(r["is_enabled"]), key=f"toggle_{r['id']}")
                if enabled != bool(r["is_enabled"]):
                    db.set_reminder_enabled(user_id, r["id"], enabled)
                    st.rerun()
            with c5:
                if st.button("🗑️", key=f"del_{r['id']}", help="Delete reminder"):
                    db.delete_reminder(user_id, r["id"])
                    st.rerun()

ui.disclaimer_footer()
