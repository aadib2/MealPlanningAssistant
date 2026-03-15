from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, List

from dotenv import load_dotenv
from .session_chat_handler import SessionChatHandler
from .ingester import Ingester
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
    calories_min: int = Field(ge=0)
    calories_max: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_calorie_range(self) -> "UserPreferences":
        if self.calories_min > self.calories_max:
            raise ValueError("calories_min must be less than or equal to calories_max")
        return self

class IngestFilters(BaseModel):
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


# define session memory & preferences store
# MAX_TURNS = 6
# session_memory: Dict[str, List[Any]] = {} --> using Redis instead
preferences_store: Dict[str, UserPreferences] = {} # keeping this until find more persistent way to track
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
        session_id = chat_input.session_id
        user_message = chat_input.user_message
        user_prefs = preferences_store.get(session_id)
        # chat
        response = chat_handler.chat(session_id, user_message, user_prefs)

        return ChatResponse(model_response=response["response"], chunks=response["chunks"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", tags=["Ingest"], response_model=IngestResponse)
async def ingest_pinecone(filters: IngestFilters):
    try:
        result = ingester.create_docs(filters.model_dump())
        ingested_count = ingester.build_index_namespace(result["documents"])

        return IngestResponse(
            message="Recipes fetched and ingested successfully.",
            fetched_count=result["raw_count"],
            ingested_count=ingested_count,
            invalid_count=result["invalid_count"],
            invalid_samples=result["invalid_samples"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


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





