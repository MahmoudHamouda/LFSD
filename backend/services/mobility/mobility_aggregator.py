"""
Mobility Aggregator - Unified interface for all mobility providers.

Provides concurrent price comparison, idempotent booking, and
lifecycle management for Uber and RTA.
"""

import asyncio
import uuid
import logging
from typing import Dict, Any, List, Optional, Sequence
from datetime import datetime, timezone

from .base_mobility_service import BaseMobilityService
from .uber_service import UberService
from .rta_service import RTAService

from sqlalchemy.orm import Session
from models.models import Order, FinancialTransaction
from services.audit_service import AuditService

logger = logging.getLogger(__name__)


class MobilityAggregator:
    """
    Unified aggregator for mobility services.
    Handles concurrency, deduplication, and financial reconciliation.
    """

    def __init__(self):
        """Initialize and register mobility providers."""
        self.providers: Dict[str, BaseMobilityService] = {
            "uber": UberService(),
            "rta": RTAService(),
        }

    def _validate_location(self, lat: float, lng: float, label: str):
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise ValueError(f"Invalid {label} coordinates: {lat}, {lng}")

    async def compare_prices(
        self,
        user_id: str,
        start_lat: float,
        start_lng: float,
        end_lat: float,
        end_lng: float,
        provider_keys: Optional[List[str]] = None,
        currency: str = "AED",
    ) -> Dict[str, Any]:
        """
        Query multiple providers concurrently and aggregate results.
        """
        # 1. Validation
        self._validate_location(start_lat, start_lng, "start")
        self._validate_location(end_lat, end_lng, "end")
        if start_lat == end_lat and start_lng == end_lng:
            raise ValueError("Start and end locations cannot be the same")

        # 2. Filter Providers
        requested_keys = [k.lower() for k in (provider_keys or self.providers.keys())]
        missing = [k for k in requested_keys if k not in self.providers]
        if missing:
            logger.warning(f"Requested unknown providers: {missing}")

        to_query = {k: self.providers[k] for k in requested_keys if k in self.providers}

        # 3. Concurrent Execution
        tasks = []
        for name, svc in to_query.items():
            tasks.append(
                self._safe_query(
                    name, svc, start_lat, start_lng, end_lat, end_lng, user_id, currency
                )
            )

        raw_results = await asyncio.gather(*tasks)
        results = {name: res for name, res in raw_results}

        # 4. Format & Sort
        return self._format_comparison(results, currency)

    async def _safe_query(
        self, name: str, service: BaseMobilityService, *args
    ) -> tuple:
        """Execute provider query with timeout and error capture."""
        try:
            # We assume the service's get_price_estimates handles its own internal timeouts,
            # but we guard the aggregator loop too.
            res = await asyncio.wait_for(
                service.get_price_estimates(*args), timeout=15.0
            )
            return (name, res)
        except Exception as e:
            logger.error(f"Aggregator failure for {name}: {e}", exc_info=True)
            return (
                name,
                {
                    "success": False,
                    "error": f"Provider {name} unreachable",
                    "prices": [],
                },
            )

    async def book_ride(
        self,
        user_id: str,
        provider: str,
        ride_type: str,
        start_location: Dict[str, Any],
        end_location: Dict[str, Any],
        db: Session,
        idempotency_key: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute an idempotent ride booking with financial reconciliation.
        """
        provider_key = provider.lower()
        svc = self.providers.get(provider_key)
        if not svc:
            return {"success": False, "error": f"Provider '{provider}' not supported"}

        # 1. Idempotency Check (Scoped to user and provider)
        if idempotency_key:
            existing = (
                db.query(Order)
                .filter(
                    Order.idempotency_key == idempotency_key, Order.user_id == user_id
                )
                .first()
            )
            if existing:
                if existing.status == "CONFIRMED":
                    return {
                        "success": True,
                        "ride_id": existing.external_order_id,
                        "is_idempotent": True,
                    }
                if existing.status == "PENDING":
                    return {
                        "success": False,
                        "error": "Ride booking is already in progress",
                    }
                # If FAILED, we might allow a retry depending on business rules, but usually we'd want a new key.

        # 2. Persist Intent (PENDING Order)
        order = Order(
            id=str(uuid.uuid4()),
            user_id=user_id,
            provider=provider_key,
            service_type="mobility",
            status="PENDING",
            idempotency_key=idempotency_key,
            details_json={
                "start": self._sanitize_location(start_location),
                "end": self._sanitize_location(end_location),
                "requested_type": ride_type,
            },
        )
        db.add(order)
        db.commit()  # Commit PENDING state immediately to block races

        try:
            # Sanitize kwargs for the provider
            provider_kwargs = {
                k: v for k, v in kwargs.items() if k not in ["db", "idempotency_key"]
            }

            response = await svc.book_ride(
                user_id, ride_type, start_location, end_location, **provider_kwargs
            )

            if response.get("success"):
                # 3. Reconcile Success
                order.status = "CONFIRMED"
                order.external_order_id = (
                    response.get("ride_id")
                    or response.get("ticket_id")
                    or response.get("id")
                )

                # Extract cost reliably (handle strings/missing values)
                raw_cost = (
                    response.get("estimated_cost")
                    or response.get("details", {}).get("cost")
                    or 0.0
                )
                if isinstance(raw_cost, str):
                    import re

                    numeric = re.search(r"(\d+\.?\d*)", raw_cost)
                    order.amount_estimated = float(numeric.group(1)) if numeric else 0.0
                else:
                    order.amount_estimated = float(raw_cost)

                # 4. Create Transaction (Negative amount for expenses)
                if order.amount_estimated > 0:
                    tx = FinancialTransaction(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        amount=-abs(
                            order.amount_estimated
                        ),  # Absolute negative for expense
                        currency_code=response.get("currency", "AED"),
                        description=f"{provider.title()} Ride: {ride_type}",
                        transaction_date=datetime.now(timezone.utc),
                    )
                    db.add(tx)
                    db.flush()
                    order.transaction_id = tx.id

                db.commit()

                # 5. Audit confirmed state
                AuditService.log_audit(
                    db=db,
                    actor_id=user_id,
                    action="CONFIRM_ORDER",
                    entity_type="ORDER",
                    entity_id=order.id,
                    changes={"status": "CONFIRMED", "ride_id": order.external_order_id},
                )
                db.commit()  # Persist Audit

                return response
            else:
                # 6. Reconcile Failure
                order.status = "FAILED"
                order.error_message = response.get("error", "Provider declined booking")
                db.commit()
                return response

        except Exception as e:
            logger.error(f"Booking crash for {provider}: {e}", exc_info=True)
            db.rollback()
            order.status = "FAILED"
            order.error_message = f"Internal Engine Error: {str(e)}"
            db.commit()
            return {"success": False, "error": str(e)}

    def _sanitize_location(self, loc: Dict[str, Any]) -> Dict[str, Any]:
        """Redact detailed address for log storage if needed, keep coords."""
        return {
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "address_redacted": bool(loc.get("address")),
        }

    def _format_comparison(
        self, results: Dict[str, Any], currency: str
    ) -> Dict[str, Any]:
        all_options = []
        queried_count = 0

        for provider, data in results.items():
            if data.get("success"):
                queried_count += 1
                for price in data.get("prices", []):
                    all_options.append(
                        {
                            "provider": provider,
                            "ride_type": price.get("localized_display_name")
                            or price.get("display_name"),
                            "estimate": price.get("estimate"),
                            "low_estimate": float(price.get("low_estimate", 0)),
                            "high_estimate": float(price.get("high_estimate", 0)),
                            "duration_sec": int(price.get("duration", 0)),
                            "distance_km": float(price.get("distance", 0)),
                            "currency": price.get("currency", currency),
                            "mock": data.get("mock", False),
                        }
                    )

        # Sort: Remove 0-price from top unless actually 0, then sort by low estimate
        all_options.sort(key=lambda x: (x["low_estimate"] == 0, x["low_estimate"]))

        return {
            "options": all_options,
            "cheapest": all_options[0] if all_options else None,
            "provider_query_count": len(results),
            "successful_provider_count": queried_count,
        }

    async def book_cheapest_ride(
        self,
        user_id: str,
        start_location: Dict[str, Any],
        end_location: Dict[str, Any],
        db: Session,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Compare prices and book the cheapest option.
        """
        comparison = await self.compare_prices(
            user_id=user_id,
            start_lat=start_location["lat"],
            start_lng=start_location["lng"],
            end_lat=end_location["lat"],
            end_lng=end_location["lng"]
        )
        cheapest = comparison.get("cheapest")
        if not cheapest:
            return {"success": False, "error": "No ride options found"}

        return await self.book_ride(
            user_id=user_id,
            provider=cheapest["provider"],
            ride_type=cheapest["ride_type"],
            start_location=start_location,
            end_location=end_location,
            db=db,
            **kwargs
        )


# Internal factory instead of singleton to avoid stale state in long-running procs
def get_mobility_aggregator() -> MobilityAggregator:
    return MobilityAggregator()

