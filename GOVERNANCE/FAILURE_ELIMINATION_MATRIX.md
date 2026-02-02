# Failure Elimination Matrix

| Failure Mode | Root Cause | Structural Fix |
| :--- | :--- | :--- |
| **Microservice Drift** | Agents creating independent folders (`services/xyz/app.py`) for features. | **Guardrail**: Enforce Monolith structure. **Action**: Deleted 6+ stub services. |
| **Ghost Resources** | Deploys to wrong regions (`europe-west1`) accumulating cost/confusion. | **Kill List**: Explicit list of active resources in `GCP_KILL_LIST.md`. |
| **Broken Imports** | Deleting a service but leaving imports in `app.py`. | **Consolidation**: `app.py` rewritten with clean, static imports. No dynamic/try-except loading. |
| **Data Pollution** | Hardcoded logic in `routes/` masking real service failures. | **Stubs**: Explicit Stubs returning empty data instead of fake meaningful data. |
| **Frontend Crashes** | API endpoints 404ing after backend refactor. | **Stubbing**: Routes maintained (`recommendation_routes`) even if service logic is removed, satisfying API contract. |
