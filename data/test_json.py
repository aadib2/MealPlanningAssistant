# load the json file
import os
import json
from bs4 import BeautifulSoup

json_data_path = os.path.join(os.path.dirname(__file__), 'raw_recipes.json')

if os.path.exists(json_data_path):
    print(json_data_path)
    
    with open(json_data_path, 'r') as f:
        json_recipes = json.load(f)

        print(json_recipes['recipes'][0]['id'])

        summary = json_recipes['recipes'][0]['instructions']
        print(BeautifulSoup(summary, "html.parser").get_text(" ", strip=True))
else:
    print("Path doesn't exist!")