import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cat.db")

def log_voice_event(
    event_type: str,
    state: str,
    latency_ms: int = 0,
    duration_ms: int = 0,
    transcription: str = "",
    success: bool = True,
    failure_reason: str = ""
):
    """Logs a voice pipeline event for dashboard observability."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO voice_telemetry 
                (event_type, state, latency_ms, duration_ms, transcription, success, failure_reason) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (event_type, state, latency_ms, duration_ms, transcription, success, failure_reason))
    except Exception as e:
        logger.error(f"Failed to log voice telemetry: {e}")

def get_voice_metrics() -> dict:
    """Retrieve voice health metrics for the dashboard."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            total_commands = conn.execute("SELECT COUNT(*) as c FROM voice_telemetry WHERE event_type='command'").fetchone()['c']
            successful_commands = conn.execute("SELECT COUNT(*) as c FROM voice_telemetry WHERE event_type='command' AND success=1").fetchone()['c']
            avg_stt_latency = conn.execute("SELECT AVG(latency_ms) as c FROM voice_telemetry WHERE event_type='command' AND success=1").fetchone()['c'] or 0
            empty_transcriptions = conn.execute("SELECT COUNT(*) as c FROM voice_telemetry WHERE event_type='command' AND failure_reason='empty'").fetchone()['c']
            wake_activations = conn.execute("SELECT COUNT(*) as c FROM voice_telemetry WHERE event_type='wake'").fetchone()['c']
            
            return {
                "total_commands": total_commands,
                "success_rate": f"{(successful_commands / total_commands * 100):.1f}%" if total_commands else "0%",
                "avg_stt_latency_ms": round(avg_stt_latency, 1),
                "empty_transcriptions": empty_transcriptions,
                "wake_activations": wake_activations
            }
    except Exception as e:
        logger.error(f"Failed to get voice metrics: {e}")
        return {}
