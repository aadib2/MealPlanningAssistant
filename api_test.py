# look into how to interact with spoontacular (either through sdk or requests library)
# https://github.com/ddsky/spoonacular-mcp
# https://github.com/ddsky/spoonacular-api-clients

import spoonacular
from spoonacular.rest import ApiException
from spoonacular.models.analyze_recipe_request import AnalyzeRecipeRequest
from pprint import pprint
from dotenv import load_dotenv
import os

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
    query = "pasta"
    maxFat = 25
    number = 2

    try:
        # Analyze Recipe
        api_response = api_instance.search_recipes(query, max_fat=maxFat, number=number)
        print("The response of RecipesAPI->search_recipes:\n")
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling : RecipesAPI->search_recipes%s\n" % e)