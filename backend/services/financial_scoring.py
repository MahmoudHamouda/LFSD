"""
Financial Scoring Engine (8 Pillars Model for Progressive Disclosure)
"""

import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.models import Transaction, User, FinancialScore, RecurringBill

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
    try:
        # 1. Fetch Transaction Data
        last_tx = db.query(func.max(Transaction.transaction_date)).filter(Transaction.user_id == user_id).scalar()
        
        if last_tx:
            if isinstance(last_tx, str):
                 try:
                     end_date = datetime.strptime(last_tx, "%Y-%m-%d %H:%M:%S.%f")
                 except ValueError:
                     try:
                         end_date = datetime.strptime(last_tx, "%Y-%m-%d")
                     except:
                         end_date = datetime.utcnow()
            else:
                end_date = last_tx
            start_date = end_date - timedelta(days=90) # 3 months window
        else:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)
        
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
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
        buffer_score = _compute_emergency_buffer(transactions, onboarding_data, has_statements)
        
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
                  monthly_bills = sum([b.amount for b in verified_bills]) if verified_bills else float(onboarding.get("monthly_bills", 0) or 0)
                  
                  result["totals"] = {
                      "monthly_income": total_inc / 3, # Avg
                      "monthly_bills": monthly_bills,
                      "monthly_expenses": (total_out / 3) - monthly_bills, 
                      "monthly_savings": (total_inc - total_out) / 3,
                      "assets_value": float(onboarding.get("investments_value", 0) or 0)
                  }
             else:
                  inc = float(onboarding.get("monthly_income", 0) or 0)
                  bills = float(onboarding.get("monthly_bills", 0) or 0) 
                  disc = float(onboarding.get("discretionary_spend", 0) or 0)
                  sav = float(onboarding.get("monthly_savings", 0) or 0)
                  assets = float(onboarding.get("investments_value", 0) or 0)
                  
                  result["totals"] = {
                      "monthly_income": inc,
                      "monthly_bills": bills,
                      "monthly_expenses": disc,
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
        print(f"SCORING CRASH: {str(e)}\n{traceback.format_exc()}")
        return {
            "overall_score": 0.0,
            "subscores": {k: 0.0 for k in WEIGHTS.keys()},
            "metadata": {"error": "Calculation Failed", "time_window": "error", "data_sources": {}}
        }

# ============================================================================
# NEW 8 Pillar Implementations
# ============================================================================

def _compute_cashflow_stability(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    # Logic: Consistency of income
    max_score = WEIGHTS["cashflow_stability"]
    if has_statements:
        incomes = [t.amount for t in transactions if t.amount > 0]
        if len(incomes) > 2:
            return max_score * 0.9 # Placeholder for variance calc
    
    # Fallback
    freq = onboarding.get("income_frequency", "Monthly")
    return max_score if freq in ["Monthly", "Bi-Weekly"] else max_score * 0.5

def _compute_bills_coverage(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool, bills: List[RecurringBill]) -> float:
    # Logic: Income vs Fixed Bills
    max_score = WEIGHTS["bills_coverage"]
    try:
        inc = float(onboarding.get("monthly_income", 0) or 1)
        bill_total = sum([b.amount for b in bills]) if bills else float(onboarding.get("monthly_bills", 0) or 0)
        ratio = bill_total / inc
        if ratio < 0.4: return max_score
        if ratio > 0.8: return 0
        return max_score * 0.5
    except:
        return 0

def _compute_discretionary_control(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool, bills: List[RecurringBill]) -> float:
    # Logic: Spending vs Leftover after bills
    max_score = WEIGHTS["discretionary_control"]
    return max_score * 0.7 # Placeholder

def _compute_savings_rate(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    # Logic: Savings / Income
    max_score = WEIGHTS["savings_rate"]
    try:
        inc = float(onboarding.get("monthly_income", 0) or 1)
        sav = float(onboarding.get("monthly_savings", 0) or 0)
        rate = sav / inc
        if rate > 0.2: return max_score
        return (rate / 0.2) * max_score
    except:
        return 0

def _compute_emergency_buffer(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    # Logic: Liquid Assets / Monthly Burn
    max_score = WEIGHTS["emergency_buffer"]
    try:
        assets = float(onboarding.get("investments_value", 0) or 0) # Proxy for now, ideally strictly cash
        burn = float(onboarding.get("monthly_expenses", 0) or 1) + float(onboarding.get("monthly_bills", 0) or 0)
        months = assets / burn
        if months >= 6: return max_score
        return (months / 6) * max_score
    except:
        return 0

def _compute_debt_load(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    # Logic: DTI
    max_score = WEIGHTS["debt_load"]
    try:
        inc = float(onboarding.get("monthly_income", 0) or 1)
        debt = float(onboarding.get("monthly_debt_payments", 0) or 0)
        dti = debt / inc
        if dti < 0.1: return max_score
        if dti > 0.5: return 0
        return max_score * 0.5
    except:
        return 0

def _compute_networth_momentum(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    # Logic: Change in Net Worth (Need history, so default is neutral for now)
    max_score = WEIGHTS["networth_momentum"]
    return max_score * 0.5 # Neutral start

def _compute_investment_health(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    # Logic: Investment allocation
    max_score = WEIGHTS["investment_health"]
    try:
        status = onboarding.get("investments_status", "no")
        if status == "yes": return max_score
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
        print(f"Error persisting score: {e}")


# ============================================================================
# Constants & Thresholds
# ============================================================================

# Weights for the 8 pillars (Total = 100)
WEIGHTS = {
    "income_stability": 15,
    "burn_rate": 15,
    "savings_momentum": 15,
    "debt_stress": 15,
    "recurring_commitments": 10,
    "spending_stability": 10,
    "liquidity_cushion": 10,
    "risk_indicators": 10
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
    try:
        # 1. Fetch Transaction Data
        # Determine the time window based on the latest transaction
        last_tx = db.query(func.max(Transaction.transaction_date)).filter(Transaction.user_id == user_id).scalar()
        
        if last_tx:
            # If we have transactions, anchor the window to the latest one
            if isinstance(last_tx, str):
                 # Handle potential string dates from SQLite
                 try:
                     end_date = datetime.strptime(last_tx, "%Y-%m-%d %H:%M:%S.%f")
                 except ValueError:
                     try:
                         end_date = datetime.strptime(last_tx, "%Y-%m-%d")
                     except:
                         end_date = datetime.utcnow()
            else:
                end_date = last_tx
                
            # Ensure we don't go into the future if data is weird, but usually trusting DB is fine.
            start_date = end_date - timedelta(days=90) # 3 months window
        else:
            # No transactions, use current time
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)
        
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).all()
        
        # DEFENSIVE: Filter bad transactions
        valid_transactions = []
        for t in transactions:
            if t.amount is not None:
                try:
                    # Check if it looks numeric
                    float(t.amount) 
                    valid_transactions.append(t)
                except:
                    pass
        transactions = valid_transactions
        
        has_statements = len(transactions) > 10 # Arbitrary threshold to consider statement data valid
        
        if is_manual_mode:
            has_statements = False
        
        # 2. Compute Sub-scores (Wrapped in try/except inside helper functions ideally, but here top-level catches all)
        
        # Pillar 1: Income Stability
        income_score = _compute_income_stability(transactions, onboarding_data, has_statements)
        
        # Pillar 2: Burn Rate
        burn_rate_score = _compute_burn_rate(transactions, onboarding_data, has_statements)
        
        # Pillar 3: Savings Momentum
        savings_score = _compute_savings_momentum(transactions, onboarding_data, has_statements)
        
        # Pillar 4: Debt Stress
        debt_score = _compute_debt_stress(transactions, onboarding_data, has_statements)
        
        # Pillar 5: Recurring Commitments
        recurring_score = _compute_recurring_commitments(transactions, onboarding_data, has_statements)
        
        # Pillar 6: Spending Stability
        spending_score = _compute_spending_stability(transactions, onboarding_data, has_statements)
        
        # Pillar 7: Liquidity Cushion
        liquidity_score = _compute_liquidity_cushion(transactions, onboarding_data, has_statements)
        
        # Pillar 8: Risk Indicators
        risk_score = _compute_risk_indicators(transactions, onboarding_data, has_statements)
        
        # 3. Aggregate
        total_score = (
            income_score + 
            burn_rate_score + 
            savings_score + 
            debt_score + 
            recurring_score + 
            spending_score + 
            liquidity_score + 
            risk_score
        )
        
        # Cap at 100 just in case
        total_score = min(100.0, max(0.0, total_score))
        
        # 4. Construct Result
        result = {
            "overall_score": round(total_score, 1),
            "subscores": {
                "income_stability": round(income_score, 1),
                "burn_rate": round(burn_rate_score, 1),
                "savings_momentum": round(savings_score, 1),
                "debt_stress": round(debt_score, 1),
                "recurring_commitments": round(recurring_score, 1),
                "spending_stability": round(spending_score, 1),
                "liquidity_cushion": round(liquidity_score, 1),
                "risk_indicators": round(risk_score, 1)
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
            if has_statements:
                 total_income = sum([t.amount for t in transactions if t.amount > 0])
                 total_out = abs(sum([t.amount for t in transactions if t.amount < 0]))
                 
                 onb_bills = float(onboarding.get("monthly_bills", 0) or 0)
                 if onb_bills == 0:
                      onb_bills = float(onboarding.get("rent_amount", 0) or 0)
                 
                 result["totals"] = {
                     "monthly_income": total_income,
                     "monthly_bills": onb_bills,
                     "monthly_expenses": max(0, total_out - onb_bills), 
                     "monthly_savings": max(0, total_income - total_out),
                     "assets_value": float(onboarding.get("investments_value", 0) or 0)
                 }
            else:
                 inc = float(onboarding.get("monthly_income", 0) or 0)
                 bills = float(onboarding.get("monthly_bills", 0) or 0) 
                 if bills == 0:
                     rent = float(onboarding.get("rent_amount", 0) or 0)
                     bills = rent
                     
                 disc = float(onboarding.get("discretionary_spend", 0) or 0)
                 sav = float(onboarding.get("monthly_savings", 0) or 0)
                 assets = float(onboarding.get("investments_value", 0) or 0)
                 
                 result["totals"] = {
                     "monthly_income": inc,
                     "monthly_bills": bills,
                     "monthly_expenses": disc,
                     "monthly_savings": sav,
                     "assets_value": assets
                 }
        except Exception as e:
             # Default to zeros if calculation fails
             result["totals"] = {
                 "monthly_income": 0, "monthly_bills": 0, "monthly_expenses": 0, "monthly_savings": 0, "assets_value": 0
             }

        # 5. Persist to DB
        _persist_score(user_id, result, db)
        
        return result

    except Exception as e:
        # CRITICAL FALLBACK
        # Log error but RETURN A VALID SCORE OBJECT so the UI doesn't crash (500)
        import traceback
        error_msg = f"SCORING CRASH: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        try:
            with open("scoring_errors.log", "a") as f:
                f.write(f"[{datetime.utcnow()}] {error_msg}\n")
        except:
            pass
            
        return {
            "overall_score": 0.0, # Default safe score
            "subscores": {k: 0.0 for k in WEIGHTS.keys()},
            "metadata": {"error": "Calculation Failed", "time_window": "error", "data_sources": {}}
        }

# ============================================================================
# Pillar Implementations
# ============================================================================

def _compute_income_stability(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    """
    Pillar 1: Income Stability (0-15)
    Reward stable, predictable income.
    """
    max_score = WEIGHTS["income_stability"]
    
    if has_statements:
        incomes = [t.amount for t in transactions if t.amount > 0] 
        # Filter for significant inflows (e.g. > $500)
        significant_incomes = [amt for amt in incomes if amt > 500]
        
        if len(significant_incomes) >= 3:
            mean_inc = statistics.mean(significant_incomes)
            stdev_inc = statistics.stdev(significant_incomes) if len(significant_incomes) > 1 else 0
            
            cv = stdev_inc / mean_inc if mean_inc > 0 else 1 
            stability_factor = 1 / (1 + cv)
            return max_score * stability_factor
            
    # Fallback to onboarding
    freq = onboarding.get("income_frequency", "Monthly")
    emp_type = onboarding.get("employment_type", "Full-time")
    
    score = max_score * 0.7 # Default mid-range
    
    if emp_type == "Full-time":
        score += max_score * 0.2
    elif emp_type in ["Freelance", "Business Owner"]:
        score -= max_score * 0.1
        
    if freq in ["Monthly", "Bi-Weekly"]:
        score += max_score * 0.1
    elif freq == "Irregular":
        score -= max_score * 0.2
        
    return min(max_score, max(0, score))

def _compute_burn_rate(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    """
    Pillar 2: Burn Rate / Expense Load (0-15)
    Lower expense ratio -> higher score.
    """
    max_score = WEIGHTS["burn_rate"]
    
    income = 0
    expenses = 0
    
    if has_statements:
        income = sum([t.amount for t in transactions if t.amount > 0])
        expenses = abs(sum([t.amount for t in transactions if t.amount < 0]))
        
        # Normalize to monthly (Assuming 3 months window)
        income /= 3
        expenses /= 3
    else:
        try:
            raw_income = onboarding.get("monthly_income", 0)
            if isinstance(raw_income, str) and "-" in raw_income:
                # Parse range "3000-7000" -> 5000
                parts = raw_income.replace('$', '').replace(',', '').split('-')
                if len(parts) == 2:
                    income = (float(parts[0]) + float(parts[1])) / 2
                elif "+" in raw_income:
                    # Handle "12000+"
                    income = float(raw_income.replace('+', '').replace('$', '').replace(',', ''))
            elif isinstance(raw_income, str) and "+" in raw_income:
                 income = float(raw_income.replace('+', '').replace('$', '').replace(',', ''))
            else:
                income = float(raw_income or 0)
                
            expenses = float(onboarding.get("monthly_expenses", 0) or 0)
        except:
            income = 0
            expenses = 0
        
    if income <= 0:
        return 0
        
    ratio = expenses / income
    
    if ratio <= 0.5:
        return max_score
    elif ratio >= 1.0:
        return 0
    else:
        return max_score - ((ratio - 0.5) * (max_score / 0.5))

def _compute_savings_momentum(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    """
    Pillar 3: Savings Momentum (0-15)
    Higher savings rate -> higher score.
    """
    max_score = WEIGHTS["savings_momentum"]
    
    savings_rate = 0
    
    try:
        if has_statements:
            income = sum([t.amount for t in transactions if t.amount > 0])
            expenses = abs(sum([t.amount for t in transactions if t.amount < 0]))
            
            if income > 0:
                savings_rate = (income - expenses) / income
        else:
            income = float(onboarding.get("monthly_income", 0) or 0)
            savings = float(onboarding.get("monthly_savings", 0) or 0)
            if income > 0:
                savings_rate = savings / income
    except:
        savings_rate = 0
            
    score = (savings_rate / 0.20) * max_score
    return min(max_score, max(0, score))

def _compute_debt_stress(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    """
    Pillar 4: Debt Stress (0-15)
    Lower DTI -> higher score.
    """
    max_score = WEIGHTS["debt_stress"]
    
    dti = 0
    
    try:
        # Use onboarding as primary for now
        income = float(onboarding.get("monthly_income", 0) or 1)
        debt_payments = float(onboarding.get("monthly_debt_payments", 0) or 0)
        
        if income > 0:
            dti = debt_payments / income
    except:
        dti = 0

    if dti >= 0.5:
        return 0
    
    score = (1 - (dti / 0.5)) * max_score
    return min(max_score, max(0, score))

def _compute_recurring_commitments(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    """
    Pillar 5: Recurring Commitments Load (0-10)
    Lower fixed costs -> higher score.
    """
    max_score = WEIGHTS["recurring_commitments"]
    
    try:
        income = float(onboarding.get("monthly_income", 0) or 1)
        rent = float(onboarding.get("rent_amount", 0) or 0)
        
        fixed_ratio = rent / income if income > 0 else 1
    except:
        fixed_ratio = 1
    
    if fixed_ratio <= 0.3:
        return max_score
    if fixed_ratio >= 0.6:
        return 0
        
    return max_score - ((fixed_ratio - 0.3) * (max_score / 0.3))

def _compute_spending_stability(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    """
    Pillar 6: Spending Stability (0-10)
    """
    max_score = WEIGHTS["spending_stability"]
    
    try:
        income = float(onboarding.get("monthly_income", 0) or 1)
        disc = float(onboarding.get("discretionary_spend", 0) or 0)
        
        ratio = disc / income if income > 0 else 0
    except:
        ratio = 0
    
    if ratio < 0.3:
        return max_score
    elif ratio > 0.6:
        return 0
    else:
        return max_score * 0.5 

def _compute_liquidity_cushion(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    """
    Pillar 7: Liquidity Cushion (0-10)
    """
    max_score = WEIGHTS["liquidity_cushion"]
    
    try:
        expenses = float(onboarding.get("monthly_expenses", 0) or 1)
        assets = float(onboarding.get("investments_value", 0) or 0)
        
        months_covered = assets / expenses if expenses > 0 else 0
    except:
        months_covered = 0
    
    score = (months_covered / 6.0) * max_score
    return min(max_score, max(0, score))

def _compute_risk_indicators(transactions: List[Transaction], onboarding: Dict[str, Any], has_statements: bool) -> float:
    """
    Pillar 8: Risk Indicators (0-10)
    """
    max_score = WEIGHTS["risk_indicators"]
    
    score = max_score
    
    try:
        risk_appetite = onboarding.get("risk_appetite", "unsure")
        has_debt = onboarding.get("has_debt", "no")
        
        if has_debt == "yes":
            income = float(onboarding.get("monthly_income", 0) or 1)
            debt = float(onboarding.get("monthly_debt_payments", 0) or 0)
            if (debt / income) > 0.4:
                score -= 3
    except:
        pass
        
    return max(0, score)

def _persist_score(user_id: str, result: Dict[str, Any], db: Session):
    """
    Save the calculated score to the DB.
    """
    try:
        score_entry = FinancialScore(
            user_id=user_id,
            overall_score=result["overall_score"],
            income_stability_score=result["subscores"]["income_stability"],
            burn_rate_score=result["subscores"]["burn_rate"],
            savings_momentum_score=result["subscores"]["savings_momentum"],
            debt_stress_score=result["subscores"]["debt_stress"],
            recurring_commitments_score=result["subscores"]["recurring_commitments"],
            spending_stability_score=result["subscores"]["spending_stability"],
            liquidity_cushion_score=result["subscores"]["liquidity_cushion"],
            risk_indicator_score=result["subscores"]["risk_indicators"],
            time_window=result["metadata"]["time_window"],
            data_sources_json=result["metadata"]["data_sources"],
            
            # New Snapshot Columns
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
        print(f"Error persisting score: {e}")
        # Don't re-raise, we want to return the result to user even if save fails
