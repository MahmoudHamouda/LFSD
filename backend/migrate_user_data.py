"""
Emergency fix: Move data from user-finance to the actual logged-in user
"""
from models.database import get_db_session
from models.models import User, VivIndex, FinancialTransaction, FinancialAccount, FinancialScore, LifeGoal
from sqlalchemy import update

db = get_db_session()

# The logged-in user ID (from /api/auth/me)
LOGGED_IN_USER_ID = "f95ddf3d-30a9-4aef-8384-d3ed0aaec8dc"
OLD_USER_ID = "user-finance"

print(f"Migrating data from {OLD_USER_ID} to {LOGGED_IN_USER_ID}")

# Update all related tables
tables_to_update = [
    (VivIndex, 'user_id'),
    (FinancialTransaction, 'user_id'),
    (FinancialAccount, 'user_id'),
    (FinancialScore, 'user_id'),
    (LifeGoal, 'user_id'),
]

for model, user_id_column in tables_to_update:
    count = db.query(model).filter(getattr(model, user_id_column) == OLD_USER_ID).count()
    if count > 0:
        print(f"  Updating {count} records in {model.__tablename__}")
        db.execute(
            update(model)
            .where(getattr(model, user_id_column) == OLD_USER_ID)
            .values({user_id_column: LOGGED_IN_USER_ID})
        )

# Delete the old user
old_user = db.query(User).filter(User.id == OLD_USER_ID).first()
if old_user:
    print(f"  Deleting old user: {OLD_USER_ID}")
    db.delete(old_user)

db.commit()
print("Migration complete!")
