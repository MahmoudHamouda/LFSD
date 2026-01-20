import pg8000
import sqlalchemy

def fix_all():
    # Direct Public IP connection since 0.0.0.0/0 is allowed
    host = "136.119.201.13" 
    db_user = "postgres"
    db_pass = "LfsdSecure2024!"
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
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected. Dropping tables...")
        tables = [
            "chat_history", "chat_sessions", "feedback", 
            "notifications", "tier_configs", "user_limit_overrides", 
            "subscriptions", "users", "alembic_version"
        ]
        
        for t in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
                print(f"Dropped {t}")
            except Exception as e:
                print(f"Error dropping {t}: {e}")
                
        print("Granting schema permissions...")
        cursor.execute("GRANT ALL ON SCHEMA public TO lfsd_app")
        # Ensure lfsd_app can create objects
        cursor.execute("GRANT CREATE ON SCHEMA public TO lfsd_app")
        # Try ownership change (might fail if not superuser, but postgres usually is)
        try:
            cursor.execute("ALTER SCHEMA public OWNER TO lfsd_app")
            print("Changed schema owner.")
        except Exception as e:
            print(f"Could not change owner (non-critical): {e}")

        conn.close()
        print("FIX INSTALLED.")
        
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")

if __name__ == "__main__":
    fix_all()
