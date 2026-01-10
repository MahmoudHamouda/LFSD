from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PlanId(str):
    FREE = "tier_free"
    PLUS = "tier_plus"
    PRO = "tier_pro"
    ENTERPRISE = "tier_enterprise"

class SubscriptionBase(BaseModel):
    plan_id: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    provider: Optional[str] = None

class SubscriptionCreate(BaseModel):
    plan_id: str
    payment_method_id: Optional[str] = None

class SubscriptionResponse(SubscriptionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EntitlementResponse(BaseModel):
    plan: str
    status: str
    features: List[str]
    limits: Dict[str, Any]
    usage: Dict[str, Any] = Field(default_factory=dict)
