"""
Reusable Streamlit UI components. Every page composes from these instead
of writing inline HTML/CSS repeatedly. Signatures are kept backward
compatible with existing call sites — new capabilities are added as
optional keyword arguments.

IMPORTANT: every HTML string passed to st.markdown(..., unsafe_allow_html=True)
is built as a SINGLE LINE with no leading whitespace. Streamlit's markdown
renderer follows CommonMark: a blank line (which conditional f-string
interpolations can produce) followed by 4+ spaces of indentation is parsed
as an indented code block, so a "pretty" multi-line/indented HTML template
can silently render as literal escaped text instead of HTML. Single-line
strings sidestep this entirely.
"""
import streamlit as st
from ui.theme import ICONS, icon_html, initials_avatar_html, circular_progress_html


def page_header(title: str, subtitle: str = "", icon_key: str = ""):
    """Consistent icon + title + subtitle header used at the top of every page."""
    badge = icon_html(icon_key, size="1.5rem") if icon_key else ""
    subtitle_html = f'<div class="sha-subtitle">{subtitle}</div>' if subtitle else ""
    html = (
        f'<div class="sha-page-header"><div class="sha-page-title-row">'
        f'{badge}<h1>{title}</h1></div>{subtitle_html}</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def metric_card(label: str, value: str, icon_key: str = "dashboard", sub: str = "",
                 trend: str = "", trend_kind: str = "neutral"):
    """trend/trend_kind are optional — existing 3-arg and 4-arg call sites
    are unaffected. trend_kind: 'up' | 'down' | 'neutral'."""
    icon = icon_html(icon_key)
    trend_html = ""
    if trend:
        arrow = ICONS["trend_up"] if trend_kind == "up" else (ICONS["trend_down"] if trend_kind == "down" else "•")
        trend_html = f'<span class="sha-trend sha-trend-{trend_kind}">{arrow} {trend}</span>'
    sub_html = f'<div class="sha-metric-sub">{sub}</div>' if sub else ""
    html = (
        f'<div class="sha-metric"><div class="sha-metric-top">{icon}{trend_html}</div>'
        f'<div><div class="sha-metric-label">{label}</div>'
        f'<div class="sha-metric-value">{value}</div>{sub_html}</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str, icon_key: str = ""):
    icon = ICONS.get(icon_key, "")
    st.markdown(f"### {icon} {title}" if icon else f"### {title}")


def avatar(name: str, size: str = "2.6rem"):
    """Renders a gradient circular avatar showing the user's initials."""
    st.markdown(initials_avatar_html(name, size), unsafe_allow_html=True)


def avatar_html(name: str, size: str = "2.6rem") -> str:
    """Inline (non-rendering) version for embedding inside other markdown blocks."""
    return initials_avatar_html(name, size)


def ring_progress(percentage: float, label: str = "", value_text: str = "",
                   size: str = "7.5rem", icon_key: str = ""):
    """Renders a conic-gradient circular progress ring — the app-style
    gauge used for BMI/health-score/water/sleep 'today's progress' visuals."""
    st.markdown(
        circular_progress_html(percentage, label, value_text, size, icon_key),
        unsafe_allow_html=True,
    )


def alert(message: str, kind: str = "info"):
    st.markdown(f'<div class="sha-alert sha-alert-{kind}">{message}</div>', unsafe_allow_html=True)


def progress_bar(percentage: float, label: str = ""):
    pct = max(0, min(100, percentage))
    label_html = f'<div style="font-size:0.85rem;color:var(--muted);margin-bottom:4px;">{label}</div>' if label else ""
    html = (
        f'<div>{label_html}<div class="sha-progress-track">'
        f'<div class="sha-progress-fill" style="width:{pct}%;"></div></div>'
        f'<div style="font-size:0.8rem;color:var(--muted);margin-top:4px;">{pct:.0f}%</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def ai_response_card(content_html: str):
    st.markdown(f'<div class="sha-ai-card">{content_html}</div>', unsafe_allow_html=True)


def food_card(name: str, category: str = "", why: str = ""):
    cat_html = f'<span class="sha-badge sha-badge-neutral">{category}</span>' if category else ""
    why_html = f'<div style="font-size:0.88rem;color:var(--muted);margin-top:0.4rem;">{why}</div>' if why else ""
    head = f'<div class="sha-food-card-head">{icon_html("food", size="1.1rem")}<h4 style="margin:0;">{name}</h4></div>'
    html = f'<div class="sha-food-card">{head}{cat_html}{why_html}</div>'
    st.markdown(html, unsafe_allow_html=True)


def recipe_card(recipe: dict):
    name = recipe.get("recipe_name") or recipe.get("food_name", "Recipe")
    nutrition = recipe.get("approx_nutrition", {})
    nutrition_line = " | ".join(f"{k.replace('_g','').replace('_',' ').title()}: {v}" for k, v in nutrition.items()) if nutrition else ""
    nutrition_html = f'<div style="font-size:0.85rem;color:var(--muted);">{nutrition_line}</div>' if nutrition_line else ""
    html = f'<div class="sha-recipe-card"><h4>📖 {name}</h4>{nutrition_html}</div>'
    st.markdown(html, unsafe_allow_html=True)
    if recipe.get("ingredients"):
        with st.expander("Ingredients"):
            for ing in recipe["ingredients"]:
                if isinstance(ing, dict):
                    st.markdown(f"- {ing.get('item', ing.get('name',''))} — {ing.get('quantity','')}")
                else:
                    st.markdown(f"- {ing}")
    if recipe.get("steps"):
        with st.expander("Steps", expanded=True):
            for i, step in enumerate(recipe["steps"], 1):
                st.markdown(f"**{i}.** {step}")
    for key, label in (
        ("healthy_modifications", "Healthy Modifications"),
        ("healthier_substitutions", "Healthier Substitutions"),
        ("serving_suggestions", "Serving Suggestions"),
        ("portion_guidance", "Portion Guidance"),
    ):
        val = recipe.get(key)
        if val:
            st.markdown(f"**{label}:**")
            if isinstance(val, list):
                for v in val:
                    st.markdown(f"- {v}")
            else:
                st.markdown(val)


def badge(text: str, kind: str = "neutral"):
    st.markdown(f'<span class="sha-badge sha-badge-{kind}">{text}</span>', unsafe_allow_html=True)


def badge_html(text: str, kind: str = "neutral") -> str:
    """Inline (non-rendering) version for embedding inside other markdown blocks."""
    return f'<span class="sha-badge sha-badge-{kind}">{text}</span>'


def info_panel(rows: list):
    """Clean label/value panel — the replacement for raw dict/JSON dumps.
    `rows` is a list of (label, value) tuples; falsy values render as '—'."""
    body = "".join(
        f'<div class="sha-info-row"><span class="sha-info-label">{label}</span>'
        f'<span class="sha-info-value">{value if value not in (None, "", []) else "—"}</span></div>'
        for label, value in rows
    )
    st.markdown(f'<div class="sha-info-panel">{body}</div>', unsafe_allow_html=True)


def quick_action(label: str, icon_key: str, key: str) -> bool:
    """Renders an app-like action tile — colored icon badge above a plain
    label button — and returns True if clicked."""
    st.markdown(f'<div class="sha-qa-icon">{icon_html(icon_key, size="1.6rem")}</div>', unsafe_allow_html=True)
    return st.button(label, width="stretch", key=key)


def data_table(df, columns: list = None, use_container_width: bool = True, hide_index: bool = True):
    """Renders a styled, responsive dataframe (CSS applies directly to
    Streamlit's dataframe widget — see div[data-testid='stDataFrame'] in
    styles.css, which handles rounding/border/horizontal-scroll)."""
    width_mode = "stretch" if use_container_width else "content"
    st.dataframe(df[columns] if columns else df, width=width_mode, hide_index=hide_index)


def chat_message(role: str, text: str, avatar_icon: str = None):
    """role: 'user' | 'assistant'."""
    icon = avatar_icon or (ICONS["profile"] if role == "user" else ICONS["ai"])
    html = (
        f'<div class="sha-chat-row {role}"><div class="sha-chat-avatar">{icon}</div>'
        f'<div class="sha-chat-bubble">{text}</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def empty_state(message: str, icon: str = "📭", action_label: str = None, action_key: str = None):
    """Optional action button returns True if clicked (existing 2-arg
    call sites are unaffected)."""
    html = f'<div class="sha-empty-state"><div class="sha-empty-icon">{icon}</div><div>{message}</div></div>'
    st.markdown(html, unsafe_allow_html=True)
    if action_label:
        return st.button(action_label, key=action_key or f"empty_action_{message[:20]}", width="content")
    return False


def loading_state(message: str = "Loading..."):
    st.markdown(f'<div class="sha-empty-state">⏳ {message}</div>', unsafe_allow_html=True)


def error_state(message: str):
    alert(f"⚠️ {message}", kind="danger")


def disclaimer_footer():
    import config
    st.markdown("---")
    st.caption(f"ℹ️ {config.DISCLAIMER}")


def card_container(key: str):
    """Returns an st.container that visually renders as a sha-card. Use as
    `with ui.card_container("some_key"):` — this is the correct way to wrap
    multiple real Streamlit elements (charts, widgets) in one styled card,
    since opening/closing a raw <div> across separate st.markdown() calls
    does NOT nest content in Streamlit's DOM (each call is an independent
    sibling element)."""
    return st.container(key=f"cardbox_{key}")


def responsive_columns(n_desktop: int):
    """Returns st.columns sized for the desktop case; Streamlit stacks
    them automatically on narrow viewports via the CSS media queries."""
    return st.columns(n_desktop)
