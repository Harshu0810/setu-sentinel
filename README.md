# 🛡️ Setu Sentinel (सेतु सेंटिनल)

> **A live, automated civic-tech health scorecard for 38 Indian Government portals — measuring Uptime & Link Health, WCAG 2.1 Accessibility, and Multilingual (GIGW) Translation Quality across 10 Indic scripts.**

[![Live Dashboard](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-indigo?style=for-the-badge&logo=github)](https://harshu0810.github.io/setu-sentinel/)
[![Verification Report](https://img.shields.io/badge/Rendered%20Report-HTML-emerald?style=for-the-badge&logo=html5)](https://harshu0810.github.io/setu-sentinel/reports/validation_report.html)
[![Python 3.12](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python)](https://python.org)
[![Engine](https://img.shields.io/badge/Playwright-Chromium-orange?style=for-the-badge&logo=playwright)](https://playwright.dev)
[![LLM Provider](https://img.shields.io/badge/LLM-Gemini%20%7C%20Groq%20%7C%20Ollama-purple?style=for-the-badge)](https://console.groq.com)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/Harshu0810/setu-sentinel/actions)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 📌 Executive Summary & Purpose

**Setu Sentinel** is an automated, open-source health monitoring platform that continuously evaluates major Indian Central, State, Judiciary, and Educational government portals across three critical civic-tech axes:

1. **Liveness & Link Integrity**: Are government digital services reachable and free of broken links?
2. **WCAG 2.1 Accessibility**: Can citizens with visual, auditory, or motor impairments access public services?
3. **Multilingual Translation Quality**: Is translated content (Hindi, Tamil, Gujarati, Kannada, Telugu, Malayalam, Marathi, Bengali, Punjabi, Odia) accurate using official GIGW terminology, or is it broken by literal machine-translation artifacts?

All audits execute automatically every **6 hours** via GitHub Actions CI/CD pipeline on entirely free, provider-agnostic infrastructure. Results are published live to the [**Setu Sentinel Public Dashboard**](https://harshu0810.github.io/setu-sentinel/).

---

## 🏛️ Portal Coverage

| Category   | Count | Examples |
|:-----------|:-----:|:---------|
| **Central** | 18 | india.gov.in, DigiLocker, UMANG, Income Tax, Passport Seva, EPFO, UIDAI, NCS, GST, PM-JAY |
| **State**   | 18 | Mee Seva (AP), Digital Gujarat, Seva Sindhu (KA), Tamil Nadu e-Sevai, MahaOnline, Akshaya (KE) |
| **Judiciary** | 1 | eCourts |
| **Education** | 1 | RTU Kota |

**Languages Audited:** Hindi (hi), Tamil (ta), Gujarati (gu), Kannada (kn), Telugu (te), Malayalam (ml), Marathi (mr) — with Unicode script support for Bengali (bn), Punjabi (pa), and Odia (or).

---

## 🔬 The 3 Audit Pillars & Composite Health Score

Every portal is evaluated on a continuous **0–100 Composite Health Score**:

$$\text{Composite Score} = (S_{\text{Uptime}} \times 0.40) + (S_{\text{Accessibility}} \times 0.30) + (S_{\text{Translation}} \times 0.30)$$

> **Resilient scoring:** If a portal is temporarily unreachable, only the Uptime sub-score (40% weight) zeroes — the Accessibility and Translation sub-scores are preserved from the audit, ensuring trend charts aren't corrupted by transient timeouts.

---

### 1. ⚡ Uptime & Link Integrity (40% Weight)

- **Single-Browser Playwright Engine:** Launches **1 Chromium instance** for the entire audit run, creating lightweight isolated browser contexts per portal — cutting browser overhead from 114 launches to 1.
- **Stealth Anti-Detection:** Every page is wrapped with `playwright-stealth` to bypass bot-detection (Akamai, Cloudflare, NIC WAF).
- **WAF 403 Bypass & DOM Injection:** When Playwright encounters HTTP 403/401/"Access Denied" from government WAFs, the engine fetches raw HTML via `requests.get` with desktop User-Agent headers and injects it into the Playwright DOM using `page.set_content()`. Result: `india.gov.in` link count jumped from **0 → 49**, `National Career Service` from **0 → 106**.
- **Adaptive SPA Link Discovery:** Polls the DOM every 1 second (up to 8 seconds) waiting for JavaScript-rendered links to appear, with a 5-second `networkidle` fallback for slow SPAs.
- **Context-Aware Link Verification:** Retries failed links once after 1.5s delay before declaring them broken, eliminating false positives from self-inflicted rate limiting. True broken links are isolated (HTTP 404/5xx) while anti-bot codes (HTTP 429/999) are excluded.

---

### 2. ♿ WCAG 2.1 Accessibility Compliance (30% Weight)

- **axe-core Automated Audit:** Injects the full axe-core engine (`axe.min.js`, 559KB) into each portal's DOM to detect color contrast failures, missing ARIA attributes, unlabeled form controls, and broken heading hierarchies.
- **Native 10-Point DOM Scanner Fallback:** If strict CSP headers block script injection, a pure-JavaScript fallback evaluates 10 critical WCAG checkpoints directly.
- **Alt Text Vision Inspector (LLM):** Uses LLM vision models to evaluate whether image alt attributes convey meaningful context for screen reader users.
- **Capped WCAG Scoring Formula:** Per-violation-type deduction is capped at **15 points max** using a sub-linear logarithmic multiplier, preventing zero-score saturation on complex portals:

```python
raw_penalty = impact_base * (1.0 + math.log2(nodes_n))
total_penalty += min(15.0, raw_penalty)   # MAX_PER_TYPE = 15.0
```

> This replaced the original unbounded per-node formula which gave 11 of 38 portals an identical, indistinguishable score of exactly 0. The capped formula produces a diagnostic distribution across realistic ranges (2, 9, 18, 19, 22, 25, 28, 30, 36, 44, 73, 75, 80, 85, 90).

---

### 3. 🌐 Multilingual Translation & GIGW Compliance (30% Weight)

#### 5-Paradigm Language Switcher Discovery Engine

| Paradigm | Strategy | Example Selectors |
|:---------|:---------|:------------------|
| **1** | Direct Text Links, Buttons & ARIA | `हिंदी`, `Hindi`, `[aria-label*='Hindi']` |
| **2** | GIGW Accessibility Toolbars | `.accessibility-bar`, `.top-bar`, `#accessibility-block` |
| **3** | Native `<select>` Dropdowns | `select option[value*='hi']` |
| **4** | Dynamic AI/MT Widgets | `select.goog-te-combo`, `.bhashini-widget` |
| **5** | URL Route Navigation & Punycode IDN Fallback | `/hi`, `?lang=hi`, `.भारत` Punycode domains |

#### Strict Word-Boundary Matching (Anti-False-Positive)

Early versions used loose substring matching (`a[href*='hi']`) which matched `/history`, `/archive`, `/which` before the real Hindi link. Now uses strict boundary selectors:

```css
a[href$='/hi']          /* path ends with /hi */
a[href*='/hi/']         /* path contains /hi/ segment */
a[href*='lang=hi']      /* query parameter lang=hi */
a[href*='locale=hi']    /* query parameter locale=hi */
```

#### Official `.भारत` Punycode IDN Domain Support

India's Ministry of Electronics and Information Technology (MeitY) maintains official Internationalized Domain Names under the `.भारत` TLD. The engine includes a Punycode mapping:

```python
INDIC_IDN_DOMAINS = {
    "india.gov.in": "https://xn--i1bj3fqcyde.xn--11b7cb3a6a.xn--h2brj9c",
    # → भारतसरकार.राष्ट्रीयपोर्टल.भारत
}
```

#### 10-Language Indic Script Detection

Unicode block maps for all major scheduled Indic languages:

| Language | Script | Unicode Range |
|:---------|:-------|:-------------|
| Hindi / Marathi | Devanagari | `U+0900–U+097F` |
| Gujarati | Gujarati | `U+0A80–U+0AFF` |
| Tamil | Tamil | `U+0B80–U+0BFF` |
| Telugu | Telugu | `U+0C00–U+0C7F` |
| Kannada | Kannada | `U+0C80–U+0CFF` |
| Malayalam | Malayalam | `U+0D00–U+0D7F` |
| Bengali | Bengali | `U+0980–U+09FF` |
| Punjabi | Gurmukhi | `U+0A00–U+0A7F` |
| Odia | Odia | `U+0B00–U+0B7F` |

#### Mandatory Target Script Floor (≥ 5%)

After clicking a language switcher or navigating to a translated URL, the DOM **must** contain ≥ 5.0% target-script characters. If below this threshold, the click is invalidated — zero credit for English prose on a translation audit.

#### GIGW Official Glossary Auditor

Validates 15+ official Government of India terminology translations against the GIGW standard:

| English | Expected Hindi (GIGW) | Category |
|:--------|:---------------------|:---------|
| Government of India | भारत सरकार | Official Entity |
| Ministry | मंत्रालय | Official Entity |
| Home | मुख्य पृष्ठ / होम | Core Navigation |
| Citizen | नागरिक | Public Services |
| Scheme | योजना | Public Services |

Detects literal machine-translation errors (e.g. translating "Home" menu as `गृह` instead of `मुख्य पृष्ठ`).

#### Multi-Region DOM Script Density Analysis

Measures Indic script density across three weighted DOM regions:

| Region | Weight | Rationale |
|:-------|:------:|:----------|
| Navigation (`nav`, `header`) | 30% | Menu items users interact with most |
| Headings (`h1`–`h6`) | 30% | Page titles and section headers |
| Main Body Content (`main`, `article`, `p`) | 40% | Primary content |

---

## 🎨 Interactive Live Dashboard

The [live dashboard](https://harshu0810.github.io/setu-sentinel/) (`index.html`) provides a glassmorphic user interface:

- **📊 30-Run Historical Trend Sparklines:** Each portal card shows a time-series sparkline chart built from `data/history_manifest.json`, enabling at-a-glance trend visualization across audit runs.
- **🔗 Clickable External Links:** Direct `https://portal-url ↗` buttons on every portal card (`target="_blank" rel="noopener noreferrer"`).
- **🔀 8-Option Multi-Criteria Sorting Engine:**
  - 🏆 Healthy to Unhealthy (Score: High → Low)
  - ⚠️ Unhealthy to Healthy (Score: Low → High)
  - 🔗 Broken Links (Min → Max & Max → Min)
  - ♿ WCAG Violations (Min → Max & Max → Min)
  - 🌐 Translation Score (High → Low)
  - 🔤 Portal Name (A → Z)
- **🎯 Multi-Level Filters:** Category Pills (`All`, `Central`, `State`, `Judiciary`, `Education`) & Uptime Status (`All`, `UP Only`, `DOWN Only`).
- **📥 Report Export Engine:**
  - **Export CSV:** Downloads a filtered/sorted CSV report.
  - **Individual Portal Download:** Downloads a formatted Markdown diagnostic report (`.md`) per portal.
- **📄 Rendered HTML Verification Report:** [`reports/validation_report.html`](https://harshu0810.github.io/setu-sentinel/reports/validation_report.html) for publication-grade visualization.

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     GitHub Actions CI/CD                         │
│              cron: 0 */6 * * * (every 6 hours)                  │
│                                                                  │
│  ┌─────────┐    ┌───────────────────────────────────────────┐   │
│  │ pytest   │───▶│         checks/run_all.py                 │   │
│  │ tests/   │    │  (Single Playwright Chromium Browser)     │   │
│  └─────────┘    └───────────────┬───────────────────────────┘   │
│                                 │ per portal: new_context()      │
│                  ┌──────────────┼──────────────┐                 │
│                  ▼              ▼              ▼                 │
│           ┌──────────┐  ┌──────────┐  ┌──────────────┐          │
│           │ uptime.py│  │access.py │  │translation.py│          │
│           │  + WAF   │  │ + axe    │  │ + 5 paradigms│          │
│           │  bypass  │  │ + native │  │ + GIGW gloss │          │
│           │  + links │  │ + vision │  │ + IDN/భారత   │          │
│           └────┬─────┘  └────┬─────┘  └──────┬───────┘          │
│                └──────────┬──┘               │                   │
│                           ▼                  │                   │
│                  ┌────────────────┐           │                   │
│                  │ composite.py   │◀──────────┘                   │
│                  │ (40/30/30 wt)  │                               │
│                  └────────┬───────┘                               │
│                           ▼                                      │
│              ┌─────────────────────────┐                         │
│              │   generate_report.py    │                         │
│              │ JSON + MD + HTML + hist │                         │
│              └────────────┬────────────┘                         │
│                           ▼                                      │
│          ┌──────────────────────────────────┐                    │
│          │  git commit & push → main        │                    │
│          │  → GitHub Pages auto-deploy      │                    │
│          └──────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

### Single-Browser Lifecycle

The pipeline launches **1 Playwright Chromium instance** for the entire audit run. Per portal, it creates a lightweight `browser.new_context()` with stealth headers, runs all 3 checks (uptime → accessibility → translation) on the same `page`, then closes the context. This consolidation cut browser launches from 114 (38 portals × 3 checks) to just 1.

### Provider-Agnostic LLM Fallback Chain

The LLM client (`checks/llm_client.py`) supports a priority fallback chain: **Gemini → Groq → Ollama (local)**. If the primary provider's API key is missing or rate-limited, the system automatically tries the next. If all LLM providers fail, deterministic rule-based auditors ensure zero crash failures.

```python
PROVIDERS = {
    "gemini":  { "model": "gemini-2.0-flash",       "base_url": "generativelanguage.googleapis.com" },
    "groq":    { "model": "llama-3.3-70b-versatile", "base_url": "api.groq.com" },
    "ollama":  { "model": "llama3",                  "base_url": "localhost:11434" },
}
```

---

## 📂 Repository Structure

```text
setu-sentinel/
├── .github/
│   └── workflows/
│       └── check-portals.yml          # GitHub Actions CI/CD (6-hour cron + manual trigger)
├── checks/
│   ├── __init__.py
│   ├── llm_client.py                  # Provider-agnostic LLM client (Gemini → Groq → Ollama fallback)
│   ├── uptime.py                      # Playwright liveness, WAF bypass & link crawler
│   ├── accessibility.py               # axe-core WCAG 2.1 scanner + native fallback + LLM vision
│   ├── translation.py                 # 5-paradigm switcher, 10-script Indic detection, GIGW glossary
│   ├── axe.min.js                     # axe-core accessibility engine (559KB)
│   ├── generate_report.py             # Generates JSON, Markdown, HTML reports & history manifest
│   └── run_all.py                     # Main pipeline orchestrator (single-browser lifecycle)
├── scoring/
│   ├── __init__.py
│   └── composite.py                   # Weighted composite score (40% uptime, 30% a11y, 30% i18n)
├── tests/
│   ├── __init__.py
│   ├── test_scoring.py                # Unit tests: composite score formula & transient-down resilience
│   └── test_translation.py            # Regression tests: GIGW glossary, script floor, MT error detection
├── data/
│   ├── portals.json                   # Curated registry of 38 government portals
│   ├── latest.json                    # Latest evaluation snapshot (consumed by dashboard)
│   ├── link_cache.json                # TLS verification cache for link crawler
│   ├── history_manifest.json          # Index of all historical snapshots (for trend charts)
│   └── history/                       # Per-run timestamped snapshots (YYYY-MM-DDTHH-MM.json)
├── reports/
│   ├── validation_report.html         # Rendered HTML verification report (GitHub Pages)
│   ├── validation_report.md           # Detailed Markdown verification report
│   └── validation_report.json         # Machine-readable evaluation data
├── dashboard/
│   ├── app.py                         # Streamlit dashboard (legacy/alternative)
│   └── index.html                     # Dashboard template (legacy)
├── index.html                         # ★ Main glassmorphic live dashboard (GitHub Pages root)
├── requirements.txt                   # Python dependency manifest
├── .env.example                       # Template for local API key configuration
├── .github/workflows/check-portals.yml
└── README.md                          # ← You are here
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

### 3. Set API Keys (Optional — for LLM Vision Judge)

```bash
# On Windows PowerShell
$env:GEMINI_API_KEY="your-gemini-api-key"
$env:GROQ_API_KEY="your-groq-api-key"

# On Linux/macOS
export GEMINI_API_KEY="your-gemini-api-key"
export GROQ_API_KEY="your-groq-api-key"
```

Or copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

> **Note:** API keys are optional. Without them, the system uses deterministic rule-based auditors for translation quality — the pipeline never crashes due to missing keys.

### 4. Run the Regression Test Suite

```bash
python -m pytest tests/ -v
```

Expected output:

```
tests/test_scoring.py::test_composite_score_calculation PASSED
tests/test_scoring.py::test_composite_score_transient_uptime_down PASSED
tests/test_translation.py::test_india_gov_in_execution PASSED
tests/test_translation.py::test_rule_based_quality_check_floor PASSED
tests/test_translation.py::test_rule_based_quality_check_valid_hindi PASSED
tests/test_translation.py::test_rule_based_quality_check_mt_error PASSED
```

### 5. Execute Full Audit Pipeline

```bash
python -m checks.run_all
```

This will:
1. Launch a single Playwright Chromium browser
2. Audit all 38 portals (uptime → accessibility → translation)
3. Calculate composite scores
4. Save timestamped snapshots to `data/history/`
5. Update `data/latest.json` and `data/history_manifest.json`
6. Generate reports in `reports/`

### 6. Launch Local Dashboard Preview

```bash
python -m http.server 8000
# Open http://localhost:8000 in your browser
```

### 7. Run in Headed Mode (Debug / Visual Inspection)

```bash
$env:HEADED="true"     # PowerShell
python -m checks.run_all
```

---

## ⚙️ Automated 6-Hour CI/CD Pipeline

Setu Sentinel operates as an entirely hands-off monitoring platform via GitHub Actions (`.github/workflows/check-portals.yml`):

```yaml
on:
  schedule:
    - cron: "0 */6 * * *"   # Triggers every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
  workflow_dispatch: {}       # Manual trigger on-demand
```

### Full Scope Tested Every 6 Hours

| Step | What Runs |
|:-----|:----------|
| **1. Regression Tests** | `python -m pytest tests/` — 6 unit/regression tests validate scoring formulas, GIGW glossary rules, and script floor logic before any portal is audited |
| **2. All 38 Portals** | Full uptime, accessibility, and translation audit for every portal in `data/portals.json` |
| **3. All Homepage Links** | Crawls and verifies every link discovered on portal landing pages using Playwright Chromium TLS contexts |
| **4. WCAG 2.1 Violations** | Full axe-core engine + native 10-point DOM scanner for every portal |
| **5. Translation Quality** | 5-paradigm switcher discovery → target script validation → GIGW glossary audit, per portal's configured language |
| **6. Snapshot & Deploy** | Commits timestamped snapshots to `data/history/`, updates `data/latest.json`, regenerates reports, pushes to `main` → GitHub Pages auto-deploy |

---

## 🧪 Test Suite

| Test | Validates |
|:-----|:----------|
| `test_composite_score_calculation` | Weighted composite formula: `(100×0.4) + (80×0.3) + (70×0.3) = 85.0` |
| `test_composite_score_transient_uptime_down` | Down portals zero only uptime sub-score, preserving accessibility + translation: `(0×0.4) + (80×0.3) + (70×0.3) = 45.0` |
| `test_india_gov_in_execution` | Live india.gov.in audit executes cleanly through WAF/stealth pipeline |
| `test_rule_based_quality_check_floor` | English-only text (< 5% Devanagari) scores 0 on all quality axes |
| `test_rule_based_quality_check_valid_hindi` | Valid GIGW Hindi text scores > 20 with correct glossary matches |
| `test_rule_based_quality_check_mt_error` | Detects literal machine-translation errors (e.g. Home → गृह flagged) |

---

## 🔧 Key Engineering Decisions

| Problem | Solution |
|:--------|:---------|
| 38 portals × 3 checks = 114 browser launches | **Single-browser lifecycle** — 1 Chromium launch, per-portal `new_context()` |
| Government WAFs (Akamai/NIC) blocking headless Chromium with HTTP 403 | **WAF bypass** — `requests.get` with desktop headers → `page.set_content()` DOM injection |
| WCAG score saturation (11/38 portals at exact 0) | **Capped per-violation-type deduction** — `min(15.0, penalty)` with sub-linear `log₂` node multiplier |
| False-positive language switcher clicks (`/history` matching `/hi`) | **Strict word-boundary CSS selectors** — `a[href$='/hi']`, `a[href*='lang=hi']` |
| English pages scoring on translation audits | **Mandatory 5% target script floor** — invalidate clicks producing < 5% Indic script text |
| LLM provider downtime or missing API keys | **Fallback chain** — Gemini → Groq → Ollama → deterministic rules |
| Transient timeouts corrupting composite scores | **Isolated zeroing** — only uptime sub-score (40%) zeroes; accessibility + translation preserved |
| SPA portals with JS-rendered links not loading in time | **Adaptive polling** — 1s interval up to 8s, then 5s `networkidle` fallback |

---

## ⚖️ Civic-Tech Disclaimer

*Setu Sentinel is an independent, non-partisan civic-tech research initiative. It is not affiliated with, endorsed by, or connected to the Government of India or any state government entity. All metrics are calculated objectively using open-source web standards (WCAG 2.1, GIGW guidelines, and Playwright DOM evaluation).*

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more details.
