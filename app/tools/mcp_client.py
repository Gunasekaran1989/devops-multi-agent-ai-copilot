"""
MCP Client Bridge
Communicates with MCP servers over stdio JSON-RPC 2.0.
Fully async — no nest_asyncio, no asyncio.run() inside a running loop.
"""
import asyncio
import json
import sys
from typing import Any

MCP_SERVERS = {
    "calendar":     "app/mcp_servers/calendar_server.py",
    "notes":        "app/mcp_servers/notes_server.py",
    "task_manager": "app/mcp_servers/task_manager_server.py",
}

TOOL_ROUTE = {
    "schedule_maintenance_window": "calendar",
    "list_calendar_events":        "calendar",
    "create_incident_note":        "notes",
    "list_notes":                  "notes",
    "create_task":                 "task_manager",
    "update_task_status":          "task_manager",
    "list_tasks":                  "task_manager",
}


async def call_mcp_tool(tool_name: str, **kwargs) -> Any:
    """
    Async MCP tool call over stdio JSON-RPC 2.0.
    Always awaitable — safe to call from any async context (uvloop, asyncio).
    """
    server_key = TOOL_ROUTE.get(tool_name)
    if not server_key:
        return {"mcp_error": f"Unknown tool: {tool_name}", "tool": tool_name}

    script = MCP_SERVERS[server_key]

    init_msg = json.dumps({
        "jsonrpc": "2.0", "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "devops-copilot", "version": "2.0"}
        }
    }) + "\n"

    call_msg = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": kwargs}
    }) + "\n"

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(
            proc.communicate(input=(init_msg + call_msg).encode()),
            timeout=10.0
        )

        for line in reversed(stdout.decode().splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                resp = json.loads(line)
                if resp.get("id") == 1:
                    if "error" in resp:
                        return {"mcp_error": resp["error"].get("message", "MCP error"), "tool": tool_name}
                    content = resp.get("result", {}).get("content", [])
                    if content and content[0].get("type") == "text":
                        return json.loads(content[0]["text"])
                    return resp.get("result", {})
            except (json.JSONDecodeError, KeyError):
                continue

        return {"mcp_error": "No valid response from MCP server", "tool": tool_name}

    except asyncio.TimeoutError:
        return {"mcp_error": "MCP server timed out", "tool": tool_name}
    except Exception as e:
        return {"mcp_error": str(e), "tool": tool_name}
