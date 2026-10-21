import os

def create_word_document(filename: str, content: str) -> str:
    """Create a Word document with the given content."""
    try:
        import docx # Lazy import so it doesn't crash the whole server if missing
    except ImportError:
        return "Error: python-docx library is not installed. Use another tool like file creation, or install it first."
        
    try:
        # Ensure it ends with .docx
        if not filename.endswith('.docx'):
            filename += '.docx'
            
        doc = docx.Document()
        doc.add_paragraph(content)
        doc.save(filename)
        return f"Successfully created Word document at: {os.path.abspath(filename)}"
    except Exception as e:
        return f"Error creating Word document: {str(e)}"
