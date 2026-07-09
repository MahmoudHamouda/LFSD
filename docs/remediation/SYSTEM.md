# System Architecture

## 1. Core Purpose
LFSD (Life Finance Strategy Dashboard) is a holistic dashboard aggregating Financial, Health, and Time data to calculate a composite "VivIndex" score.

## 2. Boundaries (`BOUNDARIES.md`)
*   **Frontend**: React (Vite). Pure UI. No business logic beyond display formatting.
*   **Backend**: FastAPI (Python). All business logic, scoring engines, and integrations.
*   **Database**: SQLite (Dev) / Cloud SQL (Prod). Relational data.
*   **AI**: Gemini 1.5 Pro. Stateless analysis agent.

## 3. Invariants
1.  **No Direct DB Access**: Frontend MUST use API.
2.  **Scoring Consistency**: Scores (0-100) are ALWAYS calculated by `backend/services/*_scoring.py`, never by AI speculation.
3.  **Stateless AI**: The AI (`gemini_service.py`) analyzes *provided* context. It does NOT store long-term state itself.
4.  **Secure Config**: Secrets MUST flow from Environment Variables.

## 4. Service Catalog
*   `gemini_service`: Orchestrates AI queries.
*   `financial_scoring`: Calculates Financial Subscores.
*   `health_scoring`: Calculates Health Subscores.
*   `time_scoring`: Calculates Time Subscores.
*   *(Consolidation In Progress...)*
