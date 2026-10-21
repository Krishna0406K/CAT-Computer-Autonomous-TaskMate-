from langgraph.graph import StateGraph, END
from services.harness.state import AgentState
from services.harness.nodes import planner_node, executor_node, verifier_node

def route_after_planner(state: AgentState) -> str:
    if state["status"] == "acting":
        return "executor"
    return "verifier"

def route_after_verifier(state: AgentState) -> str:
    # Stop if task is complete, or if we've tried 3 times (prevent infinite death loops)
    if state["status"] == "done" or state.get("iteration", 0) >= 3:
        return END
    return "planner"

def route_after_executor(state: AgentState) -> str:
    if state["status"] == "approval_required":
        return END
    return "verifier"

def build_graph():
    # Initialize the graph with the AgentState type
    workflow = StateGraph(AgentState)

    # Add the nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("verifier", verifier_node)

    # Set the entry point
    workflow.set_entry_point("planner")

    # Add edges
    workflow.add_conditional_edges("planner", route_after_planner)
    workflow.add_conditional_edges("executor", route_after_executor)
    workflow.add_conditional_edges("verifier", route_after_verifier)

    # Compile the graph
    app = workflow.compile()
    return app
