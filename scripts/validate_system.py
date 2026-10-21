import httpx
import os
import sys
import sqlite3

def print_status(component, status, message):
    try:
        mark = "✅" if status else "❌"
        print(f"{mark} {component.ljust(20)} | {message}")
    except (UnicodeEncodeError, UnicodeError):
        mark = "[OK]" if status else "[X]"
        print(f"{mark} {component.ljust(20)} | {message}")

def validate_ollama():
    try:
        response = httpx.get("http://localhost:11434/")
        if response.status_code == 200:
            print_status("Ollama Base", True, "Ollama service is running")
            
            # Check models
            models_res = httpx.get("http://localhost:11434/api/tags").json()
            available_models = [m["name"] for m in models_res.get("models", [])]
            
            required_models = ["moondream", "moondream", "moondream"]
            for rm in required_models:
                found = any(m.startswith(rm) for m in available_models)
                print_status(f"Model: {rm}", found, "Model found" if found else "Model MISSING! Run 'ollama pull'!")
        else:
            print_status("Ollama Base", False, f"Unexpected status: {response.status_code}")
    except Exception as e:
        print_status("Ollama Base", False, f"Could not connect to Ollama: {str(e)}")

def validate_gateway():
    try:
        response = httpx.get("http://localhost:8000/observatory/metrics")
        if response.status_code == 200:
            print_status("Gateway Backend", True, "FastAPI server running and responding")
        else:
            print_status("Gateway Backend", False, f"Unexpected status: {response.status_code}")
    except Exception as e:
        print_status("Gateway Backend", False, f"Backend not running: {str(e)}. Start main.py first.")

def validate_database():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cat.db")
    if os.path.exists(db_path):
        try:
            with sqlite3.connect(db_path) as conn:
                count = conn.execute("SELECT count(*) FROM tasks").fetchone()[0]
                print_status("SQLite Database", True, f"DB exists and readable. Found {count} task(s).")
        except Exception as e:
            print_status("SQLite Database", False, f"DB error: {str(e)}")
    else:
        print_status("SQLite Database", False, "cat.db not found!")

if __name__ == "__main__":
    print("==========================================")
    print("      CAT System Validation Check         ")
    print("==========================================\n")
    validate_ollama()
    validate_database()
    validate_gateway()
    print("\n==========================================")
    print("If all checks are [OK], you are ready to bundle!")
    print("Run `npm run tauri build` in apps/desktop.")
