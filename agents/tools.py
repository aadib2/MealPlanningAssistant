from langchain.tools import tool

def build_retriever_tool(vector_store):
    @tool(response_format="content_and_artifact")
    def retrieve_context(query: str):
        """Retrieve recipes relevant to a query."""
        docs = vector_store.similarity_search(query, k=5)
        serialized = "\n\n".join(
            f"Source: {d.metadata}\nContent: {d.page_content}" for d in docs
        )
        return serialized, docs
    return retrieve_context