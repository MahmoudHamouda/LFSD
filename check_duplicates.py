from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def check_dupes():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("Checking for duplicate emails...")
            res = conn.execute(text("""
                SELECT email, count(*), array_agg(id) 
                FROM users 
                GROUP BY email 
                HAVING count(*) > 1
            """)).fetchall()
            
            if not res:
                print("No duplicates found.")
            else:
                for r in res:
                    print(f"Duplicate: {r[0]} - Count: {r[1]}")
                    print(f"IDs: {r[2]}")
            
            # Specifically check 'time@helm.com'
            t_user = conn.execute(text("SELECT id, email, created_at FROM users WHERE email='time@helm.com'")).fetchall()
            print("\nTime Users:")
            for u in t_user:
                print(u)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_dupes()
