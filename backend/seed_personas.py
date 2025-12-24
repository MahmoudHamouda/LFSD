from models.database import SessionLocal
from models.models import User, FinancialAccount, VivIndex
from core.authentication import get_password_hash
import uuid

def seed_personas():
    db = SessionLocal()
    password_hash = get_password_hash("password")
    
    personas = [
        {
            "id": "user-david",
            "email": "david@example.com",
            "name": "David (Pragmatist)",
            "profile": {"name": "David", "type": "Pragmatist", "bio": "Wealth accumulation focused. Risk averse."},
            "preferences": {"risk_tolerance": "low", "trade_off_rule": "profit_first"},
            "financials": {"balance": 150000.0, "income": 20000.0, "expenses": 4000.0},
            "indices": {"financial": 95, "health": 60, "time": 70}
        },
        {
            "id": "user-sara",
            "email": "sara@example.com",
            "name": "Sara (Bio-Hacker)",
            "profile": {"name": "Sara", "type": "Bio-Hacker", "bio": "Health optimization focused. Tight budget."},
            "preferences": {"risk_tolerance": "medium", "trade_off_rule": "health_first", "share_health_data": True},
            "financials": {"balance": 2500.0, "income": 3000.0, "expenses": 2800.0},
            "indices": {"financial": 40, "health": 95, "time": 50}
        },
        {
            "id": "user-alex",
            "email": "alex@example.com",
            "name": "Alex (Optimizer)",
            "profile": {"name": "Alex", "type": "Optimizer", "bio": "Efficiency focused. High value on time."},
            "preferences": {"risk_tolerance": "high", "trade_off_rule": "time_first"},
            "financials": {"balance": 50000.0, "income": 15000.0, "expenses": 10000.0},
            "indices": {"financial": 80, "health": 50, "time": 30} # Time stressed
        }
    ]

    print("Seeding Personas...")
    try:
        for p in personas:
            # Check if exists
            existing = db.query(User).filter(User.email == p["email"]).first()
            if not existing:
                print(f"Creating {p['name']}...")
                user = User(
                    id=p["id"],
                    email=p["email"],
                    hashed_password=password_hash,
                    profile_json=p["profile"],
                    viv_preferences=p["preferences"]
                )
                db.add(user)
                
                # Add Financial Account
                account = FinancialAccount(
                    user_id=p["id"],
                    institution_name="Bank of Simul",
                    account_type="checking",
                    current_balance=p["financials"]["balance"]
                )
                db.add(account)
                
                # Add Initial Viv Index
                index = VivIndex(
                    user_id=p["id"],
                    financial_score=p["indices"]["financial"],
                    health_score=p["indices"]["health"],
                    time_score=p["indices"]["time"],
                    snapshot_reason="Initial Seed"
                )
                db.add(index)
            else:
                print(f"{p['name']} already exists.")
        
        db.commit()
        print("Seeding Complete.")
    except Exception as e:
        print(f"Error seeding personas: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_personas()
