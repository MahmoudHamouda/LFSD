# Health Scoring Model (Viv Logic Engine)

This document describes the 5-pillar health scoring engine implemented in `services/health_scoring.py`.

## Overview

The Health Score (0-100) measures a user's overall physical wellbeing by synthesizing objective data from connected devices (Apple Health, Google Fit, Whoop) and subjective data from the onboarding profile.

## The 5 Pillars

### 1. Sleep (25%)
Measures effectiveness of rest.
- **Inputs**: Average sleep hours (device > manual).
- **Scoring**:
  - 7-9 hours: 25 points (Ideal)
  - 6-7 or 9-10h: 18 points
  - 5-6 or >10h: 12 points
  - <5 hours: 5 points

### 2. Movement (25%)
Measures daily activity volume.
- **Inputs**: Average daily steps, active minutes.
- **Scoring**:
  - ≥10,000 steps: 15-25 points (based on active minutes)
  - 3,000-10,000 steps: Scaled
  - <3,000 steps: Minimal points
  - **Manual Fallback**: Uses "Activity Level" selection ("Active", "Moderate", "Sedentary").

### 3. Recovery & Stress (20%)
Measures the body's readiness and mental load.
- **Inputs**: Sleep Score (proxy), Stress Level, Energy Pattern.
- **Logic**: 
  - Starts with a base derived from Sleep Score.
  - Penalizes for high stress ("Often", "Always") and unstable energy ("Highs & lows", "Crash").

### 4. Nutrition & Habits (20%)
Measures fuel quality and lifestyle habits.
- **Inputs**: Diet Style, Water Intake, Smoking, Alcohol.
- **Logic**:
  - Base points for "Healthy" or "Balanced" diet.
  - Bonus for high water intake (>2L).
  - Significant penalties for smoking and high alcohol consumption.

### 5. Lifestyle Load (10%)
Measures the sustainability of daily choices.
- **Inputs**: Cooking frequency, Takeaway frequency, Nightlife.
- **Logic**:
  - Bonus for cooking often.
  - Penalty for frequent takeaway or nightlife.

## Data Confidence

The engine calculates a `confidence` score (0-1) for the overall result and each pillar.
- **High Confidence (>0.8)**: Driven mostly by objective device data (Steps, Sleep tracking).
- **Low Confidence (<0.6)**: Driven mostly by manual self-reports.

## API Usage

### Get Health Score

**Endpoint**: `GET /api/health/users/{user_id}/health/score`

**Response**:
```json
{
  "status": "success",
  "data": {
    "overall": {
      "score": 78.5,
      "confidence": 0.9,
      "band": "Good"
    },
    "dimensions": {
      "sleep": { "score": 25, "max": 25, "confidence": 0.9 },
      "movement": { "score": 18, "max": 25, "confidence": 0.9 },
      ...
    },
    "recommendations": []
  }
}
```

## Future Extensions

To add new metrics (e.g., HRV, VO2max):
1. **Update `models.models.HealthDailySummary`** or `HealthDataSample` to store the new metric.
2. **Update `services/health_scoring.py`**:
   - Add extraction logic in step 1.
   - Update the relevant pillar logic (e.g., Pillar 3 for HRV) to include this new input.
