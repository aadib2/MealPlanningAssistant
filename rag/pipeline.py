import getpass
import os
import json
from normalize import to_recipe_dict
from validate import validate_batch
from transform import build_documents
from dotenv import load_dotenv

# necessary imports
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain.tools import tool
from langchain.agents import create_agent

load_dotenv()


# load recipes
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw_recipes.json")
with open(DATA_PATH, 'r') as f:
    payload = json.load(f)

raw_recipes = payload.get('recipes', [])

# normalize
normalized = [to_recipe_dict(r) for r in raw_recipes]

# validate
valid_recipes, invalid_recipes = validate_batch(normalized)
for v in invalid_recipes:
    print(v['index'])
    print(v['errors'])

print(f"Valid recipes: {len(valid_recipes)}, Invalid: {len(invalid_recipes)}")

# build docs
documents = build_documents(valid_recipes)

for doc in documents: # for testing
     print(f'{doc.page_content}\n')
     print(doc.metadata)

model = ChatAnthropic(model="claude-sonnet-4-520250929")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = Chroma(
    collection_name="recipe_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db" # where to save data locally
)

document_ids = vector_store.add_documents(documents=documents) # need to get docs

# rag tool
@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=5) # will retrieve top 5 candidate recipes
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

tools = [retrieve_context]
# if desired, specify custom instructions
prompt = (
    "You have acess to a tool that retrieves relevant recipes and meals from a recipe database."
    "Use the tool to help answer user queries."
)

agent = create_agent(model, tools, system_prompt=prompt)
