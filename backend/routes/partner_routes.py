"""
Partner service endpoints.

This module contains endpoints related to partner integrations. All endpoints
require authentication and may be rate limited. Replace stub logic with
real partner onboarding and management features.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from core.authentication import get_current_user
from core.rate_limiting import limiter


router = APIRouter(prefix="/partners", tags=["Partners"])


@router.get("/", summary="List partners")
@limiter.limit("10/minute")
async def list_partners(
    *,
    current_user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated list of partners."""
    """Return a paginated list of partners."""
    return {
        "data": {
            "items": [
                {
                    "id": "p1",
                    "name": "Uber",
                    "category": "Transportation",
                    "description": "Get a ride in minutes.",
                    "status": "active"
                },
                {
                    "id": "p2",
                    "name": "Talabat",
                    "category": "Food Delivery",
                    "description": "Order food from your favorite restaurants.",
                    "status": "active"
                }
            ],
            "next_cursor": None
        }
    }


@router.post("/{partner_id}/connect", summary="Connect a partner")
@limiter.limit("5/minute")
async def connect_partner(
    partner_id: str,
    current_user=Depends(get_current_user)
) -> dict[str, Any]:
    """Connect a partner integration."""
    # In a real app, this would trigger OAuth or API key validation
    return {
        "success": True,
        "data": {
            "id": partner_id,
            "status": "active",
            "message": f"Successfully connected to {partner_id}"
        }
    }


@router.post("/{partner_id}/disconnect", summary="Disconnect a partner")
@limiter.limit("5/minute")
async def disconnect_partner(
    partner_id: str,
    current_user=Depends(get_current_user)
) -> dict[str, Any]:
    """Disconnect a partner integration."""
    return {
        "success": True,
        "data": {
            "id": partner_id,
            "status": "inactive",
            "message": f"Successfully disconnected from {partner_id}"
        }
    }


@router.put("/{partner_id}/permissions", summary="Update partner permissions")
@limiter.limit("10/minute")
async def update_partner_permissions(
    partner_id: str,
    permissions: dict[str, bool],
    current_user=Depends(get_current_user)
) -> dict[str, Any]:
    """Update permissions for a partner."""
    return {
        "success": True,
        "data": {
            "id": partner_id,
            "permissions": permissions,
            "message": "Permissions updated"
        }
    }

@router.get("/inventory", summary="Get partner inventory")
@limiter.limit("20/minute")
async def get_inventory(
    type: str = Query(..., description="Type of inventory (e.g., car)"),
    budget_max: Optional[float] = Query(None),
    city: Optional[str] = Query(None),
    current_user=Depends(get_current_user)
) -> dict[str, Any]:
    """
    Return real inventory rows only.
    If no partners / empty inventory, return baseline estimates.
    """
    if type == "car":
        # Mock Partner Inventory Logic
        # In a real scenario, this would query a partner API or DB
        
        # 1. Partner Inventory (simulated empty for now to trigger baseline)
        partner_inventory = [] 
        
        if partner_inventory:
            return {"data": partner_inventory}
            
        # 2. Baseline Internal Inventory (Fallback)
        # "Entry sedan", "Used compact", "Basic SUV (used)"
        baselines = [
            {
                "id": "base_1",
                "name": "Used Honda Civic (2018-2020)",
                "price_range": "40k - 55k AED",
                "estimated_monthly_all_in": "1200 - 1500 AED",
                "why_fit": "High reliability, low maintenance, excellent resale value.",
                "source": "baseline",
                "spec": "Used Compact"
            },
            {
                "id": "base_2",
                "name": "New Nissan Sunny (2024)",
                "price_range": "60k - 70k AED",
                "estimated_monthly_all_in": "1600 - 1900 AED",
                "why_fit": "Cheapest new car entry point, full warranty coverage.",
                "source": "baseline",
                "spec": "Entry Sedan"
            },
            {
                "id": "base_3",
                "name": "Used Toyota RAV4 (2015-2017)",
                "price_range": "50k - 65k AED",
                "estimated_monthly_all_in": "1400 - 1800 AED",
                "why_fit": "Reliable SUV, good for families, strong durability.",
                "source": "baseline",
                "spec": "Basic SUV (Used)"
            }
        ]
        
        # Filter by budget if provided (simple string parsing simulation)
        # For this mock, we just return all baselines
        
        return {"data": baselines}
        
    return {"data": []}
