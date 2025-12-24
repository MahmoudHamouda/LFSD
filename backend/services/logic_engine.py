"""
Logic Engine for Viv.
Handles complex validation and business logic that requires more than just data retrieval.
"""
from typing import Tuple, Dict, Any

def validate_financial_goal(goal_amount: float, current_financials: Dict[str, float]) -> Tuple[bool, str]:
    """
    Validate if a financial goal is mathematically possible given current financials.
    
    Args:
        goal_amount: The amount the user wants to save or spend.
        current_financials: Dictionary containing 'total_income', 'fixed_expenses', etc.
        
    Returns:
        Tuple (is_valid, message)
    """
    total_income = current_financials.get('total_income', 0.0)
    fixed_expenses = current_financials.get('fixed_expenses', 0.0)
    
    # Calculate disposable income
    disposable_income = total_income - fixed_expenses
    
    if goal_amount > disposable_income:
        return False, (
            f"I cannot set this goal. Your fixed expenses ({fixed_expenses}) plus this goal ({goal_amount}) "
            f"exceed your total income ({total_income}). You would be in debt by {goal_amount - disposable_income}."
        )
        
    return True, "Goal is feasible."
