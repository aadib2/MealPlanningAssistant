import getpass
import os
import json
from normalize import to_recipe_dict
from validate import validate_batch
from transform import build_documents

# necessary imports
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pinecone import ServerlessSpec
from uuid import uuid4

load_dotenv() # loads necessary .env variables (openai & pinecone)

# necessary paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw_recipes.json") # path for json data


def create_docs():
    # load recipe json
    with open(RAW_DATA_PATH, 'r') as f:
        payload = json.load(f)

    raw_recipes = payload.get('recipes', [])

    # normalize
    normalized = [to_recipe_dict(r) for r in raw_recipes]

    # validate
    valid_recipes, invalid_recipes = validate_batch(normalized)
    
    if invalid_recipes:
        print(f"Invalid recipes: {len(invalid_recipes)}")
        for v in invalid_recipes: # detailed overview
            print(v['index'])
            print(v['errors'])

    # build docs
    documents = build_documents(valid_recipes)

    return documents


def build_index(documents):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small") # dim = 1536

    # pinecone setup
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    pc = Pinecone(api_key=pinecone_api_key)
    index_name = "spoonacular-recipes"

    if not pc.has_index(index_name):
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
    
    index = pc.Index(index_name) # connect to existing index
    
    # init vector store
    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings,
    )

    uuids = [str(uuid4()) for _ in range(len(documents))] # create ids for each doc
    vector_store.add_documents(documents=documents, ids=uuids)


if __name__ == "__main__":
    documents = create_docs()
    build_index(documents)

