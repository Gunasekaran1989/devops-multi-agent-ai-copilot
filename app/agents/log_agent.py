"""
Log Agent — analyses raw log strings.
Uses Gemini AI when USE_AI=true; falls back to keyword logic otherwise.
USE_AI is checked on every call so runtime toggling works correctly.
"""
import os
import re
import json

_client = None  # lazy-initialised on first AI call


def _get_client():
    """Initialise and cache the Gemini client on first use."""
    global _client
    if _client is not None:
        return _client
    try:
        from google import genai
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            return None
        _client = genai.Client(api_key=api_key)
        return _client
    except Exception as e:
        print("Gemini init failed:", e)
        return None


def fallback_logic(log: str) -> dict:
    log_lower = log.lower()
    if "timeout" in log_lower:
        return {"mode": "fallback", "error": "Timeout Error",
                "severity": "High", "summary": "System timeout detected"}
    if "connection" in log_lower or "refused" in log_lower:
        return {"mode": "fallback", "error": "Connection Failure",
                "severity": "High", "summary": "Connection issue detected"}
    if "out of memory" in log_lower or "oom" in log_lower:
        return {"mode": "fallback", "error": "Out of Memory",
                "severity": "Critical", "summary": "Memory exhaustion detected"}
    if "disk" in log_lower and ("full" in log_lower or "space" in log_lower):
        return {"mode": "fallback", "error": "Disk Full",
                "severity": "High", "summary": "Disk space exhaustion"}
    if "cpu" in log_lower and ("high" in log_lower or "spike" in log_lower):
        return {"mode": "fallback", "error": "High CPU",
                "severity": "Medium", "summary": "CPU spike detected"}
    if "failed" in log_lower or "error" in log_lower:
        return {"mode": "fallback", "error": "Operation Failed",
                "severity": "Medium", "summary": "Operation failed"}
    return {"mode": "fallback", "error": "Unknown",
            "severity": "Low", "summary": log[:120]}


def analyze_log(log: str) -> dict:
    """Analyse a log string. Reads USE_AI env var on every call so toggling works."""
    use_ai = os.getenv("USE_AI", "false").lower() == "true"

    if use_ai:
        client = _get_client()
        if client:
            try:
                from google.genai import types
                prompt = f"""Return ONLY valid JSON, no markdown, no explanation:
{{
  "error": "...",
  "severity": "Low|Medium|High|Critical",
  "summary": "...",
  "suggested_action": "..."
}}
Log: {log}
"""
                response = client.models.generate_content(
                    model="models/gemini-2.5-flash",
                    
                    contents=prompt,
                )
                text = re.sub(r"```json|```", "", response.text).strip()
                data = json.loads(text)
                data["mode"] = "AI"
                return data
            except Exception as e:
                print("AI failed → fallback:", e)
        else:
            print("Gemini unavailable (no API key or init failed) → fallback")

    return fallback_logic(log)
