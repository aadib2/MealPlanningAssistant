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


def to_recipe_dict(recipe: Any) -> Dict[str, Any]:
    """Convert a RecipeInformation-like object to a normalized dict.

    Accepts either a RecipeInformation object with a .to_dict() method or an
    already-converted dict. Ensures required keys exist and applies sane
    defaults for optional fields.
    """

    if hasattr(recipe, "to_dict"):
        data = recipe.to_dict()
    elif isinstance(recipe, dict):
        data = recipe
    else:
        raise TypeError("recipe must be a RecipeInformation object or dict")

    normalized: Dict[str, Any] = {
        "id": data.get("id"),
        "title": data.get("title", ""),
        "summary": data.get("summary", ""),
        "readyInMinutes": data.get("readyInMinutes", -1),
        "preparationMinutes": data.get("preparationMinutes", -1),
        "cookingMinutes": data.get("cookingMinutes", -1),
        "servings": data.get("servings", 0),
        "pricePerServing": data.get("pricePerServing", 0),
        "cuisines": data.get("cuisines", []) or [],
        "diets": data.get("diets", []) or [],
        "dishTypes": data.get("dishTypes", []) or [],
        "extendedIngredients": data.get("extendedIngredients", []) or [],
        "sourceUrl": data.get("sourceUrl", ""),
        "healthScore": data.get("healthScore", 0),
        "spoonacularScore": data.get("spoonacularScore", 0),
        "image": data.get("image", ""),
    }

    _assert_required(normalized)
    return normalized


def _assert_required(recipe: Dict[str, Any]) -> None:
    """Fail fast if required keys are missing or empty."""

    missing = [key for key in REQUIRED_KEYS if recipe.get(key) in (None, "")]
    if missing:
        raise ValueError(f"Recipe missing required fields: {', '.join(missing)}")
