"""Sanity tests for the deterministic diet/allergy filtering layer."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.food_ai import get_filtered_catalog, filter_ai_food_list, _is_allergen_conflict


def test_vegetarian_excludes_nonveg_category():
    catalog = get_filtered_catalog("Vegetarian", ["None"])
    assert "Non-vegetarian foods" not in catalog


def test_nonveg_includes_nonveg_category():
    catalog = get_filtered_catalog("Non-Vegetarian", ["None"])
    assert "Non-vegetarian foods" in catalog


def test_allergen_conflict_detection():
    assert _is_allergen_conflict("Roasted Peanuts", ["Peanuts"]) is True
    assert _is_allergen_conflict("Apple", ["Peanuts"]) is False


def test_filter_ai_food_list_removes_meat_for_vegetarian():
    items = [{"name": "Grilled Chicken"}, {"name": "Paneer Curry"}]
    filtered = filter_ai_food_list(items, "Vegetarian", ["None"])
    names = [i["name"] for i in filtered]
    assert "Grilled Chicken" not in names
    assert "Paneer Curry" in names


def test_filter_ai_food_list_removes_allergen():
    items = [{"name": "Almond Milk"}, {"name": "Rice"}]
    filtered = filter_ai_food_list(items, "Vegetarian", ["Tree Nuts"])
    names = [i["name"] for i in filtered]
    assert "Almond Milk" not in names
    assert "Rice" in names
