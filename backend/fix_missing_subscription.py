import pg8000
import uuid
import datetime

def fix_user_subscription(email: str):
    # Direct Public IP connection
    host = "136.119.201.13" 
    db_user = "lfsd_app"     # Use the app user we created
    db_pass = "SecurePass123"
    db_name = "lfsd"
    
    print(f"Connecting to {host} as {db_user}...")
    
    try:
        conn = pg8000.connect(
            user=db_user,
            password=db_pass,
            host=host,
            database=db_name,
            timeout=10
        )
        conn.autocommit = False # We want transaction
        cursor = conn.cursor()
        
        # 1. Find User
        print(f"Looking for user {email}...")
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
        
        if not result:
            print("User not found!")
            return
            
        user_id = result[0]
        print(f"Found User ID: {user_id}")
        
        # 2. Check Subscription
        cursor.execute("SELECT id FROM subscriptions WHERE user_id = %s", (user_id,))
        sub_result = cursor.fetchone()
        
        if sub_result:
            print("Subscription already exists.")
            return

        # 3. Create Subscription
        print("Creating Free Subscription...")
        sub_id = str(uuid.uuid4())
        # Default dates
        now = datetime.datetime.utcnow()
        
        # SQL Insert
        cursor.execute("""
            INSERT INTO subscriptions (
                id, user_id, plan_id, status, 
                current_period_start, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            sub_id, user_id, "tier_free", "active",
            now, now, now
        ))
        
        conn.commit()
        print("Success! Subscription inserted.")
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_user_subscription("finance@helm.com")
