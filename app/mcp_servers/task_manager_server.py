"""
MCP Task Manager Server
Exposes task tools: create_task, update_task_status, list_tasks
"""
import sqlite3
import uuid
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TaskManagerServer")

DB_PATH = "devops.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            incident_id TEXT,
            description TEXT,
            priority TEXT,
            assignee TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn

@mcp.tool()
def create_task(
    incident_id: str,
    description: str,
    priority: str = "Medium",
    assignee: str = "on-call-team"
) -> dict:
    """Create a remediation task for an incident."""
    task_id = f"TASK-{str(uuid.uuid4())[:6].upper()}"
    created_at = datetime.utcnow().isoformat()

    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO tasks VALUES (?,?,?,?,?,?,?)",
        (task_id, incident_id, description, priority, assignee, "Pending", created_at)
    )
    conn.commit()
    conn.close()

    return {
        "task_id": task_id,
        "incident_id": incident_id,
        "description": description,
        "priority": priority,
        "assignee": assignee,
        "status": "Pending",
        "created_at": created_at
    }

@mcp.tool()
def update_task_status(task_id: str, status: str) -> dict:
    """Update status of an existing task."""
    conn = get_conn()
    conn.execute("UPDATE tasks SET status=? WHERE task_id=?", (status, task_id))
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    conn.close()
    if not row:
        return {"error": f"Task {task_id} not found"}
    cols = ["task_id","incident_id","description","priority","assignee","status","created_at"]
    return dict(zip(cols, row))

@mcp.tool()
def list_tasks(incident_id: str = None, status: str = None) -> list:
    """List tasks with optional filters."""
    conn = get_conn()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if incident_id:
        query += " AND incident_id=?"
        params.append(incident_id)
    if status:
        query += " AND status=?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT 50"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    cols = ["task_id","incident_id","description","priority","assignee","status","created_at"]
    return [dict(zip(cols, r)) for r in rows]

if __name__ == "__main__":
    mcp.run(transport="stdio")
