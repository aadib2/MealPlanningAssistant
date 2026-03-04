from langchain_core.documents import Document
from typing import List

from bs4 import BeautifulSoup # for html cleaning

# to ensure doesn't break vectorDB typing
def _safe_join(values):
    if not isinstance(values, list):
        return ""
    return ", ".join(str(v) for v in values if v is not None)

def build_documents(recipes) -> List[Document]:

    documents = []
    for recipe_dict in recipes:
        # Create rich text for embedding (semantic search)
        
        # # first convert each recipe (a RecipeInformation object) to dict --> should already be a validated dict
        # recipe_dict = recipe.to_dict()

        text = f"""

        {recipe_dict.get('title', '')}

        Summary: {clean_summary(recipe_dict.get('summary', ''))}
        Ingredients: {format_ingredients(recipe_dict.get('extendedIngredients', []))}
        Instructions Summary: {clean_summary(recipe_dict.get('instructions', ''))}

        Cuisines: {_safe_join(recipe_dict.get('cuisines', []))}
        Diets: {_safe_join(recipe_dict.get('diets', []))}
        Dish Types: {_safe_join(recipe_dict.get('dishTypes', []))}
        Cooking Method: {cooking_summary(recipe_dict)}
        Price per serving: ${recipe_dict.get('pricePerServing', 0) / 100:.2f}

        """
        
        # Metadata for filtering (NOT embedded)
        metadata = {
            "id": int(recipe_dict.get("id", 0)),
            "title": str(recipe_dict.get("title", "")),
            "readyInMinutes": float(recipe_dict.get("readyInMinutes", 0)),
            "preparationMinutes": float(recipe_dict.get("preparationMinutes", 0)),
            "cookingMinutes": float(recipe_dict.get("cookingMinutes", 0)),
            "servings": float(recipe_dict.get("servings", 0)),
            "pricePerServing": float(recipe_dict.get("pricePerServing", 0)),
            "pricePerServingDollars": round(float(recipe_dict.get("pricePerServing", 0)) / 100, 2),
            # flatten list metadata for VectorDB compatibility
            "cuisines": _safe_join(recipe_dict.get("cuisines", [])),
            "diets": _safe_join(recipe_dict.get("diets", [])),
            "dishTypes": _safe_join(recipe_dict.get("dishTypes", [])),
            "sourceUrl": str(recipe_dict.get("sourceUrl", "")),
            "healthScore": float(recipe_dict.get("healthScore", 0)),
            "spoonacularScore": float(recipe_dict.get("spoonacularScore", 0)),
            "image": str(recipe_dict.get("image", "")),
        }
        
        documents.append(Document(page_content=text, metadata=metadata))
    
    return documents

# helper functions
def format_ingredients(ingredients):
    """Extract ingredient names from Spoonacular format"""

    if len(ingredients) == 0:
        return ''

    return ', '.join([ing.get('name', ing.get('original', '')) # considers name then falls back to original
                     for ing in ingredients])  # get all incredients and save to comma separated string

def cooking_summary(recipe):
    """Extract cooking method summary rather than full instructions"""

    keys = ['cookingMinutes', 'preparationMinutes', 'readyInMinutes']

    minute_types = {}
    for key in keys:
        minutes = recipe.get(key)

        if minutes in (0, None, -1):  # likely unknown; avoid misleading the model
            minute_types[key] = 'Null'
        else:
            minute_types[key] = minutes


    cooking_summ =  f"{minute_types['cookingMinutes']} min cooking. " \
                         f"{minute_types['preparationMinutes']} min prep. " \
                         f"{minute_types['readyInMinutes']} min total time. "

    return cooking_summ

def clean_summary(summary):
    return BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)