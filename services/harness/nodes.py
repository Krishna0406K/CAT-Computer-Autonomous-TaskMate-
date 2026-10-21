import json
import re
from typing import Dict, Any

from services.harness.state import AgentState
from services.gateway.models import generate_chat_response

# Import our tools
from tools.browser_tools import open_url, open_in_browser, play_youtube_video, search_web
from tools.office_tools import create_word_document
from tools.file_tools import read_file
from tools.screen_tools import capture_screenshot, analyze_screen
from tools.system_tools import execute_system_command
from tools.keyboard_tools import media_control, press_keys
from tools.desktop_tools import open_local_app
from services.macros.manager import start_macro_recording, stop_macro_recording, list_macros, play_macro
from services.memory.rag import save_to_memory
from services.agents.delegator import delegate_to_subagent, ask_subagent_quick

# Map string names to actual tool functions
TOOL_MAP = {
    "search_web": search_web,
    "open_url": open_url,
    "open_in_browser": open_in_browser,
    "play_youtube_video": play_youtube_video,
    "create_word_document": create_word_document,
    "read_file": read_file,
    "capture_screenshot": capture_screenshot,
    "analyze_screen": analyze_screen,
    "execute_system_command": execute_system_command,
    "media_control": media_control,
    "press_keys": press_keys,
    "open_local_app": open_local_app,
    "start_macro_recording": start_macro_recording,
    "stop_macro_recording": stop_macro_recording,
    "list_macros": list_macros,
    "play_macro": play_macro,
    "save_to_memory": save_to_memory,
    "delegate_to_subagent": delegate_to_subagent,
    "ask_subagent_quick": ask_subagent_quick
}

# Merge dynamically loaded plugins into TOOL_MAP
from services.plugins.manager import plugin_manager
TOOL_MAP.update(plugin_manager.get_tools())

def extract_json_from_text(text: str) -> dict:
    """Helper to extract JSON block from markdown."""
    try:
        # Try to find a JSON block
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        # Fallback: try parsing the whole text
        return json.loads(text)
    except Exception as e:
        return {}

from services.permission.approval_queue import check_for_unapproved_tools, is_tool_denied
from services.memory.store import log_step
from services.evaluator.deterministic import evaluate_executed_tools
import json

async def planner_node(state: AgentState) -> Dict[str, Any]:
    """Generates a plan and issues tool calls."""
    from services.gateway.cancel_token import check_cancel
    if check_cancel():
        return {"status": "done", "final_response": "⚠️ Task stopped by user."}

    task = state["task"]
    observations = state.get("observations", [])
    iteration = state.get("iteration", 0)
    pending_approvals = state.get("pending_approvals", [])
    task_id = state.get("task_id")

    # If we are resuming from the CLI after a human approved/denied a tool, 
    # skip generating a new plan and just execute the existing one.
    if any(p.get("status") in ["approved", "denied"] for p in pending_approvals):
        log_step(task_id, "planner", "skipped", "Resuming from human approval")
        return {"status": "acting"}
        
    from services.memory.rag import retrieve_memory
    memories = retrieve_memory(task)
    memory_context = f"\n[Relevant Long-Term Memories]\n{memories}\n" if memories else ""

    prompt = f"""You are the Planner agent. 
Your task is to determine the next step to solve this task: "{task}"
{memory_context}
Available tools:
- search_web(query: str): Search the web using LangSearch
- open_url(url: str): Fetch text content from a URL
- open_in_browser(url: str): Open a URL visually in the browser. Do NOT use this to open local desktop apps.
- play_youtube_video(search_query: str): Play a video on YouTube
- create_word_document(filename: str, content: str): Create a docx file
- read_file(filepath: str): Read a local text file
- analyze_screen(prompt: str): Captures a screenshot and uses a Vision AI model to read text (OCR), find elements, and describe the screen. Use this to 'see' the screen.
- execute_system_command(command: str): Run terminal commands
- media_control(action: str): Controls media playback ('playpause', 'nexttrack', 'prevtrack', 'volumemute', 'volumeup', 'volumedown').
- press_keys(*keys): Simulates pressing keyboard keys.
- open_local_app(target: str): ALWAYS use this to launch computer software, local desktop applications (like docker, whatsapp, spotify), folders, or drives.
- start_macro_recording(name: str): Start recording your subsequent actions into a reusable macro.
- stop_macro_recording(): Stop the current macro recording.
- list_macros(): List all saved macros.
- play_macro(name: str): Execute a previously saved macro, bypassing the LLM to run steps instantly.
- save_to_memory(fact: str): Saves a fact, preference, or piece of context to your persistent long-term memory for future conversations.
- delegate_to_subagent(role: str, task: str): Spawns an autonomous sub-agent with full tool access to handle a complex multi-step task for you. Use to split work.
- ask_subagent_quick(role: str, question: str): Asks a fast, purely analytical sub-agent a question (no tools). Use for quick coding, math, or reasoning tasks.
{plugin_manager.get_prompt_additions()}

Previous observations:
{observations}

CRITICAL INSTRUCTION: Output ONLY a valid JSON object. Do not write any thoughts, explanations, or text outside the JSON.
```json
{{
    "tool_calls": [
        {{"name": "tool_name", "args": {{"arg1": "value1"}}}}
    ]
}}
```
"""
    messages = [{"role": "user", "content": prompt}]
    
    # Fast tool routing using the small model
    response = await generate_chat_response(
        messages=messages, 
        model="qwen3:1.7b", 
        stream=False, 
        thinking=False
    )
    content = response.choices[0].message.content
    
    parsed = extract_json_from_text(content)
    
    # Small models sometimes output the array directly instead of wrapping it in a dict
    if isinstance(parsed, list):
        tool_calls = parsed
    elif isinstance(parsed, dict):
        tool_calls = parsed.get("tool_calls", [])
    else:
        tool_calls = []
    
    log_step(task_id, "planner", "success", f"Generated {len(tool_calls)} tool calls")
    
    return {
        "plan": content,
        "tool_calls": tool_calls,
        "status": "acting" if tool_calls else "verifying",
        "iteration": iteration + 1,
        "messages": [{"role": "assistant", "content": f"Plan: {content}"}]
    }

async def executor_node(state: AgentState) -> Dict[str, Any]:
    """Executes the tool calls safely."""
    from services.gateway.cancel_token import check_cancel
    if check_cancel():
        return {"status": "done", "final_response": "⚠️ Task stopped by user."}

    tool_calls = state.get("tool_calls", [])
    pending_approvals = state.get("pending_approvals", [])
    task_id = state.get("task_id")
    new_observations = []
    executed_tools = []
    
    # 1. Pre-execution Permission Check
    unapproved_tools = check_for_unapproved_tools(tool_calls, pending_approvals)
    
    if unapproved_tools:
        log_step(task_id, "executor", "approval_required", str(unapproved_tools))
        # Pause execution and route to human-in-the-loop
        return {
            "status": "approval_required",
            "pending_approvals": unapproved_tools
        }
    
    # 2. Execute tools if LOW/MEDIUM or explicitly approved
    for call in tool_calls:
        tool_name = call.get("name")
        args = call.get("args", {})
        
        # Check if the user explicitly denied it
        if is_tool_denied(tool_name, args, pending_approvals):
            new_observations.append(f"Tool '{tool_name}' failed: User DENIED permission.")
            continue
            
        if tool_name in TOOL_MAP:
            try:
                # Execute the tool
                func = TOOL_MAP[tool_name]
                result = func(**args)
                new_observations.append(f"Tool '{tool_name}' result:\n{result}")
                executed_tools.append(call)
                
                # Record the tool call if macro recording is active
                from services.macros.manager import record_tool_call
                record_tool_call(tool_name, args)
                
            except Exception as e:
                new_observations.append(f"Tool '{tool_name}' failed: {str(e)}")
        else:
            new_observations.append(f"Tool '{tool_name}' not found.")
            
    # 3. Run Deterministic Evaluator on executed tools
    if executed_tools:
        eval_results = evaluate_executed_tools(executed_tools)
        if eval_results:
            new_observations.extend(eval_results)
            
    log_step(task_id, "executor", "success", f"Executed {len(executed_tools)} tools")
            
    return {
        "observations": new_observations,
        "status": "observing",
        "pending_approvals": [], # clear the queue once handled
        "tool_calls": [] # clear to prevent re-execution if state loops
    }

async def verifier_node(state: AgentState) -> Dict[str, Any]:
    """Verifies if the task is completed."""
    from services.gateway.cancel_token import check_cancel
    if check_cancel():
        return {"status": "done", "final_response": "⚠️ Task stopped by user."}

    task = state["task"]
    observations = state.get("observations", [])
    task_id = state.get("task_id")

    prompt = f"""You are the Verifier agent.
Task: "{task}"
Observations so far:
{observations}

Think deeply about whether every single part of the task is fully complete based on the observations. 
CRITICAL RULES:
1. If there are still pending actions requested in the task that have not been successfully observed, you MUST set "complete": false.
2. Do NOT ask the user for permission to proceed. You must complete all steps autonomously.
3. If it is NOT complete, set "final_response" to null.
4. Only if EVERY part of the task is complete, set "complete": true and write a helpful final response.
5. IF the task involved researching, extracting data, generating a summary, or answering a question, you MUST include the detailed information, summaries, and findings directly in your "final_response". Do not just say the task is complete!

Output your response as a JSON object inside a markdown code block:
```json
{{
    "thought": "your deep reasoning about whether every step of the task is complete",
    "complete": true/false,
    "final_response": "Your final message to the user, or null if not complete"
}}
```
"""
    messages = [{"role": "user", "content": prompt}]
    
    # Use the large model with thinking enabled for deep synthesis and verification
    response = await generate_chat_response(
        messages=messages, 
        model="qwen3:8b", 
        stream=False, 
        thinking=True
    )
    content = response.choices[0].message.content
    
    parsed = extract_json_from_text(content)
    
    if isinstance(parsed, dict):
        is_complete = parsed.get("complete", False)
        final_response = parsed.get("final_response", "Task verified.")
    else:
        is_complete = False
        final_response = "Error: Verifier model returned an invalid JSON structure."
        
    if is_complete:
        try:
            from services.voice.tts import synthesize_speech, play_audio, play_completion_sound
            import threading
            
            def play_voice_feedback():
                wav_path = synthesize_speech(final_response)
                if wav_path:
                    play_audio(wav_path)
                play_completion_sound()
                
            # Run audio in background thread to prevent blocking the async return
            threading.Thread(target=play_voice_feedback, daemon=True).start()
        except Exception as e:
            log_step(task_id, "voice", "error", str(e))
    
    log_step(task_id, "verifier", "done" if is_complete else "planning", final_response)
    
    return {
        "status": "done" if is_complete else "planning",
        "final_response": final_response,
        "messages": [{"role": "assistant", "content": f"Verification: {content}"}]
    }
