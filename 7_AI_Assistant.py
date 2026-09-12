import streamlit as st
import config
from core import database as db, auth
from core.models import build_user_context
from core.voice_assistant import is_voice_available, transcribe_audio_bytes
from services import ai_client
from services.prompts import chat_prompts
from ui import components as ui
from ui.theme import inject_css

inject_css()
auth.require_login()
user_id = auth.current_user_id()

ui.page_header("AI Assistant", "Ask about food, sleep, water, or exercise — personalized to your profile.", "ai")
ui.alert("This assistant gives general wellness information. It cannot diagnose, prescribe, or replace a doctor.", "warning")

context = build_user_context(user_id)

col_chat, col_side = st.columns([3, 1])

with col_side:
    if st.button("🗑️ Clear Chat History", width='stretch'):
        db.clear_chat_history(user_id)
        st.rerun()

    st.markdown("#### 🎤 Voice Input")
    if is_voice_available():
        audio = st.audio_input("Record a question")
        if audio is not None and st.button("Transcribe & Send"):
            success, result = transcribe_audio_bytes(audio.getvalue())
            if success:
                st.session_state["voice_transcript"] = result
            else:
                ui.error_state(result)
    else:
        st.caption("🎙️ Voice input isn't available in this environment. You can still type your questions below — the assistant works fully with text.")

QUICK_PROMPTS = [
    "What should I eat today?",
    "How can I improve my sleep?",
    "What can I cook with rice and dal?",
    "Give me a simple healthy dinner.",
]

with col_chat:
    history = db.get_chat_history(user_id, limit=100)
    chat_container = st.container(height=420)
    with chat_container:
        if not history:
            ui.empty_state("Ask me anything about food, sleep, water, or exercise!", "💬")
        for msg in history:
            avatar = "👤" if msg["role"] == "user" else "🤖"
            with st.chat_message("user" if msg["role"] == "user" else "assistant", avatar=avatar):
                st.markdown(msg["message"])

    if not history:
        with st.container(key="chat_suggested_prompts"):
            qp_cols = st.columns(len(QUICK_PROMPTS))
            quick_pick = None
            for i, prompt_text in enumerate(QUICK_PROMPTS):
                with qp_cols[i]:
                    if st.button(prompt_text, width='stretch', key=f"qp_{i}"):
                        quick_pick = prompt_text
    else:
        quick_pick = None

    default_text = st.session_state.pop("voice_transcript", "") or quick_pick
    user_input = st.chat_input("Ask about food, sleep, water, exercise...")
    if default_text and not user_input:
        user_input = default_text

    if user_input:
        db.add_chat_message(user_id, "user", user_input)
        with st.spinner("Thinking..."):
            try:
                ctx_dict = context.to_prompt_dict()
                prompt = chat_prompts.build_chat_prompt(ctx_dict, user_input, history)
                response = ai_client.chat(chat_prompts.SYSTEM_PROMPT, prompt)
            except ai_client.AIKeyMissingError as e:
                response = f"⚠️ {e}"
            except ai_client.AIError as e:
                response = f"⚠️ {e}"
        db.add_chat_message(user_id, "assistant", response)
        st.rerun()

ui.disclaimer_footer()
