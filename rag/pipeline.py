import getpass
import os

# ensure we have all api keys
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = getpass.getpass("Enter your Anthropic API key: ")

if "LANGSMITH_API_KEY" not in os.environ:
    os.environ["LANGSMITH_API_KEY"] = getpass.getpass("Enter your LangSmith API key: ")
    os.environ["LANGSMITH_TRACING"] = "true"

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

# necessary imports
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain.tools import tool
from langchain.agents import create_agent

model = ChatAnthropic(model="claude-sonnet-4-520250929")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = Chroma(
    collection_name="recipe_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db" # where to save data locally
)


document_ids = vector_store.add_documents(documents=documents) # need to get docs

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
