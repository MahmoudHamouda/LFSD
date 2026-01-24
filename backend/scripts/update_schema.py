from sqlalchemy import create_engine
import os
import sys

# Add services to path to import models
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.chat_service.models import Base as ChatBase
from services.notification_service.models import Base as NotifBase
from services.user_management_service.models import Base as UserBase
from backend.models.growth_models import Base as GrowthBase
# Import other bases if needed, or just these for now

db_path = os.path.join(os.getcwd(), 'backend', 'lfsd.db')
engine = create_engine(f'sqlite:///{db_path}')
from sqlalchemy import create_engine, text

# We use raw SQL because conflicting Base classes prevent cross-service FK resolution in simple scripts
with engine.connect() as conn:
    print("Creating tables via SQL...")
    
    # Users (Core)
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS users_v2 (
        id VARCHAR(50) PRIMARY KEY,
        email VARCHAR(100) UNIQUE NOT NULL,
        auth0_id VARCHAR(100) UNIQUE,
        hashed_password VARCHAR(255),
        profile_json JSON,
        viv_preferences JSON,
        account_status VARCHAR(50) DEFAULT 'ACTIVE',
        role VARCHAR(50) DEFAULT 'user',
        onboarding_status VARCHAR(50) DEFAULT 'NOT_STARTED',
        onboarding_step VARCHAR(50),
        onboarding_version INTEGER DEFAULT 1,
        password_reset_token VARCHAR(100),
        password_reset_expires DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """))

    # Notifications
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        message VARCHAR(255) NOT NULL,
        type VARCHAR(50),
        meta_data JSON,
        read_status BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """))

    # Chat Sessions
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        session_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME,
        context VARCHAR(255),
        title VARCHAR(255),
        mode VARCHAR(50) DEFAULT 'advisory'
    )
    """))
    
    # Chat History
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS chat_history (
        message_id INTEGER PRIMARY KEY,
        session_id INTEGER,
        user_id INTEGER,
        message_type VARCHAR(50),
        content VARCHAR(1000),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_summarized BOOLEAN DEFAULT 0
    )
    """))

    # Chat Summary
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS chat_summaries (
        summary_id INTEGER PRIMARY KEY,
        session_id INTEGER,
        summary_content VARCHAR(2000),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """))

    # Growth Tables
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL,
        plan_id VARCHAR(50) NOT NULL,
        status VARCHAR(20) NOT NULL,
        current_period_start DATETIME,
        current_period_end DATETIME,
        cancel_at_period_end BOOLEAN DEFAULT 0,
        canceled_at DATETIME,
        provider VARCHAR(50),
        provider_subscription_id VARCHAR(100),
        provider_customer_id VARCHAR(100),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users_v2 (id)
    )
    """))
    
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS tier_configs (
        id VARCHAR(50) PRIMARY KEY,
        plan_id VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        description VARCHAR(255),
        config_json JSON NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """))

    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS user_limit_overrides (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL,
        overrides_json JSON NOT NULL,
        reason VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users_v2 (id)
    )
    """))
    
    print("Tables created (SQL). checking schemas...")
    
    # Verify columns in case table existed but old schema
    try:
        cols = conn.execute(text("PRAGMA table_info(chat_sessions)")).fetchall()
        col_names = [c[1] for c in cols]
        if 'title' not in col_names:
            print("Altering chat_sessions to add title...")
            conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN title VARCHAR(255)"))
        if 'mode' not in col_names:
            print("Altering chat_sessions to add mode...")
            conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN mode VARCHAR(50) DEFAULT 'advisory'"))
            
        notif_cols = conn.execute(text("PRAGMA table_info(notifications)")).fetchall()
        n_names = [c[1] for c in notif_cols]
        if 'meta_data' not in n_names and 'metadata' in n_names:
            # Migration: rename or just add. Sqlite rename column:
            print("Renaming metadata to meta_data in notifications...")
            conn.execute(text("ALTER TABLE notifications RENAME COLUMN metadata TO meta_data"))

        # Token Tracking Migration
        print("Checking token tracking columns...")
        
        # Chat History
        ch_cols = conn.execute(text("PRAGMA table_info(chat_history)")).fetchall()
        ch_names = [c[1] for c in ch_cols]
        for col in ['input_tokens', 'output_tokens']:
            if col not in ch_names:
                print(f"Altering chat_history to add {col}...")
                conn.execute(text(f"ALTER TABLE chat_history ADD COLUMN {col} INTEGER"))
        if 'model_used' not in ch_names:
            print("Altering chat_history to add model_used...")
            conn.execute(text("ALTER TABLE chat_history ADD COLUMN model_used VARCHAR(100)"))

        # Messages (Core)
        # Ensure messages table exists first (it's in the core models)
        m_cols = conn.execute(text("PRAGMA table_info(messages)")).fetchall()
        if m_cols:
            m_names = [c[1] for c in m_cols]
            for col in ['input_tokens', 'output_tokens']:
                if col not in m_names:
                    print(f"Altering messages to add {col}...")
                    conn.execute(text(f"ALTER TABLE messages ADD COLUMN {col} INTEGER"))
            if 'model_used' not in m_names:
                print("Altering messages to add model_used...")
                conn.execute(text("ALTER TABLE messages ADD COLUMN model_used VARCHAR(100)"))

        # Users table migrations
        print("Checking users_v2 table columns...")
        u_cols = conn.execute(text("PRAGMA table_info(users_v2)")).fetchall()
        if u_cols:
            u_names = [c[1] for c in u_cols]
            # Add account_status if missing
            if 'account_status' not in u_names:
                print("Altering users_v2 to add account_status...")
                conn.execute(text("ALTER TABLE users_v2 ADD COLUMN account_status VARCHAR(50) DEFAULT 'ACTIVE'"))
            # Add role if missing
            if 'role' not in u_names:
                print("Altering users_v2 to add role...")
                conn.execute(text("ALTER TABLE users_v2 ADD COLUMN role VARCHAR(50) DEFAULT 'user'"))
            # Add onboarding_status if missing (just in case)
            if 'onboarding_status' not in u_names:
                print("Altering users_v2 to add onboarding_status...")
                conn.execute(text("ALTER TABLE users_v2 ADD COLUMN onboarding_status VARCHAR(50) DEFAULT 'NOT_STARTED'"))
    except Exception as e:
        print(f"Schema check error: {e}")

    conn.commit()

