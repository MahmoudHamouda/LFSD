"""
Fix foreign key constraints on chat_sessions to point to users_v2 instead of users.
Run this via: POST /api/debug/run_migration?secret=<SECRET>
Or directly against the database.
"""

import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import engine
from sqlalchemy import text


def fix_chat_fk():
    """Drop old FK to 'users' table and create new FK to 'users_v2' table."""
    with engine.begin() as conn:
        # Drop old FK if it exists
        conn.execute(
            text(
                """
            ALTER TABLE chat_sessions 
            DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey
        """
            )
        )
        print("Dropped old FK constraint on chat_sessions")

        # Drop old FK on chat_history if it exists
        conn.execute(
            text(
                """
            ALTER TABLE chat_history 
            DROP CONSTRAINT IF EXISTS chat_history_user_id_fkey
        """
            )
        )
        print("Dropped old FK constraint on chat_history")

        # Drop old FK on feedback if it exists
        conn.execute(
            text(
                """
            ALTER TABLE feedback 
            DROP CONSTRAINT IF EXISTS feedback_user_id_fkey
        """
            )
        )
        print("Dropped old FK constraint on feedback")

        # Recreate FKs pointing to users_v2
        try:
            conn.execute(
                text(
                    """
                ALTER TABLE chat_sessions 
                ADD CONSTRAINT chat_sessions_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users_v2(id)
            """
                )
            )
            print("Created new FK on chat_sessions -> users_v2")
        except Exception as e:
            print(f"Could not create FK on chat_sessions: {e}")

        try:
            conn.execute(
                text(
                    """
                ALTER TABLE chat_history 
                ADD CONSTRAINT chat_history_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users_v2(id)
            """
                )
            )
            print("Created new FK on chat_history -> users_v2")
        except Exception as e:
            print(f"Could not create FK on chat_history: {e}")

        try:
            conn.execute(
                text(
                    """
                ALTER TABLE feedback 
                ADD CONSTRAINT feedback_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users_v2(id)
            """
                )
            )
            print("Created new FK on feedback -> users_v2")
        except Exception as e:
            print(f"Could not create FK on feedback: {e}")

    print("Done! FK constraints updated.")


if __name__ == "__main__":
    fix_chat_fk()
