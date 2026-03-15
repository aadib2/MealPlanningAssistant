import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv()

# get necessary environment variables
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "spoonacular-recipes")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

_vectorstore: PineconeVectorStore | None = None


def _get_vectorstore() -> PineconeVectorStore:
    """Lazily initialize Pinecone vector store once per process."""
    global _vectorstore

    if _vectorstore is None:
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables.")

        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index(INDEX_NAME)
        _vectorstore = PineconeVectorStore(index=index, embedding=embeddings)

    return _vectorstore


def get_chunks(
    user_query: str,
    k: int = 5,
    fetch_k: int = 20,
    lambda_mult: float = 0.5,
    metadata_filter: Dict[str, Any] | None = None,
    namespace: str | None = None,
) -> List[Dict[str, Any]]:
    """Retrieve relevant chunks for a user query using MMR search.

    Returns a list of dictionaries suitable for API responses.
    """
    if not user_query or not user_query.strip():
        return []

    vectorstore = _get_vectorstore()
    docs = vectorstore.max_marginal_relevance_search(
        query=user_query,
        k=k,
        fetch_k=fetch_k,
        lambda_mult=lambda_mult,
        filter=metadata_filter,
        namespace=namespace,
    )

    results: List[Dict[str, Any]] = []
    for doc in docs:
        metadata = dict(doc.metadata or {})
        metadata["source_namespace"] = namespace if namespace else "default"
        results.append(
            {
                "content": doc.page_content,
                "metadata": metadata,
            }
        )

    return results