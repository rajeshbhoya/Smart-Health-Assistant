"""
Lightweight sanity tests for the deterministic calculation layer.
Run with: pytest tests/
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.health_calculations import (
    calculate_bmi, bmi_category, calculate_bmr, calculate_tdee, calculate_goal_calories,
)


def test_bmi_normal():
    bmi = calculate_bmi(70, 175)
    assert 22.0 <= bmi <= 23.0
    assert bmi_category(bmi) == "Normal"


def test_bmi_underweight():
    bmi = calculate_bmi(45, 175)
    assert bmi_category(bmi) == "Underweight"


def test_bmr_positive():
    bmr = calculate_bmr(70, 175, 30, "Male")
    assert bmr > 0


def test_tdee_scales_with_activity():
    bmr = 1600
    sedentary = calculate_tdee(bmr, "Sedentary")
    active = calculate_tdee(bmr, "Very Active")
    assert active > sedentary


def test_goal_calories_never_below_floor():
    tdee = 1300
    goal = calculate_goal_calories(tdee, "Weight Loss")
    assert goal >= 1200
