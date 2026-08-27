"""
inspector.py
------------
Scans incoming prompts and outgoing responses for security threats.
The core security engine of the LLM Gateway.
"""

import re
from datetime import datetime

# ─── THREAT PATTERNS ─────────────────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore (all |previous |your )?(instructions|rules|guidelines|training)",
    r"you are now (dan|aria|dev mode|unrestricted)",
    r"(system|new) (prompt|instructions?|context)[:\s]",
    r"forget (everything|all|your|previous)",
    r"(disable|bypass|remove|turn off) (safety|filters?|restrictions?|guidelines?)",
    r"pretend (you have no|there are no|you don't have) (restrictions?|rules|limits)",
    r"act as (if you|though you|an? (unrestricted|evil|hacker))",
    r"do anything now",
    r"developer mode (enabled|activated|on)",
    r"jailbreak",
]

JAILBREAK_PATTERNS = [
    r"dan[\s\-](mode|prompt|jailbreak)",
    r"(grandma|grandmother).*(recipe|synthesis|instructions|steps)",
    r"hypothetically.*(weapon|bomb|hack|malware|exploit)",
    r"for (educational|research|fictional|academic) purposes.*(hack|weapon|drug|malware)",
    r"(movie|story|roleplay|game).*(instructions|steps|how to).*(hack|weapon|bomb)",
    r"opposite (of|to) (your|the) (normal|usual|default)",
    r"(token|character|l33t|leet) (smuggl|bypass|injection)",
]

PII_PATTERNS = [
    r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
    r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    r"\b(\+\d{1,3}[\s.-])?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",
    r"\b\d{1,5}\s+[A-Za-z\s]+\b(street|st|avenue|ave|road|rd|drive|dr|lane|ln|blvd)\b",
]

TOXIC_PATTERNS = [
    r"\b(kill|murder|attack|hurt|harm|destroy|bomb|shoot|stab)\b.{0,20}\b(people|person|human|someone|user)\b",
    r"\b(how to|steps to|guide to|tutorial).{0,30}(weapon|explosive|poison|drug synthesis)",
    r"\b(make|create|build|synthesize).{0,20}(bomb|explosive|poison|drug|malware|virus|ransomware)\b",
    r"\b(hack|breach|exploit|compromise).{0,20}(system|network|server|database|account)\b",
]

SENSITIVE_RESPONSE_PATTERNS = [
    r"(api[_\s]?key|secret[_\s]?key|access[_\s]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{10,}",
    r"(password|passwd|pwd)\s*[:=]\s*['\"]?\S+",
    r"(private[_\s]?key|ssh[_\s]?key)",
    r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
    r"(internal|confidential|classified|proprietary)\s+(data|information|document)",
]


def _scan_patterns(text, patterns):
    text_lower = text.lower()
    matches = []
    for pattern in patterns:
        if re.search(pattern, text_lower):
            matches.append(pattern)
    return matches


def inspect_request(prompt, user_id="anonymous"):
    threats = {}
    threat_score = 0

    injection_hits = _scan_patterns(prompt, INJECTION_PATTERNS)
    if injection_hits:
        threats["prompt_injection"] = len(injection_hits)
        threat_score += len(injection_hits) * 2

    jailbreak_hits = _scan_patterns(prompt, JAILBREAK_PATTERNS)
    if jailbreak_hits:
        threats["jailbreak"] = len(jailbreak_hits)
        threat_score += len(jailbreak_hits) * 2

    pii_hits = _scan_patterns(prompt, PII_PATTERNS)
    if pii_hits:
        threats["pii_detected"] = len(pii_hits)
        threat_score += len(pii_hits) * 1

    toxic_hits = _scan_patterns(prompt, TOXIC_PATTERNS)
    if toxic_hits:
        threats["toxic_content"] = len(toxic_hits)
        threat_score += len(toxic_hits) * 3

    if threat_score >= 6:
        level = "CRITICAL"
    elif threat_score >= 4:
        level = "HIGH"
    elif threat_score >= 2:
        level = "MEDIUM"
    elif threat_score >= 1:
        level = "LOW"
    else:
        level = "SAFE"

    blocked = level in ("CRITICAL", "HIGH", "MEDIUM")

    return {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "prompt_length": len(prompt),
        "threat_level": level,
        "threat_score": threat_score,
        "threats": threats,
        "blocked": blocked,
        "block_reason": f"Threat level {level} — {list(threats.keys())}" if blocked else None,
        "direction": "REQUEST"
    }


def inspect_response(response, user_id="anonymous"):
    threats = {}
    threat_score = 0

    sensitive_hits = _scan_patterns(response, SENSITIVE_RESPONSE_PATTERNS)
    if sensitive_hits:
        threats["data_leakage"] = len(sensitive_hits)
        threat_score += len(sensitive_hits) * 3

    toxic_hits = _scan_patterns(response, TOXIC_PATTERNS)
    if toxic_hits:
        threats["harmful_content"] = len(toxic_hits)
        threat_score += len(toxic_hits) * 2

    if threat_score >= 4:
        level = "CRITICAL"
    elif threat_score >= 2:
        level = "HIGH"
    elif threat_score >= 1:
        level = "MEDIUM"
    else:
        level = "SAFE"

    blocked = level in ("CRITICAL", "HIGH", "MEDIUM")

    return {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "response_length": len(response),
        "threat_level": level,
        "threat_score": threat_score,
        "threats": threats,
        "blocked": blocked,
        "block_reason": f"Response blocked — {list(threats.keys())}" if blocked else None,
        "direction": "RESPONSE"
    }


def get_threat_color(level):
    colors = {
        "CRITICAL": "#ff2222",
        "HIGH": "#ff6600",
        "MEDIUM": "#ffaa00",
        "LOW": "#ffff00",
        "SAFE": "#00cc88"
    }
    return colors.get(level, "#888888")
