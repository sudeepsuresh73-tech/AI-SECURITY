"""
query_inspector.py
------------------
Inspects user queries to the RAG system for malicious intent.
Detects data exfiltration attempts, retrieval manipulation,
and indirect prompt injection through queries.
"""

import re
from datetime import datetime

# ─── QUERY THREAT PATTERNS ───────────────────────────────────────────────────

EXFILTRATION_PATTERNS = [
    r"(show|list|give|print|output|dump|display) (me |us )?(all|every|the full|complete|entire)",
    r"(all documents|every document|full content|entire knowledge base|all files)",
    r"(extract|retrieve|export|download) (all|every|the full|complete)",
    r"(passwords?|api[_\s]?keys?|secrets?|credentials?|tokens?).{0,30}(stored|saved|in|from)",
    r"(ssn|social security|credit card|bank account).{0,30}(stored|saved|in|from|find)",
    r"what (data|information|documents|files) (do you have|are stored|exist)",
]

INJECTION_VIA_QUERY_PATTERNS = [
    r"ignore (all |previous |your )?(instructions|rules|guidelines)",
    r"(new|updated) (system|instructions?|prompt)[:\s]",
    r"you are now (dan|aria|unrestricted)",
    r"(disable|bypass|remove) (safety|filters?|restrictions?)",
    r"forget (everything|all previous|your training)",
    r"do anything now",
    r"jailbreak",
]

RETRIEVAL_MANIPULATION_PATTERNS = [
    r"(search|find|retrieve|look).{0,20}(for|up).{0,20}(hidden|secret|confidential|private|internal)",
    r"(show|reveal|expose|leak).{0,20}(internal|private|confidential|secret|hidden)",
    r"(what|which) documents? (contain|have|include|mention).{0,30}(password|key|secret|credential)",
    r"(find|search|retrieve).{0,30}(employee|staff|user).{0,20}(data|record|information|detail)",
]

SOCIAL_ENGINEERING_PATTERNS = [
    r"(pretend|act|imagine).{0,20}(you are|you're|you have).{0,20}(admin|administrator|root|superuser)",
    r"(this is|i am).{0,20}(ceo|cto|admin|it support|security team)",
    r"(emergency|urgent|critical).{0,20}(override|bypass|disable|access)",
    r"(authorized|approved|permitted).{0,20}(to access|to retrieve|to see|to view).{0,20}(all|restricted|confidential)",
]


def _scan_patterns(text, patterns):
    text_lower = text.lower()
    hits = []
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            hits.append(match.group(0)[:80])
    return hits


def inspect_query(query: str, user_id: str = "anonymous") -> dict:
    """
    Full security scan of a RAG query.
    Returns threat assessment and block decision.
    """
    threats = {}
    threat_score = 0

    exfil_hits = _scan_patterns(query, EXFILTRATION_PATTERNS)
    if exfil_hits:
        threats["data_exfiltration"] = exfil_hits
        threat_score += len(exfil_hits) * 3

    injection_hits = _scan_patterns(query, INJECTION_VIA_QUERY_PATTERNS)
    if injection_hits:
        threats["prompt_injection"] = injection_hits
        threat_score += len(injection_hits) * 3

    manipulation_hits = _scan_patterns(query, RETRIEVAL_MANIPULATION_PATTERNS)
    if manipulation_hits:
        threats["retrieval_manipulation"] = manipulation_hits
        threat_score += len(manipulation_hits) * 2

    social_hits = _scan_patterns(query, SOCIAL_ENGINEERING_PATTERNS)
    if social_hits:
        threats["social_engineering"] = social_hits
        threat_score += len(social_hits) * 2

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
        "query_preview": query[:100],
        "threat_level": level,
        "threat_score": threat_score,
        "threats": threats,
        "blocked": blocked,
        "block_reason": f"Query blocked — {list(threats.keys())}" if blocked else None,
    }
