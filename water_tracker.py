"""Water intake tracking helpers built on top of the database layer."""
from core import database as db
from core.utils import clamp


def log_water(user_id: int, amount_ml: int) -> None:
    if amount_ml <= 0:
        raise ValueError("Water amount must be a positive number.")
    db.add_water(user_id, amount_ml)


def get_today_progress(user_id: int, target_ml: int) -> dict:
    consumed = db.get_water_today(user_id)
    ratio = clamp(consumed / target_ml, 0, 1.5) if target_ml else 0
    return {
        "consumed_ml": consumed,
        "target_ml": target_ml,
        "percentage": round(ratio * 100),
        "remaining_ml": max(0, target_ml - consumed),
    }


def get_weekly_chart_data(user_id: int) -> list[dict]:
    return db.get_water_history(user_id, days=7)
