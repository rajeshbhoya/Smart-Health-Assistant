"""
Authentication: registration, login, logout, session management.
Passwords are hashed with PBKDF2-HMAC-SHA256 + a per-user random salt
(standard-library only, no plain-text storage, no reversible encryption).
"""
import hashlib
import hmac
import os
import streamlit as st

from core import database as db
from core.utils import is_valid_email, is_valid_username, is_strong_password

PBKDF2_ITERATIONS = 200_000


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return dk.hex()


def _generate_salt() -> bytes:
    return os.urandom(16)


def register_user(username: str, email: str, password: str, confirm_password: str) -> tuple[bool, str]:
    """Returns (success, message)."""
    username = username.strip()
    email = email.strip().lower()

    if not is_valid_username(username):
        return False, "Username must be 3-20 characters (letters, numbers, underscore only)."
    if not is_valid_email(email):
        return False, "Please enter a valid email address."
    if password != confirm_password:
        return False, "Passwords do not match."
    ok, msg = is_strong_password(password)
    if not ok:
        return False, msg

    if db.get_user_by_username(username):
        return False, "This username is already taken."
    if db.get_user_by_email(email):
        return False, "An account with this email already exists."

    salt = _generate_salt()
    password_hash = _hash_password(password, salt)

    try:
        db.create_user(username, email, password_hash, salt.hex())
    except db.DatabaseError:
        return False, "Registration failed due to a database error. Please try again."

    return True, "Account created successfully. You can now log in."


def login_user(username_or_email: str, password: str) -> tuple[bool, str]:
    identifier = username_or_email.strip()
    if not identifier or not password:
        return False, "Please enter both username/email and password."

    user = db.get_user_by_username(identifier) or db.get_user_by_email(identifier.lower())
    if not user:
        return False, "Invalid username/email or password."

    salt = bytes.fromhex(user["salt"])
    candidate_hash = _hash_password(password, salt)

    if not hmac.compare_digest(candidate_hash, user["password_hash"]):
        return False, "Invalid username/email or password."

    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    return True, "Login successful."


def logout_user() -> None:
    for key in ("authenticated", "user_id", "username"):
        st.session_state.pop(key, None)


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated") and st.session_state.get("user_id"))


def current_user_id() -> int | None:
    return st.session_state.get("user_id")


def require_login() -> None:
    """Call at the top of any protected page; stops rendering if not logged in."""
    if not is_authenticated():
        st.warning("Please log in to access this page.")
        st.stop()
