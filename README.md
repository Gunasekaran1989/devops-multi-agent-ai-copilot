# DevOps Multi-Agent AI Copilot

A multi-agent AI system for automated DevOps incident management using MCP (Model Context Protocol), Google Gemini AI, FastAPI, and Google Cloud Run.

## Architecture
- **5 AI Agents**: log_agent → incident_agent → task_agent → notes_agent → calendar_agent
- **3 MCP Servers**: task_manager, calendar, notes
- **12 REST API endpoints**
- **Google Gemini 2.5 Flash** with intelligent fallback

## Tech Stack
- FastAPI + uvicorn
- Google Gemini AI (google-genai)
- MCP (mcp[cli] + FastMCP)
- SQLite
- Docker + Google Cloud Run

## Quick Start
```bash
docker build -t devops-copilot .
docker run -p 8080:8080 -e GOOGLE_API_KEY="your_key" devops-copilot

API Endpoints
•	POST /analyze — Run full 5-agent workflow
•	GET /incidents — List all incidents
•	GET /tasks — List tasks
•	GET /notes — List notes
•	GET /calendar — List calendar events
•	GET /health — Health check
Deployed on Google Cloud Run
