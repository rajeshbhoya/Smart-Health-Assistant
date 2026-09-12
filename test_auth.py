"""Sanity tests for auth hashing/validation logic that doesn't need Streamlit session_state."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.auth import _hash_password, _generate_salt
from core.utils import is_valid_email, is_valid_username, is_strong_password


def test_password_hash_deterministic_with_same_salt():
    salt = _generate_salt()
    h1 = _hash_password("MyPassword123", salt)
    h2 = _hash_password("MyPassword123", salt)
    assert h1 == h2


def test_password_hash_differs_with_different_salt():
    h1 = _hash_password("MyPassword123", _generate_salt())
    h2 = _hash_password("MyPassword123", _generate_salt())
    assert h1 != h2


def test_email_validation():
    assert is_valid_email("user@example.com") is True
    assert is_valid_email("not-an-email") is False


def test_username_validation():
    assert is_valid_username("valid_user1") is True
    assert is_valid_username("ab") is False


def test_password_strength():
    ok, _ = is_strong_password("abcdefgh")
    assert ok is False  # no digit
    ok2, _ = is_strong_password("abc12345")
    assert ok2 is True
