# GCP Kill List

## 💀 To Be Deleted / Deleted
| Resource Name | Type | Region | Justification | Recovery Path |
| :--- | :--- | :--- | :--- | :--- |
| `lfsd` | Cloud Run | `europe-west1` | **Ghost Service**. All active dev is in `us-central1`. | Redeploy using `cloudbuild_backend.yaml`. |
| `lfsd-api-gateway` | Cloud Run | `us-central1` | **Redundant**. Frontend Nginx proxies to Backend directly. | Re-enable in Cloud Build if microservices split occurs. |

## 🛡️ Protected / Active
| Resource Name | Type | Region | Purpose | Invariant |
| :--- | :--- | :--- | :--- | :--- |
| `lfsd-backend` | Cloud Run | `us-central1` | **Core API**. Hosts FastAPI/Python. | Must pass Health Check `/api/health`. |
| `lfsd-frontend` | Cloud Run | `us-central1` | **Core UI**. Hosts React/Vite/Nginx. | Must server `index.html` on `/`. |
| `lfsd-landing` | Cloud Run | `us-central1` | **Marketing**. Independent deploy cycle. | - |
