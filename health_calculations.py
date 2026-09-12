"""
Deterministic health math: BMI, BMR/TDEE, calorie goals, wellness-oriented
Health Score and Food Score. None of this is a medical diagnosis — see
disclaimers surfaced in the UI layer.
"""
from datetime import date, datetime, timedelta
from typing import Optional

from core import database as db
from core.models import UserProfile
from core.utils import clamp


# ---------------------------------------------------------------------------
# BMI
# ---------------------------------------------------------------------------

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    if not weight_kg or not height_cm:
        return 0.0
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def bmi_category(bmi: float) -> str:
    if bmi <= 0:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


# ---------------------------------------------------------------------------
# BMR / TDEE / Calorie goals
# ---------------------------------------------------------------------------

ACTIVITY_MULTIPLIERS = {
    "Sedentary": 1.2,
    "Lightly Active": 1.375,
    "Moderately Active": 1.55,
    "Very Active": 1.725,
    "Extremely Active": 1.9,
}

GOAL_ADJUSTMENTS = {
    "Weight Loss": -500,
    "Weight Gain": 500,
    "Muscle Gain": 300,
    "Weight Maintenance": 0,
    "General Fitness": 0,
    "Improve Sleep": 0,
    "Improve Nutrition": 0,
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor equation — a well-established estimate, not a lab measurement."""
    if not all([weight_kg, height_cm, age]):
        return 0.0
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    if gender == "Male":
        return round(base + 5, 0)
    if gender == "Female":
        return round(base - 161, 0)
    return round(base - 78, 0)  # neutral midpoint estimate for other/unspecified


def calculate_tdee(bmr: float, activity_level: str) -> float:
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return round(bmr * multiplier, 0)


def calculate_goal_calories(tdee: float, health_goal: str) -> float:
    adjustment = GOAL_ADJUSTMENTS.get(health_goal, 0)
    return max(1200, round(tdee + adjustment, 0))  # safety floor, never suggest starvation-level intake


def full_calorie_estimate(profile: UserProfile) -> dict:
    bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.gender)
    tdee = calculate_tdee(bmr, profile.activity_level)
    goal_cal = calculate_goal_calories(tdee, profile.health_goal)
    return {
        "bmr": bmr,
        "tdee": tdee,
        "goal_calories": goal_cal,
        "explanation": (
            f"Estimated using the Mifflin-St Jeor formula from your age, height, weight and gender, "
            f"scaled by your '{profile.activity_level or 'unspecified'}' activity level, then adjusted "
            f"for your '{profile.health_goal or 'unspecified'}' goal. This is an estimate, not a "
            f"medical prescription."
        ),
    }


# ---------------------------------------------------------------------------
# Weight trend
# ---------------------------------------------------------------------------

def get_weight_trend(user_id: int) -> tuple[str, Optional[float], Optional[float]]:
    """Returns (trend_label, latest_weight, change_over_period)."""
    history = db.get_weight_history(user_id, limit=30)
    if not history:
        return "unknown", None, None
    latest = history[0]["weight_kg"]
    if len(history) < 2:
        return "stable", latest, 0.0
    oldest_in_window = history[-1]["weight_kg"]
    change = round(latest - oldest_in_window, 1)
    if change <= -0.5:
        trend = "losing"
    elif change >= 0.5:
        trend = "gaining"
    else:
        trend = "stable"
    return trend, latest, change


# ---------------------------------------------------------------------------
# Health Score (wellness-oriented, NOT a clinical/medical score)
# ---------------------------------------------------------------------------

def calculate_health_score(user_id: int, profile: UserProfile) -> dict:
    """
    Composite 0-100 wellness score from BMI, weight trend, water, sleep,
    activity, and food-logging consistency. Purely educational/motivational.
    """
    factors = {}
    points = 0
    max_points = 0

    # BMI component (20 pts)
    max_points += 20
    bmi = calculate_bmi(profile.weight_kg, profile.height_cm) if profile.weight_kg and profile.height_cm else 0
    if bmi:
        if 18.5 <= bmi < 25:
            bmi_pts = 20
        elif bmi < 18.5 or (25 <= bmi < 30):
            bmi_pts = 12
        else:
            bmi_pts = 6
        points += bmi_pts
        factors["bmi"] = {"value": bmi, "category": bmi_category(bmi), "points": bmi_pts}

    # Weight trend component (10 pts) — reward stability/intentional progress, not extremes
    max_points += 10
    trend, _, change = get_weight_trend(user_id)
    if trend != "unknown":
        trend_pts = 10 if trend == "stable" or (profile.health_goal in ("Weight Loss", "Weight Gain")) else 7
        points += trend_pts
        factors["weight_trend"] = {"trend": trend, "change_kg": change, "points": trend_pts}

    # Water component (20 pts)
    max_points += 20
    water_today = db.get_water_today(user_id)
    target = profile.water_target_ml or 2500
    water_ratio = clamp(water_today / target, 0, 1) if target else 0
    water_pts = round(water_ratio * 20)
    points += water_pts
    factors["water"] = {"ml_today": water_today, "target_ml": target, "points": water_pts}

    # Sleep component (20 pts)
    max_points += 20
    sleep_hist = db.get_sleep_history(user_id, limit=7)
    if sleep_hist:
        avg_sleep = sum(s["duration_hours"] for s in sleep_hist) / len(sleep_hist)
        sleep_target = profile.sleep_target_hours or 8
        sleep_ratio = clamp(avg_sleep / sleep_target, 0, 1.15)
        sleep_pts = round(clamp(sleep_ratio, 0, 1) * 20)
        points += sleep_pts
        factors["sleep"] = {"avg_hours_7d": round(avg_sleep, 1), "target_hours": sleep_target, "points": sleep_pts}

    # Activity component (15 pts)
    max_points += 15
    exercise_hist = db.get_exercise_history(user_id, limit=14)
    recent_sessions = len([e for e in exercise_hist])
    activity_pts = min(15, recent_sessions * 3)
    points += activity_pts
    factors["activity"] = {"sessions_recent": recent_sessions, "points": activity_pts}

    # Food logging consistency (15 pts) — proxy for engagement/awareness, not nutrition quality itself
    max_points += 15
    food_hist = db.get_food_history(user_id, limit=50)
    days_logged = len({f["logged_at"][:10] for f in food_hist}) if food_hist else 0
    food_pts = min(15, days_logged * 2)
    points += food_pts
    factors["food_logging"] = {"days_logged_recent": days_logged, "points": food_pts}

    score = round((points / max_points) * 100) if max_points else 0

    if score >= 80:
        category = "Excellent"
    elif score >= 60:
        category = "Good"
    elif score >= 40:
        category = "Fair"
    else:
        category = "Needs Attention"

    positives = [k for k, v in factors.items() if v.get("points", 0) >= 0.7 * (20 if k in ("bmi", "water", "sleep") else 15 if k in ("activity", "food_logging") else 10)]
    improvements = [k for k in factors if k not in positives]

    result = {
        "score": score,
        "category": category,
        "factors": factors,
        "positives": positives,
        "improvements": improvements,
    }

    db.upsert_health_score(
        user_id, date.today().isoformat(), score, category, factors,
        trend_note=f"{trend} weight trend" if trend != "unknown" else "",
    )
    return result


# ---------------------------------------------------------------------------
# Food Score (wellness-oriented, NOT clinically validated)
# ---------------------------------------------------------------------------

PROCESSED_KEYWORDS = {"chips", "soda", "candy", "fried", "fast food", "burger", "pizza", "cookie", "cake", "ice cream", "packaged"}
VEG_KEYWORDS = {"spinach", "carrot", "broccoli", "tomato", "cucumber", "salad", "vegetable", "greens", "beans", "peas"}
FRUIT_KEYWORDS = {"apple", "banana", "orange", "berries", "mango", "papaya", "fruit", "melon", "grapes"}
PROTEIN_KEYWORDS = {"dal", "lentil", "chicken", "egg", "paneer", "tofu", "fish", "chickpea", "rajma", "beans", "yogurt", "curd"}


def calculate_food_score(user_id: int, days: int = 1) -> dict:
    since = (datetime.now() - timedelta(days=days)).isoformat()
    all_food = db.get_food_history(user_id, limit=200)
    window = [f for f in all_food if f["logged_at"] >= since] if days else all_food

    if not window:
        return {"score": 0, "note": "No food logged yet for this period.", "breakdown": {}}

    items_lower = [f["food_item"].lower() for f in window]
    unique_items = set(items_lower)

    variety_pts = min(25, len(unique_items) * 3)
    veg_hit = any(any(k in item for k in VEG_KEYWORDS) for item in items_lower)
    fruit_hit = any(any(k in item for k in FRUIT_KEYWORDS) for item in items_lower)
    protein_hit = any(any(k in item for k in PROTEIN_KEYWORDS) for item in items_lower)
    processed_hits = sum(1 for item in items_lower if any(k in item for k in PROCESSED_KEYWORDS))

    balance_pts = (15 if veg_hit else 0) + (15 if fruit_hit else 0) + (20 if protein_hit else 0)
    processed_penalty = min(25, processed_hits * 8)

    raw_score = variety_pts + balance_pts - processed_penalty
    score = int(clamp(raw_score, 0, 100))

    breakdown = {
        "variety_points": variety_pts,
        "includes_vegetables": veg_hit,
        "includes_fruit": fruit_hit,
        "includes_protein_source": protein_hit,
        "processed_food_mentions": processed_hits,
    }

    suggestions = []
    if not veg_hit:
        suggestions.append("Try adding more vegetables to your meals.")
    if not fruit_hit:
        suggestions.append("Consider including a serving of fruit.")
    if not protein_hit:
        suggestions.append("Add a protein source like dal, paneer, eggs, or beans.")
    if processed_hits > 0:
        suggestions.append("Reduce highly processed/fried food where possible.")
    if not suggestions:
        suggestions.append("Great balance — keep it up!")

    return {"score": score, "breakdown": breakdown, "suggestions": suggestions}
