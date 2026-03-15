from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from rag.query import get_chunks
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage


# ----- Init App ----
app = FastAPI()

# Allow Streamlit frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# ---- Model Initialization ----
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables.")

model = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0.3,
    api_key=ANTHROPIC_API_KEY,
)

SYSTEM_PROMPT = (
    "You are a helpful meal planning assistant. "
    "Use provided context when relevant. "
    "If context is insufficient, say what is missing."
)

# ----- Pydantic Schemas -----
class ChatRequest(BaseModel):
    user_message: str
    session_id: str


class ChatResponse(BaseModel):
    model_response: str
    chunks: List[Dict[str, Any]] = Field(default_factory=list)


class UserPreferences(BaseModel):
    session_id: str
    user_id: int
    total_time: int = Field(ge=1, le=600)
    diet_types: List[str] = Field(default_factory=list)


# define session memory & preferences store
MAX_TURNS = 6
session_memory: Dict[str, List[Any]] = {}
preferences_store: Dict[str, UserPreferences] = {}


# ----- Define routes ----
@app.get("/", tags=["root"])
async def root() -> dict:
    return {"message": "Hello from FastAPI!!"}


def query_vectordb(user_message: str) -> List[Dict[str, Any]]:
    """Fetch relevant chunks from Pinecone using MMR retrieval."""
    return get_chunks(user_query=user_message, k=5, fetch_k=20, lambda_mult=0.5)


@app.post("/chat", tags=["Chat"])
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
                "No specific context is available for this query, "
                "so respond based on your general knowledge."
            )

        # Add user preferences (if available) into system instructions
        user_prefs = preferences_store.get(session_id)
        dynamic_system_prompt = SYSTEM_PROMPT
        if user_prefs:
            diets = ", ".join(user_prefs.diet_types) if user_prefs.diet_types else "No dietary restrictions"
            dynamic_system_prompt += (
                "\n\nUser preferences:\n"
                f"- Max cooking time: {user_prefs.total_time} minutes\n"
                f"- Diet types: {diets}\n"
                "Prefer recommendations that satisfy these preferences."
            )

        messages = [
            SystemMessage(content=dynamic_system_prompt),
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
        session_memory[session_id] = updated_history[-(MAX_TURNS * 2):]

        return ChatResponse(model_response=ai_msg.content, chunks=relevant_chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", tags=["Ingest"])
async def ingest_pinecone():
    # ...existing code...
    return {"message": "Ingest endpoint not implemented yet."}


@app.get("/preferences", tags=["User Preferences"], response_model=UserPreferences)
async def get_preferences(session_id: str):
    prefs = preferences_store.get(session_id)
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found for this session.")
    return prefs


@app.post("/preferences", tags=["User Preferences"], response_model=UserPreferences)
async def store_preferences(user_prefs: UserPreferences):
    preferences_store[user_prefs.session_id] = user_prefs
    return user_prefs





