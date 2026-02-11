from rag.ingestion import get_recipes_info
from langchain_core.documents import Document
from typing import List

from bs4 import BeautifulSoup # for html cleaning


def build_documents(recipes) -> List[Document]:

    documents = []
    for recipe_dict in recipes:
        # Create rich text for embedding (semantic search)
        
        # # first convert each recipe (a RecipeInformation object) to dict --> should already be a validated dict
        # recipe_dict = recipe.to_dict()

        text = f"""

        {recipe_dict['title']}

        Summary: {clean_summary(recipe_dict)}
            
        Ingredients: {format_ingredients(recipe_dict.get('extendedIngredients', []))}
        
        Cuisines: {', '.join(recipe_dict.get('cuisines', []))}
        Diets: {', '.join(recipe_dict.get('diets', []))}
        Dish Types: {', '.join(recipe_dict.get('dishTypes', []))}
        Cooking Method: {instructions_summary(recipe_dict)}
        Price per serving: ${recipe_dict.get('pricePerServing', 0) / 100:.2f}

        """
        
        # Metadata for filtering (NOT embedded)
        metadata = {
            'id': recipe_dict['id'],
            'title': recipe_dict['title'],
            'readyInMinutes': recipe_dict['readyInMinutes'],
            'preparationMinutes': recipe_dict.get('preparationMinutes', -1),
            'cookingMinutes': recipe_dict.get('cookingMinutes', -1),
            'servings': recipe_dict['servings'],
            'pricePerServing': recipe_dict.get('pricePerServing', 0), # budget filtering
            'pricePerServingDisplay': recipe_dict.get('pricePerServing', 0) / 100,  # Dollars (for display)
            'cuisines': recipe_dict.get('cuisines', []),
            'diets': recipe_dict.get('diets', []),
            'dishTypes': recipe_dict.get('dishTypes', []),
            'sourceUrl': recipe_dict.get('sourceUrl', ''),
            'healthScore': recipe_dict['healthScore'],
            'spoonacularScore': recipe_dict['spoonacularScore'],
            'image': recipe_dict.get('image', ''),
            # Store full recipe JSON if needed
            # 'source_data': json.dumps(recipe)
        }
        
        documents.append(Document(page_content=text, metadata=metadata))
    
    return documents

def format_ingredients(ingredients):
    """Extract ingredient names from Spoonacular format"""

    if len(ingredients) == 0:
        return ''

    return ', '.join([ing.get('name', ing.get('original', '')) # considers name then falls back to original
                     for ing in ingredients])  # get all incredients and save to comma separated string

def instructions_summary(recipe):
    """Extract cooking method summary rather than full instructions"""
    instructions_summ =  f"Cooking method: {recipe.get('cookingMinutes', '')} min cooking. " \
                         f"{recipe.get('preparationMinutes')} min prep."

    return instructions_summ

def clean_summary(recipe):
    summary = recipe.get("summary", "")
    return BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)