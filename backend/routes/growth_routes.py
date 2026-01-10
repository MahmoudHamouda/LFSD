from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db
from models.growth_schemas import EntitlementResponse, SubscriptionResponse, SubscriptionCreate
from services.growth_service import GrowthService
from models.models import User
from models.logging_models import ActivityFeed, AuditLog # Use AuditLog for business events
from datetime import datetime
import uuid
from core.authentication import get_current_user

router = APIRouter(prefix="/growth", tags=["Growth"])

@router.get("/entitlements", response_model=EntitlementResponse)
def get_my_entitlements(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Get the current user's entitlements (features and limits) based on their subscription plan.
    """
    try:
        print(f"DEBUG: ROUTE get_my_entitlements for {current_user.id}")
        return GrowthService.get_entitlements(current_user.id, db)
    except Exception as e:
        print(f"ERROR in get_my_entitlements: {e}")
        import traceback
        traceback.print_exc()
        raise e

@router.post("/subscribe", response_model=SubscriptionResponse)
def subscribe_to_plan(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upgrade or downgrade the user's subscription plan.
    This action is logged in the Audit Trail and Activity Feed.
    """
    # 1. Update Subscription
    subscription = GrowthService.create_or_upgrade_subscription(
        current_user.id, 
        subscription_data.plan_id, 
        db
    )
    
    # 2. Emit ActivityFeed Event (Contract)
    feed_event = ActivityFeed(
        user_id=current_user.id,
        action_type="SUBSCRIPTION_UPDATED",
        description=f"User upgraded to {subscription_data.plan_id}",
        metadata_json={"plan": subscription_data.plan_id},
        created_at=datetime.utcnow()
    )
    db.add(feed_event)
    
    # 3. Emit Audit Event (Audit Log)
    audit_log = AuditLog(
        actor_id=current_user.id,
        actor_type="user",
        action="UPDATE",
        entity_type="Subscription",
        entity_id=subscription.id,
        changes_json={"plan_id": subscription_data.plan_id},
        metadata_json={"description": f"User subscribed to {subscription_data.plan_id}"}
    )
    db.add(audit_log)
    
    db.commit()
    
    return subscription
