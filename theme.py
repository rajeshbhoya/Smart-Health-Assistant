"""
Design tokens: colors (light + dark), typography scale, icon mapping,
and the single function that injects the whole design system as CSS.

Every page calls `inject_css()` once near the top — it is idempotent
and always reflects the current light/dark mode from session_state.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Color system — CSS variables, one source of truth for both themes.
# ---------------------------------------------------------------------------

LIGHT_COLORS = {
    "bg": "#F4F7F9",
    "surface": "#FFFFFF",
    "surface-alt": "#F8FAFC",
    "primary": "#0F3D5C",        # deep navy
    "primary-strong": "#0A2B41",
    "secondary": "#3B82C4",      # soft blue
    "accent": "#14B8A6",         # teal
    "success": "#16A34A",
    "warning": "#D97706",
    "danger": "#DC2626",
    "text": "#0F172A",
    "muted": "#5B6B7C",
    "border": "#E3E9EE",
    "shadow": "rgba(15, 61, 92, 0.08)",
    "hover": "#EEF3F7",
}

DARK_COLORS = {
    "bg": "#0B1420",
    "surface": "#131F2E",
    "surface-alt": "#182636",
    "primary": "#5AA9E6",        # soft blue on dark
    "primary-strong": "#7FC1F5",
    "secondary": "#3B82C4",
    "accent": "#2DD4BF",
    "success": "#4ADE80",
    "warning": "#FBBF24",
    "danger": "#F87171",
    "text": "#E7EEF5",
    "muted": "#93A4B8",
    "border": "#22334A",
    "shadow": "rgba(0, 0, 0, 0.35)",
    "hover": "#1B2A3D",
}

# Kept for any legacy import expecting a flat COLORS dict (light values).
COLORS = LIGHT_COLORS

# ---------------------------------------------------------------------------
# Icon system — one consistent set used everywhere. Rendered inside a
# soft-gradient circular "icon container" (via CSS) so it reads as a
# unified 3D-style icon language rather than plain inline emoji.
# ---------------------------------------------------------------------------

ICONS = {
    "health_score": "❤️",
    "bmi": "⚖️",
    "weight": "⚖️",
    "water": "💧",
    "sleep": "🌙",
    "exercise": "🏃",
    "food": "🥗",
    "medicine": "💊",
    "reports": "📊",
    "profile": "👤",
    "ai": "🤖",
    "analytics": "📈",
    "calories": "🔥",
    "recipe": "📖",
    "chat": "💬",
    "settings": "⚙️",
    "dashboard": "🏠",
    "meals": "🍽️",
    "logout": "🚪",
    "trend_up": "▲",
    "trend_down": "▼",
    "check": "✓",
}

# Distinct accent colors per metric category, used for icon-container
# backgrounds so cards are visually differentiated (not all identical).
ICON_ACCENTS = {
    "health_score": ("#FDE8EA", "#B3273B"),
    "bmi": ("#E7F0FB", "#1D4E89"),
    "weight": ("#E7F0FB", "#1D4E89"),
    "water": ("#E3F4FB", "#0E7AA6"),
    "sleep": ("#EDEAFB", "#5B3FBF"),
    "exercise": ("#E9F8EF", "#1B8A4C"),
    "food": ("#EAF7EE", "#1E8A4E"),
    "calories": ("#FEF0E3", "#C2620C"),
    "medicine": ("#FBEAF0", "#B3266B"),
    "reports": ("#EAF1FB", "#1D4E89"),
    "profile": ("#EFEAFB", "#5B3FBF"),
    "ai": ("#E7F6F5", "#0F7C72"),
    "analytics": ("#EAF1FB", "#1D4E89"),
    "recipe": ("#FBF3E3", "#A16A0C"),
    "chat": ("#E7F6F5", "#0F7C72"),
    "settings": ("#F1F3F5", "#475569"),
    "dashboard": ("#E7F0FB", "#1D4E89"),
    "meals": ("#EAF7EE", "#1E8A4E"),
}

DARK_ICON_ACCENTS = {
    k: ("rgba(255,255,255,0.06)", v[1]) for k, v in ICON_ACCENTS.items()
}


def initials_avatar_html(name: str, size: str = "2.6rem") -> str:
    """Circular gradient avatar showing the user's initials — used in the
    sidebar and auth screens in place of a generic profile icon, for a more
    personal, app-like feel."""
    name = (name or "").strip()
    parts = [p for p in name.split(" ") if p]
    if len(parts) >= 2:
        initials = (parts[0][0] + parts[1][0]).upper()
    elif parts:
        initials = parts[0][:2].upper()
    else:
        initials = "?"
    return (
        f'<span class="sha-avatar" style="width:{size}; height:{size}; '
        f'font-size:calc({size} * 0.4);">{initials}</span>'
    )


def circular_progress_html(percentage: float, label: str = "", value_text: str = "",
                            size: str = "7.5rem", icon_key: str = "") -> str:
    """Conic-gradient ring gauge — the circular equivalent of the linear
    progress bar, used for BMI/health-score/water/sleep style 'today's
    progress' visuals. `value_text` is the big text shown at the ring's
    center (defaults to the rounded percentage)."""
    pct = max(0, min(100, percentage))
    center = value_text or f"{round(pct)}%"
    icon = f'<div class="sha-ring-icon">{ICONS.get(icon_key, "")}</div>' if icon_key else ""
    label_html = f'<div class="sha-ring-label">{label}</div>' if label else ""
    html = (
        f'<div class="sha-ring-wrap"><div class="sha-ring" style="width:{size}; height:{size}; '
        f'background: conic-gradient(var(--accent) {pct * 3.6}deg, var(--surface-alt) 0deg);">'
        f'<div class="sha-ring-inner">{icon}<div class="sha-ring-value">{center}</div></div>'
        f'</div>{label_html}</div>'
    )
    return html


def icon_html(icon_key: str, size: str = "1.35rem") -> str:
    """Icon rendered inside a soft rounded container for a consistent,
    slightly-3D look across the whole app. Container scales with size
    so hero-sized icons keep visible padding/background."""
    icon = ICONS.get(icon_key, "•")
    try:
        size_val = float(size.replace("rem", ""))
        box = f"{round(size_val * 1.7, 2)}rem"
        radius = f"{round(size_val * 0.75, 2)}rem"
    except ValueError:
        box, radius = "2.5rem", "14px"
    return (
        f'<span class="sha-icon-badge sha-icon-{icon_key}" '
        f'style="font-size:{size}; width:{box}; height:{box}; border-radius:{radius};">{icon}</span>'
    )


def _is_dark() -> bool:
    import streamlit as st
    return bool(st.session_state.get("dark_mode", False))


def _vars_block(colors: dict) -> str:
    lines = "\n".join(f"  --{k}: {v};" for k, v in colors.items())
    return f":root {{\n{lines}\n}}"


def inject_css() -> None:
    """Injects the full design system: base structural CSS (from
    styles.css) plus the current theme's CSS-variable values, plus
    per-icon accent colors. Safe to call on every page/rerun."""
    import streamlit as st

    dark = _is_dark()
    colors = DARK_COLORS if dark else LIGHT_COLORS
    accents = DARK_ICON_ACCENTS if dark else ICON_ACCENTS

    css_path = Path(__file__).parent / "styles.css"
    base_css = css_path.read_text() if css_path.exists() else ""

    accent_css = "\n".join(
        f'.sha-icon-{key} {{ background: {bg}; color: {fg}; }}'
        for key, (bg, fg) in accents.items()
    )

    st.markdown(
        f"<style>\n{_vars_block(colors)}\n{base_css}\n{accent_css}\n</style>",
        unsafe_allow_html=True,
    )
