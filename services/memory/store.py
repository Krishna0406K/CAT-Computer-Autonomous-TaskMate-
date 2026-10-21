import sqlite3
import os
import json
from datetime import datetime

# Path to the SQLite database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cat.db")

def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_prompt TEXT,
                final_response TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                node_name TEXT,
                status TEXT,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS voice_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                state TEXT,
                latency_ms INTEGER,
                duration_ms INTEGER,
                transcription TEXT,
                success BOOLEAN,
                failure_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def create_task(prompt: str) -> int:
    """Create a new task record and return its ID."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("INSERT INTO tasks (task_prompt) VALUES (?)", (prompt,))
        return cur.lastrowid

def update_task_result(task_id: int, response: str):
    """Update a task record with the final response."""
    if not task_id: return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE tasks SET final_response = ? WHERE id = ?", (response, task_id))

def log_step(task_id: int, node_name: str, status: str, details: str):
    """Log an execution step for a specific task."""
    if not task_id: return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO steps (task_id, node_name, status, details) VALUES (?, ?, ?, ?)",
            (task_id, node_name, status, details)
        )
