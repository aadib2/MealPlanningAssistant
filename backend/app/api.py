from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from rag.query import get_chunks
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate


# ----- Init App ----
app = FastAPI()

load_dotenv()

# ---- Model Initialization ----

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables.")

model = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0.3,  # lower for grounded/RAG responses
    api_key=ANTHROPIC_API_KEY,
)

# define system prompt - MODIFY later to be constructed based on user preferences
SYSTEM_PROMPT = (
    "You are a helpful meal planning assistant. "
    "Use provided context when relevant. "
    "If context is insufficient, say what is missing."
)

# define session memory
MAX_TURNS = 6  # keep last 6 turns (12 messages)
session_memory: Dict[str, List[Any]] = {}  # session_id -> [HumanMessage, AIMessage, ...]

# ----- Pydantic Schemas -----
class ChatRequest(BaseModel):
    user_message: str
    session_id: str

class ChatResponse(BaseModel):
    model_response: str
    chunks: List[Dict[str, Any]] = Field(default_factory=list)

class UserPreferences: # for metdata filtering
    user_id: int
    prep_time: int
    calories: int
    diet_type: str

# ----- Define routes ----

@app.get("/", tags=["root"])
async def root() -> dict:
    return {"message": "Hello from FastAPI!!"}


def query_vectordb(user_message: str) -> List[Dict[str, Any]]:
    """Fetch relevant chunks from Pinecone using MMR retrieval."""
    return get_chunks(user_query=user_message, k=5, fetch_k=20, lambda_mult=0.5)

@app.post("/chat", tags=['Chat'])
async def chat(chat_input: ChatRequest) -> ChatResponse:
    # goal is to receive message + session id and return streamed response
    try:
        session_id = chat_input.session_id
        user_message = chat_input.user_message

        # get session history
        history = session_memory.get(session_id, [])

        # 1) Retrieve context chunks
        relevant_chunks = query_vectordb(user_message)

        if relevant_chunks:
            context_text = "\n\n".join(chunk["content"] for chunk in relevant_chunks)

            # 2) Build prompt with session history

            user_with_context = (
                f"User question:\n{user_message}\n\n"
                f"Retrieved context:\n{context_text}\n\n"
                "Answer using the context when possible."
            )
        else:
            user_with_context = (
                """No specific context is available for this query, 
                so respond based on your general knowledge."""
            )
            

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *history,
            HumanMessage(content=user_with_context),
        ]

        # 3) Invoke model
        ai_msg = model.invoke(messages)

        # 4) Save memory (store raw user msg, not augmented text)
        updated_history = history + [
            HumanMessage(content=user_message),
            AIMessage(content=ai_msg.content),
        ]

        session_memory[session_id] = updated_history[-(MAX_TURNS * 2):] # set equal to last 12 messages

        return ChatResponse(
            model_response=ai_msg.content,
            chunks=relevant_chunks,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest", tags=['Ingest'])
async def ingest_pinecone():
    # logic for triggering pinecone ingestion
    return


