import pg8000
import json

def check_tier_config():
    host = "136.119.201.13" 
    db_user = "lfsd_app"
    db_pass = "SecurePass123"
    db_name = "lfsd"
    
    try:
        conn = pg8000.connect(
            user=db_user,
            password=db_pass,
            host=host,
            database=db_name,
            timeout=10
        )
        cursor = conn.cursor()
        
        print("=== TIER CONFIGS ===")
        cursor.execute("SELECT plan_id, name, config_json FROM tier_configs")
        rows = cursor.fetchall()
        
        for row in rows:
            print(f"\nPlan: {row[0]} ({row[1]})")
            print(f"Config: {json.dumps(row[2], indent=2)}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tier_config()
