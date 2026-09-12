"""Sanity tests for the database layer, using a temporary SQLite file."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Point at a temp DB before importing config/database
tmp_dir = tempfile.mkdtemp()
os.environ["DB_PATH"] = str(Path(tmp_dir) / "test_health.db")

import config
config.DB_PATH = os.environ["DB_PATH"]

from core import database as db

db.init_db()


def test_create_and_fetch_user():
    user_id = db.create_user("testuser", "test@example.com", "hash", "salt")
    user = db.get_user_by_id(user_id)
    assert user["username"] == "testuser"


def test_profile_upsert_and_isolation():
    uid1 = db.create_user("alice_t", "alice@example.com", "h", "s")
    uid2 = db.create_user("bob_t", "bob@example.com", "h", "s")
    db.upsert_profile(uid1, {"full_name": "Alice", "diet_type": "Vegetarian", "allergies": ["Peanuts"]})
    db.upsert_profile(uid2, {"full_name": "Bob", "diet_type": "Non-Vegetarian", "allergies": ["None"]})

    p1 = db.get_profile(uid1)
    p2 = db.get_profile(uid2)
    assert p1["full_name"] == "Alice"
    assert p2["full_name"] == "Bob"
    assert p1["diet_type"] != p2["diet_type"]


def test_water_log_and_daily_total():
    uid = db.create_user("carol_t", "carol@example.com", "h", "s")
    db.add_water(uid, 250)
    db.add_water(uid, 500)
    total = db.get_water_today(uid)
    assert total == 750


def test_chat_history_isolated_per_user():
    uid1 = db.create_user("dave_t", "dave@example.com", "h", "s")
    uid2 = db.create_user("erin_t", "erin@example.com", "h", "s")
    db.add_chat_message(uid1, "user", "hello from dave")
    db.add_chat_message(uid2, "user", "hello from erin")
    h1 = db.get_chat_history(uid1)
    h2 = db.get_chat_history(uid2)
    assert len(h1) == 1 and h1[0]["message"] == "hello from dave"
    assert len(h2) == 1 and h2[0]["message"] == "hello from erin"
