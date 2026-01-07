import os
import sqlalchemy
from sqlalchemy import text
from google.cloud.sql.connector import Connector, IPTypes

# Define the connection function
def getconn():
    with Connector() as connector:
        conn = connector.connect(
            "newprojectlfsd:us-central1:lfsd-sql-instance",
            "pg8000",
            user="postgres",
            password="newpassword123",
            db="lfsd_db",
            ip_type=IPTypes.PUBLIC,
        )
        return conn

# Create the engine
pool = sqlalchemy.create_engine(
    "postgresql+pg8000://",
    creator=getconn,
)

def check_data():
    with pool.connect() as db:
        # 1. Find the user
        print("--- User Record ---")
        result = db.execute(text("SELECT id, email, auth0_id, onboarding_status FROM users WHERE email = 'finance@helm.com'"))
        user = result.fetchone()
        
        if not user:
            print("❌ User finance@helm.com NOT FOUND in database.")
            return

        print(f"User Found: ID={user.id}, Auth0_ID={user.auth0_id}, Status={user.onboarding_status}")
        user_id = user.id

        # 2. Check Financial Data
        print("\n--- Financial Data ---")
        fin_res = db.execute(text(f"SELECT COUNT(*) FROM financial_data WHERE user_id = '{user_id}'"))
        fin_count = fin_res.scalar()
        print(f"Financial Records: {fin_count}")

        # 3. Check Goals
        print("\n--- Life Goals ---")
        goals_res = db.execute(text(f"SELECT COUNT(*) FROM life_goals WHERE user_id = '{user_id}'"))
        goals_count = goals_res.scalar()
        print(f"Goal Records: {goals_count}")

        # 4. Check Recommendations
        # Assuming table name is recommendations or similar (checking models might be needed if this fails)
        try:
            print("\n--- Recommendations ---")
            rec_res = db.execute(text(f"SELECT COUNT(*) FROM recommendations WHERE user_id = '{user_id}'"))
            rec_count = rec_res.scalar()
            print(f"Recommendation Records: {rec_count}")
        except Exception as e:
            print(f"Error checking recommendations: {e}")

if __name__ == "__main__":
    check_data()
