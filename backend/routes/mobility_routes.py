"""
Mobility API Routes

Provides REST API endpoints for mobility services including price comparison,
ride booking, and ride tracking across multiple providers.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional, Dict, Any
from pydantic import BaseModel
from core.authentication import get_current_user
from core.rate_limiting import limiter
from services.mobility.mobility_aggregator import get_mobility_aggregator
from models.database import get_db
from sqlalchemy.orm import Session


router = APIRouter(prefix="/mobility", tags=["Mobility"])


# Request/Response Models
class LocationModel(BaseModel):
    """Location model for ride requests."""

    lat: float
    lng: float
    address: Optional[str] = None


class BookRideRequest(BaseModel):
    """Request model for booking a ride."""

    provider: str
    ride_type: str
    start_location: LocationModel
    end_location: LocationModel
    options: Optional[Dict[str, Any]] = None


@router.get("/compare-prices", summary="Compare prices across providers")
@limiter.limit("30/minute")
async def compare_prices(
    request: Request,
    start_lat: float = Query(..., description="Starting latitude"),
    start_lng: float = Query(..., description="Starting longitude"),
    end_lat: float = Query(..., description="Ending latitude"),
    end_lng: float = Query(..., description="Ending longitude"),
    providers: Optional[str] = Query(
        None, description="Comma-separated list of providers (uber,careem,bolt)"
    ),
    current_user=Depends(get_current_user),
):
    """
    Compare ride prices across multiple mobility providers.
    """
    aggregator = get_mobility_aggregator()

    provider_list = providers.split(",") if providers else None

    try:
        results = await aggregator.compare_prices(
            current_user.id, start_lat, start_lng, end_lat, end_lng, provider_list
        )

        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cheapest", summary="Get cheapest ride option")
@limiter.limit("30/minute")
async def get_cheapest(
    request: Request,
    start_lat: float = Query(..., description="Starting latitude"),
    start_lng: float = Query(..., description="Starting longitude"),
    end_lat: float = Query(..., description="Ending latitude"),
    end_lng: float = Query(..., description="Ending longitude"),
    providers: Optional[str] = Query(
        None, description="Comma-separated list of providers"
    ),
    current_user=Depends(get_current_user),
):
    """
    Get the cheapest ride option across all providers.
    """
    aggregator = get_mobility_aggregator()

    provider_list = providers.split(",") if providers else None

    try:
        comparison = await aggregator.compare_prices(
            current_user.id, start_lat, start_lng, end_lat, end_lng, provider_list
        )
        cheapest = comparison.get("cheapest")

        if not cheapest:
            return {"success": False, "message": "No ride options available"}

        return {"success": True, "data": cheapest}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book-ride", summary="Book a ride")
@limiter.limit("10/minute")
async def book_ride(
    request: Request,
    body: BookRideRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Book a ride with a specific provider.
    """
    aggregator = get_mobility_aggregator()

    try:
        result = await aggregator.book_ride(
            current_user.id,
            body.provider,
            body.ride_type,
            body.start_location.dict(),
            body.end_location.dict(),
            db,
            **(body.options or {})
        )

        return {"success": result.get("success", False), "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book-cheapest", summary="Book the cheapest ride")
@limiter.limit("10/minute")
async def book_cheapest(
    request: Request,
    start_location: LocationModel,
    end_location: LocationModel,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Automatically compare prices and book the cheapest option.
    """
    aggregator = get_mobility_aggregator()

    try:
        result = await aggregator.book_cheapest_ride(
            current_user.id, start_location.dict(), end_location.dict(), db
        )

        return {"success": result.get("success", False), "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ride-status/{provider}/{ride_id}", summary="Get ride status")
@limiter.limit("60/minute")
async def get_ride_status(
    request: Request,
    provider: str,
    ride_id: str,
    current_user=Depends(get_current_user),
):
    """
    Get the current status of an active ride.
    """
    aggregator = get_mobility_aggregator()

    try:
        status = await aggregator.get_ride_status(current_user.id, provider, ride_id)

        return {"success": status.get("success", False), "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers", summary="List available providers")
async def list_providers():
    """
    Get list of available mobility providers.
    """
    aggregator = get_mobility_aggregator()

    return {"success": True, "providers": list(aggregator.providers.keys())}
