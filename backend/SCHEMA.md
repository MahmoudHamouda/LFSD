# LFSD Database Schema

This document outlines the core data models used in the LFSD SQLite database (`lfsd.db`).

## 1. Core Identity
- **User**: The central entity. Contains login credentials (`hashed_password`), profile JSON, and onboarding status.
- **Connection**: Stores OAuth tokens for external integrations (e.g., Google, Whoop).
- **VivIndex**: Time-series snapshots of the user's 3-tenant scores (Finance, Health, Time).

## 2. Finance (Deep Finance)
- **FinancialAccount**: Represents bank accounts, credit cards, etc.
- **Transaction**: Individual spending records linked to accounts and statements.
- **Statement**: Metadata for uploaded PDF/CSV bank statements.
- **FinancialScore**: Detailed breakdown of the 8 financial pillars (Cashflow, Net Worth, etc.).
- **RecurringBill**: Verified recurring commitments (Subscriptions, Rent).

## 3. Health (Deep Health)
- **HealthDailySummary**: Daily aggregates of sleep, steps, and HRV.
- **SleepSession**: Detailed sleep stages (Deep, REM, Wake).
- **Workout**: Exercise sessions with duration and calorie burn.
- **HealthProfile**: Persistent user habits (Diet, Smoking, Stress).

## 4. Time & Mobility (Deep Time)
- **CalendarEvent**: Normalized calendar entries (Meetings, Focus time).
- **TimeScore**: Productivity metrics (Structure, Focus, Overwhelm).
- **MobilityTrip**: Rideshare trips (Uber/Lyft) with cost and location data.
- **TimeProfile**: User's manual inputs on work style and time drains.

## 5. Intelligence & Actions
- **LifeGoal**: User-defined goals linked to specific pillars (e.g., "Save $5k", "Run 5k").
- **VivLog**: Audit trail of AI decisions and advice logic.
- **Recommendation**: Proactive AI suggestions.
- **DBConversation / DBMessage**: Chat history storage.

## Notes
- **UUIDs**: All primary keys are UUID strings.
- **JSON Fields**: Extensive use of `JSON` columns for flexible data storage (e.g., `metrics_json`, `context_snapshot_json`).
