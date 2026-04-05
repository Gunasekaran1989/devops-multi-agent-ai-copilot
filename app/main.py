"""
FastAPI application — DevOps Multi-Agent AI Copilot
"""
from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from app.coordinator import run_workflow
from app.tools import db_tools

app = FastAPI(
    title="DevOps Multi-Agent AI Copilot",
    description="Multi-agent system with MCP tool integration for incident management",
    version="2.0.0",
)

# ── Static dashboard ──────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", tags=["UI"])
def dashboard():
    return FileResponse("app/static/dashboard.html")

# ── Request schemas ───────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    log: str

class StatusUpdate(BaseModel):
    status: str

# ── Core workflow endpoint ────────────────────────────────────────────────
@app.post("/analyze", tags=["Workflow"])
async def analyze(req: AnalyzeRequest, x_use_ai: str = Header(default="false")):
    """Run the full multi-agent workflow on a log string."""
    use_ai = x_use_ai.lower() == "true"
    result = await run_workflow(req.log, use_ai=use_ai)
    return dict(result)

# ── Incidents ─────────────────────────────────────────────────────────────
@app.get("/incidents", tags=["Incidents"])
def get_incidents(limit: int = 20):
    return db_tools.list_incidents(limit=limit)

@app.get("/incidents/{incident_id}", tags=["Incidents"])
def get_incident(incident_id: str):
    inc = db_tools.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc

@app.patch("/incidents/{incident_id}/status", tags=["Incidents"])
def update_incident(incident_id: str, body: StatusUpdate):
    db_tools.update_incident_status(incident_id, body.status)
    return {"updated": incident_id, "status": body.status}

# ── Tasks ─────────────────────────────────────────────────────────────────
@app.get("/tasks", tags=["Tasks"])
def get_tasks(incident_id: Optional[str] = None, status: Optional[str] = None):
    return db_tools.list_tasks(incident_id=incident_id, status=status)

@app.get("/tasks/{task_id}", tags=["Tasks"])
def get_task(task_id: str):
    t = db_tools.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t

@app.patch("/tasks/{task_id}/status", tags=["Tasks"])
def update_task(task_id: str, body: StatusUpdate):
    db_tools.update_task_status(task_id, body.status)
    return {"updated": task_id, "status": body.status}

# ── Notes ─────────────────────────────────────────────────────────────────
@app.get("/notes", tags=["Notes"])
def get_notes(incident_id: Optional[str] = None):
    return db_tools.list_notes(incident_id=incident_id)

# ── Calendar ──────────────────────────────────────────────────────────────
@app.get("/calendar", tags=["Calendar"])
def get_calendar(incident_id: Optional[str] = None):
    return db_tools.list_calendar_events(incident_id=incident_id)

# ── Health ────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "version": "2.0.0", "agents": 5, "mcp_servers": 3}
