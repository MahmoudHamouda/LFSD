# LFSD Backend

The backend for the Life Operating System (LFSD), built with FastAPI and SQLAlchemy.

## Tech Stack
- **Framework**: FastAPI
- **Database**: SQLite (via SQLAlchemy ORM)
- **AI Integration**: Google Gemini (via `google-generativeai`)
- **Authentication**: OAuth2 with JWT (JSON Web Tokens)

## Directory Structure
- `api_gateway/`: (Legacy/Placeholder) Gateway configurations.
- `core/`: Core configurations (Auth, Config, Logging, Middleware).
- `models/`: Database models (`models.py`) and Pydantic schemas (`api_models.py`, `schemas.py`).
- `routes/`: API route handlers organized by domain (Auth, Finance, Health, Goal, History).
- `scripts/`: Utility scripts for seeding data, migrations, and debugging.
- `services/`: Business logic layer (Gemini Service, Finance Service, Health Service).
- `tests/`: Automated tests.

## Setup & Running

1.  **Prerequisites**: Python 3.9+
2.  **Install Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    ```
    *(Note: Use root requirements.txt only if you are containerizing the entire repo)*

3.  **Environment Variables**:
    Create a `.env` file in the `backend/` directory (or root, depending on config):
    ```env
    DATABASE_URL=sqlite:///backend/lfsd.db
    SECRET_KEY=your_secret_key
    GEMINI_API_KEY=your_gemini_key_or_mock
    DEBUG=True
    ```

4.  **Run Application**:
    ```bash
    # From the LFSD root directory
    python backend/app.py
    ```
    Or using uvicorn directly:
    ```bash
    uvicorn backend.app:create_app --reload --port 8003
    ```

## API Documentation
Once running, verify the API connection by visiting the Swagger UI:
- **Swagger UI**: [http://localhost:8003/docs](http://localhost:8003/docs)
- **OpenAPI JSON**: [http://localhost:8003/openapi.json](http://localhost:8003/openapi.json)

## Key Features
- **Goal Management**: Create and track life goals linked to pillars (Finance, Health, Time).
- **Chat Interface**: AI-driven chat that understands context and user intent.
- **Data Ingestion**: Hooks for uploading financial statements (PDF), calendar data, and health metrics.
- **Scoring Engine**: Calculates `VivIndex` based on financial, health, and productivity inputs.
