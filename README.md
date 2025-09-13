# LFSD API

LFSD is a FastAPI‑based API that consolidates several service areas into a
single application. It demonstrates an app factory pattern with JWT
authentication, rate limiting using `slowapi`, and modular routing. All
configuration is managed via Pydantic settings.

## Quick start

1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start the API server locally:

   ```bash
   uvicorn app:create_app --factory --reload
   ```

3. Navigate to `http://localhost:8000/healthz` to verify the service is running.

## Environment variables

The application reads configuration from environment variables. A sample
`.env.example` file is provided. Key variables include:

| Variable | Description |
| --- | --- |
| `APP_NAME` | Application name |
| `ENV` | Environment name (e.g. `dev`, `staging`, `prod`) |
| `DEBUG` | Enable debug mode (`True`/`False`) |
| `SECRET_KEY` | Secret used to sign JWT tokens |
| `JWT_ALG` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry window |
| `ALLOWED_ORIGINS` | Comma‑separated CORS origins or `*` |
| `RATE_LIMIT` | Default request rate limit (e.g. `100/minute`) |
| `REDIS_URL` | Redis connection URI used for rate limiting |

## Docker compose

To run the API alongside a Redis instance using Docker Compose:

```bash
docker compose up --build
```

The API will be available on port 8000, and Redis on port 6379.

## Testing

This project uses pytest and HTTPX for integration testing. To execute the
test suite, run:

```bash
pytest -q
```

## Project layout

This repository uses an app factory in `app.py` to assemble routers defined in
individual `*_routes.py` modules. Authentication utilities live in
`authentication.py`, and rate limiting is configured in `rate_limiting.py`. See
the code comments for further guidance on extending the service.