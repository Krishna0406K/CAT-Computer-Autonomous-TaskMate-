import os

def read_file(filepath: str) -> str:
    """Read contents of a local file."""
    try:
        if not os.path.exists(filepath):
            return f"Error: File {filepath} does not exist."
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Truncate to avoid context limit issues
            return content[:2000] + ("..." if len(content) > 2000 else "")
    except Exception as e:
        return f"Error reading file: {str(e)}"
