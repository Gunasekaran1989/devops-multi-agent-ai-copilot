"""
Calendar Agent — schedules maintenance windows via MCP Calendar server.
"""
from app.tools.db_tools import save_calendar_event
from app.tools.mcp_client import call_mcp_tool


async def schedule_maintenance(incident: dict) -> dict:
    title = f"Maintenance: {incident.get('error','Unknown')} [{incident['id']}]"
    duration = 120 if incident.get("severity") in ("Critical","High") else 60

    result = await call_mcp_tool(
        "schedule_maintenance_window",
        incident_id=incident["id"],
        title=title,
        duration_minutes=duration,
        event_type="maintenance"
    )

    if "mcp_error" not in result:
        save_calendar_event(result)
        return result

    # Fallback
    from datetime import datetime, timedelta
    event = {
        "event_id":         f"EVT-{incident['id'][-6:]}",
        "incident_id":      incident["id"],
        "title":            title,
        "scheduled_at":     (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "duration_minutes": duration,
        "event_type":       "maintenance",
        "status":           "Scheduled",
    }
    save_calendar_event(event)
    return event
