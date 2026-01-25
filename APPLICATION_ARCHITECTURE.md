# Application Architecture

## Overview
LFSD is a modular Python application built with FastAPI (backend) and React (frontend). It follows a service-oriented architecture where core logic is separated into distinct services.

## Directory Structure
- **`backend/app.py`**: Main entry point, configures FastAPI app and middleware.
- **`backend/core/`**: Core infrastructure (Authentication, Configuration, Rate Limiting).
- **`backend/routes/`**: API Route Handlers (Controllers).
- **`backend/models/`**: Database Models (SQLAlchemy).
- **`backend/services/`**: Business Logic Services.
- **`backend/scripts/`**: Utility scripts.
- **`backend/tests/`**: Test suite.

## Key Components

### 1. API Layer (`routes/`)
Handles HTTP requests, validates input, and delegates to services.
- `user_routes.py`: Auth & Profile.
- `mobility_routes.py`: Ride booking & price checks.
- `financial_routes.py`: Financial tracking.
- `chat_routes.py`: AI Chat interface.

### 2. Service Layer (`services/`)
Contains business logic and external integrations.
- **Mobility**: `MobilityAggregator` unifies multiple providers:
  - Uber (✅ Sandbox API)
  - Careem (🔄 Mock implementation)
  - Bolt (🔄 Mock implementation)
  - RTA (🔄 Mock implementation)
- **AI**: `GeminiService` handles chat and intent recognition.
- **Health**: Integrates with health providers.
- **Financial**: Analyzes spending and affordability.

### 3. Data Layer (`models/`)
Defines database schema and handles DB interactions via SQLAlchemy.

### 4. Core (`core/`)
- `config.py`: Centralized configuration via dotenv/env vars (Settings class).
- `authentication.py`: JWT handling.
- `rate_limiting.py`: API rate limiting.

## Integration Flow
1. **Request**: Client sends request to API Endpoint.
2. **Auth**: Middleware verifies JWT token.
3. **Route**: Handler calls appropriate Service.
4. **Service**: Executes logic, calls external APIs (if needed), queries DB.
5. **Response**: Service returns data, Route formats JSON response.

## External Integrations
### Production/Sandbox APIs
- **Uber**: Sandbox API for ride estimates and booking.
- **Google Gemini**: Production AI Model for chat.
- **Google Maps**: Geocoding & Routing.
- **Whoop/Apple Health**: Health Data.

### Mock Implementations (Development)
- **Careem**: Mock service returning simulated ride data.
- **Bolt**: Mock service returning simulated ride data.
- **RTA**: Mock service returning simulated transit data.

> **Note**: Mock services provide realistic responses for development/testing without requiring production API credentials. They use the same interface as real integrations for seamless switching.
