# Vector DB using Chroma - build & persist

from langchain_chroma import Chroma

def build_load_vectorstore(documents, embeddings, persist_dir):
    '''Generate embeddings for the documents (recipes) & store them in vector store'''
    vector_store = Chroma(
        collection_name="recipe_collection",
        embedding_function=embeddings,
        persist_directory=persist_dir # where to save data locally
    )

    document_ids = vector_store.add_documents(documents=documents) # need to get docs

    print(document_ids[:3]) # for validation



