"""
Mobility Aggregator - Unified interface for all mobility providers.

This module provides a single interface to interact with multiple mobility
providers (Uber, Careem, Bolt, RTA) for price comparison and booking.
"""

from typing import Dict, Any, List, Optional
from .uber_service import UberService
from .careem_service import CareemService
from .bolt_service import BoltService
from .rta_service import RTAService
# from .bolt_service import BoltService
# from .rta_service import RTAService
from sqlalchemy.orm import Session
from models.models import Order, FinancialTransaction, User
from services.audit_service import AuditService
import uuid
from datetime import datetime



class MobilityAggregator:
    """Unified interface for all mobility providers."""
    
    def __init__(self):
        """Initialize all mobility provider services."""
        self.uber = UberService()
        self.careem = CareemService()
        self.bolt = BoltService()
        self.rta = RTAService()
        
        self.providers = {
            'uber': self.uber,
            'careem': self.careem,
            'bolt': self.bolt,
            'rta': self.rta
        }
    
    async def compare_prices(
        self,
        user_id: str,
        start_lat: float,
        start_lng: float,
        end_lat: float,
        end_lng: float,
        providers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get price estimates from multiple providers and compare them.
        
        Args:
            user_id: User ID for logging
            start_lat: Starting latitude
            start_lng: Starting longitude
            end_lat: Ending latitude
            end_lng: Ending longitude
            providers: List of provider names to query (None = all available)
            
        Returns:
            Dictionary with aggregated results:
            {
                "options": List[Dict],  # All options sorted by price
                "cheapest": Dict,       # Cheapest option
                "provider_count": int,  # Number of providers queried
                "providers": Dict       # Raw results per provider
            }
        """
        if providers is None:
            providers = list(self.providers.keys())
        
        results = {}
        
        # Query each provider
        for provider_name in providers:
            provider = self.providers.get(provider_name)
            if provider:
                try:
                    estimates = await provider.get_price_estimates(
                        start_lat, start_lng, end_lat, end_lng, user_id
                    )
                    results[provider_name] = estimates
                except Exception as e:
                    print(f"Error querying {provider_name}: {e}")
                    results[provider_name] = {"error": str(e)}
        
        # Format and sort results
        return self._format_comparison(results)
    
    async def get_cheapest_option(
        self,
        user_id: str,
        start_lat: float,
        start_lng: float,
        end_lat: float,
        end_lng: float,
        providers: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the cheapest ride option across all providers.
        
        Args:
            user_id: User ID
            start_lat: Starting latitude
            start_lng: Starting longitude
            end_lat: Ending latitude
            end_lng: Ending longitude
            providers: List of provider names to query
            
        Returns:
            Dictionary with cheapest option or None if no options available
        """
        comparison = await self.compare_prices(
            user_id, start_lat, start_lng, end_lat, end_lng, providers
        )
        
        return comparison.get("cheapest")
    
    async def book_ride(
        self,
        user_id: str,
        provider: str,
        ride_type: str,
        start_location: Dict[str, Any],
        end_location: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Book a ride with a specific provider.
        
        Args:
            user_id: User ID
            provider: Provider name (uber, careem, bolt)
            ride_type: Type of ride
            start_location: Dict with lat, lng, address
            end_location: Dict with lat, lng, address
            **kwargs: Provider-specific options
            
        Returns:
            Dictionary with booking details
        """
        provider_service = self.providers.get(provider.lower())
        
        if not provider_service:
            return {
                "success": False,
                "error": f"Provider '{provider}' not found or not available"
            }
        
        # 1. Create PENDING Order
        # This acts as our "intent" record. Even if the API call crashes, we know we tried.
        db = kwargs.get('db')
        order = None
        if db:
            try:
                # Check Idempotency
                idempotency_key = kwargs.get('idempotency_key')
                if idempotency_key:
                    existing = db.query(Order).filter(Order.idempotency_key == idempotency_key).first()
                    if existing:
                        print(f"Idempotency hit for key: {idempotency_key}")
                        if existing.status == 'CONFIRMED':
                            return {"success": True, "message": "Order already confirmed (Idempotent)", "order_id": existing.id, "eta": existing.details_json.get('eta')}
                        elif existing.status == 'PENDING':
                            return {"success": False, "error": "Order is currently processing"}

                order = Order(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    provider=provider,
                    service_type="mobility",
                    status="PENDING",
                    amount_estimated=0.0, # Placeholder
                    details_json={
                        "start": start_location,
                        "end": end_location,
                        "ride_type": ride_type
                    },
                    idempotency_key=idempotency_key
                )
                db.add(order)
                db.commit()
                db.refresh(order)
            except Exception as e:
                print(f"Failed to persist PENDING order: {e}")
                # We should probably fail hard here if strict governance is required
                return {"success": False, "error": "System Error: Could not initialization order record."}

        try:
            booking_response = await provider_service.book_ride(
                user_id,
                ride_type,
                start_location,
                end_location,
                **kwargs
            )
            
            # 2. Update Order Status
            if db and order:
                if booking_response.get('success'):
                    order.status = "CONFIRMED"
                    order.external_order_id = booking_response.get('ride_id') or "mock-id"
                    order.amount_estimated = float(booking_response.get('estimated_cost', 0))
                    
                    # Update details with driver info etc
                    details = order.details_json or {}
                    details.update(booking_response)
                    order.details_json = details
                    
                    # 3. Create Transaction Record (If cost is known)
                    if order.amount_estimated > 0:
                        transaction = FinancialTransaction(
                            id=str(uuid.uuid4()),
                            user_id=user_id,
                            amount=order.amount_estimated,
                            description=f"{provider.title()} Ride to {end_location.get('address', 'Destination')}",
                            merchant_name=provider.title(),
                            category_primary="Transport",
                            category_detailed="Rideshare",
                            transaction_date=datetime.utcnow()
                        )
                        db.add(transaction)
                        db.flush() # Get ID
                        order.transaction_id = transaction.id
                        
                    db.commit()
                    
                    # AUDIT: Logistics Confirmed
                    AuditService.log_audit(
                        db=db,
                        actor_id=user_id,
                        action="CONFIRM_ORDER",
                        entity_type="Order",
                        entity_id=order.id,
                        changes={"status": "CONFIRMED", "external_id": order.external_order_id}
                    )
                    
                else:
                    order.status = "FAILED"
                    order.error_message = booking_response.get('error', 'Unknown Error')
                    db.commit()
                    
                    # AUDIT: Logistics Failed
                    AuditService.log_audit(
                        db=db,
                        actor_id=user_id,
                        action="FAIL_ORDER",
                        entity_type="Order",
                        entity_id=order.id,
                        changes={"status": "FAILED", "error": order.error_message}
                    )
            
            return booking_response

        except Exception as e:
            print(f"Error booking with {provider}: {e}")
            if db and order:
                order.status = "FAILED"
                order.error_message = str(e)
                db.commit()
                
                # AUDIT: Logistics Error
                AuditService.log_audit(
                    db=db,
                    actor_id=user_id,
                    action="ERROR_ORDER",
                    entity_type="Order",
                    entity_id=order.id,
                    changes={"status": "FAILED", "exception": str(e)}
                )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def book_cheapest_ride(
        self,
        user_id: str,
        start_location: Dict[str, Any],
        end_location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare prices and book the cheapest option automatically.
        
        Args:
            user_id: User ID
            start_location: Dict with lat, lng, address
            end_location: Dict with lat, lng, address
            
        Returns:
            Dictionary with booking details
        """
        # Get cheapest option
        cheapest = await self.get_cheapest_option(
            user_id,
            start_location['lat'],
            start_location['lng'],
            end_location['lat'],
            end_location['lng']
        )
        
        if not cheapest:
            return {
                "success": False,
                "error": "No ride options available"
            }
        
        # Book with that provider
        return await self.book_ride(
            user_id,
            cheapest['provider'],
            cheapest['ride_type'],
            start_location,
            end_location
        )
    
    async def get_ride_status(
        self,
        user_id: str,
        provider: str,
        ride_id: str
    ) -> Dict[str, Any]:
        """
        Get status of an active ride.
        
        Args:
            user_id: User ID
            provider: Provider name
            ride_id: Ride identifier
            
        Returns:
            Dictionary with ride status
        """
        provider_service = self.providers.get(provider)
        
        if not provider_service:
            return {
                "success": False,
                "error": f"Provider '{provider}' not found"
            }
        
        try:
            return await provider_service.get_ride_status(user_id, ride_id)
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    async def get_active_bookings(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get active bookings from all providers.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active booking dictionaries
        """
        all_bookings = []
        
        # Check each provider
        for provider_name, provider in self.providers.items():
            if hasattr(provider, 'get_active_bookings'):
                try:
                    bookings = await provider.get_active_bookings(user_id)
                    all_bookings.extend(bookings)
                except Exception as e:
                    print(f"Error getting bookings from {provider_name}: {e}")
        
        return all_bookings

    def _format_comparison(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format comparison results from multiple providers.
        
        Args:
            results: Raw results from each provider
            
        Returns:
            Formatted comparison dictionary
        """
        all_options = []
        
        # Extract all price options from all providers
        for provider, data in results.items():
            if 'prices' in data and data['prices']:
                for price in data['prices']:
                    all_options.append({
                        'provider': provider,
                        'ride_type': price.get('localized_display_name', price.get('display_name', 'Unknown')),
                        'estimate': price.get('estimate'),
                        'low_estimate': price.get('low_estimate', 0),
                        'high_estimate': price.get('high_estimate', 0),
                        'duration': price.get('duration', 0),
                        'distance': price.get('distance', 0),
                        'currency': price.get('currency', 'AED'),
                        'mock': data.get('mock', False)
                    })
        
        # Sort by low_estimate (cheapest first)
        all_options.sort(key=lambda x: x.get('low_estimate', float('inf')))
        
        return {
            'options': all_options,
            'cheapest': all_options[0] if all_options else None,
            'provider_count': len([p for p in results.values() if 'prices' in p]),
            'providers': results
        }
    
    def format_comparison_for_display(self, comparison: Dict[str, Any]) -> str:
        """
        Format comparison results into a user-friendly message.
        
        Args:
            comparison: Result from compare_prices()
            
        Returns:
            Formatted string for display
        """
        options = comparison.get('options', [])
        
        if not options:
            return "No ride options available at this time."
        
        lines = ["🚗 **Ride Options (sorted by price):**\n"]
        
        for i, option in enumerate(options[:5], 1):  # Show top 5
            provider = option['provider'].title()
            ride_type = option['ride_type']
            estimate = option['estimate']
            duration = option['duration'] // 60  # Convert to minutes
            
            badge = "💰 Cheapest!" if i == 1 else ""
            mock_badge = "📝 Mock" if option.get('mock') else ""
            
            lines.append(
                f"{i}. **{provider} - {ride_type}**: {estimate} "
                f"(~{duration} mins) {badge} {mock_badge}"
            )
        
        lines.append(f"\nCompared {comparison['provider_count']} provider(s)")
        lines.append("\nWould you like me to book the cheapest option?")
        
        return "\n".join(lines)


# Singleton instance
_mobility_aggregator = None

def get_mobility_aggregator() -> MobilityAggregator:
    """Get or create the mobility aggregator singleton."""
    global _mobility_aggregator
    if _mobility_aggregator is None:
        _mobility_aggregator = MobilityAggregator()
    return _mobility_aggregator
