# look into how to interact with spoontacular (either through sdk or requests library)
# https://github.com/ddsky/spoonacular-mcp
# https://github.com/ddsky/spoonacular-api-clients

import spoonacular
from spoonacular.rest import ApiException
from spoonacular.models.analyze_recipe_request import AnalyzeRecipeRequest
from spoonacular.models.recipe_information import RecipeInformation
from pprint import pprint
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import json

load_dotenv()

# Defining the host is optional and defaults to https://api.spoonacular.com
# See configuration.py for a list of all supported configuration parameters.
configuration = spoonacular.Configuration(
    host = "https://api.spoonacular.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: apiKeyScheme
api_key = os.getenv("SPOONACULAR_API_KEY")
if not api_key:
    raise ValueError("SPOONACULAR_API_KEY not found in environment variables. Please set it in your .env file.")
configuration.api_key['apiKeyScheme'] = api_key

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['apiKeyScheme'] = 'Bearer'


# Enter a context with an instance of the API client
with spoonacular.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = spoonacular.RecipesApi(api_client)
    # example based off docs
    # params
    query = "soup"
    maxFat = 25
    number = 2

    include_nutrition = False
    include_tags = 'vegetarian'
    excluded_tags = 'meat,dairy'
    number = 2

    try:
        # Analyze Recipe
        # api_response = api_instance.search_recipes(query, max_fat=maxFat, number=number, add_recipe_information=True)
        # api_response = api_instance.get_random_recipes(include_nutrition=include_nutrition, include_tags=include_tags, exclude_tags=excluded_tags, number=number)
        # print("The response of RecipesAPI->search_recipes:\n")

        # pprint(api_response.recipes)
        # ids = [result.to_dict()['id'] for result in res]

        # ids_str = ",".join(str(i) for i in ids)

        # # get more info about this recipe (in practice, we would call the get recipe info bulk endpoint)
        # recipe_api_response = api_instance.get_recipe_information_bulk(ids_str, include_nutrition=False)
        
        # pprint(recipe_api_response)

        # clean summary
        # summary1 = recipe_api_response[0].to_dict()['summary']

        # print(summary1)
        # cleaned = BeautifulSoup(summary1, 'html.parser').get_text(" ", strip=True)

        # print(cleaned)

        # Read raw JSON to avoid strict response validation errors
        _param = api_instance._get_random_recipes_serialize(
            include_nutrition=include_nutrition,
            include_tags=include_tags,
            exclude_tags=excluded_tags,
            number=3,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0
        )
        response_data = api_instance.api_client.call_api(*_param)
        response_data.read()
        recipe_batch = json.loads(response_data.data.decode("utf-8"))

        recipes = recipe_batch.get('recipes')

        print(recipes)

    except ApiException as e:
        print("Exception when calling : RecipesAPI->search_recipes%s\n" % e)