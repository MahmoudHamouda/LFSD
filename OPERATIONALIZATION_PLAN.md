# Operationalization Plan

## Overview
This plan details the steps to operationalize the LFSD application, ensuring all integrations are active and the UI is fully functional. It is structured around the three core tenants of the "Viv" logic engine: **Time**, **Health**, and **Finance**.

## 1. Deep Time (Productivity & Mobility)
*Focus: "The Cost of Time" & "Context of Location"*

### A. Mobility (Moving through Space)
**Schema**: `mobility_trips`
- **Operationalization**:
    - **Ingestion**:
        - **Uber/Careem/Bolt**: Use `MobilityAggregator` to fetch real-time estimates.
        - **Google Maps**: Use for path visualization (Polyline) and traffic data.
    - **Processing**:
        - Calculate `cost_amount` vs. `time_saved` to recommend "Economy" vs. "Premium" (`trip_type`).
    - **UI Fields**:
        - **Map**: Render route using Google Maps API.
        - **Ride Cards**: Display Provider (Uber/Careem), ETA (`pickup_time`), Cost (`cost_amount`), and "Viv Recommendation" badge.
        - **Filters**: "Fastest", "Cheapest", "Balanced".

### B. Schedule (Moving through Time)
**Schema**: `calendar_events`
- **Operationalization**:
    - **Ingestion**:
        - **Google Calendar / Outlook**: OAuth integration to sync events.
    - **Processing**:
        - Classify events by `location_context` (WFH, Office, Traveling).
        - Calculate "Busy Score" based on `attendee_count` and `is_meeting`.
    - **UI Fields**:
        - **Timeline View**: Horizontal scroll of daily events.
        - **Context Tags**: Badges for "Meeting", "Deep Work", "Travel".
        - **Next Action**: "Leave by 10:15 AM" dynamic prompts.

### C. Productivity Score (The Index)
**Schema**: `viv_indexes.time_score`
- **Calculation**:
    - `(Free Time / Total Awake Time) * Efficiency Factor`.
- **UI**:
    - **Dashboard Widget**: Circular progress bar (0-100).
    - **Trend**: "Up 5% from yesterday".

### D. Lifestyle & Leisure (Quality Time)
*Focus: "Offsetting Stress & Enjoying Life"*
**Schema**: `lifestyle_events` (New Proposed Schema)
- **Operationalization**:
    - **Ingestion**:
        - **Food**: Uber Eats / Deliveroo / OpenTable (Reservations).
        - **Events**: Ticketmaster / Eventbrite (Concerts, Sports).
    - **Processing**:
        - Correlate "High Stress" days (from Health) with "Treat Yourself" recommendations.
    - **UI Fields**:
        - **"Treat Yourself" Card**: Suggests a favorite restaurant or upcoming concert when stress is high.
        - **Quick Book**: "Order usual from Nando's" button.

---

## 2. Deep Health (Wellbeing)
*Focus: "Good Tired vs. Bad Tired"*

### A. Physical State (Recovery)
**Schema**: `health_daily_summaries`, `sleep_sessions`
- **Operationalization**:
    - **Ingestion**:
        - **Whoop / Apple Health / Oura**: Webhook or API poll for daily recovery metrics.
    - **Processing**:
        - Normalize `hrv_average` and `resting_heart_rate` to a baseline.
        - Flag "Low Recovery" days to trigger "Light Schedule" recommendations.
    - **UI Fields**:
        - **Sleep Card**: `sleep_duration_minutes` (converted to H:MM), `sleep_quality_score` (Color-coded: Red/Amber/Green).
        - **Recovery Metric**: HRV and RHR sparklines.

### B. Activity (Exertion)
**Schema**: `workouts`
- **Operationalization**:
    - **Ingestion**:
        - Sync workouts from wearables.
    - **Processing**:
        - Calculate `calories_burned` and `perceived_exertion`.
    - **UI Fields**:
        - **Activity Log**: List of recent workouts with `activity_type` icons.
        - **Strain Score**: Visual indicator of daily physical load.

### C. Nutrition & Diet (Fuel)
**Schema**: `nutrition_logs` (New Proposed Schema)
- **Operationalization**:
    - **Ingestion**:
        - **MyFitnessPal / Cronometer**: Sync calorie and macro data.
    - **Processing**:
        - Compare `calories_in` vs. `calories_burned`.
    - **UI Fields**:
        - **Macro Wheel**: Protein/Carbs/Fat breakdown.
        - **Calorie Net**: Visual balance of In vs. Out.

### D. Health Score (The Index)
**Schema**: `viv_indexes.health_score`
- **Calculation**:
    - Weighted average of Sleep Quality, HRV, and Activity Balance.
- **UI**:
    - **Dashboard Widget**: Heart icon with score.
    - **Alerts**: "Low Energy - Suggesting early bedtime."

---

## 3. Deep Finance (Wealth)
*Focus: "Affordability vs. Value"*

### A. Accounts & Balances
**Schema**: `financial_accounts`
- **Operationalization**:
    - **Ingestion**:
        - **Stripe / Plaid (Sandbox)**: Connect dummy bank accounts.
    - **Processing**:
        - Aggregate `current_balance` across Checking/Savings.
        - Monitor `limit` usage on Credit Cards.
    - **UI Fields**:
        - **Net Worth Card**: Total Assets - Total Liabilities.
        - **Account List**: breakdown by `institution_name` and `account_type`.

### B. Investments & Wealth (Growth)
**Schema**: `investment_portfolios` (New Proposed Schema)
- **Operationalization**:
    - **Ingestion**:
        - **IBKR / Betterment / Robinhood**: API or statement import.
        - **Bank Statements**: PDF parsing for legacy accounts.
    - **Processing**:
        - Track `daily_change_percent` and `total_return`.
    - **UI Fields**:
        - **Portfolio View**: Asset allocation chart (Stocks/Bonds/Crypto).
        - **Performance**: "Your portfolio is up 3% this month."

### C. Transactions (Spending Behavior)
**Schema**: `transactions`
- **Operationalization**:
    - **Ingestion**:
        - Daily transaction sync.
    - **Processing**:
        - **Categorization**: Map `merchant_category_code` to `category_primary` (e.g., "Food", "Transport").
        - **Recurring Detection**: Flag subscriptions (`is_recurring`).
    - **UI Fields**:
        - **Recent Transactions**: List with `merchant_name`, `amount`, and `category_detailed` icon.
        - **Spending Breakdown**: Pie chart by Category.

### D. Financial Score (The Index)
**Schema**: `viv_indexes.financial_score`
- **Calculation**:
    - Savings Rate + Budget Adherence + Debt-to-Income Ratio.
- **UI**:
    - **Dashboard Widget**: Dollar sign with score.
    - **Insight**: "On track for [Goal Name]".

---

## 4. Core Logic & Goals (The Brain)

### A. Life Goals
**Schema**: `life_goals`
- **Operationalization**:
    - **UI**:
        - **Goal Setter**: Form to input `title`, `target_amount`, `deadline`.
        - **Progress Bar**: `saved_amount` / `target_amount`.
    - **Logic**:
        - `impact_vector_json` determines how a ride or purchase affects a goal (e.g., "Taking this Uber delays 'New Car' by 2 days").

### B. Viv Intelligence (The "Why")
**Schema**: `viv_logs`
- **Operationalization**:
    - **UI**:
        - **Chat Interface**: Display `ai_response`.
        - **"Why did Viv say this?"**: Expandable section showing `decision_logic` and `context_snapshot_json`.

## Deployment Strategy
1. **Staging**: Deploy to a staging environment (e.g., Docker/K8s).
2. **Monitoring**: Set up logging (ELK/Sentry) and metrics (Prometheus/Grafana).
3. **CI/CD**: Automate testing and deployment pipelines.
