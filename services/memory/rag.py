import os
import uuid
import datetime

# Attempt to import chromadb. If missing, we will fail gracefully.
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

CHROMA_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma")

client = None
collection = None

def _init_chroma():
    global client, collection
    if not CHROMA_AVAILABLE:
        return
        
    if client is None:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        # Initialize a persistent local ChromaDB instance
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        # Create or get the long-term memory collection
        # We rely on Chroma's default embedding function (all-MiniLM-L6-v2) which runs fast on CPU
        collection = client.get_or_create_collection(name="cat_long_term_memory")

def save_to_memory(fact: str) -> str:
    """
    Saves a fact, preference, or piece of information to long-term memory.
    The planner agent should use this whenever the user shares something about themselves or project context.
    """
    if not CHROMA_AVAILABLE:
        return "Error: chromadb is not installed. Please run 'pip install chromadb' to enable memory."
        
    _init_chroma()
    
    # Generate a unique ID and record the timestamp
    doc_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    collection.add(
        documents=[fact],
        metadatas=[{"timestamp": timestamp}],
        ids=[doc_id]
    )
    
    return f"Successfully saved to long-term memory: '{fact}'"

def retrieve_memory(query: str, n_results: int = 3) -> list:
    """
    Searches the long term memory for context relevant to the query.
    Returns a list of matching strings.
    """
    if not CHROMA_AVAILABLE:
        return []
        
    _init_chroma()
    
    # If the collection is empty, querying throws an error in some versions, or returns empty.
    if collection.count() == 0:
        return []
        
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    documents = results.get("documents", [[]])[0]
    return documents
