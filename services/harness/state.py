from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
import operator
from typing import Annotated

class AgentState(TypedDict):
    """
    State for the LangGraph agent harness.
    """
    task: str
    plan: Optional[str]
    tool_calls: List[Dict[str, Any]]
    observations: Annotated[List[str], operator.add]
    status: str  # "planning", "acting", "observing", "verifying", "done"
    messages: Annotated[List[Dict[str, Any]], operator.add]
    iteration: int
    final_response: Optional[str]
    pending_approvals: List[Dict[str, Any]]
    task_id: Optional[int]
