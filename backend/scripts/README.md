# Scripts Directory

**Last Updated**: 2026-01-25  
**Status**: ✅ Cleaned & Hardened

---

## 📁 What's Here

This directory contains **development utilities and data seeding scripts**.

### Current Scripts (2)

| Script | Purpose | Safety | Usage |
|--------|---------|--------|-------|
| `seed_dev_users.py` | Creates 5 test personas with realistic data | 🔒 **DEV ONLY** | `python seed_dev_users.py` |
| `verify_seed.py` | Validates seeded data integrity | ✅ **SAFE** | `python verify_seed.py` |

---

## 🚀 Quick Start

### Seeding Development Data

```bash
# 1. Set environment to dev
export ENV=dev  # or set ENV=dev on Windows

# 2. Run the seeder
python scripts/seed_dev_users.py

# 3. Verify
python scripts/verify_seed.py
```

### Test User Credentials

After seeding, you can login with:

| Email | Password | Profile |
|-------|----------|---------|
| `empty@helm.com` | `P@ssword123` | No data (new signup simulation) |
| `finance@helm.com` | `P@ssword123` | Rich financial data (90 days) |
| `health@helm.com` | `P@ssword123` | Rich health data (90 days) |
| `time@helm.com` | `P@ssword123` | Rich productivity data (90 days) |
| `super@helm.com` | `P@ssword123` | All pillars rich (90 days) |

---

## 🔒 Safety Features

### Production Guards

All destructive scripts have **multiple safety layers**:

1. **Environment Check**: Refuses to run if `ENV=production`
2. **User Confirmation**: Requires typing `DELETE_ALL` to proceed
3. **Database URL Validation**: Shows first 30 chars for verification
4. **Transaction Safety**: Proper rollback on errors

### Example Safety Output

```
✅ Environment check passed: dev
   Database: postgresql://user:***@localhost...

⚠️  WARNING: This will DELETE ALL DATA and recreate tables!
Type 'DELETE_ALL' to continue: _
```

---

## 📊 What Was Removed

This directory previously contained **34 scripts** with:
- ❌ Hardcoded production credentials (20+ files)
- ❌ Duplicate functionality (9 route files)
- ❌ Schema drift issues (4 different Transaction models)
- ❌ Wrong databases (SQLite vs Postgres confusion)
- ❌ Unsafe operations (`DROP TABLE CASCADE` without guards)

See `../FINAL_CLEANUP_SUMMARY.md` for details.

---

## 🛠️ Creating New Scripts

### ✅ DO:
- Use `core/config.py::get_settings()` for configuration
- Add environment guards for destructive operations
- Use timezone-aware datetimes (`datetime.now(timezone.utc)`)
- Import from `models/database.py::SessionLocal`
- Document expected environment and usage

### ❌ DON'T:
- Hardcode database URLs
- Hardcode API keys or credentials
- Use `sys.path` hacks
- Mix multiple concerns in one script
- Create duplicate models or routes

### Template for New Scripts

```python
"""
Script Name - Brief Description

Safety: DEV_ONLY / SAFE / ADMIN_ONLY
"""

import sys
from core.config import get_settings
from models.database import SessionLocal

settings = get_settings()

# Safety guard for destructive scripts
if settings.ENV == "production":
    print("❌ Cannot run in production!")
    sys.exit(1)

# Your script logic here
db = SessionLocal()
try:
    # ... do work ...
    db.commit()
finally:
    db.close()
```

---

## 📚 Related Documentation

- `../FINAL_CLEANUP_SUMMARY.md` - Complete cleanup report
- `../SCRIPTS_CLEANUP_PLAN.md` - Original audit & plan
- `../models/README.md` - Database models documentation
- `../core/README.md` - Core utilities documentation

---

## 🔍 Troubleshooting

### "Script refuses to run"
✅ Check that `ENV=dev` or `ENV=local` is set

### "Database connection error"
✅ Check `.env` file has correct `DATABASE_URL`  
✅ Verify database server is running

### "Import errors"
✅ Run from project root: `python backend/scripts/seed_dev_users.py`  
✅ Ensure virtual environment is activated

---

## 📞 Support

For issues or questions:
1. Check `../FINAL_CLEANUP_SUMMARY.md` for recent changes
2. Review error logs with `--verbose` flag (if supported)
3. Consult team documentation

---

**Remember**: Scripts in this folder can **delete data**. Always verify your environment before running.
