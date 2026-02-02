"""
RAG Engine implementation with vector store and LLM integration.
"""
import os
from typing import List, Dict, Optional
import hashlib
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document

from document_processor import DocumentProcessor
from config import settings


class RAGEngine:
    """
    Main RAG engine that handles document indexing and querying.
    """
    
    def __init__(self):
        """Initialize the RAG engine with embeddings and vector store."""
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        self.document_processor = DocumentProcessor()
        self.documents_metadata = {}
        
        # Initialize or load vector store
        self.vector_store = self._initialize_vector_store()
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize QA chain
        if self.vector_store:
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(
                    search_kwargs={"k": settings.MAX_RETRIEVAL_DOCS}
                )
            )
        else:
            self.qa_chain = None
    
    def _initialize_vector_store(self):
        """Initialize or load the FAISS vector store."""
        vector_store_path = settings.VECTOR_STORE_PATH
        
        if os.path.exists(vector_store_path):
            try:
                return FAISS.load_local(
                    vector_store_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Error loading vector store: {e}")
                return None
        return None
    
    def _initialize_llm(self):
        """Initialize the LLM."""
        # Using OpenAI as default, can be swapped with other LLMs
        return OpenAI(
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    async def add_document(
        self,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> Dict:
        """
        Add a document to the RAG system.
        
        Args:
            content: Document content as bytes
            filename: Original filename
            content_type: MIME type of the document
            
        Returns:
            Dictionary with document_id and status
        """
        # Process document to extract text
        text = self.document_processor.process(content, filename, content_type)
        
        # Generate document ID
        document_id = hashlib.md5(
            f"{filename}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create Document objects with metadata
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": i
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        # Add to vector store
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(
                    search_kwargs={"k": settings.MAX_RETRIEVAL_DOCS}
                )
            )
        else:
            self.vector_store.add_documents(documents)
        
        # Save vector store
        self.vector_store.save_local(settings.VECTOR_STORE_PATH)
        
        # Store metadata
        self.documents_metadata[document_id] = {
            "filename": filename,
            "content_type": content_type,
            "num_chunks": len(chunks),
            "created_at": datetime.now().isoformat()
        }
        
        return {"document_id": document_id, "num_chunks": len(chunks)}
    
    async def query(
        self,
        query: str,
        max_results: int = 5,
        temperature: float = 0.7
    ) -> Dict:
        """
        Query the RAG system.
        
        Args:
            query: User's question
            max_results: Maximum number of source documents to return
            temperature: LLM temperature parameter
            
        Returns:
            Dictionary with answer and sources
        """
        if self.qa_chain is None:
            return {
                "answer": "No documents have been indexed yet. Please upload documents first.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Update retriever with max_results
        self.qa_chain.retriever.search_kwargs["k"] = max_results
        
        # Update LLM temperature
        self.llm.temperature = temperature
        
        # Get relevant documents
        relevant_docs = self.vector_store.similarity_search(query, k=max_results)
        
        # Run the query
        result = self.qa_chain.run(query)
        
        # Format sources
        sources = [
            {
                "document_id": doc.metadata.get("document_id"),
                "filename": doc.metadata.get("filename"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "content": doc.page_content[:200] + "..."  # Preview
            }
            for doc in relevant_docs
        ]
        
        return {
            "answer": result,
            "sources": sources,
            "confidence": None  # Can be enhanced with confidence scoring
        }
    
    async def list_documents(self) -> List[Dict]:
        """List all indexed documents."""
        return [
            {"document_id": doc_id, **metadata}
            for doc_id, metadata in self.documents_metadata.items()
        ]
    
    async def delete_document(self, document_id: str):
        """
        Delete a document from the RAG system.
        
        Note: FAISS doesn't support deletion directly, so this is a placeholder.
        In production, you might want to use a different vector store or rebuild.
        """
        if document_id in self.documents_metadata:
            del self.documents_metadata[document_id]
            # In a real implementation, you'd need to rebuild the vector store
            # without the deleted document's embeddings
        else:
            raise ValueError(f"Document {document_id} not found")
