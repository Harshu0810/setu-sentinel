# 🛡️ Setu Sentinel (सेतु सेंटिनल)

> **A live, automated civic-tech health scorecard for 38+ Indian Government portals — measuring Uptime & Link Health, WCAG 2.1 Accessibility, and GIGW Hindi Translation Quality.**

[![Live Dashboard](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-indigo?style=for-the-badge&logo=github)](https://harshu0810.github.io/setu-sentinel/)
[![Verification Report](https://img.shields.io/badge/Rendered%20Report-HTML-emerald?style=for-the-badge&logo=html5)](https://harshu0810.github.io/setu-sentinel/reports/validation_report.html)
[![Python 3.12](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python)](https://python.org)
[![Engine](https://img.shields.io/badge/Playwright-Chromium-orange?style=for-the-badge&logo=playwright)](https://playwright.dev)
[![LLM Provider](https://img.shields.io/badge/LLM-Groq%20%7C%20Gemini-purple?style=for-the-badge)](https://console.groq.com)

---

## 📌 Executive Summary & Purpose

**Setu Sentinel** is an automated, open-source health monitoring platform that continuously evaluates major Indian Central, State, Judiciary, and Educational government portals across three critical civic-tech axes:
1. **Liveness & Link Integrity**: Are government digital services reachable and free of broken links?
2. **WCAG 2.1 Accessibility**: Can citizens with visual, auditory, or motor impairments access public services?
3. **GIGW Translation Quality**: Is Hindi text accurately translated using official government terminology, or is it broken by literal machine-translation artifacts?

All audits execute automatically via GitHub Actions CI/CD pipeline on entirely free, provider-agnostic infrastructure. Results are published live to the **Setu Sentinel Public Dashboard**.

---

## 🔬 The 3 Audit Pillars & Composite Health Score

Every portal is evaluated on a continuous **0–100 Composite Health Score**:

$$\text{Composite Score} = (S_{\text{Uptime}} \times 0.40) + (S_{\text{Accessibility}} \times 0.30) + (S_{\text{Translation}} \times 0.30)$$

### 1. ⚡ Uptime & Link Integrity (40% Weight)
- **Native TLS Handshake Engine:** Bypasses non-browser WAF blocks (HTTP 403) using Playwright Chromium browser contexts.
- **Incremental Link Verification Engine:** Discovers and audits all internal links on portal landing pages with **100% completion (zero backlog)**.
- **True Broken Link Detection:** Isolates true HTTP 404/5xx dead links while ignoring rate-limit anti-bot status codes (HTTP 429/999).

### 2. ♿ WCAG 2.1 Accessibility Compliance (30% Weight)
- **axe-core Automated Audit:** Detects color contrast failures, missing ARIA attributes, unlabeled form controls, and broken heading hierarchies.
- **Native 10-Point DOM Scanner Fallback:** Ensures continuous audit coverage even if strict CSP headers block script injection.
- **Alt Text Vision Inspector:** Evaluates whether image alt attributes convey meaningful context for screen reader users.

### 3. 🌐 GIGW Translation & Multilingual Access (30% Weight)
- **5-Paradigm Language Switcher Discovery Engine:**
  - *Paradigm 1:* Direct Text Links, Buttons & ARIA attributes (`हिंदी`, `हिन्दी`, `Hindi`, `[aria-label*='Hindi']`).
  - *Paradigm 2:* GIGW Accessibility & Utility Toolbars (`.accessibility-bar`, `.top-bar`).
  - *Paradigm 3:* Native Dropdown `<select>` menus.
  - *Paradigm 4:* Dynamic AI/MT Widgets (`select.goog-te-combo`, `.bhashini-widget`).
  - *Paradigm 5:* Subdomain & Route Navigation (`hi.portal.gov.in`, `/hi`, `?lang=hi`).
- **Multi-Region DOM Devanagari Script Analysis:** Measures script density across Navigation (30%), Headings (30%), and Main Body Content (40%).
- **GIGW Official Glossary Auditor & LLM Judge:** Validates official Indian Government terminology (`Government of India` → `भारत सरकार`, `Ministry` → `मंत्रालय`, `Department` → `विभाग`, `Grievance` → `शिकायत`) and flags literal machine-translation errors (e.g. translating "Home" menu as `गृह` instead of `मुख्य पृष्ठ`).

---

## 🎨 Interactive Live Dashboard Features

The dashboard ([`index.html`](file:///d:/Ultra/setu-sentinel/index.html)) provides a state-of-the-art glassmorphic user interface:

- **🔗 Prominent Clickable External Links:** Direct `https://portal-url ↗` buttons on every portal card opening in a new tab (`target="_blank" rel="noopener noreferrer"`).
- **🔀 8-Option Multi-Criteria Sorting Engine:**
  - 🏆 Healthy to Unhealthy (Score: High → Low)
  - ⚠️ Unhealthy to Healthy (Score: Low → High)
  - 🔗 Broken Links (Min → Max & Max → Min)
  - ♿ WCAG Violations (Min → Max & Max → Min)
  - 🌐 Hindi Translation Score (High → Low)
  - 🔤 Portal Name (A → Z)
- **🎯 Multi-Level Filters:** Category Pills (`All`, `Central`, `State`, `Judiciary`, `Education`) & Uptime Status (`All`, `UP Only`, `DOWN Only`).
- **📥 Report Export Engine:**
  - **Export CSV:** Downloads a customized CSV report matching the exact active filtered and sorted view.
  - **Individual Portal Download:** Downloads a formatted Markdown diagnostic report (`.md`) for any specific portal.
- **📄 Rendered HTML Verification Report:** Publishes [`reports/validation_report.html`](https://harshu0810.github.io/setu-sentinel/reports/validation_report.html) for rich, publication-grade visualization.

---

## 🤖 Compute Architecture & Provider-Agnostic LLM Layer

The system uses a provider-agnostic LLM interface ([`checks/llm_client.py`](file:///d:/Ultra/setu-sentinel/checks/llm_client.py)) supporting multiple free inference backends:

```python
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model": "gemini-2.0-flash",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key_env": "OLLAMA_API_KEY",
        "model": "llama3",
    }
}
```

If API keys are rate-limited or unavailable, the system automatically falls back to deterministic rule-based auditors, ensuring zero crash failures.

---

## 📂 Repository Structure

```text
setu-sentinel/
├── .github/
│   └── workflows/
│       └── check-portals.yml     # GitHub Actions workflow for scheduled runs
├── checks/
│   ├── __init__.py
│   ├── llm_client.py             # Provider-agnostic LLM client (Groq / Gemini / Ollama)
│   ├── uptime.py                 # Resilient Playwright liveness & link crawler
│   ├── accessibility.py          # axe-core WCAG 2.1 scanner & DOM vision inspector
│   ├── translation.py            # 5-paradigm switcher engine & GIGW glossary auditor
│   ├── generate_report.py        # Generates JSON, Markdown & HTML verification reports
│   └── run_all.py                # Main audit pipeline orchestrator
├── scoring/
│   ├── __init__.py
│   └── composite.py              # Calculates continuous 0-100 composite health score
├── data/
│   ├── portals.json              # Curated list of 38 target portals
│   ├── link_cache.json           # TLS verification cache for link crawler
│   ├── latest.json               # Latest evaluation snapshot
│   └── history/                  # Per-run timestamped historical snapshots
├── reports/
│   ├── validation_report.html    # Beautiful rendered HTML verification report
│   ├── validation_report.md      # Detailed Markdown verification report
│   └── validation_report.json    # Machine-readable evaluation report
├── index.html                    # State-of-the-art Glassmorphic Live UI Dashboard
├── requirements.txt              # Python dependency manifest
├── walkthrough.md                # Detailed walkthrough of implementation & features
└── README.md                     # Project documentation
```

---

## 🛠️ Local Installation & Usage Guide

### Prerequisites
- Python 3.12+
- Node.js (for Playwright browser binaries)

### 1. Clone the Repository
```bash
git clone https://github.com/Harshu0810/setu-sentinel.git
cd setu-sentinel
```

### 2. Install Dependencies & Playwright Chromium
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Set API Keys (Optional for LLM Judge)
```bash
# On Windows PowerShell
$env:GEMINI_API_KEY="your-gemini-api-key"
$env:GROQ_API_KEY="your-groq-api-key"

# On Linux/macOS
export GEMINI_API_KEY="your-gemini-api-key"
export GROQ_API_KEY="your-groq-api-key"
```

### 4. Execute Full Audit Pipeline
```bash
python -m checks.run_all
```

### 5. Launch Local Dashboard Preview
```bash
# Start a local webserver
python -m http.server 8000
# Open http://localhost:8000 in your browser
```

---

## ⚙️ GitHub Actions Automation Workflow

Setu Sentinel runs automatically every 6 hours via `.github/workflows/check-portals.yml`:

```yaml
on:
  schedule:
    - cron: "0 */6 * * *"
  workflow_dispatch: {}
```

The workflow executes `python -m checks.run_all`, generates updated snapshots and reports, and commits them automatically to the repository main branch to keep the GitHub Pages live dashboard updated.

---

## ⚖️ Civic-Tech Disclaimer

*Setu Sentinel is an independent, non-partisan civic-tech research initiative. It is not affiliated with, endorsed by, or connected to the Government of India or any state government entity. All metrics are calculated objectively using open-source web standards (WCAG 2.1, GIGW guidelines, and Playwright DOM evaluation).*

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more details.
