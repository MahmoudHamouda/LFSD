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

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
from typing import List

# Import Routes and Models
import core.config
from models.database import init_db, get_db
from models.models import User
from sqlalchemy.orm import Session
from core.authentication import get_current_user

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

from core.rate_limiting import RateLimitExceeded, RateLimitMiddleware, limiter


from core.logging_config import setup_logging
from core.middleware import RequestIDMiddleware, BugReportMiddleware
from models.auth_schemas import LoginRequest, RegisterRequest


def create_app() -> FastAPI:
    """Create and configure a FastAPI application."""
    setup_logging()  # Configure structured logging
    settings = core.config.get_settings()
    logger.error("!!! APP FACTORY CALLED - FULL PRODUCTION RESTORE !!!")

    # --- CLOUD SQL CONFIGURATION ---
    # DB Connection is handled in models.database via init_db() and get_db()

    # --- AUTH0 CONFIGURATION ---
    AUTH0_DOMAIN = settings.AUTH0_DOMAIN
    AUTH0_CLIENT_ID = settings.AUTH0_CLIENT_ID
    AUTH0_CLIENT_SECRET = settings.AUTH0_CLIENT_SECRET

    import requests
    from fastapi.responses import JSONResponse
    from fastapi import Body

    app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "1.0.0"}

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
            "scope": "openid profile email offline_access",
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
            "name": data.name,
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
            "audience": f"https://{AUTH0_DOMAIN}/api/v2/",
        }

    # CORS configuration
    if settings.ALLOWED_ORIGINS == "*":
        allow_origins = ["*"]
    else:
        allow_origins = [
            origin.strip()
            for origin in settings.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom Middleware
    # app.add_middleware(BugReportMiddleware)
    # app.add_middleware(RequestIDMiddleware) # Should be outer to capture everything

    # Rate limiting
    # app.state.limiter = limiter
    # app.add_middleware(RateLimitMiddleware)

    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Return errors in a consistent JSON shape."""
        detail = exc.detail
        if exc.status_code >= 500:
            import uuid

            error_id = str(uuid.uuid4())[:12]
            logger.error(f"HTTP {exc.status_code} ERROR [{error_id}]: {exc.detail}")
            detail = f"An internal system error occurred. Please contact support with Error ID: {error_id}"

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail},
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(
        request: Request, exc: RateLimitExceeded
    ) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests, please slow down."},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        import traceback
        import uuid

        error_id = str(uuid.uuid4())[:12]
        error_details = f"Internal Server Error: {str(exc)}"
        logger.error(f"CRITICAL ERROR [{error_id}]: {error_details}")
        logger.error(traceback.format_exc())

        content = {
            "detail": f"An unexpected system error occurred. Please contact support with Error ID: {error_id}"
        }

        return JSONResponse(
            status_code=500,
            content=content,
        )

    # Register routers
    from routes import (
        api_routes_time,
        api_routes_health,
        api_routes_finance,
        api_routes_lifestyle,
        history_routes,
        user_routes,
        calendar_routes,
        api_routes_onboarding,
        api_routes_scores,
        mobility_routes,
        auth0_routes,
        test_routes,
        growth_routes,
        admin_routes,
        api_routes_chat,
        api_routes_goals,
        recommendation_routes,
        partner_routes,
        api_routes,
        api_routes_session,
    )

    # Initialize Integration Registry (Domain Executors)
    # The decorators will auto-register these tools into the Action Orchestrator
    try:
        from health import executor as _he
        from wealth import executor as _we
        from productivity import executor as _pe
        from lifestyle import executor as _le
        from mobility import executor as _me
    except Exception as e:
        logger.warning(f"Failed to load some domain executors: {e}")

    app.include_router(mobility_routes.router, prefix="/api")
    app.include_router(api_routes_time.router, prefix="/api")
    app.include_router(api_routes_health.router)
    app.include_router(api_routes_finance.router, prefix="/api")
    app.include_router(api_routes_lifestyle.router, prefix="/api")
    app.include_router(history_routes.router)
    app.include_router(user_routes.router, prefix="/api")
    app.include_router(calendar_routes.router)
    app.include_router(api_routes_onboarding.router, prefix="/api")
    app.include_router(api_routes_scores.router, prefix="/api/scores")
    app.include_router(auth0_routes.router, prefix="/api")
    app.include_router(test_routes.router, prefix="/api")
    app.include_router(growth_routes.router, prefix="/api")
    app.include_router(admin_routes.router, prefix="/api")
    app.include_router(api_routes_chat.router, prefix="/api")
    app.include_router(api_routes_goals.router, prefix="/api")

    # Recommendation & Partners
    app.include_router(recommendation_routes.router, prefix="/api/home")
    app.include_router(partner_routes.router, prefix="/api")

    # Root API & Session
    app.include_router(api_routes.router)
    app.include_router(api_routes_session.router, prefix="/api")
    app.include_router(api_routes_session.user_router, prefix="/api")

    # --- DEBUG ENDPOINT FOR DB PATCH ---
    if settings.DEBUG:

        @app.get("/api/debug/patch_schema")
        async def debug_patch_schema(secret: str):
            if secret != settings.ADMIN_SECRET:
                raise HTTPException(status_code=403, detail="Forbidden")
            try:
                from models.database import SessionLocal
                from sqlalchemy import text

                with SessionLocal() as db:
                    logger.info("DEBUG: Attempting to add pillar column...")
                    db.execute(
                        text(
                            "ALTER TABLE life_goals ADD COLUMN IF NOT EXISTS pillar VARCHAR DEFAULT 'finance';"
                        )
                    )
                    db.commit()
                    return {"status": "success", "message": "Schema patch executed."}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    @app.post("/api/debug/seed_growth")
    async def seed_growth_data(
        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ):
        """
        Seeds TierConfig and ensures the current user has a subscription.
        """
        try:
            print(f"Seeding growth data for user: {current_user.id}")
            # 1. Seed Tier Configs
            from models.growth_models import TierConfig, Subscription
            from models.growth_schemas import PlanId
            import json

            # Hardcoded configs (copied from GrowthService fallback)
            PLAN_CONFIGS = {
                PlanId.FREE: {
                    "features": ["basic_charts", "limit_5_goals", "basic_insight"],
                    "limits": {
                        "goals": 5,
                        "ai_chat_calls": 100,
                        "smart_recos": 10,
                        "executions": -1,
                        "history_months": 3,
                    },
                },
                PlanId.PLUS: {
                    "features": [
                        "advanced_charts",
                        "unlimited_goals",
                        "limited_executions",
                    ],
                    "limits": {
                        "goals": -1,
                        "ai_chat_calls": 500,
                        "smart_recos": 100,
                        "executions": 20,
                        "history_months": 12,
                    },
                },
                PlanId.PRO: {
                    "features": [
                        "advanced_charts",
                        "unlimited_goals",
                        "deep_insight",
                        "forecasting",
                        "priority_support",
                    ],
                    "limits": {
                        "goals": -1,
                        "ai_chat_calls": 2000,
                        "smart_recos": 500,
                        "executions": 100,
                        "history_months": -1,
                    },
                },
            }

            for plan_id, config in PLAN_CONFIGS.items():
                existing_tier = (
                    db.query(TierConfig).filter(TierConfig.plan_id == plan_id).first()
                )
                if not existing_tier:
                    print(f"Creating TierConfig for {plan_id}")
                    new_tier = TierConfig(plan_id=plan_id, config_json=config)
                    db.add(new_tier)
                else:
                    print(f"TierConfig for {plan_id} exists. Updating...")
                    existing_tier.config_json = config

            # 2. Ensure User Subscription
            sub = (
                db.query(Subscription)
                .filter(Subscription.user_id == current_user.id)
                .first()
            )
            if not sub:
                print("Creating Default FREE Subscription")
                new_sub = Subscription(
                    user_id=current_user.id,
                    plan_id=PlanId.FREE,
                    status="active",
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow() + timedelta(days=30),
                )
                db.add(new_sub)

            db.commit()
            return {"status": "success", "message": "Growth data seeded."}

        except Exception as e:
            import traceback

            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/debug/seed_force")
    async def seed_force(request: Request, db: Session = Depends(get_db)):
        """
        Unauthenticated (Secret Protected) endpoint to Initialize DB + Seed Growth.
        Usage: POST /api/debug/seed_force?secret=...
        """
        params = request.query_params
        secret = params.get("secret")
        if secret != settings.ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Invalid Secret")

        try:
            print("Force Seeding: Initializing DB...")
            # 1. Init DB (Create Tables)
            init_db()

            # 2. Seed Tier Configs (Existing logic preserved)
            print("Force Seeding: Creating Tiers...")
            from models.growth_models import TierConfig
            from models.growth_schemas import PlanId

            # Simple seed logic strictly for tiers
            PLAN_CONFIGS = {
                PlanId.FREE: {
                    "name": "Free",
                    "config": {
                        "features": ["basic_charts", "limit_5_goals", "basic_insight"],
                        "limits": {
                            "goals": 5,
                            "ai_chat_calls": 100,
                            "smart_recos": 10,
                            "executions": -1,
                            "history_months": 3,
                        },
                    },
                },
                PlanId.PLUS: {
                    "name": "Plus",
                    "config": {
                        "features": [
                            "advanced_charts",
                            "unlimited_goals",
                            "limited_executions",
                        ],
                        "limits": {
                            "goals": -1,
                            "ai_chat_calls": 500,
                            "smart_recos": 100,
                            "executions": 20,
                            "history_months": 12,
                        },
                    },
                },
                PlanId.PRO: {
                    "name": "Pro",
                    "config": {
                        "features": [
                            "advanced_charts",
                            "unlimited_goals",
                            "deep_insight",
                            "forecasting",
                            "priority_support",
                        ],
                        "limits": {
                            "goals": -1,
                            "ai_chat_calls": 2000,
                            "smart_recos": 500,
                            "executions": 100,
                            "history_months": -1,
                        },
                    },
                },
            }

            for plan_id, data in PLAN_CONFIGS.items():
                existing_tier = (
                    db.query(TierConfig).filter(TierConfig.plan_id == plan_id).first()
                )
                name = data["name"]
                config = data["config"]

                if not existing_tier:
                    new_tier = TierConfig(
                        plan_id=plan_id, name=name, config_json=config
                    )
                    db.add(new_tier)
                else:
                    existing_tier.config_json = config
                    existing_tier.name = name

            db.commit()

            # 3. Seed Users with FULL Persona Data (Finance, Health, Time data + Goals)
            print("Force Seeding: Seeding users with comprehensive persona data...")
            user_seed_status = "NOT_ATTEMPTED"
            user_seed_error = None

            try:
                # Import the comprehensive seeding function
                import sys
                import os

                # Ensure seed_users module is importable
                backend_path = os.path.dirname(os.path.abspath(__file__))
                if backend_path not in sys.path:
                    sys.path.insert(0, backend_path)

                from seed_users import safe_seed_users

                print("Calling safe_seed_users() - This will create users WITH data:")
                print("  - Financial accounts & transactions (30 day history)")
                print("  - Health metrics & sleep data (7 day history)")
                print("  - Calendar events")
                print("  - Life goals")
                print("  - VivIndex scores")

                safe_seed_users()
                user_seed_status = "SUCCESS"
                print("✅ Comprehensive user seeding completed!")

            except Exception as e:
                import traceback

                user_seed_error = str(e)
                print(f"❌ ERROR seeding users: {e}")
                print(traceback.format_exc())
                user_seed_status = "FAILED"

            message = (
                f"Database Initialized, Tiers Seeded. User Seeding: {user_seed_status}"
            )
            if user_seed_error:
                message += f" (Error: {user_seed_error[:100]})"

            return {
                "status": "success" if user_seed_status != "FAILED" else "partial",
                "message": message,
                "user_seed_status": user_seed_status,
            }

        except Exception as e:
            import traceback

            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    # Initialize Scheduler
    from services.scheduler_service import SchedulerService

    scheduler = SchedulerService()

    @app.on_event("startup")
    async def startup_event():
        print("Startup event fired.")
        # ----------------------------------------------------------------
        # COMPREHENSIVE FK MIGRATION
        # Root cause: When 'users' was renamed to 'users_v2', none of the
        # FK constraints on child tables were updated. Every INSERT with a
        # user_id in users_v2 fails because the DB FK still references
        # the old 'users' table. Fix ALL of them here.
        # ----------------------------------------------------------------
        ALL_TABLES_WITH_USER_FK = [
            # models.py
            "connections",
            "health_data_samples",
            "viv_indexes",
            "life_goals_v2",
            "financial_accounts_v2",
            "statements",
            "transactions_v2",
            "recurring_bills",
            "health_daily_summaries",
            "sleep_sessions",
            "workouts",
            "calendar_events",
            "mobility_trips",
            "viv_logs",
            "recommendations",
            "conversations",
            "messages",
            "orders",
            "onboarding_sessions",
            "financial_scores",
            "time_scores_v2",
            "feature_interests",
            "health_profiles",
            "time_profiles",
            "time_events",
            # chat_models.py
            "chat_sessions",
            "chat_history",
            "feedback",
            # logging_models.py
            "system_logs",
            "bug_reports",
            "activity_feed",
            "notifications",
            # growth_models.py
            "subscriptions",
            "user_limit_overrides",
            # other model files
            "nutrition_logs",
            "user_scores",
            "health_connections",
            "health_metrics",
            "user_health_indexes",
            "health_insights",
            "health_settings",
            "lifestyle_events",
            "background_jobs",
            "investment_portfolios",
            "health_scores",
        ]
        try:
            from models.database import engine
            from sqlalchemy import text

            fixed = 0
            skipped = 0
            for tbl in ALL_TABLES_WITH_USER_FK:
                try:
                    with engine.connect() as conn:
                        conn.execute(
                            text(
                                f"ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {tbl}_user_id_fkey"
                            )
                        )
                        conn.execute(
                            text(
                                f"ALTER TABLE {tbl} ADD CONSTRAINT {tbl}_user_id_fkey FOREIGN KEY (user_id) REFERENCES users_v2(id)"
                            )
                        )
                        conn.commit()
                        fixed += 1
                except Exception as e:
                    skipped += 1
                    logger.debug(f"FK fix skipped for {tbl}: {e}")

            # Fix missing columns
            try:
                queries = [
                    "ALTER TABLE time_scores_v2 ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 0.0",
                    "ALTER TABLE time_scores_v2 ADD COLUMN IF NOT EXISTS structure_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE time_scores_v2 ADD COLUMN IF NOT EXISTS load_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE time_scores_v2 ADD COLUMN IF NOT EXISTS focus_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE time_scores_v2 ADD COLUMN IF NOT EXISTS friction_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE time_scores_v2 ADD COLUMN IF NOT EXISTS stress_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE viv_indexes ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 1.0",
                    "ALTER TABLE viv_indexes ADD COLUMN IF NOT EXISTS snapshot_reason TEXT",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS cashflow_stability_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS bills_coverage_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS discretionary_control_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS savings_rate_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS emergency_buffer_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS debt_load_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS networth_momentum_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS investment_health_score FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS total_monthly_income FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS total_monthly_expenses FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS total_monthly_bills FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS total_monthly_savings FLOAT DEFAULT 0.0",
                    "ALTER TABLE financial_scores ADD COLUMN IF NOT EXISTS total_assets_value FLOAT DEFAULT 0.0",
                    "ALTER TABLE recurring_bills ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'active'",
                    "ALTER TABLE recurring_bills ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE",
                ]
                for q in queries:
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(q))
                            conn.commit()
                    except Exception as sqle:
                        logger.debug(f"Column add skipped: {sqle}")
            except Exception:
                pass

            # ----------------------------------------------------------------
            # DATA NORMALIZATION: onboarding_status
            # A seed script historically wrote the invalid value "COMPLETED",
            # but every gate in the app checks for exactly "COMPLETE". Users
            # seeded that way (e.g. super@helm.com) were wrongly forced back
            # into onboarding despite having full data. Normalize idempotently.
            # ----------------------------------------------------------------
            try:
                with engine.connect() as conn:
                    result = conn.execute(
                        text(
                            "UPDATE users_v2 SET onboarding_status = 'COMPLETE' "
                            "WHERE onboarding_status = 'COMPLETED'"
                        )
                    )
                    conn.commit()
                    if getattr(result, "rowcount", 0):
                        logger.info(
                            f"Normalized onboarding_status 'COMPLETED'->'COMPLETE' "
                            f"for {result.rowcount} user(s)"
                        )
            except Exception as norm_e:
                logger.debug(f"onboarding_status normalization skipped: {norm_e}")

            logger.info(
                f"FK migration & schema sync completed: {fixed} tables fixed, {skipped} skipped"
            )
        except Exception as e:
            logger.warning(f"FK migration failed: {e}")

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
        host="0.0.0.0",  # nosec B104
        port=int(os.environ.get("PORT", 8003)),
        reload=True,
    )
# Force Reload Triggered by Agent
