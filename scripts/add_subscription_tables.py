import sys
import os
from sqlalchemy import create_engine, text
import json

# Add parent directory to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "backend"))

# Use database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lfsd_v2.db")

def migrate_subscription_tables():
    print(f"Connecting to database at {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            with conn.begin():
                # 1. Create tier_configs table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS tier_configs (
                        id VARCHAR PRIMARY KEY,
                        plan_id VARCHAR UNIQUE NOT NULL,
                        name VARCHAR NOT NULL,
                        description VARCHAR,
                        config_json JSON NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # 2. Create user_limit_overrides table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_limit_overrides (
                        id VARCHAR PRIMARY KEY,
                        user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        overrides_json JSON NOT NULL,
                        reason VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # 3. Seed initial tiers
                free_config = {
                    "features": ["basic_charts", "limit_5_goals", "basic_insight"],
                    "limits": {
                        "goals": 5,
                        "history_months": 3,
                        "ai_queries_per_day": 5
                    }
                }
                pro_config = {
                    "features": ["advanced_charts", "unlimited_goals", "deep_insight", "forecasting"],
                    "limits": {
                        "goals": -1,
                        "history_months": -1,
                        "ai_queries_per_day": -1
                    }
                }
                
                # Upsert Free
                conn.execute(text("""
                    INSERT INTO tier_configs (id, plan_id, name, config_json)
                    VALUES ('tier_free_id', 'tier_free', 'Free Tier', :config)
                    ON CONFLICT (plan_id) DO UPDATE SET config_json = :config
                """), {"config": json.dumps(free_config)})
                
                # Upsert Pro
                conn.execute(text("""
                    INSERT INTO tier_configs (id, plan_id, name, config_json)
                    VALUES ('tier_pro_id', 'tier_pro', 'Pro Tier', :config)
                    ON CONFLICT (plan_id) DO UPDATE SET config_json = :config
                """), {"config": json.dumps(pro_config)})
                
            print("Subscription tables created and seeded successfully.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_subscription_tables()
