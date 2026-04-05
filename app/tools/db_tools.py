"""
Database tools — full CRUD for incidents, tasks, notes, calendar events.
All tables are created lazily on first access.
"""
import sqlite3
from typing import Optional

DB_PATH = "devops.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn

def _ensure_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            error TEXT,
            severity TEXT,
            status TEXT,
            summary TEXT,
            mode TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            incident_id TEXT,
            description TEXT,
            priority TEXT,
            assignee TEXT,
            status TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS notes (
            note_id TEXT PRIMARY KEY,
            incident_id TEXT,
            content TEXT,
            author TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            tags TEXT
        );
        CREATE TABLE IF NOT EXISTS calendar_events (
            event_id TEXT PRIMARY KEY,
            incident_id TEXT,
            title TEXT,
            scheduled_at TEXT,
            duration_minutes INTEGER,
            event_type TEXT,
            status TEXT
        );
    """)
    conn.commit()

# ── Incidents ──────────────────────────────────────────────────────────────

def save_incident(data: dict):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO incidents (id,error,severity,status,summary,mode) VALUES (?,?,?,?,?,?)",
        (data["id"], data["error"], data["severity"],
         data.get("status","Open"), data.get("summary",""), data.get("mode","fallback"))
    )
    conn.commit()
    conn.close()

def get_incident(incident_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM incidents WHERE id=?", (incident_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def list_incidents(limit: int = 20) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_incident_status(incident_id: str, status: str):
    conn = get_conn()
    conn.execute("UPDATE incidents SET status=? WHERE id=?", (status, incident_id))
    conn.commit()
    conn.close()

# ── Tasks ──────────────────────────────────────────────────────────────────

def save_task(data: dict):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO tasks (task_id,incident_id,description,priority,assignee,status) VALUES (?,?,?,?,?,?)",
        (data["task_id"], data["incident_id"], data["description"],
         data.get("priority","Medium"), data.get("assignee","on-call-team"),
         data.get("status","Pending"))
    )
    conn.commit()
    conn.close()

def get_task(task_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def list_tasks(incident_id: str = None, status: str = None, limit: int = 50) -> list:
    conn = get_conn()
    q, p = "SELECT * FROM tasks WHERE 1=1", []
    if incident_id: q += " AND incident_id=?"; p.append(incident_id)
    if status:      q += " AND status=?";      p.append(status)
    q += f" ORDER BY created_at DESC LIMIT {limit}"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_task_status(task_id: str, status: str):
    conn = get_conn()
    conn.execute("UPDATE tasks SET status=? WHERE task_id=?", (status, task_id))
    conn.commit()
    conn.close()

# ── Notes ──────────────────────────────────────────────────────────────────

def save_note(data: dict):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO notes (note_id,incident_id,content,author,tags) VALUES (?,?,?,?,?)",
        (data["note_id"], data["incident_id"], data["content"],
         data.get("author","AI-Agent"), data.get("tags",""))
    )
    conn.commit()
    conn.close()

def list_notes(incident_id: str = None, limit: int = 50) -> list:
    conn = get_conn()
    q, p = "SELECT * FROM notes WHERE 1=1", []
    if incident_id: q += " AND incident_id=?"; p.append(incident_id)
    q += f" ORDER BY created_at DESC LIMIT {limit}"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Calendar Events ────────────────────────────────────────────────────────

def save_calendar_event(data: dict):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO calendar_events VALUES (?,?,?,?,?,?,?)",
        (data["event_id"], data["incident_id"], data["title"],
         data["scheduled_at"], data.get("duration_minutes",60),
         data.get("event_type","maintenance"), data.get("status","Scheduled"))
    )
    conn.commit()
    conn.close()

def list_calendar_events(incident_id: str = None, limit: int = 20) -> list:
    conn = get_conn()
    q, p = "SELECT * FROM calendar_events WHERE 1=1", []
    if incident_id: q += " AND incident_id=?"; p.append(incident_id)
    q += f" ORDER BY scheduled_at DESC LIMIT {limit}"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return [dict(r) for r in rows]
