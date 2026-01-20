import pg8000
import json

def debug_user_state(email: str):
    # Direct Public IP connection
    host = "136.119.201.13" 
    db_user = "lfsd_app"
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
        cursor = conn.cursor()
        
        # 1. Fetch User
        print(f"\n--- Checking User {email} ---")
        cursor.execute("SELECT id, email, onboarding_status FROM users WHERE email = %s", (email,))
        user_row = cursor.fetchone()
        
        if not user_row:
            print("❌ User NOT FOUND in users table.")
            return
            
        user_id = user_row[0]
        print(f"✅ User Found: ID={user_id}, Status={user_row[2]}")
        
        # 2. Fetch Subscription
        print(f"\n--- Checking Subscription for User {user_id} ---")
        cursor.execute("SELECT id, plan_id, status FROM subscriptions WHERE user_id = %s", (user_id,))
        sub_row = cursor.fetchone()
        
        if not sub_row:
            print("❌ Subscription NOT FOUND for this user.")
        else:
            plan_id = sub_row[1]
            print(f"✅ Subscription Found: Plan={plan_id}, Status={sub_row[2]}")
            
            # 3. Fetch Tier Config
            print(f"\n--- Checking Tier Config for Plan {plan_id} ---")
            cursor.execute("SELECT id, plan_id, config_json FROM tier_configs WHERE plan_id = %s", (plan_id,))
            tier_row = cursor.fetchone()
            
            if not tier_row:
                print(f"❌ Tier Config NOT FOUND for plan '{plan_id}'.")
            else:
                config_json = tier_row[2]
                print(f"✅ Tier Config Found:")
                print(json.dumps(config_json, indent=2))

        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_user_state("finance@helm.com")
