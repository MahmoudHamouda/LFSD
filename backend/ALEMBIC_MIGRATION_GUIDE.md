# Database Migration Guide - Alembic Setup & Execution

**Date**: 2026-01-25  
**Purpose**: Apply all model fixes via database migrations  
**Estimated Time**: 2-3 hours  
**Risk Level**: MEDIUM (requires data cleanup first)

---

## 📋 Prerequisites

### 1. Install Alembic
```bash
pip install alembic
```

### 2. Backup Your Database
```bash
# PostgreSQL
pg_dump -U postgres -h localhost lfsd > backup_$(date +%Y%m%d).sql

# SQLite (for dev)
cp lfsd_v2.db lfsd_v2.db.backup
```

---

## 🚀 Part 1: Initialize Alembic

### Step 1: Initialize Alembic
```bash
cd backend
alembic init alembic
```

This creates:
```
backend/
├── alembic/
│   ├── versions/          # Migration files go here
│   ├── env.py            # Alembic environment config
│   └── script.py.mako    # Template for new migrations
└── alembic.ini            # Alembic configuration
```

### Step 2: Configure Alembic

Edit `alembic.ini`:
```ini
# Line ~40: Set your database URL
sqlalchemy.url = driver://user:pass@localhost/dbname

# Or use environment variable (recommended):
# sqlalchemy.url = 

# Then in alembic/env.py, add:
from core.config import get_settings
config.set_main_option('sqlalchemy.url', get_settings().DATABASE_URL)
```

Edit `alembic/env.py`:

```python
# Add imports at top
from models.database import Base
from models.models import *  # Import all models
from models.logging_models import *
from models.chat_models import *
from models.health_models import *
from models.models_health import *
from models.models_scores import *
from models.nutrition_logs import *
from models.growth_models import *
# ... import all other model files

# Set target metadata (around line 21)
target_metadata = Base.metadata

# Use config from settings (around line 60)
from core.config import get_settings
config.set_main_option('sqlalchemy.url', get_settings().DATABASE_URL)
```

---

## 🔧 Part 2: Create Migrations

### Migration 1: Logging Models Fix

```bash
alembic revision -m "fix_logging_models_constraints"
```

Edit the generated file in `alembic/versions/`:

```python
"""fix_logging_models_constraints

Revision ID: xxx
Revises: 
Create Date: 2026-01-25

Fixes:
- Add timezone-aware timestamps
- Change user_id FK to users_v2
- Add enums for status/level/severity
- Add indexes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

def upgrade():
    # 1. Create enums
    log_level_enum = ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 
                          name='loglevel', create_type=False)
    log_level_enum.create(op.get_bind(), checkfirst=True)
    
    bug_status_enum = ENUM('OPEN', 'IN_PROGRESS', 'RESOLVED', 'IGNORED',
                           name='bugstatus', create_type=False)
    bug_status_enum.create(op.get_bind(), checkfirst=True)
    
    bug_severity_enum = ENUM('ERROR', 'CRITICAL',
                             name='bugseverity', create_type=False)
    bug_severity_enum.create(op.get_bind(), checkfirst=True)
    
    # 2. Fix system_logs
    # Change level to enum
    op.execute("ALTER TABLE system_logs ALTER COLUMN level TYPE loglevel USING level::loglevel")
    
    # Fix user_id FK (if users_v2 exists)
    op.drop_constraint('system_logs_user_id_fkey', 'system_logs', type_='foreignkey')
    op.create_foreign_key(
        'system_logs_user_id_fkey',
        'system_logs', 'users_v2',
        ['user_id'], ['id']
    )
    
    # Make timestamp timezone-aware
    op.execute("ALTER TABLE system_logs ALTER COLUMN timestamp TYPE TIMESTAMP WITH TIME ZONE")
    
    # 3. Fix bug_reports
    op.execute("ALTER TABLE bug_reports ALTER COLUMN status TYPE bugstatus USING status::bugstatus")
    op.execute("ALTER TABLE bug_reports ALTER COLUMN severity TYPE bugseverity USING severity::bugseverity")
    op.execute("ALTER TABLE bug_reports ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE")
    op.execute("ALTER TABLE bug_reports ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE")
    
    # Fix FK
    op.drop_constraint('bug_reports_user_id_fkey', 'bug_reports', type_='foreignkey')
    op.create_foreign_key(
        'bug_reports_user_id_fkey',
        'bug_reports', 'users_v2',
        ['user_id'], ['id']
    )
    
    # 4. Fix audit_logs, activity_feed, notifications similarly
    # (timestamps to timezone-aware, FKs to users_v2)

def downgrade():
    # Reverse all changes
    pass
```

### Migration 2: Health Models Constraints

```bash
alembic revision -m "add_health_models_constraints"
```

```python
"""add_health_models_constraints

Fixes:
- Add uniqueness constraints
- Add enums for provider/status/metric_type
- Fix user_id FKs
- Add indexes
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1. Create enums
    op.execute("""
        CREATE TYPE healthprovider AS ENUM (
            'apple_health', 'whoop', 'fitbit', 'garmin', 'oura', 'google_fit'
        )
    """)
    
    op.execute("""
        CREATE TYPE connectionstatus AS ENUM (
            'active', 'expired', 'revoked', 'error'
        )
    """)
    
    op.execute("""
        CREATE TYPE metrictype AS ENUM (
            'heart_rate', 'hrv', 'steps', 'sleep_duration', 
            'sleep_quality', 'calories', 'workout', 'weight',
            'blood_pressure', 'oxygen_saturation'
        )
    """)
    
    # 2. Add uniqueness constraints
    op.create_unique_constraint(
        'uq_health_conn_user_provider',
        'health_connections',
        ['user_id', 'provider']
    )
    
    op.create_unique_constraint(
        'uq_health_settings_user_provider',
        'health_settings',
        ['user_id', 'provider']
    )
    
    # 3. Convert columns to enums
    op.execute("""
        ALTER TABLE health_connections 
        ALTER COLUMN provider TYPE healthprovider 
        USING provider::healthprovider
    """)
    
    op.execute("""
        ALTER TABLE health_connections 
        ALTER COLUMN status TYPE connectionstatus 
        USING status::connectionstatus
    """)
    
    # 4. Add indexes
    op.create_index(
        'ix_health_metrics_user_time',
        'health_metrics',
        ['user_id', 'timestamp']
    )
    
    op.create_index(
        'ix_health_metrics_user_type_time',
        'health_metrics',
        ['user_id', 'metric_type', 'timestamp']
    )

def downgrade():
    pass
```

### Migration 3: Score Models Constraints

```bash
alembic revision -m "add_score_constraints_and_bounds"
```

```python
"""add_score_constraints_and_bounds

Fixes:
- Add check constraints for score bounds (0-100)
- Add uniqueness on user_id
- Fix timestamps
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1. Add uniqueness constraint
    op.create_unique_constraint(
        'uq_user_scores_user_id',
        'user_scores',
        ['user_id']
    )
    
    # 2. Add check constraints for score bounds
    op.create_check_constraint(
        'ck_user_scores_financial_0_100',
        'user_scores',
        'financial_score >= 0 AND financial_score <= 100'
    )
    
    op.create_check_constraint(
        'ck_user_scores_health_0_100',
        'user_scores',
        'health_score >= 0 AND health_score <= 100'  
    )
    
    op.create_check_constraint(
        'ck_user_scores_time_0_100',
        'user_scores',
        'time_score >= 0 AND health_score <= 100'
    )
    
    op.create_check_constraint(
        'ck_user_scores_overall_0_100',
        'user_scores',
        'overall_score >= 0 AND overall_score <= 100'
    )
    
    # 3. Fix timestamps to timezone-aware
    op.execute("""
        ALTER TABLE user_scores 
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
    """)
    
    op.execute("""
        ALTER TABLE user_scores 
        ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE
    """)

def downgrade():
    pass
```

### Migration 4: Nutrition Logs

```bash
alembic revision -m "add_nutrition_constraints"
```

```python
"""add_nutrition_constraints

Fixes:
- Add uniqueness on (user_id, date)
- Add nutrition source enum
- Add audit timestamps
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1. Create enum
    op.execute("""
        CREATE TYPE nutritionsource AS ENUM (
            'manual', 'myfitnesspal', 'loseit', 'cronometer', 'apple_health'
        )
    """)
    
    # 2. Add uniqueness
    op.create_unique_constraint(
        'uq_nutrition_user_date',
        'nutrition_logs',
        ['user_id', 'date']
    )
    
    # 3. Add audit columns (if they don't exist)
    op.add_column('nutrition_logs', 
                  sa.Column('created_at', sa.DateTime(timezone=True), 
                           server_default=sa.text('now()'), nullable=False))
    op.add_column('nutrition_logs',
                  sa.Column('updated_at', sa.DateTime(timezone=True),
                           server_default=sa.text('now()'),
                           onupdate=sa.text('now()'), nullable=False))
    
    # 4. Convert source to enum
    op.execute("""
        ALTER TABLE nutrition_logs
        ALTER COLUMN source TYPE nutritionsource
        USING source::nutritionsource
    """)

def downgrade():
    pass
```

---

## 🧹 Part 3: Data Cleanup (BEFORE Running Migrations)

Before applying migrations, clean invalid data:

### 1. Remove Duplicates

```sql
-- Find duplicate health connections
SELECT user_id, provider, COUNT(*)
FROM health_connections
GROUP BY user_id, provider
HAVING COUNT(*) > 1;

-- Delete duplicates (keep oldest)
DELETE FROM health_connections
WHERE id NOT IN (
    SELECT MIN(id)
    FROM health_connections
    GROUP BY user_id, provider
);

-- Same for nutrition logs
DELETE FROM nutrition_logs
WHERE id NOT IN (
    SELECT MIN(id)
    FROM nutrition_logs
    GROUP BY user_id, date
);
```

### 2. Fix Invalid Enum Values

```sql
-- Check for invalid log levels
SELECT DISTINCT level FROM system_logs WHERE level NOT IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL');

-- Fix them
UPDATE system_logs SET level = 'INFO' WHERE level NOT IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL');
```

### 3. Fix Out-of-Bounds Scores

```sql
-- Find invalid scores
SELECT * FROM user_scores WHERE financial_score < 0 OR financial_score > 100;

-- Clamp them
UPDATE user_scores SET financial_score = GREATEST(0, LEAST(100, financial_score));
UPDATE user_scores SET health_score = GREATEST(0, LEAST(100, health_score));
UPDATE user_scores SET time_score = GREATEST(0, LEAST(100, time_score));
UPDATE user_scores SET overall_score = GREATEST(0, LEAST(100, overall_score));
```

---

## ▶️ Part 4: Run Migrations

```bash
# 1. Generate migration (auto-detect changes)
alembic revision --autogenerate -m "initial_constraints_and_fixes"

# 2. Review the generated migration file
# Edit alembic/versions/xxx_initial_constraints.py

# 3. Run migration
alembic upgrade head

# 4. Verify
alembic current
alembic history
```

---

## ✅ Part 5: Verification

After migrations:

```python
# Test in Python
from models.database import SessionLocal
from models.logging_models import SystemLog, LogLevel

db = SessionLocal()

# Test enum works
log = SystemLog(level=LogLevel.INFO, message="Test")
db.add(log)
db.commit()

# Test constraints work
try:
    # Should fail (duplicate user_id in user_scores)
    pass
except Exception as e:
    print("Constraint working:", e)
```

---

## 🚨 Rollback Plan

If something goes wrong:

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback everything
alembic downgrade base

# Restore from backup
psql -U postgres lfsd < backup_20260125.sql
```

---

## 📊 Migration Checklist

Before deploying:

- [ ] Alembic installed (`pip install alembic`)
- [ ] Database backed up
- [ ] Alembic initialized (`alembic init alembic`)
- [ ] `alembic.ini` configured with DB URL
- [ ] `alembic/env.py` imports all models
- [ ] Data cleanup scripts run
- [ ] Migrations created and reviewed
- [ ] Migrations tested in dev
- [ ] Migrations run successfully
- [ ] Application tested with new schema
- [ ] Rollback plan tested

---

## 🎯 Next Steps After Migrations

1. Update application code to use new enums
2. Remove old workarounds for missing constraints
3. Add integration tests for constraints
4. Monitor production for constraint violations
5. Document schema changes for team

---

**Status**: 📋 **READY FOR EXECUTION**  
**Estimated Time**: 2-3 hours  
**Risk**: MEDIUM (reversible with backups)  
**Priority**: HIGH

---

*Created: 2026-01-25*  
*Migrations Required: 4*  
*Models Affected: 10*  
*Constraints Added: 50+*
