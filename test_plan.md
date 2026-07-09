# LFSD Integration & E2E Test Plan

This document outlines the testing strategy, test suites, and instructions for executing local unit/integration tests and production-level UI/UX browser tests.

---

## 1. Local Unit & Integration Tests

These tests verify correct pipeline logic, DB schemas, and service-level components. They execute against a local SQLite instance or mocked DB configurations.

### A. How to Run Unit Tests
Unit tests verify classification confidences, scoring rules, and route parsing.
```bash
python -m pytest tests/unit -v
```

### B. How to Run Integration Tests
Integration tests check database connection setups and API endpoints. To prevent hitting supabase database instances during local runs, execute with the local SQLite fallback environment variable:
```powershell
# On Windows PowerShell:
$env:DATABASE_URL="sqlite:///backend/lfsd.db"; python -m pytest tests/integration -v
```
```bash
# On Linux/macOS Bash:
DATABASE_URL="sqlite:///backend/lfsd.db" python -m pytest tests/integration -v
```

---

## 2. Production Browser-Level UI/UX Tests

These tests use Playwright to automate end-to-end user journeys (Sign in via Auth0, Dashboard check, Profile verification, and AI Chat prompt responses) directly on the live production environment.

### Prerequisites
Install Playwright and Chromium browser:
```bash
pip install playwright
python -m playwright install chromium
```

### Execution
Run the automated persona validation script against `https://app.helmory.com/`:
```bash
python tests/e2e/test_browser_journeys.py
```

### Persona Test Matrix
The script logs in as three different personas and runs target prompt queries to verify domain routing:

| Persona | Test Prompt | Expected AI Validation |
|---|---|---|
| **Finance** (`finance@helm.com`) | *Can I afford to spend $500 on a watch?* | AI analyzes budget/saving goals and returns formatted advisory response. |
| **Time** (`time@helm.com`) | *How much focus time did I have last week?* | AI pulls calendar/productivity events and returns deep-work highlights. |
| **Health** (`health@helm.com`) | *How much is an Uber to the Dubai Marina?* | AI detects mobility intent, queries aggregator, and returns real-time ride options + pricing (Uber/Careem/RTA). |

---

## 3. Automation Reports & Walkthroughs

After each run, the E2E script stores high-resolution screenshots of the UI state (dashboards, settings, chat bubbles) in the conversation artifact directory for visual audits.
- Verification files: `C:\Users\hmahm\.gemini\antigravity\brain\392bf087-902d-4f6e-94c7-00458be598a0\`
