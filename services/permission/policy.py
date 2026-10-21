RISK_TABLE = {
    "search_web": "LOW",
    "open_url": "LOW",
    "open_in_browser": "LOW",
    "play_youtube_video": "LOW",
    "read_file": "MEDIUM",
    "capture_screenshot": "MEDIUM",
    "analyze_screen": "MEDIUM",
    "media_control": "LOW",
    "press_keys": "MEDIUM",
    "open_local_app": "LOW",
    "start_macro_recording": "LOW",
    "stop_macro_recording": "LOW",
    "list_macros": "LOW",
    "play_macro": "LOW",
    "save_to_memory": "LOW",
    "delegate_to_subagent": "LOW",
    "ask_subagent_quick": "LOW",
    "create_word_document": "HIGH",
    "execute_system_command": "CRITICAL"
}

def get_tool_risk(tool_name: str, args: dict = None) -> str:
    """Returns the deterministic risk level of a given tool, utilizing LAYA for dynamic analysis if applicable."""
    
    # 1. Check static RISK_TABLE
    if tool_name in RISK_TABLE:
        base_risk = RISK_TABLE[tool_name]
    else:
        # 2. Check dynamic plugins
        try:
            from services.plugins.manager import plugin_manager
            plugin_risks = plugin_manager.get_risks()
            base_risk = plugin_risks.get(tool_name, "CRITICAL") # Default unknown plugins to CRITICAL for safety
        except Exception:
            base_risk = "CRITICAL"
    
    
    # Use LAYA to dynamically evaluate the risk of arbitrary shell commands
    if tool_name == "execute_system_command" and args and "command" in args:
        try:
            from services.permission.laya_engine import evaluate_command_risk
            dynamic_risk = evaluate_command_risk(args["command"])
            return dynamic_risk
        except Exception:
            return base_risk # Fallback to static CRITICAL if LAYA fails

    return base_risk

def requires_human_approval(risk_level: str) -> bool:
    """Evaluates if the given risk level requires human intervention."""
    return risk_level in ["HIGH", "CRITICAL"]
