# app.py
import streamlit as st
from rag.store import load_vector_store
from agents.tools import build_retriever_tool
from agents.meal_planner import build_meal_planner_agent

st.title("Meal Planning Assistant")

@st.cache_resource
def init_agent():
    vector_store = load_vector_store()
    retrieve_tool = build_retriever_tool(vector_store)
    return build_meal_planner_agent([retrieve_tool])

agent = init_agent()

if prompt := st.chat_input("What would you like to cook?"):
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        response = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        st.write(response["messages"][-1].content)