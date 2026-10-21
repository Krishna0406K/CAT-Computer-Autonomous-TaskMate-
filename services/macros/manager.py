import os
import json

MACROS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "macros.json")
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "macro_state.json")

def _load_macros():
    if not os.path.exists(MACROS_FILE):
        return {}
    with open(MACROS_FILE, "r") as f:
        return json.load(f)

def _save_macros(macros):
    os.makedirs(os.path.dirname(MACROS_FILE), exist_ok=True)
    with open(MACROS_FILE, "w") as f:
        json.dump(macros, f, indent=4)

def _get_state():
    if not os.path.exists(STATE_FILE):
        return {"recording": False, "current_name": None, "steps": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def _save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def start_macro_recording(name: str) -> str:
    """Starts recording a sequence of tool calls into a named macro."""
    state = _get_state()
    state["recording"] = True
    state["current_name"] = name
    state["steps"] = []
    _save_state(state)
    return f"Started recording macro '{name}'. All subsequent tool executions will be saved until you stop recording."

def stop_macro_recording() -> str:
    """Stops the current macro recording and saves the sequence."""
    state = _get_state()
    if not state.get("recording"):
        return "No macro is currently being recorded."
        
    macros = _load_macros()
    name = state["current_name"]
    macros[name] = state["steps"]
    _save_macros(macros)
    
    step_count = len(state["steps"])
    state["recording"] = False
    state["current_name"] = None
    state["steps"] = []
    _save_state(state)
    
    return f"Successfully saved macro '{name}' with {step_count} steps."

def record_tool_call(tool_name: str, args: dict):
    """Internal helper to hook into the harness executor."""
    state = _get_state()
    if state.get("recording"):
        # Prevent recursion if play_macro itself is called during recording
        if tool_name not in ["start_macro_recording", "stop_macro_recording", "play_macro"]:
            state["steps"].append({"name": tool_name, "args": args})
            _save_state(state)

def list_macros() -> str:
    """Lists all saved macros."""
    macros = _load_macros()
    if not macros:
        return "No macros found."
    return "Available Macros: " + ", ".join(macros.keys())

def play_macro(name: str) -> str:
    """Executes a previously saved macro sequence completely locally and instantly."""
    macros = _load_macros()
    if name not in macros:
        return f"Error: Macro '{name}' not found. Check list_macros()."
        
    steps = macros[name]
    
    # Deferred import to prevent circular dependencies with nodes.py
    from services.harness.nodes import TOOL_MAP
    
    results = []
    results.append(f"▶️ Starting macro: {name} ({len(steps)} steps)")
    for i, step in enumerate(steps):
        tool_name = step.get("name")
        args = step.get("args", {})
        
        results.append(f"  Step {i+1}: {tool_name}({args})")
        
        if tool_name in TOOL_MAP:
            try:
                func = TOOL_MAP[tool_name]
                res = func(**args)
                results.append(f"    -> Success: {res[:200]}...")
            except Exception as e:
                results.append(f"    -> FAILED: {str(e)}")
                # Stop on failure for safety
                results.append("🛑 Macro aborted due to failure.")
                break
        else:
            results.append(f"    -> FAILED: Tool {tool_name} not recognized.")
            results.append("🛑 Macro aborted.")
            break
            
    results.append("✅ Macro playback complete.")
    return "\n".join(results)
