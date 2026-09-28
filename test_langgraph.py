import asyncio
from langgraph.graph import StateGraph, START, END
from typing import Annotated, TypedDict
import operator

class State(TypedDict):
    messages: Annotated[list, operator.add]

def node1(state):
    return {"messages": [{"role": "assistant", "content": "hi", "name": "tool"}]}

builder = StateGraph(State)
builder.add_node("node1", node1)
builder.add_edge(START, "node1")
builder.add_edge("node1", END)
graph = builder.compile()

res = graph.invoke({"messages": [{"role": "user", "content": "hello"}]})
msg = res["messages"][-1]
print("Type of msg:", type(msg))
try:
    print("Has attr name:", hasattr(msg, "name"))
except:
    pass
