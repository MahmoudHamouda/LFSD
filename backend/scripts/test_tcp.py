
from sqlalchemy import create_engine, text

def test():
    print("Testing TCP Connection...")
    db_url = "postgresql+pg8000://postgres:LfsdSecure2024!@136.119.201.13/lfsd"
    try:
        engine = create_engine(db_url, echo=True)
        with engine.connect() as conn:
            print("Connected.")
            res = conn.execute(text("SELECT 1")).scalar()
            print(f"Result: {res}")
            print("Querying tables...")
            res2 = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' LIMIT 1")).fetchall()
            print(f"Tables: {res2}")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    test()
