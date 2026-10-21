from typing import List, Dict, Any
from services.permission.policy import get_tool_risk, requires_human_approval

def check_for_unapproved_tools(tool_calls: List[Dict[str, Any]], pending_approvals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scans requested tool calls against the risk table.
    Returns a list of tools that require approval but haven't received it yet.
    """
    unapproved_tools = []
    
    for call in tool_calls:
        t_name = call.get("name")
        args = call.get("args", {})
        risk = get_tool_risk(t_name, args)
        
        # Check if the user already approved or denied this specific call in the pending queue
        status = None
        for pa in pending_approvals:
            if pa.get("name") == t_name and pa.get("args") == call.get("args"):
                status = pa.get("status")
                break
                
        if requires_human_approval(risk) and status not in ["approved", "denied"]:
            unapproved_tools.append({
                "name": t_name,
                "args": call.get("args"),
                "risk": risk,
                "status": "pending"
            })
            
    return unapproved_tools

def is_tool_denied(tool_name: str, args: Dict[str, Any], pending_approvals: List[Dict[str, Any]]) -> bool:
    """Checks if a specific tool call was denied by the user."""
    for pa in pending_approvals:
        if pa.get("name") == tool_name and pa.get("args") == args and pa.get("status") == "denied":
            return True
    return False
