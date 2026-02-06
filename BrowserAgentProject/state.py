from typing import TypedDict, Annotated, List, Union, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    loop_step: int
    task: str
    # We can add more state here if needed, like "current_url" or "last_screenshot"
    current_url: str
    screenshot_path: str
