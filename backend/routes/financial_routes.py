"""
Financial service endpoints.

Contains endpoints for retrieving and managing financial data. These stubs
should be replaced with real implementations that integrate with payment
providers or accounting systems. Authentication and rate limiting are applied
globally.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from core.authentication import get_current_user
from core.rate_limiting import limiter


router = APIRouter(prefix="/financial", tags=["Financial"])


@router.get("/balances", summary="Get account balances")
@limiter.limit("10/minute")
async def get_balances(
    *,
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    """Return account balances for the current user."""
    from models.models import FinancialAccount

    accounts = current_user.financial_accounts
    total_checking = sum(
        acc.current_balance for acc in accounts if acc.account_type == "checking"
    )
    total_savings = sum(
        acc.current_balance for acc in accounts if acc.account_type == "savings"
    )
    total_debt = sum(
        acc.current_balance for acc in accounts if acc.account_type == "credit"
    )  # typically negative or positive depending on model

    # Return aggregated map
    return {
        "data": {
            "balances": {
                "checking": total_checking,
                "savings": total_savings,
                "debt": total_debt,
                "net_worth": total_checking + total_savings - total_debt,
            }
        }
    }


@router.get("/transactions", summary="List transactions")
@limiter.limit("15/minute")
async def list_transactions(
    *,
    current_user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated list of transactions."""
    from models.models import FinancialTransaction
    from sqlalchemy import desc

    query = current_user.financial_transactions.order_by(
        desc(FinancialTransaction.transaction_date)
    )

    # Simple pagination
    txs = query.limit(limit).all()

    items = []
    for tx in txs:
        items.append(
            {
                "id": tx.id,
                "amount": tx.amount,
                "merchant": tx.merchant_name,
                "date": tx.transaction_date.strftime("%Y-%m-%d"),
                "category": tx.category_primary,
                "institution": "Helm Bank",  # Placeholder or join with Account
            }
        )

    return {"data": {"items": items, "next_cursor": None}}
