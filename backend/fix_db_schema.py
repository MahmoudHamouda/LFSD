from models.database import engine
from sqlalchemy import text

def reset_chat_tables():
    with engine.connect() as conn:
        print("Dropping chat and notification tables...")
        conn.execute(text("DROP TABLE IF EXISTS chat_sessions;"))
        conn.execute(text("DROP TABLE IF EXISTS chat_history;"))
        conn.execute(text("DROP TABLE IF EXISTS chat_summaries;"))
        conn.execute(text("DROP TABLE IF EXISTS feedback;"))
        conn.execute(text("DROP TABLE IF EXISTS notifications;"))
        conn.commit()
        print("Dropped.")

if __name__ == "__main__":
    reset_chat_tables()
