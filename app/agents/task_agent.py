"""
Task Agent — creates remediation tasks via the MCP Task Manager server.
Falls back to direct DB write if MCP is unavailable.
"""
from app.tools.db_tools import save_task
from app.tools.mcp_client import call_mcp_tool


# Severity → priority + assignee mapping
PRIORITY_MAP = {
    "Critical": ("Critical", "senior-sre-team"),
    "High":     ("High",     "on-call-team"),
    "Medium":   ("Medium",   "dev-team"),
    "Low":      ("Low",      "dev-team"),
}

# Error type → remediation description
ACTION_MAP = {
    "Timeout Error":       "Investigate service timeouts; check upstream dependencies and increase timeout thresholds",
    "Connection Failure":  "Diagnose network connectivity; verify firewall rules and service health",
    "Out of Memory":       "Analyse memory usage; consider scaling up or restarting affected service",
    "Disk Full":           "Clear old logs and temp files; expand storage or add log rotation",
    "High CPU":            "Profile CPU usage; identify runaway processes and throttle or restart",
    "Operation Failed":    "Review service logs for root cause; apply hotfix or rollback",
}


async def create_task(incident: dict) -> dict:
    error_type = incident.get("error", "Unknown")
    severity   = incident.get("severity", "Low")
    priority, assignee = PRIORITY_MAP.get(severity, ("Medium", "dev-team"))
    description = ACTION_MAP.get(error_type, f"Investigate and resolve: {error_type}")

    # Try MCP task manager first
    result = await call_mcp_tool(
        "create_task",
        incident_id=incident["id"],
        description=description,
        priority=priority,
        assignee=assignee,
    )

    if "mcp_error" not in result:
        # MCP succeeded — persist locally too for query API consistency
        save_task(result)
        return result

    # MCP unavailable — direct DB fallback
    task = {
        "task_id":     "TASK-" + incident["id"],
        "incident_id": incident["id"],
        "description": description,
        "priority":    priority,
        "assignee":    assignee,
        "status":      "Pending",
    }
    save_task(task)
    return task
