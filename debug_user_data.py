import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from models.database import SessionLocal
from models.models import User, VivIndex, FinancialScore

def debug_user():
    with open("debug_output.txt", "w") as f:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == "pro_test_prod@example.com").first()
            if not user:
                 f.write("User not found.\n")
                 return
            
            f.write(f"User ID: {user.id}\n")
            
            # Check VivIndex
            idx = db.query(VivIndex).filter(VivIndex.user_id == user.id).first()
            if idx:
                f.write(f"VivIndex Found: Fin={idx.financial_score}, Health={idx.health_score}, Time={idx.time_score}\n")
            else:
                f.write("VivIndex NOT FOUND.\n")

            # Check FinancialScore
            fs = db.query(FinancialScore).filter(FinancialScore.user_id == user.id).order_by(FinancialScore.timestamp.desc()).first()
            if fs:
                f.write(f"FinancialScore Found: Overall={fs.overall_score}\n")
                f.write(f"Subscores: Income={fs.income_stability_score}, Burn={fs.burn_rate_score}, Debt={fs.debt_stress_score}\n")
            else:
                f.write("FinancialScore NOT FOUND.\n")

            # Profile check
            profile = user.profile_json
            if profile:
                 f.write(f"Profile keys: {list(profile.keys())}\n")
            else:
                 f.write("Profile is None/Empty.\n")

        except Exception as e:
            f.write(f"Error: {e}\n")
        finally:
            db.close()

if __name__ == "__main__":
    debug_user()
