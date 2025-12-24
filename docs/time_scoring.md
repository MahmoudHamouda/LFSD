# Time & Productivity Pillar Implementation Guide

## Overview
The Time & Productivity pillar is designed to help users understand their time usage, workload capacity, a work-life balance. It aggregates data from manual profile inputs and (eventually) calendar integrations to produce a "Productivity Pulse" score.

## Data Models

### 1. `TimeProfile` (Manual Inputs)
Stores user's self-reported habits and structure.
- **Structure**: Work status, work hours, calendar usage, commute.
- **Load**: Time spent on meals/housework, admin tasks.
- **Top Drains**: List of major time sinks (e.g., meetings, emails).
- **Psychology**: Routine style, task planning style, overwhelm level.

### 2. `TimeEvent` (Calendar Data)
Stores normalized events from Google Calendar or Outlook (via manual upload/parsing).
- `source`: 'google', 'outlook', 'upload', 'manual'.
- `start_time`, `end_time`, `duration_minutes`.
- `category`: 'work', 'personal', 'commute', etc. (derived or raw).

### 3. `TimeScore` (Calculated Metrics)
Stores the snapshot of productivity analysis.
- **Overall Score (0-100)**
- **Sub-scores**:
  - `structure_score`: Organization level.
  - `load_score`: Busyness vs capacity.
  - `focus_score`: Fragmentation of deeper work.
  - `friction_score`: Time spent on logistics/admin.
  - `stress_score`: Subjective and objective pressure.

## Services

### `services/time_data_fusion.py`
Aggregates `TimeProfile` and `TimeEvent` data into unified metrics.
- Calculates `avg_work_hours`, `calendar_density`, `commute_load`.
- Handles fallbacks when real calendar data is missing (using manual profile estimates).

### `services/time_scoring.py`
The core logic engine.
- `compute_time_score(metrics, profile)`:
  - Normalizes metrics against healthy baselines (e.g., 40h work week, <30m commute).
  - Penalizes "Red Flags" like excessive meetings (>20h/week) or "Always" overwhelmed.
  - Rewards good habits like "Planning ahead" or "Using a digital calendar".
- Returns the Score object with breakdown and actionable recommendations.

## API Endpoints (`/time` prefix)

- `POST /manual`: Save/update `TimeProfile`.
- `GET /score`: Trigger calculation and retrieve latest `TimeScore`.
- `POST /calendar/google/connect`: (Mock) Initiate OAuth.
- `GET /calendar/google/sync`: (Mock) Fetch and parse events.
- `POST /calendar/upload`: (Mock) Upload calendar screenshot for parsing.

## Frontend Flow (Onboarding)
1. **Productivity Step**: User fills out manual structure/load form.
2. **Integration Step**: User connects Google Calendar or uploads a schedule image.
3. **Productivity Pulse**: Display the calculated score (0-100) and sub-scores.

## Future Improvements
- Implement real Google Calendar OAuth flow.
- Integrate OCR/LLM for "Upload Calendar" feature.
- meaningful categorization of `TimeEvent`s (using NLP on titles).
