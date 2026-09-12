"""Shared validators, formatters, and safe-file helpers used across modules."""
import re
import io
from datetime import datetime
from typing import Optional

import config

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


def is_valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_RE.match(email.strip()))


def is_valid_username(username: str) -> bool:
    return bool(username) and bool(USERNAME_RE.match(username.strip()))


def is_strong_password(password: str) -> tuple[bool, str]:
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    return True, ""


def validate_positive_number(value, field_name: str, min_val: float = 0, max_val: float = None) -> tuple[bool, str]:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False, f"{field_name} must be a number."
    if v < min_val:
        return False, f"{field_name} must be greater than {min_val}."
    if max_val is not None and v > max_val:
        return False, f"{field_name} must be less than {max_val}."
    return True, ""


def validate_image_upload(uploaded_file) -> tuple[bool, str]:
    """Validate file type/size before it's ever passed to disk or the AI."""
    if uploaded_file is None:
        return False, "No file uploaded."

    name = getattr(uploaded_file, "name", "")
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in config.ALLOWED_IMAGE_TYPES:
        return False, f"Unsupported file type '.{ext}'. Allowed: {', '.join(config.ALLOWED_IMAGE_TYPES)}."

    size_mb = getattr(uploaded_file, "size", 0) / (1024 * 1024)
    if size_mb > config.MAX_UPLOAD_MB:
        return False, f"File too large ({size_mb:.1f} MB). Max allowed is {config.MAX_UPLOAD_MB} MB."

    return True, ""


def safe_filename(*parts: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = "_".join(str(p) for p in parts if p is not None)
    base = re.sub(r"[^a-zA-Z0-9_\-]", "_", base)
    return f"{base}_{stamp}"


def format_datetime(value: str, fmt: str = "%d %b, %I:%M %p") -> str:
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime(fmt)
    except (ValueError, TypeError):
        return value or ""


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
