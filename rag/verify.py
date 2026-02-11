from pipeline import agent

query = (
    'Quick healthy, dinner under 30 minutes'
)

for event in agent.stream(
    {"messages": [{"role": "user", "content": query}]},
    stream_mode="values",
):
    event["messages"][-1].pretty_print() # to view conversation