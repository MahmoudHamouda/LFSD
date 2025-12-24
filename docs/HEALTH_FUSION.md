# Health Source Fusion & Integration

This document describes how Viv fuses health data from multiple sources to compute a unified Health Score.

## Unified Data Model

All health data is normalized into two tables:

1.  **`HealthDataSample`**: Stores time-series data (e.g., daily steps, sleep minutes) from objective sources (Apple, Google, Whoop).
2.  **`HealthProfile`**: Stores slowly-changing attributes (diet, habits, stress) from onboarding or manual updates.

## Data Fusion Logic (`services/health_data_fusion.py`)

When computing scores, the engine fetches data from the last 30 days and applies the following precedence rules per metric:

### 1. Sleep Metrics
*   **Primary**: WHOOP (Best sleep tracking fidelity)
*   **Secondary**: Apple Health / Google Fit
*   **Fallback**: Manual sleep hours from profile

### 2. Activity / Movement
*   **Primary**: Apple Health / Google Fit (Best step counting)
*   **Secondary**: WHOOP
*   **Fallback**: Manual "Activity Level" (Sedentary/Moderate/Active)

### 3. Recovery
*   **Primary**: WHOOP (RHR, HRV)
*   **Secondary**: Wearable RHR (Apple/Google)
*   **Fallback**: Derived from sleep quality + self-reported stress.

## Confidence Scores

Every fused metric comes with a `confidence` score (0.0 - 1.0):
*   **> 0.8**: High confidence (Device data present)
*   **0.5 - 0.7**: Medium confidence (Self-reported data)
*   **< 0.5**: Low confidence (Missing or minimal data)

## Supported Integrations

### 1. Manual Onboarding
*   Captures baseline habits, diet, and lifestyle load.
*   Populates `HealthProfile`.

### 2. WHOOP (Month-in-Review)
*   Users upload their PDF report.
*   Parsed data populates `HealthDataSample` with `source='whoop'`.

### 3. Apple Health / Google Fit
*   Cloud OAuth integration.
*   Syncs daily summaries to `HealthDataSample`.

## Future Work
*   Real-time webhook updates for Google/Apple.
*   Direct WHOOP API integration (vs PDF parsing).
