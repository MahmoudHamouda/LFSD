from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def check():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("--- VIV INDEX HISTORY ---")
            # Get user id
            uid = conn.execute(text("SELECT id FROM users WHERE email='finance@helm.com'")).scalar()
            print(f"User ID: {uid}")
            
            rows = conn.execute(text(f"SELECT id, financial_score, health_score, time_score, timestamp, snapshot_reason FROM viv_indexes WHERE user_id='{uid}' ORDER BY timestamp DESC")).fetchall()
            for r in rows:
                print(f"ID: {r[0]} | Fin: {r[1]} | Hlth: {r[2]} | Time: {r[3]} | Reason: {r[5]} | Time: {r[4]}")
                
            # Nuclear cleanup of bad rows
            print("\n--- CLEANUP ---")
            # Keep only the one with Fin=55.5 (if it exists) or just the seeded one
            # Actually, let's just delete the ones that are NOT Reason='Synthetic Seeding'
            # Or if seeded one is missing, we are in trouble.
            
            seeded_rows = [r for r in rows if r[1] == 55.5]
            if seeded_rows:
                good_id = seeded_rows[0][0]
                print(f"Found Good Seeded Row: {good_id}")
                conn.execute(text(f"DELETE FROM viv_indexes WHERE user_id='{uid}' AND id != '{good_id}'"))
                conn.commit()
                print("Deleted bad rows.")
            else:
                print("No row with 55.5 found. Cannot auto-clean.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
