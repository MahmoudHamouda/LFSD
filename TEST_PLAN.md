# Test Plan

## Overview
This document outlines the testing strategy for the LFSD application, covering unit, integration, and end-to-end tests.

## Test Levels

### 1. Unit Tests (`tests/unit/`)
Focus on individual functions and classes in isolation.
- **Models**: Verify DB model constraints and methods.
- **Services**: Mock external dependencies (APIs, DB) and test logic.
- **Utils**: Test helper functions.

### 2. Integration Tests (`tests/integration/`)
Verify interactions between components and external systems (mocked or sandbox).
- **API**: Test API endpoints (status codes, response format).
- **Mobility**: Test `MobilityAggregator` with mock providers.
- **AI**: Test `GeminiService` intent recognition (mocked model).
- **Database**: Test DB queries and transactions.

### 3. End-to-End Tests (`tests/e2e/`)
Simulate real user journeys.
- **Frontend Journey**: Selenium/Playwright tests for UI flows.
- **Full Flow**: API tests covering a complete scenario (Register -> Login -> Book Ride).

## Key Test Scenarios

### Mobility
- **Price Comparison**: Verify aggregator returns sorted options.
- **Booking**: Verify booking flow (mocked).
- **Error Handling**: Verify behavior when provider is down.

### AI & Chat
- **Intent Recognition**: Verify correct intent extraction from text.
- **Context**: Verify conversation history is maintained.
- **Viv Indices**: Verify AI recommendations change based on user indices (Financial vs Health).

### Indices Calculation
- **Financial Score**: Test calculation based on income/expenses.
- **Health Score**: Test calculation based on sleep/activity.
- **Time Score**: Test calculation based on saved time.

## Execution
- Run all tests: `pytest`
- Run specific category: `pytest tests/integration/mobility`
