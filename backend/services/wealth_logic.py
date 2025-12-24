"""
Wealth Logic Helper Module
"""
from typing import Dict, Optional

def validate_financial_goal(goal_amount: float, context_data: Dict) -> Optional[str]:
    """
    Validates if a financial goal is realistic based on income and fixed expenses.
    
    Args:
        goal_amount: The amount the user wants to save or spend.
        context_data: Dictionary containing financial context (income, fixed_expenses).
        
    Returns:
        None if the goal is valid.
        Error string if the goal is unrealistic.
    """
    # Extract context data with defaults
    # In a real scenario, these would come from the user's profile or DB
    monthly_income = context_data.get('monthly_income', 5000.0) 
    fixed_expenses = context_data.get('fixed_expenses', 2500.0)
    
    # Calculate disposable income
    disposable_income = monthly_income - fixed_expenses
    
    # Check if goal exceeds disposable income
    # We assume the goal amount is a monthly target for this validation logic
    if goal_amount > disposable_income:
        return f"Unrealistic Goal: You cannot allocate {goal_amount} when your fixed costs are {fixed_expenses} and income is {monthly_income} (Disposable: {disposable_income})."
        
    # Check for extreme savings ratio (e.g., trying to save > 90% of income)
    if goal_amount > (monthly_income * 0.9):
         return f"Unrealistic Goal: You cannot save {goal_amount} (over 90% of income) when you have fixed costs."

    return None
