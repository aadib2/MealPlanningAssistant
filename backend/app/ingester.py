import spoonacular
import os
import json
from uuid import uuid4
from typing import Any, Dict, List

from rag.normalize import to_recipe_dict
from rag.validate import validate_batch
from rag.transform import build_documents

# necessary imports
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pinecone import ServerlessSpec
from spoonacular.rest import ApiException

load_dotenv()

class Ingester:
    def __init__(self):
        spoonacular_api_key = os.getenv("SPOONACULAR_API_KEY")
        if not spoonacular_api_key:
            raise ValueError("SPOONACULAR_API_KEY not found in environment variables.")

        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables.")

        # Spoonacular setup
        self.configuration = spoonacular.Configuration(host="https://api.spoonacular.com")
        self.configuration.api_key["apiKeyScheme"] = spoonacular_api_key

        # Embedding + Pinecone setup
        embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.pinecone = Pinecone(api_key=pinecone_api_key)
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "spoonacular-recipes")

    def _build_tag_string(self, filters_payload: Dict[str, Any]) -> str | None:
        """Build Spoonacular include_tags payload from user filters."""
        combined: List[str] = []
        for key in ("cuisines", "meal_types", "diet_types", "intolerances"):
            value = filters_payload.get(key, [])
            if not isinstance(value, list):
                raise ValueError(f"{key} must be a list of strings")
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            combined.extend(cleaned)

        # Remove duplicates while preserving order
        unique_tags = list(dict.fromkeys(combined))
        return ",".join(unique_tags) if unique_tags else None

    def get_recipes_info(self, filters_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Given user filters, fetch random recipes using Spoonacular get_random_recipes endpoint"""
        num_recipes = int(filters_payload.get("recipe_count", 0))
        if num_recipes < 1 or num_recipes > 100:
            raise ValueError("recipe_count must be between 1 and 100")

        include_tags = self._build_tag_string(filters_payload)
        all_recipes: List[Dict[str, Any]] = []

        with spoonacular.ApiClient(self.configuration) as api_client:
            api_instance = spoonacular.RecipesApi(api_client)

            try:
                # Read raw JSON to avoid strict response validation errors
                _param = api_instance._get_random_recipes_serialize(
                    include_nutrition=False,
                    include_tags=include_tags,
                    exclude_tags=None,
                    number=num_recipes,
                    _request_auth=None,
                    _content_type=None,
                    _headers=None,
                    _host_index=0,
                )
                response_data = api_instance.api_client.call_api(*_param)
                response_data.read()
                recipe_batch = json.loads(response_data.data.decode("utf-8"))
                all_recipes.extend(recipe_batch.get("recipes", []))
            except ApiException as e:
                raise RuntimeError(f"Spoonacular API error: {e}") from e
            except json.JSONDecodeError as e:
                raise RuntimeError("Failed to parse Spoonacular API response") from e

        # Deduplicate by recipe id in case upstream returns repeats
        unique: Dict[Any, Dict[str, Any]] = {}
        for recipe in all_recipes:
            recipe_id = recipe.get("id")
            if recipe_id is not None:
                unique[recipe_id] = recipe

        deduped = list(unique.values()) if unique else all_recipes
        return {"recipes": deduped}

    def create_docs(self, filters_payload: Dict[str, Any]) -> Dict[str, Any]:
        recipes_json = self.get_recipes_info(filters_payload)
        raw_recipes = recipes_json.get("recipes", [])

        normalized = [to_recipe_dict(r) for r in raw_recipes]
        valid_recipes, invalid_recipes = validate_batch(normalized)
        documents = build_documents(valid_recipes)

        return {
            "documents": documents,
            "raw_count": len(raw_recipes),
            "valid_count": len(valid_recipes),
            "invalid_count": len(invalid_recipes),
            "invalid_samples": invalid_recipes[:5],
        }

    def build_index_namespace(self, documents: List[Any], namespace: str | None = None) -> int:
        """Upsert documents into Pinecone, optionally to a specific namespace."""
        if not documents:
            return 0

        if not self.pinecone.has_index(self.index_name):
            self.pinecone.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        index = self.pinecone.Index(self.index_name)
        vector_store = PineconeVectorStore(index=index, embedding=self.embeddings)
        ids = [str(uuid4()) for _ in range(len(documents))]
        vector_store.add_documents(documents=documents, ids=ids, namespace=namespace)
        return len(documents)


