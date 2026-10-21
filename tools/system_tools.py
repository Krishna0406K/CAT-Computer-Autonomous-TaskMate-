import subprocess
import threading
import os

# Global reference to the currently running process
CURRENT_PROCESS = None
PROCESS_LOCK = threading.Lock()

def execute_system_command(command: str) -> str:
    """Executes a terminal/shell command on the host system."""
    global CURRENT_PROCESS
    try:
        with PROCESS_LOCK:
            CURRENT_PROCESS = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
        
        try:
            # Wait up to 60 seconds for the command to finish
            stdout, stderr = CURRENT_PROCESS.communicate(timeout=60)
            code = CURRENT_PROCESS.returncode
            
            with PROCESS_LOCK:
                CURRENT_PROCESS = None
                
            if code == 0:
                return f"Command succeeded:\n{stdout}"
            else:
                return f"Command stopped or failed (Exit code {code}):\nStdout: {stdout}\nStderr: {stderr}"
                
        except subprocess.TimeoutExpired:
            abort_current_command()
            return "Command timed out after 60 seconds and was killed."
            
    except Exception as e:
        return f"Error executing command: {str(e)}"

def abort_current_command() -> bool:
    """Forcefully terminates the currently running system command."""
    global CURRENT_PROCESS
    with PROCESS_LOCK:
        if CURRENT_PROCESS:
            try:
                # On Windows, we use taskkill to kill the entire process tree (e.g. ping and cmd)
                subprocess.run(f"taskkill /F /T /PID {CURRENT_PROCESS.pid}", shell=True, capture_output=True)
            except Exception:
                pass
            CURRENT_PROCESS = None
            return True
    return False
