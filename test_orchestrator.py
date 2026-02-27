import asyncio
import os
os.environ["DATABASE_URL"] = "sqlite:///./backend/lfsd.db"

from backend.models import database
from backend.orchestration.master import Orchestrator

async def test():
    # Force initialize all mappers so local SA doesn't crash
    database.init_db()
    
    db = database.SessionLocal()
    llm = None
    orch = Orchestrator(db, llm=llm)
    
    msg = "I want to go from Jumeira Hotel to the airport"
    print(f"Testing message: {msg}")
    try:
        ans, meta = await orch.process_message(msg, "user123", {})
        print(f"Answer: {ans}")
        print(f"Meta: {meta}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
