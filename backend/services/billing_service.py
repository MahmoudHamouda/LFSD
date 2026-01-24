from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from models.models import User, DBMessage, Recommendation, MobilityTrip
from models.growth_models import Subscription
from models.growth_schemas import PlanId
from models.logging_models import AuditLog

class BillingService:
    # Model-Aware AI Pricing (per 1M tokens)
    MODEL_PRICING = {
        "gemini-1.5-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
        "gemini-1.5-pro": {"input": 3.50 / 1_000_000, "output": 10.50 / 1_000_000},
        "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0}, # Free during exp
    }
    DEFAULT_PRICING = {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000}
    
    # Subscription Prices (Monthly)
    PLAN_PRICES = {
        PlanId.FREE: 0.0,
        PlanId.PLUS: 4.99,
        PlanId.PRO: 9.99,
        PlanId.ENTERPRISE: 49.99
    }

    def __init__(self, db: Session):
        self.db = db

    def _get_days_in_month(self, dt: datetime) -> int:
        """Helper to get number of days in a given month/year."""
        if dt.month == 12:
            return 31
        return (date(dt.year, dt.month + 1, 1) - date(dt.year, dt.month, 1)).days

    def get_overall_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate revenue and cost for a specific window.
        Defaults to current month if window not provided.
        """
        now = datetime.utcnow()
        if not start_date:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = now
            
        days_in_period = (end_date - start_date).days + 1
        days_in_month = self._get_days_in_month(start_date)

        # 1. Revenue with Proration
        total_revenue = 0.0
        active_subs = self.db.query(Subscription).filter(Subscription.status == "active").all()
        
        for sub in active_subs:
            monthly_price = self.PLAN_PRICES.get(sub.plan_id, 0.0)
            if monthly_price == 0:
                continue
                
            # Simple proration logic:
            # If sub started before or during this period, count the overlap
            sub_start = sub.current_period_start or sub.created_at or start_date
            overlap_start = max(start_date, sub_start)
            overlap_end = min(end_date, sub.current_period_end or end_date)
            
            if overlap_end > overlap_start:
                overlap_days = (overlap_end - overlap_start).days
                # Cap overlap by period length
                overlap_days = min(overlap_days, days_in_period)
                prorated_price = (monthly_price / days_in_month) * overlap_days
                total_revenue += prorated_price

        # 2. Model-Aware AI Cost
        ai_cost = 0.0
        total_in = 0
        total_out = 0
        
        # Group by model to apply correct pricing
        token_usage_by_model = self.db.query(
            DBMessage.model_used,
            func.sum(DBMessage.input_tokens).label("in_tokens"),
            func.sum(DBMessage.output_tokens).label("out_tokens")
        ).filter(DBMessage.date >= start_date, DBMessage.date <= end_date).group_by(DBMessage.model_used).all()
        
        for model_name, in_t, out_t in token_usage_by_model:
            pricing = self.MODEL_PRICING.get(model_name, self.DEFAULT_PRICING)
            ai_cost += (in_t or 0) * pricing["input"] + (out_t or 0) * pricing["output"]
            total_in += (in_t or 0)
            total_out += (out_t or 0)

        # 3. API Integration Costs (Using Trips as proxy for now)
        mobility_interactions = self.db.query(MobilityTrip).filter(MobilityTrip.created_at >= start_date).count()
        mobility_cost = mobility_interactions * 0.05

        total_cost = ai_cost + mobility_cost
        
        return {
            "period": f"{start_date.date()} to {end_date.date()}",
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "profit": round(total_revenue - total_cost, 2),
            "breakdown": {
                "ai_gemini": round(ai_cost, 4),
                "mobility_api": round(mobility_cost, 2)
            },
            "metrics": {
                "total_input_tokens": total_in,
                "total_output_tokens": total_out,
                "active_subscribers": len(active_subs)
            }
        }

    def get_customer_reconciliation(self) -> List[Dict[str, Any]]:
        """
        Calculate revenue and cost per customer using optimized aggregations.
        """
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Fetch all users and their current active subscription
        user_subs = self.db.query(
            User.id, User.email, Subscription.plan_id
        ).outerjoin(Subscription, (User.id == Subscription.user_id) & (Subscription.status == "active")).all()
        
        # 2. Fetch AI Costs per user (Grouped by model)
        ai_stats = self.db.query(
            DBMessage.user_id,
            DBMessage.model_used,
            func.sum(DBMessage.input_tokens).label("in_tokens"),
            func.sum(DBMessage.output_tokens).label("out_tokens")
        ).filter(DBMessage.date >= start_of_month).group_by(DBMessage.user_id, DBMessage.model_used).all()
        
        user_ai_costs = {}
        for uid, model, in_t, out_t in ai_stats:
            pricing = self.MODEL_PRICING.get(model, self.DEFAULT_PRICING)
            cost = (in_t or 0) * pricing["input"] + (out_t or 0) * pricing["output"]
            user_ai_costs[uid] = user_ai_costs.get(uid, 0.0) + cost
            
        # 3. Fetch Mobility Costs per user
        mobility_stats = self.db.query(
            MobilityTrip.user_id,
            func.count(MobilityTrip.id).label("trip_count")
        ).filter(MobilityTrip.created_at >= start_of_month).group_by(MobilityTrip.user_id).all()
        
        user_mobility_costs = {uid: (count * 0.05) for uid, count in mobility_stats}
        
        reconciliation = []
        for uid, email, plan in user_subs:
            revenue = self.PLAN_PRICES.get(plan or PlanId.FREE, 0.0)
            cost = user_ai_costs.get(uid, 0.0) + user_mobility_costs.get(uid, 0.0)
            
            if revenue > 0 or cost > 0:
                reconciliation.append({
                    "user_id": uid,
                    "email": email,
                    "plan": plan or "free",
                    "revenue": round(revenue, 2),
                    "cost": round(cost, 2),
                    "margin": round(revenue - cost, 2)
                })

        # Sort by margin DESCENDING (Best first)
        return sorted(reconciliation, key=lambda x: x["margin"], reverse=True)

    def get_api_integration_costs(self) -> List[Dict[str, Any]]:
        """Analyze monthly costs per API integration."""
        summary = self.get_overall_summary()
        
        return [
            {
                "integration": "Google Gemini (AI)",
                "total_cost": round(summary["breakdown"]["ai_gemini"], 4),
                "unit": "Tokens",
                "usage": self.db.query(func.sum(DBMessage.input_tokens + DBMessage.output_tokens)).filter(DBMessage.date >= datetime.utcnow() - timedelta(days=30)).scalar() or 0
            },
            {
                "integration": "Uber/Careem (Mobility)",
                "total_cost": round(summary["breakdown"]["mobility_api"], 2),
                "unit": "Trips",
                "usage": self.db.query(MobilityTrip).filter(MobilityTrip.created_at >= datetime.utcnow() - timedelta(days=30)).count()
            }
        ]

