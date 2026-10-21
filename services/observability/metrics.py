import sqlite3
import os
import psutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cat.db")

def get_dashboard_metrics():
    """Queries the SQLite database and system for Phase 9 Observatory Metrics."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            # Tasks completed today
            today_tasks = conn.execute("SELECT COUNT(*) as count FROM tasks WHERE date(created_at) = date('now', 'localtime')").fetchone()['count']
            
            # Total tasks
            total_tasks = conn.execute("SELECT COUNT(*) as count FROM tasks").fetchone()['count']
            
            # Success Rate (Tasks that don't have an error in their final response)
            # This is a safe approximation since errors usually contain 'Error communicating' or 'Error:'
            successful_tasks = conn.execute("SELECT COUNT(*) as count FROM tasks WHERE final_response IS NOT NULL AND final_response NOT LIKE '%Error%'").fetchone()['count']
            success_rate = f"{(successful_tasks / total_tasks * 100):.1f}%" if total_tasks > 0 else "0%"
            
            # Average execution time (in seconds)
            # Calculated as difference between first and last step for a given task
            time_query = """
                SELECT AVG(duration) as avg_time FROM (
                    SELECT task_id, 
                           (julianday(MAX(created_at)) - julianday(MIN(created_at))) * 86400.0 as duration 
                    FROM steps 
                    GROUP BY task_id 
                    HAVING COUNT(*) > 1
                )
            """
            avg_time = conn.execute(time_query).fetchone()['avg_time']
            avg_time_str = f"{avg_time:.1f}s" if avg_time else "0s"

            # Recent Tasks (Last 5)
            recent_tasks_query = """
                SELECT 
                    t.id, 
                    t.task_prompt, 
                    t.created_at,
                    CASE WHEN t.final_response LIKE '%Error%' THEN 'Failed' ELSE 'Success' END as status,
                    IFNULL((
                        SELECT (julianday(MAX(created_at)) - julianday(MIN(created_at))) * 86400.0 
                        FROM steps 
                        WHERE task_id = t.id
                    ), 0) as duration_seconds
                FROM tasks t
                ORDER BY t.created_at DESC
                LIMIT 5
            """
            recent_tasks = [dict(row) for row in conn.execute(recent_tasks_query).fetchall()]
            
    except Exception as e:
        # Fallback if DB is empty or missing
        today_tasks = total_tasks = 0
        success_rate = "0%"
        avg_time_str = "0s"
        recent_tasks = []

    # System Metrics (CPU/RAM)
    try:
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_percent": psutil.virtual_memory().percent,
            "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 1),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1)
        }
    except Exception:
        system_metrics = {
            "cpu_percent": 0, "ram_percent": 0, "ram_used_gb": 0, "ram_total_gb": 0
        }

    return {
        "today_tasks": today_tasks,
        "total_tasks": total_tasks,
        "success_rate": success_rate,
        "avg_execution_time": avg_time_str,
        "recent_tasks": recent_tasks,
        "system_metrics": system_metrics
    }
