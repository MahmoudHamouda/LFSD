from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from models.growth_models import Subscription, TierConfig, UserLimitOverride
from models.growth_schemas import PlanId, EntitlementResponse
from models.database import SessionLocal 
from models.models import User, LifeGoal, DBMessage, Recommendation
from models.logging_models import AuditLog
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from services.chat_service.models import ChatHistory
from loguru import logger

class GrowthService:
    @staticmethod
    def get_entitlements(user_id: str, db: Session) -> EntitlementResponse:
        logger.debug(f"Growth: Fetching entitlements for {user_id}")
        # 1. Fetch Subscription
        subscription = db.query(Subscription).filter(Subscription.user_id == user_id, Subscription.status == "active").first()
        
        plan_id = PlanId.FREE
        status = "active"
        if subscription:
            plan_id = subscription.plan_id
            status = subscription.status
        logger.debug(f"Growth: Plan={plan_id}, Status={status}")

        # 2. Fetch Global Tier Config
        tier = db.query(TierConfig).filter(TierConfig.plan_id == plan_id).first()
        # logger.debug(f"Growth: Tier Config Found={bool(tier)}")
        
        # Fallback to defaults if DB config not seeded yet
        if tier:
            base_config = tier.config_json
        else:
            # Plan Config Table
            PLAN_CONFIGS = {
                PlanId.FREE: {
                    "features": ["basic_charts", "limit_5_goals", "basic_insight"],
                    "limits": {
                        "goals": 5,
                        "ai_chat_calls": 100,
                        "smart_recos": 10,
                        "executions": -1,
                        "history_months": 3
                    }
                },
                PlanId.PLUS: {
                    "features": ["advanced_charts", "unlimited_goals", "limited_executions"],
                    "limits": {
                        "goals": -1,
                        "ai_chat_calls": 500,
                        "smart_recos": 100,
                        "executions": 20,
                        "history_months": 12
                    }
                },
                PlanId.PRO: {
                    "features": ["advanced_charts", "unlimited_goals", "deep_insight", "forecasting", "priority_support"],
                    "limits": {
                        "goals": -1,
                        "ai_chat_calls": 2000,
                        "smart_recos": 500,
                        "executions": 100,
                        "history_months": -1
                    }
                },
                PlanId.ENTERPRISE: {
                    "features": ["all_features", "sla", "audit_logs", "custom_integrations"],
                    "limits": {
                        "goals": -1,
                        "ai_chat_calls": -1,
                        "smart_recos": -1,
                        "executions": -1,
                        "history_months": -1
                    }
                }
            }
            base_config = PLAN_CONFIGS.get(plan_id, PLAN_CONFIGS[PlanId.FREE])

        # 3. Apply User-Specific Overrides
        override = db.query(UserLimitOverride).filter(UserLimitOverride.user_id == user_id).first()
        if override and "limits" in base_config:
            # Overwrite specific keys in limits
            for key, val in override.overrides_json.items():
                if key in base_config["limits"]:
                    base_config["limits"][key] = val

        # 4. Calculate Actual Usage
        usage = {}
        
        # Goals: Total goals
        usage["goals"] = db.query(LifeGoal).filter(
            LifeGoal.user_id == user_id
        ).count()
        
        # AI Chat: Messages sent by user this month (Using DBMessage/messages table)
        first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage["ai_chat_calls"] = db.query(DBMessage).filter(
            DBMessage.user_id == user_id,
            DBMessage.role == "user",
            DBMessage.date >= first_of_month
        ).count()
        
        # Token usage (Growth Agent)
        token_stats = db.query(
            func.sum(DBMessage.input_tokens).label("input"),
            func.sum(DBMessage.output_tokens).label("output")
        ).filter(
            DBMessage.user_id == user_id,
            DBMessage.date >= first_of_month
        ).first()
        
        input_tokens = getattr(token_stats, "input", 0) or 0
        output_tokens = getattr(token_stats, "output", 0) or 0
        usage["total_tokens_month"] = input_tokens + output_tokens
        
        # Smart Recommendations: Created this month
        usage["smart_recos"] = db.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.timestamp >= first_of_month
        ).count()
        
        # Executions: creation of specific entities or audit logs
        # For now, count AuditLog "EXECUTE" actions this month
        usage["executions"] = db.query(AuditLog).filter(
            AuditLog.actor_id == user_id,
            AuditLog.action == "EXECUTE",
            AuditLog.timestamp >= first_of_month
        ).count()

        res = EntitlementResponse(
            plan=plan_id,
            status=status,
            features=base_config.get("features", []),
            limits=base_config.get("limits", {}),
            usage=usage
        )
        return res

    @staticmethod
    def create_or_upgrade_subscription(user_id: str, plan_id: str, db: Session) -> Subscription:
        # Check existing
        existing_sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        
        if existing_sub:
            existing_sub.plan_id = plan_id
            existing_sub.status = "active"
            existing_sub.current_period_start = datetime.utcnow()
            existing_sub.current_period_end = datetime.utcnow() + timedelta(days=30) # Mock 30 day cycle
            db.commit()
            db.refresh(existing_sub)
            return existing_sub
        else:
            new_sub = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                status="active",
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30)
            )
            db.add(new_sub)
            db.commit()
            db.refresh(new_sub)
            return new_sub
