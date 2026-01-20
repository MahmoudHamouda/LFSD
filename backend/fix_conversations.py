import pg8000

def fix_conversations():
    host = "136.119.201.13" 
    
    print("Connecting as postgres...")
    try:
        conn = pg8000.connect(
            user="postgres",
            password="LfsdSecure2024!",
            host=host,
            database="lfsd",
            timeout=10
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Adding user_id to conversations...")
        try:
            cursor.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS user_id VARCHAR;")
            print("Column Added.")
        except Exception as e:
            print(f"Add column failed: {e}")

        # Fix ownership
        cursor.execute("SELECT tableowner FROM pg_tables WHERE tablename = 'conversations'")
        owner = cursor.fetchone()[0]
        print(f"Owner of conversations: {owner}")
        
        if owner != 'lfsd_app':
            print("Changing owner to lfsd_app...")
            cursor.execute("ALTER TABLE conversations OWNER TO lfsd_app;")
            print("Owner changed.")
            
        conn.close()
        print("Done.")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    fix_conversations()
