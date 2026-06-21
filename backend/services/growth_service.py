from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from models.growth_models import Subscription, TierConfig, UserLimitOverride
from models.growth_schemas import PlanId, EntitlementResponse
from models.models import User, LifeGoal, DBMessage, Recommendation
from models.logging_models import AuditLog
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import uuid
import copy
from loguru import logger

class GrowthService:
    @staticmethod
    def get_entitlements(user_id: str, db: Session) -> EntitlementResponse:
        logger.debug(f"Growth: Fetching entitlements for {user_id}")
        
        # 1. Fetch Subscription (Prioritize Active)
        # Using filter over 'active' ensures we don't fall back to an expired PRO plan when it should be FREE
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id, 
            Subscription.status == "active"
        ).first()

        # Handle expiration logic explicitly (treat NULL end_date as expired per audit reqs)
        if subscription:
            if not subscription.current_period_end or subscription.current_period_end < datetime.utcnow():
                subscription = None
        
        plan_id = PlanId.FREE
        status = "active" # Free is always active
        
        if subscription:
            # Type safety for PlanId
            try:
                plan_id = PlanId(subscription.plan_id)
            except ValueError:
                logger.warning(f"Invalid plan_id {subscription.plan_id} for user {user_id}, falling back to FREE")
                plan_id = PlanId.FREE
                
            status = subscription.status
            
        logger.debug(f"Growth: Plan={plan_id}, Status={status}")

        # 2. Fetch Global Tier Config (or fallback)
        tier = db.query(TierConfig).filter(TierConfig.plan_id == plan_id).first()
        
        base_config = {}
        if tier:
            # Must DEEP COPY to prevent mutation of cached/DB objects in memory
            base_config = copy.deepcopy(tier.config_json)
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
            # Deep copy here too
            base_config = copy.deepcopy(PLAN_CONFIGS.get(plan_id, PLAN_CONFIGS[PlanId.FREE]))

        # 3. Apply User-Specific Overrides (Validated)
        override = db.query(UserLimitOverride).filter(
            UserLimitOverride.user_id == user_id,
            or_(
                UserLimitOverride.expiration_date.is_(None),
                UserLimitOverride.expiration_date >= datetime.utcnow()
            )
        ).first()
        
        if override and "limits" in base_config:
            for key, val in override.overrides_json.items():
                if key in base_config["limits"]:
                    # Ensure positive integers only for limits (or -1)
                    if isinstance(val, int) and (val >= -1):
                        base_config["limits"][key] = val
                    else:
                        logger.warning(f"Invalid override value {val} for key {key} user {user_id}")

        # 4. Calculate Actual Usage (Optimized with Indices)
        usage = {}
        first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Goals: Total goals
        usage["goals"] = db.query(LifeGoal).filter(
            LifeGoal.user_id == user_id
        ).count()
        
        # AI Chat: Messages sent by user this month 
        # Note: Counting messages != 'calls' in all models, but it's our chosen proxy for now.
        # Ensure index exists on (user_id, date) or (user_id, role, date) for performance
        usage["ai_chat_calls"] = db.query(DBMessage).filter(
            DBMessage.user_id == user_id,
            DBMessage.role == "user",
            DBMessage.date >= first_of_month
        ).count()
        
        # Token usage 
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
        # Count only if configured, otherwise skip distinct count for performance
        if base_config["limits"].get("executions", 0) != 0:
            usage["executions"] = db.query(AuditLog).filter(
                AuditLog.actor_id == user_id,
                AuditLog.action == "EXECUTE",
                AuditLog.timestamp >= first_of_month
            ).count()
        else:
             usage["executions"] = 0

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
        # Validate Plan ID
        try:
             validated_plan = PlanId(plan_id)
        except ValueError:
             raise ValueError(f"Invalid Plan ID: {plan_id}")

        # Check existing (potentially including expired/cancelled to reactivate)
        existing_sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        
        now = datetime.utcnow()
        period_end = now + timedelta(days=30)
        
        if existing_sub:
            existing_sub.plan_id = validated_plan
            existing_sub.status = "active"
            existing_sub.current_period_start = now
            existing_sub.current_period_end = period_end
            existing_sub.cancel_at_period_end = False # Reset cancel
            
            db.commit()
            db.refresh(existing_sub)
            return existing_sub
        else:
            new_sub = Subscription(
                id=str(uuid.uuid4()),
                user_id=user_id,
                plan_id=validated_plan,
                status="active",
                current_period_start=now,
                current_period_end=period_end
            )
            db.add(new_sub)
            db.commit()
            db.refresh(new_sub)
            return new_sub
