import os
import uuid
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition
from langchain_together import ChatTogether

from agents.prompts.agents_prompts import CRAWLER_AGENT_PROMPT
from agents.tools.crawler_tools import get_user_interests, fetch_recent_papers
from agents.lib.utils import create_tool_node_with_fallback , LangGraphModelFactory , Assistant
import ast

load_dotenv()
model_id = os.environ.get("CRAWLER_AGENT_MODEL_ID")


class State(TypedDict):

    messages: Annotated[list, add_messages]



# --- Tools ---
tools = [get_user_interests, fetch_recent_papers]

# Bind LLM with tools
factory  = LangGraphModelFactory(model_name=model_id , temperature=0.8 , max_tokens=8000)
llm = factory.get_model()
assistant_runnable = CRAWLER_AGENT_PROMPT | llm.bind_tools(tools)
# --- Graph ---
crawler_graph = StateGraph(State)
crawler_graph.add_node("assistant", Assistant(assistant_runnable))
crawler_graph.add_node("intr_tool", create_tool_node_with_fallback([tools[0]]))
crawler_graph.add_node("pref_tool", create_tool_node_with_fallback([tools[1]]))

crawler_graph.add_edge(START, "assistant")
crawler_graph.add_edge("assistant", "intr_tool")
crawler_graph.add_edge("intr_tool", "pref_tool")
crawler_graph.add_edge("pref_tool",END)


memory = InMemorySaver()
crawler_graph = crawler_graph.compile(checkpointer=memory)


initial_state = {
    "messages": [],  
}


def call_crawler_agent(config:RunnableConfig) : 
    result = crawler_graph.invoke(initial_state, config=config) 
    res =ast.literal_eval(result["messages"][-1].content) 
    
    return res