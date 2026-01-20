from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.models import User, DBMessage, Recommendation
from models.growth_models import Subscription
from models.growth_schemas import PlanId

class BillingService:
    # Pricing Constants (Example for Gemini 1.5 Flash)
    COST_PER_INPUT_TOKEN = 0.000000075 # $0.075 per 1M
    COST_PER_OUTPUT_TOKEN = 0.00000030 # $0.30 per 1M
    
    # Subscription Prices
    PLAN_PRICES = {
        PlanId.FREE: 0.0,
        PlanId.PLUS: 4.99,
        PlanId.PRO: 9.99,
        PlanId.ENTERPRISE: 49.99 # Placeholder for custom
    }

    def __init__(self, db: Session):
        self.db = db

    def get_overall_summary(self) -> Dict[str, Any]:
        """Calculate total revenue and total cost across all systems."""
        # 1. Total Revenue (Sum of active subscriptions)
        total_revenue = 0.0
        active_subs = self.db.query(Subscription).filter(Subscription.status == "active").all()
        for sub in active_subs:
            total_revenue += self.PLAN_PRICES.get(sub.plan_id, 0.0)

        # 2. Total AI Cost (Gemini Token Usage)
        token_data = self.db.query(
            func.sum(DBMessage.input_tokens).label("in_tokens"),
            func.sum(DBMessage.output_tokens).label("out_tokens")
        ).first()
        
        total_in = token_data.in_tokens or 0
        total_out = token_data.out_tokens or 0
        
        ai_cost = (total_in * self.COST_PER_INPUT_TOKEN) + (total_out * self.COST_PER_OUTPUT_TOKEN)

        # 3. API Integration Costs (Placeholders)
        # Mobility (Uber) - assume $0.05 per comparison/booking
        mobility_interactions = self.db.query(Recommendation).filter(Recommendation.type.like("mobility%")).count()
        mobility_cost = mobility_interactions * 0.05

        total_cost = ai_cost + mobility_cost
        
        return {
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
        """Calculate revenue and cost per customer."""
        users = self.db.query(User).all()
        reconciliation = []

        for user in users:
            # Revenue
            sub = self.db.query(Subscription).filter(Subscription.user_id == user.id, Subscription.status == "active").first()
            revenue = self.PLAN_PRICES.get(sub.plan_id if sub else PlanId.FREE, 0.0)

            # Cost
            token_data = self.db.query(
                func.sum(DBMessage.input_tokens).label("in_tokens"),
                func.sum(DBMessage.output_tokens).label("out_tokens")
            ).filter(DBMessage.user_id == user.id).first()
            
            user_in = token_data.in_tokens or 0
            user_out = token_data.out_tokens or 0
            ai_cost = (user_in * self.COST_PER_INPUT_TOKEN) + (user_out * self.COST_PER_OUTPUT_TOKEN)
            
            mobility_interactions = self.db.query(Recommendation).filter(
                Recommendation.user_id == user.id, 
                Recommendation.type.like("mobility%")
            ).count()
            mobility_cost = mobility_interactions * 0.05
            
            total_cost = ai_cost + mobility_cost

            if revenue > 0 or total_cost > 0:
                reconciliation.append({
                    "user_id": user.id,
                    "email": user.email,
                    "plan": sub.plan_id if sub else "free",
                    "revenue": round(revenue, 2),
                    "cost": round(total_cost, 2),
                    "margin": round(revenue - total_cost, 2)
                })

        return sorted(reconciliation, key=lambda x: x["margin"])

    def get_api_integration_costs(self) -> List[Dict[str, Any]]:
        """Analyze costs per API integration."""
        # For now, Gemini and Mobility are our main integrations
        ai_summary = self.get_overall_summary()["breakdown"]["ai_gemini"]
        mobility_summary = self.get_overall_summary()["breakdown"]["mobility_api"]
        
        return [
            {
                "integration": "Google Gemini (AI)",
                "total_cost": round(ai_summary, 4),
                "unit": "Tokens",
                "usage": self.db.query(func.count(DBMessage.id)).filter(DBMessage.role == "assistant").scalar() or 0
            },
            {
                "integration": "Uber/Careem (Mobility)",
                "total_cost": round(mobility_summary, 2),
                "unit": "Requests",
                "usage": self.db.query(Recommendation).filter(Recommendation.type.like("mobility%")).count() or 0
            }
        ]
