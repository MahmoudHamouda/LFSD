# Application Architecture

## Overview
LFSD is a modular Python application built with FastAPI (backend) and React (frontend). It follows a service-oriented architecture where core logic is separated into distinct services.

## Directory Structure
- **`app.py`**: Main entry point, configures FastAPI app and middleware.
- **`core/`**: Core infrastructure (Authentication, Configuration, Rate Limiting).
- **`routes/`**: API Route Handlers (Controllers).
- **`models/`**: Database Models (SQLAlchemy).
- **`services/`**: Business Logic Services.
- **`scripts/`**: Utility scripts.
- **`tests/`**: Test suite.

## Key Components

### 1. API Layer (`routes/`)
Handles HTTP requests, validates input, and delegates to services.
- `user_routes.py`: Auth & Profile.
- `mobility_routes.py`: Ride booking & price checks.
- `financial_routes.py`: Financial tracking.
- `chat_routes.py`: AI Chat interface.

### 2. Service Layer (`services/`)
Contains business logic and external integrations.
- **Mobility**: `MobilityAggregator` unifies Uber, Careem, Bolt, RTA.
- **AI**: `GeminiService` handles chat and intent recognition.
- **Health**: Integrates with health providers.
- **Financial**: Analyzes spending and affordability.

### 3. Data Layer (`models/`)
Defines database schema and handles DB interactions via SQLAlchemy.

### 4. Core (`core/`)
- `config.py`: Centralized configuration using Pydantic.
- `authentication.py`: JWT handling.
- `rate_limiting.py`: API rate limiting.

## Integration Flow
1. **Request**: Client sends request to API Endpoint.
2. **Auth**: Middleware verifies JWT token.
3. **Route**: Handler calls appropriate Service.
4. **Service**: Executes logic, calls external APIs (if needed), queries DB.
5. **Response**: Service returns data, Route formats JSON response.

## External Integrations
- **Uber/Careem/Bolt**: Mobility APIs.
- **Google Gemini**: AI Model.
- **Google Maps**: Geocoding & Routing.
- **Whoop/Apple Health**: Health Data.
