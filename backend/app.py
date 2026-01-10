"""
Application entry point and factory.

This module exposes a ``create_app`` function that instantiates and configures
the FastAPI application. It mounts middleware for CORS, rate limiting and
logging, sets up global exception handlers and registers routers for the
different service areas.
"""

from __future__ import annotations

from time import perf_counter
from typing import Callable
import sys
import os

# Add current directory (backend) to sys.path so that absolute imports (e.g. 'from core') work.
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

# Try to use loguru for structured logging; fall back to standard logging if not available.
try:
    from loguru import logger  # type: ignore
except Exception:
    import logging

    class _FallbackLogger(logging.Logger):  # type: ignore
        """
        Minimal logger API compatible with loguru. It exposes ``bind`` to mimic
        loguru's structured logging.
        """

        def bind(self, **kwargs):
            return self

    logging.basicConfig(level=logging.INFO)
    logger = _FallbackLogger(name="lfsd_app", level=logging.INFO)  # type: ignore

from core.config import get_settings
from core.rate_limiting import RateLimitExceeded, RateLimitMiddleware, limiter


from core.logging_config import setup_logging
from core.middleware import RequestIDMiddleware, BugReportMiddleware
from models.auth_schemas import LoginRequest, RegisterRequest

def create_app() -> FastAPI:
    """Create and configure a FastAPI application."""
    setup_logging() # Configure structured logging
    logger.error("!!! APP FACTORY CALLED - FULL PRODUCTION RESTORE !!!")

    # --- CLOUD SQL CONFIGURATION ---
    from google.cloud.sql.connector import Connector
    import pg8000
    import sqlalchemy
    from sqlalchemy.orm import sessionmaker

    def getconn():
        if settings.ENV != "prod":
            return None
        connector = Connector()
        conn = connector.connect(
            "newprojectlfsd:us-central1:lfsd-postgres-prod",
            "pg8000",
            user="postgres",
            password="LfsdSecure2024!",
            db="lfsd",
            ip_type="public"
        )
        return conn

    # --- AUTH0 CONFIGURATION ---
    AUTH0_DOMAIN = "dev-lmc05ou12e7ep05p.eu.auth0.com"
    AUTH0_CLIENT_ID = "VVw94DZQITVcARsNlp4JEZkyzMjsgioF"
    AUTH0_CLIENT_SECRET = "vfMd6SgVMU3HYeQvFvjU4Au0i2mbpHYR_lepVuDYvdepslGRyQR1AS235hsqcHMj"

    import requests
    from fastapi.responses import JSONResponse
    from fastapi import Body
    
    settings = get_settings()
    app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

    # --- NATIVE AUTH ENDPOINTS ---
    @app.post("/api/auth/login")
    async def login(data: LoginRequest = Body(...)):
        """Login via Auth0 Resource Owner Password Grant (Realm)"""
        print(f"LOGIN ATTEMPT: {data.email}")
        url = f"https://{AUTH0_DOMAIN}/oauth/token"
        payload = {
            "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
            "realm": "Username-Password-Authentication",
            "username": data.email,
            "password": data.password,
            "client_id": AUTH0_CLIENT_ID,
            "client_secret": AUTH0_CLIENT_SECRET,
            "audience": f"https://{AUTH0_DOMAIN}/api/v2/",
            "scope": "openid profile email offline_access"
        }
        
        resp = requests.post(url, json=payload)
        if not resp.ok:
            print(f"Auth0 Login Failed: {resp.text}")
            return JSONResponse(status_code=resp.status_code, content=resp.json())
            
        return resp.json()

    @app.post("/api/auth/register")
    async def register(data: RegisterRequest):
        """Register via Auth0 DB Connection"""
        url = f"https://{AUTH0_DOMAIN}/dbconnections/signup"
        payload = {
            "client_id": AUTH0_CLIENT_ID,
            "email": data.email,
            "password": data.password,
            "connection": "Username-Password-Authentication",
            "name": data.name
        }
        resp = requests.post(url, json=payload)
        if not resp.ok:
            return JSONResponse(status_code=resp.status_code, content=resp.json())
        return resp.json()

    @app.get("/api/auth/config")
    async def auth0_config():
        return {
            "domain": AUTH0_DOMAIN,
            "clientId": AUTH0_CLIENT_ID,
            "audience": f"https://{AUTH0_DOMAIN}/api/v2/"
        }

    # CORS configuration
    if settings.ALLOWED_ORIGINS == "*":
        allow_origins = ["*"]
    else:
        allow_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom Middleware
    app.add_middleware(BugReportMiddleware)
    app.add_middleware(RequestIDMiddleware) # Should be outer to capture everything

    # Rate limiting
    app.state.limiter = limiter
    app.add_middleware(RateLimitMiddleware)

    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Return errors in a consistent JSON shape."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests, please slow down."},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        import traceback
        error_details = f"Internal Server Error: {str(exc)}"
        # logger.exception("Unhandled exception") # Already logged
        print(f"CRITICAL ERROR: {error_details}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "detail": error_details,
                "debug_models": [k for k in sys.modules.keys() if 'models' in k],
                "debug_backend": [k for k in sys.modules.keys() if 'backend' in k]
            },
        )

    # Register routers
    # Register routers
    try:
        print("DEBUG: Importing api_routes_time")
        from routes import api_routes_time
        print("DEBUG: Importing api_routes_health")
        from routes import api_routes_health
        print("DEBUG: Importing api_routes_finance")
        from routes import api_routes_finance
        print("DEBUG: Importing api_routes_lifestyle")
        from routes import api_routes_lifestyle
        print("DEBUG: Importing history_routes")
        from routes import history_routes
        print("DEBUG: Importing user_routes")
        from routes import user_routes
        print("DEBUG: Importing calendar_routes")
        from routes import calendar_routes
        print("DEBUG: Importing api_routes_onboarding")
        from routes import api_routes_onboarding
        print("DEBUG: Importing api_routes_scores")
        from routes import api_routes_scores
        print("DEBUG: Importing mobility_routes")
        from routes import mobility_routes
        print("DEBUG: Importing auth0_routes")
        from routes import auth0_routes
        print("DEBUG: Importing test_routes")
        from routes import test_routes
        print("DEBUG: Importing growth_routes")
        from routes import growth_routes
        print("DEBUG: Importing admin_routes")
        from routes import admin_routes
        print("DEBUG: Importing api_routes_chat")
        from routes import api_routes_chat
        print("DEBUG: Imports DONE")
    except Exception as e:
        import traceback
        print(f"CRITICAL IMPORT ERROR (BLOCK 1): {e}")
        traceback.print_exc()
        raise e
    
    # Ensure mappers are configured
    # from sqlalchemy.orm import configure_mappers
    # configure_mappers()
    
    app.include_router(mobility_routes.router, prefix="/api")
    app.include_router(api_routes_time.router, prefix="/api")
    app.include_router(api_routes_health.router) # Prefix is already in router definition
    app.include_router(api_routes_finance.router, prefix="/api")
    app.include_router(api_routes_lifestyle.router, prefix="/api")
    app.include_router(history_routes.router)
    app.include_router(user_routes.router, prefix="/api")
    app.include_router(calendar_routes.router)
    app.include_router(api_routes_onboarding.router, prefix="/api")
    app.include_router(api_routes_scores.router, prefix="/api/scores")
    app.include_router(auth0_routes.router, prefix="/api")  # Auth0 authentication
    app.include_router(test_routes.router, prefix="/api")  # Simple test endpoints
    app.include_router(growth_routes.router, prefix="/api")
    app.include_router(admin_routes.router, prefix="/api")
    app.include_router(api_routes_chat.router, prefix="/api")
    
    try:
        from routes import api_routes_goals
        app.include_router(api_routes_goals.router, prefix="/api")
    except Exception as e:
        import traceback
        print(f"CRITICAL IMPORT ERROR (GOALS): {e}")
        traceback.print_exc()
        raise e
    
    try:
        from routes import api_routes_auth
        app.include_router(api_routes_auth.router, prefix="/api")
    except Exception as e:
        import traceback
        print(f"CRITICAL IMPORT ERROR (AUTH): {e}")
        traceback.print_exc()
        raise e
    
    from routes import recommendation_routes, partner_routes, api_routes
    app.include_router(recommendation_routes.router, prefix="/api")
    app.include_router(partner_routes.router, prefix="/api")
    app.include_router(api_routes.router) # Exposes /.auth/me and others at root
    
    # Init DB on startup if needed
    from models.database import init_db
    print("Initializing Database...")
    init_db()
    print("Database Initialized.")

    
    # Seed disabled temporarily for debugging
    # try:
    #     from seed_users import seed_all_users
    #     print("Running startup seeds (SYNC)...")
    #     seed_all_users()
    #     print("Startup seeds completed (SYNC).")
    # except Exception as e:
    #     print(f"Startup seed failed: {e}")
        # traceback.print_exc()

    try:
        from routes import api_routes_session
        app.include_router(api_routes_session.router, prefix="/api")
        app.include_router(api_routes_session.user_router, prefix="/api")
    except Exception as e:
        import traceback
        print(f"CRITICAL IMPORT ERROR (SESSION): {e}")
        traceback.print_exc()
        raise e

    from routes import recommendation_routes
    app.include_router(recommendation_routes.router, prefix="/api/home")

    # --- DEBUG ENDPOINT FOR DB PATCH ---
    @app.get("/api/debug/patch_schema")
    async def debug_patch_schema():
        try:
            from models.database import SessionLocal
            from sqlalchemy import text
            with SessionLocal() as db:
                print("DEBUG: Attempting to add pillar column...")
                db.execute(text("ALTER TABLE life_goals ADD COLUMN IF NOT EXISTS pillar VARCHAR DEFAULT 'finance';"))
                db.commit()
                return {"status": "success", "message": "Schema patch executed."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Initialize Scheduler
    from services.scheduler_service import SchedulerService
    scheduler = SchedulerService()
    
    
    @app.on_event("startup")
    async def startup_event():
        print("Startup event fired.")
        # Auto-migrate: Add auth0_id if missing
        try:
            from models.database import SessionLocal
            from sqlalchemy import text
            with SessionLocal() as db:
                print("Checking schema for auth0_id...")
                db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS auth0_id VARCHAR;"))
                print("Checking schema for life_goals.pillar...")
                # Try adding pillar column; ignore errors if exists (using exception handling as IF NOT EXISTS for column is Postgres 9.6+, safe to just catch)
                try:
                    db.execute(text("ALTER TABLE life_goals ADD COLUMN IF NOT EXISTS pillar VARCHAR DEFAULT 'finance';"))
                except Exception as ex:
                    print(f"Migration note: {ex}")
                db.commit()
                print("Schema check/migration completed successfully.")
        except Exception as e:
            print(f"Schema migration warning: {e}") 
        
    @app.on_event("shutdown")
    async def shutdown_event():
        scheduler.stop()

    print("App Factory Completed.")
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8003,
        reload=True,
    )
# Force Reload Triggered by Agent