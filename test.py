from dotenv import load_dotenv
import os

load_dotenv()


key = os.getenv("SPOONACULAR_API_KEY")

print(key)
