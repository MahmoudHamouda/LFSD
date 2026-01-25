"""
Financial Scoring Engine (8 Pillars Model for Progressive Disclosure)
"""

import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.models import FinancialTransaction, User, FinancialScore, RecurringBill

# ============================================================================
# Constants & Thresholds
# ============================================================================

# Weights for the new 8 pillars (Total = 100)
WEIGHTS = {
    "cashflow_stability": 15,
    "bills_coverage": 15,
    "discretionary_control": 15,
    "savings_rate": 15,
    "emergency_buffer": 10,
    "debt_load": 10,
    "networth_momentum": 10,
    "investment_health": 10
}

# ============================================================================
# Core Service
# ============================================================================

def calculate_financial_health_score(
    user_id: str, 
    onboarding_data: Dict[str, Any], 
    db: Session,
    is_manual_mode: bool = False
) -> Dict[str, Any]:
    """
    Main entry point to calculate the comprehensive financial health score.
    Combines onboarding data with transaction history (if available).
    """
    # 0. Define Weights (Total 100)
    WEIGHTS = {
        "cashflow_stability": 10,  # Consistency of income > expenses
        "bills_coverage": 15,      # Ability to pay fixed costs
        "discretionary_control": 15, # Spending vs Income ratio
        "savings_rate": 15,        # % of income saved
        "emergency_buffer": 15,    # Liquid cash vs expenses
        "debt_load": 10,           # DTI or servicing cost
        "networth_momentum": 10,   # Growth over time
        "investment_health": 10    # Portfolio diversity/existence
    }
    
    try:
        # 1. Gather Data
        # Get User's transactions if they exist
        from services.finance_service import FinanceService
        
        # Check actual transaction count in DB
        tx_count = len(db.query(FinancialTransaction).filter(FinancialTransaction.user_id == user_id).limit(11).all())
        has_statements = tx_count > 10
        
        # Fetch all txns for calculation (optimize in prod to last 90 days)
        cutoff = datetime.utcnow() - timedelta(days=90)
        transactions = db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id, 
            FinancialTransaction.transaction_date >= cutoff
        ).all()
        
        # DEFENSIVE: Filter bad transactions
        valid_transactions = []
        for t in transactions:
            if t.amount is not None:
                try:
                    float(t.amount) 
                    valid_transactions.append(t)
                except:
                    pass
        transactions = valid_transactions
        
        has_statements = len(transactions) > 10 
        if is_manual_mode:
            has_statements = False
            
        # Fetch verified bills if any
        verified_bills = db.query(RecurringBill).filter(RecurringBill.user_id == user_id).all()
        
        # 2. Compute Sub-scores (New 8 Pillars)
        
        # Pillar 1: Cashflow Stability
        cashflow_score = _compute_cashflow_stability(transactions, onboarding_data, has_statements)
        
        # Pillar 2: Bills Coverage
        bills_score = _compute_bills_coverage(transactions, onboarding_data, has_statements, verified_bills)
        
        # Pillar 3: Discretionary Control
        discretionary_score = _compute_discretionary_control(transactions, onboarding_data, has_statements, verified_bills)
        
        # Pillar 4: Savings Rate
        savings_score = _compute_savings_rate(transactions, onboarding_data, has_statements)
        
        # Pillar 5: Emergency Buffer
        liquid_cash = float(onboarding_data.get("cash_balance", 0) or 0)
        buffer_score = _compute_emergency_buffer(transactions, onboarding_data, has_statements, liquid_cash=liquid_cash)
        
        # Pillar 6: Debt Load
        debt_score = _compute_debt_load(transactions, onboarding_data, has_statements)
        
        # Pillar 7: Net Worth Momentum
        nw_score = _compute_networth_momentum(transactions, onboarding_data, has_statements)
        
        # Pillar 8: Investment Health
        inv_score = _compute_investment_health(transactions, onboarding_data, has_statements)
        
        # 3. Aggregate
        total_score = (
            cashflow_score + 
            bills_score + 
            discretionary_score + 
            savings_score + 
            buffer_score + 
            debt_score + 
            nw_score + 
            inv_score
        )
        
        total_score = min(100.0, max(0.0, total_score))
        
        # 4. Construct Result
        result = {
            "overall_score": round(total_score, 1),
            "subscores": {
                "cashflow_stability": round(cashflow_score, 1),
                "bills_coverage": round(bills_score, 1),
                "discretionary_control": round(discretionary_score, 1),
                "savings_rate": round(savings_score, 1),
                "emergency_buffer": round(buffer_score, 1),
                "debt_load": round(debt_score, 1),
                "networth_momentum": round(nw_score, 1),
                "investment_health": round(inv_score, 1)
            },
            "metadata": {
                "time_window": "last_3_months",
                "data_sources": {
                    "statements": has_statements,
                    "onboarding": True
                }
            }
        }
        
        # 4a. Add Snapshot Totals (Calculated Logic)
        try:
             # Basic totals calculation logic (kept similar to before but adapted)
             if has_statements:
                  total_inc = sum([t.amount for t in transactions if t.amount > 0])
                  total_out = abs(sum([t.amount for t in transactions if t.amount < 0]))
                  # Try to deduce bills from transactions or fallback
                  monthly_bills = sum([b.amount for b in verified_bills]) if verified_bills else float(onboarding_data.get("monthly_bills", 0) or 0)
                  
                  result["totals"] = {
                      "monthly_income": total_inc / 3, # Avg
                      "monthly_bills": monthly_bills,
                      "monthly_expenses": (total_out / 3) - monthly_bills, # Discretionary = Total Out - Fixed 
                      "monthly_savings": (total_inc - total_out) / 3,
                      "assets_value": float(onboarding_data.get("investments_value", 0) or 0)
                  }
             else:
                  inc = float(onboarding_data.get("monthly_income", 0) or 0)
                  bills = float(onboarding_data.get("monthly_bills", 0) or 0) 
                  disc = float(onboarding_data.get("discretionary_spend", 0) or 0) # Explicit discretionary
                  sav = float(onboarding_data.get("monthly_savings", 0) or 0)
                  assets = float(onboarding_data.get("investments_value", 0) or 0)
                  
                  result["totals"] = {
                      "monthly_income": inc,
                      "monthly_bills": bills,
                      "monthly_expenses": disc, # Standardized to Discretionary
                      "monthly_savings": sav,
                      "assets_value": assets
                  }
        except Exception:
             result["totals"] = {"monthly_income": 0, "monthly_bills": 0, "monthly_expenses": 0, "monthly_savings": 0, "assets_value": 0}

        # 5. Persist to DB
        _persist_score(user_id, result, db)
        
        return result

    except Exception as e:
        import traceback
        logger.error(f"SCORING CRASH: {str(e)}\n{traceback.format_exc()}")
        return {
            "overall_score": 0.0,
            "subscores": {k: 0.0 for k in WEIGHTS.keys()},
            "metadata": {"error": "Calculation Failed", "time_window": "error", "data_sources": {}}
        }

# ============================================================================
# NEW 8 Pillar Implementations
# ============================================================================

def _compute_cashflow_stability(transactions: List[FinancialTransaction], onboarding_data: Dict[str, Any], has_statements: bool) -> float:
    # Logic: Consistency of income
    # Weights reference (global)
    # WEIGHTS["cashflow_stability"]
    max_score = 10 
    
    if has_statements:
        incomes = [t.amount for t in transactions if t.amount > 0]
        if len(incomes) > 2:
            try:
                mean = statistics.mean(incomes)
                stdev = statistics.stdev(incomes)
                cv = stdev / mean # Coefficient of Variation
                # CV < 0.2 is very stable (score 10), CV > 1.0 is unstable (score 2)
                if cv < 0.2: return max_score
                if cv > 1.0: return 2
                return max_score * (1 - cv)
            except:
                return max_score * 0.5
    
    # Fallback
    freq = onboarding_data.get("income_frequency", "Monthly")
    return max_score if freq in ["Monthly", "Bi-Weekly"] else max_score * 0.5

def _compute_bills_coverage(transactions: List[FinancialTransaction], onboarding_data: Dict[str, Any], has_statements: bool, bills: List[RecurringBill]) -> float:
    # Logic: Income vs Fixed Bills
    max_score = 15
    try:
        inc = float(onboarding_data.get("monthly_income", 0) or 1)
        bill_total = sum([b.amount for b in bills]) if bills else float(onboarding_data.get("monthly_bills", 0) or 0)
        ratio = bill_total / inc
        if ratio < 0.3: return max_score
        if ratio > 0.6: return max_score * 0.2
        # Linear degradation
        return max_score * (1 - ((ratio - 0.3) / 0.3))
    except:
        return 0

def _compute_discretionary_control(transactions: List[FinancialTransaction], onboarding_data: Dict[str, Any], has_statements: bool, bills: List[RecurringBill]) -> float:
    # Logic: Discretionary Spending / Income
    # Ideal: < 30% of income used for wants? 
    # Or 50/30/20 rule: 50 Needs, 30 Wants, 20 Savings.
    max_score = 15
    try:
        inc = float(onboarding_data.get("monthly_income", 0) or 1)
        
        if has_statements:
            total_out = abs(sum([t.amount for t in transactions if t.amount < 0]))
            bill_total = sum([b.amount for b in bills])
            disc_spend = (total_out / 3) - bill_total  # Estimated monthly
        else:
            disc_spend = float(onboarding_data.get("discretionary_spend", 0) or 0)
            
        ratio = disc_spend / inc
        # Target 30% or less
        if ratio <= 0.3: return max_score
        if ratio >= 0.6: return max_score * 0.2
        return max_score * (1 - ((ratio - 0.3) / 0.3))
    except:
        return max_score * 0.5

def _compute_savings_rate(transactions: List[FinancialTransaction], onboarding_data: Dict[str, Any], has_statements: bool) -> float:
    # Logic: Savings / Income
    max_score = 15
    try:
        inc = float(onboarding_data.get("monthly_income", 0) or 1)
        sav = float(onboarding_data.get("monthly_savings", 0) or 0)
        
        if has_statements:
             total_inc = sum([t.amount for t in transactions if t.amount > 0])
             total_out = abs(sum([t.amount for t in transactions if t.amount < 0]))
             calc_sav = (total_inc - total_out) / 3
             if calc_sav > sav: sav = calc_sav
             
        rate = sav / inc
        if rate >= 0.2: return max_score # 20% target
        return (rate / 0.2) * max_score
    except:
        return 0

def _compute_emergency_buffer(transactions: List[FinancialTransaction], onboarding_data: Dict[str, Any], has_statements: bool, liquid_cash: float = 0) -> float:
    # Logic: Liquid Cash (not Investments) / Monthly Burn (Bills + Expenses)
    max_score = 15
    try:
        if has_statements and liquid_cash > 0:
            buffer_amt = liquid_cash
        else:
            # Fallback if no account data linked yet, strictly use reported savings (accumulated?)
            # Usually users report "Savings Balance" not flow. 
            # Assuming "investments_value" might have been misused, but we want STRICT cash.
            # If manual, we don't have a "Cash Balance" field in standard onboarding usually, 
            # so we might have to rely on a specific field or default to 0.
            buffer_amt = float(onboarding_data.get("cash_balance", 0) or 0)
            
        bills = float(onboarding_data.get("monthly_bills", 0) or 0)
        disc = float(onboarding_data.get("discretionary_spend", 0) or 0)
        burn = bills + disc
        if burn == 0: burn = 1
        
        months = buffer_amt / burn
        if months >= 6: return max_score
        if months >= 3: return max_score * 0.8
        return (months / 3) * max_score * 0.8
    except:
        return 0

def _compute_debt_load(transactions: List[FinancialTransaction], onboarding_data: Dict[str, Any], has_statements: bool) -> float:
    # Logic: Debt Payments / Income
    max_score = 10
    try:
        inc = float(onboarding_data.get("monthly_income", 0) or 1)
        debt = float(onboarding_data.get("monthly_debt_payments", 0) or 0)
        dti = debt / inc
        if dti <= 0.1: return max_score
        if dti >= 0.4: return 0
        return max_score * (1 - ((dti - 0.1) / 0.3))
    except:
        return 10 # Assume no debt if error?

def _compute_networth_momentum(transactions: List[FinancialTransaction], onboarding_data: Dict[str, Any], has_statements: bool) -> float:
    # Logic: Ideally change over time. 
    # Current proxy: If Savings Rate > 20%, Momentum is likely Good.
    max_score = 10
    try:
        # Re-use simplified savings rate check
        inc = float(onboarding_data.get("monthly_income", 0) or 1)
        sav = float(onboarding_data.get("monthly_savings", 0) or 0)
        if (sav/inc) > 0.2: return max_score
        if (sav/inc) > 0.1: return max_score * 0.7
        return max_score * 0.4
    except:
        return max_score * 0.5

def _compute_investment_health(transactions: List[FinancialTransaction], onboarding_data: Dict[str, Any], has_statements: bool) -> float:
    # Logic: Existence of assets
    max_score = 10
    try:
        inv = float(onboarding_data.get("investments_value", 0) or 0)
        inc = float(onboarding_data.get("monthly_income", 0) or 1)
        
        # Determine 401k/Brokerage status or raw ratio
        if inv > (inc * 12): return max_score # > 1 year salary invested
        if inv > (inc * 6): return max_score * 0.8
        if inv > 0: return max_score * 0.5
        
        status = onboarding_data.get("investments_status", "no")
        if status == "yes": return max_score * 0.5
        return 0
    except:
        return 0

def _persist_score(user_id: str, result: Dict[str, Any], db: Session):
    """
    Save the calculated score to the DB.
    """
    try:
        score_entry = FinancialScore(
            user_id=user_id,
            overall_score=result["overall_score"],
            
            # New Columns
            cashflow_stability_score=result["subscores"]["cashflow_stability"],
            bills_coverage_score=result["subscores"]["bills_coverage"],
            discretionary_control_score=result["subscores"]["discretionary_control"],
            savings_rate_score=result["subscores"]["savings_rate"],
            emergency_buffer_score=result["subscores"]["emergency_buffer"],
            debt_load_score=result["subscores"]["debt_load"],
            networth_momentum_score=result["subscores"]["networth_momentum"],
            investment_health_score=result["subscores"]["investment_health"],
            
            time_window=result["metadata"]["time_window"],
            data_sources_json=result["metadata"]["data_sources"],
            
            # Snapshot Columns
            total_monthly_income=result.get("totals", {}).get("monthly_income", 0),
            total_monthly_bills=result.get("totals", {}).get("monthly_bills", 0),
            total_monthly_expenses=result.get("totals", {}).get("monthly_expenses", 0),
            total_monthly_savings=result.get("totals", {}).get("monthly_savings", 0),
            total_assets_value=result.get("totals", {}).get("assets_value", 0)
        )
        
        import uuid
        if not score_entry.id:
            score_entry.id = str(uuid.uuid4())
        
        db.add(score_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Error persisting score: {e}")


# End of valid implementation
