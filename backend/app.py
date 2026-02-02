"""
Main FastAPI application for RAG/LLM backend.
"""
import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from rag_engine import RAGEngine
from config import settings

app = FastAPI(
    title="RAG/LLM API",
    description="A generic RAG-based LLM application API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG engine
rag_engine = RAGEngine()


# Request/Response Models
class QueryRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5
    temperature: Optional[float] = 0.7


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    confidence: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    version: str


# API Routes
@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the RAG system with a question.
    """
    try:
        result = await rag_engine.query(
            query=request.query,
            max_results=request.max_results,
            temperature=request.temperature
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to be indexed in the RAG system.
    """
    try:
        content = await file.read()
        result = await rag_engine.add_document(
            content=content,
            filename=file.filename,
            content_type=file.content_type
        )
        return {"status": "success", "document_id": result["document_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def list_documents():
    """
    List all indexed documents.
    """
    try:
        documents = await rag_engine.list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the RAG system.
    """
    try:
        await rag_engine.delete_document(document_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
