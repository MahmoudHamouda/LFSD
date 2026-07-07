# Life Financial & Scoring Dashboard (LFSD)

LFSD is a personal financial, health, and productivity dashboard built with FastAPI (backend) and React/TypeScript (frontend). It integrates with external calendar services, travel/hospitality APIs, and LLM (Gemini) intelligence to deliver unified dashboard scoring, insights, and recommendations.

## Project Structure

- `backend/`: Core backend APIs, database models, and service classes.
- `frontend/`: React dashboard application.
- `docs/`: System documentation, setup runbooks, and implementation guides.
- `.github/workflows/`: CI/CD automation pipelines.

## Getting Started

### Local Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   pip install -r backend/requirements-dev.txt
   ```
3. Set up environment variables in a `.env` file based on configuration settings.
4. Run the development server:
   ```bash
   uvicorn app:app --host 127.0.0.1 --port 8000 --reload
   ```

---

## Decision-making architecture

HELM answers with a **policy-first, AI-assisted** engine: it *weighs* choices
rather than describing them, and never fabricates data. A message runs through a
tool-first **Orchestrator** (mobility) and a 7-stage **Intelligence Pipeline**,
with a universal **Decision Engine** that scores every decision on
Wealth / Health / Time and grounds it in the user's memory (finances, recurring
commitments, goals). Local search returns real Google Maps places; ride requests
hand off with pre-filled Uber/Maps deep links (no fabricated bookings).

See **[docs/DECISION_ENGINE.md](docs/DECISION_ENGINE.md)** for the full reference,
and [SYSTEM.md](SYSTEM.md) for the orchestrator. Key configuration:

| Env var | Effect |
|---------|--------|
| `GEMINI_API_KEY` | LLM for classification/synthesis/response (`mock` disables LLM paths). |
| `USE_LEGACY_PIPELINE` | `true` bypasses the intelligence pipeline. |
| `RAI_GOVERNANCE_ENABLED` | `true` (default) enables consent + PII governance. |
| `GOOGLE_MAPS_API_KEY` | Enables real local search + geocoding/distance. |
| `UBER_SERVER_TOKEN` | Enables real Uber price estimates (booking is always a hand-off). |

## Security

Security is integrated into our engineering practices and automated pipelines:

1. **Vulnerability Reporting**: If you discover a vulnerability or suspect a security issue, please read [SECURITY.md](SECURITY.md) for instructions on how to report it responsibly.
2. **Secure Coding**: All contributors must review [SECURITY.md](SECURITY.md) to ensure no secrets or sensitive keys are hardcoded in source control.
3. **Automated Pipeline Audits**:
   - Every push and pull request runs automated security checks via GitHub Actions.
   - **Bandit** checks the codebase for common security issues.
   - **Safety** checks dependencies for known vulnerability disclosures.
