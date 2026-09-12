"""
Typed dataclasses used to pass structured data between layers
(especially into AI prompt builders, so the AI never has to guess shapes).
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserProfile:
    user_id: int
    full_name: str = ""
    age: Optional[int] = None
    gender: str = ""
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: str = ""
    fitness_level: str = ""
    health_goal: str = ""
    diet_type: str = ""
    food_preferences: list = field(default_factory=list)
    allergies: list = field(default_factory=list)
    daily_food_budget: Optional[float] = None
    preferred_meal_style: str = ""
    available_ingredients: list = field(default_factory=list)
    sleep_target_hours: float = 8.0
    water_target_ml: int = 2500

    @property
    def is_complete(self) -> bool:
        return bool(self.age and self.gender and self.height_cm and self.weight_kg and self.diet_type)

    @classmethod
    def from_db_row(cls, row: dict) -> "UserProfile":
        if not row:
            return cls(user_id=0)
        return cls(
            user_id=row.get("user_id", 0),
            full_name=row.get("full_name") or "",
            age=row.get("age"),
            gender=row.get("gender") or "",
            height_cm=row.get("height_cm"),
            weight_kg=row.get("weight_kg"),
            activity_level=row.get("activity_level") or "",
            fitness_level=row.get("fitness_level") or "",
            health_goal=row.get("health_goal") or "",
            diet_type=row.get("diet_type") or "",
            food_preferences=row.get("food_preferences") or [],
            allergies=row.get("allergies") or [],
            daily_food_budget=row.get("daily_food_budget"),
            preferred_meal_style=row.get("preferred_meal_style") or "",
            available_ingredients=row.get("available_ingredients") or [],
            sleep_target_hours=row.get("sleep_target_hours") or 8.0,
            water_target_ml=row.get("water_target_ml") or 2500,
        )


@dataclass
class UserContext:
    """
    The single source of truth handed to AI prompt builders.
    Anything not present here must be treated by the AI as 'unavailable' —
    prompts explicitly instruct this (see services/prompts).
    """
    profile: UserProfile
    latest_weight_kg: Optional[float] = None
    weight_trend: str = "unknown"          # 'losing' / 'gaining' / 'stable' / 'unknown'
    avg_sleep_hours_7d: Optional[float] = None
    avg_water_ml_7d: Optional[float] = None
    recent_exercise_summary: str = ""
    current_health_score: Optional[int] = None
    current_food_score: Optional[int] = None

    def to_prompt_dict(self) -> dict:
        p = self.profile
        return {
            "age": p.age or "unknown",
            "gender": p.gender or "unknown",
            "height_cm": p.height_cm or "unknown",
            "weight_kg": p.weight_kg or "unknown",
            "activity_level": p.activity_level or "unknown",
            "fitness_level": p.fitness_level or "unknown",
            "health_goal": p.health_goal or "unknown",
            "diet_type": p.diet_type or "unknown",
            "food_preferences": p.food_preferences or [],
            "allergies": p.allergies or [],
            "daily_food_budget": p.daily_food_budget or "unknown",
            "preferred_meal_style": p.preferred_meal_style or "unknown",
            "available_ingredients": p.available_ingredients or [],
            "weight_trend": self.weight_trend,
            "avg_sleep_hours_7d": self.avg_sleep_hours_7d or "unknown",
            "avg_water_ml_7d": self.avg_water_ml_7d or "unknown",
            "recent_exercise_summary": self.recent_exercise_summary or "no recent data",
            "current_health_score": self.current_health_score or "not yet calculated",
            "current_food_score": self.current_food_score or "not yet calculated",
        }


def build_user_context(user_id: int) -> "UserContext":
    """Assembles the single source-of-truth context object from the database.
    Import is local to avoid a circular import between models <-> database."""
    from core import database as db
    from core.health_calculations import get_weight_trend

    profile_row = db.get_profile(user_id)
    profile = UserProfile.from_db_row(profile_row) if profile_row else UserProfile(user_id=user_id)

    trend, latest_weight, _ = get_weight_trend(user_id)

    sleep_hist = db.get_sleep_history(user_id, limit=7)
    avg_sleep = round(sum(s["duration_hours"] for s in sleep_hist) / len(sleep_hist), 1) if sleep_hist else None

    water_hist = db.get_water_history(user_id, days=7)
    avg_water = round(sum(w["total"] for w in water_hist) / len(water_hist), 0) if water_hist else None

    exercise_hist = db.get_exercise_history(user_id, limit=7)
    exercise_summary = f"{len(exercise_hist)} session(s) logged in the last 7 days" if exercise_hist else ""

    score_hist = db.get_health_score_history(user_id, limit=1)
    current_health_score = score_hist[0]["score"] if score_hist else None

    return UserContext(
        profile=profile,
        latest_weight_kg=latest_weight,
        weight_trend=trend,
        avg_sleep_hours_7d=avg_sleep,
        avg_water_ml_7d=avg_water,
        recent_exercise_summary=exercise_summary,
        current_health_score=current_health_score,
        current_food_score=None,
    )
