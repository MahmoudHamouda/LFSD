"""
Logic Engine for HELM.
Handles complex validation and business logic that requires more than just data retrieval.
"""
from typing import Tuple, Dict, Any, Optional
from services.wealth_logic import validate_monthly_allocation

def validate_cashflow_feasibility(
    allocation_amount: float, 
    financial_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validates if a specific allocation fits within monthly cashflow constraints.
    Canonical implementation delegates to wealth_logic.validate_monthly_allocation.
    
    Args:
        allocation_amount: Amount to check (monthly basis).
        financial_context: Dict containing 'monthly_income', 'fixed_expenses', etc.
        
    Returns:
        Structured dictionary with 'valid' (bool), 'message' (str), 'error_type' (str).
    """
    # Map input keys if necessary (logic_engine used 'total_income', wealth_logic uses 'monthly_income')
    # We normalize here to ensure compatibility
    context = financial_context.copy()
    if 'total_income' in context and 'monthly_income' not in context:
        context['monthly_income'] = context['total_income']
        
    return validate_monthly_allocation(allocation_amount, context)

def validate_financial_goal(goal_amount: float, current_financials: Dict[str, float]) -> Tuple[bool, str]:
    """
    DEPRECATED: Use validate_cashflow_feasibility instead.
    Wrapper for backward compatibility.
    """
    result = validate_cashflow_feasibility(goal_amount, current_financials)
    return result["valid"], result["message"]

