import os
import uuid
from dotenv import load_dotenv
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import tools_condition
from agents.prompts.agents_prompts import CRAWLER_AGENT_PROMPT
from agents.tools.crawler_tools import get_user_interests, fetch_recent_papers
from agents.lib.utils import LangGraphModelFactory, Assistant , _print_event , create_tool_node_with_fallback , State
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import ast
import json
load_dotenv()
model_id = os.environ.get("CRAWLER_AGENT_MODEL_ID")



tools = [get_user_interests, fetch_recent_papers]

def should_continue(state):
    """Determine if we should continue to tools or end."""
    last_message = state["messages"][-1]
    # If the last message has tool calls, go to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "__end__"


factory = LangGraphModelFactory(model_name=model_id, temperature=0.1)
llm = factory.get_model()


assistant_runnable = CRAWLER_AGENT_PROMPT | llm.bind_tools(tools)


crawler_graph = StateGraph(State)

crawler_graph.add_node("assistant", Assistant(assistant_runnable))

crawler_graph.add_node("tools", create_tool_node_with_fallback(tools))




crawler_graph.add_edge(START, "assistant")


crawler_graph.add_conditional_edges(
    "assistant",
    tools_condition) 


crawler_graph.add_edge("tools", "assistant")
memory = InMemorySaver()
crawler_graph = crawler_graph.compile(checkpointer=memory)


def call_crawler_agent(config: RunnableConfig):
    initial_state = {
        "messages": ["Suggest to me papers based on my interests"],  
    }
    result = crawler_graph.invoke(initial_state, config=config)
    return result["messages"][-1].content  



def run_agent(thread_id , user_id) : 
    config = {
        "configurable": {
            "user_id": user_id,
            "thread_id": thread_id,
        }
    }
    results = call_crawler_agent(config)
    res = results.strip().strip("```json").strip("```")
    re_list = ast.literal_eval(res)
    
    return re_list


""" 
if __name__ == "__main__":
    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "user_id": "1",
            "thread_id": thread_id,
        }
    }


    results = call_crawler_agent(config)
    res = ast.literal_eval(results) """





