"""Sleep logging, summaries, and general (non-diagnostic) wellness suggestions."""
from datetime import datetime, time

from core import database as db


def compute_duration_hours(sleep_time: time, wake_time: time) -> float:
    sleep_dt = datetime.combine(datetime.today(), sleep_time)
    wake_dt = datetime.combine(datetime.today(), wake_time)
    if wake_dt <= sleep_dt:
        wake_dt = wake_dt.replace(day=wake_dt.day + 1) if False else wake_dt
        # crossed midnight
        from datetime import timedelta
        wake_dt += timedelta(days=1)
    delta = wake_dt - sleep_dt
    return round(delta.total_seconds() / 3600, 1)


def log_sleep(user_id: int, sleep_time: time, wake_time: time, quality_rating: int | None) -> float:
    duration = compute_duration_hours(sleep_time, wake_time)
    db.add_sleep(user_id, sleep_time.strftime("%H:%M"), wake_time.strftime("%H:%M"), duration, quality_rating)
    return duration


def get_weekly_summary(user_id: int, sleep_target_hours: float = 8.0) -> dict:
    history = db.get_sleep_history(user_id, limit=7)
    if not history:
        return {"avg_hours": 0, "avg_quality": None, "entries": 0, "suggestions": ["Log your sleep to see trends here."]}

    avg_hours = round(sum(h["duration_hours"] for h in history) / len(history), 1)
    qualities = [h["quality_rating"] for h in history if h["quality_rating"]]
    avg_quality = round(sum(qualities) / len(qualities), 1) if qualities else None

    suggestions = []
    if avg_hours < sleep_target_hours - 0.5:
        suggestions.append("You're averaging less sleep than your target — consider an earlier wind-down routine.")
    elif avg_hours > sleep_target_hours + 1.5:
        suggestions.append("You're sleeping notably more than your target — if this is new, consider tracking how you feel.")
    else:
        suggestions.append("Your sleep duration is close to your target — nice consistency.")
    if avg_quality is not None and avg_quality < 3:
        suggestions.append("Your logged sleep quality has been on the lower side — a consistent bedtime may help.")

    return {"avg_hours": avg_hours, "avg_quality": avg_quality, "entries": len(history), "suggestions": suggestions}
