"""
MCP Notes Server
Exposes notes tool: create_incident_note, list_notes
"""
import sqlite3
import uuid
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("NotesServer")

DB_PATH = "devops.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            note_id TEXT PRIMARY KEY,
            incident_id TEXT,
            content TEXT,
            author TEXT,
            created_at TEXT,
            tags TEXT
        )
    """)
    conn.commit()
    return conn

@mcp.tool()
def create_incident_note(
    incident_id: str,
    content: str,
    author: str = "AI-Agent",
    tags: str = ""
) -> dict:
    """Create a note linked to an incident."""
    note_id = f"NOTE-{str(uuid.uuid4())[:6].upper()}"
    created_at = datetime.utcnow().isoformat()

    conn = get_conn()
    conn.execute(
        "INSERT INTO notes VALUES (?,?,?,?,?,?)",
        (note_id, incident_id, content, author, created_at, tags)
    )
    conn.commit()
    conn.close()

    return {
        "note_id": note_id,
        "incident_id": incident_id,
        "content": content,
        "author": author,
        "created_at": created_at,
        "tags": tags
    }

@mcp.tool()
def list_notes(incident_id: str = None) -> list:
    """List notes, optionally filtered by incident_id."""
    conn = get_conn()
    if incident_id:
        rows = conn.execute(
            "SELECT * FROM notes WHERE incident_id=? ORDER BY created_at DESC", (incident_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM notes ORDER BY created_at DESC LIMIT 20").fetchall()
    conn.close()
    cols = ["note_id","incident_id","content","author","created_at","tags"]
    return [dict(zip(cols, r)) for r in rows]

if __name__ == "__main__":
    mcp.run(transport="stdio")
