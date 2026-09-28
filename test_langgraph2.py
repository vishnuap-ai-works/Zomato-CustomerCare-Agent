from langchain.agents.factory import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import os

@tool
def dummy():
    """dummy"""
    return "ok"

llm = ChatOpenAI(model="gpt-4o-mini", api_key="fake")
agent = create_agent(llm=llm, tools=[dummy], system_prompt="test")
# Let's inspect the graph
print(agent)
