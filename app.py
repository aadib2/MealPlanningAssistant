import json
from uuid import uuid4
from urllib import error, request

import streamlit as st


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

    diet_options = [
        "Gluten Free",
        "Ketogenic",
        "Vegetarian",
        "Lacto Vegetarian",
        "Ovo Vegetarian",
        "Vegan",
        "Pescatarian",
        "Paleo",
        "Primal",
    ]
    diet_types = st.multiselect("Diet Types", options=diet_options, default=[])

    if st.button("Submit preferences"):
        payload = {
            "session_id": st.session_state.chat_session_id,
            "user_id": 1,
            "total_time": int(user_time),
            "diet_types": diet_types,
        }
        try:
            api_response = post_preferences(payload=payload, base_url=api_base_url)
            st.success("Preferences saved.")
            st.caption(
                f"Saved: total_time={api_response.get('total_time')} | "
                f"diet_types={api_response.get('diet_types', [])}"
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