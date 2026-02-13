# agents/meal_planner.py
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent

def build_meal_planner_agent(tools):
    model = ChatAnthropic(model="claude-sonnet-4-520250929")
    system_prompt = (
        "You have access to a tool that retrieves relevant recipes and meals "
        "from a recipe database. Use it to help answer user queries."
    )
    return create_agent(model, tools, system_prompt=system_prompt)