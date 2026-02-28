import getpass
import os
import json
from normalize import to_recipe_dict
from validate import validate_batch
from transform import build_documents
from dotenv import load_dotenv

# # necessary imports
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pinecone import ServerlessSpec
from uuid import uuid4

load_dotenv()


# load recipes
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw_recipes.json")
PERSIST_DIR = os.path.join(BASE_DIR, "chroma_langchain_db")

def build_index():
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

    for doc in documents[:10]: # for testing
        print(f'{doc.page_content}\n')
        print(doc.metadata)

    print(len(documents))

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
    
    index = pc.Index(index_name)
    
    # init vector store
    vector_store = PineconeVectorStore(
        index=index,
        embeddings=embeddings,
    )

    uuids = [str(uuid4()) for _ in range(len(documents))] # create ids for each doc
    vector_store.add_documents(documents=documents, ids=uuids)


if __name__ == "__main__":
    build_index()

    # a test - similarity search

# # rag tool
# @tool(response_format="content_and_artifact")
# def retrieve_context(query: str):
#     """Retrieve information to help answer a query."""
#     retrieved_docs = vector_store.similarity_search(query, k=5) # will retrieve top 5 candidate recipes
#     serialized = "\n\n".join(
#         (f"Source: {doc.metadata}\nContent: {doc.page_content}")
#         for doc in retrieved_docs
#     )
#     return serialized, retrieved_docs

# tools = [retrieve_context]
# # if desired, specify custom instructions
# prompt = (
#     "You have acess to a tool that retrieves relevant recipes and meals from a recipe database."
#     "Use the tool to help answer user queries."
# )

# agent = create_agent(model, tools, system_prompt=prompt)
