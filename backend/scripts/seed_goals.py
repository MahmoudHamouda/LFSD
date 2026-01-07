"""
Seed Goals for User Personas
Creates realistic goals for finance, health, time, and super users
"""
import sys
import os
from datetime import datetime, timedelta

# Add backend to path for model imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User, LifeGoal

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def seed_goals():
    print("=== SEEDING USER GOALS ===")
    
    session = Session()
    try:
        # Get all users
        users = {
            'finance': session.query(User).filter_by(email='finance@helm.com').first(),
            'health': session.query(User).filter_by(email='health@helm.com').first(),
            'time': session.query(User).filter_by(email='time@helm.com').first(),
            'super': session.query(User).filter_by(email='super@helm.com').first()
        }
        
        # Clear existing goals
        for persona, user in users.items():
            if user:
                deleted = session.query(LifeGoal).filter_by(user_id=user.id).delete()
                print(f"Cleared {deleted} existing goals for {persona}@helm.com")
        
        session.commit()
        
        # Define goals for each persona
        goals_data = {
            'finance': [
                {
                    'title': 'Emergency Fund',
                    'type': 'emergency_fund',
                    'pillar': 'finance',
                    'target_amount': 15000.0,
                    'saved_amount': 5000.0,
                    'target_date': datetime.utcnow() + timedelta(days=365),
                    'monthly_contribution_target': 833.0,
                    'priority': 'high'
                },
                {
                    'title': 'Down Payment for House',
                    'type': 'house',
                    'pillar': 'finance',
                    'target_amount': 60000.0,
                    'saved_amount': 12000.0,
                    'target_date': datetime.utcnow() + timedelta(days=730),
                    'monthly_contribution_target': 2000.0,
                    'priority': 'high'
                },
                {
                    'title': 'Vacation Fund',
                    'type': 'travel',
                    'pillar': 'finance',
                    'target_amount': 5000.0,
                    'saved_amount': 1500.0,
                    'target_date': datetime.utcnow() + timedelta(days=180),
                    'monthly_contribution_target': 583.0,
                    'priority': 'medium'
                }
            ],
            'health': [
                {
                    'title': 'Run a Marathon',
                    'type': 'custom',
                    'pillar': 'health',
                    'target_amount': 0.0,
                    'saved_amount': 0.0,
                    'target_date': datetime.utcnow() + timedelta(days=180),
                    'monthly_contribution_target': 0.0,
                    'priority': 'high'
                },
                {
                    'title': 'Lose 15 Pounds',
                    'type': 'custom',
                    'pillar': 'health',
                    'target_amount': 0.0,
                    'saved_amount': 0.0,
                    'target_date': datetime.utcnow() + timedelta(days=90),
                    'monthly_contribution_target': 0.0,
                    'priority': 'high'
                }
            ],
            'time': [
                {
                    'title': 'Complete Online Course',
                    'type': 'education',
                    'pillar': 'time',
                    'target_amount': 500.0,
                    'saved_amount': 500.0,
                    'target_date': datetime.utcnow() + timedelta(days=90),
                    'monthly_contribution_target': 0.0,
                    'priority': 'high'
                },
                {
                    'title': 'Establish Morning Routine',
                    'type': 'custom',
                    'pillar': 'time',
                    'target_amount': 0.0,
                    'saved_amount': 0.0,
                    'target_date': datetime.utcnow() + timedelta(days=30),
                    'monthly_contribution_target': 0.0,
                    'priority': 'medium'
                }
            ],
            'super': [
                {
                    'title': 'Retirement Savings',
                    'type': 'custom',
                    'pillar': 'finance',
                    'target_amount': 1000000.0,
                    'saved_amount': 150000.0,
                    'target_date': datetime.utcnow() + timedelta(days=7300),  # 20 years
                    'monthly_contribution_target': 3542.0,
                    'priority': 'high'
                },
                {
                    'title': 'Get Fit for Summer',
                    'type': 'custom',
                    'pillar': 'health',
                    'target_amount': 0.0,
                    'saved_amount': 0.0,
                    'target_date': datetime.utcnow() + timedelta(days=120),
                    'monthly_contribution_target': 0.0,
                    'priority': 'medium'
                },
                {
                    'title': 'Learn New Language',
                    'type': 'education',
                    'pillar': 'time',
                    'target_amount': 300.0,
                    'saved_amount': 300.0,
                    'target_date': datetime.utcnow() + timedelta(days=365),
                    'monthly_contribution_target': 0.0,
                    'priority': 'medium'
                },
                {
                    'title': 'New Car Fund',
                    'type': 'car',
                    'pillar': 'finance',
                    'target_amount': 35000.0,
                    'saved_amount': 8000.0,
                    'target_date': datetime.utcnow() + timedelta(days=540),
                    'monthly_contribution_target': 1500.0,
                    'priority': 'medium'
                }
            ]
        }
        
        # Create goals for each user
        total_created = 0
        for persona, user in users.items():
            if not user:
                print(f"⚠️  User {persona}@helm.com not found, skipping")
                continue
            
            persona_goals = goals_data.get(persona, [])
            for goal_data in persona_goals:
                goal = LifeGoal(
                    user_id=user.id,
                    title=goal_data['title'],
                    type=goal_data['type'],
                    pillar=goal_data['pillar'],
                    target_amount=goal_data['target_amount'],
                    saved_amount=goal_data['saved_amount'],
                    target_date=goal_data['target_date'],
                    monthly_contribution_target=goal_data['monthly_contribution_target'],
                    priority=goal_data['priority']
                )
                session.add(goal)
                total_created += 1
            
            print(f"✅ Created {len(persona_goals)} goals for {persona}@helm.com")
        
        session.commit()
        print(f"\n✅ Total goals created: {total_created}")
        
        # Verify
        print("\n=== VERIFICATION ===")
        for persona, user in users.items():
            if user:
                count = session.query(LifeGoal).filter_by(user_id=user.id).count()
                print(f"{persona}@helm.com: {count} goals")
                
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    seed_goals()
    print("\n✅ GOAL SEEDING COMPLETE")
