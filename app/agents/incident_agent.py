"""
Incident Agent — creates structured incident records in the database.
"""
import uuid
from app.tools.db_tools import save_incident


def create_incident(log_data: dict) -> dict:
    incident = {
        "id":       "INC-" + str(uuid.uuid4())[:6].upper(),
        "error":    log_data.get("error", "Unknown"),
        "severity": log_data.get("severity", "Low"),
        "status":   "Open",
        "summary":  log_data.get("summary", ""),
        "mode":     log_data.get("mode", "fallback"),
    }
    save_incident(incident)
    return incident
