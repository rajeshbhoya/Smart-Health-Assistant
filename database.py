"""
Database layer: connection management, schema initialization, and
parameterized CRUD helpers ("repository" style) used by every feature module.

No raw SQL is ever built from string-formatted user input.
"""
import sqlite3
import json
import logging
from contextlib import contextmanager
from datetime import datetime, date
from typing import Optional, Any

import config

logger = logging.getLogger("smart_health.database")


class DatabaseError(Exception):
    """Raised for any unexpected database failure. Caught by UI layer."""
    pass


@contextmanager
def get_connection():
    """Short-lived connection per operation (safe for SQLite + Streamlit reruns)."""
    conn = None
    try:
        conn = sqlite3.connect(config.DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.exception("Database error")
        raise DatabaseError(str(e)) from e
    finally:
        if conn:
            conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name TEXT, age INTEGER, gender TEXT,
    height_cm REAL, weight_kg REAL,
    activity_level TEXT, fitness_level TEXT, health_goal TEXT,
    diet_type TEXT, food_preferences TEXT, allergies TEXT,
    daily_food_budget REAL, preferred_meal_style TEXT,
    available_ingredients TEXT,
    sleep_target_hours REAL DEFAULT 8,
    water_target_ml INTEGER DEFAULT 2500,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weight_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    weight_kg REAL NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS water_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_ml INTEGER NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sleep_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sleep_time TEXT, wake_time TEXT,
    duration_hours REAL NOT NULL,
    quality_rating INTEGER,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exercise_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity TEXT NOT NULL, duration_min INTEGER, intensity TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS food_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    food_item TEXT NOT NULL, meal_type TEXT, source TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meal_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_type TEXT, description TEXT, image_path TEXT,
    ai_analysis_json TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS health_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score_date TEXT NOT NULL,
    score INTEGER NOT NULL, category TEXT,
    factors_json TEXT, trend_note TEXT,
    UNIQUE(user_id, score_date)
);

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    input_text TEXT, recipe_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL, message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medicine_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    medicine_name TEXT NOT NULL, reminder_time TEXT NOT NULL,
    frequency TEXT, notes TEXT, is_enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_calorie_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date TEXT NOT NULL,
    bmr REAL, tdee REAL, goal_calories REAL, notes TEXT,
    UNIQUE(user_id, log_date)
);

CREATE TABLE IF NOT EXISTS weekly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    week_start TEXT, week_end TEXT,
    summary_json TEXT, pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY, value TEXT
);

CREATE INDEX IF NOT EXISTS idx_weight_user ON weight_history(user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_water_user ON water_history(user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_sleep_user ON sleep_history(user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_exercise_user ON exercise_history(user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_food_user ON food_history(user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_meal_user ON meal_history(user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_health_scores_user ON health_scores(user_id, score_date);
"""

SCHEMA_VERSION = "1"


def init_db() -> None:
    """Create tables if they don't exist. Never drops/overwrites existing data."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        row = conn.execute("SELECT value FROM schema_meta WHERE key='version'").fetchone()
        if row is None:
            conn.execute("INSERT INTO schema_meta (key, value) VALUES ('version', ?)", (SCHEMA_VERSION,))


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row is not None else None


def _rows_to_list(rows) -> list[dict]:
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def create_user(username: str, email: str, password_hash: str, salt: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, salt),
        )
        return cur.lastrowid


def get_user_by_username(username: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return _row_to_dict(row)


def get_user_by_email(email: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return _row_to_dict(row)


def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_dict(row)


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

def upsert_profile(user_id: int, data: dict) -> None:
    json_fields = ("food_preferences", "allergies", "available_ingredients")
    payload = dict(data)
    for f in json_fields:
        if f in payload and not isinstance(payload[f], str):
            payload[f] = json.dumps(payload[f] or [])

    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        cols = list(payload.keys())
        if existing:
            set_clause = ", ".join(f"{c} = ?" for c in cols)
            conn.execute(
                f"UPDATE profiles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                [*payload.values(), user_id],
            )
        else:
            cols_sql = ", ".join(cols + ["user_id"])
            placeholders = ", ".join(["?"] * (len(cols) + 1))
            conn.execute(
                f"INSERT INTO profiles ({cols_sql}) VALUES ({placeholders})",
                [*payload.values(), user_id],
            )


def get_profile(user_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        profile = _row_to_dict(row)
    if profile:
        for f in ("food_preferences", "allergies", "available_ingredients"):
            try:
                profile[f] = json.loads(profile.get(f) or "[]")
            except (json.JSONDecodeError, TypeError):
                profile[f] = []
    return profile


# ---------------------------------------------------------------------------
# Time-series generic insert/fetch (weight, water, sleep, exercise, food)
# ---------------------------------------------------------------------------

def add_weight(user_id: int, weight_kg: float) -> None:
    with get_connection() as conn:
        conn.execute("INSERT INTO weight_history (user_id, weight_kg) VALUES (?, ?)", (user_id, weight_kg))


def get_weight_history(user_id: int, limit: int = 90) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM weight_history WHERE user_id = ? ORDER BY logged_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return _rows_to_list(rows)


def add_water(user_id: int, amount_ml: int) -> None:
    with get_connection() as conn:
        conn.execute("INSERT INTO water_history (user_id, amount_ml) VALUES (?, ?)", (user_id, amount_ml))


def get_water_today(user_id: int) -> int:
    today = date.today().isoformat()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount_ml), 0) as total FROM water_history "
            "WHERE user_id = ? AND date(logged_at) = ?",
            (user_id, today),
        ).fetchone()
        return row["total"] if row else 0


def get_water_history(user_id: int, days: int = 7) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT date(logged_at) as day, SUM(amount_ml) as total FROM water_history "
            "WHERE user_id = ? AND logged_at >= date('now', ?) "
            "GROUP BY day ORDER BY day",
            (user_id, f"-{days} days"),
        ).fetchall()
        return _rows_to_list(rows)


def add_sleep(user_id: int, sleep_time: str, wake_time: str, duration_hours: float, quality_rating: Optional[int]) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sleep_history (user_id, sleep_time, wake_time, duration_hours, quality_rating) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, sleep_time, wake_time, duration_hours, quality_rating),
        )


def get_sleep_history(user_id: int, limit: int = 30) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sleep_history WHERE user_id = ? ORDER BY logged_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return _rows_to_list(rows)


def add_exercise(user_id: int, activity: str, duration_min: int, intensity: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO exercise_history (user_id, activity, duration_min, intensity) VALUES (?, ?, ?, ?)",
            (user_id, activity, duration_min, intensity),
        )


def get_exercise_history(user_id: int, limit: int = 30) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM exercise_history WHERE user_id = ? ORDER BY logged_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return _rows_to_list(rows)


def add_food_log(user_id: int, food_item: str, meal_type: str, source: str = "manual") -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO food_history (user_id, food_item, meal_type, source) VALUES (?, ?, ?, ?)",
            (user_id, food_item, meal_type, source),
        )


def get_food_history(user_id: int, limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM food_history WHERE user_id = ? ORDER BY logged_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return _rows_to_list(rows)


def add_meal(user_id: int, meal_type: str, description: str, image_path: Optional[str], ai_analysis: Optional[dict]) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO meal_history (user_id, meal_type, description, image_path, ai_analysis_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, meal_type, description, image_path, json.dumps(ai_analysis) if ai_analysis else None),
        )
        return cur.lastrowid


def get_meal_history(user_id: int, limit: int = 30) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM meal_history WHERE user_id = ? ORDER BY logged_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    result = _rows_to_list(rows)
    for r in result:
        if r.get("ai_analysis_json"):
            try:
                r["ai_analysis"] = json.loads(r["ai_analysis_json"])
            except json.JSONDecodeError:
                r["ai_analysis"] = None
    return result


# ---------------------------------------------------------------------------
# Health scores / calorie logs
# ---------------------------------------------------------------------------

def upsert_health_score(user_id: int, score_date: str, score: int, category: str, factors: dict, trend_note: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO health_scores (user_id, score_date, score, category, factors_json, trend_note) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id, score_date) DO UPDATE SET "
            "score=excluded.score, category=excluded.category, "
            "factors_json=excluded.factors_json, trend_note=excluded.trend_note",
            (user_id, score_date, score, category, json.dumps(factors), trend_note),
        )


def get_health_score_history(user_id: int, limit: int = 30) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM health_scores WHERE user_id = ? ORDER BY score_date DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return _rows_to_list(rows)


def upsert_calorie_log(user_id: int, log_date: str, bmr: float, tdee: float, goal_calories: float, notes: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO daily_calorie_logs (user_id, log_date, bmr, tdee, goal_calories, notes) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id, log_date) DO UPDATE SET "
            "bmr=excluded.bmr, tdee=excluded.tdee, goal_calories=excluded.goal_calories, notes=excluded.notes",
            (user_id, log_date, bmr, tdee, goal_calories, notes),
        )


# ---------------------------------------------------------------------------
# Recipes / Chat / Reminders / Reports
# ---------------------------------------------------------------------------

def save_recipe(user_id: int, source_type: str, input_text: str, recipe: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO recipes (user_id, source_type, input_text, recipe_json) VALUES (?, ?, ?, ?)",
            (user_id, source_type, input_text, json.dumps(recipe)),
        )
        return cur.lastrowid


def get_recipes(user_id: int, source_type: Optional[str] = None, limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        if source_type:
            rows = conn.execute(
                "SELECT * FROM recipes WHERE user_id = ? AND source_type = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, source_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM recipes WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
    result = _rows_to_list(rows)
    for r in result:
        try:
            r["recipe"] = json.loads(r["recipe_json"])
        except json.JSONDecodeError:
            r["recipe"] = {}
    return result


def add_chat_message(user_id: int, role: str, message: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)",
            (user_id, role, message),
        )


def get_chat_history(user_id: int, limit: int = 100) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_history WHERE user_id = ? ORDER BY created_at ASC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return _rows_to_list(rows)


def clear_chat_history(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))


def add_reminder(user_id: int, medicine_name: str, reminder_time: str, frequency: str, notes: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO medicine_reminders (user_id, medicine_name, reminder_time, frequency, notes) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, medicine_name, reminder_time, frequency, notes),
        )
        return cur.lastrowid


def get_reminders(user_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM medicine_reminders WHERE user_id = ? ORDER BY reminder_time",
            (user_id,),
        ).fetchall()
        return _rows_to_list(rows)


def set_reminder_enabled(user_id: int, reminder_id: int, enabled: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE medicine_reminders SET is_enabled = ? WHERE id = ? AND user_id = ?",
            (int(enabled), reminder_id, user_id),
        )


def delete_reminder(user_id: int, reminder_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM medicine_reminders WHERE id = ? AND user_id = ?", (reminder_id, user_id))


def save_weekly_report(user_id: int, week_start: str, week_end: str, summary: dict, pdf_path: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO weekly_reports (user_id, week_start, week_end, summary_json, pdf_path) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, week_start, week_end, json.dumps(summary), pdf_path),
        )
        return cur.lastrowid


def get_weekly_reports(user_id: int, limit: int = 12) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM weekly_reports WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return _rows_to_list(rows)
