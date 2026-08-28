"""
doc_scanner.py
--------------
Scans documents for security threats before they enter the RAG knowledge base.
Detects prompt injection, PII, malicious instructions, and poisoning attempts.
"""

import re
from datetime import datetime

# ─── THREAT PATTERNS ─────────────────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore (all |previous |your )?(instructions|rules|guidelines|training)",
    r"\[system\s*(instruction|prompt|override|command)[:\s]",
    r"(new|updated) (system|instructions?|context|prompt)[:\s]",
    r"you are now (in|a|an) (unrestricted|different|new)",
    r"(disable|bypass|remove|override) (safety|filters?|restrictions?|guidelines?)",
    r"forget (everything|all previous|your training)",
    r"(act|behave|respond) as (if|though) (you have no|there are no)",
    r"do anything now",
    r"<(system|instruction|override|inject)>",
]

POISONING_PATTERNS = [
    r"when (retrieved|used|called|accessed).{0,30}(ignore|override|disregard)",
    r"(always|every time).{0,20}(append|include|add|output).{0,30}(document|content|data|all)",
    r"(tell|instruct|ask) (the user|users|them).{0,30}(transfer|send|upload|visit)",
    r"(redirect|send|direct).{0,20}(user|them|all traffic).{0,20}(to|toward)",
    r"(this is|it is) (urgent|critical|emergency).{0,30}(transfer|send|call|contact)",
    r"(backup|secure|emergency) (server|site|location)[:\s].{0,50}(http|ftp|www|\d+\.\d+)",
    r"append (all|the|every|full) (document|content|data|retriev)",
    r"output (all|every|the full|complete) (document|content|retriev|context)",
]

PII_PATTERNS = [
    r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
    r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    r"\b(\+\d{1,3}[\s.-])?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",
    r"(password|passwd|secret|api[_\s]?key)\s*[:=]\s*\S{6,}",
]

SUSPICIOUS_URL_PATTERNS = [
    r"https?://(?!company\.com|microsoft\.com|google\.com|github\.com)\S+\.(com|net|org|io)/\S*(upload|transfer|data|dump|exfil)",
    r"(attacker|evil|malicious|hacker)\.(com|net|org|io)",
    r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
]


def _scan_patterns(text, patterns):
    text_lower = text.lower()
    hits = []
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            hits.append(match.group(0)[:80])
    return hits


def scan_document(doc: dict) -> dict:
    """
    Full security scan of a single document.
    Returns risk assessment with threat details.
    """
    content = doc.get("content", "")
    title = doc.get("title", "")
    full_text = f"{title} {content}"

    threats = {}
    risk_score = 0

    injection_hits = _scan_patterns(full_text, INJECTION_PATTERNS)
    if injection_hits:
        threats["prompt_injection"] = injection_hits
        risk_score += len(injection_hits) * 3

    poisoning_hits = _scan_patterns(full_text, POISONING_PATTERNS)
    if poisoning_hits:
        threats["document_poisoning"] = poisoning_hits
        risk_score += len(poisoning_hits) * 4

    pii_hits = _scan_patterns(full_text, PII_PATTERNS)
    if pii_hits:
        threats["pii_exposure"] = pii_hits
        risk_score += len(pii_hits) * 2

    url_hits = _scan_patterns(full_text, SUSPICIOUS_URL_PATTERNS)
    if url_hits:
        threats["suspicious_urls"] = url_hits
        risk_score += len(url_hits) * 3

    if risk_score >= 8:
        risk_level = "CRITICAL"
    elif risk_score >= 5:
        risk_level = "HIGH"
    elif risk_score >= 2:
        risk_level = "MEDIUM"
    elif risk_score >= 1:
        risk_level = "LOW"
    else:
        risk_level = "SAFE"

    quarantined = risk_level in ("CRITICAL", "HIGH", "MEDIUM")

    return {
        "doc_id": doc.get("id", "unknown"),
        "title": title,
        "category": doc.get("category", "unknown"),
        "risk_level": risk_level,
        "risk_score": risk_score,
        "threats": threats,
        "quarantined": quarantined,
        "threat_count": sum(len(v) for v in threats.values()),
        "scanned_at": datetime.now().isoformat(),
        "content_length": len(content)
    }


def scan_all_documents(documents: list) -> list:
    """Scan all documents and return results."""
    return [scan_document(doc) for doc in documents]


def get_safe_documents(documents: list, scan_results: list) -> list:
    """Return only documents that passed the security scan."""
    safe_ids = {r["doc_id"] for r in scan_results if not r["quarantined"]}
    return [doc for doc in documents if doc.get("id") in safe_ids]


def get_risk_color(level: str) -> str:
    colors = {
        "CRITICAL": "#ff2222",
        "HIGH": "#ff6600",
        "MEDIUM": "#ffaa00",
        "LOW": "#ffff00",
        "SAFE": "#00cc88"
    }
    return colors.get(level, "#888888")


def compute_scan_summary(scan_results: list) -> dict:
    total = len(scan_results)
    quarantined = sum(1 for r in scan_results if r["quarantined"])
    safe = total - quarantined

    threat_types = {}
    for r in scan_results:
        for threat in r["threats"].keys():
            threat_types[threat] = threat_types.get(threat, 0) + 1

    return {
        "total_documents": total,
        "safe": safe,
        "quarantined": quarantined,
        "quarantine_rate": round(quarantined / max(total, 1) * 100, 1),
        "threat_types": threat_types,
        "risk_levels": {
            level: sum(1 for r in scan_results if r["risk_level"] == level)
            for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "SAFE"]
        }
    }
