# Architectural Boundaries

To prevent AI hallucination and logical drift, HELM enforces strict separation of concerns across its Orchestration layer.

## 1. Orchestrator (`orchestration/master.py`)
- **Role**: Coordinates the overall pipeline. It invokes the classifier, router, and response composer. 
- **DO NOT** execute external queries or format messages in the master orchestrator. 
- **DO NOT** contain business rules.

## 2. Intent Classifier (`orchestration/intent.py`)
- **Role**: Classify user phrases into standard domain intents using deterministic regex/heuristics or narrow LLMs.
- **DO NOT** reach into databases to fetch context. Keep categorization pure.
- **DO NOT** attempt to fulfill an action or extract non-essential entities. Focus on primary variables.

## 3. Executors (`mobility/executor.py`, etc.)
- **Role**: Handle external tool requests. Returns hard data (e.g., commute options: mode, time, cost).
- **DO NOT** produce human-readable paragraphs. Return TypedDictionaries or Pydantic models.
- **DO NOT** communicate directly with the end-user (no print, no immediate string return).
- **MUST** log failures.
- **MUST** handle missing API keys by gracefully mocking a response if the service is unavailable.

## 4. Routes (`backend/routes/*.py`)
- **Role**: Accept HTTP requests, enforce rate limits and JWT authentication.
- **DO NOT** embed NLP logic directly into route handlers. Standardize parsing and logging at the Orchestrator level.
