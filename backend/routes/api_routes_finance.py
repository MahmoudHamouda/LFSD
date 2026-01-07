from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db
from models.database import get_db
from services.finance_service import FinanceService
from services.statement_processing_service import StatementService
from core.authentication import get_current_user
from models.models import User
import base64
from fastapi import APIRouter, Depends, HTTPException, Body, Request

router = APIRouter(prefix="/finance", tags=["finance"])

@router.get("/net-worth", summary="Get total net worth")
async def get_net_worth(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = FinanceService(db)
    return {"net_worth": service.get_net_worth(current_user.id)}

@router.get("/portfolio", summary="Get portfolio performance")
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = FinanceService(db)
    return service.get_portfolio_performance(current_user.id)

@router.post("/transactions", summary="Add a transaction")
async def add_transaction(
    transaction_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = FinanceService(db)
    return service.add_transaction(current_user.id, transaction_data)
@router.get("/accounts", summary="Get financial accounts")
async def get_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = FinanceService(db)
    return {"data": service.get_accounts(current_user.id)}

@router.get("/transactions", summary="Get transactions")
async def get_transactions(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = FinanceService(db)
    transactions = service.get_transactions(current_user.id, limit)
    data = []
    for t in transactions:
        row = t.__dict__.copy()
        if "_sa_instance_state" in row:
            del row["_sa_instance_state"]
        row["merchant"] = t.merchant_name or t.description or "Unknown"
        # Fix: Frontend widget expects 'date' (YYYY-MM-DD or readable)
        # Assuming transaction_date is date or datetime object
        if hasattr(t, 'transaction_date') and t.transaction_date:
             row["date"] = str(t.transaction_date).split(" ")[0] # YYYY-MM-DD
        data.append(row)
        
    return {"data": data}

@router.post("/upload-statement", summary="Upload bank statement")
async def upload_statement(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        files_data = data.get("files", [])
        
        service = StatementService(db)
        results = []
        
        for file_data in files_data:
            filename = file_data.get("filename")
            content_b64 = file_data.get("content")
            
            if not filename or not content_b64:
                continue
                
            # Handle data URI
            if "," in content_b64:
                content_b64 = content_b64.split(",")[1]
            
            file_bytes = base64.b64decode(content_b64)
            
            result = await service.process_statement(
                user_id=current_user.id,
                file_content=file_bytes,
                filename=filename
            )
            results.append(result)
            
        return {"status": "success", "results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", summary="Get monthly financial summary")
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = FinanceService(db)
    return service.get_monthly_summary(current_user.id)

@router.get("/scores/current")
async def get_current_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the latest financial score snapshot with all 8 pillars.
    """
    latest = db.query(FinancialScore).filter(
        FinancialScore.user_id == current_user.id
    ).order_by(FinancialScore.timestamp.desc()).first()
    
    if not latest:
        # Return empty struct if no score yet
        return {
            "overall": {"score": 0},
            "categories": {},
            "source": "estimated",
            "generated_at": datetime.utcnow()
        }

    # Map DB columns to category keys
    cats = {
        "cashflow_stability": latest.cashflow_stability_score,
        "bills_coverage": latest.bills_coverage_score,
        "discretionary_control": latest.discretionary_control_score,
        "savings_rate": latest.savings_rate_score,
        "emergency_buffer": latest.emergency_buffer_score,
        "debt_load": latest.debt_load_score,
        "networth_momentum": latest.networth_momentum_score,
        "investment_health": latest.investment_health_score
    }

    # Determine source based on metadata
    source = "estimated"
    if latest.data_sources_json and latest.data_sources_json.get("statements"):
        source = "verified"

    return {
        "generated_at": latest.timestamp,
        "source": source,
        "overall": {"score": latest.overall_score},
        "categories": {
            k: {"score": v, "badge": source.capitalize()} for k, v in cats.items()
        }
    }

@router.get("/categories/{category_id}/coverage")
async def get_category_coverage(
    category_id: str,
    window_days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if enough data exists to unlock the trend chart.
    WHOOP-style: Need X days of data in the last Y days.
    """
    from datetime import datetime, timedelta
    from models.models import FinancialTransaction, RecurringBill
    
    try:
        # 1. Determine "Days with Data"
        start_date = datetime.utcnow() - timedelta(days=window_days)
        
        tx_dates = db.query(FinancialTransaction.transaction_date).filter(
            FinancialTransaction.user_id == current_user.id,
            FinancialTransaction.transaction_date >= start_date
        ).distinct().count()
        
        days_with_data = tx_dates
        required = 20 # Unlock threshold (20 out of 30 days)
        
        # Override for specific categories if needed
        if category_id == "bills_coverage":
            pass

        has_data = days_with_data > 0
        
        if days_with_data == 0 and current_user.onboarding_status == "COMPLETE":
            days_with_data = 1
            has_data = True
            
        coverage_ratio = 1.0
        if required > 0:
            coverage_ratio = min(1.0, days_with_data / required)

        return {
            "category_id": category_id,
            "window_days": window_days,
            "days_with_data": days_with_data,
            "required_days": required,
            "coverage_ratio": coverage_ratio,
            "has_some_data": has_data,
            "no_data": not has_data,
            "chart_unlocked": days_with_data >= required,
            "remaining_days": max(0, required - days_with_data),
            "expected_unlock_date": (datetime.utcnow() + timedelta(days=max(0, required - days_with_data))).strftime("%Y-%m-%d")
        }
    except Exception as e:
        import traceback
        print(f"ERROR in coverage: {e}")
        traceback.print_exc()
        return {
            "category_id": category_id,
            "error": str(e),
            "chart_unlocked": False
        }

@router.get("/categories/{category_id}/history")
async def get_category_history(
    category_id: str,
    range: str = "30d",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return historical data points for the trend chart.
    """
    # Map category_id to DB column
    col_map = {
        "cashflow_stability": FinancialScore.cashflow_stability_score,
        "bills_coverage": FinancialScore.bills_coverage_score,
        "discretionary_control": FinancialScore.discretionary_control_score,
        "savings_rate": FinancialScore.savings_rate_score,
        "emergency_buffer": FinancialScore.emergency_buffer_score,
        "debt_load": FinancialScore.debt_load_score,
        "networth_momentum": FinancialScore.networth_momentum_score,
        "investment_health": FinancialScore.investment_health_score
    }
    
    if category_id not in col_map:
        return {"error": "Invalid category"}
        
    limit = 30
    if range == "90d": limit = 90
    if range == "365d": limit = 365
    
    history = db.query(FinancialScore).filter(
        FinancialScore.user_id == current_user.id
    ).order_by(FinancialScore.timestamp.desc()).limit(limit).all()
    
    # Reverse to chronological order for charts
    points = []
    for h in reversed(history):
        val = getattr(h, col_map[category_id].name)
        points.append({
            "date": h.timestamp.strftime("%Y-%m-%d"),
            "value": val or 0,
            "score": val or 0
        })
        
    return {
        "category_id": category_id,
        "range": range,
        "points": points,
        "source": "verified" # Placeholder
    }
