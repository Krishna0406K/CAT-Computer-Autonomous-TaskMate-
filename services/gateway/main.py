from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from services.gateway.models import generate_chat_response

app = FastAPI(title="CAT Gateway - Phase 14")

# Enable CORS for the Tauri frontend and Mobile Web App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your phone to connect via Local IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os

# Mount the Mobile Web App
mobile_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "apps", "mobile")
app.mount("/mobile", StaticFiles(directory=mobile_path, html=True), name="mobile")

@app.post("/cancel")
async def cancel_endpoint():
    from tools.system_tools import abort_current_command
    from services.gateway.cancel_token import set_cancel
    
    set_cancel(True) # Tell the LangGraph loop to abort
    aborted = abort_current_command() # Also kill any running system commands
    return {"status": "cancelled", "command_aborted": aborted}

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = False
    thinking: bool = True
    model: str = "qwen3:8b"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Convert pydantic models to dicts for the openai client
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        response = await generate_chat_response(
            messages=messages,
            model=request.model,
            stream=request.stream,
            thinking=request.thinking
        )

        if request.stream:
            async def stream_generator():
                async for chunk in response:
                    # The OpenAI compatible response chunking structure
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content
                        
            return StreamingResponse(stream_generator(), media_type="text/plain")
        else:
            return {"response": response.choices[0].message.content}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from services.memory.store import init_db, create_task, update_task_result

# Initialize database on startup
init_db()

import asyncio
from fastapi import Request
from queue import Queue

# Cross-thread communication queue for SSE
voice_command_queue = Queue()
voice_state_queue = Queue()
active_sse_connections = 0

@app.get("/voice_stream")
async def voice_stream(request: Request):
    """Server-Sent Events endpoint to stream voice commands to the desktop UI."""
    global active_sse_connections
    active_sse_connections += 1
    
    async def event_generator():
        global active_sse_connections
        try:
            while True:
                if await request.is_disconnected():
                    break
                if not voice_command_queue.empty():
                    cmd = voice_command_queue.get()
                    yield f"data: {cmd}\n\n"
                await asyncio.sleep(0.5)
        finally:
            active_sse_connections -= 1
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/voice_state_stream")
async def voice_state_stream(request: Request):
    """Server-Sent Events endpoint to stream voice pipeline state changes."""
    async def state_generator():
        while True:
            if await request.is_disconnected():
                break
            if not voice_state_queue.empty():
                state = voice_state_queue.get()
                yield f"data: {state}\n\n"
            await asyncio.sleep(0.2)
    return StreamingResponse(state_generator(), media_type="text/event-stream")

@app.get("/voice_telemetry")
async def get_telemetry():
    from services.voice.telemetry import get_voice_metrics
    return get_voice_metrics()

@app.get("/observatory/metrics")
async def get_observatory_metrics():
    from services.observability.metrics import get_dashboard_metrics
    return get_dashboard_metrics()

class VoiceCommand(BaseModel):
    task: str

@app.post("/internal/voice_command")
async def handle_voice_command(cmd: VoiceCommand):
    """Internal router for background voice commands."""
    global active_sse_connections
    if active_sse_connections > 0:
        voice_command_queue.put(cmd.task)
        return {"status": "routed_to_ui"}
    else:
        import threading
        import httpx
        def _run_headless():
            try:
                with httpx.Client(timeout=300.0) as client:
                    client.post("http://localhost:8000/agent", json={"task": cmd.task})
            except:
                pass
        threading.Thread(target=_run_headless, daemon=True).start()
        return {"status": "routed_headless"}

# Start the new Voice Pipeline
from services.voice.pipeline import VoicePipeline

def _on_voice_state_change(new_state):
    voice_state_queue.put(new_state)

voice_pipeline = None
try:
    voice_pipeline = VoicePipeline(state_callback=_on_voice_state_change)
    voice_pipeline.start()
except Exception as e:
    logger.error(f"Failed to start Voice Pipeline: {e}")

@app.on_event("shutdown")
def shutdown_event():
    """Gracefully shutdown background processes to prevent zombie microphone locks."""
    global voice_pipeline
    logger.info("Initiating graceful shutdown of backend services...")
    if voice_pipeline:
        try:
            voice_pipeline.stop()
            logger.info("Voice Pipeline stopped cleanly.")
        except Exception as e:
            logger.error(f"Error stopping Voice Pipeline: {e}")

class AgentRequest(BaseModel):
    task: str
    state: Optional[dict] = None

@app.post("/agent")
async def agent_endpoint(request: AgentRequest):
    try:
        from services.gateway.cancel_token import set_cancel
        set_cancel(False)
        from services.harness.graph import build_graph
        app_graph = build_graph()
        
        # Load passed state (to resume) or initialize new state
        if request.state:
            initial_state = request.state
            task_id = request.state.get("task_id")
        else:
            task_id = create_task(request.task)
            initial_state = {
                "task": request.task,
                "plan": None,
                "tool_calls": [],
                "observations": [],
                "status": "planning",
                "messages": [],
                "iteration": 0,
                "final_response": None,
                "pending_approvals": [],
                "task_id": task_id
            }
        
        # Invoke graph. If approval is required, it exits early and returns the paused state
        final_state = await app_graph.ainvoke(initial_state)
        
        # Safely handle responses if the agent hit iteration limit or failed to verify
        final_response = final_state.get("final_response")
        if not final_response and final_state.get("status") != "approval_required":
            final_response = "I searched for the information but could not definitively verify the answer. Please try rephrasing your question."
            final_state["final_response"] = final_response
            
        if final_state.get("status") == "done" or final_response:
            update_task_result(task_id, final_response)
            
        # Optional Voice feedback if high-risk approval is required
        if final_state.get("status") == "approval_required":
            try:
                from services.voice.tts import synthesize_speech, play_audio
                import threading
                def _play_approval():
                    wav = synthesize_speech("I need your permission for that. Please approve the action in the desktop shell.")
                    if wav: play_audio(wav)
                threading.Thread(target=_play_approval, daemon=True).start()
            except:
                pass
            
        return {
            "status": final_state.get("status"),
            "final_response": final_response,
            "iterations": final_state.get("iteration"),
            "state": final_state # Send full state back so CLI can resume it
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

import socket

@app.get("/network_info")
async def get_network_info():
    """Returns the local IP and mobile URL for the QR Code."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
    
    return {
        "ip": local_ip,
        "mobile_url": f"http://{local_ip}:8000/mobile"
    }

from fastapi import UploadFile, File
import shutil
import os

@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    try:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        from services.voice.stt import transcribe_audio
        text = transcribe_audio(temp_path)
        
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
            
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.gateway.main:app", host="0.0.0.0", port=8000, reload=True)
