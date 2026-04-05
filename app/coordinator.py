"""
Primary Coordinator
Orchestrates the full multi-agent workflow:
  1. Log Agent      → analyse log
  2. Incident Agent → create incident record
  3. Task Agent     → create remediation task (via MCP Task Manager)
  4. Notes Agent    → document incident        (via MCP Notes)
  5. Calendar Agent → schedule maintenance     (via MCP Calendar)
"""
import os
from app.agents.log_agent      import analyze_log
from app.agents.incident_agent import create_incident
from app.agents.task_agent     import create_task
from app.agents.calendar_agent import schedule_maintenance
from app.agents.notes_agent    import create_note


async def run_workflow(log: str, use_ai: bool = False) -> dict:
    os.environ["USE_AI"] = "true" if use_ai else "false"

    # ── Step 1: Log Agent (sync) ───────────────────────────────────────────
    log_data: dict = analyze_log(log)

    # ── Step 2: Incident Agent (sync) ─────────────────────────────────────
    incident: dict = create_incident(log_data)

    # ── Step 3: Task Agent (async → MCP task_manager) ─────────────────────
    task: dict = await create_task(incident)

    # ── Step 4: Notes Agent (async → MCP notes) ───────────────────────────
    note: dict = await create_note(incident, log_data)

    # ── Step 5: Calendar Agent (async → MCP calendar) ─────────────────────
    event: dict = await schedule_maintenance(incident)

    # Build a clean serialisable trace — no raw objects, only plain strings
    agent_trace = [
        {"agent": "log_agent",      "status": "completed", "tool": "internal"},
        {"agent": "incident_agent", "status": "completed", "tool": "internal"},
        {"agent": "task_agent",     "status": "completed", "tool": "MCP:task_manager"},
        {"agent": "notes_agent",    "status": "completed", "tool": "MCP:notes"},
        {"agent": "calendar_agent", "status": "completed", "tool": "MCP:calendar"},
    ]

    return {
        "workflow":       "coordinated_multi_agent_execution",
        "agent_trace":    agent_trace,
        "log_analysis":   log_data,
        "incident":       incident,
        "task":           task,
        "note":           note,
        "calendar_event": event,
    }
