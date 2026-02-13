import spoonacular
from spoonacular.rest import ApiException
from spoonacular.models.recipe_information import RecipeInformation
from spoonacular.models.get_random_recipes200_response import GetRandomRecipes200Response
from pprint import pprint


from pprint import pprint
from dotenv import load_dotenv
import os
import json

'''
Link to docs of supported meal types: https://spoonacular.com/food-api/docs#Meal-Types
Link to docs of supported cuisines: https://spoonacular.com/food-api/docs#Cuisines
'''

load_dotenv()

# define host
configuration = spoonacular.Configuration(
    host = "https://api.spoonacular.com"
)

# Configure API key authorization: apiKeyScheme
api_key = os.getenv("SPOONACULAR_API_KEY")
if not api_key:
    raise ValueError("SPOONACULAR_API_KEY not found in environment variables. Please set it in your .env file.")
configuration.api_key['apiKeyScheme'] = api_key


def get_recipes_info():
    # can be modified later
    output = {}
    cuisines = ['Italian', 'Mexican', 'Asian'] # 'American', 'Indian', 'Mediterranean']
    meal_types = ['breakfast'] # 'lunch', 'dinner'] #, 'snack']
    batch_size = 1 # can be modified

    # we can get 35 recipes each time for each category (cuisine, meal_type) --> 18 * 35 = 630
    all_recipes = []
    for cuisine in cuisines:
        for meal_type in meal_types:
            with spoonacular.ApiClient(configuration) as api_client:
                api_instance = spoonacular.RecipesApi(api_client)
                
                try:
                    recipe_batch = api_instance.get_random_recipes(
                        include_nutrition=False,
                        include_tags=f'{cuisine},{meal_type}',
                        number=batch_size
                    ) # returns a GetRandomRecipes200Response

                    all_recipes.extend([r.to_dict() for r in recipe_batch.recipes])
                except ApiException as e:
                    print("Exception when calling : RecipesAPI/get_random_recipes %s\n" % e)
    
    print(len(all_recipes)) # for debugging --> should return 630
    payload = {"recipes": all_recipes} # convert to a json payload once all recipes have been fetched
    return payload

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw_recipes.json")

def ingest_recipes():
    #load from disk if already fetched
    # if os.path.exists(RAW_DATA_PATH):
    #     print("Loading from cache...")
    #     with open(RAW_DATA_PATH, 'r') as f:
    #         return json.load(f)
    
    # otherwise call API and save
    print("Fetching from API...")   
    recipes_payload = get_recipes_info() # Your API calls here
    
    os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True) # make sure the parent directory exists
    with open(RAW_DATA_PATH, 'w') as f:
        json.dump(recipes_payload, f)
        print('json file written to successfully!')

    return recipes_payload


if __name__ == "__main__": # for testing
    ingested_recipes = ingest_recipes()

    print(len(ingested_recipes['recipes'])) # should return 3 total
    # pprint(ingested_recipes['recipes']) 