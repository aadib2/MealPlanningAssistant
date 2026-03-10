import json
from uuid import uuid4
from urllib import error, request

import streamlit as st


# ---- Streamlit UI ----

st.set_page_config(layout="wide")
st.title("Meal Planning Assistant")

# Persist a chat session id for backend memory across Streamlit reruns.
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.subheader("Backend Settings")
    api_base_url = st.text_input("FastAPI URL", value="http://localhost:8000")
    st.caption(f"Session ID: {st.session_state.chat_session_id}")
    st.subheader("User Preferences")
    user_calories = st.number_input("Max Calories", value=400)
    st.selectbox("Diet Type", ["Vegetarian", "Vegan", "Pescatarian", "Gluten Free", "None"])

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chunks"):
            with st.expander("Retrieved chunks"):
                for i, chunk in enumerate(msg["chunks"], start=1):
                    st.markdown(f"**Chunk {i}**")
                    st.write(chunk.get("content", ""))


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