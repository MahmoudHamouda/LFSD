from backend.models.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE time_scores_v2 ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 0.0"))
    conn.commit()
print("Done")
