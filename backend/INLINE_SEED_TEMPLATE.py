"""
Inline user seeding for Cloud Run endpoint
This version creates users inline without relying on seed_users module
"""

# Add this to your backend/app.py in the seed_force endpoint

INLINE_SEED_CODE = """
# Inside the /api/debug/seed_force endpoint, replace the user seeding section with:

try:
    from models.models import User, VivIndex
    from core.authentication import get_password_hash
    from datetime import datetime
    import uuid
    
    users_to_create = [
        {"id": "user-finance", "email": "finance@helm.com", "password": "P@ssword123", "name": "Finance User"},
        {"id": "user-empty", "email": "empty@helm.com", "password": "P@ssword123", "name": "Empty User"},
        {"id": "user-health", "email": "health@helm.com", "password": "P@ssword123", "name": "Health User"},
        {"id": "user-time", "email": "time@helm.com", "password": "P@ssword123", "name": "Time User"},
        {"id": "user-super", "email": "super@helm.com", "password": "P@ssword123", "name": "Super User"},
        {"id": "user-david", "email": "david@example.com", "password": "password", "name": "David"},
        {"id": "user-sara", "email": "sara@example.com", "password": "password", "name": "Sara"},
        {"id": "user-alex", "email": "alex@example.com", "password": "password", "name": "Alex"},
    ]
    
    for user_data in users_to_create:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user = User(
                id=user_data["id"],
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                profile_json={"name": user_data["name"]},
                onboarding_status="COMPLETE"
            )
            db.add(user)
            db.flush()
            
            # Add VivIndex
            viv = VivIndex(
                id=str(uuid.uuid4()),
                user_id=user.id,
                financial_score=50.0,
                health_score=50.0,
                time_score=50.0,
                snapshot_reason="Initial",
                timestamp=datetime.utcnow()
            )
            db.add(viv)
    
    db.commit()
    user_seed_status = "SUCCESS"
    print("Inline user seeding completed!")
    
except Exception as e:
    user_seed_error = str(e)
    user_seed_status = "FAILED"
    print(f"Inline seeding error: {e}")
"""

print(INLINE_SEED_CODE)
print("\n" + "="*60)
print("COPY THE CODE ABOVE AND:")
print("1. Edit backend/app.py in Cloud Console")
print("2. Replace the seed_users import section (lines 446-468)")
print("3. Paste the inline code above")
print("4. Deploy the revision")
print("="*60)
