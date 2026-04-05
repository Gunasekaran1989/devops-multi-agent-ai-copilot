"""
MCP Calendar Server
Exposes calendar tool: schedule_maintenance_window
"""
import json
import sqlite3
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("CalendarServer")

DB_PATH = "devops.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            event_id TEXT PRIMARY KEY,
            incident_id TEXT,
            title TEXT,
            scheduled_at TEXT,
            duration_minutes INTEGER,
            event_type TEXT,
            status TEXT
        )
    """)
    conn.commit()
    return conn

@mcp.tool()
def schedule_maintenance_window(
    incident_id: str,
    title: str,
    duration_minutes: int = 60,
    event_type: str = "maintenance"
) -> dict:
    """Schedule a maintenance window for an incident."""
    scheduled_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    event_id = f"EVT-{incident_id[-6:]}"

    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO calendar_events VALUES (?,?,?,?,?,?,?)",
        (event_id, incident_id, title, scheduled_at, duration_minutes, event_type, "Scheduled")
    )
    conn.commit()
    conn.close()

    return {
        "event_id": event_id,
        "incident_id": incident_id,
        "title": title,
        "scheduled_at": scheduled_at,
        "duration_minutes": duration_minutes,
        "event_type": event_type,
        "status": "Scheduled"
    }

@mcp.tool()
def list_calendar_events(incident_id: str = None) -> list:
    """List all calendar events, optionally filtered by incident_id."""
    conn = get_conn()
    if incident_id:
        rows = conn.execute(
            "SELECT * FROM calendar_events WHERE incident_id=?", (incident_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM calendar_events ORDER BY scheduled_at DESC LIMIT 20").fetchall()
    conn.close()
    cols = ["event_id","incident_id","title","scheduled_at","duration_minutes","event_type","status"]
    return [dict(zip(cols, r)) for r in rows]

if __name__ == "__main__":
    mcp.run(transport="stdio")
