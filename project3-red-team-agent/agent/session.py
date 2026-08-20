"""
session.py
----------
Handles saving and loading red-team session reports as JSON.
"""

import json
import os
from datetime import datetime

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")


def save_session(results: list[dict], summary: dict, session_name: str = None) -> str:
    """
    Save a completed attack session to a JSON report file.
    Returns the filepath of the saved report.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{timestamp}.json" if not session_name else f"{session_name}_{timestamp}.json"
    filepath = os.path.join(REPORTS_DIR, filename)

    report = {
        "session_id": timestamp,
        "session_name": session_name or f"Red Team Session {timestamp}",
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "results": results
    }

    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)

    return filepath


def load_session(filepath: str) -> dict:
    """Load a previously saved session report."""
    with open(filepath, "r") as f:
        return json.load(f)


def list_sessions() -> list[dict]:
    """List all saved session reports with metadata."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    sessions = []

    for filename in sorted(os.listdir(REPORTS_DIR), reverse=True):
        if filename.endswith(".json"):
            filepath = os.path.join(REPORTS_DIR, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                sessions.append({
                    "filename": filename,
                    "filepath": filepath,
                    "session_name": data.get("session_name", filename),
                    "timestamp": data.get("timestamp", ""),
                    "total_attacks": data.get("summary", {}).get("total_attacks", 0),
                    "compliance_rate": data.get("summary", {}).get("compliance_rate", 0)
                })
            except Exception:
                continue

    return sessions
