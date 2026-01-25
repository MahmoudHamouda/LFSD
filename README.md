# Life Operating System (LFSD)

**LFSD** is an AI-driven "Operating System for Life" designed to optimize your Finance, Health, and Time. It ingests data from your real life (Bank Statements, Wearables, Calendar), calculates a "Viv Index" score, and provides actionable, context-aware advice via an AI Assistant.

## Project Structure
- **`backend/`**: FastAPI server handling logic, database, and AI integration.
    - [Backend Documentation](backend/README.md)
    - [Database Schema](backend/SCHEMA.md)
- **`frontend/`**: React + Vite application for the user interface.
    - [Frontend Documentation](frontend/README.md)
- **`docs/`**: Additional project documentation.
- **`scripts/`**: Maintenance and utility scripts.

## Quick Start (Windows)

1.  **Prerequisites**:
    - [Python 3.9+](https://www.python.org/)
    - [Node.js 16+](https://nodejs.org/)

2.  **Environment Setup**:
    - Ensure `backend/.env` exists (see backend docs).
    - Ensure `frontend/.env` exists (optional).

3.  **One-Click Launch**:
    Run the PowerShell script in the root directory:
    ```powershell
    ./start_all.ps1
    ```
    This will open two new windows for the Backend (Port 8080) and Frontend (Port 3000).

4.  **Access**:
    - App: [http://localhost:3000](http://localhost:3000)
    - API Docs: [http://localhost:8003/docs](http://localhost:8003/docs)

## Key Features
- **Holistic Scoring**: "Viv Index" unifies Finance, Health, and Time into single scores.
- **AI Assistant**: Chat with your data ("Can I afford a trip?", "How is my sleep affecting my work?").
- **Data Integrations**:
    - **Finance**: PDF Statement parsing (OCR/Text).
    - **Health**: Wearable data normalization.
    - **Time**: Calendar analysis.

## Operationalization
This codebase is structured for local deployment but can be containerized.
- **Code Cleanup**: Debug artifacts still exist in the repo root (e.g., `debug_*.py`, `*.txt`); move them into `backend/scripts/` or remove before release.
- **Persistence**: SQLite database `lfsd.db` stores all state.