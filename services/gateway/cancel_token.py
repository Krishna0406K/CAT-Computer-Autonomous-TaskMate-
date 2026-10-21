# Global cancellation token to gracefully stop the LangGraph execution
is_cancelled = False

def set_cancel(val: bool):
    global is_cancelled
    is_cancelled = val

def check_cancel() -> bool:
    return is_cancelled
