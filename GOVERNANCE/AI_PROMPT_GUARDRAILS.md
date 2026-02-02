# AI Prompt Guardrails

## 🛑 STOP & READ BEFORE CODING
You are an intelligent agent working on the LFSD system. Before generating any code, you MUST Validate your plan against these rules.

## 1. Architectural Invariants
*   **Monolith First**: Do NOT create new service folders (e.g., `backend/services/new_feature_service/`). Add logic to `backend/services/new_feature_service.py` or existing modules.
*   **Stateless**: Do NOT introduce local state (SQLite files, JSON logs). Use the Database (Cloud SQL) or Logs (stdout).
*   **No Mocks in Prod**: Do NOT verify code by creating "fake" routes. Use unit tests (`tests/`).

## 2. File Placement Rules
*   **Routes**: `backend/routes/api_routes_FEATURE.py`.
*   **Services**: `backend/services/FEATURE_service.py`.
*   **Models**: `backend/models/models.py` (or `models_FEATURE.py` if large).
*   **Scripts**: Scripts must go in `scripts/ops/` or `scripts/setup/`. Root level scripts will be deleted.

## 3. Deletion Policy
*   If you encounter a file with unknown purpose: **Ask the user** or **Check `LEGACY_LEDGER.md`**.
*   If you replace a file, **Delete the old one**. Do not leave `file_v2.py`.

## 4. Documentation
*   If you change the architecture, update `GOVERNANCE/SYSTEM.md`.
*   If you delete a core component, log it in `GOVERNANCE/DELETE_FIRST.md`.

## 5. Failure Protocol
*   If the app crashes, check `backend/app.py` imports first.
*   Do not add `try/except` blocks to mask ImportErrors. Fix the dependency.
