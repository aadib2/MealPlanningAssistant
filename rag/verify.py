# from agents.meal_planner import create_agent
# from agents.tools import build_retriever_tool
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone



load_dotenv()
# # access vector store and create tool

# agent = create_agent()


# query = (
#     'Quick healthy, dinner under 30 minutes'
# )

# for event in agent.stream(
#     {"messages": [{"role": "user", "content": query}]},
#     stream_mode="values",
# ):
#     event["messages"][-1].pretty_print() # to view conversation

# perform similarity search on vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

pinecone_api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=pinecone_api_key)
index_name = "spoonacular-recipes"
index = pc.Index(index_name)

vectorstore = PineconeVectorStore(index=index, embedding=embeddings)

query = "Vegetarian lunch recipes that are quick"
res = vectorstore.similarity_search(
    query,
    k=3
)

print(res)

