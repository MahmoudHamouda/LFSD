from backend.models.database import SessionLocal, get_db
from backend.models.models import User
from backend.models.growth_models import Subscription, TierConfig
from backend.models.growth_schemas import PlanId
from datetime import datetime, timedelta
import uuid

def seed_test_user():
    db = SessionLocal()
    try:
        user_id = "verify-user-123"
        email = "verify@lfsd.com"
        
        # 1. Ensure User exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"Creating user {user_id}")
            user = User(
                id=user_id,
                email=email,
                onboarding_status="COMPLETE",
                role="user"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # 2. Ensure TierConfigs exist (Basic ones)
        plans = [
            (PlanId.FREE, "Free Plan", {"ai_chat_calls": 10, "total_tokens_month": 50000}),
            (PlanId.PLUS, "Plus Plan", {"ai_chat_calls": 50, "total_tokens_month": 500000}),
            (PlanId.PRO, "Pro Plan", {"ai_chat_calls": 200, "total_tokens_month": 2000000})
        ]
        
        for plan_id, name, config in plans:
            tier = db.query(TierConfig).filter(TierConfig.plan_id == plan_id).first()
            if not tier:
                print(f"Creating tier {plan_id}")
                tier = TierConfig(
                    plan_id=plan_id,
                    name=name,
                    config_json=config
                )
                db.add(tier)
        
        db.commit()
        
        # 3. Ensure Subscription exists for user
        sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        if not sub:
            print(f"Creating subscription for {user_id}")
            sub = Subscription(
                id=str(uuid.uuid4()),
                user_id=user_id,
                plan_id=PlanId.PLUS,
                status="active",
                current_period_end=datetime.utcnow() + timedelta(days=30)
            )
            db.add(sub)
            db.commit()
        
        print("✅ Seeding successful.")
        
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_user()
