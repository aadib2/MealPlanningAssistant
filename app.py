import json
from uuid import uuid4
from urllib import error, request
import streamlit as st

# get spoonacular metadata
from data.spoonacular_data_options import diet_options, cuisine_options, meal_type_options, intolerances_options

def post_chat(user_message: str, session_id: str, base_url: str) -> dict:
    payload = {
        "user_message": user_message,
        "session_id": session_id,
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{base_url.rstrip('/')}/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_preferences(payload: dict, base_url: str) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{base_url.rstrip('/')}/preferences",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_ingest(payload: dict, base_url: str) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{base_url.rstrip('/')}/ingest",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---- Streamlit UI ----
st.set_page_config(layout="wide")
st.title("Meal Planning Assistant")

if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.subheader("Backend Settings")
    api_base_url = st.text_input("FastAPI URL", value="http://localhost:8000")
    st.caption(f"Session ID: {st.session_state.chat_session_id}")

    st.subheader("User Preferences")
    user_time = st.number_input("Max Time to Cook (minutes)", min_value=1, max_value=600, value=45)

    diet_types = st.multiselect("Diet Types", options=diet_options, default=[])
    calories_min = st.number_input("Minimum Calorie Count (per serving)", min_value=50, max_value=1000, value=200)
    calories_max = st.number_input("Maximum Calorie Count (per serving)", min_value=100, max_value=2000, value=400)

    if st.button("Submit preferences"):
        payload = {
            "session_id": st.session_state.chat_session_id,
            "user_id": 1,
            "total_time": int(user_time),
            "diet_types": diet_types,
            "calories_min": calories_min,
            "calories_max": calories_max
        }
        try:
            api_response = post_preferences(payload=payload, base_url=api_base_url)
            st.success("Preferences saved.")
            st.caption(
                f"Saved: total_time={api_response.get('total_time')} | "
                f"diet_types={api_response.get('diet_types', [])} | "
                f"calories min={api_response.get('calories_min')} | "
                f"calories max={api_response.get('calories_max')} | "
            )
        except error.HTTPError as http_err:
            err_msg = f"Backend error {http_err.code}: {http_err.reason}"
            st.error(err_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
        except error.URLError:
            err_msg = (
                "Could not reach FastAPI backend. Start it with: "
                "`uv run uvicorn backend.app.api:app --reload`"
            )
            st.error(err_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
    st.subheader("Ingest New Recipes into DB")

    cuisine_pref = st.multiselect("Cuisines", options=cuisine_options, default=[])
    meal_types = st.multiselect("Meal Types", options=meal_type_options, default=[])
    ingest_diet_types = st.multiselect("Diet Types (Ingest)", options=diet_options, default=[])
    intolerances = st.multiselect("Intolerances/Allergies", options=intolerances_options, default=[])
    num_recipes = st.number_input("Number of New Recipes to Add", min_value=1, max_value=100, value=25)
    if st.button("Refresh Recipes Based on Filters"):
        ingest_payload = {
            "session_id": st.session_state.chat_session_id,
            "cuisines": cuisine_pref,
            "meal_types": meal_types,
            "diet_types": ingest_diet_types,
            "intolerances": intolerances,
            "recipe_count": int(num_recipes),
        }

        try:
            ingest_response = post_ingest(payload=ingest_payload, base_url=api_base_url)
            st.success(ingest_response.get("message", "Ingestion complete."))
            st.caption(
                f"Fetched={ingest_response.get('fetched_count', 0)} | "
                f"Ingested={ingest_response.get('ingested_count', 0)} | "
                f"Invalid={ingest_response.get('invalid_count', 0)}"
            )
        except error.HTTPError as http_err:
            detail = ""
            try:
                body = http_err.read().decode("utf-8")
                detail = f" | {body}" if body else ""
            except Exception:
                detail = ""
            st.error(f"Ingest failed ({http_err.code}: {http_err.reason}){detail}")
        except error.URLError:
            st.error(
                "Could not reach FastAPI backend. Start it with: "
                "`uv run uvicorn backend.app.api:app --reload`"
            )


for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chunks"):
            with st.expander("Retrieved chunks"):
                for i, chunk in enumerate(msg["chunks"], start=1):
                    st.markdown(f"**Chunk {i}**")
                    st.write(chunk.get("content", ""))


if prompt := st.chat_input("What would you like to cook?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            api_response = post_chat(
                user_message=prompt,
                session_id=st.session_state.chat_session_id,
                base_url=api_base_url,
            )

            assistant_text = api_response.get("model_response", "No response returned.")
            chunks = api_response.get("chunks", [])

            st.markdown(assistant_text)

            if chunks:
                with st.expander("Retrieved chunks"):
                    for i, chunk in enumerate(chunks, start=1):
                        st.markdown(f"**Chunk {i}**")
                        st.write(chunk.get("content", ""))

            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": assistant_text,
                    "chunks": chunks,
                }
            )
        except error.HTTPError as http_err:
            err_msg = f"Backend error {http_err.code}: {http_err.reason}"
            st.error(err_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
        except error.URLError:
            err_msg = (
                "Could not reach FastAPI backend. Start it with: "
                "`uv run uvicorn backend.app.api:app --reload`"
            )
            st.error(err_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": err_msg})