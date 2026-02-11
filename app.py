# app.py - entire app in ~200 lines
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.agents import initialize_agent

# Initialize
llm = ChatOpenAI(model="gpt-4")
vectorstore = Chroma(persist_directory="./chroma_db")
agent = initialize_agent(tools=[...], llm=llm)

# UI
st.title("🍳 Meal Planning Assistant")

if prompt := st.chat_input("What would you like to cook?"):
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        response = agent.run(prompt)
        st.write(response)