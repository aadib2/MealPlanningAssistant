"""Normalize Spoonacular recipe objects into a consistent dict schema."""

from __future__ import annotations

from typing import Any, Dict, List


REQUIRED_KEYS = (
    "id",
    "title",
    "readyInMinutes",
    "servings",
)

# safe handling of None values
def _num(value: Any, default: float = 0) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)

def _list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []

def to_recipe_dict(recipe: Any) -> Dict[str, Any]:
    """Convert a RecipeInformation-like object to a normalized dict."""
    if hasattr(recipe, "to_dict"):
        data = recipe.to_dict()
    elif isinstance(recipe, dict):
        data = recipe
    else:
        raise TypeError("Recipe must be a dict or have a .to_dict() method")

    normalized: Dict[str, Any] = {
        "id": _num(data.get("id"), 0),
        "title": _text(data.get("title"), ""),
        "summary": _text(data.get("summary"), ""),
        "readyInMinutes": _num(data.get("readyInMinutes"), 0),
        "servings": _num(data.get("servings"), 0),
        "preparationMinutes": _num(data.get("preparationMinutes"), 0),
        "cookingMinutes": _num(data.get("cookingMinutes"), 0),
        "pricePerServing": _num(data.get("pricePerServing"), 0),
        "healthScore": _num(data.get("healthScore"), 0),
        "spoonacularScore": _num(data.get("spoonacularScore"), 0),
        "sourceUrl": _text(data.get("sourceUrl"), ""),
        "image": _text(data.get("image"), ""),
        "cuisines": _list(data.get("cuisines")),
        "diets": _list(data.get("diets")),
        "dishTypes": _list(data.get("dishTypes")),
        "extendedIngredients": _list(data.get("extendedIngredients")),
        "instructions": _text(data.get("instructions"), ""),
    }

    return normalized
