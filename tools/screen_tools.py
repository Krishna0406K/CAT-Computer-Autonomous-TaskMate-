from PIL import Image, ImageGrab
import os
import base64
import httpx

def capture_screenshot(filename: str) -> str:
    """Capture a screenshot of the primary monitor and save to file."""
    try:
        if not filename.endswith('.png'):
            filename += '.png'
            
        # grab() takes a screenshot of the primary screen
        screenshot = ImageGrab.grab()
        screenshot.save(filename)
        return f"Successfully captured screenshot at: {os.path.abspath(filename)}"
    except Exception as e:
        return f"Error capturing screenshot: {str(e)}"

def analyze_screen(prompt: str) -> str:
    """
    Captures a screenshot and uses the local moondream vision model to analyze it via Ollama.
    """
    filename = "temp_vision_screenshot.jpg"
    try:
        # 1. Capture the screenshot
        screenshot = ImageGrab.grab()
        screenshot = screenshot.convert("RGB") # Standardize format
        
        # Optimize image size for 6GB VRAM constraint (Prevent Ollama 500 Errors)
        # Vision LLM compute graphs grow quadratically O(N^2) with image pixels!
        # We MUST shrink to 512x512 to keep the compute graph under 1 GB.
        max_size = (512, 512)
        screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save as JPEG (massive reduction in base64 payload size vs PNG)
        screenshot.save(filename, format="JPEG", quality=80)
        
        # 2. Encode to base64
        with open(filename, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        # 3. Explicitly unload ALL models to free up VRAM for the vision model
        import time
        try:
            httpx.post("http://localhost:11434/api/generate", json={"model": "qwen3:8b", "keep_alive": 0}, timeout=5.0)
            httpx.post("http://localhost:11434/api/generate", json={"model": "qwen3:1.7b", "keep_alive": 0}, timeout=5.0)
            httpx.post("http://localhost:11434/api/generate", json={"model": "moondream", "keep_alive": 0}, timeout=5.0)
            time.sleep(2) # Give Ollama exactly 2 seconds to flush the GPU memory
            
            # 3.5. PRE-LOAD Vision model with restricted context to force Ollama to honor it
            preload_payload = {
                "model": "moondream",
                "options": {"num_ctx": 2048}
            }
            httpx.post("http://localhost:11434/api/generate", json=preload_payload, timeout=30.0)
            
        except Exception:
            pass # Ignore connection errors here, we just attempt to clear VRAM
            
        # 4. Call Vision Model (moondream)
        payload = {
            "model": "moondream",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [base64_image]
                }
            ],
            "stream": False,
            "options": {
                "num_ctx": 2048
            }
        }
        
        response = httpx.post("http://localhost:11434/api/chat", json=payload, timeout=120.0)
        
        # If the user hasn't finished pulling the model, capture the specific 404 error nicely
        if response.status_code == 404:
            return "Error: Local Vision model not found! Please run 'ollama pull moondream' in your terminal and wait for it to finish."
            
        response.raise_for_status()
        data = response.json()
        
        # 4.5 UNLOAD Moondream immediately so the Verifier model (Qwen 8B) has room!
        try:
            httpx.post("http://localhost:11434/api/generate", json={"model": "moondream", "keep_alive": 0}, timeout=5.0)
        except: pass
        
        content = data.get("message", {}).get("content", "No content returned.")
        return f"Vision Analysis Result:\n{content}"
        
    except Exception as e:
        return f"Error analyzing screen via local Ollama model: {str(e)}"
    finally:
        # 5. Cleanup temp file
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass
