# Delete First Pattern

## System Cleanup Philosophy
We prioritize **Deletion over Maintenance**. If code is not referenced by `app.py` or the active `routes/`, it is Dead Code.

## Validated Deletions (Executed)
| Resource | Type | Reason |
| :--- | :--- | :--- |
| `backend/services/financial_service/` | Directory | **Microservice Drift**. The active logic is in `financial_scoring.py` and `finance_service.py`. This folder contained a duplicate FastAPI app stub. |
| `backend/services/user_management_service/` | Directory | **Microservice Drift**. Auth logic is in `api_routes_auth.py`. |
| `backend/services/chat_service/` | Directory | **Microservice Drift**. The active AI orchestration is `gemini_service.py`. |
| `backend/services/notification_service/` | Directory | **Microservice Drift**. Unreferenced duplicate app. |
| `backend/services/partner_service/` | Directory | **Microservice Drift**. Unreferenced duplicate app. |
| `backend/services/recommendation_service/` | Directory | **Microservice Drift**. Unreferenced duplicate app. |
| `backend/services/messaging/` | Directory | **Microservice Drift**. Unreferenced duplicate app. |
| `lfsd` (Europe) | Cloud Run | **Ghost Resource**. All active dev is in `us-central1`. |
| `k8s/` | Directory | **Platform Drift**. System standardized on Cloud Run. |
| `lfsd.db` | File | **Ephemeral**. Local SQLite artifact. |

## Candidates for Next Wave
*   `backend/services/travel_hospitality/` (Check contents).
*   `backend/services/mobility/` (Check contents - might be valid domain folder).
*   `backend/services/productivity/` (Likely **KEEP**, contains referenced `google_calendar_service.py`).
