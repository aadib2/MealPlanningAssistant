"""Validate normalized recipe dictionaries before embedding/storage."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .normalize import REQUIRED_KEYS # imported from normalize.py


LIST_KEYS = (
	"cuisines",
	"diets",
	"dishTypes",
	"extendedIngredients",
)

NUMERIC_KEYS = (
	"id",
	"readyInMinutes",
	"preparationMinutes",
	"cookingMinutes",
	"servings",
	"pricePerServing",
	"healthScore",
	"spoonacularScore",
)

STRING_KEYS = (
	"title",
	"summary",
	"sourceUrl",
	"image",
)


def validate_recipe_dict(recipe: Dict[str, Any]) -> List[str]:
	"""Return a list of validation errors for a normalized recipe dict."""

	errors: List[str] = []

	for key in REQUIRED_KEYS:
		if key not in recipe or recipe.get(key) in (None, ""):
			errors.append(f"missing required field: {key}")

    # validate types for each of these
	for key in LIST_KEYS:
		value = recipe.get(key, [])
		if not isinstance(value, list):
			errors.append(f"{key} must be a list")

	for key in NUMERIC_KEYS:
		value = recipe.get(key, 0)
		if value is None or not isinstance(value, (int, float)):
			errors.append(f"{key} must be a number")

	for key in STRING_KEYS:
		value = recipe.get(key, "")
		if value is None or not isinstance(value, str):
			errors.append(f"{key} must be a string")

	return errors


def validate_batch(
	recipes: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
	"""Split recipes (dict objects) into valid and invalid buckets with error details."""

	valid: List[Dict[str, Any]] = []
	invalid: List[Dict[str, Any]] = []

	for index, recipe in enumerate(recipes):
		errors = validate_recipe_dict(recipe)
		if errors:
			invalid.append({"index": index, "errors": errors, "recipe": recipe})
		else:
			valid.append(recipe)

	return valid, invalid
