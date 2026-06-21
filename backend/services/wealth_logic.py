from typing import Dict, Optional, Any, Union


def validate_monthly_allocation(
    allocation_amount: float, context_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validates if a monthly financial allocation (saving or spending) is realistic.

    Args:
        allocation_amount: The monthly amount to allocate (must be > 0).
        context_data: Dictionary containing financial context.
                      Must include: 'monthly_income', 'fixed_expenses'.
                      Optional: 'variable_expenses', 'debt_payments'.

    Returns:
        Dictionary with:
            - valid (bool): True if feasible.
            - message (str): User-facing explanation.
            - error_type (str, optional): machine-readable error code.
    """
    # 1. Input Validation
    if not isinstance(allocation_amount, (int, float)) or allocation_amount <= 0:
        return {
            "valid": False,
            "message": "Allocation amount must be a positive number.",
            "error_type": "INVALID_INPUT",
        }

    required_keys = ["monthly_income", "fixed_expenses"]
    missing_keys = [k for k in required_keys if k not in context_data]
    if missing_keys:
        return {
            "valid": False,
            "message": f"Missing financial data for validation: {', '.join(missing_keys)}",
            "error_type": "MISSING_CONTEXT",
        }

    try:
        monthly_income = float(context_data["monthly_income"])
        fixed_expenses = float(context_data["fixed_expenses"])
        # Optional fields default to 0
        variable_expenses = float(context_data.get("variable_expenses", 0))
        debt_payments = float(context_data.get("debt_payments", 0))
    except (ValueError, TypeError):
        return {
            "valid": False,
            "message": "Financial context data must be numeric.",
            "error_type": "INVALID_CONTEXT_TYPE",
        }

    # 2. Logic Validation
    if monthly_income <= 0:
        return {
            "valid": False,
            "message": "Monthly income must be positive to validate goals.",
            "error_type": "ZERO_INCOME",
        }

    # Calculate comprehensive disposable income
    # Disposable = Income - (Fixed + Debt + Variable)
    # Variable expenses are often flexible, but existing debt and fixed bills are not.
    committed_outflows = fixed_expenses + debt_payments
    discretionary_baseline = monthly_income - committed_outflows

    # Check Base Feasibility (Cashflow Negative)
    if discretionary_baseline < 0:
        return {
            "valid": False,
            "message": "You are currently cashflow negative (Expenses > Income). Focus on stabilizing finances before adding new goals.",
            "error_type": "NEGATIVE_CASHFLOW",
        }

    # Now consider variable expenses if we want a conservative check,
    # but strictly speaking, variable expenses *can* be cut for a goal.
    # However, let's subtract them for a "Maintainable" check.
    net_available = discretionary_baseline - variable_expenses

    # If net_available is negative, it means they are spending more than they earn due to lifestyle (variable),
    # even if fixed costs are covered. They technically *could* save if they cut lifestyle.
    # So we check against discretionary_baseline (Hard Limit) and net_available (Soft Limit).

    # HARD CHECK: Can't afford even without variable expenses?
    if allocation_amount > discretionary_baseline:
        return {
            "valid": False,
            "message": f"This amount exceeds your income after fixed costs and debts.",
            "error_type": "INSUFFICIENT_FUNDS_HARD",
        }

    # SOFT CHECK: Can't afford with current lifestyle?
    if allocation_amount > net_available:
        shortfall = allocation_amount - net_available
        # Valid but requires trade-off
        return {
            "valid": True,
            "message": f"Feasible, but requires reducing variable spending by {abs(shortfall):.0f} to maintain cashflow neutrality.",
            "warning": "LIFESTYLE_TRADE_OFF",
        }

    # 3. Buffer Check (Safety Margin)
    # Ensure they aren't allocating 100% of every last penny
    remaining_buffer = net_available - allocation_amount
    buffer_ratio = remaining_buffer / monthly_income

    if buffer_ratio < 0.02:  # Less than 2% buffer is dangerous
        return {
            "valid": True,
            "message": "This is mathematically possible but looks very tight (leaves <2% buffer).",
            "warning": "LOW_BUFFER",
        }

    return {
        "valid": True,
        "message": "Goal allocation appears feasible and sustainable.",
    }


def validate_financial_goal(goal_amount: float, context_data: Dict) -> Optional[str]:
    """
    Deprecated Wrapper: references validate_monthly_allocation.
    Returns None if valid, error string if invalid.
    """
    result = validate_monthly_allocation(goal_amount, context_data)
    if not result["valid"]:
        return result["message"]
    return None
