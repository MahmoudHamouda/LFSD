from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from models.models import FinancialAccount, FinancialTransaction
from models.investment_portfolios import InvestmentPortfolio
from models.database import get_db

class FinanceService:
    def __init__(self, db: Session):
        self.db = db

    def get_net_worth(self, user_id: str) -> float:
        """Calculate total net worth."""
        accounts = self.db.query(FinancialAccount).filter(FinancialAccount.user_id == user_id).all()
        portfolios = self.db.query(InvestmentPortfolio).filter(InvestmentPortfolio.user_id == user_id).all()
        
        cash_balance = sum(acc.current_balance for acc in accounts)
        investments_balance = sum(port.total_value for port in portfolios)
        
        return cash_balance + investments_balance

    def get_portfolio_performance(self, user_id: str) -> dict:
        """Get aggregated portfolio performance."""
        portfolios = self.db.query(InvestmentPortfolio).filter(InvestmentPortfolio.user_id == user_id).all()
        
        if not portfolios:
            return {"total_value": 0, "daily_change_percent": 0}
            
        total_value = sum(p.total_value for p in portfolios)
        weighted_change = sum(p.daily_change_percent * (p.total_value / total_value) for p in portfolios if total_value > 0)
        
        return {
            "total_value": total_value,
            "daily_change_percent": round(weighted_change, 2)
        }

    def add_transaction(self, user_id: str, transaction_data: dict) -> FinancialTransaction:
        """Add a manual transaction."""
        transaction = FinancialTransaction(
            user_id=user_id,
            account_id=transaction_data.get("account_id"),
            amount=transaction_data.get("amount"),
            merchant_name=transaction_data.get("merchant_name"),
            category_primary=transaction_data.get("category"),
            transaction_date=datetime.utcnow()
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
        """Calculate monthly financial summary (Income, Expenses, Bills, Savings)."""
        from datetime import timedelta
        # Simple logic: Aggregates for last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        transactions = self.db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.transaction_date >= cutoff_date
        ).all()
        
        current_investments = self.get_portfolio_performance(user_id)["total_value"]
        
        income = 0.0
        expenses = 0.0
        recurring_bills = 0.0
        
        for txn in transactions:
            amount = txn.amount
            # Assumption: Negative amount is expense, Positive is income (or vice versa depending on ingestion)
            # Typically in banking apps: -100 is spend.
            # But let's check how StatementService handles it. 
            # If standard convention: < 0 is expense.
            
            if amount > 0:
                income += amount
            else:
                expenses += abs(amount) # convert to positive for display
                # Simple heuristic for bills: category check
                if txn.category_primary in ['Subscription', 'Bills', 'Utilities']:
                    recurring_bills += abs(amount)
                    
        monthly_savings = income - expenses
        
        return {
            "total_income": round(income, 2),
            "total_expenses": round(expenses, 2),
            "recurring_bills": round(recurring_bills, 2),
            "monthly_savings": round(monthly_savings, 2),
            "current_investments": round(current_investments, 2)
        }
