# HELM Orchestration System

## Overview
The HELM Orchestration Layer is a deterministic, tool-first wrapper that evaluates user intent and executes system commands *before* delegating responses to an LLM. It transforms the AI from a conversational commentator into an autonomous 'race engineer' capable of fetching data, triggering services, and returning concrete options.

## Request Flow
1. **Input Gateway**: User requests flow into the `chat_routes.py` or `/history/generate` endpoints.
2. **Intent Classification** (`orchestration/intent.py`):
   - Uses strict deterministic rule sets (regex/keyword matching) to categorize requests into domains (`MOBILITY`, `FINANCE`, `HEALTH`, etc.).
   - Extracts required entities (e.g., origin, destination).
3. **Tool/Service Routing** (`orchestration/router.py`):
   - Maps the classified Intent to a specific deterministic Executor (e.g., `MobilityExecutor`).
   - Short-circuits with a clarifying question if required entities are missing.
4. **Execution & Data Fetching** (`mobility/executor.py`, etc.):
   - Contacts internal services or external APIs (e.g., Google Maps) to fetch explicit structured data (ETA, cost, distance).
   - Generates confidence scores and applies user preferences.
5. **LLM-last Response Composition** (`orchestration/response.py`):
   - Takes the structured data output from the executor and optionally uses an LLM solely to formulate a concise, human-readable response.
   - Proposes one recommended action and one alternative.
6. **Audit & Activity Logging**:
   - Every tool call generates immutable `AuditLog` records.
   - Successful actions drop trace records into the user's `ActivityFeed`.

## Key Architectural Rules & Governance
1. **Contextual Memory (Intent Layer)**: The `IntentClassifier` must accept and parse `history` to retain context. When a user provides missing entities in subsequent messages (e.g. "yes book it"), the classifier must traverse recent chat history to retrieve previously declared entities (e.g. origin/destination) to prevent amnesia loops.
2. **Database Integrity (`users_v2`)**: All tables containing a `user_id` foreign key MUST explicitly reference `users_v2(id)`. **Do not** reference the deprecated `users` table. If seeding or inserting data fails silently, always check if the FK constraint was updated during the v1->v2 migration.
3. **Transaction Safety**: Do not allow cascading transaction aborts across distinct analytical domains. Score recalculations (e.g. Time vs Finance vs Health) must be isolated with individual `db.rollback()` blocks to prevent a failure in one isolated module from crashing the entire batch process.
