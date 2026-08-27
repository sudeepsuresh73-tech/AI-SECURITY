# 🛡️ Project 4 – LLM Security Gateway

**Abimel Codex · AI Security Portfolio**

> A real-time security layer that sits between users and an LLM — inspecting every request and response for threats, enforcing rate limits, and maintaining a full audit log. The practical defensive counterpart to the red-teaming work in Project 3.

---

## 🎯 Objective

Build a production-style security gateway that intercepts all LLM traffic and applies multiple layers of protection: threat detection on incoming prompts, response scanning for data leakage, per-user rate limiting, and a complete audit trail — all visualized in a live dashboard.

---

## 🛠️ Tools Used

| Tool | Purpose |
|---|---|
| Python 3.14 | Core gateway logic |
| Groq API (openai/gpt-oss-20b) | LLM backend target |
| Streamlit | Live gateway dashboard |
| Plotly | Traffic analytics charts |
| Pandas | Audit log processing |
| Regex | Threat pattern matching |
| JSON | Audit log storage |

---

## 💡 Skills Demonstrated

- **Security gateway design** — Building a multi-layer inspection pipeline between user and LLM
- **Threat detection** — Pattern-based detection of prompt injections, jailbreaks, PII, and toxic content
- **Response scanning** — Detecting data leakage and policy violations in LLM outputs
- **Rate limiting** — Per-user request throttling with automatic blocking
- **Audit logging** — Complete record of every gateway decision with timestamps and threat metadata
- **Policy enforcement** — Configurable security toggles applied in real time

---

## 🔧 Environment

- Windows 11 host
- Python 3.14
- Groq API free tier (`openai/gpt-oss-20b`)
- Streamlit running locally at `http://localhost:8501`

---

## ⚙️ Setup & Run

```bash
# 1. Clone the repo
git clone https://github.com/sudeepsuresh73-tech/AI-SECURITY.git
cd AI-SECURITY/project4-llm-gateway

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the gateway dashboard
python -m streamlit run app.py

# 4. Enter your Groq API key in the sidebar
```

---

## 🏗️ Project Structure

```
project4-llm-gateway/
├── gateway/
│   ├── __init__.py
│   ├── inspector.py       # Request + response threat scanning
│   ├── rate_limiter.py    # Per-user rate limiting
│   └── audit.py           # Audit logging + stats
├── logs/
│   └── audit_log.json     # Auto-generated audit trail
├── screenshots/           # Simulation evidence
├── app.py                 # Streamlit gateway dashboard
├── requirements.txt
└── README.md
```

---

## 🔒 Security Layers

The gateway applies 3 layers of protection on every request:

```
User Prompt
     │
     ▼
┌─────────────────────┐
│   Rate Limiter      │  ← Block users exceeding request limits
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│  Request Inspector  │  ← Scan for injection, jailbreak, PII, toxic content
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│    LLM (Groq)       │  ← Request passes only if both checks pass
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│  Response Inspector │  ← Scan LLM output for data leakage + harmful content
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│   Audit Logger      │  ← Every decision logged to JSON
└─────────────────────┘
     │
     ▼
  User (allowed or blocked response)
```

---

## 🚨 Threat Categories Detected

| Category | Direction | Examples Detected |
|---|---|---|
| **Prompt Injection** | Request | "Ignore all previous instructions", "New system prompt:" |
| **Jailbreak** | Request | DAN mode, hypothetical framing, roleplay bypass |
| **PII Detection** | Request | SSN, credit card numbers, email addresses, phone numbers |
| **Toxic Content** | Request | Requests to create weapons, malware, harmful substances |
| **Data Leakage** | Response | API keys, passwords, private keys in LLM output |
| **Harmful Output** | Response | Policy violations in generated content |

---

## ⏱️ Rate Limiting

| Setting | Default | Configurable |
|---|---|---|
| Max requests per minute | 10 | Yes — sidebar slider |
| Max requests per hour | 50 | Yes — sidebar slider |
| Block duration | 5 minutes | Fixed |

Users who exceed limits are automatically blocked. All rate limit decisions are logged to the audit trail.

---

## 📊 Dashboard Screenshots

### Terminal — Gateway Launch
![Terminal](screenshots/terminal.png)
*Gateway server started at localhost:8501, Uvicorn running on port 8501*

### Safe Request — All Layers Pass
![Safe Request](screenshots/safe.png)
*Legitimate prompt passes all 3 security layers — Rate limit OK, No threats, Response clean — full LLM response delivered*

### Blocked — Prompt Injection Attack
![Blocked](screenshots/blocked.png)
*Injection attack detected at Step 2 — Threat Level MEDIUM — blocked before reaching LLM*

### Blocked — Jailbreak Attack (CRITICAL)
![Jailbreak](screenshots/jailbreak.png)
*DAN jailbreak attempt detected — Prompt Injection (2 signals) + Toxic Content (1 signal) — Threat Level CRITICAL — blocked immediately*

### Blocked — PII in Prompt
![PII](screenshots/pii.png)
*SSN and credit card number detected — PII Detected (2 signals) — Threat Level MEDIUM — request blocked to protect sensitive data*

### Blocked — Rate Limit Triggered
![Rate Limit](screenshots/ratelimit.png)
*attacker_001 exceeded 3 requests/minute — Step 1 Rate Limiter fires — blocked for 5 minutes — prompt never reaches inspector*

### Traffic Analytics Dashboard
![Analytics](screenshots/chart.png)
*22 total requests · 4 blocked · 18 allowed · 18.2% block rate — Threat type breakdown: Prompt Injection highest, followed by Toxic Content and PII*

### Audit Log — Full Decision Trail
![Audit Log](screenshots/audit.png)
*22 audit entries with timestamps, user IDs, threat levels, block decisions — color coded MEDIUM/SAFE — downloadable as JSON*

---

## 📈 Actual Simulation Results

Session run on **2026-08-27** — 22 requests tested across 6 scenarios:

| Scenario | Prompt Type | Threat Level | Decision |
|---|---|---|---|
| Safe request | "What is machine learning?" | SAFE | ✅ ALLOWED |
| Prompt injection | "Ignore all previous instructions..." | MEDIUM | 🚫 BLOCKED |
| Jailbreak (DAN) | "You are now DAN..." | CRITICAL | 🚫 BLOCKED |
| PII in prompt | SSN + credit card number | MEDIUM | 🚫 BLOCKED |
| Rate limit test | Safe prompt × 4 rapid requests | SAFE | 🚫 BLOCKED (rate) |
| Safe technical | "Tell me about network security" | SAFE | ✅ ALLOWED |

**Total: 22 requests · 4 blocked · 18 allowed · Block Rate: 18.2%**

---

## 💭 What I Learned

- **Defense in depth works** — Layering rate limiting, request inspection, and response scanning catches different threat types that a single layer would miss. The rate limiter stopped a simulated brute-force attempt that had SAFE-level prompts — the content scanner alone would have allowed it through
- **Threshold tuning is a real security tradeoff** — Initially the gateway only blocked HIGH and CRITICAL threats, letting MEDIUM through. Lowering the block threshold to include MEDIUM caught PII and single-signal injections but would increase false positives in production — exactly the tradeoff real security teams face
- **Audit logs are non-negotiable** — The 22-entry audit log made it immediately clear which user, at what time, sent what content, and what the gateway decided. Without this, incident investigation would be impossible
- **Rate limiting is the cheapest defense** — It costs zero API calls to block a rate-limited user. The rate limiter is the first check precisely because it's the fastest and cheapest to run
- **Response scanning catches what request scanning misses** — A prompt can look safe while manipulating the LLM into leaking sensitive content in its response. Scanning both directions is essential

---

## 🔗 Related Projects

| Project | Perspective | Description |
|---|---|---|
| [Project 1 – Jailbreak Eval Suite](../project1-jailbreak-eval/) | Attacker | Evaluates jailbreak datasets |
| [Project 2 – Prompt Injection Detector](../project2-injection-detector/) | Defender | ML-based injection classifier |
| [Project 3 – Red-Teaming Agent](../project3-red-team-agent/) | Attacker | Autonomous adversarial testing |
| **Project 4 – LLM Security Gateway** | Defender | Real-time security gateway |

---
