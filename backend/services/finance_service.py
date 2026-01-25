from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Literal
import uuid
from models.models import FinancialAccount, FinancialTransaction
try:
    from models.investment_portfolios import InvestmentPortfolio
except ImportError:
    InvestmentPortfolio = None
    logger.warning("InvestmentPortfolio model not found. Portfolio features disabled.")
from loguru import logger 

class FinanceService:
    def __init__(self, db: Session):
        self.db = db

    def get_net_worth(self, user_id: str) -> float:
        """
        Calculate total net worth (Assets - Liabilities).
        - Assets: Savings, Checking, Investments
        - Liabilities: Credit, Loans
        """
        accounts = self.db.query(FinancialAccount).filter(FinancialAccount.user_id == user_id).all()
        
        portfolios = []
        if InvestmentPortfolio:
            portfolios = self.db.query(InvestmentPortfolio).filter(InvestmentPortfolio.user_id == user_id).all()
        
        assets = 0.0
        liabilities = 0.0
        
        for acc in accounts:
            # Normalize type string
            acc_type = (acc.account_type or "").lower()
            balance = acc.current_balance or 0.0
            
            if acc_type in ["credit", "loan", "mortgage", "liability"]:
                liabilities += abs(balance) # Assume balance is amount owed
            else:
                assets += balance
                
        investments_value = sum((p.total_value or 0.0) for p in portfolios)
        assets += investments_value
        
        return round(assets - liabilities, 2)

        """Get aggregated portfolio performance."""
        if not InvestmentPortfolio:
             return {"total_value": 0, "daily_change_percent": 0}
             
        portfolios = self.db.query(InvestmentPortfolio).filter(InvestmentPortfolio.user_id == user_id).all()
        
        if not portfolios:
            return {"total_value": 0, "daily_change_percent": 0}
            
        total_value = sum((p.total_value or 0.0) for p in portfolios)
        
        # Weighted Average Change
        weighted_change = 0.0
        if total_value > 0:
            for p in portfolios:
                val = p.total_value or 0.0
                change = p.daily_change_percent or 0.0
                weighted_change += change * (val / total_value)
        
        return {
            "total_value": round(total_value, 2),
            "daily_change_percent": round(weighted_change, 2)
        }

    def add_transaction(self, user_id: str, transaction_data: dict) -> FinancialTransaction:
        """
        Add a manual transaction with strictly enforced sign convention.
        
        Direction Rule:
        - CREDIT (Income) -> Amount stored as POSITIVE
        - DEBIT (Expense) -> Amount stored as NEGATIVE
        """
        raw_amount = float(transaction_data.get("amount", 0))
        direction = transaction_data.get("direction", "DEBIT").upper() # Default to expense if unspecified
        
        # Normalize Sign
        if direction == "DEBIT":
            final_amount = -abs(raw_amount)
        elif direction == "CREDIT":
            final_amount = abs(raw_amount)
        else:
            # Fallback if direction is unknown but amount implies something? 
            # Safer to default to negative if ambiguous to avoid inflating income
            final_amount = -abs(raw_amount) 
            
        transaction = FinancialTransaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=transaction_data.get("account_id"),
            amount=final_amount, 
            merchant_name=transaction_data.get("merchant_name"),
            category_primary=transaction_data.get("category"),
            description=transaction_data.get("description"), # Ensure this is passed
            transaction_date=datetime.utcnow(),
            currency_code=transaction_data.get("currency_code", "USD")
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def get_accounts(self, user_id: str) -> List[FinancialAccount]:
        """Get all financial accounts."""
        return self.db.query(FinancialAccount).filter(FinancialAccount.user_id == user_id).all()

    def get_transactions(self, user_id: str, limit: int = 20) -> List[FinancialTransaction]:
        """Get recent transactions."""
        return self.db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id
        ).order_by(FinancialTransaction.transaction_date.desc()).limit(limit).all()

    def get_monthly_summary(self, user_id: str) -> dict:
        """
        Calculate monthly financial summary.
        Convention: 
        - Income = Sum of Positive Txns
        - Expenses = Sum of ABS(Negative Txns) 
        - Bills = Subset of Expenses (do NOT double count in total expenses, but return separate metric)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        transactions = self.db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.transaction_date >= cutoff_date
        ).all()
        
        current_investments = self.get_portfolio_performance(user_id)["total_value"]
        
        income = 0.0
        expenses = 0.0
        recurring_bills = 0.0
        
        bill_categories = {'subscription', 'bills', 'utilities', 'recurring', 'insurance', 'rent'}
        
        for txn in transactions:
            amount = txn.amount or 0.0
            
            if amount > 0:
                income += amount
            else:
                abs_amt = abs(amount)
                expenses += abs_amt
                
                # Check for Bill (Normalized check)
                cat_primary = (txn.category_primary or "").lower()
                cat_detailed = (txn.category_detailed or "").lower()
                
                if cat_primary in bill_categories or cat_detailed in bill_categories or txn.is_recurring:
                    recurring_bills += abs_amt
                    
        monthly_savings = income - expenses
        
        return {
            "total_income": round(income, 2),
            "total_expenses": round(expenses, 2),
            "recurring_bills": round(recurring_bills, 2), # This is a subset/highlight, not added to expenses
            "monthly_savings": round(monthly_savings, 2),
            "current_investments": round(current_investments, 2)
        }

