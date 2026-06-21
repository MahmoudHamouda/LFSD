"""
Admin service endpoints.

This module defines routes related to the admin domain. Endpoints require
authentication via JWT and are rate limited.
"""

from typing import Any, Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Body, Request
from sqlalchemy.orm import Session

from core.authentication import get_current_user
from models.database import get_db
from services.admin_service import AdminService
from services.growth_service import GrowthService
from services.billing_service import BillingService
from models.growth_models import TierConfig, UserLimitOverride, Subscription
from core.rate_limiting import limiter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])


# Pydantic Models for Response
class UserOut(BaseModel):
    id: str
    email: str
    account_status: str
    created_at: datetime

    class Config:
        orm_mode = True


class UnlockRequest(BaseModel):
    user_id: str
    reason: str


class AuditLogOut(BaseModel):
    id: str
    timestamp: datetime
    actor_id: Optional[str]
    action: str
    entity_type: str
    entity_id: str
    changes_json: Optional[dict]

    class Config:
        orm_mode = True


@router.get("/users", summary="List users", response_model=List[UserOut])
@limiter.limit("20/minute")
async def list_users(
    *,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    """
    List users with status.
    """
    # Verify Admin
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    service = AdminService(db)
    users = service.get_users(skip=skip, limit=limit)
    return users


@router.post("/unlock", summary="Unlock User")
@limiter.limit("5/minute")
async def unlock_user(
    *,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    payload: UnlockRequest,
) -> Any:
    """
    Unlock a locked user.
    """
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    service = AdminService(db)
    try:
        user = service.unlock_user(
            target_user_id=payload.user_id,
            admin_user_id=current_user.id,
            reason=payload.reason,
        )
        return {
            "status": "success",
            "user_id": user.id,
            "account_status": user.account_status,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/audit", summary="List audit logs", response_model=List[AuditLogOut])
@limiter.limit("20/minute")
async def list_audits(
    *,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    """Return a list of recent audit logs."""
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    service = AdminService(db)
    logs = service.get_audit_logs(limit=limit)
    return logs


# --- Subscription & Tier Management ---


class TierUpdate(BaseModel):
    name: Optional[str]
    config_json: dict


@router.get("/tiers", summary="List all subscription tiers")
async def list_tiers(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(TierConfig).all()


@router.put("/tiers/{plan_id}", summary="Update a subscription tier")
async def update_tier(
    plan_id: str,
    payload: TierUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    tier = db.query(TierConfig).filter(TierConfig.plan_id == plan_id).first()
    if not tier:
        # Create if not exists (for seeding)
        tier = TierConfig(
            plan_id=plan_id,
            name=payload.name or plan_id,
            config_json=payload.config_json,
        )
        db.add(tier)
    else:
        if payload.name:
            tier.name = payload.name
        tier.config_json = payload.config_json

    db.commit()
    db.refresh(tier)
    return tier


@router.get("/users/{user_id}/limits", summary="Get user limits and overrides")
async def get_user_limits(
    user_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    entitlements = GrowthService.get_entitlements(user_id, db)
    override = (
        db.query(UserLimitOverride).filter(UserLimitOverride.user_id == user_id).first()
    )

    return {
        "user_id": user_id,
        "plan": entitlements.plan,
        "current_limits": entitlements.limits,
        "overrides": override.overrides_json if override else {},
    }


@router.post("/users/{user_id}/limits", summary="Set user limit overrides")
async def set_user_limits(
    user_id: str,
    payload: dict = Body(..., example={"ai_queries_per_day": 100}),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    override = (
        db.query(UserLimitOverride).filter(UserLimitOverride.user_id == user_id).first()
    )
    if not override:
        override = UserLimitOverride(user_id=user_id, overrides_json=payload)
        db.add(override)
    else:
        override.overrides_json = payload

    db.commit()
    return {"status": "success", "overrides": override.overrides_json}


@router.put("/users/{user_id}/tier", summary="Update user subscription tier")
async def update_user_tier(
    user_id: str,
    plan_id: str = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    sub = GrowthService.create_or_upgrade_subscription(user_id, plan_id, db)
    return {"status": "success", "plan_id": sub.plan_id}


# --- Billing & Reconciliation ---


@router.get("/billing/summary", summary="Get overall revenue and cost summary")
async def get_billing_summary(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    service = BillingService(db)
    return service.get_overall_summary()


@router.get("/billing/customers", summary="Get per-customer revenue and cost")
async def get_customer_billing(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    service = BillingService(db)
    return service.get_customer_reconciliation()


@router.get("/billing/apis", summary="Get per-API integration costs")
async def get_api_billing(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    service = BillingService(db)
    return service.get_api_integration_costs()
