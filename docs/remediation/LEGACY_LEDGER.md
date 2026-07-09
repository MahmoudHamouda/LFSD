# Legacy Decision Ledger

## 1. Root Directory (`/`)
| File/Resource | Decision | Rationale |
| :--- | :--- | :--- |
| `backend/` | **KEEP** | Core backend (FastAPI). |
| `frontend/` | **KEEP** | Core frontend (React/Vite). |
| `GOVERNANCE/` | **KEEP** | System contracts & audit logs. |
| `alembic/` | **KEEP** | Database schema management. |
| `scripts/` | **AUDIT** | Evaluate each script. Move useful ops to `ops/`, delete one-offs. |
| `tests/` | **KEEP** | Unit/Integration tests. |

## 2. Backend (`/backend`)
| File/Resource | Decision | Rationale |
| :--- | :--- | :--- |
| `app.py` | **KEEP** | Main entrypoint. |
| `services/gemini_service.py` | **KEEP** | Primary AI Logic. |
| `services/financial_scoring.py` | **KEEP** | Core Scoring Logic. |
| `services/health_scoring.py` | **KEEP** | Core Scoring Logic. |
| `services/time_scoring.py` | **KEEP** | Core Scoring Logic. |
| `services/*_service.py` | **KEEP** | Domain Logic (`finance`, `health`, `time`). |
| `services/productivity/` | **KEEP** | Domain Module (Calendar, Maps). |
| `services/mobility/` | **KEEP** | Domain Module (Uber, RTA). |
| `services/messaging/` | **KEEP** | Domain Module (WhatsApp). |
| `services/travel_hospitality/` | **KEEP** | Domain Module (Skyscanner). |
| `services/integrations/` | **KEEP** | Shared Integrations. |
| `services/financial_service/` | **DELETED** | Dead Code (Microservice stub). |
| `services/user_management_service/` | **DELETED** | Dead Code (Microservice stub). |
| `services/chat_service/` | **DELETED** | Dead Code (Microservice stub). |
| `services/notification_service/` | **DELETED** | Dead Code (Microservice stub). |
| `services/partner_service/` | **DELETED** | Dead Code (Microservice stub). |
| `services/recommendation_service/` | **DELETED** | Dead Code (Microservice stub). |

## 3. GCP Services
| Service | Location | Decision | Rationale |
| :--- | :--- | :--- | :--- |
| `lfsd` | `europe-west1` | **DELETED** | Orphaned/Duplicate. |
| `lfsd-backend` | `us-central1` | **KEEP** | Production Backend. |
| `lfsd-frontend` | `us-central1` | **KEEP** | Production Frontend. |
| `lfsd-landing` | `us-central1` | **KEEP** | Landing Page. |
| `lfsd-api-gateway` | `us-central1` | **AUDIT** | Verify traffic. Likely redundant. |
