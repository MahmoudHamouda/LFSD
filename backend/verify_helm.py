import sys
import os

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models.database import SessionLocal
from models.models import User
from services.gemini_service import GeminiService

def verify_helm():
    print("Starting HELM Verification...")
    db = SessionLocal()
    service = GeminiService(db)
    
    try:
        # 1. Fetch Sara (Bio-Hacker)
        sara = db.query(User).filter(User.email == "sara@example.com").first()
        if not sara:
            print("ERROR: Sara not found. Seed script failed?")
            return

        print(f"Testing User: {sara.profile_json.get('name')}")
        
        # 2. Test Context Loading (Silent Average Fix)
        # Sara has seeds, but maybe no health data yet for Today?
        # seed_personas.py didn't seed HealthDailySummary, only VivIndex.
        # So health_data should be missing.
        context = service._load_viv_context(sara.id)
        
        print("\n[Test 1] Confidence Scores:")
        conf = context.get('confidence_scores', {})
        print(f"Confidence: {conf}")
        if conf.get('health') == 0.5:
             print("PASS: Health confidence correctly penalized due to missing data.")
        else:
             print(f"FAIL: Health confidence is {conf.get('health')}, expected 0.5")

        print("\n[Test 2] Financial Snapshot:")
        snap = context.get('financial_snapshot', {})
        print(f"Snapshot: {snap}")
        if snap.get('total_balance') == 2500.0:
            print("PASS: Financial balance correctly loaded (2500.0).")
        else:
            print(f"FAIL: Balance is {snap.get('total_balance')}, expected 2500.0")

        # 3. Test Deep Financial Guardrail
        print("\n[Test 3] Guardrail Simulation:")
        # Attempt to spend 3000 (Balance is 2500)
        intent = {'intent': 'financial_spend', 'amount': 3000, 'category': 'spa'}
        impact = service._simulate_impact(intent, context)
        
        goals = impact.get('goal_impact', [])
        print(f"Impact Analysis: {goals}")
        
        has_warning = any("exceeds your total balance" in g for g in goals)
        is_crisis = impact.get('crisis_override')
        
        if has_warning and is_crisis:
             print("PASS: Guardrail triggered CRITICAL warning and Crisis Mode.")
        else:
             print("FAIL: Guardrail failed to trigger.")

    except Exception as e:
        print(f"Verification Failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_helm()
