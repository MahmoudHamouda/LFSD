
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.models import LifeGoal
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def recategorize_goals():
    if not DATABASE_URL:
        print("DATABASE_URL not found.")
        return

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    time_keywords = ["deep work", "focus", "productivity", "time", "hours", "context switch", "schedule"]
    health_keywords = ["sleep", "health", "workout", "run", "walk", "nutrition", "fitness", "recovery"]
    finance_keywords = ["save", "fund", "debt", "invest", "money", "$", "financial", "cashflow"]

    try:
        goals = session.query(LifeGoal).all()
        print(f"Total goals to process: {len(goals)}")
        
        updates = 0
        for goal in goals:
            title_lower = goal.title.lower()
            old_pillar = goal.pillar
            new_pillar = "finance" # Default

            if any(k in title_lower for k in time_keywords):
                new_pillar = "time"
            elif any(k in title_lower for k in health_keywords):
                new_pillar = "health"
            elif any(k in title_lower for k in finance_keywords):
                new_pillar = "finance"
            
            if old_pillar != new_pillar:
                goal.pillar = new_pillar
                updates += 1
                # print(f"Updated: '{goal.title}' -> {new_pillar}")

        session.commit()
        print(f"Recategorization complete. Updated {updates} goals.")

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    recategorize_goals()
