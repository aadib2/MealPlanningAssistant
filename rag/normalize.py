"""Normalize Spoonacular recipe objects into a consistent dict schema."""

from __future__ import annotations

from typing import Any, Dict


REQUIRED_KEYS = (
    "id",
    "title",
    "summary",
    "readyInMinutes",
    "servings",
)

def _num(value, default=0):
    return default if value is None else value

def to_recipe_dict(recipe: Any) -> Dict[str, Any]:
    """Convert a RecipeInformation-like object to a normalized dict."""
    if hasattr(recipe, "to_dict"):
        data = recipe.to_dict()
    elif isinstance(recipe, dict):
        data = recipe
    else:
        raise TypeError("Recipe must be a dict or have a .to_dict() method")

    # Ensure required keys + defaults
    normalized: Dict[str, Any] = {
        "id": data.get("id"),
        "title": data.get("title", ""),
        "summary": data.get("summary", ""),
        "readyInMinutes": _num(data.get("readyInMinutes", 0)),
        "servings": _num(data.get("servings", 0)),
        # optional fields with defaults
        "preparationMinutes": _num(data.get("preparationMinutes", 0)),
        "cookingMinutes": _num(data.get("cookingMinutes", 0)),
        "pricePerServing": _num(data.get("pricePerServing", 0)),
        "healthScore": _num(data.get("healthScore", 0)),
        "spoonacularScore": _num(data.get("spoonacularScore", 0)),
        "sourceUrl": data.get("sourceUrl", ""),
        "image": data.get("image", ""),
        "cuisines": data.get("cuisines", []),
        "diets": data.get("diets", []),
        "dishTypes": data.get("dishTypes", []),
        "extendedIngredients": data.get("extendedIngredients", []),
        "instructions": data.get("instructions", ""),
    }
    _assert_required(normalized)
    return normalized


def _assert_required(recipe: Dict[str, Any]) -> None:
    for key in REQUIRED_KEYS:
        if key not in recipe or recipe.get(key) in (None, ""):
            raise ValueError(f"Missing required key: {key}")
