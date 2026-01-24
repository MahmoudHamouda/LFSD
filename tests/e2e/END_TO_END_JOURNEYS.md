# End-to-End Test Journeys

This document defines **end-to-end test journeys** for LFSD. Each journey includes both:
- **Gherkin-style steps** for readability.
- **A test-case checklist** for execution and traceability.

## Scope
- **Auth & Onboarding**
- **Finance**
- **Health**
- **Time**
- **Chat / Viv Intelligence**
- **Goals & Recommendations**
- **Error Handling & Resilience**

---

## Journey E2E-01: New user onboarding with integrations

### Gherkin
```
Scenario: New user completes onboarding and connects integrations
  Given the user is on the signup page
  When the user registers with a valid email and password
  And the user logs in successfully
  And the user completes onboarding steps
  And the user connects a Finance provider (sandbox)
  And the user connects a Health provider (sandbox)
  And the user connects a Calendar provider (sandbox)
  Then the dashboard should show initial Viv Index scores
  And the integrations should be marked as connected
```

### Test Checklist
- **Preconditions**: Backend + frontend running; sandbox integrations enabled.
- **Steps**:
  1. Register and login.
  2. Complete onboarding form (profile, goals, baseline info).
  3. Connect Finance, Health, Calendar providers.
  4. Navigate to Dashboard.
- **Expected Results**:
  - User session active.
  - Integration badges show "connected".
  - Viv Index widgets appear with non-null scores.

---

## Journey E2E-02: Finance ingestion → transactions → Viv Index update

### Gherkin
```
Scenario: User uploads a statement and sees financial metrics update
  Given the user is authenticated
  When the user uploads a bank statement (PDF/CSV)
  And the system parses transactions and categories
  Then the finance dashboard should list new transactions
  And the financial Viv Index score should update
```

### Test Checklist
- **Preconditions**: User logged in; sample statement file available.
- **Steps**:
  1. Upload statement via Finance section.
  2. Wait for parsing/completion.
  3. Open transactions list.
  4. Verify Viv Index score updated.
- **Expected Results**:
  - Statement appears in statement list.
  - Transactions appear with categories.
  - Financial score changes from baseline.

---

## Journey E2E-03: Health sync → sleep summary → health score

### Gherkin
```
Scenario: User syncs wearable data and reviews health summary
  Given the user is authenticated
  When the user syncs wearable data for the last 7 days
  And the system ingests sleep and activity summaries
  Then the Health dashboard should display sleep sessions
  And the Health Viv Index score should update
```

### Test Checklist
- **Preconditions**: Health provider connected.
- **Steps**:
  1. Trigger health sync.
  2. Open Health dashboard.
  3. Review sleep sessions and activity summaries.
- **Expected Results**:
  - Sleep sessions listed with durations.
  - Health score changes from baseline.

---

## Journey E2E-04: Time sync → calendar view → time score

### Gherkin
```
Scenario: User syncs calendar events and reviews time metrics
  Given the user is authenticated
  When the user syncs calendar events for the current week
  Then the Calendar view should render the events
  And the Time Viv Index score should update
```

### Test Checklist
- **Preconditions**: Calendar provider connected.
- **Steps**:
  1. Trigger calendar sync.
  2. Open Calendar page.
  3. Verify events display with tags (meeting/deep work).
- **Expected Results**:
  - Events appear in the weekly view.
  - Time score updates to reflect schedule load.

---

## Journey E2E-05: Chat query → AI response → Viv rationale

### Gherkin
```
Scenario: User asks a finance affordability question in chat
  Given the user is authenticated
  And the user has finance data ingested
  When the user asks "Can I afford a weekend trip?"
  Then the assistant should reply with an affordability recommendation
  And the response should include the Viv rationale or context snapshot
```

### Test Checklist
- **Preconditions**: Finance data present; AI service enabled.
- **Steps**:
  1. Open Chat.
  2. Ask the affordability question.
  3. Expand the "Why" or rationale panel.
- **Expected Results**:
  - AI response includes recommendation.
  - Rationale/context is visible.

---

## Journey E2E-06: Create goal → track progress → recommendation

### Gherkin
```
Scenario: User creates a goal and receives a recommendation
  Given the user is authenticated
  When the user creates a financial goal with target and deadline
  And the system saves the goal
  Then the goal should appear with progress tracking
  And the recommendations should reference the new goal
```

### Test Checklist
- **Preconditions**: User logged in.
- **Steps**:
  1. Create a new goal (title, target amount, deadline).
  2. Save and open goal list.
  3. Trigger recommendations or chat.
- **Expected Results**:
  - Goal appears with progress bar.
  - Recommendations mention the goal.

---

## Journey E2E-07: Dashboard roll-up across pillars

### Gherkin
```
Scenario: Dashboard shows rolled-up Viv Index after updates
  Given the user is authenticated
  And the user has Finance, Health, and Time data ingested
  When the user opens the Dashboard
  Then the Viv Index cards should show current scores for all pillars
  And the trend indicators should reflect recent changes
```

### Test Checklist
- **Preconditions**: Data available across all pillars.
- **Steps**:
  1. Navigate to Dashboard.
  2. Review pillar cards and trend badges.
- **Expected Results**:
  - All three pillar scores visible.
  - Trend indicators show relative changes.

---

## Journey E2E-08: Resilience on provider failure

### Gherkin
```
Scenario: System handles integration provider outage gracefully
  Given the user is authenticated
  When the user triggers a sync and the provider is unavailable
  Then the system should show a non-blocking error message
  And previously synced data should remain visible
```

### Test Checklist
- **Preconditions**: Simulate provider outage or invalid token.
- **Steps**:
  1. Trigger sync with provider disabled.
  2. Observe UI and logs.
- **Expected Results**:
  - Error message displayed (not a crash).
  - Existing data remains visible.

---

## Journey E2E-09: Session expiry → re-authentication

### Gherkin
```
Scenario: User session expires and re-authenticates
  Given the user is authenticated
  And the session token expires
  When the user attempts to access a protected page
  Then the user should be redirected to login
  And after login the user returns to the requested page
```

### Test Checklist
- **Preconditions**: Short-lived token or forced expiry.
- **Steps**:
  1. Expire token and request a protected route.
  2. Login again.
- **Expected Results**:
  - Redirect to login.
  - Return to the original page post-login.

---

## Journey E2E-10: Data consistency across exports

### Gherkin
```
Scenario: Exported data matches dashboard totals
  Given the user is authenticated
  And the user has finance data ingested
  When the user exports transactions
  Then the export totals should match dashboard summaries
```

### Test Checklist
- **Preconditions**: Finance data present.
- **Steps**:
  1. Export transactions (CSV/JSON).
  2. Compare totals with dashboard summary.
- **Expected Results**:
  - Export totals equal dashboard totals.
