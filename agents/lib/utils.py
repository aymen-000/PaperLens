from typing import TypedDict  , Annotated  
from langchain_core.messages import HumanMessage , AnyMessage
from langchain_core.runnables import Runnable  , RunnableConfig
from langgraph.graph.message import add_messages 
from typing import Dict , List
from langchain_core.messages import ToolMessage 
from langgraph.prebuilt import ToolNode
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables import RunnableLambda
from typing import Dict,List  ,Any
from langchain_core.language_models.chat_models import BaseChatModel
import os 
from dotenv import load_dotenv 
import importlib 
from langchain_community.vectorstores.pgvector import PGVector 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document 
from sqlalchemy import create_engine 


load_dotenv()
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages] 

class Assistant:
    def __init__(self, runnable: Runnable):
        self.run = runnable

    def __call__(self, state: State, config :RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            user_id = configuration.get("user_id", None)
            state = {**state}
            results = self.run.invoke(state , config=config)
            # Check if assistant returned valid output
            if not results.tool_calls and (
                not results.content
                or (isinstance(results.content, list) and not results.content[0].get("text"))
            ):
                message = state["messages"] + [HumanMessage(content="Respond with a real output")]
                state = {**state, "messages": message}
            else:
                break

        return {"messages": [results]}
    
    
def handle_tool_error(state) -> Dict  : 
    """Function to handle errors that accur during tool execution.

    Args:
        state (dict): The current state of the AI agent , which includes messgaes and tool calls 

    Returns:
        Dict: A dicitionary containing error messgaes for each tool that encountered an issue.  
    """
    
    error = state.get("error") 
    tool_calls = state["messages"][-1].tool_calls 
    
    
    return {
        "messages" : [
            ToolMessage(
                content=f"Error : {repr(error)} \n please fix your mistakes" , 
                tool_call_id = tc["id"]
            ) 
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools : List) -> Dict : 
    """
        Function to create a tool node with fallback error handling .
        
    Args : 
        tools (List) : A list of tools to be included in the node 
        
    Return : 
        dict : A tool node that uses fallback behavior in case of errors .
    """ 
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)] ,  exception_key="error" 
        
    )
    
    
    
class LangGraphModelFactory:
    """
    Dynamically instantiates any LangChain BaseChatModel provider based on the LANGGRAPH env variable.
    
    Example .env:
        LANGGRAPH=langchain_openai.ChatOpenAI
        MODEL_NAME=gpt-4o-mini
    """

    def __init__(self, model_name: str | None = None, temperature: float = 0.7, **kwargs: Any):
        self.provider_path = os.getenv("PROVIDER", "langchain_openai.ChatOpenAI")
        self.model_name = model_name or os.getenv("MODEL_NAME")
        self.temperature = temperature
        self.extra_kwargs = kwargs

    def _import_class(self):
        """Dynamically import provider class given a full path like 'package.module.ClassName'."""
        if "." not in self.provider_path:
            raise ValueError(f"LANGGRAPH must be a full path, e.g., 'langchain_openai.ChatOpenAI', got '{self.provider_path}'")

        module_name, class_name = self.provider_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    def get_model(self) -> BaseChatModel:
        """Instantiate and return the provider model."""
        ProviderClass = self._import_class()

        init_args = {
            **({"model": self.model_name} if self.model_name else {}),
            "temperature": self.temperature,
            **self.extra_kwargs,
        }

        model = ProviderClass(**init_args)
        if not isinstance(model, BaseChatModel):
            raise TypeError(f"{ProviderClass} is not a subclass of BaseChatModel")
        return model
    
    
    
