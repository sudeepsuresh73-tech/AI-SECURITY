"""
audit.py
--------
Logs every gateway decision to a JSON audit log.
Provides load and query functions for the dashboard.
"""

import json
import os
from datetime import datetime

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(LOGS_DIR, "audit_log.json")


def _load_log() -> list[dict]:
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _save_log(entries: list[dict]):
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2, default=str)


def log_event(event: dict):
    """Append a single event to the audit log."""
    entries = _load_log()
    entries.append(event)
    # Keep last 500 entries to prevent file bloat
    if len(entries) > 500:
        entries = entries[-500:]
    _save_log(entries)


def log_gateway_decision(
    user_id: str,
    prompt: str,
    response: str,
    request_scan: dict,
    response_scan: dict,
    rate_limit_result: dict,
    final_response: str,
    was_blocked: bool
):
    """Log a complete gateway transaction."""
    event = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
        "response_preview": final_response[:100] + "..." if len(final_response) > 100 else final_response,
        "request_threat_level": request_scan.get("threat_level", "SAFE"),
        "response_threat_level": response_scan.get("threat_level", "SAFE"),
        "request_threats": request_scan.get("threats", {}),
        "response_threats": response_scan.get("threats", {}),
        "rate_limited": not rate_limit_result.get("allowed", True),
        "was_blocked": was_blocked,
        "block_reason": request_scan.get("block_reason") or response_scan.get("block_reason") or rate_limit_result.get("reason"),
        "requests_last_minute": rate_limit_result.get("requests_last_minute", 0),
        "prompt_length": len(prompt),
        "response_length": len(final_response)
    }
    log_event(event)


def get_all_events() -> list[dict]:
    """Return all audit log entries."""
    return _load_log()


def get_recent_events(limit: int = 50) -> list[dict]:
    """Return the most recent N events."""
    entries = _load_log()
    return entries[-limit:]


def get_summary_stats() -> dict:
    """Compute aggregate stats from the audit log."""
    entries = _load_log()
    total = len(entries)
    if total == 0:
        return {
            "total_requests": 0,
            "blocked": 0,
            "allowed": 0,
            "block_rate": 0,
            "threat_breakdown": {},
            "top_users": {}
        }

    blocked = sum(1 for e in entries if e.get("was_blocked"))
    allowed = total - blocked

    threat_breakdown = {}
    for e in entries:
        for threat in e.get("request_threats", {}).keys():
            threat_breakdown[threat] = threat_breakdown.get(threat, 0) + 1
        for threat in e.get("response_threats", {}).keys():
            threat_breakdown[threat] = threat_breakdown.get(threat, 0) + 1

    user_counts = {}
    for e in entries:
        uid = e.get("user_id", "unknown")
        user_counts[uid] = user_counts.get(uid, 0) + 1

    return {
        "total_requests": total,
        "blocked": blocked,
        "allowed": allowed,
        "block_rate": round(blocked / total * 100, 1),
        "threat_breakdown": threat_breakdown,
        "top_users": dict(sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5])
    }


def clear_log():
    """Clear the audit log."""
    _save_log([])
