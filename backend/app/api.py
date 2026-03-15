from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, List

from dotenv import load_dotenv
from .session_chat_handler import SessionChatHandler
from .ingester import Ingester
from .user_memory_store import UserMemoryStore
from data.spoonacular_data_options import (
    cuisine_options,
    meal_type_options,
    diet_options,
    intolerances_options,
)


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

# ----- Pydantic Schemas -----
class ChatRequest(BaseModel):
    user_id: int
    user_message: str
    session_id: str


class ChatResponse(BaseModel):
    model_response: str
    chunks: List[Dict[str, Any]] = Field(default_factory=list)


class EffectiveChatContext(BaseModel):
    user_id: int
    total_time: int = 60
    diet_types: List[str] = Field(default_factory=list)
    calories_min: int = 0
    calories_max: int = 2000
    dietary_restrictions: List[str] = Field(default_factory=list)
    disliked_ingredients: List[str] = Field(default_factory=list)
    saved_recipes: List[Any] = Field(default_factory=list)
    preference_summary: str = ""


class UserPreferences(BaseModel):
    user_id: int
    dietary_restrictions: List[str] = Field(default_factory=list)
    disliked_ingredients: List[str] = Field(default_factory=list)
    saved_recipes: List[Any] = Field(default_factory=list)
    preference_summary: str = ""


class SessionPreferences(BaseModel):
    session_id: str
    user_id: int
    total_time: int = Field(ge=1, le=600)
    diet_types: List[str] = Field(default_factory=list)
    calories_min: int = Field(ge=0)
    calories_max: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_calorie_range(self) -> "SessionPreferences":
        if self.calories_min > self.calories_max:
            raise ValueError("calories_min must be less than or equal to calories_max")
        return self

class IngestFilters(BaseModel):
    user_id: int
    session_id: str
    cuisines: List[str] = Field(default_factory=list)
    meal_types: List[str] = Field(default_factory=list)
    diet_types: List[str] = Field(default_factory=list)
    intolerances: List[str] = Field(default_factory=list)
    recipe_count: int = Field(ge=1, le=100)

    @model_validator(mode="after")
    def validate_allowed_values(self) -> "IngestFilters":
        valid_sets = {
            "cuisines": set(cuisine_options),
            "meal_types": set(meal_type_options),
            "diet_types": set(diet_options),
            "intolerances": set(intolerances_options),
        }

        for field_name, valid_values in valid_sets.items():
            values = getattr(self, field_name)
            invalid = [item for item in values if item not in valid_values]
            if invalid:
                raise ValueError(f"Invalid {field_name}: {invalid}")

        return self


class IngestResponse(BaseModel):
    message: str
    fetched_count: int
    ingested_count: int
    invalid_count: int
    invalid_samples: List[Dict[str, Any]] = Field(default_factory=list)


# define session memory + lightweight user memory store
session_preferences_store: Dict[str, SessionPreferences] = {}
user_memory_store = UserMemoryStore()
chat_handler = SessionChatHandler()
ingester = Ingester()


# ----- Define routes ----
@app.get("/", tags=["root"])
async def root() -> dict:
    return {"message": "Hello from FastAPI!!"}



@app.post("/chat", tags=["Chat"])
async def chat(chat_input: ChatRequest) -> ChatResponse:
    # goal is to receive message + session id and return streamed response
    try:
        user_id = chat_input.user_id
        session_id = chat_input.session_id
        user_message = chat_input.user_message

        # Ensure the session exists and belongs to this user.
        # If frontend creates a fresh UUID locally, register it on first chat.
        owner_id = user_memory_store.get_user_for_session(session_id)
        if owner_id is None:
            user_memory_store.attach_session(user_id=user_id, session_id=session_id)
        elif owner_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Session does not belong to this user.",
            )

        # update 'last_active_at' param for session
        user_memory_store.touch_session(session_id)

        # Build effective context from both preference layers:
        # - session-level filters (temporary, take precedence)
        # - user-level preferences (persistent personalization)
        persistent_user_prefs = user_memory_store.get_preferences(user_id)
        session_prefs = session_preferences_store.get(session_id)

        effective_context = EffectiveChatContext(
            user_id=user_id,
            total_time=session_prefs.total_time if session_prefs else 60,
            diet_types=session_prefs.diet_types if session_prefs else [],
            calories_min=session_prefs.calories_min if session_prefs else 0,
            calories_max=session_prefs.calories_max if session_prefs else 2000,
            dietary_restrictions=persistent_user_prefs.get("dietary_restrictions", []),
            disliked_ingredients=persistent_user_prefs.get("disliked_ingredients", []),
            saved_recipes=persistent_user_prefs.get("saved_recipes", []),
            preference_summary=persistent_user_prefs.get("preference_summary", ""),
        )

        # chat
        response = chat_handler.chat(session_id, user_message, effective_context.model_dump())

        return ChatResponse(model_response=response["response"], chunks=response["chunks"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", tags=["Ingest"], response_model=IngestResponse)
async def ingest_pinecone(filters: IngestFilters):
    try:
        owner_id = user_memory_store.get_user_for_session(filters.session_id)
        if owner_id is None:
            user_memory_store.attach_session(
                user_id=filters.user_id,
                session_id=filters.session_id,
            )
        elif owner_id != filters.user_id:
            raise HTTPException(
                status_code=403,
                detail="Session does not belong to this user.",
            )

        user_memory_store.touch_session(filters.session_id)

        result = ingester.create_docs(filters.model_dump())
        user_namespace = f"user-{filters.user_id}"
        ingested_count = ingester.build_index_namespace(
            result["documents"],
            namespace=user_namespace,
        )

        return IngestResponse(
            message=f"Recipes fetched and ingested successfully into namespace '{user_namespace}'.",
            fetched_count=result["raw_count"],
            ingested_count=ingested_count,
            invalid_count=result["invalid_count"],
            invalid_samples=result["invalid_samples"],
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


@app.get("/preferences", tags=["User Preferences"], response_model=UserPreferences)
async def get_preferences(user_id: int):
    user_memory_store.get_or_create_user(user_id)
    prefs = user_memory_store.get_preferences(user_id)
    return UserPreferences(user_id=user_id, **prefs)


@app.post("/preferences", tags=["User Preferences"], response_model=UserPreferences)
async def store_preferences(user_prefs: UserPreferences):
    user_memory_store.get_or_create_user(user_prefs.user_id)
    saved = user_memory_store.save_preferences(
        user_id=user_prefs.user_id,
        prefs=user_prefs.model_dump(exclude={"user_id"}),
    )
    return UserPreferences(user_id=user_prefs.user_id, **saved)


@app.get(
    "/session-preferences",
    tags=["Session Preferences"],
    response_model=SessionPreferences,
)
async def get_session_preferences(session_id: str):
    prefs = session_preferences_store.get(session_id)
    if not prefs:
        raise HTTPException(status_code=404, detail="Session preferences not found.")
    return prefs


@app.post(
    "/session-preferences",
    tags=["Session Preferences"],
    response_model=SessionPreferences,
)
async def store_session_preferences(session_prefs: SessionPreferences):
    owner_id = user_memory_store.get_user_for_session(session_prefs.session_id)
    if owner_id is None:
        user_memory_store.attach_session(
            user_id=session_prefs.user_id,
            session_id=session_prefs.session_id,
        )
    elif owner_id != session_prefs.user_id:
        raise HTTPException(
            status_code=403,
            detail="Session does not belong to this user.",
        )

    session_preferences_store[session_prefs.session_id] = session_prefs
    user_memory_store.touch_session(session_prefs.session_id)
    return session_prefs





