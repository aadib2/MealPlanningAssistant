from .redis_session_manager import RedisSessionManager
import os
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from rag.query import get_chunks

load_dotenv()

# ---- Model Initialization ----
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables.")

class SessionChatHandler:
    """
    Handles chat interactions with session-based memory.
    Each user gets their own isolated conversation context.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.session_manager = RedisSessionManager(redis_url)
        self.llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            temperature=0.3,
            api_key=ANTHROPIC_API_KEY,
        )

        self.system_message = """
        You are a helpful meal planning assistant.
        Use provided context when relevant.
        If context is insufficient, say what is missing.
        """

    def _dedupe_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate retrieved chunks by recipe id (fallback to title/content)."""
        seen: set[str] = set()
        deduped: List[Dict[str, Any]] = []

        for chunk in chunks:
            metadata = chunk.get("metadata", {}) or {}
            recipe_id = metadata.get("id")
            title = metadata.get("title", "")
            content = chunk.get("content", "")
            key = str(recipe_id) if recipe_id is not None else f"{title}::{content[:120]}"

            if key in seen:
                continue

            seen.add(key)
            deduped.append(chunk)

        return deduped

    def _query_vectordb(
        self,
        user_message: str,
        chat_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch and merge chunks from core + user namespaces."""
        metadata_filter: Dict[str, Any] | None = None

        if chat_context:
            calories_min = chat_context.get("calories_min")
            calories_max = chat_context.get("calories_max")
        else:
            calories_min = None
            calories_max = None

        if calories_min is not None and calories_max is not None:
            metadata_filter = {
                "caloriesPerServing": {
                    "$gte": float(calories_min),
                    "$lte": float(calories_max),
                }
            }

        core_namespace = os.getenv("PINECONE_CORE_NAMESPACE") or None
        user_namespace: str | None = None
        if chat_context and chat_context.get("user_id") is not None:
            user_namespace = f"user-{int(chat_context['user_id'])}"

        merged: List[Dict[str, Any]] = []
        merged.extend(
            get_chunks(
                user_query=user_message,
                k=5,
                fetch_k=20,
                lambda_mult=0.5,
                metadata_filter=metadata_filter,
                namespace=core_namespace,
            )
        )

        if user_namespace:
            merged.extend(
                get_chunks(
                    user_query=user_message,
                    k=5,
                    fetch_k=20,
                    lambda_mult=0.5,
                    metadata_filter=metadata_filter,
                    namespace=user_namespace,
                )
            )

        return self._dedupe_chunks(merged)[:5]

    def chat(
        self,
        session_id: str,
        user_message: str,
        chat_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a chat message within a session context.
        Loads history, generates response, and saves updated history.
        """
        # Load existing conversation history
        messages = self.session_manager.load_messages(session_id)

        # 1) Retrieve context chunks
        relevant_chunks = self._query_vectordb(user_message, chat_context=chat_context)

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

        # Add effective preferences (session + persistent user profile) into system instructions
        dynamic_system_prompt = self.system_message
        if chat_context:
            diets = ", ".join(chat_context.get("diet_types", [])) or "No diet type filters"
            restrictions = ", ".join(chat_context.get("dietary_restrictions", [])) or "None"
            dislikes = ", ".join(chat_context.get("disliked_ingredients", [])) or "None"
            summary = chat_context.get("preference_summary", "")
            dynamic_system_prompt += (
                "\n\nUser context:\n"
                f"- Max cooking time: {chat_context.get('total_time', 60)} minutes\n"
                f"- Diet types: {diets}\n"
                f"- Min and Max Calories Per Serving: {chat_context.get('calories_min', 0)}, {chat_context.get('calories_max', 2000)}\n"
                f"- Dietary restrictions: {restrictions}\n"
                f"- Disliked ingredients: {dislikes}\n"
                f"- Preference summary: {summary if summary else 'Not set'}\n"
                "Prefer recommendations that satisfy these preferences."
            )

        # Build the full message list for the LLM
        full_messages = [
            {"role": "system", "content": dynamic_system_prompt}
        ]

        # Add conversation history
        for msg in messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            full_messages.append({"role": role, "content": msg.content})

        # Add current user message augmented with retrieved context
        full_messages.append({"role": "user", "content": user_with_context})
        messages.append(HumanMessage(content=user_with_context))

        # Get LLM response
        response = self.llm.invoke(full_messages)

        # Add response to history
        messages.append(AIMessage(content=response.content))

        # Save updated history
        self.session_manager.save_messages(session_id, messages)

        output: Dict[str, Any] = {
            "response": response.content,
            "chunks": relevant_chunks
        }

        return output

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get formatted conversation history for display.
        Returns list of dictionaries with role and content.
        """
        messages = self.session_manager.load_messages(session_id)
        return [
            {
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content
            }
            for msg in messages
        ]
