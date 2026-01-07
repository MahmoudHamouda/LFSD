"""
Update Goals with Appropriate Target Types
- Time goals: use hours as target_amount
- Health goals: use health metrics (steps, sleep hours, weight) as target_amount
- Finance goals: keep monetary amounts
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User, LifeGoal

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def update_goals():
    print("=== UPDATING GOALS WITH APPROPRIATE TARGETS ===")
    
    session = Session()
    try:
        # Get all users
        users = {
            'finance': session.query(User).filter_by(email='finance@helm.com').first(),
            'health': session.query(User).filter_by(email='health@helm.com').first(),
            'time': session.query(User).filter_by(email='time@helm.com').first(),
            'super': session.query(User).filter_by(email='super@helm.com').first()
        }
        
        # Clear all existing goals
        for persona, user in users.items():
            if user:
                deleted = session.query(LifeGoal).filter_by(user_id=user.id).delete()
                print(f"Cleared {deleted} goals for {persona}@helm.com")
        
        session.commit()
        
        # Create new goals with appropriate targets
        all_goals = []
        
        # FINANCE USER - Monetary goals
        if users['finance']:
            all_goals.extend([
                LifeGoal(
                    user_id=users['finance'].id,
                    title='Emergency Fund',
                    type='emergency_fund',
                    pillar='finance',
                    target_amount=15000.0,  # $15,000
                    saved_amount=5000.0,
                    target_date=datetime.utcnow() + timedelta(days=365),
                    monthly_contribution_target=833.0,
                    priority='high'
                ),
                LifeGoal(
                    user_id=users['finance'].id,
                    title='Down Payment for House',
                    type='house',
                    pillar='finance',
                    target_amount=60000.0,  # $60,000
                    saved_amount=12000.0,
                    target_date=datetime.utcnow() + timedelta(days=730),
                    monthly_contribution_target=2000.0,
                    priority='high'
                ),
                LifeGoal(
                    user_id=users['finance'].id,
                    title='Vacation Fund',
                    type='travel',
                    pillar='finance',
                    target_amount=5000.0,  # $5,000
                    saved_amount=1500.0,
                    target_date=datetime.utcnow() + timedelta(days=180),
                    monthly_contribution_target=583.0,
                    priority='medium'
                )
            ])
        
        # HEALTH USER - Health metric goals
        if users['health']:
            all_goals.extend([
                LifeGoal(
                    user_id=users['health'].id,
                    title='Run a Marathon',
                    type='custom',
                    pillar='health',
                    target_amount=42.2,  # 42.2 km
                    saved_amount=21.0,  # Currently can run 21km
                    target_date=datetime.utcnow() + timedelta(days=180),
                    monthly_contribution_target=0.0,
                    priority='high'
                ),
                LifeGoal(
                    user_id=users['health'].id,
                    title='Lose 15 Pounds',
                    type='custom',
                    pillar='health',
                    target_amount=15.0,  # 15 pounds to lose
                    saved_amount=5.0,  # Already lost 5 pounds
                    target_date=datetime.utcnow() + timedelta(days=90),
                    monthly_contribution_target=0.0,
                    priority='high'
                ),
                LifeGoal(
                    user_id=users['health'].id,
                    title='Daily Steps Goal',
                    type='custom',
                    pillar='health',
                    target_amount=10000.0,  # 10,000 steps per day
                    saved_amount=7500.0,  # Current average
                    target_date=datetime.utcnow() + timedelta(days=30),
                    monthly_contribution_target=0.0,
                    priority='medium'
                )
            ])
        
        # TIME USER - Time-based goals (hours)
        if users['time']:
            all_goals.extend([
                LifeGoal(
                    user_id=users['time'].id,
                    title='Complete Online Course',
                    type='education',
                    pillar='time',
                    target_amount=40.0,  # 40 hours total
                    saved_amount=25.0,  # 25 hours completed
                    target_date=datetime.utcnow() + timedelta(days=90),
                    monthly_contribution_target=5.0,  # 5 hours per month
                    priority='high'
                ),
                LifeGoal(
                    user_id=users['time'].id,
                    title='Establish Morning Routine',
                    type='custom',
                    pillar='time',
                    target_amount=30.0,  # 30 days of consistency
                    saved_amount=15.0,  # 15 days completed
                    target_date=datetime.utcnow() + timedelta(days=30),
                    monthly_contribution_target=0.0,
                    priority='medium'
                ),
                LifeGoal(
                    user_id=users['time'].id,
                    title='Read 12 Books This Year',
                    type='custom',
                    pillar='time',
                    target_amount=12.0,  # 12 books
                    saved_amount=4.0,  # 4 books completed
                    target_date=datetime.utcnow() + timedelta(days=365),
                    monthly_contribution_target=1.0,  # 1 book per month
                    priority='medium'
                )
            ])
        
        # SUPER USER - Mixed goals across all pillars
        if users['super']:
            all_goals.extend([
                LifeGoal(
                    user_id=users['super'].id,
                    title='Retirement Savings',
                    type='custom',
                    pillar='finance',
                    target_amount=1000000.0,  # $1M
                    saved_amount=150000.0,
                    target_date=datetime.utcnow() + timedelta(days=7300),
                    monthly_contribution_target=3542.0,
                    priority='high'
                ),
                LifeGoal(
                    user_id=users['super'].id,
                    title='Get Fit for Summer',
                    type='custom',
                    pillar='health',
                    target_amount=20.0,  # Lose 20 pounds
                    saved_amount=5.0,
                    target_date=datetime.utcnow() + timedelta(days=120),
                    monthly_contribution_target=0.0,
                    priority='medium'
                ),
                LifeGoal(
                    user_id=users['super'].id,
                    title='Learn Spanish',
                    type='education',
                    pillar='time',
                    target_amount=200.0,  # 200 hours of study
                    saved_amount=50.0,
                    target_date=datetime.utcnow() + timedelta(days=365),
                    monthly_contribution_target=12.5,  # 12.5 hours per month
                    priority='medium'
                ),
                LifeGoal(
                    user_id=users['super'].id,
                    title='New Car Fund',
                    type='car',
                    pillar='finance',
                    target_amount=35000.0,  # $35,000
                    saved_amount=8000.0,
                    target_date=datetime.utcnow() + timedelta(days=540),
                    monthly_contribution_target=1500.0,
                    priority='medium'
                )
            ])
        
        # Add all goals
        for goal in all_goals:
            session.add(goal)
        
        session.commit()
        print(f"\n✅ Created {len(all_goals)} goals with appropriate targets")
        
        # Verify
        print("\n=== VERIFICATION ===")
        for persona, user in users.items():
            if user:
                goals = session.query(LifeGoal).filter_by(user_id=user.id).all()
                print(f"\n{persona}@helm.com ({len(goals)} goals):")
                for goal in goals:
                    unit = "$" if goal.pillar == "finance" else ("hrs" if goal.pillar == "time" else "units")
                    print(f"  - {goal.title}: {goal.saved_amount}/{goal.target_amount} {unit}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    update_goals()
    print("\n✅ GOAL UPDATE COMPLETE")
