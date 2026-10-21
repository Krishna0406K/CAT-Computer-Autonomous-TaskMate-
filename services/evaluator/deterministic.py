import os
import sqlite3

def check_file_exists(filepath: str) -> bool:
    """Deterministically verify a file exists and has a size greater than 0."""
    return os.path.exists(filepath) and os.path.getsize(filepath) > 0

def check_docx_valid(filepath: str) -> bool:
    """Verify the file exists and is a valid docx readable by python-docx."""
    if not check_file_exists(filepath): return False
    try:
        import docx
        doc = docx.Document(filepath)
        return len(doc.paragraphs) > 0
    except Exception:
        return False

def check_db_rows(db_path: str, table: str, expected_min: int = 1) -> bool:
    """Verify a database table has at least expected_min rows."""
    if not os.path.exists(db_path): return False
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            return count >= expected_min
    except Exception:
        return False

def evaluate_executed_tools(tool_calls: list) -> list:
    """
    Run deterministic evaluation checks on executed tools.
    Returns a list of verification statements to feed back into the agent's memory.
    """
    results = []
    for call in tool_calls:
        name = call.get("name")
        args = call.get("args", {})
        
        if name == "create_word_document":
            fname = args.get("filename")
            if fname:
                valid = check_docx_valid(fname)
                results.append(f"[EVALUATOR] create_word_document for '{fname}' -> Valid DOCX: {valid}")
        elif name == "capture_screenshot":
            fname = args.get("filename")
            if fname:
                exists = check_file_exists(fname)
                results.append(f"[EVALUATOR] capture_screenshot for '{fname}' -> File Exists: {exists}")
        elif name == "read_file":
            fname = args.get("filepath")
            if fname:
                exists = check_file_exists(fname)
                results.append(f"[EVALUATOR] read_file for '{fname}' -> File Exists: {exists}")
                
    return results
