from agents.meal_planner import create_agent
from agents.tools import build_retriever_tool


# access vector store and create tool

agent = create_agent()


query = (
    'Quick healthy, dinner under 30 minutes'
)

for event in agent.stream(
    {"messages": [{"role": "user", "content": query}]},
    stream_mode="values",
):
    event["messages"][-1].pretty_print() # to view conversation