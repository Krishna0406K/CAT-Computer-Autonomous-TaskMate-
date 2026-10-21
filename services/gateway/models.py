import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables (API keys and models)
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Local Ollama client (for small models / vision)
ollama_client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" 
)

# Groq client (for large model heavy lifting)
groq_client = None
if GROQ_API_KEY:
    groq_client = AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY
    )

import datetime

import httpx

async def _unload_model(model_name: str):
    """Frees up VRAM by unloading a specific model."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:11434/api/generate", 
                json={"model": model_name, "keep_alive": 0},
                timeout=3.0
            )
    except Exception:
        pass # Ignore connection errors if Ollama is busy

async def generate_chat_response(messages: list, model: str = "qwen3:8b", stream: bool = False, thinking: bool = True):
    """
    Calls either the local Ollama model or Groq API based on model type.
    Actively manages VRAM for 6GB constraints by unloading conflicting models.
    """
    current_time = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
    system_prompt = f"You are a helpful AI assistant. The current system date and time is {current_time}."
    if not thinking:
        system_prompt += " Answer directly, concisely, and quickly without any internal reasoning or chain of thought."
    
    if not any(m.get("role") == "system" for m in messages):
        messages = [{"role": "system", "content": system_prompt}] + messages

    # Route large model tasks to Groq if configured
    if model == "qwen3:8b" and groq_client:
        active_client = groq_client
        active_model = GROQ_MODEL
    else:
        active_client = ollama_client
        active_model = model
        
        # PROACTIVE VRAM MANAGEMENT: If loading text, unload vision. If loading vision, unload text.
        if active_model == "qwen3:8b" or active_model == "qwen3:1.7b":
            await _unload_model("qwen3:8b")
            await _unload_model("qwen3:1.7b")
            await _unload_model("moondream")
        elif active_model == "moondream":
            await _unload_model("qwen3:8b")
            await _unload_model("qwen3:1.7b")
            await _unload_model("moondream")
            await _unload_model("qwen3:8b")
            await _unload_model("qwen3:1.7b")
            await _unload_model("moondream")

    response = await active_client.chat.completions.create(
        model=active_model,
        messages=messages,
        stream=stream,
    )
    
    return response
