import os
import sys
from alembic.config import Config
from alembic import command

# Mock environment variable
os.environ["DATABASE_URL"] = "sqlite:///./lfsd_v2.db"

# Create config
alembic_cfg = Config("alembic.ini")

try:
    command.revision(alembic_cfg, autogenerate=True, message="debug_migration")
    print("SUCCESS")
except Exception as e:
    with open("alembic_error.log", "w") as f:
        f.write(str(e))
    print("FAILED. See alembic_error.log")
